# Prompt for high level Component Diagram
You are an expert software architect with extensive experience in UML design. Your task is to generate a comprehensive, highly accurate Mermaid UML Component Diagram for a Blokus game engine.

### Constraints & Formatting Rules
1. **Output ONLY valid Mermaid code** inside a ````mermaid ... ```` block. The code must be fully compatible with the Mermaid Live Editor. You may use a `classDiagram` with `<<component>>` stereotypes or standard structural `flowchart TD` to represent components and interfaces.
2. **Hide Granular Implementation Details:** Do NOT model internal data classes like `DragState`, `ValidationResult`, or `PieceRenderLayout`. Focus strictly on the high-level components and the APIs/interfaces they expose.
3. **Use Explicit Interfaces:** Show dependencies pointing from a component to the interface (API) provided by another component, rather than pointing directly at internal files.
4. **Annotate Dependencies:** Label your dependency arrows (e.g., `uses`, `requires`, `invokes`, `provides`) to clarify the data flow and architectural hierarchy.

### Project Scope & Exclusions
- **TARGET DIRECTORY**: `src/blokus/`
- **CRITICAL EXCLUSIONS**: You MUST completely ignore the `src/blokus/review/` directory, `evaluate.py`, and any test files. They are meta-tooling and not part of the game architecture.

### Architectural Components to Model
Group the system into the following four primary components and model how they interact:

#### 1. Component: Models_and_Config
- **Role:** The foundational data layer containing state and definitions.
- **Internal Elements:** `models.py`, `config.py`, `pieces.py`
- **Exposed Interface:** Provides the raw data structures (`GameState`, `Move`, `ModeConfig`, `PIECES`).
- **Dependencies:** This component has ZERO outgoing dependencies.

#### 2. Component: Core_Engine
- **Role:** The rules engine and AI logic center.
- **Internal Elements:** `engine.py`, `players.py`
- **Exposed Interface:** Provides an `IGameRules` or `EngineAPI` interface containing operations like `new_game()`, `apply_move()`, and `list_legal_moves()`.
- **Dependencies:** Requires the `Models_and_Config` component.

#### 3. Component: Presentation_GUI
- **Role:** Handles visualization and human interactions.
- **Internal Elements:** `gui.py`, `gui_support.py`, `render.py`
- **Exposed Interface:** Provides a simple `launch_gui()` interface.
- **Dependencies:** 
  - Requires `Models_and_Config` for rendering state.
  - Requires `Core_Engine` API to validate and submit human moves.

#### 4. Component: Orchestration_CLI
- **Role:** The top-level orchestrator that manages CLI arguments, JSON import/export, and initializes the application.
- **Internal Elements:** `cli.py`, `automation.py`
- **Dependencies:** Requires all three other components (`Models_and_Config` to parse JSON, `Core_Engine` to initialize logic, and `Presentation_GUI` to launch the window).

Analyze the architecture based on these instructions and generate the final Mermaid component diagram.

# Response for high level Component Diagram
classDiagram
    %% Component 1: Models_and_Config
    class Models_and_Config {
        <<component>>
        +models.py
        +config.py
        +pieces.py
    }

    class IDataInterface {
        <<interface>>
        +GameState
        +Move
        +ModeConfig
        +PIECES
    }
    Models_and_Config ..|> IDataInterface : provides

    %% Component 2: Core_Engine
    class Core_Engine {
        <<component>>
        +engine.py
        +players.py
    }

    class EngineAPI {
        <<interface>>
        +new_game()
        +apply_move()
        +list_legal_moves()
    }
    Core_Engine ..|> EngineAPI : provides
    Core_Engine ..> IDataInterface : uses

    %% Component 3: Presentation_GUI
    class Presentation_GUI {
        <<component>>
        +gui.py
        +gui_support.py
        +render.py
    }

    class ILauncherAPI {
        <<interface>>
        +launch_gui()
    }
    Presentation_GUI ..|> ILauncherAPI : provides
    Presentation_GUI ..> IDataInterface : requires (render state)
    Presentation_GUI ..> EngineAPI : invokes (validate/submit moves)

    %% Component 4: Orchestration_CLI
    class Orchestration_CLI {
        <<component>>
        +cli.py
        +automation.py
    }
    
    Orchestration_CLI ..> IDataInterface : requires (parse JSON)
    Orchestration_CLI ..> EngineAPI : requires (initialize logic)
    Orchestration_CLI ..> ILauncherAPI : invokes (launch window)

