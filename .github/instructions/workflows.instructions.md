---
applyTo: ".github/**,scripts/github/**,docs/AGENT_POLICY.md,docs/PIPELINE_SECURITY.md,docs/INCIDENT_RESPONSE.md,docs/RELEASE_POLICY.md,docs/RELEASE_CONTENTS.md"
---

These files are part of the repository's governance and delivery trust boundary.

- Keep GitHub Actions permissions minimal. Prefer `contents: read` by default and raise permissions only for the exact job that needs them.
- Do not relax pull-request review, CODEOWNERS, status-check, or environment-approval controls.
- Do not add new third-party GitHub Actions unless a human explicitly requests and reviews that addition.
- Preserve the `rc` and `submission` environment gates. Packaging happens before approval; publication happens after approval.
- If a workflow change could affect merge authority, secret scope, release publication, or repair-loop behavior, mark it as human-gated in the PR explanation.
- Do not "fix" CI by weakening policy. Fix the underlying workflow or code instead.
- Keep comments and automation output concise, auditable, and easy for human reviewers to follow.
