"""Helpers for issue, PR, and repair automation in GitHub workflows."""

from __future__ import annotations

import json
import re
from typing import Iterable


COMMENT_MARKERS = {
    "triage": "agent-triage",
    "entry": "agent-entry",
    "pr_intelligence": "agent-pr-intelligence",
    "failure_summary": "agent-failure-summary",
    "repair": "agent-repair-loop",
}

REPAIR_STATE_MARKER = "agent-repair-loop-state"

DOMAIN_LABELS = ("rules", "cli", "tests", "fixtures", "schemas", "docs", "ci")
ALLOWED_REPAIR_CATEGORIES = {"lint", "unit-test", "cli-smoke", "fixture-schema"}
SENSITIVE_PATH_PREFIXES = (".github/",)
SENSITIVE_PATHS = {
    "OWNERSHIP.md",
    "TEAM_SUMMARY.md",
    "docs/AGENT_POLICY.md",
}

_SECTION_RE = re.compile(r"^###\s+(.+?)\s*$", re.MULTILINE)
_CHECKBOX_RE = re.compile(r"^- \[(?P<checked>[ xX])\] (?P<label>.+?)\s*$")
_STATE_RE_TEMPLATE = r"<!-- {marker} (?P<payload>\{{.*?\}}) -->"


def _normalize_path(value: str) -> str:
    path = value.strip()
    if path.startswith("./"):
        return path[2:]
    return path


def parse_markdown_sections(body: str) -> dict[str, str]:
    """Split a form-style Markdown body into named sections."""

    sections: dict[str, str] = {}
    current_name: str | None = None
    current_lines: list[str] = []

    for line in body.splitlines():
        match = _SECTION_RE.match(line)
        if match:
            if current_name is not None:
                sections[current_name] = "\n".join(current_lines).strip()
            current_name = match.group(1).strip().lower()
            current_lines = []
            continue
        current_lines.append(line)

    if current_name is not None:
        sections[current_name] = "\n".join(current_lines).strip()

    return sections


def section_value(sections: dict[str, str], name: str) -> str:
    """Return one form section with comments stripped."""

    value = sections.get(name.lower(), "")
    cleaned_lines = []
    for line in value.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue
        cleaned_lines.append(stripped)
    return "\n".join(cleaned_lines).strip()


def checked_items(section_text: str) -> tuple[str, ...]:
    """Return the checked options from a Markdown checkbox block."""

    values = []
    for line in section_text.splitlines():
        match = _CHECKBOX_RE.match(line.strip())
        if match and match.group("checked").lower() == "x":
            values.append(match.group("label").strip())
    return tuple(values)


def bullet_items(section_text: str) -> tuple[str, ...]:
    """Normalize freeform textarea content into plain bullet-like items."""

    values = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("<!--"):
            continue
        line = re.sub(r"^[-*]\s+", "", line)
        values.append(line)
    return tuple(values)


def slugify(value: str) -> str:
    """Convert a freeform string to a short branch-safe slug."""

    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug[:48].rstrip("-") or "task"


def build_agent_branch_name(issue_number: int, title: str) -> str:
    """Build the canonical autonomous branch name for one issue."""

    return f"agent/issue-{issue_number}-{slugify(title)}"


def _detect_issue_kind(title: str, labels: Iterable[str], sections: dict[str, str]) -> str:
    title_lower = title.lower()
    labels_lower = {label.lower() for label in labels}

    if title_lower.startswith("[rule ambiguity]:") or "rule ambiguity" in labels_lower:
        return "rule-ambiguity"
    if title_lower.startswith("[bug]:") or "bug" in labels_lower:
        return "bug-report"
    if title_lower.startswith("[agent task]:"):
        return "agent-task"
    if "acceptance criteria" in sections and "required tests" in sections:
        return "agent-task"
    return "unknown"


def _normalize_ambiguity(value: str) -> str:
    lowered = value.lower()
    if "no ambiguity" in lowered:
        return "no ambiguity"
    if "possible ambiguity" in lowered:
        return "possible ambiguity"
    if "high ambiguity" in lowered:
        return "high ambiguity"
    return "unknown"


def _infer_domain_labels_from_areas(areas: Iterable[str], likely_paths: Iterable[str]) -> set[str]:
    domain_labels: set[str] = set()
    haystack = " ".join((*areas, *likely_paths)).lower()

    mapping = {
        "src/blokus": "rules",
        "rules": "rules",
        "tests": "tests",
        "fixtures": "fixtures",
        "schemas": "schemas",
        "docs": "docs",
        "cli": "cli",
        ".github": "ci",
        "ci": "ci",
        "workflow": "ci",
    }
    for needle, label in mapping.items():
        if needle in haystack:
            domain_labels.add(label)

    return domain_labels


def is_sensitive_path(path: str) -> bool:
    """Return whether a path should stop autonomous repair."""

    normalized = _normalize_path(path)
    return normalized.startswith(SENSITIVE_PATH_PREFIXES) or normalized in SENSITIVE_PATHS


