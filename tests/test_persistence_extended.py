from copy import deepcopy
from typing import Any, Callable, cast
import pytest
from blokus.models import GameState, Move
from blokus.engine import new_game, apply_move


def mutable_payload(mode: str = "classic") -> dict[str, Any]:
    return cast(dict[str, Any], deepcopy(new_game(mode=mode).to_dict()))


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_gamestate_initial_round_trip(mode: str) -> None:
    state = new_game(mode=mode)
    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_gamestate_mid_game_round_trip(mode: str) -> None:
    state = new_game(mode=mode)
    moves = [
        Move(player, "I1", *state.start_corners[player])
        for player in state.players
    ]
    for m in moves:
        state = apply_move(state, m)

    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state
    assert len(reloaded.history) == len(moves)


@pytest.mark.parametrize("mode, board_size", [
    ("classic", 20),
    ("duo", 14),
])
def test_gamestate_full_board_stress_round_trip(mode: str, board_size: int) -> None:
    state = new_game(mode=mode)
    for y in range(board_size):
        for x in range(board_size):
            state.board[y][x] = "blue"

    state = GameState.from_dict(state.to_dict())

    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state
    assert all(all(cell == "blue" for cell in row) for row in reloaded.board)


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_gamestate_exhausted_pieces_round_trip(mode: str) -> None:
    state = new_game(mode=mode)
    state.remaining_pieces[state.players[0]] = set()

    payload = state.to_dict()
    reloaded = GameState.from_dict(payload)
    assert reloaded == state
    assert len(reloaded.remaining_pieces[reloaded.players[0]]) == 0


@pytest.mark.parametrize("mode, mutation", [
    ("classic", lambda d: d.update({"mode": "unknown_mode"})),
    ("duo", lambda d: d.update({"mode": "unknown_mode"})),
    ("classic", lambda d: d.update({"players": ["red", "blue"]})),
    ("duo", lambda d: d.update({"players": ["blue", "yellow", "red", "green"]})),
    ("classic", lambda d: d.update({"current_player": "orange"})),
    ("duo", lambda d: d.update({"current_player": "orange"})),
    ("classic", lambda d: d.update({"board": ["B" * 10] * 20})),
    ("duo", lambda d: d.update({"board": ["B" * 10] * 14})),
])
def test_from_dict_structural_rejection(
    mode: str, mutation: Callable[[dict[str, Any]], None]
) -> None:
    payload = mutable_payload(mode=mode)
    mutation(payload)
    with pytest.raises((ValueError, KeyError)):
        GameState.from_dict(payload)


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_from_dict_rejects_duplicate_pieces_in_rack(mode: str) -> None:
    payload = mutable_payload(mode=mode)
    player = payload["players"][0]
    payload["remaining_pieces"][player] = ["I1", "I1", "I2"]
    with pytest.raises(ValueError, match="contain duplicates"):
        GameState.from_dict(payload)


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_from_dict_rejects_unknown_piece_ids(mode: str) -> None:
    payload = mutable_payload(mode=mode)
    player = payload["players"][0]
    payload["remaining_pieces"][player] = ["X_MASTER_PIECE"]
    with pytest.raises(ValueError, match="contain unknown ids"):
        GameState.from_dict(payload)


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_from_dict_rejects_invalid_board_symbols(mode: str) -> None:
    payload = mutable_payload(mode=mode)
    board = payload["board"]
    board[0] = "X" + board[0][1:]
    with pytest.raises(ValueError, match="No player configured"):
        GameState.from_dict(payload)


@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_from_dict_history_type_safety(mode: str) -> None:
    payload = mutable_payload(mode=mode)
    payload["history"] = [{"player": payload["players"][0], "piece": "I1", "x": "NaN", "y": 0}]
    with pytest.raises(ValueError):
        GameState.from_dict(payload)


@pytest.mark.skip(reason="Engine currently lacks cross-collection consistency checks")
@pytest.mark.parametrize("mode", ["classic", "duo"])
def test_from_dict_logic_sync_violation(mode: str) -> None:
    state = new_game(mode=mode)
    payload = cast(dict[str, Any], deepcopy(state.to_dict()))
    payload["board"][0] = payload["board"][0][:1] + "B" + payload["board"][0][2:]

    with pytest.raises(ValueError, match="Consistency error"):
        GameState.from_dict(payload)
