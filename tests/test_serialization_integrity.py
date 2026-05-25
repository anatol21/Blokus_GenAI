from copy import deepcopy
from typing import Any, Callable, cast
import pytest
from blokus.models import GameState, Move
from blokus.engine import new_game, apply_move


def create_mid_game_state(mode: str = "classic") -> GameState:
    state = new_game(mode=mode)
    for player in state.players:
        state = apply_move(state, Move(player, "I1", *state.start_corners[player]))
    return state


def create_finished_game_state(mode: str = "classic") -> GameState:
    state = create_mid_game_state(mode)
    state.finished = True
    return state


def mutable_payload_from_state(state: GameState | None = None, mode: str = "classic") -> dict[str, Any]:
    source_state = state or new_game(mode=mode)
    return cast(dict[str, Any], deepcopy(source_state.to_dict()))


def test_move_round_trip() -> None:
    original = Move(player="blue", piece="F5", x=5, y=5, rotation=2, flipped=True)
    payload = original.to_dict()
    reloaded = Move.from_dict(payload)

    assert reloaded == original
    assert reloaded.rotation == 2
    assert reloaded.flipped is True


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_gamestate_round_trip(mode: str) -> None:
    for factory in [
        lambda: new_game(mode=mode),
        lambda: create_mid_game_state(mode=mode),
        lambda: create_finished_game_state(mode=mode),
    ]:
        original = factory()
        payload = original.to_dict()
        reloaded = GameState.from_dict(payload)

        assert reloaded == original
        assert reloaded.occupied_cells_by_player == original.occupied_cells_by_player


MUTATION_CASES: list[tuple[str, str, Callable[[dict[str, Any]], None], type[Exception], str]] = [
    ("classic", "missing_mode", lambda d: d.pop("mode"), KeyError, "mode"),
    ("duo", "missing_mode", lambda d: d.pop("mode"), KeyError, "mode"),
    ("classic", "unsupported_mode", lambda d: d.update({"mode": "invalid_mode"}), ValueError, "Unsupported mode"),
    ("duo", "unsupported_mode", lambda d: d.update({"mode": "invalid_mode"}), ValueError, "Unsupported mode"),
    ("classic", "mismatched_players", lambda d: d.update({"players": ["blue", "red"]}), ValueError, "do not match mode"),
    ("duo", "mismatched_players", lambda d: d.update({"players": ["blue", "yellow", "red", "green"]}), ValueError, "do not match mode"),
    ("classic", "wrong_row_count", lambda d: d.update({"board": d["board"][:-1]}), ValueError, "Board must contain exactly 20 rows"),
    ("duo", "wrong_row_count", lambda d: d.update({"board": d["board"][:-1]}), ValueError, "Board must contain exactly 14 rows"),
    ("classic", "wrong_row_length", lambda d: d.update({"board": ["B" * 10] * 20}), ValueError, "Each board row must be a string with length 20"),
    ("duo", "wrong_row_length", lambda d: d.update({"board": ["B" * 10] * 14}), ValueError, "Each board row must be a string with length 14"),
    ("classic", "invalid_symbol", lambda d: d.update({"board": ["Q" + "." * 19] * 20}), ValueError, "No player configured for board symbol"),
    ("duo", "invalid_symbol", lambda d: d.update({"board": ["Q" + "." * 13] * 14}), ValueError, "No player configured for board symbol"),
    ("classic", "invalid_current_player", lambda d: d.update({"current_player": "orange"}), ValueError, "is not part of the mode player order"),
    ("duo", "invalid_current_player", lambda d: d.update({"current_player": "orange"}), ValueError, "is not part of the mode player order"),
    ("classic", "missing_remaining_pieces", lambda d: d.pop("remaining_pieces"), ValueError, "missing 'remaining_pieces'"),
    ("duo", "missing_remaining_pieces", lambda d: d.pop("remaining_pieces"), ValueError, "missing 'remaining_pieces'"),
    ("classic", "duplicate_pieces", lambda d: d["remaining_pieces"].update({"blue": ["I1", "I1"]}), ValueError, "contain duplicates"),
    ("duo", "duplicate_pieces", lambda d: d["remaining_pieces"].update({"blue": ["I1", "I1"]}), ValueError, "contain duplicates"),
    ("classic", "unknown_piece_ids", lambda d: d["remaining_pieces"].update({"blue": ["INVALID_PIECE"]}), ValueError, "contain unknown ids"),
    ("duo", "unknown_piece_ids", lambda d: d["remaining_pieces"].update({"blue": ["INVALID_PIECE"]}), ValueError, "contain unknown ids"),
    ("classic", "board_player_not_in_list", lambda d: d.update({"board": ["O" + "." * 19] * 20}), ValueError, "Board contains player 'orange' not present in players"),
    ("duo", "board_player_not_in_list", lambda d: d.update({"board": ["Y" + "." * 13] * 14}), ValueError, "Board contains player 'yellow' not present in players"),
]

@pytest.mark.parametrize(
    "mode, _id, mutation_fn, expected_error, error_match",
    MUTATION_CASES,
    ids=[f"{mode}_{id_}" for mode, id_, *_ in MUTATION_CASES],
)
def test_from_dict_validation_errors(
    mode: str,
    _id: str,
    mutation_fn: Callable[[dict[str, Any]], None],
    expected_error: type[Exception],
    error_match: str,
) -> None:
    payload = mutable_payload_from_state(mode=mode)
    mutation_fn(payload)
    with pytest.raises(expected_error, match=error_match):
        GameState.from_dict(payload)


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_from_dict_with_corrupted_move_history(mode: str) -> None:
    state = create_mid_game_state(mode=mode)
    payload = mutable_payload_from_state(state)
    payload["history"][0]["x"] = "invalid"
    with pytest.raises(ValueError):
        GameState.from_dict(payload)
