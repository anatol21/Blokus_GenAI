# Autonomy Scorecard

This scorecard is the lightweight operating view for the autonomous pipeline. Update it once per week or once per release-candidate review, whichever happens first.

## Purpose

Track whether autonomy is reducing cycle time without increasing review churn, regressions, or release risk.

## Metrics

Record the following for each reporting period:

- number of agent-started tasks
- merge rate of agent-touched PRs
- median time from issue creation to PR
- median time from PR open to merge
- number of repair-loop attempts
- number of escalations due to ambiguity
- number of post-merge regressions
- number of RC rejections at `rc`
- number of failed promotions at `submission`

## Reporting Table

| Period | Agent-started tasks | Agent PR merge rate | Median issue -> PR | Median PR -> merge | Repair-loop attempts | Ambiguity escalations | Post-merge regressions | RC rejections | Submission failures | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-04 | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | Baseline period after Phase 5 hardening |

## Review Prompts

Use this scorecard in the next retro or RC review and answer:

- Are agents helping on the tasks we actually send them?
- Are escalations mostly caused by bad task selection, missing context, or unstable CI?
- Which workflow or policy caused the most avoidable human cleanup?
- Should any workflow become stricter, looser, or temporarily paused?

## Ownership

- Metric owner: `@anatol21`
- Review cadence: weekly governance review plus each release-candidate retro
