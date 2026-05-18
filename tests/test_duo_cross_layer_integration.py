import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from blokus.engine import list_legal_moves
from blokus.evaluate import run_scenario
from blokus.gui import BlokusGui
from blokus.models import GameState


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "blokus", *args],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )


def load_json(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class FakeRoot:
    def __init__(self) -> None:
        self.titles: list[str] = []

    def title(self, value: str) -> None:
        self.titles.append(value)


class FakeCanvas:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.images: list[dict[str, object]] = []
        self.texts: list[dict[str, object]] = []

    def delete(self, tag: str) -> None:
        self.deleted.append(tag)

    def create_image(self, *args: object, **kwargs: object) -> int:
        self.images.append({"args": args, "kwargs": kwargs})
        return len(self.images)

    def create_text(self, *args: object, **kwargs: object) -> int:
        self.texts.append({"args": args, "kwargs": kwargs})
        return len(self.texts)


class DuoCrossLayerIntegrationTests(unittest.TestCase):
    def test_cli_duo_new_apply_show_and_invalid_apply_lifecycle(self) -> None:
        """CLI commands interoperate across Duo new/apply/show/failed apply."""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            initial_path = temp_path / "initial.json"
            after_path = temp_path / "after.json"
            invalid_path = temp_path / "invalid.json"

            created = run_cli("new", "--mode", "duo", "--output", str(initial_path))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)

            initial_payload = load_json(initial_path)
            self.assertEqual(initial_payload["mode"], "duo")
            self.assertEqual(initial_payload["current_player"], "blue")

            initial_text = initial_path.read_text(encoding="utf-8")
            applied = run_cli(
                "apply",
                "--state",
                str(initial_path),
                "--piece",
                "I1",
                "--x",
                "4",
                "--y",
                "4",
                "--output",
                str(after_path),
            )
            self.assertEqual(applied.returncode, 0, applied.stdout + applied.stderr)
            self.assertEqual(initial_path.read_text(encoding="utf-8"), initial_text)

            after_payload = load_json(after_path)
            self.assertEqual(after_payload["board"][4][4], "B")
            self.assertEqual(after_payload["current_player"], "red")
            self.assertEqual(
                after_payload["history"],
                [
                    {
                        "player": "blue",
                        "piece": "I1",
                        "x": 4,
                        "y": 4,
                        "rotation": 0,
                        "flipped": False,
                    }
                ],
            )
            self.assertNotIn("I1", after_payload["remaining_pieces"]["blue"])

            shown = run_cli("show", "--state", str(after_path))
            self.assertEqual(shown.returncode, 0, shown.stdout + shown.stderr)
            self.assertIn("Mode: duo", shown.stdout)
            self.assertIn("Current player: red", shown.stdout)
            self.assertIn("Moves played: 1", shown.stdout)
            self.assertIn("Occupied squares: blue=1, red=0", shown.stdout)
            self.assertIn(
                "   00 01 02 03 04 05 06 07 08 09 10 11 12 13",
                shown.stdout,
            )
            self.assertIn("04 . . . . B . . . . . . . . .", shown.stdout)

            after_text = after_path.read_text(encoding="utf-8")
            rejected = run_cli(
                "apply",
                "--state",
                str(after_path),
                "--player",
                "red",
                "--piece",
                "I1",
                "--x",
                "8",
                "--y",
                "8",
                "--output",
                str(invalid_path),
            )
            self.assertEqual(rejected.returncode, 1)
            self.assertIn(
                "Opening move for red must cover start corner (9, 9).",
                rejected.stdout,
            )
            self.assertEqual(after_path.read_text(encoding="utf-8"), after_text)
            self.assertFalse(invalid_path.exists())

    def test_cli_duo_legal_moves_json_matches_engine_limited_listing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            created = run_cli("new", "--mode", "duo", "--output", str(state_path))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)

            listed = run_cli(
                "legal-moves",
                "--state",
                str(state_path),
                "--player",
                "blue",
                "--limit",
                "3",
                "--json",
            )
            self.assertEqual(listed.returncode, 0, listed.stdout + listed.stderr)

            state = GameState.from_dict(load_json(state_path))
            engine_moves = list_legal_moves(state, player="blue", limit=3)
            cli_moves = json.loads(listed.stdout)["moves"]
            self.assertEqual(cli_moves, [move.to_dict() for move in engine_moves])
            self.assertTrue(cli_moves)

    def test_gui_switch_mode_duo_uses_duo_state_and_board_asset_without_tk_mainloop(self) -> None:
        sidebars_asset = object()
        classic_asset = object()
        duo_asset = object()
        root = FakeRoot()
        canvas = FakeCanvas()
        self.assertFalse(hasattr(root, "mainloop"))

        gui = BlokusGui.__new__(BlokusGui)
        gui.mode = "classic"
        gui.root = root
        gui.canvas = canvas
        gui.window_width = 1500
        gui.window_height = 950
        gui.board_x = 338
        gui.board_y = 66
        gui.scale = 1
        gui.images = {
            "sidebars": sidebars_asset,
            "board_classic": classic_asset,
            "board_duo": duo_asset,
        }
        gui.status_width = 220
        gui.font_small = ("Avenir Next", 10)
        gui.hovered_piece = "I1"
        gui.drag_state = object()
        gui.active_panel = "settings"
        gui.status_text = "before"

        with patch.object(BlokusGui, "draw_sidebar_overlays", return_value=None), patch.object(
            BlokusGui, "draw_board_state", return_value=None
        ), patch.object(BlokusGui, "draw_status_panel", return_value=None), patch.object(
            BlokusGui, "draw_piece_panel", return_value=None
        ), patch.object(BlokusGui, "draw_drag_preview", return_value=None):
            gui.switch_mode("duo")

        self.assertEqual(gui.mode, "duo")
        self.assertEqual(root.titles, ["Blokus Duo GUI"])
        self.assertEqual(gui.state.mode, "duo")
        self.assertEqual(gui.state.board_size, 14)
        self.assertEqual(gui.state.players, ("blue", "red"))
        self.assertEqual(gui.state.start_corners, {"blue": (4, 4), "red": (9, 9)})
        self.assertEqual(gui.state.controller_types, {"blue": "human", "red": "human"})
        self.assertIsNone(gui.hovered_piece)
        self.assertIsNone(gui.drag_state)
        self.assertIsNone(gui.active_panel)
        self.assertEqual(
            gui.status_text,
            "Drag a piece onto the board. Press R to rotate and F to flip while dragging.",
        )
        self.assertEqual(canvas.deleted, ["all"])
        used_images = [call["kwargs"]["image"] for call in canvas.images]
        self.assertIn(duo_asset, used_images)
        self.assertNotIn(classic_asset, used_images)
        self.assertFalse(hasattr(root, "mainloop"))


def test_duo_evaluator_replays_temporary_scenario_contract(tmp_path: Path) -> None:
    """Verify Duo evaluator scenario replay without depending on shared fixtures."""

    scenario_path = tmp_path / "duo_opening_sequence.json"
    scenario_path.write_text(
        json.dumps(
            {
                "name": "Duo opening sequence",
                "mode": "duo",
                "steps": [
                    {
                        "player": "blue",
                        "piece": "I1",
                        "x": 4,
                        "y": 4,
                        "rotation": 0,
                        "flipped": False,
                    },
                    {
                        "player": "red",
                        "piece": "I1",
                        "x": 9,
                        "y": 9,
                        "rotation": 0,
                        "flipped": False,
                    },
                ],
                "expect": {
                    "current_player": "blue",
                    "history_length": 2,
                    "occupied_counts": {"blue": 1, "red": 1},
                    "finished": False,
                },
            }
        ),
        encoding="utf-8",
    )

    result = run_scenario(scenario_path)
    assert result.passed, result.detail


if __name__ == "__main__":
    unittest.main()
