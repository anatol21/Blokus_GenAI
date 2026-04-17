# Repository instructions for GitHub Copilot

This repository uses plain Python with reproducible shell-script entrypoints. Prefer the documented project commands instead of inventing one-off setup or validation steps.

## Working style

- Keep changes scoped to the linked issue or pull request.
- Do not suggest or perform direct pushes to `main`.
- Assume all changes reach `main` through a pull request with human review.
- Preserve the current trust boundaries around protected branches and protected environments.

## Validation

Use the repository scripts whenever they are relevant:

- `./scripts/install.sh`
- `./scripts/test.sh`
- `./scripts/cli_smoke.sh`
- `./scripts/validate_fixtures.sh`
- `./scripts/evaluate.sh`

If you change code, tests, fixtures, schemas, or CLI behavior, prefer the matching script rather than an ad hoc command.

## Repository priorities

- Keep behavior deterministic and reproducible.
- Keep fixtures and schemas aligned with implementation changes.
- Update tests for behavior changes.
- Update documentation when contracts, release flow, or operational expectations change.
- Call out assumptions clearly in pull requests, especially around rule behavior.

## Sensitive boundaries

- Do not relax branch protection, environment approval, or review requirements.
- Do not introduce secrets, tokens, or copied credentials into code, docs, logs, or artifacts.
- Treat `.github/`, workflow permissions, release policy, and incident policy as sensitive and human-gated.
- Do not introduce new third-party GitHub Actions without explicit human approval.

## Current merge gates on `main`

The required checks on `main` are:

- `lint`
- `test`
- `cli-smoke`
- `fixture-schema`
- `evaluate`

Additional security-oriented checks may also run, including CodeQL and dependency review.
