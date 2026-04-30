import json
from pathlib import Path
import unittest

from blokus.engine import apply_move, new_game
from blokus.models import GameState, Move


REPO_ROOT = Path(__file__).resolve().parents[1]


class SerializationTests(unittest.TestCase):
    def load_initial_payload(self) -> dict[str, object]:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        with fixture_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_initial_fixture_round_trips(self) -> None:
        payload = self.load_initial_payload()
        state = GameState.from_dict(payload)
        self.assertEqual(state.to_dict(), payload)

    def test_state_round_trip_after_moves(self) -> None:
        state = new_game(
            controllers={"blue": "computer", "yellow": "human", "red": "human", "green": "human"},
            strategies={"blue": "default", "yellow": "default", "red": "default", "green": "default"},
        )
        for move in (
            Move("blue", "I1", 0, 0),
            Move("yellow", "I1", 19, 0),
            Move("red", "I1", 19, 19),
            Move("green", "I1", 0, 19),
            Move("blue", "I2", 1, 1),
        ):
            state = apply_move(state, move)
        reloaded = GameState.from_dict(state.to_dict())
        self.assertEqual(reloaded.to_dict(), state.to_dict())
        self.assertEqual(reloaded.controller_types["blue"], "computer")
        self.assertEqual(reloaded.controller_strategies["blue"], "default")

    def test_invalid_board_symbol_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["board"][0] = "Q" + payload["board"][0][1:]
        with self.assertRaisesRegex(ValueError, "No player configured for board symbol"):
            GameState.from_dict(payload)

    def test_mismatched_player_list_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["players"] = ["blue", "yellow"]
        with self.assertRaisesRegex(ValueError, "do not match mode"):
            GameState.from_dict(payload)

    def test_invalid_current_player_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["current_player"] = "orange"
        with self.assertRaisesRegex(ValueError, "is not part of the mode player order"):
            GameState.from_dict(payload)

    def test_unknown_remaining_piece_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["remaining_pieces"]["blue"][0] = "BAD"
        with self.assertRaisesRegex(ValueError, "contain unknown ids"):
            GameState.from_dict(payload)

    def test_duplicate_remaining_piece_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["remaining_pieces"]["blue"] = ["I1", "I1"]
        with self.assertRaisesRegex(ValueError, "contain duplicates"):
            GameState.from_dict(payload)


if __name__ == "__main__":
    unittest.main()
