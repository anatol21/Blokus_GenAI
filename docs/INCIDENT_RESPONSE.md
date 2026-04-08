# Incident Response

This document defines how the team pauses, diagnoses, and recovers from autonomy incidents without shutting down the whole repository.

## What Counts As An Autonomy Incident

Treat any of the following as an autonomy incident:

- the bounded repair loop repeats the same failure pattern without meaningful progress
- an agent-generated change introduces a regression that reaches `main`
- a workflow attempts work outside the documented trust boundaries
- release automation produces an incorrect or incomplete artifact bundle
- a secret, token, or sensitive repository setting is exposed in code, logs, or release assets

## Immediate Response

When an incident is detected:

1. stop the affected workflow path from progressing further
2. label affected issues or PRs with `agent-blocked` and `needs-review`
3. capture the failing run, PR, and branch links in the incident notes
4. decide whether the problem is task-specific or pipeline-wide

## Kill Switch Policy

Use the smallest pause that contains the problem:

- if one agent task is bad, remove `agent-ready` and keep the rest of the pipeline running
- if one repair pattern misbehaves, disable or bypass the repair loop for that category
- if two consecutive RCs fail because of the same autonomous workflow pattern, disable the affected automation path until it is reviewed

## Who Can Pause What

- any repository admin may disable a workflow, remove `agent-ready`, or close an unsafe RC
- `@anatol21` owns the initial incident triage for this repository
- any reviewer may block `rc` or `submission` approval when artifacts, provenance, or evidence are incomplete

## Rollback Guidance

For bad code already merged:

1. open a human-led rollback or fix PR against `main`
2. keep normal review and CI gates in place
3. document the regression source and whether autonomy contributed

For a bad RC:

1. do not approve `rc` or `submission`
2. cancel the release workflow if appropriate
3. close or replace the pre-release after human review

## Required Incident Notes

Capture at least:

- date and triggering run
- affected workflow or policy
- symptom and immediate impact
- whether the issue came from task intake, CI, repair, or release automation
- corrective action
- whether autonomy should remain enabled, tightened, or paused

## Recovery Exit Criteria

Resume the paused automation path only when:

- the root cause is understood
- the workflow or policy change has been reviewed by a human
- a dry run shows the path behaving as intended
- the team agrees that the same failure is unlikely to recur immediately
