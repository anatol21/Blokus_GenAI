import unittest

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


if __name__ == "__main__":
    unittest.main()
