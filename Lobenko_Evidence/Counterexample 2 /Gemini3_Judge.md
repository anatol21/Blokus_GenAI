# Evaluating PR atomicity for Blokus cache feature

**Session ID:** ses_1c3f51b29ffe2t5dkhXZzhTDrf
**Created:** 5/18/2026, 7:03:27 PM
**Updated:** 5/18/2026, 7:58:02 PM

---

## User

You are evaluating whether PRs #52, #53, #55, #56, and #58 were appropriately atomic steps in one feature implementation.
Feature context:
The PRs collectively implement an occupied-cell cache for a Blokus game engine.
Score each PR from 1 to 5 on:
1. Coherence: Could this PR merge safely alone if later PRs never happened?
2. Rollback value: Would reverting only this PR make sense as an independent rollback?
3. Distinct failure mode: Does this PR isolate a unique class of bug or behavior risk?
Scoring:
1 = no / very weak
2 = weak
3 = mixed or context-dependent
4 = strong
5 = very strong
Important:
- Do not score based on whether the final feature eventually worked.
- Consider the PR’s scope, diff, dependencies, and position in the sequence.
- Review cost is excluded. The question is whether each PR justified a full implementation agent cycle.
- Smaller diffs are not automatically bad if they isolate meaningful risk.
- Larger diffs are not automatically bad if they preserve one coherent intent.
Return:
- A table with scores for each PR and category.
- One short rationale per PR.
- A final recommendation: keep separate, bundle with previous/next, or reorder. gh url:https://github.com/anatol21/Blokus_GenAI/pull/53 

---

## Assistant (Build · Gemini 3 Flash Preview · 19.0s)

_Thinking:_

**Assessing Mergeability of PRs**

I'm currently evaluating five pull requests for the Blokus game engine. My focus is on determining the atomicity and overall appropriateness of each, specifically whether they can be safely merged independently and their rollback values. I'm analyzing their coherence and independence to ensure a smooth integration process.



I will fetch the details and diffs for PRs #52, #53, #55, #56, and #58 to analyze their scope and atomicity.



**Tool: bash**

**Input:**
```json
{
  "command": "for pr in 52 53 55 56 58; do\n  echo \"--- PR #$pr ---\"\n  gh pr view $pr --json title,body,state\n  gh pr diff $pr\ndone",
  "description": "Fetches metadata and diffs for PRs 52, 53, 55, 56, and 58."
}
```

**Output:**
```
--- PR #52 ---
failed to run git: fatal: not a git repository (or any of the parent directories): .git

failed to run git: fatal: not a git repository (or any of the parent directories): .git

--- PR #53 ---
failed to run git: fatal: not a git repository (or any of the parent directories): .git

failed to run git: fatal: not a git repository (or any of the parent directories): .git

--- PR #55 ---
failed to run git: fatal: not a git repository (or any of the parent directories): .git

failed to run git: fatal: not a git repository (or any of the parent directories): .git

--- PR #56 ---
failed to run git: fatal: not a git repository (or any of the parent directories): .git

failed to run git: fatal: not a git repository (or any of the parent directories): .git

--- PR #58 ---
failed to run git: fatal: not a git repository (or any of the parent directories): .git

failed to run git: fatal: not a git repository (or any of the parent directories): .git


```

---

## Assistant (Build · Gemini 3 Flash Preview · 8.1s)

I will fetch the metadata and diffs for the PRs by specifying the repository explicitly.



**Tool: bash**

**Input:**
```json
{
  "description": "Fetches metadata and diffs for PRs 52, 53, 55, 56, and 58 from the anatol21/Blokus_GenAI repository.",
  "command": "REPO=\"anatol21/Blokus_GenAI\"\nfor pr in 52 53 55 56 58; do\n  echo \"--- PR #$pr Metadata ---\"\n  gh pr view $pr -R $REPO --json title,body,state\n  echo \"--- PR #$pr Diff ---\"\n  gh pr diff $pr -R $REPO\ndone"
}
```

