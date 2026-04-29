# Evidence-Link Validation Sweep
## Task: [Implementation] Evidence-link validation sweep (docs + harness index)

**Status:** In Progress  
**Assignee:** Owner 3  
**Reviewer:** Owner 2  
**Date:** 2026-04-27  
**Linked requirements:** R-NF-03, R-NF-05, R-D-04, R-D-08, R-E-04, R-E-05, R-T-04, R-T-05  
**Linked scenarios:** TEST-05, TEST-08, DOC-06, EVAL-01, EVAL-02, EVAL-03

---

## How to Use This Document

This document is the living record of the evidence sweep.
It has two parts:

**Part A — Pre-populated analysis** (done from available docs):
All claims, scenarios, and expected artifacts have been extracted
from `requirements_source_matrix.md` and `requirements.md`.
Each row shows what *should* exist according to the docs.

**Part B — Verification columns** (to be filled by Owner 3 in the repo):
For each row, Owner 3 must open the repository and check whether
the artifact actually exists, then fill in the Status and Notes columns.

**Oracle (pass condition):**
Every targeted evidence link resolves to a concrete file, fixture,
test, or harness artifact. No broken traceability remains for the
scoped set.

---

## What "Broken" Means — Reference Guide

Before running the sweep, use this guide to classify each link:

| Status | Symbol | Meaning |
|--------|--------|---------|
| Resolved | ✅ | File/test/fixture exists, is non-empty, and directly supports the claim |
| Partial | ⚠️ | File exists but is a stub, placeholder, or covers only part of the claim |
| Broken | ❌ | File does not exist, path is wrong, or artifact is referenced but never created |
| Circular | 🔄 | Link A points to link B, which points back to link A with no concrete artifact at either end |
| Planned | 📋 | Artifact is explicitly deferred to Phase 2 — not broken, but not current evidence either |

---

---

# PART A — Scoped Scenario Analysis

The six release-gate scenarios in scope are analyzed below.
Each section contains: what the scenario claims, what artifacts
it expects, and the verification instructions for Owner 3.

---

## Scenario 1: TEST-05
**Full name:** Validation evidence exists for core engine claims  
**Purpose:** Prove legality, apply, and serialization claims have direct validation artifacts  
**Source requirement:** R-T-04  
**Priority:** P0 — must pass for release

### What TEST-05 expects to exist

According to `requirements_source_matrix.md` (R-T-04 row), TEST-05 requires:

> Every core claim (legality checking, move application, serialization)
> maps to a concrete test, fixture, or log entry.

The sub-scenarios that feed TEST-05 are:

| Sub-scenario ID | Description | Expected artifact type | Expected path (repo) |
|----------------|-------------|----------------------|---------------------|
| VAL-01 | Valid opening move is accepted | Automated test | `tests/` — test for legal opening placement |
| VAL-02 | Opening move off start is rejected | Automated test | `tests/` — test for illegal opening rejection |
| PERS-03 | Apply then serialize round-trips | Automated test + fixture | `tests/` + `fixtures/` — round-trip state test |
| PERS-09 | CLI load-validate-apply-serialize chain is reproducible | Automated test or script | `tests/` or `scripts/` — CLI chain test |
| TEST-02 | Harness replays deterministic fixtures | Harness + fixture | Evaluation harness entry + fixture file |
| PERS-01 | Valid JSON state loads cleanly | Fixture + test | `fixtures/` — canonical JSON state file |

### Verification instructions for Owner 3

Go to the repository and for each row above:
1. Navigate to the expected path
2. Confirm the file exists and is non-empty
3. Read enough of the file to confirm it actually tests what the description says
4. Fill in the sweep table in Part B

### Linked requirements
R-E-01, R-E-02, R-E-04, R-F-05, R-F-07, R-NF-01, R-NF-04, R-NF-05, R-T-04

---

## Scenario 2: TEST-08
**Full name:** Evidence links stay navigable during review  
**Purpose:** Prove reviewers can traverse from summary claims to artifacts quickly  
**Source requirement:** R-T-05  
**Priority:** P1 — review-critical

### What TEST-08 expects to exist

