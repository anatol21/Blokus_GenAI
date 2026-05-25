import json
from pathlib import Path
from typing import cast
import unittest

from blokus.engine import apply_move, get_occupied_cells, new_game
from blokus.models import GameState, Move

REPO_ROOT = Path(__file__).resolve().parents[1]

def board_occupied_cells(state: GameState):
    """Derive occupied cells by scanning the board (not cache-backed helpers)."""
    expected_all = {
        (x, y)
        for y, row in enumerate(state.board)
        for x, cell in enumerate(row)
        if cell is not None
    }
    expected_by_player = {
        player: {
            (x, y)
            for y, row in enumerate(state.board)
            for x, cell in enumerate(row)
            if cell == player
        }
        for player in state.players
    }
    return expected_all, expected_by_player

class SerializationDuoTests(unittest.TestCase):
    def load_initial_payload(self) -> dict[str, object]:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "duo_initial_state.json"
        with fixture_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_initial_fixture_round_trips(self) -> None:
        payload = self.load_initial_payload()
        state = GameState.from_dict(payload)
        self.assertEqual(state.to_dict(), payload)

    def test_state_to_dict_excludes_occupied_cells_by_player(self) -> None:
        state = new_game(mode="duo")
        payload = state.to_dict()
        self.assertNotIn("occupied_cells_by_player", payload)

        reloaded = GameState.from_dict(payload)
        self.assertEqual(set(reloaded.occupied_cells_by_player.keys()), set(reloaded.players))

    def test_state_round_trip_after_moves(self) -> None:
        state = new_game(
            mode="duo",
            controllers={"blue": "computer", "red": "human"},
            strategies={"blue": "default", "red": "default"},
        )
        for move in (
            Move("blue", "I1", 4, 4),
            Move("red", "I1", 9, 9),
            Move("blue", "I2", 3, 5, rotation=1),
        ):
            state = apply_move(state, move)
        reloaded = GameState.from_dict(state.to_dict())
        self.assertEqual(reloaded.to_dict(), state.to_dict())
        self.assertEqual(reloaded.controller_types["blue"], "computer")
        self.assertEqual(reloaded.controller_strategies["blue"], "default")

    def test_round_tripped_state_rebuilds_occupied_cells_cache_from_board(self) -> None:
        state = new_game(mode="duo")
        for move in (
            Move("blue", "I1", 4, 4),
            Move("red", "I1", 9, 9),
            Move("blue", "I2", 3, 5, rotation=1),
        ):
            state = apply_move(state, move)

        reloaded = GameState.from_dict(state.to_dict())
        expected_all, expected_by_player = board_occupied_cells(reloaded)

        for player in reloaded.players:
            self.assertEqual(reloaded.occupied_cells_by_player[player], expected_by_player[player])
            self.assertEqual(get_occupied_cells(reloaded, player), expected_by_player[player])

        self.assertEqual(get_occupied_cells(reloaded), expected_all)

    def test_invalid_board_symbol_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        board = cast(list[str], payload["board"])
        board[0] = "Q" + board[0][1:]
        with self.assertRaisesRegex(ValueError, "No player configured for board symbol"):
            GameState.from_dict(payload)

    def test_board_player_missing_from_players_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        # 'O' maps to player 'orange' which is not in duo mode's player list.
        board = cast(list[str], payload["board"])
        board[0] = "O" + board[0][1:]
        with self.assertRaisesRegex(ValueError, "Board contains player 'orange'"):
            GameState.from_dict(payload)

    def test_mismatched_player_list_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["players"] = ["blue", "yellow", "red", "green"]
        with self.assertRaisesRegex(ValueError, "do not match mode"):
            GameState.from_dict(payload)

    def test_invalid_current_player_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["current_player"] = "orange"
        with self.assertRaisesRegex(ValueError, "is not part of the mode player order"):
            GameState.from_dict(payload)

    def test_unknown_remaining_piece_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        remaining_pieces = cast(dict[str, list[str]], payload["remaining_pieces"])
        remaining_pieces["blue"][0] = "BAD"
        with self.assertRaisesRegex(ValueError, "contain unknown ids"):
            GameState.from_dict(payload)

    def test_duplicate_remaining_piece_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        remaining_pieces = cast(dict[str, list[str]], payload["remaining_pieces"])
        remaining_pieces["blue"] = ["I1", "I1"]
        with self.assertRaisesRegex(ValueError, "contain duplicates"):
            GameState.from_dict(payload)

if __name__ == "__main__":
    unittest.main()
