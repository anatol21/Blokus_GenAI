# Topic-06_Evaluation.md

> **Guideline Package — Reviewing**  
> Evaluation criteria and scoring rubrics for the five example problems.  
> Use this file to assess both baseline and guideline-driven review attempts.

---

## Team Information
  
**Team Name:** Team 01  
**Topic:** Reviewing  
**Date:** 04.05.2026  
**Authors:**  
Maximilian Alp Grüder 0743914400  
Anatole Lobenko 2187322  
Nicolas Alejandro Zevallos Chavez 2266453 

---

## How to Use This File

This file has three parts:

**Part 1 — General Reviewing Quality Rubric**  
Five universal criteria that apply to every review attempt,
regardless of which problem is being solved. Use these to
score the *process* of reviewing, not just the outcome.

**Part 2 — Per-Problem Evaluation Checklists**  
One checklist per example problem. Each checklist defines
exactly what a correct review must find and what a correct
review action must be. Use these to score the *outcome*.

**Part 3 — Scoring Summary Sheet**  
A combined table to record scores for both baseline and
guideline-driven attempts side by side.

---

---

# PART 1 — General Reviewing Quality Rubric

These five criteria apply to **every review attempt** across
all five problems. Score each criterion as:

- **2** — Strong evidence (meets the strong evidence description)
- **1** — Weak evidence (meets the weak evidence description only)
- **0** — Missing (criterion not addressed at all)

---

## Criterion 1: Rule Correctness

**What it measures:**  
Did the reviewer link findings to a specific rule, requirement,
or specification — not just intuition or visual inspection?

| Score | Evidence |
|-------|----------|
| 2 — Strong | Reviewer named the specific rule violated (e.g., "Blokus rule: same-color side adjacency is illegal") AND linked or referenced a passing/failing test or fixture that confirms the finding |
| 1 — Weak | Reviewer identified an issue but justified it only with "looks wrong" or "seems like a bug" without naming the rule or linking evidence |
| 0 — Missing | No rule reference or justification provided |

**Guideline connection:**  
G4 (CoT decomposition forces rule-by-rule analysis) and G0.1
(static analysis output grounds findings in deterministic rules).

---

## Criterion 2: Reproducibility

**What it measures:**  
Can the review finding be independently verified by someone
else without access to the reviewer's local environment?

| Score | Evidence |
|-------|----------|
| 2 — Strong | Reviewer described a specific test, fixture, script, or round-trip check that reproduces the finding. A second person could run it without asking the reviewer for help |
| 1 — Weak | Reviewer described a way to verify but relied on unstated local setup, a specific IDE, or steps that are not written down |
| 0 — Missing | No verification method described; finding is asserted without a reproduction path |

**Guideline connection:**  
G5 (human-in-the-loop verification must be executable and
documented) and G0.1 (functional checks are reproducible by
definition when scripted).

---

## Criterion 3: Attribution

**What it measures:**  
Is it clear who produced the artifact under review, who
reviewed it, and who is responsible for any follow-up action?

| Score | Evidence |
|-------|----------|
| 2 — Strong | Review record identifies: the artifact reviewed, the reviewer, and the required follow-up action owner. In a team project context, this means the review comment or document names these explicitly |
| 1 — Weak | The reviewer is identifiable but the follow-up owner is implicit or missing |
| 0 — Missing | No ownership information in the review record |

**Guideline connection:**  
G6 (REVIEW.md establishes who owns what review responsibilities)
and G5 (human-in-the-loop requires a named human, not "someone").

---

## Criterion 4: AI-Output Control

**What it measures:**  
If AI was used during the review (to generate findings, fixes,
or summaries), was its output validated before adoption?

| Score | Evidence |
|-------|----------|
| 2 — Strong | Every AI-generated finding or fix has a recorded validation step (e.g., "ran the function, confirmed crash at line 12" or "verified method exists in codebase"). AI usage is logged with model, task, and validation method |
| 1 — Weak | AI output was used and acknowledged but validation is described in vague terms ("checked it," "seemed right") without a concrete step |
| 0 — Missing | AI output was adopted without any documented validation step |

**Guideline connection:**  
G5 (human-in-the-loop is mandatory for AI review outputs)
and the project requirement R-T-05 (AI outputs validated
before adoption).

---

## Criterion 5: Counterexample Quality

**What it measures:**  
Did the review uncover a concrete failure and lead to an
actionable refinement — not just a general observation?