> All evidence links in documents resolve to relevant artifacts
> without broken or circular references.

The sub-scenarios that feed TEST-08 are:

| Sub-scenario ID | Description | Expected artifact type | Expected path (repo) |
|----------------|-------------|----------------------|---------------------|
| TEST-06 | Unvalidated AI output cannot be adopted silently | AI usage log entry | `docs/ai-usage.md` — log with validation field |
| DOC-05 | AI usage records are structurally complete | AI usage log | `docs/ai-usage.md` — entries with all required fields |
| DOC-06 | Major claims resolve to direct evidence | Docs with links | `docs/` — documents where every major claim has a link |
| DOC-04 | Guideline artifacts map to real review work | Guideline package | `docs/` or repo root — reviewing guideline files |

### Required fields in ai-usage.md (per R-R-04)

Each entry in `docs/ai-usage.md` must contain ALL of these fields.
If any field is missing from any entry, that entry is Partial (⚠️):

- Model / tool name
- Task description
- Prompt or prompt category
- Validation method used
- Adoption decision (accepted / rejected / modified)

### Verification instructions for Owner 3

1. Open `docs/ai-usage.md` — confirm it exists
2. Count entries — confirm at least one entry per major AI-assisted task
3. Check each entry for the 5 required fields above
4. Open at least 3 documents in `docs/` and follow 2 evidence links each
5. Record whether each link resolves to a real artifact

### Linked requirements
R-D-08, R-E-04, R-E-05, R-NF-03, R-NF-05, R-T-05

---

## Scenario 3: DOC-06
**Full name:** Major claims resolve to direct evidence  
**Purpose:** Prove claims in docs link to concrete repository evidence  
**Source requirement:** R-NF-05, R-D-04  
**Priority:** P1 — review-critical

### What DOC-06 expects to exist

> Each major claim in project documentation resolves to a specific
> file, fixture, test, or log entry. No claim is left floating
> without a traceable artifact.

### Which documents are in scope for DOC-06

Based on `requirements.md` traceability notes, the following
documents must have navigable evidence links:

| Document | What it should link to |
|----------|----------------------|
| `docs/traceability-matrix.md` | Requirement IDs → test/fixture paths |
| `docs/requirements_source_matrix.md` | Requirement IDs → scenario IDs → artifact paths |
| `docs/evidence-log.md` | Claim statements → test names or fixture files |
| `docs/ai-usage.md` | AI tasks → validation records |
| `OWNERSHIP.md` | Work packages → contributor commits or test files |
| `TEAM_SUMMARY.md` | Key results → evidence links (top 3 counterexamples) |

### Verification instructions for Owner 3

For each document above:
1. Confirm it exists in the repository
2. Pick 3 claims or links at random
3. Follow each link and confirm it resolves to something real
4. If a document does not exist at all, mark as ❌ Broken

### Linked requirements
R-D-04, R-D-09, R-E-04, R-E-05, R-NF-02, R-NF-03, R-NF-05, R-R-02, R-T-05

---

## Scenario 4: EVAL-01
**Full name:** Happy-path scenario fixtures assert exact state oracles  
**Purpose:** Prove evaluation harness fixtures check exact state, not just pass/fail smoke  
**Source requirement:** R-T-06, R-E-01  
**Priority:** P0 — must pass for release

### What EVAL-01 expects to exist

> A valid scenario fixture exists. When the evaluation harness runs it,
> the fixture asserts exact values for: `current_player`,
> `history_length`, `finished`, and per-player occupied counts.

### Expected artifacts

| Artifact | Type | Expected location | What to check |
|----------|------|------------------|---------------|
| Happy-path scenario fixture | JSON or equivalent | `fixtures/` | File exists, contains scenario with expected oracle fields |
| Evaluation harness | Python script or test runner | `tests/` or `scripts/` | Can be invoked, reads fixtures, reports pass/fail |
| Oracle fields in fixture | Fields in JSON | Inside fixture file | `current_player`, `history_length`, `finished`, occupied counts all present |

### Specific oracle fields to verify

When you open a happy-path fixture file, it must contain
ALL of these fields in its expected-output section:

