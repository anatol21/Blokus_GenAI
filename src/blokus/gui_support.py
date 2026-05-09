"""Pure helper functions shared by the GUI layer."""

from dataclasses import dataclass
import math
from pathlib import Path
import xml.etree.ElementTree as ET

from blokus.config import Coordinate
from blokus.pieces import PIECES

BOARD_VIEWBOX_SIZE = 2004
BOARD_GRID_ORIGIN = 202
BOARD_GRID_SIZE = 1600
BOARD_CELL_UNITS = 80
SIDEBAR_VIEWBOX_WIDTH = 3200
SIDEBAR_VIEWBOX_HEIGHT = 2000
SIDEBAR_PIECE_ORDER = (
    "U5",
    "I1",
    "V5",
    "I5",
    "V3",
    "L5",
    "L4",
    "P5",
    "T5",
    "Y5",
    "I4",
    "N5",
    "O4",
    "Z5",
    "X5",
    "I2",
    "T4",
    "W5",
    "F5",
    "Z4",
    "I3",
)


@dataclass(frozen=True)
class BoardMetrics:
    """Scaled geometry for mapping between canvas and board coordinates."""

    board_x: int
    board_y: int
    display_size: int

    @property
    def grid_origin_x(self) -> float:
        return self.board_x + (BOARD_GRID_ORIGIN / BOARD_VIEWBOX_SIZE) * self.display_size

    @property
    def grid_origin_y(self) -> float:
        return self.board_y + (BOARD_GRID_ORIGIN / BOARD_VIEWBOX_SIZE) * self.display_size

    @property
    def cell_size(self) -> float:
        return (BOARD_CELL_UNITS / BOARD_VIEWBOX_SIZE) * self.display_size


@dataclass(frozen=True)
class SidebarPieceSlot:
    """One embedded piece slot extracted from the provided sidebar artwork."""

    bbox: tuple[float, float, float, float]
    normalized_shape: tuple[Coordinate, ...]
    cell_rects: dict[Coordinate, tuple[float, float, float, float]]


def build_board_metrics(board_x: int, board_y: int, display_size: int) -> BoardMetrics:
    """Build the coordinate mapper for the rendered board asset."""

    return BoardMetrics(board_x=board_x, board_y=board_y, display_size=display_size)


def _cluster_levels(values: list[float], tolerance: float = 5.0) -> list[float]:
    """Group nearly identical SVG coordinates into stable grid rows or columns."""

    groups: list[list[float]] = []
    for value in sorted(values):
        if not groups or abs(value - groups[-1][-1]) > tolerance:
            groups.append([value])
            continue
        groups[-1].append(value)
    return [sum(group) / len(group) for group in groups]


def load_sidebar_piece_slots(
    svg_path: Path,
    window_width: int,
    window_height: int,
) -> dict[str, SidebarPieceSlot]:
    """Read the right-sidebar piece layout directly from `SideBars.svg`."""

    root = ET.parse(svg_path).getroot()
    layer = next((element for element in root.iter() if element.attrib.get("id") == "Ebene_5"), None)
    if layer is None:
        raise ValueError("Could not locate the piece layout layer in SideBars.svg.")

    raw_slots = [
        child
        for child in list(layer)
        if child.tag.endswith("g") or child.tag.endswith("rect")
    ]
    if len(raw_slots) != len(SIDEBAR_PIECE_ORDER):
        raise ValueError(
            f"Expected {len(SIDEBAR_PIECE_ORDER)} piece placeholders, found {len(raw_slots)}."
        )

    slots: dict[str, SidebarPieceSlot] = {}
    for piece_id, child in zip(SIDEBAR_PIECE_ORDER, raw_slots):
        rect_elements = [child] if child.tag.endswith("rect") else [
            element for element in list(child) if element.tag.endswith("rect")
        ]
        xs = [float(element.attrib["x"]) for element in rect_elements]
        ys = [float(element.attrib["y"]) for element in rect_elements]
        widths = [float(element.attrib["width"]) for element in rect_elements]
        heights = [float(element.attrib["height"]) for element in rect_elements]

        x_levels = _cluster_levels(xs)
        y_levels = _cluster_levels(ys)
        scaled_rects: dict[Coordinate, tuple[float, float, float, float]] = {}
        for element, x, y, width, height in zip(rect_elements, xs, ys, widths, heights):
            column = min(range(len(x_levels)), key=lambda index: abs(x_levels[index] - x))
            row = min(range(len(y_levels)), key=lambda index: abs(y_levels[index] - y))
            scaled_rects[(column, row)] = (
                (x / SIDEBAR_VIEWBOX_WIDTH) * window_width,
                (y / SIDEBAR_VIEWBOX_HEIGHT) * window_height,
                ((x + width) / SIDEBAR_VIEWBOX_WIDTH) * window_width,
                ((y + height) / SIDEBAR_VIEWBOX_HEIGHT) * window_height,
            )

        min_column = min(column for column, _ in scaled_rects)
        min_row = min(row for _, row in scaled_rects)
        normalized_rects = {
            (column - min_column, row - min_row): rect
            for (column, row), rect in scaled_rects.items()
        }
        bbox = (
            min(rect[0] for rect in normalized_rects.values()),
            min(rect[1] for rect in normalized_rects.values()),
            max(rect[2] for rect in normalized_rects.values()),
            max(rect[3] for rect in normalized_rects.values()),
        )
        normalized_shape = tuple(sorted(normalized_rects))
        slots[piece_id] = SidebarPieceSlot(
            bbox=bbox,
            normalized_shape=normalized_shape,
            cell_rects=normalized_rects,
        )
    return slots


