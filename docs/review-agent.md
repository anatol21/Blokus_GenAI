# Review Agent

The Review Agent is a GitHub-deployed pull request reviewer. It runs in the
GitHub automation environment, builds a bounded diff context for a PR, runs
changed-file static analysis, optionally asks OpenRouter-backed specialist
reviewers for additional findings, and publishes review output back to GitHub.

The implementation lives in `src/blokus/review/`. The script entry point used by
the deployment is `scripts/github/agentic_code_review.py`.

## GitHub deployment model

GitHub is the operational interface for the Review Agent. The normal workflow is
not a local command run by a developer; it is a GitHub-triggered review that uses
GitHub Actions context, repository secrets, checked-out refs, and PR metadata.

Runtime configuration, prompt assets, credentials, and secret values belong to
the GitHub deployment environment. A local checkout is useful for reading and
testing the implementation, but local file presence is not the source of truth
for whether the deployed Review Agent is operational on GitHub.

The deployed run is expected to:

- Receive PR context from GitHub event data.
- Resolve the base and head refs for the pull request.
- Generate Markdown and JSON review artifacts.
- Upsert a PR conversation comment with the `agentic-code-review` marker when
  the run has permission to write to the PR.
- Use the process exit code as the GitHub check result.

## GitHub operation

On pull request review runs, GitHub provides the event payload, repository name,
workspace path, and token context. The Review Agent uses that context to infer
the PR number, base SHA, head SHA, and whether the PR branch belongs to the same
repository or a fork.

Same-repository PRs can use repository secrets and the default GitHub token to
run the full review path and publish the PR comment. Forked PRs intentionally
skip the LLM-backed specialist layer because repository secrets are not exposed
to untrusted fork contexts; those runs should be treated as requiring human
coverage for the LLM-only portion.

The generated review artifacts use these default paths inside the GitHub
workspace:

- `artifacts/agentic-review/review.json`
- `artifacts/agentic-review/review.md`

The Markdown artifact is the human review body. When `GITHUB_REPOSITORY` and
`GITHUB_TOKEN` are available and the PR is eligible for comment writes, the same
Markdown is posted or updated in the pull request conversation.

## Maintainer debug entry point

Local execution is not the normal user workflow. Maintainers can still use the
script entry point to inspect CLI options or reproduce GitHub behavior when they
provide equivalent refs, environment variables, and deployment configuration.

```bash
python -m scripts.github.agentic_code_review --help
```

The script form is also supported:

```bash
python scripts/github/agentic_code_review.py --help
```

The implementation accepts these options for deployment wiring and debugging:

- `--base-ref`: review base ref. If omitted, the script uses
  `REVIEW_BASE_REF` or the GitHub event payload.
- `--head-ref`: review head ref. If omitted, the script uses
  `REVIEW_HEAD_REF` or the GitHub event payload.
- `--pr-number`: optional pull request number. If omitted, the script uses
  `REVIEW_PULL_NUMBER` or the GitHub event payload.
- `--json-out`: machine-readable output path. Defaults to
  `artifacts/agentic-review/review.json`.
- `--markdown-out`: Markdown output path. Defaults to
  `artifacts/agentic-review/review.md`.

The process exits with status `0` only when the final verdict is `LGTM`.
`DISCUSS` and `NEEDS CHANGES` return status `1`, which lets GitHub checks fail
when the agent finds blocking or discussion-required review results.

## Environment

GitHub-provided runtime context:

- `GITHUB_EVENT_PATH`: event payload used to infer PR refs, PR number, and
  same-repository versus fork status.
- `GITHUB_WORKSPACE`: checked-out repository workspace. Relative artifact paths
  are resolved from this root.
- `GITHUB_REPOSITORY`: owner/repo value used when publishing a PR comment.
- `GITHUB_TOKEN`: token used to upsert the PR comment when permissions allow it.

Repository secrets:

- `OPENROUTER_API_KEY`: enables the LLM specialist review layer for trusted
  same-repository runs.

Optional deployment overrides:

- `REVIEW_BASE_REF`: fallback base ref when CLI arguments and event payload do
  not provide one.
- `REVIEW_HEAD_REF`: fallback head ref when CLI arguments and event payload do
  not provide one.
- `REVIEW_PULL_NUMBER`: fallback PR number.
- `REVIEW_MODEL_DEFAULT`: overrides the default OpenRouter model from config.
- `REVIEW_MODEL_CORRECTNESS`: overrides the correctness specialist model.
- `REVIEW_MODEL_TESTS`: overrides the tests specialist model.
- `REVIEW_MODEL_PERFORMANCE`: overrides the performance specialist model.

## What it reviews

The Review Agent reviews the changed files between a base ref and a head ref. It
uses the deployed review configuration to exclude paths, keeps findings tied to
changed lines, and reports uncertainty when the review context is incomplete or
too large to inspect fully.

The review has two layers:

- Static analysis: runs local checks on the GitHub runner for changed Python and
  shell files, then adds repository-aware heuristic findings.
- Specialist review: when `OPENROUTER_API_KEY` is available and the PR is from
  the same repository, invokes prompt-driven correctness, tests, and conditional
  performance specialists.

## Outputs

