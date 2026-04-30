# Topic-06_Example-Problems.md

> **Guideline Package — Reviewing**  
> Example problems for hands-on practice during the guideline session.

---

## Team Information

**Team Name:** `[Your Team Name/ID]`  
**Topic:** `Reviewing`  
**Date:** `[Submission Date]`  
**Authors:** `Nicolas Zevallos, Maximilian Alp Grüder, Anatole...`

---

## 1. Guidelines Quick Reference

The table below maps each example problem to the unified guidelines
it exercises. Use this as a lookup during the hands-on session.

| ID | Guideline Title | Core Purpose |
|----|----------------|-------------|
| G0.1 | Combine Static Analysis with LLM Reviews (Hybrid Approach) | Run static tools first; inject output into LLM prompt for grounded review |
| G0.2 | Calibrate Triage and Cap Findings | Define Critical / Supporting / Nit hierarchy; cap minor comments |
| G1 | Implement Agentic AI for Orchestration | Delegate review sub-tasks to specialized agents |
| G2 | Give an Output Format and Constraints | Enforce structured, human-readable review output |
| G3 | Strip Misleading or Bias-Inducing Comments | Remove authority cues before LLM review |
| G4 | Structured Prompting, Personas, Pseudocode and CoT | Use step-by-step reasoning and multi-perspective personas for complex reviews |
| G5 | LLM as a Judge + Human in the Loop | Use LLM to flag; human decides on high-stakes items |
| G6 | Maintain a Separate REVIEW.md | Keep review rules in a dedicated file separate from general project docs |

---

## 2. How to Use These Problems

1. **Baseline attempt** — Try each problem without applying any guideline.
   Record what you noticed and what you missed. Time yourself.

2. **Guideline-driven attempt** — Apply the guidelines listed in the
   problem header. Record your prompt, the LLM's output, and what changed.

3. **Compare** — Did the guideline-driven attempt catch more issues?
   Were there false positives? Did structured output help?

4. **Evaluate** — Use `Topic-06_Evaluation.md` to score both attempts
   against the provided evaluation criteria.

> **Time estimate per problem:** 10–15 minutes  
> **Programming language:** Python (Blokus engine context)

---

---

## Problem 1: False-Positive Legality Check

### Context

In the Blokus engine, a move is **legal** only if the placed piece
touches at least one existing same-color piece at a **corner**,
and shares **no edge** (side) with any same-color piece.

A false positive occurs when the engine accepts a move that
visually looks diagonal-only but actually also shares an edge
with an existing piece — or vice versa: rejects a move that is
actually legal.

---

### The Code Under Review

```python
def is_legal_move(board, piece_coords, color):
    """
    Returns True if placing piece_coords on the board is legal for color.
    Piece_coords: list of (row, col) tuples representing the new piece squares.
    """
    has_corner_touch = False

    for (r, c) in piece_coords:
        # Check for edge (side) adjacency with same color — illegal
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if board[nr][nc] == color:
                return False  # side touch → illegal

        # Check for corner adjacency with same color — required
        for dr, dc in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            nr, nc = r + dr, c + dc
            if board[nr][nc] == color:
                has_corner_touch = True

    return has_corner_touch
```

---

### The Bug

A board state exists where one square of the new piece is at `(3, 4)`.
An existing same-color piece occupies `(3, 5)` — directly to the right,
a **side adjacency**. However, the same square `(3, 5)` is also
diagonally adjacent to another square of the new piece at `(2, 5)`,
making it appear to be a corner touch when inspected visually.

The engine returns `True` (legal) for this move even though a side
touch exists. No test currently covers this exact coordinate overlap.

---

### Review Task

You are conducting a code review of this function.

**Baseline (no guideline):**
Read the code and describe any issues you find.

**Guideline-driven attempt:**
Apply the guidelines below in sequence.

**Step 1 — G0.1 (Hybrid Approach):**
Pretend a static analyzer has flagged the following on this function:

```
Line 11: Loop variable (nr, nc) not bounds-checked before board access.
Line 11: Potential IndexError if piece is placed at board edge (row/col = 0).
```

Inject this into your LLM prompt alongside the code diff and ask for a review.

**Step 2 — G4 (Structured Prompting + CoT):**
Use the following prompt structure:

