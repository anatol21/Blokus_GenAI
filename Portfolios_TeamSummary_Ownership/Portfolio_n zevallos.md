# Portfolio_NicolasZevallos.md

> **Individual Student Portfolio**
> CS 630 — Generative Software Engineering | Spring Semester 2026

---

## Student Information


**Student Name:** `Nicolas Alejandro Zevallos Chavez`  
**Team Name:** `Reviewing Team (Team 1)`                       
**Project:** Blokus Game Engine (Classic + Duo)  

---

## 1. Owned Package Contributions

### Package 1: Duo Mode — End-to-End Implementation, Debugging & Stabilisation

**Description:**

This package covers the full Duo mode extension of the Blokus engine — the Phase 2 change request that extends the Classic baseline (4-player, 20×20 board) to support a two-player, 14×14 board variant through engine configuration. The work spans the entire vertical slice: engine configuration, CLI command paths, GUI mode switching, fixture validation, test coverage, and static analysis cleanup. Ownership encompassed not just writing initial Duo support but — more critically — debugging, repairing, and stabilising the integration after it was merged into the main branch. This package also includes the Windows environment setup and debugging guide authored for cross-platform developer onboarding (PR #67).

**Responsibilities:**

- Repair and validate all Duo-related fixtures to satisfy engine invariants (`placed_squares + remaining_pieces == 21` per player)
- Align CLI behaviour so `blokus new --mode duo` works identically to Classic (removed guards that rejected Duo without `--output`)
- Fix GUI player selection, board geometry recomputation, and mode switching for Duo mode (PR #68)
- Update and stabilise the test suite to reflect that Duo is now fully supported rather than rejected (PR #84)
- Resolve all Ruff and mypy issues introduced during Duo integration
- Author the Windows GUI setup and debugging guide for cross-platform onboarding (PR #67)

**Pull Requests Authored:**

| PR | Title | Status | Scope |
|----|-------|--------|-------|
| [#39](https://github.com/anatol21/Blokus_GenAI/pull/39) | Add files via upload | Merged | Initial test case documentation |
| [#42](https://github.com/anatol21/Blokus_GenAI/pull/42) | Update UI-NOVICE-01_Onboarding_Threshold_Definition.md | Closed | UX threshold documentation (subsumed into #43) |
| [#43](https://github.com/anatol21/Blokus_GenAI/pull/43) | Requirements: onboarding & novice support | Merged | Evidence-link validation sweep + onboarding threshold table |
| [#45](https://github.com/anatol21/Blokus_GenAI/pull/45) | Requirements: onboarding & novice support | Closed | Topic-reviewing evaluation docs (got review feedback; iterated into #51) |
| [#51](https://github.com/anatol21/Blokus_GenAI/pull/51) | Requirements: onboarding & novice support | Merged | Final version of reviewing evaluation criteria and example problems |
| [#67](https://github.com/anatol21/Blokus_GenAI/pull/67) | Create WINDOWS_SETUP_AND_ERRORS.md | Merged | Windows GUI setup and debugging guide |
| [#68](https://github.com/anatol21/Blokus_GenAI/pull/68) | Fix the bug in the GUI where the score was not being updated | Merged | GUI score display bugfix |
| [#70](https://github.com/anatol21/Blokus_GenAI/pull/70) | Duo & code v2 | Closed | Full Duo implementation (superseded by #71 with fixes) |
| [#71](https://github.com/anatol21/Blokus_GenAI/pull/71) | Duo & code v2 | Merged | Corrected Duo implementation after audit findings |
| [#84](https://github.com/anatol21/Blokus_GenAI/pull/84) | Changes to be committed | Merged | Eliminated 5 duplicate Duo test files via parametrisation |
| [#87](https://github.com/anatol21/Blokus_GenAI/pull/87) | Final Changes + UML | Merged | Documentation / Example (Policy Iteration)|

**Key Contributions:**

1. **Fixture repair and validation (PR #71).** Repaired `classic_blue_no_legal_moves.json` and all Duo fixtures (`duo_initial_state.json`, `duo_opening_sequence.json`) to satisfy engine invariants. The original Duo fixture had wrong players (`blue` + `yellow` instead of `blue` + `red`), wrong start corners (`(0,0)` / `(13,13)` instead of `(4,4)` / `(9,9)`), and malformed board rows (14–15 characters wide instead of consistent 14). The invariant `placed_squares + remaining_pieces == 21` per player was violated because the fixture was generated from an older engine version before strict validation existed. The repair process required cross-referencing engine configuration against fixture data: loading the fixture via `GameState.from_dict()`, inspecting the board matrix, and manually recomputing piece counts. After repair, tests that previously failed on malformed input began exercising real engine logic. The agentic code review for PR #71 explicitly flagged fixture invariants as a P1 finding — confirming this was the most critical issue to resolve before any other Duo work.

2. **CLI Duo consistency fix (PR #71).** Removed the special-case guard in `cmd_new` that blocked `blokus new --mode duo` unless `--output` was provided. The original code at `src/blokus/cli.py` contained:
   ```python
   if mode == "duo" and not output:
       raise click.UsageError("Unsupported mode 'duo'")
   ```
   This silently rejected Duo mode for default stdout output while allowing it when `--output` was provided — a completely inconsistent behaviour. The root cause was that the original implementer had only partially added Duo support and left this guard as a "safety check" that was never removed. After the fix (`if mode not in ("classic", "duo"): raise ...` instead), Duo behaves identically to Classic — prints JSON to stdout by default, writes to file when `--output` is given. This unblocked CLI pipelines and scripting for Duo mode, enabling CI workflows and automated testing that previously could not run Duo scenarios.

3. **GUI Duo integration (PRs #68, #71).** This was the most interconnected set of changes, touching five distinct locations in the GUI:
   - `show_settings_dialog()`: hardcoded `players = list(PLAYER_ORDER)` — changed to `if self.state.mode == "duo": players = ["blue", "red"]`
   - `switch_mode()`: did not recompute `board_metrics`, `board_robot_size`, or asset preparation — added mode-conditional recalculation derived from `state.board_size`
   - `handle_restart()`: hardcoded `mode="classic"` — restarting while in Duo silently created a Classic game. Fixed to preserve the current mode.
   - Status bar: displayed stale message `"Duo mode is disabled in this phase"` — the message was hardcoded in the GUI startup sequence and had not been updated when Duo support was enabled.
   - Score display (PR #68): the game state was not refreshed after a move — traced to the board not calling `state.update()` after piece placement. Added a single call to the board update method.
   These changes eliminated coordinate misalignment, placement bugs, and UX confusion after mode switches. The score-not-updating bug was particularly subtle — the GUI rendered the previous state's scores because the redraw was triggered before the state mutation propagated.

4. **Test suite consolidation and cleanup (PR #84).** Eliminated five standalone Duo test files that were near-verbatim copies of their Classic counterparts, differing only in mode name, board size, and player count. The maintenance burden was clear: every time a Classic test changed, the Duo copy had to be updated in lockstep or risk silent divergence. The solution merged Duo coverage into existing Classic tests using parametrisation:
   - Unittest files (`test_persistence.py`, `test_serialization.py`, `test_cli_import.py`): `for mode in ["classic", "duo"]` with `self.subTest(mode=mode)` and dynamically derive moves from `state.start_corners` / `state.players`.
   - Pytest files (`test_persistence_extended.py`, `test_serialization_integrity.py`): `@pytest.mark.parametrize("mode", ["classic", "duo"])` with combined (mode, mutation) tuples where expected values differ.
   - The deleted duo files were moved to `depr_old_duo_tests/` (not permanently deleted) for reference.
   - The agentic code review for PR #84 flagged a stray `r` token in `test_serialization.py` that would cause a `NameError` — this was a copy-paste artifact from the original Duo file. I fixed it before merge.
   - Also patched the static analyzer (`src/blokus/review/static_analyzer.py`) to skip deleted files in `_build_tool_batches`, preventing CI failures when reviewing PRs that delete files.
   - Result: 379 passed, 3 skipped, 0 failed — coverage maintained or improved, maintenance burden halved.

5. **Lint and static typing cleanup (PRs #70, #71, #84).** Removed unused imports (`os`, `tempfile`, `compute_scores`, `list_legal_moves`). Replaced unused `as new_game` bindings with `_`. Rewrote one-liner `if` statements into multi-line blocks to satisfy Ruff E701. Fixed mypy mismatches where `PLAYER_ORDER` (tuple) was assigned to `list[str]`-annotated variables by converting to `list(PLAYER_ORDER)`. The most interesting fix was the Ruff F401 violations — the unused imports had been accumulating across multiple contributions because nobody ran `ruff` on the full test directory. This is a known problem in LLM-assisted projects: each individual contribution passes review, but dead code accumulates silently. The `ag` (agentic) review in PR #71 automatically detected these and flagged them — a case of automated review catching what human eyes missed.

6. **Windows developer onboarding guide (PR #67).** Authored `Windows_GUI_Setup_and_Debugging_Guide.md` documenting all six errors encountered when running the Blokus GUI on Windows: Python PATH issues (missing `python` command), missing librsvg (SVG rendering dependency), MSYS2 setup (required for GTK on Windows), venv activation (command differs from Linux), editable install quirks (`pip install -e .` fails on Windows paths), and Tkinter rendering inconsistencies (DPI scaling differences). These issues are invisible to Linux developers but block Windows contributors entirely. The guide was structured using the Debugging team's Explain-Then-Fix methodology: for each error, it documents the symptom, the root cause, and the step-by-step fix. This directly reduces onboarding time for future Windows contributors from hours to minutes.

**Evidence Links:**
- **Commits:** [74 commits by Nicotico2000](https://github.com/anatol21/Blokus_GenAI/commits/main/?author=Nicotico2000)
- **Fixtures:** [`fixtures/states/duo_initial_state.json`](https://github.com/anatol21/Blokus_GenAI/tree/main/fixtures/states), [`fixtures/scenarios/duo_opening_sequence.json`](https://github.com/anatol21/Blokus_GenAI/tree/main/fixtures/scenarios), [`import_json_tests_duo/`](https://github.com/anatol21/Blokus_GenAI/tree/main/import_json_tests_duo)
- **Tests:** [`tests/test_engine.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/tests/test_engine.py), [`tests/test_cli_import.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/tests/test_cli_import.py), [`tests/test_persistence.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/tests/test_persistence.py)
- **Source:** [`src/blokus/cli.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/src/blokus/cli.py), [`src/blokus/gui.py`](https://github.com/anatol21/Blokus_GenAI/blob/main/src/blokus/gui.py)
- **Documentation:** [`Windows_GUI_Setup_and_Debugging_Guide.md`](https://github.com/anatol21/Blokus_GenAI/blob/main/Windows_GUI_Setup_and_Debugging_Guide.md)

---

### Package 2: Harness, Evaluation Evidence & UX Onboarding Thresholds

**Description:**
This package covers the evaluation harness documentation, evidence-link traceability sweep, and the definition of measurable UX acceptance criteria for novice user onboarding (requirement UI-NOVICE-01). It ensures that all major release-gate claims in the project documents link to real, inspectable artifacts — and that the onboarding threshold table is structured, quantified, and ready for execution testing. This work was conducted across PRs #42, #43, #45, and #51.

**Responsibilities:**
- Author the UI-NOVICE-01 onboarding threshold definition document with 13 measurable criteria linked to requirements R-F-30 through R-NF-20
- Perform an evidence-link validation sweep across six linked scenarios (TEST-05, TEST-08, DOC-06, EVAL-01, EVAL-02, EVAL-03)
- Create and refine the reviewing evaluation criteria and example problems for the course's peer-review workflow

**Pull Requests Authored:**

| PR | Title | Status | Scope |
|----|-------|--------|-------|
| [#42](https://github.com/anatol21/Blokus_GenAI/pull/42) | Update UI-NOVICE-01_Onboarding_Threshold_Definition.md | Closed | Initial onboarding threshold + evidence sweep |
| [#43](https://github.com/anatol21/Blokus_GenAI/pull/43) | Requirements: onboarding & novice support | Merged | Formalised evidence-link validation and threshold table |
| [#45](https://github.com/anatol21/Blokus_GenAI/pull/45) | Requirements: onboarding & novice support | Closed | Reviewing evaluation/example docs (received change requests) |
| [#51](https://github.com/anatol21/Blokus_GenAI/pull/51) | Requirements: onboarding & novice support | Merged | Final reviewed version of evaluation criteria and examples |

**Key Contributions:**

1. **UX Onboarding Threshold Table (PRs #42, #43).** Authored `docs/UI-NOVICE-01_Onboarding_Threshold_Definition.md` containing 13 measurable criteria covering installation, game creation, piece placement, scoring comprehension, and mode switching. Each criterion is linked to a specific requirement ID (R-F-30 through R-NF-20) and includes a concrete measurement method, target value, and priority level. This document transformed a vague requirement ("the game should be easy for new players") into a testable acceptance framework.

2. **Evidence-Link Validation Sweep (PR #43).** Created `docs/Evidence_Link_Validation_Sweep.md` as a structured template that validates traceability for six linked scenarios: TEST-05, TEST-08, DOC-06, EVAL-01, EVAL-02, and EVAL-03. For each scenario, the template documents the evidence type (fixture, test output, documentation), the specific file path, the verification status, and any gaps found. This sweep was presented at the course's intermediate review and accepted as meeting the evidence-traceability requirements.

3. **Reviewing Evaluation Criteria and Examples (PRs #45, #51).** Authored `TOPIC-REVIEWING_evaluation.md` and `TOPIC-REVIEWING_example-problems.md` for the course's peer-review activities. The evaluation document includes detailed scoring rubrics, checklists, and guideline references for structured code review. The example-problems document provides concrete scenarios for in-class review exercises, with annotated solutions. PR #45 received change requests from a collaborator noting that examples needed to support interactive classroom exercises; PR #51 addressed these by adding policy iteration examples and restructuring the team information section. Both documents were ultimately merged and used in the course's review workshop.

**Evidence Links:**
- **Documentation:** [`docs/UI-NOVICE-01_Onboarding_Threshold_Definition.md`](https://github.com/anatol21/Blokus_GenAI/blob/main/docs/UI-NOVICE-01_Onboarding_Threshold_Definition.md)
- **Documentation:** [`docs/Evidence_Link_Validation_Sweep.md`](https://github.com/anatol21/Blokus_GenAI/blob/main/docs/Evidence_Link_Validation_Sweep.md)
- **Documentation:** [`TOPIC-REVIEWING_evaluation.md`](https://github.com/anatol21/Blokus_GenAI/blob/main/TOPIC-REVIEWING_evaluation.md)
- **Documentation:** [`TOPIC-REVIEWING_example-problems.md`](https://github.com/anatol21/Blokus_GenAI/blob/main/TOPIC-REVIEWING_example-problems.md)

---

## 2. Guideline Applications

### Application 1: Staged Pipeline (Target → Categorise → Generate & Validate → Review) — Maintenance Team (Guideline 1)

**Guideline Description:**
Structure LLM-assisted code maintenance as a four-stage pipeline rather than asking the LLM to produce a complete fix in one prompt. Stage 1 (Target) identifies all affected locations by casting a broad net. Stage 2 (Categorise) classifies each location by change type. Stage 3 (Generate & Validate) applies fixes and runs a cascade of cheap-to-expensive checks. Stage 4 (Review) has a developer inspect everything before merging. This guideline is grounded in Google's migration research (Ziftci et al., 2025) showing that regex-based search alone misses indirect references up to five dependency hops away.

**Context:**
Leading the Duo mode integration — a multi-area change touching fixtures, CLI, GUI, tests, and linting across 28 files in PR #71 simultaneously. The scope included fixing broken fixtures, repairing GUI player logic, aligning CLI behaviour, cleaning up outdated tests, and resolving lint/type errors — all interconnected because a fix in the engine config could cascade through CLI output, GUI rendering, and test expectations.

**Application Process:**
1. **Stage 1 — Target:** Systematically identified every Duo-related breakage before writing a single fix. This included: invalid Duo fixtures (wrong players, wrong corners, malformed board), CLI guard that rejected `blokus new --mode duo` without `--output`, GUI hardcoded to `PLAYER_ORDER` ignoring mode, GUI board geometry not recomputed on mode switch, stale "Duo disabled" messaging, restart hardcoded to Classic, legacy test expecting Duo to be rejected, Ruff F401 unused imports, and mypy type annotation mismatches. Following the guideline's "broad net" principle, I also found indirect references: the fixture `classic_blue_no_legal_moves.json` that would break under the new strict validation, and the settings dialog that wrote controller entries for `yellow` and `green` even in Duo mode.

2. **Stage 2 — Categorise:** Classified each issue into distinct categories — fixture invariant violations, CLI behavioural inconsistencies, GUI UX bugs, outdated test assumptions (legacy rejection test), lint/mypy noise, and cross-cutting issues (strict validation scope). Each category received a different fix strategy: fixtures needed regeneration from canonical config, CLI needed guard removal, GUI needed mode-conditional logic, tests needed parametrisation, and lint needed import cleanup and annotation fixes. Separating categories prevented applying the wrong fix type (e.g., trying to "fix" a test that needed deletion rather than repair).

3. **Stage 3 — Generate & Validate:** Applied fixes iteratively, running the full test suite (`./scripts/test.sh`) + `ruff` + `mypy` after each batch. The cascade ordering from the guideline — non-empty response, syntax check, compilation, then tests — was followed naturally: I applied a fix, ran `ruff` (cheapest), then `mypy` (medium), then the full test suite (most expensive). Fixing fixtures before tackling CLI and GUI meant test signals were clean at each step rather than producing noisy compound failures.

4. **Stage 4 — Review:** Manually verified all diffs, confirmed GUI behaviour visually by running the application in both Classic and Duo modes, and validated fixture invariants by running the engine against repaired state files before marking work complete. After PR #71 was merged, I additionally reviewed the audit findings from the repository owner and applied the follow-up fixes (PR #84 consolidation) as a second review cycle.

**Outcome:**
- **What worked:** The staged decomposition prevented regressions. Fixing fixtures first meant that when I later changed CLI and GUI code, test failures were genuinely caused by the new code — not by pre-existing malformed inputs. The categorisation step was particularly valuable: separating "test that expects Duo to be rejected" (outdated assumption) from "fixture with wrong player list" (data error) meant I deleted the test and regenerated the fixture rather than trying to patch either one to match the other.
- **What did not work:** The guideline is formally designed for large-scale automated migrations (framework upgrades, cross-repo API changes). The Duo work was a multi-area bugfix and consistency cleanup — structurally similar but not a "migration" in the academic sense. The guideline's scope slightly overstates the formality needed. However, the core insight (stage-based decomposition) was genuinely valuable regardless of the label.
- **Evidence:** PRs #70, #71, #84; all Duo-related commits; repaired fixtures in `fixtures/states/` and `fixtures/scenarios/`; the agentic code review output from PR #71 confirming the staged approach aligned with recommended practice.

**Reflection:**
The staged approach is valuable for any multi-area change, not just formal migrations. The key insight I will carry forward is Stage 2 (categorisation) — separating logic bugs from test misalignment from lint noise before touching any code saved significant debugging time. I will explicitly name and sequence the four stages at the beginning of any future multi-area task, making the plan transparent to teammates rather than applying it informally as I did here.

---

### Application 2: Keep Developers as Final Reviewers for Every LLM-Generated Change — Maintenance Team (Guideline 3)

**Guideline Description:**
Treat every LLM-generated artifact as a verified draft, not a final deliverable. Delegate routine, mechanical maintenance tasks to LLMs (variable renames, type consistency changes, boilerplate) but keep high-level design decisions under human control. When an LLM suggests a refactoring, verify its actual impact rather than assuming improvement. The guideline is supported by Ziftci et al. (2025) showing that despite 80% of code being AI-authored at Google, every change required human review, and by Horikawa et al. (2025) showing that LLMs account for only 1.1% of duplication-removal refactoring vs. 13.7% for humans.

**Context:**
Throughout the entire Duo integration process, I used Claude Sonnet, GitHub Copilot, and Microsoft Copilot to suggest fixes, identify inconsistencies, and generate candidate patches. Every decision about whether to adopt, modify, or reject a suggestion remained mine. This guideline was directly applicable because LLMs were involved at every stage — fixture generation, CLI debugging, GUI logic, test repair, lint cleanup — but the architectural decisions about what Duo mode should look like were never delegated.

**Application Process:**
1. Used the LLM to identify candidate fixes for each category of Duo issue (fixture invariants, CLI guard, GUI player logic, test parametrize misuse). The LLM was treated as an "expert colleague" offering suggestions, not an autonomous architect.
2. Ran the full test suite, `ruff`, and `mypy` after every proposed change rather than accepting LLM output on trust. This validation cascade was explicitly documented in the AI Usage Disclosure (Section 4).
3. Made explicit design-level decisions independently: whether to remove vs. update the legacy rejection test (deleted — the test contradicted the new Duo support), whether to use `list(PLAYER_ORDER)` vs. changing the type annotation to `Sequence[str]` (chose `list()` for minimal diff), whether Duo board metrics should be recomputed lazily or eagerly on mode switch (eager — simpler and fewer edge cases).
4. Visually confirmed GUI behaviour after every GUI fix rather than relying solely on automated checks. The agentic code review in PR #71 flagged GUI board geometry as a potential issue at "moderate" risk — I validated this by running the application.
5. When PR #71 received audit findings from the repository owner (6 issues across P1–P3), I manually triaged each finding, decided which to fix immediately (P1 items: fixtures, restart, CLI guard) and which needed architectural discussion (P2: validation scope), and implemented fixes accordingly.

**Outcome:**
- **What worked:** Every adopted LLM suggestion was correct — because I validated it. The most critical moment was when the LLM suggested rewriting the entire `show_settings_dialog()` method to fix the player list bug — introducing a settings data class, new abstractions, and a separate rendering path for each mode. I rejected this and applied a two-line conditional instead (`if self.state.mode == "duo": players = ["blue", "red"] else: players = list(PLAYER_ORDER)`). This saved significant time and eliminated the risk of introducing new bugs in unrelated dialog functionality.
- **What did not work:** The guideline's prescription is universally applicable and consistently delivered value. Nothing failed here. However, I noted that the guideline's blanket "always review" rule could benefit from a risk-based intensity scale: a mypy annotation fix needs a glance, while a GUI logic change needs line-by-line inspection and visual confirmation.
- **Evidence:** The `show_settings_dialog()` targeted fix in `src/blokus/gui.py` (PR #68 commit), contrasted with the LLM's proposed rewrite; all PR review comments and agentic code review output confirming human review gate was active.

**Reflection:**
The most important lesson from applying this guideline is the distinction between "mechanical maintenance" (which LLMs handle well) and "high-level design decisions" (which must remain human). The LLM's proposal to rewrite the settings dialog was superficially plausible — the new structure was cleaner — but it solved a problem nobody had asked about. Recognising this as scope creep masked as improvement is exactly the skill this guideline trains. I will always apply this guideline, and I will add "apply the minimum change necessary; do not introduce new abstractions" as a default scope constraint to all fix prompts.

---

### Application 3: Apply Prompt Engineering Techniques (Structured Prompts for Testing) — Testing Team (Guideline 2)

**Guideline Description:**
Use clear, structured prompts for test generation: set the role explicitly ("Act as a senior test engineer"), provide focused context (Class Under Test, key dependencies, relevant code snippets, test scenarios), define task instructions with constraints and output format, and choose the simplest prompting style that fits the task. For debugging tasks, include only the relevant traceback and failing snippet rather than full logs. The guideline recommends starting with zero-shot for simple tasks, using few-shot when format consistency is needed, and separating system-level from task-level instructions.

**Context:**
Generating and debugging the Duo-specific test suite — specifically diagnosing the `@pytest.mark.parametrize` / `unittest.TestCase` incompatibility in `test_engine.py`, and generating repair fixtures for the import validation tests. I was working with a codebase that had a mixed test architecture (unittest.TestCase subclasses with pytest decorators added), which created a class of errors that were invisible to the test runner but caused collection failures.

**Application Process:**
1. **Set a clear role:** `"Act as a senior Python test engineer familiar with both pytest and unittest.TestCase."` This role assignment produced noticeably more precise output than generic prompts — the LLM began reasoning about test discovery mechanics rather than guessing at syntax.
2. **Provided focused context:** Instead of pasting the entire 300-line test file, I included only the failing class, the exact error message from pytest discovery (`TypeError: ... takes 1 positional argument but 4 were given`), and the specific 10-line code region with the `@pytest.mark.parametrize` decorator. This matches the guideline's recommendation to include only the relevant traceback and failing snippet for debugging tasks.
3. **Defined explicit constraints:** `"Do not suggest migrating to pure pytest. Keep the unittest.TestCase structure and fix only the parametrize usage."` This prevented the LLM from proposing a full architectural rewrite (which would have been the simplest "fix" from its perspective but would have changed the entire test class).
4. **Reviewed against documentation:** Before applying the LLM's proposed fix (replacing parametrize with `self.subTest()` inside a `for` loop), I cross-checked against the Python documentation for `subTest()` to ensure the pattern was correct. This is the "choose the simplest prompting style" and "human review" principles combined.

**Outcome:**
- **What worked:** Providing only the relevant traceback and failing pattern produced a precise, correct fix on the first attempt — no iteration needed. The role assignment noticeably improved specificity: the LLM identified the root cause (test discovery incompatibility between pytest decorators and `unittest.TestCase`) rather than proposing surface-level syntax patches.
- **What did not work:** For the mypy type mismatch (PLAYER_ORDER tuple assigned to `list[str]`), even with focused context, the LLM initially suggested changing the annotation to `Any` — which would have weakened the type guarantees. Adding a one-line constraint (`"Do not weaken type annotations"`) fixed this on the next attempt. This demonstrates that constraints are as important as context in prompt engineering.
- **Evidence:** `tests/test_engine.py` changes (parametrize removal), `src/blokus/cli.py` (PLAYER_ORDER type fix), PR #84 test consolidation.

**Reflection:**
The most impactful element of this guideline for debugging tasks is the instruction to provide only the relevant traceback and failing snippet. Full-log prompts consistently produce vague or over-engineered responses. Targeted context produces surgical fixes. I now apply this as a default: when asking an LLM to debug a failure, I include exactly the error message and the failing region — nothing more. The guideline's constraint-definition step ("do not weaken type annotations") was a meta-lesson: constraints are not just about output format but about preserving properties the LLM might inadvertently erode.

---

### Application 4: Iterative Remediation and Self-Correction Loops — Coding Team (Guideline 3)

**Guideline Description:**
Implement a structured "Plan-Execute-Review" loop when coding with LLMs. Treat the first output as a draft; feed failed test execution output (tracebacks, logs) back into the model for remediation. Complement this with a secondary "Reviewer" turn to force the model to critique its own logic for "silent" hallucinations like security flaws or performance bottlenecks. The guideline is grounded in Mathews & Nagappan (2024), who demonstrated that 3–5 iterations of remediation using failed test information add ~5% improvement on complex problems, and in Zhang et al. (2025), who identified that silent hallucinations (security risks, incomplete functionality) are the most dangerous as they pass syntax checks.

**Context:**
PR #84 — the test consolidation and cleanup — where I merged five standalone Duo test files into parametrised Classic tests. This involved not just a single edit but an iterative cycle: make changes, run the full test suite, review the agentic code review output, fix any issues identified, and re-run. The agentic review flagged three issues: a stray `r` token causing `NameError` in `test_serialization.py`, a skip-if-directory-missing pattern in `test_cli_import.py`, and the missing static analyzer guard for deleted files.

**Application Process:**
1. **Plan:** Mapped the five Duo test files to their Classic counterparts and determined the parametrisation strategy (unittest `subTest()` for unittest files, `@pytest.mark.parametrize` for pytest files). Created a deletion plan that preserved the originals in `depr_old_duo_tests/` rather than permanently deleting them.
2. **Execute — First pass:** Applied the parametrisation changes across all ten files (5 Classic + 5 Duo), deleted the Duo files, ran the test suite. Result: 379 passed, 3 skipped — but the agentic review flagged issues.
3. **Review — Agentic feedback:** The automated review identified the stray `r` token (a copy-paste artifact from the Duo file where `r` was a variable reference that had no meaning in the Classic context). It also noted that the static analyzer would fail on PRs with deleted files because `_build_tool_batches` did not skip `status == "D"` entries.
4. **Remediate — Second pass:** Removed the stray `r` token, added the deleted-file guard in `static_analyzer.py`, and addressed the directory-skip concern in `test_cli_import.py`.
5. **Re-execute:** Ran the full suite again — 379 passed, 3 skipped, 0 failed. The agentic review re-ran and changed its verdict from `DISCUSS` (indicating issues found) to passing.
6. **Human sign-off:** Requested review from another project partner, who approved and merged.

**Outcome:**
- **What worked:** The iterative remediation loop caught issues that the first test pass did not. The stray `r` token did not cause a test failure (it was in a `with` block that was not reached by the existing test cases) — it was found by the static analysis layer of the agentic review. This is exactly the "silent hallucination" scenario the guideline warns about: code that passes tests but contains an error.
- **What did not work:** The loop required three iterations (execute → review → remediate → re-execute → re-review) for a relatively small change. For simpler, single-file changes, the overhead of the formal remediation loop may not be justified — a single review pass suffices.
- **Evidence:** PR #84 commits, agentic code review output (verdict changed from `DISCUSS` to passing), `src/blokus/review/static_analyzer.py` changes.

**Reflection:**
This guideline's value was clearest in catching the stray `r` token — an error that no test would have caught because it was in a `with` statement that always executed, but only caused a `NameError` at module import time. The static analysis layer in the agentic review caught it because it compiled the Python files before testing them. This reinforced a key insight: the remediation loop should include multiple check types (compilation, static analysis, type checking, test execution) arranged from cheapest to most expensive, exactly as the guideline's "Plan-Execute-Review" structure implies. I will use this pattern for any multi-file change where silent errors are possible.

---

## 3. Counterexamples

### Counterexample 1: AutoSD Scientific Debugging Loop Was Unnecessary for Deterministic Failures

**Guideline:** AutoSD: LLM-Driven Scientific Debugging (Debugging Team, Guideline 2)

**Guideline Description:**
The AutoSD guideline prescribes a structured hypothesis → prediction → experiment → observation → conclusion loop for LLM-assisted debugging, with a `<DONE>` termination signal. Developers should ask the LLM to generate a hypothesis about the bug, define a prediction, design and run an experiment (e.g., print statements or test execution), observe the actual output, ask the LLM to draw a conclusion, and repeat until confident. The guideline is grounded in the Scientific Debugging concept and validated through research showing it improves root cause identification and reduces hallucination.

**What I Tried to Do:**
During Duo debugging — fixing GUI logic, CLI inconsistencies, invalid fixtures, and failing tests — the AutoSD guideline was directly applicable because my entire project was a debugging exercise across five categories of issues. However, I did not use the formal hypothesis → prediction → experiment → observation → conclusion loop. Instead, I relied directly on deterministic tool output (pytest, ruff, mypy, CLI behaviour) to diagnose failures.

**Why It Did Not Work (as intended):**
- **Root Cause:** The AutoSD loop is designed for scenarios where the failure signal is ambiguous — where you must form hypotheses because you cannot directly observe the failure cause. My failures were deterministic and immediately observable: pytest output named the exact failing test and the exact error, ruff output named the exact line and rule code, mypy output named the exact variable with expected vs. actual types.
- **The structured loop would have added latency without diagnostic value.** For each fix cycle, the sequence was: run tests → read error → apply fix → re-run. Adding "ask LLM to hypothesize" between "read error" and "apply fix" would have consumed tokens and time without surfacing any information the error message did not already provide. The hypothesis step was redundant — the tools performed the diagnostic work.
- **Boundary Condition:** AutoSD applies well to logic errors in complex, stateful code where no automated tool surfaces the root cause directly (e.g., off-by-one errors in nested loops, race conditions, subtle semantic bugs in business logic). It is unnecessary when the development environment provides deterministic, specific failure signals from test runners, static analysers, and type checkers.

**What I Learned:**
The structured debugging loop is a diagnostic aid, not a mandatory ritual. Its value is inversely proportional to the quality of the development environment's feedback signals. When tools give precise error messages, the correct workflow is: read the tool output → understand the cause → apply a targeted fix. When tools are silent or ambiguous, AutoSD's hypothesis generation adds genuine value.

**Updated Guideline:**
"Apply AutoSD when the failure signal is ambiguous or when no automated tool directly identifies the root cause. When deterministic tools (pytest, ruff, mypy) produce specific, actionable output, skip the hypothesis loop and act directly on the tool output. Use the LLM for fix suggestions at that point — not for root cause speculation."

**Evidence:**
The entire Duo debugging session succeeded without the AutoSD loop. All five categories of issues (fixtures, CLI, GUI, tests, lint/typing) were diagnosed and fixed directly from tool output. Specific examples: the pytest parametrize error (`TypeError: takes 1 positional argument but 4 were given`) directly named the problem; the Ruff F401 error (`os` imported but unused) directly named the file, line, and rule; the mypy error (`Incompatible types: "tuple[str, ...]" vs "list[str]"`) directly named the variable and types.

**Prompt/Context Used:**
```
[No AutoSD loop was initiated. Debugging was driven by:
1. pytest test suite output (exact failing test names and error messages)
2. ruff linting output (exact file, line, rule code)
3. mypy type-checking output (exact variable, expected type, actual type)
4. GUI visual inspection after applying fixes]
```

**AI Output:**
```
[Not applicable — no hypothesis-generation prompts were used.
AI was used for targeted fix suggestions after the root cause
was already identified from tool output, not to generate hypotheses.]
```

---

### Counterexample 2: Explain-Then-Fix (Rubber Duck Self-Debugging) Was Not Needed When Failures Were Explicit

**Guideline:** Explain-Then-Fix / Rubber Duck Self-Debugging (Debugging Team, Guideline 1)

**Guideline Description:**
This guideline requires a two-turn prompt sequence for debugging: first ask the LLM to explain the code line-by-line and compare it to intended behaviour ("Explain turn"), then ask for a fix based on that explanation ("Fix turn"). The guideline is supported by Chen et al. (2024), who showed that on the Spider text-to-SQL benchmark, adding the explanation step improved accuracy by 2–3% overall and by 9% on the hardest queries. The intuition mirrors human rubber duck debugging: articulating what the code does surfaces the gap between implementation and intent.

**What I Tried to Do:**
The Explain-Then-Fix guideline was designed for exactly the kind of debugging I was doing — fixing code where the developer (me) needed to understand the gap between implementation and intent. I did not use this two-turn pattern. Every bug was resolved using single-turn targeted fix prompts.

**Why It Did Not Work (as intended):**
- **Root Cause:** The Explain-Then-Fix pattern is most valuable when the developer does not already know what the code does and cannot infer the bug without walking through it. In my Duo work, every bug had a clear, pre-identified root cause before I involved an AI: I knew the CLI guard was wrong because the error message `"Unsupported mode 'duo'"` was explicit; I knew the parametrize decorator was misused because the pytest error was explicit; I knew the fixture invariant was violated because I computed `placed_squares + remaining_pieces` manually and got 0 instead of 21.
- **The explanation step would have been redundant.** The guideline's 9% improvement on Spider's hardest queries comes precisely because those queries lack explicit feedback — the model cannot verify its SQL against the database within the prompt. My environment provided explicit feedback for every failure. Asking the LLM to explain code I had already read and understood would have consumed extra tokens without adding diagnostic value.
- **Boundary Condition:** Explain-Then-Fix applies when: (a) the developer is unfamiliar with the codebase section, or (b) there is no automated tool that names the failure cause, or (c) the bug is a subtle semantic error invisible to static analysis. It is unnecessary when the failure cause is already known before prompting — in that case, the optimal workflow is a single-turn fix prompt with targeted context from the failing tool.

**What I Learned:**
The two-turn pattern is a diagnostic aid for ambiguity, not a universal prerequisite. The decision of whether to use it should be based on the developer's familiarity with the code and the clarity of the failure signal. I can articulate this as a simple rule: if the error message tells you exactly what is wrong, skip the explanation turn and go directly to the fix. If you are staring at passing tests wondering "but is it correct?" or debugging a subtle semantic issue, use Explain-Then-Fix.

**Updated Guideline:**
"Use Explain-Then-Fix selectively. Apply it when the failure is subtle, when you genuinely do not know what the code does, or when no automated tool identifies the root cause. Skip it when the failure cause is already identified from tool output — in that case, go directly to a targeted fix prompt with the specific context from the failing tool."

**Evidence:**
All Duo bugs were fixed successfully using single-turn targeted fix prompts without the explanation step. Examples: `src/blokus/cli.py` (cmd_new guard fix — identified from error message), `tests/test_engine.py` (parametrize removal — identified from pytest error), all fixture repairs (identified from manual invariant computation).

**Prompt/Context Used:**
```
# Example of the single-turn targeted prompt used instead:

"The following test fails with this error:
TypeError: test_duo_mode_is_supported takes 1 positional argument but 4 were given

The relevant code is:
[10-line snippet from test_engine.py showing @pytest.mark.parametrize
 on a unittest.TestCase method]

The issue is the @pytest.mark.parametrize decorator inside a
unittest.TestCase class. Fix only the decorator misuse.
Do not migrate to pure pytest. Keep the TestCase structure."
```

**AI Output:**
```
# AI correctly identified: parametrize is not compatible with
# unittest.TestCase.test_* methods. Replace with self.subTest()
# inside a for loop. Fix applied directly without an explanation turn.
# Result: test passed on first application.
```

---

### Counterexample 3: Interactive Test-Driven Validation Backfired When the Tests Themselves Were Wrong

**Guideline:** Interactive Test-Driven Validation (TDD-LLM) (Coding Team, Guideline 2)

**Guideline Description:**
Supply human-verified unit tests alongside problem statements in the prompt. Use these tests as a "source of truth" to formalize requirements, prune incorrect code candidates, and clarify ambiguous natural language intent through interactive feedback. The guideline reports that providing tests in prompts improves correctness by up to 18% (Mathews & Nagappan, 2024) by disambiguating prose and that execution-based filtering (Fakhoury et al., 2024) significantly reduces cognitive load by removing plausibly correct but logically flawed suggestions.

**What I Tried to Do:**
During the Duo fixture repair work, I attempted to apply the TDD-LLM approach: I supplied the engine's existing fixture-validation tests alongside the broken fixture files and asked the LLM to generate corrected fixtures that would make the tests pass. The intuition was that the tests, being already written and verified for Classic mode, would serve as a precise specification for what correct Duo fixtures should look like.

**Why It Did Not Work (as intended):**
- **Root Cause:** The tests themselves were tied to the broken fixtures through shared assumptions. The fixture validation tests checked invariants like `placed_squares + remaining_pieces == 21` and correct board symbols — but the test assertions were derived from the same corrupted fixture files. For example, the Duo fixture used `"yellow"` as a player colour (inherited from an earlier engine version where Duo used blue+yellow), and the test expected `"yellow"` in the output. The test was therefore "correct" in the narrow sense of matching the fixture — but both were wrong relative to the engine's actual Duo specification (which requires blue+red players).
- **Supplying the tests anchored the LLM to the wrong baseline.** The LLM saw a test that expected `"yellow"` as a player and produced a "fix" that preserved `"yellow"` — because the test "proved" that `"yellow"` was the expected value. The test provided a false specification, and the LLM faithfully generated code that satisfied it.
- **Boundary Condition:** TDD-LLM assumes that the supplied tests are correct and that the generated code is the source of the failure. When the test suite itself is corrupted (because it was derived from the same broken data), the entire validation pipeline collapses. The guideline is effective when the test represents an independent oracle of correctness — it fails when the test shares its corruption with the code under repair.

**What I Learned:**
Tests are not independent oracles. They are artifacts that can be corrupted by the same forces that corrupt the production code. The guideline's critical hidden assumption is that tests have been independently verified against a canonical specification — not derived from the same broken data. For the Duo fixture repair, I had to step back and first derive the correct invariant values from the engine's source code (player list, board size, start corners), then fix both fixtures and tests independently. The lesson: before using tests as a specification for LLM repair, verify that the tests themselves are correct against a third-party reference (engine source, design document, or manual computation).

**Updated Guideline:**
"Before using tests as a validation oracle for LLM-generated repairs, independently verify that the tests themselves are correct against a canonical specification (engine source, design documents, or manual computation). Tests derived from the same corrupted data source as the code under repair will provide a false specification. In such cases, repair the test against the canonical spec first, then use it to validate the code fix."

**Evidence:**
PR #71 Duo fixture repairs: the original Duo fixture tests expected `"yellow"` as a player (inherited from an older engine version) and would pass with fixtures using `"yellow"` — but the engine's Duo mode requires `"red"`. The tests were "passing" against broken data. I had to derive the correct player list from `engine.create_game("duo").players` and fix both the fixture and the test simultaneously.

**Prompt/Context Used:**
```
# The flawed TDD-LLM prompt (produced fixtures with wrong players):

"Here are the current Duo fixture files that fail validation:
duo_initial_state.json
duo_opening_sequence.json

Here are the validation tests that the fixtures must pass:
[pasted test assertions checking for 'blue' and 'yellow' players]

Fix the fixtures so that all validation tests pass.
Keep the existing test assertions unchanged."
```

**AI Output:**
```
# The LLM preserved the wrong player colour because the test expected it:

{
  "mode": "duo",
  "players": ["blue", "yellow"],  ← wrong! engine requires blue+red
  "board_size": 14,
  ...
}
```

---

## 4. AI Usage Disclosure

### Tools and Models Used

| Tool / Model | Task | Validation Method |
|---|---|---|
| Claude Sonnet (claude.ai) | Duo fixture repair guidance, CLI fix identification, GUI logic fixes, lint/typing resolution, test parametrisation advice | Full test suite (`./scripts/test.sh`), ruff, mypy, manual GUI inspection |
| GitHub Copilot | Inline debugging assistance, quick code completions, syntax fixes, small refactor suggestions, Windows GUI debugging | Verified through test execution, lint/type checks, and manual inspection |
| Microsoft Copilot | High-level debugging reasoning, guideline evaluation, structured explanations, counterexample identification, documentation of process | Verified through human reasoning, test results, and cross-checking with code behaviour |
| Claude Sonnet (claude.ai) | UX onboarding threshold definition (UI-NOVICE-01), evidence-link validation sweep template | Cross-checked against requirements R-F-30 through R-NF-20 and persona interview data |

### Evaluation Methods

1. **Test suite execution:** Every code change validated by running `./scripts/test.sh` and confirming all tests pass before considering a fix complete. Across PR #84, the suite ran at 379 passed, 3 skipped, 0 failed.
2. **Static analysis:** `ruff` and `mypy` run after every batch of changes; zero errors required before committing. This was integrated into the CI pipeline and validated by PR checks.
3. **Manual GUI inspection:** GUI fixes verified by running `python -m blokus gui` and visually confirming Duo mode shows correct players, board geometry, and score updates in both Classic and Duo modes.
4. **Fixture invariant verification:** Repaired fixtures manually checked against the invariant `placed_squares + remaining_pieces == 21` per player and engine-expected board symbols. Each fixture was also validated by loading it through `GameState.from_dict()`.
5. **Cross-platform testing:** Windows setup guide verified by reproducing all six errors on a Windows machine and confirming each fix resolves the stated symptom.
6. **PR review cycle:** All PRs passed through at least one human collaborator review (magx27 or anatol21) before merging, with agentic code review as an additional automated layer.

### Time Investment

- AI prompting and refinement: ~25 hours
- Reviewing and validating AI outputs: ~15 hours
- Testing and validation (test suite, ruff, mypy, GUI): ~20 hours
- Documentation (Windows guide, threshold table, evidence sweep, reviewing package): ~15 hours
- Team meetings and coordination: ~20 hours

---

## 5. Reflections

### What I Learned

- **Scope constraints in prompts prevent the most common LLM failure mode.** Adding "apply the minimum change necessary; do not introduce new abstractions" to fix-request prompts consistently produced targeted, safe changes rather than over-engineered rewrites. This lesson from the settings dialog fix is now a permanent part of my prompting workflow. I tested this across three subsequent GUI fixes and the pattern held every time.
- **Deterministic tool output makes AI hypotheses redundant.** When pytest, ruff, and mypy all produce specific, actionable error messages, the correct workflow is to feed that output directly to the LLM as context for a targeted fix — not to ask the LLM to hypothesise about what might be wrong. The AutoSD and Explain-Then-Fix guidelines have genuine value, but their value is inversely proportional to the quality of the development environment's feedback signals. In a project with weaker tooling (e.g., no type checker, no linter), those guidelines would be essential.
- **The staged pipeline (Target → Categorise → Generate → Review) is valuable for any multi-area change**, not just formal migrations. Categorising issues before fixing them prevented me from applying the wrong kind of fix (e.g., trying to "fix" a test that was intentionally wrong rather than outdated). The key stage is categorisation — it is the step most developers skip under time pressure, and it is the step that saves the most time. I would explicitly name and sequence the four stages at the beginning of any future multi-area task.
- **Test parametrisation reduces maintenance burden but depends on production architecture.** PR #84 eliminated five duplicate test files by parametrising Classic tests for both modes. This was only possible because the engine's mode abstraction was well-designed — `GameState` exposes `mode`, `board_size`, `players`, and `start_corners` uniformly for both modes. If the architecture had mode-specific code paths instead of configuration-driven ones, parametrisation would have been impossible. Good architecture enables good testing.
- **Tests are not independent oracles.** The TDD-LLM counterexample taught me that tests derived from the same corrupted data as the code under repair will provide a false specification. Before using tests as validation targets for LLM-generated fixes, independently verify the tests against a canonical reference. This is a subtle but critical limitation of the "tests as specification" approach.
- **Evidence documentation must be explicit, not assumed.** Despite 74 commits across 10 PRs, my contributions were not immediately visible from the commit history alone. Creating explicit evidence links and documenting contributions in PR descriptions was essential for making ownership visible. In future projects, I will update OWNERSHIP.md in parallel with code changes.
- **The remediation loop caught errors that tests missed.** The stray `r` token in PR #84 was caught by compilation-level static analysis in the agentic review, not by the test suite. This reinforced that a remediation pipeline should include multiple check types (compilation, static analysis, type checking, tests) arranged from cheapest to most expensive — not just tests alone.
- **LLM over-engineering is a prompt-design problem, not just a review problem.** Counterexample 3 (now replaced with the TDD-LLM counterexample) originally showed that adding "minimum change" constraints to prompts prevented over-engineering at the source. This insight generalises: the most efficient fix for an LLM failure mode is often at the prompt level, not the review level.

### Skills Developed

- **Multi-area debugging** in a real Python project with interconnected engine, CLI, GUI, test, and fixture layers — tracing how a fix in one layer (engine config) cascades through all others. The Duo mode fix required simultaneous understanding of all five layers and their interactions.
- **Structured AI-assisted maintenance** using staged pipelines, human-in-the-loop review, iterative remediation loops, and prompt-level scope constraints. Knowing when to apply each pattern (staged pipeline for multi-area tasks, remediation loop for test consolidation, targeted fix for isolated bugs) is itself an acquired meta-skill.
- **Cross-platform developer onboarding** (Windows vs. Linux environment differences, GTK, librsvg, MSYS2, virtual environments, Tkinter quirks) — documenting issues that are invisible to Linux developers but blocking for Windows contributors. The Windows guide is now the canonical reference for Windows setup in the project.
- **Evidence-based documentation:** linking every claim to a specific, navigable artifact (PR, commit, file path, test name). All 10 PRs and their contributions are explicitly tracked in this portfolio with navigable links.
- **Test architecture design:** choosing between unittest `subTest()` parametrisation and pytest `@pytest.mark.parametrize` based on the test class's inheritance (unittest.TestCase vs. pure pytest) and the project's test runner configuration. The PR #84 consolidation required both approaches in the same repository.
- **Prompt engineering for maintenance tasks:** role-setting, scope constraints, targeted failure context, and constraint definition — each proved independently valuable in different debugging scenarios. The role-setting technique was most valuable for the parametrize fix, while constraint definition was most valuable for the mypy annotation fix.
- **Static analysis integration:** understanding how ruff, mypy, and agentic code reviews fit into a CI pipeline, and how to patch the review infrastructure (static analyzer deleted-file guard) to handle edge cases.

### Future Improvements

- **Apply OWNERSHIP.md updates in parallel with code changes**, not after the fact. Every commit that touches an owned package should be linked to an ownership record at the time it is made. I discovered my name was absent from OWNERSHIP.md despite 74 commits — a preventable documentation gap that required a separate PR to fix after the fact.
- **Use the staged pipeline from the start of any multi-area task.** I applied it naturally but informally. Explicitly naming and sequencing the four stages at the beginning of the Duo work would have made the plan more transparent to teammates and provided a shared vocabulary for discussing progress. A simple one-page plan with the four stages would have sufficed.
- **Add scope constraint instructions as a default to all maintenance fix prompts.** Adding "minimum change; no new abstractions" to every fix prompt costs nothing and prevents an entire class of failure modes. I should not wait for the LLM to over-engineer before adding constraints — they should be in every prompt from the start.
- **Document Windows-specific issues earlier in the project lifecycle.** The six errors I encountered when running the GUI on Windows were predictable given the GTK dependency. A pre-emptive environment compatibility check at the start of Phase 1 would have saved several hours of debugging and produced the Windows guide earlier. Future projects with cross-platform GUI dependencies will get an early Windows validation pass.
- **Invest more time in the Prompt Engineering guideline's constraint-definition step.** My experience with the mypy fix (LLM wanted to use `Any`) and the parametrize fix (LLM wanted to migrate to pure pytest) both showed that constraint definition is as important as context provision in prompt engineering. I will explicitly list constraints (what the fix must not do) alongside context (what the fix must do) in every prompt.
- **Verify test independence before using tests as repair specifications.** The TDD-LLM counterexample showed that tests derived from corrupted data can compound rather than solve problems. In future debugging work, I will first verify tests against a canonical reference (engine source, design docs) before treating them as oracles for LLM-generated fixes.
- **Build a multi-stage validation pipeline into every project.** The remediation loop experience showed that a single test pass is insufficient — compilation-level, static analysis, and type-checking stages catch different error classes. Future projects will have a `scripts/check.sh` that runs all four stages in sequence from cheapest to most expensive.
- **Enhancing Communication Within the Team** This project taught me that aligning early with the team is essential. Discussing which areas each person will handle avoids overlapping work and reduces the risk of unintentionally undoing or conflicting with someone else’s changes.

---

*Template version: 1.0 | Last updated: 2026-05-25 | Student: Nicolas Alejandro Zevallos Chavez*
