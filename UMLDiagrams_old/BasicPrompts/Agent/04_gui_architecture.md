# Blokus GUI Architecture

```mermaid
classDiagram
    class BlokusGui {
        -root: tk.Tk
        -scale: float
        -window_width: int
        -window_height: int
        -board_size: int
        -board_x: int
        -board_y: int
        -icon_size: int
        -strategy_names: tuple
        -state: GameState
        +__init__(root)
        +compute_scale()
        +scale_value(value)
        +new_game()
        +show_legal_moves()
        +on_canvas_click()
        +on_drag_start()
        +on_drag_motion()
        +on_drag_end()
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
        +grid_origin_x: float
        +grid_origin_y: float
        +cell_size: float
        +build_board_metrics()
    }

    class SidebarPieceSlot {
        +bbox: tuple
        +normalized_shape: tuple[Coordinate]
        +cell_rects: dict[Coordinate, tuple]
        +load_sidebar_piece_slots()
    }

    class PieceRenderLayout {
        +bbox: tuple
        +cell_rects: dict[tuple[int, int], tuple]
    }

    BlokusGui --> DragState : manages
    BlokusGui --> BoardMetrics : uses
    BlokusGui --> SidebarPieceSlot : loads
    BlokusGui --> PieceRenderLayout : renders
    BlokusGui --> GameState : maintains
```

## Description
Tkinter GUI architecture with supporting classes:

### Main Class
- **BlokusGui**: Main GUI window class managing the Blokus game interface
  - Handles window scaling and layout calculations
  - Manages piece drag-and-drop interactions
  - Renders board, pieces, and player controls
  - Maintains current game state

### Supporting Classes
- **DragState**: Tracks the piece currently being dragged, including rotation and flip state
- **BoardMetrics**: Calculates coordinate mappings between canvas pixels and board cells
- **SidebarPieceSlot**: Represents layout and hit-test information for sidebar piece UI
- **PieceRenderLayout**: Canvas rectangles for rendering and hit-testing individual pieces

### Supporting Modules
- **gui_assets.py**: SVG rasterization and asset caching for performance
- **gui_support.py**: Pure helper functions for GUI calculations
