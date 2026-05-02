import unittest

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
from blokus.models import Move
from blokus.pieces import PIECE_IDS, absolute_cells


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


def blocked_blue_state():
    state = new_game()
    state.remaining_pieces["blue"] = set()
    return state


class EngineRuleTests(unittest.TestCase):
    def test_unsupported_duo_mode_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported mode 'duo'"):
            new_game("duo")

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

    def test_new_game_initializes_occupied_cells_by_player_cache(self) -> None:
        state = new_game()

        self.assertEqual(set(state.occupied_cells_by_player.keys()), set(state.players))
        for player in state.players:
            self.assertEqual(state.occupied_cells_by_player[player], set())

        # Board remains empty.
        self.assertTrue(all(cell is None for row in state.board for cell in row))

        # Per-player cache entries must be distinct and independent.
        state.occupied_cells_by_player["blue"].add((0, 0))
        for player in state.players:
            if player == "blue":
                continue
            self.assertEqual(state.occupied_cells_by_player[player], set())
            self.assertIsNot(
                state.occupied_cells_by_player["blue"],
                state.occupied_cells_by_player[player],
            )

        # Existing initialization behavior remains intact.
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

        # Existing board behavior still matches the applied move.
        self.assertEqual(board_cells, {(0, 0), (1, 0)})

    def test_apply_move_does_not_mutate_original_state_cache(self) -> None:
        state = new_game()
        move = Move("blue", "I2", 0, 0)

        _ = apply_move(state, move)

        # Original state remains unchanged.
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

    def test_list_legal_moves_respects_zero_limit(self) -> None:
        state = new_game()
        self.assertEqual(list_legal_moves(state, limit=0), [])

    def test_list_legal_moves_returns_empty_for_blocked_unknown_and_finished_states(self) -> None:
        blocked_state = blocked_blue_state()
        self.assertEqual(list_legal_moves(blocked_state, player="blue"), [])
        self.assertEqual(list_legal_moves(blocked_state, player="orange"), [])
        blocked_state.finished = True
        self.assertEqual(list_legal_moves(blocked_state), [])

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
