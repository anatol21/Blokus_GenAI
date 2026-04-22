"""Core game rules, move generation, and scoring."""

from blokus.config import Coordinate, get_mode_config
from blokus.models import GameState, Move, ValidationResult
from blokus.pieces import PIECES, PIECE_IDS, absolute_cells, piece_sort_key

ORTHOGONAL_DELTAS = ((1, 0), (-1, 0), (0, 1), (0, -1))
DIAGONAL_DELTAS = ((1, 1), (1, -1), (-1, 1), (-1, -1))


def new_game(
    mode: str = "classic",
    controllers: dict[str, str] | None = None,
    strategies: dict[str, str] | None = None,
) -> GameState:
    """Create a fresh game state for a supported mode."""

    config = get_mode_config(mode)
    board = [[None for _ in range(config.board_size)] for _ in range(config.board_size)]
    controller_types = {
        player: (controllers or {}).get(player, "human") for player in config.players
    }
    controller_strategies = {
        player: (strategies or {}).get(player, "default") for player in config.players
    }
    return GameState(
        mode=mode,
        board=board,
        players=config.players,
        start_corners=dict(config.start_corners),
        remaining_pieces={player: set(PIECE_IDS) for player in config.players},
        controller_types=controller_types,
        controller_strategies=controller_strategies,
    )


def board_in_bounds(state: GameState, x: int, y: int) -> bool:
    """Return whether a coordinate lies inside the current board."""

    return 0 <= x < state.board_size and 0 <= y < state.board_size


def get_occupied_cells(state: GameState, player: str | None = None) -> set[Coordinate]:
    """Collect occupied coordinates, optionally filtering to one player."""

    occupied: set[Coordinate] = set()
    for y, row in enumerate(state.board):
        for x, cell in enumerate(row):
            if cell is None:
                continue
            if player is None or cell == player:
                occupied.add((x, y))
    return occupied


def is_first_move(state: GameState, player: str) -> bool:
    """Return whether the player has not yet placed any piece."""

    return not any(cell == player for row in state.board for cell in row)


def _has_edge_contact_with_player(state: GameState, player: str, cells: tuple[Coordinate, ...]) -> bool:
    """Check whether any candidate cell touches the player's color orthogonally."""

    occupied = get_occupied_cells(state, player)
    for x, y in cells:
        for dx, dy in ORTHOGONAL_DELTAS:
            if (x + dx, y + dy) in occupied:
                return True
    return False


def _has_corner_contact_with_player(state: GameState, player: str, cells: tuple[Coordinate, ...]) -> bool:
    """Check whether any candidate cell touches the player's color diagonally."""

    occupied = get_occupied_cells(state, player)
    for x, y in cells:
        for dx, dy in DIAGONAL_DELTAS:
            if (x + dx, y + dy) in occupied:
                return True
    return False


def _validate_move(state: GameState, move: Move, enforce_turn: bool) -> ValidationResult:
    """Validate a move against board bounds, occupancy, and Blokus touch rules."""

    if state.finished:
        return ValidationResult(False, "The game is already finished.", "game_finished")
    if move.player not in state.players:
        return ValidationResult(False, f"Unknown player '{move.player}'.", "unknown_player")
    if enforce_turn and move.player != state.current_player:
        return ValidationResult(
            False,
            f"It is {state.current_player}'s turn, not {move.player}'s turn.",
            "wrong_turn",
        )
    if move.piece not in PIECES:
        return ValidationResult(False, f"Unknown piece '{move.piece}'.", "unknown_piece")
    if move.piece not in state.remaining_pieces[move.player]:
        return ValidationResult(
            False,
            f"Piece '{move.piece}' is no longer available for player '{move.player}'.",
            "piece_unavailable",
        )

    cells = absolute_cells(
        move.piece,
        origin=(move.x, move.y),
        rotation=move.rotation,
        flipped=move.flipped,
    )

    # Reject any move that would leave the board or overwrite an existing square.
    for x, y in cells:
        if not board_in_bounds(state, x, y):
            return ValidationResult(
                False,
                "Move places at least one square outside the board.",
                "out_of_bounds",
            )
        if state.board[y][x] is not None:
            return ValidationResult(
                False,
                "Move overlaps an already occupied square.",
                "overlap",
            )

    if is_first_move(state, move.player):
        start_corner = state.start_corners[move.player]
        # Opening moves must claim the player-specific corner.
        if start_corner not in cells:
            return ValidationResult(
                False,
                f"Opening move for {move.player} must cover start corner {start_corner}.",
            )
        return ValidationResult(True, "Legal opening move.")

    # After the opening move, same-color pieces may only touch at corners.
    if _has_edge_contact_with_player(state, move.player, cells):
        return ValidationResult(
            False,
            "Pieces of the same color may not touch along an edge.",
        )

    # Every non-opening move must extend the player's chain through a corner.
    if not _has_corner_contact_with_player(state, move.player, cells):
        return ValidationResult(
            False,
            "Move must touch at least one same-color piece at a corner.",
            "missing_corner_contact",
        )

    return ValidationResult(True, "Legal move.")


def validate_move(state: GameState, move: Move) -> ValidationResult:
    """Validate a move using the public turn-enforcing rules."""

    return _validate_move(state, move, enforce_turn=True)


def _next_player_index(state: GameState) -> int:
    """Advance to the next player in round-robin order."""

    return (state.current_player_index + 1) % len(state.players)


