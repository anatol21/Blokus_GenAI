Focus only on performance-sensitive changed executable code.

Check for:

- algorithmic complexity regressions
- repeated I/O
- inefficient loops
- degraded caching behavior
- unnecessary synchronous work
- large-input risks
- excessive memory use

Do not report theoretical micro-optimizations unless they are likely material.
Return concise, actionable findings only, up to `3`.
Return valid JSON only.
