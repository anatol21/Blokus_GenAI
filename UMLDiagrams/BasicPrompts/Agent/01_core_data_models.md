# Blokus Core Data Models

```mermaid
classDiagram
    class Move {
        +player: str
        +piece: str
        +x: int
        +y: int
        +rotation: int
        +flipped: bool
        +to_dict() dict
        +from_dict(data) Move
    }

    class ValidationResult {
        +ok: bool
        +reason: str
    }

    class GameState {
        +mode: str
        +board: list[list[str | None]]
        +players: tuple[str]
        +start_corners: dict[str, Coordinate]
        +remaining_pieces: dict[str, set[str]]
        +history: list[Move]
        +current_player_index: int
        +consecutive_passes: int
        +finished: bool
        +controller_types: dict[str, str]
        +controller_strategies: dict[str, str]
        +board_size: int
        +current_player: str
        +clone() GameState
        +to_dict() dict
        +from_dict(data) GameState
    }

    class Transform {
        +rotation: int
        +flipped: bool
        +cells: tuple[Coordinate]
    }

    class PieceDefinition {
        +piece_id: str
        +cells: tuple[Coordinate]
        +transforms: tuple[Transform]
        +size: int
    }

    class ModeConfig {
        +name: str
        +board_size: int
        +players: tuple[str]
        +start_corners: dict[str, Coordinate]
    }

    class ScenarioResult {
        +name: str
        +passed: bool
        +detail: str
    }

    GameState --> Move : history
    GameState --> ModeConfig : mode
    PieceDefinition --> Transform : contains
```

## Description
Represents the core data models in the Blokus engine:
- **Move**: Represents a single piece placement action
- **GameState**: Complete mutable game state containing board, players, and game progress
- **ValidationResult**: Wrapper for move validation success/failure
- **PieceDefinition**: Definition of a piece with all its unique geometric transforms
- **Transform**: One unique orientation of a piece (rotation + flip combination)
- **ModeConfig**: Static configuration for a game mode (board size, players, starting positions)
- **ScenarioResult**: Test fixture result with pass/fail and details
