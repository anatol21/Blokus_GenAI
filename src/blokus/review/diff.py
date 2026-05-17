"""Build diff-backed review context for the agentic PR review flow.

This module resolves review refs, reads local git history, streams unified diff
patches, and converts patch metadata into ReviewContext and ChangedFile objects.
It tracks changed-line spans, path/category metadata, executable files,
performance-sensitive markers, excluded files, commit-context limits, and
stored patch truncation for downstream static and LLM review. The parser is
bounded and local-git based; it does not claim parity with GitHub's PR file
model or complete repository history.
"""

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
MAX_STORED_PATCH_FILES = 500
MAX_TOTAL_STORED_PATCH_CHARS = 1_500_000
MAX_ANALYZED_PATCH_LINES = 50_000
MAX_ANALYZED_PATCH_CHARS = 2_000_000
MAX_POST_TRUNCATION_ANALYSIS_LINES = 2_000
MAX_POST_TRUNCATION_ANALYSIS_CHARS = 100_000
MAX_POST_CAP_PERFORMANCE_SCAN_LINES = 2_000
MAX_POST_CAP_PERFORMANCE_SCAN_CHARS = 100_000
MAX_REVIEW_CONTEXT_COMMITS = 25
_PATCH_TRUNCATION_MARKER = "\n... [diff context truncated for scale]\n"


