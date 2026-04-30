import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import cast
from urllib.error import URLError
from unittest import mock

import blokus.review.diff as review_diff
from blokus.review.config import HeuristicConfig, PerformanceConfig, ProviderConfig, ReviewConfig, load_review_config
from blokus.review.coordinator import ReviewCoordinator, ReviewRun
from blokus.review.diff import build_review_context, should_run_performance_review
from blokus.review.provider import OpenRouterClient, ProviderUnavailable
from blokus.review.specialists import _parse_specialist_response
from blokus.review.static_analyzer import StaticAnalysisReport, StaticAnalyzer, ToolRun
from blokus.review.types import ChangedFile, Finding, LineSpan, ReviewContext, ReviewPayload, ReviewResult, ReviewSummary, UncertainRisk


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_GITHUB = REPO_ROOT / "scripts" / "github"
if str(SCRIPTS_GITHUB) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_GITHUB))

import agentic_code_review  # noqa: E402


def _make_config(repo_root: Path) -> ReviewConfig:
    return ReviewConfig(
        repo_root=repo_root,
        max_findings=5,
        excluded_globs=("*.md", "*.ai", "*.svg", "*.png", "*.xlsx", "*.pdf"),
        blocking_severities=("critical", "high"),
        prompt_dir=repo_root / ".github" / "prompts",
        spec_path=repo_root / "docs" / "agentic-review" / "spec.md",
        schema_path=repo_root / "schemas" / "agentic_review_output.schema.json",
        provider=ProviderConfig(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            timeout_seconds=30,
            max_retries=2,
        ),
        performance=PerformanceConfig(
            path_markers=("src/blokus/engine.py",),
            diff_markers=("for ", "while ", "cache"),
        ),
        heuristics=HeuristicConfig(
            schema_test_paths=("tests/test_serialization.py",),
            fixture_test_paths=("tests/test_serialization.py", "tests/test_evaluate.py"),
            cli_test_paths=("tests/test_cli.py", "scripts/cli_smoke.sh"),
            serialization_paths=("src/blokus/models.py", "src/blokus/release.py"),
            dependency_files=("pyproject.toml", "setup.cfg"),
        ),
        models={
            "default": "default-model",
            "correctness": "correctness-model",
            "tests": "tests-model",
            "performance": "performance-model",
        },
    )


def _changed_file(
    path: str,
    *,
    line_start: int = 1,
    line_end: int = 1,
    patch: str = "",
    performance_sensitive: bool = False,
) -> ChangedFile:
    categories = []
    if path.endswith(".py"):
        categories.append("python")
    if path.endswith(".sh"):
        categories.append("shell")
    if path.startswith("tests/"):
        categories.append("test")
    if path.startswith("schemas/"):
        categories.append("schema")
    if path.startswith("fixtures/"):
        categories.append("fixture")
    return ChangedFile(
        path=path,
        status="M",
        patch=patch or f"@@ -0,0 +{line_start},1 @@\n+change\n",
        line_spans=(LineSpan(line_start, line_end),),
        executable=path.endswith(".py") or path.endswith(".sh"),
        categories=tuple(categories),
        performance_sensitive=performance_sensitive,
    )


def _review_context(*changed_files: ChangedFile, same_repo: bool = True) -> ReviewContext:
    executable_files = tuple(item for item in changed_files if item.executable)
    return ReviewContext(
        pr=ReviewPayload(number=17, head_sha="headsha", base_sha="basesha"),
        base_ref="origin/main",
        head_ref="HEAD",
        branch_name="feature/fix-review",
        commits=("fix issue",),
        changed_files=tuple(changed_files),
        impact="moderate",
        bias_risks=("self-declared-correctness-bias", "misleading-task-bias"),
        same_repo=same_repo,
        executable_files=executable_files,
        raw_diff="\n".join(item.patch for item in changed_files),
    )


