# OWNERSHIP.md

> **Team Project Ownership Table (who did what)**  
> *Document individual contributions and responsibilities for the Blokus Game Engine project.*

---

## Team Information

**Team Name:** `[Your Team Name/ID]`  
**Project:** Blokus Game Engine (Classic + Duo)  
**Date:** `[Last Updated Date]`  
**Team Members:** `[Student Name 1, Student Name 2, Student Name 3, ...]`

---

## Work Package Ownership

| Package Name | Owner | Responsibilities | Acceptance Criteria | Evidence Links |
|--------------|-------|------------------|---------------------|----------------|
| Architecture Diagrams | Grueder | creating class, sequence and component diagrams | `[Specific acceptance criteria]` | Portfolio_mgrueder.md Section ### Package Name: Architecture Diagrams - **Evidence Links** |
| Serialization | Grueder | ensure export and import functionality works, Generate tests for export and import functionality, Generate legality checker for the import functionality.| tests are successfull and seriality is ensured throughout the game sequence. | import_json_tests/*, tests/test_persistence_extended.py, tests/test_serialization_integrity.py |
| GUI Optimizations | Grueder | The two double-layer problem, Programmatic cards painted over pre-baked SVG artwork, Button shapes drawn over pre-baked button artwork, Remove the unaligned and strange-looking "tokens" from on top of the icons for the text "Classic" and "GUI", Either correct the adjustment of the yellow circle showing whose turn it is, or replace it with another solution, Even up the sizes of the robot icons on the board. | manual evaluation of UI | https://github.com/anatol21/Blokus_GenAI/pull/61 |
| Harness / Evaluation / Evidence / UX-Threshold | Grueder | Input Translation, Input Validation, Evaluation Harness Design, Regression Diagnosis, Scoring Mechanics, State Validation | generated tests to ensure the requirements are fulfilled.  | Portfolio_mgrueder.md Section ### Package Name: Harness / Evaluation / Evidence / UX-Threshold - **Evidence Links** |
| CLI (`src/blokus/cli.py`, `src/blokus/render.py`) | Lobenko / Zevallos | Implement CLI commands (new, play, import, export, suggest, legal-moves), output formatting, mode-consistent behaviour | - CLI commands match documented contracts<br>- `blokus new --mode duo` works identically to Classic<br>- Import/export handles success and failure paths<br>- Error messages are informative | `tests/test_cli.py`, `tests/test_cli_import.py`, `docs/json-contracts.md` |
| Agentic Review, Automation, Governance, and Release Tooling | Lobenko | Designed and maintained agentic PR review workflow, diff parsing, static analysis, specialist orchestration, provider handling, structured artifacts, GitHub automation scripts, repair loops, governance checks, CI quality gates, and release tooling | • PR review workflow produces Markdown/JSON review artifacts<br>• Review system supports diff-scoped static analysis and specialist review<br>• Automation supports agent entry points, issue triage, PR intelligence, repair loops, and failure summaries<br>• Governance/release tooling is covered by tests and documentation | **PRs:** #44, #77, #32, #79<br>**Tests:** tests/test_agentic_review.py, tests/test_agentic_code_review_cli.py, tests/test_automation.py, tests/test_release.py<br>**Docs:** docs/review-agent.md |
| Blokus Classic Core Engine | Lobenko | Maintained Classic game-engine behavior, board state, piece placement rules, legal move validation, legal move generation, turn progression, pass/finish lifecycle, serialization safety, and regression coverage for Classic rule edge cases | • Classic move validation enforces opening, corner-touch, and illegal placement rules<br>• Turn progression, pass, finish, and legal-move listing behavior are deterministic<br>• Occupied-cell cache improves engine efficiency without breaking serialization correctness<br>• Core gameplay behavior is covered by regression tests and gameplay documentation | **PRs:** #50, #52, #53, #55, #56, #58, #80<br>**Tests:** tests/test_engine.py, tests/test_cli.py, tests/test_serialization.py<br>**Docs:** docs/engine-gameplay.md, README.md, inline docstrings |
| UX Onboarding & Evidence Traceability | Zevallos | Define measurable UX acceptance criteria, create evidence-link validation sweep, author reviewing evaluation rubrics | - UI-NOVICE-01 threshold table has 13 measurable criteria linked to R-F-30–R-NF-20<br>- Evidence sweep covers 6 scenarios (TEST-05, TEST-08, DOC-06, EVAL-01/02/03)<br>- Reviewing evaluation docs are usable for peer-review workshops | `docs/UI-NOVICE-01_Onboarding_Threshold_Definition.md`, `docs/Evidence_Link_Validation_Sweep.md`, PR #43, PR #51 |
| Cross-Platform Support (Windows) | Zevallos | Document Windows-specific setup errors, provide step-by-step debugging guide for GTK/librsvg/venv issues | - All 6 Windows errors documented with symptom, cause, and fix<br>- Guide is reproducible on a fresh Windows machine | `Windows_GUI_Setup_and_Debugging_Guide.md`, PR #67 |
| Duo Mode Integration (Fixtures, CLI parity, GUI compatibility) | Zevallos | Repair Duo fixtures, align CLI behaviour for Duo, fix GUI player/board logic for Duo, resolve lint/typing issues | - All Duo fixtures satisfy `placed_squares + remaining_pieces == 21` per player<br>- `blokus new --mode duo` outputs to stdout by default<br>- GUI shows `["blue", "red"]` in Duo mode<br>- Duo board metrics recomputed on mode switch<br>- 0 ruff/mypy errors | PR #71, PR #84, `fixtures/states/duo_initial_state.json`, `fixtures/scenarios/duo_opening_sequence.json` |
| Test Architecture & Consolidation | Zevallos | Parametrise test suite to cover both Classic and Duo modes without duplication, maintain test health | - 5 Duo test files merged into parametrised Classic tests<br>- Coverage maintained: 379 passed, 3 skipped, 0 failed<br>- Parametrisation uses `self.subTest()` for unittest and `@pytest.mark.parametrize` for pytest files | PR #84, `tests/test_persistence.py`, `tests/test_serialization.py`, `tests/test_cli_import.py`, `tests/test_persistence_extended.py`, `tests/test_serialization_integrity.py` |
| GUI (`src/blokus/gui.py`, `src/blokus/gui_support.py`) | Lobenko / Grueder / Zevallos | Implement graphical interface, mode switching, score display, board rendering, SVG asset management | - Classic and Duo modes render correctly<br>- Score updates after every move<br>- Mode switch recomputes board geometry and player list<br>- Visual inconsistencies eliminated | `tests/` (GUI tested manually), PR #61, PR #68, PR #71 |



---

> **Note:** Use these as examples only. Define additional packages relevant to your team's implementation (i.e., splitting of tasks depend on team size etc.).

---

## Instructions for Use

1. **Replace all `[...]` placeholders** with your team's specific content
2. **List all major work packages** in your project
3. **Assign primary ownership** to team members (one owner per package)
4. **Include specific acceptance criteria** that can be verified
5. **Link to evidence** (commits, tests, documentation) for each package
6. **Keep this updated** throughout the semester as work progresses
7. **Submit as `OWNERSHIP.md`** in your project repository

---

## Notes

- Each team member should have at least one primary ownership package
- Other team members can contribute to any package, but the primary owner is responsible for reviewing and ensuring correctness
- Evidence links should point to specific commits, pull requests, or files in your repository
- Update this document regularly (e.g., after each sprint or milestone)

---

*Template version: 1.0 | Last updated: 24 February 2026*
