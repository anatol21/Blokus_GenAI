# Blokus Module Architecture

```mermaid
graph TB
    A["__init__.py\nPublic API"]
    MAIN["__main__.py\nEntry Point"]
    
    Config["config.py\nMode & Symbol Config\n- ModeConfig\n- get_mode_config"]
    
    Models["models.py\nGame Data Models\n- Move\n- GameState\n- ValidationResult"]
    
    Pieces["pieces.py\nPiece Definitions\n- PieceDefinition\n- Transform\n- apply_transform"]
    
    Engine["engine.py\nGame Rules & Logic\n- new_game\n- validate_move\n- apply_move\n- list_legal_moves\n- pass_turn"]
    
    Players["players.py\nComputer Players\n- choose_move\n- choose_simple_move\n- available_strategies"]
    
    CLI["cli.py\nCommand Line Interface\n- cmd_new\n- cmd_show\n- cmd_apply"]
    
    Evaluate["evaluate.py\nTesting & Fixtures\n- run_scenario\n- ScenarioResult"]
    
    Render["render.py\nText Rendering\n- render_board\n- render_state"]
    
    GUI["gui.py\nTkinter GUI\n- BlokusGui\n- DragState"]
    
    GUISupport["gui_support.py\nGUI Helpers\n- BoardMetrics\n- SidebarPieceSlot"]
    
    GUIAssets["gui_assets.py\nGUI Asset Management\n- prepare_gui_assets"]
    
    A --> Models
    A --> Engine
    MAIN --> CLI
    
    Engine --> Models
    Engine --> Config
    Engine --> Pieces
    
    Players --> Models
    Players --> Pieces
    Players --> Engine
    
    CLI --> Engine
    CLI --> Models
    CLI --> Config
    CLI --> Players
    CLI --> Render
    CLI --> Evaluate
    
    Evaluate --> Engine
    Evaluate --> Models
    
    Render --> Config
    Render --> Engine
    Render --> Models
    
    GUI --> Engine
    GUI --> Models
    GUI --> Players
    GUI --> GUISupport
    GUI --> GUIAssets
    
    GUISupport --> Pieces
    GUISupport --> Config
    
    GUIAssets --> Config
```

## Description
Shows the dependency structure of all 12 Python modules in the Blokus engine:
- **config.py**: Foundation - game mode and symbol configuration
- **models.py**: Core data structures built on config
- **pieces.py**: Piece definitions and transformation logic
- **engine.py**: Main game logic using models, config, and pieces
- **players.py**: AI/Computer player strategies using engine
- **cli.py**: Command-line interface orchestrating all modules
- **render.py**: Text rendering for terminal output
- **gui.py**: Tkinter GUI implementation
- **gui_support.py**: Helper functions for GUI
- **gui_assets.py**: Asset management for GUI
- **evaluate.py**: Testing framework using engine
- **__init__.py**: Public API exports
- **__main__.py**: Entry point for python -m blokus
