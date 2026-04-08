# Release Contents

This document defines the artifact bundle produced by the Phase 4 release automation.

## Required contents

Each release candidate must include the following:

- source snapshot archive generated from the current commit
- provenance attestation bundle for the published release archive
- automated test output summary
- CLI smoke output summary
- fixture/schema validation summary
- evaluation summary
- machine-generated evidence delta
- release metadata file
- automated release notes generated as a workflow artifact and attached to the GitHub Release
- release policy and release contents references

## Optional contents

The workflow may also include:

- example state JSON generated from the CLI
- rendered board output for the generated example state
- additional notes or supplementary artifacts attached to the GitHub Release

## Naming convention

- release candidate tag: `v<version>-rc.<n>`
- final submission tag by default: `v<version>`
- release bundle archive: `blokus-focus-pokus-<tag>.tar.gz`

## Workflow artifact layout

The release workflow stores generated files under `dist/release-candidate/` before uploading them as workflow artifacts.
Release notes are generated separately under `dist/release-notes/` and uploaded alongside the package artifact.

Expected layout:

```text
dist/
  release-candidate/
    docs/
    examples/
    logs/
    source/
    evidence-delta.md
    release-metadata.json
  provenance/
    <tag>-provenance.jsonl
  blokus-focus-pokus-<tag>.tar.gz
```

## Review expectation

The `rc` environment gate should review the uploaded release-candidate artifact bundle together with the generated release notes. The `submission` gate should review the approved RC artifact plus the promotion manifest before final publication.