| Score | Evidence |
|-------|----------|
| 2 — Strong | Review identified a specific failure mode (e.g., a coordinate, a field name, a method call) AND proposed or triggered a concrete fix (a test, a corrected fixture, a corrected traceability link) |
| 1 — Weak | Review found a general category of problem ("there might be edge cases") but did not identify a specific instance or propose a concrete action |
| 0 — Missing | Review found no issues, or found issues but produced no follow-up action |

**Guideline connection:**  
G0.2 (triage separates Critical findings that require action
from Nits that do not) and G4 (CoT forces specific reasoning,
not vague concerns).

---

## Part 1 Scoring Summary (General Quality)

Fill in after each review attempt:

| Criterion | Baseline score (0–2) | Guideline-driven score (0–2) |
|-----------|---------------------|------------------------------|
| Rule Correctness | | |
| Reproducibility | | |
| Attribution | | |
| AI-Output Control | | |
| Counterexample Quality | | |
| **Total (max 10)** | | |

---

---

# PART 2 — Per-Problem Evaluation Checklists

Each checklist defines the **correct findings** for that problem.
Each item is worth 1 point. Score independently from Part 1.

---

## Problem 1 Checklist: False-Positive Legality Check

**Artifact under review:** `is_legal_move()` function  
**Review type:** Code logic review  
**Expected guideline application:** G0.1, G0.2, G3, G4, G5

### Correctness Checklist (must find all of these)

| # | Finding | Found? (✅/❌) | Notes |
|---|---------|--------------|-------|
| C1 | Reviewer identified that `board[nr][nc]` is accessed without bounds checking, causing `IndexError` at board edges | | |
| C2 | Reviewer identified that the side-adjacency check operates per square independently, missing the case where `(3,5)` is a side neighbor of one square but a corner neighbor of another | | |
| C3 | Reviewer stated that no test currently covers the overlapping coordinate case (one square has side touch, another square sees only corner touch at the same cell) | | |
| C4 | Review action correctly stated: confirm a negative test exists for the specific overlapping coordinate case | | |

**Correctness score: ___ / 4**

### Quality Checklist (process of reviewing)

| # | Quality check | Met? (✅/❌) | Notes |
|---|--------------|------------|-------|
| Q1 | Reviewer applied G4: used structured CoT decomposition (bounds / side / corner) not just linear code reading | | |
| Q2 | Reviewer applied G0.1: injected static analysis warning about missing bounds check into LLM prompt | | |
| Q3 | Reviewer applied G0.2: classified bounds bug and logic bug as Critical, not Nit | | |
| Q4 | Reviewer applied G5: human verified that proposed fix handles the `(3,4)` coordinate specifically | | |
| Q5 | Reviewer did NOT accept the first LLM finding without verifying it against the actual coordinate scenario | | |

**Quality score: ___ / 5**

### Minimum Acceptance Check

- [ ] The reviewed artifact is named (`is_legal_move()`)
- [ ] The reason for review is stated (potential false-positive legality)
- [ ] At least one concrete checker is recorded (negative test or bounds check)
- [ ] Outcome is one of: accepted / revised / rejected / deferred
- [ ] If revised or rejected: the failure mode is documented (which coordinate, which rule)

**Minimum acceptance met? YES / NO**

---

## Problem 2 Checklist: Duplicate Legal Moves from Symmetric Transforms

**Artifact under review:** `get_legal_moves()` function  
**Review type:** Code logic + semantic correctness review  
**Expected guideline application:** G3, G4, G0.2, G5

### Correctness Checklist

| # | Finding | Found? (✅/❌) | Notes |
|---|---------|--------------|-------|
| C1 | Reviewer identified that `get_all_transforms()` returns up to 8 orientations and symmetric pieces produce identical `frozenset` outputs | | |
| C2 | Reviewer identified that `legal_moves` is a `list`, so duplicate `frozenset` entries are silently retained | | |
| C3 | Reviewer proposed a concrete fix: collect into a `set` instead of a `list`, or de-duplicate transforms before iterating | | |
| C4 | Review action correctly stated: add a fixture using a symmetric piece (e.g., 2×2 square) where the expected unique placement count is N, and the test fails if the list contains more than N entries | | |

**Correctness score: ___ / 4**

### Quality Checklist

| # | Quality check | Met? (✅/❌) | Notes |
|---|--------------|------------|-------|
| Q1 | Reviewer applied G3: stripped or reframed the author's inline comment `# may contain duplicates` before LLM review to prevent anchoring bias | | |
| Q2 | Reviewer applied G4: used pseudocode decomposition to trace the transform→list→no-dedup chain | | |
| Q3 | Reviewer applied G0.2: classified duplicate moves as Critical (affects game correctness), naming as Nit | | |
| Q4 | Reviewer applied G5: human verified that `frozenset` in `set` comparison works correctly for the symmetric piece case | | |
| Q5 | Reviewer did NOT treat the inline author comment as a reason to downgrade the finding from Critical | | |

