# EVAL-03 Implementation Plan

## User Story

> **Purpose:** Harness reports the mismatched oracle field and actual value when expected data is wrong.
>
> **Scope:** fixture-harness oracle-mismatch scenario on Classic baseline.
>
> **Oracle:** Oracle mismatches are diagnosed field-by-field, not collapsed into vague failure output.

**Linked requirements:** R-E-01, R-T-04, R-T-06  
**Linked scenario:** EVAL-03  
**Dependencies:** EVAL-01

---

## 1. Current State Assessment

### Fixture recap

[classic_expectation_mismatch.json](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/fixtures/scenario_failures/classic_expectation_mismatch.json) plays one legal move (blue I1 at corner) then sets a **deliberately wrong** oracle:

```json
"expect": {
    "current_player": "blue",   ← wrong (actual: "yellow")
    "history_length": 1         ← correct
}
```

The harness checks `current_player` first ([evaluate.py:79](file:///Users/maximilianalpgruder/Desktop/UNIMA%20FSS26/Gen_AI/projects/blokus/src/blokus/evaluate.py#L79)), finds the mismatch, and returns immediately with:

```
name:   'classic_expectation_mismatch'
passed: False
detail: 'Expected current player blue, got yellow.'
```

This detail message is **field-specific and diagnosable** — it names the field (`current player`), the expected value (`blue`), and the actual value (`yellow`). This is exactly the "diagnosed field-by-field" behavior the oracle demands.

### ✅ What already works

| Component | Status |
|-----------|--------|
| Fixture | **Complete** — deliberately wrong `current_player` triggers a clean field-level mismatch |
| Harness logic | **Complete** — returns structured "Expected X, got Y" per field |
| Existing test (line 74-77) | **Exists, partial** — checks `passed=False` and the full detail string |
| Execution matrix EVAL-03 row | **Exists** — status "implemented" / "executable now" |

### 🔴 Gaps to close

| # | Gap | Impact |
|---|-----|--------|
| **G1** | Test does **not assert `result.name`** | The oracle says the harness "reports" the mismatch — the scenario name is part of that report identity. Untested. |
| **G2** | No EVAL-03 docstring for traceability | No link from test to scenario ID |
| **G3** | Single `assertIn` merges expected-value and actual-value checking | The oracle demands "field-by-field" diagnosis with explicit **expected** and **actual** values. Separate assertions for each make the evidence clearer and pinpoint which part of the message would break on regression. |

---

## 2. Implementation — Single test method edit

```diff
     def test_expectation_mismatch_scenario_reports_actual_value(self) -> None:
+        """EVAL-03: oracle mismatch reports the specific field, expected value, and actual value."""
+
         result = run_scenario(SCENARIO_FAILURE_DIR / "classic_expectation_mismatch.json")
         self.assertFalse(result.passed)
-        self.assertIn("Expected current player blue, got yellow.", result.detail)
+        # Oracle: result includes the scenario name
+        self.assertEqual(result.name, "classic_expectation_mismatch")
+        # Oracle: detail identifies the mismatched field with expected and actual values
+        self.assertIn("Expected current player", result.detail)
+        self.assertIn("blue", result.detail)
+        self.assertIn("got yellow", result.detail)
```

### What each assertion proves

| Assertion | Oracle guarantee |
|-----------|-----------------|
| `assertFalse(result.passed)` | Wrong expectations → failure |
| `assertEqual(result.name, ...)` | Scenario is identifiable by name |
| `assertIn("Expected current player", ...)` | Detail identifies **which field** mismatched |
| `assertIn("blue", ...)` | Detail includes the **expected value** |
| `assertIn("got yellow", ...)` | Detail includes the **actual value** |

Splitting the original single `assertIn` into three gives field-by-field evidence: if the message format ever changes (e.g. expected/actual order swaps), the test pinpoints exactly which component broke.

---

## 3. File Change Summary

| File | Action | Scope |
|------|--------|-------|
| `tests/test_evaluate.py` | **Edit** | Add docstring + replace 1 assertion with 4 at lines 74-77 |
| `fixtures/scenario_failures/classic_expectation_mismatch.json` | **No change** | Fixture is correct |
| `src/blokus/evaluate.py` | **No change** | Harness already reports field-level diagnostics |
| `docs/test_execution_matrix.md` | **No change** | EVAL-03 row already accurate |

---

## 4. Verification

```bash
PYTHONPATH=src python3 -m pytest tests/test_evaluate.py -v
```
