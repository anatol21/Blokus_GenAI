# Requirements Baseline

This document is the stable requirements source of truth for this repository. Actionable implementation work should be tracked in GitHub Issues, but requirements must remain stable here with explicit IDs.

## Project scope

- Build a configurable Blokus engine in plain Python.
- Deliver a Phase 1 Classic baseline and prepare for a Phase 2 Duo extension through configuration.
- Keep strong traceability between requirements, code, tests, documentation, and evidence.

## Phase 1 scope

- Classic mode baseline with four-player gameplay.
- Minimal CLI and JSON state contracts.
- Move validation, move application, legal move listing, and state serialization.
- Automated tests, reproducible scripts, and fixtures.

## Phase 2 scope

- Add Duo support by extending the same engine configuration layer.
- Add Duo-specific contracts, fixtures, tests, and evaluation evidence.
- Treat Classic to Duo as a requirements-evolution case study.

## Constraints

- Plain Python implementation.
- No heavy GUI dependency for baseline acceptance.
- No LLM runtime dependency in the delivered runtime solution.
- No online multiplayer requirement for baseline delivery.

## Core product goal

- `R-PG-01`: The product shall provide a digital Blokus experience that is easy to start, easy to learn, and flexible enough to support both casual family play and deeper solo or competitive practice, emphasising guided learning and reassurance for newcomers (Andrea), low setup and mixed-skill accessibility (Emily), seamless multiplayer flexibility with polished usability (Lukas), and AI-based practice plus strategic analysis support (Daniel).

## Functional requirements

- `R-F-01`: The system shall provide a configurable Blokus engine that supports Classic and Duo modes.
- `R-F-02`: The system shall provide a minimal CLI.
- `R-F-03`: The system shall load a game state from JSON.
- `R-F-04`: The system shall validate proposed move legality.
- `R-F-05`: The system shall apply a valid move.
- `R-F-06`: The system shall list legal moves.
- `R-F-07`: The system shall print or serialize resulting game state.
- `R-F-08`: The system shall support human players.
- `R-F-09`: The system shall support at least one simple computer player.
- `R-F-10`: The system shall enforce rulebook conditions necessary to start, continue, and terminate a Classic game session.
- `R-F-11`: Classic mode shall support four-player gameplay baseline.
- `R-F-12`: Duo mode shall support two-player gameplay with Duo-specific board and starting positions.
- `R-F-13`: The system shall support piece transformations required for legal placements.
- `R-F-14`: The same engine implementation shall be extended by configuration to support Duo.

### Player-facing requirements

#### Game setup and session start
- `R-F-15`: The system shall allow a user to start a game in very few steps.
- `R-F-16`: The system shall support solo play against a computer opponent.
- `R-F-17`: The system shall support multiplayer play with friends once Phase 3 or higher introduces multiplayer hooks.
- `R-F-18`: The system shall support asynchronous multiplayer once Phase 3 or higher introduces multiplayer hooks.
- `R-F-19`: The system should support real-time multiplayer as an additional mode when Phase 3 or higher adds multiplayer capability.
- `R-F-20`: The system should support same-device/local pass-and-play.
- `R-F-21`: The system shall save ongoing sessions so players can resume later without losing progress.

#### Core gameplay interaction
- `R-F-22`: The system shall allow intuitive piece placement through drag-and-drop or an equally simple interaction.
- `R-F-23`: The system shall provide clear visual feedback when a piece is placed.
- `R-F-24`: The system shall snap pieces into valid positions or otherwise make placement precise without requiring pixel-perfect input.
- `R-F-25`: The system shall clearly indicate whose turn it is.
- `R-F-26`: The system shall enforce Blokus move legality.
- `R-F-27`: The system should explain why a move is invalid.
- `R-F-28`: The system shall provide an undo function in learning or practice contexts.
- `R-F-29`: The system should provide a hint function for users who are stuck.

#### Onboarding and tutorial
- `R-F-30`: The system shall provide a short onboarding flow for first-time users.
- `R-F-31`: The tutorial shall explain the basic rules through interaction rather than long text.
- `R-F-32`: The tutorial shall explicitly guide the first move.
- `R-F-33`: The tutorial should visually highlight valid starting placement.
- `R-F-34`: The tutorial shall allow beginners to learn step by step at a slow pace.
- `R-F-35`: The system should offer optional refresher guidance during play.
- `R-F-36`: The tutorial should be skippable or lightweight for experienced users.

#### Learning and practice support
- `R-F-37`: The system shall provide a practice mode against a computer.
- `R-F-38`: The system should provide a what-if or sandbox mode for trying alternative moves once Phase 4 work begins.
- `R-F-39`: The system should allow move replay or game replay.
- `R-F-40`: The system should surface move history or key moments after a game.
- `R-F-41`: The system should provide optional strategy guidance for advanced players once Phase 4 work begins.
- `R-F-42`: The system should track player progress over time, such as win rate or placement efficiency.

#### Multiplayer and social play
- `R-F-43`: The system shall allow inviting friends into games easily once Phase 3 or higher introduces multiplayer.
- `R-F-44`: The system shall support turn-taking without requiring all players to be present simultaneously once Phase 3 or higher introduces multiplayer.
- `R-F-45`: The system should support switching easily between solo and multiplayer contexts once Phase 3 or higher introduces multiplayer.
- `R-F-46`: The system should support different skill levels without making beginners feel excluded once multiplayer planning reaches Phase 3 or later.
- `R-F-47`: The system may support quick match or matchmaking for strangers as an optional feature in Phase 3 or later.
- `R-F-48`: Competitive ranking and leaderboards should be optional, not mandatory, when multiplayer capabilities are added in Phase 3 or later.

