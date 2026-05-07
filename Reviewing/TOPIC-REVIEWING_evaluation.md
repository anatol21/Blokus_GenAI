# Reviewing Evaluation Criteria

Use this rubric when evaluating whether a review activity was effective in this project.

## Criteria

| Criterion | Strong evidence | Weak evidence |
| --- | --- | --- |
| Rule correctness | Reviewer linked the rule source and a passing/failing test | Reviewer only said the code “looks right” |
| Reproducibility | Reviewer replayed scripts, tests, or fixture scenarios | Reviewer relied on unstated local setup |
| Attribution | Review comments or evidence identify who changed and who reviewed | Ownership is implicit or missing |
| AI-output control | Adopted AI output has a recorded validation step | AI output was copied without validation notes |
| Counterexample quality | Review uncovered a failure and led to refinement | Review found no issues because nothing concrete was checked |

## Minimum acceptance for a review record

- The reviewed artifact is named.
- The reason for review is stated.
- At least one concrete checker is recorded.
- The outcome is one of: accepted, revised, rejected, or deferred.
- If revised or rejected, the failure mode is documented.

