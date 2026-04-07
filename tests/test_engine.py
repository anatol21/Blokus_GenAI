import unittest

from blokus.engine import apply_move, new_game, pass_turn, validate_move
from blokus.models import Move


def play_standard_opening_cycle():
    state = new_game()
    moves = [
        Move("blue", "I1", 0, 0),
        Move("yellow", "I1", 19, 0),
        Move("red", "I1", 19, 19),
        Move("green", "I1", 0, 19),
    ]
    for move in moves:
        state = apply_move(state, move)
    return state


class EngineRuleTests(unittest.TestCase):
    def test_opening_move_must_cover_corner(self) -> None:
        state = new_game()
        result = validate_move(state, Move("blue", "I1", 1, 1))
        self.assertFalse(result.ok)
        self.assertIn("must cover start corner", result.reason)

    def test_turn_order_is_enforced(self) -> None:
        state = new_game()
        result = validate_move(state, Move("yellow", "I1", 19, 0))
        self.assertFalse(result.ok)
        self.assertIn("It is blue's turn", result.reason)

    def test_same_color_edge_contact_is_illegal(self) -> None:
        state = play_standard_opening_cycle()
        result = validate_move(state, Move("blue", "I2", 1, 0))
        self.assertFalse(result.ok)
        self.assertIn("may not touch along an edge", result.reason)

    def test_same_color_corner_contact_is_legal(self) -> None:
        state = play_standard_opening_cycle()
        result = validate_move(state, Move("blue", "I2", 1, 1))
        self.assertTrue(result.ok)

    def test_apply_move_updates_turn_history_and_piece_pool(self) -> None:
        state = new_game()
        next_state = apply_move(state, Move("blue", "I1", 0, 0))
        self.assertEqual(next_state.current_player, "yellow")
        self.assertEqual(len(next_state.history), 1)
        self.assertNotIn("I1", next_state.remaining_pieces["blue"])
        self.assertEqual(next_state.board[0][0], "blue")

    def test_pass_requires_player_to_be_blocked(self) -> None:
        state = new_game()
        with self.assertRaisesRegex(ValueError, "only pass when no legal move exists"):
            pass_turn(state)

    def test_phase2_test_failure_probe(self) -> None:
        self.fail("temporary Phase 2 test failure probe")


if __name__ == "__main__":
    unittest.main()
