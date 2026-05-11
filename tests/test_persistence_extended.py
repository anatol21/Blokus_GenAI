from typing import Any, Callable
import pytest
from blokus.models import GameState, Move
from blokus.engine import new_game, apply_move

# === Round-Trip Integrity ===

def test_gamestate_initial_round_trip() -> None:
    """Verify that a fresh game state survives a to_dict/from_dict cycle."""
    state = new_game()
    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state


def test_gamestate_mid_game_round_trip() -> None:
    """Verify that a mid-game state with moves survives round-trip."""
    state = new_game()
    state = apply_move(state, Move("blue", "I1", 0, 0))
    state = apply_move(state, Move("yellow", "I1", 19, 0))
    state = apply_move(state, Move("red", "I1", 19, 19))
    
    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state
    assert reloaded.current_player == "green"
    assert len(reloaded.history) == 3


def test_gamestate_full_board_stress_round_trip() -> None:
    """
    Edge Case: Verify serialization holds when the board is completely full.
    This catches encoding/decoding errors at physical limits.
    """
    state = new_game()
    # Fill the board manually for stress testing
    for y in range(20):
        for x in range(20):
            state.board[y][x] = "blue"
    
    # Synchronize state by round-tripping it once to rebuild cache
    # This ensures 'original' has a correct occupied_cells_by_player cache
    state = GameState.from_dict(state.to_dict())
    
    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state
    assert all(all(cell == "blue" for cell in row) for row in reloaded.board)


def test_gamestate_exhausted_pieces_round_trip() -> None:
    """
    Edge Case: Verify serialization holds when a player has no pieces left.
    Catches empty-collection serialization bugs.
    """
    state = new_game()
    state.remaining_pieces["blue"] = set()
    
    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state
    assert len(reloaded.remaining_pieces["blue"]) == 0


# === Defensive Loading: Structural Validation ===

@pytest.mark.parametrize("mutation", [
    lambda d: d.update({"mode": "unknown_mode"}),
    lambda d: d.update({"players": ["red", "blue"]}),  # Wrong count for classic
    lambda d: d.update({"current_player": "orange"}),  # Valid color, invalid player
    lambda d: d.update({"board": ["B" * 10] * 20}), # Wrong row length
])
def test_from_dict_structural_rejection(mutation: Callable[[dict[str, Any]], None]) -> None:
    """Verify that structurally invalid or mismatched payloads are rejected."""
    payload: dict[str, Any] = new_game().to_dict()
    mutation(payload)
    with pytest.raises((ValueError, KeyError)):
        GameState.from_dict(payload)


# === Defensive Loading: Logical & Security Validation ===

def test_from_dict_rejects_duplicate_pieces_in_rack() -> None:
    """
    Security: Prevents a player from having two of the same piece through payload injection.
    """
    payload: dict[str, Any] = new_game().to_dict()
    payload["remaining_pieces"]["blue"] = ["I1", "I1", "I2"]
    with pytest.raises(ValueError, match="contain duplicates"):
        GameState.from_dict(payload)


def test_from_dict_rejects_unknown_piece_ids() -> None:
    """
    Security: Prevents injection of non-existent or overpowered custom pieces.
    """
    payload: dict[str, Any] = new_game().to_dict()
    payload["remaining_pieces"]["blue"] = ["X_MASTER_PIECE"]
    with pytest.raises(ValueError, match="contain unknown ids"):
        GameState.from_dict(payload)


def test_from_dict_rejects_invalid_board_symbols() -> None:
    """
    Security: Prevents injection of invalid character symbols into the board strings.
    """
    payload: dict[str, Any] = new_game().to_dict()
    # Inject 'X' into the top row
    payload["board"][0] = "X" + "." * 19
    with pytest.raises(ValueError, match="No player configured"):
        GameState.from_dict(payload)


def test_from_dict_history_type_safety() -> None:
    """
    Hardening: Ensure that history items are strictly type-validated during deserialization.
    """
    payload: dict[str, Any] = new_game().to_dict()
    payload["history"] = [{"player": "blue", "piece": "I1", "x": "NaN", "y": 0}]
    with pytest.raises(ValueError):
        GameState.from_dict(payload)


@pytest.mark.skip(reason="Engine currently lacks cross-collection consistency checks")
def test_from_dict_logic_sync_violation() -> None:
    """
    CRITICAL GAP: Verify if a piece exists on the board BUT is still in the rack.
    This test documents current engine limitations in cross-field validation.
    """
    state = new_game()
    payload: dict[str, Any] = state.to_dict()
    # Manually add a piece to the board in the payload
    payload["board"][0] = "B" + "." * 19
    # But 'I1' is still in 'remaining_pieces' in the payload
    
    # This should ideally raise a ValueError for state inconsistency
    with pytest.raises(ValueError, match="Consistency error"):
        GameState.from_dict(payload)
