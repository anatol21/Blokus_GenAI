import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from dataclasses import replace
from email.message import Message
from pathlib import Path
from typing import cast
from urllib.error import HTTPError, URLError
from unittest import mock

import blokus.review.coordinator as review_coordinator
import blokus.review.diff as review_diff
from blokus.review.config import HeuristicConfig, PerformanceConfig, ProviderConfig, ReviewConfig, load_review_config
from blokus.review.coordinator import ReviewCoordinator, ReviewRun
from blokus.review.diff import build_review_context, should_run_performance_review
from blokus.review.provider import OpenRouterClient, ProviderUnavailable
from blokus.review.specialists import SpecialistRunner, _parse_specialist_response
from blokus.review.static_analyzer import StaticAnalysisReport, StaticAnalyzer, ToolRun
from blokus.review.types import ChangedFile, Finding, LineSpan, ReviewContext, ReviewPayload, ReviewResult, ReviewSummary, SpecialistResponse, UncertainRisk


REPO_ROOT = Path(__file__).resolve().parents[1]
import scripts.github.agentic_code_review as agentic_code_review  # noqa: E402


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
    patch_truncated: bool = False,
    old_path: str | None = None,
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
        old_path=old_path,
        performance_sensitive=performance_sensitive,
        patch_truncated=patch_truncated,
    )