```
You are a senior game-engine engineer and a correctness expert.

Step 1 — Convert the function's logic to pseudocode.
Step 2 — Decompose the pseudocode into: 
          (a) bounds checking, 
          (b) side-adjacency detection, 
          (c) corner-adjacency detection.
Step 3 — Analyze each part for logical flaws and edge cases.
Step 4 — Provide a final review from two perspectives:
          (a) correctness reviewer: does the function enforce all Blokus rules?
          (b) test engineer: what test case would expose the deepest flaw?
```

**Step 3 — G0.2 (Triage + Cap):**
After the LLM responds, categorize its findings into:
- **Critical:** would cause a wrong game outcome
- **Nit:** style or minor optimization
Cap Nits at 3.

**Step 4 — G5 (Human in the Loop):**
The LLM will likely suggest a fix. Before accepting it:
- Verify the fix handles the coordinate `(3, 4)` case described above
- Confirm a negative test would fail without the fix and pass after

---

### What a Correct Review Must Find

A complete review of this problem must identify ALL of the following:

1. The function does not check bounds before accessing `board[nr][nc]`,
   which will crash with `IndexError` when a piece is placed at the edge
2. The side-adjacency check iterates over piece squares independently —
   it does not prevent the case where `(3, 5)` is a side neighbor of
   one piece square but only a corner neighbor of another
3. No test currently covers this exact overlapping coordinate scenario
4. The review action is: **confirm a negative test exists** for the case
   where one square has a side touch even if another square sees only
   a corner touch at the same occupied cell

---

### Guidelines Applied and Why

| Guideline | Applied? | Why |
|-----------|----------|-----|
| G0.1 | ✅ Yes | Static analysis flagged the bounds issue — feeds the LLM with a concrete starting point |
| G0.2 | ✅ Yes | Separates the critical bounds/logic bugs from trivial nits |
| G3 | ✅ Yes | The docstring says "Returns True if... legal" — this is not an authority cue per se, but any comment claiming correctness must be stripped before LLM review |
| G4 | ✅ Yes | CoT decomposition into (bounds / side / corner) is the only reliable way to catch the overlapping coordinate edge case |
| G5 | ✅ Yes | Human must verify the proposed fix handles the specific `(3,4)` scenario |
| G1 | ⚠️ Optional | Overkill for a single function; would apply if reviewing the whole legality module |
| G6 | ⚠️ Optional | Useful if the team has a REVIEW.md defining what "Critical" means for the engine |

---

---

## Problem 2: Duplicate Legal Moves from Symmetric Transforms

### Context

Each Blokus piece can be placed in multiple orientations through
rotations and flips. A symmetric piece (e.g., the 2×2 square)
looks identical after certain transforms. If the engine does not
de-duplicate, it may list the same effective board placement
multiple times in its legal move list.

---

### The Code Under Review

```python
def get_legal_moves(board, piece_shape, color):
    """
    Returns a list of all legal placements for piece_shape on the board for color.
    Each placement is a frozenset of (row, col) tuples.
    """
    legal_moves = []
    transforms = get_all_transforms(piece_shape)  # returns all rotations + flips

    for transform in transforms:
        for row in range(BOARD_SIZE):
            for col in range(BOARD_SIZE):
                coords = translate(transform, row, col)
                if is_legal_move(board, coords, color):
                    legal_moves.append(frozenset(coords))

    return legal_moves  # may contain duplicates for symmetric pieces
```

The comment in the last line was added by the original author.
The function `get_all_transforms` returns all 8 possible orientations
(4 rotations × 2 flips) without checking for geometric equivalence.

---

### Review Task

**Baseline (no guideline):**
Read the code. What is wrong? What would a test look like?

**Guideline-driven attempt:**

**Step 1 — G3 (Strip Bias):**
The author's comment `# may contain duplicates for symmetric pieces`
is a rare case of the author **admitting the bug inline**. This is
useful context but can also bias the LLM into treating it as
"acknowledged and acceptable." Strip or reframe it before passing
to the LLM:

```
[Author note removed for blind review]
```

**Step 2 — G4 (Structured Prompting + Pseudocode):**

