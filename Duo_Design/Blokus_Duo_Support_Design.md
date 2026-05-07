
# Prompt 1:
As a Senior Requirements Analyst, I have extracted the technical requirements for **Blokus Duo** based on the provided context and project baseline (`docs/requirements.md`).

The requirements are structured into functional specifications, constraints, and invariants, with a focus on the 2-player configuration and necessary GUI adaptations.

### Key Extracted Requirements:
- **Functional (Duo Mode):**
    - **R-F-12.1:** Board size 14x14.
    - **R-F-12.2:** Exactly 2 players.
    - **R-F-12.3:** Starting positions at (5,5) and (9,9).
    - **R-F-12.4:** Standard 21nd-piece set per player.
- **GUI Adaptations:**
    - **R-F-12.5 & R-F-12.6:** Reduction of player color indicators from 4 to 2 and layout optimization for the 14x14 grid.
- **Constraints:**
    - **R-C-01:** No LLM runtime dependency (Strict).
- **Invariants:**
    - Standard Blokus rules (Corner-to-corner placement, no edge-to-edge for same color, piece uniqueness).

You can find the detailed requirements document here: [extracted_duo_requirements.md](file:///Users/maximilianalpgruder/.gemini/antigravity/brain/fcee60bd-465c-40b3-8cb5-4b549ff6e7bb/extracted_duo_requirements.md)


# Prompt 2:
As a Software Architect, I have evaluated the requirements for adding **Blokus Duo** support to the existing engine. Below are two distinct architectural candidates designed to adhere to the "no duplication" principle while ensuring a robust and maintainable implementation.

---

### Option 1: Pure Configuration-Driven
**Overview**: This approach treats "Duo" as a data variation of the "Classic" game. It leverages and extends the existing `ModeConfig` structure in `config.py` to drive engine behavior dynamically.

#### Major Components
*   **`ModeConfig` (Extended)**: Located in `src/blokus/config.py`, this dataclass is updated to support arbitrary start positions (moving beyond the semantic limitation of "corners").
*   **`DUO_CONFIG`**: A new instance of `ModeConfig` defining the 14x14 grid, the two-player set, and the specific $(5,5)$ and $(9,9)$ start squares.
*   **`engine.py` (Generalized)**: The core validation logic is refactored to consume `state.start_squares` instead of hardcoded corner checks.

#### Responsibility Allocation
*   **`config.py`**: Owns all mode-specific constants (board dimensions, player names/colors, start coordinates).
*   **`engine.py`**: Acts as a "Universal Blokus Interpreter." It enforces the fundamental invariants (edge-touch vs. corner-touch) using the parameters injected from the configuration.

#### Adherence to "No Duplication"
*   **Logic Reuse**: 100% of the game logic is shared between Classic and Duo. There is no separate `duo_engine.py`.
*   **Single Source of Truth**: All "Blokus Rules" exist in exactly one place. If the corner-touch rule changes or is optimized, both modes benefit immediately.
*   **Data-Driven Evolution**: Adding a third mode (e.g., Team Blokus) only requires a new dictionary entry in `config.py`, not new code.

---

### Option 2: Rule Strategy Pattern
**Overview**: This approach introduces a `Rules` interface to encapsulate variant-specific logic. It separates the **mechanics** of the game (state transitions, piece transformations) from the **policies** (start conditions, board size).

#### Major Components
*   **`BlokusRules` (Abstract Interface)**: Defines the policy API, such as `get_board_size()`, `get_players()`, and `validate_first_move(state, move)`.
*   **`ClassicRules` & `DuoRules` (Strategies)**: Concrete implementations of the interface. `DuoRules` specifically overrides the first-move validation to check for the $(5,5)/(9,9)$ requirement.
*   **`engine.py` (The Context)**: The engine is refactored to hold a reference to a `BlokusRules` object. It delegates policy-heavy decisions to this strategy.

#### Responsibility Allocation
*   **Strategy Objects**: Responsible for "Variant Policy" (e.g., "Where must the first piece go?" or "How many players are allowed?").
*   **Engine Context**: Responsible for "Game Mechanics" (e.g., calculating rotation/flipping of piece matrices, updating the board array, and managing the move history).

#### Adherence to "No Duplication"
*   **Structural Reuse**: Both strategies share the same `GameState` model and `Piece` library.
*   **Clean Separation**: Instead of cluttering the engine with `if mode == "duo":` blocks, the differences are isolated in small, focused strategy classes. This prevents the "God Object" anti-pattern in `engine.py`.
*   **Polymorphic Invariants**: Common rules (like "No edge contact") can be implemented in a `BaseRules` class, ensuring that common logic is written only once but can be customized if a future variant (like Blokus Trigon) requires it.

---

### Summary Comparison

| Feature | Option 1: Configuration-Driven | Option 2: Rule Strategy Pattern |
| :--- | :--- | :--- |
| **Complexity** | Low (Minimal code changes) | Medium (Requires new classes/interfaces) |
| **Flexibility** | Limited to parameter changes | High (Can change entire rule sets) |
| **Maintenance** | Single file for all logic | Modular, isolated files |
| **Best For** | Fast delivery of Duo mode | Future-proofing for diverse variants |

**Recommendation**: Given the project's current scope and the requirement for immediate performance parity (**R-C-06**), **Option 1** is recommended for its simplicity and direct adherence to the "No LLM Runtime" and "No Duplication" principles.


# Prompt 3
As a Technical Critic, I have evaluated the two architectural candidates for adding Blokus Duo support. While Option 1 offers immediate efficiency, Option 2 provides the structural integrity required for long-term geometric expansion (e.g., Blokus Trigon).

### Structured Comparison

| Criterion | Option 1: Pure Configuration-Driven | Option 2: Rule Strategy Pattern |
| :--- | :--- | :--- |
| **Maintainability** | **High (Short-term):** Simple to understand; logic is centralized. However, risks "Condition Hell" if future modes require subtle logic shifts. | **High (Long-term):** Clean separation of concerns. Bug fixes in specific mode logic are isolated and don't risk regressing other modes. |
| **Extensibility** | **Low:** Limited to variations in scale (board size) and constants. Ill-suited for modes like "Trigon" which change the grid geometry itself. | **Very High:** Designed for variance. Swapping a "SquareRules" strategy for a "TrigonRules" strategy is a first-class operation. |
| **Implementation Cost** | **Minimal:** Primarily involves updating `config.py` and generalizing two or three lines in `engine.py`. | **Moderate:** Requires refactoring the Engine into a Context, defining an Abstract Base Class (ABC), and implementing concrete strategies. |
| **Complexity** | **Low:** Relies on existing procedural patterns. | **Medium:** Introduces polymorphism and dependency injection. |

---

### Risk Analysis

#### Option 1: Configuration-Driven
*   **The "Flat-File Bloat" Risk**: As more modes are added, the `ModeConfig` dataclass may become a "catch-all" for every edge case. We might end up with flags like `is_hexagonal`, `has_special_start_rule`, or `allows_three_players`, leading to a fragmented and unreadable `engine.py` filled with nested `if/else` blocks.
*   **Geometric Rigidity**: This approach assumes the core "Blokus Invariants" (edge/corner rules on a Cartesian grid) never change. If a new mode changes the fundamental definition of a "neighbor," this pattern breaks.

#### Option 2: Rule Strategy Pattern
*   **Over-Engineering Risk**: For a project currently only supporting two very similar square-grid modes, introducing a full Strategy pattern might be seen as "Gold Plating." It increases the cognitive load for new developers who must navigate multiple files to understand a single move validation.
*   **State Leakage**: There is a risk that the `Rules` strategy might need access to too much of the `GameState` or vice versa, leading to tight coupling that defeats the purpose of the abstraction.

---

### Trade-offs and Final Critique

The choice between these two options is a classic **"Speed vs. Scalability"** trade-off.

*   **Choose Option 1** if the goal is to ship Blokus Duo as a minor feature update within the existing square-grid framework. It is the most pragmatic choice for the immediate requirements (R-F-14.1).
*   **Choose Option 2** if the roadmap includes **Blokus Trigon** or **Blokus Giant**. Trigon, in particular, uses a triangular grid where "orthogonal" and "diagonal" are defined differently. Option 1 would require a complete rewrite to support Trigon, whereas Option 2 would simply require a new `TrigonRules` implementation.

**Critic's Verdict**: While Option 1 is faster to implement today, it creates "Technical Debt" for any future mode that isn't a square-grid variant. If "Trigon" is a serious future requirement, the cost of refactoring to Option 2 now is significantly lower than the cost of unpicking a bloated configuration-driven engine later.

# Prompt 4:
Edited Blokus_Duo_Support_Options.md
Edited Duo_LLM_Logs
Viewed Duo_LLM_Logs:61-77

# Architectural Decision Record (ADR)

## Status
**Proposed**

## Context
The Blokus engine (Phase 1 & 2) currently supports "Classic" mode (20x20 board, 4 players, corner starts). We need to extend this engine to support **Blokus Duo** (14x14 board, 2 players, specific $(5,5)$ and $(9,9)$ start squares). 

The key requirements include:
- **R-F-12**: Full support for 2-player competitive play.
- **R-F-14.1**: Transition between modes must be handled via configuration within the same engine logic to avoid codebase duplication.
- **R-C-01**: No LLM runtime dependency.
- **Performance**: Move validation must remain immediate.

We evaluated two architectural candidates: a data-centric **Configuration-Driven** approach and a policy-centric **Rule Strategy Pattern**.

## Decision
We have decided to implement **Option 1: Pure Configuration-Driven** for the support of Blokus Duo.

This involves:
1.  **Generalizing the `ModeConfig` dataclass** in `src/blokus/config.py` to replace `start_corners` with a more flexible `start_squares` parameter.
2.  **Updating `engine.py`** to consume these start coordinates dynamically during the first-move validation.
3.  **Injecting mode-specific parameters** (board size, player count, colors) directly from the `MODE_CONFIGS` registry.

## Consequences
- **Positive**: 
    - **Speed of Delivery**: Minimal refactoring required; implementation is primarily data entry in `config.py`.
    - **Logic Consolidation**: 100% of the game invariants (Blokus touch rules) are shared, ensuring that bug fixes in the core engine apply to all modes.
    - **Low Complexity**: No new design patterns or interfaces are introduced, keeping the barrier to entry low for future contributors.
- **Negative**:
    - **Limited Structural Flexibility**: Adding a fundamentally different variant (like Blokus Trigon with a non-square grid) will require a significant refactor, as this approach assumes square grid geometry.
    - **Condition Bloat Risk**: If Duo and Classic rules diverge in logic (rather than just constants), the engine may become cluttered with `if mode == 'duo'` checks.

## Alternatives Considered (and Rejected)

### Option 2: Rule Strategy Pattern
This approach involved creating an abstract `Rules` interface and separate `ClassicRules` and `DuoRules` classes.

**Reason for Rejection**:
While Option 2 offered superior extensibility for non-square variants (like Trigon), it was rejected for the following reasons:
1.  **Over-Engineering**: The current project scope is limited to square-grid Blokus. Introducing a polymorphic strategy pattern adds unnecessary boilerplate and cognitive complexity for the current needs.
2.  **Higher Implementation Cost**: Refactoring the engine into a strategy-based context would delay the delivery of the Duo mode without providing immediate functional benefits.
3.  **Maintainability Overhead**: Managing multiple rule files for nearly identical logic (80%+ overlap between Classic and Duo) increases the risk of "Logic Drift" if core Blokus rules are updated in one strategy but forgotten in another.