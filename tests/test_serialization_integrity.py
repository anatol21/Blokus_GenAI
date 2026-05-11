from typing import Any, Callable
import pytest
from blokus.models import GameState, Move
from blokus.engine import new_game, apply_move

# --- Helpers ---

def create_mid_game_state() -> GameState:
    """Create a game state with a few moves played."""
    state = new_game()
    # Blue opens
    state = apply_move(state, Move("blue", "I1", 0, 0))
    # Yellow opens
    state = apply_move(state, Move("yellow", "I1", 19, 0))
    # Red opens
    state = apply_move(state, Move("red", "I1", 19, 19))
    # Green opens
    state = apply_move(state, Move("green", "I1", 0, 19))
    return state

def create_finished_game_state() -> GameState:
    """Create a game state that is marked as finished."""
    state = create_mid_game_state()
    state.finished = True
    return state

# --- Round-Trip Integrity Tests ---

def test_move_round_trip() -> None:
    """Verify that a Move object survives serialization round-trip."""
    original = Move(player="blue", piece="F", x=10, y=10, rotation=2, flipped=True)
    payload = original.to_dict()
    reloaded = Move.from_dict(payload)
    
    assert reloaded == original
    assert reloaded.rotation == 2
    assert reloaded.flipped is True

@pytest.mark.parametrize("state_factory", [
    new_game,
    create_mid_game_state,
    create_finished_game_state
], ids=["initial", "mid_game", "finished"])
def test_gamestate_round_trip(state_factory: Callable[[], GameState]) -> None:
    """Verify that GameState survives serialization round-trip in all phases."""
    original = state_factory()
    payload = original.to_dict()
    reloaded = GameState.from_dict(payload)
    
    # Direct object equality via dataclass __eq__
    assert reloaded == original
    
    # Verify derived state (cache) is also identical
    assert reloaded.occupied_cells_by_player == original.occupied_cells_by_player

# --- Defensive Loading Tests ---

@pytest.mark.parametrize("mutation_fn, expected_error, error_match", [
    (lambda d: d.pop("mode"), KeyError, "mode"),
    (lambda d: d.update({"mode": "invalid_mode"}), ValueError, "Unsupported mode"),
    (lambda d: d.update({"players": ["blue", "red"]}), ValueError, "do not match mode"),
    (lambda d: d.update({"board": d["board"][:-1]}), ValueError, "Board must contain exactly 20 rows"),
    (lambda d: d.update({"board": ["B" * 10] * 20}), ValueError, "Each board row must be a string with length 20"),
    (lambda d: d.update({"board": ["Q" + "." * 19] * 20}), ValueError, "No player configured for board symbol"),
    (lambda d: d.update({"current_player": "orange"}), ValueError, "is not part of the mode player order"),
    (lambda d: d.pop("remaining_pieces"), ValueError, "missing 'remaining_pieces'"),
    (lambda d: d["remaining_pieces"].update({"blue": ["I1", "I1"]}), ValueError, "contain duplicates"),
    (lambda d: d["remaining_pieces"].update({"blue": ["INVALID_PIECE"]}), ValueError, "contain unknown ids"),
    (lambda d: d.update({"board": ["O" + "." * 19] * 20}), ValueError, "Board contains player 'orange' not present in players"),
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
    """Verify that from_dict raises appropriate errors for malformed data."""
    valid_state = new_game()
    payload: dict[str, Any] = valid_state.to_dict()
    
    # Apply mutation to corrupt the payload
    mutation_fn(payload)
    
    with pytest.raises(expected_error, match=error_match):
        GameState.from_dict(payload)

def test_from_dict_with_corrupted_move_history() -> None:
    """Verify history items are also validated."""
    state = create_mid_game_state()
    payload: dict[str, Any] = state.to_dict()
    
    # Corrupt one move in history
    payload["history"][0]["x"] = "invalid" # Should cause ValueError when calling int()
    
    with pytest.raises(ValueError):
        GameState.from_dict(payload)
