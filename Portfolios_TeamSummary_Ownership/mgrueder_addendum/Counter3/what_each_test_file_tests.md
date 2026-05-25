Viewed generate_edge_cases.py:1-30
Edited Portfolio_%20%282%29.md
Edited Portfolio_%20%282%29.md

Here is a detailed breakdown of exactly what each of the Blokus Duo serialization test files was designed to test. You can think of them as moving from the raw data level up to the user-facing CLI level:

### 1. `test_serialization_duo.py`
**Purpose:** Base serialization and caching logic.
**What it tests:** 
This file tests the foundational `to_dict()` and `GameState.from_dict()` methods, strictly tailored to the 14x14 Duo dimensions and 2-player (`blue`, `red`) configurations. It ensures that when a Duo game is serialized to JSON, it does not bloat the file with derived caches (like `occupied_cells_by_player`). Instead, it tests that when the state is reloaded, the engine accurately scans the 14x14 grid and automatically mathematically reconstructs those caches flawlessly.

### 2. `test_serialization_integrity_duo.py`
**Purpose:** Defensive loading and strict boundary limits.
**What it tests:** 
This file acts as a firewall against fundamentally malformed data. It intentionally corrupts JSON payloads and verifies that the engine throws exact, descriptive `ValueError`s. It enforces Duo-specific constraints, ensuring the system violently rejects:
* Boards that aren't exactly 14 rows of 14 characters.
* Files that attempt to inject a 4-player array (e.g., adding `yellow` or `green`) while the mode is set to `"duo"`.
* Payloads containing duplicate piece IDs in the remaining pieces rack.
* Histories that contain corrupted coordinate strings (like `x: "invalid"`).

### 3. `test_persistence_duo.py`
**Purpose:** Real-world Command Line Interface (CLI) integration.
**What it tests:** 
Instead of just testing raw Python objects, this file spins up actual `subprocess` commands mimicking how a real user interacts with the app. It tests terminal commands like `python -m blokus new --mode duo --output file.json` and `python -m blokus apply --state file.json`. It guarantees that a state can be created, saved to a file, reloaded into a new CLI command, played on, and re-saved—proving the entire end-to-end "round-trip" works identically for Duo as it does for Classic.

### 4. `test_persistence_extended_duo.py`
**Purpose:** Extreme stress limits and physical boundaries.
**What it tests:** 
This tests the edges of the simulation. For example, it forces a state where the entire 14x14 board is completely filled with `"blue"`, or where a player has 0 pieces remaining. It ensures the serialization engine doesn't crash or throw division-by-zero or empty-collection errors under extreme, late-game, or mathematically extreme conditions.

### 5. `test_cli_import_duo.py`
**Purpose:** Semantic and logical game-rule enforcement.
**What it tests:** 
While `test_serialization_integrity` tests *structural* corruption, this file tests *logical* corruption. It actively reads the 8 custom JSON edge-case files we generated in the `import_json_tests_duo/` folder. It tests the `validate_loaded_state()` function to ensure it catches physically impossible scenarios, such as:
* **Quantum Pieces:** A piece (`I1`) existing on the board grid, but also still sitting in the player's `remaining_pieces` list.
* **Illegal Placements:** A file where a piece is placed at `0,0` even though Duo specifically requires the first pieces to be placed at the center corners `4,4` and `9,9`.
* **State Drift:** A file where the "Finished" flag is set to `True`, but the board dictates the game is clearly still ongoing.