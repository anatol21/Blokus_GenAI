# Reviewing Example Problems

## Example 1: False-positive legality

Problem:
A move visually appears diagonal-only, but one square also shares a same-color edge with an existing piece.

Review action:
Check the exact occupied coordinates and confirm a negative test exists.

## Example 2: Duplicate legal moves from symmetric transforms

Problem:
The engine lists the same board placement multiple times because a symmetric piece can be generated through multiple rotation/flip combinations.

Review action:
Inspect transform de-duplication logic and add a fixture or test that would fail on duplicates.

## Example 3: JSON fixture drift

Problem:
A fixture still parses, but no longer reflects the authoritative mode configuration after a structural refactor.

Review action:
Round-trip the fixture through `GameState.from_dict(...).to_dict()` and compare the result.

## Example 4: Unsupported documentation claim

Problem:
The documentation says a requirement is covered, but there is no direct code/test evidence linked.

Review action:
Add or correct the traceability entry instead of leaving the claim implicit.

## Example 5: Weak AI-output validation

Problem:
AI drafted a code block or requirement note, but nobody checked it against the rule source or executable behavior.

Review action:
Require explicit validation evidence before adopting the output into the repository.

