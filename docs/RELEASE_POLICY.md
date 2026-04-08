# Release Policy

## Purpose

Phase 4 extends the repository from supervised autonomous development into supervised delivery. The delivery loop may package, summarize, and publish artifacts automatically, but it must stop at protected environment gates until a human reviewer approves progress.

## RC Generation

The `release-candidate` workflow is the release entrypoint.

It runs when:

- code is pushed to `main`
- a human manually dispatches the workflow for a controlled rerun

The workflow must:

- verify the merged code with install, test, CLI smoke, fixture/schema validation, and evaluation
- build the release-candidate artifact bundle
- generate an artifact attestation for the release archive
- generate release notes and an evidence delta
- upload artifacts for review before any release publication happens

## RC Approval

The `rc` environment is the first trust boundary.

Rules:

- `rc` approval is required before the workflow may publish or update a GitHub pre-release
- self-review must remain disabled
- the author of the merged PR should not be the reviewer who approves the environment

## GitHub Pre-Release Publication

After `rc` approval, the workflow may create or update a GitHub pre-release:

- tag scheme: `v<version>-rc.<n>` unless a manual override is supplied
- release type: GitHub pre-release
- assets: packaged archive, provenance bundle, and evidence-oriented artifacts
- notes: generated automatically through GitHub release-note generation

## Submission Promotion

The `promote-submission` workflow is a manual workflow-dispatch step.

It must:

- accept an approved RC tag
- retrieve the RC assets
- prepare a submission manifest
- pause at the `submission` environment for approval
- publish or update the final GitHub Release only after approval

By default, the final submission tag is the RC version with the `-rc.<n>` suffix removed. A manual override may be supplied when needed.

## Reviewer Rules

- `rc` reviewers: any configured reviewer except the initiating actor when self-review prevention is enabled
- `submission` reviewers: same reviewer policy, with the expectation that a non-author approves
- humans still control protected environments, merges to `main`, and any sensitive repository settings

## Blocking Conditions

Release publication must stop when any of the following are true:

- verification commands fail
- packaging fails
- evidence or release metadata cannot be generated
- the environment gate is not approved
- the final release tag would be ambiguous and no human override is provided
- the provenance attestation cannot be generated for the packaged archive

## Failure Handling And Reruns

- use `workflow_dispatch` on `release-candidate` to rerun packaging for the same ref without merging new code
- use `workflow_dispatch` on `promote-submission` to retry final promotion from an existing RC tag
- reruns do not bypass `rc` or `submission` approval gates
- reruns should reuse the existing release tag when the intent is to update the same candidate

## Artifact Review Checklist

Before approving `rc` or `submission`, reviewers should confirm:

- the archive exists and opens correctly
- the provenance bundle or attestation record exists for the release archive
- the evidence delta matches the expected merged change set
- the evaluation summary is present and successful
- any docs, fixtures, schemas, or CI-sensitive changes are visible and intentional

## Retention Policy

The repository uses focused retention windows instead of keeping every artifact indefinitely:

- CI debug artifacts: `14` days
- governance review reports: `30` days
- release-candidate and submission artifacts: `90` days

If repository-level artifact and log retention is adjusted later in GitHub settings, it should stay aligned with these workflow-level values and any course audit needs.
