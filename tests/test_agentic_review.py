import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from blokus.review.config import HeuristicConfig, PerformanceConfig, ProviderConfig, ReviewConfig, load_review_config
from blokus.review.coordinator import ReviewCoordinator, ReviewRun
from blokus.review.diff import build_review_context
from blokus.review.specialists import _parse_specialist_response
from blokus.review.static_analyzer import StaticAnalysisReport, StaticAnalyzer, ToolRun
from blokus.review.types import ChangedFile, Finding, LineSpan, ReviewContext, ReviewPayload, ReviewResult, ReviewSummary


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


def _changed_file(path: str, *, line_start: int = 1, line_end: int = 1, patch: str = "") -> ChangedFile:
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
            self.assertEqual(exit_code, 1)
            self.assertTrue((Path(tmpdir) / "review.json").exists())
            self.assertTrue((Path(tmpdir) / "review.md").exists())
            client_cls.return_value.upsert_issue_comment.assert_called_once()

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
