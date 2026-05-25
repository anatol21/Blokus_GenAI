# Score Panel Alignment Fix — Implementation Plan

## Problem Statement

Two visual defects in the right-panel score area:

1. **Yellow highlight circle is misplaced** — drawn at `BASE_PLAYER_ICON_POSITIONS` offsets which don't match where the SVG robots actually sit.
2. **Score numbers overlap robot icons** — the text offset (`icon_x + 34`) places numbers directly on top of the robot artwork.

## Root Cause Analysis

After the Option B fix removed code-drawn robot icons, the score panel relies entirely on the SVG-baked robots in `Ebene_2`. But `BASE_PLAYER_ICON_POSITIONS` was originally tuned for the *code-drawn* icons, not the SVG positions. The two coordinate systems are misaligned.

### Measured Positions (SVG → Window coords at scale=1.0)

| SVG Group | Player | SVG Center | Window Center | Current `BASE_PLAYER_ICON_POSITIONS` | Delta |
|---|---|---|---|---|---|
| `Generatives_Objekt8` | blue | (2870, 228) | **(1345, 108)** | (1250, 110) | **Δx=+95, Δy=−2** |
| `Generatives_Objekt7` | yellow | (3122, 237) | **(1463, 112)** | (1380, 110) | **Δx=+83, Δy=+2** |
| `Generatives_Objekt10` sub | green | (2871, 422) | **(1346, 201)** | (1250, 200) | **Δx=+96, Δy=+1** |
| `Generatives_Objekt9` | red | (3120, 430) | **(1463, 204)** | (1380, 200) | **Δx=+83, Δy=+4** |

> [!IMPORTANT]
> The code positions are ~85-96px too far left. The yellow circle and score text
> are both anchored to these wrong positions.

### Current `draw_status_panel()` Layout

```
[circle at icon_x,icon_y]  [score at icon_x+34, icon_y, anchor="w"]
```

The score text starts 34px right of `icon_x` with `anchor="w"` (left-aligned). Since the SVG robot is actually ~90px further right, the text renders directly on top of or behind the robot body.

## Proposed Fix

### Step 1 — Update `BASE_PLAYER_ICON_POSITIONS` to match SVG robots

```python
# Before (tuned for code-drawn icons)
BASE_PLAYER_ICON_POSITIONS = {
    "blue": (1250, 110),
    "yellow": (1380, 110),
    "green": (1250, 200),
    "red": (1380, 200),
}

# After (aligned to SVG-baked robot centers)
BASE_PLAYER_ICON_POSITIONS = {
    "blue": (1345, 108),
    "yellow": (1463, 112),
    "green": (1346, 201),
    "red": (1463, 204),
}
```

This single change fixes the yellow highlight circle position, because `draw_status_panel()` draws the oval at `icon_x ± 25, icon_y ± 25`.

### Step 2 — Move score text to the LEFT of the robot, not the right

The score text at `icon_x + 34` overlaps the robot because there's no room to the right (the panel edge is close). Move it to the left of the robot with `anchor="e"` (right-aligned, so text grows leftward away from the robot):

```python
# Before
text_x = icon_x + self.scale_value(34)
...
anchor="w",

# After
text_x = icon_x - self.scale_value(34)
...
anchor="e",
```

This places the score number to the left of the robot with consistent spacing, matching the visual layout shown in the screenshots where the numbers already appear to the left.

### Step 3 — Verify highlight ring radius

The oval currently uses `± self.scale_value(25)` which creates a 50px diameter ring at scale=1.0. The SVG robots are approximately 68×97 SVG units → ~32×46 window pixels. A 25px radius (50px diameter) should frame the robot head well. No change needed, but worth visual confirmation.

## Files Changed

| File | Change |
|---|---|
| `src/blokus/gui.py` L37-42 | Update `BASE_PLAYER_ICON_POSITIONS` coordinates |
| `src/blokus/gui.py` L358 | Change `+ 34` to `- 34` for score text x offset |
| `src/blokus/gui.py` L366 | Change `anchor="w"` to `anchor="e"` |

## Risk Assessment

| Risk | Severity | Mitigation |
|---|---|---|
| SVG robot centers are approximated from path M-commands, may be off by a few px | Low | Fine-tune after visual check |
| Score text with `anchor="e"` might overflow left panel boundary for large numbers | Very Low | Scores are always small integers; panel has ~100px of space |
| Scale factor causes rounding drift on different screens | Low | Already handled by `scale_value()` which rounds to int |

## Verification

1. Launch GUI → confirm yellow circle is centered on blue robot (first turn)
2. Play a move → confirm circle moves to yellow robot position
3. Confirm score numbers are to the left of each robot with no overlap
4. Confirm hover/drag interactions still work (no position-dependent regressions)
