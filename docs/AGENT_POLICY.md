# Agent Policy

## Purpose

This document defines the Phase 3 trust boundary for repository automation. Agents may prepare, implement, and repair changes inside their own branch and pull request loop, but they do not replace protected-branch review, protected environments, or human approval.

## What Counts As Agent-Ready

An issue is agent-ready only when all of the following are true:

- the issue uses the structured agent or bug form
- the problem statement is specific
- acceptance criteria are explicit
- required tests are named
- rule ambiguity is marked `no ambiguity`
- the work does not require repository settings, secrets, or protected-environment authority

If those conditions are not met, the issue must be routed to `needs-human-spec`.

## Allowed Autonomous Actions

For agent-ready tasks, the agent may:

- create or update a dedicated `agent/*` branch
- modify code, tests, fixtures, schemas, and docs related to the issue
- open or update a pull request
- summarize CI failures on its own branch
- perform bounded repair on its own branch within the retry budget

## Prohibited Autonomous Actions

The agent may not:

- merge to `main`
- approve protected environments
- change branch protections, secrets, repository settings, or environment configuration
- invent game-rule semantics when requirements are ambiguous
- widen scope beyond the linked issue without escalation
- autonomously repair workflow-sensitive changes under `.github/`

## Labels And Workflow States

- `agent-ready`: structured enough for branch-level agent work
- `agent-in-progress`: an agent branch or PR is actively being worked
- `agent-blocked`: automation stopped and needs human intervention
- `needs-human-spec`: requirements or ambiguity still need human clarification
- `repair-loop`: the PR is inside the bounded autonomous repair loop
- `needs-review`: a human review checkpoint is needed
- `rules`, `cli`, `tests`, `fixtures`, `schemas`, `docs`, `ci`: impacted domain labels
- `safe-autonomy`: autonomy is allowed inside the issue or PR branch loop
- `workflow-sensitive`: `.github/` or automation-sensitive paths are involved
- `human-gate-required`: agent work may draft changes, but humans must explicitly gate progress

## Agent Task Contract

Every agent-ready task uses the same contract:

- keep changes scoped to the linked issue
- explain assumptions in the pull request
- update tests for behavior changes
- stop and escalate if ambiguity is detected
- stay inside the branch and pull-request path

## Sensitive Files

The following areas are treated as sensitive for autonomous repair:

- `.github/`
- `OWNERSHIP.md`
- `TEAM_SUMMARY.md`
- `docs/AGENT_POLICY.md`

Agents may help draft changes in these areas when humans ask for them, but the bounded repair loop does not patch them automatically.

## Repair Policy

Autonomous repair is allowed only when all of the following are true:

- the branch name starts with `agent/`
- the pull request is not labeled `workflow-sensitive`
- the pull request is not labeled `needs-human-spec`
- the pull request is not labeled `human-gate-required`
- the failure category is one of `lint`, `unit-test`, `cli-smoke`, or `fixture-schema`
- the retry budget is not exhausted

Retry budget:

- maximum retries: `2`
- after retry `2`, automation must stop and escalate

Current bounded actions:

- `lint`: attempt a deterministic `ruff --fix` patch, then push back to the same branch if changes were produced
- `unit-test`, `cli-smoke`, `fixture-schema`: rerun failed CI jobs inside the retry budget
- `evaluate`, `environment`, and `unknown`: escalate immediately

## Escalation Policy

Autonomy must stop and route back to humans when any of the following are true:

- `needs-human-spec` is present
- retry budget is exhausted
- failure category is `unknown`
- failure category is `evaluate`
- workflow-sensitive files changed
- the issue or PR widens scope beyond the linked task
- the agent needs settings, permissions, or secret changes to proceed

When escalation happens, workflows should:

- add `agent-blocked`
- add `needs-review`
- remove or avoid `repair-loop`
- post a comment that explains why autonomy stopped

## Human Approval Boundaries

Humans still approve:

- all merges to `main`
- changes that cross workflow or repository-governance boundaries
- protected-environment approvals for `rc` and `submission`
- any rule interpretation not already made explicit in the requirements or issue
