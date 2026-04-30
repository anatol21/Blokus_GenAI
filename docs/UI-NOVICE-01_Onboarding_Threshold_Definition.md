**Task:** [Execution] UI-NOVICE-01: UI onboarding thresholds need refinement (design-only)  
**Status:** Design complete — ready for execution review  
**Assignee:** Owner 3  
**Reviewer:** Owner 1  
**Date:** 2026-04-22  
**Linked scenarios:** UI-NOVICE-01, ACC-01, TUT-01, TUT-03, TUT-05, TUT-06, TUT-08

---

## How This Document Was Produced (AI + Guidelines Applied)

This document was produced by applying Group 1's Requirements Guidelines
to the existing project material. The process followed four steps:

**Step 1 — (Persona-Based Elicitation):**
The three validated personas from the simulated interview set
(Andrea, Emily, Lukas) were used as the primary lens for deriving
thresholds. Each threshold is anchored to at least one persona.
Sophie was excluded as primary evidence per the interview evaluation
judgment (PDF, p.2: "not recommended as primary RE evidence").

**Step 2 — (Ambiguity Detection):**
All onboarding requirements (R-F-30 through R-F-36, R-NF-06,
R-NF-10, R-NF-18 through R-NF-20) were reviewed for vague language.
Ambiguous terms such as "within minutes", "minimal reading", and
"few steps" were flagged and resolved into concrete measurable values.
Conflicting goals were also identified and resolved (see Section 4).

**Step 3 — (Chain-of-Thought + Reproducibility):**
Each threshold was derived through explicit reasoning: persona need →
requirement text → ambiguity resolution → measurable criterion.
This chain is preserved in the "Derivation" column of the threshold
table so the reasoning is inspectable and reproducible.

**Step 4 — (Human-in-the-Loop):**
This document is a design artifact, not a final verdict.
A human reviewer (Owner 1) must validate the thresholds before
execution (Task 3) begins. Open questions that require human
judgment are listed in Section 5.

---

## 1. Persona Reference Summary

These personas were used to derive thresholds. They come from the
simulated interview set evaluated in Requirements_Elicitation_Judgment.pdf.

| Persona | Profile | Onboarding Priority | Interview Quality |
|---------|---------|--------------------|--------------------|
| **Andrea** | Low technical confidence, nervous beginner, wants to learn the game to play with grandchildren | Calm pace, visible guidance, explicit first-move help, undo safety net | 4-5/5 across criteria — strongly usable |
| **Emily** | Casual household organiser, mixed-skill family group, time-constrained | Fast setup, skippable tutorial for experienced players, rules explainable under 1 minute | 4-5/5 across criteria — strongly usable |
| **Lukas** | Experienced player, wants minimal friction, dislikes mandatory walkthroughs | Lightweight onboarding, power users not blocked, optional controls only | 3-4/5 — usable with caution (slightly over-specified) |
| **Daniel** | Strategic, technically confident, focused on depth and practice | Learning support must be non-intrusive, advanced features should not be delayed by tutorial | Not primary onboarding evidence — referenced for non-intrusiveness only |

---

## 2. Requirements Cluster — Onboarding Scope

The following requirements from `requirements.md` form the onboarding
acceptance cluster. All thresholds in Section 3 trace back to at least
one of these IDs.