```
current_player: <player id>
history_length: <integer>
finished: <true/false>
<player>_occupied_count: <integer>  (one per player)
```

If any field is missing, EVAL-01 is ⚠️ Partial.

### Verification instructions for Owner 3

1. Navigate to `fixtures/` in the repository
2. Find at least one fixture file that represents a happy-path scenario
3. Open it and check for the 4 oracle field types listed above
4. Run the harness against it if possible: confirm it reports a result
5. Record what fields are present and what is missing

### Linked requirements
R-E-01, R-F-07, R-T-04, R-T-06

---

## Scenario 5: EVAL-02
**Full name:** Invalid-move scenario fixtures report execution failure detail  
**Purpose:** Prove negative-path fixtures are replayable and diagnosable  
**Source requirement:** R-T-06, R-E-01  
**Priority:** P0 — must pass for release

### What EVAL-02 expects to exist

> A scenario fixture containing an illegal move exists. When the harness
> runs it, the failure reports both the scenario name AND a concrete
> move-execution error detail (not just "failed").

### Expected artifacts

| Artifact | Type | Expected location | What to check |
|----------|------|------------------|---------------|
| Invalid-move scenario fixture | JSON or equivalent | `fixtures/` | File exists, contains a move that violates a game rule |
| Harness failure output | Console or log output | Runtime | Reports scenario name + specific error (e.g., "side-adjacency violation") |

### What "concrete error detail" means

A pass requires the error message to name the specific violation.
Examples of passing output:

- `"EVAL-02 FAILED: side-adjacency rule violated at (3,4)"`
- `"Scenario invalid_opening: move rejected — piece does not cover start corner"`

Examples of failing output (too vague):

- `"EVAL-02 FAILED"`
- `"Error: invalid move"`
- No output at all

### Verification instructions for Owner 3

1. Find a negative-path fixture in `fixtures/`
2. Run the harness against it
3. Read the output — does it name the scenario AND the specific rule?
4. If the fixture exists but the error output is generic, mark as ⚠️ Partial

### Linked requirements
R-E-01, R-R-03, R-T-06

---

## Scenario 6: EVAL-03
**Full name:** Expectation-mismatch fixtures report the mismatched oracle field  
**Purpose:** Distinguish bad engine behavior from bad expected data in test fixtures  
**Source requirement:** R-T-06, R-E-01  
**Priority:** P0 — must pass for release

### What EVAL-03 expects to exist

> A fixture with an intentionally wrong expected value exists.
> When the harness runs it, the failure output identifies WHICH field
> was wrong and shows the actual value the engine produced.

### Expected artifacts

| Artifact | Type | Expected location | What to check |
|----------|------|------------------|---------------|
| Oracle-mismatch fixture | JSON with intentionally wrong expected value | `fixtures/` | File exists, one expected field is intentionally wrong |
| Harness mismatch output | Console or log output | Runtime | Reports field name + expected value + actual value |

### What "identifies the mismatched field" means

Passing output example:

- `"EVAL-03 FAILED: current_player expected=2 actual=1"`
- `"Mismatch on field 'finished': expected=true, got=false"`

Failing output (too vague):

- `"EVAL-03 FAILED: oracle mismatch"`
- `"Test failed"`

### Verification instructions for Owner 3

1. Find a fixture in `fixtures/` where an expected value is deliberately wrong
2. Run the harness against it
3. Read the output — does it name the specific field and show actual vs expected?
4. If no such fixture exists at all, this is ❌ Broken (the fixture must be created)

### Linked requirements
R-E-01, R-T-04, R-T-06

---

---

# PART B — Sweep Result Tables

**Instructions for Owner 3:**
Fill in Status and Notes for every row after checking the repository.
Use the symbols from the reference guide at the top of this document.
When done, update the summary table at the bottom.

---

## Table B1 — TEST-05: Core Engine Validation Evidence

