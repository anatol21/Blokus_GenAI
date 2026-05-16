"""Mode and symbol configuration."""

from dataclasses import dataclass

Coordinate = tuple[int, int]


@dataclass(frozen=True)
class ModeConfig:
    """Static rule parameters for a supported game mode."""

    name: str
    board_size: int
    players: tuple[str, ...]
    start_corners: dict[str, Coordinate]


CLASSIC_CONFIG = ModeConfig(
    name="classic",
    board_size=20,
    players=("blue", "yellow", "red", "green"),
    start_corners={
        "blue": (0, 0),
        "yellow": (19, 0),
        "red": (19, 19),
        "green": (0, 19),
    },
)

DUO_CONFIG = ModeConfig(
    name="duo",
    board_size=14,
    players=("blue", "red"),  # 2 players only
    start_corners={
        "blue": (4, 4),
        "red": (9, 9),
    },
)

MODE_CONFIGS = {
    CLASSIC_CONFIG.name: CLASSIC_CONFIG,
    DUO_CONFIG.name: DUO_CONFIG,
}

PLAYER_SYMBOLS = {
    "blue": "B",
    "yellow": "Y",
    "red": "R",
    "green": "G",
    "orange": "O",
}

SYMBOL_PLAYERS = {symbol: player for player, symbol in PLAYER_SYMBOLS.items()}


def get_mode_config(name: str) -> ModeConfig:
    """Return the configuration for a named mode or raise a helpful error."""

    try:
        return MODE_CONFIGS[name]
    except KeyError as exc:
        supported = ", ".join(sorted(MODE_CONFIGS))
        raise ValueError(f"Unsupported mode '{name}'. Supported modes: {supported}.") from exc


def symbol_for_player(player: str) -> str:
    """Translate an internal player id into the one-character board symbol."""

    try:
        return PLAYER_SYMBOLS[player]
    except KeyError as exc:
        raise ValueError(f"No board symbol configured for player '{player}'.") from exc


def player_for_symbol(symbol: str) -> str:
    """Translate a serialized board symbol back into a player id."""

    try:
        return SYMBOL_PLAYERS[symbol]
    except KeyError as exc:
        raise ValueError(f"No player configured for board symbol '{symbol}'.") from exc
