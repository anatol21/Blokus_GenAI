# Blokus Duo Serialization & Import/Export Tests Implementation Plan

This document outlines the comprehensive test suite to be developed for validating the serialization, deserialization, and persistence features of the newly implemented Blokus Duo game mode. As requested, this plan targets the creation of parallel test files specifically tailored for Blokus Duo without modifying the original Classic test suite directly (except for dynamic adaptations that can be reused).

## Phase 1: Parameterize the Existing Tests

The current test suite covers Classic mode rigorously. We will replicate this robust structure for Duo mode in parallel files, replacing hardcoded assumptions (20x20 board, 4 players) with Duo-specific constants (14x14 board, 2 players: `"blue"` and `"red"`).

### 1. `tests/test_serialization_duo.py`
- **Dynamic Fixtures**: Update the `load_initial_payload` equivalent to load a new fixture: `duo_initial_state.json`.
- **Abstract Hardcoded Data**:
  - Update `test_state_round_trip_after_moves` to use a sequence of valid Duo moves (e.g., `Move("blue", "I1", 4, 4)` and `Move("red", "I1", 9, 9)` assuming the classic Duo starting positions, or corners `0,0` and `13,13` depending on engine specifics). 
  - Exclude tests irrelevant to Duo (e.g., mismatched 4-player list tests can be modified to assert against the 2-player list).
  - Ensure the board shape assertions expect a `14x14` array of strings instead of `20x20`.

### 2. `tests/test_serialization_integrity_duo.py`
- **Mid-Game Factories**: Refactor `create_mid_game_state` and `create_finished_game_state` to generate valid Duo states instead of Classic states.
- **Defensive Tests**: Update the parameterized malformed data tests (like `wrong_row_count` and `wrong_row_length`) to test against 14 instead of 20. Update the invalid player test to reject anything other than `"blue"` and `"red"`.

### 3. `tests/test_persistence_duo.py`
- **Board Reproducibility & History**: Update `RoundTripFidelityTests` and `BoardReproducibilityTests` to use the Duo board limits and only 2 players.
- **Play/Resume Workflows**: Ensure the CLI subprocess commands for `play` use `--mode duo`.

### 4. `tests/test_persistence_extended_duo.py`
- **Full Board Stress Test**: Modify `test_gamestate_full_board_stress_round_trip` to fill a 14x14 board.
- **Defensive Loading**: Modify structural validations to ensure it rejects a payload if the `players` array has 4 items (Classic) but `mode` is `duo`.

### 5. `tests/test_cli_import_duo.py`
- **State Replays**: Update `TestImportValidation` to use a valid Duo move sequence to verify history replaying.
- **Malformed State Rejection**: Update the CLI-level integration tests to provide specifically malformed Duo JSON representations to ensure the validation logic catches them.

---

## Phase 2: Verify Persistence Layer

### 1. CLI Integration
- Complete the skeleton test `test_duo_state_export_import_round_trip` (currently sitting in `test_persistence.py`).
- Implement subprocess tests invoking `python -m blokus new --mode duo --output tmp.json`.
- Apply a valid Duo move via `python -m blokus apply --mode duo --state tmp.json ...` and verify the exported file remains clean and valid.

### 2. Mid-Game Round-Tripping
- Simulate a half-played Duo game (at least 10 moves per player).
- Serialize it to a JSON payload.
- Deserialize it and assert strict equivalence of `occupied_cells_by_player` and the `history` cache.

---

## Phase 3: Implement Duo-Specific Edge Case Tests

We will create a directory named `import_json_tests_duo/` containing 8 crafted invalid JSON payloads to stress test the validation mechanism during import. The tests in `test_cli_import_duo.py` will systematically load these and assert that the expected validation errors are raised.

All files will conform to the baseline requirements: `"mode": "duo"`, 14x14 board, and `"players": ["blue", "red"]`.

1. **`01_piece_in_rack_and_board.json`**
   - **Scenario**: A piece (`I1`) is present on the board (indicated in the `history` and `board` matrix) but is also mistakenly still in the `remaining_pieces` list for that player.
2. **`02_invalid_remaining_squares_sum.json`**
   - **Scenario**: The mathematical sum of the piece sizes in `remaining_pieces` plus the cells occupied on the board does not equal the total starting squares per player (89).
3. **`03_illegal_piece_placement.json`**
   - **Scenario**: A piece is placed in an illegal position (e.g., sharing a flat edge with another piece of the same color, or not starting in the correct initial position).
4. **`04_wrong_current_player.json`**
   - **Scenario**: The `history` shows Blue just played, but `current_player` is incorrectly set to `"blue"` instead of `"red"`.
5. **`05_incorrect_player_scores.json`**
   - **Scenario**: If scores are cached/saved, they intentionally do not match the geometric reality of the board state. (If dynamically computed, we will test the cache assertion).
6. **`06_misconfigured_board.json`**
   - **Scenario**: The `board` array is configured as a 14x15 or 15x14 grid, or contains illegal characters like `"Y"` or `"G"`.
7. **`07_wrong_starting_corners.json`**
   - **Scenario**: The first moves in the `history` do not match the required starting constraints for Duo mode (where pieces must cover specific central or corner squares).
8. **`08_invalid_history_moves.json`**
   - **Scenario**: The `history` array contains a syntactically invalid move (e.g., negative coordinates, out-of-bounds `x: 15`, or referencing a non-existent player `"green"`).

---

## Output File Manifest

When execution of this plan begins, the following files will be generated:

1. `tests/test_serialization_duo.py`
2. `tests/test_serialization_integrity_duo.py`
3. `tests/test_persistence_duo.py`
4. `tests/test_persistence_extended_duo.py`
5. `tests/test_cli_import_duo.py`
6. `import_json_tests_duo/01_piece_in_rack_and_board.json`
7. `import_json_tests_duo/02_invalid_remaining_squares_sum.json`
8. `import_json_tests_duo/03_illegal_piece_placement.json`
9. `import_json_tests_duo/04_wrong_current_player.json`
10. `import_json_tests_duo/05_incorrect_player_scores.json`
11. `import_json_tests_duo/06_misconfigured_board.json`
12. `import_json_tests_duo/07_wrong_starting_corners.json`
13. `import_json_tests_duo/08_invalid_history_moves.json`

This structured approach ensures the new mode has the exact same security, integrity, and operational guarantees as the classic engine, isolating the test suites for maintainability while adhering strictly to Duo's 14x14/2-player constraints.
