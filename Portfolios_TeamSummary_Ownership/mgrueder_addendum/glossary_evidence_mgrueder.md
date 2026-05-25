# Glossary of Evidence Types

## **Commits**
- **Definition**: Git commits that contain your direct contributions
 - Harness
  - the user now sees the correct placement of the pieces. Fixed the issue where the users saw always the top left coordinate when placing a piece: https://github.com/anatol21/Blokus_GenAI/pull/78/changes/d9e63506fbba7d3e2ae9123dd4580d9f0438029f
  - User Story SCORE-01: Initial scores and bonus scoring behavior: https://github.com/anatol21/Blokus_GenAI/pull/78/changes/55fefc702832ebaa8f12230995300f9591099a4c
  - [Execution] EVAL-01: Positive harness fixtures now include both move and pass coverage: https://github.com/anatol21/Blokus_GenAI/pull/78/changes/fc5796bf7108f5464d38f000bde95283903e483a
  - [Execution] EVAL-02: Turns negative-path replay into a concrete regression artifact: https://github.com/anatol21/Blokus_GenAI/pull/78/changes/253734eb5e4a0769ee766e7ef5f49b5a380c2928
  - EVAL-03: Separates bad-engine behavior from bad-fixture expectations: https://github.com/anatol21/Blokus_GenAI/pull/78/changes/3a563cea8f4e43056f5db168a499ed6239a0e235
  - PERS-10: Dedicated counterexample row avoids hiding regression assets inside generic invalid-move coverage: https://github.com/anatol21/Blokus_GenAI/pull/78/changes/df95a6ea63a5804d3b47946faf0f0e235fde0499
  - added an error catcher to block wrong piece name inputs from terminating the program: https://github.com/anatol21/Blokus_GenAI/pull/78/changes/44f11379dd55f24a06392b005d03072ca603bb4f
  - fix: resolve CLI review feedback: https://github.com/anatol21/Blokus_GenAI/pull/78/changes/15ce93efe5efae08aa67397ee52e3abd535b0ea4

 - Serialization
  - created serialization and import/export tests for the duo functionality. Also extended validation logic so that it also includes imports from the command line. https://github.com/anatol21/Blokus_GenAI/pull/71/changes/6acfd3b9ca01a6a2ad9aca8ec427972b0e849efd 
  - feat(test): add serialization integrity and extended persistence tests with pytest. https://github.com/anatol21/Blokus_GenAI/pull/65/changes/076f04a8c14be835f3ebdfb35d93764536f6d84e
  - Add import/export CLI, validation fixes, and import_json_tests scenarios. https://github.com/anatol21/Blokus_GenAI/pull/65/changes/a791963f2dd213b83f3b5b420079f1257ae02e7a
  - Serialization, import export from command line, tests. https://github.com/anatol21/Blokus_GenAI/pull/65/changes/b2b45f90fa78c32c85ec7d88c4b2ad98058c40e8

 - GUI troubleshooting
  - UI fixes: https://github.com/anatol21/Blokus_GenAI/pull/61/changes/09da79cc375abe9b5eb1cc43ad1dc81aaf44659e
  - graphics changes: https://github.com/anatol21/Blokus_GenAI/pull/61/changes/15c455d2b7837e52754a1d822e0cd249f48d5274
 
 - UML Diagrams
  - Add new UML files created after duo functionality: https://github.com/anatol21/Blokus_GenAI/pull/83/changes/ee49e242e4c984921506d842e9416f46d284eb9f
  - improved the UML diagrams: https://github.com/anatol21/Blokus_GenAI/pull/66/changes/3e68c7118ba5a6703a6d340fd3f9b3357d7a7175
  - Add new UML diagrams: https://github.com/anatol21/Blokus_GenAI/pull/66/changes/9493be048bbb9ebe3dbbb72654b3dba574b0e20d
  - add UML outputs generated via basic prompting: https://github.com/anatol21/Blokus_GenAI/pull/36/changes/711402394ac3cc9957ba81966733321af4de19f8

