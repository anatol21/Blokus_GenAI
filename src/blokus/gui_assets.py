"""GUI asset preparation using the provided SVG sources."""

from pathlib import Path
import shutil
import subprocess


def repo_root() -> Path:
    """Return the repository root so asset paths stay stable from any caller."""

    return Path(__file__).resolve().parents[2]


def cache_dir() -> Path:
    """Return the rasterized asset cache directory, creating it on demand."""

    path = repo_root() / ".cache" / "gui_assets"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _render_svg(svg_path: Path, png_path: Path, width: int, height: int) -> None:
    """Rasterize one SVG asset into a PNG sized for the active window layout."""

    converter = shutil.which("rsvg-convert")
    if converter is None:
        raise RuntimeError(
            "GUI asset preparation requires 'rsvg-convert' to be available in PATH."
        )
    subprocess.run(
        [
            converter,
            "-w",
            str(width),
            "-h",
            str(height),
            str(svg_path),
            "-o",
            str(png_path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )


def _ensure_render(svg_path: Path, png_path: Path, width: int, height: int) -> Path:
    """Render an SVG only when the cached PNG is missing or stale."""

    if not png_path.exists() or png_path.stat().st_mtime < svg_path.stat().st_mtime:
        png_path.parent.mkdir(parents=True, exist_ok=True)
        _render_svg(svg_path, png_path, width=width, height=height)
    return png_path


def prepare_gui_assets(
    window_width: int,
    window_height: int,
    board_size: int,
    icon_size: int,
    piece_icon_size: int,
    board_icon_size: int,
) -> dict[str, Path]:
    """Prepare every raster asset size needed by the Tkinter GUI."""

    graphics_dir = repo_root() / "Brokus Graphics"
    cache = cache_dir()
    assets = {
        "sidebars": _ensure_render(
            graphics_dir / "SideBars.svg",
            cache / f"sidebars_{window_width}x{window_height}.png",
            width=window_width,
            height=window_height,
        ),
        "board_classic": _ensure_render(
            graphics_dir / "GameBoardClassic.svg",
            cache / f"classic_board_{board_size}.png",
            width=board_size,
            height=board_size,
        ),
        "board_duo": _ensure_render(
            graphics_dir / "BlokusBoardDuo.svg",
            cache / f"duo_board_{board_size}.png",
            width = int(board_size * 0.7),
            height = int(board_size * 0.7),
        ),
        "robot_blue": _ensure_render(
            graphics_dir / "player_blue.svg",
            cache / f"player_blue_{icon_size}.png",
            width=icon_size,
            height=icon_size,
        ),
        "robot_yellow": _ensure_render(
            graphics_dir / "player_yellow.svg",
            cache / f"player_yellow_{icon_size}.png",
            width=icon_size,
            height=icon_size,
        ),
        "robot_red": _ensure_render(
            graphics_dir / "player_red.svg",
            cache / f"player_red_{icon_size}.png",
            width=icon_size,
            height=icon_size,
        ),
        "robot_green": _ensure_render(
            graphics_dir / "player_green.svg",
            cache / f"player_green_{icon_size}.png",
            width=icon_size,
            height=icon_size,
        ),
        "robot_blue_piece": _ensure_render(
            graphics_dir / "player_blue.svg",
            cache / f"player_blue_piece_{piece_icon_size}.png",
            width=piece_icon_size,
            height=piece_icon_size,
        ),
        "robot_yellow_piece": _ensure_render(
            graphics_dir / "player_yellow.svg",
            cache / f"player_yellow_piece_{piece_icon_size}.png",
            width=piece_icon_size,
            height=piece_icon_size,
        ),
        "robot_red_piece": _ensure_render(
            graphics_dir / "player_red.svg",
            cache / f"player_red_piece_{piece_icon_size}.png",
            width=piece_icon_size,
            height=piece_icon_size,
        ),
        "robot_green_piece": _ensure_render(
            graphics_dir / "player_green.svg",
            cache / f"player_green_piece_{piece_icon_size}.png",
            width=piece_icon_size,
            height=piece_icon_size,
        ),
        "robot_blue_board": _ensure_render(
            graphics_dir / "player_blue.svg",
            cache / f"player_blue_board_{board_icon_size}.png",
            width=board_icon_size,
            height=board_icon_size,
        ),
        "robot_yellow_board": _ensure_render(
            graphics_dir / "player_yellow.svg",
            cache / f"player_yellow_board_{board_icon_size}.png",
            width=board_icon_size,
            height=board_icon_size,
        ),
        "robot_red_board": _ensure_render(
            graphics_dir / "player_red.svg",
            cache / f"player_red_board_{board_icon_size}.png",
            width=board_icon_size,
            height=board_icon_size,
        ),
        "robot_green_board": _ensure_render(
            graphics_dir / "player_green.svg",
            cache / f"player_green_board_{board_icon_size}.png",
            width=board_icon_size,
            height=board_icon_size,
        ),
    }
    return assets
