# Guideline 3: UML Specifcation
UML's to generate: Component, Class, and Sequence diagrams.
## Stage 1: Inputs
Architecture and Design is already selected and implemented. Agent needs to understand it and create UML diagrams for it.
Use Mermaid UML.
*Test: To reduce syntax errors, provide few-shot examples from the official Mermaid or PlantUML documentation in your prompt.*

## Stage 2: Prompting Strategy
For each diagram, follow these steps:
- extract entities from code → define relationships → format output → validate
- For behavioral features, use a two-step pipeline: generate the static model first
specify target syntax clearly: 
Output strictly in valid MermaidLLM code". Forbid conversational text outside code blocks. Demand concrete data types (no `<Type>` placeholders), visibility markers (`+`, `#`, `-`), and valid arrow syntax. Explicitly request advanced constructs (e.g. enumerations) 

Explicitly tell the LLM what *not* to do: (not relevant since the functions already have names)
- No database tables, REST endpoints, or infrastructure in domain models.
- No generic setters — use named state transitions (e.g., `activateAccount()` instead of `setStatus("active")`).
- No dual representations (e.g., both an Enumeration and subclasses for the same type).
- No modeling of temporary method parameters as structural associations.

## UML Generation 
**Class Diagrams:**
(a) extract entities and roles, (b) define attributes with concrete types, (c) decide inheritance and interfaces, (d) assign associations with multiplicities, and (e) sanity-check the syntax before outputting the final code.

**Sequence Diagrams:**
- Test: Do not rely on the LLM to decide when to use `loop`, `alt`, or `opt` fragments. Explicitly instruct which actions are cyclic, which are conditional, and which are optional. Without this, the LLM either scatters actions randomly or creates unreadably deep nesting.
- I believe LLM's will be able to generate cyclic, conditional and optional actions from the implemented code. 

**Component Diagrams:**


## LLM as a judge
Open a fresh LLM session and provide a strict 1–5 scoring rubric covering: (1) Completeness — are all requirements represented? (2) Correctness — are relationships and multiplicities accurate? (3) Standards adherence — is the UML/PlantUML/Mermaid syntax valid? (4) Comprehensibility — is the diagram readable? (5) Terminological alignment — do names match the domain language? Limit the validator to finding missing elements and fixing relationship errors. Do not let it redesign the class hierarchy.


------------------
## Repository Overview - Class Diagram

To generate a class diagram focusing purely on the game's internal data structures, state management, and engine, the following files are the most relevant:

### Core Data Models & State (Highly Relevant)
These files contain the primary classes that define the state and components of the game:
*   **`src/blokus/models.py`**: This is the absolute center of the game's architecture. It contains:
    *   `GameState`: Represents the complete, mutable state of a Blokus session (the board, history, players, remaining pieces).
    *   `Move`: Represents a single attempted or completed piece placement.
    *   `ValidationResult`: A simple wrapper for the result of rule checks.
*   **`src/blokus/pieces.py`**: Manages the geometric representation of the polyominoes.
    *   `PieceDefinition`: Defines the shape structure and pre-calculates variants.
    *   `Transform`: Represents the rotation and flip states of a piece.
*   **`src/blokus/config.py`**: Defines the static rules for different game variations (Standard vs. Duo).
    *   `ModeConfig`: Configuration class for board size, player count, and starting corners.

### Engine Logic (Functional Modules)
While you asked for a *class* diagram, it's worth noting that the core execution logic in this repository is designed using pure functions rather than object-oriented engine classes. Depending on your UML tool, you may still want to represent these modules conceptually:
*   **`src/blokus/engine.py`**: The central rule engine. It contains purely functional logic like `apply_move`, `validate_move`, and `score_player` that operate on the `GameState`.
*   **`src/blokus/players.py`**: Contains the decision-making functions (`choose_move`, `choose_simple_move`) for various player strategies (Human vs. AI).

### Graphical Interface
If your diagram should also cover how the game engine interacts with the screen, you would include:
*   **`src/blokus/gui.py`**: Contains `BlokusGui`, `DragState`, and `PieceRenderLayout`.
*   **`src/blokus/gui_support.py`**: Contains `BoardMetrics` and `SidebarPieceSlot`.

### Files to  Exclude
To keep the diagram focused purely on the game and engine (and per your request):
*   **`src/blokus/review/*`**: The entire directory containing agentic review tools (`coordinator.py`, `renderer.py`, etc.).
*   **`src/blokus/automation.py` & `src/blokus/evaluate.py`**: Used for autonomous testing and scenario evaluation.
*   **`src/blokus/cli.py`**: The command-line entry points.

## Repository Overview - Sequence Diagram

Game Initialization Flow (cli.py):
1. User runs `blokus new --mode classic` or `blokus play` in the terminal.
2. CLI parses arguments and delegates to `cli.cmd_new()` (or `cmd_play`).
3. CLI calls `engine.new_game(mode, controllers)`.
4. Engine calls `config.get_mode_config(mode)` to fetch the board size and players.
5. Engine initializes and returns a fresh `GameState` object.
6. CLI optionally serializes it to disk via `_dump_json()` or renders it to the terminal.

Import Game Flow (cli.py):
1. User runs blokus --load <file.json> ...
2. cli._load_state() opens the file and parses the JSON.
3. Calls GameState.from_dict(data) to rebuild the structural state.
4. Calls engine.validate_loaded_state(loaded_state) to ensure the imported JSON isn't corrupted or mathematically impossible (e.g., verifying piece counts against the board).

Export Game Flow (cli.py):
1. User runs blokus --save <file.json> or blokus export <file.json>.
2. CLI calls GameState.to_dict() to serialize the current game memory.
3. cli._dump_json() writes it to the disk.

## Repository Overview - Component Diagram

The system is divided into four primary logical components:

1. **Models & Config Component** (`models.py`, `config.py`, `pieces.py`)
   - Defines the core data structures (`GameState`, `Move`) and game constraints.
   - Has NO outgoing dependencies.

2. **Core Engine Component** (`engine.py`, `players.py`)
   - Functional module containing the rules, move validation, and AI logic.
   - Depends strictly on the Models & Config component.

3. **CLI Component** (`cli.py`)
   - Handles terminal execution, JSON state import/export, and headless play.
   - Depends on Engine and Models.

4. **GUI Component** (`gui.py`, `gui_support.py`, `gui_assets.py`, `render.py`)
   - Handles the Tkinter visual client, user interactions, and visual layout.
   - Depends on Engine and Models.

*Excluded:* `review/*`, `evaluate.py`, and `automation.py` should be excluded to focus strictly on the playable game architecture.


