"""Persistence tests: import/export, board reproducibility, and save/resume.

These tests verify the current CLI and engine persistence functionality
as described in the Persistence & Evidence epic (PERS-01 through PERS-10).

Coverage areas:
  - Round-trip fidelity (save → load → save produces identical output)
  - Board reproducibility after serialization
  - CLI export/import workflows
  - Multi-move state chain persistence
  - Resume-from-saved-state via the play command
  - Edge cases: empty history, encoding, truncation, concurrent field consistency
"""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from typing import Any

from blokus.engine import (
    apply_move,
    compute_scores,
    get_occupied_cells,
    list_legal_moves,
    new_game,
)
from blokus.models import GameState, Move


REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_DIR = REPO_ROOT / "fixtures" / "states"


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    """Run a CLI command in a subprocess matching the test environment."""

    return subprocess.run(
        [sys.executable, "-m", "blokus", *args],
        cwd=REPO_ROOT,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )


# ── Round-Trip Fidelity ─────────────────────────────────────────────


class RoundTripFidelityTests(unittest.TestCase):
    """Verify that to_dict → from_dict → to_dict is lossless."""

    def test_fresh_state_round_trips_exactly(self) -> None:
        """A brand-new game state survives serialization without any field drift."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                state = new_game(mode=mode)
                payload = state.to_dict()
                reloaded = GameState.from_dict(payload)
                self.assertEqual(reloaded.to_dict(), payload)

    def test_round_trip_after_opening_moves(self) -> None:
        """State after each player opens still round-trips exactly."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                state = new_game(mode=mode)
                moves = [
                    Move(player, "I1", *state.start_corners[player])
                    for player in state.players
                ]
                for m in moves:
                    state = apply_move(state, m)

                payload = state.to_dict()
                reloaded = GameState.from_dict(payload)
                self.assertEqual(reloaded.to_dict(), payload)

    def test_round_trip_after_follow_up_moves(self) -> None:
        """Classic state after opening + follow-up moves round-trips exactly."""

        state = new_game(mode="classic")
        moves = [
            Move("blue", "I1", 0, 0),
            Move("yellow", "I1", 19, 0),
            Move("red", "I1", 19, 19),
            Move("green", "I1", 0, 19),
            Move("blue", "I2", 1, 1, rotation=1),
        ]
        for m in moves:
            state = apply_move(state, m)

        payload = state.to_dict()
        reloaded = GameState.from_dict(payload)
        self.assertEqual(reloaded.to_dict(), payload)

    def test_serialization_is_deterministic(self) -> None:
        """Serializing the same state twice produces identical JSON text."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                state = new_game(mode=mode)
                state = apply_move(state, Move(state.players[0], "I1", *state.start_corners[state.players[0]]))
                json_a = json.dumps(state.to_dict(), sort_keys=True)
                json_b = json.dumps(state.to_dict(), sort_keys=True)
                self.assertEqual(json_a, json_b)

    def test_round_trip_with_computer_controllers(self) -> None:
        """Controller metadata (human/computer + strategy) survives round-trip."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                players = new_game(mode=mode).players
                state = new_game(
                    mode=mode,
                    controllers={player: "computer" for player in players},
                    strategies={player: "default" for player in players},
                )
                payload = state.to_dict()
                reloaded = GameState.from_dict(payload)

                for player in state.players:
                    self.assertEqual(
                        reloaded.controller_types[player],
                        state.controller_types[player],
                        f"controller_types mismatch for {player}",
                    )
                    self.assertEqual(
                        reloaded.controller_strategies[player],
                        state.controller_strategies[player],
                        f"controller_strategies mismatch for {player}",
                    )


# ── Board Reproducibility ───────────────────────────────────────────


