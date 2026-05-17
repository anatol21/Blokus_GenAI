import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from blokus.engine import (
    apply_move,
    compute_scores,
    get_occupied_cells,
    list_legal_moves,
    new_game,
)
from blokus.models import GameState, Move

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "states"

def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "blokus", *args],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )

class RoundTripFidelityDuoTests(unittest.TestCase):
    def test_fresh_state_round_trips_exactly(self) -> None:
        state = new_game(mode="duo")
        payload = state.to_dict()
        reloaded = GameState.from_dict(payload)
        self.assertEqual(reloaded.to_dict(), payload)

    def test_round_trip_after_opening_moves(self) -> None:
        state = new_game(mode="duo")
        moves = [
            Move("blue", "I1", 4, 4),
            Move("red", "I1", 9, 9),
        ]
        for m in moves:
            state = apply_move(state, m)

        payload = state.to_dict()
        reloaded = GameState.from_dict(payload)
        self.assertEqual(reloaded.to_dict(), payload)

    def test_round_trip_with_computer_controllers(self) -> None:
        state = new_game(
            mode="duo",
            controllers={"blue": "computer", "red": "human"},
            strategies={"blue": "default", "red": "default"},
        )
        payload = state.to_dict()
        reloaded = GameState.from_dict(payload)

        for player in state.players:
            self.assertEqual(reloaded.controller_types[player], state.controller_types[player])
            self.assertEqual(reloaded.controller_strategies[player], state.controller_strategies[player])


class BoardReproducibilityDuoTests(unittest.TestCase):
    def test_board_cells_match_after_reload(self) -> None:
        state = new_game(mode="duo")
        state = apply_move(state, Move("blue", "I1", 4, 4))
        state = apply_move(state, Move("red", "I1", 9, 9))

        reloaded = GameState.from_dict(state.to_dict())

        for y in range(state.board_size):
            for x in range(state.board_size):
                self.assertEqual(reloaded.board[y][x], state.board[y][x])

    def test_occupied_cells_cache_rebuilt_from_board(self) -> None:
        state = new_game(mode="duo")
        state = apply_move(state, Move("blue", "I1", 4, 4))
        state = apply_move(state, Move("red", "I1", 9, 9))

        reloaded = GameState.from_dict(state.to_dict())

        for player in reloaded.players:
            original_cells = get_occupied_cells(state, player)
            reloaded_cells = get_occupied_cells(reloaded, player)
            self.assertEqual(reloaded_cells, original_cells)


class CliExportImportDuoTests(unittest.TestCase):
    def test_duo_state_export_import_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "duo_test.json"
            result = run_cli("new", "--mode", "duo", "--output", str(temp_path))
            self.assertEqual(result.returncode, 0)
            
            with temp_path.open("r", encoding="utf-8") as f:
                exported = json.load(f)
            reloaded = GameState.from_dict(exported)
            self.assertEqual(reloaded.to_dict(), exported)

    def test_apply_chain_produces_valid_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path_a = Path(tmp) / "step0.json"
            path_b = Path(tmp) / "step1.json"

            result = run_cli("new", "--mode", "duo", "--output", str(path_a))
            self.assertEqual(result.returncode, 0)

            result = run_cli(
                "apply", "--state", str(path_a),
                "--piece", "I1", "--x", "4", "--y", "4",
                "--output", str(path_b),
            )
            self.assertEqual(result.returncode, 0, result.stderr)

            with path_b.open("r", encoding="utf-8") as f:
                step1 = json.load(f)
            self.assertEqual(step1["current_player"], "red")


if __name__ == "__main__":
    unittest.main()
