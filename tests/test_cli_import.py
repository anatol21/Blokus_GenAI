"""Tests for CLI import functionality."""

import json
import tempfile
import unittest
from pathlib import Path

from blokus.engine import apply_move, new_game, validate_loaded_state
from blokus.models import GameState, Move


class TestImportValidation(unittest.TestCase):
    """Test the validate_loaded_state semantic validation function."""

    def test_validate_valid_state(self):
        """A valid, freshly created state should pass validation."""
        state = new_game(mode="classic")
        # Should not raise
        validate_loaded_state(state)

    def test_validate_state_after_moves(self):
        """A state with valid history should pass validation."""
        state = new_game(mode="classic")
        # Apply a few moves (following the classic mode player order: blue, yellow, red, green)
        moves = [
            Move("blue", "I1", 0, 0, 0, False),  # blue claims its corner
            Move("yellow", "I1", 19, 0, 0, False),  # yellow claims its corner
            Move("red", "I1", 19, 19, 0, False),  # red claims its corner
            Move("green", "I1", 0, 19, 0, False),  # green claims its corner
        ]
        for move in moves:
            state = apply_move(state, move)
        # Should not raise
        validate_loaded_state(state)

    def test_validate_remaining_pieces_mismatch(self):
        """Remaining pieces count mismatch should fail validation."""
        state = new_game(mode="classic")
        # Manually corrupt the remaining_pieces
        state.remaining_pieces["red"].remove("I1")
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("Remaining pieces mismatch", str(cm.exception))

    def test_validate_illegal_move_in_history(self):
        """Illegal move in history should fail validation."""
        state = new_game(mode="classic")
        # Create state with valid move
        state = apply_move(state, Move("blue", "I1", 0, 0, 0, False))
        # Corrupt history: add an illegal move (e.g., wrong player claiming corner)
        state.history.append(
            Move("red", "I1", 0, 0, 0, False)  # red trying to claim blue's corner
        )
        # To pass quick consistency check, remove the piece from red's remaining
        state.remaining_pieces["red"].discard("I1")
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("History contains illegal move", str(cm.exception))

    def test_validate_board_mismatch_after_replay(self):
        """Board state mismatch after replaying history should fail."""
        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0, 0, False))
        # Manually corrupt the board (add an extra piece)
        state.board[15][15] = "yellow"
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("Board state mismatch", str(cm.exception))

    def test_validate_finished_flag_mismatch(self):
        """Finished flag mismatch should fail validation."""
        state = new_game(mode="classic")
        state.finished = True  # Manually set finished while game is active
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("Finished flag mismatch", str(cm.exception))


class TestImportCLI(unittest.TestCase):
    """Test CLI import command functionality (integration tests)."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

    def tearDown(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def _create_test_state_file(self, filename: str = "test_state.json") -> Path:
        """Create a valid exported game state file for testing."""
        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0, 0, False))
        state = apply_move(state, Move("yellow", "I1", 19, 0, 0, False))

        file_path = self.temp_path / filename
        with open(file_path, "w") as f:
            json.dump(state.to_dict(), f)
        return file_path

    def test_import_loads_valid_state(self):
        """Test that importing a valid state file loads it correctly."""
        test_file = self._create_test_state_file("valid.json")
        
        # Load the exported file to get expected state
        with open(test_file) as f:
            data = json.load(f)
        expected_state = GameState.from_dict(data)
        validate_loaded_state(expected_state)
        
        # Verify the state is valid
        self.assertEqual(expected_state.mode, "classic")
        self.assertEqual(len(expected_state.history), 2)

    def test_import_rejects_invalid_json(self):
        """Test that invalid JSON is properly rejected."""
        bad_file = self.temp_path / "bad.json"
        bad_file.write_text("{invalid json}")
        
        with self.assertRaises(json.JSONDecodeError):
            with open(bad_file) as f:
                json.load(f)

    def test_import_rejects_malformed_state(self):
        """Test that malformed state dict is properly rejected."""
        bad_file = self.temp_path / "malformed.json"
        
        # Create state dict with wrong board size
        data = {
            "mode": "classic",
            "board": [["." for _ in range(15)] for _ in range(15)],  # Wrong size
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
        
        # Should raise ValueError from from_dict
        with open(bad_file) as f:
            data = json.load(f)
        with self.assertRaises(ValueError):
            GameState.from_dict(data)

    def test_import_roundtrip_preserves_state(self):
        """Test that exporting and importing preserves game state."""
        from blokus.cli import _dump_json
        
        # Create a state with some moves
        original_state = new_game(mode="classic")
        original_state = apply_move(original_state, Move("blue", "I1", 0, 0, 0, False))
        original_state = apply_move(original_state, Move("yellow", "I1", 19, 0, 0, False))
        
        # Export
        export_file = self.temp_path / "roundtrip.json"
        _dump_json(original_state.to_dict(), str(export_file))
        
        # Import
        with open(export_file) as f:
            data = json.load(f)
        imported_state = GameState.from_dict(data)
        validate_loaded_state(imported_state)
        
        # Verify equality
        self.assertEqual(imported_state.to_dict(), original_state.to_dict())

    def test_import_catches_corrupted_history(self):
        """Test that corrupted history is caught by validation."""
        # Create state with valid structure but illegal move in history
        corrupted_file = self.temp_path / "corrupted.json"
        
        # Use valid piece IDs: each player should have exactly 21 unique pieces
        valid_pieces = [
            "I1", "I2", "I3", "V3", "I4", "O4", "T4", "L4", "Z4", "F5",
            "I5", "L5", "N5", "P5", "T5", "U5", "V5", "W5", "X5", "Y5", "Z5"
        ]
        
        state_dict = {
            "mode": "classic",
            "board_size": 20,
            "players": ["blue", "yellow", "red", "green"],
            "start_corners": {"blue": [0, 0], "yellow": [19, 0], "red": [19, 19], "green": [0, 19]},
            "board": ["." * 20 for _ in range(20)],  # 20x20 board as strings
            "remaining_pieces": {
                    "blue": [p for p in valid_pieces if p != "I1"],  # blue used I1
                "yellow": valid_pieces,
                    "red": [p for p in valid_pieces if p != "I1"],  # red falsely claims I1
                "green": valid_pieces,
            },
            "history": [
                {"player": "blue", "piece": "I1", "x": 0, "y": 0, "rotation": 0, "flipped": False},
                {"player": "red", "piece": "I1", "x": 0, "y": 0, "rotation": 0, "flipped": False},  # Illegal: red can't claim blue's corner
            ],
            "current_player": "yellow",
            "consecutive_passes": 0,
            "finished": False,
            "controller_types": {"blue": "human", "yellow": "computer", "red": "computer", "green": "computer"},
            "controller_strategies": {"blue": "default", "yellow": "default", "red": "default", "green": "default"},
        }
        
        with open(corrupted_file, "w") as f:
            json.dump(state_dict, f)
        
        # Should load structurally but fail validation
        with open(corrupted_file) as f:
            data = json.load(f)
        state = GameState.from_dict(data)
        
        with self.assertRaises(ValueError) as cm:
            validate_loaded_state(state)
        self.assertIn("History contains illegal move", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