```
You are a correctness reviewer for a board game engine.

Step 1 — Convert get_legal_moves to pseudocode.
Step 2 — Identify what get_all_transforms returns and
          whether any two outputs could represent the same 
          physical board placement.
Step 3 — Identify the data structure used to store results
          and whether it prevents duplicates.
Step 4 — Propose the smallest change that eliminates duplicates
          without changing the function signature.
Step 5 — Describe exactly one test fixture that would FAIL 
          without your fix and PASS after it.
```

**Step 3 — G0.2 (Triage):**
Categorize findings:
- **Critical:** duplicate moves affect game correctness (a player
  appears to have more options than they do)
- **Supporting:** the comment admits the bug, meaning it was known
  but not fixed — is there an open issue?
- **Nit:** the function name could be `get_unique_legal_moves`

**Step 4 — G5 (Human in the Loop):**
The LLM will likely suggest wrapping `legal_moves` in a `set()`.
Before accepting:
- Confirm `frozenset` is hashable and the set comparison works correctly
- Verify with the 2×2 square piece: all 8 transforms should produce
  identical frozensets, so the final result should contain exactly
  the number of unique board positions, not 8× that number

---

### What a Correct Review Must Find

1. `get_all_transforms` produces up to 8 orientations; symmetric pieces
   produce duplicate frozensets
2. `legal_moves` is a `list`, so duplicates are silently retained
3. Fix: collect into a `set` instead of a `list`, or de-duplicate
   transforms before iterating
4. The review action is: **inspect the de-duplication logic** and
   **add a fixture that would fail on duplicates** — specifically, a
   fixture using the 2×2 square piece where the expected count of
   legal moves is N, not 8N

---

### Guidelines Applied and Why

| Guideline | Applied? | Why |
|-----------|----------|-----|
| G3 | ✅ Yes | The inline author comment creates anchoring bias — LLM may accept the bug as "acknowledged" rather than flagging it as Critical |
| G4 | ✅ Yes | Pseudocode decomposition exposes the transform→list→no-dedup chain clearly |
| G0.2 | ✅ Yes | Duplicate moves are Critical (game correctness); naming is a Nit |
| G5 | ✅ Yes | Human must verify the frozenset-in-set approach actually works for the symmetric case |
| G0.1 | ⚠️ Partial | A static analyzer would not catch semantic duplication; limited value here |

---

---

## Problem 3: JSON Fixture Drift

### Context

The engine saves and loads game state via JSON using
`GameState.from_dict()` and `GameState.to_dict()`.
After a structural refactor (e.g., renaming a field or changing
the mode configuration schema), old fixture files may still
**parse successfully** but silently produce wrong game state
because the field names no longer match.

---

### The Fixture File Under Review

```json
{
  "mode": "classic",
  "board_size": 20,
  "players": ["red", "blue", "green", "yellow"],
  "current_player": "red",
  "board": [],
  "pieces_remaining": {
    "red": 21,
    "blue": 21,
    "green": 21,
    "yellow": 21
  }
}
```

After a recent refactor, the engine now expects the mode
configuration to be structured as:

```json
{
  "config": {
    "mode": "classic",
    "board_size": 20,
    "player_colors": ["red", "blue", "green", "yellow"]
  },
  "state": {
    "current_player": "red",
    "board": [],
    "pieces_remaining": { "red": 21, "blue": 21, "green": 21, "yellow": 21 }
  }
}
```

The old fixture still passes `json.loads()` without error.
The engine silently defaults missing fields when loading,
so no exception is raised — but `GameState.config.mode` is
now `None` instead of `"classic"`.

---

### Review Task

**Baseline (no guideline):**
Read the fixture. Is anything wrong? How would you find it?

**Guideline-driven attempt:**

**Step 1 — G0.1 (Hybrid Approach):**
A schema validator (e.g., `jsonschema`) has flagged this:

```
ValidationError: 'config' is a required property
ValidationError: 'players' is not valid under the new schema
```

Inject this into your LLM prompt:

```
[Schema validator output]:
- 'config' key is missing from fixture root
- 'players' key should be nested under 'config' as 'player_colors'
- 'mode' and 'board_size' should be nested under 'config'

[Fixture under review]:
<paste fixture JSON>

You are a test-data engineer. Review this fixture against the 
schema validation output above and the round-trip contract:
GameState.from_dict(fixture).to_dict() must equal the fixture.
Identify what will break and what the corrected fixture should look like.
```