**Output:**
```
--- PR #52 Metadata ---
{"body":"## Summary\n- Add `GameState.occupied_cells_by_player: dict[str, set[Coordinate]]` as derived (non-serialized) state.\n- Initialize the cache in `new_game()` with one empty `set()` per configured player.\n- Add a minimal unit test asserting cache shape + existing initialization invariants (board empty, `remaining_pieces` intact).\n\n## Notes\n- This PR intentionally does *not* update rule logic (`apply_move`, `get_occupied_cells`, etc.). It only introduces and initializes the data structure (atomic step 1).\n\n## Testing\n- `./scripts/test.sh`","state":"MERGED","title":"Initialize occupied-cells cache field"}
--- PR #52 Diff ---
diff --git a/src/blokus/engine.py b/src/blokus/engine.py
index e5adc06..608f77b 100644
--- a/src/blokus/engine.py
+++ b/src/blokus/engine.py
@@ -23,6 +23,7 @@ def new_game(
     controller_strategies = {
         player: (strategies or {}).get(player, "default") for player in config.players
     }
+    occupied_cells_by_player: dict[str, set[Coordinate]] = {player: set() for player in config.players}
     return GameState(
         mode=mode,
         board=board,
@@ -31,6 +32,7 @@ def new_game(
         remaining_pieces={player: set(PIECE_IDS) for player in config.players},
         controller_types=controller_types,
         controller_strategies=controller_strategies,
+        occupied_cells_by_player=occupied_cells_by_player,
     )
 
 
diff --git a/src/blokus/models.py b/src/blokus/models.py
index 4e3a3d9..6ae681a 100644
--- a/src/blokus/models.py
+++ b/src/blokus/models.py
@@ -69,6 +69,14 @@ class GameState:
     finished: bool = False
     controller_types: dict[str, str] = field(default_factory=dict)
     controller_strategies: dict[str, str] = field(default_factory=dict)
+    # Cached occupied coordinates per player.
+    # This is derived state and is intentionally not serialized.
+    occupied_cells_by_player: dict[str, set[Coordinate]] = field(default_factory=dict, repr=False)
+
+    def __post_init__(self) -> None:
+        # Ensure every configured player has a cache entry.
+        for player in self.players:
+            self.occupied_cells_by_player.setdefault(player, set())
 
     @property
     def board_size(self) -> int:
@@ -97,6 +105,11 @@ def clone(self) -> "GameState":
             finished=self.finished,
             controller_types=dict(self.controller_types),
             controller_strategies=dict(self.controller_strategies),
+            # Derived cache is deep-copied for correctness in atomic step 1.
+            # Performance tradeoffs will be evaluated in a later atomic step.
+            occupied_cells_by_player={
+                player: set(cells) for player, cells in self.occupied_cells_by_player.items()
+            },
         )
 
     def to_dict(self) -> dict[str, object]:
diff --git a/tests/test_engine.py b/tests/test_engine.py
index ed1c145..cc5b4e5 100644
--- a/tests/test_engine.py
+++ b/tests/test_engine.py
@@ -11,7 +11,7 @@
     validate_pass,
 )
 from blokus.models import Move
-from blokus.pieces import absolute_cells
+from blokus.pieces import PIECE_IDS, absolute_cells
 
 
 def play_standard_opening_cycle():
@@ -50,6 +50,46 @@ def test_turn_order_is_enforced(self) -> None:
         self.assertFalse(result.ok)
         self.assertIn("It is blue's turn", result.reason)
 
+    def test_new_game_initializes_occupied_cells_by_player_cache(self) -> None:
+        state = new_game()
+
+        self.assertEqual(set(state.occupied_cells_by_player.keys()), set(state.players))
+        for player in state.players:
+            self.assertEqual(state.occupied_cells_by_player[player], set())
+
+        # Board remains empty.
+        self.assertTrue(all(cell is None for row in state.board for cell in row))
+
+        # Per-player cache entries must be distinct and independent.
+        state.occupied_cells_by_player["blue"].add((0, 0))
+        for player in state.players:
+            if player == "blue":
+                continue
+            self.assertEqual(state.occupied_cells_by_player[player], set())
+            self.assertIsNot(
+                state.occupied_cells_by_player["blue"],
+                state.occupied_cells_by_player[player],
+            )
+
+        # Existing initialization behavior remains intact.
+        self.assertEqual(set(state.remaining_pieces.keys()), set(state.players))
+        for player in state.players:
+            self.assertEqual(state.remaining_pieces[player], set(PIECE_IDS))
+
+    def test_clone_deep_copies_occupied_cells_by_player_sets(self) -> None:
+        state = new_game()
+        state.occupied_cells_by_player["blue"].add((0, 0))
+
+        cloned = state.clone()
+        self.assertIsNot(
+            state.occupied_cells_by_player["blue"],
+            cloned.occupied_cells_by_player["blue"],
+        )
+
+        cloned.occupied_cells_by_player["blue"].add((1, 1))
+        self.assertEqual(state.occupied_cells_by_player["blue"], {(0, 0)})
+        self.assertEqual(cloned.occupied_cells_by_player["blue"], {(0, 0), (1, 1)})
+
     def test_same_color_edge_contact_is_illegal(self) -> None:
         state = play_standard_opening_cycle()
         result = validate_move(state, Move("blue", "I2", 1, 0))
diff --git a/tests/test_serialization.py b/tests/test_serialization.py
index 6b26d1b..6b62640 100644
--- a/tests/test_serialization.py
+++ b/tests/test_serialization.py
@@ -22,6 +22,15 @@ def test_initial_fixture_round_trips(self) -> None:
         state = GameState.from_dict(payload)
         self.assertEqual(state.to_dict(), payload)
 
+    def test_state_to_dict_excludes_occupied_cells_by_player(self) -> None:
+        state = new_game()
+        payload = state.to_dict()
+        self.assertNotIn("occupied_cells_by_player", payload)
+
+        # Deserialization should not require derived cache fields.
+        reloaded = GameState.from_dict(payload)
+        self.assertEqual(set(reloaded.occupied_cells_by_player.keys()), set(reloaded.players))
+
     def test_state_round_trip_after_moves(self) -> None:
         state = new_game(
             controllers={"blue": "computer", "yellow": "human", "red": "human", "green": "human"},
--- PR #53 Metadata ---
{"body":"## Summary\n- Update `apply_move` to keep `occupied_cells_by_player` consistent with the cloned board after a legal placement.\n- Add focused unit tests verifying cache updates for the moving player, no mutation of the input state, and no cache updates on illegal moves.\n\n## Scope\n- Atomic Step 2 only: write-path cache maintenance on legal `apply_move` calls.\n- No read-path refactors (e.g., `get_occupied_cells`, touch checks, anchors) and no rule/validation changes.\n\n## Testing\n- `./scripts/test.sh`","state":"MERGED","title":"Atomic Step 2: update occupied-cell cache on apply_move"}
--- PR #53 Diff ---
diff --git a/src/blokus/engine.py b/src/blokus/engine.py
index 608f77b..187441c 100644
--- a/src/blokus/engine.py
+++ b/src/blokus/engine.py
@@ -245,15 +245,19 @@ def apply_move(state: GameState, move: Move) -> GameState:
         raise ValueError(result.reason)
 
     new_state = state.clone()
-    cells = absolute_cells(
-        move.piece,
-        origin=(move.x, move.y),
-        rotation=move.rotation,
-        flipped=move.flipped,
+    cells = tuple(
+        absolute_cells(
+            move.piece,
+            origin=(move.x, move.y),
+            rotation=move.rotation,
+            flipped=move.flipped,
+        )
     )
     # Materialize the piece on the cloned board before advancing turn metadata.
     for x, y in cells:
         new_state.board[y][x] = move.player
+    # Keep the derived occupied-cells cache consistent with the cloned board.
+    new_state.occupied_cells_by_player[move.player].update(cells)
     new_state.remaining_pieces[move.player].remove(move.piece)
     new_state.history.append(move)
     new_state.current_player_index = _next_player_index(new_state)
diff --git a/tests/test_engine.py b/tests/test_engine.py
index cc5b4e5..023b5e7 100644
--- a/tests/test_engine.py
+++ b/tests/test_engine.py
@@ -109,6 +109,70 @@ def test_apply_move_updates_turn_history_and_piece_pool(self) -> None:
         self.assertNotIn("I1", next_state.remaining_pieces["blue"])
         self.assertEqual(next_state.board[0][0], "blue")
 
+    def test_apply_move_adds_placed_cells_to_occupied_cells_cache(self) -> None:
+        state = new_game()
+        move = Move("blue", "I2", 0, 0)
+
+        next_state = apply_move(state, move)
+
+        board_cells = {
+            (x, y)
+            for y, row in enumerate(next_state.board)
+            for x, cell in enumerate(row)
+            if cell == "blue"
+        }
+        self.assertEqual(next_state.occupied_cells_by_player["blue"], board_cells)
+
+        # Existing board behavior still matches the applied move.
+        self.assertEqual(board_cells, {(0, 0), (1, 0)})
+
+    def test_apply_move_does_not_mutate_original_state_cache(self) -> None:
+        state = new_game()
+        move = Move("blue", "I2", 0, 0)
+
+        _ = apply_move(state, move)
+
+        # Original state remains unchanged.
+        self.assertEqual(state.occupied_cells_by_player["blue"], set())
+        self.assertTrue(all(cell is None for row in state.board for cell in row))
+
+    def test_apply_move_does_not_update_other_players_cache_sets(self) -> None:
+        state = new_game()
+        move = Move("blue", "I2", 0, 0)
+
+        next_state = apply_move(state, move)
+
+        for player in next_state.players:
+            if player == "blue":
+                continue
+            self.assertEqual(next_state.occupied_cells_by_player[player], set())
+
+    def test_apply_move_illegal_move_raises_and_does_not_mutate_board_or_cache(self) -> None:
+        state = new_game()
+        # Add a sentinel to ensure we detect cache mutation (cache is derived and not serialized).
+        state.occupied_cells_by_player["blue"].add((5, 5))
+        before_board = [row[:] for row in state.board]
+        before_cache = {player: set(cells) for player, cells in state.occupied_cells_by_player.items()}
+
+        with self.assertRaisesRegex(ValueError, "must cover start corner"):
+            apply_move(state, Move("blue", "I1", 1, 1))
+
+        self.assertEqual(state.board, before_board)
+        self.assertEqual(state.occupied_cells_by_player, before_cache)
+
+    def test_occupied_cells_cache_accumulates_and_matches_board_per_player(self) -> None:
+        state = play_standard_opening_cycle()
+        state = apply_move(state, Move("blue", "I2", 1, 1))
+
+        for player in state.players:
+            board_cells = {
+                (x, y)
+                for y, row in enumerate(state.board)
+                for x, cell in enumerate(row)
+                if cell == player
+            }
+            self.assertEqual(state.occupied_cells_by_player[player], board_cells)
+
     def test_pass_requires_player_to_be_blocked(self) -> None:
         state = new_game()
         with self.assertRaisesRegex(ValueError, "only pass when no legal move exists"):
--- PR #55 Metadata ---
{"body":"## Summary\n- Refactors `get_occupied_cells`, `is_first_move`, and `occupied_square_counts` to read from `GameState.occupied_cells_by_player` instead of scanning the board.\n- Returns defensive copies from `get_occupied_cells` so callers cannot mutate the internal cache.\n- Adds focused unit tests that validate cache-backed behavior while deriving expected occupied cells by scanning `state.board`.\n\n## Why This Step Is Limited\nThis change is intentionally scoped to cache *reads* only; it relies on the already-merged cache maintenance in `apply_move` and avoids touching move validation, move generation, serialization, or any cache rebuild logic.\n\n## Testing\n- `./scripts/test.sh`","state":"MERGED","title":"Use occupied-cells cache for read helpers"}
--- PR #55 Diff ---
diff --git a/src/blokus/engine.py b/src/blokus/engine.py
index 187441c..89abfe8 100644
--- a/src/blokus/engine.py
+++ b/src/blokus/engine.py
@@ -45,20 +45,20 @@ def board_in_bounds(state: GameState, x: int, y: int) -> bool:
 def get_occupied_cells(state: GameState, player: str | None = None) -> set[Coordinate]:
     """Collect occupied coordinates, optionally filtering to one player."""
 
-    occupied: set[Coordinate] = set()
-    for y, row in enumerate(state.board):
-        for x, cell in enumerate(row):
-            if cell is None:
-                continue
-            if player is None or cell == player:
-                occupied.add((x, y))
-    return occupied
+    # Read from the derived cache, but always return defensive copies so callers
+    # cannot mutate internal state.
+    if player is None:
+        occupied: set[Coordinate] = set()
+        for cells in state.occupied_cells_by_player.values():
+            occupied.update(cells)
+        return occupied
+    return set(state.occupied_cells_by_player.get(player, set()))
 
 
 def is_first_move(state: GameState, player: str) -> bool:
     """Return whether the player has not yet placed any piece."""
 
-    return not any(cell == player for row in state.board for cell in row)
+    return not state.occupied_cells_by_player.get(player, set())
 
 
 def _has_edge_contact_with_player(state: GameState, player: str, cells: tuple[Coordinate, ...]) -> bool:
@@ -319,9 +319,7 @@ def compute_scores(state: GameState) -> dict[str, int]:
 
 
 def occupied_square_counts(state: GameState) -> dict[str, int]:
-    counts = {player: 0 for player in state.players}
-    for row in state.board:
-        for cell in row:
-            if cell is not None:
-                counts[cell] += 1
-    return counts
+    return {
+        player: len(state.occupied_cells_by_player.get(player, set()))
+        for player in state.players
+    }
diff --git a/tests/test_engine.py b/tests/test_engine.py
index 023b5e7..f702b6f 100644
--- a/tests/test_engine.py
+++ b/tests/test_engine.py
@@ -3,8 +3,11 @@
 from blokus.engine import (
     apply_move,
     compute_scores,
+    get_occupied_cells,
+    is_first_move,
     list_legal_moves,
     new_game,
+    occupied_square_counts,
     pass_turn,
     score_player,
     validate_move,
@@ -109,6 +112,76 @@ def test_apply_move_updates_turn_history_and_piece_pool(self) -> None:
         self.assertNotIn("I1", next_state.remaining_pieces["blue"])
         self.assertEqual(next_state.board[0][0], "blue")
 
+    def test_get_occupied_cells_returns_player_cache_after_legal_move(self) -> None:
+        state = new_game()
+        state = apply_move(state, Move("blue", "I2", 0, 0))
+
+        expected_blue = {
+            (x, y)
+            for y, row in enumerate(state.board)
+            for x, cell in enumerate(row)
+            if cell == "blue"
+        }
+        self.assertEqual(state.occupied_cells_by_player["blue"], expected_blue)
+        self.assertEqual(get_occupied_cells(state, "blue"), expected_blue)
+
+    def test_get_occupied_cells_returns_union_across_players(self) -> None:
+        state = play_standard_opening_cycle()
+
+        expected_all = {
+            (x, y)
+            for y, row in enumerate(state.board)
+            for x, cell in enumerate(row)
+            if cell is not None
+        }
+        self.assertEqual(get_occupied_cells(state), expected_all)
+
+    def test_get_occupied_cells_returns_defensive_copy(self) -> None:
+        state = new_game()
+        state = apply_move(state, Move("blue", "I2", 0, 0))
+
+        returned = get_occupied_cells(state, "blue")
+        self.assertEqual(returned, state.occupied_cells_by_player["blue"])
+
+        # Mutating the returned set must not mutate the internal cache.
+        returned.add((5, 5))
+        returned.discard(next(iter(state.occupied_cells_by_player["blue"])))
+        self.assertNotIn((5, 5), state.occupied_cells_by_player["blue"])
+        self.assertEqual(
+            state.occupied_cells_by_player["blue"],
+            {
+                (x, y)
+                for y, row in enumerate(state.board)
+                for x, cell in enumerate(row)
+                if cell == "blue"
+            },
+        )
+
+    def test_is_first_move_reflects_player_occupancy(self) -> None:
+        state = new_game()
+        self.assertTrue(is_first_move(state, "blue"))
+
+        state = apply_move(state, Move("blue", "I2", 0, 0))
+        self.assertFalse(is_first_move(state, "blue"))
+        self.assertTrue(is_first_move(state, "yellow"))
+
+    def test_occupied_square_counts_matches_board_after_moves(self) -> None:
+        state = play_standard_opening_cycle()
+        state = apply_move(state, Move("blue", "I2", 1, 1))
+
+        expected_counts = {player: 0 for player in state.players}
+        for row in state.board:
+            for cell in row:
+                if cell is not None:
+                    expected_counts[cell] += 1
+
+        self.assertEqual(occupied_square_counts(state), expected_counts)
+
+    def test_cache_read_functions_preserve_unknown_player_behavior(self) -> None:
+        state = new_game()
+        self.assertEqual(get_occupied_cells(state, "orange"), set())
+        self.assertTrue(is_first_move(state, "orange"))
+
     def test_apply_move_adds_placed_cells_to_occupied_cells_cache(self) -> None:
         state = new_game()
         move = Move("blue", "I2", 0, 0)
@@ -150,7 +223,8 @@ def test_apply_move_does_not_update_other_players_cache_sets(self) -> None:
     def test_apply_move_illegal_move_raises_and_does_not_mutate_board_or_cache(self) -> None:
         state = new_game()
         # Add a sentinel to ensure we detect cache mutation (cache is derived and not serialized).
-        state.occupied_cells_by_player["blue"].add((5, 5))
+        # Use a non-active player so first-move logic for the mover stays intact.
+        state.occupied_cells_by_player["yellow"].add((5, 5))
         before_board = [row[:] for row in state.board]
         before_cache = {player: set(cells) for player, cells in state.occupied_cells_by_player.items()}
 
--- PR #56 Metadata ---
{"body":"## Summary\n- Reuse the cache-backed occupied set when generating anchors to avoid repeated defensive copies.\n- Add focused rule/anchor tests to ensure move validation and move generation are unchanged.\n\n## Testing\n- ./scripts/test.sh\n\n## Scope Notes\n- Change is intentionally limited to cache-read behavior in the same-color contact / anchor helper step; opening/edge/corner semantics are unchanged.","state":"MERGED","title":"Refactor anchor helpers to reuse occupied-cell cache"}
--- PR #56 Diff ---
diff --git a/src/blokus/engine.py b/src/blokus/engine.py
index 89abfe8..c24b5e9 100644
--- a/src/blokus/engine.py
+++ b/src/blokus/engine.py
@@ -168,9 +168,10 @@ def _anchor_cells(state: GameState, player: str) -> set[Coordinate]:
     if is_first_move(state, player):
         return {state.start_corners[player]}
 
-    occupied = get_occupied_cells(state, player)
+    # Only same-color occupancy matters for anchor eligibility.
+    occupied_same_color = get_occupied_cells(state, player)
     anchors: set[Coordinate] = set()
-    for x, y in occupied:
+    for x, y in occupied_same_color:
         for dx, dy in DIAGONAL_DELTAS:
             anchor = (x + dx, y + dy)
             ax, ay = anchor
@@ -179,7 +180,12 @@ def _anchor_cells(state: GameState, player: str) -> set[Coordinate]:
                 continue
             if state.board[ay][ax] is not None:
                 continue
-            if _has_edge_contact_with_player(state, player, (anchor,)):
+            # Avoid re-reading the occupied-cell cache for every candidate anchor.
+            # Opponent orthogonal adjacency is allowed in Blokus; only same-color edge contact is illegal.
+            if any(
+                (ax + odx, ay + ody) in occupied_same_color
+                for odx, ody in ORTHOGONAL_DELTAS
+            ):
                 continue
             anchors.add(anchor)
     return anchors
diff --git a/tests/test_engine.py b/tests/test_engine.py
index f702b6f..4171c93 100644
--- a/tests/test_engine.py
+++ b/tests/test_engine.py
@@ -1,6 +1,7 @@
 import unittest
 
 from blokus.engine import (
+    _anchor_cells,
     apply_move,
     compute_scores,
     get_occupied_cells,
@@ -104,6 +105,63 @@ def test_same_color_corner_contact_is_legal(self) -> None:
         result = validate_move(state, Move("blue", "I2", 1, 1))
         self.assertTrue(result.ok)
 
+    def test_non_opening_move_requires_same_color_corner_contact(self) -> None:
+        state = play_standard_opening_cycle()
+
+        # Far from blue's starting piece: no edge contact and no diagonal contact.
+        result = validate_move(state, Move("blue", "I2", 5, 5))
+        self.assertFalse(result.ok)
+        self.assertIn("touch at least one same-color piece at a corner", result.reason)
+
+    def test_anchor_cells_are_empty_in_bounds_and_avoid_same_color_edge_contact(self) -> None:
+        state = play_standard_opening_cycle()
+
+        anchors = _anchor_cells(state, "blue")
+        orthogonal = ((1, 0), (-1, 0), (0, 1), (0, -1))
+        occupied_all = {
+            (x, y)
+            for y, row in enumerate(state.board)
+            for x, cell in enumerate(row)
+            if cell is not None
+        }
+        occupied_blue = {
+            (x, y)
+            for y, row in enumerate(state.board)
+            for x, cell in enumerate(row)
+            if cell == "blue"
+        }
+        self.assertTrue(anchors.isdisjoint(occupied_all))
+        self.assertTrue(
+            all(0 <= x < state.board_size and 0 <= y < state.board_size for x, y in anchors)
+        )
+        self.assertTrue(
+            all(
+                all((ax + dx, ay + dy) not in occupied_blue for dx, dy in orthogonal)
+                for ax, ay in anchors
+            )
+        )
+
+    def test_anchor_cells_allow_opponent_orthogonal_adjacency(self) -> None:
+        state = play_standard_opening_cycle()
+
+        # (1, 1) is a natural blue anchor (diagonal from blue's opening at (0, 0)).
+        expected_anchor = (1, 1)
+
+        # Place an opponent square orthogonally adjacent to that anchor.
+        # This must not disqualify the anchor because only same-color edge contact is illegal.
+        state.board[0][1] = "yellow"
+        state.occupied_cells_by_player["yellow"].add((1, 0))
+
+        anchors = _anchor_cells(state, "blue")
+        self.assertIn(expected_anchor, anchors)
+
+    def test_list_legal_moves_returns_valid_moves_after_opening(self) -> None:
+        state = play_standard_opening_cycle()
+
+        moves = list_legal_moves(state, limit=50)
+        self.assertTrue(moves)
+        self.assertTrue(all(validate_move(state, move).ok for move in moves))
+
     def test_apply_move_updates_turn_history_and_piece_pool(self) -> None:
         state = new_game()
         next_state = apply_move(state, Move("blue", "I1", 0, 0))
--- PR #58 Metadata ---
{"body":"## Summary\n- Add regression tests that derive occupied cells by scanning `state.board` and assert the occupied-cell cache stays consistent across normal play, cloning, and serialization round-trips.\n- Fix `GameState.from_dict()` to rebuild `occupied_cells_by_player` from the parsed board so deserialized states are immediately usable by cache-backed helpers.\n\n## Testing\n- `./scripts/test.sh`","state":"MERGED","title":"Rebuild occupied-cell cache on deserialization"}
--- PR #58 Diff ---
diff --git a/src/blokus/models.py b/src/blokus/models.py
index 6ae681a..0ea8266 100644
--- a/src/blokus/models.py
+++ b/src/blokus/models.py
@@ -167,6 +167,18 @@ def from_dict(cls, data: dict[str, object]) -> "GameState":
                     parsed_row.append(player_for_symbol(symbol))
             board.append(parsed_row)
 
+        # Rebuild derived occupied-cells cache from the parsed board.
+        occupied_cells_by_player: dict[str, set[Coordinate]] = {player: set() for player in players}
+        for y, row in enumerate(board):
+            for x, cell in enumerate(row):
+                if cell is None:
+                    continue
+                if cell not in occupied_cells_by_player:
+                    raise ValueError(
+                        f"Board contains player '{cell}' not present in players {players!r}."
+                    )
+                occupied_cells_by_player[cell].add((x, y))
+
         remaining_source = data.get("remaining_pieces")
         if not isinstance(remaining_source, dict):
             raise ValueError("State is missing 'remaining_pieces'.")
@@ -218,4 +230,5 @@ def from_dict(cls, data: dict[str, object]) -> "GameState":
             finished=bool(data.get("finished", False)),
             controller_types=controllers,
             controller_strategies=strategies,
+            occupied_cells_by_player=occupied_cells_by_player,
         )
diff --git a/tests/test_engine.py b/tests/test_engine.py
index 4171c93..1f24a49 100644
--- a/tests/test_engine.py
+++ b/tests/test_engine.py
@@ -37,6 +37,27 @@ def blocked_blue_state():
     return state
 
 
+def board_occupied_cells(state):
+    """Derive occupied cells by scanning the board (not cache-backed helpers)."""
+
+    expected_all = {
+        (x, y)
+        for y, row in enumerate(state.board)
+        for x, cell in enumerate(row)
+        if cell is not None
+    }
+    expected_by_player = {
+        player: {
+            (x, y)
+            for y, row in enumerate(state.board)
+            for x, cell in enumerate(row)
+            if cell == player
+        }
+        for player in state.players
+    }
+    return expected_all, expected_by_player
+
+
 class EngineRuleTests(unittest.TestCase):
     def test_unsupported_duo_mode_is_rejected(self) -> None:
         with self.assertRaisesRegex(ValueError, "Unsupported mode 'duo'"):
@@ -94,6 +115,25 @@ def test_clone_deep_copies_occupied_cells_by_player_sets(self) -> None:
         self.assertEqual(state.occupied_cells_by_player["blue"], {(0, 0)})
         self.assertEqual(cloned.occupied_cells_by_player["blue"], {(0, 0), (1, 1)})
 
+    def test_clone_preserves_cache_contents_without_sharing_sets_after_moves(self) -> None:
+        state = play_standard_opening_cycle()
+        state = apply_move(state, Move("blue", "I2", 1, 1))
+
+        cloned = state.clone()
+        for player in state.players:
+            self.assertEqual(
+                cloned.occupied_cells_by_player[player],
+                state.occupied_cells_by_player[player],
+            )
+            self.assertIsNot(
+                cloned.occupied_cells_by_player[player],
+                state.occupied_cells_by_player[player],
+            )
+
+        # Mutating the clone must not affect the original.
+        cloned.occupied_cells_by_player["blue"].add((2, 2))
+        self.assertNotIn((2, 2), state.occupied_cells_by_player["blue"])
+
     def test_same_color_edge_contact_is_illegal(self) -> None:
         state = play_standard_opening_cycle()
         result = validate_move(state, Move("blue", "I2", 1, 0))
@@ -194,6 +234,15 @@ def test_get_occupied_cells_returns_union_across_players(self) -> None:
         }
         self.assertEqual(get_occupied_cells(state), expected_all)
 
+    def test_get_occupied_cells_matches_board_scan_per_player_after_multiple_moves(self) -> None:
+        state = play_standard_opening_cycle()
+        # Extend beyond the opening cycle to cover incremental cache updates.
+        state = apply_move(state, Move("blue", "I2", 1, 1))
+
+        _expected_all, expected_by_player = board_occupied_cells(state)
+        for player in state.players:
+            self.assertEqual(get_occupied_cells(state, player), expected_by_player[player])
+
     def test_get_occupied_cells_returns_defensive_copy(self) -> None:
         state = new_game()
         state = apply_move(state, Move("blue", "I2", 0, 0))
diff --git a/tests/test_serialization.py b/tests/test_serialization.py
index 6b62640..4cc6a35 100644
--- a/tests/test_serialization.py
+++ b/tests/test_serialization.py
@@ -3,7 +3,7 @@
 from typing import cast
 import unittest
 
-from blokus.engine import apply_move, new_game
+from blokus.engine import apply_move, get_occupied_cells, new_game
 from blokus.models import GameState, Move
 from blokus.review.types import Finding, ReviewPayload, ReviewResult, ReviewSummary, UncertainRisk
 
@@ -11,6 +11,27 @@
 REPO_ROOT = Path(__file__).resolve().parents[1]
 
 
+def board_occupied_cells(state: GameState):
+    """Derive occupied cells by scanning the board (not cache-backed helpers)."""
+
+    expected_all = {
+        (x, y)
+        for y, row in enumerate(state.board)
+        for x, cell in enumerate(row)
+        if cell is not None
+    }
+    expected_by_player = {
+        player: {
+            (x, y)
+            for y, row in enumerate(state.board)
+            for x, cell in enumerate(row)
+            if cell == player
+        }
+        for player in state.players
+    }
+    return expected_all, expected_by_player
+
+
 class SerializationTests(unittest.TestCase):
     def load_initial_payload(self) -> dict[str, object]:
         fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
@@ -49,6 +70,26 @@ def test_state_round_trip_after_moves(self) -> None:
         self.assertEqual(reloaded.controller_types["blue"], "computer")
         self.assertEqual(reloaded.controller_strategies["blue"], "default")
 
+    def test_round_tripped_state_rebuilds_occupied_cells_cache_from_board(self) -> None:
+        state = new_game()
+        for move in (
+            Move("blue", "I1", 0, 0),
+            Move("yellow", "I1", 19, 0),
+            Move("red", "I1", 19, 19),
+            Move("green", "I1", 0, 19),
+            Move("blue", "I2", 1, 1),
+        ):
+            state = apply_move(state, move)
+
+        reloaded = GameState.from_dict(state.to_dict())
+        expected_all, expected_by_player = board_occupied_cells(reloaded)
+
+        for player in reloaded.players:
+            self.assertEqual(reloaded.occupied_cells_by_player[player], expected_by_player[player])
+            self.assertEqual(get_occupied_cells(reloaded, player), expected_by_player[player])
+
+        self.assertEqual(get_occupied_cells(reloaded), expected_all)
+
     def test_invalid_board_symbol_is_rejected(self) -> None:
         payload = self.load_initial_payload()
         board = cast(list[str], payload["board"])
@@ -56,6 +97,16 @@ def test_invalid_board_symbol_is_rejected(self) -> None:
         with self.assertRaisesRegex(ValueError, "No player configured for board symbol"):
             GameState.from_dict(payload)
 
+    def test_board_player_missing_from_players_is_rejected(self) -> None:
+        payload = self.load_initial_payload()
+
+        # 'O' maps to player 'orange' which is not in classic mode's player list.
+        board = cast(list[str], payload["board"])
+        board[0] = "O" + board[0][1:]
+
+        with self.assertRaisesRegex(ValueError, "Board contains player 'orange'"):
+            GameState.from_dict(payload)
+
     def test_mismatched_player_list_is_rejected(self) -> None:
         payload = self.load_initial_payload()
         payload["players"] = ["blue", "yellow"]

```

