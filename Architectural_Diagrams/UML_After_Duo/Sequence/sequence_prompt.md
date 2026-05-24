# Prompt

You are an expert software architect with extensive experience in UML design and the Mermaid syntax. Your task is to generate comprehensive Mermaid UML Sequence Diagrams for a Blokus game engine based on the Python codebase in `src/blokus/`.

### Constraints & Formatting Rules
1. **Output ONLY valid Mermaid code** inside ````mermaid ... ```` blocks. 
2. **Multiple Diagrams:** Because Mermaid Live Editor prefers one diagram per block, generate THREE SEPARATE ````mermaid ... ```` blocks, one for each scenario defined below.
3. **Synchronous vs. Return Calls:** Use solid arrows (`->>`) for synchronous method calls and dashed arrows (`-->>`) for return values. Include the returned data types in the return arrow text (e.g., `-->>BlokusGui: ValidationResult`).
4. **Lifelines:** Use `activate` and `deactivate` (or the `+`/`-` shorthand) to accurately reflect the execution lifecycle of the components.
5. **Hide Noise:** Do NOT model internal dictionary lookups (like `PiecesCatalog` or `ModeConfig`) and do NOT model every single mouse movement event (skip `on_motion`). Focus strictly on the core method calls between the components.

### Participants (Use exactly these)
- `actor User`
- `participant CLI as cli.py`
- `participant GUI as BlokusGui`
- `participant Engine as engine.py`
- `participant Players as players.py`
- `participant State as GameState`

### Scenarios to Model

#### 1. Scenario A: Application Startup & Initialization
Model the flow of launching a new game from the terminal.
- The `User` executes the CLI.
- The `CLI` calls `Engine.new_game(mode, controllers, strategies)`.
- The `Engine` initializes and returns a `GameState`.
- The `CLI` instantiates `BlokusGui`, passing it the `GameState`.
- The `CLI` invokes `GUI.run()` to start the game loop.

#### 2. Scenario B: The Human Gameplay Loop
Model a human making a single move using drag-and-drop. Use logical flow blocks!
- **Start:** `User` triggers `on_button_press` to pick up a piece, then `on_button_release` to drop it on the board.
- **Validation:** The `GUI` calls `Engine.validate_move(state, move)`. 
- **Logic Block (`alt`/`else`):** Use an `alt` block to handle the `ValidationResult`. 
  - *If valid:* The `GUI` calls `Engine.apply_move(state, move)`, which mutates the `GameState`. The `GUI` then calls its internal `redraw()` method.
  - *Else (invalid):* The piece returns to the sidebar (no state mutation).

#### 3. Scenario C: The Bot/AI Gameplay Loop
Model the automated turn cycle when an AI plays.
- **Start:** The `GUI`'s event loop triggers `advance_automatic_turns()`.
- **AI Decision:** The `GUI` calls `Players.choose_move(state, player, strategy)`.
- **Querying Rules:** The `Players` module calls `Engine.list_legal_moves(state, player)` to see available options, and then returns a selected `Move` to the `GUI`.
- **Application:** The `GUI` calls `Engine.apply_move(state, move)` to update the `GameState`.
- **Looping:** Use an `opt` or `loop` block to indicate that this process repeats as long as it is a bot's turn.

Analyze the architecture based on these instructions and generate the final Mermaid sequence diagrams.

# Response

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
        Engine->>+State: mutate()
        State-->>-Engine: void
        Engine-->>-GUI: void
        
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
        Engine->>+State: mutate()
        State-->>-Engine: void
        Engine-->>-GUI: void
        
        GUI-->>-GUI: void
    end

# Evaluation Prompt
You are a strict UML evaluator. Score this sequence diagram against the code using integers 1–5:

Completeness: Are all components from the code represented?
Correctness: Are relationships and multiplicities accurate?
Standards Adherence: Is the Mermaid syntax valid?
Comprehensibility: Is the diagram readable?
Terminological Alignment: Do names match the domain?
If any score is below 4, output the corrected Mermaid code. [sequence_prompt.md]

# Response
Here is the evaluation of the three sequence diagrams against the blokus codebase:

1. Completeness: 5 All required participants (User, CLI, GUI, Engine, Players, GameState) and the three prompted scenarios (A, B, C) are fully represented.

2. Correctness: 3 The relationships and method names are mostly accurate, but the data flow and mutability around apply_move() are incorrect. The sequence diagrams show Engine->>State: mutate() returning void, and then Engine-->>GUI: void. In the codebase, GameState is treated as immutable—apply_move() clones the state, applies the move to the clone, and returns the new GameState which the GUI then stores. Furthermore, __init__ in Python returns None, so mapping that to void was acceptable, but apply_move definitively returns GameState.

3. Standards Adherence: 5 The Mermaid syntax itself is fully valid. Lifelines (+/-), participant aliasing (participant CLI as cli.py), and sequence control blocks (loop, alt) are used perfectly to model lifecycle activations and logic.

4. Comprehensibility: 5 The diagrams are extremely readable. The logical flow is clear, and separating them into three distinct scenarios keeps the visual cognitive load low.

5. Terminological Alignment: 5 The terminology aligns perfectly with the domain (ValidationResult, advance_automatic_turns, choose_move, redraw, etc. all match the actual code).


