#!/usr/bin/env python3
"""Execute one bounded autonomous repair attempt on an agent branch."""

from __future__ import annotations

import os
import subprocess

from blokus.automation import (
    COMMENT_MARKERS,
    REPAIR_STATE_MARKER,
    parse_state_marker,
    render_state_marker,
    repair_allowed,
)

from gh_helpers import GitHubClient, load_event_payload


def _run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def _has_diff() -> bool:
    result = subprocess.run(
        ["git", "status", "--short"],
        check=True,
        text=True,
        capture_output=True,
    )
    return bool(result.stdout.strip())


def _commit_and_push(branch_name: str, pull_number: int) -> str:
    _run(["git", "config", "user.name", "github-actions[bot]"])
    _run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"])
    _run(["git", "add", "-A"])
    _run(["git", "commit", "-m", f"Apply bounded repair for PR #{pull_number}"])
    _run(["git", "push", "origin", f"HEAD:{branch_name}"])
    return "pushed bounded repair patch"


def main() -> int:
    payload = load_event_payload(os.environ["GITHUB_EVENT_PATH"])
    inputs = payload["inputs"]
    pull_number = int(inputs["pull_number"])
    branch_name = inputs["head_branch"]
    run_id = int(inputs["ci_run_id"])
    category = inputs["failure_category"]

    client = GitHubClient(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    pull_request = client.get_pull_request(pull_number)
    labels = [label["name"] for label in pull_request["labels"]]
    changed_files = [item["filename"] for item in client.list_pr_files(pull_number)]

    state = {"attempts": 0, "handled_runs": []}
    for comment in reversed(client.list_issue_comments(pull_number)):
        parsed = parse_state_marker(REPAIR_STATE_MARKER, comment.get("body", ""))
        if parsed is not None:
            state = parsed
            break

    handled_runs = [int(item) for item in state.get("handled_runs", [])]
    if run_id in handled_runs:
        return 0

    retry_count = int(state.get("attempts", 0))
    allowed, reason = repair_allowed(branch_name, labels, category, changed_files, retry_count)
    next_state = {
        "attempts": retry_count,
        "handled_runs": handled_runs,
    }

    if not allowed:
        client.remove_label(pull_number, "repair-loop")
        client.add_labels(pull_number, ["agent-blocked", "needs-review"])
        body = "\n".join(
            [
                f"<!-- {COMMENT_MARKERS['repair']} -->",
                "## Autonomous Repair",
                "- Status: `stopped`",
                f"- Reason: {reason}",
                render_state_marker(REPAIR_STATE_MARKER, next_state),
            ]
        )
        client.upsert_issue_comment(pull_number, COMMENT_MARKERS["repair"], body)
        return 0

    next_state["attempts"] = retry_count + 1
    next_state["handled_runs"] = handled_runs + [run_id]

    if category == "lint":
        _run(["./scripts/install.sh"])
        _run([".venv/bin/python", "-m", "pip", "install", "ruff"])
        _run([".venv/bin/ruff", "check", "--fix", "."])
        if _has_diff():
            action_taken = _commit_and_push(branch_name, pull_number)
        else:
            client.rerun_failed_jobs(run_id)
            action_taken = "reran failed CI jobs after no deterministic lint fix applied"
    else:
        client.rerun_failed_jobs(run_id)
        action_taken = "reran failed CI jobs within the bounded retry budget"

    client.add_labels(pull_number, ["repair-loop"])
    client.remove_label(pull_number, "agent-blocked")

    body = "\n".join(
        [
            f"<!-- {COMMENT_MARKERS['repair']} -->",
            "## Autonomous Repair",
            "- Status: `attempted`",
            f"- Attempt: `{next_state['attempts']}/2`",
            f"- Failure category: `{category}`",
            f"- Action taken: {action_taken}",
            render_state_marker(REPAIR_STATE_MARKER, next_state),
        ]
    )
    client.upsert_issue_comment(pull_number, COMMENT_MARKERS["repair"], body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