def _review_context(
    *changed_files: ChangedFile,
    same_repo: bool = True,
    raw_diff: str | None = None,
    commits: tuple[str, ...] = ("fix issue",),
    commit_context_truncated: bool = False,
) -> ReviewContext:
    executable_files = tuple(item for item in changed_files if item.executable)
    rendered_diff = (
        raw_diff
        if raw_diff is not None
        else "\n\n".join(
            f"File: {item.path}\n```diff\n{item.patch.strip()}\n```"
            for item in changed_files
            if item.patch
        )
    )
    return ReviewContext(
        pr=ReviewPayload(number=17, head_sha="headsha", base_sha="basesha"),
        base_ref="origin/main",
        head_ref="HEAD",
        branch_name="feature/fix-review",
        commits=commits,
        changed_files=tuple(changed_files),
        impact="moderate",
        bias_risks=("self-declared-correctness-bias", "misleading-task-bias"),
        same_repo=same_repo,
        commit_context_truncated=commit_context_truncated,
        executable_files=executable_files,
        raw_diff=rendered_diff,
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

    def test_model_for_ignores_blank_environment_overrides(self) -> None:
        with mock.patch.dict(
            os.environ,
            {
                "REVIEW_MODEL_DEFAULT": "   ",
                "REVIEW_MODEL_CORRECTNESS": "   ",
            },
            clear=False,
        ):
            config = load_review_config(repo_root=REPO_ROOT)
            self.assertEqual(config.model_for("correctness"), config.models["correctness"])
            self.assertEqual(config.model_for("tests"), config.models["default"])

    def test_load_review_config_rejects_missing_config_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            with self.assertRaisesRegex(ValueError, "Agentic review config was not found"):
                load_review_config(repo_root=tmpdir)

    def test_load_review_config_rejects_invalid_toml(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / ".github").mkdir()
            (repo_root / ".github" / "agentic-review.toml").write_text("not = [valid", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "is not valid TOML"):
                load_review_config(repo_root=repo_root)

    def test_load_review_config_rejects_missing_required_key(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            repo_root = Path(tmpdir)
            (repo_root / ".github").mkdir()
            config_text = (REPO_ROOT / ".github" / "agentic-review.toml").read_text(encoding="utf-8")
            config_text = config_text.replace("[provider]", "")
            (repo_root / ".github" / "agentic-review.toml").write_text(config_text, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "missing required key"):
                load_review_config(repo_root=repo_root)

    def test_validate_provider_rejects_negative_retry_budget(self) -> None:
        config = replace(_make_config(REPO_ROOT), provider=ProviderConfig(
            name="openrouter",
            base_url="https://openrouter.ai/api/v1",
            timeout_seconds=30,
            max_retries=-1,
        ))

        with self.assertRaisesRegex(ValueError, "max_retries"):
            config.validate_provider()

    def test_model_for_requires_default_model(self) -> None:
        config = replace(_make_config(REPO_ROOT), models={"correctness": "correctness-model"})

        with self.assertRaisesRegex(ValueError, "models.default"):
            config.model_for("tests")

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

        with mock.patch.object(
            review_diff,
            "_iter_git_patch_blocks",
            return_value=[
                review_diff._PatchBlock(
                    path="src/demo.py",
                    status="M",
                    patch=patch_text,
                    line_spans=(LineSpan(3, 3),),
                    old_path=None,
                    performance_sensitive=False,
                    patch_truncated=False,
                )
            ],
        ) as git_output:
            changed_files = review_diff._load_changed_files(config, "base", "head")

        self.assertEqual(len(changed_files), 1)
        self.assertEqual(changed_files[0].line_spans, (LineSpan(3, 3),))
        self.assertEqual(changed_files[0].status, "M")
        self.assertEqual(git_output.call_count, 1)
        git_output.assert_called_once_with(config, config.repo_root, ["diff", "--unified=3", "base...head"])

    def test_load_changed_files_truncates_large_patches_after_analysis(self) -> None:
        config = _make_config(REPO_ROOT)
        large_hunk_lines = [f"+line {index}" for index in range(1800)]
        large_hunk_lines[-1] = "+cache warmup marker"
        patch_text = "\n".join(
            [
                "diff --git a/src/blokus/review/diff.py b/src/blokus/review/diff.py",
                "index 1111111..2222222 100644",
                "--- a/src/blokus/review/diff.py",
                "+++ b/src/blokus/review/diff.py",
                "@@ -0,0 +1,1800 @@",
                *large_hunk_lines,
            ]
        )

        with mock.patch.object(
            review_diff,
            "_iter_git_patch_blocks",
            return_value=[
                review_diff._PatchBlock(
                    path="src/blokus/review/diff.py",
                    status="M",
                    patch=patch_text[: review_diff.MAX_STORED_PATCH_CHARS - len("\n... [diff context truncated for scale]\n")]
                    + "\n... [diff context truncated for scale]\n",
                    line_spans=(LineSpan(1, 1800),),
                    old_path=None,
                    performance_sensitive=True,
                    patch_truncated=True,
                )
            ],
        ):
            changed_files = review_diff._load_changed_files(config, "base", "head")

        self.assertEqual(len(changed_files), 1)
        self.assertTrue(changed_files[0].patch_truncated)
        self.assertTrue(changed_files[0].performance_sensitive)
        self.assertLessEqual(len(changed_files[0].patch), review_diff.MAX_STORED_PATCH_CHARS)
        self.assertIn("truncated for scale", changed_files[0].patch)

    def test_patch_accumulator_marks_performance_sensitive_from_regex_markers(self) -> None:
        accumulator = review_diff._PatchAccumulator(_make_config(REPO_ROOT))
        for line in (
            "diff --git a/src/demo.py b/src/demo.py",
            "--- a/src/demo.py",
            "+++ b/src/demo.py",
            "@@ -1,1 +1,1 @@",
            "+cache lookup result",
        ):
            accumulator.add_line(line)

        block = accumulator.build()

        self.assertIsNotNone(block)
        self.assertTrue(cast(review_diff._PatchBlock, block).performance_sensitive)

    def test_parse_line_spans_adds_anchor_for_deletion_only_hunks(self) -> None:
        patch_text = "\n".join(
            [
                "diff --git a/src/demo.py b/src/demo.py",
                "index 1111111..2222222 100644",
                "--- a/src/demo.py",
                "+++ b/src/demo.py",
                "@@ -10,2 +12,0 @@",
                "-old value",
                "-other old value",
            ]
        )

        spans = review_diff._parse_line_spans(patch_text)

        self.assertEqual(spans, [LineSpan(12, 12)])

    def test_deletion_only_anchor_filters_unrelated_static_findings(self) -> None:
        config = _make_config(REPO_ROOT)
        patch_text = "\n".join(
            [
                "diff --git a/src/demo.py b/src/demo.py",
                "index 1111111..2222222 100644",
                "--- a/src/demo.py",
                "+++ b/src/demo.py",
                "@@ -10,2 +12,0 @@",
                "-old value",
                "-other old value",
            ]
        )

        with mock.patch.object(
            review_diff,
            "_iter_git_patch_blocks",
            return_value=[
                review_diff._PatchBlock(
                    path="src/demo.py",
                    status="M",
                    patch=patch_text,
                    line_spans=(LineSpan(12, 12),),
                    old_path=None,
                    performance_sensitive=False,
                    patch_truncated=False,
                )
            ],
        ):
            changed_files = review_diff._load_changed_files(config, "base", "head")

        analyzer = StaticAnalyzer(config)
        context = _review_context(*changed_files)
        tool_run = ToolRun(
            command="mypy src/demo.py",
            returncode=1,
            stdout="src/demo.py:30: error: Baseline issue should be filtered\n",
            stderr="",
        )

        findings = analyzer._parse_mypy(context, tool_run)

        self.assertEqual(findings, [])

    def test_patch_blocks_carry_rename_metadata_without_name_status_pass(self) -> None:
        config = _make_config(REPO_ROOT)

        with mock.patch.object(
            review_diff,
            "_iter_git_patch_blocks",
            return_value=[
                review_diff._PatchBlock(
                    path="src/blokus/new_engine.py",
                    status="R",
                    patch="diff --git a/src/blokus/old_engine.py b/src/blokus/new_engine.py",
                    line_spans=(LineSpan(5, 5),),
                    old_path="src/blokus/old_engine.py",
                    performance_sensitive=False,
                    patch_truncated=False,
                )
            ],
        ):
            changed_files = review_diff._load_changed_files(config, "base", "head")

        self.assertEqual(len(changed_files), 1)
        self.assertEqual(changed_files[0].status, "R")
        self.assertEqual(changed_files[0].old_path, "src/blokus/old_engine.py")

    def test_resolve_refs_falls_back_for_partial_pull_request_payload(self) -> None:
        resolved = review_diff._resolve_refs(
            {"pull_request": {"base": {"repo": {"full_name": "owner/repo"}}}},
            "env-base",
            "env-head",
            44,
        )

        self.assertEqual(resolved, ("env-base", "env-head", 44, True))

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

    def test_mypy_parser_normalizes_absolute_paths(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/engine.py", line_start=12, line_end=12))
        analyzer = StaticAnalyzer(config)
        absolute_path = str((REPO_ROOT / "src" / "blokus" / "engine.py").resolve())
        tool_run = ToolRun(
            command="mypy src/blokus/engine.py",
            returncode=1,
            stdout=f"{absolute_path}:12: error: Incompatible return value type\n",
            stderr="",
        )

        findings = analyzer._parse_mypy(context, tool_run)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].file, "src/blokus/engine.py")

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

    def test_specialist_response_handles_invalid_embedded_json(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=20),)
        response = _parse_specialist_response(
            'Here is a draft:\n{ "findings": [ }\n```',
            "correctness",
            files,
        )

        self.assertEqual(response.findings, ())
        self.assertEqual(response.uncertain_risks, ())
        self.assertTrue(response.note)

    def test_specialist_response_skips_findings_missing_required_keys(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=20),)
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [
                        {
                            "title": "Missing evidence",
                            "severity": "high",
                            "confidence": "high",
                            "category": "correctness",
                            "file": "src/blokus/engine.py",
                            "line_start": 20,
                            "line_end": 20,
                            "impact": "Should be ignored.",
                            "suggested_action": "Ignore malformed payloads.",
                            "blocking_recommendation": True,
                        }
                    ]
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(response.findings, ())

    def test_specialist_response_normalizes_paths_and_matches_old_path(self) -> None:
        files = (
            _changed_file(
                "src/blokus/new_engine.py",
                old_path="src/blokus/old_engine.py",
                line_start=20,
                line_end=20,
            ),
        )
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [
                        {
                            "title": "Rename-aware path",
                            "severity": "high",
                            "confidence": "high",
                            "category": "correctness",
                            "file": "`./src/blokus/old_engine.py`",
                            "line_start": 20,
                            "line_end": 20,
                            "evidence": "The renamed file still has the issue.",
                            "impact": "Review should keep renamed-file findings.",
                            "suggested_action": "Map the old path to the new changed file.",
                            "blocking_recommendation": True,
                        }
                    ]
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(len(response.findings), 1)
        self.assertEqual(response.findings[0].file, "src/blokus/new_engine.py")

    def test_specialist_response_adds_uncertain_risk_for_unrecognized_path(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=20),)
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [
                        {
                            "title": "Unmatched path",
                            "severity": "moderate",
                            "confidence": "medium",
                            "category": "correctness",
                            "file": "./src/blokus/missing.py",
                            "line_start": 20,
                            "line_end": 20,
                            "evidence": "The file path does not match the diff.",
                            "impact": "The finding would otherwise disappear silently.",
                            "suggested_action": "Normalize or reconcile the path.",
                            "blocking_recommendation": False,
                        }
                    ]
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(response.findings, ())
        self.assertEqual(len(response.uncertain_risks), 1)
        self.assertIn("did not match the current diff", response.uncertain_risks[0].risk)

    def test_specialist_runner_loads_only_requested_prompt(self) -> None:
        config = _make_config(REPO_ROOT)
        provider = mock.Mock()
        provider.complete.return_value = json.dumps({"findings": [], "uncertain_risks": [], "note": ""})
        runner = SpecialistRunner(config, cast(OpenRouterClient, provider))
        context = _review_context(_changed_file("src/blokus/engine.py"))
        seen_prompts: list[str] = []

        def fake_load_prompt(config: ReviewConfig, name: str) -> str:
            del config
            seen_prompts.append(name)
            if name == "review-performance":
                raise AssertionError("Performance prompt should not be loaded for correctness-only runs.")
            return f"prompt:{name}"

        with mock.patch("blokus.review.specialists.load_prompt", side_effect=fake_load_prompt):
            response = runner.run("correctness", context, context.executable_files, "diff")

        self.assertEqual(response.findings, ())
        self.assertEqual(seen_prompts, ["review-common", "review-correctness"])

    def test_specialist_runner_reports_missing_prompt_as_uncertain_risk(self) -> None:
        config = _make_config(REPO_ROOT)
        provider = mock.Mock()
        runner = SpecialistRunner(config, cast(OpenRouterClient, provider))
        context = _review_context(_changed_file("src/blokus/engine.py"))

        def fake_load_prompt(config: ReviewConfig, name: str) -> str:
            del config
            if name == "review-tests":
                raise FileNotFoundError(name)
            return f"prompt:{name}"

        with mock.patch("blokus.review.specialists.load_prompt", side_effect=fake_load_prompt):
            response = runner.run("tests", context, context.executable_files, "diff")

        self.assertEqual(response.findings, ())
        self.assertEqual(len(response.uncertain_risks), 1)
        self.assertIn("prompt asset", response.uncertain_risks[0].risk.lower())
        provider.complete.assert_not_called()

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

    def test_specialist_response_keeps_findings_when_end_of_range_overlaps_changed_span(self) -> None:
        files = (_changed_file("src/blokus/engine.py", line_start=20, line_end=22),)
        response = _parse_specialist_response(
            json.dumps(
                {
                    "findings": [
                        {
                            "title": "Range overlap finding",
                            "severity": "moderate",
                            "confidence": "high",
                            "category": "correctness",
                            "file": "src/blokus/engine.py",
                            "line_start": 18,
                            "line_end": 21,
                            "evidence": "The reported range overlaps a changed line even though it starts earlier.",
                            "impact": "Overlap-aware filtering should keep the finding.",
                            "suggested_action": "Accept findings whose reported span intersects changed lines.",
                            "blocking_recommendation": False,
                        }
                    ]
                }
            ),
            "correctness",
            files,
        )

        self.assertEqual(len(response.findings), 1)
        self.assertEqual(response.findings[0].line_end, 21)

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

    def test_coordinator_keeps_lgtm_for_specialist_provider_billing_outages(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/engine.py", line_start=12, line_end=12))
        static_report = StaticAnalysisReport(findings=(), uncertain_risks=(), commands=("compileall",), posture="clean")
        coordinator = ReviewCoordinator(config)

        class FakeProvider:
            def complete(self, *, model: str, system_prompt: str, user_prompt: str) -> str:
                del model, system_prompt, user_prompt
                raise ProviderUnavailable("OpenRouter request failed: HTTP Error 402: Payment Required")

        with mock.patch("blokus.review.coordinator.build_review_context", return_value=context), mock.patch.object(
            coordinator.static_analyzer,
            "analyze",
            return_value=static_report,
        ), mock.patch(
            "blokus.review.coordinator.OpenRouterClient.from_env",
            return_value=cast(OpenRouterClient, FakeProvider()),
        ):
            run = coordinator.run()

        self.assertEqual(run.result.verdict, "LGTM")
        self.assertTrue(
            any(risk.risk == "Correctness specialist could not complete this run." for risk in run.result.uncertain_risks)
        )

    def test_coordinator_skips_provider_for_forked_pull_requests(self) -> None:
        config = _make_config(REPO_ROOT)
        context = _review_context(_changed_file("src/blokus/engine.py", line_start=12, line_end=12), same_repo=False)
        static_report = StaticAnalysisReport(findings=(), uncertain_risks=(), commands=("compileall",), posture="clean")
        coordinator = ReviewCoordinator(config)

        with mock.patch("blokus.review.coordinator.build_review_context", return_value=context), mock.patch.object(
            coordinator.static_analyzer,
            "analyze",
            return_value=static_report,
        ), mock.patch("blokus.review.coordinator.OpenRouterClient.from_env") as from_env:
            run = coordinator.run()

        self.assertEqual(run.result.verdict, "DISCUSS")
        self.assertEqual(len(run.result.uncertain_risks), 1)
        self.assertIn("forked `pull_request` runs", run.result.uncertain_risks[0].reason_uncertain)
        from_env.assert_not_called()

    def test_coordinator_gracefully_falls_back_when_refs_are_unavailable(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        event_payload = cast(
            dict[str, object],
            {
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
        },
        )
        schema = json.loads((REPO_ROOT / "schemas" / "agentic_review_output.schema.json").read_text(encoding="utf-8"))

        with mock.patch(
            "blokus.review.coordinator.build_review_context",
            side_effect=subprocess.CalledProcessError(128, ["git", "rev-parse", "base-sha"], stderr="fatal: bad object"),
        ), mock.patch.object(coordinator.static_analyzer, "analyze") as analyze_mock:
            run = coordinator.run(event_payload=event_payload)

        self.assertEqual(run.result.verdict, "DISCUSS")
        self.assertEqual(run.static_report.posture, "not_run")
        self.assertEqual(run.result.summary.static_analysis_posture, "not_run")
        self.assertEqual(run.result.summary.performance_posture, "not_applicable")
        self.assertEqual(run.context.pr.number, 44)
        self.assertEqual(run.context.base_ref, "base-sha")
        self.assertEqual(run.context.head_ref, "head-sha")
        self.assertEqual(run.context.branch_name, "unavailable")
        self.assertFalse(run.result.findings)
        self.assertEqual(len(run.result.uncertain_risks), 1)
        self.assertIn("refs were unavailable", run.result.uncertain_risks[0].risk)
        self.assertIn("### Uncertain Risks", run.markdown)
        self._assert_review_payload_matches_schema(run.result.to_dict(), schema)
        analyze_mock.assert_not_called()

    def test_should_run_performance_review_uses_derived_marker_path(self) -> None:
        config = _make_config(REPO_ROOT)
        patch_text = "\n".join(
            [
                "diff --git a/src/blokus/engine.py b/src/blokus/engine.py",
                "index 1111111..2222222 100644",
                "--- a/src/blokus/engine.py",
                "+++ b/src/blokus/engine.py",
                "@@ -10,3 +10,3 @@",
                " old",
                "-value = old()",
                "+value = new()",
                " done",
            ]
        )

        with mock.patch.object(
            review_diff,
            "_iter_git_patch_blocks",
            return_value=[
                review_diff._PatchBlock(
                    path="src/blokus/engine.py",
                    status="M",
                    patch=patch_text,
                    line_spans=(LineSpan(11, 11),),
                    old_path=None,
                    performance_sensitive=True,
                    patch_truncated=False,
                )
            ],
        ):
            changed_files = review_diff._load_changed_files(config, "base", "head")

        self.assertTrue(changed_files[0].performance_sensitive)
        context = _review_context(*changed_files)
        self.assertTrue(should_run_performance_review(config, context))

    def test_should_run_performance_review_uses_derived_diff_marker(self) -> None:
        config = _make_config(REPO_ROOT)
        patch_text = "\n".join(
            [
                "diff --git a/src/blokus/review/diff.py b/src/blokus/review/diff.py",
                "index 1111111..2222222 100644",
                "--- a/src/blokus/review/diff.py",
                "+++ b/src/blokus/review/diff.py",
                "@@ -10,3 +10,3 @@",
                " setup",
                "-value = old()",
                "+for item in cache:",
                " finish",
            ]
        )

        with mock.patch.object(
            review_diff,
            "_iter_git_patch_blocks",
            return_value=[
                review_diff._PatchBlock(
                    path="src/blokus/review/diff.py",
                    status="M",
                    patch=patch_text,
                    line_spans=(LineSpan(11, 11),),
                    old_path=None,
                    performance_sensitive=True,
                    patch_truncated=False,
                )
            ],
        ):
            changed_files = review_diff._load_changed_files(config, "base", "head")

        self.assertTrue(changed_files[0].performance_sensitive)
        context = _review_context(*changed_files)
        self.assertTrue(should_run_performance_review(config, context))

    def test_coordinator_reuses_precomputed_diff_bundles_for_specialists(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        context = _review_context(
            _changed_file("src/blokus/engine.py", line_start=8, line_end=8),
            _changed_file("schemas/agentic_review_output.schema.json", line_start=1, line_end=1),
        )
        captured: dict[str, tuple[tuple[str, ...], str]] = {}

        class FakeRunner:
            def run(
                self,
                specialist: str,
                context: ReviewContext,
                files: tuple[ChangedFile, ...],
                rendered_diff: str,
            ) -> SpecialistResponse:
                captured[specialist] = (tuple(changed_file.path for changed_file in files), rendered_diff)
                return SpecialistResponse(findings=(), uncertain_risks=(), note="")

        findings, uncertain_risks, truncated = coordinator._run_specialists(
            cast(SpecialistRunner, FakeRunner()),
            context,
            [],
            [],
            performance_requested=True,
        )

        self.assertEqual(findings, [])
        self.assertEqual(uncertain_risks, [])
        self.assertEqual(set(captured), {"correctness", "tests", "performance"})
        self.assertFalse(truncated)
        self.assertIs(captured["correctness"][1], captured["performance"][1])
        self.assertEqual(captured["tests"][1], context.raw_diff)
        self.assertIn("src/blokus/engine.py", captured["correctness"][1])
        self.assertNotIn("schemas/agentic_review_output.schema.json", captured["correctness"][1])
        self.assertIn("schemas/agentic_review_output.schema.json", captured["tests"][1])

    def test_coordinator_runs_specialists_concurrently(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        context = _review_context(
            _changed_file("src/blokus/engine.py", line_start=8, line_end=8),
            _changed_file("schemas/agentic_review_output.schema.json", line_start=1, line_end=1),
        )
        expected = 3
        started: set[str] = set()
        started_lock = threading.Lock()
        all_started = threading.Event()

        class FakeRunner:
            def run(
                self,
                specialist: str,
                context: ReviewContext,
                files: tuple[ChangedFile, ...],
                rendered_diff: str,
            ) -> SpecialistResponse:
                with started_lock:
                    started.add(specialist)
                    if len(started) == expected:
                        all_started.set()
                if not all_started.wait(0.5):
                    raise AssertionError("Specialists did not start concurrently.")
                return SpecialistResponse(findings=(), uncertain_risks=(), note="")

        findings, uncertain_risks, truncated = coordinator._run_specialists(
            cast(SpecialistRunner, FakeRunner()),
            context,
            [],
            [],
            performance_requested=True,
        )

        self.assertEqual(findings, [])
        self.assertEqual(uncertain_risks, [])
        self.assertFalse(truncated)
        self.assertEqual(started, {"correctness", "tests", "performance"})

    def test_coordinator_adds_uncertain_risk_when_prompt_context_is_truncated(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        changed_files = tuple(
            _changed_file(f"src/blokus/module_{index}.py", line_start=1, line_end=1)
            for index in range(100)
        )
        context = _review_context(*changed_files, raw_diff="", commits=tuple(f"commit {i}" for i in range(30)))

        class FakeRunner:
            def run(
                self,
                specialist: str,
                context: ReviewContext,
                files: tuple[ChangedFile, ...],
                rendered_diff: str,
            ) -> SpecialistResponse:
                return SpecialistResponse(findings=(), uncertain_risks=(), note="")

        findings, uncertain_risks, truncated = coordinator._run_specialists(
            cast(SpecialistRunner, FakeRunner()),
            context,
            [],
            [],
            performance_requested=False,
        )

        self.assertEqual(findings, [])
        self.assertFalse(truncated)
        self.assertTrue(
            any(risk.risk == "Commit or file-list context was truncated for scale." for risk in uncertain_risks)
        )

    def test_coordinator_renders_each_patch_block_once_for_cached_bundles(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        context = _review_context(
            _changed_file("src/blokus/engine.py", line_start=8, line_end=8),
            _changed_file("schemas/agentic_review_output.schema.json", line_start=1, line_end=1),
            raw_diff="",
        )

        class FakeRunner:
            def run(
                self,
                specialist: str,
                context: ReviewContext,
                files: tuple[ChangedFile, ...],
                rendered_diff: str,
            ) -> SpecialistResponse:
                return SpecialistResponse(findings=(), uncertain_risks=(), note="")

        with mock.patch(
            "blokus.review.coordinator._render_patch_block",
            side_effect=lambda changed_file: (f"File: {changed_file.path}\n```diff\n{changed_file.patch.strip()}\n```", False),
        ) as render_patch_block:
            coordinator._run_specialists(
                cast(SpecialistRunner, FakeRunner()),
                context,
                [],
                [],
                performance_requested=True,
            )

        self.assertEqual(render_patch_block.call_count, 2)

    def test_coordinator_renders_only_needed_patch_blocks_when_bundle_truncates(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        changed_files = tuple(
            _changed_file(
                f"src/blokus/module_{index}.py",
                line_start=1,
                line_end=1,
                patch="@@ -1,1 +1,1 @@\n-change\n+change\n",
            )
            for index in range(30)
        )
        context = _review_context(*changed_files, raw_diff="")

        class FakeRunner:
            def run(
                self,
                specialist: str,
                context: ReviewContext,
                files: tuple[ChangedFile, ...],
                rendered_diff: str,
            ) -> SpecialistResponse:
                return SpecialistResponse(findings=(), uncertain_risks=(), note="")

        oversized_block = "File: demo.py\n```diff\n" + ("x" * 15_000) + "\n```"
        with mock.patch(
            "blokus.review.coordinator._render_patch_block",
            return_value=(oversized_block, False),
        ) as render_patch_block:
            findings, uncertain_risks, truncated = coordinator._run_specialists(
                cast(SpecialistRunner, FakeRunner()),
                context,
                [],
                [],
                performance_requested=False,
            )

        self.assertEqual(findings, [])
        self.assertEqual(uncertain_risks, [])
        self.assertTrue(truncated)
        self.assertLess(render_patch_block.call_count, len(changed_files))

    def test_coordinator_bounds_rendered_diff_bundles_for_specialists(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        huge_patch = "\n".join(
            [
                "diff --git a/src/blokus/engine.py b/src/blokus/engine.py",
                "index 1111111..2222222 100644",
                "--- a/src/blokus/engine.py",
                "+++ b/src/blokus/engine.py",
                "@@ -1,1 +1,1400 @@",
                *["+value = cache_lookup(item)" for _ in range(1400)],
            ]
        )
        context = _review_context(
            _changed_file(
                "src/blokus/engine.py",
                line_start=1,
                line_end=1400,
                patch=huge_patch,
            ),
            raw_diff="",
        )
        captured: list[str] = []

        class FakeRunner:
            def run(
                self,
                specialist: str,
                context: ReviewContext,
                files: tuple[ChangedFile, ...],
                rendered_diff: str,
            ) -> SpecialistResponse:
                captured.append(rendered_diff)
                return SpecialistResponse(findings=(), uncertain_risks=(), note="")

        findings, uncertain_risks, truncated = coordinator._run_specialists(
            cast(SpecialistRunner, FakeRunner()),
            context,
            [],
            [],
            performance_requested=True,
        )

        self.assertEqual(findings, [])
        self.assertEqual(uncertain_risks, [])
        self.assertTrue(truncated)
        self.assertTrue(captured)
        self.assertTrue(all(len(bundle) <= review_coordinator.MAX_RENDERED_DIFF_CHARS for bundle in captured))
        self.assertTrue(any("truncated for scale" in bundle for bundle in captured))

    def test_coordinator_filters_findings_with_invalid_category(self) -> None:
        coordinator = ReviewCoordinator(_make_config(REPO_ROOT))
        invalid = Finding(
            id="invalid-category",
            title="Bad enum",
            severity="high",
            confidence="high",
            category="test",
            file="src/blokus/engine.py",
            line_start=4,
            line_end=4,
            evidence="Schema-unsafe category.",
            impact="Would violate the published review schema.",
            suggested_action="Use a supported category enum.",
            blocking_recommendation=True,
        )

        self.assertEqual(coordinator._dedupe_and_limit([invalid]), [])

    def test_coordinator_dedupes_invalid_and_lower_ranked_findings(self) -> None:
        coordinator = ReviewCoordinator(_make_config(REPO_ROOT))
        duplicate_lower = Finding(
            id="dup-low",
            title="Duplicate",
            severity="moderate",
            confidence="medium",
            category="correctness",
            file="src/blokus/engine.py",
            line_start=12,
            line_end=12,
            evidence="Lower-ranked duplicate.",
            impact="Less serious.",
            suggested_action="Minor change.",
            blocking_recommendation=False,
        )
        duplicate_higher = Finding(
            id="dup-high",
            title="Duplicate",
            severity="high",
            confidence="high",
            category="correctness",
            file="src/blokus/engine.py",
            line_start=12,
            line_end=12,
            evidence="Higher-ranked duplicate.",
            impact="More serious.",
            suggested_action="Critical change.",
            blocking_recommendation=True,
        )
        invalid = Finding(
            id="invalid",
            title="",
            severity="high",
            confidence="high",
            category="correctness",
            file="src/blokus/engine.py",
            line_start=0,
            line_end=0,
            evidence="",
            impact="",
            suggested_action="",
            blocking_recommendation=True,
        )

        deduped = coordinator._dedupe_and_limit([duplicate_lower, duplicate_higher, invalid])

        self.assertEqual(deduped, [duplicate_higher])

    def test_coordinator_limits_findings_to_configured_maximum(self) -> None:
        config = replace(_make_config(REPO_ROOT), max_findings=1)
        coordinator = ReviewCoordinator(config)
        findings = [
            Finding(
                id="finding-1",
                title="First",
                severity="high",
                confidence="high",
                category="correctness",
                file="src/blokus/engine.py",
                line_start=10,
                line_end=10,
                evidence="More severe.",
                impact="Higher priority.",
                suggested_action="Fix first.",
                blocking_recommendation=True,
            ),
            Finding(
                id="finding-2",
                title="Second",
                severity="moderate",
                confidence="medium",
                category="tests",
                file="tests/test_engine.py",
                line_start=5,
                line_end=5,
                evidence="Less severe.",
                impact="Lower priority.",
                suggested_action="Fix later.",
                blocking_recommendation=False,
            ),
        ]

        limited = coordinator._dedupe_and_limit(findings)

        self.assertEqual(limited, [findings[0]])

    def test_script_resolve_repo_root_is_independent_of_cwd(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.dict(
                os.environ,
                {},
                clear=True,
        ):
            original_cwd = Path.cwd()
            try:
                os.chdir(tmpdir)

                self.assertEqual(agentic_code_review._resolve_repo_root(), REPO_ROOT)
            finally:
                os.chdir(original_cwd)

    def test_script_resolve_repo_root_prefers_github_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.dict(
                os.environ,
                {"GITHUB_WORKSPACE": tmpdir},
                clear=True,
        ):
            self.assertEqual(agentic_code_review._resolve_repo_root(), Path(tmpdir).resolve())

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

    def test_script_main_uses_environment_overrides_and_discuss_exits_nonzero(self) -> None:
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

            self.assertEqual(exit_code, 1)
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
        self.assertIn(
            payload["verdict"],
            cast(list[str], cast(dict[str, object], cast(dict[str, object], schema["properties"])["verdict"])["enum"]),
        )

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
            finding_properties = cast(dict[str, object], finding_schema["properties"])
            for finding in findings_payload:
                self.assertEqual(set(finding.keys()), set(cast(list[str], finding_schema["required"])))
                self.assertIn(
                    finding["severity"],
                    cast(list[str], cast(dict[str, object], finding_properties["severity"])["enum"]),
                )
                self.assertIn(
                    finding["confidence"],
                    cast(list[str], cast(dict[str, object], finding_properties["confidence"])["enum"]),
                )
                self.assertIn(
                    finding["category"],
                    cast(list[str], cast(dict[str, object], finding_properties["category"])["enum"]),
                )
                self.assertGreaterEqual(cast(int, finding["line_start"]), 1)
                self.assertGreaterEqual(
                    cast(int, finding["line_end"]),
                    cast(int, finding["line_start"]),
                )

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

    def test_static_analyzer_uses_larger_python_batches(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(*[_changed_file(f"src/module_{index}.py") for index in range(250)])
        commands: list[list[str]] = []

        def fake_run(args: list[str]) -> ToolRun:
            commands.append(args)
            if args[0] == "/ruff":
                return ToolRun(command=" ".join(args), returncode=0, stdout="[]", stderr="")
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(
            analyzer,
            "_discover_tool",
            side_effect=lambda name: f"/{name}",
        ), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            report = analyzer.analyze(context)

        compileall_commands = [command for command in report.commands if "compileall" in command]
        ruff_commands = [command for command in report.commands if command.startswith("/ruff check")]
        mypy_commands = [command for command in report.commands if command.startswith("/mypy ")]
        self.assertEqual(len(compileall_commands), 1)
        self.assertEqual(len(ruff_commands), 1)
        self.assertEqual(len(mypy_commands), 1)
        self.assertEqual(len(commands), 3)

    def test_static_analyzer_skips_ruff_and_mypy_for_very_large_python_change_sets(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(*[_changed_file(f"src/module_{index}.py") for index in range(401)])
        commands: list[list[str]] = []

        def fake_run(args: list[str]) -> ToolRun:
            commands.append(args)
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(
            analyzer,
            "_discover_tool",
            side_effect=lambda name: f"/{name}",
        ), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            report = analyzer.analyze(context)

        self.assertEqual(len(commands), 1)
        self.assertIn("compileall", report.commands[0])
        self.assertFalse(any(args[0] == "/ruff" for args in commands))
        self.assertFalse(any(args[0] == "/mypy" for args in commands))
        self.assertTrue(
            any(risk.risk == "Expensive Python static analysis was skipped for a very large change set." for risk in report.uncertain_risks)
        )
        self.assertIn(report.posture, {"issues_found", "unavailable"})

    def test_static_analyzer_builds_single_mypy_response_file_when_batches_would_split(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        changed_files = [_changed_file(f"src/module_{index}.py") for index in range(1201)]
        response_file = ""

        mypy_commands, cleanup_paths = analyzer._build_mypy_commands("/mypy", changed_files)

        try:
            self.assertEqual(len(mypy_commands), 1)
            self.assertTrue(any(argument.startswith("@") for argument in mypy_commands[0][1:]))
            response_file = next(argument[1:] for argument in mypy_commands[0][1:] if argument.startswith("@"))
            self.assertTrue(Path(response_file).exists())
        finally:
            for cleanup_path in cleanup_paths:
                cleanup_path.unlink(missing_ok=True)

        self.assertFalse(Path(response_file).exists())

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

        self.assertEqual(invocations, [["bash", "-n", "--", "scripts/check.sh"]])

    def test_static_analyzer_uses_larger_shell_batches(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(*[_changed_file(f"scripts/check_{index}.sh") for index in range(250)])

        def fake_run(args: list[str]) -> ToolRun:
            if args[0] == "/shellcheck":
                return ToolRun(command=" ".join(args), returncode=0, stdout='{"comments": []}', stderr="")
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(
            analyzer,
            "_discover_tool",
            side_effect=lambda name: "/shellcheck" if name == "shellcheck" else None,
        ), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            report = analyzer.analyze(context)

        bash_commands = [command for command in report.commands if command.startswith("bash -n ")]
        shellcheck_commands = [command for command in report.commands if command.startswith("/shellcheck -f json1")]
        self.assertEqual(len(bash_commands), 1)
        self.assertEqual(len(shellcheck_commands), 1)

    def test_static_analyzer_uses_option_terminators_and_safe_paths(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(_changed_file("-odd.py"), _changed_file("-check.sh"))
        commands: list[list[str]] = []

        def fake_run(args: list[str]) -> ToolRun:
            commands.append(args)
            if args[0] == "/ruff":
                return ToolRun(command=" ".join(args), returncode=0, stdout="[]", stderr="")
            if args[0] == "/shellcheck":
                return ToolRun(command=" ".join(args), returncode=0, stdout='{"comments": []}', stderr="")
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(
            analyzer,
            "_discover_tool",
            side_effect=lambda name: f"/{name}",
        ), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            analyzer.analyze(context)

        self.assertEqual(commands[0], [sys.executable, "-m", "compileall", "./-odd.py"])
        self.assertEqual(commands[1], ["/ruff", "check", "--output-format", "json", "--", "./-odd.py"])
        self.assertEqual(
            commands[2],
            [
                "/mypy",
                "--config-file",
                str(config.repo_root / "pyproject.toml"),
                "--show-column-numbers",
                "--hide-error-context",
                "--no-error-summary",
                "--",
                "./-odd.py",
            ],
        )
        self.assertEqual(commands[3], ["bash", "-n", "--", "./-check.sh"])
        self.assertEqual(commands[4], ["/shellcheck", "-f", "json1", "--", "./-check.sh"])

    def test_static_analyzer_marks_ruff_json_parse_failures_as_uncertain(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(_changed_file("sandbox/demo.py"))

        def fake_run(args: list[str]) -> ToolRun:
            if args[0] == "/ruff":
                return ToolRun(command=" ".join(args), returncode=1, stdout="{invalid", stderr="")
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(
            analyzer,
            "_discover_tool",
            side_effect=lambda name: f"/{name}",
        ), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            report = analyzer.analyze(context)

        self.assertEqual(report.posture, "unavailable")
        self.assertTrue(any(risk.risk == "Ruff output could not be parsed as JSON." for risk in report.uncertain_risks))

    def test_static_analyzer_bounds_large_ruff_json_output(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(_changed_file("sandbox/demo.py"))

        def fake_run(args: list[str]) -> ToolRun:
            if args[0] == "/ruff":
                return ToolRun(
                    command=" ".join(args),
                    returncode=1,
                    stdout="[" + (" " * (1_000_001)),
                    stderr="",
                )
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(
            analyzer,
            "_discover_tool",
            side_effect=lambda name: f"/{name}",
        ), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            report = analyzer.analyze(context)

        self.assertEqual(report.posture, "unavailable")
        self.assertTrue(
            any(risk.risk == "Ruff output exceeded the safe JSON parsing limit." for risk in report.uncertain_risks)
        )

    def test_static_analyzer_marks_shellcheck_json_parse_failures_as_uncertain(self) -> None:
        config = _make_config(REPO_ROOT)
        analyzer = StaticAnalyzer(config)
        context = _review_context(_changed_file("scripts/check.sh"))

        def fake_run(args: list[str]) -> ToolRun:
            if args[0] == "/shellcheck":
                return ToolRun(command=" ".join(args), returncode=1, stdout="{invalid", stderr="")
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch.object(
            analyzer,
            "_discover_tool",
            side_effect=lambda name: "/shellcheck" if name == "shellcheck" else None,
        ), mock.patch.object(
            analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            report = analyzer.analyze(context)

        self.assertEqual(report.posture, "unavailable")
        self.assertTrue(
            any(risk.risk == "ShellCheck output could not be parsed as JSON." for risk in report.uncertain_risks)
        )

    def test_coordinator_keeps_review_context_when_ruff_json_is_invalid(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        context = _review_context(
            _changed_file("sandbox/demo.py", line_start=12, line_end=12),
            same_repo=False,
            raw_diff="",
        )

        def fake_run(args: list[str]) -> ToolRun:
            if args[0] == sys.executable:
                return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")
            if args[0] == "/ruff":
                return ToolRun(command=" ".join(args), returncode=1, stdout="{invalid", stderr="")
            return ToolRun(command=" ".join(args), returncode=0, stdout="", stderr="")

        with mock.patch("blokus.review.coordinator.build_review_context", return_value=context), mock.patch.object(
            coordinator.static_analyzer,
            "_discover_tool",
            side_effect=lambda name: f"/{name}",
        ), mock.patch.object(
            coordinator.static_analyzer,
            "_run_command",
            side_effect=fake_run,
        ):
            run = coordinator.run()

        self.assertEqual(run.context.base_ref, "origin/main")
        self.assertEqual(run.static_report.posture, "unavailable")
        self.assertTrue(
            any(risk.risk == "Ruff output could not be parsed as JSON." for risk in run.result.uncertain_risks)
        )
        self.assertFalse(any("refs were unavailable" in risk.risk for risk in run.result.uncertain_risks))

    def test_coordinator_adds_uncertain_risk_when_diff_context_is_truncated(self) -> None:
        config = _make_config(REPO_ROOT)
        coordinator = ReviewCoordinator(config)
        huge_patch = "\n".join(
            [
                "diff --git a/src/blokus/engine.py b/src/blokus/engine.py",
                "index 1111111..2222222 100644",
                "--- a/src/blokus/engine.py",
                "+++ b/src/blokus/engine.py",
                "@@ -1,1 +1,1600 @@",
                *["+value = cache_lookup(item)" for _ in range(1600)],
            ]
        )
        context = _review_context(
            _changed_file(
                "src/blokus/engine.py",
                line_start=1,
                line_end=1600,
                patch=huge_patch,
            ),
            raw_diff="",
        )
        static_report = StaticAnalysisReport(findings=(), uncertain_risks=(), commands=("compileall",), posture="clean")

        class FakeProvider:
            def complete(self, *, model: str, system_prompt: str, user_prompt: str) -> str:
                return json.dumps({"findings": [], "uncertain_risks": [], "note": ""})

        with mock.patch("blokus.review.coordinator.build_review_context", return_value=context), mock.patch.object(
            coordinator.static_analyzer,
            "analyze",
            return_value=static_report,
        ), mock.patch(
            "blokus.review.coordinator.OpenRouterClient.from_env",
            return_value=FakeProvider(),
        ):
            run = coordinator.run()

        self.assertEqual(run.result.verdict, "LGTM")
        self.assertTrue(
            any(risk.risk == "Diff context was truncated for scale." for risk in run.result.uncertain_risks)
        )

    def test_verdict_ignores_dependency_metadata_uncertainty(self) -> None:
        coordinator = ReviewCoordinator(_make_config(REPO_ROOT))
        verdict = coordinator._build_verdict(
            [],
            [
                UncertainRisk(
                    risk="Dependency-related files changed in this PR.",
                    reason_uncertain="The diff includes dependency metadata, but static analysis cannot confirm the runtime or supply-chain intent from changed code alone.",
                    suggested_verification="Review dependency intent.",
                )
            ],
        )

        self.assertEqual(verdict, "LGTM")

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

        with mock.patch("blokus.review.provider._sleep_before_retry") as sleep_mock, mock.patch(
            "blokus.review.provider.urlopen",
            side_effect=[URLError("temporary failure"), URLError("temporary failure"), response],
        ) as urlopen_mock:
            result = client.complete(model="gpt", system_prompt="sys", user_prompt="user")

        self.assertEqual(result, "LGTM")
        self.assertEqual(urlopen_mock.call_count, 3)
        sleep_mock.assert_has_calls([mock.call(1), mock.call(2)])

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

    def test_openrouter_client_retries_retryable_http_errors(self) -> None:
        client = OpenRouterClient(
            api_key="token",
            base_url="https://openrouter.example",
            timeout_seconds=30,
            max_retries=2,
        )
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "LGTM"}}]}
        ).encode("utf-8")
        retryable_error = HTTPError(
            "https://openrouter.example/chat/completions",
            429,
            "rate limited",
            hdrs=Message(),
            fp=None,
        )

        with mock.patch("blokus.review.provider._sleep_before_retry") as sleep_mock, mock.patch(
            "blokus.review.provider.urlopen",
            side_effect=[retryable_error, response],
        ) as urlopen_mock:
            result = client.complete(model="gpt", system_prompt="sys", user_prompt="user")

        self.assertEqual(result, "LGTM")
        self.assertEqual(urlopen_mock.call_count, 2)
        sleep_mock.assert_called_once_with(1)

    def test_openrouter_client_does_not_retry_nonretryable_http_errors(self) -> None:
        client = OpenRouterClient(
            api_key="token",
            base_url="https://openrouter.example",
            timeout_seconds=30,
            max_retries=2,
        )
        auth_error = HTTPError(
            "https://openrouter.example/chat/completions",
            401,
            "unauthorized",
            hdrs=Message(),
            fp=None,
        )

        with mock.patch("blokus.review.provider._sleep_before_retry") as sleep_mock, mock.patch(
            "blokus.review.provider.urlopen",
            side_effect=[auth_error],
        ) as urlopen_mock:
            with self.assertRaisesRegex(ProviderUnavailable, "OpenRouter request failed"):
                client.complete(model="gpt", system_prompt="sys", user_prompt="user")

        self.assertEqual(urlopen_mock.call_count, 1)
        sleep_mock.assert_not_called()

    def test_openrouter_client_retries_invalid_json_response(self) -> None:
        client = OpenRouterClient(
            api_key="token",
            base_url="https://openrouter.example",
            timeout_seconds=30,
            max_retries=2,
        )
        invalid_response = mock.MagicMock()
        invalid_response.__enter__.return_value.read.return_value = b"{not-json"
        valid_response = mock.MagicMock()
        valid_response.__enter__.return_value.read.return_value = json.dumps(
            {"choices": [{"message": {"content": "LGTM"}}]}
        ).encode("utf-8")

        with mock.patch("blokus.review.provider._sleep_before_retry") as sleep_mock, mock.patch(
            "blokus.review.provider.urlopen",
            side_effect=[invalid_response, valid_response],
        ) as urlopen_mock:
            result = client.complete(model="gpt", system_prompt="sys", user_prompt="user")

        self.assertEqual(result, "LGTM")
        self.assertEqual(urlopen_mock.call_count, 2)
        sleep_mock.assert_called_once_with(1)

    def test_openrouter_client_rejects_negative_retry_budget(self) -> None:
        client = OpenRouterClient(
            api_key="token",
            base_url="https://openrouter.example",
            timeout_seconds=30,
            max_retries=-1,
        )

        with self.assertRaisesRegex(ProviderUnavailable, "max_retries"):
            client.complete(model="gpt", system_prompt="sys", user_prompt="user")

    def test_diff_module_imports_cleanly_in_subprocess(self) -> None:
        result = subprocess.run(
            [sys.executable, "-c", "import blokus.review.diff"],
            cwd=REPO_ROOT,
            env={**os.environ, "PYTHONPATH": "src"},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr)

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