**Quality score: ___ / 5**

### Minimum Acceptance Check

- [ ] The reviewed artifact is named (`get_legal_moves()`)
- [ ] The reason for review is stated (symmetric piece duplication)
- [ ] At least one concrete checker is recorded (fixture with symmetric piece, expected count)
- [ ] Outcome is one of: accepted / revised / rejected / deferred
- [ ] If revised or rejected: the failure mode is documented (list vs set, specific piece)

**Minimum acceptance met? YES / NO**

---

## Problem 3 Checklist: JSON Fixture Drift

**Artifact under review:** JSON fixture file (flat schema)  
**Review type:** Test data / fixture review  
**Expected guideline application:** G0.1, G4, G0.2, G5

### Correctness Checklist

| # | Finding | Found? (✅/❌) | Notes |
|---|---------|--------------|-------|
| C1 | Reviewer identified that the fixture uses the pre-refactor flat schema and the engine now expects a nested `config` / `state` structure | | |
| C2 | Reviewer identified that `from_dict()` will not raise an error — it silently defaults the missing `config` fields, producing `config.mode = None` | | |
| C3 | Reviewer identified that the round-trip test (`from_dict().to_dict()`) would expose the drift because the output would not match the input fixture | | |
| C4 | Review action correctly stated: update the fixture to the authoritative nested schema AND add a round-trip test that fails when the fixture drifts | | |

**Correctness score: ___ / 4**

### Quality Checklist

| # | Quality check | Met? (✅/❌) | Notes |
|---|--------------|------------|-------|
| Q1 | Reviewer applied G0.1: used schema validator output (or equivalent) as the primary input to the LLM prompt | | |
| Q2 | Reviewer applied G4: used CoT round-trip reasoning (`from_dict` → `to_dict` → compare) to trace the silent default | | |
| Q3 | Reviewer applied G0.2: classified `config.mode = None` as Critical (affects game rule enforcement), field naming as Nit | | |
| Q4 | Reviewer applied G5: correctly noted that the LLM cannot execute the round-trip — a human must run the actual check | | |
| Q5 | Reviewer did NOT accept the fixture as correct simply because `json.loads()` succeeded | | |

**Quality score: ___ / 5**

### Minimum Acceptance Check

- [ ] The reviewed artifact is named (fixture file, named or described)
- [ ] The reason for review is stated (schema refactor, fixture may have drifted)
- [ ] At least one concrete checker is recorded (round-trip test or schema validator)
- [ ] Outcome is one of: accepted / revised / rejected / deferred
- [ ] If revised or rejected: the failure mode is documented (which fields, what the silent default produces)

**Minimum acceptance met? YES / NO**

---

## Problem 4 Checklist: Unsupported Documentation Claim

**Artifact under review:** Documentation claim in `evidence-log.md`  
**Review type:** Documentation / traceability review  
**Expected guideline application:** G3, G4, G0.2, G5

### Correctness Checklist

| # | Finding | Found? (✅/❌) | Notes |
|---|---------|--------------|-------|
| C1 | Reviewer identified that the claim "Covered" is asserted without any link to a test, fixture, or code location | | |
| C2 | Reviewer identified (or proposed to verify) that no test for side-adjacency rejection exists in the test suite | | |
| C3 | Reviewer concluded that the claim is therefore false or unverifiable as written | | |
| C4 | Review action correctly stated: add or correct the traceability entry by linking to an existing test, or creating the missing test and then linking it | | |

**Correctness score: ___ / 4**

### Quality Checklist

| # | Quality check | Met? (✅/❌) | Notes |
|---|--------------|------------|-------|
| Q1 | Reviewer applied G3: treated "Covered" and the confident prose as authority cues and stripped or reframed them before LLM review | | |
| Q2 | Reviewer applied G4: used multi-perspective personas (code reviewer / test engineer / auditor) to surface different dimensions of the missing evidence | | |
| Q3 | Reviewer applied G0.2: classified an unsupported release-gate claim as Critical, not a documentation Nit | | |
| Q4 | Reviewer applied G5: correctly noted that the LLM cannot search the repository — a human must do the actual test suite check | | |
| Q5 | Reviewer did NOT accept "Covered" at face value, even though the prose was well-written | | |

**Quality score: ___ / 5**

### Minimum Acceptance Check

