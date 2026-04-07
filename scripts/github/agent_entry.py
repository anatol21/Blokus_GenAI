#!/usr/bin/env python3
"""Prepare a structured agent task packet for one issue."""

from __future__ import annotations

import os

from blokus.automation import (
    COMMENT_MARKERS,
    build_agent_branch_name,
    parse_markdown_sections,
    section_value,
)

from gh_helpers import GitHubClient, load_event_payload


def _issue_number_from_payload(payload: dict[str, object]) -> int:
    if "issue" in payload:
        return int(payload["issue"]["number"])
    return int(payload["inputs"]["issue_number"])


def main() -> int:
    payload = load_event_payload(os.environ["GITHUB_EVENT_PATH"])
    issue_number = _issue_number_from_payload(payload)
    client = GitHubClient(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    issue = client.get_issue(issue_number)

    labels = [label["name"] for label in issue["labels"]]
    if "agent-ready" not in labels or "needs-human-spec" in labels:
        body = "\n".join(
            [
                f"<!-- {COMMENT_MARKERS['entry']} -->",
                "## Agent Task Packet",
                "This issue is not currently eligible for agent entry.",
                "",
                "- `agent-ready` must be present.",
                "- `needs-human-spec` must be absent.",
            ]
        )
        client.upsert_issue_comment(issue_number, COMMENT_MARKERS["entry"], body)
        return 0

    sections = parse_markdown_sections(issue.get("body") or "")
    branch_name = build_agent_branch_name(issue_number, issue["title"])

    body_lines = [
        f"<!-- {COMMENT_MARKERS['entry']} -->",
        "## Agent Task Packet",
        f"- Issue: #{issue_number}",
        f"- Suggested branch: `{branch_name}`",
        f"- Labels: {', '.join(f'`{label}`' for label in labels)}",
        "",
        "### Problem statement",
        section_value(sections, "problem statement") or "Not provided.",
        "",
        "### Acceptance criteria",
        section_value(sections, "acceptance criteria") or "Not provided.",
        "",
        "### Required tests",
        section_value(sections, "required tests") or "Not provided.",
        "",
        "### Likely paths",
        section_value(sections, "files likely affected") or "Not provided.",
        "",
        "### Guardrails",
        "- Stay on the dedicated `agent/*` branch for this issue.",
        "- Update tests for any changed behavior.",
        "- Stop and escalate if rule semantics become ambiguous.",
        "- Do not change repository settings, secrets, branch protections, or protected environments.",
    ]

    if "workflow-sensitive" in labels:
        body_lines.extend(
            [
                "",
                "### Human Gate",
                "This issue touches workflow-sensitive areas. Agent work may draft changes, but autonomous repair remains disabled.",
            ]
        )

    body_lines.extend(
        [
            "",
            "### GitHub-native handoff",
            "Assign this issue to GitHub Copilot coding agent from the issue sidebar when you want GitHub-hosted implementation to start.",
        ]
    )

    client.upsert_issue_comment(issue_number, COMMENT_MARKERS["entry"], "\n".join(body_lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
