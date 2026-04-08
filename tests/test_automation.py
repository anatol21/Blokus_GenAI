import unittest

from blokus.automation import (
    build_agent_branch_name,
    classify_failure_category,
    infer_domains_from_paths,
    parse_state_marker,
    repair_allowed,
    render_state_marker,
    tests_missing,
    triage_issue,
)


class AutomationTests(unittest.TestCase):
    def test_triage_marks_structured_issue_as_agent_ready(self) -> None:
        issue_body = """
### Problem statement
Implement a safer CLI summary.

### Acceptance criteria
- Command output is deterministic.

### Why this is suitable for autonomous implementation
- The change is local to the CLI and tests.

### Files likely affected
- src/blokus/cli.py
- tests/test_cli.py

### Required tests
- Update CLI tests.

### Context bundle
- docs/requirements.md
- tests/test_cli.py

### Rule ambiguity
no ambiguity

### Areas affected
- [x] src/blokus
- [x] tests
- [x] CLI
""".strip()

        result = triage_issue("[Agent Task]: Tighten CLI output", issue_body, [])

        self.assertEqual(result["state"], "agent-ready")
        self.assertIn("agent-ready", result["add_labels"])
        self.assertIn("safe-autonomy", result["add_labels"])
        self.assertIn("cli", result["add_labels"])
        self.assertNotIn("needs-human-spec", result["add_labels"])

    def test_triage_routes_ambiguous_issue_to_humans(self) -> None:
        issue_body = """
### Problem statement
Clarify whether corner-touching should ignore occupied diagonals.

### Acceptance criteria
- Human confirms the exact rule.

### Why this is suitable for autonomous implementation
- The work should stay blocked until the rule is clarified.

### Files likely affected
- src/blokus/engine.py

### Required tests
- Update legality tests after decision.

### Context bundle
- docs/rule-sources.md

### Rule ambiguity
possible ambiguity

### Areas affected
- [x] src/blokus
""".strip()

        result = triage_issue("[Agent Task]: Clarify diagonal rule", issue_body, [])

        self.assertEqual(result["state"], "needs-human-spec")
        self.assertIn("needs-human-spec", result["add_labels"])
        self.assertIn("human-gate-required", result["add_labels"])
        self.assertNotIn("safe-autonomy", result["add_labels"])

    def test_triage_flags_workflow_sensitive_issue(self) -> None:
        issue_body = """
### Problem statement
Adjust CI permissions.

### Acceptance criteria
- Workflow has least-privilege permissions.

### Why this is suitable for autonomous implementation
- The change is mechanically scoped, but it still needs human gating.

### Files likely affected
- .github/workflows/ci.yml

### Required tests
- Trigger a CI dry run.

### Context bundle
- docs/AGENT_POLICY.md

### Rule ambiguity
no ambiguity

### Areas affected
- [x] .github / CI workflows
""".strip()

        result = triage_issue("[Agent Task]: Tighten CI permissions", issue_body, [])

        self.assertEqual(result["state"], "agent-ready")
        self.assertIn("workflow-sensitive", result["add_labels"])
        self.assertIn("human-gate-required", result["add_labels"])
        self.assertNotIn("safe-autonomy", result["add_labels"])

    def test_triage_requires_agent_suitability_and_context_bundle(self) -> None:
        issue_body = """
### Problem statement
Tighten CLI output.

### Acceptance criteria
- Output is deterministic.

### Files likely affected
- src/blokus/cli.py

### Required tests
- Update CLI tests.

### Rule ambiguity
no ambiguity
""".strip()

        result = triage_issue("[Agent Task]: Tighten CLI output", issue_body, [])

        self.assertEqual(result["state"], "needs-human-spec")
        self.assertIn("needs-human-spec", result["add_labels"])

    def test_domain_inference_covers_ci_and_docs(self) -> None:
        domains = infer_domains_from_paths(
            [".github/workflows/ci.yml", "docs/AGENT_POLICY.md", "src/blokus/engine.py"]
        )

        self.assertEqual(domains, ("ci", "docs", "rules"))

    def test_tests_missing_detects_code_without_test_changes(self) -> None:
        self.assertTrue(tests_missing(["src/blokus/engine.py", "README.md"]))
        self.assertFalse(tests_missing(["src/blokus/engine.py", "tests/test_engine.py"]))

    def test_failure_category_mapping_prefers_specific_jobs(self) -> None:
        self.assertEqual(classify_failure_category(["cli-smoke"]), "cli-smoke")
        self.assertEqual(classify_failure_category(["fixture-schema"]), "fixture-schema")
        self.assertEqual(classify_failure_category(["test"]), "unit-test")
        self.assertEqual(classify_failure_category(["mystery-job"]), "unknown")

    def test_repair_policy_blocks_sensitive_paths(self) -> None:
        allowed, reason = repair_allowed(
            branch_name="agent/issue-42-fix-lint",
            labels=["agent-ready"],
            category="lint",
            changed_files=[".github/workflows/ci.yml"],
            retry_count=0,
        )

        self.assertFalse(allowed)
        self.assertIn("Sensitive", reason)

    def test_repair_policy_allows_safe_agent_branch(self) -> None:
        allowed, reason = repair_allowed(
            branch_name="agent/issue-42-fix-lint",
            labels=["agent-ready", "safe-autonomy"],
            category="lint",
            changed_files=["src/blokus/engine.py", "tests/test_engine.py"],
            retry_count=1,
        )

        self.assertTrue(allowed)
        self.assertIn("allowed", reason.lower())

    def test_branch_name_slug_is_bounded(self) -> None:
        branch = build_agent_branch_name(12, "[Agent Task]: Normalize CLI output and fixture docs")

        self.assertTrue(branch.startswith("agent/issue-12-"))
        self.assertLessEqual(len(branch.split("-", 3)[-1]), 48)

    def test_state_marker_round_trips(self) -> None:
        rendered = render_state_marker("agent-repair-loop-state", {"attempts": 1, "handled_runs": [7]})
        parsed = parse_state_marker("agent-repair-loop-state", rendered)

        self.assertEqual(parsed, {"attempts": 1, "handled_runs": [7]})


if __name__ == "__main__":
    unittest.main()