def triage_issue(title: str, body: str, labels: Iterable[str]) -> dict[str, object]:
    """Route one issue into the Phase 3 agent workflow states."""

    sections = parse_markdown_sections(body)
    kind = _detect_issue_kind(title, labels, sections)
    ambiguity = _normalize_ambiguity(section_value(sections, "rule ambiguity"))
    areas = checked_items(section_value(sections, "areas affected"))
    likely_paths = bullet_items(section_value(sections, "files likely affected"))
    domain_labels = _infer_domain_labels_from_areas(areas, likely_paths)
    if kind == "rule-ambiguity":
        domain_labels.add("rules")

    if not domain_labels and kind in {"agent-task", "bug-report"}:
        domain_labels.add("rules")

    workflow_sensitive = any(is_sensitive_path(path) for path in likely_paths) or "ci" in domain_labels

    required_sections = {
        "agent-task": ("problem statement", "acceptance criteria", "required tests"),
        "bug-report": ("what broke", "reproduction steps", "expected behavior", "required tests"),
        "rule-ambiguity": ("ambiguity or decision needed", "why this blocks implementation"),
    }.get(kind, ())
    missing_sections = [
        name for name in required_sections if not section_value(sections, name)
    ]

    add_labels = set(domain_labels)
    remove_labels: set[str] = set()
    reasons: list[str] = []

    if kind == "rule-ambiguity":
        state = "needs-human-spec"
        add_labels.update({"needs-human-spec", "human-gate-required"})
        remove_labels.update({"agent-ready", "agent-in-progress", "safe-autonomy"})
        reasons.append("Rule ambiguity issues stay on the human-spec path by design.")
    elif missing_sections:
        state = "needs-human-spec"
        add_labels.update({"needs-human-spec", "human-gate-required"})
        remove_labels.update({"agent-ready", "agent-in-progress", "safe-autonomy"})
        reasons.append(
            "Required form sections are missing: " + ", ".join(missing_sections) + "."
        )
    elif ambiguity != "no ambiguity":
        state = "needs-human-spec"
        add_labels.update({"needs-human-spec", "human-gate-required"})
        remove_labels.update({"agent-ready", "agent-in-progress", "safe-autonomy"})
        reasons.append(f"Rule ambiguity is marked as `{ambiguity}`.")
    else:
        state = "agent-ready"
        add_labels.add("agent-ready")
        remove_labels.update({"needs-human-spec", "agent-blocked"})
        reasons.append("Structured task data is complete and rule ambiguity is low.")

    if workflow_sensitive:
        add_labels.update({"workflow-sensitive", "human-gate-required", "ci"})
        remove_labels.add("safe-autonomy")
        reasons.append("Workflow-sensitive paths mean autonomy must stay human-gated.")
    elif state == "agent-ready":
        add_labels.add("safe-autonomy")

    if kind == "bug-report":
        add_labels.add("bug")

    return {
        "kind": kind,
        "state": state,
        "ambiguity": ambiguity,
        "areas": sorted(areas),
        "likely_paths": sorted(likely_paths),
        "workflow_sensitive": workflow_sensitive,
        "add_labels": sorted(add_labels),
        "remove_labels": sorted(remove_labels),
        "reasons": reasons,
    }


def infer_domains_from_paths(paths: Iterable[str]) -> tuple[str, ...]:
    """Infer the review domains affected by a PR."""

    domains: set[str] = set()
    for path in paths:
        normalized = _normalize_path(path)
        if normalized.startswith("src/"):
            domains.add("rules")
        if normalized in {"src/blokus/cli.py", "src/blokus/__main__.py"}:
            domains.add("cli")
        if normalized.startswith("tests/"):
            domains.add("tests")
        if normalized.startswith("fixtures/"):
            domains.add("fixtures")
        if normalized.startswith("schemas/"):
            domains.add("schemas")
        if normalized.startswith("docs/") or normalized in {
            "README.md",
            "OWNERSHIP.md",
            "TEAM_SUMMARY.md",
        }:
            domains.add("docs")
        if normalized.startswith(".github/") or normalized.startswith("scripts/github/"):
            domains.add("ci")
    return tuple(sorted(domains))


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


def classify_failure_category(job_names: Iterable[str]) -> str:
    """Map failing CI job names into the Phase 3 repair categories."""

    names = [name.lower() for name in job_names]
    if any("lint" in name for name in names):
        return "lint"
    if any("cli-smoke" in name or "cli smoke" in name for name in names):
        return "cli-smoke"
    if any("fixture-schema" in name or ("fixture" in name and "schema" in name) for name in names):
        return "fixture-schema"
    if any(name == "test" or "unit" in name or "tests" in name for name in names):
        return "unit-test"
    if any("evaluate" in name for name in names):
        return "evaluate"
    if any("environment" in name or "deployment" in name for name in names):
        return "environment"
    return "unknown"


def repair_allowed(
    branch_name: str,
    labels: Iterable[str],
    category: str,
    changed_files: Iterable[str],
    retry_count: int,
) -> tuple[bool, str]:
    """Return whether bounded autonomous repair is allowed."""

    label_set = {label.lower() for label in labels}
    if not branch_name.startswith("agent/"):
        return False, "Branch is not agent-owned (`agent/*`)."
    if retry_count >= 2:
        return False, "Retry budget exhausted."
    if category not in ALLOWED_REPAIR_CATEGORIES:
        return False, f"Failure category `{category}` is outside the autonomous repair set."
    if "needs-human-spec" in label_set:
        return False, "Issue still needs human clarification."
    if "workflow-sensitive" in label_set or "human-gate-required" in label_set:
        return False, "Human-gated work cannot enter the repair loop."
    if any(is_sensitive_path(path) for path in changed_files):
        return False, "Sensitive repository automation files changed in this PR."
    return True, "Autonomous repair is allowed."


def render_state_marker(marker: str, payload: dict[str, object]) -> str:
    """Embed machine-readable state inside a bot comment."""

    return f"<!-- {marker} {json.dumps(payload, sort_keys=True)} -->"


def parse_state_marker(marker: str, body: str) -> dict[str, object] | None:
    """Extract one machine-readable state payload from a bot comment."""

    pattern = re.compile(_STATE_RE_TEMPLATE.format(marker=re.escape(marker)), re.DOTALL)
    match = pattern.search(body)
    if not match:
        return None
    return json.loads(match.group("payload"))
