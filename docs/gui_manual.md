# GUI Manual Guide

## Scope

The current GUI implements Classic mode only. Duo is visible in the mode switch but disabled by design in this phase.

## How to launch

From the repository root:

```bash
PYTHONPATH=src python -m blokus gui
```

or, after the bootstrap script:

```bash
./scripts/run_gui.sh
```

## Controls

- Drag a piece from the right-side piece panel onto the board.
- Press `R` while dragging to rotate clockwise.
- Press `F` while dragging to flip horizontally.
- Release the mouse on the board to attempt placement.
- Classic mode is highlighted in the mode switch and remains the active mode in this phase.
- Duo remains visible as a disabled control and does not activate gameplay when clicked.
- Illegal drops are rejected and leave the game state unchanged.
- `Legal Moves` opens a modal with up to five valid moves ordered by largest piece first.
- `Instructions` opens a modal with rules and controls guidance.
- `Restart` opens a confirmation dialog before resetting the current game.

## Manual acceptance checklist

1. Launch the GUI and confirm Classic is highlighted by default.
2. Confirm the Duo control is visible but disabled.
3. Confirm four robot icons and four score values are visible in the right sidebar.
4. Confirm the active player icon is highlighted.
5. Drag an unused piece from the current player’s panel.
6. Press `R` and `F` during drag and confirm the preview updates.
7. Drop a piece on an illegal location and confirm the board does not change.
8. Drop a piece on a legal location and confirm the board, turn highlight, score, and used-piece state all update.
9. Open `Legal Moves` and confirm no more than five suggestions are shown.
10. Select a suggestion and confirm it is applied through the engine.
11. Open `Instructions` and confirm it closes without changing the board state.
12. Click `Restart`, cancel, and confirm the board is unchanged.
13. Click `Restart` again, confirm, and verify a fresh Classic game starts.

## Design notes

- The board, sidebar, and robot visuals come from the supplied SVG assets in `Brokus Graphics/`.
- The GUI rasterizes those assets into `.cache/gui_assets/` for Tkinter display.
- The GUI does not re-implement rule enforcement; all legality and move application stay in `engine.py`.