class AgenticReviewTests(unittest.TestCase):
    maxDiff = None

    def test_load_review_config_applies_model_overrides(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "REVIEW_MODEL_DEFAULT": "env-default",
                "REVIEW_MODEL_CORRECTNESS": "env-correctness",
            },
            clear=False,
        ):
            config = load_review_config(repo_root=REPO_ROOT)
            self.assertEqual(config.model_for("correctness"), "env-correctness")
            self.assertEqual(config.model_for("tests"), "env-default")

    def test_build_review_context_filters_excluded_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            self._init_git_repo(repo_root)
            (repo_root / "src").mkdir()
            (repo_root / "src" / "demo.py").write_text("print('one')\n", encoding="utf-8")
            (repo_root / "README.md").write_text("# demo\n", encoding="utf-8")
            self._git(repo_root, "add", ".")
            self._git(repo_root, "commit", "-m", "base")
            base_sha = self._git_output(repo_root, "rev-parse", "HEAD")

            (repo_root / "src" / "demo.py").write_text("print('two')\n", encoding="utf-8")
            (repo_root / "README.md").write_text("# demo\n\nupdated\n", encoding="utf-8")
            self._git(repo_root, "add", ".")
            self._git(repo_root, "commit", "-m", "head")
            head_sha = self._git_output(repo_root, "rev-parse", "HEAD")

            context = build_review_context(_make_config(repo_root), base_ref=base_sha, head_ref=head_sha)

        self.assertEqual([item.path for item in context.changed_files], ["src/demo.py"])
        self.assertEqual([item.path for item in context.executable_files], ["src/demo.py"])
        self.assertTrue(context.executable_files[0].touches_line(1))

    def test_load_changed_files_uses_single_patch_diff_and_precise_line_spans(self) -> None:
        config = _make_config(REPO_ROOT)
        patch_text = "\n".join(
            [
                "diff --git a/src/demo.py b/src/demo.py",
                "index 1111111..2222222 100644",
                "--- a/src/demo.py",
                "+++ b/src/demo.py",
                "@@ -1,5 +1,5 @@",
                " one",
                " two",
                "-three",
                "+three updated",
                " four",
                " five",
            ]
        )

        with mock.patch.object(review_diff, "_git_lines", return_value=["M\tsrc/demo.py"]), mock.patch.object(
            review_diff,
            "_git_output",
            return_value=patch_text,
        ) as git_output:
            changed_files = review_diff._load_changed_files(config, "base", "head")

        self.assertEqual(len(changed_files), 1)
        self.assertEqual(changed_files[0].line_spans, (LineSpan(3, 3),))
        self.assertEqual(git_output.call_count, 1)
        git_output.assert_called_once_with(config.repo_root, ["diff", "--unified=3", "base...head"])

    def test_static_analyzer_heuristics_flag_cli_gap(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/cli.py", line_start=10, line_end=12))
        analyzer = StaticAnalyzer(config)

        with mock.patch.object(analyzer, "_discover_tool", return_value="/tool"), mock.patch.object(
            analyzer,
            "_run_command",
            return_value=ToolRun(command="tool", returncode=0, stdout="", stderr=""),
        ):
            report = analyzer.analyze(context)

        titles = [finding.title for finding in report.findings]
        self.assertIn("CLI change lacks direct CLI coverage", titles)
        self.assertTrue(report.commands)

    def test_mypy_parser_keeps_only_changed_lines(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/engine.py", line_start=12, line_end=12))
        analyzer = StaticAnalyzer(config)
        tool_run = ToolRun(
            command="mypy src/blokus/engine.py",
            returncode=1,
            stdout=(
                "src/blokus/engine.py:12: error: Incompatible return value type\n"
                "src/blokus/engine.py:99: error: Unrelated baseline issue\n"
            ),
            stderr="",
        )

        findings = analyzer._parse_mypy(context, tool_run)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].line_start, 12)

    def test_specialist_response_drops_findings_outside_changed_lines(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=20),)
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [
                        {
                            "title": "Valid",
                            "severity": "high",
                            "confidence": "high",
                            "category": "correctness",
                            "file": "src/blokus/engine.py",
                            "line_start": 20,
                            "line_end": 20,
                            "evidence": "Changed logic mishandles empty input.",
                            "impact": "Can reject legal moves.",
                            "suggested_action": "Add the missing empty-input guard.",
                            "blocking_recommendation": True,
                        },
                        {
                            "title": "Ignore me",
                            "severity": "moderate",
                            "confidence": "medium",
                            "category": "correctness",
                            "file": "src/blokus/engine.py",
                            "line_start": 30,
                            "line_end": 30,
                            "evidence": "Outside changed lines.",
                            "impact": "Should not survive validation.",
                            "suggested_action": "Ignore.",
                            "blocking_recommendation": False,
                        },
                    ]
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(len(response.findings), 1)
        self.assertEqual(response.findings[0].title, "Valid")

    def test_specialist_response_parses_uncertain_risks_and_note(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=20),)
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [],
                    "uncertain_risks": [
                        {
                            "risk": "Line numbers may drift.",
                            "reason_uncertain": "Provider can omit line anchors.",
                            "suggested_verification": "Manually inspect the generated review.",
                        }
                    ],
                    "note": "Provider returned a partial review.",
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(len(response.uncertain_risks), 1)
        self.assertEqual(response.uncertain_risks[0].risk, "Line numbers may drift.")
        self.assertEqual(response.note, "Provider returned a partial review.")

    def test_specialist_response_handles_invalid_json(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=20),)
        response = _parse_specialist_response("not-json", "correctness", files)

        self.assertEqual(response.findings, ())
        self.assertEqual(response.uncertain_risks, ())
        self.assertEqual(response.note, "Invalid non-JSON specialist response.")

    def test_specialist_response_ignores_incomplete_findings(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=20),)
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [
                        {
                            "title": "Missing line metadata",
                            "severity": "high",
                            "confidence": "high",
                            "category": "correctness",
                            "file": "src/blokus/engine.py",
                            "evidence": "No line numbers were returned.",
                            "impact": "Should be ignored.",
                            "suggested_action": "Ignore incomplete payloads.",
                            "blocking_recommendation": True,
                        }
                    ]
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(response.findings, ())

    def test_specialist_response_keeps_findings_on_changed_span_boundary(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=22),)
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [
                        {
                            "title": "Boundary line finding",
                            "severity": "moderate",
                            "confidence": "high",
                            "category": "correctness",
                            "file": "src/blokus/engine.py",
                            "line_start": 22,
                            "line_end": 30,
                            "evidence": "The changed line at the end of the span is still relevant.",
                            "impact": "Boundary filtering must keep the finding.",
                            "suggested_action": "Retain findings whose start line is inside the changed span.",
                            "blocking_recommendation": False,
                        }
                    ]
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(len(response.findings), 1)
        self.assertEqual(response.findings[0].line_start, 22)

    def test_specialist_response_drops_malformed_uncertain_risks(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=22),)
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [],
                    "uncertain_risks": [
                        {
                            "risk": "Missing verification field",
                            "reason_uncertain": "Payload is incomplete.",
                        }
                    ],
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(response.uncertain_risks, ())

    def test_coordinator_discusses_when_provider_unavailable(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/engine.py", line_start=12, line_end=12))
        static_report = StaticAnalysisReport(findings=(), uncertain_risks=(), commands=("compileall",), posture="clean")
        coordinator = ReviewCoordinator(config)

        with mock.patch("blokus.review.coordinator.build_review_context", return_value=context), mock.patch.object(
            coordinator.static_analyzer,
            "analyze",
            return_value=static_report,
        ), mock.patch.dict(os.environ, {}, clear=True):
            run = coordinator.run()

        self.assertEqual(run.result.verdict, "DISCUSS")
        self.assertTrue(run.result.uncertain_risks)
        self.assertIn("OpenRouter review was unavailable", run.result.uncertain_risks[0].risk)

    def test_should_run_performance_review_triggers_for_marker_path(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(
            _changed_file("src/blokus/engine.py", line_start=8, line_end=8, performance_sensitive=True)
        )

        self.assertTrue(should_run_performance_review(config, context))

    def test_should_run_performance_review_triggers_for_diff_marker(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(
            _changed_file(
                "src/blokus/review/diff.py",
                line_start=10,
                line_end=12,
                patch="@@ -0,0 +10,3 @@\n+for item in items:\n+    cache[key] = item\n+return cache\n",
                performance_sensitive=True,
            )
        )

        self.assertTrue(should_run_performance_review(config, context))

    def test_script_main_writes_artifacts_and_sets_exit_code(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/engine.py", line_start=8, line_end=8))
        result = ReviewResult(
            pr=context.pr,
            summary=ReviewSummary(
                overall_risk="high",
                test_posture="partial",
                static_analysis_posture="issues_found",
                performance_posture="not_applicable",
            ),
            findings=(
                Finding(
                    id="finding-1",
                    title="Blocking issue",
                    severity="high",
                    confidence="high",
                    category="correctness",
                    file="src/blokus/engine.py",
                    line_start=8,
                    line_end=8,
                    evidence="Changed rule check dropped a guard.",
                    impact="Can accept illegal moves.",
                    suggested_action="Restore the guard.",
                    blocking_recommendation=True,
                ),
            ),
            uncertain_risks=(),
            verdict="NEEDS CHANGES",
        )
        run = ReviewRun(
            context=context,
            result=result,
            markdown="## Agentic Code Review\n",
            static_report=StaticAnalysisReport(findings=(), uncertain_risks=(), commands=(), posture="clean"),
        )

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            agentic_code_review,
            "load_review_config",
            return_value=config,
        ), mock.patch.object(
            agentic_code_review,
            "ReviewCoordinator",
        ) as coordinator_cls, mock.patch.object(
            agentic_code_review,
            "GitHubClient",
        ) as client_cls, mock.patch.dict(
            os.environ,
            {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_TOKEN": "token",
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            [
                "agentic_code_review.py",
                "--json-out",
                str(Path(tmpdir) / "review.json"),
                "--markdown-out",
                str(Path(tmpdir) / "review.md"),
            ],
        ):
            coordinator_cls.return_value.run.return_value = run
            exit_code = agentic_code_review.main()
            written_payload = json.loads((Path(tmpdir) / "review.json").read_text(encoding="utf-8"))
            self.assertEqual(exit_code, 1)
            self.assertTrue((Path(tmpdir) / "review.json").exists())
            self.assertTrue((Path(tmpdir) / "review.md").exists())
            self.assertEqual(written_payload["summary"]["overall_risk"], "high")
            self.assertEqual((Path(tmpdir) / "review.md").read_text(encoding="utf-8"), "## Agentic Code Review\n")
            client_cls.return_value.upsert_issue_comment.assert_called_once()

    def test_script_main_uses_environment_overrides_and_discuss_exits_zero(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/review/diff.py", line_start=8, line_end=8), same_repo=False)
        result = ReviewResult(
            pr=context.pr,
            summary=ReviewSummary(
                overall_risk="moderate",
                test_posture="adequate",
                static_analysis_posture="clean",
                performance_posture="not_applicable",
            ),
            findings=(),
            uncertain_risks=(
                UncertainRisk(
                    risk="Provider was unavailable.",
                    reason_uncertain="OPENROUTER_API_KEY was missing.",
                    suggested_verification="Rerun the review with provider credentials.",
                ),
            ),
            verdict="DISCUSS",
        )
        run = ReviewRun(
            context=context,
            result=result,
            markdown="## Agentic Code Review\nDISCUSS\n",
            static_report=StaticAnalysisReport(findings=(), uncertain_risks=(), commands=(), posture="clean"),
        )

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            agentic_code_review,
            "load_review_config",
            return_value=config,
        ), mock.patch.object(
            agentic_code_review,
            "ReviewCoordinator",
        ) as coordinator_cls, mock.patch.object(
            agentic_code_review,
            "GitHubClient",
        ) as client_cls, mock.patch.dict(
            os.environ,
            {
                "REVIEW_BASE_REF": "env-base",
                "REVIEW_HEAD_REF": "env-head",
                "REVIEW_PULL_NUMBER": "44",
                "GITHUB_EVENT_PATH": "",
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            [
                "agentic_code_review.py",
                "--json-out",
                str(Path(tmpdir) / "review.json"),
                "--markdown-out",
                str(Path(tmpdir) / "review.md"),
            ],
        ):
            coordinator_cls.return_value.run.return_value = run
            exit_code = agentic_code_review.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                coordinator_cls.return_value.run.call_args.kwargs,
                {
                    "event_payload": None,
                    "base_ref": "env-base",
                    "head_ref": "env-head",
                    "pr_number": 44,
                },
            )
            client_cls.assert_not_called()

    def test_script_main_cli_args_override_environment(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/review/diff.py", line_start=8, line_end=8))
        result = ReviewResult(
            pr=context.pr,
            summary=ReviewSummary(
                overall_risk="low",
                test_posture="adequate",
                static_analysis_posture="clean",
                performance_posture="not_applicable",
            ),
            findings=(),
            uncertain_risks=(),
            verdict="LGTM",
        )
        run = ReviewRun(
            context=context,
            result=result,
            markdown="## Agentic Code Review\nLGTM\n",
            static_report=StaticAnalysisReport(findings=(), uncertain_risks=(), commands=(), posture="clean"),
        )

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            agentic_code_review,
            "load_review_config",
            return_value=config,
        ), mock.patch.object(
            agentic_code_review,
            "ReviewCoordinator",
        ) as coordinator_cls, mock.patch.dict(
            os.environ,
            {
                "REVIEW_BASE_REF": "env-base",
                "REVIEW_HEAD_REF": "env-head",
                "REVIEW_PULL_NUMBER": "44",
                "GITHUB_EVENT_PATH": "",
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            [
                "agentic_code_review.py",
                "--base-ref",
                "cli-base",
                "--head-ref",
                "cli-head",
                "--pr-number",
                "99",
                "--json-out",
                str(Path(tmpdir) / "review.json"),
                "--markdown-out",
                str(Path(tmpdir) / "review.md"),
            ],
        ):
            coordinator_cls.return_value.run.return_value = run
            exit_code = agentic_code_review.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                coordinator_cls.return_value.run.call_args.kwargs,
                {
                    "event_payload": None,
                    "base_ref": "cli-base",
                    "head_ref": "cli-head",
                    "pr_number": 99,
                },
            )

    def test_script_main_invalid_environment_pull_number_degrades_gracefully(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/review/diff.py", line_start=8, line_end=8))
        result = ReviewResult(
            pr=context.pr,
            summary=ReviewSummary(
                overall_risk="low",
                test_posture="adequate",
                static_analysis_posture="clean",
                performance_posture="not_applicable",
            ),
            findings=(),
            uncertain_risks=(),
            verdict="LGTM",
        )
        run = ReviewRun(
            context=context,
            result=result,
            markdown="## Agentic Code Review\nLGTM\n",
            static_report=StaticAnalysisReport(findings=(), uncertain_risks=(), commands=(), posture="clean"),
        )

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            agentic_code_review,
            "load_review_config",
            return_value=config,
        ), mock.patch.object(
            agentic_code_review,
            "ReviewCoordinator",
        ) as coordinator_cls, mock.patch.dict(
            os.environ,
            {
                "REVIEW_BASE_REF": "env-base",
                "REVIEW_HEAD_REF": "env-head",
                "REVIEW_PULL_NUMBER": "PR-44",
                "GITHUB_EVENT_PATH": "",
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            [
                "agentic_code_review.py",
                "--json-out",
                str(Path(tmpdir) / "review.json"),
                "--markdown-out",
                str(Path(tmpdir) / "review.md"),
            ],
        ):
            coordinator_cls.return_value.run.return_value = run
            exit_code = agentic_code_review.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                coordinator_cls.return_value.run.call_args.kwargs,
                {
                    "event_payload": None,
                    "base_ref": "env-base",
                    "head_ref": "env-head",
                    "pr_number": None,
                },
            )

    def test_script_main_loads_pull_request_event_and_writes_schema_shaped_output(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/review/diff.py", line_start=8, line_end=8))
        result = ReviewResult(
            pr=context.pr,
            summary=ReviewSummary(
                overall_risk="low",
                test_posture="adequate",
                static_analysis_posture="clean",
                performance_posture="not_applicable",
            ),
            findings=(),
            uncertain_risks=(),
            verdict="LGTM",
        )
        run = ReviewRun(
            context=context,
            result=result,
            markdown="## Agentic Code Review\n\n### Verdict\n- `LGTM`\n",
            static_report=StaticAnalysisReport(findings=(), uncertain_risks=(), commands=(), posture="clean"),
        )
        event_payload = {
            "pull_request": {
                "number": 44,
                "base": {
                    "sha": "base-sha",
                    "repo": {"full_name": "owner/repo"},
                },
                "head": {
                    "sha": "head-sha",
                    "repo": {"full_name": "owner/repo"},
                },
            }
        }

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            agentic_code_review,
            "load_review_config",
            return_value=config,
        ), mock.patch.object(
            agentic_code_review,
            "ReviewCoordinator",
        ) as coordinator_cls, mock.patch.object(
            agentic_code_review,
            "GitHubClient",
        ) as client_cls, mock.patch.dict(
            os.environ,
            {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_TOKEN": "token",
                "GITHUB_EVENT_PATH": str(Path(tmpdir) / "event.json"),
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            [
                "agentic_code_review.py",
                "--json-out",
                str(Path(tmpdir) / "review.json"),
                "--markdown-out",
                str(Path(tmpdir) / "review.md"),
            ],
        ):
            (Path(tmpdir) / "event.json").write_text(json.dumps(event_payload), encoding="utf-8")
            coordinator_cls.return_value.run.return_value = run

            exit_code = agentic_code_review.main()
            written_payload = json.loads((Path(tmpdir) / "review.json").read_text(encoding="utf-8"))
            schema = json.loads((REPO_ROOT / "schemas" / "agentic_review_output.schema.json").read_text(encoding="utf-8"))

            self.assertEqual(exit_code, 0)
            self.assertEqual(
                coordinator_cls.return_value.run.call_args.kwargs,
                {
                    "event_payload": event_payload,
                    "base_ref": None,
                    "head_ref": None,
                    "pr_number": None,
                },
            )
            self._assert_review_payload_matches_schema(written_payload, schema)
            self.assertIn("## Agentic Code Review", (Path(tmpdir) / "review.md").read_text(encoding="utf-8"))
            self.assertIn("### Verdict", (Path(tmpdir) / "review.md").read_text(encoding="utf-8"))
            client_cls.return_value.upsert_issue_comment.assert_called_once()

    def test_script_main_with_real_coordinator_writes_schema_compliant_output(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/review/diff.py", line_start=8, line_end=8), same_repo=True)
        static_report = StaticAnalysisReport(findings=(), uncertain_risks=(), commands=("compileall",), posture="clean")
        event_payload = {
            "pull_request": {
                "number": 44,
                "base": {
                    "sha": "base-sha",
                    "repo": {"full_name": "owner/repo"},
                },
                "head": {
                    "sha": "head-sha",
                    "repo": {"full_name": "owner/repo"},
                },
            }
        }

        class FakeProvider:
            def complete(self, *, model: str, system_prompt: str, user_prompt: str) -> str:
                return json.dumps(
                    {
                        "findings": [],
                        "uncertain_risks": [],
                        "note": f"Reviewed with {model}",
                    }
                )

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            agentic_code_review,
            "load_review_config",
            return_value=config,
        ), mock.patch(
            "blokus.review.coordinator.build_review_context",
            return_value=context,
        ), mock.patch.object(
            StaticAnalyzer,
            "analyze",
            return_value=static_report,
        ), mock.patch(
            "blokus.review.coordinator.OpenRouterClient.from_env",
            return_value=FakeProvider(),
        ), mock.patch.object(
            agentic_code_review,
            "GitHubClient",
        ) as client_cls, mock.patch.dict(
            os.environ,
            {
                "GITHUB_REPOSITORY": "owner/repo",
                "GITHUB_TOKEN": "token",
                "GITHUB_EVENT_PATH": str(Path(tmpdir) / "event.json"),
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            [
                "agentic_code_review.py",
                "--json-out",
                str(Path(tmpdir) / "review.json"),
                "--markdown-out",
                str(Path(tmpdir) / "review.md"),
            ],
        ):
            (Path(tmpdir) / "event.json").write_text(json.dumps(event_payload), encoding="utf-8")

            exit_code = agentic_code_review.main()
            written_payload = json.loads((Path(tmpdir) / "review.json").read_text(encoding="utf-8"))
            schema = json.loads((REPO_ROOT / "schemas" / "agentic_review_output.schema.json").read_text(encoding="utf-8"))
            written_markdown = (Path(tmpdir) / "review.md").read_text(encoding="utf-8")

            self.assertEqual(exit_code, 0)
            self._assert_review_payload_matches_schema(written_payload, schema)
            self.assertIn("## Agentic Code Review", written_markdown)
            self.assertIn("### Static Analysis", written_markdown)
            self.assertIn("### Verdict", written_markdown)
            client_cls.return_value.upsert_issue_comment.assert_called_once()

    def _assert_review_payload_matches_schema(self, payload: dict[str, object], schema: dict[str, object]) -> None:
        self.assertEqual(set(payload.keys()), set(cast(list[str], schema["required"])))

        properties = cast(dict[str, object], schema["properties"])
        pr_payload = cast(dict[str, object], payload["pr"])
        pr_schema = cast(dict[str, object], properties["pr"])
        self.assertEqual(set(pr_payload.keys()), set(cast(list[str], pr_schema["required"])))

        summary_payload = cast(dict[str, object], payload["summary"])
        summary_schema = cast(
            dict[str, object],
            cast(dict[str, object], properties["summary"])["properties"],
        )
        self.assertIn(
            summary_payload["overall_risk"],
            cast(list[str], cast(dict[str, object], summary_schema["overall_risk"])["enum"]),
        )
        self.assertIn(
            summary_payload["test_posture"],
            cast(list[str], cast(dict[str, object], summary_schema["test_posture"])["enum"]),
        )
        self.assertIn(
            summary_payload["static_analysis_posture"],
            cast(list[str], cast(dict[str, object], summary_schema["static_analysis_posture"])["enum"]),
        )
        self.assertIn(
            summary_payload["performance_posture"],
            cast(list[str], cast(dict[str, object], summary_schema["performance_posture"])["enum"]),
        )

        findings_payload = cast(list[dict[str, object]], payload["findings"])
        if findings_payload:
            finding_schema = cast(
                dict[str, object],
                cast(dict[str, object], properties["findings"])["items"],
            )
            self.assertEqual(set(findings_payload[0].keys()), set(cast(list[str], finding_schema["required"])))

        risks_payload = cast(list[dict[str, object]], payload["uncertain_risks"])
        if risks_payload:
            risk_schema = cast(
                dict[str, object],
                cast(dict[str, object], properties["uncertain_risks"])["items"],
            )
            self.assertEqual(set(risks_payload[0].keys()), set(cast(list[str], risk_schema["required"])))

    def test_static_analyzer_run_command_uses_timeout(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)

        with mock.patch("subprocess.run") as run_mock:
            run_mock.return_value = subprocess.CompletedProcess(args=["python"], returncode=0, stdout="", stderr="")
            analyzer._run_command(["python", "-V"])

        self.assertEqual(run_mock.call_args.kwargs["timeout"], config.provider.timeout_seconds)

    def test_static_analyzer_run_command_handles_timeout(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)

        with mock.patch("subprocess.run", side_effect=subprocess.TimeoutExpired(["python"], config.provider.timeout_seconds)):
            tool_run = analyzer._run_command(["python", "-V"])

        self.assertEqual(tool_run.returncode, 124)
        self.assertIn("timed out", tool_run.stderr.lower())

    def test_static_analyzer_limits_compileall_to_changed_python_files(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(_changed_file("src/blokus/cli.py", line_start=10, line_end=12))
        invocations: list[list[str]] = []

        def fake_run(args: list[str]) -> ToolRun:
            invocations.append(args)
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(analyzer, "_discover_tool", return_value="/tool"), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            analyzer.analyze(context)

        self.assertEqual(invocations[0], [sys.executable, "-m", "compileall", "src/blokus/cli.py"])

    def test_static_analyzer_skips_compileall_for_shell_only_changes(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(_changed_file("scripts/check.sh", line_start=1, line_end=1))
        invocations: list[list[str]] = []

        def fake_run(args: list[str]) -> ToolRun:
            invocations.append(args)
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(analyzer, "_discover_tool", return_value=None), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            analyzer.analyze(context)

        self.assertEqual(invocations, [["bash", "-n", "scripts/check.sh"]])

    def test_openrouter_client_retries_retryable_failures(self) -> None:
        client = OpenRouterClient(
            api_key="token",
            base_url="https://openrouter.example",
            timeout_seconds=30,
            max_retries=2,
        )
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "  LGTM  "}}]}
        ).encode("utf-8")

        with mock.patch("blokus.review.provider.time.sleep"), mock.patch(
            "blokus.review.provider.urlopen",
            side_effect=[URLError("temporary failure"), response],
        ) as urlopen_mock:
            result = client.complete(model="gpt", system_prompt="sys", user_prompt="user")

        self.assertEqual(result, "LGTM")
        self.assertEqual(urlopen_mock.call_count, 2)

    def test_openrouter_client_raises_after_retry_budget_is_exhausted(self) -> None:
        client = OpenRouterClient(
            api_key="token",
            base_url="https://openrouter.example",
            timeout_seconds=30,
            max_retries=2,
        )

        with mock.patch("blokus.review.provider.time.sleep"), mock.patch(
            "blokus.review.provider.urlopen",
            side_effect=[URLError("temporary failure"), URLError("temporary failure"), URLError("still failing")],
        ) as urlopen_mock:
            with self.assertRaisesRegex(ProviderUnavailable, "after 3 attempts"):
                client.complete(model="gpt", system_prompt="sys", user_prompt="user")

        self.assertEqual(urlopen_mock.call_count, 3)

    def _init_git_repo(self, repo_root: Path) -> None:
        self._git(repo_root, "init")
        self._git(repo_root, "config", "user.email", "tests@example.com")
        self._git(repo_root, "config", "user.name", "Tests")

    def _git(self, repo_root: Path, *args: str) -> None:
        subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)

    def _git_output(self, repo_root: Path, *args: str) -> str:
        completed = subprocess.run(["git", *args], cwd=repo_root, check=True, capture_output=True, text=True)
        return completed.stdout.strip()


if __name__ == "__main__":
    unittest.main()
