from copy import deepcopy
from typing import Any, Callable, cast
import pytest
from blokus.models import GameState, Move
from blokus.engine import new_game, apply_move

def mutable_payload() -> dict[str, Any]:
    return cast(dict[str, Any], deepcopy(new_game(mode="duo").to_dict()))

def test_gamestate_mid_game_round_trip() -> None:
    state = new_game(mode="duo")
    state = apply_move(state, Move("blue", "I1", 4, 4))
    state = apply_move(state, Move("red", "I1", 9, 9))
    
    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state
    assert reloaded.current_player == "blue"
    assert len(reloaded.history) == 2

def test_gamestate_full_board_stress_round_trip() -> None:
    state = new_game(mode="duo")
    for y in range(14):
        for x in range(14):
            state.board[y][x] = "blue"
    
    state = GameState.from_dict(state.to_dict())
    
    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state
    assert all(all(cell == "blue" for cell in row) for row in reloaded.board)

@pytest.mark.parametrize("mutation", [
    lambda d: d.update({"mode": "unknown_mode"}),
    lambda d: d.update({"players": ["blue", "yellow", "red", "green"]}),  # Wrong count for duo
    lambda d: d.update({"current_player": "orange"}),
    lambda d: d.update({"board": ["B" * 10] * 14}), # Wrong row length
])
def test_from_dict_structural_rejection(mutation: Callable[[dict[str, Any]], None]) -> None:
    payload = mutable_payload()
    mutation(payload)
    with pytest.raises((ValueError, KeyError)):
        GameState.from_dict(payload)
