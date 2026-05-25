# EVAL-02 Implementation Plan

## User Story

> **Purpose:** Harness returns `passed=false` and includes the scenario name plus concrete move-execution failure detail for the illegal opening.
>
> **Scope:** fixture-harness negative scenario on Classic baseline.
>
> **Oracle:** Negative replay fails with structured, diagnosable output.

**Linked requirements:** R-E-01, R-R-03, R-T-06  
**Linked scenario:** EVAL-02  
**Dependencies:** VAL-02

---

## 1. Current State Assessment

### ✅ What already works

| Component | Status | Detail |
|-----------|--------|--------|
| Failure fixture ([classic_invalid_opening_move.json](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/fixtures/scenario_failures/classic_invalid_opening_move.json)) | **Complete** | Places I1 at (1,1) instead of (0,0) — triggers the "must cover start corner" engine rejection |
| Harness failure path ([evaluate.py:74-75](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/src/blokus/evaluate.py#L74-L75)) | **Complete** | Catches the exception, returns `ScenarioResult(name=..., passed=False, detail="Scenario failed during move execution: ...")` |
| Existing test ([test_evaluate.py:60-64](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/tests/test_evaluate.py#L60-L64)) | **Exists, partial** | Asserts `passed=False` and checks `detail` for two substrings — but **does not assert `result.name`** |
| Execution matrix EVAL-02 row | **Exists** | Status = "implemented" / "executable now" |
| Harness output (verified live) | **Correct** | `name='classic_invalid_opening_move'`, `passed=False`, `detail='Scenario failed during move execution: Opening move for blue must cover start corner (0, 0).'` |

### 🔴 Gaps to close

| # | Gap | Impact |
|---|-----|--------|
| **G1** | The existing test does **not assert `result.name`** | The oracle says "includes the scenario name" — currently untested. If the fixture's `name` field were removed, the harness would fall back to the file stem, and the test wouldn't notice the difference. |
| **G2** | The test docstring does not reference EVAL-02 | No traceability from test to scenario ID |
| **G3** | The test does not assert the **specific engine reason** beyond a substring | The oracle demands "concrete move-execution failure detail". The current test checks `"must cover start corner"` but doesn't verify the full structured message, e.g. that it mentions player `blue` and corner `(0, 0)` |

> [!NOTE]
> These are **small, surgical gaps**. The infrastructure is solid — the fixture is correct, the harness logic is correct, and the test is 90% there. We just need to tighten the assertions.

---

## 2. Implementation Steps

### Step 1 — Strengthen the existing test (G1, G2, G3)

Replace the existing `test_invalid_move_scenario_reports_execution_failure` with a more thorough version:

```diff
-    def test_invalid_move_scenario_reports_execution_failure(self) -> None:
+    def test_invalid_move_scenario_reports_execution_failure(self) -> None:
+        """EVAL-02: illegal opening replay returns passed=false with scenario name and engine detail."""
+
         result = run_scenario(SCENARIO_FAILURE_DIR / "classic_invalid_opening_move.json")
         self.assertFalse(result.passed)
+        # Oracle: result includes the scenario name
+        self.assertEqual(result.name, "classic_invalid_opening_move")
+        # Oracle: result includes structured move-execution failure wrapper
         self.assertIn("Scenario failed during move execution", result.detail)
+        # Oracle: result includes concrete engine reason (player + corner)
         self.assertIn("must cover start corner", result.detail)
+        self.assertIn("blue", result.detail)
+        self.assertIn("(0, 0)", result.detail)
```

### What this adds:

| Assertion | What it proves |
|-----------|---------------|
| `assertEqual(result.name, "classic_invalid_opening_move")` | Scenario name is propagated from fixture `name` field |
| `assertIn("Scenario failed during move execution", ...)` | Harness wraps engine errors in a structured prefix (already existed) |
| `assertIn("must cover start corner", ...)` | Engine produces the correct rule violation (already existed) |
| `assertIn("blue", ...)` | Error identifies **which player** violated the rule |
| `assertIn("(0, 0)", ...)` | Error identifies **which corner** was required |

### Step 2 — No fixture changes needed

The fixture is already correct and minimal:
- `name` field present → harness reads it ✅
- Move at (1,1) misses the (0,0) start corner → triggers the exact engine error ✅
- No `expect` block → harness takes the failure path, not the oracle comparison path ✅

### Step 3 — No harness changes needed

The failure path in `evaluate.py` lines 74-75 already:
- Catches the exception
- Returns `ScenarioResult(name=name, passed=False, detail=f"Scenario failed during move execution: {exc}")`
- Preserves the engine's error message verbatim

### Step 4 — Execution matrix (no change needed)

The EVAL-02 row already has:
- Correct fixture path ✅
- Correct oracle description ✅
- Correct evidence links (`tests/test_evaluate.py` + fixture path) ✅

---

## 3. File Change Summary

| File | Action | Scope |
|------|--------|-------|
| `tests/test_evaluate.py` | **Edit** | Add docstring + 3 new assertions to existing test method (lines 60-64) |
| `fixtures/scenario_failures/classic_invalid_opening_move.json` | **No change** | Fixture is complete |
| `src/blokus/evaluate.py` | **No change** | Harness failure path is complete |
| `docs/test_execution_matrix.md` | **No change** | EVAL-02 row is accurate |

---

## 4. Verification Plan

```bash
# 1. Target test
PYTHONPATH=src python3 -m pytest tests/test_evaluate.py::EvaluationHarnessTests::test_invalid_move_scenario_reports_execution_failure -v

# 2. Full test_evaluate.py
PYTHONPATH=src python3 -m pytest tests/test_evaluate.py -v

# 3. Regression check
PYTHONPATH=src python3 -m blokus evaluate
```

---

## 5. Checklist Mapping

| Checklist item | Covered by |
|----------------|------------|
| Execute failure fixture through harness | Step 1 (test calls `run_scenario()`) |
| Assert passed=false plus scenario name and concrete move-execution detail | Step 1 (5 assertions total) |
| Capture evidence in tests/test_evaluate.py | Step 1 (strengthened test method) |
| Link failure fixture in review | Fixture path is in the test, in the matrix row, and in this plan |
| Update execution matrix status and link evidence | Step 4 — already accurate, no change needed |