def board_cell_from_point(
    x: float, y: float, metrics: BoardMetrics, board_size: int = 20,
) -> Coordinate | None:
    """Convert a canvas point into a board cell, or return `None` if outside."""

    local_x = x - metrics.grid_origin_x
    local_y = y - metrics.grid_origin_y
    if local_x < 0 or local_y < 0:
        return None
    column = int(math.floor(local_x / metrics.cell_size))
    row = int(math.floor(local_y / metrics.cell_size))
    if 0 <= column < board_size and 0 <= row < board_size:
        return (column, row)
    return None


def canvas_rect_for_cell(cell: Coordinate, metrics: BoardMetrics, inset: float = 1.5) -> tuple[float, float, float, float]:
    """Convert a board cell into the corresponding canvas rectangle."""

    column, row = cell
    x0 = metrics.grid_origin_x + column * metrics.cell_size + inset
    y0 = metrics.grid_origin_y + row * metrics.cell_size + inset
    x1 = x0 + metrics.cell_size - 2 * inset
    y1 = y0 + metrics.cell_size - 2 * inset
    return (x0, y0, x1, y1)


def transformed_cell_map(
    piece_id: str,
    rotation: int = 0,
    flipped: bool = False,
) -> dict[Coordinate, Coordinate]:
    """Map each base piece cell to its transformed local coordinate."""

    base_cells = PIECES[piece_id].cells
    transformed_cells = list(base_cells)
    mapped_cells = list(base_cells)

    if flipped:
        transformed_cells = [(-x, y) for x, y in transformed_cells]

    for _ in range(rotation % 4):
        transformed_cells = [(y, -x) for x, y in transformed_cells]

    min_x = min(x for x, _ in transformed_cells)
    min_y = min(y for _, y in transformed_cells)

    return {
        original: (transformed[0] - min_x, transformed[1] - min_y)
        for original, transformed in zip(mapped_cells, transformed_cells)
    }


def piece_panel_layout(
    piece_ids: list[str] | tuple[str, ...],
    panel_left: int,
    panel_top: int,
    panel_width: int,
    cell_size: int = 18,
    column_gap: int = 24,
    row_gap: int = 20,
    columns: int = 2,
) -> dict[str, tuple[int, int]]:
    """Lay out pieces in balanced columns for generic non-SVG piece panels."""

    column_width = (panel_width - column_gap * (columns - 1)) // columns
    y_offsets = [panel_top for _ in range(columns)]
    positions: dict[str, tuple[int, int]] = {}
    for piece_id in piece_ids:
        col = min(range(columns), key=lambda index: y_offsets[index])
        piece = PIECES[piece_id]
        width = (max(x for x, _ in piece.cells) + 1) * cell_size
        x = panel_left + col * (column_width + column_gap) + max((column_width - width) // 2, 0)
        y = y_offsets[col]
        positions[piece_id] = (x, y)
        height = (max(y_value for _, y_value in piece.cells) + 1) * cell_size
        y_offsets[col] += height + row_gap + 14
    return positions


def format_suggestion_label(
    piece_id: str,
    x: int,
    y: int,
    rotation: int,
    flipped: bool,
) -> str:
    """Format a legal-move suggestion for dialog display."""

    flip_suffix = "flip" if flipped else "plain"
    return f"{piece_id} at ({x}, {y}), rot={rotation}, {flip_suffix}"
