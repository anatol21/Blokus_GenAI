"""Git diff loading and review-context construction."""

from __future__ import annotations

from dataclasses import dataclass, field
import fnmatch
from functools import lru_cache
import re
import subprocess
import threading
from pathlib import Path
from typing import Iterator

from blokus.review.config import ReviewConfig
from blokus.review.types import ChangedFile, LineSpan, ReviewContext, ReviewPayload


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(?P<start>\d+)(?:,(?P<count>\d+))? @@")
_SELF_DECLARED_RE = re.compile(r"\b(fix(?:ed)?|safe|tested|optimized?|performance|refactor)\b", re.IGNORECASE)
MAX_STORED_PATCH_CHARS = 16_000
MAX_ANALYZED_PATCH_LINES = 50_000
MAX_ANALYZED_PATCH_CHARS = 2_000_000
MAX_REVIEW_CONTEXT_COMMITS = 25
_PATCH_TRUNCATION_MARKER = "\n... [diff context truncated for scale]\n"


@dataclass(frozen=True)
class _PatchBlock:
    path: str
    status: str
    patch: str
    line_spans: tuple[LineSpan, ...]
    old_path: str | None
    performance_sensitive: bool
    patch_truncated: bool
    analysis_truncated: bool = False


@dataclass
class _LineSpanTracker:
    spans: list[LineSpan] = field(default_factory=list)
    current_line: int | None = None
    span_start: int | None = None
    deletion_anchor: int | None = None

    def feed(self, raw_line: str) -> None:
        if raw_line.startswith("diff --git "):
            if self.current_line is not None:
                self._flush_current_hunk()
            self.current_line = None
            return

        match = _HUNK_RE.match(raw_line)
        if match:
            if self.current_line is not None:
                self._flush_current_hunk()
            self.current_line = int(match.group("start"))
            self.deletion_anchor = self.current_line if int(match.group("count") or "1") == 0 else None
            return

        if self.current_line is None or raw_line.startswith(("--- ", "+++ ")):
            return

        if raw_line.startswith("+"):
            if self.span_start is None:
                self.span_start = self.current_line
            self.current_line += 1
            self.deletion_anchor = None
            return

        if raw_line.startswith("-") or raw_line.startswith("\\"):
            return

        if self.span_start is not None:
            self._flush_current_hunk()
        elif self.deletion_anchor is not None:
            self._flush_current_hunk()
        else:
            self.deletion_anchor = None
        self.current_line += 1

    def finish(self) -> tuple[LineSpan, ...]:
        if self.current_line is not None:
            self._flush_current_hunk()
        return tuple(self.spans)

    def _flush_current_hunk(self) -> None:
        if self.span_start is not None and self.current_line is not None:
            self.spans.append(LineSpan(start=self.span_start, end=self.current_line - 1))
        elif self.deletion_anchor is not None:
            anchor_line = max(1, self.deletion_anchor)
            self.spans.append(LineSpan(start=anchor_line, end=anchor_line))
        self.span_start = None
        self.deletion_anchor = None