| # | Sub-scenario | Expected artifact | Expected path | Status | Actual path found | Notes |
|---|-------------|-------------------|--------------|--------|------------------|-------|
| 1 | VAL-01: Valid opening move accepted | Automated test | `tests/` | | | |
| 2 | VAL-02: Opening off start rejected | Automated test | `tests/` | | | |
| 3 | PERS-03: Apply then serialize round-trips | Test + fixture | `tests/` + `fixtures/` | | | |
| 4 | PERS-09: CLI chain is reproducible | Test or script | `tests/` or `scripts/` | | | |
| 5 | TEST-02: Harness replays deterministic fixtures | Harness + fixture | Harness entry + `fixtures/` | | | |
| 6 | PERS-01: Valid JSON state loads cleanly | Fixture + test | `fixtures/` | | | |

**TEST-05 overall status:** [ ] ✅ Resolved [ ] ⚠️ Partial [ ] ❌ Broken

---

## Table B2 — TEST-08: Evidence Links Stay Navigable

| # | Sub-scenario | Expected artifact | Expected path | Status | Actual path found | Notes |
|---|-------------|-------------------|--------------|--------|------------------|-------|
| 1 | TEST-06: Unvalidated AI output blocked | AI usage log entry | `docs/ai-usage.md` | | | |
| 2 | DOC-05: AI usage records complete | AI usage log (all 5 fields) | `docs/ai-usage.md` | | | |
| 3 | DOC-06: Major claims resolve | Docs with working links | `docs/` | | | |
| 4 | DOC-04: Guideline artifacts map to review work | Reviewing guideline files | `docs/` or root | | | |

**TEST-08 overall status:** [ ] ✅ Resolved [ ] ⚠️ Partial [ ] ❌ Broken

---

## Table B3 — DOC-06: Document Evidence Link Audit

| # | Document | Exists? | Links checked (3 per doc) | Links resolved | Status | Notes |
|---|----------|---------|--------------------------|---------------|--------|-------|
| 1 | `docs/traceability-matrix.md` | | | | | |
| 2 | `docs/requirements_source_matrix.md` | | | | | |
| 3 | `docs/evidence-log.md` | | | | | |
| 4 | `docs/ai-usage.md` | | | | | |
| 5 | `OWNERSHIP.md` | | | | | |
| 6 | `TEAM_SUMMARY.md` | | | | | |

**DOC-06 overall status:** [ ] ✅ Resolved [ ] ⚠️ Partial [ ] ❌ Broken

---

## Table B4 — EVAL-01: Happy-Path Fixture Oracle Fields

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | At least one happy-path fixture file exists in `fixtures/` | | |
| 2 | Fixture contains `current_player` field in expected output | | |
| 3 | Fixture contains `history_length` field in expected output | | |
| 4 | Fixture contains `finished` field in expected output | | |
| 5 | Fixture contains per-player occupied count field(s) | | |
| 6 | Harness can be invoked and reads this fixture | | |
| 7 | Harness reports pass/fail with scenario name | | |

**EVAL-01 overall status:** [ ] ✅ Resolved [ ] ⚠️ Partial [ ] ❌ Broken

---

## Table B5 — EVAL-02: Invalid-Move Fixture Error Detail

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | At least one invalid-move fixture exists in `fixtures/` | | |
| 2 | Fixture contains a move that violates a named game rule | | |
| 3 | Harness failure output includes scenario name | | |
| 4 | Harness failure output includes specific rule or location | | |
| 5 | Output is NOT just "failed" or "invalid move" (generic) | | |

**EVAL-02 overall status:** [ ] ✅ Resolved [ ] ⚠️ Partial [ ] ❌ Broken

---

## Table B6 — EVAL-03: Oracle-Mismatch Field Identification

| # | Check | Result | Notes |
|---|-------|--------|-------|
| 1 | At least one oracle-mismatch fixture exists in `fixtures/` | | |
| 2 | The fixture has an intentionally wrong expected value | | |
| 3 | Harness failure output names the specific field that mismatched | | |
| 4 | Output shows both expected value and actual value | | |
| 5 | Output is NOT just "oracle mismatch" (generic) | | |

**EVAL-03 overall status:** [ ] ✅ Resolved [ ] ⚠️ Partial [ ] ❌ Broken

---

---

# PART C — Gap Register

**Instructions:** After completing Part B, record every broken
or missing artifact here. This is the list Owner 2 will review
and the team will use to decide what to fix before release.

