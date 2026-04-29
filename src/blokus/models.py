"""Serializable game models."""

from copy import deepcopy
from dataclasses import dataclass, field

from blokus.config import get_mode_config, player_for_symbol, symbol_for_player
from blokus.pieces import PIECE_IDS

Coordinate = tuple[int, int]


@dataclass(frozen=True)
class Move:
    """One attempted or completed piece placement."""

    player: str
    piece: str
    x: int
    y: int
    rotation: int = 0
    flipped: bool = False

    def to_dict(self) -> dict[str, object]:
        """Serialize a move into JSON-friendly primitives."""

        return {
            "player": self.player,
            "piece": self.piece,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "flipped": self.flipped,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Move":
        """Rebuild a move from JSON-compatible data."""

        return cls(
            player=str(data["player"]),
            piece=str(data["piece"]),
            x=int(data["x"]),
            y=int(data["y"]),
            rotation=int(data.get("rotation", 0)),
            flipped=bool(data.get("flipped", False)),
        )


@dataclass(frozen=True)
class ValidationResult:
    """Simple success/failure wrapper for rule checks."""

    ok: bool
    reason: str
    reason_category: str | None = None


@dataclass
class GameState:
    """Complete mutable game state for one Blokus session."""

    mode: str
    board: list[list[str | None]]
    players: tuple[str, ...]
    start_corners: dict[str, Coordinate]
    remaining_pieces: dict[str, set[str]]
    history: list[Move] = field(default_factory=list)
    current_player_index: int = 0
    consecutive_passes: int = 0
    finished: bool = False
    controller_types: dict[str, str] = field(default_factory=dict)
    controller_strategies: dict[str, str] = field(default_factory=dict)

    @property
    def board_size(self) -> int:
        """Return the board dimension for the active mode."""

        return len(self.board)

    @property
    def current_player(self) -> str:
        """Return the player whose turn is currently active."""

        return self.players[self.current_player_index]

    def clone(self) -> "GameState":
        """Create a deep-enough copy for safe state transitions."""

        return GameState(
            mode=self.mode,
            board=deepcopy(self.board),
            players=self.players,
            start_corners=dict(self.start_corners),
            remaining_pieces={player: set(pieces) for player, pieces in self.remaining_pieces.items()},
            history=list(self.history),
            current_player_index=self.current_player_index,
            consecutive_passes=self.consecutive_passes,
            finished=self.finished,
            controller_types=dict(self.controller_types),
            controller_strategies=dict(self.controller_strategies),
        )

    def to_dict(self) -> dict[str, object]:
        """Serialize the full game state into a JSON-friendly structure."""

        board_rows = [
            "".join(symbol_for_player(cell) if cell else "." for cell in row)
            for row in self.board
        ]
        return {
            "mode": self.mode,
            "board_size": self.board_size,
            "players": list(self.players),
            "start_corners": {player: list(corner) for player, corner in self.start_corners.items()},
            "board": board_rows,
            "remaining_pieces": {
                player: sorted(pieces, key=lambda piece_id: PIECE_IDS.index(piece_id))
                for player, pieces in self.remaining_pieces.items()
            },
            "history": [move.to_dict() for move in self.history],
            "current_player": self.current_player,
            "consecutive_passes": self.consecutive_passes,
            "finished": self.finished,
            "controller_types": dict(self.controller_types),
            "controller_strategies": dict(self.controller_strategies),
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameState":
        """Validate and rebuild a game state from serialized JSON data."""

        mode = str(data["mode"])
        config = get_mode_config(mode)
        players = tuple(data.get("players", config.players))
        if players != config.players:
            raise ValueError(
                f"State players {players!r} do not match mode '{mode}' players {config.players!r}."
            )

        board_rows = data.get("board")
        if not isinstance(board_rows, list) or len(board_rows) != config.board_size:
            raise ValueError(f"Board must contain exactly {config.board_size} rows for mode '{mode}'.")

        board: list[list[str | None]] = []
        for row in board_rows:
            if not isinstance(row, str) or len(row) != config.board_size:
                raise ValueError(
                    f"Each board row must be a string with length {config.board_size}."
                )
            parsed_row: list[str | None] = []
            for symbol in row:
                if symbol == ".":
                    parsed_row.append(None)
                else:
                    parsed_row.append(player_for_symbol(symbol))
            board.append(parsed_row)

        remaining_source = data.get("remaining_pieces")
        if not isinstance(remaining_source, dict):
            raise ValueError("State is missing 'remaining_pieces'.")
        remaining_pieces: dict[str, set[str]] = {}
        for player in players:
            raw_pieces = remaining_source.get(player)
            if not isinstance(raw_pieces, list):
                raise ValueError(f"Remaining pieces for player '{player}' must be a list.")
            piece_ids = [str(piece_id) for piece_id in raw_pieces]
            if len(piece_ids) != len(set(piece_ids)):
                raise ValueError(f"Remaining pieces for player '{player}' contain duplicates.")
            unknown_piece_ids = [piece_id for piece_id in piece_ids if piece_id not in PIECE_IDS]
            if unknown_piece_ids:
                raise ValueError(
                    f"Remaining pieces for player '{player}' contain unknown ids {unknown_piece_ids!r}."
                )
            remaining_pieces[player] = set(piece_ids)

        current_player = str(data.get("current_player", players[0]))
        if current_player not in players:
            raise ValueError(f"Current player '{current_player}' is not part of the mode player order.")

        raw_corners = data.get("start_corners", config.start_corners)
        start_corners = {
            player: tuple(raw_corners[player]) if isinstance(raw_corners, dict) else config.start_corners[player]
            for player in players
        }

        history = [Move.from_dict(item) for item in data.get("history", [])]

        controller_source = data.get("controller_types", {})
        controllers = {
            player: str(controller_source.get(player, "human")) for player in players
        }
        strategy_source = data.get("controller_strategies", {})
        strategies = {
            player: str(strategy_source.get(player, "default")) for player in players
        }

        return cls(
            mode=mode,
            board=board,
            players=players,
            start_corners=start_corners,
            remaining_pieces=remaining_pieces,
            history=history,
            current_player_index=players.index(current_player),
            consecutive_passes=int(data.get("consecutive_passes", 0)),
            finished=bool(data.get("finished", False)),
            controller_types=controllers,
            controller_strategies=strategies,
        )
