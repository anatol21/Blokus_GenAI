---
applyTo: "src/blokus/**,tests/**,fixtures/**,schemas/**"
---

These files define game behavior, correctness, and reproducibility.

- Do not invent or silently change rule semantics. If requirements, fixtures, and expected behavior disagree, stop and escalate.
- Update tests whenever behavior changes.
- Keep fixtures and schemas synchronized with implementation changes.
- Preserve deterministic CLI and serialization behavior where possible.
- Prefer small, explicit changes over broad refactors when touching game rules.
- When editing tests, make the expected behavior obvious from the test name and assertions.
- When editing fixtures or schemas, explain in the PR why the contract changed and which tests validate it.
