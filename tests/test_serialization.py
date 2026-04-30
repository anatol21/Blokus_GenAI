import json
from pathlib import Path
from typing import cast
import unittest

from blokus.engine import apply_move, new_game
from blokus.models import GameState, Move
from blokus.review.types import Finding, ReviewPayload, ReviewResult, ReviewSummary, UncertainRisk


REPO_ROOT = Path(__file__).resolve().parents[1]


class SerializationTests(unittest.TestCase):
    def load_initial_payload(self) -> dict[str, object]:
        fixture_path = REPO_ROOT / "fixtures" / "states" / "classic_initial.json"
        with fixture_path.open("r", encoding="utf-8") as handle:
            return json.load(handle)

    def test_initial_fixture_round_trips(self) -> None:
        payload = self.load_initial_payload()
        state = GameState.from_dict(payload)
        self.assertEqual(state.to_dict(), payload)

    def test_state_round_trip_after_moves(self) -> None:
        state = new_game(
            controllers={"blue": "computer", "yellow": "human", "red": "human", "green": "human"},
            strategies={"blue": "default", "yellow": "default", "red": "default", "green": "default"},
        )
        for move in (
            Move("blue", "I1", 0, 0),
            Move("yellow", "I1", 19, 0),
            Move("red", "I1", 19, 19),
            Move("green", "I1", 0, 19),
            Move("blue", "I2", 1, 1),
        ):
            state = apply_move(state, move)
        reloaded = GameState.from_dict(state.to_dict())
        self.assertEqual(reloaded.to_dict(), state.to_dict())
        self.assertEqual(reloaded.controller_types["blue"], "computer")
        self.assertEqual(reloaded.controller_strategies["blue"], "default")

    def test_invalid_board_symbol_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        board = cast(list[str], payload["board"])
        board[0] = "Q" + board[0][1:]
        with self.assertRaisesRegex(ValueError, "No player configured for board symbol"):
            GameState.from_dict(payload)

    def test_mismatched_player_list_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["players"] = ["blue", "yellow"]
        with self.assertRaisesRegex(ValueError, "do not match mode"):
            GameState.from_dict(payload)

    def test_invalid_current_player_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        payload["current_player"] = "orange"
        with self.assertRaisesRegex(ValueError, "is not part of the mode player order"):
            GameState.from_dict(payload)

    def test_unknown_remaining_piece_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        remaining_pieces = cast(dict[str, list[str]], payload["remaining_pieces"])
        remaining_pieces["blue"][0] = "BAD"
        with self.assertRaisesRegex(ValueError, "contain unknown ids"):
            GameState.from_dict(payload)

    def test_duplicate_remaining_piece_is_rejected(self) -> None:
        payload = self.load_initial_payload()
        remaining_pieces = cast(dict[str, list[str]], payload["remaining_pieces"])
        remaining_pieces["blue"] = ["I1", "I1"]
        with self.assertRaisesRegex(ValueError, "contain duplicates"):
            GameState.from_dict(payload)

    def test_agentic_review_payload_matches_schema_shape(self) -> None:
        schema_path = REPO_ROOT / "schemas" / "agentic_review_output.schema.json"
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        payload = ReviewResult(
            pr=ReviewPayload(number=44, head_sha="headsha", base_sha="basesha"),
            summary=ReviewSummary(
                overall_risk="high",
                test_posture="weak",
                static_analysis_posture="issues_found",
                performance_posture="clean",
            ),
            findings=(
                Finding(
                    id="finding-1",
                    title="Blocking issue",
                    severity="high",
                    confidence="high",
                    category="static-analysis",
                    file="src/blokus/review/diff.py",
                    line_start=81,
                    line_end=84,
                    evidence="Example evidence.",
                    impact="Example impact.",
                    suggested_action="Example fix.",
                    blocking_recommendation=True,
                ),
            ),
            uncertain_risks=(
                UncertainRisk(
                    risk="Dependency files changed.",
                    reason_uncertain="Intent is not obvious from the diff alone.",
                    suggested_verification="Review dependency intent.",
                ),
            ),
            verdict="NEEDS CHANGES",
        ).to_dict()

        self.assertEqual(set(payload.keys()), set(schema["required"]))

        pr_schema = schema["properties"]["pr"]
        self.assertEqual(set(payload["pr"].keys()), set(pr_schema["required"]))

        summary_schema = schema["properties"]["summary"]["properties"]
        self.assertEqual(payload["summary"]["overall_risk"], "high")
        self.assertIn(payload["summary"]["overall_risk"], summary_schema["overall_risk"]["enum"])
        self.assertIn(payload["summary"]["test_posture"], summary_schema["test_posture"]["enum"])
        self.assertIn(
            payload["summary"]["static_analysis_posture"],
            summary_schema["static_analysis_posture"]["enum"],
        )
        self.assertIn(
            payload["summary"]["performance_posture"],
            summary_schema["performance_posture"]["enum"],
        )

        finding_schema = schema["properties"]["findings"]["items"]
        self.assertEqual(set(payload["findings"][0].keys()), set(finding_schema["required"]))
        self.assertGreaterEqual(payload["findings"][0]["line_start"], 1)
        self.assertGreaterEqual(payload["findings"][0]["line_end"], payload["findings"][0]["line_start"])

        risk_schema = schema["properties"]["uncertain_risks"]["items"]
        self.assertEqual(set(payload["uncertain_risks"][0].keys()), set(risk_schema["required"]))


if __name__ == "__main__":
    unittest.main()
