# Requirements Source, User Story, Ownership, and Decision Matrix

This matrix makes requirement origin explicit across Interview-derived needs and General project requirements.

Legend for `Source`:
- `General` = baseline project requirements from assignment/spec material.
- Person names (`Andrea`, `Emily`, `Lukas`, `Daniel`) = elicitation interview sources.
- Multiple sources indicate overlap.

## Product and Gameplay Requirements

| Requirement ID | Requirement (short) | Source | User story | Responsible Teammate | Decision |
| --- | --- | --- | --- | --- | --- |
| R-PG-01 | Easy-start, easy-learn, flexible Blokus product goal | Andrea, Emily, Lukas, Daniel, General | As a player, I want a Blokus app that is quick to start and deep to grow into, so that both casual and serious play feel supported. | Product Owner (TBD) | Keep |
| R-F-01 | Configurable engine for Classic and Duo | General | As a developer, I want one configurable engine for both modes, so that we avoid duplicate logic and reduce defects. | Engine Owner (TBD) | Keep |
| R-F-02 | Minimal CLI support | General | As a maintainer, I want a minimal CLI, so that I can run and debug game flows reproducibly. | Engine Owner (TBD) | Keep |
| R-F-03 | Load state from JSON | General | As a tester, I want to load game states from JSON, so that I can reproduce scenarios quickly. | Engine Owner (TBD) | Keep |
| R-F-04 | Validate move legality | General | As a player, I want illegal moves to be rejected correctly, so that games remain fair. | Engine Owner (TBD) | Keep |
| R-F-05 | Apply valid move | General | As a player, I want legal moves applied consistently, so that game progress is trustworthy. | Engine Owner (TBD) | Keep |
| R-F-06 | List legal moves | General | As a player, I want legal move listings, so that I can understand my options. | Engine Owner (TBD) | Keep |
| R-F-07 | Serialize resulting game state | General | As a tester, I want state serialization, so that I can save and verify outcomes. | Engine Owner (TBD) | Keep |
| R-F-08 | Support human players | General | As a user, I want human-controlled play, so that people can play directly. | Engine Owner (TBD) | Keep |
| R-F-09 | Support simple computer player | Daniel, General | As a solo player, I want a computer opponent, so that I can practice anytime. | Engine Owner (TBD) | Keep |
| R-F-10 | Enforce rulebook session lifecycle | Andrea, General | As a player, I want full rule enforcement from start to finish, so that each match is valid. | Engine Owner (TBD) | Keep |
| R-F-11 | Classic four-player baseline | General | As an instructor/evaluator, I want Classic 4-player support, so that milestone scope is met. | Engine Owner (TBD) | Keep |
| R-F-12 | Duo two-player mode specifics | General | As a player, I want Duo-specific board and starts, so that Duo behaves correctly. | Engine Owner (TBD) | Keep |
| R-F-13 | Piece transformations for legality | General | As a player, I want rotation/reflection support, so that all legal placements are available. | Engine Owner (TBD) | Keep |
| R-F-14 | Extend same engine by configuration | General | As a developer, I want mode extension via config, so that future mode work is maintainable. | Engine Owner (TBD) | Keep |
| R-F-15 | Start game in very few steps | Emily, Lukas | As a casual player, I want to start quickly, so that setup does not block play. | GUI Owner (TBD) | Keep |
| R-F-16 | Solo play vs computer | Andrea, Daniel, General | As a learner, I want solo play against computer, so that I can practice independently. | Engine Owner (TBD) | Keep |
| R-F-17 | Multiplayer with friends (Phase 3+) | Emily, Lukas | As a social player, I want to invite friends, so that remote play is easy later. | Multiplayer Owner (TBD) | Keep |
| R-F-18 | Asynchronous multiplayer (Phase 3+) | Emily, Lukas | As a busy player, I want asynchronous turns, so that scheduling is flexible. | Multiplayer Owner (TBD) | Keep |
| R-F-19 | Real-time multiplayer optional (Phase 3+) | Lukas | As a synchronous group, I want live play, so that we can play in one session. | Multiplayer Owner (TBD) | Keep |
| R-F-20 | Same-device pass-and-play | Emily, Lukas | As co-located players, we want pass-and-play, so that one device can host a match. | GUI Owner (TBD) | Keep |
| R-F-21 | Save and resume sessions | Emily | As a player, I want resume support, so that interrupted games are not lost. | Engine Owner (TBD) | Keep |
| R-F-22 | Intuitive placement interaction | Emily, Daniel | As a player, I want intuitive piece placement, so that interaction feels natural. | GUI Owner (TBD) | Keep |
| R-F-23 | Clear visual feedback on placement | Andrea, Daniel | As a player, I want immediate visual confirmation, so that I trust what happened. | GUI Owner (TBD) | Keep |
| R-F-24 | Precise placement without pixel-perfect input | Emily, Daniel | As a player, I want forgiving placement precision, so that controls are not frustrating. | GUI Owner (TBD) | Keep |
| R-F-25 | Clear active-turn indicator | Andrea, Emily | As a player, I want turn clarity, so that I always know whose move it is. | GUI Owner (TBD) | Keep |
| R-F-26 | Enforce Blokus move legality | Andrea, General | As a player, I want strict rule checks, so that outcomes are fair and correct. | Engine Owner (TBD) | Keep |
| R-F-27 | Explain invalid moves | Andrea, Emily | As a learner, I want invalid-move explanations, so that mistakes become learning moments. | GUI Owner (TBD) | Keep |
| R-F-28 | Undo in learning/practice contexts | Andrea, Lukas | As a learner, I want undo in practice, so that experimentation is safe. | Engine Owner (TBD) | Keep |
| R-F-29 | Hint function for stuck users | Andrea, Emily, Lukas | As a stuck player, I want hints, so that I can keep momentum. | Engine Owner (TBD) | Keep |
| R-F-30 | Short first-time onboarding | Andrea, Emily | As a new user, I want quick onboarding, so that I can start confidently. | Product Owner (TBD) | Keep |
| R-F-31 | Interactive tutorial over long text | Andrea, Emily | As a beginner, I want interactive learning, so that rules are easier to absorb. | GUI Owner (TBD) | Keep |
| R-F-32 | Explicit guidance for first move | Andrea | As a first-time player, I want first-move guidance, so that I avoid early confusion. | GUI Owner (TBD) | Keep |
| R-F-33 | Highlight valid starting placement | Andrea | As a beginner, I want highlighted valid starts, so that I can act with confidence. | GUI Owner (TBD) | Keep |
| R-F-34 | Slow step-by-step tutorial pacing | Andrea | As a low-confidence user, I want slow pacing, so that learning is not stressful. | Product Owner (TBD) | Keep |
| R-F-35 | Optional refresher guidance during play | Andrea, Emily | As a returning player, I want optional refreshers, so that I can recover quickly. | GUI Owner (TBD) | Keep |
| R-F-36 | Tutorial skippable/lightweight | Emily, Lukas | As an experienced player, I want to skip tutorial friction, so that I can play immediately. | GUI Owner (TBD) | Keep |
| R-F-37 | Practice mode against computer | Daniel, Andrea, General | As a strategist, I want AI practice mode, so that I can train between social sessions. | Engine Owner (TBD) | Keep |
| R-F-38 | What-if/sandbox mode (Phase 4) | Daniel | As an advanced player, I want sandbox analysis, so that I can test alternatives. | Engine Owner (TBD) | Keep |
| R-F-39 | Move replay or game replay | Daniel, Andrea | As a learner, I want replay, so that I can review decisions. | GUI Owner (TBD) | Keep |
| R-F-40 | Surface move history/key moments | Daniel | As a strategist, I want key moments surfaced, so that post-game learning is faster. | GUI Owner (TBD) | Keep |
| R-F-41 | Optional advanced strategy guidance (Phase 4) | Daniel | As an advanced player, I want optional strategy guidance, so that I can improve intentionally. | Product Owner (TBD) | Keep |
| R-F-42 | Track progress over time | Daniel, Emily | As a player, I want progress metrics, so that I can see improvement. | Analytics Owner (TBD) | Keep |
| R-F-43 | Invite friends easily (Phase 3+) | Emily, Lukas | As a social player, I want easy invites, so that game setup is lightweight. | Multiplayer Owner (TBD) | Keep |
| R-F-44 | Async turn-taking without co-presence (Phase 3+) | Emily, Lukas | As a distributed group, we want turn-taking without everyone online, so that play fits schedules. | Multiplayer Owner (TBD) | Keep |
| R-F-45 | Easy switching between solo/multiplayer contexts (Phase 3+) | Lukas | As a flexible user, I want context switching, so that the app adapts to my session. | Product Owner (TBD) | Keep |
| R-F-46 | Support mixed skill levels (Phase 3+) | Emily, Lukas | As a mixed-skill group, we want fair-feeling play, so that beginners stay engaged. | Product Owner (TBD) | Keep |
| R-F-47 | Optional quick match/matchmaking (Phase 3+) | Daniel, Lukas | As a player, I want optional quick matchmaking, so that I can find games quickly when needed. | Multiplayer Owner (TBD) | Keep |
| R-F-48 | Optional leaderboard/ranking (Phase 3+) | Daniel, General | As a competitive player, I want optional ranking, so that competition is available but not forced. | Product Owner (TBD) | Keep |
| R-F-49 | Adjustable computer difficulty | Andrea, Daniel, Emily | As a player, I want adjustable difficulty, so that challenge matches my skill. | Engine Owner (TBD) | Keep |
| R-F-50 | Visual/theme customization deferred until scoped | Emily | As a product owner, I want undefined customization deferred, so that core scope stays stable. | Product Owner (TBD) | Remove |
| R-F-51 | Custom rules/board settings via load/generation | Lukas, Daniel | As an advanced player, I want configurable board setups, so that I can run custom scenarios. | Engine Owner (TBD) | Keep |
| R-NF-01 | Repository testable | General | As QA, I want testable architecture, so that regressions are catchable. | QA Owner (TBD) | Keep |
| R-NF-02 | Reproducible install/test/run workflows | General | As a teammate, I want reproducible workflows, so that setup differences do not block delivery. | DevOps Owner (TBD) | Keep |
| R-NF-03 | Clear ownership and traceability | General | As a team lead, I want clear ownership and traceability, so that accountability is explicit. | Documentation Owner (TBD) | Keep |
| R-NF-04 | Prioritize correctness over fancy UI/strong AI | General | As an evaluator, I want correctness-first scope, so that core quality is delivered reliably. | Product Owner (TBD) | Keep |
| R-NF-05 | Major claims backed with direct evidence links | General | As a reviewer, I want evidence-linked claims, so that verification is fast and objective. | Documentation Owner (TBD) | Keep |
| R-NF-06 | Interface simple for novices | Andrea, Emily | As a novice user, I want a simple interface, so that I can use it without intimidation. | GUI Owner (TBD) | Keep |
| R-NF-07 | Clear visual hierarchy and readable text | Andrea | As a user, I want readable, well-structured UI, so that actions are easy to find. | GUI Owner (TBD) | Keep |
| R-NF-08 | Responsive and predictable controls | Daniel, Lukas | As a player, I want predictable controls, so that strategy is not disrupted by UI friction. | GUI Owner (TBD) | Keep |
| R-NF-09 | No deep menu dependency for common actions | Emily, Lukas | As a user, I want shallow navigation, so that core actions stay fast. | GUI Owner (TBD) | Keep |
| R-NF-10 | Reassuring UI patterns for low-tech confidence | Andrea | As a low-confidence user, I want reassuring UI patterns, so that I feel safe using the app. | GUI Owner (TBD) | Keep |
| R-NF-11 | Reliable session preservation | Emily | As a player, I want reliable persistence, so that progress is never lost. | Engine Owner (TBD) | Keep |
| R-NF-12 | Multiplayer turn sync reliability (Phase 3+) | Emily, General | As a multiplayer user, I want synchronized turn state, so that everyone sees the same game. | Multiplayer Owner (TBD) | Keep |
| R-NF-13 | Consistent hints/undo/tutorial flow | Andrea, Emily | As a learner, I want support features to work consistently, so that trust is maintained. | QA Owner (TBD) | Keep |
| R-NF-14 | Immediate-feeling placement feedback | Daniel, Emily | As a player, I want immediate placement feedback, so that gameplay feels fluid. | GUI Owner (TBD) | Keep |
| R-NF-15 | Fast computer response times | Daniel | As a solo player, I want quick computer turns, so that waiting does not break focus. | Engine Owner (TBD) | Keep |
| R-NF-16 | No lag in navigation/board interaction | Lukas | As a user, I want lag-free interaction, so that the interface feels polished. | GUI Owner (TBD) | Keep |
| R-NF-17 | Smooth camera/zoom/panning if present | Lukas | As a player, I want smooth board navigation, so that I can inspect positions comfortably. | GUI Owner (TBD) | Keep |
| R-NF-18 | New user can play meaningfully within minutes | Andrea, Emily | As a beginner, I want to be productive quickly, so that onboarding feels successful. | Product Owner (TBD) | Keep |
| R-NF-19 | Rules understandable with minimal reading | Andrea, Emily | As a user, I want low-reading learning, so that I can learn by doing. | Product Owner (TBD) | Keep |
| R-NF-20 | Learning support optional for experienced players | Emily, Daniel | As an experienced player, I want optional guidance, so that advanced flow stays uninterrupted. | Product Owner (TBD) | Keep |

