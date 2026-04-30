#!/usr/bin/env python3
"""Run agentic pull-request review and publish its artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from blokus.automation import COMMENT_MARKERS
from blokus.review.config import load_review_config
from blokus.review.coordinator import ReviewCoordinator
from gh_helpers import GitHubClient, load_event_payload


def main() -> int:
    args = _parse_args()
    repo_root = _resolve_repo_root()
    config = load_review_config(repo_root=repo_root)
    coordinator = ReviewCoordinator(config)

    event_payload = None
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if event_path and Path(event_path).exists():
        event_payload = load_event_payload(event_path)

    run = coordinator.run(
        event_payload=event_payload,
        base_ref=args.base_ref or os.environ.get("REVIEW_BASE_REF"),
        head_ref=args.head_ref or os.environ.get("REVIEW_HEAD_REF"),
        pr_number=args.pr_number or _env_int("REVIEW_PULL_NUMBER"),
    )

    json_path = Path(args.json_out)
    markdown_path = Path(args.markdown_out)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(run.result.to_dict(), indent=2) + "\n", encoding="utf-8")
    markdown_path.write_text(run.markdown, encoding="utf-8")

    if run.context.same_repo and run.context.pr.number is not None:
        repository = os.environ.get("GITHUB_REPOSITORY")
        token = os.environ.get("GITHUB_TOKEN")
        if repository and token:
            client = GitHubClient(repository, token)
            client.upsert_issue_comment(
                run.context.pr.number,
                COMMENT_MARKERS["agentic_review"],
                run.markdown,
            )

    print(run.markdown)
    return 1 if run.result.verdict == "NEEDS CHANGES" else 0


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", help="Override the review base ref.")
    parser.add_argument("--head-ref", help="Override the review head ref.")
    parser.add_argument("--pr-number", type=int, help="Optional pull request number.")
    parser.add_argument(
        "--json-out",
        default="artifacts/agentic-review/review.json",
        help="Path for the machine-readable review output.",
    )
    parser.add_argument(
        "--markdown-out",
        default="artifacts/agentic-review/review.md",
        help="Path for the markdown review output.",
    )
    return parser.parse_args()


def _env_int(name: str) -> int | None:
    raw = os.environ.get(name)
    if not raw:
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None

def _resolve_repo_root() -> Path:
    workspace = os.environ.get("GITHUB_WORKSPACE")
    if workspace:
        return Path(workspace).resolve()

    return Path(__file__).resolve().parents[2]

if __name__ == "__main__":
    raise SystemExit(main())