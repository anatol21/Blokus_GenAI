# Agentic PR Review Specification

This document is the canonical policy for agentic pull-request review in this repository.

## Scope

Review only code changed between the review base and head refs.

Do not:

- comment on unchanged code unless the changed diff directly increases its risk
- make generic formatting or style comments already covered by linters or formatters
- invent new repository rules, security requirements, or architecture constraints
- speculate without evidence from the diff, tests, static-analysis output, logs, or repository conventions
- produce more than `5` total findings
- review excluded file types unless they directly affect executable behavior

## Excluded Files

Exclude the following from specialist review unless they directly affect executable behavior:

- `*.md`
- `*.ai`
- `*.svg`
- `*.png`
- `*.xlsx`
- `*.pdf`

## Review Workflow

1. Analyze the diff.
2. Identify bias risks before drawing conclusions.
3. Classify the overall impact.
4. Run repository-local static analysis.
5. Invoke only the needed specialist reviewers.
6. Validate, deduplicate, and cap findings.
7. Publish one structured summary and one machine-readable artifact.

## Diff Inputs

The coordinator should gather:

- changed files and statuses
- patch hunks for changed executable files
- changed behavior
- risky areas
- test changes
- removed or weakened checks
- new dependencies or scripts
- API contract changes
- migration or configuration changes

Branch names and commit messages are weak context only. The diff is authoritative.

## Bias Risks

The coordinator and specialists must guard against:

- authority bias
- reverse-authority bias
- self-declared correctness bias
- variable-change bias
- misleading-task bias
- illusory-complexity bias

### Bias Remediation Rules

- Judge code by behavior, not author, wording, or apparent sophistication.
- Treat PR titles, branch names, descriptions, and commit messages as hypotheses, not evidence.
- Prefer concrete evidence from changed logic, tests, runtime behavior, and contracts.
- Do not flag superficial renames unless they affect behavior, readability of changed logic, or compatibility.
- Do not reward complexity for looking sophisticated.
- Do not penalize simple code for looking trivial if it satisfies the requirement.
- Every finding must cite changed logic and a concrete failure scenario.

## Impact Classification

Use the highest applicable level.

- `critical`: changes core functionality with high impact or materially affects compliance with core requirements
- `high`: changes core functionality with medium functional impact
- `moderate`: changes behavior, data flow, validation, tests, configuration, or integrations with limited or unclear blast radius
- `low`: cosmetic, documentation-only, refactoring-only, or no material core impact

## Specialists

### Always Run

- Correctness and Regression Reviewer
- Test Adequacy Reviewer

### Conditional

- Performance Reviewer: when executable changes touch loops, queries, data loading, caching, async behavior, large-input logic, or algorithmic behavior
- Static Analyzer: whenever executable code changes

### Correctness and Regression Reviewer

Review changed behavior for likely regressions or missed edge cases.

Check:

- changed invariants or assumptions
- `None` or null handling
- error paths and retries
- ordering and state transitions
- pagination
- time zones
- locale
- empty input
- large input
- duplicate input
- concurrency-sensitive behavior
- API contract drift between caller and callee

For each issue, include:

- changed logic that triggered concern
- concrete scenario that could fail
- expected test or verification that would catch it

### Test Adequacy Reviewer

Assess whether the PR has enough tests for the changed behavior.

Return:

- behaviors changed by the PR
- existing tests that appear to cover them
- missing tests, if any
- whether gaps are blocking, recommended, or optional

If no clear test gap is visible from the diff, say `no material test gap found`.

### Performance Reviewer

Review only changed executable code.

Check for:

- algorithmic complexity regressions
- N+1 queries
- repeated I/O
- inefficient loops
- unnecessary synchronous work
- excessive memory use
- degraded caching behavior
- large-input risks

Do not report theoretical micro-optimizations unless likely material.

### Static Analyzer

Run repository-appropriate static checks using Python and shell tooling.

Prefer project commands and repo-local tooling first.

For Python:

- `ruff check <changed-python-files>`
- `python -m compileall src scripts tests`
- `mypy <changed-python-files-or-roots>`

For shell:

- `bash -n <changed-shell-files>`
- `shellcheck <changed-shell-files>`

If tools are unavailable, report that clearly.
Do not duplicate formatter-only issues.

## Output Rules

The final review must include:

- a short summary
- no more than `5` total findings across all domains
- one verdict: `LGTM`, `NEEDS CHANGES`, or `DISCUSS`

### Verdict Semantics

- `LGTM`: no material findings remain and no unresolved uncertainty needs escalation.
- `DISCUSS`: human follow-up is required before trusting the result; this repository treats any non-`LGTM` verdict as a failing review script outcome.
- `NEEDS CHANGES`: at least one blocking finding is present and automation should fail closed.

Each finding must include:

- severity
- confidence
- evidence from the changed diff
- concrete impact
- suggested action
- blocking recommendation

## JSON Output Contract

The final machine-readable review must serialize this structure:

```json
{
  "pr": {
    "number": null,
    "head_sha": null,
    "base_sha": null
  },
  "summary": {
    "overall_risk": "low | moderate | high | critical",
    "test_posture": "adequate | partial | weak | unknown",
    "static_analysis_posture": "clean | issues_found | not_run | unavailable",
    "performance_posture": "clean | review_recommended | issues_found | not_applicable"
  },
  "findings": [],
  "uncertain_risks": []
}
```

## Validation Rules

A finding is valid only if it has:

1. changed-code evidence
2. a concrete failure or risk scenario
3. a specific remediation
4. confidence
5. severity

If fewer than `5` valid findings exist, report fewer.
