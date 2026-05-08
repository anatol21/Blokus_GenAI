import unittest

import pytest

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


def test_apply_move_illegal_move_preserves_serialized_classic_state() -> None:
    """Evidence: R-F-05, R-F-10, R-F-25, R-T-04, LIFE-02."""

    state = new_game()
    serialized_before = state.to_dict()

    with pytest.raises(ValueError, match="must cover start corner"):
        apply_move(state, Move("blue", "I1", 1, 1))

    assert state.to_dict() == serialized_before


def test_apply_move_resets_accumulated_consecutive_passes_in_classic_lifecycle() -> None:
    """Evidence: LIFE-03, R-F-05, R-F-10, R-F-25."""

    state = play_standard_opening_cycle()
    state.consecutive_passes = 3

    next_state = apply_move(state, Move("blue", "I2", 1, 1))

    assert next_state.consecutive_passes == 0
    assert next_state.current_player == "yellow"
    assert next_state.finished is False


def test_terminal_pass_finishes_classic_game_once_without_repeat_mutation() -> None:
    """Evidence: LIFE-03, R-F-10, R-F-25."""

    state = new_game()
    for player in state.players:
        state.remaining_pieces[player].clear()
    state.consecutive_passes = len(state.players) - 1

    terminal_state = pass_turn(state)

    assert terminal_state.finished is True
    assert terminal_state.consecutive_passes == len(terminal_state.players)
    assert terminal_state.current_player == "yellow"

    serialized_terminal = terminal_state.to_dict()
    with pytest.raises(ValueError, match="already finished"):
        pass_turn(terminal_state)

    assert terminal_state.to_dict() == serialized_terminal


if __name__ == "__main__":
    unittest.main()
