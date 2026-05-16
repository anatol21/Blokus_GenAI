# Blokus Piece Transformation System

```mermaid
graph LR
    Base["Base Piece Cells\nBASE_PIECE_CELLS"]
    
    Norm["normalize_cells\nShift to origin"]
    
    Rotate["apply_transform\nRotate & Flip"]
    
    RCW["_rotate_clockwise\n90° rotation"]
    FH["_flip_horizontally\nMirror across Y"]
    
    Build["_build_transforms\nEnumerate unique\ntransforms"]
    
    PD["PieceDefinition\n+ piece_id\n+ cells\n+ transforms"]
    
    Transform["Transform\n+ rotation\n+ flipped\n+ cells"]
    
    PICS["PIECES dict\nAll 21 pieces"]
    PIDS["PIECE_IDS tuple"]
    
    Base -->|normalize| Norm
    Norm -->|apply| Rotate
    Rotate -->|uses| RCW
    Rotate -->|uses| FH
    Rotate -->|build| Build
    Build -->|creates| Transform
    Transform -->|collected in| PD
    PD -->|stored in| PICS
    PICS -->|keys in| PIDS
```

## Description
The piece transformation pipeline that generates all geometric variations:

### Base Definitions
- **BASE_PIECE_CELLS**: Dictionary defining the 21 canonical Blokus pieces

### Transformation Functions
- **normalize_cells()**: Shifts cell coordinates so top-left occupied square becomes origin
- **_rotate_clockwise()**: Rotates 90 degrees clockwise around local origin
- **_flip_horizontally()**: Mirrors across vertical axis through origin
- **apply_transform()**: Applies flip and rotation transformations in sequence, then normalizes

### Build Pipeline
- **_build_transforms()**: Enumerates all 8 possible transforms (2 flip states × 4 rotations)
  - Filters out duplicate symmetries to store only unique orientations
  - Creates Transform objects for each unique orientation

### Output Structures
- **Transform**: Dataclass containing rotation, flip, and normalized cells
- **PieceDefinition**: Canonical piece with piece_id, base cells, and all unique transforms
- **PIECES**: Dictionary mapping piece_id to PieceDefinition
- **PIECE_IDS**: Tuple of all 21 piece identifiers for easy iteration

### Result
21 pieces × variable unique transforms (depending on symmetry) = complete piece library used by game engine
