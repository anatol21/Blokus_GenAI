import unittest
from types import SimpleNamespace
from unittest.mock import patch

from blokus.gui import BlokusGui


class GuiTests(unittest.TestCase):
    def test_restart_preserves_active_mode(self) -> None:
        gui = BlokusGui.__new__(BlokusGui)
        gui.mode = "duo"
        gui.root = object() # type: ignore[assignment]
        gui.state = SimpleNamespace(  # type: ignore[assignment]
            controller_types={"blue": "human"},
            controller_strategies={"blue": "human"},
        )
        gui.drag_state = "dragging" # type: ignore[assignment]
        gui.status_text = ""

        with patch("blokus.gui.messagebox.askokcancel", return_value=True) as ask_ok_cancel:
            with patch(
                "blokus.gui.new_game",
                return_value=SimpleNamespace(
                    finished=True,
                    controller_types={"blue": "human"},
                    controller_strategies={"blue": "human"},
                    current_player="blue",
                ),
            ):
                gui.handle_restart()

        ask_ok_cancel.assert_called_once()
        self.assertTrue(hasattr(gui.state, "finished"))
        self.assertIsNone(gui.drag_state)
        self.assertEqual(gui.status_text, "Started a fresh Duo game.")


if __name__ == "__main__":
    unittest.main()
