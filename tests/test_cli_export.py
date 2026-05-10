import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

REPO_ROOT = Path(__file__).resolve().parents[1]


class CliExportTests(unittest.TestCase):
    def run_cli_input(self, input_text: str, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "blokus", *args],
            cwd=REPO_ROOT,
            env={"PYTHONPATH": str(REPO_ROOT / "src")},
            input=input_text,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_export_prompts_and_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            # provide invalid directory first, then valid directory
            good_dir = Path(temp_dir)
            input_lines = [
                "export",
                "mygame",
                "/nonexistent_dir_should_fail",
                "mygame",  # filename again after invalid path
                str(good_dir),
                "quit",
            ]
            completed = self.run_cli_input("\n".join(input_lines) + "\n", "play", "--mode", "classic", "--players", "human,computer,computer,computer")
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            out_path = good_dir / "mygame.json"
            self.assertTrue(out_path.exists(), completed.stdout + completed.stderr)
            with out_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            # basic shape checks
            self.assertIn("mode", payload)
            self.assertIn("current_player", payload)

    def test_export_overwrites_existing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            target = Path(temp_dir) / "exists.json"
            target.write_text("old", encoding="utf-8")
            input_lines = [
                "export",
                "exists",
                str(Path(temp_dir)),
                "quit",
            ]
            completed = self.run_cli_input("\n".join(input_lines) + "\n", "play", "--mode", "classic", "--players", "human,computer,computer,computer")
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            # ensure file now contains JSON
            with target.open("r", encoding="utf-8") as handle:
                text = handle.read()
            self.assertIn("mode", text)

    def test_export_cancel_returns_to_game(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_lines = [
                "export",
                "cancel",
                "quit",
            ]
            completed = self.run_cli_input("\n".join(input_lines) + "\n", "play", "--mode", "classic", "--players", "human,computer,computer,computer")
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            # ensure no file created
            dir_path = Path(temp_dir)
            self.assertFalse(any(dir_path.iterdir()))


if __name__ == "__main__":
    unittest.main()
