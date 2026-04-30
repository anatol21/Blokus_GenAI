Focus only on test adequacy for changed behavior.

Check:

- what behavior changed
- which existing tests appear to cover it
- what test coverage is missing, if any
- whether gaps are blocking, recommended, or optional

Do not demand tests for cosmetic-only changes.
If no material gap is visible, return an empty findings list and note `no material test gap found`.
Return valid JSON only.