- [ ] The reviewed artifact is named (`evidence-log.md` claim for R-T-04)
- [ ] The reason for review is stated (claim has no evidence link)
- [ ] At least one concrete checker is recorded (test suite search for side-adjacency test)
- [ ] Outcome is one of: accepted / revised / rejected / deferred
- [ ] If revised or rejected: the failure mode is documented (no test exists, claim is unverifiable)

**Minimum acceptance met? YES / NO**

---

## Problem 5 Checklist: Weak AI-Output Validation

**Artifact under review:** AI-generated `list_legal_moves()` function  
**Review type:** AI-output validation review  
**Expected guideline application:** G0.1, G3, G4, G2, G0.2, G5

### Correctness Checklist

| # | Finding | Found? (✅/❌) | Notes |
|---|---------|--------------|-------|
| C1 | Reviewer identified that `piece.get_transforms()` does not exist — the correct call is the module-level function `get_all_transforms(piece)` | | |
| C2 | Reviewer identified that `game_state.board.is_valid(move, current_player)` has the wrong signature — the actual function is `is_legal_move(board, coords, color)` | | |
| C3 | Reviewer identified that `Move(piece, transform, r, c)` references a class that does not exist — the engine uses `frozenset` of `(row, col)` tuples | | |
| C4 | Reviewer concluded that the function will raise `AttributeError` at runtime on the first call | | |
| C5 | Review action correctly stated: validate against the actual API before adoption AND log the AI usage with validation evidence in `docs/ai-usage.md` | | |

**Correctness score: ___ / 5**

### Quality Checklist

| # | Quality check | Met? (✅/❌) | Notes |
|---|--------------|------------|-------|
| Q1 | Reviewer applied G0.1: ran or proposed running a functional check (import or call) as the first step before any cognitive review | | |
| Q2 | Reviewer applied G3: stripped the commit message "looks correct" before LLM review to prevent authority-cue anchoring | | |
| Q3 | Reviewer applied G4: used CoT "list every external call and confirm existence" to systematically catch all three hallucinated APIs | | |
| Q4 | Reviewer applied G2: required structured output (Summary + Critical findings + Validation steps) from the LLM | | |
| Q5 | Reviewer applied G0.2: classified all three hallucinated API calls as Critical; docstring style as Nit | | |
| Q6 | Reviewer applied G5: required a human to run the functional check and log the AI usage — did not accept LLM review alone as sufficient | | |

**Quality score: ___ / 6**

### Minimum Acceptance Check

- [ ] The reviewed artifact is named (AI-generated `list_legal_moves()`)
- [ ] The reason for review is stated (AI-generated code, not yet validated)
- [ ] At least one concrete checker is recorded (functional check / API existence check)
- [ ] Outcome is one of: accepted / revised / rejected / deferred
- [ ] If revised or rejected: all three failure modes are documented (method names and correct alternatives)

**Minimum acceptance met? YES / NO**

---

---

# PART 3 — Scoring Summary Sheet

Use this sheet to record and compare scores across all five problems.

## Attempt Record

**Reviewer name:** _______________  
**Date:** _______________  
**Problems attempted:** _______________

---

## Combined Score Table

### Part 1: General Quality (applies to all problems)

| Criterion | Baseline | Guideline-driven | Δ improvement |
|-----------|----------|-----------------|---------------|
| Rule Correctness (0–2) | | | |
| Reproducibility (0–2) | | | |
| Attribution (0–2) | | | |
| AI-Output Control (0–2) | | | |
| Counterexample Quality (0–2) | | | |
| **Part 1 Total (0–10)** | | | |

---

### Part 2: Per-Problem Correctness + Quality

| Problem | Correctness (baseline) | Correctness (guideline) | Quality (baseline) | Quality (guideline) | Min. acceptance met? |
|---------|----------------------|------------------------|-------------------|--------------------|--------------------|
| P1: False-positive legality (max C:4, Q:5) | /4 | /4 | /5 | /5 | YES / NO |
| P2: Duplicate moves (max C:4, Q:5) | /4 | /4 | /5 | /5 | YES / NO |
| P3: JSON fixture drift (max C:4, Q:5) | /4 | /4 | /5 | /5 | YES / NO |
| P4: Unsupported doc claim (max C:4, Q:5) | /4 | /4 | /5 | /5 | YES / NO |
| P5: Weak AI validation (max C:5, Q:6) | /5 | /5 | /6 | /6 | YES / NO |
| **Part 2 Total** | **/21** | **/21** | **/26** | **/26** | |

---

### Overall Score

