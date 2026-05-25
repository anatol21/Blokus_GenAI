# Portfolio_Anatole_Lobenko.md

> **Individual Student Portfolio**  
---

## Student Information

**Student Name:** Anatole Lobenko  
**Team Name:** Review  
**Project:** Blokus Game Engine (Classic + Duo)

---

## 1. Owned Package Contributions

### Package Name: Agentic Review, Automation, Governance, and Release Tooling

**Description:**  
I owned the repository automation and review infrastructure package. This package supports automated PR review, GitHub workflow orchestration, issue/PR intelligence, repair loops, governance checks, CI quality gates, and release candidate packaging.

**Responsibilities:**
- Designed and maintained the agentic PR review workflow, including diff parsing, static analysis, specialist orchestration, provider handling, and structured review artifacts.
- Built GitHub automation scripts for issue triage, PR intelligence, repair loops, failure summaries, governance review, and agent entry points.
- Maintained release and governance tooling.

**Evidence Links:**
- **Commits / PRs:** PR #44, PR #77, PR #32, PR #79, and others
- **Tests:** `tests/test_agentic_review.py`, `tests/test_agentic_code_review_cli.py`, `tests/test_automation.py`, `tests/test_release.py`
- **Documentation:** `docs/review-agent.md` (PR #79)

**Key Contributions:**
- Built an agentic PR review system with diff-scoped static analysis, OpenRouter-backed specialist review, schema validation, and Markdown/JSON outputs.
- Added GitHub automation for agent entry points, issue triage, PR intelligence, repair loops, and failure summaries.

---

### Package Name: Blokus Classic Core Engine

**Description:**  
I primarily owned the Classic Blokus gameplay and engine behavior package. This includes board state, piece placement rules, move validation, legal move generation, turn progression, and game lifecycle behavior.

**Responsibilities:**
- Maintained Classic game-engine behavior, including legal placement validation, turn progression, pass/finish lifecycle, and legal-move listing.
- Added regression coverage for Classic rule edge cases.

**Evidence Links:**
- **PRs:** PR #50 (draft/negative example), PR #52, PR #53, PR #55, PR #56, PR #58, and others
- **Tests:** `tests/test_engine.py`, `tests/test_cli.py`, `tests/test_serialization.py`, and others
- **Documentation:** `docs/engine-gameplay.md` (PR #80), `README.md`, inline docstrings

**Key Contributions:**
- Added and repaired deterministic Classic engine coverage for move validation, opening constraints, illegal move handling, pass/finish lifecycle, and legal-move listing.
- Added regression coverage for Classic rule edge cases, lifecycle transitions, and legal-move generation boundaries.
- Designed and integrated cache-backed occupied-cell handling to improve engine efficiency while preserving rule correctness and serialization safety.

---

## 2. Guideline Applications

### Application 1: Guideline 5 — Multi-Layer Documentation with LLM Summarization and Deterministic Code Analysis

**Source Team:** Maintenance

**Guideline Description:**  
This guideline recommends generating maintainability documentation in layers: module/file summaries, docstrings, user stories, system descriptions, traceability to code, and explicit maintenance warnings for risky behavior.

**Context:**  
I applied the guideline to the agentic review workflow and GitHub helper scripts by generating module summaries, Python docstrings, user stories, and maintenance-risk warnings.

**Application Process:**
1. I adapted the prompt for Python and applied it to relevant files. The first result was only partially useful (PR #72).
2. I revised the prompt closer to the original guideline and tested it across different LLMs. This made the weaknesses easier to identify (PR #73).
3. I refined the prompt and used it to complete the documentation task (PR #74). The relevant prompt is documented in the PR.

**Outcome:**
- **Worked:** Module summaries and selected docstrings improved understandability.
- **Did not work:** User stories, fixed-count risks, and underspecified docstring formats produced unstable or low-value artifacts.
- **Evidence:** PR #72, PR #73, PR #74

**Reflection:**  
The guideline is useful when applied selectively. It should be tested on small, relevant problems first and refined for project-specific documentation standards, especially docstring format, risk-register structure, and when user stories are actually useful.

---

### Application 2: Guideline 4 — Atomic Task Decomposition with Systematic Reasoning

**Source Team:** Coding

**Guideline Description:**  
This guideline recommends decomposing complex requirements into atomic, testable tasks before implementing with AI (or prompting). It also allows using structured task fields such as required implementation, scope, success criteria, tests, and concise rationale instead of relying on hidden chain-of-thought (which is optional, given differences in AI models).

**Context:**  
I applied the guideline to reduce repeated full-board scans in the Classic Blokus engine by introducing an occupied-cell cache per player.

**Application Process:**
1. I first created a broad one-shot implementation attempt, which caused errors (PR #50) and serves as a negative example or a baseline.
2. I decomposed the cache implementation into smaller steps: cache initialization, move-application updates, read-function refactoring, contact/anchor helper refactoring, consistency safeguards, and deserialization cache reconstruction (PR #52, #53, #55, #56, #58).
3. When the review agent flagged issues in an atomic step, I fixed them before continuing.

**Outcome:**
- **Worked:** Smaller diffs made errors easier to localize, review, and repair. The full task was completed successfully.
- **Did not work:** Some steps were too small and caused high generation/review overhead. Atomicity improved review quality but increased cost.
- **Evidence:** PR #50, PR #52, PR #53, PR #55, PR #56, PR #58

**Reflection:**  
I would use atomic decomposition again, but with a cost-proportionality check. “Atomic” should mean independently reviewable and coherent, not merely small. I would also avoid requiring explicit chain-of-thought examples for frontier coding models.

---

### Application 3: Guideline 01 — Define the Testing Objective

**Source Team:** Testing

**Guideline Description:**  
This guideline requires defining the test objective, expected artifact, scope boundaries, negative paths, edge cases, and success criteria before generating or accepting test code.

**Context:**  
I applied the guideline while designing a minimal Duo integration test suite for PR #75. The target artifact was `tests/test_duo_cross_layer_integration.py`, covering seams across `cli.py`, `config.py`, `evaluate.py`, `gui.py`, `gui_assets.py`, and `pieces.py`.

**Application Process:**
1. Defined the objective as minimal cross-layer Duo integration, not broad Duo correctness or serialization coverage.
2. Set scope boundaries: include CLI lifecycle, CLI-to-engine legal-move parity, evaluator scenario replay, GUI mode/asset wiring, and GUI button dispatch.
3. Excluded shared fixture ownership, screenshot/pixel testing, and duplicate serialization/import tests.
4. Refined the tests after feedback by removing duplicated assertions, replacing shared fixture dependency with a temporary scenario fixture, fixing environment issues, and adding a targeted pass-turn rejection case.

**Outcome:**
- **Worked:** The suite provides focused integration coverage and passed with four tests.
- **Did not work:** The first evaluator test assumed an existing fixture was replayable, but it behaved like a saved-state snapshot. It had to be replaced with a temporary scenario fixture.
- **Evidence:** PR #75

**Reflection:**  
The guideline helped prevent overbroad test generation. It is especially useful when integration tests risk duplicating unit tests or becoming dependent on unstable fixtures.

---

## 3. Counterexamples

### Counterexample 1: Low-Value Maintainability Artifacts

**Related Guideline:** Maintenance Guideline 5

**Failure Description:**  
Applying the documentation guideline produced useful module summaries and some docstrings, but also generated inconsistent user stories, generic risk warnings, and unstable docstring structures. The same prompt was tested with Codex, ChatGPT 5.5, and DeepSeek Expert Thinking. The outputs showed that broad maintainability prompts can overgenerate artifacts that are not operationally useful.

**Diagnosis:**
- **Root Cause:** The guideline bundled heterogeneous artifacts under “maintainability documentation” without defining when each artifact is appropriate.
- **Why It Failed:** The prompt encouraged user stories and exactly three risks even when the module did not naturally support them. It also named (sensitive) areas in advance, which anchored the models and (potentially) encouraged restating the prompt (focusing only on the defined areas) rather than independently assessing the code.
- **Boundary Condition:** The guideline fails on small technical infrastructure modules, especially when stakeholder value is indirect and strict documentation format is needed.

**Refinement:**  
The prompt should require evidence-based documentation, enforce PEP 257 / Google-style Python docstrings, generate user stories only for user-facing behavior, and include only actionable risks ranked by likelihood × severity.

**How It Was Tested:**  
I compared an old prompt in PR #73 with the refined prompt in PR #74. The refined prompt produced more stable results: no artificial user stories, clearer docstrings, and fewer but more actionable risks.

**Evidence:**  
Old prompt: https://github.com/anatol21/Blokus_GenAI/pull/73  
Refined prompt: https://github.com/anatol21/Blokus_GenAI/pull/74

**Prompt/Context Used:**  
The original prompt asked the model to generate a module summary, public docstrings, three user stories, and the three riskiest maintenance areas for a Python module with external API calls, credentials, retry logic, and response parsing. A detailed prompt can be found under PR #73.

**AI Output Summary:**  
The model generated useful docstrings but also produced arbitrary user-story roles, generic risk warnings, and inconsistent documentation format. These findings are also documented under PR #73.

---

### Counterexample 2: Atomic Task Decomposition Has Costs

**Related Guideline:** Coding Guideline 4

**Failure Description:**  
The guideline did not define how small an atomic step should be or how to account for fixed implementation-agent overhead. PR #53 changed only a few lines of production logic, but still required a full agent cycle: context loading, planning, test generation, validation, review, and PR synthesis. This cost approximately 0.85 USD / 68K tokens via OpenRouter with GPT-5.2 medium. The full atomic cache sequence across PR #52, #53, #55, #56, and #58 cost approximately 5.10 USD, excluding agentic review. The one-shot PR #50 cost approximately 0.78 USD under the same setting, although it produced errors.

**Diagnosis:**
- **Root Cause:** The guideline optimized for isolation and reviewability, but ignored the (fixed and variable) cost of each full agent cycle.
- **Why It Failed:** Several steps were technically atomic but not economically justified as separate PRs.
- **Boundary Condition:** The guideline fails when a step is small, local, mechanically dependent on neighboring steps, uses the same context/tests, or does not provide enough standalone value to justify separate orchestration.

**Refinement:**  
A step should be atomic enough to review, test, and roll back independently, but not so small that orchestration cost dominates. Related low-risk steps should be bundled when they share context, tests, and failure modes.

**How It Was Tested:**  
Six judge models evaluated PR #52, #53, #55, #56, and #58 on coherence, rollback value, distinct failure mode, and later cost proportionality. The evaluation showed that some technically atomic steps should have been bundled or reordered.

**Evidence:**  
PR #50, PR #52, PR #53, PR #55, PR #56, PR #58  
LLM judge evidence: https://github.com/anatol21/Blokus_GenAI/pull/81

**Prompt/Context Used:**  
For PRs #52, #53, #55, #56, and #58, I decomposed the larger cache-backed occupied-cell task into atomic implementation steps. Each step included both production code and focused unit tests, so the decomposition did not separate implementation from verification. I used a standardized prompt template for each step, adding step-specific context, scope boundaries, expected files, and validation requirements. The step prompts are documented in the relevant PRs.
For additional evaluation, I used multiple LLM judges to review the decomposition strategy and assess whether the atomic PR structure was efficient. The judge experiment and supporting materials are documented in PR #81 and in `Lobenko_Evidence/Counterexample 2 /Blokus_PR_Atomicity_Experiment_Analysis_Report.pdf`.

**AI Output Summary:**
The AI-generated implementation was functionally successful, with occasional refinements after review. However, the experiment showed that the atomic decomposition guideline was not economically optimized. It encouraged very small steps but did not provide clear guidance on how atomic a step should be relative to review cost, implementation value, and context reuse.
At scale, applying this guideline too literally can create unnecessary review overhead and financial cost. The analysis examines this inefficiency: when multiple LLM judges independently recommend bundling adjacent steps, the original atomic decomposition can be treated as evidence that “atomic” without an economic tradeoff model is inefficient. In that sense, the guideline fails because it optimizes for step isolation but not for cost-effective engineering workflow.

---

### Counterexample 3: RepairAgent Over-Expanded a Serialization Fix

**Related Workflow:** Autonomous repair workflow

**Failure Description:**  
A repair agent investigated a serialization/deserialization defect. It correctly found that a serialized payload could re-add an already played piece to `remaining_pieces`, allowing the same piece to be played twice after loading. However, the agent proposed a broader validation plan than the confirmed defect required, including checks for exact `start_corners` matching and strict `board_size` validation.

**Diagnosis:**
- **Root Cause:** The repair workflow generalized from one verified invariant violation into broader loader hardening.
- **Why It Failed:** The workflow did not require a scope-control step before implementation. It mixed the required `history` / `remaining_pieces` invariant repair with optional or contract-changing validation.
- **Boundary Condition:** This failure occurs in cases where many adjacent invariants might look suspicious but are not necessarily part of the confirmed bug.

**Refinement:**  
A repair agent should first identify the minimal invariant needed to prevent the reproduced failure. Additional validation must be classified as required, reasonable hardening, possible overreach, or domain decision. Only the minimal defect fix should be implemented unless broader validation is justified by tests, documentation, or human approval. https://github.com/anatol21/Blokus_GenAI/pull/76

**How It Was Tested:**  
The proposed validation plan was reviewed against the confirmed duplicate-piece defect. The `remaining_pieces` versus `history` consistency check was necessary; exact `start_corners` matching was not necessary and could reject previously accepted custom states.

**Prompt/Context Used:**  
The prompt instructed the agent to investigate `GameState.from_dict`, inspect serialization and move-validation logic, create a minimal failing regression test, apply the smallest safe patch, run targeted tests, and avoid redesigning serialization or changing game rules. The prompt interaction is stored under `Lobenko_Evidence/Counterexample 3_game_state_loading_bug_conversation_evidence.pdf`.

**AI Output Summary:**  
The agent proposed broad loader validation: reject mismatched board size, mismatched start corners, invalid board symbols, unknown/duplicate remaining pieces, inconsistent history, and duplicate piece use.
Only the minimal duplicate-piece patch was implemented.

---

## 4. AI Usage Disclosure

### Tools and Models Used

| Tool / Model | Usage | Validation Method |
|---|---|---|
| Codex / coding agents | Code generation, refactoring, repair tasks, PR implementation | Unit tests, CI, manual diff review, agentic review |
| GPT-5.x / ChatGPT 5.5 | Architecture analysis, documentation, guideline evaluation, review of ambiguous findings | Manual verification, cross-model comparison, tests |
| DeepSeek Expert Thinking | Alternative reasoning and comparison for documentation/guideline outputs | Manual comparison against project needs |
| Claude Sonnet | Additional review and design/test reasoning | Manual comparison, tests |
| OpenRouter | Model access for agentic review and implementation experiments | Cost/token tracking, output inspection |
| GitHub Actions | CI/CD, workflow execution, automated review support | Passing CI checks and manual review |

### Evaluation Methods

Most evaluation was done through repeated code execution, manual code inspection, and LLM-as-judge review. I used unit and integration tests to check Blokus behavior, including legal moves, placement rules, turn handling, serialization, CLI behavior, and Duo integration. Since much of the code and test suite was AI-assisted, I additionally reviewed edge cases with LLMs and an agentic review workflow.
For performance and design validation, I asked GPT-5.x, DeepSeek, and Claude Sonnet to assess the Classic Blokus engine. Their feedback consistently identified repeated board scanning as a weakness and suggested caching occupied cells.

### Time Investment

| Activity | Approximate Time |
|---|---:|
| AI prompting and refinement | 50 hours |
| Reviewing AI outputs | 50 hours |
| Testing and validation | 15 hours |
| Documentation | 30 hours |

---

## 5. Reflections

### What I Learned

- LLMs are useful for early prototyping, but generated code must be reviewed and tested before becoming part of the codebase.
- LLMs can generate code and tests quickly, but the tests may miss important edge cases or merely confirm the generated implementation.
- Agentic coding benefits from agentic review because review automation can detect inefficient or lazy generation patterns at similar speed.
- Engineering judgment remains important. Blind generation can become inefficient when token cost, review cost, and debugging cost are considered.
- Some small changes are faster and cheaper for a human to make directly.

### Skills Developed

- Prototyping and AI-assisted software development.
- CI/CD and GitHub workflow automation.
- Critical evaluation of LLM-generated code, tests, documentation, and reviews.
- Agent-based software-engineering workflows.
- Cost-aware prompting and task decomposition.

### Future Improvements

- Define project-wide standards earlier, especially for documentation, risks, tests, and review output.
- Use less blind code generation and more targeted human implementation for small local changes.
- Use agentic workflows more for review, documentation, governance, and maintenance.
- Enforce agentic review earlier in the project.
- Maintain central registers for risks, user stories, requirements, prompts, and guideline applications.
- Start the portfolio earlier and update it continuously during the project.
