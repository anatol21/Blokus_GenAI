import json
from pathlib import Path
import unittest

from blokus.evaluate import run_all_scenarios, run_scenario


REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_DIR = REPO_ROOT / "fixtures" / "scenarios"
SCENARIO_FAILURE_DIR = REPO_ROOT / "fixtures" / "scenario_failures"

# Every EVAL-01 positive scenario must assert exactly these oracle fields.
POSITIVE_ORACLE_FIELDS = {
    "current_player",
    "history_length",
    "finished",
    "occupied_counts",
    "consecutive_passes",
}


class EvaluationHarnessTests(unittest.TestCase):
    def test_all_scenarios_pass(self) -> None:
        results = run_all_scenarios()
        self.assertTrue(results)
        self.assertTrue(all(result.passed for result in results), results)

    # ── EVAL-01 positive-scenario evidence ──────────────────────────

    def _assert_oracle_completeness(self, fixture_path: Path) -> None:
        """Verify the fixture's expect block covers all EVAL-01 oracle fields."""

        with fixture_path.open("r", encoding="utf-8") as f:
            scenario = json.load(f)
        expect = scenario.get("expect", {})
        missing = POSITIVE_ORACLE_FIELDS - set(expect.keys())
        self.assertFalse(
            missing,
            f"Fixture {fixture_path.name} is missing oracle fields: {missing}",
        )

    def test_corner_sequence_scenario_passes_with_full_oracle(self) -> None:
        """EVAL-01: classic_corner_sequence passes with all 5 oracle fields checked."""

        fixture = SCENARIO_DIR / "classic_corner_sequence.json"
        self._assert_oracle_completeness(fixture)
        result = run_scenario(fixture)
        self.assertTrue(result.passed, result.detail)

    def test_blocked_blue_pass_scenario_passes_with_full_oracle(self) -> None:
        """EVAL-01: classic_blocked_blue_pass passes with all 5 oracle fields checked."""

        fixture = SCENARIO_DIR / "classic_blocked_blue_pass.json"
        self._assert_oracle_completeness(fixture)
        result = run_scenario(fixture)
        self.assertTrue(result.passed, result.detail)

    # ── Negative-scenario evidence ──────────────────────────────────

    def test_invalid_move_scenario_reports_execution_failure(self) -> None:
        result = run_scenario(SCENARIO_FAILURE_DIR / "classic_invalid_opening_move.json")
        self.assertFalse(result.passed)
        self.assertIn("Scenario failed during move execution", result.detail)
        self.assertIn("must cover start corner", result.detail)

    def test_expectation_mismatch_scenario_reports_actual_value(self) -> None:
        result = run_scenario(SCENARIO_FAILURE_DIR / "classic_expectation_mismatch.json")
        self.assertFalse(result.passed)
        self.assertIn("Expected current player blue, got yellow.", result.detail)

    def test_counterexample_scenario_replays_piece_reuse_failure(self) -> None:
        result = run_scenario(SCENARIO_FAILURE_DIR / "classic_spent_piece_reuse_counterexample.json")
        self.assertFalse(result.passed)
        self.assertIn("no longer available", result.detail)


if __name__ == "__main__":
    unittest.main()