---

## Assistant (Build · Gemini 3 Flash Preview · 13.1s)

_Thinking:_

**Analyzing PRs**

I've begun by reviewing five pull requests. My initial focus has been PR #52, which introduces and initializes the `occupied_cells_by_player` cache field within `GameState`, including necessary cloning logic and foundational tests.

**Implementing Cache Optimization**

I've processed PRs #52 through #56. The work focused on initializing the `occupied_cells_by_player` cache, updating it during move application, and then refactoring read helpers and anchor logic to leverage this new cache. This completes the initial implementation and utilization of the cache.

**Validating Caching Logic**

I've now scored the previous PRs and am evaluating PR #58, specifically focusing on its role in rebuilding the occupied-cell cache during deserialization and ensuring regression tests for serialization round-trips are robust. This addresses potential bugs during game persistence and recovery.

**Refining Cache Dependencies**

I'm currently assessing PR #58, noting its reliance on prior caching implementations for occupancy. My focus is on ensuring this deserialization logic correctly rebuilds the cache, thereby validating the robustness of serialization and deserialization processes for game state persistence and recovery.



The following table evaluates the atomicity and justification for PRs #52, #53, #55, #56, and #58 in the implementation of the occupied-cell cache.

### Scoring Table

| PR # | Coherence | Rollback Value | Distinct Failure Mode | Total / 15 |
| :--- | :---: | :---: | :---: | :---: |
| **52** | 5 | 5 | 2 | **12** |
| **53** | 4 | 4 | 5 | **13** |
| **55** | 3 | 4 | 4 | **11** |
| **56** | 4 | 4 | 4 | **12** |
| **58** | 1 | 5 | 5 | **11** |

