#!/usr/bin/env bash
set -euo pipefail

OUTPUT_ROOT="${1:-dist/release-candidate}"
RELEASE_TAG="${RELEASE_TAG:-dev-$(git rev-parse --short HEAD)}"
ARCHIVE_NAME="${ARCHIVE_NAME:-blokus-focus-pokus-${RELEASE_TAG}.tar.gz}"

rm -rf "$OUTPUT_ROOT"
mkdir -p "$OUTPUT_ROOT/logs" "$OUTPUT_ROOT/docs" "$OUTPUT_ROOT/examples" "$OUTPUT_ROOT/source"

if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
else
  export PYTHONPATH=src
fi

./scripts/test.sh 2>&1 | tee "$OUTPUT_ROOT/logs/test-output.txt"
./scripts/cli_smoke.sh 2>&1 | tee "$OUTPUT_ROOT/logs/cli-smoke-output.txt"
./scripts/validate_fixtures.sh 2>&1 | tee "$OUTPUT_ROOT/logs/fixture-schema-output.txt"
./scripts/evaluate.sh 2>&1 | tee "$OUTPUT_ROOT/logs/evaluate-output.txt"

python -m blokus new --mode classic --output "$OUTPUT_ROOT/examples/classic-initial.json"
python -m blokus show --state "$OUTPUT_ROOT/examples/classic-initial.json" > "$OUTPUT_ROOT/examples/classic-render.txt"

for path in \
  README.md \
  OWNERSHIP.md \
  TEAM_SUMMARY.md \
  docs/AGENT_POLICY.md \
  docs/RELEASE_CONTENTS.md \
  docs/RELEASE_POLICY.md \
  docs/evidence-log.md \
  docs/traceability-matrix.md \
  docs/ai-usage.md
do
  cp "$path" "$OUTPUT_ROOT/docs/"
done

git archive --format=tar.gz --output "$OUTPUT_ROOT/source/blokus-focus-pokus-${RELEASE_TAG}-source.tar.gz" HEAD

./scripts/generate_evidence_delta.sh \
  "$OUTPUT_ROOT/evidence-delta.md" \
  "$OUTPUT_ROOT/logs/test-output.txt" \
  "$OUTPUT_ROOT/logs/evaluate-output.txt"

export OUTPUT_ROOT RELEASE_TAG ARCHIVE_NAME

python - <<'PY'
from __future__ import annotations

import json
import os
import subprocess
from datetime import UTC, datetime
from pathlib import Path

output_root = Path(os.environ["OUTPUT_ROOT"])
release_tag = os.environ["RELEASE_TAG"]
archive_name = os.environ["ARCHIVE_NAME"]

metadata = {
    "release_tag": release_tag,
    "archive_name": archive_name,
    "generated_at": datetime.now(UTC).isoformat(),
    "commit": subprocess.run(
        ["git", "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip(),
    "artifacts": {
        "evidence_delta": "evidence-delta.md",
        "logs": [
            "logs/test-output.txt",
            "logs/cli-smoke-output.txt",
            "logs/fixture-schema-output.txt",
            "logs/evaluate-output.txt",
        ],
        "example_state": "examples/classic-initial.json",
        "example_render": "examples/classic-render.txt",
    },
}

(output_root / "release-metadata.json").write_text(
    json.dumps(metadata, indent=2) + "\n",
    encoding="utf-8",
)
PY

mkdir -p dist
tar -czf "dist/${ARCHIVE_NAME}" -C "$(dirname "$OUTPUT_ROOT")" "$(basename "$OUTPUT_ROOT")"
echo "Created dist/${ARCHIVE_NAME}"
