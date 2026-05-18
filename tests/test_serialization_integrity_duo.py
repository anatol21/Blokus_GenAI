from copy import deepcopy
from typing import Any, Callable, cast
import pytest
from blokus.models import GameState, Move
from blokus.engine import new_game, apply_move

def create_mid_game_state_duo() -> GameState:
    """Create a duo game state with a few moves played."""
    state = new_game(mode="duo")
    state = apply_move(state, Move("blue", "I1", 4, 4))
    state = apply_move(state, Move("red", "I1", 9, 9))
    state = apply_move(state, Move("blue", "I2", 3, 5, rotation=1))
    return state

def create_finished_game_state_duo() -> GameState:
    """Create a duo game state that is marked as finished."""
    state = create_mid_game_state_duo()
    state.finished = True
    return state

def mutable_payload_from_state(state: GameState | None = None) -> dict[str, Any]:
    source_state = state or new_game(mode="duo")
    return cast(dict[str, Any], deepcopy(source_state.to_dict()))

def test_move_round_trip() -> None:
    original = Move(player="blue", piece="F5", x=5, y=5, rotation=2, flipped=True)
    payload = original.to_dict()
    reloaded = Move.from_dict(payload)
    
    assert reloaded == original
    assert reloaded.rotation == 2
    assert reloaded.flipped is True

@pytest.mark.parametrize("state_factory", [
    lambda: new_game(mode="duo"),
    create_mid_game_state_duo,
    create_finished_game_state_duo
], ids=["initial", "mid_game", "finished"])
def test_gamestate_round_trip(state_factory: Callable[[], GameState]) -> None:
    original = state_factory()
    payload = original.to_dict()
    reloaded = GameState.from_dict(payload)
    
    assert reloaded == original
    assert reloaded.occupied_cells_by_player == original.occupied_cells_by_player

@pytest.mark.parametrize("mutation_fn, expected_error, error_match", [
    (lambda d: d.pop("mode"), KeyError, "mode"),
    (lambda d: d.update({"mode": "invalid_mode"}), ValueError, "Unsupported mode"),
    (lambda d: d.update({"players": ["blue", "yellow", "red", "green"]}), ValueError, "do not match mode"),
    (lambda d: d.update({"board": d["board"][:-1]}), ValueError, "Board must contain exactly 14 rows"),
    (lambda d: d.update({"board": ["B" * 10] * 14}), ValueError, "Each board row must be a string with length 14"),
    (lambda d: d.update({"board": ["Q" + "." * 13] * 14}), ValueError, "No player configured for board symbol"),
    (lambda d: d.update({"current_player": "orange"}), ValueError, "is not part of the mode player order"),
    (lambda d: d.pop("remaining_pieces"), ValueError, "missing 'remaining_pieces'"),
    (lambda d: d["remaining_pieces"].update({"blue": ["I1", "I1"]}), ValueError, "contain duplicates"),
    (lambda d: d["remaining_pieces"].update({"blue": ["INVALID_PIECE"]}), ValueError, "contain unknown ids"),
    (lambda d: d.update({"board": ["Y" + "." * 13] * 14}), ValueError, "Board contains player 'yellow' not present in players"),
], ids=[
    "missing_mode",
    "unsupported_mode",
    "mismatched_players",
    "wrong_row_count",
    "wrong_row_length",
    "invalid_symbol",
    "invalid_current_player",
    "missing_remaining_pieces",
    "duplicate_pieces",
    "unknown_piece_ids",
    "board_player_not_in_list"
])
def test_from_dict_validation_errors(
    mutation_fn: Callable[[dict[str, Any]], None],
    expected_error: type[Exception],
    error_match: str
) -> None:
    payload = mutable_payload_from_state()
    mutation_fn(payload)
    with pytest.raises(expected_error, match=error_match):
        GameState.from_dict(payload)

def test_from_dict_with_corrupted_move_history() -> None:
    state = create_mid_game_state_duo()
    payload = mutable_payload_from_state(state)
    payload["history"][0]["x"] = "invalid" 
    with pytest.raises(ValueError):
        GameState.from_dict(payload)