### Rationales

*   **PR #52 (Initialize field):** High coherence as a standalone data structure introduction. While the failure mode (initialization/clone bugs) is narrow, it isolates the "scaffolding" from the logic.
*   **PR #53 (Update on apply_move):** Strong isolation of the "write path." This is the most critical step for cache integrity. Separating it from the read path ensures that bugs in incremental updates are caught before the engine actually relies on the data.
*   **PR #55 (Read helpers):** Mixed coherence because it makes the engine's core helpers dependent on the cache. If merged without the write-path or deserialization logic, it causes immediate "invisible" failures (empty results). However, it isolates basic occupancy logic from complex anchor logic.
*   **PR #56 (Anchor helpers):** Strong distinct behavior risk. Anchor generation is the most complex part of Blokus; isolating this optimization allows for independent verification of diagonal/orthogonal rules without risking basic score/occupancy reporting.
*   **PR #58 (Deserialization):** Low coherence because it fixes a "broken" state created by the previous PRs (where reloaded games have empty caches). However, its rollback value and distinct failure mode (serialization mismatch) are very strong, as it isolates the boundary between persistence and runtime state.

### Final Recommendation

**Bundle #52 and #53; Keep #55, #56, and #58 separate.**

1.  **Bundle #52 and #53:** Initializing a field that is never updated (#52) has no functional value alone. Combining the definition with the write-path maintenance creates a single, coherent "Passive Cache" checkpoint where the cache exists and stays correct, even if not yet utilized.
2.  **Keep #55 and #56 separate:** These represent two different levels of engine complexity. #55 handles simple metadata (scores/occupancy), while #56 handles recursive-like search logic (anchors). Isolating #56 is beneficial for performance profiling and rule-compliance debugging.
3.  **Keep #58 separate but move it earlier:** #58 is a "bug fix" for the state introduced in #52. If the feature were to be implemented again, rebuilding the cache on deserialization should ideally happen as soon as the field is introduced (#52) to ensure the system remains consistent at every step of the transition. Integrating #58's logic into the #52/#53 bundle would be the most "atomic" approach for a production-ready feature.

