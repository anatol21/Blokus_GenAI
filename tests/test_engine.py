import unittest

from blokus.engine import (
    apply_move,
    compute_scores,
    list_legal_moves,
    new_game,
    pass_turn,
    score_player,
    validate_move,
    validate_pass,
)
from blokus.models import Move
from blokus.pieces import absolute_cells


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
        self.assertIsInstance(result.reason, str)
        self.assertIn("It is blue's turn", result.reason)
        self.assertEqual(result.reason_category, "wrong_turn")

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

    def test_apply_move_matches_exact_opening_transition_contract(self) -> None:
        state = new_game()
        move = Move("blue", "I1", 0, 0, rotation=0, flipped=False)

        next_state = apply_move(state, move)

        expected_blue_pieces = [
            piece_id for piece_id in state.to_dict()["remaining_pieces"]["blue"] if piece_id != "I1"
        ]
        expected_post_state = {
            "mode": "classic",
            "board_size": 20,
            "players": ["blue", "yellow", "red", "green"],
            "start_corners": {
                "blue": [0, 0],
                "yellow": [19, 0],
                "red": [19, 19],
                "green": [0, 19],
            },
            "board": ["B..................."] + ["...................."] * 19,
            "remaining_pieces": {
                "blue": expected_blue_pieces,
                "yellow": state.to_dict()["remaining_pieces"]["yellow"],
                "red": state.to_dict()["remaining_pieces"]["red"],
                "green": state.to_dict()["remaining_pieces"]["green"],
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
        }

        self.assertEqual(next_state.to_dict(), expected_post_state)

    def test_pass_requires_player_to_be_blocked(self) -> None:
        state = new_game()
        with self.assertRaisesRegex(ValueError, "only pass when no legal move exists"):
            pass_turn(state)

    def test_unknown_player_is_rejected(self) -> None:
        state = new_game()
        result = validate_move(state, Move("orange", "I1", 0, 0))
        self.assertFalse(result.ok)
        self.assertIsInstance(result.reason, str)
        self.assertIn("Unknown player", result.reason)
        self.assertEqual(result.reason_category, "unknown_player")

    def test_unknown_piece_is_rejected(self) -> None:
        state = new_game()
        result = validate_move(state, Move("blue", "NOPE", 0, 0))
        self.assertFalse(result.ok)
        self.assertIsInstance(result.reason, str)
        self.assertIn("Unknown piece", result.reason)
        self.assertEqual(result.reason_category, "unknown_piece")

    def test_spent_piece_reuse_is_rejected(self) -> None:
        state = play_standard_opening_cycle()
        result = validate_move(state, Move("blue", "I1", 1, 1))
        self.assertFalse(result.ok)
        self.assertIsInstance(result.reason, str)
        self.assertIn("no longer available", result.reason)
        self.assertEqual(result.reason_category, "piece_unavailable")

    def test_rack_unavailable_failure_precedes_spatial_checks_for_spent_piece(self) -> None:
        state = play_standard_opening_cycle()
        result = validate_move(state, Move("blue", "I1", -1, 0))
        self.assertFalse(result.ok)
        self.assertIsInstance(result.reason, str)
        self.assertIn("no longer available", result.reason)
        self.assertEqual(result.reason_category, "piece_unavailable")

    def test_negative_coordinate_move_is_rejected(self) -> None:
        state = new_game()
        result = validate_move(state, Move("blue", "I1", -1, 0))
        self.assertFalse(result.ok)
        self.assertIn("outside the board", result.reason)

    def test_out_of_bounds_moves_are_rejected_without_mutation(self) -> None:
        for move in (Move("blue", "I1", -1, 0), Move("blue", "I2", 19, 0)):
            with self.subTest(move=move):
                state = new_game()
                before = state.to_dict()
                result = validate_move(state, move)
                after = state.to_dict()
                self.assertFalse(result.ok)
                self.assertEqual(result.reason_category, "out_of_bounds")
                self.assertEqual(after, before)

    def test_overlap_move_is_rejected_without_mutation(self) -> None:
        state = play_standard_opening_cycle()
        before = state.to_dict()
        result = validate_move(state, Move("blue", "I2", 19, 0, rotation=1))
        after = state.to_dict()
        self.assertFalse(result.ok)
        self.assertEqual(result.reason_category, "overlap")
        self.assertEqual(after, before)

    def test_disconnected_follow_up_move_is_rejected_without_mutation(self) -> None:
        state = play_standard_opening_cycle()
        before = state.to_dict()
        result = validate_move(state, Move("blue", "I2", 2, 2))
        after = state.to_dict()
        self.assertFalse(result.ok)
        self.assertEqual(result.reason_category, "missing_corner_contact")
        self.assertEqual(after, before)

    def test_finished_game_rejects_move_without_mutation(self) -> None:
        state = new_game()
        state.finished = True
        before = state.to_dict()
        result = validate_move(state, Move("blue", "I1", 0, 0))
        after = state.to_dict()
        self.assertFalse(result.ok)
        self.assertEqual(result.reason_category, "game_finished")
        self.assertIn("already finished", result.reason)
        self.assertEqual(after, before)

    def test_apply_move_does_not_mutate_state_on_failure(self) -> None:
        state = new_game()
        before = state.to_dict()
        with self.assertRaisesRegex(ValueError, "must cover start corner"):
            apply_move(state, Move("blue", "I1", 1, 1))
        self.assertEqual(state.to_dict(), before)

    def test_apply_move_illegal_opening_raises_without_mutation(self) -> None:
        state = new_game()
        before = state.to_dict()

        with self.assertRaises(ValueError):
            apply_move(state, Move("blue", "I1", 1, 0))

        after = state.to_dict()
        self.assertEqual(after, before)

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
