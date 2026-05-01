#!/usr/bin/env python3
"""Run agentic pull-request review and publish its artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Callable
    from typing import Type

    from blokus.review.config import load_review_config as _load_review_config  # noqa: F401
    from blokus.review.coordinator import ReviewCoordinator as _ReviewCoordinator  # noqa: F401
    from scripts.github.gh_helpers import (  # noqa: F401
        GitHubClient as _GitHubClient,
        load_event_payload as _load_event_payload,
    )

# Module-level placeholders for lazy imports (required for test patching)
load_review_config: "Callable[..., Any] | None" = None
ReviewCoordinator: "Type[Any] | None" = None
GitHubClient: "Type[Any] | None" = None
load_event_payload: "Callable[..., Any] | None" = None
COMMENT_MARKERS: "dict[str, str] | None" = None


def main() -> int:
    """Main entry point - sets up import path and runs review."""
    # Lazy-load dependencies to avoid import-time side effects
    _lazy_imports()

    # Asserts inform mypy that lazy imports have been initialized
    assert load_review_config is not None
    assert ReviewCoordinator is not None
    assert GitHubClient is not None
    assert load_event_payload is not None
    assert COMMENT_MARKERS is not None

    args = _parse_args()
    repo_root = _resolve_repo_root()
    config = load_review_config(repo_root=repo_root)
    coordinator = ReviewCoordinator(config)

    event_payload = _load_event_payload_if_available()

    run = coordinator.run(
        event_payload=event_payload,
        base_ref=args.base_ref if args.base_ref is not None else os.environ.get("REVIEW_BASE_REF"),
        head_ref=args.head_ref if args.head_ref is not None else os.environ.get("REVIEW_HEAD_REF"),
        pr_number=args.pr_number if args.pr_number is not None else _env_int("REVIEW_PULL_NUMBER"),
    )

    json_path = _resolve_output_path(repo_root, args.json_out)
    markdown_path = _resolve_output_path(repo_root, args.markdown_out)
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
    return 0 if run.result.verdict == "LGTM" else 1


def _lazy_imports() -> None:
    """Lazy-load dependencies at runtime to avoid import-time side effects.

    This allows tests to patch module-level attributes before main() runs.
    """
    global load_review_config, ReviewCoordinator, GitHubClient, load_event_payload, COMMENT_MARKERS

    _setup_import_path()

    if load_review_config is None:
        import blokus.review.config as rc

        load_review_config = rc.load_review_config

    if ReviewCoordinator is None:
        import blokus.review.coordinator as rco

        ReviewCoordinator = rco.ReviewCoordinator

    if GitHubClient is None or load_event_payload is None:
        import scripts.github.gh_helpers as gh

        if GitHubClient is None:
            GitHubClient = gh.GitHubClient
        if load_event_payload is None:
            load_event_payload = gh.load_event_payload

    if COMMENT_MARKERS is None:
        import blokus.automation as auto

        COMMENT_MARKERS = auto.COMMENT_MARKERS


def _setup_import_path() -> None:
    """Add repository paths to sys.path for imports.

    This is called from _lazy_imports() to avoid side effects at import time.
    """
    repo_root = Path(__file__).resolve().parents[2]
    src_root = repo_root / "src"
    for import_root in (str(src_root), str(repo_root)):
        if import_root not in sys.path:
            sys.path.insert(0, import_root)


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


def _load_event_payload_if_available() -> dict[str, object] | None:
    assert load_event_payload is not None

    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None

    path = Path(event_path)
    if not path.is_file():
        return None

    try:
        return load_event_payload(event_path)
    except (OSError, ValueError) as exc:
        print(
            f"Warning: failed to load GitHub event payload from `{event_path}`: {exc}",
            file=sys.stderr,
        )
        return None


def _resolve_repo_root() -> Path:
    workspace = os.environ.get("GITHUB_WORKSPACE")
    if workspace:
        return Path(workspace).resolve()

    return Path(__file__).resolve().parents[2]


def _resolve_output_path(repo_root: Path, raw_path: str) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return (repo_root / path).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
