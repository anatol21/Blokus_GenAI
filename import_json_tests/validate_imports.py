#!/usr/bin/env python3
"""Validate all JSON files in this directory using GameState.from_dict and validate_loaded_state.

Usage: PYTHONPATH=src python3 import_json_tests/validate_imports.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "src")
from blokus.models import GameState
from blokus.engine import validate_loaded_state

HERE = Path(__file__).parent

results = {}
for p in sorted(HERE.glob("*.json")):
    try:
        data = json.loads(p.read_text())
    except Exception as e:
        results[p.name] = (False, f"JSON parse error: {e}")
        continue
    # Attempt structural load
    try:
        state = GameState.from_dict(data)
    except Exception as e:
        results[p.name] = (False, f"from_dict error: {e}")
        continue
    # Attempt semantic validation
    try:
        validate_loaded_state(state)
    except Exception as e:
        results[p.name] = (False, f"validate_loaded_state error: {e}")
    else:
        results[p.name] = (True, "OK")

# Print summary
ok = [n for n,(s,m) in results.items() if s]
bad = [n for n,(s,m) in results.items() if not s]
print(f"Checked {len(results)} files: {len(ok)} valid, {len(bad)} invalid")
for n,(s,m) in results.items():
    status = "VALID" if s else "INVALID"
    print(f"- {n}: {status} - {m}")

# Exit code non-zero if any unexpected passes/fails? For now, exit 0