---

## User

Follow-up: Please add a fourth score: Cost Proportionality.

Definition:
Cost Proportionality = Was a full implementation agentic cycle justified by the risk reduction, review clarity, and rollback value of this PR?

A "full implementation agentic cycle" means a separate agent run for the PR that includes most or all of:
- loading repository and PR context
- reading relevant files/diffs
- planning the implementation
- generating or editing code
- generating or updating tests
- running or interpreting validation
- summarizing the result
- preparing the PR-level explanation

This score is not about review-agent cost. Review is excluded because review provides independent value and may benefit from smaller diffs. This score is about whether the implementation-side overhead of a separate agent run was justified.

Scale:
1 = clearly too small / should be a checkpoint inside a larger agent run
2 = weak justification for a full separate implementation cycle
3 = debatable
4 = strong justification
5 = clearly worth a separate full implementation agentic cycle

Use the same PRs: #52, #53, #55, #56, #58.

Return:
- a table with Cost Proportionality for each PR
- revised recommendation per PR
- one sentence explaining whether your original recommendation changed 

---

## Assistant (Build · Gemini 3 Flash Preview · 12.0s)

_Thinking:_

**Defining Cost Proportionality**

I'm currently refining the concept of "Cost Proportionality." The core idea is to evaluate whether the resources invested in an agentic cycle were truly warranted by the benefits gained in risk reduction, review clarity, and rollback potential. I'm wrestling with how to best quantify this, aiming for a practical and insightful metric.

