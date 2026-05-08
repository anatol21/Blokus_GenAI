import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "blokus", *args],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )


class CliTests(unittest.TestCase):
    def test_new_command_writes_valid_json_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "state.json"

            completed = _run_cli(
                "new",
                "--mode",
                "classic",
                "--output",
                str(output_path),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            with output_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["mode"], "classic")
            self.assertEqual(payload["current_player"], "blue")

    def test_validate_command_rejects_bad_opening(self) -> None:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"

        completed = _run_cli(
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

    def test_legal_moves_command_with_zero_limit_returns_empty_json_list(self) -> None:
        """Evidence: LIST-03, R-F-02, R-F-06, R-T-06."""

        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"

        completed = _run_cli(
            "legal-moves",
            "--state",
            str(fixture_path),
            "--limit",
            "0",
            "--json",
        )

        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(completed.stderr, "")
        self.assertEqual(json.loads(completed.stdout), {"moves": []})


if __name__ == "__main__":
    unittest.main()