**Step 2 — G4 (CoT + Pseudocode):**

```
Step 1 — Describe what from_dict() would do with the old fixture.
Step 2 — Identify which fields would be silently defaulted vs. 
          which would raise an error.
Step 3 — Describe what to_dict() would produce from the loaded state.
Step 4 — Compare the to_dict() output to the original fixture.
          Are they equal? If not, what differs?
Step 5 — Propose the corrected fixture.
```

**Step 3 — G0.2 (Triage):**
- **Critical:** `config.mode` silently becomes `None` — this will
  affect game rule enforcement (Classic vs Duo differs in board size
  and player count)
- **Supporting:** The fixture is referenced by at least one test —
  that test is now testing against wrong game state silently
- **Nit:** Field naming inconsistency (`players` vs `player_colors`)

**Step 4 — G5 (Human in the Loop):**
The review action for this problem is explicit:
> Round-trip the fixture through `GameState.from_dict(...).to_dict()`
> and compare the result.

A human must run this check. The LLM cannot execute code.
The correct verdict: if the round-trip output differs from the
input fixture in any field, the fixture is drifted and must be
updated to match the authoritative schema.

---

### What a Correct Review Must Find

1. The fixture uses the pre-refactor flat schema; the engine now
   expects a nested `config` / `state` structure
2. `from_dict()` will not raise an error — it will silently default
   the missing `config` fields, producing wrong game state
3. The round-trip test (`from_dict().to_dict()`) would expose the
   drift because the output would not match the input
4. The review action is: update the fixture to the authoritative schema
   AND add a round-trip test that fails when the fixture drifts

---

### Guidelines Applied and Why

| Guideline | Applied? | Why |
|-----------|----------|-----|
| G0.1 | ✅ Yes | Schema validation is the exact static tool for JSON fixture review — its output is the most useful LLM input here |
| G4 | ✅ Yes | CoT round-trip reasoning (from_dict → to_dict → compare) is the only way to catch silent defaulting |
| G0.2 | ✅ Yes | Silent mode=None is Critical; naming inconsistency is Nit |
| G5 | ✅ Yes | LLM cannot execute code — human must run the actual round-trip check |
| G3 | ⚠️ Not needed | No misleading comments in a JSON file |
| G1 | ⚠️ Partial | An agent could automate round-trip validation across all fixtures in CI |

---

---

## Problem 4: Unsupported Documentation Claim

### Context

A documentation file (`OWNERSHIP.md` or `docs/evidence-log.md`)
contains the following claim:

```markdown
## R-T-04 — Legality Checking

**Status:** Covered  
**Evidence:** The move validator enforces all legality rules
including corner-touch, side-adjacency, and board-boundary checks.
```

No link to a test, fixture, or code location is provided.
When a reviewer searches the repository for tests covering
side-adjacency, they find:

- `tests/test_move_basic.py` — tests valid opening moves only
- No test for side-adjacency rejection
- No fixture for the edge case in Problem 1

The claim "Covered" is therefore unsupported.

---

### Review Task

This is a **documentation review**, not a code review.
The artifact under review is the claim in `evidence-log.md`.

**Baseline (no guideline):**
How would you verify this claim? What is the risk if you don't?

**Guideline-driven attempt:**

**Step 1 — G3 (Strip Bias):**
The word "Covered" and the confident prose description are
authority cues. Before passing to the LLM, reframe the claim:

```
[Claim to evaluate — bias stripped]:
"A document asserts that requirement R-T-04 (legality checking) 
is satisfied. No evidence link is provided. 
Evaluate whether this claim is supported."
```

**Step 2 — G4 (Structured Prompting + Multi-Perspective Personas):**

```
You are evaluating a documentation claim in a software project.

Step 1 — Identify what evidence would be needed to support 
          a claim that legality checking is fully covered.
Step 2 — From the perspective of a code reviewer: 
          is the prose description sufficient evidence?
Step 3 — From the perspective of a test engineer: 
          what specific tests would need to exist?
Step 4 — From the perspective of an auditor: 
          what is the risk if this claim is accepted without evidence?
Step 5 — Recommend the minimum corrective action.
```

**Step 3 — G0.2 (Triage):**
- **Critical:** A release-gate claim with no linked evidence cannot
  be used to approve a release — this blocks the evidence sweep
