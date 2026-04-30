# Blokus Game Engine Core Functions

```mermaid
graph TB
    GS["GameState"]
    
    New["new_game"]
    Validate["validate_move"]
    Apply["apply_move"]
    ListMoves["list_legal_moves"]
    Pass["pass_turn"]
    
    Helper1["board_in_bounds"]
    Helper2["get_occupied_cells"]
    Helper3["is_first_move"]
    Helper4["_has_edge_contact"]
    Helper5["_has_corner_contact"]
    
    Score["compute_scores"]
    Counts["occupied_square_counts"]
    
    MM["Move"]
    VR["ValidationResult"]
    PC["PieceDefinition"]
    
    New -->|creates| GS
    New -->|uses| PC
    
    Validate -->|checks| MM
    Validate -->|returns| VR
    Validate -->|reads| GS
    
    Apply -->|processes| MM
    Apply -->|modifies| GS
    
    ListMoves -->|generates| MM
    ListMoves -->|reads| GS
    ListMoves -->|uses| PC
    
    Pass -->|updates| GS
    
    Validate -->|uses| Helper1
    Validate -->|uses| Helper2
    Validate -->|uses| Helper3
    Validate -->|uses| Helper4
    Validate -->|uses| Helper5
    
    ListMoves -->|uses| Helper4
    ListMoves -->|uses| Helper5
    
    ListMoves -->|uses| Score
    
    Apply -->|calls| ListMoves
    Apply -->|calls| Pass
    
    Score -->|reads| GS
    Counts -->|reads| GS
```

## Description
Core game engine functions and their interactions:

### Primary Functions
- **new_game()**: Creates initial GameState with empty board and all pieces available
- **validate_move()**: Checks if a Move is legal according to Blokus rules
- **apply_move()**: Updates GameState with a legal move
- **list_legal_moves()**: Generates all possible legal moves for the current player
- **pass_turn()**: Advances to next player when no legal moves exist

### Helper Functions
- **board_in_bounds()**: Coordinate boundary checking
- **get_occupied_cells()**: Retrieves all occupied board positions
- **is_first_move()**: Checks if player's turn is their first move
- **_has_edge_contact_with_player()**: Validates orthogonal touch requirement
- **_has_corner_contact_with_player()**: Validates diagonal corner placement

### Utility Functions
- **compute_scores()**: Calculates player scores based on occupied squares
- **occupied_square_counts()**: Returns occupied square count per player