@dataclass(frozen=True)
class _PatchBlock:
    """Internal normalized patch block produced from one git diff file block.

    Purpose:
        Carry parsed patch metadata before conversion to ChangedFile.
    Important parameters:
        path is the selected review path, status is git-like status metadata,
        patch is bounded stored diff text, line_spans are changed post-change
        lines, old_path carries rename/copy source metadata, and the boolean
        fields carry performance/truncation signals.
    Return value:
        Dataclass value consumed by _load_changed_files().
    Side effects:
        None.
    Failure or fallback behavior:
        Instances are only built when _PatchAccumulator.build() can determine a
        non-null path.
    Trace:
        _PatchAccumulator.build(), _load_changed_files(), ChangedFile.
    """
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
    """Track post-change line spans while reading unified diff lines.

    Purpose:
        Convert hunk headers and patch body lines into LineSpan values for
        additions and deletion-only anchors.
    Important parameters:
        spans stores completed spans, current_line tracks the new-file hunk
        line, span_start tracks an active addition span, and deletion_anchor
        tracks zero-line hunks.
    Return value:
        finish() returns tuple[LineSpan, ...].
    Side effects:
        Mutates tracker state while feed() is called.
    Failure or fallback behavior:
        Lines outside hunks and file header lines are ignored; deletion-only
        hunks produce a one-line anchor.
    Trace:
        _HUNK_RE, feed(), finish(), _flush_current_hunk(), LineSpan.
    """
    spans: list[LineSpan] = field(default_factory=list)
    current_line: int | None = None
    span_start: int | None = None
    deletion_anchor: int | None = None

    def feed(self, raw_line: str) -> None:
        """Consume one raw unified diff line and update changed-line state.

        Purpose:
            Start new hunks, track added-line spans, ignore deletion/context
            marker lines as appropriate, and flush completed spans.
        Important parameters:
            raw_line is one line from a git patch, without requiring a trailing
            newline.
        Return value:
            None.
        Side effects:
            Mutates current_line, span_start, deletion_anchor, and spans.
        Failure or fallback behavior:
            Non-hunk lines before any current hunk, `---`/`+++` file headers,
            deletion lines, and `\\ No newline` markers do not create additions.
        Trace:
            _HUNK_RE, _flush_current_hunk(), LineSpan.
        """
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

        if raw_line.startswith("-"):
            if self.span_start is None and self.deletion_anchor is None:
                self.deletion_anchor = self.current_line
            return

        if raw_line.startswith("\\"):
            return

        if self.span_start is not None:
            self._flush_current_hunk()
        elif self.deletion_anchor is not None:
            self._flush_current_hunk()
        else:
            self.deletion_anchor = None
        self.current_line += 1

    def finish(self) -> tuple[LineSpan, ...]:
        """Flush any active hunk state and return parsed changed-line spans.

        Purpose:
            Complete the final active addition span or deletion anchor after all
            patch lines have been fed.
        Important parameters:
            Uses the tracker's current mutable state.
        Return value:
            tuple of LineSpan objects.
        Side effects:
            May append one final span and clears active span/deletion state
            through _flush_current_hunk().
        Failure or fallback behavior:
            If no hunk was active, returns the spans already collected.
        Trace:
            _flush_current_hunk(), LineSpan.
        """
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
    """Accumulate one git diff file block into a bounded _PatchBlock.

    Purpose:
        Track paths, status, line spans, performance sensitivity, and stored
        patch text while _iter_git_patch_blocks() streams stdout.
    Important parameters:
        config supplies performance markers. tracker parses line spans.
        old_path/new_path/status mirror patch metadata. stored_parts and
        stored_chars implement MAX_STORED_PATCH_CHARS truncation.
    Return value:
        build() returns _PatchBlock or None.
    Side effects:
        Mutates accumulator state as each patch line is added.
    Failure or fallback behavior:
        build() returns None when no path can be inferred; truncated patches are
        marked with _PATCH_TRUNCATION_MARKER.
    Trace:
        add_line(), build(), _track_paths(), _track_performance(),
        _append_bounded(), MAX_STORED_PATCH_CHARS.
    """
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
    post_truncation_analyzed_lines: int = 0
    post_truncation_analyzed_chars: int = 0
    analysis_truncated: bool = False
    post_cap_performance_scan_lines: int = 0
    post_cap_performance_scan_chars: int = 0
    _path_markers_checked: bool = field(default=False, repr=False)
    _diff_marker_pattern: re.Pattern[str] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        # Pre-compile the diff marker regex once
        self._diff_marker_pattern = _diff_marker_pattern(self.config.performance.diff_markers)

    def add_line(self, line: str) -> None:
        """Process one patch line into all accumulator subsystems.

        Purpose:
            Feed the line-span tracker, update path/status metadata, update
            performance sensitivity, and append bounded patch context.
        Important parameters:
            line is one stdout line from `git diff`, with the trailing newline
            already stripped.
        Return value:
            None.
        Side effects:
            Mutates tracker, path/status fields, performance_sensitive,
            stored_parts, stored_chars, and patch_truncated.
        Failure or fallback behavior:
            Once patch_truncated is true, further patch text is not stored,
            though line-span and metadata tracking still continue.
        Trace:
            _LineSpanTracker.feed(), _track_paths(), _track_performance(),
            _append_bounded().
        """
        if self._should_skip_remaining_lines():
            if self._should_scan_post_cap_performance(line):
                self._track_performance(line)
            return
        self._track_paths(line)
        self.tracker.feed(line)
        if self.analysis_truncated:
            self._track_performance(line)
        elif self._would_exceed_analysis_limit(line):
            self.analysis_truncated = True
            self._track_performance(line)
        else:
            self._track_performance(line)
            self._record_analyzed_line(line)
        self._append_bounded(line)

    def build(self) -> _PatchBlock | None:
        """Finalize accumulated patch metadata into a _PatchBlock.

        Purpose:
            Choose the review path, append the truncation marker if needed,
            flush line spans, and expose rename/copy source metadata.
        Important parameters:
            Uses accumulated old_path, new_path, stored_parts, tracker, status,
            performance_sensitive, and patch_truncated.
        Return value:
            _PatchBlock when a path is available; otherwise None.
        Side effects:
            Calls tracker.finish(), which may mutate tracker state by flushing a
            final span.
        Failure or fallback behavior:
            Uses old_path when new_path is missing or `/dev/null`; returns None
            if neither path is available.
        Trace:
            _PATCH_TRUNCATION_MARKER, _LineSpanTracker.finish(), _PatchBlock.
        """
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
            if path:
                if any(marker in path for marker in self.config.performance.path_markers):
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
        line_size = len(line) + 1
        return (
            self.analyzed_lines >= MAX_ANALYZED_PATCH_LINES
            or self.analyzed_chars + line_size > MAX_ANALYZED_PATCH_CHARS
            or (
                self.patch_truncated
                and (
                    self.post_truncation_analyzed_lines >= MAX_POST_TRUNCATION_ANALYSIS_LINES
                    or self.post_truncation_analyzed_chars + line_size > MAX_POST_TRUNCATION_ANALYSIS_CHARS
                )
            )
        )

    def _should_skip_remaining_lines(self) -> bool:
        return (
            self.patch_truncated
            and self.analysis_truncated
            and (self.new_path is not None or self.old_path is not None)
        )

    def _should_scan_post_cap_performance(self, line: str) -> bool:
        if self.performance_sensitive:
            return False
        line_size = len(line) + 1
        if self.post_cap_performance_scan_lines >= MAX_POST_CAP_PERFORMANCE_SCAN_LINES:
            return False
        if self.post_cap_performance_scan_chars + line_size > MAX_POST_CAP_PERFORMANCE_SCAN_CHARS:
            return False
        self.post_cap_performance_scan_lines += 1
        self.post_cap_performance_scan_chars += line_size
        return True

    def _record_analyzed_line(self, line: str) -> None:
        line_size = len(line) + 1
        self.analyzed_lines += 1
        self.analyzed_chars += line_size
        if self.patch_truncated:
            self.post_truncation_analyzed_lines += 1
            self.post_truncation_analyzed_chars += line_size


