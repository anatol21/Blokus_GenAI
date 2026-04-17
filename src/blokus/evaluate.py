"""Fixture-backed evaluation harness."""

from dataclasses import dataclass
import json
from pathlib import Path

from blokus.engine import apply_move, compute_scores, new_game, occupied_square_counts, pass_turn
from blokus.models import GameState, Move


SCENARIO_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "scenarios"
STATE_DIR = Path(__file__).resolve().parents[2] / "fixtures" / "states"


@dataclass(frozen=True)
class ScenarioResult:
    """Outcome summary for a single fixture scenario."""

    name: str
    passed: bool
    detail: str


def _load_scenario(path: Path) -> dict[str, object]:
    """Read a JSON scenario fixture from disk."""

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_state_fixture(name: str) -> GameState:
    """Read a serialized state fixture and rebuild the game state."""

    path = Path(name)
    if not path.is_absolute():
        path = STATE_DIR / name
    with path.open("r", encoding="utf-8") as handle:
        return GameState.from_dict(json.load(handle))


def _initial_state_for_scenario(scenario: dict[str, object]) -> GameState:
    """Build the starting state for a scenario, optionally from a saved fixture."""

    state_fixture = scenario.get("state_fixture")
    if state_fixture is not None:
        return _load_state_fixture(str(state_fixture))
    return new_game(mode=str(scenario.get("mode", "classic")))


def _scenario_steps(scenario: dict[str, object]) -> list[dict[str, object]]:
    """Normalize fixture steps so scenarios can mix moves and pass actions."""

    raw_steps = scenario.get("steps")
    if isinstance(raw_steps, list):
        return [dict(step) for step in raw_steps]
    return [{"type": "move", **dict(raw_move)} for raw_move in scenario.get("moves", [])]


def run_scenario(path: Path) -> ScenarioResult:
    """Execute one scenario fixture against the engine and compare expectations."""

    scenario = _load_scenario(path)
    state = _initial_state_for_scenario(scenario)
    name = str(scenario.get("name", path.stem))

    try:
        for step in _scenario_steps(scenario):
            step_type = str(step.get("type", "move"))
            if step_type == "pass":
                player = step.get("player")
                state = pass_turn(state, player=str(player) if player is not None else None)
                continue
            move_payload = {key: value for key, value in step.items() if key != "type"}
            state = apply_move(state, Move.from_dict(move_payload))
    except Exception as exc:  # pragma: no cover - surfaced in tests and CLI output
        return ScenarioResult(name=name, passed=False, detail=f"Scenario failed during move execution: {exc}")

    expected = scenario.get("expect", {})
    expected_current_player = expected.get("current_player")
    if expected_current_player and state.current_player != expected_current_player:
        return ScenarioResult(
            name=name,
            passed=False,
            detail=(
                f"Expected current player {expected_current_player}, "
                f"got {state.current_player}."
            ),
        )

    expected_finished = expected.get("finished")
    if expected_finished is not None and state.finished != bool(expected_finished):
        return ScenarioResult(
            name=name,
            passed=False,
            detail=f"Expected finished={expected_finished}, got {state.finished}.",
        )

    expected_history_length = expected.get("history_length")
    if expected_history_length is not None and len(state.history) != int(expected_history_length):
        return ScenarioResult(
            name=name,
            passed=False,
            detail=f"Expected history length {expected_history_length}, got {len(state.history)}.",
        )

    expected_consecutive_passes = expected.get("consecutive_passes")
    if expected_consecutive_passes is not None and state.consecutive_passes != int(expected_consecutive_passes):
        return ScenarioResult(
            name=name,
            passed=False,
            detail=(
                f"Expected consecutive_passes={expected_consecutive_passes}, "
                f"got {state.consecutive_passes}."
            ),
        )

    expected_counts = expected.get("occupied_counts")
    if isinstance(expected_counts, dict):
        actual_counts = occupied_square_counts(state)
        for player, expected_count in expected_counts.items():
            if actual_counts[str(player)] != int(expected_count):
                return ScenarioResult(
                    name=name,
                    passed=False,
                    detail=(
                        f"Expected {player} to occupy {expected_count} squares, "
                        f"got {actual_counts[str(player)]}."
                    ),
                )

    expected_scores = expected.get("scores")
    if isinstance(expected_scores, dict):
        actual_scores = compute_scores(state)
        for player, expected_score in expected_scores.items():
            if actual_scores[str(player)] != int(expected_score):
                return ScenarioResult(
                    name=name,
                    passed=False,
                    detail=(
                        f"Expected score for {player} to be {expected_score}, "
                        f"got {actual_scores[str(player)]}."
                    ),
                )

    return ScenarioResult(name=name, passed=True, detail="Passed.")


def run_all_scenarios(directory: Path = SCENARIO_DIR) -> list[ScenarioResult]:
    """Run every scenario fixture in a directory in filename order."""

    return [run_scenario(path) for path in sorted(directory.glob("*.json"))]


def main() -> int:
    """CLI entry point for the evaluation harness."""

    results = run_all_scenarios()
    passed = sum(1 for result in results if result.passed)
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}: {result.name} - {result.detail}")
    print(f"\nSummary: {passed}/{len(results)} scenarios passed.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