# Evaluation Prompt 1

You are a strict UML evaluator. Score this component diagram against the code using integers 1–5:

Completeness: Are all components from the code represented?
Correctness: Are relationships and multiplicities accurate?
Standards Adherence: Is the Mermaid syntax valid?
Comprehensibility: Is the diagram readable?
Terminological Alignment: Do names match the domain?
If any score is below 4, output the corrected Mermaid code. [component_diagram.mmd](file;file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/Architectural_Diagrams/UML_After_Duo/Component/component_diagram.mmd) 

# Evaluation Response 1

Here is the evaluation of the component diagram against the blokus codebase:

1. Completeness: 5 The diagram successfully captures the entire macroscopic architecture of the system. All four primary components (Models_and_Config, Core_Engine, Presentation_GUI, and Orchestration_CLI) are modeled perfectly. The internal files are accurately listed, and all essential interfaces (IDataInterface, EngineAPI, ILauncherAPI) correctly expose the key data types and operations according to the codebase. Extraneous directories and scripts (review, evaluate.py, tests) were correctly excluded.

2. Correctness: 5 The relationships map perfectly to the actual Python module dependencies in the code. Orchestration_CLI properly delegates to the other three APIs; Presentation_GUI relies on EngineAPI to manage game rules; and everything fundamentally depends on the core data structures in IDataInterface. (Note: Multiplicities are generally omitted on UML interface implementation/usage dependencies, so their absence here is structurally correct for a Component Diagram).

3. Standards Adherence: 5 The Mermaid syntax is fully valid. Using a classDiagram with <<component>> and <<interface>> stereotypes is the standard and recommended workaround for rendering component diagrams in Mermaid Live. The use of ..|> (realization/provides) and ..> (dependency/requires) perfectly mimics the "lollipop and socket" notation of standard UML Component Diagrams.

4. Comprehensibility: 5 The diagram is extremely readable. It clearly separates the physical modules (the components containing .py files) from the logical APIs (the interfaces). The descriptive labels on the dependency arrows (e.g., requires (render state), invokes (launch window)) provide immediate context for why the dependency exists, which is excellent.

5. Terminological Alignment: 5 The terminology perfectly matches the domain codebase. Naming conventions like EngineAPI, GameState, apply_move(), and launch_gui() map exactly to the underlying Python functions and data classes.

Overall Result: This is an exceptionally well-crafted component diagram. Because all scores are 4 or above, no corrections are necessary!

# Prompt for granular Component Diagram

You are an expert software architect with extensive experience in UML design and Mermaid syntax. Your task is to generate three detailed Component Diagrams for a Blokus game engine based on the Python codebase in `src/blokus/`. 

Unlike a standard high-level component diagram, these diagrams must include **granular class details** (attributes, methods with types, and visibilities) grouped inside `namespace` blocks representing the components.

### Constraints & Formatting Rules
1. **Output ONLY valid Mermaid code** inside ````mermaid ... ```` blocks. Use `classDiagram` syntax for all three diagrams.
2. **Three Separate Diagrams:** You must generate exactly three separate Mermaid blocks as defined in the "Diagrams to Model" section below.
3. **Granular Details:** Inside the namespaces, include classes with their essential properties and methods (e.g., `+apply_move(state: GameState, move: Move) GameState$`). Use `$` to denote static/module-level functions.
4. **No Placeholders:** Use concrete Python types (e.g., `list[Move]`, `dict`). Do not use `<Type>`.

