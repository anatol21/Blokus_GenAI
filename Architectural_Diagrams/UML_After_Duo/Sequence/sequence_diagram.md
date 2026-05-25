## Sequence Diagram: Scenario A - Application Startup & Initialization

sequenceDiagram
    actor User
    participant CLI as cli.py
    participant GUI as BlokusGui
    participant Engine as engine.py
    participant Players as players.py
    participant State as GameState

    User->>+CLI: execute()
    
    CLI->>+Engine: new_game(mode, controllers, strategies)
    Engine-->>-CLI: GameState
    
    CLI->>+GUI: __init__(GameState)
    GUI-->>-CLI: void
    
    CLI->>+GUI: run()
    GUI-->>-CLI: void
    
    CLI-->>-User: void


## Sequence Diagram: Scenario B - Human Gameplay Loop

sequenceDiagram
    actor User
    participant CLI as cli.py
    participant GUI as BlokusGui
    participant Engine as engine.py
    participant Players as players.py
    participant State as GameState

    User->>+GUI: on_button_press()
    GUI-->>-User: void
    
    User->>+GUI: on_button_release()
    
    GUI->>+Engine: validate_move(state, move)
    Engine-->>-GUI: ValidationResult
    
    alt ValidationResult is Valid
        GUI->>+Engine: apply_move(state, move)
        Engine->>+State: clone()
        State-->>-Engine: GameState
        Engine-->>-GUI: GameState
        
        GUI->>+GUI: redraw()
        GUI-->>-GUI: void
    else ValidationResult is Invalid
        GUI->>+GUI: return piece to sidebar
        GUI-->>-GUI: void
    end
    
    GUI-->>-User: void


## Sequence Diagram: Scenario C - The Bot/AI Gameplay Loop

sequenceDiagram
    actor User
    participant CLI as cli.py
    participant GUI as BlokusGui
    participant Engine as engine.py
    participant Players as players.py
    participant State as GameState

    loop While bot's turn
        GUI->>+GUI: advance_automatic_turns()
        
        GUI->>+Players: choose_move(state, player, strategy)
        
        Players->>+Engine: list_legal_moves(state, player)
        Engine-->>-Players: list[Move]
        
        Players-->>-GUI: Move
        
        GUI->>+Engine: apply_move(state, move)
        Engine->>+State: clone()
        State-->>-Engine: GameState
        Engine-->>-GUI: GameState
        
        GUI-->>-GUI: void
    end

    