## Delivery and Engineering Requirements

| Requirement ID | Requirement (short) | Source | User story | Responsible Teammate | Decision |
| --- | --- | --- | --- | --- | --- |
| R-C-01 | No LLM runtime dependency in delivered solution | General | As an evaluator, I want no runtime LLM dependency, so that delivery matches assignment constraints. | Architecture Owner (TBD) | Keep |
| R-C-02 | Heavy GUI out of baseline scope | General | As a planner, I want heavy GUI excluded from baseline, so that scope remains achievable. | Product Owner (TBD) | Keep |
| R-C-03 | Strong AI optional only | General | As a team, we want advanced AI optional, so that correctness work is prioritized. | Product Owner (TBD) | Keep |
| R-C-04 | Online multiplayer out of baseline scope | General | As a planner, I want online multiplayer deferred, so that baseline delivery risk stays controlled. | Product Owner (TBD) | Keep |
| R-D-01 | TEAM_SUMMARY.md required | General | As a reviewer, I want a concise team summary, so that project status is easy to inspect. | Documentation Owner (TBD) | Keep |
| R-D-02 | OWNERSHIP.md required | General | As a reviewer, I want an ownership map, so that responsibility boundaries are clear. | Documentation Owner (TBD) | Keep |
| R-D-03 | Individual portfolio deliverables required later | General | As an instructor, I want per-member portfolios, so that individual contribution is assessable. | Documentation Owner (TBD) | Keep |
| R-D-04 | Owned-package contributions documented with evidence | General | As an evaluator, I want contribution evidence, so that claimed ownership is verifiable. | Documentation Owner (TBD) | Keep |
| R-D-05 | Guideline applications documented | General | As a reviewer, I want documented guideline usage, so that process quality is visible. | Documentation Owner (TBD) | Keep |
| R-D-06 | Reproducible counterexamples documented | General | As a reviewer, I want reproducible counterexamples, so that failures and fixes are auditable. | Documentation Owner (TBD) | Keep |
| R-D-07 | Reviewing guideline package required | General | As an evaluator, I want the guideline package present, so that assignment deliverables are complete. | Review Owner (TBD) | Keep |
| R-D-08 | Guideline package addresses reviewing tasks | General | As an evaluator, I want project-relevant reviewing content, so that guidance is actionable. | Review Owner (TBD) | Keep |
| R-D-09 | Report analyzes guideline usage/failures/refinements | General | As a reviewer, I want reflective analysis, so that learning outcomes are explicit. | Review Owner (TBD) | Keep |
| R-D-10 | AI usage documentation required | General | As an evaluator, I want AI-use disclosure, so that compliance and rigor are clear. | Documentation Owner (TBD) | Keep |
| R-E-01 | Evaluation harness required | General | As QA, I want an evaluation harness, so that quality checks are repeatable. | QA Owner (TBD) | Keep |
| R-E-02 | Evaluate correctness for Classic and Duo | General | As an evaluator, I want both modes assessed, so that mode quality is comparable. | QA Owner (TBD) | Keep |
| R-E-03 | Classic->Duo as requirements-evolution case | General | As a reviewer, I want explicit evolution analysis, so that change-management quality is visible. | Product Owner (TBD) | Keep |
| R-E-04 | Report explains breakage, suggestions, what worked | General | As an evaluator, I want evidence-backed retrospection, so that process claims are testable. | Documentation Owner (TBD) | Keep |
| R-E-05 | AI-assisted claims evidence-based | General | As a reviewer, I want evidence-based AI claims, so that assertions are trustworthy. | Documentation Owner (TBD) | Keep |
| R-R-01 | Reproducible install/test/run scripts | General | As a teammate, I want scripts for setup/run/test, so that onboarding is reliable. | DevOps Owner (TBD) | Keep |
| R-R-02 | Evidence log of worked and failed attempts | General | As a reviewer, I want a work/failure log, so that iteration history is transparent. | Documentation Owner (TBD) | Keep |
| R-R-03 | Counterexamples reproducible with refinement details | General | As QA, I want reproducible failure cases, so that regressions can be replayed. | QA Owner (TBD) | Keep |
| R-R-04 | AI usage logs include model/task/prompt/validation | General | As an evaluator, I want structured AI metadata, so that validation discipline is auditable. | Documentation Owner (TBD) | Keep |
| R-T-01 | Automated test suite exists | General | As QA, I want automated tests, so that regression checking is continuous. | QA Owner (TBD) | Keep |
| R-T-02 | Tests cover key rules/transforms | General | As a maintainer, I want rule-transform coverage, so that core mechanics remain stable. | QA Owner (TBD) | Keep |
| R-T-03 | Tests and harness cover Classic and Duo | General | As QA, I want both modes covered, so that cross-mode regressions are detected. | QA Owner (TBD) | Keep |
| R-T-04 | Validation evidence for legality/apply/serialization | General | As a reviewer, I want explicit validation artifacts, so that critical engine behavior is proven. | QA Owner (TBD) | Keep |
| R-T-05 | AI outputs validated before adoption | General | As a maintainer, I want AI outputs validated, so that low-quality suggestions do not ship. | Review Owner (TBD) | Keep |
| R-T-06 | Use fixtures/repeatable inputs where appropriate | General | As QA, I want repeatable fixtures, so that tests stay deterministic and debuggable. | QA Owner (TBD) | Keep |
