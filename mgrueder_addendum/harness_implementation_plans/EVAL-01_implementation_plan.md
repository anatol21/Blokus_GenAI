# EVAL-01 Implementation Plan

## User Story

> **Purpose:** Harness passes only when exact expected `current_player`, `history_length`, `finished`, `occupied_counts`, and `consecutive_passes` are met.
>
> **Scope:** fixture-harness positive scenario on Classic baseline.
>
> **Oracle:** Positive scenarios pass only when exact expected-state fields match.

**Linked requirements:** R-E-01, R-F-07, R-T-04, R-T-06
**Linked scenarios:** EVAL-01
**Dependencies:** CLI-06, PERS-10

---

## 1. Current State Assessment

### ✅ What already works

| Component | Status | Detail |
|-----------|--------|--------|
| Evaluation harness ([evaluate.py](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/src/blokus/evaluate.py)) | **Complete** | `run_scenario()` already checks all 5 required fields: `current_player`, `history_length`, `finished`, `occupied_counts`, `consecutive_passes` (lines 78-128) |
| [classic_corner_sequence.json](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/fixtures/scenarios/classic_corner_sequence.json) | **Exists, partial** | Has `current_player`, `finished`, `history_length`, `occupied_counts` — **missing `consecutive_passes`** |
| [classic_blocked_blue_pass.json](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/fixtures/scenarios/classic_blocked_blue_pass.json) | **Exists, complete** | Has all 5 fields including `consecutive_passes: 1` |
| [test_evaluate.py](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/tests/test_evaluate.py) | **Exists, partial** | `test_all_scenarios_pass` runs all scenarios but does **not** individually assert that each of the 5 oracle fields was checked |
| CLI harness (`python -m blokus evaluate`) | **Works** | 3/3 scenarios pass |
| Execution matrix entry (EVAL-01) | **Exists** | Row at line 36 of `test_execution_matrix.md` — status shows "implemented" / "executable now" |

### 🔴 Gaps to close

| # | Gap | Impact |
|---|-----|--------|
| **G1** | `classic_corner_sequence.json` is missing `consecutive_passes` in its `expect` block | The oracle for this scenario is incomplete — the harness can't verify pass-counter correctness |
| **G2** | `test_evaluate.py` has no per-scenario test that names the two required fixtures | The user story's checklist demands individual evidence for "corner-sequence" and "blocked-blue-pass" |
| **G3** | No test asserts that the oracle actually checks **all 5** expected fields, not just a subset | If a fixture omits a field, the harness silently skips that check — this violates the "only when exact expected-state fields match" oracle |
| **G4** | Execution matrix says "implemented" but we haven't yet demonstrated the per-field evidence | The checklist item "attach evidence under tests/test_evaluate.py and fixture folder" isn't satisfied |

---

## 2. Implementation Steps

### Step 1 — Fix `classic_corner_sequence.json` fixture (G1)

Add the missing `consecutive_passes` field to the `expect` block.

After 8 legal moves with no passes, the expected value is `0`.

```diff
 "expect": {
     "current_player": "blue",
     "finished": false,
     "history_length": 8,
+    "consecutive_passes": 0,
     "occupied_counts": {
       "blue": 3,
       "yellow": 3,
       "red": 3,
       "green": 3
     }
   }
```

> [!IMPORTANT]
> This is the only fixture change needed. `classic_blocked_blue_pass.json` already has all 5 fields.

### Step 2 — Add per-scenario positive tests to `test_evaluate.py` (G2, G3)

Add two new test methods that individually run each scenario and assert:

1. The scenario **passes** (`result.passed is True`)
2. The fixture's `expect` block contains **all 5** required oracle fields
3. The `result.detail` confirms the expected outcome

```python
SCENARIO_DIR = REPO_ROOT / "fixtures" / "scenarios"

POSITIVE_ORACLE_FIELDS = {
    "current_player",
    "history_length",
    "finished",
    "occupied_counts",
    "consecutive_passes",
}


def _assert_oracle_completeness(self, fixture_path: Path) -> None:
    """Verify the fixture's expect block covers all EVAL-01 oracle fields."""
    with fixture_path.open("r", encoding="utf-8") as f:
        scenario = json.load(f)
    expect = scenario.get("expect", {})
    missing = POSITIVE_ORACLE_FIELDS - set(expect.keys())
    self.assertFalse(
        missing,
        f"Fixture {fixture_path.name} is missing oracle fields: {missing}",
    )


def test_corner_sequence_scenario_passes_with_full_oracle(self) -> None:
    """EVAL-01: classic_corner_sequence passes with all 5 oracle fields checked."""
    fixture = SCENARIO_DIR / "classic_corner_sequence.json"
    self._assert_oracle_completeness(fixture)
    result = run_scenario(fixture)
    self.assertTrue(result.passed, result.detail)


def test_blocked_blue_pass_scenario_passes_with_full_oracle(self) -> None:
    """EVAL-01: classic_blocked_blue_pass passes with all 5 oracle fields checked."""
    fixture = SCENARIO_DIR / "classic_blocked_blue_pass.json"
    self._assert_oracle_completeness(fixture)
    result = run_scenario(fixture)
    self.assertTrue(result.passed, result.detail)
```