class BoardReproducibilityTests(unittest.TestCase):
    """Verify the board is byte-for-byte reproducible after save/load."""

    def test_board_cells_match_after_reload(self) -> None:
        """Every cell on the board is identical after a round-trip."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                state = new_game(mode=mode)
                state = apply_move(state, Move(state.players[0], "I1", *state.start_corners[state.players[0]]))
                if len(state.players) > 1:
                    state = apply_move(state, Move(state.players[1], "I1", *state.start_corners[state.players[1]]))

                reloaded = GameState.from_dict(state.to_dict())

                for y in range(state.board_size):
                    for x in range(state.board_size):
                        self.assertEqual(
                            reloaded.board[y][x],
                            state.board[y][x],
                            f"Board mismatch at ({x}, {y})",
                        )

    def test_occupied_cells_cache_rebuilt_from_board(self) -> None:
        """The derived occupied_cells_by_player cache is rebuilt correctly on load."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                state = new_game(mode=mode)
                for player in state.players:
                    state = apply_move(state, Move(player, "I1", *state.start_corners[player]))

                reloaded = GameState.from_dict(state.to_dict())

                for player in reloaded.players:
                    original_cells = get_occupied_cells(state, player)
                    reloaded_cells = get_occupied_cells(reloaded, player)
                    self.assertEqual(reloaded_cells, original_cells, f"Cache mismatch for {player}")

    def test_board_string_representation_is_stable(self) -> None:
        """The compact string-per-row board format is stable across serialization."""

        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0))

        payload = state.to_dict()
        self.assertEqual(payload["board"][0][0], "B")
        self.assertEqual(payload["board"][1][0], ".")

        reloaded = GameState.from_dict(payload)
        repayload = reloaded.to_dict()
        self.assertEqual(repayload["board"], payload["board"])


# ── History & Metadata Preservation ─────────────────────────────────


class HistoryPreservationTests(unittest.TestCase):
    """Verify move history and scalar metadata survive persistence."""

    def test_history_entries_preserved(self) -> None:
        """All history entries are present and ordered after round-trip."""

        state = new_game(mode="classic")
        moves = [
            Move("blue", "I1", 0, 0),
            Move("yellow", "I1", 19, 0),
            Move("red", "I1", 19, 19),
        ]
        for m in moves:
            state = apply_move(state, m)

        reloaded = GameState.from_dict(state.to_dict())
        self.assertEqual(len(reloaded.history), 3)

        for i, original_move in enumerate(moves):
            loaded_move = reloaded.history[i]
            self.assertEqual(loaded_move.player, original_move.player)
            self.assertEqual(loaded_move.piece, original_move.piece)
            self.assertEqual(loaded_move.x, original_move.x)
            self.assertEqual(loaded_move.y, original_move.y)

    def test_current_player_preserved(self) -> None:
        """The current_player advances correctly and survives round-trip."""

        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0))
        self.assertEqual(state.current_player, "yellow")

        reloaded = GameState.from_dict(state.to_dict())
        self.assertEqual(reloaded.current_player, "yellow")

    def test_consecutive_passes_preserved(self) -> None:
        """consecutive_passes value survives round-trip."""

        state = new_game(mode="classic")
        payload = state.to_dict()
        payload["consecutive_passes"] = 3
        reloaded = GameState.from_dict(payload)
        self.assertEqual(reloaded.consecutive_passes, 3)

    def test_finished_flag_preserved(self) -> None:
        """finished flag survives round-trip."""

        state = new_game(mode="classic")
        payload = state.to_dict()
        payload["finished"] = True
        reloaded = GameState.from_dict(payload)
        self.assertTrue(reloaded.finished)

    def test_remaining_pieces_decrease_after_move(self) -> None:
        """After a move, the placed piece is removed from remaining_pieces and stays removed after round-trip."""

        state = new_game(mode="classic")
        self.assertIn("I1", state.remaining_pieces["blue"])

        state = apply_move(state, Move("blue", "I1", 0, 0))
        self.assertNotIn("I1", state.remaining_pieces["blue"])

        reloaded = GameState.from_dict(state.to_dict())
        self.assertNotIn("I1", reloaded.remaining_pieces["blue"])

    def test_scores_reproducible_after_round_trip(self) -> None:
        """Scores computed from original and reloaded state are identical."""

        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0))
        state = apply_move(state, Move("yellow", "I1", 19, 0))

        reloaded = GameState.from_dict(state.to_dict())
        self.assertEqual(compute_scores(reloaded), compute_scores(state))