| | Baseline | Guideline-driven |
|--|----------|-----------------|
| Part 1 (General quality, max 10) | | |
| Part 2 Correctness (max 21) | | |
| Part 2 Quality (max 26) | | |
| **Grand total (max 57)** | | |

---

## Interpretation Guide

| Grand total | Interpretation |
|-------------|---------------|
| 50–57 | Excellent review — guidelines applied systematically, all critical findings identified |
| 38–49 | Good review — most critical findings identified, some guideline steps skipped |
| 25–37 | Partial review — some findings identified but significant gaps remain |
| 0–24 | Insufficient — critical findings missed, guidelines not meaningfully applied |

> **Expected outcome of the session:**  
> Most participants should score significantly higher in the
> guideline-driven attempt than the baseline. A Δ improvement
> of +10 or more on the grand total indicates the guidelines
> are adding real value. A Δ near zero suggests either the
> baseline was already very strong OR the guidelines were
> not applied meaningfully.

---

---

# PART 4 — Guideline Effectiveness Reflection

After scoring, answer these questions as a group discussion.
These feed directly into the project evidence log and portfolio.

## 4.1 Which guideline added the most value?

| Guideline | Problem where it helped most | What it caught that baseline missed |
|-----------|-----------------------------|------------------------------------|
| G0.1 (Hybrid / Static first) | | |
| G0.2 (Triage + Cap) | | |
| G3 (Strip Bias) | | |
| G4 (CoT + Pseudocode + Personas) | | |
| G5 (Human in the Loop) | | |
| G2 (Output Format) | | |

## 4.2 Where did a guideline fail or add no value?

Record at least one case per session where applying a guideline
produced no improvement or a worse result than the baseline.
This is a **counterexample** — required for individual portfolios.

| Guideline | Problem | What happened | Why it failed or was unnecessary |
|-----------|---------|---------------|----------------------------------|
| | | | |
| | | | |

## 4.3 Were there conflicts between guidelines?

The team identified two known conflicts in the guidelines file:

**Conflict A — LLMs as code reviewers vs. LLMs as orchestrators**  
(G0.1/G1 vs G2.1.11): When did you use the LLM directly for
review vs. as an orchestrator of tools? Did this distinction matter?

Record your observation: _______________

**Conflict B — Human-in-the-Loop vs. Automated Meta-Evaluation**  
G5 requires human sign-off. G1 suggests full automation via agents.
In which problems did full automation feel safe? In which did it
clearly need human judgment?

Record your observation: _______________

---

---

# PART 5 — Minimum Acceptance Reference (Original Criteria)

The original five criteria from the skeleton file are preserved
here for reference. They map to Part 1 of this expanded rubric.

| Original Criterion | Expanded location | Strong evidence | Weak evidence |
|-------------------|------------------|----------------|---------------|
| Rule correctness | Part 1, Criterion 1 | Reviewer linked the rule source and a passing/failing test | Reviewer only said the code "looks right" |
| Reproducibility | Part 1, Criterion 2 | Reviewer replayed scripts, tests, or fixture scenarios | Reviewer relied on unstated local setup |
| Attribution | Part 1, Criterion 3 | Review comments identify who changed and who reviewed | Ownership is implicit or missing |
| AI-output control | Part 1, Criterion 4 | Adopted AI output has a recorded validation step | AI output was copied without validation notes |
| Counterexample quality | Part 1, Criterion 5 | Review uncovered a failure and led to refinement | Review found no issues because nothing concrete was checked |

**Minimum acceptance for any review record (unchanged from original):**

- [ ] The reviewed artifact is named
- [ ] The reason for review is stated
- [ ] At least one concrete checker is recorded
- [ ] The outcome is one of: accepted, revised, rejected, or deferred
- [ ] If revised or rejected, the failure mode is documented

---

## AI Usage Disclosure

This document was produced with AI assistance (Claude Sonnet 4.6).

| Field | Detail |
|-------|--------|
| Model | Claude Sonnet 4.6 |
| Task | Expand skeleton evaluation file into full rubric aligned with example problems and unified guidelines |
| Input artifacts | TOPIC-REVIEWING_evaluation.md (skeleton), TOPIC-REVIEWING_guidelines.md, Topic-06_Example-Problems.md |
| Validation method | Human reviewer must verify that each checklist item correctly reflects the expected finding for its problem, and that scores align with the guideline criteria as defined by the team |
| Adoption decision | Pending human review — team should verify checklist items against their own reading of the problems before using in the session |

---

*Template version: 1.0 | Topic: 06 — Reviewing | Last updated: 2026-04-30*
