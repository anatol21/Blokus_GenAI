import unittest
from copy import deepcopy

from blokus.engine import (
    apply_move,
    compute_scores,
    get_occupied_cells,
    is_first_move,
    list_legal_moves,
    new_game,
    occupied_square_counts,
    pass_turn,
    score_player,
    validate_move,
    validate_pass,
)
from blokus.models import GameState, Move
from blokus.pieces import PIECE_IDS, absolute_cells


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


def blocked_blue_state() -> GameState:
    state = new_game(mode="classic")
    state.remaining_pieces["blue"].clear()
    return state


def _unknown_player_classic_state() -> tuple[GameState, str]:
    state = new_game(mode="classic")
    return state, "purple"


def _finished_classic_state() -> tuple[GameState, str]:
    state = new_game(mode="classic")
    state.finished = True
    return state, state.current_player
def board_occupied_cells(state):
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


class EngineRuleTests(unittest.TestCase):
    def test_unsupported_duo_mode_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported mode 'duo'"):
            new_game("duo")

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

    def test_new_game_initializes_occupied_cells_by_player_cache(self) -> None:
        state = new_game()

        self.assertEqual(set(state.occupied_cells_by_player.keys()), set(state.players))
        for player in state.players:
            self.assertEqual(state.occupied_cells_by_player[player], set())

        self.assertTrue(all(cell is None for row in state.board for cell in row))

        state.occupied_cells_by_player["blue"].add((0, 0))
        for player in state.players:
            if player == "blue":
                continue
            self.assertEqual(state.occupied_cells_by_player[player], set())
            self.assertIsNot(
                state.occupied_cells_by_player["blue"],
                state.occupied_cells_by_player[player],
            )

        self.assertEqual(set(state.remaining_pieces.keys()), set(state.players))
        for player in state.players:
            self.assertEqual(state.remaining_pieces[player], set(PIECE_IDS))

    def test_clone_deep_copies_occupied_cells_by_player_sets(self) -> None:
        state = new_game()
        state.occupied_cells_by_player["blue"].add((0, 0))

        cloned = state.clone()
        self.assertIsNot(
            state.occupied_cells_by_player["blue"],
            cloned.occupied_cells_by_player["blue"],
        )

        cloned.occupied_cells_by_player["blue"].add((1, 1))
        self.assertEqual(state.occupied_cells_by_player["blue"], {(0, 0)})
        self.assertEqual(cloned.occupied_cells_by_player["blue"], {(0, 0), (1, 1)})

    def test_clone_preserves_cache_contents_without_sharing_sets_after_moves(self) -> None:
        state = play_standard_opening_cycle()
        state = apply_move(state, Move("blue", "I2", 1, 1))

        cloned = state.clone()
        for player in state.players:
            self.assertEqual(
                cloned.occupied_cells_by_player[player],
                state.occupied_cells_by_player[player],
            )
            self.assertIsNot(
                cloned.occupied_cells_by_player[player],
                state.occupied_cells_by_player[player],
            )

        # Mutating the clone must not affect the original.
        cloned.occupied_cells_by_player["blue"].add((2, 2))
        self.assertNotIn((2, 2), state.occupied_cells_by_player["blue"])

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

    def test_apply_move_updates_turn_history_and_piece_pool(self) -> None:
        state = new_game()
        next_state = apply_move(state, Move("blue", "I1", 0, 0))
        self.assertEqual(next_state.current_player, "yellow")
        self.assertEqual(len(next_state.history), 1)
        self.assertNotIn("I1", next_state.remaining_pieces["blue"])
        self.assertEqual(next_state.board[0][0], "blue")

    def test_get_occupied_cells_returns_player_cache_after_legal_move(self) -> None:
        state = new_game()
        state = apply_move(state, Move("blue", "I2", 0, 0))

        expected_blue = {
            (x, y)
            for y, row in enumerate(state.board)
            for x, cell in enumerate(row)
            if cell == "blue"
        }
        self.assertEqual(state.occupied_cells_by_player["blue"], expected_blue)
        self.assertEqual(get_occupied_cells(state, "blue"), expected_blue)

    def test_get_occupied_cells_returns_union_across_players(self) -> None:
        state = play_standard_opening_cycle()

        expected_all = {
            (x, y)
            for y, row in enumerate(state.board)
            for x, cell in enumerate(row)
            if cell is not None
        }
        self.assertEqual(get_occupied_cells(state), expected_all)

    def test_get_occupied_cells_matches_board_scan_per_player_after_multiple_moves(self) -> None:
        state = play_standard_opening_cycle()
        # Extend beyond the opening cycle to cover incremental cache updates.
        state = apply_move(state, Move("blue", "I2", 1, 1))

        _expected_all, expected_by_player = board_occupied_cells(state)
        for player in state.players:
            self.assertEqual(get_occupied_cells(state, player), expected_by_player[player])

    def test_get_occupied_cells_returns_defensive_copy(self) -> None:
        state = new_game()
        state = apply_move(state, Move("blue", "I2", 0, 0))

        returned = get_occupied_cells(state, "blue")
        self.assertEqual(returned, state.occupied_cells_by_player["blue"])

        # Mutating the returned set must not mutate the internal cache.
        returned.add((5, 5))
        returned.discard(next(iter(state.occupied_cells_by_player["blue"])))
        self.assertNotIn((5, 5), state.occupied_cells_by_player["blue"])
        self.assertEqual(
            state.occupied_cells_by_player["blue"],
            {
                (x, y)
                for y, row in enumerate(state.board)
                for x, cell in enumerate(row)
                if cell == "blue"
            },
        )

    def test_is_first_move_reflects_player_occupancy(self) -> None:
        state = new_game()
        self.assertTrue(is_first_move(state, "blue"))

        state = apply_move(state, Move("blue", "I2", 0, 0))
        self.assertFalse(is_first_move(state, "blue"))
        self.assertTrue(is_first_move(state, "yellow"))

    def test_occupied_square_counts_matches_board_after_moves(self) -> None:
        state = play_standard_opening_cycle()
        state = apply_move(state, Move("blue", "I2", 1, 1))

        expected_counts = {player: 0 for player in state.players}
        for row in state.board:
            for cell in row:
                if cell is not None:
                    expected_counts[cell] += 1

        self.assertEqual(occupied_square_counts(state), expected_counts)

    def test_cache_read_functions_preserve_unknown_player_behavior(self) -> None:
        state = new_game()
        self.assertEqual(get_occupied_cells(state, "orange"), set())
        self.assertTrue(is_first_move(state, "orange"))

    def test_apply_move_adds_placed_cells_to_occupied_cells_cache(self) -> None:
        state = new_game()
        move = Move("blue", "I2", 0, 0)

        next_state = apply_move(state, move)

        board_cells = {
            (x, y)
            for y, row in enumerate(next_state.board)
            for x, cell in enumerate(row)
            if cell == "blue"
        }
        self.assertEqual(next_state.occupied_cells_by_player["blue"], board_cells)
        self.assertEqual(board_cells, {(0, 0), (1, 0)})

    def test_apply_move_does_not_mutate_original_state_cache(self) -> None:
        state = new_game()
        move = Move("blue", "I2", 0, 0)

        _ = apply_move(state, move)

        self.assertEqual(state.occupied_cells_by_player["blue"], set())
        self.assertTrue(all(cell is None for row in state.board for cell in row))

    def test_apply_move_does_not_update_other_players_cache_sets(self) -> None:
        state = new_game()
        move = Move("blue", "I2", 0, 0)

        next_state = apply_move(state, move)

        for player in next_state.players:
            if player == "blue":
                continue
            self.assertEqual(next_state.occupied_cells_by_player[player], set())

    def test_apply_move_illegal_move_raises_and_does_not_mutate_board_or_cache(self) -> None:
        state = new_game()
        # Add a sentinel to ensure we detect cache mutation (cache is derived and not serialized).
        # Use a non-active player so first-move logic for the mover stays intact.
        state.occupied_cells_by_player["yellow"].add((5, 5))
        before_board = [row[:] for row in state.board]
        before_cache = {player: set(cells) for player, cells in state.occupied_cells_by_player.items()}

        with self.assertRaisesRegex(ValueError, "must cover start corner"):
            apply_move(state, Move("blue", "I1", 1, 1))

        self.assertEqual(state.board, before_board)
        self.assertEqual(state.occupied_cells_by_player, before_cache)

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

    def test_occupied_cells_cache_accumulates_and_matches_board_per_player(self) -> None:
        state = play_standard_opening_cycle()
        state = apply_move(state, Move("blue", "I2", 1, 1))

        for player in state.players:
            board_cells = {
                (x, y)
                for y, row in enumerate(state.board)
                for x, cell in enumerate(row)
                if cell == player
            }
            self.assertEqual(state.occupied_cells_by_player[player], board_cells)

    def test_pass_requires_player_to_be_blocked(self) -> None:
        state = new_game()
        with self.assertRaisesRegex(ValueError, "only pass when no legal move exists"):
            pass_turn(state)

    def test_unknown_player_is_rejected(self) -> None:
        state = new_game()
        result = validate_move(state, Move("orange", "I1", 0, 0))
        self.assertFalse(result.ok)
        self.assertIn("Unknown player", result.reason)

    def test_unknown_piece_is_rejected(self) -> None:
        state = new_game()
        result = validate_move(state, Move("blue", "NOPE", 0, 0))
        self.assertFalse(result.ok)
        self.assertIn("Unknown piece", result.reason)

    def test_spent_piece_reuse_is_rejected(self) -> None:
        state = play_standard_opening_cycle()
        result = validate_move(state, Move("blue", "I1", 1, 1))
        self.assertFalse(result.ok)
        self.assertIn("no longer available", result.reason)

    def test_negative_coordinate_move_is_rejected(self) -> None:
        state = new_game()
        result = validate_move(state, Move("blue", "I1", -1, 0))
        self.assertFalse(result.ok)
        self.assertIn("outside the board", result.reason)

    def test_finished_game_rejects_moves(self) -> None:
        state = new_game()
        state.finished = True
        result = validate_move(state, Move("blue", "I1", 0, 0))
        self.assertFalse(result.ok)
        self.assertIn("already finished", result.reason)

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

    def test_apply_move_does_not_mutate_state_on_failure(self) -> None:
        state = new_game()
        before = state.to_dict()
        with self.assertRaisesRegex(ValueError, "must cover start corner"):
            apply_move(state, Move("blue", "I1", 1, 1))
        self.assertEqual(state.to_dict(), before)

    def test_apply_move_resets_consecutive_passes(self) -> None:
        state = new_game()
        state.consecutive_passes = 2
        next_state = apply_move(state, Move("blue", "I1", 0, 0))
        self.assertEqual(next_state.consecutive_passes, 0)

    def test_apply_move_resets_accumulated_consecutive_passes_in_classic_lifecycle(self) -> None:
        """Evidence: LIFE-03, R-F-05, R-F-10, R-F-25."""

        state = play_standard_opening_cycle()
        state.consecutive_passes = 3

        next_state = apply_move(state, Move("blue", "I2", 1, 1))

        self.assertEqual(next_state.consecutive_passes, 0)
        self.assertEqual(next_state.current_player, "yellow")
        self.assertFalse(next_state.finished)

    def test_pass_from_blocked_player_advances_turn(self) -> None:
        state = blocked_blue_state()
        validation = validate_pass(state)
        self.assertTrue(validation.ok)
        next_state = pass_turn(state)
        self.assertEqual(next_state.current_player, "yellow")
        self.assertEqual(next_state.consecutive_passes, 1)
        self.assertFalse(next_state.finished)

    def test_pass_finishes_game_when_all_players_are_blocked(self) -> None:
        state = new_game()
        for player in state.players:
            state.remaining_pieces[player] = set()
        next_state = pass_turn(state)
        self.assertTrue(next_state.finished)
        self.assertEqual(next_state.current_player, "yellow")

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

    def test_list_legal_moves_returns_unique_legal_placements(self) -> None:
        state = new_game()
        moves = list_legal_moves(state)
        placements = {
            (
                move.piece,
                tuple(
                    absolute_cells(
                        move.piece,
                        origin=(move.x, move.y),
                        rotation=move.rotation,
                        flipped=move.flipped,
                    )
                ),
            )
            for move in moves
        }
        self.assertEqual(len(moves), len(placements))
        self.assertTrue(all(validate_move(state, move).ok for move in moves))

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

    def test_list_legal_moves_respects_zero_limit(self) -> None:
        state = new_game()
        self.assertEqual(list_legal_moves(state, limit=0), [])

    def test_list_legal_moves_with_zero_limit_returns_empty_list_on_fresh_classic_state(self) -> None:
        """Evidence: LIST-03, R-F-02, R-F-06, R-T-06."""

        state = new_game(mode="classic")
        self.assertEqual(list_legal_moves(state, limit=0), [])

    def test_list_legal_moves_returns_empty_for_blocked_unknown_and_finished_states(self) -> None:
        blocked_state = blocked_blue_state()
        self.assertEqual(list_legal_moves(blocked_state, player="blue"), [])
        self.assertEqual(list_legal_moves(blocked_state, player="orange"), [])
        blocked_state.finished = True
        self.assertEqual(list_legal_moves(blocked_state), [])

    def test_list_legal_moves_returns_empty_without_mutation_in_invalid_or_terminal_classic_contexts(
        self,
    ) -> None:
        """Evidence: LIST-04, R-F-06, R-F-25."""

        cases = [
            (blocked_blue_state(), "blue", "blocked-player"),
            (*_unknown_player_classic_state(), "unknown-player"),
            (*_finished_classic_state(), "finished-game"),
        ]

        for state, player, case_id in cases:
            with self.subTest(case_id=case_id):
                serialized_before = _serialized_snapshot(state)

                moves = list_legal_moves(state, player=player)

                self.assertEqual(moves, [])
                self.assertEqual(state.to_dict(), serialized_before)

                if case_id == "unknown-player":
                    self.assertNotIn(player, state.remaining_pieces)
                    self.assertEqual(state.current_player, serialized_before["current_player"])

    def test_list_legal_moves_with_zero_limit_is_still_empty_for_unknown_and_finished_contexts(self) -> None:
        """Evidence: LIST-03, LIST-04, R-F-06, R-T-06."""

        cases = [
            (*_unknown_player_classic_state(), "unknown-player"),
            (*_finished_classic_state(), "finished-game"),
        ]

        for state, player, case_id in cases:
            with self.subTest(case_id=case_id):
                serialized_before = _serialized_snapshot(state)

                moves = list_legal_moves(state, player=player, limit=0)

                self.assertEqual(moves, [])
                self.assertEqual(state.to_dict(), serialized_before)

    def test_initial_scores_reflect_all_remaining_squares(self) -> None:
        scores = compute_scores(new_game())
        self.assertEqual(scores, {player: -89 for player in scores})

    def test_empty_rack_scoring_awards_finish_bonus_and_i1_bonus(self) -> None:
        state = new_game()
        state.remaining_pieces["blue"] = set()
        state.history = [Move("blue", "I2", 0, 0), Move("blue", "I1", 1, 1)]
        self.assertEqual(score_player(state, "blue"), 20)


if __name__ == "__main__":
    unittest.main()
