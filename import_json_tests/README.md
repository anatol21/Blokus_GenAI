Import JSON Tests

Each JSON file includes a top-level `_comment` describing the scenario.

Groups:
- 00_valid_* : Known-good exported game(s).
- 01_invalid_* : Structural issues (duplicates, missing pieces).
- 02_invalid_* : Semantic issues (illegal placements, history/remaining mismatch).

Validator script `validate_imports.py` will attempt to load each JSON via `GameState.from_dict()` and then run `validate_loaded_state()` to check semantic consistency. Files that are intentionally invalid include `_expected": "invalid"` in their comments.
