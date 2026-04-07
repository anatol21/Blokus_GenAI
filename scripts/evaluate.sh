#!/usr/bin/env bash
set -euo pipefail

if [ -f .venv/bin/activate ]; then
  . .venv/bin/activate
else
  export PYTHONPATH=src
fi

python -m blokus evaluate
exit 1
