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

from blokus.evaluate import SCENARIO_DIR
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

scenario_paths = sorted(SCENARIO_DIR.glob("*.json"))
if not scenario_paths:
    raise SystemExit("No scenario fixtures were found in fixtures/scenarios/.")

for path in scenario_paths:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a top-level JSON object.")
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
    report_lines.append(f"OK scenario fixture {path.relative_to(Path.cwd())}")

report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")
print(report_path.read_text(encoding="utf-8"), end="")
PY
