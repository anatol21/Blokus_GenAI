# Phase 1 Governance Foundation

This note captures the Phase 1 audit snapshot, the repository-side changes made in this workspace, and the remaining GitHub settings required to finish the governance baseline.

Temporary validation branch note: used to confirm Phase 1 review routing after protections were enabled.

## Audit snapshot

Audit date: `2026-04-07`

- [x] `.github/workflows/ci.yml` present
- [x] `.github/pull_request_template.md` present
- [ ] `.github/CODEOWNERS` present on `main`
- [ ] `main` protection active
- [ ] `rc` environment exists
- [ ] `submission` environment exists

Observed live repository state during the audit:

- `main` is currently unprotected (`protected: false`) via `GET /repos/anatol21/Blokus_GenAI/branches/main` on `2026-04-07`.
- No environments currently exist (`total_count: 0`) via `GET /repos/anatol21/Blokus_GenAI/environments` on `2026-04-07`.
- The latest successful `main` CI run inspected was Actions run `23662240365` from `2026-03-27`, and its single job name is `test`.
- Collaborator permissions were verified for the temporary CODEOWNERS reviewers:
  - `@anatol21`: `admin`
  - `@magx27`: `write`
  - `@Nicotico2000`: `write`

## Repo changes completed in this workspace

- Added `.github/CODEOWNERS` with a temporary all-team ownership map for the key Phase 1 paths.
- Kept the path-specific entries even though ownership is broad for now, so future tightening is a small diff instead of a restructure.
- Added this runbook so the remaining GitHub-side controls can be applied consistently.

## Apply the remaining GitHub controls

### 1. Merge `CODEOWNERS`

Open a PR and merge `.github/CODEOWNERS` into `main` before turning on required code-owner review.

### 2. Protect `main`

Create a branch protection rule for `main` with these settings:

- Require a pull request before merging: on
- Required approvals: `1`
- Dismiss stale pull request approvals when new commits are pushed: on
- Require review from Code Owners: on
- Require status checks to pass before merging: on
- Require conversation resolution before merging: on

### 3. Select the required check

Use the real CI job name currently emitted by `.github/workflows/ci.yml`:

- Required check: `test`

Notes:

- The repository currently has one merge-critical CI job, `test`, under the `CI` workflow.
- Do not mark `Seed Issues And Labels` as required for `main`; it is repository-maintenance automation, not merge readiness.

### 4. Create protected environments

Create these environments in GitHub settings:

- `rc`
- `submission`

Use these settings for both:

- Required reviewers: `@anatol21`, `@magx27`, `@Nicotico2000`
- Prevent self-review: on

Operational note:

- Only one reviewer approval is required for an environment-gated job to continue, so in practice the author should wait for one of the other two teammates to approve.

## Dry-run validation

After the GitHub settings above are applied, validate the controls with these checks:

### Review gate

1. Create a branch from `main`.
2. Change a file under an owned path such as `docs/` or `tests/`.
3. Open a PR to `main`.
4. Confirm code owners are auto-requested.
5. Confirm merge is blocked before approval.

### Status-check gate

1. Push a deliberate CI-breaking change on a test branch.
2. Open a PR to `main`.
3. Confirm merge is blocked while the required `test` check fails.

### Stale approval invalidation

1. Open a PR.
2. Obtain one approval.
3. Push another commit to the same branch.
4. Confirm the previous approval is dismissed.

### Environment approval

1. Reference `environment: rc` or `environment: submission` from a later workflow.
2. Trigger that workflow.
3. Confirm the job pauses for reviewer approval before continuing.

## Follow-up reminder

- [ ] Create a follow-up issue to replace the temporary all-team CODEOWNERS rules with narrower path owners once module ownership is finalized.
