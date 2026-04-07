#!/usr/bin/env python3
"""Post structured review intelligence for a pull request."""

from __future__ import annotations

import os

from blokus.automation import COMMENT_MARKERS, infer_domains_from_paths, is_sensitive_path, tests_missing

from gh_helpers import GitHubClient, load_event_payload


def _checked(body: str, fragment: str) -> bool:
    normalized = body.lower()
    target = fragment.lower()
    return f"- [x] {target}" in normalized


def main() -> int:
    payload = load_event_payload(os.environ["GITHUB_EVENT_PATH"])
    pull_request = payload["pull_request"]
    pull_number = pull_request["number"]
    pr_body = pull_request.get("body") or ""
    labels = [label["name"] for label in pull_request["labels"]]

    client = GitHubClient(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    files = client.list_pr_files(pull_number)
    changed_paths = [item["filename"] for item in files]
    impacted_domains = infer_domains_from_paths(changed_paths)
    workflow_sensitive = any(is_sensitive_path(path) for path in changed_paths)
    missing_test_signal = tests_missing(changed_paths) and not _checked(pr_body, "Tests updated")

    add_labels = ["needs-review"]
    if workflow_sensitive:
        add_labels.append("workflow-sensitive")
    client.add_labels(pull_number, [label for label in add_labels if label not in labels])
    if "workflow-sensitive" in labels and not workflow_sensitive:
        client.remove_label(pull_number, "workflow-sensitive")

    body_lines = [
        f"<!-- {COMMENT_MARKERS['pr_intelligence']} -->",
        "## PR Intelligence",
        f"- Changed files: `{len(changed_paths)}`",
        f"- Impacted domains: {', '.join(f'`{label}`' for label in impacted_domains) or '`none inferred`'}",
        f"- Workflow-sensitive: `{'yes' if workflow_sensitive else 'no'}`",
        f"- Tests appear missing: `{'yes' if missing_test_signal else 'no'}`",
        "",
        "### Review checklist",
        "- [ ] PR matches the linked issue and acceptance criteria.",
        "- [ ] Tests were added or updated for behavior changes.",
        "- [ ] CLI behavior was checked if command paths changed.",
        "- [ ] Fixtures, schemas, or docs changed where user-facing contracts moved.",
        "- [ ] No hidden rule-semantics change slipped in without explanation.",
    ]

    if changed_paths:
        preview = changed_paths[:12]
        body_lines.extend(
            [
                "",
                "### Changed paths",
                *(f"- `{path}`" for path in preview),
            ]
        )
        if len(changed_paths) > len(preview):
            body_lines.append(f"- ...and `{len(changed_paths) - len(preview)}` more")

    warnings = []
    if missing_test_signal:
        warnings.append("Code-bearing changes landed without matching `tests/` updates.")
    if workflow_sensitive:
        warnings.append("The PR changes `.github/` content, so autonomous repair should stay disabled.")
    if warnings:
        body_lines.extend(["", "### Flags", *(f"- {warning}" for warning in warnings)])

    client.upsert_issue_comment(
        pull_number,
        COMMENT_MARKERS["pr_intelligence"],
        "\n".join(body_lines),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
