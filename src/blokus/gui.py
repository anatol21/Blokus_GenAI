"""Classic-mode Tkinter GUI for Blokus."""

from dataclasses import dataclass
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from blokus.engine import apply_move, compute_scores, list_legal_moves, new_game, occupied_square_counts, pass_turn, validate_move
from blokus.gui_assets import prepare_gui_assets
from blokus.gui_support import (
    build_board_metrics,
    board_cell_from_point,
    canvas_rect_for_cell,
    format_suggestion_label,
    load_sidebar_piece_slots,
    SidebarPieceSlot,
    transformed_cell_map,
)
from blokus.models import Move
from blokus.pieces import PIECE_IDS
from blokus.players import available_strategies, choose_move

BASE_WINDOW_WIDTH = 1500
BASE_WINDOW_HEIGHT = 950
BASE_BOARD_SIZE = 820
BASE_BOARD_X = 338
BASE_BOARD_Y = 66
BASE_ICON_SIZE = 54
BASE_SIDEBAR_BOUNDS = {
    "duo": (48, 260, 115, 327),
    "classic": (132, 260, 199, 327),
    "settings": (25, 336, 214, 406),
    "restart": (25, 418, 214, 488),
    "legal_moves": (25, 548, 214, 618),
    "instructions": (25, 690, 214, 760),
}
BASE_PLAYER_ICON_POSITIONS = {
    "blue": (1250, 110),
    "yellow": (1380, 110),
    "green": (1250, 200),
    "red": (1380, 200),
}
PLAYER_ORDER = ("blue", "yellow", "red", "green")
ROBOT_ICON_KEY = {
    "blue": "robot_blue",
    "yellow": "robot_yellow",
    "red": "robot_red",
    "green": "robot_green",
}
SIDEBAR_BUTTON_STYLE = {
    "settings": {"fill": "#d8c1e8", "outline": "#5b6fcb", "text": "Settings"},
    "restart": {"fill": "#c3afe7", "outline": "#5b6fcb", "text": "Restart"},
    "legal_moves": {"fill": "#6b91d8", "outline": "#4b68bf", "text": "Legal Moves"},
    "instructions": {"fill": "#efc8ae", "outline": "#5b6fcb", "text": "Instructions"},
}
PANEL_GRADIENT_LEFT = "#c79aa6"
PANEL_GRADIENT_RIGHT = "#a896df"


@dataclass
class DragState:
    """The piece currently being dragged from the sidebar onto the board."""

    piece_id: str
    base_cell: tuple[int, int]
    rotation: int = 0
    flipped: bool = False


@dataclass
class PieceRenderLayout:
    """Canvas rectangles used to render and hit-test one sidebar piece."""

    bbox: tuple[float, float, float, float]
    cell_rects: dict[tuple[int, int], tuple[float, float, float, float]]


