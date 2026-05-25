# Implementation Plan: CLI Coordinate Translation Layer

## Problem Statement

The Blokus CLI displays piece placement coordinates as the **bounding-box origin** of the piece's local coordinate system. For pieces like `F5` and `X5`, the bounding-box origin `(0,0)` is an empty gap in the piece shape — not an actual occupied cell. This causes the CLI to show coordinates like `F5 @ (17, 0)` for yellow's opening move, where `(17, 0)` on the board will remain empty after the piece is placed. The actual piece cells land at `(18,0)`, `(19,0)`, `(17,1)`, `(18,1)`, `(18,2)`.

## Design Principle

> **Invariant:** Every coordinate displayed to or accepted from a human player in the CLI refers to a cell that is part of the piece being placed — a square that will become occupied once the move executes.

The engine, JSON serialization, GUI, and all existing test fixtures remain **completely unchanged**. The translation exists only at the CLI boundary.

## Scope

### Files Modified
| File | Change Type | Purpose |
|------|-------------|---------|
| `pieces.py` | Add function | Compute the reference cell offset for a given transform |
| `cli.py` | Modify existing functions | Apply translation in all 5 CLI surfaces + update help text |

### Files NOT Modified
| File | Reason |
|------|--------|
| `engine.py` | Core rules remain bounding-box based |
| `models.py` | `Move` dataclass and JSON schema unchanged |
| `config.py` | Mode configs unchanged |
| `gui.py` | GUI has its own visual placement; unaffected |

---

## Step 1: Add Reference Cell Computation to `pieces.py`

### 1a. Add a `reference_cell()` function

Add a public function that, given a piece ID, rotation, and flip state, returns the **reference cell offset** `(ref_dx, ref_dy)` — the first occupied cell of the transformed piece in sorted order (top-most row first, then left-most column).

Since `_build_transforms()` already sorts cells in each `Transform`, the reference cell is simply `transform.cells[0]` — the first element of the sorted cell tuple. The new function looks up the matching transform and returns its first cell.

### 1b. Add a `start_corner_cell()` function

Add a function that, given a piece ID, rotation, flip state, and a target start corner coordinate, returns the offset `(dx, dy)` of the specific cell in the transform that would land on the start corner. This is needed for first-move translation.

**Logic:** Compute the transformed cells, then for each cell `(dx, dy)`, check whether placing the piece with bounding-box origin at `(corner_x - dx, corner_y - dy)` would cause that cell to land exactly on the start corner. Return the first cell where this holds and the resulting placement is within board bounds.

---

## Step 2: Add Translation Functions to `cli.py`

### 2a. `_engine_to_human()` — for display (engine → human-friendly)

**Signature:** `_engine_to_human(state, move) → (human_x, human_y)`

**Logic:**
1. **First move?** Check `is_first_move(state, move.player)`.
2. **If first move:** Return the player's start corner coordinate. Every legal opening move covers the start corner, so the displayed coordinate is always that corner.
3. **If not first move:** Compute the reference cell `(ref_dx, ref_dy)` via `reference_cell(move.piece, move.rotation, move.flipped)`. Return `(move.x + ref_dx, move.y + ref_dy)`.

### 2b. `_human_to_engine()` — for input (human-friendly → engine)

**Signature:** `_human_to_engine(state, player, piece, human_x, human_y, rotation, flipped) → (engine_x, engine_y)`

**Logic:**
1. **First move?** Check `is_first_move(state, player)`.
2. **If first move:** Use `start_corner_cell()` to find which cell `(dx, dy)` in the transform covers the start corner. Compute engine origin as `(human_x - dx, human_y - dy)`.
3. **If not first move:** Compute the reference cell `(ref_dx, ref_dy)`. Compute engine origin as `(human_x - ref_dx, human_y - ref_dy)`.

> [!IMPORTANT]
> For first moves, the human coordinate is always the start corner. The translation must find the correct cell offset to reconstruct the bounding-box origin. If no cell in the transform can reach the start corner within board bounds, the move is invalid and the CLI should report an error.

---

## Step 3: Apply Translation Across All CLI Surfaces

### 3a. `cmd_legal_moves` (non-interactive)

**Current:** Prints `move.x, move.y` directly from the engine.  
**Change:** Pass each move through `_engine_to_human()` before printing. The `--json` output path should **NOT** be translated — JSON output is engine-facing and must remain bounding-box based for programmatic consumers.

### 3b. `cmd_suggest` (non-interactive)

**Current:** Prints `move.x, move.y` directly.  
**Change:** Same as `cmd_legal_moves` — translate for text output, leave `--json` untranslated.

