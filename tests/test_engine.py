import unittest
from copy import deepcopy

from blokus.engine import apply_move, list_legal_moves, new_game, pass_turn, validate_move
from blokus.models import GameState, Move
from blokus.pieces import absolute_cells


def play_standard_opening_cycle() -> GameState:
    state = new_game(mode="classic")
    moves = [
        Move("blue", "I1", 0, 0),
        Move("yellow", "I1", 19, 0),
        Move("red", "I1", 19, 19),
        Move("green", "I1", 0, 19),
    ]
    for move in moves:
        state = apply_move(state, move)
    return state


def _absolute_occupied_cells(move: Move) -> frozenset[tuple[int, int]]:
    return frozenset(
        absolute_cells(
            move.piece,
            origin=(move.x, move.y),
            rotation=move.rotation,
            flipped=move.flipped,
        )
    )


def _move_uniqueness_key(move: Move) -> tuple[str, frozenset[tuple[int, int]]]:
    return (move.piece, _absolute_occupied_cells(move))


def _serialized_snapshot(state: GameState) -> dict[str, object]:
    return deepcopy(state.to_dict())


def _blocked_blue_classic_state() -> tuple[GameState, str]:
    state = new_game(mode="classic")
    state.remaining_pieces["blue"].clear()
    return state, "blue"


def _unknown_player_classic_state() -> tuple[GameState, str]:
    state = new_game(mode="classic")
    return state, "purple"


def _finished_classic_state() -> tuple[GameState, str]:
    state = new_game(mode="classic")
    state.finished = True
    return state, state.current_player