| ID | Requirement Text | Type | Primary Persona |
|----|-----------------|------|----------------|
| R-F-30 | System shall provide a short onboarding flow for first-time users | Functional | Andrea, Emily |
| R-F-31 | Tutorial shall explain basic rules through interaction, not long text | Functional | Andrea, Emily |
| R-F-32 | Tutorial shall explicitly guide the first move | Functional | Andrea |
| R-F-33 | Tutorial should visually highlight valid starting placement | Functional | Andrea |
| R-F-34 | Tutorial shall allow beginners to learn step by step at a slow pace | Functional | Andrea |
| R-F-35 | System should offer optional refresher guidance during play | Functional | Andrea, Emily |
| R-F-36 | Tutorial should be skippable or lightweight for experienced users | Functional | Emily, Lukas |
| R-NF-06 | Interface shall be simple and immediately understandable for novice users | Non-functional | Andrea, Emily |
| R-NF-10 | Product shall support users with limited technical confidence through clear, reassuring UI patterns | Non-functional | Andrea |
| R-NF-18 | A new user should be able to begin meaningful play within minutes | Non-functional | Andrea, Emily |
| R-NF-19 | Rules should be understandable with minimal reading | Non-functional | Emily |
| R-NF-20 | Learning support should be optional and non-intrusive for experienced players | Non-functional | Lukas, Daniel |

---

## 3. Threshold Table — Measurable Acceptance Criteria

This is the core output of Task 2. Each row resolves a previously
vague requirement into a concrete, testable pass/fail criterion.

> **How to read this table:**
> - **Pass** = the threshold that must be met for the requirement to be accepted
> - **Fail** = the condition that definitively fails the requirement
> - **Needs refinement** = result is between pass and fail; not a blocker but must be logged
> - **Derivation** = the reasoning chain from persona → requirement → number

---

### 3.1 Time and Steps to First Valid Move

| ID | What is measured | Pass threshold | Needs refinement | Fail condition | Persona | Linked requirement | Derivation |
|----|-----------------|---------------|-----------------|----------------|---------|-------------------|------------|
| THR-01 | Time from game launch to first successfully placed piece (novice, no prior Blokus knowledge) | ≤ 3 minutes | 3–5 minutes | > 5 minutes | Andrea | R-NF-18 | R-NF-18 says "within minutes." Andrea's interview shows she needs visible step-by-step guidance. 3 min is achievable with clear guidance; beyond 5 min indicates the onboarding is not working. |
| THR-02 | Number of distinct user actions (clicks, key presses, commands) required to reach first valid move from launch | ≤ 7 actions | 8–12 actions | > 12 actions | Emily | R-F-30, R-NF-18 | R-F-30 requires "few steps." Emily wants sessions to start quickly for a household group. 7 actions is generous but realistic for a CLI-based flow; beyond 12 suggests onboarding is too complex. |
| THR-03 | Number of lines of text a novice must read before they can place their first piece | ≤ 10 lines | 11–20 lines | > 20 lines | Emily, Andrea | R-NF-19 | R-NF-19 says "minimal reading." Emily's interview states rules must be explainable "in under a minute." 10 lines at average reading speed takes ~20 seconds; beyond 20 lines breaks this expectation. |

---

### 3.2 First-Move Guidance Visibility

| ID | What is measured | Pass threshold | Needs refinement | Fail condition | Persona | Linked requirement | Derivation |
|----|-----------------|---------------|-----------------|----------------|---------|-------------------|------------|
| THR-04 | Is the valid starting placement location explicitly shown or highlighted before the first move? | Yes — the valid corner(s) are indicated without the player having to ask | Indicated only after an error | Not indicated at any point; player must guess | Andrea | R-F-32, R-F-33 | R-F-32 requires explicit first-move guidance. R-F-33 requires visual highlighting. Andrea's interview specifically flags "first move must be visibly indicated" as a proto-acceptance criterion in the evaluation PDF. |
| THR-05 | Does the system explain what an invalid first move means if the player makes one? | Yes — error message names the rule that was violated (e.g., "must start from a corner") | Error shown but generic ("invalid move") | No feedback at all | Andrea | R-F-27, R-NF-06 | Andrea needs reassurance and explanation. A generic error forces her to guess what went wrong, which breaks the "immediately understandable" standard of R-NF-06. |
| THR-06 | Is the current player's turn clearly indicated at all times during onboarding? | Yes — current player is always visible on screen without scrolling or extra input | Visible only after a specific command | Not visible | Emily, Andrea | R-F-25, R-NF-06 | R-F-25 requires turn indication. Both Emily and Andrea would experience confusion in a multi-player family session if turn ownership is unclear. |

