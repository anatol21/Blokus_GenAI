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
        """First-move coordinates must match the player's start corner.

        Coordinates that don't equal the start corner are rejected with
        a clear error message rather than being silently remapped.
        Out-of-turn moves are also rejected.
        """
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        # Wrong coordinates on first move: (5, 5) != blue's start corner (0, 0).
        completed = self.run_cli(
            "validate",
            "--state", str(fixture_path),
            "--piece", "I1",
            "--x", "5",
            "--y", "5",
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("start corner", completed.stdout)

        # Out-of-turn: yellow cannot move when it's blue's turn.
        # Use yellow's actual start corner (19, 0) so the coordinate
        # check passes and the turn-order rejection is what we test.
        completed = self.run_cli(
            "validate",
            "--state", str(fixture_path),
            "--player", "yellow",
            "--piece", "I1",
            "--x", "19",
            "--y", "0",
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("turn", completed.stdout)

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
        """Applying an out-of-turn move must fail and not modify the file."""
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_state = Path(temp_dir) / "state.json"
            temp_state.write_text(fixture_path.read_text(encoding="utf-8"), encoding="utf-8")
            before = temp_state.read_text(encoding="utf-8")
            completed = self.run_cli(
                "apply",
                "--state",
                str(temp_state),
                "--player",
                "yellow",
                "--piece",
                "I1",
                "--x",
                "19",
                "--y",
                "0",
            )
            self.assertEqual(completed.returncode, 1)
            self.assertIn("turn", completed.stdout)
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

    def test_new_command_rejects_unknown_mode(self) -> None:
        completed = self.run_cli("new", "--mode", "not-a-mode")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Unsupported mode 'not-a-mode'", completed.stdout)

    def test_new_command_rejects_unknown_controller_type(self) -> None:
        completed = self.run_cli("new", "--players", "human,human,human,alien")
        self.assertEqual(completed.returncode, 1)
        self.assertIn("Controller types must be", completed.stdout)

    def test_new_duo_game_creates_valid_state(self) -> None:
        """blokus new --mode duo creates a valid 14x14 2-player game."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "duo_state.json"
            completed = self.run_cli("new", "--mode", "duo", "--output", str(output_path))
            self.assertEqual(completed.returncode, 0, completed.stderr)
            with output_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            self.assertEqual(payload["mode"], "duo")
            self.assertEqual(payload["board_size"], 14)
            self.assertEqual(payload["players"], ["blue", "red"])
            self.assertEqual(payload["current_player"], "blue")
            self.assertEqual(len(payload["board"]), 14)
            self.assertEqual(len(payload["board"][0]), 14)

    def test_duo_opening_move_must_cover_corner(self) -> None:
        """Duo mode enforces start corner rule — wrong player is rejected."""
        fixture_path = REPO_ROOT / "fixtures" / "states" / "duo_initial_state.json"
        if not fixture_path.exists():
            self.skipTest(f"Fixture not found: {fixture_path}")
        
        # On a fresh duo board, blue moves first.  Requesting validation
        # for red (out of turn) must fail regardless of the coordinate
        # translation layer.
        completed = self.run_cli(
            "validate",
            "--state", str(fixture_path),
            "--player", "red",
            "--piece", "I1",
            "--x", "9",
            "--y", "9",
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("turn", completed.stdout)

    def test_duo_legal_moves_at_start(self) -> None:
        """Duo opening generates legal moves on blue's start corner."""
        fixture_path = REPO_ROOT / "fixtures" / "states" / "duo_initial_state.json"
        if not fixture_path.exists():
            self.skipTest(f"Fixture not found: {fixture_path}")
        
        completed = self.run_cli(
            "legal-moves",
            "--state", str(fixture_path),
            "--player", "blue",
            "--limit", "5",
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        lines = completed.stdout.strip().split("\n")
        self.assertGreater(len(lines), 0)
        self.assertTrue(any("blue" in line for line in lines))
    def test_legal_moves_command_with_zero_limit_returns_empty_json_list(self) -> None:
        """Evidence: LIST-03, R-F-02, R-F-06, R-T-06."""

        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        completed = self.run_cli(
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


class InvalidInputTests(unittest.TestCase):
    """Tests that invalid piece names and player names produce clean errors,
    not tracebacks, for non-interactive CLI commands (validate/apply)."""

    CLASSIC_FIXTURE = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
    DUO_FIXTURE = REPO_ROOT / "fixtures" / "states" / "duo_initial_state.json"

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "blokus", *args],
            cwd=REPO_ROOT,
            env={"PYTHONPATH": str(REPO_ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

    def _assert_clean_rejection(
        self,
        completed: subprocess.CompletedProcess[str],
        expected_fragment: str,
    ) -> None:
        """Assert non-zero exit, friendly message in stdout, no traceback."""
        self.assertEqual(completed.returncode, 1)
        self.assertIn(expected_fragment, completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)
        self.assertNotIn("KeyError", completed.stderr)

    # ── T1 + T2: unknown piece on validate/apply (parameterized) ───

    def test_validate_rejects_unknown_piece(self) -> None:
        """T1: validate --piece NOT_A_PIECE exits cleanly with a friendly message."""
        completed = self.run_cli(
            "validate",
            "--state", str(self.CLASSIC_FIXTURE),
            "--piece", "NOT_A_PIECE",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "Unknown piece")

    def test_apply_rejects_unknown_piece(self) -> None:
        """T2: apply --piece NOT_A_PIECE exits cleanly with a friendly message."""
        completed = self.run_cli(
            "apply",
            "--state", str(self.CLASSIC_FIXTURE),
            "--piece", "NOT_A_PIECE",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "Unknown piece")

    # ── T3 + T4: unknown player on validate/apply (parameterized) ──

    def test_validate_rejects_unknown_player(self) -> None:
        """T3: validate --player NOBODY exits cleanly with a friendly message."""
        completed = self.run_cli(
            "validate",
            "--state", str(self.CLASSIC_FIXTURE),
            "--player", "NOBODY",
            "--piece", "I1",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "Unknown player")

    def test_apply_rejects_unknown_player(self) -> None:
        """T4: apply --player NOBODY exits cleanly with a friendly message."""
        completed = self.run_cli(
            "apply",
            "--state", str(self.CLASSIC_FIXTURE),
            "--player", "NOBODY",
            "--piece", "I1",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "Unknown player")

    # ── T5: apply --output must NOT create file on bad piece ───────

    def test_apply_does_not_write_output_on_unknown_piece(self) -> None:
        """T5: apply with bad piece must not create the --output file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "should_not_exist.json"
            completed = self.run_cli(
                "apply",
                "--state", str(self.CLASSIC_FIXTURE),
                "--piece", "NOT_A_PIECE",
                "--x", "0", "--y", "0",
                "--output", str(output_path),
            )
            self.assertEqual(completed.returncode, 1)
            self.assertFalse(
                output_path.exists(),
                "Output file was created despite invalid piece name",
            )

    # ── T6: piece substring that is not a real piece ──────────────

    def test_validate_rejects_piece_substring(self) -> None:
        """T6: --piece I (not I1) is rejected as unknown."""
        completed = self.run_cli(
            "validate",
            "--state", str(self.CLASSIC_FIXTURE),
            "--piece", "I",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "Unknown piece")

    # ── T7: empty-string piece name ───────────────────────────────

    def test_validate_rejects_empty_piece_name(self) -> None:
        """T7: --piece '' is rejected as unknown."""
        completed = self.run_cli(
            "validate",
            "--state", str(self.CLASSIC_FIXTURE),
            "--piece", "",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "Unknown piece")

    # ── T8: Duo mode — unknown piece ──────────────────────────────

    def test_duo_validate_rejects_unknown_piece(self) -> None:
        """T8: unknown piece on a duo state is rejected cleanly."""
        if not self.DUO_FIXTURE.exists():
            self.skipTest(f"Fixture not found: {self.DUO_FIXTURE}")
        completed = self.run_cli(
            "validate",
            "--state", str(self.DUO_FIXTURE),
            "--piece", "NOT_A_PIECE",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "Unknown piece")

    # ── T9: Duo mode — classic-valid player rejected in duo ───────

    def test_duo_validate_rejects_classic_only_player(self) -> None:
        """T9: 'green' is valid in classic but must be rejected in duo."""
        if not self.DUO_FIXTURE.exists():
            self.skipTest(f"Fixture not found: {self.DUO_FIXTURE}")
        completed = self.run_cli(
            "validate",
            "--state", str(self.DUO_FIXTURE),
            "--player", "green",
            "--piece", "I1",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "Unknown player")

    # ── First-move coordinate enforcement ─────────────────────────

    def test_validate_rejects_nonsensical_first_move_coordinates(self) -> None:
        """Nonsensical coordinates on a first move are rejected, not silently remapped."""
        completed = self.run_cli(
            "validate",
            "--state", str(self.CLASSIC_FIXTURE),
            "--piece", "I1",
            "--x", "999", "--y", "999",
        )
        self._assert_clean_rejection(completed, "start corner")

    # ── Cases 1-5: state file, transform, turn order, pass ────────

    def test_validate_rejects_nonexistent_state_file(self) -> None:
        """Case 1: a missing state file produces a friendly error, not a traceback."""
        completed = self.run_cli(
            "validate",
            "--state", "/does/not/exist.json",
            "--piece", "I1",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "not found")

    def test_validate_rejects_malformed_state_file(self) -> None:
        """Case 2: a JSON file missing required game state keys is rejected cleanly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_state = Path(temp_dir) / "bad.json"
            bad_state.write_text('{"board": []}', encoding="utf-8")
            completed = self.run_cli(
                "validate",
                "--state", str(bad_state),
                "--piece", "I1",
                "--x", "0", "--y", "0",
            )
            self.assertEqual(completed.returncode, 1)
            self.assertNotIn("Traceback", completed.stderr)
            # The error comes from missing 'mode' key or similar structural issue.
            output = completed.stdout + completed.stderr
            self.assertTrue(
                "Malformed game state" in output or "mode" in output.lower(),
                f"Expected a structured error about the game state, got: {output}",
            )

    def test_validate_rejects_impossible_start_corner_transform(self) -> None:
        """Case 3: a valid piece with a rotation that cannot cover the start corner.

        F5 at rotation=0 (unflipped) has its top-left occupied cell at
        offset (1, 0), so no placement can cover corner (0, 0) without
        going out of bounds in the negative direction.
        """
        completed = self.run_cli(
            "validate",
            "--state", str(self.CLASSIC_FIXTURE),
            "--piece", "F5",
            "--rotation", "0",
            "--x", "0", "--y", "0",
        )
        self._assert_clean_rejection(completed, "cannot cover start corner")

    def test_validate_rejects_valid_player_out_of_turn(self) -> None:
        """Case 4: yellow is a valid classic player, but it's blue's turn.

        Uses yellow's actual start corner (19, 0) so the coordinate check
        passes and the turn-order rejection is what surfaces.
        """
        completed = self.run_cli(
            "validate",
            "--state", str(self.CLASSIC_FIXTURE),
            "--player", "yellow",
            "--piece", "I1",
            "--x", "19", "--y", "0",
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("turn", completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)

    def test_pass_turn_rejects_player_with_legal_moves(self) -> None:
        """Case 5: passing when legal moves exist must be rejected cleanly."""
        completed = self.run_cli(
            "pass-turn",
            "--state", str(self.CLASSIC_FIXTURE),
        )
        self.assertEqual(completed.returncode, 1)
        self.assertIn("pass", completed.stdout.lower())
        self.assertNotIn("Traceback", completed.stderr)


class CoordinateTranslationTests(unittest.TestCase):
    """Exercises coordinate translation logic for pieces where the reference cell
    offset is non-trivial (not (0, 0)), ensuring human/engine coordinate mapping is correct."""

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-m", "blokus", *args],
            cwd=REPO_ROOT,
            env={"PYTHONPATH": str(REPO_ROOT / "src")},
            capture_output=True,
            text=True,
            check=False,
        )

    def test_non_trivial_piece_translation_in_validate_and_apply(self) -> None:
        """Verify that a non-trivial piece translation maps correctly from human to engine.

        Using 'V3' rotation=1 flipped=False, the reference cell offset is (0, 1).
        If blue has already placed 'I1' at (0, 0), the move for 'V3' at engine coordinates
        x=1, y=0 is legal (cells: (1, 1), (2, 0), (2, 1)).
        The human coordinates for this move are x = 1 + 0 = 1, y = 0 + 1 = 1.
        """
        # Construct a mid-game state where blue has placed I1 at (0, 0)
        state_dict = {
            "mode": "classic",
            "board_size": 20,
            "players": ["blue", "yellow", "red", "green"],
            "start_corners": {"blue": [0, 0], "yellow": [19, 0], "red": [19, 19], "green": [0, 19]},
            "board": ["B" + "." * 19] + ["." * 20] * 19,
            "remaining_pieces": {
                "blue": ["V3"],
                "yellow": ["I1"], "red": ["I1"], "green": ["I1"]
            },
            "history": [{"player": "blue", "piece": "I1", "x": 0, "y": 0}],
            "current_player": "blue",
            "consecutive_passes": 0,
            "finished": False,
            "controller_types": {"blue": "human", "yellow": "human", "red": "human", "green": "human"},
            "controller_strategies": {"blue": "default", "yellow": "default", "red": "default", "green": "default"}
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text(json.dumps(state_dict), encoding="utf-8")

            # 1. Validate the move using human coordinates --x 1 --y 1
            completed_val = self.run_cli(
                "validate",
                "--state", str(state_path),
                "--player", "blue",
                "--piece", "V3",
                "--rotation", "1",
                "--x", "1",
                "--y", "1",
            )
            self.assertEqual(completed_val.returncode, 0, completed_val.stdout + completed_val.stderr)

            # 2. Apply the move using human coordinates --x 1 --y 1 and write output
            output_path = Path(temp_dir) / "applied.json"
            completed_app = self.run_cli(
                "apply",
                "--state", str(state_path),
                "--player", "blue",
                "--piece", "V3",
                "--rotation", "1",
                "--x", "1",
                "--y", "1",
                "--output", str(output_path),
            )
            self.assertEqual(completed_app.returncode, 0, completed_app.stdout + completed_app.stderr)

            # Assert that the serialized JSON state contains the ENGINE coordinates (x=1, y=0) in history
            with output_path.open("r", encoding="utf-8") as f:
                applied_state = json.load(f)
            
            # The second history entry (index 1) should be our V3 move
            self.assertEqual(len(applied_state["history"]), 2)
            v3_move = applied_state["history"][1]
            self.assertEqual(v3_move["player"], "blue")
            self.assertEqual(v3_move["piece"], "V3")
            self.assertEqual(v3_move["x"], 1)
            self.assertEqual(v3_move["y"], 0)
            self.assertEqual(v3_move["rotation"], 1)
            self.assertEqual(v3_move["flipped"], False)

            # 3. Verify suggest and legal-moves CLI output formatting (optionally, to verify coordinate mapping)
            completed_sug = self.run_cli("suggest", "--state", str(state_path), "--player", "blue")
            self.assertEqual(completed_sug.returncode, 0)
            self.assertIn("blue: V3 @ (1, 1) rotation=1 flipped=False", completed_sug.stdout)

            completed_leg = self.run_cli("legal-moves", "--state", str(state_path), "--player", "blue")
            self.assertEqual(completed_leg.returncode, 0)
            self.assertIn("blue: V3 @ (1, 1) rotation=1 flipped=False", completed_leg.stdout)


if __name__ == "__main__":
    unittest.main()