def build_review_context(
    config: ReviewConfig,
    *,
    event_payload: dict[str, object] | None = None,
    base_ref: str | None = None,
    head_ref: str | None = None,
    pr_number: int | None = None,
) -> ReviewContext:
    """Collect the diff-backed inputs for one review run.

    Purpose:
        Resolve base/head refs, read commit metadata, load changed files, filter
        excluded paths, identify executable files, and assemble ReviewContext.
    Important parameters:
        config supplies repo_root and excluded_globs. event_payload may provide
        pull_request base/head SHAs and PR number. base_ref, head_ref, and
        pr_number are fallback explicit inputs.
    Return value:
        ReviewContext with ReviewPayload, resolved refs, branch name, bounded
        commit subjects, included changed files, executable files, impact, bias
        risks, same_repo, commit_context_truncated, and raw_diff="".
    Side effects:
        Runs git subprocesses through _git_output(), _git_lines(), and
        _load_changed_files().
    Failure or fallback behavior:
        Missing or invalid git refs can raise subprocess.CalledProcessError via
        _git_output() or _iter_git_patch_blocks(). Partial PR payloads fall back
        through _resolve_refs().
    Trace:
        _resolve_refs(), _git_output(), _git_lines(), MAX_REVIEW_CONTEXT_COMMITS,
        _load_changed_files(), _is_excluded(), _classify_impact(),
        _infer_bias_risks().
    """

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
    """Return whether the performance specialist should run for this context.

    Purpose:
        Check whether any executable changed file was already marked
        performance_sensitive during patch accumulation.
    Important parameters:
        context supplies executable_files. config is accepted for the public
        call shape but is currently unused.
    Return value:
        True if any executable ChangedFile has performance_sensitive=True;
        otherwise False.
    Side effects:
        None.
    Failure or fallback behavior:
        Non-executable files do not trigger this check even if marked
        performance_sensitive.
    Trace:
        ChangedFile.performance_sensitive, ReviewContext.executable_files,
        _PatchAccumulator._track_performance().
    """

    del config
    return any(changed_file.performance_sensitive for changed_file in context.executable_files)