def _player_search_order(state: GameState, player: str) -> list[str]:
    """Search larger remaining pieces first to surface useful moves early."""

    return sorted(state.remaining_pieces[player], key=piece_sort_key)


def _anchor_cells(state: GameState, player: str) -> set[Coordinate]:
    """Compute empty candidate anchor squares for legal move generation."""

    if is_first_move(state, player):
        return {state.start_corners[player]}

    occupied = get_occupied_cells(state, player)
    anchors: set[Coordinate] = set()
    for x, y in occupied:
        for dx, dy in DIAGONAL_DELTAS:
            anchor = (x + dx, y + dy)
            ax, ay = anchor
            # Anchors must be empty in-bounds squares that do not already violate edge-touch rules.
            if not board_in_bounds(state, ax, ay):
                continue
            if state.board[ay][ax] is not None:
                continue
            if _has_edge_contact_with_player(state, player, (anchor,)):
                continue
            anchors.add(anchor)
    return anchors


def list_legal_moves(
    state: GameState,
    player: str | None = None,
    limit: int | None = None,
) -> list[Move]:
    """Enumerate legal moves for a player, optionally stopping after a limit."""

    active_player = player or state.current_player
    if limit is not None and limit <= 0:
        return []
    if active_player not in state.players or state.finished:
        return []

    anchors = _anchor_cells(state, active_player)
    legal_moves: list[Move] = []
    seen: set[tuple[str, tuple[Coordinate, ...]]] = set()

    for piece_id in _player_search_order(state, active_player):
        for transform in PIECES[piece_id].transforms:
            for anchor_x, anchor_y in anchors:
                for cell_x, cell_y in transform.cells:
                    # Each anchor can be satisfied by aligning any transformed cell with it.
                    origin_x = anchor_x - cell_x
                    origin_y = anchor_y - cell_y
                    absolute = tuple(
                        sorted((origin_x + dx, origin_y + dy) for dx, dy in transform.cells)
                    )
                    key = (piece_id, absolute)
                    if key in seen:
                        continue
                    seen.add(key)
                    move = Move(
                        player=active_player,
                        piece=piece_id,
                        x=origin_x,
                        y=origin_y,
                        rotation=transform.rotation,
                        flipped=transform.flipped,
                    )
                    if _validate_move(state, move, enforce_turn=False).ok:
                        legal_moves.append(move)
                        if limit is not None and len(legal_moves) >= limit:
                            return legal_moves
    return legal_moves


def _all_players_blocked(state: GameState) -> bool:
    """Return whether every player is currently unable to move."""

    return all(not list_legal_moves(state, player=player, limit=1) for player in state.players)


def apply_move(state: GameState, move: Move) -> GameState:
    """Apply a legal move and return the resulting next-turn state."""

    result = validate_move(state, move)
    if not result.ok:
        raise ValueError(result.reason)

    new_state = state.clone()
    cells = absolute_cells(
        move.piece,
        origin=(move.x, move.y),
        rotation=move.rotation,
        flipped=move.flipped,
    )
    # Materialize the piece on the cloned board before advancing turn metadata.
    for x, y in cells:
        new_state.board[y][x] = move.player
    new_state.remaining_pieces[move.player].remove(move.piece)
    new_state.history.append(move)
    new_state.current_player_index = _next_player_index(new_state)
    new_state.consecutive_passes = 0
    new_state.finished = _all_players_blocked(new_state)
    return new_state


def validate_pass(state: GameState, player: str | None = None) -> ValidationResult:
    """Validate that the current player is allowed to pass."""

    active_player = player or state.current_player
    if state.finished:
        return ValidationResult(False, "The game is already finished.")
    if active_player != state.current_player:
        return ValidationResult(
            False,
            f"It is {state.current_player}'s turn, not {active_player}'s turn.",
        )
    if list_legal_moves(state, player=active_player, limit=1):
        return ValidationResult(False, "A player may only pass when no legal move exists.")
    return ValidationResult(True, "Pass is legal.")


def pass_turn(state: GameState, player: str | None = None) -> GameState:
    """Advance the turn without placing a piece when passing is legal."""

    active_player = player or state.current_player
    result = validate_pass(state, player=active_player)
    if not result.ok:
        raise ValueError(result.reason)
    new_state = state.clone()
    new_state.current_player_index = _next_player_index(new_state)
    new_state.consecutive_passes += 1
    new_state.finished = new_state.consecutive_passes >= len(new_state.players) or _all_players_blocked(
        new_state
    )
    return new_state


def score_player(state: GameState, player: str) -> int:
    """Score a player using official remaining-square scoring bonuses."""

    remaining = sum(PIECES[piece_id].size for piece_id in state.remaining_pieces[player])
    score = -remaining
    # Emptying the rack grants the normal 15-point bonus plus 5 more for ending on I1.
    if not state.remaining_pieces[player]:
        score += 15
        player_moves = [move for move in state.history if move.player == player]
        if player_moves and player_moves[-1].piece == "I1":
            score += 5
    return score


def compute_scores(state: GameState) -> dict[str, int]:
    """Compute the score for every player in the current state."""

    return {player: score_player(state, player) for player in state.players}


def occupied_square_counts(state: GameState) -> dict[str, int]:
    counts = {player: 0 for player in state.players}
    for row in state.board:
        for cell in row:
            if cell is not None:
                counts[cell] += 1
    return counts
