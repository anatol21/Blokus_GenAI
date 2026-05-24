# Blokus Game Flow Sequence

```mermaid
sequenceDiagram
    participant User as User/CLI/GUI
    participant CLI as CLI Module
    participant Engine as Game Engine
    participant Models as Data Models
    participant Players as Players Module
    participant State as GameState

    User->>CLI: cmd_new(mode, controllers)
    CLI->>Engine: new_game(mode, controllers)
    Engine->>Models: Create GameState
    Engine-->>CLI: GameState
    CLI->>Models: state.to_dict()
    CLI-->>User: JSON output

    User->>CLI: cmd_apply(state, move)
    CLI->>Models: Load GameState
    
    CLI->>Engine: validate_move(state, move)
    Engine->>State: Check Move Validity
    Engine-->>CLI: ValidationResult
    
    alt Move is Valid
        CLI->>Engine: apply_move(state, move)
        Engine->>Engine: list_legal_moves()
        alt Legal moves exist
            Engine->>State: Update GameState
        else No legal moves
            Engine->>Engine: pass_turn()
            Engine->>State: Check for consecutive passes
        end
        Engine-->>CLI: New GameState
        CLI-->>User: Updated state.json
    else Move is Invalid
        CLI-->>User: Error message
    end

    User->>Players: choose_move(state, strategy)
    Players->>Engine: list_legal_moves()
    Engine-->>Players: Available moves
    Players-->>User: Selected move
```

## Description
Typical game flow interactions:

### Game Initialization
1. User requests new game with mode and controller configuration
2. CLI calls engine to create GameState
3. Engine creates board, initializes players, and loads all pieces
4. State is serialized to JSON and returned

### Move Execution
1. User (or GUI) submits a move
2. CLI loads the current game state
3. Engine validates the move against Blokus rules
4. If valid:
   - Move is applied to the state
   - Engine generates legal moves for next player
   - If legal moves exist, turn advances normally
   - If no legal moves, pass_turn() is called and pass counter increments
5. Updated state is serialized and returned

### AI Move Selection
1. Player module requests move for current player
2. Module queries engine for all legal moves
3. Module selects move based on strategy (e.g., prefer larger pieces)
4. Move is returned for execution
