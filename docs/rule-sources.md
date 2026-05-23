# Rule Sources

## Assignment inputs used

- Course requirement excerpts provided in the task prompt, especially the Phase 1 baseline statements for Classic, legality checking, serialization, transforms, tests, reproducibility, and documentation.
- Official Mattel Blokus instructions for Classic: [Mattel instruction sheet](https://service.mattel.com/instruction_sheets/BJV44-Eng.pdf).

## Phase 1 implementation assumptions derived from those sources

1. Classic uses a 20x20 board and four players.
2. Starting corners are assigned one per player.
3. A first move must cover the assigned corner.
4. Later moves must touch same-color pieces only at corners, never along same-color edges.
5. The game ends when all players are blocked.
6. Scoring follows the standard remaining-squares rule with official perfect-game bonuses.

## Implementation boundary

- Duo is engine-supported through mode configuration; Classic remains the primary rule-source baseline.
- The CLI is intentionally minimal and text-based.
- The computer player is deterministic and simple by design; strong play strength is out of scope.