# ── CLI Export / Import Workflows ────────────────────────────────────


class CliExportImportTests(unittest.TestCase):
    """Verify import/export through the actual CLI subprocess interface."""

    def test_new_then_reimport_produces_same_state(self) -> None:
        """CLI 'new' exports a file that reimports to the same payload."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "state.json"
                    result = run_cli("new", "--mode", mode, "--output", str(path))
                    self.assertEqual(result.returncode, 0, result.stderr)

                    with path.open("r", encoding="utf-8") as f:
                        exported = json.load(f)

                    reloaded = GameState.from_dict(exported)
                    self.assertEqual(reloaded.to_dict(), exported)

    def test_apply_chain_produces_valid_state_at_each_step(self) -> None:
        """Chaining CLI apply commands produces valid, loadable state at every step."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as tmp:
                    path_a = Path(tmp) / "step0.json"
                    path_b = Path(tmp) / "step1.json"

                    result = run_cli("new", "--mode", mode, "--output", str(path_a))
                    self.assertEqual(result.returncode, 0, result.stderr)

                    with path_a.open("r", encoding="utf-8") as f:
                        initial = json.load(f)
                    first_player = initial["players"][0]
                    corner = initial["start_corners"][first_player]

                    result = run_cli(
                        "apply", "--state", str(path_a),
                        "--player", first_player,
                        "--piece", "I1", "--x", str(corner[0]), "--y", str(corner[1]),
                        "--output", str(path_b),
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

                    with path_b.open("r", encoding="utf-8") as f:
                        step1 = json.load(f)
                    self.assertEqual(step1["current_player"], initial["players"][1] if len(initial["players"]) > 1 else initial["players"][0])
                    self.assertEqual(len(step1["history"]), 1)

    def test_export_file_is_valid_utf8_json(self) -> None:
        """Exported file is valid UTF-8 JSON with a trailing newline."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                with tempfile.TemporaryDirectory() as tmp:
                    path = Path(tmp) / "state.json"
                    run_cli("new", "--mode", mode, "--output", str(path))

                    raw = path.read_bytes()
                    text = raw.decode("utf-8")
                    self.assertTrue(text.endswith("\n"))
                    json.loads(text)

    def test_cli_show_reproduces_board_from_saved_file(self) -> None:
        """CLI 'show' renders a saved state without errors."""
        for mode in ["classic", "duo"]:
            with self.subTest(mode=mode):
                fixture = FIXTURE_DIR / f"{mode}_initial.json"
                if not fixture.exists():
                    self.skipTest(f"Fixture not found: {fixture}")
                result = run_cli("show", "--state", str(fixture))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertGreater(len(result.stdout.strip()), 0)


# ── Save and Resume Workflow ─────────────────────────────────────────


class SaveResumeTests(unittest.TestCase):
    """Verify the save-and-resume workflow through the play command and engine."""

    def test_play_resume_from_mid_game_state(self) -> None:
        """A state saved mid-game can be loaded and continued with valid moves."""

        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0))
        state = apply_move(state, Move("yellow", "I1", 19, 0))
        state = apply_move(state, Move("red", "I1", 19, 19))
        state = apply_move(state, Move("green", "I1", 0, 19))

        with tempfile.TemporaryDirectory() as tmp:
            save_path = Path(tmp) / "mid_game.json"
            with save_path.open("w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)

            with save_path.open("r", encoding="utf-8") as f:
                loaded_payload = json.load(f)
            resumed = GameState.from_dict(loaded_payload)

            self.assertEqual(resumed.current_player, "blue")
            self.assertFalse(resumed.finished)
            legal = list_legal_moves(resumed, limit=1)
            self.assertGreater(len(legal), 0, "Resumed state should have legal moves")

    def test_save_then_continue_playing(self) -> None:
        """Save a state, reload it, apply another move, and verify consistency."""

        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0))

        payload = state.to_dict()

        resumed = GameState.from_dict(payload)

        resumed = apply_move(resumed, Move("yellow", "I1", 19, 0))

        self.assertEqual(resumed.current_player, "red")
        self.assertEqual(len(resumed.history), 2)
        self.assertNotIn("I1", resumed.remaining_pieces["yellow"])

    def test_cli_play_with_state_and_output(self) -> None:
        """CLI play --state with computer players and --max-turns saves valid output."""

        with tempfile.TemporaryDirectory() as tmp:
            init_path = Path(tmp) / "init.json"
            run_cli(
                "new",
                "--players", "computer,computer,computer,computer",
                "--output", str(init_path),
            )

            out_path = Path(tmp) / "after_play.json"
            result = run_cli(
                "play",
                "--state", str(init_path),
                "--max-turns", "4",
                "--output", str(out_path),
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(out_path.exists(), "Output file should be created")

            with out_path.open("r", encoding="utf-8") as f:
                played = json.load(f)

            self.assertGreater(len(played["history"]), 0)
            GameState.from_dict(played)


# ── Fixture Baseline Tests ───────────────────────────────────────────


class FixtureBaselineTests(unittest.TestCase):
    """Verify canonical fixture files load, round-trip, and produce valid states."""

    def test_classic_initial_fixture_loads(self) -> None:
        """The canonical classic_initial.json fixture loads without error."""

        fixture = FIXTURE_DIR / "classic_initial.json"
        with fixture.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        state = GameState.from_dict(payload)
        self.assertEqual(state.mode, "classic")
        self.assertEqual(state.board_size, 20)
        self.assertEqual(state.current_player, "blue")
        self.assertFalse(state.finished)

    def test_classic_initial_has_full_piece_sets(self) -> None:
        """Every player starts with all 21 pieces."""

        state = GameState.from_dict(
            json.loads((FIXTURE_DIR / "classic_initial.json").read_text(encoding="utf-8"))
        )
        for player in state.players:
            self.assertEqual(
                len(state.remaining_pieces[player]),
                21,
                f"{player} should have 21 pieces, got {len(state.remaining_pieces[player])}",
            )

    def test_classic_initial_board_is_empty(self) -> None:
        """The initial fixture board has no occupied cells."""

        state = GameState.from_dict(
            json.loads((FIXTURE_DIR / "classic_initial.json").read_text(encoding="utf-8"))
        )
        for y in range(state.board_size):
            for x in range(state.board_size):
                self.assertIsNone(state.board[y][x], f"Cell ({x}, {y}) should be empty")

    def test_blocked_player_fixture_loads(self) -> None:
        """The classic_blue_no_legal_moves fixture loads and has expected properties."""

        fixture = FIXTURE_DIR / "classic_blue_no_legal_moves.json"
        with fixture.open("r", encoding="utf-8") as f:
            payload = json.load(f)
        state = GameState.from_dict(payload)
        self.assertEqual(state.current_player, "blue")

        legal = list_legal_moves(state, player="blue", limit=1)
        self.assertEqual(len(legal), 0, "Blue should have no legal moves in this fixture")


# ── Serialization Edge Cases ─────────────────────────────────────────


class SerializationEdgeCaseTests(unittest.TestCase):
    """Edge cases and defensive checks for the serialization path."""

    def test_malformed_json_raises(self) -> None:
        """Truncated or malformed JSON raises a parse error, not a silent failure."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.json"
            path.write_text("{\"mode\": \"classic\", \"board\":", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                with path.open("r", encoding="utf-8") as f:
                    json.load(f)

    def test_empty_file_raises(self) -> None:
        """An empty file raises a parse error."""

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.json"
            path.write_text("", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                with path.open("r", encoding="utf-8") as f:
                    json.load(f)

    def test_missing_mode_field_raises(self) -> None:
        """A JSON object missing the 'mode' key raises a clear error."""

        payload = {"board": [], "players": []}
        with self.assertRaises((KeyError, ValueError)):
            GameState.from_dict(payload)

    def test_wrong_board_row_count_raises(self) -> None:
        """Board with wrong number of rows is rejected."""

        state = new_game(mode="classic")
        payload = state.to_dict()
        payload["board"] = payload["board"][:10]
        with self.assertRaises(ValueError):
            GameState.from_dict(payload)

    def test_wrong_board_row_length_raises(self) -> None:
        """Board with a row of wrong length is rejected."""

        state = new_game(mode="classic")
        payload = state.to_dict()
        rows = payload["board"]
        rows[5] = rows[5][:10]
        with self.assertRaises(ValueError):
            GameState.from_dict(payload)

    def test_missing_remaining_pieces_raises(self) -> None:
        """Missing remaining_pieces field raises."""

        state = new_game(mode="classic")
        payload = state.to_dict()
        del payload["remaining_pieces"]
        with self.assertRaises(ValueError):
            GameState.from_dict(payload)

    def test_extra_fields_are_tolerated(self) -> None:
        """Unknown extra fields in the JSON do not cause errors."""

        state = new_game(mode="classic")
        payload = state.to_dict()
        payload["extra_field"] = "should be ignored"
        payload["another_extra"] = 42

        reloaded = GameState.from_dict(payload)
        self.assertEqual(reloaded.mode, "classic")

    def test_defaults_applied_for_optional_fields(self) -> None:
        """Optional fields that are missing get sensible defaults."""

        state = new_game(mode="classic")
        payload: dict[str, Any] = state.to_dict()
        del payload["consecutive_passes"]
        del payload["finished"]
        del payload["history"]

        reloaded = GameState.from_dict(payload)
        self.assertEqual(reloaded.consecutive_passes, 0)
        self.assertFalse(reloaded.finished)
        self.assertEqual(len(reloaded.history), 0)

    def test_cli_rejects_nonexistent_state_file(self) -> None:
        """CLI apply with a nonexistent state file fails cleanly."""

        result = run_cli(
            "apply", "--state", "/nonexistent/path/to/state.json",
            "--piece", "I1", "--x", "0", "--y", "0",
        )
        self.assertNotEqual(result.returncode, 0)

    def test_overwrite_does_not_corrupt_on_failed_apply(self) -> None:
        """When apply fails, the output file is not created or changed."""

        with tempfile.TemporaryDirectory() as tmp:
            state_path = Path(tmp) / "state.json"
            output_path = Path(tmp) / "output.json"

            state = new_game(mode="classic")
            with state_path.open("w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)

            result = run_cli(
                "apply", "--state", str(state_path),
                "--player", "yellow",
                "--piece", "I1", "--x", "19", "--y", "0",
                "--output", str(output_path),
            )
            self.assertEqual(result.returncode, 1)
            self.assertFalse(
                output_path.exists(),
                "Output file should not be created when apply fails",
            )


# ── Legal Move Continuity After Persistence ──────────────────────────


class LegalMoveContinuityTests(unittest.TestCase):
    """Verify legal move generation produces identical results after round-trip."""

    def test_legal_moves_identical_before_and_after_round_trip(self) -> None:
        """Legal moves listed from an original state match those from a reloaded state."""

        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0))
        state = apply_move(state, Move("yellow", "I1", 19, 0))
        state = apply_move(state, Move("red", "I1", 19, 19))
        state = apply_move(state, Move("green", "I1", 0, 19))

        original_moves = list_legal_moves(state, limit=50)
        original_set = {
            (m.player, m.piece, m.x, m.y, m.rotation, m.flipped) for m in original_moves
        }

        reloaded = GameState.from_dict(state.to_dict())
        reloaded_moves = list_legal_moves(reloaded, limit=50)
        reloaded_set = {
            (m.player, m.piece, m.x, m.y, m.rotation, m.flipped) for m in reloaded_moves
        }

        self.assertEqual(reloaded_set, original_set)

    def test_scoring_identical_after_round_trip(self) -> None:
        """Scores computed from reloaded state match the original."""

        state = new_game(mode="classic")
        state = apply_move(state, Move("blue", "I1", 0, 0))
        state = apply_move(state, Move("yellow", "I1", 19, 0))

        original_scores = compute_scores(state)
        reloaded = GameState.from_dict(state.to_dict())
        reloaded_scores = compute_scores(reloaded)

        self.assertEqual(reloaded_scores, original_scores)


if __name__ == "__main__":
    unittest.main()
