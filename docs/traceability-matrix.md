# Traceability Matrix

This matrix links each requirement ID to planned or existing issues, repository artifacts, verification points, and evidence locations.

Issue references (`I-01` ... `I-22`) map to drafts in `docs/issue-seed.md` when live issue creation is unavailable.

## Functional requirements

| Requirement ID | Related issue(s) | Related file(s) | Related test(s) | Related evidence |
| --- | --- | --- | --- | --- |
| R-F-01 | I-04, I-05, I-06 | `src/blokus/config.py`, `src/blokus/engine.py` | `tests/test_engine.py`, `tests/test_serialization.py` | `docs/evidence-log.md` |
| R-F-02 | I-12 | `src/blokus/cli.py` | `tests/test_cli.py` | `README.md`, `docs/evidence-log.md` |
| R-F-03 | I-11, I-19 | `src/blokus/models.py`, `schemas/game_state.schema.json` | `tests/test_serialization.py`, `tests/test_cli.py` | `fixtures/states/classic_initial.json` |
| R-F-04 | I-08 | `src/blokus/engine.py`, `src/blokus/models.py` | `tests/test_engine.py` | `docs/evidence-log.md` |
| R-F-05 | I-09 | `src/blokus/engine.py`, `docs/test_execution_matrix.md` | `tests/test_engine.py`, `tests/test_evaluate.py` | `docs/evidence-log.md`, `docs/test_execution_matrix.md` (`LIFE-01`, `LIFE-02`) |
| R-F-06 | I-10 | `src/blokus/engine.py` | `tests/test_ai.py` | `docs/evidence-log.md` |
| R-F-07 | I-11 | `src/blokus/models.py`, `src/blokus/cli.py` | `tests/test_serialization.py`, `tests/test_cli.py` | `docs/json-contracts.md` |
| R-F-08 | I-12 | `src/blokus/cli.py` | `tests/test_cli.py` | `README.md` |
| R-F-09 | I-12 | `src/blokus/players.py` | `tests/test_ai.py` | `docs/evidence-log.md` |
| R-F-10 | I-08, I-22 | `src/blokus/engine.py` | `tests/test_engine.py`, `tests/test_evaluate.py` | `docs/review-guidelines.md` |
| R-F-11 | I-05, I-16 | `src/blokus/config.py` | `tests/test_engine.py`, `tests/test_evaluate.py` | `fixtures/scenarios/classic_corner_sequence.json` |
| R-F-12 | I-06 | `src/blokus/config.py`, `schemas/mode_config.schema.json` | `tests/test_duo_config.py` (planned) | `docs/evidence-log.md` |
| R-F-13 | I-07, I-14 | `src/blokus/pieces.py` | `tests/test_pieces.py` | `docs/evidence-log.md` |
| R-F-14 | I-04, I-06 | `src/blokus/config.py`, `src/blokus/engine.py` | `tests/test_engine.py`, `tests/test_duo_config.py` (planned) | `docs/architecture.md` |

## Non-functional requirements

| Requirement ID | Related issue(s) | Related file(s) | Related test(s) | Related evidence |
| --- | --- | --- | --- | --- |
| R-NF-01 | I-16 | `tests/`, `scripts/test.sh` | `python -m unittest discover -s tests -v` | `.github/workflows/ci.yml` |
| R-NF-02 | I-16 | `scripts/install.sh`, `scripts/test.sh`, `scripts/evaluate.sh` | `tests/test_evaluate.py` | `docs/evidence-log.md` |
| R-NF-03 | I-02, I-20 | `OWNERSHIP.md`, `docs/traceability-matrix.md`, `docs/issue-seed.md` | review-based | `docs/evidence-log.md` |
| R-NF-04 | I-01, I-04 | `docs/requirements.md`, `src/blokus/engine.py` | `tests/test_engine.py` | `README.md` |
| R-NF-05 | I-18, I-20 | `docs/evidence-log.md`, `docs/traceability-matrix.md` | review-based | PR evidence sections |

## Constraints and exclusions

| Requirement ID | Related issue(s) | Related file(s) | Related test(s) | Related evidence |
| --- | --- | --- | --- | --- |
| R-C-01 | I-17 | `docs/ai-usage.md`, `pyproject.toml` | dependency inspection | `docs/evidence-log.md` |
| R-C-02 | I-01 | `docs/requirements.md` | review-based | `README.md` |
| R-C-03 | I-01 | `docs/requirements.md`, `src/blokus/players.py` | `tests/test_ai.py` | `docs/evidence-log.md` |
| R-C-04 | I-01 | `docs/requirements.md` | review-based | `README.md` |