### 3c. `cmd_validate` (non-interactive)

**Current:** Accepts `--x` and `--y` as engine coordinates.  
**Change:** Accept `--x` and `--y` as human-friendly coordinates, translate to engine coordinates via `_human_to_engine()` before calling `validate_move()`.

### 3d. `cmd_apply` (non-interactive)

**Current:** Accepts `--x` and `--y` as engine coordinates.  
**Change:** Same as `cmd_validate` — translate input before passing to the engine. The JSON output (game state) remains in engine coordinates since it's the serialized `Move` format.

### 3e. `_handle_human_turn` (interactive play mode)

This is the most visible surface. Three interaction points need translation:

1. **`move PIECE X Y ROT FLIP` input:** Translate `(X, Y)` via `_human_to_engine()` before constructing the `Move` object.
2. **`legal [N]` output:** Translate each move's coordinates via `_engine_to_human()` before printing.
3. **Computer move announcements** in `cmd_play`: Translate the computer's move coordinates via `_engine_to_human()` before printing.

### Summary Table

| CLI Surface | Input Translation | Output Translation | JSON Translation |
|-------------|-------------------|--------------------|------------------|
| `legal-moves` | N/A | ✅ Text only | ❌ No (raw engine) |
| `suggest` | N/A | ✅ Text only | ❌ No (raw engine) |
| `validate` | ✅ `--x`, `--y` | N/A | N/A |
| `apply` | ✅ `--x`, `--y` | N/A | ❌ No (raw engine) |
| `play` (human) | ✅ `move` command | ✅ `legal` output | N/A |
| `play` (computer) | N/A | ✅ Announcements | N/A |

> [!WARNING]
> JSON output (`--json` flag and exported game states) must **never** be translated. JSON is consumed by the engine, tests, and programmatic tools that expect bounding-box coordinates. Translating JSON would break backward compatibility.

---

## Step 4: Update Help Text

### 4a. Global CLI description

Update the `ArgumentParser` description to include a note:

> *"Coordinates in human-readable output refer to an occupied cell of the piece being placed. JSON output uses internal bounding-box origin coordinates."*

### 4b. Per-subcommand help for `--x` and `--y`

Update the help strings for `validate` and `apply`:

- `--x`: *"Column of an occupied cell of the piece on the board."*
- `--y`: *"Row of an occupied cell of the piece on the board."*

### 4c. Interactive mode prompt text

Update the `_handle_human_turn` instruction line from:
```
'move PIECE X Y ROTATION FLIPPED(0|1)'
```
to:
```
'move PIECE X Y ROTATION FLIPPED(0|1)  (X,Y = occupied cell position)'
```

---

## Step 5: Testing Strategy

### 5a. Unit tests for translation functions

- **`reference_cell()`:** Verify that for every piece/transform, the returned cell is occupied (exists in the transform's cell tuple). Specifically test `F5` and `X5` where the bounding-box corner is empty.
- **`start_corner_cell()`:** Verify correct offset for `F5` at rotation=0 targeting corner `(19, 0)` → should return cell `(2, 0)`.
- **Round-trip:** For a representative set of piece/rotation/flip combinations, verify `_human_to_engine(_engine_to_human(move)) == original move`.

### 5b. Integration tests for each CLI surface

- **`legal-moves`:** Run against a fresh classic state, verify that all displayed first-move coordinates equal the current player's start corner.
- **`validate` + `apply`:** Verify that `F5` at human coordinate `(19, 0)` with rotation=0 for yellow is accepted and produces the same game state as the old `F5` at `(17, 0)`.
- **`play` mode:** Verify that the interactive `legal` command output matches `legal-moves` text output.
- **JSON preservation:** Verify that `--json` output from `legal-moves` and `suggest` still uses bounding-box coordinates (unchanged from current behavior).

### 5c. Regression tests

- Run the full existing test suite to confirm zero breakage. No engine or model changes means all existing serialization, fixture, and validation tests should pass unmodified.

---

## Risk Assessment

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Existing tests break | **Very low** — engine/model unchanged | Run full suite before and after |
| First-move ambiguity (multiple cells could cover corner) | **Low** — board bounds constrain to one valid origin | `start_corner_cell()` validates bounds; error if no valid cell found |
| Player confusion with JSON export vs CLI coordinates | **Medium** — two coordinate systems coexist | Document clearly in help text; JSON is labeled as "internal" |
| GUI affected | **None** — GUI is a separate rendering layer | No GUI files modified |
