# Pipeline Security

This document records the Phase 5 security posture for the autonomous pipeline.

## Purpose

The goal of Phase 5 is to raise assurance, not autonomy. These controls harden the workflow surface without relaxing the existing trust boundaries around `main`, `rc`, or `submission`.

## Workflow Permission Baseline

| Workflow | Permission intent |
| --- | --- |
| `ci` | `contents: read` only |
| `issue-triage` | `contents: read`, `issues: write` |
| `agent-entry` | `contents: read`, `issues: write` |
| `pr-intelligence` | `contents: read`, `issues: write`, `pull-requests: write` |
| `failure-summary` | `contents: read`, `actions: write`, `issues: write`, `pull-requests: write` |
| `repair-loop` | `contents: write`, `actions: write`, `issues: write`, `pull-requests: write` |
| `dependency-review` | `contents: read` |
| `code-scanning` | `actions: read`, `contents: read`, `security-events: write` |
| `release-candidate` | read-only by default, with write access only in publish jobs and attestation permissions only in the package job |
| `promote-submission` | read-only by default, with `contents: write` only in the final publication job |
| `governance-review` | `actions: read`, `contents: read` |

## Action Inventory

Current workflow actions are limited to GitHub-owned actions:

| Action | Owner | Purpose |
| --- | --- | --- |
| `actions/checkout` | GitHub | Checkout repository contents |
| `actions/setup-python` | GitHub | Pin Python runtime in workflows |
| `actions/upload-artifact` | GitHub | Upload CI, release, and governance artifacts |
| `actions/download-artifact` | GitHub | Retrieve release and submission artifacts |
| `actions/github-script` | GitHub | Seed labels and issues |
| `actions/dependency-review-action` | GitHub | Review dependency changes on PRs |
| `actions/attest` | GitHub | Generate release provenance attestations |
| `github/codeql-action` | GitHub | Run CodeQL scanning |

There are currently no non-GitHub third-party actions in the repository.

## Third-Party Action Rule

New third-party actions may not be introduced by autonomous workflows. Any proposal to add one must:

- be reviewed by a human
- explain why a GitHub-owned action or inline script is not sufficient
- be treated as `workflow-sensitive`

## Retention Policy

Workflow artifacts use targeted retention:

- CI debug artifacts: `14` days
- governance review artifacts: `30` days
- RC and submission artifacts: `90` days

This keeps enough debugging window without defaulting to long-lived storage for low-value artifacts.

## Provenance Policy

Release candidates generate a provenance attestation for the packaged archive. RC reviewers should confirm that:

- the archive exists
- the provenance bundle exists
- the provenance is attached to the release candidate or retained with the workflow artifacts

## Secret Handling Rule

- automation must never commit or print secrets
- secrets should stay environment-scoped when they are only needed for `rc` or `submission`
- PR reviews should explicitly confirm that no secret material was introduced
