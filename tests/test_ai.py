import unittest
import pytest

from blokus.engine import new_game, validate_move
from blokus.players import choose_simple_move
from blokus.pieces import PIECES


class SimpleAiTests(unittest.TestCase):
    def test_simple_ai_returns_a_legal_opening_move(self) -> None:
        state = new_game()
        move = choose_simple_move(state)
        self.assertIsNotNone(move)
        self.assertTrue(validate_move(state, move).ok)

    def test_simple_ai_prefers_large_pieces(self) -> None:
        state = new_game()
        move = choose_simple_move(state)
        assert move is not None
        self.assertEqual(PIECES[move.piece].size, 5)

    def test_simple_ai_returns_none_for_blocked_player(self) -> None:
        state = new_game()
        state.remaining_pieces["blue"] = set()
        self.assertIsNone(choose_simple_move(state))


class AiTests(unittest.TestCase):
    @pytest.mark.parametrize("mode", ["classic", "duo"])
    def test_ai_can_select_legal_move_in_mode(self, mode):
        """AI player can pick a legal move in any mode."""
        state = new_game(mode=mode)
        player = state.players[0]
        move = choose_move(state, player=player, strategy="default")

        self.assertIsNotNone(move)
        self.assertEqual(move.player, player)
        result = validate_move(state, move)
        self.assertTrue(result.ok)


if __name__ == "__main__":
    unittest.main()