| Gap ID | Scenario | Missing artifact | Impact | Recommended action | Owner | Fixed? |
|--------|----------|-----------------|--------|-------------------|-------|--------|
| GAP-01 | | | | | | |
| GAP-02 | | | | | | |
| GAP-03 | | | | | | |
| GAP-04 | | | | | | |
| GAP-05 | | | | | | |

*Add rows as needed. Delete placeholder rows when done.*

**Impact levels:**
- **Blocker** — release gate cannot pass until this is fixed
- **High** — review-critical claim is unverifiable; must fix before submission
- **Medium** — partial evidence exists; needs strengthening
- **Low** — non-critical gap; acceptable to log and defer

---

---

# PART D — Sweep Summary (to be filled after Part B and C are complete)

**Sweep date:** _______________  
**Completed by:** Owner 3  
**Reviewed by:** Owner 2

| Scenario | Total checks | ✅ Resolved | ⚠️ Partial | ❌ Broken | 📋 Planned | Overall |
|----------|-------------|-----------|----------|---------|----------|---------|
| TEST-05 | 6 | | | | | |
| TEST-08 | 4 | | | | | |
| DOC-06 | 6 | | | | | |
| EVAL-01 | 7 | | | | | |
| EVAL-02 | 5 | | | | | |
| EVAL-03 | 5 | | | | | |
| **TOTAL** | **33** | | | | | |

### Release-gate verdict

- [ ] **GREEN** — All P0 scenarios (TEST-05, EVAL-01, EVAL-02, EVAL-03) are ✅ Resolved
- [ ] **AMBER** — Some P0 checks are ⚠️ Partial; gaps logged and assigned
- [ ] **RED** — One or more P0 checks are ❌ Broken; release blocked until fixed

### Unresolved gaps count

- Blocker gaps: ___
- High gaps: ___
- Medium gaps: ___
- Low gaps: ___

### Sign-off

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Owner 3 (sweep author) | | | |
| Owner 2 (reviewer) | | | |

---

---

# PART E — Harness Index Alignment Check

This section checks that the evaluation harness index (if it exists)
correctly lists and links all fixture files in scope.

**What the harness index should contain:**
A file (typically in `docs/` or the harness root) that lists:
- All fixture files by name and path
- The scenario ID each fixture supports
- Whether the fixture is automated (Yes/Partial/No)
- The requirement IDs the fixture covers

### Harness Index Verification Table

| # | Check | Status | Notes |
|---|-------|--------|-------|
| 1 | Harness index file exists | | |
| 2 | All fixture files in `fixtures/` are listed in the index | | |
| 3 | Every index entry has a scenario ID | | |
| 4 | Every index entry has at least one requirement ID | | |
| 5 | Automation status is recorded for each entry (Yes/Partial/No) | | |
| 6 | No fixture file exists in the repo that is NOT in the index | | |

**Harness index overall status:** [ ] ✅ Aligned [ ] ⚠️ Gaps found [ ] ❌ Index missing

---

---

# PART F — AI Usage Disclosure for This Sweep

This document was produced with help of AI assistance (Claude Sonnet 4.6).

| Field | Detail |
|-------|--------|
| Model | Claude Sonnet 4.6 |
| Task | Extract all scoped scenarios and expected artifacts from requirements_source_matrix.md; structure sweep template with verification instructions |
| Prompt category | Structured analysis — evidence extraction and traceability mapping |
| Input artifacts | requirements_source_matrix.md, requirements.md, task description |
| Validation method | Owner 3 must complete Part B by physically checking the repository; AI cannot access the repository |
| Adoption decision | Template is ready for use; Part B, C, D, E columns are blank and require human completion |

**Known limitation:**
This document pre-populates everything that can be derived from
the written documents. It cannot verify whether actual files exist
in the GitHub/GitLab repository. Part B is intentionally left blank
for Owner 3 to complete. The sweep is not done until Part D
(Summary) and Part C (Gap Register) are filled in and signed off
by Owner 2.

---

*Document version: 1.0 | Created: 2026-04-27 | Status: Awaiting Owner 3 repo verification*
