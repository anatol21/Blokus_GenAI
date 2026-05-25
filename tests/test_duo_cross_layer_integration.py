"""Minimal Duo cross-layer integration coverage.

This module verifies that Duo mode works across the command-line entry point,
engine-backed legal move listing, evaluator scenario replay, and GUI mode
wiring. It intentionally avoids duplicating the Duo serialization and import
test suites, and it does not depend on shared scenario fixtures for evaluator
coverage. The GUI test uses fakes to validate mode wiring without starting a
real Tk mainloop.
"""

# Maintenance risk register:
# High: subprocess environment handling.
#   Evidence: run_cli shells out to `python -m blokus` with an augmented
#   PYTHONPATH.
#   Failure scenario: replacing the full environment can hide interpreter or
#   platform settings needed by CI or developer machines.
#   Recommended action: preserve os.environ and prepend the repo src path.
#   Suggested test: keep CLI integration assertions running through run_cli.
#
# Medium: fake Tk objects can drift from the GUI redraw contract.
#   Evidence: test_gui_switch_mode_duo_uses_duo_state_and_board_asset_without_tk_mainloop
#   calls switch_mode on a __new__ instance with FakeRoot and FakeCanvas.
#   Failure scenario: switch_mode/redraw starts requiring new canvas/root calls
#   and the fake no longer proves the intended non-mainloop boundary.
#   Recommended action: update the fakes only for calls needed by switch_mode
#   and keep the no-mainloop assertion.
#   Suggested test: continue asserting board_duo is rendered and FakeRoot has no
#   mainloop attribute.

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from blokus.engine import list_legal_moves
from blokus.evaluate import run_scenario
from blokus.gui import BlokusGui
from blokus.models import GameState


REPO_ROOT = Path(__file__).resolve().parents[1]


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run the Blokus CLI in a subprocess from the repository root.

    Args:
        *args: Command-line arguments passed after ``python -m blokus``.

    Returns:
        The completed subprocess with captured stdout and stderr.

    Warning:
        This helper preserves the caller's environment and prepends ``src`` to
        ``PYTHONPATH`` so subprocess behavior stays close to CI and local shells.
    """

    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    existing_pythonpath = env.get("PYTHONPATH")
    env["PYTHONPATH"] = (
        src_path
        if not existing_pythonpath
        else src_path + os.pathsep + existing_pythonpath
    )
    return subprocess.run(
        [sys.executable, "-m", "blokus", *args],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def load_json(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk for focused test assertions.

    Args:
        path: Path to a JSON file expected to contain an object.

    Returns:
        The decoded JSON object.
    """

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


class FakeRoot:
    """Small Tk root stand-in that records title updates.

    Attributes:
        titles: Window titles passed to ``title``.

    Warning:
        This fake intentionally has no ``mainloop`` attribute so the GUI test
        can prove ``switch_mode`` does not start a real Tk loop.
    """

    def __init__(self) -> None:
        self.titles: list[str] = []

    def title(self, value: str) -> None:
        """Record a title assigned by the GUI.

        Args:
            value: Window title text.
        """

        self.titles.append(value)


class FakeCanvas:
    """Small Canvas stand-in that records redraw calls used by switch_mode.

    Attributes:
        deleted: Canvas tags passed to ``delete``.
        images: Calls made to ``create_image`` with positional and keyword
            arguments.
        texts: Calls made to ``create_text`` with positional and keyword
            arguments.
    """

    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.images: list[dict[str, Any]] = []
        self.texts: list[dict[str, Any]] = []

    def delete(self, tag: str) -> None:
        """Record a canvas delete call.

        Args:
            tag: Canvas tag or item id requested for deletion.
        """

        self.deleted.append(tag)

    def create_image(self, *args: object, **kwargs: object) -> int:
        """Record an image draw call.

        Args:
            *args: Positional canvas arguments.
            **kwargs: Keyword canvas arguments.

        Returns:
            A stable fake canvas item id.
        """

        self.images.append({"args": args, "kwargs": kwargs})
        return len(self.images)

    def create_text(self, *args: object, **kwargs: object) -> int:
        """Record a text draw call.

        Args:
            *args: Positional canvas arguments.
            **kwargs: Keyword canvas arguments.

        Returns:
            A stable fake canvas item id.
        """

        self.texts.append({"args": args, "kwargs": kwargs})
        return len(self.texts)


class DuoCrossLayerIntegrationTests(unittest.TestCase):
    """Cross-layer checks for Duo behavior that spans multiple modules."""

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
                "First move coordinates must be the start corner (9, 9), got (8, 8).",
                rejected.stdout,
            )
            self.assertEqual(after_path.read_text(encoding="utf-8"), after_text)
            self.assertFalse(invalid_path.exists())

    def test_cli_duo_pass_turn_rejects_player_with_legal_moves(self) -> None:
        """Duo pass-turn rejects a current player who still has legal moves."""

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            initial_path = temp_path / "initial.json"
            after_path = temp_path / "after.json"
            passed_path = temp_path / "passed.json"

            created = run_cli("new", "--mode", "duo", "--output", str(initial_path))
            self.assertEqual(created.returncode, 0, created.stdout + created.stderr)

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

            after_text = after_path.read_text(encoding="utf-8")
            rejected = run_cli(
                "pass-turn",
                "--state",
                str(after_path),
                "--player",
                "red",
                "--output",
                str(passed_path),
            )
            self.assertEqual(rejected.returncode, 1)
            self.assertIn(
                "A player may only pass when no legal move exists.",
                rejected.stdout,
            )
            self.assertEqual(after_path.read_text(encoding="utf-8"), after_text)
            self.assertFalse(passed_path.exists())
            self.assertEqual(load_json(after_path)["current_player"], "red")

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
        """GUI mode switching wires Duo state and assets without a Tk mainloop."""

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

    def test_gui_duo_button_click_dispatches_switch_mode_without_tk_mainloop(self) -> None:
        """Duo sidebar clicks dispatch to switch_mode without a Tk mainloop."""

        root = FakeRoot()
        gui = BlokusGui.__new__(BlokusGui)
        gui.mode = "classic"
        gui.root = root
        gui.sidebar_bounds = {
            "duo": (10, 10, 30, 30),
            "classic": (40, 10, 60, 30),
        }
        event: Any = type("FakeEvent", (), {"x": 20, "y": 20})()
        self.assertFalse(hasattr(root, "mainloop"))

        with patch.object(gui, "switch_mode", return_value=None) as switch_mode:
            BlokusGui.on_button_press(gui, event)

        switch_mode.assert_called_once_with("duo")
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