The Markdown output is the primary GitHub-facing review artifact. It is suitable
for both the PR conversation comment and the workflow artifact. It contains
these sections:

- Changed paths
- Findings
- Static Analysis
- Uncertain Risks, when present
- Verdict

The JSON output is the machine-readable review artifact. It contains:

- `pr`: pull request number plus base and head SHAs.
- `summary`: overall risk, test posture, static-analysis posture, and
  performance posture.
- `findings`: normalized findings with file, changed-line span, severity,
  confidence, category, evidence, impact, suggested action, and blocking flag.
- `uncertain_risks`: risks the agent could not verify conclusively, with
  recommended human verification.
- `verdict`: one of `LGTM`, `DISCUSS`, or `NEEDS CHANGES`.

## Verdicts

- `LGTM`: no blocking findings and no discussion-required uncertain risks.
- `DISCUSS`: no blocking findings, but at least one uncertain risk needs human
  judgment.
- `NEEDS CHANGES`: at least one finding has a blocking recommendation.

Some uncertain risks are intentionally non-blocking, such as dependency-related
changes, diff truncation, commit/file-list truncation, and OpenRouter specialist
failures caused by provider unavailability.

## Architecture

The Review Agent is coordinated by `ReviewCoordinator`.

1. `load_review_config` reads the deployed review configuration and validates
   the provider, prompt, model, heuristic, and exclusion settings.
2. `build_review_context` resolves refs, reads commit subjects, loads a bounded
   `git diff`, filters excluded paths, computes changed-line spans, and marks
   executable or performance-sensitive files.
3. `StaticAnalyzer` runs changed-file tools and heuristics. It can invoke
   `compileall`, Ruff, Mypy, `bash -n`, and ShellCheck when the relevant tools
   are available on the runner.
4. `OpenRouterClient` loads `OPENROUTER_API_KEY` and sends chat-completion
   requests using the configured base URL, timeout, retry budget, and models.
5. `SpecialistRunner` loads common and specialist prompts, builds a bounded user
   prompt, parses JSON responses, normalizes enums, and drops findings that do
   not map to changed files and changed lines.
6. `ReviewCoordinator` merges static and specialist findings, records uncertain
   risks, deduplicates and ranks findings, computes the summary and verdict, and
   asks the renderer for Markdown.
7. `render_review_markdown` produces the PR comment and artifact body.

## Safety limits

- Findings are accepted only when required fields are present, category and enum
  values are valid, and line ranges map to changed lines.
- Findings are deduplicated by category, file, starting line, and title.
- The coordinator returns at most `max_findings` from config.
- Stored patches and rendered prompt bundles are truncated for large diffs.
- Specialist prompts review only changed files and are capped at three findings.
- Commit and file-list context are bounded to avoid unbounded prompt growth.
- Large Python and shell batches are capped to keep static analysis predictable.
- Missing or unavailable runner tools are reported as uncertain risks instead of
  being treated as silent success.
- Forked PRs skip the LLM layer and require human review for LLM-only coverage.

## Troubleshooting

`OPENROUTER_API_KEY is not available`

The static-analysis layer can still run, but the OpenRouter specialist layer is
skipped or reported as an uncertain risk. Confirm the secret is configured for
the GitHub deployment and that the event type is allowed to access it.

`GitHub event payload is missing or incomplete`

The agent may not infer the PR number, base ref, head ref, or fork status. Check
the workflow trigger and confirm `GITHUB_EVENT_PATH` points to the event payload
for the run.

`Diff-based review was skipped because refs were unavailable`

Confirm the workflow checkout fetches enough history for the base and head refs,
or provide explicit ref overrides through the deployment.

`Forked pull request skipped specialist review`

This is expected for untrusted fork contexts. Treat the result as requiring
human review for specialist-only coverage.

`Ruff was unavailable`, `Mypy was unavailable`, or `ShellCheck was unavailable`

Install the tool in the GitHub runner setup or accept that the agent will record
the missing tool as an uncertain risk.

`PR comment was not posted or updated`

Check workflow permissions for `issues: write` and `pull-requests: write`, and
confirm `GITHUB_TOKEN` and `GITHUB_REPOSITORY` are available to the run.

`Review artifacts were not uploaded`

Confirm the workflow uploads `artifacts/agentic-review/review.json` and
`artifacts/agentic-review/review.md` after the script step, including on failure
when the verdict is `DISCUSS` or `NEEDS CHANGES`.

`Diff context was truncated for scale`

Manually inspect the full PR diff in GitHub, especially omitted hunks or files
not fully included in the rendered prompt bundle.

## Related files

- `src/blokus/review/config.py`: configuration loading and model override
  precedence.
- `src/blokus/review/diff.py`: diff parsing and review context construction.
- `src/blokus/review/static_analyzer.py`: local static-analysis and heuristic
  findings.
- `src/blokus/review/specialists.py`: prompt assembly and specialist response
  parsing.
- `src/blokus/review/provider.py`: OpenRouter client.
- `src/blokus/review/coordinator.py`: end-to-end orchestration and verdict
  computation.
- `src/blokus/review/renderer.py`: Markdown rendering.
- `scripts/github/agentic_code_review.py`: CLI and GitHub comment publishing.
