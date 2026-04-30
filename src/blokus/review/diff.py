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
    raw_diff = "\n\n".join(
        _render_patch_block(changed_file) for changed_file in included_files if changed_file.patch
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
        raw_diff=raw_diff,
    )


def should_run_performance_review(config: ReviewConfig, context: ReviewContext) -> bool:
    """Return whether the performance specialist should run."""

    path_markers = config.performance.path_markers
    diff_markers = config.performance.diff_markers

    for changed_file in context.executable_files:
        if any(marker in changed_file.path for marker in path_markers):
            return True
        if any(marker in changed_file.patch for marker in diff_markers):
            return True
    return False


def _resolve_refs(
    event_payload: dict[str, object] | None,
    base_ref: str | None,
    head_ref: str | None,
    pr_number: int | None,
) -> tuple[str, str, int | None, bool]:
    if event_payload and "pull_request" in event_payload:
        pull_request = event_payload["pull_request"]
        base_value = str(pull_request["base"]["sha"])
        head_value = str(pull_request["head"]["sha"])
        same_repo = pull_request["head"]["repo"]["full_name"] == pull_request["base"]["repo"]["full_name"]
        return base_value, head_value, int(pull_request["number"]), bool(same_repo)

    resolved_base = base_ref or "origin/main"
    resolved_head = head_ref or "HEAD"
    return resolved_base, resolved_head, pr_number, True


def _load_changed_files(config: ReviewConfig, base_ref: str, head_ref: str) -> tuple[ChangedFile, ...]:
    diff_ref = f"{base_ref}...{head_ref}"
    name_status_lines = _git_lines(config.repo_root, ["diff", "--name-status", diff_ref])
    changed_files: list[ChangedFile] = []

    for line in name_status_lines:
        if not line.strip():
            continue
        parts = line.split("\t")
        status = parts[0]
        old_path = parts[1] if status.startswith(("R", "C")) and len(parts) > 2 else None
        path = parts[-1]
        patch = _git_output(config.repo_root, ["diff", "--unified=3", diff_ref, "--", path])
        zero_context_patch = _git_output(config.repo_root, ["diff", "--unified=0", diff_ref, "--", path])
        changed_files.append(
            ChangedFile(
                path=path,
                status=status,
                patch=patch,
                line_spans=tuple(_parse_line_spans(zero_context_patch)),
                executable=_is_executable_path(path),
                categories=tuple(_categorize_path(path)),
                old_path=old_path,
            )
        )

    return tuple(changed_files)


def _current_branch(repo_root: Path) -> str:
    branch = _git_output(repo_root, ["branch", "--show-current"]).strip()
    return branch or "HEAD"


def _parse_line_spans(patch_text: str) -> list[LineSpan]:
    spans: list[LineSpan] = []
    for raw_line in patch_text.splitlines():
        match = _HUNK_RE.match(raw_line)
        if not match:
            continue
        start = int(match.group("start"))
        count = int(match.group("count") or "1")
        if count == 0:
            continue
        spans.append(LineSpan(start=start, end=start + count - 1))
    return spans


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