---

### 3.3 Tutorial Pace and Interaction Style

| ID | What is measured | Pass threshold | Needs refinement | Fail condition | Persona | Linked requirement | Derivation |
|----|-----------------|---------------|-----------------|----------------|---------|-------------------|------------|
| THR-07 | Does the tutorial explain rules through doing (interactive) rather than a block of text upfront? | Yes — each rule is introduced at the moment it is needed during play | Mixed — some interactive, some upfront text | No — all rules presented as a text block before play begins | Andrea | R-F-31 | R-F-31 requires interaction-based teaching. Andrea's interview shows she learns better through doing. A text dump before play begins is the explicit fail condition for this requirement. |
| THR-08 | Can a novice pause or slow down during the tutorial without losing progress? | Yes — tutorial allows any pause and resumes from the same point | Pause allowed but resumes from start | No pause mechanism exists | Andrea | R-F-34 | R-F-34 requires "step by step at a slow pace." Andrea needs to feel calm, not rushed. Losing progress on pause is a direct violation of this requirement. |
| THR-09 | Is optional refresher guidance available during active play without interrupting the game? | Yes — accessible via a single command or toggle, does not disrupt turn flow | Available but requires navigating a menu | Not available during play | Andrea, Emily | R-F-35 | R-F-35 requires optional mid-game guidance. Emily wants it non-intrusive; Andrea wants it available. A menu-based path adds too much friction for Andrea while still satisfying Emily if it exists at all. |

---

### 3.4 Tutorial Skippability and Non-intrusiveness

| ID | What is measured | Pass threshold | Needs refinement | Fail condition | Persona | Linked requirement | Derivation |
|----|-----------------|---------------|-----------------|----------------|---------|-------------------|------------|
| THR-10 | Can an experienced player skip the entire tutorial in 1 action? | Yes — single skip command or option at start | Skip exists but requires 2–3 steps | Tutorial is mandatory with no skip option | Lukas, Emily | R-F-36, R-NF-20 | R-F-36 says tutorial should be skippable. Lukas explicitly wants "lightweight onboarding controls." Emily wants experienced family members to start faster. Requiring more than 1 action to skip is unnecessary friction for this group. |
| THR-11 | Does learning support (hints, tutorial prompts) appear without being requested by the experienced player? | No — learning support is opt-in only, never appears unless requested | Appears once per session but is dismissable | Appears repeatedly and cannot be permanently dismissed | Lukas, Daniel | R-NF-20 | R-NF-20 requires learning support to be "optional and non-intrusive." Both Lukas and Daniel flag mandatory walkthroughs and coaching as blockers. Any unrequested appearance of tutorial content for an experienced player fails this requirement. |

---

### 3.5 Reassurance and Recovery

| ID | What is measured | Pass threshold | Needs refinement | Fail condition | Persona | Linked requirement | Derivation |
|----|-----------------|---------------|-----------------|----------------|---------|-------------------|------------|
| THR-12 | After an invalid move, can the player immediately retry without restarting or losing state? | Yes — player is returned to the same turn with board unchanged | Player must re-enter state but board is preserved | Game crashes or session must be restarted | Andrea | R-NF-06, R-NF-10 | R-NF-10 requires "reassuring and predictable UI patterns." Andrea's biggest fear is making an irreversible mistake. Recovery from an invalid move must be immediate and visible to pass. |
| THR-13 | Does the interface use clear, readable text with no technical jargon in onboarding messages? | Yes — all messages use plain language; no engine error codes or internal terms exposed | Mostly plain but occasional technical terms appear | Error codes, stack traces, or internal identifiers are visible to the user | Andrea | R-NF-06, R-NF-07 | R-NF-06 requires "immediately understandable" language. R-NF-07 requires "readable text." Andrea has low technical confidence — any exposed internal term breaks her trust in the interface. |

