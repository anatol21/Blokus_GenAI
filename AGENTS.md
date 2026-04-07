# Agent Instructions

These instructions are for AI agents working in this repository.

## Scope and branch rules

- Work only on issue-scoped branches.
- The `agent/*` prefix is reserved for autonomous branch work.
- Never merge to `main`.
- Never bypass pull-request review or protected-environment approval.
- Keep changes tightly scoped to the linked issue.

## What to read first

Before making changes, ground yourself in the repository documents that match the task:

- `docs/requirements.md`
- `docs/AGENT_POLICY.md`
- `docs/RELEASE_POLICY.md`
- `docs/PIPELINE_SECURITY.md`
- `docs/GITHUB_CICD_GUIDE.md`

Use the smallest relevant context bundle rather than loading every document at once.

## Validation commands

Use the repository scripts as the canonical validation surface:

- `./scripts/install.sh`
- `./scripts/test.sh`
- `./scripts/cli_smoke.sh`
- `./scripts/validate_fixtures.sh`
- `./scripts/evaluate.sh`

## Hard stops

Stop and escalate instead of guessing when any of the following are true:

- rule semantics are ambiguous
- the task needs repository settings, secrets, branch protection, or environment changes
- `.github/` changes would widen permissions or alter trust boundaries
- the task wants to widen scope beyond the linked issue
- release artifacts, evidence, or provenance do not match expectations

## Sensitive areas

Treat these as human-gated:

- `.github/`
- `scripts/github/`
- `docs/AGENT_POLICY.md`
- `docs/PIPELINE_SECURITY.md`
- `docs/INCIDENT_RESPONSE.md`
- `docs/RELEASE_POLICY.md`
- `docs/RELEASE_CONTENTS.md`

## Delivery boundaries

- `rc` and `submission` approvals are always human decisions.
- Release automation may package artifacts, but humans approve publication.
- Never invent a workflow or secret change to "make CI pass."