## Documentation requirements

| Requirement ID | Related issue(s) | Related file(s) | Related test(s) | Related evidence |
| --- | --- | --- | --- | --- |
| R-D-01 | I-03 | `TEAM_SUMMARY.md` | review-based | PR references |
| R-D-02 | I-02 | `OWNERSHIP.md` | review-based | PR references |
| R-D-03 | I-03 | `Portfolio_TEMPLATE.md` | review-based | portfolio links (later) |
| R-D-04 | I-02 | `OWNERSHIP.md`, `docs/evidence-log.md` | review-based | package ownership evidence |
| R-D-05 | I-21 | `docs/review-guidelines.md` | review-based | review notes |
| R-D-06 | I-18 | `docs/evidence-log.md` | fixture replay | counterexample records |
| R-D-07 | I-21 | `docs/review-guidelines.md` | review-based | PR checklist |
| R-D-08 | I-21, I-22 | `docs/review-example-problems.md`, `docs/review-evaluation.md` | review-based | review records |
| R-D-09 | I-21 | `docs/review-evaluation.md` | review-based | final report references |
| R-D-10 | I-17 | `docs/ai-usage.md` | review-based | AI log entries |

## Evaluation requirements

| Requirement ID | Related issue(s) | Related file(s) | Related test(s) | Related evidence |
| --- | --- | --- | --- | --- |
| R-E-01 | I-16 | `src/blokus/evaluate.py` | `tests/test_evaluate.py` | `scripts/evaluate.sh` output |
| R-E-02 | I-16, I-06 | `src/blokus/evaluate.py`, `fixtures/` | `tests/test_evaluate.py`, Duo tests (planned) | `docs/evidence-log.md` |
| R-E-03 | I-06, I-20 | `docs/requirements.md`, `docs/traceability-matrix.md` | review-based | evolution notes (later) |
| R-E-04 | I-17, I-18 | `docs/ai-usage.md`, `docs/evidence-log.md` | review-based | report artifacts (later) |
| R-E-05 | I-17, I-22 | `docs/ai-usage.md`, PR template | review-based | validation notes |

## Reproducibility requirements

| Requirement ID | Related issue(s) | Related file(s) | Related test(s) | Related evidence |
| --- | --- | --- | --- | --- |
| R-R-01 | I-16 | `scripts/install.sh`, `scripts/test.sh`, `scripts/run_demo.sh` | CI and local runs | `.github/workflows/ci.yml` |
| R-R-02 | I-18 | `docs/evidence-log.md` | review-based | evidence log entries |
| R-R-03 | I-18, I-22 | `docs/evidence-log.md`, `docs/review-example-problems.md` | fixture reproduction | counterexample entries |
| R-R-04 | I-17 | `docs/ai-usage.md` | review-based | AI log entries |

## Testing and validation requirements

| Requirement ID | Related issue(s) | Related file(s) | Related test(s) | Related evidence |
| --- | --- | --- | --- | --- |
| R-T-01 | I-16 | `tests/` | `python -m unittest discover -s tests -v` | CI logs |
| R-T-02 | I-14 | `tests/test_engine.py`, `tests/test_pieces.py` | existing suite | `docs/evidence-log.md` |
| R-T-03 | I-06, I-16 | `fixtures/`, `src/blokus/evaluate.py` | Duo coverage (planned) | `docs/requirements.md` |
| R-T-04 | I-08, I-09, I-11, I-15 | `src/blokus/engine.py`, `src/blokus/models.py`, `docs/test_execution_matrix.md` | `tests/test_engine.py`, `tests/test_serialization.py` | fixture and test outputs, `docs/evidence-log.md`, `docs/test_execution_matrix.md` (`LIFE-01`, `LIFE-02`, `VAL-05`) |
| R-T-05 | I-17, I-22 | `docs/ai-usage.md`, `.github/pull_request_template.md` | review-based | AI validation entries |
| R-T-06 | I-13 | `fixtures/`, `tests/test_evaluate.py` | fixture-backed harness | `fixtures/scenarios/classic_corner_sequence.json` |
