"""Diff-aware static-analysis support for the agentic PR review flow.

This module runs deterministic checks over changed executable Python and shell
files before the agentic review coordinator renders final findings. It invokes
local tools such as compileall, Ruff, Mypy, bash syntax checks, and ShellCheck
when they are available, then normalizes changed-line diagnostics into Finding
objects. It also emits UncertainRisk records for skipped, capped, unavailable,
or unparsable analysis and adds repository-specific heuristics for sensitive
paths, dependency metadata, and missing nearby tests.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from blokus.automation import is_sensitive_path, tests_missing
from blokus.review.config import ReviewConfig
from blokus.review.types import ChangedFile, Finding, ReviewContext, UncertainRisk, stable_finding_id


_MYPY_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+)(?::(?P<column>\d+))?: (?P<kind>error|note): (?P<message>.+)$"
)
_COMPILEALL_RE = re.compile(r'File "(?P<file>.+?)", line (?P<line>\d+)')
_BASH_RE = re.compile(r"^(?P<file>.+?): line (?P<line>\d+): (?P<message>.+)$")
_MAX_TOOL_BATCH_FILES = 1000
_MAX_TOOL_BATCH_CHARS = 65_536
_MAX_JSON_TOOL_OUTPUT_CHARS = 1_000_000
_MAX_TOOL_CAPTURE_CHARS = _MAX_JSON_TOOL_OUTPUT_CHARS + 10_000
_MAX_EXPENSIVE_PYTHON_ANALYSIS_FILES = 400
_MAX_COMPILEALL_FILES = 100
_MAX_STATIC_FINDINGS_PER_TOOL = 100  # Cap to prevent OOM with excessive diagnostics
_TOOL_OUTPUT_TRUNCATION_MARKER = "\n... [output truncated for scale]\n"


@dataclass(frozen=True)
class ToolRun:
    """Captured execution details for one static-analysis command."""

    command: str
    returncode: int
    stdout: str
    stderr: str


@dataclass(frozen=True)
class StaticAnalysisReport:
    """Normalized static-analysis results."""

    findings: tuple[Finding, ...]
    uncertain_risks: tuple[UncertainRisk, ...]
    commands: tuple[str, ...]
    false_positives_ignored: tuple[str, ...] = field(default_factory=tuple)
    posture: str = "not_run"


@dataclass(frozen=True)
class _ToolParseResult:
    findings: tuple[Finding, ...] = ()
    uncertain_risks: tuple[UncertainRisk, ...] = ()
    unavailable: bool = False


class StaticAnalyzer:
    """Coordinate deterministic static checks and repository heuristics.

    Purpose:
        Provide the static-analysis layer used by ReviewCoordinator before any
        provider-backed specialist review runs.
    Important parameters:
        config: ReviewConfig stored at construction time; supplies repo_root,
            command timeout settings, and heuristic path configuration.
    Return value:
        Public analysis returns StaticAnalysisReport instances containing
        normalized Finding and UncertainRisk objects.
    Side effects:
        Methods may execute local subprocesses under config.repo_root and may
        create temporary Mypy response files for oversized command batches.
    Failure or fallback behavior:
        Missing tools, capped analysis, command timeouts, and invalid JSON tool
        output are represented as uncertain risks instead of being treated as a
        complete static-analysis result.
    Trace:
        analyze(), _run_command(), _discover_tool(), _build_mypy_commands(),
        _heuristic_findings(), StaticAnalysisReport.
    """

    def __init__(self, config: ReviewConfig) -> None:
        self.config = config

    def analyze(self, context: ReviewContext) -> StaticAnalysisReport:
        """Run changed-file static analysis and return a normalized report.

        Purpose:
            Select changed executable Python and shell files, run bounded local
            tool checks, parse changed-line diagnostics, add repository
            heuristics, and compute the static-analysis posture.
        Important parameters:
            context: ReviewContext containing changed_files, executable_files,
                file categories, paths, and changed line spans.
        Return value:
            StaticAnalysisReport with findings, uncertain_risks, executed
            command strings, and a posture of "not_run", "clean",
            "issues_found", or "unavailable".
        Side effects:
            Executes compileall, Ruff, Mypy, bash, and ShellCheck subprocesses
            when relevant and available; deletes Mypy temporary response files
            in a finally block.
        Failure or fallback behavior:
            Caps compileall at _MAX_COMPILEALL_FILES, skips Ruff and Mypy above
            _MAX_EXPENSIVE_PYTHON_ANALYSIS_FILES, records missing tools as
            UncertainRisk entries, and propagates parser uncertainty from JSON
            tool output.
        Trace:
            _build_tool_batches(), _discover_tool(), _run_command(),
            _parse_compileall(), _parse_ruff(), _parse_mypy(), _parse_bash(),
            _parse_shellcheck(), _heuristic_findings().
        """
        python_files = [changed_file for changed_file in context.executable_files if "python" in changed_file.categories]
        shell_files = [changed_file for changed_file in context.executable_files if "shell" in changed_file.categories]

        findings: list[Finding] = []
        uncertain_risks: list[UncertainRisk] = []
        commands: list[str] = []
        tool_finding_counts: dict[str, int] = {}
        capped_finding_tools: set[str] = set()
        unavailable_tools = False
        skip_expensive_python_tools = len(python_files) > _MAX_EXPENSIVE_PYTHON_ANALYSIS_FILES

        if python_files:
            compileall_files = python_files
            if len(python_files) > _MAX_COMPILEALL_FILES:
                compileall_files = python_files[:_MAX_COMPILEALL_FILES]
                uncertain_risks.append(
                    UncertainRisk(
                        risk="Compileall was capped for a large change set.",
                        reason_uncertain=(
                            f"The diff touched {len(python_files)} Python files, which exceeds the bounded review limit "
                            f"of {_MAX_COMPILEALL_FILES} files for compileall. Only the first {_MAX_COMPILEALL_FILES} files were checked."
                        ),
                        suggested_verification="Run `python -m compileall` manually for the full change set or split the change into smaller PRs.",
                    )
                )
            for compileall_args in _build_tool_batches(
                [sys.executable, "-m", "compileall"],
                compileall_files,
            ):
                compileall_run = self._run_command(compileall_args)
                commands.append(compileall_run.command)
                self._extend_bounded_findings(
                    findings,
                    uncertain_risks,
                    tool_name="Compileall",
                    tool_findings=self._parse_compileall(context, compileall_run),
                    tool_finding_counts=tool_finding_counts,
                    capped_tools=capped_finding_tools,
                )

        if python_files:
            if skip_expensive_python_tools:
                unavailable_tools = True
                uncertain_risks.append(
                    UncertainRisk(
                        risk="Expensive Python static analysis was skipped for a very large change set.",
                        reason_uncertain=(
                            f"The diff touched {len(python_files)} Python files, which exceeds the bounded review limit "
                            f"of {_MAX_EXPENSIVE_PYTHON_ANALYSIS_FILES} files for Ruff and Mypy."
                        ),
                        suggested_verification="Run Ruff and Mypy manually for the full change set or split the change into smaller PRs.",
                    )
                )
            else:
                ruff_path = self._discover_tool("ruff")
                if ruff_path is None:
                    unavailable_tools = True
                    uncertain_risks.append(
                        UncertainRisk(
                            risk="Ruff was unavailable for changed Python files.",
                            reason_uncertain="`ruff` was not found on PATH or under `.venv/bin`.",
                            suggested_verification="Install Ruff or run `ruff check <changed-python-files>` manually.",
                        )
                    )
                else:
                    for ruff_args in _build_tool_batches(
                        [ruff_path, "check", "--output-format", "json"],
                        python_files,
                        supports_option_terminator=True,
                    ):
                        ruff_run = self._run_command(ruff_args)
                        commands.append(ruff_run.command)
                        parsed = self._parse_ruff(context, ruff_run)
                        self._extend_bounded_findings(
                            findings,
                            uncertain_risks,
                            tool_name="Ruff",
                            tool_findings=parsed.findings,
                            tool_finding_counts=tool_finding_counts,
                            capped_tools=capped_finding_tools,
                        )
                        uncertain_risks.extend(parsed.uncertain_risks)
                        unavailable_tools = unavailable_tools or parsed.unavailable

                mypy_path = self._discover_tool("mypy")
                if mypy_path is None:
                    unavailable_tools = True
                    uncertain_risks.append(
                        UncertainRisk(
                            risk="Mypy was unavailable for changed Python files.",
                            reason_uncertain="`mypy` was not found on PATH or under `.venv/bin`.",
                            suggested_verification="Install Mypy or run `mypy <changed-python-files>` manually.",
                        )
                    )
                else:
                    mypy_commands, cleanup_paths = self._build_mypy_commands(mypy_path, python_files)
                    try:
                        for mypy_args in mypy_commands:
                            mypy_run = self._run_command(
                                mypy_args
                            )
                            commands.append(mypy_run.command)
                            self._extend_bounded_findings(
                                findings,
                                uncertain_risks,
                                tool_name="Mypy",
                                tool_findings=self._parse_mypy(context, mypy_run),
                                tool_finding_counts=tool_finding_counts,
                                capped_tools=capped_finding_tools,
                            )
                    finally:
                        for cleanup_path in cleanup_paths:
                            cleanup_path.unlink(missing_ok=True)

        if shell_files:
            for bash_args in _build_tool_batches(
                ["bash", "-n"],
                shell_files,
                supports_option_terminator=True,
            ):
                bash_run = self._run_command(bash_args)
                commands.append(bash_run.command)
                self._extend_bounded_findings(
                    findings,
                    uncertain_risks,
                    tool_name="bash -n",
                    tool_findings=self._parse_bash(shell_files, bash_run),
                    tool_finding_counts=tool_finding_counts,
                    capped_tools=capped_finding_tools,
                )

            shellcheck_path = self._discover_tool("shellcheck")
            if shellcheck_path is None:
                unavailable_tools = True
                uncertain_risks.append(
                    UncertainRisk(
                        risk="ShellCheck was unavailable for changed shell scripts.",
                        reason_uncertain="`shellcheck` was not found on PATH or under `.venv/bin`.",
                        suggested_verification="Install ShellCheck or run `shellcheck <changed-shell-files>` manually.",
                    )
                )
            else:
                for shellcheck_args in _build_tool_batches(
                    [shellcheck_path, "-f", "json1"],
                    shell_files,
                    supports_option_terminator=True,
                ):
                    shellcheck_run = self._run_command(shellcheck_args)
                    commands.append(shellcheck_run.command)
                    parsed = self._parse_shellcheck(shell_files, shellcheck_run)
                    self._extend_bounded_findings(
                        findings,
                        uncertain_risks,
                        tool_name="ShellCheck",
                        tool_findings=parsed.findings,
                        tool_finding_counts=tool_finding_counts,
                        capped_tools=capped_finding_tools,
                    )
                    uncertain_risks.extend(parsed.uncertain_risks)
                    unavailable_tools = unavailable_tools or parsed.unavailable

        self._extend_bounded_findings(
            findings,
            uncertain_risks,
            tool_name="Heuristic static analysis",
            tool_findings=self._heuristic_findings(context),
            tool_finding_counts=tool_finding_counts,
            capped_tools=capped_finding_tools,
        )
        uncertain_risks.extend(self._heuristic_uncertain_risks(context))

        posture = "not_run"
        if findings:
            posture = "issues_found"
        elif commands:
            posture = "clean"
        if unavailable_tools and posture == "clean":
            posture = "unavailable"

        return StaticAnalysisReport(
            findings=tuple(findings),
            uncertain_risks=tuple(uncertain_risks),
            commands=tuple(commands),
            posture=posture,
        )

    def _extend_bounded_findings(
        self,
        findings: list[Finding],
        uncertain_risks: list[UncertainRisk],
        *,
        tool_name: str,
        tool_findings: list[Finding] | tuple[Finding, ...],
        tool_finding_counts: dict[str, int],
        capped_tools: set[str],
    ) -> None:
        if not tool_findings:
            return

        current_count = tool_finding_counts.get(tool_name, 0)
        remaining = max(0, _MAX_STATIC_FINDINGS_PER_TOOL - current_count)
        if remaining <= 0:
            self._append_findings_cap_risk(tool_name, uncertain_risks, capped_tools)
            return

        ordered_findings = sorted(tool_findings, key=lambda finding: finding.rank(), reverse=True)
        accepted_findings = ordered_findings[:remaining]
        findings.extend(accepted_findings)
        tool_finding_counts[tool_name] = current_count + len(accepted_findings)

        if len(ordered_findings) > remaining:
            self._append_findings_cap_risk(tool_name, uncertain_risks, capped_tools)

    def _append_findings_cap_risk(
        self,
        tool_name: str,
        uncertain_risks: list[UncertainRisk],
        capped_tools: set[str],
    ) -> None:
        if tool_name in capped_tools:
            return

        capped_tools.add(tool_name)
        uncertain_risks.append(
            UncertainRisk(
                risk=f"{tool_name} findings were capped.",
                reason_uncertain=(
                    f"{tool_name} produced more than {_MAX_STATIC_FINDINGS_PER_TOOL} findings across this review run. "
                    f"Only up to {_MAX_STATIC_FINDINGS_PER_TOOL} findings from that tool were retained."
                ),
                suggested_verification=(
                    f"Rerun the relevant `{tool_name}` check manually or narrow the changed-file set to inspect the full "
                    "diagnostic output."
                ),
            )
        )

    def _parse_ruff(self, context: ReviewContext, tool_run: ToolRun) -> _ToolParseResult:
        """Convert Ruff JSON diagnostics into changed-line findings.

        Purpose:
            Parse stdout from `ruff check --output-format json` and emit
            findings only for diagnostics whose file and start line match the
            review diff.
        Important parameters:
            context: ReviewContext used to verify changed files and line spans.
            tool_run: ToolRun containing Ruff stdout, stderr, return code, and
                command text.
        Return value:
            _ToolParseResult containing findings plus any JSON parsing
            uncertainty.
        Side effects:
            None.
        Failure or fallback behavior:
            Empty stdout returns no findings; oversized, invalid, or
            wrong-shaped JSON returns an UncertainRisk with unavailable=True;
            malformed entries are skipped.
        Trace:
            _load_json_output(), _normalize_tool_path(), _positive_int(),
            _lookup_changed_file(), stable_finding_id().
        """
        if not tool_run.stdout.strip():
            return _ToolParseResult()

        findings: list[Finding] = []
        payload, parse_risk = self._load_json_output(tool_run, tool_name="Ruff", expected_shape="array")
        if parse_risk is not None:
            return _ToolParseResult(uncertain_risks=(parse_risk,), unavailable=True)

        for entry in cast(list[dict[str, object]], payload):
            location = entry.get("location")
            end_location = entry.get("end_location")
            if not isinstance(location, dict) or not isinstance(end_location, dict):
                continue
            path = _normalize_tool_path(entry.get("filename"), self.config.repo_root)
            line_number = _positive_int(location.get("row"))
            if path is None or line_number is None:
                continue
            line_end = _positive_int(end_location.get("row"))
            if line_end is None:
                line_end = line_number

            changed_file = _lookup_changed_file(context, path, line_number)
            if changed_file is None:
                continue

            code = str(entry.get("code") or "unknown")
            message = str(entry.get("message") or "Ruff reported a diagnostic.")

            severity = "high" if code.startswith("E9") or code in {"F821", "F822", "F823", "F831"} else "moderate"
            blocking = severity == "high"
            findings.append(
                Finding(
                    id=stable_finding_id("ruff", path, line_number, code, message),
                    title=f"Ruff {code}",
                    severity=severity,
                    confidence="high",
                    category="static-analysis",
                    file=path,
                    line_start=line_number,
                    line_end=max(line_number, line_end),
                    evidence=f"`ruff check` reported `{code}` on a changed line: {message}",
                    impact="The changed code includes a lint diagnostic that may indicate an executable defect or maintenance hazard.",
                    suggested_action=f"Fix the Ruff diagnostic `{code}` on `{path}:{line_number}` and rerun Ruff.",
                    blocking_recommendation=blocking,
                    source="static-analyzer",
                )
            )
        return _ToolParseResult(findings=tuple(findings))

    def _parse_mypy(self, context: ReviewContext, tool_run: ToolRun) -> list[Finding]:
        """Parse Mypy text output into changed-line type findings.

        Purpose:
            Read Mypy stdout lines matching _MYPY_RE and report only `error`
            diagnostics that map to changed lines.
        Important parameters:
            context: ReviewContext used for changed-file and changed-line
                filtering.
            tool_run: ToolRun containing Mypy stdout.
        Return value:
            High-severity Finding objects for changed-line Mypy errors.
        Side effects:
            None.
        Failure or fallback behavior:
            Non-matching lines, `note` diagnostics, unnormalizable paths, and
            diagnostics outside changed lines are ignored.
        Trace:
            _MYPY_RE, _normalize_tool_path(), _lookup_changed_file(),
            stable_finding_id().
        """
        findings: list[Finding] = []
        for raw_line in tool_run.stdout.splitlines():
            match = _MYPY_RE.match(raw_line.strip())
            if not match or match.group("kind") != "error":
                continue
            #path = str(Path(match.group("file")).as_posix())
            path = _normalize_tool_path(match.group("file"), self.config.repo_root)
            if path is None:
                continue
            line_number = int(match.group("line"))
            changed_file = _lookup_changed_file(context, path, line_number)
            if changed_file is None:
                continue
            message = match.group("message")
            findings.append(
                Finding(
                    id=stable_finding_id("mypy", path, line_number, message),
                    title="Mypy type error",
                    severity="high",
                    confidence="high",
                    category="static-analysis",
                    file=path,
                    line_start=line_number,
                    line_end=line_number,
                    evidence=f"`mypy` reported a type error on a changed line: {message}",
                    impact="The changed code no longer satisfies the configured static type checks and may fail at runtime or drift from its contract.",
                    suggested_action="Fix the reported type mismatch or update the typed contract intentionally and rerun Mypy.",
                    blocking_recommendation=True,
                    source="static-analyzer",
                )
            )
        return findings

    def _parse_compileall(self, context: ReviewContext, tool_run: ToolRun) -> list[Finding]:
        """Parse compileall failures into Python compile-error findings.

        Purpose:
            Use _COMPILEALL_RE over combined stdout and stderr from
            `python -m compileall` to identify changed Python files that failed
            to compile.
        Important parameters:
            context: ReviewContext used to restrict findings to changed lines.
            tool_run: ToolRun produced by the compileall command.
        Return value:
            High-severity Python compile-error findings.
        Side effects:
            None.
        Failure or fallback behavior:
            Return code 0 returns no findings; unmatched output,
            unnormalizable paths, and diagnostics outside changed lines are
            ignored.
        Trace:
            _COMPILEALL_RE, _normalize_tool_path(), _lookup_changed_file(),
            stable_finding_id().
        """
        if tool_run.returncode == 0:
            return []
        findings: list[Finding] = []
        for match in _COMPILEALL_RE.finditer("\n".join([tool_run.stdout, tool_run.stderr])):
            path = _normalize_tool_path(match.group("file"), self.config.repo_root)
            if path is None:
              continue


            line_number = int(match.group("line"))
            changed_file = _lookup_changed_file(context, path, line_number)
            if changed_file is None:
                continue
            findings.append(
                Finding(
                    id=stable_finding_id("compileall", path, line_number),
                    title="Python compile error",
                    severity="high",
                    confidence="high",
                    category="static-analysis",
                    file=path,
                    line_start=line_number,
                    line_end=line_number,
                    evidence="`python -m compileall` failed on a changed Python file.",
                    impact="The changed Python module cannot be compiled successfully and is likely to fail at import time.",
                    suggested_action="Fix the syntax or compilation error and rerun compileall.",
                    blocking_recommendation=True,
                    source="static-analyzer",
                )
            )
        return findings

    def _parse_bash(self, shell_files: list[ChangedFile], tool_run: ToolRun) -> list[Finding]:
        """Parse bash syntax-check stderr for changed shell-script lines.

        Purpose:
            Convert `bash -n` syntax errors into findings for changed shell
            files.
        Important parameters:
            shell_files: Changed shell files selected by analyze().
            tool_run: ToolRun produced by the bash syntax-check command.
        Return value:
            High-severity shell syntax findings.
        Side effects:
            None.
        Failure or fallback behavior:
            Return code 0 returns no findings; stderr lines that do not match
            _BASH_RE, paths outside shell_files, invalid line numbers, and
            unchanged lines are ignored.
        Trace:
            _BASH_RE, _normalize_tool_path(), _positive_int(),
            ChangedFile.touches_line(), stable_finding_id().
        """
        if tool_run.returncode == 0:
            return []
        findings: list[Finding] = []
        shell_by_path = {item.path: item for item in shell_files}
        for raw_line in tool_run.stderr.splitlines():
            match = _BASH_RE.match(raw_line.strip())
            if not match:
                continue
            path = _normalize_tool_path(match.group("file"), self.config.repo_root)
            line_number = _positive_int(match.group("line"))
            if path is None or line_number is None:
                continue
            changed_file = shell_by_path.get(path)
            if changed_file is None or not changed_file.touches_line(line_number):
                continue
            findings.append(
                Finding(
                    id=stable_finding_id("bash", path, line_number, match.group("message")),
                    title="Shell syntax error",
                    severity="high",
                    confidence="high",
                    category="static-analysis",
                    file=path,
                    line_start=line_number,
                    line_end=line_number,
                    evidence=f"`bash -n` reported a syntax error on a changed line: {match.group('message')}",
                    impact="The changed shell script does not parse correctly and may fail before executing its intended logic.",
                    suggested_action="Fix the shell syntax error and rerun `bash -n`.",
                    blocking_recommendation=True,
                    source="static-analyzer",
                )
            )
        return findings

    def _parse_shellcheck(self, shell_files: list[ChangedFile], tool_run: ToolRun) -> _ToolParseResult:
        """Convert ShellCheck JSON comments into changed-line findings.

        Purpose:
            Parse stdout from `shellcheck -f json1` and report comments that
            apply to changed shell-script lines.
        Important parameters:
            shell_files: Changed shell files selected by analyze().
            tool_run: ToolRun containing ShellCheck stdout, stderr, return code,
                and command text.
        Return value:
            _ToolParseResult containing findings plus any JSON parsing
            uncertainty.
        Side effects:
            None.
        Failure or fallback behavior:
            Empty stdout returns no result; oversized, invalid, or wrong-shaped
            JSON returns an UncertainRisk with unavailable=True; missing or
            non-list `comments` returns no findings.
        Trace:
            _load_json_output(), _normalize_tool_path(), _positive_int(),
            ChangedFile.touches_line(), stable_finding_id().
        """
        if not tool_run.stdout.strip():
            return _ToolParseResult()
        findings: list[Finding] = []
        payload, parse_risk = self._load_json_output(tool_run, tool_name="ShellCheck", expected_shape="object")
        if parse_risk is not None:
            return _ToolParseResult(uncertain_risks=(parse_risk,), unavailable=True)
        shell_by_path = {item.path: item for item in shell_files}
        comments = cast(dict[str, object], payload).get("comments")
        if not isinstance(comments, list):
            return _ToolParseResult()
        for comment in comments:
            if not isinstance(comment, dict):
                continue
            path = _normalize_tool_path(comment.get("file"), self.config.repo_root)
            line_number = _positive_int(comment.get("line"))
            if path is None or line_number is None:
                continue
            changed_file = shell_by_path.get(path)
            if changed_file is None or not changed_file.touches_line(line_number):
                continue
            code = comment.get("code")
            message = comment.get("message")
            if code is None or message is None:
                continue
            level = str(comment.get("level", "warning"))
            severity = "high" if level == "error" else "moderate"
            findings.append(
                Finding(
                    id=stable_finding_id("shellcheck", path, line_number, code),
                    title=f"ShellCheck {code}",
                    severity=severity,
                    confidence="high",
                    category="static-analysis",
                    file=path,
                    line_start=line_number,
                    line_end=line_number,
                    evidence=f"`shellcheck` reported `{code}` on a changed line: {message}",
                    impact="The changed shell script includes a shell correctness issue that can break execution or make behavior brittle.",
                    suggested_action="Address the ShellCheck diagnostic and rerun the shell checks.",
                    blocking_recommendation=severity == "high",
                    source="static-analyzer",
                )
            )
        return _ToolParseResult(findings=tuple(findings))

    def _heuristic_findings(self, context: ReviewContext) -> list[Finding]:
        """Add repository-specific findings that do not come from tools.

        Purpose:
            Flag path-based review risks for schemas, fixtures, CLI entrypoints,
            serialization-sensitive files, missing test updates, and
            workflow-sensitive paths.
        Important parameters:
            context: ReviewContext containing all changed file paths.
        Return value:
            Normalized Finding objects with source="static-analyzer".
        Side effects:
            None.
        Failure or fallback behavior:
            Heuristics emit findings only when their path and coverage
            conditions match; the generic missing-tests finding is skipped if a
            more specific heuristic finding already exists.
        Trace:
            config.heuristics, tests_missing(), is_sensitive_path(),
            stable_finding_id().
        """
        findings: list[Finding] = []
        changed_paths = {changed_file.path for changed_file in context.changed_files}
        test_paths = {path for path in changed_paths if path.startswith("tests/")}
        fixture_paths = {path for path in changed_paths if path.startswith("fixtures/")}
        schema_paths = {path for path in changed_paths if path.startswith("schemas/")}
        serialization_paths = set(self.config.heuristics.serialization_paths)
        cli_paths = {"src/blokus/cli.py", "src/blokus/__main__.py"}

        if schema_paths and not (test_paths & set(self.config.heuristics.schema_test_paths) or fixture_paths):
            findings.append(
                Finding(
                    id=stable_finding_id("heuristic", "schema", *sorted(schema_paths)),
                    title="Schema change lacks validation coverage",
                    severity="high",
                    confidence="medium",
                    category="tests",
                    file=sorted(schema_paths)[0],
                    line_start=1,
                    line_end=1,
                    evidence="`schemas/` changed without matching serialization tests or fixture updates in the diff.",
                    impact="Contract changes can drift from fixtures or runtime serialization behavior without a direct validation signal.",
                    suggested_action="Add or update serialization coverage or fixture updates for the changed schema paths.",
                    blocking_recommendation=True,
                    source="static-analyzer",
                )
            )

        if fixture_paths and not (test_paths or schema_paths):
            findings.append(
                Finding(
                    id=stable_finding_id("heuristic", "fixtures", *sorted(fixture_paths)),
                    title="Fixture change lacks nearby validation evidence",
                    severity="moderate",
                    confidence="medium",
                    category="tests",
                    file=sorted(fixture_paths)[0],
                    line_start=1,
                    line_end=1,
                    evidence="`fixtures/` changed without matching schema or test updates in the diff.",
                    impact="Fixtures can stop reflecting the active contract while still appearing syntactically valid.",
                    suggested_action="Add or update fixture-focused tests or schema-touching validation alongside the fixture change.",
                    blocking_recommendation=False,
                    source="static-analyzer",
                )
            )

        if changed_paths & cli_paths and not any(path in changed_paths for path in self.config.heuristics.cli_test_paths):
            file_path = sorted(changed_paths & cli_paths)[0]
            findings.append(
                Finding(
                    id=stable_finding_id("heuristic", "cli", file_path),
                    title="CLI change lacks direct CLI coverage",
                    severity="moderate",
                    confidence="medium",
                    category="tests",
                    file=file_path,
                    line_start=1,
                    line_end=1,
                    evidence="CLI entrypoint code changed without `tests/test_cli.py` or `scripts/cli_smoke.sh` changing in the same diff.",
                    impact="CLI contract changes can regress user-facing behavior without an obvious focused check in the PR.",
                    suggested_action="Update CLI tests or the smoke path if the change affects command behavior or output.",
                    blocking_recommendation=False,
                    source="static-analyzer",
                )
            )

        if changed_paths & serialization_paths and not (test_paths & set(self.config.heuristics.schema_test_paths) or fixture_paths):
            file_path = sorted(changed_paths & serialization_paths)[0]
            findings.append(
                Finding(
                    id=stable_finding_id("heuristic", "serialization", file_path),
                    title="Serialization-sensitive change lacks contract coverage",
                    severity="high",
                    confidence="medium",
                    category="tests",
                    file=file_path,
                    line_start=1,
                    line_end=1,
                    evidence="Serialization-sensitive code changed without touching serialization tests or fixtures.",
                    impact="State or contract drift can slip through without an explicit replay or round-trip check.",
                    suggested_action="Add serialization or fixture round-trip coverage for the changed contract path.",
                    blocking_recommendation=True,
                    source="static-analyzer",
                )
            )

        if tests_missing(changed_paths) and not findings:
            code_paths = sorted(
                path for path in changed_paths if path.startswith(("src/", "fixtures/", "schemas/"))
            )
            if code_paths:
                findings.append(
                    Finding(
                        id=stable_finding_id("heuristic", "tests-missing", *code_paths),
                        title="Behavioral change lacks test updates",
                        severity="moderate",
                        confidence="medium",
                        category="tests",
                        file=code_paths[0],
                        line_start=1,
                        line_end=1,
                        evidence="Code-bearing paths changed without matching `tests/` updates in the diff.",
                        impact="The PR may change behavior without a nearby automated signal that the new behavior is intentional and covered.",
                        suggested_action="Add or update tests that exercise the changed behavior.",
                        blocking_recommendation=False,
                        source="static-analyzer",
                    )
                )

        workflow_sensitive = sorted(path for path in changed_paths if is_sensitive_path(path))
        if workflow_sensitive:
            findings.append(
                Finding(
                    id=stable_finding_id("heuristic", "workflow-sensitive", *workflow_sensitive),
                    title="Workflow-sensitive paths changed",
                    severity="low",
                    confidence="high",
                    category="requirements",
                    file=workflow_sensitive[0],
                    line_start=1,
                    line_end=1,
                    evidence="The diff touches workflow-sensitive paths such as `.github/` or pipeline governance files.",
                    impact="Automation and repair trust boundaries tighten for this PR and may require human review even if code changes are small.",
                    suggested_action="Confirm the workflow-sensitive change is intentional and keep human review in the loop.",
                    blocking_recommendation=False,
                    source="static-analyzer",
                )
            )

        return findings

    def _heuristic_uncertain_risks(self, context: ReviewContext) -> list[UncertainRisk]:
        """Record uncertainty for dependency metadata changes.

        Purpose:
            Note that dependency-related files changed when configured
            dependency paths appear in the diff.
        Important parameters:
            context: ReviewContext containing changed file paths.
        Return value:
            A one-item UncertainRisk list when dependency paths changed;
            otherwise an empty list.
        Side effects:
            None.
        Failure or fallback behavior:
            No dependency-path overlap returns no risk. The function does not
            inspect dependency contents or verify supply-chain intent.
        Trace:
            config.heuristics.dependency_files, UncertainRisk.
        """
        changed_paths = {changed_file.path for changed_file in context.changed_files}
        dependency_paths = changed_paths & set(self.config.heuristics.dependency_files)
        if not dependency_paths:
            return []
        return [
            UncertainRisk(
                risk="Dependency-related files changed in this PR.",
                reason_uncertain="The diff includes dependency metadata, but static analysis cannot confirm the runtime or supply-chain intent from changed code alone.",
                suggested_verification="Review dependency intent, confirm dependency-review output, and verify the change matches the PR description.",
            )
        ]

    def _discover_tool(self, name: str) -> str | None:
        discovered = shutil.which(name)
        if discovered:
            return discovered
        candidate = self.config.repo_root / ".venv" / "bin" / name
        if candidate.exists():
            return str(candidate)
        return None

    def _run_command(self, args: list[str]) -> ToolRun:
        """Execute one static-analysis subprocess and capture its streams.

        Purpose:
            Run a local command in the repository root with captured text output
            and the configured timeout.
        Important parameters:
            args: Command argument list passed directly to subprocess.run().
        Return value:
            ToolRun containing the joined command string, return code, stdout,
            and stderr.
        Side effects:
            Executes a local subprocess with cwd=config.repo_root.
        Failure or fallback behavior:
            subprocess.TimeoutExpired is converted to returncode 124 with any
            captured partial streams coerced to text and a timeout message
            appended to stderr.
        Trace:
            subprocess.run(), config.repo_root, config.provider.timeout_seconds,
            _coerce_stream_text(), ToolRun.
        """
        with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
            try:
                completed = subprocess.run(
                    args,
                    cwd=self.config.repo_root,
                    stdout=stdout_file,
                    stderr=stderr_file,
                    timeout=self.config.provider.tool_timeout_seconds,
                )
                return ToolRun(
                    command=" ".join(args),
                    returncode=completed.returncode,
                    stdout=_read_bounded_tool_output(stdout_file),
                    stderr=_read_bounded_tool_output(stderr_file),
                )
            except subprocess.TimeoutExpired:
                return ToolRun(
                    command=" ".join(args),
                    returncode=124,
                    stdout=_read_bounded_tool_output(stdout_file),
                    stderr=(
                        _read_bounded_tool_output(stderr_file)
                        + f"\nCommand timed out after {self.config.provider.tool_timeout_seconds} seconds."
                    ),
                )

    def _load_json_output(
        self,
        tool_run: ToolRun,
        *,
        tool_name: str,
        expected_shape: str,
    ) -> tuple[object | None, UncertainRisk | None]:
        if len(tool_run.stdout) > _MAX_JSON_TOOL_OUTPUT_CHARS:
            return None, UncertainRisk(
                risk=f"{tool_name} output exceeded the safe JSON parsing limit.",
                reason_uncertain=f"{tool_name} produced more than {_MAX_JSON_TOOL_OUTPUT_CHARS} characters of JSON output for one invocation, so the review skipped parsing it to avoid excessive memory and CPU use.",
                suggested_verification=f"Rerun `{tool_run.command}` manually, narrow the changed-file set, or reduce diagnostic volume before relying on the {tool_name} results.",
            )
        try:
            payload = json.loads(tool_run.stdout)
            if expected_shape == "array" and not isinstance(payload, list):
                raise TypeError("expected a JSON array")
            if expected_shape == "object" and not isinstance(payload, dict):
                raise TypeError("expected a JSON object")
            return payload, None
        except (json.JSONDecodeError, TypeError) as exc:
            return None, UncertainRisk(
                risk=f"{tool_name} output could not be parsed as JSON.",
                reason_uncertain=f"{tool_name} returned invalid or unexpected JSON output: {exc}",
                suggested_verification=f"Rerun `{tool_run.command}` and inspect the raw {tool_name} output for crashes, truncation, or configuration issues.",
            )

    def _build_mypy_commands(
        self,
        mypy_path: str,
        python_files: list[ChangedFile],
    ) -> tuple[list[list[str]], list[Path]]:
        """Build Mypy command arguments and cleanup paths.

        Purpose:
            Create Mypy invocations using pyproject.toml and stable output
            flags, falling back to one response-file invocation when direct
            batching would split the file list.
        Important parameters:
            mypy_path: Resolved path to the Mypy executable.
            python_files: Changed Python files selected by analyze().
        Return value:
            A tuple of command argument lists and temporary Paths that callers
            must delete after command execution.
        Side effects:
            May create a `.agentic-mypy-*.txt` temporary response file under
            config.repo_root.
        Failure or fallback behavior:
            If response-file creation or writing fails, the temporary file is
            unlinked before the exception is re-raised.
        Trace:
            _build_tool_batches(), _safe_tool_path(),
            tempfile.NamedTemporaryFile(), analyze() finally cleanup.
        """
        prefix_args = [
            mypy_path,
            "--config-file",
            str(self.config.repo_root / "pyproject.toml"),
            "--show-column-numbers",
            "--hide-error-context",
            "--no-error-summary",
        ]
        direct_batches = _build_tool_batches(
            prefix_args,
            python_files,
            supports_option_terminator=True,
        )
        if len(direct_batches) <= 1:
            return direct_batches, []

        response_file = tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=self.config.repo_root,
            prefix=".agentic-mypy-",
            suffix=".txt",
            delete=False,
        )
        response_path = Path(response_file.name)
        try:
            with response_file:
                for changed_file in python_files:
                    response_file.write(f"{_safe_tool_path(changed_file.path)}\n")
            return [[*prefix_args, f"@{response_path}"]], [response_path]
        except Exception:
            response_path.unlink(missing_ok=True)
            raise


def _coerce_stream_text(value: bytes | str | None) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value


def _read_bounded_tool_output(handle: object, *, max_chars: int = _MAX_TOOL_CAPTURE_CHARS) -> str:
    seek = getattr(handle, "seek", None)
    read = getattr(handle, "read", None)
    if not callable(seek) or not callable(read):
        return ""

    seek(0)
    raw_value = read(max_chars + 1)
    raw_bytes = _coerce_stream_bytes(raw_value)
    truncated = len(raw_bytes) > max_chars
    if truncated:
        raw_bytes = raw_bytes[:max_chars]
    text = raw_bytes.decode("utf-8", errors="replace")
    if truncated:
        text += _TOOL_OUTPUT_TRUNCATION_MARKER
    return text


def _coerce_stream_bytes(value: bytes | str | None) -> bytes:
    if value is None:
        return b""
    if isinstance(value, bytes):
        return value
    return value.encode("utf-8", errors="replace")


def _positive_int(value: object) -> int | None:
    try:
        parsed = int(str(value))
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 1 else None


def _normalize_tool_path(value: object, repo_root: Path) -> str | None:
    if value is None:
        return None
    path = Path(str(value))
    try:
        if path.is_absolute():
            path = path.resolve().relative_to(repo_root.resolve())
    except ValueError:
        pass
    return path.as_posix()


def _lookup_changed_file(context: ReviewContext, path: str, line_number: int) -> ChangedFile | None:
    normalized_path = Path(path).as_posix()
    for changed_file in context.changed_files:
        if changed_file.path != normalized_path:
            continue
        if not changed_file.line_spans or changed_file.touches_line(line_number):
            return changed_file
    return None


def _build_tool_batches(
    prefix_args: list[str],
    changed_files: list[ChangedFile],
    *,
    supports_option_terminator: bool = False,
) -> list[list[str]]:
    """Split changed-file tool invocations into bounded argument batches.

    Purpose:
        Build command argument lists that combine a tool prefix with changed-file
        paths while respecting file-count and argument-length limits.
    Important parameters:
        prefix_args: Command prefix placed before file paths.
        changed_files: Changed files whose paths should be passed to the tool.
        supports_option_terminator: When true, inserts `--` before paths for
            tools that support option termination.
    Return value:
        A list of command argument lists; empty changed_files returns [].
    Side effects:
        None.
    Failure or fallback behavior:
        Paths are normalized through _safe_tool_path(); batches split at
        _MAX_TOOL_BATCH_FILES or _MAX_TOOL_BATCH_CHARS.
    Trace:
        _MAX_TOOL_BATCH_FILES, _MAX_TOOL_BATCH_CHARS, _safe_tool_path().
    """
    if not changed_files:
        return []

    prefix = [*prefix_args]
    if supports_option_terminator:
        prefix.append("--")
    prefix_cost = sum(len(arg) + 1 for arg in prefix)

    batches: list[list[str]] = []
    current_paths: list[str] = []
    current_cost = prefix_cost

    for changed_file in changed_files:
        safe_path = _safe_tool_path(changed_file.path)
        path_cost = len(safe_path) + 1
        if current_paths and (
            len(current_paths) >= _MAX_TOOL_BATCH_FILES
            or current_cost + path_cost > _MAX_TOOL_BATCH_CHARS
        ):
            batches.append([*prefix, *current_paths])
            current_paths = []
            current_cost = prefix_cost

        current_paths.append(safe_path)
        current_cost += path_cost

    if current_paths:
        batches.append([*prefix, *current_paths])
    return batches


def _safe_tool_path(path: str) -> str:
    normalized = Path(path).as_posix()
    if normalized.startswith("-"):
        return f"./{normalized}"
    return normalized
