"""Minimal automation helpers shared by agentic review scripts."""

from __future__ import annotations

from typing import Iterable


COMMENT_MARKERS = {
    "agentic_review": "agentic-code-review",
}

SENSITIVE_PATH_PREFIXES = (".github/",)
SENSITIVE_PATHS = {
    "OWNERSHIP.md",
    "TEAM_SUMMARY.md",
    "docs/AGENT_POLICY.md",
    "docs/INCIDENT_RESPONSE.md",
    "docs/PIPELINE_SECURITY.md",
}


def _normalize_path(value: str) -> str:
    path = value.strip()
    if path.startswith("./"):
        return path[2:]
    return path


def is_sensitive_path(path: str) -> bool:
    """Return whether a path should be treated as workflow-sensitive."""

    normalized = _normalize_path(path)
    return normalized.startswith(SENSITIVE_PATH_PREFIXES) or normalized in SENSITIVE_PATHS


def tests_missing(paths: Iterable[str]) -> bool:
    """Return whether code-bearing changes land without matching test updates."""

    normalized = [_normalize_path(path) for path in paths]
    code_touched = any(
        path.startswith(prefix)
        for path in normalized
        for prefix in ("src/", "fixtures/", "schemas/")
    )
    tests_touched = any(path.startswith("tests/") for path in normalized)
    return code_touched and not tests_touched
