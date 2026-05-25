# Glossary of Evidence Types

## **Commits**
- **Definition**: Git commits that contain your direct contributions

- **Duo Mode Implementation, Debugging & Stabilisation**
  - Fixed Duo fixture invariants (wrong players, wrong corners, malformed board): https://github.com/anatol21/Blokus_GenAI/pull/71
  - Removed CLI guard blocking `blokus new --mode duo` without `--output`: https://github.com/anatol21/Blokus_GenAI/pull/71/commits
  - Fixed GUI player list hardcoded to `PLAYER_ORDER` for Duo mode: https://github.com/anatol21/Blokus_GenAI/pull/71/commits
  - Fixed GUI `switch_mode()` board geometry recomputation: https://github.com/anatol21/Blokus_GenAI/pull/71/commits
  - Fixed GUI `handle_restart()` hardcoded to Classic mode: https://github.com/anatol21/Blokus_GenAI/pull/71/commits
  - Fixed stale "Duo mode is disabled in this phase" status message: https://github.com/anatol21/Blokus_GenAI/pull/71/commits

- **GUI Score Bugfix**
  - Fixed score not updating after move — state refresh was missing: https://github.com/anatol21/Blokus_GenAI/pull/68

- **Test Consolidation (PR #84)**
  - Merged 5 standalone Duo test files into parametrised Classic tests: https://github.com/anatol21/Blokus_GenAI/pull/84/commits
  - Patched static analyzer to skip deleted files in `_build_tool_batches`: https://github.com/anatol21/Blokus_GenAI/pull/84/commits/81949f0
  - Removed stray `r` token causing `NameError` in serialization test: https://github.com/anatol21/Blokus_GenAI/pull/84/commits

- **Lint & Static Typing Cleanup**
  - Removed unused imports, fixed Ruff E701 violations across test files: https://github.com/anatol21/Blokus_GenAI/pull/71/commits
  - Fixed mypy type mismatches (`PLAYER_ORDER` tuple vs `list[str]`): https://github.com/anatol21/Blokus_GenAI/pull/71/commits

- **Documentation & Requirements**
  - Authored Windows GUI setup and debugging guide: https://github.com/anatol21/Blokus_GenAI/pull/67
  - Created UI-NOVICE-01 onboarding threshold definition: https://github.com/anatol21/Blokus_GenAI/pull/43
  - Created evidence-link validation sweep template: https://github.com/anatol21/Blokus_GenAI/pull/43
  - Authored topic-reviewing evaluation criteria and example problems: https://github.com/anatol21/Blokus_GenAI/pull/51

## **Tests**
- **Definition**: Test files or specific test cases you authored or extensively edited
  - tests/test_engine.py — Duo mode parametrisation and fixture validation
  - tests/test_cli_import.py — Duo import edge cases from files (parametrised)
  - tests/test_persistence.py — Duo state export/import round-trip (parametrised)
  - tests/test_serialization.py — Duo serialization round-trip (parametrised)
  - tests/test_persistence_extended.py — Extended persistence scenarios (pytest parametrised)
  - tests/test_serialization_integrity.py — Serialization integrity checks (pytest parametrised)
  - Fixtures: `fixtures/states/duo_initial_state.json`, `fixtures/scenarios/duo_opening_sequence.json`
  - All JSON edge-case files under `import_json_tests_duo/`
  - Deprecated reference copies: `depr_old_duo_tests/`

## **Documentation**
- **Definition**: Documentation files you wrote or significantly modified
  - `Windows_GUI_Setup_and_Debugging_Guide.md` — 6 documented Windows-specific errors with step-by-step fixes
  - `docs/UI-NOVICE-01_Onboarding_Threshold_Definition.md` — 13 measurable UX criteria linked to requirements R-F-30 through R-NF-20
  - `docs/Evidence_Link_Validation_Sweep.md` — Structured template for evidence traceability across 6 scenarios
  - `TOPIC-REVIEWING_evaluation.md` — Scoring rubrics and checklists for peer-review activities
  - `TOPIC-REVIEWING_example-problems.md` — Concrete review scenarios with annotated solutions
  - `MDP_PolicyIteration.py` — Initial prototype for exploring AI-driven behavior through policy‑iteration logic and also used for the example
  
  **The rest is included below in the pull request section.**

## **Pull Requests / Merge Requests**
- **Definition**: GitHub pull requests you created or primarily worked on
- **What to Link**:
  - Issue number and title
  - Your specific contributions within the PR

- **PRs You Created**:
  - PR #84 — Changes to be committed (test consolidation): https://github.com/anatol21/Blokus_GenAI/pull/84
  - PR #71 — Duo & code v2 (corrected Duo implementation): https://github.com/anatol21/Blokus_GenAI/pull/71
  - PR #70 — Duo & code v2 (initial implementation): https://github.com/anatol21/Blokus_GenAI/pull/70
  - PR #68 — Fix the bug in the GUI where the score was not being updated: https://github.com/anatol21/Blokus_GenAI/pull/68
  - PR #67 — Create WINDOWS_SETUP_AND_ERRORS.md: https://github.com/anatol21/Blokus_GenAI/pull/67
  - PR #51 — Requirements onboarding & novice support (final): https://github.com/anatol21/Blokus_GenAI/pull/51
  - PR #45 — Requirements onboarding & novice support (review feedback iteration): https://github.com/anatol21/Blokus_GenAI/pull/45
  - PR #43 — Requirements onboarding & novice support (merged): https://github.com/anatol21/Blokus_GenAI/pull/43
  - PR #42 — Update UI-NOVICE-01_Onboarding_Threshold_Definition.md: https://github.com/anatol21/Blokus_GenAI/pull/42
  - PR #39 — Add files via upload: https://github.com/anatol21/Blokus_GenAI/pull/39

- **Significant Reviews You Provided**:
  - PR #69 review: https://github.com/anatol21/Blokus_GenAI/pull/69#pullrequestreview-4304176218
  - PR #76 review: https://github.com/anatol21/Blokus_GenAI/pull/76#pullrequestreview-4348698568

## **Issues**
- **Definition**: GitHub or Trello issues you created or primarily worked on
  - [Execution] Duo integration — fixtures, CLI, GUI, tests: Linked via PR #71
  - [Execution] Score display bug — GUI state not refreshing after move: Linked via PR #68
  - [Execution] Test consolidation — eliminate duplicate Duo test files: Linked via PR #84
  - [Requirements] UI-NOVICE-01 onboarding threshold definition: Linked via PR #43
  - [Requirements] Evidence-link validation sweep: Linked via PR #43
  - [Requirements] Topic-reviewing evaluation criteria and examples: Linked via PRs #45, #51

## **Files**
- **Definition**: Source code files you primarily authored or significantly modified
- **What to Link**:
  - File paths with key changes
  - Key functions/classes in the file

- **PR #71 (Duo implementation):**
  - `src/blokus/cli.py` — removed `"Unsupported mode 'duo'"` guard in `cmd_new`
  - `src/blokus/gui.py` — conditional player list in `show_settings_dialog()`, board metric recomputation in `switch_mode()`, mode preservation in `handle_restart()`

- **PR #68 (Score bugfix):**
  - `src/blokus/gui.py` — added state refresh after move execution

- **PR #84 (Test consolidation):**
  - `tests/test_persistence.py` — parametrised with `self.subTest(mode=mode)`
  - `tests/test_serialization.py` — parametrised with `self.subTest(mode=mode)`
  - `tests/test_cli_import.py` — parametrised with `self.subTest(mode=mode)`
  - `tests/test_persistence_extended.py` — parametrised with `@pytest.mark.parametrize`
  - `tests/test_serialization_integrity.py` — parametrised with `@pytest.mark.parametrize`
  - `src/blokus/review/static_analyzer.py` — added deleted-file skip in `_build_tool_batches`

- **Fixtures:**
  - `fixtures/states/duo_initial_state.json` — repaired Duo initial state
  - `fixtures/scenarios/duo_opening_sequence.json` — repaired Duo opening sequence
  - `fixtures/states/classic_blue_no_legal_moves.json` — repaired invariant violations

## **Reproducible Counterexamples**
- **Definition**: Documentation of failures that can be reproduced by others

- **Counterexample 1 — AutoSD Debugging Loop Skipped**
  - Evidence documented in: `portfolio.md#counterexample-1` (Section 3, Counterexample 1)
  - Summary: The AutoSD hypothesis-generation loop was unnecessary because deterministic tool output (pytest, ruff, mypy) directly named every failure cause. No separate evidence file needed — the entire Duo debugging session across PRs #70, #71, #84 succeeded without the loop.
  - Key insight: Tool quality determines guideline relevance. High-quality tool output renders the hypothesis step redundant.

- **Counterexample 2 — Explain-Then-Fix Turn Skipped**
  - Evidence documented in: `portfolio.md#counterexample-2` (Section 3, Counterexample 2)
  - Summary: The two-turn explain-then-fix pattern was replaced with single-turn targeted fix prompts. All 5 categories of Duo bugs (fixtures, CLI, GUI, tests, lint/typing) were fixed with single-turn prompts because the root cause was already identified from tool output before prompting.
  - Examples: CLI guard fix (`src/blokus/cli.py`), parametrize misuse fix (`tests/test_engine.py`), fixture invariant repair.

- **Counterexample 3 — TDD-LLM Backfired on Corrupted Fixtures**
  - Evidence documented in: `portfolio.md#counterexample-3` (Section 3, Counterexample 3)
  - Summary: Supplying fixture-validation tests alongside broken fixtures anchored the LLM to the wrong baseline (tests expected `"yellow"` player, engine requires `"red"`). The tests were derived from the same corrupted data and provided a false specification.
  - Evidence code: The flawed prompt and the LLM output preserving `"yellow"` are documented in the portfolio.
  - Key insight: Tests are not independent oracles — verify tests against a canonical source before using them as LLM specifications.

---

## **Best Practices for Evidence Links**

1. **Be Specific**: Link to exact commits, functions, or sections — not just repository roots
2. **Be Persistent**: Use commit hashes (not branch names) for permanent references
3. **Be Complete**: Include enough context so others can understand the evidence without extra digging
4. **Be Verifiable**: Ensure links work and content hasn't been deleted

---

*Template version: 1.0 | Last updated: 2026-05-25 | Student: Nicolas Alejandro Zevallos Chavez*
