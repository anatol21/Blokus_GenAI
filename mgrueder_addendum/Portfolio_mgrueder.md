# Portfolio_mgrueder.md

> **Individual Student Portfolio** > *~4-5 page report documenting your contributions, guideline applications, and counterexamples.*

---

## Student Information

**Student Name:** Maximilian Alp Grueder 
**Team Name:** Team 1 (Reviewing Team)
**Project:** Blokus Game Engine (Classic + Duo)  

---

## 1. Owned Package Contributions

### Package Name: Architecture Diagrams

**Description:** This package is concerned with the generation of UML diagrams for the Blokus project. The reason for this was to improve everyone's understanding of the codebase and to serve as a basis for future development. Additionally, UML diagrams serve as a convenient method to introduce new LLM Sessions to the concepts and architecture of the project. 

**Responsibilities:** 
    - Generate comprehensive architecture diagrams of the Blokus project.
    - Generate a comprehensive class diagram
    - Generate four component diagrams of the Blokus game engine, showing Models, Config Components, Core Engine Components, CLI Components and GUI Components.
    - Generate three sequence diagrams of the Blokus game engine showing import, export and start game initialization.
- Adapt and improve the architecture diagrams after implementation of the duo functionality.
    - A comprehensive class diagram separated into namespaces Models_and_Config, Core_Engine, Presentation_GUI and Orchestration_CLI.
    - Three sequence diagrams, depicting: Scenario A - Application Startup & Initialization, Scenario B - Starting a new game, Scenario C - Passing turn
    - Four component diagrams, depicting: Models & Config, Core Engine, CLI, GUI and a summary component diagram.

**Evidence Links:**
- **Commits:** 
    - classic: https://github.com/anatol21/Blokus_GenAI/pull/66/changes/9493be048bbb9ebe3dbbb72654b3dba574b0e20d
    - duo: https://github.com/anatol21/Blokus_GenAI/commit/ee49e242e4c984921506d842e9416f46d284eb9f
- **Tests:** 1. Manual testing through the use of the Mermaid Live Editor.
    2. LLM-as-a-Judge approach to evaluate the correctness of the generated diagrams. 
- **Documentation:**
    1. Each diagram has its own folder, and the prompts used to generate the diagrams alongside the evaluation of Judge LLMs are in the respective folders.
    2. Pull request summary before duo: https://github.com/anatol21/Blokus_GenAI/pull/66#issue-4424842663 
    3. Pull request after duo: https://github.com/anatol21/Blokus_GenAI/pull/83 

**Key Contributions:** All diagrams are under projects/blokus/Architectural_Diagrams
- Classic: 
    - Class Diagram Generation
    - Class Diagram Evaluation
    - Component Diagram of Models & Configuration
    - Component Diagram of Core Engine
    - Component Diagram of CLI Components
    - Evaluation of Component Diagrams
    - Sequence Diagram of Import Functionality
    - Sequence Diagram of Export Functionality
    - Sequence Diagram of Start Game Initialization
    - Evaluation of Sequence Diagrams  
- After Duo:
    - Class diagram separated into namespaces Models_and_Config, Core_Engine, Presentation_GUI and Orchestration_CLI.
    - Three sequence diagrams, depicting: Scenario A - Application Startup & Initialization, Scenario B - Starting a new game, Scenario C - Passing turn
    - Four component diagrams, depicting: Models & Config, Core Engine, CLI, GUI and a summary component diagram.
    
---

### Package Name: Serialization

**Description:** At any time during the game, the human players can export the current game state to a JSON file, or import a previously exported game state to continue the game. 

**Responsibilities:** 
1. Implement export and import functionality.
2. Generate tests for export and import functionality.
3. Generate legality checker for the import functionality.

**Evidence Links:**
- **Commits:** 
    1. feat(test): add serialization integrity and extended persistence tests with pytest: `https://github.com/anatol21/Blokus_GenAI/pull/65/changes/076f04a8c14be835f3ebdfb35d93764536f6d84e`
    2. Add import/export CLI, validation fixes, and import_json_tests scenarios: `https://github.com/anatol21/Blokus_GenAI/pull/65/changes/a791963f2dd213b83f3b5b420079f1257ae02e7a`
