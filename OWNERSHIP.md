# Ownership

Ownership below is derived from current repository contribution history and should be updated if the team reassigns areas.

| Package / Area | Primary owner | Reviewer | Acceptance basis | Evidence |
| --- | --- | --- | --- | --- |
| Engine core (`src/blokus/engine.py`, `src/blokus/models.py`, `src/blokus/pieces.py`) | Anatole | Maximilian Alp Grueder | Rules pass required tests and satisfy mapped requirements (`R-F-01`, `R-F-04`, `R-F-05`, `R-F-06`, `R-F-10`, `R-F-13`, `R-F-14`) | `tests/test_engine.py`, `tests/test_pieces.py`, `docs/traceability-matrix.md` |
| CLI (`src/blokus/cli.py`, `src/blokus/render.py`) | Anatole | Maximilian Alp Grueder | CLI commands match documented contracts and handle success/failure paths (`R-F-02`, `R-F-03`, `R-F-07`) | `tests/test_cli.py`, `README.md`, `docs/json-contracts.md` |
| Tests / fixtures (`tests/`, `fixtures/`) | Anatole | Maximilian Alp Grueder | Core legality, transforms, and serialization remain reproducible (`R-T-01`, `R-T-02`, `R-T-04`, `R-T-06`) | `scripts/test.sh`, `tests/test_serialization.py`, `fixtures/` |
| Documentation (`docs/`, `README.md`, `TEAM_SUMMARY.md`) | Anatole | Maximilian Alp Grueder | Requirements, architecture, traceability, and review docs are current and internally consistent (`R-D-*`, `R-NF-03`, `R-NF-05`) | `docs/requirements.md`, `docs/architecture.md`, `docs/traceability-matrix.md` |
| Reproducibility / scripts (`scripts/`, `.github/workflows/ci.yml`) | Anatole | Maximilian Alp Grueder | Fresh setup can run install, tests, and evaluation in CI and locally (`R-R-01`, `R-NF-01`, `R-NF-02`) | `scripts/install.sh`, `scripts/test.sh`, `scripts/evaluate.sh`, `.github/workflows/ci.yml` |
| Review / evidence (`docs/review-*.md`, `docs/evidence-log.md`, `docs/ai-usage.md`) | Anatole | Maximilian Alp Grueder | Human review and evidence logging are visible for merged changes (`R-D-07`, `R-D-08`, `R-E-05`, `R-T-05`) | PR checklist, `docs/evidence-log.md`, `docs/ai-usage.md` |

## Working agreement

- Every merged change should have one primary owner and one reviewer.
- Reviewer should not be the same person as primary owner.
- Acceptance basis must reference requirement IDs and at least one executable or inspectable artifact.