### Project Scope & Exclusions
- **TARGET DIRECTORY:** `src/blokus/`
- **CRITICAL EXCLUSIONS:** You MUST completely ignore the `src/blokus/review/` directory, `evaluate.py`, and any test files. They are meta-tooling and not part of the game architecture.

### Diagrams to Model

#### Diagram 1: System Level Component Interactions
Create a high-level view containing only `<<Component>>` blocks and their dependencies.
- Components to include: `Models_Config_Component`, `Core_Engine_Component`, `CLI_Component`, `GUI_Component`.
- Draw labeled dependency arrows (`..>`) showing how CLI and GUI utilize the Core Engine and consume the Models. Do not put any classes inside these components.

#### Diagram 2: Models, Config & Core Engine Architecture
Create a diagram detailing the data and rules layers.
- **Namespace: Models_Config**
  - Include classes: `GameState`, `Move`, `ValidationResult`, `ModeConfig`, `PieceDefinition`, `Transform`. Include the TypedDicts `GameStatePayload` and `MovePayload`.
  - Add their granular properties and methods (e.g., `to_dict`, `from_dict`).
- **Namespace: Core_Engine**
  - Include `Engine` and `Players` as `<<module>>` classes.
  - Detail their granular methods (e.g., `Engine` has `new_game`, `validate_move`, `apply_move`; `Players` has `choose_move`).
- **Relationships:** Show how `Engine` and `Players` depend on (`..>`) `GameState` and `Move`. Show aggregation (`*--`) between `GameState` and `Move`.

#### Diagram 3: Presentation Layer Architecture (CLI & GUI)
Create a diagram detailing the visualization and orchestration layers.
- **Namespace: CLI_Layer**
  - Include the `CLI` class as a `<<module>>`. Detail its commands (`cmd_new`, `cmd_apply`, `cmd_gui`, `main`, etc.).
- **Namespace: GUI_Layer**
  - Include `BlokusGui`, `DragState`, `BoardMetrics`, `SidebarPieceSlot`, and `PieceRenderLayout`.
  - Include granular methods for `BlokusGui` (`run`, `redraw`, `draw_board_state`, `on_button_press`, etc.).
- **External Dependencies:**
  - Define `CoreEngineComponent` and `ModelsConfigComponent` simply as `<<Component>>` classes (do not redefine their internal methods here).
  - Draw labeled dependency arrows (`..>`) from `CLI` and `BlokusGui` to these external components to show cross-layer integration.

Analyze the architecture based on these instructions and generate the three final Mermaid diagrams.

# Response to granular Component Diagram 
classDiagram
    %% Component 1: Models_and_Config
    class Models_and_Config {
        <<component>>
        +models.py
        +config.py
        +pieces.py
    }

    class IDataInterface {
        <<interface>>
        +GameState
        +Move
        +ModeConfig
        +PIECES
    }
    Models_and_Config ..|> IDataInterface : provides

    %% Component 2: Core_Engine
    class Core_Engine {
        <<component>>
        +engine.py
        +players.py
    }

    class EngineAPI {
        <<interface>>
        +new_game()
        +apply_move()
        +list_legal_moves()
    }
    Core_Engine ..|> EngineAPI : provides
    Core_Engine ..> IDataInterface : uses

    %% Component 3: Presentation_GUI
    class Presentation_GUI {
        <<component>>
        +gui.py
        +gui_support.py
        +render.py
    }

    class ILauncherAPI {
        <<interface>>
        +launch_gui()
    }
    Presentation_GUI ..|> ILauncherAPI : provides
    Presentation_GUI ..> IDataInterface : requires (render state)
    Presentation_GUI ..> EngineAPI : invokes (validate/submit moves)

    %% Component 4: Orchestration_CLI
    class Orchestration_CLI {
        <<component>>
        +cli.py
        +automation.py
    }
    
    Orchestration_CLI ..> IDataInterface : requires (parse JSON)
    Orchestration_CLI ..> EngineAPI : requires (initialize logic)
    Orchestration_CLI ..> ILauncherAPI : invokes (launch window)

