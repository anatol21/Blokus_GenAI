#!/usr/bin/env python3
"""Route structured issues into agent-ready or human-spec states."""

from __future__ import annotations

import os

from blokus.automation import COMMENT_MARKERS, triage_issue

from gh_helpers import GitHubClient, load_event_payload


def main() -> int:
    payload = load_event_payload(os.environ["GITHUB_EVENT_PATH"])
    issue = payload["issue"]
    issue_number = issue["number"]
    labels = [label["name"] for label in issue["labels"]]

    decision = triage_issue(issue["title"], issue.get("body") or "", labels)
    client = GitHubClient(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])

    labels_to_add = [label for label in decision["add_labels"] if label not in labels]
    labels_to_remove = [label for label in decision["remove_labels"] if label in labels]
    client.add_labels(issue_number, labels_to_add)
    for label in labels_to_remove:
        client.remove_label(issue_number, label)

    body_lines = [
        f"<!-- {COMMENT_MARKERS['triage']} -->",
        "## Agent Triage",
        f"- Route: `{decision['state']}`",
        f"- Issue kind: `{decision['kind']}`",
        f"- Ambiguity: `{decision['ambiguity']}`",
    ]
    if decision["areas"]:
        body_lines.append(f"- Areas affected: {', '.join(f'`{item}`' for item in decision['areas'])}")
    if decision["likely_paths"]:
        body_lines.append(
            f"- Likely paths: {', '.join(f'`{item}`' for item in decision['likely_paths'])}"
        )
    body_lines.append("")
    body_lines.append("### Why it landed here")
    for reason in decision["reasons"]:
        body_lines.append(f"- {reason}")

    if decision["state"] == "agent-ready":
        body_lines.extend(
            [
                "",
                "This issue is structured enough for branch-level agent work.",
            ]
        )
    else:
        body_lines.extend(
            [
                "",
                "This issue needs human clarification before an agent should implement it.",
            ]
        )

    client.upsert_issue_comment(
        issue_number,
        COMMENT_MARKERS["triage"],
        "\n".join(body_lines),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
