# Engine And Gameplay Guide

## Scope

This guide documents engine and gameplay behavior from the GitHub source of truth:
`anatol21/Blokus_GenAI@main`. It focuses on Classic gameplay because Classic is the
primary rule baseline and fixture-backed review target. Duo is also engine-supported
through the same mode configuration layer and is summarized where it affects shared
engine behavior.

This guide intentionally excludes CLI usage, JSON serialization walkthroughs, schema
contracts, and import validation details.

## Mode Baselines

Classic is the primary gameplay baseline:

- Board: 20x20.
- Players and turn order: `blue`, `yellow`, `red`, `green`.
- Start corners: `blue` at `(0, 0)`, `yellow` at `(19, 0)`, `red` at `(19, 19)`,
  and `green` at `(0, 19)`.
- Evidence: `CLASSIC_CONFIG` in
  [`src/blokus/config.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/src/blokus/config.py)
  and the Classic opening fixture in
  [`fixtures/scenarios/classic_corner_sequence.json`](https://github.com/anatol21/Blokus_GenAI/blob/main/fixtures/scenarios/classic_corner_sequence.json).

Duo is implemented in the shared engine through `ModeConfig`:

- Board: 14x14.
- Players and turn order: `blue`, `red`.
- Start corners: `blue` at `(4, 4)` and `red` at `(9, 9)`.
- The same validation, move application, legal-move listing, passing, scoring, and
  computer-player helpers operate on the configured mode.

The GUI remains Classic-only in the current manual documentation. That is a
presentation-layer limit, not an engine-mode limit.

## Gameplay Rules

Each player has the standard 21-piece catalog: 12 pentominoes, 5 tetrominoes,
2 triominoes, 1 domino, and 1 monomino, for 89 total squares. The piece catalog
normalizes local cells, supports clockwise rotations and horizontal flips, and stores
only unique transformed orientations so symmetric pieces do not duplicate equivalent
placements.

A legal placement must satisfy all core Blokus constraints:

- The game must not already be finished.
- The player must belong to the active mode.
- Turn-enforcing validation requires the move player to match `state.current_player`.
- The piece id must exist and still be available in that player's rack.
- Every occupied square of the transformed piece must be in bounds.
- The placement must not overlap any occupied board square.
- A player's opening move must cover that player's configured start corner.
- Later moves must touch at least one same-color square diagonally.
- Later moves must not touch a same-color square orthogonally.
- Opponent edge or corner contact is allowed; only same-color edge contact is illegal.

The tests emphasize Classic coverage for these rules, including off-corner openings,
turn-order rejection, same-color edge rejection, same-color corner acceptance, unknown
players, unknown pieces, spent pieces, out-of-bounds moves, finished games, and
non-mutating rejection paths.

## Engine Lifecycle

`new_game(mode)` creates an empty board from `ModeConfig`, initializes players,
start corners, each player's remaining-piece set, controller metadata, and a derived
`occupied_cells_by_player` cache.

`validate_move(state, move)` applies public turn-enforcing validation and returns a
`ValidationResult`. Internal validation can also run without turn enforcement so
`list_legal_moves` can ask whether a candidate is legal for a specific player.

`apply_move(state, move)` validates first. If the move is illegal, it raises
`ValueError` and leaves the input state unchanged. If legal, it clones the state,
places the transformed cells on the board, updates the occupied-cell cache, removes
the spent piece, appends the move to history, advances round-robin turn order, resets
`consecutive_passes`, and marks the game finished when all players are blocked.

`validate_pass(state, player)` allows passing only when the requested player is the
current player and has no legal move. `pass_turn` clones the state, advances the turn,
increments consecutive passes, and finishes the game when all players are blocked or
the consecutive-pass count reaches the player count.

`compute_scores(state)` scores each player as negative remaining squares. Emptying a
rack adds 15 points, and ending with `I1` adds 5 more points.

`occupied_square_counts(state)` reports per-player occupied-square totals from the
derived occupied-cell cache. Cache accessors return defensive copies so callers cannot
mutate internal engine state through read helpers.

## Legal Move Generation

`list_legal_moves(state, player=None, limit=None)` enumerates legal placements for the
requested player, defaulting to the current player. It returns an empty list for
unknown players, finished games, blocked players, and `limit <= 0`.

Move generation is anchored rather than scanning every origin blindly:

- For a first move, the only anchor is the player's configured start corner.
- After a player has placed at least one piece, anchors are empty in-bounds diagonal
  neighbors of that player's occupied cells.
- Candidate anchors are filtered if they already have same-color orthogonal contact,
  because any later placement through that square would violate the edge-contact rule.
- Remaining pieces are searched larger first, then by piece id.
- Each unique transform is aligned so each transformed cell can satisfy the anchor.
- Candidate placements are de-duplicated by piece id plus absolute occupied cells.
- Final legality is still checked by the shared validator before a move is returned.

This keeps the generator tied to the same rules that validate user or AI moves, while
also avoiding duplicate placements from symmetric transforms.

## Computer Player

The default computer player is intentionally deterministic. `choose_move` dispatches
to the default strategy, and `choose_simple_move` selects from legal moves for the
requested player. It prefers larger pieces, then stable board position, piece id,
rotation, and flip ordering. If no legal move exists, it returns `None`.

This is a baseline gameplay helper, not a strong-play AI.

## Evidence Map

- Mode configuration: [`src/blokus/config.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/src/blokus/config.py)
- Rule validation, move generation, passing, scoring, and occupied-cell counts:
  [`src/blokus/engine.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/src/blokus/engine.py)
- Piece catalog and transforms: [`src/blokus/pieces.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/src/blokus/pieces.py)
- Computer-player strategy: [`src/blokus/players.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/src/blokus/players.py)
- Engine rule tests: [`tests/test_engine.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/tests/test_engine.py)
- Piece transform tests: [`tests/test_pieces.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/tests/test_pieces.py)
- Computer-player tests: [`tests/test_ai.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/tests/test_ai.py)
- Classic replay fixture:
  [`fixtures/scenarios/classic_corner_sequence.json`](https://github.com/anatol21/Blokus_GenAI/blob/main/fixtures/scenarios/classic_corner_sequence.json)
