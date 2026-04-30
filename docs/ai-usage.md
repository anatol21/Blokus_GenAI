# AI Usage Log

This log documents AI assistance used during engineering. Runtime behavior of the delivered solution must remain independent of LLM services (`R-C-01`).

## Logging policy

- Capture AI usage before or at merge time.
- Each entry must include validation and adoption decision.
- Do not mark output as adopted without human review or executable validation.

## Template

| Date (YYYY-MM-DD) | Tool / model | Task supported | Prompt or prompt category | Output summary | Validation performed | Adoption decision | Related files / issues |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-03-27 | GPT-based coding assistant | Repository governance setup | Requirements/doc-structure drafting | Drafted requirements, review, traceability, and issue-seed artifacts | Human inspection and repository consistency checks | Adopted with edits | `docs/requirements.md`, `docs/traceability-matrix.md`, `docs/issue-seed.md`, I-01, I-20 |
| 2026-04-30 | GPT-based coding assistant | Agentic PR review implementation and PR cleanup | Code generation, refactoring, test scaffolding, and PR artifact drafting | Implemented the agentic review workflow, static analyzer, prompt/config assets, tests, and cleanup docs for a clean PR branch | `PYTHONPATH=src python3 -m compileall src scripts tests`, `./scripts/test.sh`, `./scripts/evaluate.sh`, human review of branch scope and secret handling | Adopted with edits | `scripts/github/agentic_code_review.py`, `src/blokus/review/`, `.github/workflows/agentic-code-review.yml`, `docs/agentic-review/spec.md` |

## Minimum validation checklist for AI-assisted outputs

- Requirement IDs and wording checked against baseline scope.
- File references verified to exist in repository.
- Commands/scripts validated for reproducibility expectations.
- Tests run for code changes, if code paths were modified.
