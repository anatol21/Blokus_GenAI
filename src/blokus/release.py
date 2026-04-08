"""Release automation helpers."""

from __future__ import annotations

import re
from typing import Iterable


_RC_TAG_PATTERN = re.compile(r"^v(?P<version>\d+\.\d+\.\d+)-rc\.(?P<index>\d+)$")


def next_rc_tag(version: str, existing_tags: Iterable[str]) -> str:
    """Return the next monotonically increasing RC tag for one version."""

    highest = 0
    for tag in existing_tags:
        match = _RC_TAG_PATTERN.match(tag.strip())
        if match and match.group("version") == version:
            highest = max(highest, int(match.group("index")))
    return f"v{version}-rc.{highest + 1}"


def final_tag_from_rc(rc_tag: str) -> str:
    """Return the default final tag derived from an RC tag."""

    match = _RC_TAG_PATTERN.match(rc_tag.strip())
    if not match:
        return rc_tag.strip()
    return f"v{match.group('version')}"


def classify_release_areas(paths: Iterable[str]) -> tuple[str, ...]:
    """Classify changed files into review-friendly release areas."""

    areas: set[str] = set()
    for raw_path in paths:
        path = raw_path.strip()
        if not path:
            continue
        if path.startswith("src/"):
            areas.add("source")
        if path.startswith("tests/"):
            areas.add("tests")
        if path.startswith("fixtures/"):
            areas.add("fixtures")
        if path.startswith("schemas/"):
            areas.add("schemas")
        if path.startswith("docs/") or path in {"README.md", "OWNERSHIP.md", "TEAM_SUMMARY.md"}:
            areas.add("docs")
        if path.startswith(".github/") or path.startswith("scripts/github/"):
            areas.add("ci")
        if path.startswith("scripts/") and not path.startswith("scripts/github/"):
            areas.add("scripts")
    return tuple(sorted(areas))


def extract_bullets_under_heading(markdown: str, heading: str) -> tuple[str, ...]:
    """Extract the bullet list under one Markdown heading."""

    target = heading.strip().lower()
    current_heading: str | None = None
    bullets: list[str] = []

    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            current_heading = stripped.lstrip("#").strip().lower()
            continue
        if current_heading != target:
            continue
        if not stripped:
            continue
        if stripped.startswith("- "):
            bullets.append(stripped[2:].strip())
            continue
        if bullets and stripped.startswith("#"):
            break
    return tuple(bullets)