---

## 4. Conflict Resolution

This section addresses the conflicting goals identified in the
requirements cluster (as required by the Task 2 checklist item:
"Identify conflicting goals such as calm and step-by-step versus
fast and lightweight").

---

### Conflict 1: Andrea wants slow and calm vs. Emily wants fast and quick-start

**Tension:** R-F-34 (step-by-step slow pace for Andrea) conflicts with
R-NF-18 (begin play within minutes for Emily).

**Resolution:** These goals are compatible if the tutorial is adaptive.
The proposed resolution is:
- Default path: guided, step-by-step (serves Andrea, THR-07, THR-08)
- Skip path: single-action bypass to immediate play (serves Emily and Lukas, THR-10)
- The 3-minute threshold in THR-01 applies only to the guided default path
- An experienced player using the skip path should reach first move in ≤ 1 minute

**Threshold impact:** THR-01 threshold of 3 minutes applies to the
guided novice path only. The skip path has no time threshold because
experienced players are not the primary onboarding subject.

---

### Conflict 2: Andrea wants persistent optional reminders vs. Lukas wants zero unprompted guidance

**Tension:** R-F-35 (optional refresher guidance available) conflicts
with R-NF-20 (learning support must not appear unrequested).

**Resolution:** These goals are compatible through opt-in design.
- Guidance must never appear automatically (serves Lukas, Daniel — THR-11)
- Guidance must always be available on demand (serves Andrea, Emily — THR-09)
- The single-command access threshold (THR-09) satisfies both: it is
  never intrusive, but always reachable

**Threshold impact:** THR-09 and THR-11 together define the boundary.
Any implementation that satisfies both simultaneously resolves the conflict.

---

### Conflict 3: Step-by-step interaction vs. minimal reading

**Tension:** R-F-31 (interaction-based tutorial) could conflict with
R-NF-19 (rules understandable with minimal reading) if interactive
prompts are implemented as text-heavy instructions.

**Resolution:** The interaction requirement takes precedence.
Prompts must be short (≤ 2 sentences per interaction step) and
action-oriented. THR-03 (≤ 10 lines total before first move) is
the binding constraint that prevents interactive prompts from
becoming a text wall.

---

## 5. Open Questions (Blocking Execution)

These questions must be answered by the team before Task 3
(execution of the onboarding test) can proceed.
Per G1 (Human-in-the-Loop), these require human judgment
and cannot be resolved by AI alone.

| # | Open question | Blocks which threshold | Owner |
|---|--------------|----------------------|-------|
| OQ-01 | Is the CLI-based interface the final delivery format for Phase 1 onboarding? If yes, visual highlighting (R-F-33) must be implemented via color codes or ASCII markers. If no, THR-04 needs revision. | THR-04 | Owner 1 to confirm with team lead |
| OQ-02 | Does "launching the game" count from the moment the CLI command is run, or from the moment the player sees the first prompt? This affects how THR-01 and THR-02 are measured. | THR-01, THR-02 | Owner 3 to define with Owner 1 |
| OQ-03 | Is a computer opponent (R-F-09) present during onboarding, or is the novice test run in solo/tutorial mode only? This changes the number of actions needed and the turn-indicator test (THR-06). | THR-02, THR-06 | Owner 1 |
| OQ-04 | Is the undo function (R-F-28) in scope for Phase 1 CLI? If yes, THR-12 recovery standard is already partially met. If no, recovery depends entirely on error message quality. | THR-12 | Team lead to confirm Phase 1 scope |
| OQ-05 | What is the agreed novice tester profile for executing UI-NOVICE-01? A real person unfamiliar with Blokus, or a simulated persona run by a team member? The test validity is significantly different. | All THR rows | Owner 3 to propose; Owner 1 to approve |

---

## 6. Unified Novice Acceptance Definition

This is the single summary definition of what "successful novice
onboarding" means for this project, combining all thresholds above.

> **A novice user (no prior Blokus knowledge, low technical confidence)
> successfully completes onboarding if and only if:**
>
> 1. They place their first valid piece within **3 minutes** and **7 actions**
>    from game launch, using only the information provided by the system.
> 2. The system explicitly showed them where to place their first piece
>    **before** they were asked to act (THR-04).
> 3. They read **10 lines or fewer** of text before reaching their first move (THR-03).
> 4. At least one invalid move attempt returned a **plain-language explanation**
>    of the rule violated (THR-05).
> 5. After any invalid move, they were able to **retry immediately** without
>    losing state (THR-12).
> 6. No technical jargon, error codes, or internal identifiers appeared
>    in any message they received (THR-13).
>
> **An experienced player (Lukas/Daniel profile) completes the skip path if:**
>
> 1. They bypassed the tutorial in **1 action** and reached their first
>    move within **1 minute** (THR-10).
> 2. No tutorial prompt appeared without them requesting it (THR-11).

---

## 7. Traceability Summary

| Threshold ID | Requirement IDs | Persona | Scenario ID |
|-------------|----------------|---------|-------------|
| THR-01 | R-NF-18 | Andrea, Emily | UI-NOVICE-01, TUT-01 |
| THR-02 | R-F-30, R-NF-18 | Emily | UI-NOVICE-01, TUT-01 |
| THR-03 | R-NF-19 | Emily, Andrea | UI-NOVICE-01, TUT-03 |
| THR-04 | R-F-32, R-F-33 | Andrea | UI-NOVICE-01, TUT-01 |
| THR-05 | R-F-27, R-NF-06 | Andrea | UI-NOVICE-01, ACC-01 |
| THR-06 | R-F-25, R-NF-06 | Emily, Andrea | UI-NOVICE-01 |
| THR-07 | R-F-31 | Andrea | TUT-01, TUT-03 |
| THR-08 | R-F-34 | Andrea | TUT-03, TUT-05 |
| THR-09 | R-F-35 | Andrea, Emily | TUT-05, TUT-06 |
| THR-10 | R-F-36, R-NF-20 | Lukas, Emily | TUT-08 |
| THR-11 | R-NF-20 | Lukas, Daniel | TUT-08 |
| THR-12 | R-NF-06, R-NF-10 | Andrea | ACC-01, UI-NOVICE-01 |
| THR-13 | R-NF-06, R-NF-07 | Andrea | UI-NOVICE-01, ACC-01 |

---

## 8. AI Usage Disclosure

This document was produced with help of AI assistance (Claude Sonnet 4.6)
following Group 1 Requirements Guidelines.

| Field | Detail |
|-------|--------|
| Model | Claude Sonnet 4.6 |
| Task | Derive measurable onboarding thresholds from requirements and persona data |
| Prompt category | Persona-based elicitation (G2) + ambiguity resolution (G3) + chain-of-thought derivation (G4) |
| Input artifacts | requirements.md, requirements_source_matrix.md, Topic-01_Guidelines.md, Requirements_Elicitation_Judgment.pdf |
| Validation method | Human reviewer (Owner 1) must review Section 3 thresholds and resolve open questions in Section 5 before execution |
| Adoption decision | Pending human review — not final until Owner 1 sign-off |

**Known AI limitations applied here (per G1 and G4):**
- The threshold numbers (3 min, 7 actions, 10 lines) are reasoned estimates
  derived from persona descriptions, not from empirical user testing.
  They should be treated as starting hypotheses, not proven standards.
- The AI may have missed lateral conflicts between requirements.
  Human review should specifically check Section 4 for completeness.

---

*Document version: 1.0 | Created: 2026-04-22 | Status: Awaiting Owner 1 review*