- **Tests:** 
    1. import_json_tests/*
    2. tests/test_persistence_extended.py
    3. tests/test_serialization_integrity.py
- **Documentation:** 
    1. https://github.com/anatol21/Blokus_GenAI/pull/65#issue-4416787602
    2. docs/EPIC-PERSISTENCE-EVIDENCE.md

**Key Contributions:**
- Add import and export functionality to the Blokus game engine. (Implemented for classic, re-validated after duo implementation. Serialization was minimally affected due to both modes using the same engine.)
- Create automated test scenarios to test the import and export functionality.
- Create valid and invalid test scenarios for the import functionality, and test them. 
- Error wrapper for write and read operations during export and import.
- Add additional checks such as:
    - Is the history consistent?
    - Are the remaining pieces correct?
    - Is the current player correct?
    - Are the board states of all players correct?
    - Is the state structure valid?
    - Are the moves valid regarding the rules of Blokus?

### Package Name: GUI Optimizations
**Description:** This package is all about eliminating the visual inconsistencies of the GUI and preparing it to be compatible with the Duo mode.

**Responsibilities:** Fix the inconsistencies, and prepare the GUI to be compatible with the Duo mode. 
 - The two double-layer problem:
    - Programmatic cards painted over pre-baked SVG artwork.
    - Button shapes drawn over pre-baked button artwork.
 - Remove the unaligned and strange-looking "tokens" from on top of the icons for the text "Classic" and "GUI".
 - Either correct the adjustment of the yellow circle showing whose turn it is, or replace it with another solution. 
 - Even up the sizes of the robot icons on the board. 

**Evidence Links:**
- **Commits:** 
    - https://github.com/anatol21/Blokus_GenAI/pull/61/changes/09da79cc375abe9b5eb1cc43ad1dc81aaf44659e
    - https://github.com/anatol21/Blokus_GenAI/pull/61/changes/15c455d2b7837e52754a1d822e0cd249f48d5274
- **Tests:** Manually tested by running the game in GUI mode.
- **Documentation:** Documented the changes in the Pull Request: https://github.com/anatol21/Blokus_GenAI/pull/61

### Package Name: Harness / Evaluation / Evidence / UX-Threshold

**Description:** The Harness / Evaluation / Evidence / UX-Threshold package acts as the critical bridge between the raw Blokus game engine and human interaction. It features a deterministic evaluation harness that runs automated gameplay scenarios to strictly verify the internal game state using precise oracles. When tests fail or illegal moves occur, the package generates concrete, actionable evidence by explicitly detailing the exact reason for the failure, such as mismatched players or spent pieces. This diagnostic reporting drastically reduces debugging time and serves as a robust defense against regressions. On the user experience side, the package provides a translation layer that maps human-friendly piece coordinates into the abstract bounding-box logic the engine requires. Finally, it acts as a gatekeeper at the CLI level, gracefully validating inputs and cleanly rejecting illegal plays before they can reach or corrupt the core game engine.

**Responsibilities:** 
- Input Translation: Recognized a UX flaw where the engine's internal representation (bounding box top-left corners) was bleeding into the user interface. Built a translation layer (reference_cell and start_corner_cell) so players could specify coordinates that mapped to the actual pieces they were seeing on the board. (d9e63506)
- Input Validation: Hardened the CLI arguments, ensuring that the system fails gracefully and informatively when a user makes a mistake. Updated tests to ensure that out-of-turn plays (like explicitly passing --player yellow on the first move) were correctly caught by the validation layer rather than triggering unrelated coordinate errors. (d9e63506)
- Evaluation Harness Design: Designing and testing the "oracles" (expected outcomes) that evaluate the game's state. (fc5796bf)
- Regression Diagnosis: Built the harness to explicitly trace and report exactly why a failure occurred (e.g., identifying the specific player, piece, expected vs. actual values, and scenario names). Updated the harness to identify mismatched fields expected vs. actual values (3a563cea), concrete engine reasons for illegal openings (253734eb), and explicitly stating the piece and player involved in a spent-piece violation (df95a6ea).
- Scoring Mechanics: Implemented and verified the edge cases of the game's scoring system (55fefc70).
- State Validation: Built logic to handle and reject illegal game states, ensuring the engine properly catches spent-piece reuse and start-corner violations. (df95a6ea, 253734eb)

**Evidence Links:**
- **Commits:** 
    - https://github.com/anatol21/Blokus_GenAI/commit/55fefc702832ebaa8f12230995300f9591099a4c
    - https://github.com/anatol21/Blokus_GenAI/commit/d9e63506fbba7d3e2ae9123dd4580d9f0438029f
    - https://github.com/anatol21/Blokus_GenAI/commit/3a563cea8f4e43056f5db168a499ed6239a0e235
    - https://github.com/anatol21/Blokus_GenAI/commit/253734eb5e4a0769ee766e7ef5f49b5a380c2928
    - https://github.com/anatol21/Blokus_GenAI/commit/fc5796bf7108f5464d38f000bde95283903e483a
    - https://github.com/anatol21/Blokus_GenAI/commit/df95a6ea63a5804d3b47946faf0f0e235fde0499
- **Tests:** Edited test files:
    - tests/test_cli.py
    - tests/test_persistence.py
    - tests/test_engine.py
    - tests/test_evaluate.py
    - fixtures/scenarios/classic_corner_sequence.json
- **Documentation:** 
    - https://trello.com/c/3kv95dDT/67-execution-pers-10-dedicated-counterexample-row-avoids-hiding-regression-assets-inside-generic-invalid-move-coverage
    - https://trello.com/c/R1MA2KQJ/64-execution-eval-01-positive-harness-fixtures-now-include-both-move-and-pass-coverage
    - https://trello.com/c/FokQ6Uh2/65-execution-eval-02-turns-negative-path-replay-into-a-concrete-regression-artifact
    - https://trello.com/c/sZ2aLwEL/66-execution-eval-03-separates-bad-engine-behavior-from-bad-fixture-expectations
    - https://trello.com/c/uG94vy0L/71-execution-ui-novice-01-ui-onboarding-thresholds-need-refinement-design-only
    - https://trello.com/c/k2pG3BBB/63-execution-score-01-initial-scores-and-bonus-scoring-behavior
- **Implementation Plans for harness related changes:**
    - mgrueder_addendum/harness_implementation_plans

---

## 2. Guideline Applications

> **Note:** Document at least 3 applications of guidelines from other teams' guideline packages. For each, describe the guideline, how you applied it, and the outcome.


### Application 1: UML Specification from Design Team

**Guideline Description:** The guideline revolves around using LLMs to generate UML diagrams. The guideline consists of 4 phases, each one building on the previous one. The phases are (1) prepare inputs, (2) apply core prompting principles, (3) follow diagram-type-specific guidance, and (4) validate outputs. As inputs, the guideline mentions to use ADRs. In my case, I did not use ADRs since I wanted to generate the UML diagrams for an already existing codebase. I replaced the ADRs with a sequence of prompts that extracted the necessary information from the codebase.

**Context:** UML Diagrams are an important tool for software engineering. They provide a way to understand the structure and behavior of a software system, its architecture, design and implementation details. Additionally, they serve as documentation and a basis for communication between developers and LLM agents. 

**Application Process:** 
1. Prepare inputs for prompting (prep.md)
2. Prepare prompts for generation
3. Have LLMs generate diagrams
4. Evaluate generated diagrams manually by using the Mermaid Live Editor
5. Prepare evaluation prompts for validation
6. Evaluate generated UML diagrams using LLMs
7. Refine generated UML diagrams based on the evaluation

**Outcome:** 
- **What worked:** Breaking the UML generation down into distinct, sequential phases (preparation, generation, and evaluation) worked exceptionally well. By extracting the codebase context through a series of structured prompts rather than relying on non-existent ADRs, the LLM was able to generate accurate Mermaid syntax. Utilizing a separate "Judge LLM" session for validation also successfully caught edge-case syntax errors before I brought them into the Mermaid Live Editor.
- **What didn't work:** The guideline was well written, and while following it, I did not encounter any issues.

**Evidence:** 
1. **Diagrams**
    - UML_new/Class/blokus_class_diagram.md
    - UML_new/Sequence/blokus_sequence_diagrams.md
    - UML_new/Component/blokus_component_diagrams.md
2. **Prompts**
    - UML_new/Class/prompts/generate_class_diagram_prompt.md
    - UML_new/Sequence/prompts/generate_sequence_diagram_prompt.md
    - UML_new/Component/prompts/generate_component_diagram_prompt.md
3. **Evaluation**
    - UML_new/Class/prompts/Judge_LLM.md
    - UML_new/Sequence/prompts/Judge_LLM_Sequence.md
    - UML_new/Component/prompts/Judge_LLM_Component.md
4. **Preparation**
    - UML_new/Preperation/prep.md

**Reflection:** Yes, I would use it again in a similar context. I found decomposing tasks into smaller sections, and having the results evaluated in a different session with clear guidelines very helpful. This approach led to a reliable process for generating high-quality UML diagrams, but is also applicable to a wide range of other tasks where a system must be represented in different formats. 

---


### Application 2: Atomic Task Decomposition with Systematic Reasoning from Coding Team

**Guideline Description:** Break complex, multi-step requirements into atomic, testable units (functions/modules) before prompting. For each unit, use Few-Shot Chain-of-Thought (CoT) prompting—providing 2–5 worked examples that include both the reasoning process and the final code.

**Context:** I applied this guideline when the classic mode of the project was near completion, and when the duo requirement got added. There were problems in the GUI stemming from previous pull requests. We wanted to fix these issues before continuing with the duo mode. The fixes include:
- Fixing Double-Layer Rendering: The UI had a bug where programmatic shapes (drawn by Tkinter code) were being layered directly on top of identical, pre-baked artwork in the background SVG (SideBars.svg).
- Duo Mode Parameterization: updated hard-coded board sizes (like range(20)) in gui.py and gui_support.py to use dynamic parameters like self.state.board_size so the 14x14 Duo board could be rendered correctly.
- SVG Asset Cleanup: cleared the static circular "token" graphics behind the mode buttons that did not integrate at all with the rest of the GUI. 
- Score Panel Alignment: The yellow and green robot icons on the score panel had different sizes in the score panel. This was fixed and all icons are the same size. Additionally, the golden circle showing who is in charge was misaligned. This was replaced and the active player's score text simply turns gold.
- Robot Icon Scaling/Normalization: The green and yellow robot icons looked smaller and blurrier than the blue and red ones. This was because their SVG viewBox attributes were different (48x76 vs 80x80). I patched player_green.svg and player_yellow.svg to use an 80x80 viewBox and applied an SVG transform (scale and translate) so all four robots render identically across the board and sidebars.

**Application Process:** 
1. Identify the faulty GUI components.
2. Have the agent familiarize itself with the project, and the codebase.
3. Work on atomic, small-scale tasks, and let the agent evaluate and fix them one by one.

**Outcome:** 
- **What worked:** Decomposing worked great with smaller tasks, focusing on one GUI issue at a time.
- **What didn't work:** I did not have worked examples that include both the reasoning process and the final code, so I skipped this part. What I provided instead was a detailed explanation of the solution I wanted implemented.
- **Evidence:** `The chat export: mgrueder_addendum/Applied2/Duo GUI.md`
    - **Issue 1**
        - Prompt 1: There are still 2 problems with the gui that are disturbing visually. The first one is this: There are still the "token" like icons on the GUI. Please remove them, so that only the DUO and Classic text are visible. 
        - Result 1: The fix is applied. The Classic and Duo buttons now draw an opaque filled rounded rect first (covering the SVG token artwork), then a hover outline on top if hovered, then the text label.
        - Explanation 1: tokens were not removed, but covered using rectangle blocks that stood out in the GUI.
        - Prompt 2: Instead of covering the artwork with opaque rectangles, edit the "Ebene 2" and remove the icons directly.
        - Result 2: Removed the opaque fill workaround from draw_mode_control(). It now only draws a hover outline ring + text label (no fill needed since the SVG tokens are gone at the source). Restart the GUI to verify — the Duo and Classic areas should show only the text labels on the clean gradient background, no circular token artwork.
        - Explanation 2: This fixed the issue and I moved on to the next problem. 
    - **Issue 2**
        - Prompt 1: This looks good thank you! Now we move on the second GUI problem. The yellow circle showing whose turn it is is in the completely wrong place. It needs to be on top of the robots themselves. Second issue is the robot figures and the scores are not aligned very well. The numbers and icons should not overlap. Consider yourself a senior software developer and create an implementation plan. 
        - Result 1: -> Implementation Plan and chain of thought. 
        - Explanation 1: The integrated "Implementation Plan" behaviour of Antigravity also triggers a chain of thought process. It plans and explains the solution in detail and asks the user for feedback before making changes. Therefore I did not explicitly state the need to apply chain of thought. (Implementation Plan for this step is the file "Score Panel Fix Plan") 
    - **Remaining issues:** I continued the same way, and fixed the GUI rendering issues one by one by using small scale atomic tasks instead of complex multi step prompts.

**Reflection:** I would definitely apply this guideline in contexts where the agents struggle to perceive the issue. In my experience, this is mostly the case when working with GUIs. Since the integrated agents do not render the GUI and instead use the code to understand the issue, they are not always able to map a valid solution and implement it. It is then extremely worthwhile to decompose the task at hand into smaller bits. If the task is easy to understand, decomposition does not help much and there is a strong argument to skip the guideline and have the LLM agent work within the project scope. 



### Application 3: Iterative Remediation and Self-Correction Loops from Coding Team
**Guideline Description:** This guideline revolves around using a multi-step process while coding with LLM agents. The guideline encourages users to apply an iterative approach, where the first snippet of code generated is not accepted, but evaluated, improved by pointing to exact errors removing any "silent" hallucinations like security flaws or performance bottlenecks.

**Context:** I used this guideline during the coding of the export/import functionality of the Blokus project. When I started working on this user story, a basic import/export functionality was already implemented. However, it was not robust enough to handle corrupted or malicious input and bad filepaths. The functionality was there, but it lacked robustness. One example of a vulnerability was that the import function counted points of each played piece on the board not part of a bigger piece, but individual points. This meant that if a piece was played correctly on the board, it would be counted as invalid by the import function. 

When I set out for this task, the serialization logic was already implemented and had tests in place. 

**Application Process:** 
1. Introduced the project to the LLM
2. Described the desired functionality.
3. Assign a senior software developer persona and ask for an implementation plan.
4. Assign a senior software reviewer and critic and ask for an evaluation of the implementation plan.
5. Perform manual evaluation of the plan.
6. Have the agent create a revised implementation plan based on the evaluation and my own critique. (Assign a senior software developer persona)
7. Iteratively refine the implementation plan.
8. Most models put tests on their own in the implementation plan. Refine tests according to the relevant guideline.
9. Have the agent implement functionality according to the implementation plan.
10. Have the agent run tests and verify the functionality.
11. Perform manual verification of the functionality.
12. Repeat steps 8-11 until the implementation plan is satisfactory and the implementation is working.

**Outcome:** 
- **What worked:** Once the LLM Agent understood the serialization logic, the quality of its suggestions and responses increased drastically. By repeatedly asking the LLM to fit its answers to my needs, having it evaluate its own work and providing constructive feedback, I was able to produce a much more robust and well-tested implementation than I would have been able to do on my own. The LLM agent was also able to identify edge cases that I would have missed, and provide test cases for them.
- **What didn't work:** Even though I asked for multiple reviews of its own work, the agent was unable to identify the piece count logic on its own. I had to still perform manual tests to find this bug.
- **Evidence:** Created:
    - `validate_imports.py` — validator script that loads each JSON, runs GameState.from_dict() and validate_loaded_state()
    - `engine.py` — changed validate_loaded_state() quick consistency check:
        - old: counted occupied cells per player
        - new: counts pieces placed by counting moves in loaded.history (fixed false-positive imports)
    - `test_cli_import.py` — updated tests to reflect new validation order and construct failures that exercise full-replay checks (several targeted edits)

    (Committed as part of the same change) exported.json / state.json / test_cli_export.py / test_persistence.py / EPIC-PERSISTENCE-EVIDENCE.md — these files were added in the commit I made while working on the import/export feature and import tests. (Note: the import_json_tests files above are the fixtures I explicitly created in this session.)

    Commit Link: 
    https://github.com/anatol21/Blokus_GenAI/commit/a791963f2dd213b83f3b5b420079f1257ae02e7a 

**Reflection:** Yes. The iterative remediation loop (generate → test → inspect failure → fix → update tests/fixtures → re-run) prevented acceptance of an incorrect logic and ensured a robust, test-covered resolution. 

### Application 4: Explain-Then-Fix (Rubber Duck Self-Debugging) from Debugging Team   
**Guideline Description:** The guideline recommends a multi-turn prompting approach to debugging, where the first prompt asks the LLM to explain the code and the intended behaviour, and the second prompt asks the LLM to fix the bug based on the explanation and intended behaviour. 

**Context:** The piece placing mechanism had an error where it processed pieces as if they were in a box, indexing on the upper left corner. This method proved faulty, and could not deal with pieces that did not cover their upper left corner. An example is the piece F5. Placing F5 as the yellow (second) player to the coordinate (17,0) with rotation 0 and flipped false is not possible since the piece ends in coordinate (18,0) in the given position. 

**Application Process:** 
1. Identify a bug either through manual testing or through automated tests.
2. Ask the agent to explain the code and ask for intended behaviour.
3. Pass the intended behaviour of the code to the agent and ask for options on how to fix the bug.
4. Select and adjust an option to fix the bug, and implement.

**Outcome:** 
- **What worked:** Having the agent explain the problem helped with identifying and implementing chain-of-thought reasoning.
- **What didn't work:** Fixing the bug part of the guideline is a bit lackluster. I found it more useful to ask for fix ideas, and evaluate the ideas with a different model.
- **Evidence:** Prompts below: (Implementation plan is the file mgrueder_addendum/Applied4/cli_translation_layer_plan.md )

    **Prompt 1 (first have the LLM explain the issue):**
    I have a question with how the piece F5 is represented. In the classic mode, played in the cli mode, one of the legal moves for the yellow (second) player is to place F5 in the coordinate 17,0 with rotation 0 and flipped false. I believe this is caused by how the piece is defined in the pieces.py file. In this context, review the pieces file and explain if this could be the reason. 
    pieces.py

    **Prompt 2 (Ask for options to fix):**
    This is misleading to the player, since the intended behaviour is that the starting point should include a part of the piece itself. What options do you see where we can fix this problem?

    **Prompt 3:**
    Now I switched the model to Claude Opus 4.6. Do you agree with the implementation plans of the previous agent? Create a short review of the 4 options Gemini came up with, and add another option of your own which you think is better than the existing solutions. If there is no better alternative, say so. 

    .
    .
    .

    **This is the result:** Implementation is complete across both files:

    pieces.py — Added two new functions:
    - reference_cell(): returns the first occupied cell of a transformed piece (used as the human-friendly anchor for non-first moves)
    - start_corner_cell(): finds which cell in a transform covers a given start corner (used for first-move translation)

    cli.py — Applied the translation layer consistently across all 5 CLI surfaces:
    - _engine_to_human() / _human_to_engine(): core translation functions
    - legal-moves text output: translated ✅ | JSON output: raw engine coords ✅
    - suggest text output: translated ✅ | JSON output: raw engine coords ✅
    - validate + apply input (--x, --y): translated ✅
    - play mode: interactive move input, legal output, and computer move announcements all translated ✅

    Tests — 3 CLI tests and 1 persistence test updated to use genuinely illegal moves (wrong player/turn) instead of bad coordinates that the translation now legitimately maps to valid placements. All 364 tests pass.

**Reflection:** This guideline is very foundational due to the application of better prompting techniques. Nonetheless it is an effective method of getting the LLM to reason and self-correct, making it a valuable tool for debugging. I would use this guideline in any future projects where I need to debug code. I believe the time invested in having LLMs explain the code is invaluable and will result in a smoother and cleaner debugging and code fixing process. 


### Application 5: Define the Testing Objective from Testing Team

**Guideline Description:**  
Define the test target, scope boundaries and success criteria prior to prompt design or code generation. Use three concrete inputs: Identify the Testing Objective and Expected Artifact, Establish Scope Boundaries, and Anchor Success Criteria.

**Context:**  
After implementing the duo functionality, there was a need to create duo specific tests to make sure the serialization works as intended. The classic serialization tests were used as a reference, increasing the specification of the objective, scope, and expected artifacts.

**Application Process:**  
1. Have agent familiarize itself with the import function and serialization. So start by asking the LLM to produce an explaniation of how the import function and serialization works and what the current tests check for.
2. Identify the edge cases you want your tests to cover. 
3. Formulate a prompt based on the Testing Team guideline to generate test cases that cover the edge cases you identified. 

**Outcome:**  
- **What worked:** Numerous tests and artifacts to test edge cases and other scenarios according to the narrow scope I specified were generated fairly quickly. Additionally, the structured process of generated tests helped me keep track of the code generation and the testing process.
- **What didn't work:** Unless the objective is provided very specifically, some adidtional prompting is needed to create a test suite that covers all edge cases I will talk more about this in the counterexample 2.
- **Evidence:** 
Full logs are under mgrueder_addendum/Applied5/

Here is the first prompt I gave the agent:

Continue to Act as a senior test engineer and a expert blokus player.

Your task is to design and create a set of comprehensive tests for the serialization and import/export functionality of the Blokus Duo game engine.

There are already tests created for the regular Blokus game. You can use these as a reference. Follow a three phase approach, and generate an implementation file first. 

Phase 1: Parameterize the Existing Tests
Use the existing tests for the regular Blokus game and parameterize them for Blokus Duo. 
1) Dynamic Fixtures: Refactor methods like load_initial_payload() to accept a mode argument so it can load either classic_initial.json or the newly pulled duo_initial_state.json.
2) Abstract Hardcoded Data: Tests like test_state_round_trip_after_moves use hardcoded moves (e.g., Move("red", "I1", 19, 19)). In Duo, "red" isn't a valid player, and coordinate 19, 19 is out of bounds for a 14x14 board. You should update these tests to use a sequence of valid moves provided dynamically based on the mode.
Go over the files one by one, find the tests that need to be parameterized and create a new test file for each test file of the regular Blokus game. If a test is not relevant for Blokus Duo, skip it. If a test can be used without changing anything, add to the new relevant duo test file.

Phase 2: Verify persistance layer
1) CLI integration: In test_persistence.py and test_persistence_extended.py, make sure you test the CLI's export/import functionalities specifically calling --mode duo. (there's a skeleton test_duo_state_export_import_round_trip already in there waiting to be completed!).
2) Mid-Game Round-tripping: Similar to the stress tests, simulate a half-played Duo game, serialize it, deserialize it, and ensure the occupied_cells and history caches match perfectly

Phase 3: Implement Duo-Specific Edge Case Tests 
Create x edge cases and test if the import functionality catches evaluates them correctly. 
1) An invalid file where there a piece that is played is also in the set of remaining pieces for the player.
2) An invalid file where the sum of the squares of the remaining pieces is not equal to the expected number of squares of the remaining pieces.
3) An invalid file where a piece is played in an illegal position by a player. 
4) An invalid file where the current player is wrong. 
5) An invalid file where the player scores are wrong.
6) An invalid file where the board is misconfigured
7) An invalid file where the players started in the wrong corners.
8) An invalid file where the moves list contains invalid moves.

Ensure the "mode": "duo" key is set, the board is a 14-string array of 14 characters, and the players array is ["blue", "red"].

You should output following files: 
Duo_serialization_tests_implementation_plan.md!

Plan for the creation of these files, but do not create them yet: 
tests/test_serialization_duo.py
tests/test_serialization_integrity_duo.py
tests/test_persistence_duo.py
tests/test_persistence_extended_duo.py
tests/test_cli_import_duo.py
a folder named import_json_tests_duo and create the 8 edge cases there. Name the files appropriately. 

**Reflection:**  
I would definetly use this guideline in the future. This guideline has proven to be a great template to use when I need specific edge cases tests for a function. It provides a clear and structured approach to generating test cases that cover the edge cases I identify. 
However, I also mention this guideline in the counterexamples. The reason is that this guideline is only effective when the objective could be provided in a very concise manner. If the objective and the tests created are not specific enough, some additional prompting is needed to create a test suite that covers all edge cases. 


### Application 6: Human in the loop 
I want to avoid extending this document beyond its purpose. But I still want to talk about how I kept myself in the loop. I tried to optimize the process by being as involved as possible in the process, with my main aim being guiding the agent to perform as well as possible. 

My approach to Human in the loop:
1. The tools had only access to OS-Level commands if I gave explicit permission to use them. For all commands except ls, cat, grep, cd, git status, the agent had to ask for confirmation before running the command. 
2. I followed the code generation process as closely as possible. I took notes on paper on what we did that session (ironic, I know). I frequently asked for implementation plans and summaries of what we did. This was very helpful in making sure we were on the same page. Summaries to understand the current status of the code, and implementation plans to avoid the agent going out of scope without me realizing, and also for keeping track of all the changes it did. 
3. The testing team states that each artifact created by an LLM should be treated as a draft, and must be manually evaluated by a human for functional accuracy, code maintainability, logic, and strict alignment with internal team coding standards before integration into a CI/CD pipeline. This has been the case for me in which I inspected the artifacts and, when necessary, asked the agent to modify them. The coding and testing processes have become more and more natural. One loophole here is that when the artifact is too long, I could ask an LLM to review it (using our own Reviewing guidelines). It is open to discussion if this could also be considered as "human in the loop". 

**Reflection:** I have a limited background in software development, especially code writing. It would have been extremely elaborate for me to do my part in this project if it wasn't for the agents. My code production capacity increased significantly, but this brought more responsibility with it. The ability to comprehend the project structure and direction of the changes gained a lot more importance. Planning and being organized became even more important.

---

## 3. Counterexamples

---

### Counterexample 1: Including format examples in the prompts.
I followed Guideline 3: `UML Specification` from Design Team.

**Failure Description:** If the desired output format is popular and not customized, including examples or the desired output format in the prompt is unnecessary and leads to more token usage and doesn't improve the quality of the output in a significant way. 

**Diagnosis:** 
- **Root Cause:** Unnecessary information in prompts
- **Why the Guideline Failed:** The LLM wastes tokens by trying to create the diagrams in the exact format of the examples, which is not needed if the formal name of the format is provided. Additionally, it can lead to a degradation in the quality of the diagrams if the examples are not diverse enough.
- **Boundary Condition:** When the output format example does not include all the elements, when the cost or token limit is a factor, when the diagram is already well-known.

**Refinement:** 
- **Updated Guideline:** Instead of providing examples for popular formats, it is better to mention the formal name of the diagram format in the prompt. Use output examples only if the format is not well-known or customized according to some specifications.
- **How It Was Tested (evaluated):** I created 3 types of diagrams, and in two of them, I used different methods to imply my desired output format. For the class diagrams, I asked the agent to use Mermaid syntax. This resulted in a diagram that compiled in the Mermaid Live Editor, but the diagram did not follow strict Mermaid class diagram syntax rules.
Examples include: 
attributes must be declared as `[visibility]type name` (e.g., `+int board_size`), rather than the Python-style `+name: type`. Furthermore, using brackets `[]` for generic types (like `dict[str, object]` or `list[list[Optional[str]]]`) is invalid in Mermaid; standard Mermaid generics require tildes (e.g., `dict~str, object~`).
The diagram still compiled, but got a 3 out of 5 in the LLM evaluation.

For the component diagrams I asked the agent to follow the latest Mermaid specifications. This resulted in a diagram that followed the specifications and got a 5 out of 5 in the LLM evaluation, that also compiled in the Mermaid Live Editor.
The part of the prompt about output format is here: `Output strictly in valid MermaidLLM code. Resulting component diagram follow the latest mermaid specifications, and be renderable in Mermaid LiveEditor!!`

- **Evidence:** `All code and process is documented in the files "Architectural_Diagrams/UML_classic/*". The used prompts, evaluation results and outputs are provided in the uploaded files.`

**Prompt/Context Used:** 
```
1. Prompts
Architectural_Diagrams/UML_classic/Class/class_dia_prompt.md
Architectural_Diagrams/UML_classic/Component/comp_dia_prompt.md
Architectural_Diagrams/UML_classic/Sequence/seq_dia_prompt.md

AI Output:   

1. Final Diagrams
Architectural_Diagrams/UML_classic/Component/blokus_component_diagrams.md
Architectural_Diagrams/UML_classic/Sequence/blokus_sequence_diagrams.md
Architectural_Diagrams/UML_classic/Class/blokus_class_diagram.md

2. Diagrams before evaluation are at the bottom of the prompt files.
Architectural_Diagrams/UML_classic/Class/class_dia_prompt.md
Architectural_Diagrams/UML_classic/Component/comp_dia_prompt.md
Architectural_Diagrams/UML_classic/Sequence/seq_dia_prompt.md

3. Evaluation
Architectural_Diagrams/UML_classic/Class/Judge_LLM.md
Architectural_Diagrams/UML_classic/Sequence/Judge_LLM_Sequence.md
Architectural_Diagrams/UML_classic/Component/Judge_LLM_Component.md
```

---

### Counterexample 2: Define the Testing Objective alone does not produce comprehensive tests
I followed Guideline 3: `Define the Testing Objective from Testing Team` from Testing Team.

**Failure Description:** I wanted to create a comprehensive test suite to verify the persistence layer of the Blokus engine. This effort focused on round-trip fidelity, defensive loading of corrupted states, and addressing logical security gaps.I 

**Diagnosis:** 
- **Root Cause:** One prompt is not extensive enough to cover all aspects of the testing objective.
- **Why the Guideline Failed:** Some edge cases were not included some critical and important gaps were not identified and thus not tested.
- **Boundary Condition:** The guideline will most likely fail while generating tests for complex, stateful systems; and when high coverage of edge cases and important scenarios are required.

**Refinement:** 
- **Updated Guideline:** After the creation of an initial set of tests, use a separate prompt to evaluate the tests and identify gaps. Ask the evaluator LLM 
 - What am I not testing that is relevant to the testing objective?
 - What edge cases are missing?
 - What important scenarios are missing?
 - What security critical risks are missing? 
 - List these gaps and prioritize them as Critical, Important, or Nice-to-Have

 For the final generation of the tests, combine the outputs of the first and second prompt. 

- **How It Was Tested (evaluated):**
I applied the guideline to create tests for the serialization mechanism. After the agent created the tests, I used another guideline approach and prompte to check for missing edge cases and other issues (prompt is below). This resulted in a number of new tests that were in scope, but were not generated the first time. I also evaluated the new tests manually, and confirmed that they were indeed missing from the original output. 
 
```
Review the target objective above. 
 
Ask yourself: **What am I NOT testing?**
- What edge cases in board serialization (e.g., symbols, empty vs full) are missing?
- What security-critical risks (e.g., JSON injection, player identity spoofing in the payload) should be addressed?
- What boundary conditions for piece racks or history chains have I overlooked?
 
List these gaps and prioritize them as Critical, Important, or Nice-to-Have.
```


- **Evidence:** `The first prompt resulted in the creation of a test file, that had some critical and important gaps. These gaps were then caught with a subsequent evaluation of another LLM agent (all chats logs are stored in the Verifying Blokus Serialization Integrity.md file, under the section ## Prompts for testing the new functionality.)`

**Prompt/Context Used:** 
```
Initial Prompt:
Role: Act as a Senior SDET specialized in Python persistence and game engine verification.
 
Objective: I need to verify the **Serialization Integrity (Round-Trip)** and **Defensive Loading** for the Blokus engine. 
 
Context:
- Language: Python 3.12+
- Framework: PyTest
- Target: `GameState` and `Move` models in `src/blokus/models.py`.
- Rules: Blokus Classic (20x20).

Success Criteria: 
- `from_dict(to_dict(state)) == state` must be true for all game phases.
- Malformed JSON or corrupted board dimensions must raise specific `ValueError` or `KeyError`.
 
Technical Practices:
- Use `@pytest.mark.parametrize` for data-driven scenarios.
- Use `unittest.mock` if external dependencies are needed (though engine is plain Python).
 
Please acknowledge the objective and summarize your understanding of the serialization logic.

```
Chat files:
- Verifying_Blokus_Serialization_Integrity_full.md

AI Output: ```
test_persistence_extended.py, 
test_serialization_integrity.py ```

---

### Counterexample 3: Test all serialization of duo in one detailed, long prompt. Have the LLM agents create an implementation plan and review that plan instead of using many small prompts.
I followed Guideline `Atomic Task Decomposition with Systematic Reasoning` from Coding Team.

**Failure Description:** The guideline "batch large tasks" recommends splitting complex, multi-objective requests into smaller prompt batches. Following this guideline for the Blokus Duo serialization testing task would have required fragmenting the single coherent objective "adapt the entire Classic serialization test suite for Duo mode" into multiple smaller prompts. By instead using a single structured prompt with a built-in review gate (the implementation plan), the task was completed in just three (four if the implementation plan was not approved of and the prompt had to be adjusted accordingly) prompts total. This shows that this guideline could be improved. 

**Diagnosis:** - **Root Cause:** The "batch large tasks" guideline assumes that LLM agents lose coherence and produce lower-quality output when given complex, multi-objective prompts. However, this assumption breaks down when the single prompt is well-structured with explicit phase decomposition, concrete output specifications, and a built-in review checkpoint (the implementation plan). In this chat, Prompt 2 was a single, dense prompt containing three phases, eight edge-case specifications, six output files, and detailed adaptation instructions — yet it produced a correct, comprehensive implementation plan on the first attempt, which then led to 42 passing tests with only one minor edge-case adjustment needed.

  Another reason a single prompt can work well has to do with the guideline itself. The guideline combines powerful prompt engineering techniques, and using these techniques ensure that the resulting prompts are well-structured and detailed, so that the LLM agent stays coherent and produces a high-quality output. This could be used in conjunction with an implementation plan, to ensure the context and findings of the agents are preserved, making the agents less likely to repeat mistakes, hallucinate and more likely to produce high quality, consistent output. 

  A personal opinion is that it is easier to follow the conversation as the development continues if the milestones are saved in implementation files that are easy to edit and revert back to in case of a mistake. 

- **Why the Guideline Failed:** The guideline fails to account for the critical advantage of shared context within a single prompt. Splitting this task into many small prompts (e.g., "parameterize test_serialization.py for Duo," then "now do test_persistence.py," then "now create edge case 1," etc.) would have forced the LLM to repeatedly re-establish context about the Duo functionality. With a single prompt, all of this context was loaded once, and the LLM could reason holistically — for example, correctly recognizing that the Classic move Move("red", "I1", 19, 19) needed to become Move("red", "I1", 9, 9) across all five test files simultaneously, rather than risking inconsistent adaptations across fragmented prompts. Furthermore, the single prompt explicitly instructed the LLM to produce an implementation plan first (a review checkpoint), which gave the user a chance to validate the approach before any code was written — achieving the same risk-mitigation goal that batching claims to provide, but without losing cross-file coherence.
- **Boundary Condition:** The "batch large tasks" guideline becomes detrimental when sub-tasks are highly interdependent and require a strict, shared domain context to prevent inconsistencies (e.g., adapting shared coordinate logic across multiple test files simultaneously).

**Refinement:** 
- **Updated Guideline:** Rather than defaulting to splitting complex tasks into smaller prompt batches, prefer a single comprehensive prompt when the task involves multiple interdependent outputs that share domain context (e.g., adapting a test suite across multiple files for a new game mode). Structure the prompt with explicit phases, numbered sub-tasks, concrete output file names, and require the LLM to produce a reviewable implementation plan before generating code. Reserve batching for tasks where sub-objectives are truly independent and do not share critical context.
- **How It Was Tested (evaluated):** The single-prompt approach was evaluated by executing the full implementation in this chat session. Prompt 1 established context (familiarization with the Blokus project, running all 324 existing tests). Prompt 2 delivered the entire three-phase task specification in one message, producing a detailed implementation plan (Duo_serialization_tests_implementation_plan.md) that correctly identified all necessary adaptations. Prompt 3 ("Please implement the plan!") triggered the generation of 5 test files and 8 edge-case JSON fixtures. The resulting test suite was executed immediately via PYTHONPATH=src pytest tests/*_duo.py, yielding 42 tests collected, 41 passed on the first run, with only one edge case (05_incorrect_player_scores.json) requiring a minor adjustment because scores in the engine are dynamically computed rather than stored. After that single fix, all 42 tests passed in 0.53 seconds. No cross-file inconsistencies were observed — all five test files consistently used the correct Duo board size (14), player list (["blue", "red"]), and starting corners ((4,4) / (9,9)), demonstrating that the shared context within the single prompt prevented the drift errors that batched prompts risk introducing.
- **Evidence:** `Folder Duo serialization tests - counter 3`
    Generated test files: 
    - test_cli_import_duo.py 
    - test_persistence_duo.py 
    - test_persistence_extended_duo.py 
    - test_serialization_duo.py 
    - test_serialization_integrity_duo.py 

**Prompt/Context Used:** ```
Testing Blokus Duo Serialization.md
Duo_serialization_tests_implementation_plan.md
```
AI Output: 
Testing Blokus Duo Serialization.md
Duo_serialization_tests_implementation_plan.md
```

---

## 4. AI Usage Disclosure

### Tools and Models Used

| Tool/Model | Usage | Validation Method |
|------------|-------|-------------------|
| Gemini 3.1 Pro | Code generation, Architecture analysis, LLM as an evaluator/reviewer, Implementation plans, Design, Debugging, Testing, proofreading and documentation | Manual Verification, Tests, LLM as evaluator / reviewer |
| Gemini 3 Flash | Code generation, Architecture analysis, LLM as an evaluator/reviewer, Implementation plans, Design, Debugging, Testing, proofreading and documentation | Manual Verification, Test generation, LLM as evaluator / reviewer |
| Gemini 3.5 Flash | UML generation, LLM as a Judge for the UML diagrams | Manual Verification, LLM as evaluator / reviewer |
| GitHub Copilot on Auto | Serialization Tasks. Planning, Generation, Implementation and generation of relevant test cases. | Manual Verification, Tests, LLM as evaluator / reviewer |

### Evaluation Methods

Describe how you evaluated AI-generated outputs (below are examples for your guidance):

1. **Correctness Testing:** Manual testing, LLM as a reviewer, discussions with group members.
2. **Code Review:** Static review tools, Manual reviews, LLM as a reviewer.
3. **Unit Tests:** Human oversight, LLM as an evaluator.
4. **Integration Tests:** Human oversight, LLM as an evaluator.
5. **Performance Testing:** Not applicable.

### Time Investment

Approximately how much time did you spend on:
- AI prompting and refinement: 50 hours
- Reviewing AI outputs: 40 hours
- Testing and validation: 25 hours
- Documentation: 10 hours

---

## 5. Reflections

### What You Learned

- Human in the loop.
- Detailed prompts. If you are not sure what the details are, discussing them with AI is a very viable option.
- AI creates good looking and feeling code very quickly, but requires thorough validation and testing. It is easy to get lost in the details and code generation pace of the agents. While creating code has become easier, validating and understanding the code has become harder.
- LLMs are great at bouncing ideas off of. They can suggest alternatives and help you think through problems.
- The difference in quality and cost between different AI models is significant. Claude Opus 4.6 deals with complex prompts and implementations better, and produces a higher quality code. Gemini 3.1 Pro is by no means bad, and works much better when integrated with Antigravity's implementation plans. Gemini 3.1 Pro is much better integrated, and using Gemini together with the native Implementation Plans of Antigravity offers a very smooth workflow, and a high quality result, easily on par with Claude Opus 4.6. Gemini Flash 3.0 is a personal favorite of mine, due to its speed and simplicity in its answers. Also it uses way less tokens than the other two. From a price-performance ratio, it is (in my opinion) the best model available as of May 2026. The newest Gemini model, Flash 3.5, produces a lot of text. Where most models do not explicitly write their thinking process, Flash 3.5 seems to put more emphasis on displaying its thinking process when it generates its answers.
- When the partner in a session is a new agent with no prior context, taking the time to explain the project and the current status is very important. I mostly achieved this by first prompting: "Familiarize yourself with the project, and focus on ..."

### Skills Developed

- Better use of AI agents to develop solutions. 
- Improved understanding of the limitations of AI agents and the importance of still having human supervision.
- I switched my focus from code itself to communication with agents and how to better communicate my ideas and thoughts to them. 
- Being able to manage agents while still being on top of everything is harder than it sounds. I developed new skills to keep track of everything I have the agents create.

### Future Improvements

If you could do this project again, what would you do differently?

- Follow a more detailed implementation plan. Spend more time in the beginning thinking about the architecture and design of the system.
- Assign a higher importance to creating meaningful GitHub/Trello issues and follow them in a more structured way.
- Experiment more on same tasks with different AI models.
- One interesting approach I would like to try out would be to use a tool like Google AI Studio to one-shot the project with my current knowledge of the requirements and specifications. Then, I would compare the project we have now with the result of the Google AI Studio. 
- Agree on and stick to a standardized format for storing and documenting AI chats. 

---