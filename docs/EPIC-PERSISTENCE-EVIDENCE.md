# Planning Card: Persistence, Replay, and Evidence Governance

| Attribute | Value |
| --- | --- |
| **Epic Title** | Serialization, Persistence, Replay, Harness, and Evidence Governance |
| **Assignee** | Owner 3 |
| **Reviewer** | Owner 2 |
| **Status** | Active / Planning |
| **Linked Requirements** | R-F-03, R-F-07, R-F-21, R-F-39, R-F-40, R-NF-01, R-NF-05, R-R-03, R-T-01, R-T-04, R-T-06, R-E-01, R-E-04, R-E-05 |
| **Linked Scenarios** | PERS-01, PERS-03, PERS-04, PERS-05, PERS-10, EVAL-01, EVAL-02, EVAL-03 |

## Purpose
Group all requirement-level concerns around save/load integrity, replayability, deterministic fixtures, harness repeatability, and evidence traceability so that persistence and proof obligations stay coordinated.

## Oracle and Governance
- **Traceability**: Persistence and evidence requirements are traceable to executable scenarios in `docs/test_execution_matrix.md`.
- **Determinism**: Deterministic fixture use is explicit (see `fixtures/` directory).
- **Separation of Concerns**: Audit-oriented expectations (e.g., proof of AI usage, review logs) are not confused with engine-behavior requirements (e.g., move legality).

## Requirements Source Matrix (Traceability)

| ID | User Story Summary | Status |
| --- | --- | --- |
| **R-F-03** | Load game states from JSON for quick scenario reproduction. | **Executable** |
| **R-F-07** | State serialization to save and verify outcomes. | **Executable** |
| **R-F-21** | Automatic save-and-resume support for interrupted sessions. | **Executable** |
| **R-F-39** | Move/Game replay for strategy inspection and rule clarity. | **Executable** |
| **R-F-40** | Highlight key moments in move history for efficient analysis. | **Planning/UI** |
| **R-NF-01** | Testable architecture to ensure regressions are catchable. | **Executable** |
| **R-NF-05** | Evidence-linked claims for fast and objective verification. | **Process** |
| **R-R-03** | Reproducible failure cases for replaying regressions. | **Executable** |
| **R-T-01** | Automated tests for continuous regression checking. | **Executable** |
| **R-T-04** | Explicit validation artifacts to prove critical engine behavior. | **Executable** |
| **R-T-06** | Repeatable fixtures to keep tests deterministic and debuggable. | **Executable** |
| **R-E-01** | Evaluation harness for repeatable quality checks. | **Executable** |
| **R-E-04** | Evidence-backed retrospection for testable process claims. | **Process** |
| **R-E-05** | Evidence-based AI claims for trustworthy assertions. | **Process** |

## Test Execution Matrix (Persistence & Evidence Scenarios)

| Scenario ID | Primary Requirement | Fixture / Dependency | Oracle / Expected Outcome |
| --- | --- | --- | --- |
| **PERS-01** | R-F-03, R-F-07 | `classic_initial.json` | Round-trip consistency: `from_dict(to_dict(state))` preserves all fields. |
| **PERS-03** | R-F-03, R-R-03 | Corrupted board payload | Loader rejects malformed row counts/lengths cleanly. |
| **PERS-04** | R-F-03, R-R-03 | Mismatched player payload | Loader rejects identity drift (mismatched players/corners). |
| **PERS-05** | R-F-03, R-F-07 | Corrupted rack payload | Loader rejects unknown or duplicated remaining pieces. |
| **PERS-10** | R-F-07, R-R-03 | `classic_spent_piece_reuse_counterexample.json` | Replay fails with spent-piece-unavailable reason; regression asset is repeatable. |
| **EVAL-01** | R-E-01, R-T-06 | `classic_corner_sequence.json` | Harness passes only when exact expected state fields are met. |
| **EVAL-02** | R-E-01, R-R-03 | `classic_invalid_opening_move.json` | Harness returns `passed=false` with actionable failure detail for illegal moves. |
| **EVAL-03** | R-E-01, R-T-04 | `classic_expectation_mismatch.json` | Harness reports mismatched oracle field vs actual engine value. |

## Dependencies & Fixture Governance
- **Baseline**: `fixtures/states/classic_initial.json` serves as the root for all Classic mode sessions.
- **Failures**: `fixtures/scenario_failures/` contains deterministic "counterexample" payloads used to prove regression fixes.
- **Harness**: `scripts/evaluate.sh` (or `python -m blokus evaluate`) is the canonical entry point for repeatable quality checks.
- **Evidence**: `docs/evidence-log.md` and `docs/ai-usage.md` provide the audit trail for development process claims.

## Checklist
- [x] Confirm persistence, replay, harness, and evidence requirements are grouped intentionally
- [x] Verify every linked execution scenario has a clear fixture and evidence path
- [x] Identify requirement statements that are still planning-only versus executable-now
- [x] Check that counterexample replay and evidence-link expectations are explicitly covered
- [x] Note any missing fixture or evidence-governance dependencies
- [x] Update epic notes with links to execution scenarios and documentation paths