def _resolve_refs(
    event_payload: dict[str, object] | None,
    base_ref: str | None,
    head_ref: str | None,
    pr_number: int | None,
) -> tuple[str, str, int | None, bool]:
    """Resolve review base/head refs and PR metadata.

    Purpose:
        Prefer pull_request base/head SHAs from an event payload when both are
        present, otherwise fall back to explicit refs or default local refs.
    Important parameters:
        event_payload may contain a pull_request dict. base_ref, head_ref, and
        pr_number are fallback values.
    Return value:
        (base_ref_or_sha, head_ref_or_sha, pr_number_or_none, same_repo).
    Side effects:
        None.
    Failure or fallback behavior:
        Partial or malformed pull_request payloads fall back to base_ref or
        "origin/main", head_ref or "HEAD", pr_number, and same_repo=True.
    Trace:
        _nested_sha(), _optional_int(), _same_repo().
    """
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
    """Load changed files from a three-dot git diff and normalize them.

    Purpose:
        Stream patch blocks for `base_ref...head_ref` and convert each block to
        a ChangedFile with executable, category, rename, performance, and
        truncation metadata.
    Important parameters:
        config supplies repo_root and parsing/performance settings. base_ref and
        head_ref are expected to be git-resolvable refs or SHAs.
    Return value:
        tuple[ChangedFile, ...].
    Side effects:
        Runs git diff indirectly through _iter_git_patch_blocks().
    Failure or fallback behavior:
        Propagates subprocess.CalledProcessError from _iter_git_patch_blocks()
        when git exits non-zero.
    Trace:
        _iter_git_patch_blocks(), _is_executable_path(), _categorize_path(),
        ChangedFile.
    """
    diff_ref = f"{base_ref}...{head_ref}"
    changed_files: list[ChangedFile] = []
    stored_patch_files = 0
    stored_patch_chars = 0

    for patch_block in _iter_git_patch_blocks(config, config.repo_root, ["diff", "--unified=3", diff_ref]):
        excluded = _is_excluded(config, patch_block.path)
        patch = patch_block.patch
        patch_truncated = patch_block.patch_truncated

        if excluded:
            patch = ""
        elif patch and (
            stored_patch_files >= MAX_STORED_PATCH_FILES
            or stored_patch_chars + len(patch) > MAX_TOTAL_STORED_PATCH_CHARS
        ):
            patch = ""
            patch_truncated = True
        elif patch:
            stored_patch_files += 1
            stored_patch_chars += len(patch)

        changed_files.append(
            ChangedFile(
                path=patch_block.path,
                status=patch_block.status,
                patch=patch,
                line_spans=patch_block.line_spans,
                executable=_is_executable_path(patch_block.path),
                categories=tuple(_categorize_path(patch_block.path)),
                old_path=patch_block.old_path,
                performance_sensitive=patch_block.performance_sensitive,
                patch_truncated=patch_truncated,
                analysis_truncated=patch_block.analysis_truncated,
            )
        )

    return tuple(changed_files)


def _current_branch(repo_root: Path) -> str:
    branch = _git_output(repo_root, ["branch", "--show-current"]).strip()
    return branch or "HEAD"


def _parse_line_spans(patch_text: str) -> list[LineSpan]:
    """Parse changed post-change line spans from patch text.

    Purpose:
        Convenience wrapper that feeds split patch lines into _LineSpanTracker.
    Important parameters:
        patch_text is unified diff text for one or more file blocks.
    Return value:
        list[LineSpan] produced by the tracker.
    Side effects:
        None outside local tracker state.
    Failure or fallback behavior:
        Lines not recognized by _LineSpanTracker.feed() are ignored.
    Trace:
        _LineSpanTracker.feed(), _LineSpanTracker.finish(), _HUNK_RE.
    """
    tracker = _LineSpanTracker()
    for raw_line in patch_text.splitlines():
        tracker.feed(raw_line)
    return list(tracker.finish())


