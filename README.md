# Blocus Focus Pokus

Plain-Python Blokus project repository for course delivery. Phase 1 targets Classic as a stable baseline. Phase 2 extends the same engine to Duo through mode configuration. Phase 3 adds structured issue intake, PR intelligence, and bounded branch-level agent repair. Phase 4 adds release-candidate packaging and protected-environment delivery gates.

## Project purpose

- Implement a configurable Blokus engine in plain Python.
- Provide a minimal CLI for state creation, validation, application, legal-move listing, and serialization.
- Maintain testability, reproducibility, and traceable documentation/evidence.
- Use GitHub Issues for execution tracking while keeping stable requirements in Markdown.

## Phase scope

- Phase 1 baseline: Classic mode, 4 players, JSON state I/O, legality checks, move application, legal-move generation, simple computer player, tests, and fixtures.
- Phase 2 direction: Duo mode by configuration in the same engine (`ModeConfig` extension + tests/fixtures), not by a separate engine.
- Phase 3 direction: structured issue forms, label-driven agent entry, PR review intelligence, and bounded autonomous repair on `agent/*` branches.
- Phase 4 direction: automated release-candidate packaging, evidence bundles, GitHub pre-releases, and protected `rc` / `submission` approval gates.

## Repository structure

- `src/blokus/`: engine, models, piece transforms, CLI, rendering, evaluation harness, optional GUI.
- `tests/`: automated `unittest` coverage for rules, transforms, serialization, CLI, AI move selection, and evaluation scenarios.
- `fixtures/`: repeatable JSON fixtures for states and scenarios.
- `scripts/`: reproducible install/test/evaluate/run entry points plus CI smoke and fixture validation helpers.
- `schemas/`: JSON contracts for game state, move, and mode configuration.
- `docs/`: requirements, architecture, contracts, review discipline, traceability, issue seeds, evidence, and AI usage logs.
- `.github/workflows/ci.yml`: CI lint + test + CLI smoke + fixture/schema + evaluation pipeline.
- `.github/workflows/release-candidate.yml`: release-candidate packaging and protected `rc` publication flow.
- `.github/workflows/promote-submission.yml`: manual promotion through the protected `submission` gate.
- `.github/pull_request_template.md`: merge checklist with requirements/evidence/review gates.
- `.github/ISSUE_TEMPLATE/`: structured issue intake for agent tasks, bugs, and rule ambiguity.
- `.github/CODEOWNERS`: review routing for owned paths and governance checks.
- `.github/labels.yml`: normalized label definitions for issue workflow.

## Requirements and tracking workflow

- Stable requirements baseline: `docs/requirements.md`.
- Execution tracking: GitHub Issues (or fallback drafts in `docs/issue-seed.md`).
- Traceability: `docs/traceability-matrix.md` links requirements to issues, code, tests, and evidence.
- Ownership: `OWNERSHIP.md`.
- Team/report snapshot: `TEAM_SUMMARY.md`.
- Phase 1 governance setup: `docs/phase1-governance.md`.
- Phase 3 policy and autonomy boundary: `docs/AGENT_POLICY.md`.
- Release contents and policy: `docs/RELEASE_CONTENTS.md`, `docs/RELEASE_POLICY.md`.
- Evidence: `docs/evidence-log.md`.
- AI usage disclosure: `docs/ai-usage.md`.

## Quick start (plain Python)

```bash
./scripts/install.sh
./scripts/test.sh
./scripts/evaluate.sh
```

Optional run paths:

```bash
./scripts/run_demo.sh
./scripts/run_gui.sh
```

Without a virtual environment, commands also work with `PYTHONPATH=src`.

## CLI examples

Create a new state:

```bash
python -m blokus new --mode classic --output /tmp/classic.json
```

Validate a move:

```bash
python -m blokus validate --state /tmp/classic.json --piece I1 --x 0 --y 0
```

Apply a move:

```bash
python -m blokus apply --state /tmp/classic.json --piece I1 --x 0 --y 0 --output /tmp/classic.json
```

List legal moves:

```bash
python -m blokus legal-moves --state /tmp/classic.json --limit 10
```

Render state:

```bash
python -m blokus show --state /tmp/classic.json
```

## Testing and reproducibility

- Unit tests: `./scripts/test.sh`
- CLI smoke checks: `./scripts/cli_smoke.sh`
- Fixture/schema validation: `./scripts/validate_fixtures.sh`
- Fixture-backed evaluation harness: `./scripts/evaluate.sh`
- CI workflow: `.github/workflows/ci.yml`
- Repeatable inputs: `fixtures/states/` and `fixtures/scenarios/`

## Additional notes

- Rule-source notes: `docs/rule-sources.md`
- GUI manual checklist: `docs/gui_manual.md`
- Legacy reviewing files (`TOPIC-REVIEWING_*.md`) are retained; canonical review package now lives in `docs/review-*.md`.
