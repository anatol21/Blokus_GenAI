import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class CliTests(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "blokus", *args],
            cwd=REPO_ROOT,
            env={"PYTHONPATH": str(REPO_ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

    def test_new_command_writes_valid_json_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "state.json"
            completed = self.run_cli("new", "--mode", "classic", "--output", str(output_path))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with output_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["mode"], "classic")
            self.assertEqual(payload["current_player"], "blue")

    def test_validate_command_rejects_bad_opening(self) -> None:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        completed = self.run_cli(
            "validate",
            "--state",
            str(fixture_path),
            "--piece",
            "I1",
            "--x",
            "1",
            "--y",
            "1",
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("must cover start corner", completed.stdout)

    def test_apply_command_writes_expected_state(self) -> None:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "applied.json"
            completed = self.run_cli(
                "apply",
                "--state",
                str(fixture_path),
                "--piece",
                "I1",
                "--x",
                "0",
                "--y",
                "0",
                "--output",
                str(output_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            with output_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["current_player"], "yellow")
            self.assertEqual(len(payload["history"]), 1)
            self.assertEqual(payload["board"][0][0], "B")
            self.assertNotIn("I1", payload["remaining_pieces"]["blue"])
            self.assertEqual(payload["consecutive_passes"], 0)

    def test_apply_command_rejects_illegal_move_without_rewriting_input(self) -> None:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_state = Path(temp_dir) / "state.json"
            temp_state.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")
            before = temp_state.read_text(encoding="utf-8")
            completed = self.run_cli(
                "apply",
                "--state",
                str(temp_state),
                "--piece",
                "I1",
                "--x",
                "1",
                "--y",
                "1",
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("must cover start corner", completed.stdout)
            self.assertEqual(temp_state.read_text(encoding="utf-8"), before)

    def test_legal_moves_json_respects_zero_limit(self) -> None:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        completed = self.run_cli(
            "legal-moves",
            "--state",
            str(fixture_path),
            "--limit",
            "0",
            "--json",
        )
        self.assertEqual(completed.returncode, 0)
        payload = json.loads(completed.stdout)
        self.assertEqual(payload, {"moves": []})

    def test_pass_turn_command_advances_blocked_player(self) -> None:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_blue_no_legal_moves.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "passed.json"
            completed = self.run_cli(
                "pass-turn",
                "--state",
                str(fixture_path),
                "--output",
                str(output_path),
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            with output_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["current_player"], "yellow")
            self.assertEqual(payload["consecutive_passes"], 1)
            self.assertFalse(payload["finished"])

    def test_new_command_rejects_bad_controller_count(self) -> None:
        completed = self.run_cli("new", "--players", "human,computer")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("expects 4 controller types", completed.stdout)

    def test_new_command_rejects_unsupported_mode(self) -> None:
        completed = self.run_cli("new", "--mode", "duo")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Unsupported mode 'duo'", completed.stdout)

    def test_new_command_rejects_unknown_controller_type(self) -> None:
        completed = self.run_cli("new", "--players", "human,human,human,alien")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Controller types must be", completed.stdout)


if __name__ == "__main__":
    unittest.main()
