#!/usr/bin/env bash
set -euo pipefail

if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
else
  export PYTHONPATH=src
fi

artifact_dir="${1:-artifacts/ci/fixture-schema}"
mkdir -p "${artifact_dir}"

python - "${artifact_dir}" <<'PY'
import json
import sys
from pathlib import Path

from blokus.evaluate import SCENARIO_DIR, STATE_DIR
from blokus.models import GameState, Move

artifact_dir = Path(sys.argv[1])
report_path = artifact_dir / "report.txt"
report_lines: list[str] = []

schema_paths = sorted(Path("schemas").glob("*.json"))
if not schema_paths:
    raise SystemExit("No schema files were found in schemas/.")

for path in schema_paths:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a top-level JSON object.")
    for key in ("$schema", "title", "type"):
        if key not in payload:
            raise ValueError(f"{path} is missing required top-level key {key!r}.")
    report_lines.append(f"OK schema {path}")

state_fixture_paths = sorted(Path("fixtures/states").glob("*.json"))
if not state_fixture_paths:
    raise SystemExit("No state fixtures were found in fixtures/states/.")

for path in state_fixture_paths:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    state = GameState.from_dict(payload)
    if state.to_dict() != payload:
        raise ValueError(f"{path} does not round-trip through GameState serialization.")
    report_lines.append(f"OK state fixture {path}")

scenario_directories = [
    ("scenario fixture", SCENARIO_DIR),
    ("scenario failure fixture", Path("fixtures/scenario_failures")),
]
scenario_paths: list[tuple[str, Path]] = []
for label, directory in scenario_directories:
    if directory.exists():
        for path in sorted(directory.glob("*.json")):
            scenario_paths.append((label, path))

if not scenario_paths:
    raise SystemExit("No scenario fixtures were found in fixtures/scenarios/.")

for label, path in scenario_paths:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a top-level JSON object.")
    state_fixture = payload.get("state_fixture")
    if state_fixture is not None:
        fixture_path = Path(str(state_fixture))
        if not fixture_path.is_absolute():
            fixture_path = STATE_DIR / str(state_fixture)
        if not fixture_path.exists():
            raise ValueError(f"{path} references missing state fixture {fixture_path}.")

    steps = payload.get("steps")
    if steps is not None:
        if not isinstance(steps, list):
            raise ValueError(f"{path} field 'steps' must be a list.")
        for index, raw_step in enumerate(steps):
            if not isinstance(raw_step, dict):
                raise ValueError(f"{path} step #{index} must be a JSON object.")
            step_type = str(raw_step.get("type", "move"))
            if step_type == "pass":
                player = raw_step.get("player")
                if player is not None and not isinstance(player, str):
                    raise ValueError(f"{path} pass step #{index} player must be a string when present.")
                continue
            Move.from_dict({key: value for key, value in raw_step.items() if key != "type"})
    else:
        moves = payload.get("moves", [])
        if not isinstance(moves, list):
            raise ValueError(f"{path} field 'moves' must be a list.")
        for index, raw_move in enumerate(moves):
            if not isinstance(raw_move, dict):
                raise ValueError(f"{path} move #{index} must be a JSON object.")
            Move.from_dict(raw_move)
    expect = payload.get("expect", {})
    if not isinstance(expect, dict):
        raise ValueError(f"{path} field 'expect' must be a JSON object when present.")
    report_lines.append(f"OK {label} {path.as_posix()}")

report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
print(report_path.read_text(encoding="utf-8"), end="")
PY