- **Supporting:** The claim implies side-adjacency is tested, but
  Problem 1 shows no such test exists
- **Nit:** The prose is well-written but empty of verifiable content

**Step 4 — G5 (Human in the Loop):**
The LLM will correctly flag the missing evidence link.
The human review action is explicit:
> Add or correct the traceability entry instead of leaving the
> claim implicit.

A human must either:
1. Find an existing test that covers the claim and add the link, or
2. Create the missing test and then add the link

The LLM cannot make this decision — it does not know what is in the repo.

---

### What a Correct Review Must Find

1. The claim "Covered" is asserted without any link to evidence
2. A search of the test suite reveals no test for side-adjacency rejection
3. The claim in the documentation is therefore false or unverifiable
4. The review action is: **add or correct the traceability entry**,
   specifically by linking to a test that actually covers R-T-04,
   or by creating that test and then linking it

---

### Guidelines Applied and Why

| Guideline | Applied? | Why |
|-----------|----------|-----|
| G3 | ✅ Yes | "Covered" and confident prose are exactly the authority cues that cause LLMs to accept false claims without scrutiny |
| G4 | ✅ Yes | Multi-perspective personas (reviewer / test engineer / auditor) reveal different dimensions of the same unsupported claim |
| G0.2 | ✅ Yes | An unsupported release-gate claim is Critical, not a Nit |
| G5 | ✅ Yes | Human must do the actual repository search — LLM cannot access the repo |
| G0.1 | ⚠️ Limited | No static tool directly checks documentation-to-test traceability; a custom script could, but that is out of scope here |

---

---

## Problem 5: Weak AI-Output Validation

### Context

A team member asked an AI assistant to generate the following
Python function for listing all legal moves:

```python
def list_legal_moves(game_state):
    """
    Lists all legal moves for the current player.
    Generated by AI assistant. Not yet reviewed.
    """
    current_player = game_state.current_player
    available_pieces = game_state.pieces[current_player]
    legal = []

    for piece in available_pieces:
        for transform in piece.get_transforms():
            for r in range(game_state.board.size):
                for c in range(game_state.board.size):
                    move = Move(piece, transform, r, c)
                    if game_state.board.is_valid(move, current_player):
                        legal.append(move)
    return legal
```

The team member committed this to the repository with the commit
message: *"Add legal move listing (AI-generated, looks correct)"*.

No validation was performed. The function calls:
- `piece.get_transforms()` — this method does not exist in the
  actual codebase; the correct method is `get_all_transforms(piece)`
- `game_state.board.is_valid()` — the actual method is
  `is_legal_move(board, coords, color)` with a different signature
- `Move(piece, transform, r, c)` — the `Move` class does not exist;
  the engine uses plain `frozenset` of `(row, col)` tuples

The code looks plausible, follows the right pattern, and contains
no syntax errors. It will crash at runtime.

---

### Review Task

This is a review of **AI-generated code before adoption**.

**Baseline (no guideline):**
Read the function. Does it look correct? Would you merge it?

**Guideline-driven attempt:**

**Step 1 — G0.1 (Hybrid Approach + Functional Check First):**
Before any LLM review, run the functional check:

```bash
python -c "from blokus.engine import list_legal_moves; print('import ok')"
```

This will fail immediately if the method calls do not match
the actual API. Record the error. This is the static baseline
before any cognitive review effort.

**Step 2 — G3 (Strip Bias):**
The commit message says "looks correct." Strip it before review:

```
[Commit message removed for blind review]
[Docstring modified]: "AI-generated. Not yet reviewed." → removed.
```

**Step 3 — G4 (Structured Prompting + CoT):**

```
You are a code reviewer for a Python board game engine.
The function below was AI-generated and has NOT been validated.

Step 1 — List every external method or class the function calls.
Step 2 — For each call, state: "exists in codebase / cannot confirm."
          Do not assume any method exists without evidence.
Step 3 — Identify any call whose signature differs from what you 
          would expect for a Blokus engine.
Step 4 — List the Critical issues that would cause a runtime crash.
Step 5 — State the minimum validation steps a human must take
          before this function can be safely adopted.
```

**Step 4 — G2 (Output Format):**
Require the LLM to structure its response as:

