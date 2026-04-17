from pathlib import Path
import unittest

from blokus.evaluate import run_all_scenarios, run_scenario


REPO_ROOT = Path(__file__).resolve().parents[1]
SCENARIO_FAILURE_DIR = REPO_ROOT / "fixtures" / "scenario_failures"


class EvaluationHarnessTests(unittest.TestCase):
    def test_all_scenarios_pass(self) -> None:
        results = run_all_scenarios()
        self.assertTrue(results)
        self.assertTrue(all(result.passed for result in results), results)

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
