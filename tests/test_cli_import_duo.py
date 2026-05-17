import json
import unittest
from pathlib import Path

from blokus.engine import apply_move, new_game, validate_loaded_state
from blokus.models import GameState, Move

REPO_ROOT = Path(__file__).resolve().parents[1]
IMPORT_TESTS_DIR = REPO_ROOT / "import_json_tests_duo"

class TestImportValidationDuo(unittest.TestCase):
    def test_validate_valid_state(self):
        state = new_game(mode="duo")
        validate_loaded_state(state)

    def test_validate_state_after_moves(self):
        state = new_game(mode="duo")
        moves = [
            Move("blue", "I1", 4, 4, 0, False),
            Move("red", "I1", 9, 9, 0, False),
        ]
        for move in moves:
            state = apply_move(state, move)
        validate_loaded_state(state)

    def test_edge_cases_from_files(self):
        # We will dynamically test the generated edge cases
        # to ensure they fail validation or parsing.
        
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
            path = IMPORT_TESTS_DIR / filename
            if not path.exists():
                continue # Skip if not generated yet
            
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            
            with self.subTest(file=filename):
                try:
                    state = GameState.from_dict(data)
                    with self.assertRaises(expected_error):
                        validate_loaded_state(state)
                except Exception as e:
                    # from_dict might also correctly catch structural issues
                    self.assertIsInstance(e, expected_error)

if __name__ == "__main__":
    unittest.main()