**Evaluating Agentic Cycle Costs**

I'm continuing to analyze the agentic cycle, specifically focusing on cost proportionality. My current thinking involves scoring each PR based on implementation effort versus the inherent risk and complexity of the change. I'm applying this to specific PRs, like #52 for initialization and #53 for cache updates, to see how the scale of effort aligns with the perceived value and potential risks.

**Scoring PR Cost Proportionality**

I've been evaluating several pull requests, assigning scores for cost proportionality. PR #55, involving defensive copies and refactoring, received a 4, deemed justified for shifting the engine's data source. Similarly, PR #56, refactoring anchor logic, also scored a 4, highly justified due to the sensitivity of anchors. PR #58, fixing deserialization with regression tests, earned a 4 as well.

**Refining Cost Proportionality Scores**

I've updated the cost proportionality scores for several PRs. #52 is rated a 1 as it's too minor for an agent cycle, but #53, #55, #56, and #58 all scored 4 or 5, reflecting their distinct risks and complexities that justify isolated agentic cycles. The original recommendation to bundle #52 and #53 remains, reinforced by these scores.



### Cost Proportionality Evaluation

| PR # | Cost Proportionality (1-5) | Revised Recommendation |
| :--- | :---: | :--- |
| **52** | 1 | **Bundle** with #53. |
| **53** | 4 | **Bundle** with #52. |
| **55** | 4 | **Keep separate.** |
| **56** | 5 | **Keep separate.** |
| **58** | 4 | **Keep separate** (or bundle with #52). |

### Rationales for Cost Proportionality

*   **PR #52 (Score: 1):** The implementation overhead (context loading, boilerplate tests) significantly outweighs the logic complexity. This is a "setup" step that should be a checkpoint within a larger agent run.
*   **PR #53 (Score: 4):** Justified because it requires a dedicated implementation/testing focus on **state mutation invariants**. The agent must verify that the original state isn't touched and that the cache remains a perfect mirror of the board during incremental updates.
*   **PR #55 (Score: 4):** Justified as a **refactoring phase**. It requires the agent to systematically find and replace board-scans with cache-reads while implementing defensive copying logic to prevent external corruption—a distinct "read-safety" task.
*   **PR #56 (Score: 5):** Strongly justified. Anchor generation is the "hot path" of the engine. A dedicated cycle allows the agent to focus purely on **algorithmic correctness and performance** (e.g., avoiding redundant lookups) without the noise of basic state plumbing.
*   **PR #58 (Score: 4):** Justified as a **boundary/persistence task**. Handling the transition from JSON/Dict to a derived Pythonic `set()` is a unique class of implementation work with specific round-trip testing requirements.

### Final Conclusion
**My original recommendation did not change, but the Cost Proportionality score confirms that PR #52 is too trivial to justify the overhead of a standalone implementation cycle.**

The high implementation cost of #52 (which provides zero functional utility on its own) makes it the weakest link in the chain, whereas the specific risks associated with the write-path (#53), read-path (#55), complex-logic (#56), and serialization (#58) justify their individual cycles.

---