## **Tests**
- **Definition**: Test files or specific test cases you authored or extensively edited. 
  - All test files under: import_json_tests/
  - tests/test_cli_export.py
  - tests/test_cli_import.py
  - tests/test_persistence.py
  - tests/test_persistence_extended.py
  - tests/test_serialization_integrity.py
  - state.json (to test basic import functionality
  - All json files to test states and scenarios under: fixtures/
  - All  test files for duo under: import_json_tests_duo/
  - tests/depr_old_duo_tests/test_cli_import_duo.py
  - tests/depr_old_duo_tests/test_persistence_duo.py
  - tests/depr_old_duo_tests/test_persistence_extended_duo.py
  - tests/depr_old_duo_tests/test_serialization_duo.py
  - tests/depr_old_duo_tests/test_serialization_integrity_duo.py
  - tests/test_evaluate.py
  - tests/test_engine.py


## **Documentation**
- **Definition**: Documentation files you wrote or significantly modified
The documentation of my work is included in the pull requests. 

## **Pull Requests / Merge Requests**
- **Definition**: GitHub/GitLab issues you created or primarily worked on
  - PRs I created
    - PR #83 Uml after duo: https://github.com/anatol21/Blokus_GenAI/pull/83 
    - PR #78 Additional Layer to fix starting corners, Trello Tasks: https://github.com/anatol21/Blokus_GenAI/pull/78
    - PR #66 New uml diagrams + continuation of serialization: https://github.com/anatol21/Blokus_GenAI/pull/66
    - PR #65 Serialization + fixed starting corners (with errors): https://github.com/anatol21/Blokus_GenAI/pull/65
    - PR #71 Duo & code v2: https://github.com/anatol21/Blokus_GenAI/pull/71
    - PR #65 Serialization, import export from command line, tests:https://github.com/anatol21/Blokus_GenAI/pull/65
    - PR #61 GUI fixes (for DUO): https://github.com/anatol21/Blokus_GenAI/pull/61
    - PR #36 add UML outputs generated via basic prompting: https://github.com/anatol21/Blokus_GenAI/pull/36
  - Significant reviews I provided
    https://github.com/anatol21/Blokus_GenAI/pull/77#pullrequestreview-4348710969
    https://github.com/anatol21/Blokus_GenAI/pull/76#pullrequestreview-4348698568
    https://github.com/anatol21/Blokus_GenAI/pull/69#pullrequestreview-4304176218
    https://github.com/anatol21/Blokus_GenAI/pull/68#pullrequestreview-4299427498
    https://github.com/anatol21/Blokus_GenAI/pull/60#pullrequestreview-4251956592  


## **Issues**
- **Definition**: Below you can find the trello issues I have worked on. My commits and work have been documented on the cards. 
  - [Requirements] Serialization, persistence integrity, harness replay, and evidence discipline: https://trello.com/c/OoZLNbNu
  - [Execution] PERS-10: Dedicated counterexample row avoids hiding regression assets inside generic invalid-move coverage: https://trello.com/c/3kv95dDT
  - [Execution] EVAL-01: Positive harness fixtures now include both move and pass coverage: https://trello.com/c/R1MA2KQJ
  - [Execution] EVAL-02: Turns negative-path replay into a concrete regression artifact: https://trello.com/c/FokQ6Uh2
  - [Execution] EVAL-03: Separates bad-engine behavior from bad-fixture expectations: https://trello.com/c/sZ2aLwEL
  - [Execution] UI-NOVICE-01: UI onboarding thresholds need refinement (design-only): https://trello.com/c/uG94vy0L
  - [Execution] SCORE-01: Initial scores and bonus scoring behavior: https://trello.com/c/k2pG3BBB

## **Files**
- **Definition**: Source code files you primarily authored
  - All UML diagrams under Architectural_Diagrams: https://github.com/anatol21/Blokus_GenAI/tree/UML_after_duo/Architectural_Diagrams 
  - New Files:
   - generate_edge_cases.py

  - Extensive changes to: 
   - PR61
    - src/blokus/gui.py
    - src/blokus/gui_support.py

   - PR65:
    - src/blokus/cli.py
    - src/blokus/engine.py
    - src/blokus/models.py
    
   - PR71:
    - src/blokus/cli.py
    - src/blokus/config.py
    - src/blokus/evaluate.py

  - PR78:
    - src/blokus/pieces.py
    - tests/test_cli.py

## **Reproducible Counterexamples**
- **Definition**: Documentation of failures that can be reproduced by others
 -**Counterexample 1** All code and process is documented in the files "Architectural_Diagrams/UML_classic/*". The used prompts, evaluation results and outputs are provided in the uploaded files.`

 - **Counterexample 2** mgrueder/addendum/counter2/Verifying_Blokus_Serialization_Integrity_full.md includes:
  - Initial user prompt in line with the guidelines
  - First response of the agent
  - Prompt to ask for missing edge cases, etc
  - Resulting implementation plan 
  - Created tests as a result of the implementation plan. 
  - User prompts are stored under '### User Input'
  - At the end of the file, there is a '# Walkthrough: Serialization & Defensive Loading Verification' section, detailing the contents of the file. 
  
 - **Counterexample 3** mgrueder/addendum/counter3 includes:
    - what_each_test_file_tests.md: an overview of what each generated test file tests. 
    - Duo_serialization_tests_implementation_plan.md: the implementation plan generated. 
    - Testing Blokus Duo Serialization.md: The full prompt history. 
  


---

## **Best Practices for Evidence Links**

1. **Be Specific**: Link to exact commits, functions, or sections—not just repository roots
2. **Be Persistent**: Use commit hashes (not branch names) for permanent references
3. **Be Complete**: Include enough context so others can understand the evidence without extra digging
4. **Be Verifiable**: Ensure links work and content hasn't been deleted

---

*Template version: 2.0 | Last updated: 25 May 2026*



