#!/usr/bin/env python3
"""Generate a lightweight weekly governance report for the autonomous pipeline."""

from __future__ import annotations

import os
from collections import Counter
from datetime import UTC, datetime, timedelta
from pathlib import Path

from gh_helpers import GitHubClient


WORKFLOWS = {
    "ci": "ci.yml",
    "release-candidate": "release-candidate.yml",
    "promote-submission": "promote-submission.yml",
    "dependency-review": "dependency-review.yml",
    "code-scanning": "code-scanning.yml",
}


def _parse_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    return datetime.fromisoformat(raw.replace("Z", "+00:00"))


def _recent_runs(client: GitHubClient, workflow_file: str, *, days: int = 30) -> list[dict[str, object]]:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    runs = client.list_workflow_runs(workflow_file, per_page=25)
    recent: list[dict[str, object]] = []
    for run in runs:
        created_at = _parse_timestamp(run.get("created_at"))
        if created_at is not None and created_at >= cutoff:
            recent.append(run)
    return recent


def _summarize_runs(runs: list[dict[str, object]]) -> Counter[str]:
    counter: Counter[str] = Counter()
    for run in runs:
        conclusion = str(run.get("conclusion") or "in_progress")
        counter[conclusion] += 1
    return counter


def _approval_counts(client: GitHubClient, runs: list[dict[str, object]], job_name: str) -> Counter[str]:
    counter: Counter[str] = Counter()
    for run in runs[:10]:
        run_id = int(run["id"])
        for job in client.list_workflow_run_jobs(run_id):
            if job.get("name") != job_name:
                continue
            counter[str(job.get("conclusion") or "in_progress")] += 1
            break
    return counter


def _expiring_artifacts(client: GitHubClient) -> list[dict[str, object]]:
    cutoff = datetime.now(UTC) + timedelta(days=7)
    results: list[dict[str, object]] = []
    for artifact in client.list_artifacts(per_page=100):
        if artifact.get("expired"):
            continue
        expires_at = _parse_timestamp(artifact.get("expires_at"))
        if expires_at is not None and expires_at <= cutoff:
            results.append(artifact)
    return results[:10]


def main() -> int:
    client = GitHubClient(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])

    workflow_runs = {
        name: _recent_runs(client, workflow_file)
        for name, workflow_file in WORKFLOWS.items()
    }
    run_summaries = {
        name: _summarize_runs(runs)
        for name, runs in workflow_runs.items()
    }
    failed_total = sum(
        counter.get("failure", 0) + counter.get("cancelled", 0) + counter.get("timed_out", 0)
        for counter in run_summaries.values()
    )
    rc_approvals = _approval_counts(client, workflow_runs["release-candidate"], "rc-approval")
    submission_approvals = _approval_counts(
        client,
        workflow_runs["promote-submission"],
        "submission-approval",
    )
    expiring_artifacts = _expiring_artifacts(client)

    lines = [
        "# Governance Review",
        "",
        f"- Generated at: `{datetime.now(UTC).isoformat()}`",
        "- Window: last `30` days of workflow activity",
        f"- Total failed or cancelled runs across tracked workflows: `{failed_total}`",
        "",
        "## Workflow run summary",
    ]

    for name in WORKFLOWS:
        summary = run_summaries[name]
        if not summary:
            lines.append(f"- `{name}`: no runs in the current review window")
            continue
        parts = ", ".join(f"`{key}`={value}" for key, value in sorted(summary.items()))
        lines.append(f"- `{name}`: {parts}")

    lines.extend(
        [
            "",
            "## Approval-gate outcomes",
            f"- `rc-approval`: {', '.join(f'`{key}`={value}' for key, value in sorted(rc_approvals.items())) or '`no recent approval jobs`'}",
            f"- `submission-approval`: {', '.join(f'`{key}`={value}' for key, value in sorted(submission_approvals.items())) or '`no recent approval jobs`'}",
            "",
            "## Artifact retention watch",
        ]
    )

    if expiring_artifacts:
        for artifact in expiring_artifacts:
            lines.append(
                f"- `{artifact['name']}` expires at `{artifact['expires_at']}`"
            )
    else:
        lines.append("- No retained workflow artifacts are due to expire within the next seven days.")

    lines.extend(
        [
            "",
            "## Team reminders",
            "- Review Dependabot and dependency-review results for any dependency-changing PRs.",
            "- Review code-scanning alerts and triage false positives rather than ignoring them.",
            "- Update `docs/AUTONOMY_SCORECARD.md` after the next RC or milestone retro.",
            "- If the same autonomy failure pattern appears in two consecutive RCs, follow `docs/INCIDENT_RESPONSE.md` and pause the affected automation path.",
        ]
    )

    output_path = Path("artifacts/governance-review/report.md")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
