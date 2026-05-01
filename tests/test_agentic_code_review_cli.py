import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from blokus.review.config import HeuristicConfig, PerformanceConfig, ProviderConfig, ReviewConfig
from blokus.review.coordinator import ReviewRun
from blokus.review.static_analyzer import StaticAnalysisReport
from blokus.review.types import ChangedFile, LineSpan, ReviewContext, ReviewPayload, ReviewResult, ReviewSummary, UncertainRisk


REPO_ROOT = Path(__file__).resolve().parents[1]
import scripts.github.agentic_code_review as agentic_code_review  # noqa: E402


def _make_config() -> ReviewConfig:
    return ReviewConfig(
        repo_root=REPO_ROOT,
        max_findings=5,
        excluded_globs=("*.md", "*.ai", "*.svg", "*.png", "*.xlsx", "*.pdf"),
        blocking_severities=("critical", "high"),
        prompt_dir=REPO_ROOT / ".github" / "prompts",
        spec_path=REPO_ROOT / "docs" / "agentic-review" / "spec.md",
        schema_path=REPO_ROOT / "schemas" / "agentic_review_output.schema.json",
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


def _make_run(*, same_repo: bool, verdict: str) -> ReviewRun:
    changed_file = ChangedFile(
        path="src/blokus/review/diff.py",
        status="M",
        patch="@@ -1,1 +1,1 @@\n-change\n+change\n",
        line_spans=(LineSpan(1, 1),),
        executable=True,
        categories=("python",),
    )
    context = ReviewContext(
        pr=ReviewPayload(number=44, head_sha="headsha", base_sha="basesha"),
        base_ref="origin/main",
        head_ref="HEAD",
        branch_name="feature/fix-review",
        commits=("fix issue",),
        changed_files=(changed_file,),
        impact="moderate",
        bias_risks=("misleading-task-bias",),
        same_repo=same_repo,
        executable_files=(changed_file,),
        raw_diff="File: src/blokus/review/diff.py\n```diff\n@@ -1,1 +1,1 @@\n-change\n+change\n```",
    )
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
            ()
            if verdict == "LGTM"
            else (
                UncertainRisk(
                    risk="Provider unavailable.",
                    reason_uncertain="Missing OPENROUTER_API_KEY.",
                    suggested_verification="Rerun with provider credentials.",
                ),
            )
        ),
        verdict=verdict,
    )
    return ReviewRun(
        context=context,
        result=result,
        markdown=f"## Agentic Code Review\n\n### Verdict\n- `{verdict}`\n",
        static_report=StaticAnalysisReport(findings=(), uncertain_risks=(), commands=(), posture="clean"),
    )