class BlokusGui:
    """Classic-only Tkinter GUI layered on top of the engine."""

    def __init__(self, root: tk.Tk | None = None) -> None:
        """Create the window, load assets, and prepare the initial game state."""

        self.root = root or tk.Tk()
        self.root.title("Blokus Classic GUI")
        self.scale = self.compute_scale()
        self.window_width = self.scale_value(BASE_WINDOW_WIDTH)
        self.window_height = self.scale_value(BASE_WINDOW_HEIGHT)
        self.board_size = self.scale_value(BASE_BOARD_SIZE)
        self.board_x = self.scale_value(BASE_BOARD_X)
        self.board_y = self.scale_value(BASE_BOARD_Y)
        self.icon_size = self.scale_value(BASE_ICON_SIZE)
        self.piece_cell_size = max(10, self.scale_value(14))
        self.floating_piece_cell_size = max(14, self.scale_value(20))
        self.piece_robot_size = max(14, self.scale_value(20))
        self.font_display = ("Avenir Next", max(13, self.scale_value(18)), "bold")
        self.font_body = ("Avenir Next", max(10, self.scale_value(12)))
        self.font_small = ("Avenir Next", max(9, self.scale_value(10)))
        self.status_width = self.scale_value(220)
        self.strategy_names = available_strategies()

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        offset_x = max((screen_width - self.window_width) // 2, 0)
        offset_y = max((screen_height - self.window_height) // 2 - 24, 0)
        self.root.geometry(f"{self.window_width}x{self.window_height}+{offset_x}+{offset_y}")
        self.root.resizable(False, False)

        # The GUI remains a thin presentation layer over the engine state.
        self.state = new_game(mode="classic", controllers={player: "human" for player in PLAYER_ORDER})
        self.board_metrics = build_board_metrics(self.board_x, self.board_y, self.board_size)
        self.board_robot_size = max(16, int(round(self.board_metrics.cell_size * 0.72)))
        self.assets = prepare_gui_assets(
            window_width=self.window_width,
            window_height=self.window_height,
            board_size=self.board_size,
            icon_size=self.icon_size,
            piece_icon_size=self.piece_robot_size,
            board_icon_size=self.board_robot_size,
        )
        self.images = {
            name: tk.PhotoImage(file=str(path))
            for name, path in self.assets.items()
        }

        self.canvas = tk.Canvas(
            self.root,
            width=self.window_width,
            height=self.window_height,
            bg="#14111d",
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True)

        self.status_text = "Drag a piece onto the board. Press R to rotate and F to flip while dragging."
        self.hovered_button: str | None = None
        self.active_panel: str | None = None
        self.hovered_piece: str | None = None
        self.drag_state: DragState | None = None
        self.pointer_x = 0
        self.pointer_y = 0
        self.piece_bounds: dict[str, tuple[float, float, float, float]] = {}
        self.piece_layouts: dict[str, PieceRenderLayout] = {}
        self.sidebar_bounds = {
            name: tuple(self.scale_value(value) for value in bounds)
            for name, bounds in BASE_SIDEBAR_BOUNDS.items()
        }
        self.player_icon_positions = {
            player: (self.scale_value(x), self.scale_value(y))
            for player, (x, y) in BASE_PLAYER_ICON_POSITIONS.items()
        }
        self.piece_slots = load_sidebar_piece_slots(
            Path(__file__).resolve().parents[2] / "Brokus Graphics" / "SideBars.svg",
            window_width=self.window_width,
            window_height=self.window_height,
        )

        # Bind mouse and keyboard input once; redraw() handles the visual updates.
        self.canvas.bind("<Motion>", self.on_motion)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
        self.root.bind("<KeyPress-r>", self.rotate_drag_clockwise)
        self.root.bind("<KeyPress-R>", self.rotate_drag_clockwise)
        self.root.bind("<KeyPress-f>", self.flip_drag_piece)
        self.root.bind("<KeyPress-F>", self.flip_drag_piece)

        self.redraw()

    def compute_scale(self) -> float:
        """Choose a uniform scale that fits the design inside the current screen."""

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        width_scale = (screen_width - 120) / BASE_WINDOW_WIDTH
        height_scale = (screen_height - 180) / BASE_WINDOW_HEIGHT
        return min(width_scale, height_scale, 1.0)

    def scale_value(self, value: int | float) -> int:
        """Scale one design-space value into the active window size."""

        return max(1, int(round(value * self.scale)))

    def run(self) -> None:
        """Start the Tkinter event loop."""

        self.root.mainloop()

    def redraw(self) -> None:
        """Redraw the full frame from the current engine and UI state."""

        self.canvas.delete("all")
        self.canvas.create_image(
            self.window_width // 2,
            self.window_height // 2,
            image=self.images["sidebars"],
        )
        self.canvas.create_image(
            self.board_x,
            self.board_y,
            image=self.images["board_classic"],
            anchor="nw",
        )
        self.draw_sidebar_overlays()
        self.draw_board_state()
        self.draw_status_panel()
        self.draw_piece_panel()
        self.draw_drag_preview()
        self.canvas.create_text(
            self.scale_value(140),
            self.scale_value(875),
            text=self.status_text,
            fill="#2a348e",
            width=self.status_width,
            justify="center",
            font=self.font_small,
        )

    def draw_sidebar_overlays(self) -> None:
        """Draw the clickable left-sidebar buttons over the provided artwork."""

        for button_name, bounds in self.sidebar_bounds.items():
            if button_name in {"classic", "duo"}:
                continue
            x0, y0, x1, y1 = bounds
            outline = ""
            width = 0
            if self.hovered_button == button_name:
                outline = "#ffe174"
                width = self.scale_value(4)
            if self.active_panel == button_name:
                outline = "#2a348e"
                width = self.scale_value(5)
            style = SIDEBAR_BUTTON_STYLE[button_name]
            outline = outline or style["outline"]
            width = width or self.scale_value(3)
            self.create_round_rect(
                x0,
                y0,
                x1,
                y1,
                radius=self.scale_value(28),
                fill=style["fill"],
                outline=outline,
                width=width,
            )
            self.canvas.create_text(
                (x0 + x1) / 2,
                (y0 + y1) / 2,
                text=style["text"],
                fill="#37448f",
                font=self.font_body,
            )

    def draw_board_state(self) -> None:
        """Render all placed pieces and the board summary line."""

        counts = occupied_square_counts(self.state)
        for row in range(20):
            for column in range(20):
                occupant = self.state.board[row][column]
                if occupant is None:
                    continue
                x0, y0, x1, y1 = canvas_rect_for_cell((column, row), self.board_metrics)
                # Board cells use larger robot icons so occupied squares stay readable.
                self.canvas.create_image(
                    (x0 + x1) / 2,
                    (y0 + y1) / 2,
                    image=self.images[f"robot_{occupant}_board"],
                )
        self.canvas.create_text(
            self.board_x + self.board_size // 2,
            self.board_y + self.board_size + self.scale_value(28),
            text=" | ".join(f"{player.title()}: {counts[player]} squares" for player in PLAYER_ORDER),
            fill="#2a348e",
            font=self.font_body,
        )
        if self.state.finished:
            scores = compute_scores(self.state)
            winner = max(scores, key=scores.get)
            self.canvas.create_text(
                self.board_x + self.board_size // 2,
                self.board_y - self.scale_value(18),
                text=f"Game over. Winner: {winner.title()}",
                fill="#ffffff",
                font=self.font_display,
            )

    def draw_status_panel(self) -> None:
        """Draw scores near the static player robots in the top-right panel."""

        scores = compute_scores(self.state)
        score_font = ("Avenir Next", max(18, self.scale_value(24)), "bold")
        for player, (icon_x, icon_y) in self.player_icon_positions.items():
            text_x = icon_x + self.scale_value(22)
            text_y = icon_y
            self.canvas.create_text(
                text_x,
                text_y,
                text=str(scores[player]),
                fill="#2a348e",
                font=score_font,
            )
            if player == self.state.current_player:
                self.canvas.create_line(
                    text_x - self.scale_value(28),
                    text_y + self.scale_value(18),
                    text_x + self.scale_value(28),
                    text_y + self.scale_value(18),
                    fill="#ecd04c",
                    width=self.scale_value(5),
                    capstyle=tk.ROUND,
                )

    def draw_piece_panel(self) -> None:
        """Render only the current player's remaining pieces inside sidebar slots."""

        current_player = self.state.current_player
        self.piece_bounds = {}
        self.piece_layouts = {}
        for piece_id in PIECE_IDS:
            used = piece_id not in self.state.remaining_pieces[current_player]
            layout = self.layout_piece_cells(piece_id)
            self.piece_layouts[piece_id] = layout
            self.piece_bounds[piece_id] = layout.bbox
            for x0, y0, x1, y1 in layout.cell_rects.values():
                # Sidebar pieces reuse the same player-colored robot asset at a smaller size.
                self.canvas.create_image(
                    (x0 + x1) / 2,
                    (y0 + y1) / 2,
                    image=self.images[f"robot_{current_player}_piece"],
                )
            if piece_id == self.hovered_piece and not used:
                x0, y0, x1, y1 = layout.bbox
                self.create_round_rect(
                    x0 - self.scale_value(5),
                    y0 - self.scale_value(5),
                    x1 + self.scale_value(5),
                    y1 + self.scale_value(5),
                    radius=self.scale_value(16),
                    outline="#ffe174",
                    width=self.scale_value(3),
                )
            if used:
                x0, y0, x1, y1 = layout.bbox
                self.canvas.create_line(x0, y0, x1, y1, fill="#7c6f95", width=self.scale_value(3))
                self.canvas.create_line(x0, y1, x1, y0, fill="#7c6f95", width=self.scale_value(3))

    def layout_piece_cells(self, piece_id: str) -> PieceRenderLayout:
        """Choose the best sidebar layout for a piece using the SVG slots first."""

        slot = self.piece_slots[piece_id]
        exact_layout = self.exact_piece_layout(piece_id, slot)
        if exact_layout is not None:
            return exact_layout
        return self.fitted_piece_layout(piece_id, slot.bbox)

    def exact_piece_layout(self, piece_id: str, slot: SidebarPieceSlot) -> PieceRenderLayout | None:
        """Reuse the exact slot geometry when the SVG shape matches a real transform."""

        for flipped in (False, True):
            for rotation in range(4):
                cell_map = transformed_cell_map(piece_id, rotation=rotation, flipped=flipped)
                normalized_shape = tuple(sorted(cell_map.values()))
                if normalized_shape != slot.normalized_shape:
                    continue
                # Reverse the transform so click-hit testing still returns base piece cells.
                by_display_cell = {display_cell: base_cell for base_cell, display_cell in cell_map.items()}
                cell_rects = {
                    by_display_cell[display_cell]: rect
                    for display_cell, rect in slot.cell_rects.items()
                }
                return PieceRenderLayout(
                    bbox=slot.bbox,
                    cell_rects=cell_rects,
                )
        return None

    def fitted_piece_layout(self, piece_id: str, bbox: tuple[float, float, float, float]) -> PieceRenderLayout:
        """Fallback layout when a sidebar placeholder is decorative rather than exact."""

        x0, y0, x1, y1 = bbox
        padding = self.scale_value(6)
        available_width = max((x1 - x0) - padding * 2, self.scale_value(18))
        available_height = max((y1 - y0) - padding * 2, self.scale_value(18))
        best_map = self.best_piece_transform(piece_id, available_width, available_height)
        width_units = max(column for column, _ in best_map.values()) + 1
        height_units = max(row for _, row in best_map.values()) + 1
        cell_size = min(available_width / width_units, available_height / height_units)
        origin_x = x0 + ((x1 - x0) - width_units * cell_size) / 2
        origin_y = y0 + ((y1 - y0) - height_units * cell_size) / 2
        cell_rects = {
            base_cell: (
                origin_x + column * cell_size,
                origin_y + row * cell_size,
                origin_x + (column + 1) * cell_size,
                origin_y + (row + 1) * cell_size,
            )
            for base_cell, (column, row) in best_map.items()
        }
        return PieceRenderLayout(
            bbox=bbox,
            cell_rects=cell_rects,
        )

    def best_piece_transform(
        self,
        piece_id: str,
        available_width: float,
        available_height: float,
    ) -> dict[tuple[int, int], tuple[int, int]]:
        """Pick the transform that maximizes readable size inside a slot box."""

        best_map: dict[tuple[int, int], tuple[int, int]] | None = None
        best_cell_size = -1.0
        best_aspect_delta = float("inf")
        target_ratio = available_width / max(available_height, 1.0)
        for flipped in (False, True):
            for rotation in range(4):
                cell_map = transformed_cell_map(piece_id, rotation=rotation, flipped=flipped)
                width_units = max(column for column, _ in cell_map.values()) + 1
                height_units = max(row for _, row in cell_map.values()) + 1
                cell_size = min(available_width / width_units, available_height / height_units)
                aspect_delta = abs((width_units / max(height_units, 1)) - target_ratio)
                if cell_size > best_cell_size or (
                    abs(cell_size - best_cell_size) < 0.01 and aspect_delta < best_aspect_delta
                ):
                    best_map = cell_map
                    best_cell_size = cell_size
                    best_aspect_delta = aspect_delta
        assert best_map is not None
        return best_map

    def draw_drag_preview(self) -> None:
        """Draw the live placement preview for the currently dragged piece."""

        if self.drag_state is None:
            return
        board_cell = board_cell_from_point(self.pointer_x, self.pointer_y, self.board_metrics)
        if board_cell is None:
            self.draw_floating_piece_preview()
            return

        transformed_map = transformed_cell_map(
            self.drag_state.piece_id,
            rotation=self.drag_state.rotation,
            flipped=self.drag_state.flipped,
        )
        anchor = transformed_map[self.drag_state.base_cell]
        origin = (board_cell[0] - anchor[0], board_cell[1] - anchor[1])
        move = Move(
            player=self.state.current_player,
            piece=self.drag_state.piece_id,
            x=origin[0],
            y=origin[1],
            rotation=self.drag_state.rotation,
            flipped=self.drag_state.flipped,
        )
        validation = validate_move(self.state, move)
        outline = "#6adf8c" if validation.ok else "#ff6f7a"
        for cell in transformed_map.values():
            rect = canvas_rect_for_cell(
                (origin[0] + cell[0], origin[1] + cell[1]),
                self.board_metrics,
                inset=max(1.2, 2.4 * self.scale),
            )
            # Show both an outline and the robot fill so legality is obvious while dragging.
            self.create_round_rect(
                *rect,
                radius=self.scale_value(6),
                outline=outline,
                width=self.scale_value(2),
            )
            self.canvas.create_image(
                (rect[0] + rect[2]) / 2,
                (rect[1] + rect[3]) / 2,
                image=self.images[f"robot_{self.state.current_player}_board"],
            )
        ax0, ay0, ax1, ay1 = canvas_rect_for_cell(
            (origin[0] + anchor[0], origin[1] + anchor[1]),
            self.board_metrics,
            inset=max(2.5, 7.0 * self.scale),
        )
        self.canvas.create_oval(ax0, ay0, ax1, ay1, outline=outline, width=self.scale_value(3))

    def draw_floating_piece_preview(self) -> None:
        """Draw the dragged piece near the cursor when it is off the board."""

        assert self.drag_state is not None
        transformed_map = transformed_cell_map(
            self.drag_state.piece_id,
            rotation=self.drag_state.rotation,
            flipped=self.drag_state.flipped,
        )
        cells = transformed_map.values()
        min_x = min(x for x, _ in cells)
        min_y = min(y for _, y in cells)
        for column, row in cells:
            x0 = self.pointer_x + (column - min_x) * self.floating_piece_cell_size
            y0 = self.pointer_y + (row - min_y) * self.floating_piece_cell_size
            self.canvas.create_image(
                x0 + self.floating_piece_cell_size / 2,
                y0 + self.floating_piece_cell_size / 2,
                image=self.images[f"robot_{self.state.current_player}_piece"],
            )
            self.create_round_rect(
                x0,
                y0,
                x0 + self.floating_piece_cell_size,
                y0 + self.floating_piece_cell_size,
                radius=self.scale_value(5),
                outline="#2a348e",
                width=self.scale_value(2),
            )

    def on_motion(self, event: tk.Event) -> None:
        """Track hover state and cursor position for redraw-driven feedback."""

        self.pointer_x = event.x
        self.pointer_y = event.y
        self.hovered_button = self.button_at(event.x, event.y)
        self.hovered_piece = self.available_piece_at(event.x, event.y) if self.drag_state is None else None
        self.redraw()

    def on_button_press(self, event: tk.Event) -> None:
        """Start dragging a piece or activate a sidebar control."""

        self.root.focus_set()
        piece_id = self.available_piece_at(event.x, event.y)
        if piece_id is not None:
            base_cell = self.base_cell_at_piece_point(piece_id, event.x, event.y)
            self.drag_state = DragState(piece_id=piece_id, base_cell=base_cell)
            self.status_text = (
                f"Dragging {piece_id}. Press R to rotate, F to flip, and release on a legal board square."
            )
            self.redraw()
            return

        button = self.button_at(event.x, event.y)
        # Buttons only open dialogs or reset state; game rules stay in the engine.
        if button == "classic":
            self.active_panel = "classic"
            self.status_text = "Classic mode is active."
        elif button == "duo":
            self.status_text = "Duo mode is disabled in this phase."
        elif button == "settings":
            self.active_panel = "settings"
            self.show_settings_dialog()
        elif button == "restart":
            self.active_panel = "restart"
            self.handle_restart()
        elif button == "legal_moves":
            self.active_panel = "legal_moves"
            self.show_legal_move_dialog()
        elif button == "instructions":
            self.active_panel = "instructions"
            self.show_instructions_dialog()
        self.redraw()

    def on_button_release(self, event: tk.Event) -> None:
        """Finish a drag by validating and applying the candidate placement."""

        if self.drag_state is None:
            return
        board_cell = board_cell_from_point(event.x, event.y, self.board_metrics)
        if board_cell is None:
            self.status_text = "Placement cancelled."
            self.drag_state = None
            self.redraw()
            return

        transformed_map = transformed_cell_map(
            self.drag_state.piece_id,
            rotation=self.drag_state.rotation,
            flipped=self.drag_state.flipped,
        )
        anchor = transformed_map[self.drag_state.base_cell]
        origin = (board_cell[0] - anchor[0], board_cell[1] - anchor[1])
        move = Move(
            player=self.state.current_player,
            piece=self.drag_state.piece_id,
            x=origin[0],
            y=origin[1],
            rotation=self.drag_state.rotation,
            flipped=self.drag_state.flipped,
        )
        validation = validate_move(self.state, move)
        if validation.ok:
            # Only a validated move mutates the engine state.
            self.state = apply_move(self.state, move)
            self.drag_state = None
            self.status_text = f"{move.player.title()} placed {move.piece}."
            self.advance_automatic_turns()
        else:
            self.status_text = f"Illegal placement rejected: {validation.reason}"
            self.drag_state = None
        self.redraw()

    def rotate_drag_clockwise(self, _: tk.Event) -> None:
        """Rotate the dragged piece one quarter-turn clockwise."""

        if self.drag_state is None:
            return
        self.drag_state.rotation = (self.drag_state.rotation + 1) % 4
        self.redraw()

    def flip_drag_piece(self, _: tk.Event) -> None:
        """Flip the dragged piece horizontally."""

        if self.drag_state is None:
            return
        self.drag_state.flipped = not self.drag_state.flipped
        self.redraw()

    def advance_automatic_turns(self) -> None:
        """Resolve forced passes and computer turns until a human turn is reached."""

        messages: list[str] = []
        while not self.state.finished:
            if not list_legal_moves(self.state, limit=1):
                blocked_player = self.state.current_player
                self.state = pass_turn(self.state)
                messages.append(f"{blocked_player.title()} had no legal move and passed automatically.")
                continue
            current_player = self.state.current_player
            if self.state.controller_types.get(current_player, "human") != "computer":
                break
            strategy = self.state.controller_strategies.get(current_player, self.strategy_names[0])
            move = choose_move(self.state, player=current_player, strategy=strategy)
            if move is None:
                self.state = pass_turn(self.state)
                messages.append(f"{current_player.title()} had no legal move and passed automatically.")
                continue
            self.state = apply_move(self.state, move)
            messages.append(f"{current_player.title()} ({strategy}) placed {move.piece}.")
        if messages:
            self.status_text = " ".join(messages)

    def show_legal_move_dialog(self) -> None:
        """Open the top-five legal-moves dialog sourced from the engine."""

        suggestions = list_legal_moves(self.state, limit=5)
        dialog = tk.Toplevel(self.root)
        dialog.title("Legal Moves")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#f2d3cf")
        dialog.resizable(False, False)
        tk.Label(
            dialog,
            text="Top legal moves",
            bg="#f2d3cf",
            fg="#2a348e",
            font=self.font_display,
        ).pack(
            padx=self.scale_value(24),
            pady=(self.scale_value(20), self.scale_value(12)),
        )
        if not suggestions:
            tk.Label(
                dialog,
                text="No legal moves are available for the current player.",
                bg="#f2d3cf",
                fg="#2a348e",
                font=self.font_body,
                wraplength=self.scale_value(360),
            ).pack(padx=self.scale_value(24), pady=self.scale_value(12))
        for move in suggestions:
            # Each row can be clicked to apply the engine-generated move directly.
            label = format_suggestion_label(
                move.piece,
                move.x,
                move.y,
                move.rotation,
                move.flipped,
            )
            row = tk.Label(
                dialog,
                text=label,
                font=self.font_body,
                bg="#6b91d8",
                fg="#ffffff",
                padx=self.scale_value(14),
                pady=self.scale_value(10),
                anchor="w",
                cursor="hand2",
            )
            row.pack(fill="x", padx=self.scale_value(24), pady=self.scale_value(6))
            row.bind(
                "<Button-1>",
                lambda _event, candidate=move, window=dialog: self.apply_suggested_move(candidate, window),
            )
            row.bind("<Enter>", lambda _event, widget=row: widget.configure(bg="#5578c2"))
            row.bind("<Leave>", lambda _event, widget=row: widget.configure(bg="#6b91d8"))
        close_label = tk.Label(
            dialog,
            text="Close",
            font=self.font_body,
            bg="#c3afe7",
            fg="#2a348e",
            padx=self.scale_value(18),
            pady=self.scale_value(10),
            cursor="hand2",
        )
        close_label.pack(pady=(self.scale_value(18), self.scale_value(20)))
        close_label.bind("<Button-1>", lambda _event, window=dialog: self.close_panel(window))
        close_label.bind("<Enter>", lambda _event, widget=close_label: widget.configure(bg="#d1c0ef"))
        close_label.bind("<Leave>", lambda _event, widget=close_label: widget.configure(bg="#c3afe7"))
        dialog.protocol("WM_DELETE_WINDOW", lambda window=dialog: self.close_panel(window))

    def apply_suggested_move(self, move: Move, dialog: tk.Toplevel) -> None:
        """Apply a move chosen from the legal-move dialog."""

        self.state = apply_move(self.state, move)
        self.status_text = f"Applied suggested move {move.piece} for {move.player.title()}."
        self.close_panel(dialog)
        self.advance_automatic_turns()
        self.redraw()

    def show_settings_dialog(self) -> None:
        """Open a modal dialog for controller and strategy selection."""

        dialog = tk.Toplevel(self.root)
        dialog.title("Settings")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#f2d3cf")
        dialog.resizable(False, False)

        controller_vars: dict[str, tk.StringVar] = {}
        strategy_vars: dict[str, tk.StringVar] = {}
        strategy_menus: dict[str, tk.OptionMenu] = {}

        tk.Label(
            dialog,
            text="Player Settings",
            bg="#f2d3cf",
            fg="#2a348e",
            font=self.font_display,
        ).grid(row=0, column=0, columnspan=3, padx=self.scale_value(24), pady=(self.scale_value(20), self.scale_value(14)))
        tk.Label(dialog, text="Player", bg="#f2d3cf", fg="#2a348e", font=self.font_body).grid(row=1, column=0, sticky="w", padx=self.scale_value(24))
        tk.Label(dialog, text="Controller", bg="#f2d3cf", fg="#2a348e", font=self.font_body).grid(row=1, column=1, sticky="w", padx=self.scale_value(10))
        tk.Label(dialog, text="Strategy", bg="#f2d3cf", fg="#2a348e", font=self.font_body).grid(row=1, column=2, sticky="w", padx=self.scale_value(10))

        def sync_strategy_state(player: str) -> None:
            state = tk.NORMAL if controller_vars[player].get() == "computer" else tk.DISABLED
            strategy_menus[player].configure(state=state)

        for row_index, player in enumerate(PLAYER_ORDER, start=2):
            controller_vars[player] = tk.StringVar(value=self.state.controller_types.get(player, "human"))
            strategy_vars[player] = tk.StringVar(
                value=self.state.controller_strategies.get(player, self.strategy_names[0])
            )
            tk.Label(
                dialog,
                text=player.title(),
                bg="#f2d3cf",
                fg="#2a348e",
                font=self.font_body,
            ).grid(row=row_index, column=0, sticky="w", padx=self.scale_value(24), pady=self.scale_value(8))
            controller_menu = tk.OptionMenu(dialog, controller_vars[player], "human", "computer")
            controller_menu.configure(font=self.font_body, width=9, highlightthickness=0)
            controller_menu.grid(row=row_index, column=1, padx=self.scale_value(10), pady=self.scale_value(8), sticky="ew")
            strategy_menu = tk.OptionMenu(dialog, strategy_vars[player], *self.strategy_names)
            strategy_menu.configure(font=self.font_body, width=10, highlightthickness=0)
            strategy_menu.grid(row=row_index, column=2, padx=self.scale_value(10), pady=self.scale_value(8), sticky="ew")
            strategy_menus[player] = strategy_menu
            controller_vars[player].trace_add(
                "write",
                lambda *_args, tracked_player=player: sync_strategy_state(tracked_player),
            )
            sync_strategy_state(player)

        def apply_settings() -> None:
            self.state.controller_types = {
                player: controller_vars[player].get() for player in PLAYER_ORDER
            }
            self.state.controller_strategies = {
                player: strategy_vars[player].get() if controller_vars[player].get() == "computer" else self.strategy_names[0]
                for player in PLAYER_ORDER
            }
            self.status_text = "Player settings updated."
            self.close_panel(dialog)
            self.advance_automatic_turns()
            self.redraw()

        button_frame = tk.Frame(dialog, bg="#f2d3cf")
        button_frame.grid(row=len(PLAYER_ORDER) + 2, column=0, columnspan=3, pady=(self.scale_value(18), self.scale_value(20)))
        tk.Button(button_frame, text="Apply", font=self.font_body, command=apply_settings).pack(side="left", padx=self.scale_value(6))
        tk.Button(button_frame, text="Cancel", font=self.font_body, command=lambda window=dialog: self.close_panel(window)).pack(side="left", padx=self.scale_value(6))
        dialog.protocol("WM_DELETE_WINDOW", lambda window=dialog: self.close_panel(window))

    def show_instructions_dialog(self) -> None:
        """Open the modal instructions dialog for Classic mode."""

        dialog = tk.Toplevel(self.root)
        dialog.title("Instructions")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.configure(bg="#f2d3cf")
        copy = (
            "Classic Blokus rules:\n"
            "- The first move for each player must cover that player's corner.\n"
            "- Later moves must touch your own color only at corners.\n"
            "- Pieces of the same color may not share an edge.\n"
            "- Scores use official remaining-square scoring.\n\n"
            "GUI controls:\n"
            "- Drag a piece from the right panel onto the board.\n"
            "- Press R while dragging to rotate.\n"
            "- Press F while dragging to flip.\n"
            "- Used pieces stay visible and crossed out.\n"
            "- Legal Moves shows up to five valid suggestions from the engine.\n"
            "- Restart asks for confirmation before resetting the game."
        )
        tk.Label(
            dialog,
            text="Instructions",
            bg="#f2d3cf",
            fg="#2a348e",
            font=self.font_display,
        ).pack(
            padx=self.scale_value(24),
            pady=(self.scale_value(20), self.scale_value(12)),
        )
        tk.Label(
            dialog,
            text=copy,
            bg="#f2d3cf",
            fg="#2a348e",
            font=self.font_body,
            justify="left",
            wraplength=self.scale_value(460),
        ).pack(padx=self.scale_value(24), pady=self.scale_value(12))
        tk.Button(
            dialog,
            text="Close",
            font=self.font_body,
            command=lambda window=dialog: self.close_panel(window),
        ).pack(pady=(self.scale_value(8), self.scale_value(20)))
        dialog.protocol("WM_DELETE_WINDOW", lambda window=dialog: self.close_panel(window))

    def close_panel(self, dialog: tk.Toplevel) -> None:
        """Close a modal dialog and clear the active sidebar selection."""

        self.active_panel = None
        dialog.destroy()
        self.redraw()

    def handle_restart(self) -> None:
        """Confirm and reset the current Classic game session."""

        confirmed = messagebox.askokcancel(
            title="Restart Classic Game",
            message="Restart the current Classic game? This will discard the current board state.",
            parent=self.root,
        )
        self.active_panel = None
        if not confirmed:
            self.status_text = "Restart cancelled."
            return
        self.state = new_game(
            mode="classic",
            controllers=dict(self.state.controller_types),
            strategies=dict(self.state.controller_strategies),
        )
        self.drag_state = None
        self.status_text = "Started a fresh Classic game."
        self.advance_automatic_turns()

    def button_at(self, x: int, y: int) -> str | None:
        """Return the sidebar button under the cursor, if any."""

        for name, (x0, y0, x1, y1) in self.sidebar_bounds.items():
            if name in {"classic", "duo"}:
                continue
            if x0 <= x <= x1 and y0 <= y <= y1:
                return name
        return None

    def available_piece_at(self, x: int, y: int) -> str | None:
        """Return the draggable piece under the cursor, if it is still unused."""

        current_player = self.state.current_player
        if self.state.controller_types.get(current_player, "human") != "human":
            return None
        for piece_id, bounds in self.piece_bounds.items():
            x0, y0, x1, y1 = bounds
            if piece_id not in self.state.remaining_pieces[current_player]:
                continue
            if x0 <= x <= x1 and y0 <= y <= y1:
                return piece_id
        return None

    def base_cell_at_piece_point(self, piece_id: str, x: int, y: int) -> tuple[int, int]:
        """Map a sidebar click back to the originating local cell of a piece."""

        layout = self.piece_layouts[piece_id]
        for cell, (x0, y0, x1, y1) in layout.cell_rects.items():
            if x0 <= x <= x1 and y0 <= y <= y1:
                return cell
        return min(layout.cell_rects, key=lambda cell: (layout.cell_rects[cell][1], layout.cell_rects[cell][0]))

    def draw_gradient_rect(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        left_color: str,
        right_color: str,
        steps: int = 80,
    ) -> None:
        """Paint a simple horizontal gradient directly on the canvas."""

        def hex_to_rgb(value: str) -> tuple[int, int, int]:
            value = value.lstrip("#")
            return tuple(int(value[index:index + 2], 16) for index in (0, 2, 4))

        def rgb_to_hex(rgb: tuple[int, int, int]) -> str:
            return "#" + "".join(f"{part:02x}" for part in rgb)

        start = hex_to_rgb(left_color)
        end = hex_to_rgb(right_color)
        width = x1 - x0
        for step in range(steps):
            ratio = step / max(steps - 1, 1)
            color = rgb_to_hex(
                tuple(
                    int(start[channel] + (end[channel] - start[channel]) * ratio)
                    for channel in range(3)
                )
            )
            segment_x0 = x0 + width * (step / steps)
            segment_x1 = x0 + width * ((step + 1) / steps)
            self.canvas.create_rectangle(
                segment_x0,
                y0,
                segment_x1 + 1,
                y1,
                outline="",
                fill=color,
            )

    def create_round_rect(
        self,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
        radius: float,
        **kwargs: object,
    ) -> int:
        """Approximate a rounded rectangle using a smoothed polygon."""

        points = [
            x0 + radius,
            y0,
            x1 - radius,
            y0,
            x1,
            y0,
            x1,
            y0 + radius,
            x1,
            y1 - radius,
            x1,
            y1,
            x1 - radius,
            y1,
            x0 + radius,
            y1,
            x0,
            y1,
            x0,
            y1 - radius,
            x0,
            y0 + radius,
            x0,
            y0,
        ]
        return self.canvas.create_polygon(points, smooth=True, splinesteps=24, **kwargs)


def launch_gui() -> None:
    """Convenience launcher used by the CLI `gui` subcommand."""

    BlokusGui().run()