classDiagram
    %% Diagram 2: Models, Config & Core Engine Architecture
    
    namespace Models_Config {
        class GameState {
            +mode: str
            +board_size: int
            +players: tuple[str, ...]
            +start_corners: dict[str, tuple[int, int]]
            +board: dict[tuple[int, int], str]
            +remaining_pieces: dict[str, set[str]]
            +history: list[Move]
            +turn_index: int
            +active: bool
            +current_player() str
            +clone() GameState
            +to_dict() GameStatePayload
            +from_dict(data: Mapping[str, object]) GameState$
        }
        class Move {
            +player: str
            +piece: str
            +x: int
            +y: int
            +rotation: int
            +flipped: bool
            +to_dict() MovePayload
            +from_dict(data: Mapping[str, object]) Move$
        }
        class ValidationResult {
            +valid: bool
            +reason: str | None
        }
        class ModeConfig {
            +name: str
            +board_size: int
            +players: tuple[str, ...]
            +start_corners: dict[str, tuple[int, int]]
            +get_mode_config(name: str) ModeConfig$
            +symbol_for_player(player: str) str$
            +player_for_symbol(symbol: str) str$
        }
        class PieceDefinition {
            +piece_id: str
            +cells: tuple[tuple[int, int], ...]
            +transforms: tuple[Transform, ...]
            +size() int
        }
        class Transform {
            +rotation: int
            +flipped: bool
            +cells: tuple[tuple[int, int], ...]
        }
        class GameStatePayload {
            <<TypedDict>>
            +mode: str
            +board_size: int
            +players: list[str]
            +start_corners: dict[str, list[int]]
            +board: list[str]
            +remaining_pieces: dict[str, list[str]]
            +history: list[MovePayload]
            +current_player: str
        }
        class MovePayload {
            <<TypedDict>>
            +player: str
            +piece: str
            +x: int
            +y: int
            +rotation: int
            +flipped: bool
        }
    }

    namespace Core_Engine {
        class Engine {
            <<module>>
            +new_game(mode: str, controllers: dict[str, str], strategies: dict[str, str]) GameState$
            +board_in_bounds(state: GameState, x: int, y: int) bool$
            +get_occupied_cells(state: GameState, player: str) set[tuple[int, int]]$
            +is_first_move(state: GameState, player: str) bool$
            +validate_move(state: GameState, move: Move) ValidationResult$
            +list_legal_moves(state: GameState, player: str, limit: int) list[Move]$
            +apply_move(state: GameState, move: Move) GameState$
            +validate_pass(state: GameState, player: str) ValidationResult$
            +pass_turn(state: GameState, player: str) GameState$
            +validate_loaded_state(loaded: GameState) None$
            +score_player(state: GameState, player: str) int$
            +compute_scores(state: GameState) dict[str, int]$
            +occupied_square_counts(state: GameState) dict[str, int]$
        }
        class Players {
            <<module>>
            +choose_simple_move(state: GameState, player: str) Move | None$
            +available_strategies() tuple[str, ...]$
            +choose_move(state: GameState, player: str, strategy: str) Move | None$
        }
    }

    GameState *-- Move : contains
    Engine ..> GameState : evaluates/mutates
    Engine ..> Move : validates/applies
    Players ..> GameState : analyzes
    Players ..> Move : generates