def _iter_git_patch_blocks(
    config: ReviewConfig,
    repo_root: Path,
    args: list[str],
) -> Iterator[_PatchBlock]:
    """Stream git patch output into _PatchBlock objects.

    Purpose:
        Run a git command, split stdout into file-level diff blocks, and yield
        normalized patch blocks without first storing the full diff output.
    Important parameters:
        config is passed to each _PatchAccumulator. repo_root is the subprocess
        cwd. args are appended after `git`.
    Return value:
        Iterator[_PatchBlock].
    Side effects:
        Starts subprocess.Popen(["git", *args]), reads stdout, starts a daemon
        thread to drain stderr, closes pipes, and waits for the process.
    Failure or fallback behavior:
        Raises subprocess.CalledProcessError with stderr if git exits non-zero.
        Blocks with no inferred path are skipped through _PatchAccumulator.build().
    Trace:
        subprocess.Popen, threading.Thread, _PatchAccumulator.add_line(),
        _PatchAccumulator.build().
    """
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



def _classify_impact(changed_files: tuple[ChangedFile, ...]) -> str:
    """Classify coarse review impact from included changed paths.

    Purpose:
        Assign low/moderate/high/critical impact using path heuristics.
    Important parameters:
        changed_files supplies already-filtered ChangedFile paths.
    Return value:
        "low", "moderate", "high", or "critical".
    Side effects:
        None.
    Failure or fallback behavior:
        Empty changes are "low"; only hard-coded critical markers, `.github/`,
        and known path prefixes affect higher levels.
    Trace:
        critical_markers, path prefix checks in _classify_impact().
    """
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
    """Produce ordered bias-risk prompts from branch and commit text.

    Purpose:
        Return the review flow's standard bias-risk labels and prioritize
        self-declared-correctness-bias when branch/commit text contains matching
        terms.
    Important parameters:
        branch_name and commit subject strings form weak_context.
    Return value:
        tuple[str, ...] with duplicates removed while preserving order.
    Side effects:
        None.
    Failure or fallback behavior:
        If _SELF_DECLARED_RE does not match, self-declared-correctness-bias is
        appended rather than prepended.
    Trace:
        _SELF_DECLARED_RE, MAX_REVIEW_CONTEXT_COMMITS, dict.fromkeys().
    """
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
    """Return simple path categories used by downstream review stages.

    Purpose:
        Classify a changed path as python, shell, workflow, schema, fixture,
        test, and/or docs.
    Important parameters:
        path is a normalized repository-relative path.
    Return value:
        list[str] of zero or more categories.
    Side effects:
        None.
    Failure or fallback behavior:
        Unknown paths return an empty list; categories are suffix/prefix based.
    Trace:
        _load_changed_files(), ChangedFile.categories.
    """
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
    """Return whether a path should be removed from review context.

    Purpose:
        Apply configured fnmatch-style excluded globs after changed files are
        loaded.
    Important parameters:
        config.excluded_globs supplies patterns; path is repository-relative.
    Return value:
        True when any pattern matches, otherwise False.
    Side effects:
        None.
    Failure or fallback behavior:
        Empty excluded_globs means no path is excluded.
    Trace:
        fnmatch.fnmatch(), build_review_context().
    """
    return any(fnmatch.fnmatch(path, pattern) for pattern in config.excluded_globs)


def _git_output(repo_root: Path, args: list[str]) -> str:
    """Run a git command and return captured stdout.

    Purpose:
        Execute small git commands used for ref resolution, branch lookup, and
        commit subjects.
    Important parameters:
        repo_root is subprocess cwd. args are appended after `git`.
    Return value:
        Completed stdout as text.
    Side effects:
        Runs subprocess.run(["git", *args], cwd=repo_root, check=True,
        capture_output=True, text=True).
    Failure or fallback behavior:
        Non-zero git exit raises subprocess.CalledProcessError because
        check=True.
    Trace:
        subprocess.run(), build_review_context(), _current_branch(),
        _git_lines().
    """
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
