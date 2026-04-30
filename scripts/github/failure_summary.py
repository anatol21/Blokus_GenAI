#!/usr/bin/env python3
"""Summarize CI failures and dispatch bounded repair when allowed."""

from __future__ import annotations

import os

from blokus.automation import (
    COMMENT_MARKERS,
    REPAIR_STATE_MARKER,
    classify_failure_category,
    parse_state_marker,
    render_state_marker,
    repair_allowed,
)

from gh_helpers import GitHubClient, load_event_payload


def main() -> int:
    payload = load_event_payload(os.environ["GITHUB_EVENT_PATH"])
    workflow_run = payload["workflow_run"]
    pull_requests = workflow_run.get("pull_requests") or []
    if not pull_requests:
        return 0

    pull_number = int(pull_requests[0]["number"])
    branch_name = workflow_run["head_branch"]
    run_id = int(workflow_run["id"])
    client = GitHubClient(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])

    jobs = client.list_workflow_run_jobs(run_id)
    failed_jobs = [
        job["name"]
        for job in jobs
        if job.get("conclusion") in {"failure", "cancelled", "timed_out", "startup_failure"}
    ]
    category = classify_failure_category(failed_jobs)

    pull_request = client.get_pull_request(pull_number)
    labels = [label["name"] for label in pull_request["labels"]]
    changed_files = [item["filename"] for item in client.list_pr_files(pull_number)]

    repair_comments = client.list_issue_comments(pull_number)
    repair_state = {"attempts": 0, "handled_runs": []}
    for comment in reversed(repair_comments):
        parsed = parse_state_marker(REPAIR_STATE_MARKER, comment.get("body", ""))
        if parsed is not None:
            repair_state = parsed
            break

    allowed, reason = repair_allowed(
        branch_name=branch_name,
        labels=labels,
        category=category,
        changed_files=changed_files,
        retry_count=int(repair_state.get("attempts", 0)),
    )

    body_lines = [
        f"<!-- {COMMENT_MARKERS['failure_summary']} -->",
        "## CI Failure Summary",
        f"- Source workflow: `{workflow_run['name']}`",
        f"- Source run: `{run_id}`",
        f"- Branch: `{branch_name}`",
        f"- Failed jobs: {', '.join(f'`{name}`' for name in failed_jobs) or '`none detected`'}",
        f"- Failure category: `{category}`",
        f"- Autonomous repair eligible: `{'yes' if allowed else 'no'}`",
        "",
        "### Classification note",
        reason,
    ]
    body_lines.append(render_state_marker("agent-failure-summary-state", {"category": category, "run_id": run_id}))
    client.upsert_issue_comment(
        pull_number,
        COMMENT_MARKERS["failure_summary"],
        "\n".join(body_lines),
    )

    if allowed:
        client.add_labels(pull_number, ["repair-loop"])
        client.dispatch_workflow(
            "repair-loop.yml",
            branch_name,
            {
                "pull_number": str(pull_number),
                "head_branch": branch_name,
                "ci_run_id": str(run_id),
                "failure_category": category,
            },
        )
    else:
        client.remove_label(pull_number, "repair-loop")
        if branch_name.startswith("agent/"):
            client.add_labels(pull_number, ["agent-blocked", "needs-review"])

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
