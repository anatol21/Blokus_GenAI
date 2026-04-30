"""Git diff loading and review-context construction."""

from __future__ import annotations

import fnmatch
import re
import subprocess
from pathlib import Path

from blokus.review.config import ReviewConfig
from blokus.review.types import ChangedFile, LineSpan, ReviewContext, ReviewPayload


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")
_SELF_DECLARED_RE = re.compile(r"\b(fix(?:ed)?|safe|tested|optimized?|performance|refactor)\b", re.IGNORECASE)
MAX_STORED_PATCH_CHARS = 16_000
_PATCH_TRUNCATION_MARKER = "\n... [diff context truncated for scale]\n"


def build_review_context(
    config: ReviewConfig,
    *,
    event_payload: dict[str, object] | None = None,
    base_ref: str | None = None,
    head_ref: str | None = None,
    pr_number: int | None = None,
) -> ReviewContext:
    """Collect diff-backed review context for one review run."""

    base_value, head_value, number, same_repo = _resolve_refs(event_payload, base_ref, head_ref, pr_number)
    base_sha = _git_output(config.repo_root, ["rev-parse", base_value]).strip()
    head_sha = _git_output(config.repo_root, ["rev-parse", head_value]).strip()
    branch_name = _current_branch(config.repo_root)
    commits = _git_lines(config.repo_root, ["log", "--format=%s", f"{base_sha}..{head_sha}"])
    changed_files = _load_changed_files(config, base_sha, head_sha)
    included_files = tuple(
        changed_file for changed_file in changed_files if not _is_excluded(config, changed_file.path)
    )
    executable_files = tuple(
        changed_file for changed_file in included_files if changed_file.executable
    )
    return ReviewContext(
        pr=ReviewPayload(number=number, head_sha=head_sha, base_sha=base_sha),
        base_ref=base_value,
        head_ref=head_value,
        branch_name=branch_name,
        commits=tuple(commits),
        changed_files=included_files,
        impact=_classify_impact(included_files),
        bias_risks=_infer_bias_risks(branch_name, commits),
        same_repo=same_repo,
        executable_files=executable_files,
        raw_diff="",
    )


def should_run_performance_review(config: ReviewConfig, context: ReviewContext) -> bool:
    """Return whether the performance specialist should run."""

    del config
    return any(changed_file.performance_sensitive for changed_file in context.executable_files)


def _resolve_refs(
    event_payload: dict[str, object] | None,
    base_ref: str | None,
    head_ref: str | None,
    pr_number: int | None,
) -> tuple[str, str, int | None, bool]:
    resolved_base = base_ref or "origin/main"
    resolved_head = head_ref or "HEAD"
    if event_payload and "pull_request" in event_payload:
        pull_request = event_payload.get("pull_request")
        if isinstance(pull_request, dict):
            base_value = _nested_sha(pull_request.get("base"))
            head_value = _nested_sha(pull_request.get("head"))
            if base_value and head_value:
                same_repo = _same_repo(pull_request.get("base"), pull_request.get("head"))
                return (
                    base_value,
                    head_value,
                    _optional_int(pull_request.get("number"), pr_number),
                    same_repo,
                )

    return resolved_base, resolved_head, pr_number, True


def _load_changed_files(config: ReviewConfig, base_ref: str, head_ref: str) -> tuple[ChangedFile, ...]:
    diff_ref = f"{base_ref}...{head_ref}"
    name_status_lines = _git_lines(config.repo_root, ["diff", "--name-status", diff_ref])
    full_patch_by_path = _split_patch_by_path(_git_output(config.repo_root, ["diff", "--unified=3", diff_ref]))
    changed_files: list[ChangedFile] = []

    for line in name_status_lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        old_path = parts[1] if status.startswith(("R", "C")) and len(parts) > 2 else None
        path = parts[-1]
        full_patch = full_patch_by_path.get(path, "")
        line_spans = tuple(_parse_line_spans(full_patch))
        performance_sensitive = _is_performance_sensitive(config, path, full_patch)
        patch, patch_truncated = _truncate_patch_for_storage(full_patch)
        changed_files.append(
            ChangedFile(
                path=path,
                status=status,
                patch=patch,
                line_spans=line_spans,
                executable=_is_executable_path(path),
                categories=tuple(_categorize_path(path)),
                old_path=old_path,
                performance_sensitive=performance_sensitive,
                patch_truncated=patch_truncated,
            )
        )

    return tuple(changed_files)


def _current_branch(repo_root: Path) -> str:
    branch = _git_output(repo_root, ["branch", "--show-current"]).strip()
    return branch or "HEAD"


def _parse_line_spans(patch_text: str) -> list[LineSpan]:
    spans: list[LineSpan] = []
    current_line: int | None = None
    span_start: int | None = None
    deletion_anchor: int | None = None

    def flush_current_hunk() -> None:
        nonlocal span_start, deletion_anchor
        if span_start is not None and current_line is not None:
            spans.append(LineSpan(start=span_start, end=current_line - 1))
        elif deletion_anchor is not None:
            anchor_line = max(1, deletion_anchor)
            spans.append(LineSpan(start=anchor_line, end=anchor_line))
        span_start = None
        deletion_anchor = None

    for raw_line in patch_text.splitlines():
        if raw_line.startswith("diff --git "):
            if current_line is not None:
                flush_current_hunk()
            current_line = None
            continue

        match = _HUNK_RE.match(raw_line)
        if match:
            if current_line is not None:
                flush_current_hunk()
            current_line = int(match.group("start"))
            deletion_anchor = current_line if int(match.group("count") or "1") == 0 else None
            continue

        if current_line is None or raw_line.startswith(("--- ", "+++ ")):
            continue

        if raw_line.startswith("+"):
            if span_start is None:
                span_start = current_line
            current_line += 1
            deletion_anchor = None
            continue

        if raw_line.startswith("-") or raw_line.startswith("\\"):
            continue

        if span_start is not None:
            flush_current_hunk()
        else:
            deletion_anchor = None
        current_line += 1

    if current_line is not None:
        flush_current_hunk()
    return spans


