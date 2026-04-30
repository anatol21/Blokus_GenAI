Focus only on correctness and regression risk in changed executable code.

Check:

- changed invariants or assumptions
- null or None handling
- error paths and retries
- ordering and state transitions
- pagination
- time zones
- locale
- empty input
- duplicate input
- large input
- concurrency or race-sensitive behavior
- caller/callee API contract drift

Return concise, actionable findings only, up to `3`.
Return valid JSON only.