```
Summary: [N critical, M supporting, K nits]

Critical findings:
1. [method name]: [does not exist / wrong signature] — will crash at [line]

Supporting findings:
1. [pattern issue that would not crash but is wrong]

Nits: (max 3)
1. [style issue]

Validation steps required before adoption:
1. [step]
2. [step]
```

**Step 5 — G5 (Human in the Loop):**
The review action for this problem is explicit:
> Require explicit validation evidence before adopting the output
> into the repository.

A human must:
1. Run the function against a known fixture and verify the output
2. Cross-check every method call against the actual codebase API
3. Add an entry to `docs/ai-usage.md` recording: model used,
   task, validation method, and adoption decision
4. Only then merge the function

---

### What a Correct Review Must Find

1. `piece.get_transforms()` does not exist — the correct call is
   `get_all_transforms(piece)` (module-level function)
2. `game_state.board.is_valid(move, current_player)` has the wrong
   signature — the actual function is `is_legal_move(board, coords, color)`
3. `Move(piece, transform, r, c)` — the `Move` class does not exist;
   the engine uses `frozenset` of `(row, col)` tuples
4. The code will raise `AttributeError` at runtime on the first call
5. The review action is: **validate against the actual API before adoption**
   and **log the AI usage with validation evidence in `docs/ai-usage.md`**

---

### Guidelines Applied and Why

| Guideline | Applied? | Why |
|-----------|----------|-----|
| G0.1 | ✅ Yes | Functional check (run the import) is the first and cheapest way to catch hallucinated APIs — faster than any cognitive review |
| G3 | ✅ Yes | "Looks correct" in the commit message is a textbook authority cue that would cause an LLM (and a human) to review less critically |
| G4 | ✅ Yes | CoT "list every call and confirm existence" is the structured path to catching hallucinated APIs without missing any |
| G2 | ✅ Yes | Structured output format (Summary + Critical + Validation steps) forces the LLM to be specific and caps Nits |
| G5 | ✅ Yes | Human must run the actual functional check and log the AI usage — LLM review alone is insufficient for AI-generated code adoption |
| G0.2 | ✅ Yes | Three hallucinated API calls are Critical; docstring style is Nit |
| G1 | ⚠️ Optional | An orchestrator agent could automate API-existence checks across all AI-generated PRs |

---

---

## 3. Cross-Problem Summary

| Problem | Core reviewing skill | Primary guideline trap if skipped |
|---------|--------------------|------------------------------------|
| P1: False-positive legality | Catch overlapping coordinate edge cases in logic | Without G4 CoT, the multi-square interaction is missed |
| P2: Duplicate moves | Detect semantic duplication not visible to static tools | Without G3, author's inline comment anchors reviewer to "acknowledged" |
| P3: JSON fixture drift | Identify silent schema mismatch | Without G0.1 schema validator, the fixture passes silently |
| P4: Unsupported doc claim | Verify that claims have linked evidence | Without G3 and G5, "Covered" is accepted at face value |
| P5: Weak AI validation | Validate AI-generated code against real API | Without G0.1 functional check, hallucinated APIs ship to production |

---

## 4. References

**Literature References:**  
[1] Taufiqul Islam Khan, Shaowei Wang, Haoxiang Zhang, and Tse-Hsun Chen.
"A Survey of Code Review Benchmarks and Evaluation Practices in Pre-LLM
and LLM Era." ACM, 2026.  
[2] Imen Jaoua, Oussama Ben Sghaier, and Houari Sahraoui. "Combining
Large Language Models with Static Analyzers for Code Review Generation." 2025.  
[3] Jiwon Moon et al. "Don't Judge Code by Its Cover: Exploring Biases
in LLM Judges for Code Evaluation." 2025.  
[4] Junda He et al. "LLM-as-a-Judge for Software Engineering: Literature
Review, Vision, and the Road Ahead." 2025.

**Grey Literature References:**  
[1] "Review AI-generated code." GitHub Docs.
https://docs.github.com/en/copilot/using-github-copilot/code-review  
[2] "Code Review." Claude Code Docs. https://docs.claude.ai/code-review  
[3] "Using GitHub Copilot code review." GitHub Docs.

---

*Template version: 1.0 | Topic: 06 — Reviewing | Last updated: 2026-04-30*

