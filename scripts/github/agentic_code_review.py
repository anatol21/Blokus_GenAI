#!/usr/bin/env python3
"""Run agentic pull-request review and publish its artifacts."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import TYPE_CHECKING, Any, cast

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

    (
        load_review_config_fn,
        coordinator_cls,
        github_client_cls,
        load_event_payload_fn,
        comment_markers,
    ) = _initialized_lazy_imports()

    args = _parse_args()
    repo_root = _resolve_repo_root()
    config = load_review_config_fn(repo_root=repo_root)
    coordinator = coordinator_cls(config)

    event_payload = _load_event_payload_if_available(load_event_payload_fn)

    run = coordinator.run(
        event_payload=event_payload,
        base_ref=_resolved_ref_value(args.base_ref, "REVIEW_BASE_REF"),
        head_ref=_resolved_ref_value(args.head_ref, "REVIEW_HEAD_REF"),
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
            client = github_client_cls(repository, token)
            client.upsert_issue_comment(
                run.context.pr.number,
                comment_markers["agentic_review"],
                run.markdown,
            )

    print(run.markdown)
    return 1 if run.result.verdict == "NEEDS CHANGES" else 0


def _lazy_imports() -> None:
    """Lazy-load dependencies at runtime to avoid import-time side effects.

    This allows tests to patch module-level attributes before main() runs.
    """
    global load_review_config, ReviewCoordinator, GitHubClient, load_event_payload, COMMENT_MARKERS

    _setup_import_path(_resolve_repo_root())

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


def _initialized_lazy_imports() -> tuple[
    "Callable[..., Any]",
    "Type[Any]",
    "Type[Any]",
    "Callable[..., Any]",
    dict[str, str],
]:
    missing: list[str] = []
    if load_review_config is None:
        missing.append("load_review_config")
    if ReviewCoordinator is None:
        missing.append("ReviewCoordinator")
    if GitHubClient is None:
        missing.append("GitHubClient")
    if load_event_payload is None:
        missing.append("load_event_payload")
    if COMMENT_MARKERS is None:
        missing.append("COMMENT_MARKERS")
    if missing:
        missing_list = ", ".join(missing)
        raise RuntimeError(f"Lazy imports were not initialized: {missing_list}.")

    return (
        cast("Callable[..., Any]", load_review_config),
        cast("Type[Any]", ReviewCoordinator),
        cast("Type[Any]", GitHubClient),
        cast("Callable[..., Any]", load_event_payload),
        cast(dict[str, str], COMMENT_MARKERS),
    )


def _setup_import_path(repo_root: Path) -> None:
    """Add repository paths to sys.path for imports.

    This is called from _lazy_imports() to avoid side effects at import time.
    """
    src_root = repo_root / "src"
    desired_prefix = [str(src_root), str(repo_root)]
    for import_root in desired_prefix:
        while import_root in sys.path:
            sys.path.remove(import_root)
    sys.path[:0] = desired_prefix


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


def _resolved_ref_value(cli_value: str | None, env_name: str) -> str | None:
    if cli_value is not None:
        return _normalized_ref_value(cli_value)
    return _normalized_ref_value(os.environ.get(env_name))


def _normalized_ref_value(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _load_event_payload_if_available(
    load_event_payload_fn: "Callable[..., Any]",
) -> dict[str, object] | None:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return None

    path = Path(event_path)
    if not path.is_file():
        return None

    try:
        payload = load_event_payload_fn(event_path)
    except (OSError, ValueError) as exc:
        print(
            f"Warning: failed to load GitHub event payload from `{event_path}`: {exc}",
            file=sys.stderr,
        )
        return None
    if not isinstance(payload, dict):
        print(
            f"Warning: GitHub event payload at `{event_path}` did not contain a JSON object.",
            file=sys.stderr,
        )
        return None
    return payload


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