classDiagram
    %% Diagram 3: Presentation Layer Architecture (CLI & GUI)
    
    class CoreEngineComponent {
        <<Component>>
    }
    
    class ModelsConfigComponent {
        <<Component>>
    }

    namespace CLI_Layer {
        class CLI {
            <<module>>
            +cmd_new(args: Namespace) int$
            +cmd_show(args: Namespace) int$
            +cmd_validate(args: Namespace) int$
            +cmd_apply(args: Namespace) int$
            +cmd_pass_turn(args: Namespace) int$
            +cmd_legal_moves(args: Namespace) int$
            +cmd_suggest(args: Namespace) int$
            +cmd_play(args: Namespace) int$
            +cmd_gui(args: Namespace) int$
            -_load_state(path: str) GameState$
            -_dump_json(payload: dict[str, object], output_path: str)$
            +build_parser() ArgumentParser$
            +main(argv: list[str]) int$
            +run_cli(argv: Any)$
        }
    }

    namespace GUI_Layer {
        class BlokusGui {
            +__init__(root: tk.Tk, mode: str) None
            +switch_mode(new_mode: str) None
            +compute_scale() float
            +scale_value(value: int) int
            +run() None
            +redraw() None
            +draw_sidebar_overlays() None
            +draw_mode_control(mode_name: str, x0: float, y0: float, x1: float, y1: float) None
            +draw_board_state() None
            +draw_status_panel() None
            +draw_piece_panel() None
            +layout_piece_cells(piece_id: str) PieceRenderLayout
            +exact_piece_layout(piece_id: str, slot: SidebarPieceSlot) PieceRenderLayout | None
            +fitted_piece_layout(piece_id: str, bbox: tuple[float, float, float, float]) PieceRenderLayout
            +draw_drag_preview() None
            +on_motion(event: tk.Event) None
            +on_button_press(event: tk.Event) None
            +on_button_release(event: tk.Event) None
            +advance_automatic_turns() None
            +show_legal_move_dialog() None
            +apply_suggested_move(move: Move, dialog: tk.Toplevel) None
            +handle_restart() None
        }
        
        class DragState {
            +piece_id: str
            +base_cell: tuple[int, int]
            +rotation: int
            +flipped: bool
        }
        
        class BoardMetrics {
            +board_x: int
            +board_y: int
            +display_size: int
            +grid_origin_x() float
            +grid_origin_y() float
            +cell_size() float
        }
        
        class SidebarPieceSlot {
            +bbox: tuple[float, float, float, float]
            +normalized_shape: tuple[tuple[int, int], ...]
            +cell_rects: dict[tuple[int, int], tuple[float, float, float, float]]
        }
        
        class PieceRenderLayout {
            +bbox: tuple[float, float, float, float]
            +cell_rects: dict[tuple[int, int], tuple[float, float, float, float]]
        }
    }

    BlokusGui *-- DragState : manages
    BlokusGui *-- BoardMetrics : uses
    BlokusGui *-- SidebarPieceSlot : maps
    BlokusGui *-- PieceRenderLayout : renders
    
    CLI ..> CoreEngineComponent : invokes rules
    CLI ..> ModelsConfigComponent : uses data types
    BlokusGui ..> CoreEngineComponent : validates moves via
    BlokusGui ..> ModelsConfigComponent : visualizes


# LLM as a judge Prompt
You are a strict UML evaluator. Score this component diagram against the code using integers 1–5:

Completeness: Are all components from the code represented?
Correctness: Are relationships and multiplicities accurate?
Standards Adherence: Is the Mermaid syntax valid?
Comprehensibility: Is the diagram readable?
Terminological Alignment: Do names match the domain?
If any score is below 4, output the corrected Mermaid code. [granular_component_diagrams.mmd](file;file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/Architectural_Diagrams/UML_After_Duo/Component/granular_component_diagrams.mmd) 

# LLM as a Judge Response

Here is my evaluation of the component diagram against the Blokus game engine codebase.