#### Customization
- `R-F-49`: The system should allow difficulty adjustment for the computer opponent.
- `R-F-50`: The system may allow board or visual customization, such as color themes, but this capability is deferred until the scope is defined.
- `R-F-51`: The system may allow custom rules or board settings, such as loading or generating specific board configurations, once the stable core experience ships.

## Non-functional requirements

- `R-NF-01`: The repository shall be testable.
- `R-NF-02`: The repository shall provide reproducible install, test, and run workflows.
- `R-NF-03`: The repository shall maintain clear ownership, traceable contributions, and issue-based tracking.
- `R-NF-04`: The implementation shall prioritize correctness over sophisticated UI or strong AI play strength.
- `R-NF-05`: Project documents shall include direct evidence links for major claims.

### Usability

- `R-NF-06`: The interface shall be simple and immediately understandable for novice users.
- `R-NF-07`: The interface shall use clear visual hierarchy and readable text.
- `R-NF-08`: Controls shall be responsive and predictable.
- `R-NF-09`: Common actions shall not require deep menu navigation.
- `R-NF-10`: The product shall support users with limited technical confidence through large, clear, reassuring UI patterns.

### Reliability

- `R-NF-11`: The game shall preserve session state reliably.
- `R-NF-12`: Multiplayer turn state shall remain synchronized correctly once Phase 3 or higher introduces multiplayer capability.
- `R-NF-13`: Hints, undo, and tutorials shall function consistently without breaking flow.

### Performance

- `R-NF-14`: Piece placement feedback shall feel immediate.
- `R-NF-15`: Computer response times shall be fast enough to preserve play flow.
- `R-NF-16`: Navigation and board interaction shall not lag.
- `R-NF-17`: Camera movement, zoom, and panning, if present, shall be smooth and responsive.

### Learnability

- `R-NF-18`: A new user should be able to begin meaningful play within minutes.
- `R-NF-19`: Rules should be understandable with minimal reading.
- `R-NF-20`: Learning support should be optional and non-intrusive for experienced players.

## Constraint and exclusion requirements

- `R-C-01`: The delivered runtime solution shall have no LLM runtime dependency.
- `R-C-02`: Heavy GUI is out of scope for baseline acceptance.
- `R-C-03`: A strong AI player is optional only.
- `R-C-04`: Online multiplayer is out of scope.

## Documentation requirements

- `R-D-01`: `TEAM_SUMMARY.md` exists.
- `R-D-02`: `OWNERSHIP.md` exists.
- `R-D-03`: Individual portfolio deliverables are required later.
- `R-D-04`: Project shall document owned-package contributions with evidence.
- `R-D-05`: Project shall document guideline applications.
- `R-D-06`: Project shall document reproducible counterexamples.
- `R-D-07`: Reviewing guideline package is required.
- `R-D-08`: Reviewing guideline package shall address reviewing tasks in this project.
- `R-D-09`: Project report shall analyze guideline usage, failures, and refinements.
- `R-D-10`: AI usage shall be documented.

## Evaluation requirements

- `R-E-01`: Project shall provide an evaluation harness.
- `R-E-02`: Project shall evaluate implementation quality and correctness for Classic and Duo.
- `R-E-03`: Project shall treat Classic to Duo as a requirements-evolution case study.
- `R-E-04`: Report shall explain what broke, what the LLM suggested, and what actually worked.
- `R-E-05`: AI-assisted engineering claims shall be evidence-based.

## Reproducibility requirements

- `R-R-01`: Repository shall include reproducible install, test, and run scripts.
- `R-R-02`: Project shall maintain an evidence log of what worked and failed.
- `R-R-03`: Counterexamples shall be documented with enough detail to reproduce failure and refinement.
- `R-R-04`: AI usage documentation shall identify tool/model, task, prompt or prompt category, validation method, and adoption decision.

## Testing and validation requirements

- `R-T-01`: Automated test suite exists.
- `R-T-02`: Tests cover key rules and transforms.
- `R-T-03`: Tests and evaluation harness shall later cover both Classic and Duo.
- `R-T-04`: Project shall include validation evidence for legality checking, move application, and serialization.
- `R-T-05`: AI-assisted outputs shall be validated before adoption.
- `R-T-06`: Project shall use fixtures or equivalent repeatable test inputs where appropriate.

## Out-of-scope baseline

- Strong AI gameplay quality beyond a simple baseline strategy.
- Production-grade online services, matchmaking, or multiplayer infrastructure.
- Rich GUI as a gating requirement for core correctness acceptance.

## Open risks and open issues

- Duo mode is not fully implemented yet in runtime config and tests.
- Requirements may drift if issue descriptions diverge from this baseline.
- Human-review evidence can become inconsistent without PR checklist discipline.
- Counterexample capture is currently process-driven and needs ongoing enforcement.

## Traceability notes

- Requirement-to-implementation/test mapping lives in `docs/traceability-matrix.md`.
- Source attribution, user stories, ownership, and keep/remove decisions live in `docs/requirements_source_matrix.md`.
- Work items should reference requirement IDs in issue bodies and PRs.
- Evidence for requirement claims should be logged in `docs/evidence-log.md`.
- AI-assisted changes should be logged in `docs/ai-usage.md` before adoption.