def _split_patch_by_path(patch_text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    current_lines: list[str] = []

    for line in patch_text.splitlines():
        if line.startswith("diff --git "):
            _store_patch_block(blocks, current_lines)
            current_lines = [line]
            continue
        if current_lines:
            current_lines.append(line)

    _store_patch_block(blocks, current_lines)
    return blocks


def _store_patch_block(blocks: dict[str, str], lines: list[str]) -> None:
    if not lines:
        return

    old_path: str | None = None
    new_path: str | None = None
    for line in lines:
        if line.startswith("--- "):
            old_path = _normalize_patch_path(line[4:])
        elif line.startswith("+++ "):
            new_path = _normalize_patch_path(line[4:])

    path = new_path if new_path and new_path != "/dev/null" else old_path
    if path is None:
        return
    blocks[path] = "\n".join(lines)


def _normalize_patch_path(raw_path: str) -> str:
    stripped = raw_path.strip()
    if stripped in {"/dev/null", "dev/null"}:
        return "/dev/null"
    if stripped.startswith(("a/", "b/")):
        stripped = stripped[2:]
    return stripped.strip('"')


def _nested_sha(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    sha = value.get("sha")
    return str(sha) if sha else None


def _same_repo(base_value: object, head_value: object) -> bool:
    base_full_name = _nested_full_name(base_value)
    head_full_name = _nested_full_name(head_value)
    if not base_full_name or not head_full_name:
        return True
    return head_full_name == base_full_name


def _nested_full_name(value: object) -> str | None:
    if not isinstance(value, dict):
        return None
    repo = value.get("repo")
    if not isinstance(repo, dict):
        return None
    full_name = repo.get("full_name")
    return str(full_name) if full_name else None


def _optional_int(value: object, default: int | None) -> int | None:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return default


def _is_performance_sensitive(config: ReviewConfig, path: str, patch: str) -> bool:
    if any(marker in path for marker in config.performance.path_markers):
        return True
    return any(marker in patch for marker in config.performance.diff_markers)


def _truncate_patch_for_storage(patch: str) -> tuple[str, bool]:
    if len(patch) <= MAX_STORED_PATCH_CHARS:
        return patch, False
    available = max(0, MAX_STORED_PATCH_CHARS - len(_PATCH_TRUNCATION_MARKER))
    trimmed = patch[:available].rstrip("\n")
    return f"{trimmed}{_PATCH_TRUNCATION_MARKER}", True


def _classify_impact(changed_files: tuple[ChangedFile, ...]) -> str:
    if not changed_files:
        return "low"

    changed_paths = {changed_file.path for changed_file in changed_files}
    critical_markers = {
        "src/blokus/engine.py",
        "src/blokus/models.py",
    }
    if changed_paths & critical_markers and any(path.startswith(".github/") for path in changed_paths):
        return "critical"
    if changed_paths & critical_markers or any(path.startswith(".github/") for path in changed_paths):
        return "high"
    if any(
        path.startswith(prefix)
        for path in changed_paths
        for prefix in ("src/", "scripts/github/", "schemas/", "fixtures/", "tests/")
    ):
        return "moderate"
    return "low"


def _infer_bias_risks(branch_name: str, commits: list[str]) -> tuple[str, ...]:
    risks = [
        "authority-bias",
        "reverse-authority-bias",
        "misleading-task-bias",
        "illusory-complexity-bias",
        "variable-change-bias",
    ]
    weak_context = " ".join([branch_name, *commits])
    if _SELF_DECLARED_RE.search(weak_context):
        risks.insert(0, "self-declared-correctness-bias")
    else:
        risks.append("self-declared-correctness-bias")
    return tuple(dict.fromkeys(risks))


def _categorize_path(path: str) -> list[str]:
    categories: list[str] = []
    if path.endswith(".py"):
        categories.append("python")
    if path.endswith(".sh"):
        categories.append("shell")
    if path.startswith(".github/workflows/"):
        categories.append("workflow")
    if path.startswith("schemas/"):
        categories.append("schema")
    if path.startswith("fixtures/"):
        categories.append("fixture")
    if path.startswith("tests/"):
        categories.append("test")
    if path.startswith("docs/") or path.endswith(".md"):
        categories.append("docs")
    return categories


def _is_executable_path(path: str) -> bool:
    return path.endswith(".py") or path.endswith(".sh")


def _is_excluded(config: ReviewConfig, path: str) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in config.excluded_globs)


def _git_output(repo_root: Path, args: list[str]) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout


def _git_lines(repo_root: Path, args: list[str]) -> list[str]:
    output = _git_output(repo_root, args)
    return [line for line in output.splitlines() if line.strip()]


def _render_patch_block(changed_file: ChangedFile) -> str:
    return f"File: {changed_file.path}\n```diff\n{changed_file.patch.strip()}\n```"