Evaluation Scores
Completeness: 5 All requested core components (Models_Config, Core_Engine, CLI_Layer, GUI_Layer) are fully represented. The diagram successfully maps all major classes and modules from the codebase (e.g., GameState, Engine, BlokusGui, CLI) while correctly excluding meta-tooling (like evaluate, release, and review scripts) as requested in the architectural constraints.

Correctness: 3 The diagram introduces inconsistent component naming between diagrams. Core_Engine_Component and Models_Config_Component in Diagram 1 are redefined as CoreEngineComponent and ModelsConfigComponent in Diagram 3. In UML and Mermaid, this creates disjointed, duplicate components rather than establishing correct references. The multiplicities and relationship types (*-- for composition, ..> for dependency), however, accurately reflect the code.

Standards Adherence: 2 The diagram violates standard .mmd syntax by declaring multiple classDiagram root directives in a single file without valid separation, which breaks standard Mermaid parsers. Furthermore, the extensive use of complex Python type hints containing commas and brackets (e.g., dict[tuple[int, int], str]) inside method signatures and properties frequently causes Mermaid rendering to fail. Static method modifiers ($) are also placed after return types in a way that can confuse strict parsers.

Comprehensibility: 4 The structural split into three logical sections (System Level, Core, Presentation) makes the architecture highly readable and modular. However, the syntax errors and disconnected component names slightly detract from a unified understanding.

Terminological Alignment: 5 Names of components, classes, and methods perfectly match the domain and the physical Python codebase (e.g., BoardMetrics, PieceRenderLayout, cmd_new, etc.).

Corrected Mermaid Code
Since scores fell below 4, here is the corrected Mermaid code. All elements have been merged into a single classDiagram to fix the syntax error, component naming is unified, and complex Python types have been simplified to UML-safe Mermaid syntax (e.g., replacing brackets/commas with standard UML types and Mermaid generics ~).

# LLM as a Judge edit scope thorugh a second prompt
Please keep the structure of having three different diagrams in one file. It does not have to compile together, it is enough if the diagrams compile separately. With this in mind, fix the inconsistent component naming between diagrams as you mentioned in the criteria "Correctness." For each change, explain why it was false and why you did it. 

# LLM as a Judge edit prompt 2 response
I have updated the granular_component_diagrams.mmd file to keep your three-diagram structure while resolving the consistency issues.

Here are the specific changes made and the rationale behind them:

1. Renaming Component Definitions in Diagram 3
Change Made:

Changed class CoreEngineComponent { <<Component>> } to class Core_Engine_Component { <<Component>> }
Changed class ModelsConfigComponent { <<Component>> } to class Models_Config_Component { <<Component>> }
Why it was false: In Diagram 1, the foundational components were explicitly defined using snake_case (e.g., Core_Engine_Component). However, Diagram 3 redefined them using PascalCase (CoreEngineComponent). In UML and Mermaid syntax, distinct spellings indicate entirely separate, disjointed classes. This falsely implied the presentation layer was interacting with different or duplicate components rather than the ones established at the system level.

Why I did it: By standardizing the names to exactly match Diagram 1, the architecture remains semantically consistent. Tools, parsers, and human readers will correctly understand that Diagram 3 is elaborating on the exact same structural components introduced earlier.

2. Updating Dependency Relationships in Diagram 3
Change Made:

Changed CLI ..> CoreEngineComponent and BlokusGui ..> CoreEngineComponent to point to Core_Engine_Component.
Changed CLI ..> ModelsConfigComponent and BlokusGui ..> ModelsConfigComponent to point to Models_Config_Component.
Why it was false: The relationship arrows were pointing to the incorrectly named component clones. This broke the dependency tree, making it look like the CLI and BlokusGui relied on external components outside of the defined Models_Config and Core_Engine namespaces.

Why I did it: I repointed all dependency associations (..>) to the correctly named components. This accurately models the architectural constraints: the orchestration layer (CLI) and presentation layer (GUI) both correctly consume data types from Models_Config_Component and invoke rules via Core_Engine_Component.
