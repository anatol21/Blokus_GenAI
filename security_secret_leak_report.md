# Secret And Sensitive Data Review

Date: 2026-03-27

## Executive Summary

I did not find committed API keys, access tokens, passwords, or private keys in the current working tree or in git history.

I did find three sensitive-data exposure issues:

1. The repository tracks generated interview transcripts and PDFs under `persona_interviews/`, and the simulator defaults to writing future runs there.
2. The repository tracks an Adobe temporary sidecar file that exposes internal design metadata and an embedded thumbnail.
3. A committed Illustrator source file retains embedded preview and provenance metadata that may reveal more than intended when the repo is shared publicly.

The highest-risk issue is the interview export workflow. The current samples appear synthetic, but the default output path and lack of ignore rules would cause real participant data to be committed if the script is ever used with live interviews.

## Method

- Searched the working tree for common secret patterns with `rg`.
- Searched git history for high-signal credential markers with `git grep` over all commits.
- Reviewed tracked generated artifacts, PDFs, design files, and IDE/project metadata for privacy leaks.
- Manually inspected the interview generator configuration and sample outputs.

## High Severity

### F-01: Generated interview artifacts are committed, and future runs default to a tracked directory

Impact: if this workflow is ever used with real participants, ages, family context, behavioral notes, and full transcripts will be committed to the repository by default.

Evidence:

- `persona_interview_simulator.py` writes output to `persona_interviews` by default at line 67.
- `.gitignore` does not exclude `persona_interviews/` or generated PDFs.
- Sample committed outputs include structured profile data such as age and personal context:
  - `persona_interviews/full_qwen3_8b/andrea_2026-03-27_18-13-52.md` lines 5-9
  - `persona_interviews/full_qwen3_8b/lukas_2026-03-27_18-19-26.md` lines 5-9

Why this matters:

- The current corpus looks synthetic because personas are hardcoded in `persona_interview_simulator.py` lines 88-174.
- Even so, the repository already contains interview-style profile documents and matching PDFs, which is the same storage pattern that would leak real research data if reused without changes.

Recommended remediation:

- Move interview output outside the repository by default.
- Add `persona_interviews/` and generated `*.pdf` interview outputs to `.gitignore`.
- Remove committed transcript artifacts from the repository and, if the repo has been shared publicly, consider rewriting history.

## Medium Severity

### F-02: Adobe temporary sidecar file is committed and exposes internal metadata

Impact: temporary design sidecars can expose internal working state, embedded previews, document lineage, and authoring metadata that are not necessary for source control and may disclose private production details.

Evidence:

- `Brokus Graphics/~ai-a537fe4a-5fc5-4ad7-8ca7-d60de6688bf2_.tmp` line 24 includes the authoring tool metadata.
- The same file records persistent document identifiers at lines 38-45.
- It embeds an image thumbnail payload beginning at line 34.
- It exposes Illustrator-specific metadata, including `CreatorSubTool`, at lines 48-51.

Why this matters:

- `~ai-*.tmp` is a temporary Adobe artifact, not a stable source file.
- These files are easy to commit accidentally and often contain more metadata than the final design asset.

Recommended remediation:

- Remove committed `~ai*.tmp` files.
- Add ignore rules for Adobe temp artifacts such as `~ai*.tmp`.
- If the repository is public, assume the metadata is already disclosed.

## Low Severity

### F-03: Illustrator source file retains embedded preview and provenance metadata

Impact: the design source itself may be intended to be shared, but the extra XMP metadata and embedded thumbnail disclose toolchain details and a built-in preview that may not be necessary to publish.

Evidence:

- `Brokus Graphics/SideBars.ai` line 20 records `xmp:CreatorTool`.
- The same file includes document lineage identifiers at lines 24-26.
- It records `illustrator:CreatorSubTool` at line 30.
- It embeds a large thumbnail payload beginning at line 48.

Why this matters:

- This is not a credential leak.
- It is still a privacy and repository-hygiene concern, especially for public repos or when asset provenance should stay internal.

Recommended remediation:

- Export a metadata-stripped asset if the art needs to be public.
- Keep source art in a private artifact store if public sharing is not required.

## No Credential Findings

I did not find:

- AWS access keys
- GitHub personal access tokens
- OpenAI-style API keys
- Slack tokens
- Private key blocks
- Database connection strings
- Generic password or client-secret markers in git history

This result is based on working-tree searches plus `git grep` across all commits currently reachable from repository history.

## Residual Risk

- I could not fully text-extract the untracked PDF `persona_interviews/Requirements Elicitation Judgment.pdf` in this environment, so this review treats it as unconfirmed rather than clean.
- If the repository has LFS objects, ignored files outside git history, or unpublished branches elsewhere, those were not part of this local scan.