class AgenticCodeReviewCliTests(unittest.TestCase):
    def test_lazy_imports_bootstrap_runtime_dependencies(self) -> None:
        repo_root = str(REPO_ROOT)
        src_root = str(REPO_ROOT / "src")
        trimmed_sys_path = [entry for entry in sys.path if entry not in {repo_root, src_root}]

        with mock.patch.multiple(
            agentic_code_review,
            load_review_config=None,
            ReviewCoordinator=None,
            GitHubClient=None,
            load_event_payload=None,
            COMMENT_MARKERS=None,
        ), mock.patch.object(sys, "path", list(trimmed_sys_path)):
            agentic_code_review._lazy_imports()

            self.assertIsNotNone(agentic_code_review.load_review_config)
            self.assertIsNotNone(agentic_code_review.ReviewCoordinator)
            self.assertIsNotNone(agentic_code_review.GitHubClient)
            self.assertIsNotNone(agentic_code_review.load_event_payload)
            self.assertIsNotNone(agentic_code_review.COMMENT_MARKERS)
            self.assertIn(repo_root, sys.path)
            self.assertIn(src_root, sys.path)

    def test_main_loads_event_payload_and_forwards_it_to_coordinator(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="LGTM")
        event_payload = {
            "pull_request": {
                "number": 44,
                "base": {"sha": "base-sha", "repo": {"full_name": "owner/repo"}},
                "head": {"sha": "head-sha", "repo": {"full_name": "fork/repo"}},
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
            "load_event_payload",
            return_value=event_payload,
        ) as load_event_payload, mock.patch.dict(
            os.environ,
            {"GITHUB_EVENT_PATH": str(Path(tmpdir) / "event.json")},
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
            Path(tmpdir, "event.json").write_text("{}", encoding="utf-8")
            coordinator_cls.return_value.run.return_value = run

            exit_code = agentic_code_review.main()

            self.assertEqual(exit_code, 0)
            load_event_payload.assert_called_once_with(str(Path(tmpdir) / "event.json"))
            self.assertIs(
                coordinator_cls.return_value.run.call_args.kwargs["event_payload"],
                event_payload,
            )

    def test_main_ignores_non_file_event_paths(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="LGTM")

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            agentic_code_review,
            "load_review_config",
            return_value=config,
        ), mock.patch.object(
            agentic_code_review,
            "ReviewCoordinator",
        ) as coordinator_cls, mock.patch.object(
            agentic_code_review,
            "load_event_payload",
        ) as load_event_payload, mock.patch.dict(
            os.environ,
            {"GITHUB_EVENT_PATH": tmpdir},
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
            load_event_payload.assert_not_called()
            self.assertIsNone(coordinator_cls.return_value.run.call_args.kwargs["event_payload"])

    def test_main_continues_when_event_payload_cannot_be_loaded(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="LGTM")

        with tempfile.TemporaryDirectory() as tmpdir, mock.patch.object(
            agentic_code_review,
            "load_review_config",
            return_value=config,
        ), mock.patch.object(
            agentic_code_review,
            "ReviewCoordinator",
        ) as coordinator_cls, mock.patch.object(
            agentic_code_review,
            "load_event_payload",
            side_effect=ValueError("bad payload"),
        ) as load_event_payload, mock.patch.dict(
            os.environ,
            {"GITHUB_EVENT_PATH": str(Path(tmpdir) / "event.json")},
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
            Path(tmpdir, "event.json").write_text("{}", encoding="utf-8")
            coordinator_cls.return_value.run.return_value = run

            exit_code = agentic_code_review.main()

            self.assertEqual(exit_code, 0)
            load_event_payload.assert_called_once_with(str(Path(tmpdir) / "event.json"))
            self.assertIsNone(coordinator_cls.return_value.run.call_args.kwargs["event_payload"])

    def test_main_writes_artifacts_and_posts_same_repo_comment(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=True, verdict="LGTM")

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
                json.loads((Path(tmpdir) / "review.json").read_text(encoding="utf-8"))["summary"]["overall_risk"],
                "moderate",
            )
            self.assertEqual(
                json.loads((Path(tmpdir) / "review.json").read_text(encoding="utf-8"))["verdict"],
                "LGTM",
            )
            self.assertIn("`LGTM`", (Path(tmpdir) / "review.md").read_text(encoding="utf-8"))
            client_cls.return_value.upsert_issue_comment.assert_called_once_with(
                run.context.pr.number,
                "agentic-code-review",
                run.markdown,
            )

    def test_main_fails_non_lgtm_and_skips_comment_for_forks(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="DISCUSS")

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
            {"GITHUB_EVENT_PATH": ""},
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
            client_cls.assert_not_called()

    def test_main_uses_default_artifact_paths(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="LGTM")
        original_cwd = Path.cwd()

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
                "GITHUB_WORKSPACE": tmpdir,
                "GITHUB_EVENT_PATH": "",
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            ["agentic_code_review.py"],
        ):
            coordinator_cls.return_value.run.return_value = run
            try:
                os.chdir(tmpdir)
                exit_code = agentic_code_review.main()
            finally:
                os.chdir(original_cwd)

            self.assertEqual(exit_code, 0)
            artifact_dir = Path(tmpdir) / "artifacts" / "agentic-review"
            self.assertTrue((artifact_dir / "review.json").exists())
            self.assertTrue((artifact_dir / "review.md").exists())
            payload = json.loads((artifact_dir / "review.json").read_text(encoding="utf-8"))
            self.assertIn("summary", payload)
            self.assertIn("findings", payload)
            self.assertEqual(payload["verdict"], "LGTM")
            self.assertIn("`LGTM`", (artifact_dir / "review.md").read_text(encoding="utf-8"))

    def test_main_prefers_explicit_cli_pr_number_over_environment(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="LGTM")

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
                "GITHUB_EVENT_PATH": "",
                "REVIEW_PULL_NUMBER": "44",
                "REVIEW_BASE_REF": "env-base",
                "REVIEW_HEAD_REF": "env-head",
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            [
                "agentic_code_review.py",
                "--pr-number",
                "0",
                "--base-ref",
                "",
                "--head-ref",
                "",
                "--json-out",
                str(Path(tmpdir) / "review.json"),
                "--markdown-out",
                str(Path(tmpdir) / "review.md"),
            ],
        ):
            coordinator_cls.return_value.run.return_value = run

            exit_code = agentic_code_review.main()

            self.assertEqual(exit_code, 0)
            self.assertEqual(coordinator_cls.return_value.run.call_args.kwargs["pr_number"], 0)
            self.assertEqual(coordinator_cls.return_value.run.call_args.kwargs["base_ref"], "")
            self.assertEqual(coordinator_cls.return_value.run.call_args.kwargs["head_ref"], "")

    def test_main_uses_environment_ref_fallbacks_when_cli_overrides_are_absent(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="LGTM")

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
                "GITHUB_EVENT_PATH": "",
                "REVIEW_PULL_NUMBER": "44",
                "REVIEW_BASE_REF": "env-base",
                "REVIEW_HEAD_REF": "env-head",
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
            self.assertEqual(coordinator_cls.return_value.run.call_args.kwargs["pr_number"], 44)
            self.assertEqual(coordinator_cls.return_value.run.call_args.kwargs["base_ref"], "env-base")
            self.assertEqual(coordinator_cls.return_value.run.call_args.kwargs["head_ref"], "env-head")

    def test_main_forwards_invalid_environment_pr_number_as_none(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="LGTM")

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
                "GITHUB_EVENT_PATH": "",
                "REVIEW_PULL_NUMBER": "not-a-number",
                "REVIEW_BASE_REF": "env-base",
                "REVIEW_HEAD_REF": "env-head",
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
            self.assertIsNone(coordinator_cls.return_value.run.call_args.kwargs["pr_number"])
            self.assertEqual(coordinator_cls.return_value.run.call_args.kwargs["base_ref"], "env-base")
            self.assertEqual(coordinator_cls.return_value.run.call_args.kwargs["head_ref"], "env-head")

    def test_main_resolves_relative_artifact_paths_from_workspace_root(self) -> None:
        config = _make_config()
        run = _make_run(same_repo=False, verdict="LGTM")
        original_cwd = Path.cwd()

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
                "GITHUB_WORKSPACE": tmpdir,
                "GITHUB_EVENT_PATH": "",
            },
            clear=False,
        ), mock.patch.object(
            sys,
            "argv",
            [
                "agentic_code_review.py",
                "--json-out",
                "custom/review.json",
                "--markdown-out",
                "custom/review.md",
            ],
        ):
            coordinator_cls.return_value.run.return_value = run
            nested_cwd = Path(tmpdir) / "nested" / "workdir"
            nested_cwd.mkdir(parents=True, exist_ok=True)
            try:
                os.chdir(nested_cwd)
                exit_code = agentic_code_review.main()
            finally:
                os.chdir(original_cwd)

            self.assertEqual(exit_code, 0)
            self.assertTrue((Path(tmpdir) / "custom" / "review.json").exists())
            self.assertTrue((Path(tmpdir) / "custom" / "review.md").exists())
            self.assertFalse((nested_cwd / "custom" / "review.json").exists())

    def test_module_entrypoint_imports_cleanly_from_repo_root(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "scripts.github.agentic_code_review", "--help"],
            cwd=REPO_ROOT,
            env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Path for the markdown review output", result.stdout)

    def test_script_entrypoint_imports_cleanly_without_pythonpath(self) -> None:
        result = subprocess.run(
            [sys.executable, "scripts/github/agentic_code_review.py", "--help"],
            cwd=REPO_ROOT,
            env={key: value for key, value in os.environ.items() if key != "PYTHONPATH"},
            capture_output=True,
            text=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("Path for the machine-readable review output", result.stdout)


if __name__ == "__main__":
    unittest.main()