class EngineRuleTests(unittest.TestCase):
    def test_opening_move_must_cover_corner(self) -> None:
        state = new_game(mode="classic")

        result = validate_move(state, Move("blue", "I1", 1, 1))

        self.assertFalse(result.ok)
        self.assertIn("must cover start corner", result.reason)

    def test_turn_order_is_enforced(self) -> None:
        state = new_game(mode="classic")

        result = validate_move(state, Move("yellow", "I1", 19, 0))

        self.assertFalse(result.ok)
        self.assertIn("It is blue's turn", result.reason)

    def test_same_color_edge_contact_is_illegal(self) -> None:
        """Evidence: VAL-03, R-F-04, R-F-13, R-T-02."""

        state = play_standard_opening_cycle()

        result = validate_move(state, Move("blue", "I2", 1, 0))

        self.assertFalse(result.ok)
        self.assertIn("may not touch along an edge", result.reason)

    def test_same_color_corner_contact_is_legal(self) -> None:
        state = play_standard_opening_cycle()

        result = validate_move(state, Move("blue", "I2", 1, 1))

        self.assertTrue(result.ok)

    def test_validate_move_prioritizes_piece_identity_and_rack_failures_over_spatial_failures(self) -> None:
        """Evidence: VAL-03, R-F-04, R-F-25."""

        state = play_standard_opening_cycle()

        result = validate_move(state, Move("blue", "I1", -1, 0))

        self.assertFalse(result.ok)
        self.assertIn("is no longer available", result.reason)
        self.assertNotIn("outside the board", result.reason)

    def test_apply_move_opening_transition_matches_expected_serialized_state(self) -> None:
        """Evidence: LIFE-01, LIFE-02, R-F-05, R-F-10, R-F-25, R-T-04."""

        state = new_game(mode="classic")

        next_state = apply_move(state, Move("blue", "I1", 0, 0))

        self.assertEqual(
            next_state.to_dict(),
            {
                "mode": "classic",
                "board_size": 20,
                "players": ["blue", "yellow", "red", "green"],
                "start_corners": {
                    "blue": [0, 0],
                    "yellow": [19, 0],
                    "red": [19, 19],
                    "green": [0, 19],
                },
                "board": [
                    "B...................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                    "....................",
                ],
                "remaining_pieces": {
                    "blue": [
                        "F5",
                        "I5",
                        "L5",
                        "N5",
                        "P5",
                        "T5",
                        "U5",
                        "V5",
                        "W5",
                        "X5",
                        "Y5",
                        "Z5",
                        "I4",
                        "L4",
                        "O4",
                        "T4",
                        "Z4",
                        "I3",
                        "V3",
                        "I2",
                    ],
                    "yellow": [
                        "F5",
                        "I5",
                        "L5",
                        "N5",
                        "P5",
                        "T5",
                        "U5",
                        "V5",
                        "W5",
                        "X5",
                        "Y5",
                        "Z5",
                        "I4",
                        "L4",
                        "O4",
                        "T4",
                        "Z4",
                        "I3",
                        "V3",
                        "I2",
                        "I1",
                    ],
                    "red": [
                        "F5",
                        "I5",
                        "L5",
                        "N5",
                        "P5",
                        "T5",
                        "U5",
                        "V5",
                        "W5",
                        "X5",
                        "Y5",
                        "Z5",
                        "I4",
                        "L4",
                        "O4",
                        "T4",
                        "Z4",
                        "I3",
                        "V3",
                        "I2",
                        "I1",
                    ],
                    "green": [
                        "F5",
                        "I5",
                        "L5",
                        "N5",
                        "P5",
                        "T5",
                        "U5",
                        "V5",
                        "W5",
                        "X5",
                        "Y5",
                        "Z5",
                        "I4",
                        "L4",
                        "O4",
                        "T4",
                        "Z4",
                        "I3",
                        "V3",
                        "I2",
                        "I1",
                    ],
                },
                "history": [
                    {
                        "player": "blue",
                        "piece": "I1",
                        "x": 0,
                        "y": 0,
                        "rotation": 0,
                        "flipped": False,
                    }
                ],
                "current_player": "yellow",
                "consecutive_passes": 0,
                "finished": False,
                "controller_types": {
                    "blue": "human",
                    "yellow": "human",
                    "red": "human",
                    "green": "human",
                },
                "controller_strategies": {
                    "blue": "default",
                    "yellow": "default",
                    "red": "default",
                    "green": "default",
                },
            },
        )

    def test_apply_move_rejection_paths_preserve_serialized_classic_state(self) -> None:
        """Evidence: VAL-05, LIFE-02, R-F-05, R-F-10, R-T-04."""

        cases = [
            (new_game(mode="classic"), Move("blue", "I1", 1, 1), "must cover start corner"),
            (
                play_standard_opening_cycle(),
                Move("blue", "I2", 0, 0),
                "overlaps an already occupied square",
            ),
            (
                play_standard_opening_cycle(),
                Move("blue", "I5", 18, 16, rotation=1),
                "outside the board",
            ),
        ]

        for state, move, reason in cases:
            with self.subTest(move=move, reason=reason):
                serialized_before = _serialized_snapshot(state)

                with self.assertRaisesRegex(ValueError, reason):
                    apply_move(state, move)

                self.assertEqual(state.to_dict(), serialized_before)

    def test_apply_move_resets_accumulated_consecutive_passes_in_classic_lifecycle(self) -> None:
        """Evidence: LIFE-03, R-F-05, R-F-10, R-F-25."""

        state = play_standard_opening_cycle()
        state.consecutive_passes = 3

        next_state = apply_move(state, Move("blue", "I2", 1, 1))

        self.assertEqual(next_state.consecutive_passes, 0)
        self.assertEqual(next_state.current_player, "yellow")
        self.assertFalse(next_state.finished)

    def test_terminal_pass_finishes_classic_game_once_without_repeat_mutation(self) -> None:
        """Evidence: LIFE-03, R-F-10, R-F-25."""

        state = new_game(mode="classic")
        for player in state.players:
            state.remaining_pieces[player].clear()
        state.consecutive_passes = len(state.players) - 1

        terminal_state = pass_turn(state)

        self.assertTrue(terminal_state.finished)
        self.assertEqual(terminal_state.consecutive_passes, len(terminal_state.players))
        self.assertEqual(terminal_state.current_player, "yellow")

        serialized_terminal = _serialized_snapshot(terminal_state)
        with self.assertRaisesRegex(ValueError, "already finished"):
            pass_turn(terminal_state)

        self.assertEqual(terminal_state.to_dict(), serialized_terminal)

    def test_terminal_move_rejection_aligns_with_empty_legal_move_listing(self) -> None:
        """Evidence: VAL-09, LIST-04, R-F-06, R-F-25."""

        state = new_game(mode="classic")
        state.finished = True
        serialized_before = _serialized_snapshot(state)

        self.assertEqual(list_legal_moves(state), [])

        result = validate_move(state, Move("blue", "I1", 0, 0))

        self.assertFalse(result.ok)
        self.assertIn("already finished", result.reason)
        self.assertEqual(state.to_dict(), serialized_before)

    def test_list_legal_moves_on_fresh_classic_state_is_legal_corner_covering_unique_and_deterministic(
        self,
    ) -> None:
        """Evidence: LIST-01, R-F-06, R-F-13, R-T-02, R-T-06."""

        state = new_game(mode="classic")
        start_corner = state.start_corners[state.current_player]

        first_listing = list_legal_moves(state)
        second_listing = list_legal_moves(state)

        self.assertTrue(first_listing)
        self.assertEqual(
            {_move_uniqueness_key(move) for move in first_listing},
            {_move_uniqueness_key(move) for move in second_listing},
        )

        uniqueness_keys = [_move_uniqueness_key(move) for move in first_listing]
        self.assertEqual(len(uniqueness_keys), len(set(uniqueness_keys)))

        for move in first_listing:
            self.assertEqual(move.player, state.current_player)
            self.assertTrue(validate_move(state, move).ok)
            self.assertIn(start_corner, _absolute_occupied_cells(move))

    def test_list_legal_moves_with_zero_limit_returns_empty_list_on_fresh_classic_state(self) -> None:
        """Evidence: LIST-03, R-F-02, R-F-06, R-T-06."""

        state = new_game(mode="classic")

        self.assertEqual(list_legal_moves(state, limit=0), [])

    def test_list_legal_moves_returns_empty_without_mutation_in_invalid_or_terminal_classic_contexts(
        self,
    ) -> None:
        """Evidence: LIST-04, R-F-06, R-F-25."""

        cases = [
            (_blocked_blue_classic_state(), "blocked-player"),
            (_unknown_player_classic_state(), "unknown-player"),
            (_finished_classic_state(), "finished-game"),
        ]

        for (state, player), case_id in cases:
            with self.subTest(case_id=case_id):
                serialized_before = _serialized_snapshot(state)

                moves = list_legal_moves(state, player=player)

                self.assertEqual(moves, [])
                self.assertEqual(state.to_dict(), serialized_before)

                if case_id == "unknown-player":
                    self.assertNotIn(player, state.remaining_pieces)
                    self.assertEqual(state.current_player, serialized_before["current_player"])


if __name__ == "__main__":
    unittest.main()
