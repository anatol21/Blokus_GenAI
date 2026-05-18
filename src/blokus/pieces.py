"""Piece definitions and transform helpers."""

from dataclasses import dataclass

Coordinate = tuple[int, int]


@dataclass(frozen=True)
class Transform:
    """One unique geometric orientation of a piece."""

    rotation: int
    flipped: bool
    cells: tuple[Coordinate, ...]


@dataclass(frozen=True)
class PieceDefinition:
    """Canonical piece definition plus all unique transforms."""

    piece_id: str
    cells: tuple[Coordinate, ...]
    transforms: tuple[Transform, ...]

    @property
    def size(self) -> int:
        """Return the number of occupied squares in the piece."""

        return len(self.cells)


BASE_PIECE_CELLS: dict[str, tuple[Coordinate, ...]] = {
    "I1": ((0, 0),),
    "I2": ((0, 0), (1, 0)),
    "I3": ((0, 0), (1, 0), (2, 0)),
    "V3": ((0, 0), (0, 1), (1, 1)),
    "I4": ((0, 0), (1, 0), (2, 0), (3, 0)),
    "O4": ((0, 0), (1, 0), (0, 1), (1, 1)),
    "T4": ((0, 0), (1, 0), (2, 0), (1, 1)),
    "L4": ((0, 0), (0, 1), (0, 2), (1, 2)),
    "Z4": ((0, 0), (1, 0), (1, 1), (2, 1)),
    "F5": ((1, 0), (2, 0), (0, 1), (1, 1), (1, 2)),
    "I5": ((0, 0), (1, 0), (2, 0), (3, 0), (4, 0)),
    "L5": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 3)),
    "N5": ((0, 0), (1, 0), (1, 1), (2, 1), (3, 1)),
    "P5": ((0, 0), (1, 0), (0, 1), (1, 1), (0, 2)),
    "T5": ((0, 0), (1, 0), (2, 0), (1, 1), (1, 2)),
    "U5": ((0, 0), (2, 0), (0, 1), (1, 1), (2, 1)),
    "V5": ((0, 0), (0, 1), (0, 2), (1, 2), (2, 2)),
    "W5": ((0, 0), (0, 1), (1, 1), (1, 2), (2, 2)),
    "X5": ((1, 0), (0, 1), (1, 1), (2, 1), (1, 2)),
    "Y5": ((0, 0), (0, 1), (0, 2), (0, 3), (1, 1)),
    "Z5": ((0, 0), (1, 0), (2, 0), (2, 1), (3, 1)),
}


def normalize_cells(cells: tuple[Coordinate, ...] | list[Coordinate]) -> tuple[Coordinate, ...]:
    """Shift a cell set so its top-left occupied square becomes the origin."""

    min_x = min(x for x, _ in cells)
    min_y = min(y for _, y in cells)
    normalized = sorted((x - min_x, y - min_y) for x, y in cells)
    return tuple(normalized)


def _rotate_clockwise(cells: tuple[Coordinate, ...]) -> tuple[Coordinate, ...]:
    """Rotate a cell set 90 degrees clockwise around the local origin."""

    return tuple((y, -x) for x, y in cells)


def _flip_horizontally(cells: tuple[Coordinate, ...]) -> tuple[Coordinate, ...]:
    """Mirror a cell set across the vertical axis through the origin."""

    return tuple((-x, y) for x, y in cells)


def apply_transform(
    cells: tuple[Coordinate, ...],
    rotation: int = 0,
    flipped: bool = False,
) -> tuple[Coordinate, ...]:
    """Apply the requested reflection and rotation, then normalize the result."""

    transformed = cells
    if flipped:
        transformed = _flip_horizontally(transformed)
    for _ in range(rotation % 4):
        transformed = _rotate_clockwise(transformed)
    return normalize_cells(transformed)


def _build_transforms(cells: tuple[Coordinate, ...]) -> tuple[Transform, ...]:
    """Enumerate each unique transform once, ignoring duplicate symmetries."""

    unique: dict[tuple[Coordinate, ...], Transform] = {}
    for flipped in (False, True):
        for rotation in range(4):
            transformed = apply_transform(cells, rotation=rotation, flipped=flipped)
            unique.setdefault(
                transformed,
                Transform(rotation=rotation, flipped=flipped, cells=transformed),
            )
    return tuple(sorted(unique.values(), key=lambda item: (item.cells, item.flipped, item.rotation)))


def _build_piece_catalog() -> dict[str, PieceDefinition]:
    """Build the full immutable piece catalog used by the engine and GUI."""

    catalog: dict[str, PieceDefinition] = {}
    for piece_id, cells in BASE_PIECE_CELLS.items():
        normalized = normalize_cells(cells)
        catalog[piece_id] = PieceDefinition(
            piece_id=piece_id,
            cells=normalized,
            transforms=_build_transforms(normalized),
        )
    return catalog


PIECES = _build_piece_catalog()


def piece_sort_key(piece_id: str) -> tuple[int, str]:
    """Sort larger pieces first, then break ties by piece id."""

    return (-PIECES[piece_id].size, piece_id)


PIECE_IDS = tuple(sorted(PIECES, key=piece_sort_key))


def absolute_cells(
    piece_or_move,
    origin: Coordinate | None = None,
    rotation: int = 0,
    flipped: bool = False,
) -> tuple[Coordinate, ...]:
    """Translate a transformed piece from local coordinates onto the board.

    Supports both:
    - absolute_cells(move)
    - absolute_cells(piece_id, origin, rotation, flipped)
    """

    # If the first argument is a Move object, extract fields
    if hasattr(piece_or_move, "piece"):
        move = piece_or_move
        piece_id = move.piece
        origin = (move.x, move.y)
        rotation = move.rotation
        flipped = move.flipped
    else:
        # Old-style call
        piece_id = piece_or_move
        if origin is None:
            raise ValueError("origin must be provided when not passing a Move")

    transformed = apply_transform(
        PIECES[piece_id].cells,
        rotation=rotation,
        flipped=flipped,
    )

    ox, oy = origin
    return tuple(sorted((ox + dx, oy + dy) for dx, dy in transformed))


def reference_cell(piece_id: str, rotation: int, flipped: bool) -> Coordinate:
    """Return the first occupied cell offset for the given piece transform.

    The CLI translation layer uses this to convert between bounding-box
    origin coordinates (used internally by the engine) and human-friendly
    coordinates that always point to an actual occupied cell of the piece.

    Cells are sorted by normalize_cells (lexicographic on (x, y)), so
    index 0 is the top-left-most occupied cell of the transformed piece.
    """

    transformed = apply_transform(PIECES[piece_id].cells, rotation=rotation, flipped=flipped)
    return transformed[0]


def start_corner_cell(
    piece_id: str,
    rotation: int,
    flipped: bool,
    corner: Coordinate,
    board_size: int,
) -> Coordinate | None:
    """Return the cell offset that lands on the given start corner.

    For first-move translation, finds which cell in the transformed piece
    would cover the mandatory start corner when the piece is placed at a
    valid board position.  Returns None if no valid placement exists for
    this transform at the corner.
    """

    transformed = apply_transform(PIECES[piece_id].cells, rotation=rotation, flipped=flipped)
    cx, cy = corner
    for dx, dy in transformed:
        origin_x = cx - dx
        origin_y = cy - dy
        if all(
            0 <= origin_x + cell_x < board_size and 0 <= origin_y + cell_y < board_size
            for cell_x, cell_y in transformed
        ):
            return (dx, dy)
    return None
