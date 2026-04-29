# Evidence Log

Use this log for reproducible evidence of implementation and review outcomes.

## Logging policy

- Add one row per meaningful attempt or verification event.
- Link requirement IDs and issue IDs whenever possible.
- Record both what worked and what failed.
- Include direct evidence pointers (test output, fixture path, commit, PR, screenshot, or notes).

## Template

| Date (YYYY-MM-DD) | Area | Related issue | Related requirement | What was attempted | What worked | What failed | Evidence | Next action |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-03-27 | Repository setup | I-01, I-20 | R-NF-03, R-NF-05 | Added requirements baseline and traceability matrix | Required docs created and linked | Live GitHub sync pending environment access | `docs/requirements.md`, `docs/traceability-matrix.md` | Sync labels/issues when API access is available |
| 2026-04-19 | engine-core | I-14 | R-F-04, R-T-02, R-T-04 | Completed Phase 1 Classic legality-validation test evidence in `tests/test_engine.py` for validator identity/rack failures and precedence | `tests/test_engine.py` now provides evidence for `unknown_player`, `unknown_piece`, `wrong_turn`, generic rack-unavailable rejection for spent-piece reuse, and precedence of rack-unavailable failure over later spatial checks; local run passed | `piece_not_owned_by_player` is not yet a distinct validator category and remains deferred under the current free-form `ValidationResult.reason` contract | `tests/test_engine.py`, `PYTHONPATH=src python -m unittest tests.test_engine` | Keep `piece_not_owned_by_player` deferred until the validator exposes a distinct machine-assertable category |
| 2026-04-19 | engine-core | I-14 | R-F-04, R-T-02, R-T-04 | Refined Classic move validation to emit machine-assertable `reason_category` values while preserving human-readable `reason` text | `validate_move()` now returns machine-assertable `reason_category` values for `unknown_player`, `unknown_piece`, `wrong_turn`, and `piece_unavailable`, with direct verification in `tests/test_engine.py`; local run passed | Under the current state model, rack-related failures are intentionally normalized to `piece_unavailable` rather than split into `spent_piece_reuse` and `piece_not_owned_by_player` | `src/blokus/models.py`, `src/blokus/engine.py`, `tests/test_engine.py`, `PYTHONPATH=src python -m unittest tests.test_engine` | Revisit category split only if the state model later records distinct rack-ownership and spent-piece provenance |
| 2026-04-19 | engine-core | I-14 | R-F-04, R-F-26, R-F-27, R-T-02, R-T-04 | Implemented Classic `VAL-05` legality-validation evidence for out-of-bounds, overlap, and disconnected follow-up failures | `validate_move()` now emits stable `reason_category` values for `out_of_bounds`, `overlap`, and `missing_corner_contact`; `tests/test_engine.py` verifies the approved witness moves and proves rejected validations leave the full serialized source state unchanged; local run passed | No additional validator-category split was needed beyond the approved three-category slice | `src/blokus/engine.py`, `tests/test_engine.py`, `PYTHONPATH=src python -m unittest tests.test_engine` | Reuse the same full-state snapshot oracle for future negative validator scenarios that must prove no mutation on failure |
| 2026-04-19 | engine-core | I-14 | R-F-04, R-F-25, R-T-04 | Implemented Classic `VAL-09` finished-state legality-validation evidence for terminal move rejection | `validate_move()` now returns `reason_category=\"game_finished\"` for finished Classic states while preserving the existing human-readable reason text; `tests/test_engine.py` verifies the approved witness move and proves rejected validation leaves the full serialized source state unchanged; focused local run passed | No broader validator redesign or `validate_pass()` scope change was needed for this slice | `src/blokus/engine.py`, `tests/test_engine.py`, `PYTHONPATH=src python -m unittest tests.test_engine.EngineRuleTests.test_finished_game_rejects_move_without_mutation` | Keep terminal move rejection aligned with `LIST-04` finished-state empty-list behavior |
| 2026-04-19 | engine-core | I-09 | R-F-05, R-F-08, R-F-10, R-F-21, R-T-04 | Implemented Classic `LIFE-01` exact opening-apply transition evidence in `tests/test_engine.py` using the approved witness move `Move(\"blue\", \"I1\", 0, 0, rotation=0, flipped=False)` | `test_apply_move_matches_exact_opening_transition_contract` now proves one legal opening apply produces the exact serialized post-state: only `(0, 0)` is filled with blue, only blue's `I1` is removed, exactly one history item is appended, turn advances to yellow, `consecutive_passes` resets to `0`, `finished` stays `False`, and static metadata remains unchanged; focused local run passed | No broader apply-behavior expansion was needed beyond the exact-state oracle for this single successful Classic opening | `tests/test_engine.py`, `docs/test_execution_matrix.md`, `PYTHONPATH=src python -m unittest tests.test_engine.EngineRuleTests.test_apply_move_matches_exact_opening_transition_contract` | Reuse this exact serialized transition contract as the primary oracle for related CLI and serialization evidence |
| 2026-04-20 | engine-core | I-09 | R-F-05, R-F-10, R-F-25, R-T-04 | Implemented Classic `LIFE-02` illegal-opening apply evidence in `tests/test_engine.py` using the approved witness move `Move(\"blue\", \"I1\", 1, 0)` | `test_apply_move_illegal_opening_raises_without_mutation` now proves the illegal opening apply raises and leaves the full serialized state unchanged: board, history, remaining pieces, current player, `consecutive_passes`, and `finished` all match the pre-call snapshot exactly; focused local run passed | No `apply_move()` redesign or broader invalid-move expansion was needed for this slice | `tests/test_engine.py`, `docs/test_execution_matrix.md`, `PYTHONPATH=src python -m unittest tests.test_engine.EngineRuleTests.test_apply_move_illegal_opening_raises_without_mutation` | Reuse this full-state failed-apply oracle for adjacent CLI rejection evidence without broadening the engine scope |

## Suggested area tags

- `engine-core`
- `cli`
- `serialization`
- `transforms`
- `fixtures`
- `evaluation-harness`
- `documentation`
- `review`