@dataclass
class _PatchAccumulator:
    config: ReviewConfig
    tracker: _LineSpanTracker = field(default_factory=_LineSpanTracker)
    status: str = "M"
    old_path: str | None = None
    new_path: str | None = None
    stored_parts: list[str] = field(default_factory=list)
    stored_chars: int = 0
    patch_truncated: bool = False
    performance_sensitive: bool = False
    analyzed_lines: int = 0
    analyzed_chars: int = 0
    analysis_truncated: bool = False
    _path_markers_checked: bool = field(default=False, repr=False)
    _diff_marker_pattern: re.Pattern[str] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        # Pre-compile the diff marker regex once
        self._diff_marker_pattern = _diff_marker_pattern(self.config.performance.diff_markers)

    def add_line(self, line: str) -> None:
        self._track_paths(line)
        self.tracker.feed(line)
        if not self.analysis_truncated:
            if self._would_exceed_analysis_limit(line):
                self.analysis_truncated = True
            else:
                self._track_performance(line)
                self.analyzed_lines += 1
                self.analyzed_chars += len(line) + 1
        self._append_bounded(line)

    def build(self) -> _PatchBlock | None:
        path = self.new_path if self.new_path and self.new_path != "/dev/null" else self.old_path
        if path is None:
            return None

        patch = "".join(self.stored_parts)
        if self.patch_truncated:
            patch = f"{patch.rstrip()}{_PATCH_TRUNCATION_MARKER}"

        return _PatchBlock(
            path=path,
            status=self.status,
            patch=patch,
            line_spans=self.tracker.finish(),
            old_path=self.old_path if self.old_path != path else None,
            performance_sensitive=self.performance_sensitive,
            patch_truncated=self.patch_truncated,
            analysis_truncated=self.analysis_truncated,
        )

    def _track_paths(self, line: str) -> None:
        if line.startswith("diff --git "):
            old_path, new_path = _parse_diff_header_paths(line)
            if old_path is not None:
                self.old_path = old_path
            if new_path is not None:
                self.new_path = new_path
        elif line.startswith("--- "):
            self.old_path = _normalize_patch_path(line[4:])
        elif line.startswith("+++ "):
            self.new_path = _normalize_patch_path(line[4:])
        elif line.startswith("rename from "):
            self.status = "R"
            self.old_path = _normalize_patch_path(line[len("rename from ") :])
        elif line.startswith("rename to "):
            self.status = "R"
            self.new_path = _normalize_patch_path(line[len("rename to ") :])
        elif line.startswith("copy from "):
            self.status = "C"
            self.old_path = _normalize_patch_path(line[len("copy from ") :])
        elif line.startswith("copy to "):
            self.status = "C"
            self.new_path = _normalize_patch_path(line[len("copy to ") :])
        elif line.startswith("new file mode "):
            self.status = "A"
        elif line.startswith("deleted file mode "):
            self.status = "D"

    def _track_performance(self, line: str) -> None:
        if self.performance_sensitive:
            return
        # Check diff markers using pre-compiled pattern
        if self._diff_marker_pattern is not None and self._diff_marker_pattern.search(line):
            self.performance_sensitive = True
            return
        # Check path markers once when path is known
        if not self._path_markers_checked:
            path = self.new_path or self.old_path
            if path and any(marker in path for marker in self.config.performance.path_markers):
                self.performance_sensitive = True
            self._path_markers_checked = True

    def _append_bounded(self, line: str) -> None:
        if self.patch_truncated:
            return

        available = max(0, MAX_STORED_PATCH_CHARS - len(_PATCH_TRUNCATION_MARKER))
        piece = line if not self.stored_parts else f"\n{line}"
        remaining = available - self.stored_chars
        if remaining <= 0:
            self.patch_truncated = True
            return

        if len(piece) <= remaining:
            self.stored_parts.append(piece)
            self.stored_chars += len(piece)
            return

        self.stored_parts.append(piece[:remaining])
        self.stored_chars += remaining
        self.patch_truncated = True

    def _would_exceed_analysis_limit(self, line: str) -> bool:
        return (
            self.analyzed_lines >= MAX_ANALYZED_PATCH_LINES
            or self.analyzed_chars + len(line) + 1 > MAX_ANALYZED_PATCH_CHARS
        )


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
    commits = _git_lines(
        config.repo_root,
        ["log", f"-n{MAX_REVIEW_CONTEXT_COMMITS + 1}", "--format=%s", f"{base_sha}..{head_sha}"],
    )
    commit_context_truncated = len(commits) > MAX_REVIEW_CONTEXT_COMMITS
    changed_files = _load_changed_files(config, base_sha, head_sha)
    included_files = tuple(
        changed_file for changed_file in changed_files if not _is_excluded(config, changed_file.path)
    )
    executable_files = tuple(changed_file for changed_file in included_files if changed_file.executable)

    return ReviewContext(
        pr=ReviewPayload(number=number, head_sha=head_sha, base_sha=base_sha),
        base_ref=base_value,
        head_ref=head_value,
        branch_name=branch_name,
        commits=tuple(commits[:MAX_REVIEW_CONTEXT_COMMITS]),
        changed_files=included_files,
        impact=_classify_impact(included_files),
        bias_risks=_infer_bias_risks(branch_name, commits),
        same_repo=same_repo,
        commit_context_truncated=commit_context_truncated,
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
    changed_files: list[ChangedFile] = []

    for patch_block in _iter_git_patch_blocks(config, config.repo_root, ["diff", "--unified=3", diff_ref]):
        changed_files.append(
            ChangedFile(
                path=patch_block.path,
                status=patch_block.status,
                patch=patch_block.patch,
                line_spans=patch_block.line_spans,
                executable=_is_executable_path(patch_block.path),
                categories=tuple(_categorize_path(patch_block.path)),
                old_path=patch_block.old_path,
                performance_sensitive=patch_block.performance_sensitive,
                patch_truncated=patch_block.patch_truncated,
                analysis_truncated=patch_block.analysis_truncated,
            )
        )

    return tuple(changed_files)


def _current_branch(repo_root: Path) -> str:
    branch = _git_output(repo_root, ["branch", "--show-current"]).strip()
    return branch or "HEAD"


def _parse_line_spans(patch_text: str) -> list[LineSpan]:
    tracker = _LineSpanTracker()
    for raw_line in patch_text.splitlines():
        tracker.feed(raw_line)
    return list(tracker.finish())


def _iter_git_patch_blocks(
    config: ReviewConfig,
    repo_root: Path,
    args: list[str],
) -> Iterator[_PatchBlock]:
    process = subprocess.Popen(
        ["git", *args],
        cwd=repo_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    assert process.stdout is not None
    assert process.stderr is not None
    stdout = process.stdout
    stderr_pipe = process.stderr
    stderr_chunks: list[str] = []

    def read_stderr() -> None:
        stderr_chunks.append(stderr_pipe.read())

    stderr_reader = threading.Thread(target=read_stderr, daemon=True)
    stderr_reader.start()
    current_patch: _PatchAccumulator | None = None

    try:
        for raw_line in stdout:
            line = raw_line.rstrip("\n")
            if line.startswith("diff --git "):
                block = current_patch.build() if current_patch is not None else None
                if block is not None:
                    yield block
                current_patch = _PatchAccumulator(config)

            if current_patch is not None:
                current_patch.add_line(line)

        block = current_patch.build() if current_patch is not None else None
        if block is not None:
            yield block
    finally:
        stdout.close()
        stderr_reader.join()
        stderr = "".join(stderr_chunks)
        stderr_pipe.close()
        returncode = process.wait()
        if returncode != 0:
            raise subprocess.CalledProcessError(
                returncode,
                ["git", *args],
                stderr=stderr,
            )


def _normalize_patch_path(raw_path: str) -> str:
    stripped = raw_path.strip()
    if stripped in {"/dev/null", "dev/null"}:
        return "/dev/null"
    if stripped.startswith(("a/", "b/")):
        stripped = stripped[2:]
    return stripped.strip('"')


def _parse_diff_header_paths(line: str) -> tuple[str | None, str | None]:
    parts = line.split(maxsplit=3)
    if len(parts) < 4:
        return None, None
    old_path, new_path = parts[2], parts[3]
    return _normalize_patch_path(old_path), _normalize_patch_path(new_path)


@lru_cache(maxsize=None)
def _diff_marker_pattern(markers: tuple[str, ...]) -> re.Pattern[str] | None:
    escaped_markers = [re.escape(marker) for marker in markers if marker]
    if not escaped_markers:
        return None
    return re.compile("|".join(escaped_markers))


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