> [!TIP]
> The `_assert_oracle_completeness` helper ensures that if someone accidentally removes a field from the fixture, the test **fails** instead of silently passing with an incomplete oracle. This directly satisfies the "passes **only** when exact expected-state fields match" requirement.

### Step 3 — Verify existing infrastructure handles all fields (No code change)

The harness code in [evaluate.py lines 78-128](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/src/blokus/evaluate.py#L78-L128) already:

- Checks `current_player` (line 79)
- Checks `finished` (line 90)
- Checks `history_length` (line 98)
- Checks `consecutive_passes` (line 106)
- Checks `occupied_counts` per player (lines 117-128)

**No changes to `evaluate.py` are needed.** The harness logic is complete.

### Step 4 — Update execution matrix (G4)

The EVAL-01 row already exists and says "implemented". After running the tests successfully, the only update needed is confirming that the evidence links are accurate. The current row already references:

- `tests/test_evaluate.py` ✅
- `fixtures/scenarios/` ✅

No execution matrix content change is required unless you want to add the specific test method names as evidence detail. I'd suggest adding the per-test names for clarity:

```diff
-| Observable Evidence | `tests/test_evaluate.py`<br>`fixtures/scenarios/` |
+| Observable Evidence | `tests/test_evaluate.py::EvaluationHarnessTests::test_corner_sequence_scenario_passes_with_full_oracle`<br>`tests/test_evaluate.py::EvaluationHarnessTests::test_blocked_blue_pass_scenario_passes_with_full_oracle`<br>`fixtures/scenarios/` |
```

---

## 3. File Change Summary

| File | Action | Scope |
|------|--------|-------|
| `fixtures/scenarios/classic_corner_sequence.json` | **Edit** | Add `"consecutive_passes": 0` to `expect` block |
| `tests/test_evaluate.py` | **Edit** | Add `import json`, add 2 test methods + 1 helper, add `SCENARIO_DIR` + `POSITIVE_ORACLE_FIELDS` constants |
| `docs/test_execution_matrix.md` | **Edit** (optional) | Refine EVAL-01 evidence links |
| `src/blokus/evaluate.py` | **No change** | Harness already checks all 5 fields |

---

## 4. Verification Plan

After implementation, run:

```bash
# 1. Harness CLI — all scenarios should pass
PYTHONPATH=src python3 -m blokus evaluate

# 2. Per-scenario tests — both positive oracle tests should pass
PYTHONPATH=src python3 -m pytest tests/test_evaluate.py -v

# 3. Full test suite — no regressions
PYTHONPATH=src python3 -m pytest tests/ -v --timeout=60
```

### Expected output for step 2:

```
tests/test_evaluate.py::EvaluationHarnessTests::test_all_scenarios_pass PASSED
tests/test_evaluate.py::EvaluationHarnessTests::test_corner_sequence_scenario_passes_with_full_oracle PASSED
tests/test_evaluate.py::EvaluationHarnessTests::test_blocked_blue_pass_scenario_passes_with_full_oracle PASSED
tests/test_evaluate.py::EvaluationHarnessTests::test_counterexample_scenario_replays_piece_reuse_failure PASSED
tests/test_evaluate.py::EvaluationHarnessTests::test_expectation_mismatch_scenario_reports_actual_value PASSED
tests/test_evaluate.py::EvaluationHarnessTests::test_invalid_move_scenario_reports_execution_failure PASSED
```

---

## 5. Checklist Mapping

| Checklist item | Covered by |
|----------------|------------|
| Confirm both positive fixtures exist and are runnable | Step 1 (fixture fix) + Step 2 (tests assert fixture exists and runs) |
| Execute harness against corner-sequence and blocked-blue-pass scenarios | Step 2 (individual `run_scenario()` calls in tests) |
| Assert exact expected-state fields | Step 2 (`_assert_oracle_completeness` + `result.passed`) |
| Attach evidence under tests/test_evaluate.py and fixture folder | Step 2 (new tests) + Step 1 (fixture update) |
| Update execution matrix status and link evidence | Step 4 (optional evidence link refinement) |
