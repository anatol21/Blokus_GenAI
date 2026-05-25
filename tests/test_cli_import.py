"""Tests for CLI import functionality."""

import json
import tempfile
import unittest
from pathlib import Path

from blokus.engine import apply_move, new_game, validate_loaded_state
from blokus.models import GameState, Move


REPO_ROOT = Path(__file__).resolve().parents[1]


class TestImportValidation(unittest.TestCase):
    """Test the validate_loaded_state semantic validation function."""

    def test_validate_valid_state(self):
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                state = new_game(mode=mode)
                validate_loaded_state(state)

    def test_validate_state_after_moves(self):
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                state = new_game(mode=mode)
                moves = [
                    Move(player, "I1", *state.start_corners[player], 0, False)
                    for player in state.players
                ]
                for move in moves:
                    state = apply_move(state, move)
                validate_loaded_state(state)

    def test_validate_remaining_pieces_mismatch(self):
        """Remaining pieces count mismatch should fail validation."""
        state = new_game(mode="classic")
        state.remaining_pieces["red"].remove("I1")
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("Remaining pieces mismatch", str(cm.exception))

    def test_validate_illegal_move_in_history(self):
        """Illegal move in history should fail validation."""
        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0, 0, False))
        state.history.append(
            Move("red", "I1", 0, 0, 0, False)
        )
        state.remaining_pieces["red"].discard("I1")
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("History contains illegal move", str(cm.exception))

    def test_validate_board_mismatch_after_replay(self):
        """Board state mismatch after replaying history should fail."""
        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0, 0, False))
        state.board[15][15] = "yellow"
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("Board state mismatch", str(cm.exception))

    def test_validate_finished_flag_mismatch(self):
        """Finished flag mismatch should fail validation."""
        state = new_game(mode="classic")
        state.finished = True
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("Finished flag mismatch", str(cm.exception))

    def test_duo_import_edge_cases_from_files(self):
        duo_dir = REPO_ROOT / "import_json_tests_duo"
        if not duo_dir.exists():
            self.skipTest("Duo import test data directory not found")

        edge_cases = [
            ("01_piece_in_rack_and_board.json", ValueError),
            ("02_invalid_remaining_squares_sum.json", ValueError),
            ("03_illegal_piece_placement.json", ValueError),
            ("04_wrong_current_player.json", ValueError),
            ("05_incorrect_player_scores.json", ValueError),
            ("06_misconfigured_board.json", ValueError),
            ("07_wrong_starting_corners.json", ValueError),
            ("08_invalid_history_moves.json", ValueError),
        ]

        for filename, expected_error in edge_cases:
            path = duo_dir / filename
            if not path.exists():
                continue
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)

            with self.subTest(file=filename):
                try:
                    state = GameState.from_dict(data)
                    with self.assertRaises(expected_error):
                        validate_loaded_state(state)
                except Exception as e:
                    self.assertIsInstance(e, expected_error)


class TestImportCLI(unittest.TestCase):
    """Test CLI import command functionality (integration tests)."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _create_test_state_file(self, filename: str = "test_state.json") -> Path:
        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0, 0, False))
        state = apply_move(state, Move("yellow", "I1", 19, 0, 0, False))

        file_path = self.temp_path / filename
        with open(file_path, "w") as f:
            json.dump(state.to_dict(), f)
        return file_path

    def test_import_loads_valid_state(self):
        test_file = self._create_test_state_file("valid.json")

        with open(test_file) as f:
            data = json.load(f)
        expected_state = GameState.from_dict(data)
        validate_loaded_state(expected_state)

        self.assertEqual(expected_state.mode, "classic")
        self.assertEqual(len(expected_state.history), 2)

    def test_import_rejects_invalid_json(self):
        bad_file = self.temp_path / "bad.json"
        bad_file.write_text("{invalid json}")

        with self.assertRaises(json.JSONDecodeError):
            with open(bad_file) as f:
                json.load(f)

    def test_import_rejects_malformed_state(self):
        bad_file = self.temp_path / "malformed.json"

        data = {
            "mode": "classic",
            "board": [["." for _ in range(15)] for _ in range(15)],
            "players": ["blue", "yellow", "red", "green"],
            "start_corners": {"blue": [0, 0], "yellow": [19, 0], "red": [19, 19], "green": [0, 19]},
            "remaining_pieces": {
                "blue": ["I1"], "yellow": ["I1"], "red": ["I1"], "green": ["I1"]
            },
            "history": [],
            "current_player": "blue",
            "consecutive_passes": 0,
            "finished": False,
            "controller_types": {"blue": "human", "yellow": "computer", "red": "computer", "green": "computer"},
            "controller_strategies": {"blue": "default", "yellow": "default", "red": "default", "green": "default"},
        }
        with open(bad_file, "w") as f:
            json.dump(data, f)

        with open(bad_file) as f:
            data = json.load(f)
        with self.assertRaises(ValueError):
            GameState.from_dict(data)

    def test_import_roundtrip_preserves_state(self):
        from blokus.cli import _dump_json

        original_state = new_game(mode="classic")
        original_state = apply_move(original_state, Move("blue", "I1", 0, 0, 0, False))
        original_state = apply_move(original_state, Move("yellow", "I1", 19, 0, 0, False))

        export_file = self.temp_path / "roundtrip.json"
        _dump_json(original_state.to_dict(), str(export_file))

        with open(export_file) as f:
            data = json.load(f)
        imported_state = GameState.from_dict(data)
        validate_loaded_state(imported_state)

        self.assertEqual(imported_state.to_dict(), original_state.to_dict())

    def test_import_catches_corrupted_history(self):
        corrupted_file = self.temp_path / "corrupted.json"

        valid_pieces = [
            "I1", "I2", "I3", "V3", "I4", "O4", "T4", "L4", "Z4", "F5",
            "I5", "L5", "N5", "P5", "T5", "U5", "V5", "W5", "X5", "Y5", "Z5"
        ]

        state_dict = {
            "mode": "classic",
            "board_size": 20,
            "players": ["blue", "yellow", "red", "green"],
            "start_corners": {"blue": [0, 0], "yellow": [19, 0], "red": [19, 19], "green": [0, 19]},
            "board": ["." * 20 for _ in range(20)],
            "remaining_pieces": {
                "blue": [p for p in valid_pieces if p != "I1"],
                "yellow": valid_pieces,
                "red": [p for p in valid_pieces if p != "I1"],
                "green": valid_pieces,
            },
            "history": [
                {"player": "blue", "piece": "I1", "x": 0, "y": 0, "rotation": 0, "flipped": False},
                {"player": "red", "piece": "I1", "x": 0, "y": 0, "rotation": 0, "flipped": False},
            ],
            "current_player": "yellow",
            "consecutive_passes": 0,
            "finished": False,
            "controller_types": {"blue": "human", "yellow": "computer", "red": "computer", "green": "computer"},
            "controller_strategies": {"blue": "default", "yellow": "default", "red": "default", "green": "default"},
        }

        with open(corrupted_file, "w") as f:
            json.dump(state_dict, f)

        with open(corrupted_file) as f:
            data = json.load(f)
        state = GameState.from_dict(data)

        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("History contains illegal move", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
