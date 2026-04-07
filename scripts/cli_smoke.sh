#!/usr/bin/env bash
set -euo pipefail

if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
else
  export PYTHONPATH=src
fi

artifact_dir="${1:-artifacts/ci/cli}"
mkdir -p "${artifact_dir}"

state_path="${artifact_dir}/classic.json"

python -m blokus new --mode classic --output "${state_path}"
python -m blokus validate --state "${state_path}" --piece I1 --x 0 --y 0 | tee "${artifact_dir}/validate.txt"
python -m blokus apply --state "${state_path}" --piece I1 --x 0 --y 0 --output "${state_path}"
python -m blokus legal-moves --state "${state_path}" --limit 10 | tee "${artifact_dir}/legal_moves.txt"
python -m blokus show --state "${state_path}" | tee "${artifact_dir}/show.txt"
python -m blokus unknown-subcommand
