# GitHub CI/CD Guide

This guide is the day-to-day operating manual for teammates working in this repository through GitHub. It reflects the live repository controls as of April 7, 2026.

## Core rules

- Never push directly to `main`.
- Every change reaches `main` through a pull request.
- Normal development follows the review gates. Admin bypass is not part of the normal development workflow.
- Human branches should use `codex/...` or another descriptive feature branch. The `agent/*` prefix is reserved for autonomous branch work.
- Treat `.github/`, secrets, branch protections, and environment settings as sensitive. Those changes need extra human review.

## What GitHub enforces today

- `main` requires a pull request.
- `main` requires `1` human approval.
- Code-owner review is required when the changed paths are owned in `.github/CODEOWNERS`.
- Approvals are dismissed when new commits are pushed.
- Conversation resolution is required before merge.
- The required merge-gate checks on `main` are: `lint`, `test`, `cli-smoke`, `fixture-schema`, and `evaluate`.
- Additional checks may run on top of the merge gate, including `analyze (python)` from CodeQL and `dependency-review` when dependency manifests change.

## Start work

1. Open an issue or pick an existing one.
2. Use the structured issue forms when possible.
3. If the task is suitable for agent work, make sure the issue is precise enough to become `agent-ready`.
4. Create a branch from `main`.
5. Keep the branch scoped to the issue.

Good local commands before you push:

- `./scripts/install.sh`
- `./scripts/test.sh`
- `./scripts/cli_smoke.sh`
- `./scripts/validate_fixtures.sh`
- `./scripts/evaluate.sh`

## Open a pull request

When you open a PR:

- link the issue
- fill in the PR template
- explain assumptions clearly
- call out dependency changes, schema changes, docs changes, or workflow changes explicitly
- confirm that no secret material was introduced

The repository will automatically add review guidance:

- `pr-intelligence` posts a review summary comment
- workflow-sensitive PRs get `workflow-sensitive`
- sensitive PRs also get `needs-review`

## How to read CI

The main CI workflow runs these jobs:

- `lint`: fast style and import checks
- `test`: unit and integration tests
- `cli-smoke`: command-line surface sanity check
- `fixture-schema`: JSON fixture and schema validation
- `evaluate`: fixture-backed evaluation harness

If CI fails:

1. Open the PR Checks tab.
2. Look at the first failed job, not only the overall red X.
3. Read the job logs.
4. Download any uploaded failure artifacts if they exist.
5. Fix the narrowest cause first.

Failure artifacts currently use short retention windows:

- CI debug artifacts: `14` days
- governance-review artifacts: `30` days
- release-candidate and submission artifacts: `90` days

## Security and supply chain checks

The repository now has these GitHub-side protections enabled:

- secret scanning
- push protection
- vulnerability alerts
- Dependabot security updates
- CodeQL scanning

Important consequences:

- pushes that include detected secrets may be blocked
- dependency changes are visible and reviewable
- new third-party GitHub Actions should not be introduced casually
- default `GITHUB_TOKEN` permissions are read-only unless a workflow job explicitly asks for more

## What agents read

The repository now includes explicit guidance files for GitHub Copilot and repository agents:

- `.github/copilot-instructions.md`: repo-wide coding and validation guidance
- `AGENTS.md`: agent-specific operating rules and hard stops
- `.github/instructions/workflows.instructions.md`: extra rules for workflow, policy, and release-boundary files
- `.github/instructions/rules.instructions.md`: extra rules for engine, tests, fixtures, and schemas

If you open a task for agent work, assume those files are part of the agent's working context.

## Agent workflow expectations

Agent work is allowed only inside the documented branch and PR loop.

Use `docs/AGENT_POLICY.md` for the exact rules, but the short version is:

- `agent-ready` means the issue is structured enough for bounded agent work
- `needs-human-spec` means humans need to clarify the task before an agent should implement it
- autonomous repair is limited and only applies on `agent/*` branches
- workflow-sensitive changes stay human-gated

If you are unsure whether a task belongs with an agent, default to human-led clarification first.

## Merge process

A normal merge to `main` should happen only when:

- required checks are green
- the right reviewer has approved
- unresolved conversations are closed
- the PR scope is still aligned with the linked issue

Do not use admin bypass for normal feature, bug-fix, docs, or test work.

## What happens after merge

After a PR merges into `main`:

1. the `release-candidate` workflow starts automatically
2. the repository packages a release candidate
3. release notes, evidence, and provenance are generated
4. the workflow pauses at the protected `rc` environment
5. after human approval, GitHub can publish the pre-release

Final publication is separate:

1. a human manually runs `promote-submission`
2. the workflow pauses at the protected `submission` environment
3. after approval, the final GitHub Release is published

## Who approves what

- Normal PR merge: at least one human reviewer, plus code-owner coverage where applicable
- `rc`: one configured reviewer in the `rc` environment; self-review is blocked
- `submission`: one configured reviewer in the `submission` environment; self-review is blocked

Operationally, the PR author should not be the release approver.

## When to stop and ask for help

Stop and escalate when:

- rules semantics are unclear
- the task needs secrets, settings, or workflow-permission changes
- CI is failing for a reason you cannot classify quickly
- a repair loop keeps repeating without progress
- release artifacts or provenance do not look right

Use these docs when that happens:

- `docs/AGENT_POLICY.md`
- `docs/RELEASE_POLICY.md`
- `docs/PIPELINE_SECURITY.md`
- `docs/INCIDENT_RESPONSE.md`
- `docs/AUTONOMY_SCORECARD.md`

## Suggested team habit

For each PR review, ask the same quick questions:

- Does this PR match the issue?
- Are the right tests updated?
- Are any workflow or contract changes hidden in the diff?
- Would I be comfortable approving the resulting release candidate if this merged today?
