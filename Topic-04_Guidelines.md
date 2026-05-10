# Topic-04_Guidelines.md

## Team Information

**Team Name:** The Testing Team  
**Topic:** Testing  
**Date:** 22.04.2026  
**Authors:** Julian Maurus, Sebastian Menzel, Simon Wally

## 1. Unified Guidelines

### Scope & Applicability
These guidelines are optimized for Unit Testing (the testing level) and Defect Testing (the testing type). They define how to leverage classic LLM chat interfaces and integrated AI agents to effectively identify defects within a software codebase.

### Guideline 01: Define the Testing Objective

**Description:**  
Define the test target, scope boundaries and success criteria prior to prompt design or code generation. Use three concrete inputs:

1. **Identify the Testing Objective and Expected Artifact**  
    Clearly specify what testing goal you want to achieve (e.g., generating test cases for a specific feature, analyzing logs, or validating code behavior) and which artifact you expect as output (e.g., test file, test report, test data). Name the exact target function/module and when known the intended scenario set.

2. **Establish Scope Boundaries**  
    Define the scope explicitly by identifying which functions/features are in scope and which are out of scope. Articulate negative paths, edge cases and boundary conditions you want to cover. For security-critical targets, explicitly include required security scenarios (e.g., enumeration resistance, timing-awareness checks).

3. **Anchor Success Criteria**  
    Ground success criteria in concrete, verifiable sources: acceptance criteria from user stories, requirement documents, real-world examples and past test data. Define measurable quality constraints (e.g., mutation score targets) and required technical practices (e.g., parametrization, dependency mocking, documentation quality) to reduce redundancy and improve maintainability.

**Reasoning:**  
This guideline is foundational because a clearly defined testing objective prevents misalignment between stakeholder expectations and LLM outputs. Identifying the specific testing objective and expected artifact ensures the LLM understands context and generates relevant outputs (see Guideline 01.A). Analyzing software requirements to explicitly identify testing objectives, scope boundaries and success criteria establishes the foundational target required for the entire testing lifecycle (see Guideline 01.B). Creating a formal test plan that outlines the testing strategy and specific test objectives clarifies the target before test design, ensuring that subsequent test generation aligns with software goals (see Guideline 01.C). Grounding success criteria in structured project documentation-such as user stories, requirement documents, acceptance criteria and real-world examples-ensures the testing objective is concrete and verifiable (see Guideline 01.F; see Guideline 01.H). Establishing explicit scope boundaries by identifying edge cases, negative paths and boundary conditions prevents ambiguous or incomplete test coverage (see Guideline 01.G). LLM experimentation further shows that explicitly enumerating scenarios sharply reduces scope creep while increasing scenario completeness (see Guideline 01.I) and that security-focused checks in sensitive domains are only reliably generated when requested directly in the objective (see Guideline 01.J). It also demonstrates that embedding technical practices in the objective (e.g., parametrization and mocking) improves maintainability and reduces redundant tests (see Guideline 01.K). Employing mutation testing as a success criterion optimizes test evaluation-while code coverage is a useful metric, its correlation with actual bug detection is weak; mutation testing ensures tests fulfill the primary objective of detecting faults (see Guideline 01.D).

**Example:**  
> Note: This example represents a structured test specification. It is the conceptual input used to inform prompt engineering, not the final prompt text itself.
```
Test Objective: Generate unit tests for the apply_discount(price, is_vip) function
Expected Artifact: PyTest test file with parametrized tests
Scope:
  - In: Boundary testing ($100), VIP logic, discount calculation
  - Out: Integration with payment systems
Success Criteria:
  - Acceptance: Function returns 20% discount only when price > 100 AND is_vip == True
  - Mutation: Test suite achieves >80% mutation score (kills high-order mutants)
Edge Cases:
  - Boundary: price == 100 (exactly at threshold)
  - Negative: non-VIP users, prices <= $100
```

**When to Apply:**  
- During the design phase, before any prompt execution or automated test code is generated
- When defining the baseline for test suite evaluation
- When multiple stakeholders are involved and clarity is needed
- When mutation testing or coverage metrics will be used to validate output
- During requirement analysis or test planning phases

**When to Avoid:**  
- Trivial utility functions where informal scoping is sufficient
- Exploratory testing phases where scope naturally evolves
- Legacy codebases with undefined or conflicting requirements
- Scenarios with missing functional context or incomplete code

---

### Guideline 02: Apply Prompt Engineering Techniques

**Description:**  
Use clear, structured prompts to express an already-defined testing objective and keep the prompt as simple as the task allows. Apply this sequence:
1. **Set the role clearly**  
    Example: “Act as a senior test engineer.” For larger suites, role assignment should encourage categorical organization.

2. **Provide focused context and input data**  
    Include the Class Under Test (or relevant method), key dependencies, relevant code snippets and test scenarios that support the defined objective.

3. **Define task instructions, constraints and output format**  
    State exactly what the model should do, what to prioritize and which artifact is expected. Also specify framework/assertion style, required edge cases, non-goals, naming conventions and exact structure. Add examples when format consistency is required.

4. **Choose the simplest prompting style that fits the task**  
    Start with **zero-shot** for simple tasks. Use **few-shot** when format consistency or domain-specific behavior is needed. For reasoning-heavy tasks, consider **Chain-of-Thought (CoT)** and verify outputs carefully. For narrow requests, a short instruction-light prompt can be sufficient.

5. **Separate system-level and task-level instructions when helpful**  
    Put stable behavior/persona rules in the system prompt and task-specific requests in the user prompt when persistent behavior is needed.

6. **Batch large tasks**  
    Split complex or multi-objective requests into smaller prompt batches instead of one overloaded prompt.

7. **Use targeted failure context for debugging tasks**  
    For bug localization or repair, include only the relevant traceback/error message and failing snippet instead of full logs.

8. **Use multimodal or graph context only when it adds value**  
    Add diagrams, UI screenshots, or graph representations only for structurally complex scenarios and keep them focused.


**Reasoning:**  
This guideline is important because prompt structure directly influences whether generated tests are relevant, executable and consistent: defining role, context, instructions, constraints, and output format reduces ambiguity and aligns outputs with the intended testing artifact (see Guideline 02.K). Clear and specific task framing also reduces generic or off-target outputs (see Guideline 02.R). Starting with simple prompting improves robustness for compilable code generation (see Guideline 02.G), while few-shot examples should be added when output consistency or format control is required (see Guideline 02.B). Role assignment improves perspective and focus during testing tasks (see Guideline 02.C) and experimentation additionally shows it can improve organization and navigability by producing clearer category-based test structures (see Guideline 02.T). Separating stable system behavior from task-specific user requests supports more predictable responses across iterations (see Guideline 02.M). Context quality is equally critical: providing CUT-level context improves oracle accuracy (see Guideline 02.K), combining functional code with explicit scenario lists improves test alignment (see Guideline 02.L) and including targeted snippets or error messages improves diagnostic precision (see Guideline 02.M). To prevent overload and token-related quality loss, complex objectives should be split into smaller prompt batches (see Guideline 02.O). For complex reasoning-heavy tasks, advanced prompting can be used with caution (see Guideline 02.F) and multimodal or graph context is valuable when structural understanding is needed, such as GUI or coverage-oriented analysis (see Guideline 02.D; see Guideline 02.E).

**Example:**  
```text
System prompt: You are a senior software tester.

User prompt:
Goal: Generate PyTest unit tests for password validation

Context:
- Use the full class/module logic
- Cover scenarios:
    1) valid strong password
    2) too short
    3) missing uppercase
    4) missing number
    5) empty input

Constraints:
- Use PyTest only
- Use @pytest.mark.parametrize for repeated boundary cases
- Include both positive and negative tests
- Do not generate integration tests

Output format:
- Return test file content only
- Test names must start with "test_"
- Add a short comment above each scenario group
```

**When to Apply:**  
- Test generation tasks where the target behavior, framework and output format are already defined
- Tasks that require consistent and executable results
- Prompts that need a clear structure, stable formatting or a reusable template
- Tasks where a few-shot example or smaller prompt batches improve reliability
- Debugging, repair or bug-localization tasks where targeted error context improves precision
- GUI or structurally complex testing tasks where multimodal or graph context adds clear value

**When to Avoid:**  
- Very small exploratory tasks where a short ad-hoc prompt is faster
- Scenarios with missing functional context, changing requirements or incomplete code
- Cases where the prompt would become overloaded instead of being split into smaller steps
- Cases where multimodal assets or graphs add noise instead of clarifying the testing objective

---

### Guideline 03: Evaluate, Expand, and Integrate
**Description:**
Measures the effectiveness of LLM generated test suite by combining traditional metrics with LLM-in-the-Loop feedback and AI-assisted mutation testing. 

1. **Track core metrics:** Monitor code coverage, defect detection rate, execution time, and test flakiness to maintain a reliable and fast feedback loop.
2. **LLM-in-the-Loop Feedback**: 
    - Integrate hybrid testing systems that combine LLMs with State of the Art traditional testing tools (e.g., linters, compilers) before manual review to correct hallucinations or missing elements.
    - Feed test failures, execution errors, and validation data back to the LLM as follow-up prompts, enabling the model to iteratively self-correct and enhance its generated tests
    - To further ensure accuracy, triangulate results across multiple LLM tools for cross-validation. 
    - Finally, proactively prompt the model to audit the current suite (e.g., asking, "What am I not testing?") to identify missing edge cases, unverified requirements, and unhandled error conditions.
3. **Generate High-Order Mutants:** Prompt the LLM to create complex, realistic test mutants by providing the focal method's code as context alongside few-shot examples of real-world bugs (adhering strictly to Guideline 2: Prompt Engineering).
4. **Target Surviving Mutants:** Write new unit tests specifically targeting the "Not Covered" and "Not Injected" areas exposed by surviving mutants to increase test coverage

**Reasoning:** 
Tracking code coverage, defect detection rate, execution time, and test flakiness ensures the test suite remains a fast, trusted feedback loop (Guideline 3.L; Guideline 3.H; Guideline 3.J). Unit tests provide the best balance of value, they are fast, maintainable, and offer strong protection against regression. Incorporating execution feedback through an "LLM-in-the-loop" approach actively addresses test correctness, reliability and test completeness by identifying and discarding invalid test cases, and iteratively fixing compilation problems and failures .LLMs are prone to hallucinations, which frequently result in unreliable or structurally flawed test code (Guideline 3.G; Guideline 3.S). Integrating models with reliable SOTA tools mitigates these issues, reinforcing test reliability, stability, and developer trust by ensuring complex testing scenarios are correctly validated (Guideline 3.E). Because LLMs are prone to genereating incorrect or logical inconsistent test data, cross-verifying outputs preserves the functional correctness and accuracy of the test suite (Guideline 3.H). Prompting LLMs to generate high-order mutants faults that closely mimic real-world defects. This provides a much stronger guarantee of test accuracy compared to traditional, first-order, rule-based mutations (Guideline 3D; Guideline 3.I; Guideline 3.U). Surviving mutants serve as highly actionable guides for developers to write targeted unit tests, directly eliminating test suite weaknesses (Guideline 3.C; Guideline 3.T). 

**Example**:   
**Context:** You are testing a Python function apply_discount(price, is_vip) that applies a 20% discount only if the price is over $100 and the user is a VIP. Your initial unit test only checks the "happy path" with a $150 price and a VIP user.

```
# 1. Original Method
def apply_discount(price, is_vip):
    if price > 100 and is_vip:
        return price * 0.8  # 20% discount
    return price

# 2. LLM-Generated High-Order Mutant
# The LLM is prompted to inject a complex fault. It alters the boundary, the logic gate, and the math.
def apply_discount_mutant(price, is_vip):
    if price >= 100 or is_vip: # Mutated: > to >=, and 'and' to 'or'
        return price * 0.8      
    return price
```
```
3. Survival & LLM-in-the-Loop Feedback: You run your test suite, and the mutant survives because your single test (price=150, is_vip=True) doesn't verify the $100 boundary or non-VIP users. You feed this surviving mutant back to the LLM with the prompt: "This mutant survived. Write targeted unit tests to kill it and cover the unexercised logic.
```

```
# 4. Resulting Targeted Tests
def test_discount_boundary_and_conditions():
    assert apply_discount(100, True) == 100   # Kills the ">=" mutation (targets the exact boundary)
    assert apply_discount(150, False) == 150  # Kills the "or" mutation (targets the unexercised boolean logic)
```

**When to Apply:** 
- Apply when you suspect the test suite provides a false sense of security by only exercising "happy path" scenarios.
- Use when undetected edge cases could cause severe system failures, financial loss, or safety risks.
- Ideal for authentication, authorization, or transaction logic where LLMs can simulate creative "logic-breaking" that traditional tools might miss.
- Acts as an automated "Senior Reviewer" to help teams without deep testing intuition identify subtle logic gaps.  

**When to Avoid:**
- Avoid when rapid iteration and time-to-market are prioritized over building a robust, long-term test infrastructure.
- Unsuitable when computational power, time, or API token budgets are limited, as continuous feedback loops are expensive.
- Do not apply to simple CRUD operations, getters/setters, or DTOs; the ROI on mutation testing for trivial code is near zero.
- Avoid in industries (e.g., medical, avionics) where auditors require strictly human-authored, traceable test cases for compliance.

---

### Guideline 04: Implement Iterative Validate-and-Repair Pipelines with Targeted Feedback

**Description:**  
Configure your CI/CD pipeline to automatically generate tests using LLMs, but implement a mandatory iterative validation loop. When generated tests fail to compile or execute, extract only the specific error traceback and the failing test block—not the entire suite—and feed this targeted feedback back to the LLM for automatic repair. Limit repair iterations to 2-3 cycles before escalating to human review.

**Reasoning:**  
LLM-generated tests frequently fail on first pass due to syntax errors, framework-specific behaviors, or hallucinated APIs, so generation should be embedded in CI/CD with explicit validation and refinement stages (see Guideline 04.A; see Guideline 04.B; see Guideline 04.E). Iterative validate-and-repair loops significantly improve execution correctness when runtime or compilation feedback is fed back into subsequent prompts (see Guideline 04.F), especially for framework-specific failures in React, Vue, and Angular ecosystems (see Guideline 04.G).

To preserve repair precision, feedback should remain targeted and task-specific: provide only the failing traceback/snippet and explicitly state the intended repair layer (test vs source) to avoid wrong-layer fixes and regression-inducing context overload (see Guideline 04.N). For consistency and fewer syntax mismatches during generation and repair, pin framework/assertion conventions and provide few-shot examples when project-specific structure matters (see Guideline 04.L; see Guideline 04.M).

Finally, bounded repair attempts with a human escalation gate prevent infinite loops and keep automation reliable in production workflows, aligning with staged evaluation and governance practices in CI pipelines (see Guideline 04.H; see Guideline 04.I; see Guideline 04.J).

**Example:**
```yaml
# CI/CD Pipeline Configuration
test_generation:
  - step: generate_tests
    script: python llm_generate_tests.py --target ./src
  
  - step: validate_and_repair
    script: |
      for i in {1..3}; do
        pytest ./generated_tests --json-report > report.json
        if [ $? -eq 0 ]; then break; fi
        
        # Extract only failing test + traceback
        python extract_failures.py report.json > failures.txt
        
        # Repair with targeted feedback
        python llm_repair_tests.py --errors failures.txt
      done
  
  - step: human_review
    when: manual
    condition: repair_iterations >= 3 || test_pass_rate < 85%
```

**When to Apply:**  
- When generating unit or integration tests for modern frameworks (React, Vue, Angular, Spring Boot)
- In projects with established test suites where coverage metrics can benchmark LLM output quality
- When CI/CD pipelines already support automated testing and have time budgets for iterative refinement (2-5 minutes)

**When to Avoid:**  
- For trivial utility functions where manual test writing is faster than prompt engineering and repair cycles
- When API costs or latency of multiple LLM calls (generation + 2-3 repairs) outweigh the value gained from automation
- In fully autonomous CD pipelines requiring sub-minute execution times where repair loops would block deployments

---

### Guideline 05: Human in the Loop 
**Description:** Testers and developers must actively mediate both the inputs and outputs when using LLMs for software testing.
1. Manually sanitize all prompts to remove confidential data 
2. Treat all AI-generated testing artifacts (unit tests, automation scripts, and metamorphic relations) as preliminary drafts. Human testers must manually evaluate these drafts for functional accuracy, code maintainability, logic, and strict alignment with internal team coding standards before integration into a CI/CD pipeline


**Reasoning:**  
Prompts often require details from internal systems. Without human oversight to manually sanitize and filter sensitive data, organizations face severe confidentiality risks and potential data leakage to external APIs (Guideline 5.A). Generative AI frequently suffers from hallucinations, faulty logic, and inaccuracies. Blindly trusting AI-generated tests risks propagating false positives or false negatives, which undermines test reliability and stability (Guideline 5.B, Guideline 5.F; Guideline 5.R; Guideline 5.G). Tests should be easily readable to enhance maintainability and decrease errors (Guideline 5.G). LLM generated output can contain errors and needs thorough validation (Guideline 5.D)

**Example:**  
A developer needs to write automated tests for a new, proprietary payment processing function.
Input Mediation: Instead of pasting the actual database schema and real API endpoints into the LLM prompt, the developer manually sanitizes the input by replacing them with generic, mock variable names.   
Output Mediation: The LLM generates the test suite. Before committing it, the developer reviews the code and notices the LLM hallucinated an assertion library method that the team does not use. The developer manually corrects the syntax to match the team's internal coding standards and runs the tests locally to verify accuracy before pushing it to the CI/CD pipeline.

**When to Apply:**   
Always when using LLMs for Test Generation. 

**When to Avoid:**  
There is no occasion in which human involvement should be avoided when working with LLMs in test generation.


## 2. Raw Guidelines (Source Documents)

### 2.1 Guidelines from Literature Readings

#### Guideline 01 - Defining the Testing Objective

**Readings Assigned:**  
- Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 96-104). IEEE.
- Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911-936.
- Zhang, Q., Fang, C., Gu, S., Shang, Y., Chen, Z., & Xiao, L. (2025). Large language models for unit testing: A systematic literature review. arXiv preprint arXiv:2506.15227.
- Li, Y., Liu, P., Wang, H., Chu, J., & Wong, W. E. (2025). Evaluating large language models for software testing. Computer Standards & Interfaces, 93, 103942.

**Extracted Guidelines:**  

**Guideline 01.A: Identify Testing Objective and Expected Artifact**  
**Source:** Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 96-104). IEEE.
**Description:** Identify the specific testing objective (such as generating test cases for a specific feature, analyzing logs, or refactoring existing scripts) and clearly specify the expected testing artifact before prompting the LLM.  
**Reasoning:** Creating an initial alignment between the test goal and the expected artifact ensures the LLM understands the context and generates relevant outputs suited to the testing task.  
**Example:** None provided.  

**Guideline 01.B: Identify Testing Objectives and Scope During Requirement Analysis**  
**Source:** Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911-936.  
**Description:** Analyze the software requirements to explicitly identify the testing objectives, scope boundaries, and criteria before generating tests.  
**Reasoning:** This establishes the foundational target and success criteria required for the testing lifecycle, ensuring subsequent LLM tasks align with intended requirements.  
**Example:** None provided.  

**Guideline 01.C: Outline Objectives in a Test Plan**  
**Source:** Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911-936.  
**Description:** Develop a formal test plan that clearly outlines the testing strategy and specific test objectives before attempting test design or execution.  
**Reasoning:** Creating a structured plan clarifies the testing target, ensuring that the test cases and test suites eventually generated align with the software's overarching goals.  
**Example:** None provided.  

**Guideline 01.D: Define Success Criteria Using Mutation Testing**  
**Source:** Zhang, Q., Fang, C., Gu, S., Shang, Y., Chen, Z., & Xiao, L. (2025). Large language models for unit testing: A systematic literature review. arXiv preprint arXiv:2506.15227.  
**Description:** Employ mutation testing to simulate real bugs and use the mutation score as a success criterion to optimize and evaluate the test cases generated by LLMs.  
**Reasoning:** While code coverage is widely regarded as a useful metric, its correlation with actual bug detection capability remains weak. Defining success through mutation testing ensures the generated tests fulfill the primary objective of effectively detecting faults.  
**Example:** None provided.  

**Guideline 01.E: Define Objective and Scope for Test Case Generation**  
**Source:** Li, Y., Liu, P., Wang, H., Chu, J., & Wong, W. E. (2025). Evaluating large language models for software testing. Computer Standards & Interfaces, 93, 103942.  
**Description:** Explicitly state the software name, its source or URL, the specific functions that need to be covered, and require exact execution steps when asking the LLM to generate test cases.  
**Reasoning:** Clarifying the test target (software name and URL), the scope boundaries (specific functions), and the expected testing artifact (exact steps) ensures the generated test cases are directly applicable and relevant to the objective.  
**Example:** "Write test cases for the software [software name] on the website [URL]. Ensure that your test cases cover [specific functions], and describe the exact steps required to execute each test case."  

#### Guideline 02 - Apply Prompt Engineering Techniques

**Readings Assigned:**  

- Bodicoat, A., Jahangirova, G., & Terragni, V. (2025, November). Understanding LLM-Driven Test Oracle Generation. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 29-39). IEEE.
- Godage, T., Nimishan, S., Vasanthapriyan, S., Palanisamy, V., Joseph, C., & Thuseethan, S. (2025, February). Evaluating the effectiveness of large language models in automated unit test generation. In 2025 5th International Conference on Advanced Research in Computing (ICARC) (pp. 1-6). IEEE.
- Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 96-104). IEEE.
- Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911-936.
- Zhang, Q., Fang, C., Gu, S., Shang, Y., Chen, Z., & Xiao, L. (2025). Large language models for unit testing: A systematic literature review. arXiv preprint arXiv:2506.15227.
- Li, Y., Liu, P., Wang, H., Chu, J., & Wong, W. E. (2025). Evaluating large language models for software testing. Computer Standards & Interfaces, 93, 103942.



**Extracted Guidelines:**  

**Guideline 02.A: Zero-Shot Prompting for General Testing Tasks**  
**Source:** Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911–936.  
**Description:** Directly prompt the LLM to perform a testing task, such as unit test generation or program repair, without providing any prior examples or demonstrations in the prompt. Use instructions or no instructions based on the situation.  
**Reasoning:** Often LLMS are pre-trained on large datasets of source codes, thats why it is common practice to just provide them with the prompt. In general providing prompts with clear instructions yields more accurate results and prompts without instructions are typically suitabel for very specific situations.  
**Example:** “please help me generate a JUnit test for a specific Java method...”  

**Guideline 02.B: Few-Shot Prompting for Specific Input Formats**  
**Source:** Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911–936. 
**Description:** Provide a set of high-quality demonstrations consisting of input and desired output pairs for the target testing task before presenting the actual task to the model.  
**Reasoning:** Demonstrations help the LLM to better understand human intention and criteria for what kind of answers are wanteed. This is especially important for non-intuitive and non-straightforward tasks.  
**Example:** Not provided.  

**Guideline 02.C: Assigning Roles to the LLM**  
**Source:** Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911–936.  
**Description:** In the prompt, assign the LLM to image itself in different roles (e.g. developer, user, QA).  
**Reasoning:** The change of perspective enables the LLM to see the testing tasks from different viewpoints and uncover aspects that potentially require more investigation or attention.
**Example:** Not provided.

**Guideline 02.D: Multimodal Chain of Thought**  
**Source:** Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911–936.    
**Description:** Explicitly prompt the model to generate intermediate reasoning steps before arriving at the final testing outcome. Also add sensory or cognitive cues (e.g. images) to the prompt.  
**Reasoning:** The inclusion of such cues stimulates the thinking and the creativity of LLMs. It helps the LLM to better understand the software context and potential issues.  
**Example:** Provide images when testing GUIs.  

**Guideline 02.E: Graph Prompting**  
**Source:** Wang, J., Huang, Y., Chen, C., Liu, Z., Wang, S., & Wang, Q. (2024). Software testing with large language models: Survey, landscape, and vision. IEEE Transactions on Software Engineering, 50(4), 911–936.     
**Description:** Provide the LLMs with graphs or visual structures to support the understanding and problem-solving of the LLM.  
**Reasoning:** Graph prompting is beneficial for analyzing structural information and enables the LLM to compehend the software under test.  
**Example:** Provide graphs when testing test coverage.  

**Guideline 02.F: Combine CUT Context with Simple Prompting**  
**Source:** Bodicoat, A., Jahangirova, G., & Terragni, V. (2025, November). Understanding LLM-driven test oracle generation. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 29-39). IEEE.  
**Description:** For the most consistent performance, standardize the prompt configuration to use Class Under Test (CUT) context combined with Zero-Shot or Few-Shot prompting. However, reserve reasoning-based techniques (CoT/ToT) for complex scenarios where a higher level of internal reasoning is needed, provided the output can be verified for compilation.  
**Reasoning:** This specific combination leads to the most consistently accurate LLM-generated test oracles. While CoT and ToT currently suffer from lower robustness, they demonstrate high potential for accuracy in cases where they successfully produce compilable assertions, suggesting they may be useful for high-complexity test logic.  
**Example:** "Use the following Chain-of-Thought steps in the prompt: (1) Identify the purpose of the test prefix and code under test, (2) Determine the expected outcome of the code and test, and (3) Formulate the correct test oracles".

**Guideline 02.G: Prioritize Simple Prompting (Zero/Few-Shot) for Robust Compilation**  
**Source:** Bodicoat, A., Jahangirova, G., & Terragni, V. (2025, November). Understanding LLM-driven test oracle generation. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 29-39). IEEE.  
**Description:** For generating unit test assertions, utilize Zero-Shot or Few-Shot prompting techniques to ensure the highest rates of compilable and accurate code.   
**Reasoning:** Simple prompting styles are more robust for code generation; Zero-Shot and Few-Shot prompts yield significantly higher compilation rates (67.38% and 72.96% respectively) and accuracy (~51-54%) compared to complex reasoning techniques like Chain-of-Thought (CoT) and Tree-of-Thoughts (ToT), which both struggle with compilation rates below 50%.    
**Example:** "Few-Shot prompting (F) involves providing the model with a limited number of examples [...] use three test oracle examples from the same repository as the test prefix".

**Guideline 02.H: Apply Prompt Engineering Techniques for Testing Tasks**  
**Source:** Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 96-104). IEEE.  
**Description:** Use structured techniques (see example below) in your prompt in order to guide the LLMs behavior in a favorable way.  
**Reasoning:** This approach reduces ambiguity and improves the precision of generated code artifacts.  
**Example:** Use prompt engineering techniques like the CARE method, one-shot or few-shot to provide the model with references for context.

**Guideline 02.I: Batch Processing for Token Mitigation**  
**Source:** Li, Y., Liu, P., Wang, H., Chu, J., & Wong, W. E. (2025). Evaluating large language models for software testing. Computer Standards & Interfaces, 93, 103942.  
**Description:** When using LLMs with token limitations, large inputs should be segmented into manageable parts, and code and other software information should be inputted sequentially into the LLM in batches.  
**Reasoning:** Exceeding the token limitations causes the LLM to "strike" and can lead to no thourough testing.  
**Example:** Not provided.

**Guideline 02.J: Professional Role-Play Prompting**  
**Source:** Li, Y., Liu, P., Wang, H., Chu, J., & Wong, W. E. (2025). Evaluating large language models for software testing. Computer Standards & Interfaces, 93, 103942.  
**Description:** Explicitly assign the LLM the "role of a tester" when performing software testing tasks.  
**Reasoning:** The quality of prompts significantly influences LLM outputs. Combining role-playing with specific testing tasks is a strategy used to develop high-quality prompts that ensure "meaningful outputs".  
**Example:**  "Please act as a professional software tester and complete the following test task: [Test Task]".  

**Guideline 02.K: Maximize Input Context with Class Under Test (CUT)**  
**Source:** Bodicoat, A., Jahangirova, G., & Terragni, V. (2025, November). Understanding LLM-driven test oracle generation. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 29-39). IEEE.  
**Description:** When prompting an LLM to generate test oracles (assertions), developers should provide the full Class Under Test (CUT) in the prompt rather than providing only the Method Under Test (MUT) or the test prefix alone.  
**Reasoning:** Providing class-level context significantly improves the reliability of bug detection. Experimental results show that CUT-level context achieves an accuracy of 53.64%, which significantly outperforms configurations providing only the MUT (40.38%) or the test prefix (40.74%).  
**Example:** "Test Prefix + CUT (C): Adds the class containing the test and method, providing more comprehensive context"  

**Guideline 02.L: Dual-Input Context Prompting**  
**Source:** Godage, T., Nimishan, S., Vasanthapriyan, S., Palanisamy, V., Joseph, C., & Thuseethan, S. (2025, February). Evaluating the effectiveness of large language models in automated unit test generation. In 2025 5th International Conference on Advanced Research in Computing (ICARC) (pp. 1-6). IEEE.  
**Description:** Provide the LLM with two specific inputs: the functional source code of the module and a detailed list of the test scenario descriptions.  
**Reasoning:** The functional code allows the model to understand the internal logic, while the scenario descriptions guide it to generate the unit tests.  
**Example:**  
<Module/Function Code>,
Based on the above module, create the test
cases below in Jest. Ensure they satisfy
all functional and mutation testing
requirements:
- <Test Scenario 1 Description>
- <Test Scenario 2 Description>
- .............................
- <Test Scenario n Description>

**Guideline 02.M: Targeted Bug Localization/Analysis**  
**Source:** Li, Y., Liu, P., Wang, H., Chu, J., & Wong, W. E. (2025). Evaluating large language models for software testing. Computer Standards & Interfaces, 93, 103942.   
**Description:** Optimize the input data provided to the LLM by including code snippets or other information (e.g. error messages) directly in the prompt.  
**Reasoning:** This approach helps to maximize the effectiveness especially with regard to token limitations.  
**Example:**  
"Analyze the following code
snippet: [Code Snippets]. Identify any potential bugs or defects and
suggest the likely locations of the bugs within the code" or "Given the following error
message [Error Message], please analyze the potential causes of the
error and provide possible solutions based on your understanding of
the software"

---

#### Guideline 03

**Readings Assigned:**  
- Wang, B., Chen, M., Deng, M., Lin, Y., Harman, M., Papadakis, M., & Zhang, J. M. (2026). A comprehensive study on large language models for mutation testing. ACM Transactions on Software Engineering and Methodology.
- Augusto, C., Bertolino, A., De Angelis, G., Lonetti, F., & Morán, J. (2025). Large language models for software testing: A research roadmap. arXiv preprint arXiv:2509.25043.
- Tian, Z., Shu, H., Wang, D., Cao, X., Kamei, Y., & Chen, J. (2024, September). Large language models for equivalent mutant detection: How far are we?. In Proceedings of the 33rd ACM SIGSOFT International Symposium on Software Testing and Analysis
- Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 96-104). IEEE.




**Guideline 3.A: Use Focused Context and Few-Shot Examples for Effective Mutant Generation**  
**Source:** Wang, B., Chen, M., Deng, M., Lin, Y., Harman, M., Papadakis, M., & Zhang, J. M. (2026). A comprehensive study on large language models for mutation testing. ACM Transactions on Software Engineering and Methodology.  
**Description:** Testers should prompt the LLM to generate test mutants by providing the focal method's code as context, combined with few-shot examples of real-world bug mutations (e.g., from defect datasets like QuixBugs), and request a structured JSON output. Providing the entire source file or including unit tests in the context should be avoided.  
**Reasoning:** To evaluate test suite effectiveness (mutation testing), the generated mutants must closely mimic real bugs. The paper demonstrates that providing the whole method along with few-shot examples achieves the best overall performance, producing mutants with the highest semantic similarity to real defects (highest Average Ochiai and Coupling Rate). Adding unit tests to the prompt slightly reduces effectiveness, and providing the entire file wastes tokens without improving mutant quality.

**Guideline 3.B: Implement a Fine-Tuned Code Embedding Strategy to filter out Equivalent Mutants**  
**Source:**  Tian, Z., Shu, H., Wang, D., Cao, X., Kamei, Y., & Chen, J. (2024, September). Large language models for equivalent mutant detection: How far are we?. In Proceedings of the 33rd ACM SIGSOFT International Symposium on Software Testing and Analysis
**Description:** To accurately filter out equivalent mutants, testers should employ a fine-tuned code embedding strategy using a small encoder-based LLM (such as UniXCoder or CodeT5+) combined with an MLP-based classifier. During the training phase, developers must simultaneously update the parameters of both the pre-trained LLM encoder and the classifier, rather than keeping the encoder's parameters fixed.  
**Reasoning:** Equivalent mutants exhibit the exact same behavior as the original program, which artificially restricts the mutation score and introduces redundant computational costs during test execution. The paper demonstrates that a fine-tuned code embedding strategy outperforms all pure prompting strategies and traditional EMD techniques (improving F1-scores by up to 78.85%) because it directly and efficiently compares the deep semantic vectors of mutant pairs

**Guideline 3.C: Leverage surviving mutants to increase test coverage and strengthen Unit Tests**       
**Source:** Wang, B., Chen, M., Deng, M., Lin, Y., Harman, M., Papadakis, M., & Zhang, J. M. (2026). A comprehensive study on large language models for mutation testing. ACM Transactions on Software Engineering and Methodology.  
**Description:** Testers should isolate the valid LLM-generated mutants that survive the current test suite and categorize them. Specifically, testers should write new unit tests targeting the "Not Covered" (NC) and "Not Injected" (NI) code areas exposed by these surviving mutants to increase test coverage   
**Reasoning:** LLM-based mutant generation tools produce a substantially higher proportion of "Not Covered" mutants (e.g., 79.52% for GPT-3.5 and 72.94% for GPT-4o) compared to traditional rule-based tools. Because LLMs naturally modify code lines that existing test suites currently fail to execute, these surviving mutants serve as highly actionable guides for developers to augment unit tests, directly improving test effectiveness and code coverage.

**Guideline 3.D: Prompt LLMs to Generate High-Order Mutants for Rigorous Evaluation**   
**Source:** Wang, B., Chen, M., Deng, M., Lin, Y., Harman, M., Papadakis, M., & Zhang, J. M. (2026). A comprehensive study on large language models for mutation testing. ACM Transactions on Software Engineering and Methodology.   
**Description:** To rigorously evaluate test suite effectiveness, testers should explicitly prompt the LLM to generate high-order mutants (HOMs) by composing multiple first-order mutant changes within a specific code element.
Reasoning: Test effectiveness validation requires complex, hard-to-kill faults. The paper's empirical results show that High-Order Mutants generated by LLMs generally achieve higher coupling rates and Average Ochiai scores than first-order mutants, meaning they align more closely with complex, real-world bugs. Evaluating a test suite against HOMs provides a stronger guarantee of test correctness and accuracy.

**Guideline 3.E: Mitigate Hallucinations by Integrating LLMs with Traditional SOTA Tools**  
**Source:** Augusto, C., Bertolino, A., De Angelis, G., Lonetti, F., & Morán, J. (2025). Large language models for software testing: A research roadmap. arXiv preprint arXiv:2509.25043.  
**Description:** Developers should build hybrid testing systems that combine LLMs with established state-of-the-art (SOTA) testing tools to cross-validate outputs and filter out flawed code or inaccurate calculations generated by the model.   
**Reasoning:** LLMs are prone to hallucinations, which frequently result in unreliable or structurally flawed test code. Integrating models with reliable SOTA tools mitigates these issues, reinforcing test reliability, stability, and developer trust by ensuring complex testing scenarios are correctly validated

**Guideline 3.F: Human in the Loop**   
**Source:** Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 96-104). IEEE.  
**Description:** Before integrating LLM-generated test cases or automation scripts into the CI/CD pipeline, testers must treat the outputs as preliminary drafts and manually evaluate them for accuracy, readability, and maintainability, comparing the generated assertions against their own implementation standards.    
**Reasoning:** LLMs frequently suffer from hallucinations, faulty logic, and inaccuracies. Relying solely on automated outputs risks propagating false positives or false negatives in test suites; rigorous human evaluation ensures test reliability, stability, and code quality.

**Guideline 3.G: Iterative Test Refinement using LLM-in-the-Loop**  
**Source:** Augusto, C., Bertolino, A., De Angelis, G., Lonetti, F., & Morán, J. (2025). Large language models for software testing: A research roadmap. arXiv preprint arXiv:2509.25043.    
**Description:** Testers should prompt the LLM iteratively by feeding back validation outputs as test coverage data, syntax errors, test smells, failure traces, and bug detection rates—directly into the model's context to guide the repair and enhancement of the generated unit tests.   
**Reasoning:** Incorporating execution feedback through an "LLM-in-the-loop" approach actively addresses test correctness and reliability by identifying and discarding invalid test cases, and iteratively fixing compilation problems and failures

**Guideline 3.H: Triangulate Outputs and Ground Prompts to Mitigate Hallucinations**   
**Source:** Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software   
**Description:** When validating defect explanations or generating test cases, testers should mitigate inaccurate artifacts by triangulating outputs across multiple different LLM tools, or by using retrieval-augmented generation (RAG) to ground the prompt strictly in verified project documentation.  
**Reasoning:** Because LLMs are prone to generating incorrect or logically inconsistent test data, cross-verifying outputs and anchoring responses in actual software documentation preserves the functional correctness and accuracy of the resulting test suite


---

#### Guideline 04

**Readings Assigned:**  
- Godage, T., Nimishan, S., Vasanthapriyan, S., Palanisamy, V., Joseph, C., & Thuseethan, S. (2025, February). Evaluating the effectiveness of large language models in automated unit test generation. In 2025 5th International Conference on Advanced Research in Computing (ICARC) (pp. 1-6). IEEE. 
- Haratua, W., Handoko, F. C., Valentino, K., & Sukmaningsih, D. W. (2025, August). Effectiveness of Artificial Intelligence in Automation Testing in Software Development Cycle. In 2025 International Conference on Information Technology and Computing (ICITCOM) (pp. 314-319). IEEE.  
- Sapkota, R., Roumeliotis, K. I., & Karkee, M. (2025). Vibe coding vs. agentic coding: Fundamentals and practical implications of agentic ai. arXiv preprint arXiv:2505.19443.
- Bodicoat, A., Jahangirova, G., & Terragni, V. (2025, November). Understanding LLM-Driven Test Oracle Generation. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 29-39). IEEE.
- Zhang, Q., Fang, C., Gu, S., Shang, Y., Chen, Z., & Xiao, L. (2025). Large language models for unit testing: A systematic literature review. arXiv preprint arXiv:2506.15227.
- Wimalagunasekara, G., & Vasanthapriyan, S. (2026, Februar). LLM-Based Unit Test Cases Generation for React, Vue, and Angular Components. 1–6.

**Extracted Guidelines:**  
For each relevant guideline from readings:

**Guideline 04.A: Integrate LLM Generation into the CI/CD Pipeline**  
**Source:** Godage, T., Nimishan, S., Vasanthapriyan, S., Palanisamy, V., Joseph, C., & Thuseethan, S. (2025, February). Evaluating the effectiveness of large language models in automated unit test generation. In 2025 5th International Conference on Advanced Research in Computing (ICARC) (pp. 1-6). IEEE.   
**Description:** Testers and developers should integrate the LLM-based test generation process directly into their continuous integration/continuous deployment (CI/CD) pipelines to automatically generate unit test cases in response to the latest code changes.  
**Reasoning:** Embedding the LLM into the CI/CD pipeline allows for seamless, ongoing test automation that scales with development, ensuring that new codebase modifications are continuously tested without relying entirely on manual test creation.  
**Example:** None provided.

**Guideline 04.B: Implementation of Validation Metrics for Generated Code**   
**Source:** Haratua, W., Handoko, F. C., Valentino, K., & Sukmaningsih, D. W. (2025, August). Effectiveness of Artificial Intelligence in Automation Testing in Software Development Cycle. In 2025 International Conference on Information Technology and Computing (ICITCOM) (pp. 314-319). IEEE.  
**Description:** Development teams must implement validation tools and metrics to verify the executability of unit tests generated by LLMs.  
**Reasoning:** LLMs suffer from output fallibility, often generating hallucinated but incorrect test cases or code with uncertain executability, which poses direct stability risks to the software development lifecycle.  
**Example:** None provided.

**Guideline 04.C: Feedback-Driven Autonomous Debugging and Rollback Integration**   
**Source:** Sapkota, R., Roumeliotis, K. I., & Karkee, M. (2025). Vibe coding vs. agentic coding: Fundamentals and practical implications of agentic ai. arXiv preprint arXiv:2505.19443.
**Description:** Developers should integrate autonomous debugging loops within the software lifecycle where an agent executes the full test suite. If a test fails, the agent must automatically isolate the code diff, revert the change, and retry with an alternate patch, finalizing the changes only when all tests pass successfully.  
**Reasoning:** Implementing automated rollback and recursive error resolution minimizes manual intervention, ensures reproducibility, and scales efficiently across larger codebases.  
**Example:** Agent Workflow: Refactor class structure -> Run full test suite -> On failure: isolate diff, revert, and retry with alternate patch -> Finalize changes only if all tests pass.

**Guideline 04.D: Integration with Automated Test Generators in Hybrid Pipelines**   
**Source:** Bodicoat, A., Jahangirova, G., & Terragni, V. (2025, November). Understanding LLM-Driven Test Oracle Generation. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 29-39). IEEE.
**Description:** Testers and developers should integrate LLMs into their automated testing workflows to complement existing test generation tools, such as EVOSUITE. In this pipeline, the automated tool produces assertion-free tests, and the LLM is subsequently queried to generate the test oracles.  
**Reasoning:** Automated generation tools typically rely on regression oracles that assume the current version of the code is correct, which limits their ability to detect faults. LLMs solve this integration bottleneck by generating new, potentially fault-revealing assertions that align with intended behaviors rather than just implemented ones.  
**Example:** A workflow where an automated test generator produces assertion-free tests, and the LLM complements the tool by generating new assertions to complete the test suite.

**Guideline 04.E: Post-Generation Automated Refinement Loops**   
**Source:** Bodicoat, A., Jahangirova, G., & Terragni, V. (2025, November). Understanding LLM-Driven Test Oracle Generation. In 2025 2nd IEEE/ACM International Conference on AI-powered Software (AIware) (pp. 29-39). IEEE.
**Description:** The CI/CD testing pipeline should incorporate a post-generation phase utilizing static analysis or LLM-driven refinement prompts to handle non-compiling outputs.  
**Reasoning:** Assertion compilability remains a major obstacle for LLM-generated test oracles. Implementing an automated feedback loop ensures that raw, uncompilable LLM outputs are refined into robust and usable assertions before the test suite is executed against the build.  
**Example:** None provided.

**Guideline 04.F: Iterative Validate-and-Repair Pipeline Loop**   
**Source:** Zhang, Q., Fang, C., Gu, S., Shang, Y., Chen, Z., & Xiao, L. (2025). Large language models for unit testing: A systematic literature review. arXiv preprint arXiv:2506.15227.
**Description:** CI/CD test generation pipelines should adopt a validate-and-repair paradigm for generated unit tests. When the LLM generates a test case that produces a compilation or runtime error, the pipeline must extract the error messages or dynamic execution feedback and feed them directly back into the LLM as a new prompt to iteratively refine and fix the test code.  
**Reasoning:** Generating syntactically correct test code on the first attempt remains a significant challenge for LLMs, frequently resulting in runtime and compilation errors. Implementing an iterative feedback loop utilizing dynamic feedback-based repair or static pattern-based repair significantly improves the execution correctness and overall reliability of the test cases.  
**Example:** Re-prompting ChatGPT with explicit compilation error messages to iteratively fix buggy test cases.

**Guideline 04.G: Framework-Specific Execution Feedback Loops**    
**Source:** Wimalagunasekara, G., & Vasanthapriyan, S. (2026, Februar). LLM-Based Unit Test Cases Generation for React, Vue, and Angular Components. 1–6.
**Description:** When generating tests for specific frontend frameworks (like React, Vue, or Angular), the testing pipeline should implement an iterative test fix loop that feeds framework-specific execution failures (such as JEST runner outputs) back to the LLM for correction.  
**Reasoning:** LLMs frequently produce failing suites due to framework-specific paradigms (like Angular's property binding or Vue's composition-API patterns) or by querying implementation details instead of public APIs. Looping execution failures back into the prompt allows the model to incrementally correct non-determinism and poor logic, potentially pushing test pass rates beyond 98%.  
**Example:** None provided.

---

#### Guideline 05 - Human in the Loop 

**Readings Assigned:**  
- Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software 




**Guideline 5.A: Sanitize Test Inputs and Anonymize Data**
**Source:** Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software    
**Description:** Before crafting a prompt for test generation or bug reproduction, the tester must manually sanitize the inputs and anonymize any confidential test data, user stories, or project specifications. If anonymization is not possible, testers must operate the LLM on restricted, private infrastructure.   
**Reasoning:** Prompts often require details from internal systems to generate accurate test cases. Failing to sanitize this data introduces severe confidentiality risks and potential data leakage to external APIs. Human oversight is required to filter sensitive data while maintaining enough context for the LLM to generate valid test inputs. Example: None provided

**Guideline 5.B: Human in the Loop**   
**Source:** Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software 
**Description:** Before integrating LLM-generated test cases or automation scripts into the CI/CD pipeline, testers must treat the outputs as preliminary drafts and manually evaluate them for accuracy, readability, and maintainability, comparing the generated assertions against their own implementation standards.  
**Reasoning:** LLMs frequently suffer from hallucinations, faulty logic, and inaccuracies. Relying solely on automated outputs risks propagating false positives or false negatives in test suites; rigorous human evaluation ensures test reliability, stability, and code quality.

**Guideline 5.C: Triangulate Outputs and Ground Prompts to Mitigate Hallucinations**   
**Source:** Santana, D., Magalhaes, C., & de Souza Santos, R. (2025, November). Software Testing with Large Language Models: An Interview Study with Practitioners. In 2025 2nd IEEE/ACM International Conference on AI-powered Software   
**Description:** When validating defect explanations or generating test cases, testers should mitigate inaccurate artifacts by triangulating outputs across multiple different LLM tools, or by using retrieval-augmented generation (RAG) to ground the prompt strictly in verified project documentation.  
**Reasoning:** Because LLMs are prone to generating incorrect or logically inconsistent test data, cross-verifying outputs and anchoring responses in actual software documentation preserves the functional correctness and accuracy of the resulting test suite





---

### 2.2 Guidelines from Grey Literature / Practitioner Sources

#### Guideline 01

**Sources Explored:**  
- Testomat.io. (2026, March 6). Test case generation using LLMs. https://testomat.io/blog/test-case-generation-using-llms/#use-acceptance-criteria-and-examples

**Extracted Guidelines:**  

**Guideline 01.F: Base the Objective on Structured Project Documentation**  
**Source:** Testomat.io. (2026, March 6). Test case generation using LLMs. https://testomat.io/blog/test-case-generation-using-llms/#use-acceptance-criteria-and-examples  
**Description:** Define the baseline testing objective using concrete information from user stories, requirement documents, acceptance criteria, bug reports, and past test data.  
**Reasoning:** Accurate test derivation requires a consistent, complete, and domain-specific foundation so the LLM can understand the real testing goal.  
**Example:** None provided.

**Guideline 01.G: Establish Scope Boundaries for Edge Cases and Negative Paths**  
**Source:** Testomat.io. (2026, March 6). Test case generation using LLMs. https://testomat.io/blog/test-case-generation-using-llms/#use-acceptance-criteria-and-examples  
**Description:** Explicitly define the logic and scope boundaries of the test to identify negative scenarios, edge cases, and boundary conditions before generation.  
**Reasoning:** Clear boundaries help the LLM cover invalid inputs and boundary values instead of producing only happy-path tests.  
**Example:** None provided.

**Guideline 01.H: Anchor Success Criteria to Acceptance Criteria and Examples**  
**Source:** Testomat.io. (2026, March 6). Test case generation using LLMs. https://testomat.io/blog/test-case-generation-using-llms/#use-acceptance-criteria-and-examples  
**Description:** Define success criteria using exact acceptance criteria and concrete real-world examples.  
**Reasoning:** Acceptance criteria provide unambiguous expectations for what constitutes a correct and complete test case.  
**Example:** None provided.

---

#### Guideline 02

**Sources Explored:**  
- andagon Team. (2025, December 1). Prompt engineering for software testers: What you really need to know in 2026. andagon. https://www.andagon.com/en/blog/prompt-engineering-for-software-testers
- Bhavani, R. (2025, September 19). Prompt engineering for testers. QA Touch. https://www.qatouch.com/blog/prompt-engineering-for-testers/
- Kumar, S. (2025, November 15). Prompt engineering for effective software testing. Medium. https://medium.com/@santoshkumar.devop/prompt-engineering-for-effective-software-testing-650b2c236b53
- Linders, B. (2025, November 6). How AI with prompt engineering supports software testing. InfoQ. https://www.infoq.com/news/2025/11/prompts-software-testing/

**Extracted Guidelines:**  

**Guideline 02.K: Use a Structured Prompt**  
**Source:** Kumar, S. (2025, November 15). Prompt engineering for effective software testing. Medium. https://medium.com/@santoshkumar.devop/prompt-engineering-for-effective-software-testing-650b2c236b53  
**Description:** Build every prompt using six core components: role, context, instructions, input data, constraints, and output format.  
**Reasoning:** The different components contribute to a clear and precise prompt, which ensures that the LLM knows the required requirements and expected output.  
**Example:** A detailed example is provided on the website.  

**Guideline 02.L: Use Few-Shot Prompting for Test Case Generation**  
**Source:** Kumar, S. (2025, November 15). Prompt engineering for effective software testing. Medium. https://medium.com/@santoshkumar.devop/prompt-engineering-for-effective-software-testing-650b2c236b53  
**Description:** Use few-shot prompting to provide the LLM with examples that guide it toward consistent outputs.  
**Reasoning:** Examples help the LLM stay consistent and ensure you receive the desired output format.  
**Example:** “Here are two sample test cases for the login page. Generate 5 more following the same structure.”  

**Guideline 02.M: Combine System Prompt and User Prompt**  
**Source:** Kumar, S. (2025, November 15). Prompt engineering for effective software testing. Medium. https://medium.com/@santoshkumar.devop/prompt-engineering-for-effective-software-testing-650b2c236b53  
**Description:** When interacting with the LLM, combine system and user prompts for a consistent and accurate response.  
**Reasoning:** System prompts help the LLM behave consistently and align with the purpose of the application, while user prompts specify the testing tasks.  
**Example:** A detailed example is provided on the website.  

**Guideline 02.N: Create Structured and Targeted Prompts**  
**Source:** Linders, B. (2025, November 6). How AI with prompt engineering supports software testing. InfoQ. https://www.infoq.com/news/2025/11/prompts-software-testing/  
**Description:** Create effective test prompts by combining a specific professional persona, detailed requirements and constraints, and a predefined structure for the output format.  
**Reasoning:** Using such a technique enables the LLM to generate structured and prioritized scenarios instead of random lists of test cases.  
**Example:** A detailed example is provided on the website.  

**Guideline 02.O: Don't Overload the Prompt**  
**Source:** Bhavani, R. (2025, September 19). Prompt engineering for testers. QA Touch. https://www.qatouch.com/blog/prompt-engineering-for-testers/  
**Description:** Break down complex tasks; if you have multiple objectives, handle them one at a time.  
**Reasoning:** If you try to include everything in a single, long prompt, the LLM can be overwhelmed, which leads to disorganized or incomplete results.  
**Example:** Generate test cases first, then create test data, then summarize defects — each with its own clear prompt.  

**Guideline 02.P: Use Examples in Your Prompts**  
**Source:** Bhavani, R. (2025, September 19). Prompt engineering for testers. QA Touch. https://www.qatouch.com/blog/prompt-engineering-for-testers/  
**Description:** Add examples to your prompt if you need specific formats in your test cases.  
**Reasoning:** Providing examples in your prompt helps the LLM understand the structure and level of detail you expect.  
**Example:** “Generate test cases for the checkout process. Format each test case as: [Test Case ID], [Description], [Expected Result]. Example: TC_01: Verify successful purchase with valid credit card. Expected Result: Order confirmation is displayed.”  

**Guideline 02.Q: Provide Context and Constraints**  
**Source:** Bhavani, R. (2025, September 19). Prompt engineering for testers. QA Touch. https://www.qatouch.com/blog/prompt-engineering-for-testers/  
**Description:** Ensure that you provide the LLM with enough context about your domain, the scope of a feature, and other relevant constraints.  
**Reasoning:** If the LLM does not have enough context, it tends to make incorrect assumptions or deliver irrelevant results. Providing enough context helps the LLM fit the solution to your needs.  
**Example:** Not provided.  

**Guideline 02.R: Be Clear and Specific**  
**Source:** Bhavani, R. (2025, September 19). Prompt engineering for testers. QA Touch. https://www.qatouch.com/blog/prompt-engineering-for-testers/  
**Description:** In your prompt, be clear and specific. For example, exactly describe which functionalities, scenarios, and edge cases should be covered.  
**Reasoning:** The LLM can better understand what you need if you provide a clear and specific prompt. If you are too vague, the LLM will output equally vague or generic responses.  
**Example:** “Generate 10 negative test cases for the login feature, focusing on invalid usernames, invalid passwords, empty fields, and SQL injection attempts.”  

**Guideline 02.S: Use a Good Prompt**  
**Source:** andagon Team. (2025, December 1). Prompt engineering for software testers: What you really need to know in 2026. andagon. https://www.andagon.com/en/blog/prompt-engineering-for-software-testers  
**Description:** Use the following attributes when writing a prompt:  
- Be specific  
- Provide full context  
- Define the expected output format  
- Use role-based prompts  
- Build reusable prompt templates  

**Reasoning:** Prompt engineering will become a critical skill. It helps speed up test case generation, improves the quality of test data, enhances bug reporting, and optimizes test planning and risk analysis.  
**Examples:**  
“As a Product Risk Analyst, create a risk matrix based on these user stories.”  
“Act as a Senior SDET and identify potential risks in the following test automation code.”  
“Create a structured bug report with steps, results, and environment details.”  

---

#### Guideline 03

**Sources Explored:**  
- Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad
- Ahmet Ildirim. (2024, March 24). How to assess the value of a unit test: The four pillars of an ideal test. Talon.One https://www.talon.one/blog/how-to-asses-the-value-of-a-unit-test  
- Larkin, G. (2024, December 5). How to generate unit tests with GitHub Copilot: Tips and examples. The GitHub Blog. https://github.blog/ai-and-ml/github-copilot/how-to-generate-unit-tests-with-github-copilot-tips-and-examples/

**Extracted Guidelines:**  

**Guideline 3.H: Code Coverage**  
**Source:** Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad   
**Description:** Monitor and measure the percentage of your codebase that is exercised by unit tests. 
**Reasoning:** Low code coverage serves as a warning signal for untested functionality, which increases the risk of hidden bugs.  
**Example:** Not provided

**Guideline 3.I: Mutation Testing**  
**Source:** Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad  
**Description:** Implement mutation testing by systematically injecting faults (altering sections of code) and executing your test suite to see if the tests catch the changes and fail.   
**Reasoning:** Mutation testing is used to determine the true strength and effectiveness of your unit tests. If the tests continue to pass even after the underlying code has been mutated, it reveals a critical weakness in the test suite's ability to detect real bugs   
**Example:** Not provided

**Guideline 3.J: Defect Detection Rate**  
**Source:** Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad  
**Description:** Track the proportion of real bugs and defects that are caught by your unit tests before the code reaches production.   
**Reasoning:** This metric serves as a direct indicator of your testing suite's overall health and reliability.
**Example:** Not provided

**Guideline 3.K: Test Execution Time**  
**Source:** Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad  
**Description:** Monitor and optimize the time it takes to run your unit test suite, ensuring that the tests execute quickly and efficiently.  
**Reasoning:** If unit tests are slow, developers are less likely to run them frequently, which significantly diminishes their utility as a continuous feedback loop. Keeping execution times short ensures that the tests can be seamlessly integrated into CI/CD pipelines without causing delays or bottlenecks.
**Example:** Not provided

**Guideline 3.L: Test Flakiness**  
**Source:** Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad  
**Description:** Actively monitor your test suite for "flaky" tests that exhibit inconsistent results (passing sometimes and failing others) without any changes being made to the underlying codebase. Once identified, prioritize investigating and resolving their root causes.  
**Reasoning:** Flaky tests severely erode developer confidence in the test suite. If a team cannot trust the results of a test suite, they may start ignoring legitimate test failures, assuming it is just another false alarm. Eliminating flakiness is essential for maintaining a reliable, trustworthy testing environment.  
**Example:** Not provided

**Guideline 3.M: Prioritize Important Code Paths**  
**Source:** Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad  
**Description:** Prioritize your unit testing efforts by focusing first on critical business rules and the most frequently used features of the application, rather than treating all code as equally important.
**Reasoning:** Not every piece of code carries the same weight, risk, or value to the user. By directing testing resources toward high-impact areas first, teams can guarantee that the most essential functions of the software are robustly tested and reliable.  
**Example:** Not provided

**Guideline 3.N: Write clear and concise Tests**  
**Source:** Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad   
**Description:** Ensure your test are easily readable. Descriptive test names, arranged setups, and concise assertions enhance maintainability and decrease errors.  
**Reasoning:** Easily readable tests are much simpler for the team to maintain and comprehend over time.  
**Example:** Not provided

**Guideline 3.O: Adhere to the Test Pyramid**  
**Source:** Ahmet Ildirim. (2024, March 24). How to assess the value of a unit test: The four pillars of an ideal test. Talon.One https://www.talon.one/blog/how-to-asses-the-value-of-a-unit-test   
**Description:** Structure your testing suite according to the test pyramid principle: build a large foundation of unit tests, a smaller middle layer of integration tests, and the fewest number of end-to-end (E2E) tests.  
**Reasoning:** Unit tests provide the best balance of value, they are fast, maintainable, and offer strong protection against regression. As you move up the pyramid, integration and E2E tests become slower, costlier, and harder to maintain due to complex dependencies.   
**Example:** Not provided

**Guideline 3.P: Use Test Coverage Tools**   
**Source:** Larkin, G. (2024, December 5). How to generate unit tests with GitHub Copilot: Tips and examples. The GitHub Blog. https://github.blog/ai-and-ml/github-copilot/how-to-generate-unit-tests-with-github-copilot-tips-and-examples/  
**Description:** Combine Copilot with traditional code coverage tools to assess current test coverage and identify untested code paths  
**Reasoning:** Using a dedicated tool highlights exact gaps in your test suite, allowing you to use Copilot precisely where it is needed to reduce the risk of unforeseen errors.   
**Example:** Not provided

**Guideline 3.R: Ask Copilot to Identify Missing Tests**   
**Source:** Larkin, G. (2024, December 5). How to generate unit tests with GitHub Copilot: Tips and examples. The GitHub Blog. https://github.blog/ai-and-ml/github-copilot/how-to-generate-unit-tests-with-github-copilot-tips-and-examples/  
**Description:** Prompt the AI to evaluate your current test suite for missing edge cases, requirement verifications, and error conditions.       
**Reasoning:** Testing for expected failures is just as important as testing good inputs. Copilot can help ensure your application handles errors gracefully by identifying blind spots.  
Example: Asking Copilot, “is there anything I’m not testing?” to generate code paths that result in expected failures.

---

#### Guideline 04

**Sources Explored:**  
- Latitude. (n.d.). The ultimate guide to CI/CD for LLMs: Building a robust evaluation pipeline. Latitude Blog. https://latitude.so/blog/ultimate-ci-cd-llm-evaluation-guide
- Sailotech. (2026, February 24). Wie man Gen AI-Testautomatisierung in CI/CD-Pipelines implementiert. Sailotech. https://sailotech.com/blog/how-to-implement-gen-ai-test-automation-in-ci-cd-pipelines/
- Lucas, F. (2025, October 17). Automating QA like a pro: How I built an AI-driven testing pipeline using Python. Top Python Libraries. https://medium.com/top-python-libraries/automating-qa-like-a-pro-how-i-built-an-ai-driven-testing-pipeline-using-python-781a5bcca35c
- keploy. (2025, February 14). Automatic test generation: Enhancing software quality and speed. DEV Community. https://dev.to/keploy/automatic-test-generation-enhancing-software-quality-and-speed-1fhn



**Guideline 04.H: Multi-Stage Evaluation Gates (The Kitchen Model)** 
**Source:** Latitude. (n.d.). The ultimate guide to CI/CD for LLMs: Building a robust evaluation pipeline. Latitude Blog. https://latitude.so/blog/ultimate-ci-cd-llm-evaluation-guide  
**Description:** Structure the CI pipeline into three distinct gates for testing LLM-based modules: 1. Deterministic Checks (Regex/JSON Schema validation for format). 2. Heuristic Scoring (Similarity/Helpfulness metrics). 3. LLM-as-a-Judge (Using a more powerful model like GPT-4o to grade the performance of a smaller testing model).  
**Reasoning:** Running high-level LLM evaluations on every commit is slow and expensive. Layering allows the pipeline to "fail fast" on simple formatting errors before committing expensive compute resources.  
**Example:** Engineering teams manage deterministic checks while domain experts conduct subjective evaluations through LLM-as-a-judge frameworks.

**Guideline 04.I: AI-Driven Test Automation Lifecycle in CI/CD** 
**Source:** Sailotech. (2026, February 24). Wie man Gen AI-Testautomatisierung in CI/CD-Pipelines implementiert. Sailotech. https://sailotech.com/blog/how-to-implement-gen-ai-test-automation-in-ci-cd-pipelines/
**Description:** Systematically integrate Generative AI into the CI/CD pipeline by targeting high-risk and frequently changing modules. Enable automatic test generation from user stories, integrate triggers within DevOps tools (e.g., Jenkins, GitHub Actions) for post-build execution, utilize self-healing for dynamic UI locators, and apply risk-based intelligent test selection.  
**Reasoning:** Dynamic application environments with frequent deployments render manual test script maintenance inefficient and costly. AI integration enables self-healing to minimize flaky tests and uses historical data and impact analysis to run only necessary tests, significantly reducing execution time while maintaining high test coverage and rapid release speeds.  
**Example:** Instead of running the complete regression suite on every single commit, the AI analyzes the specific code changes, selects only the impacted tests, and automatically updates any broken UI element locators during execution to prevent false pipeline failures.

**Guideline 04.J: Autonomous AI-Driven Testing Loop (The Self-Healing QA Architecture)** 
**Source:** Lucas, F. (2025, October 17). Automating QA like a pro: How I built an AI-driven testing pipeline using Python. Top Python Libraries. https://medium.com/top-python-libraries/automating-qa-like-a-pro-how-i-built-an-ai-driven-testing-pipeline-using-python-781a5bcca35c  
**Description:** Implement a fully autonomous, five-step testing architecture within the CI/CD workflow: 1. Detect code changes via Git hooks. 2. Use an LLM (e.g., OpenAI API) to dynamically generate or update tests. 3. Execute the test suite (e.g., using pytest). 4. Use AI heuristics to analyze and classify test failures (regression, environment issue, or flaky test). 5. Auto-repair and patch flaky tests intelligently before pushing an automated PR update.  
**Reasoning:** Relying on humans to constantly fix flaky tests and manually maintain test scripts creates severe bottlenecks. Making the testing loop smart enough to adapt, self-evaluate, and auto-repair removes developers from the QA maintenance cycle and accelerates deployment.
**Example:** When a developer pushes a new commit, the CI pipeline triggers an AI Test Generator to create necessary test files. If the Pytest Executor flags a failure, an "AI Analyzer + Fixer" determines if it is a flaky timing issue, patches the test code automatically, and retries the test without manual intervention.

**Guideline 04.K: Traffic-Driven Automatic Test Generation (The Keploy Model)** **Source:** keploy. (2025, February 14). Automatic test generation: Enhancing software quality and speed. DEV Community. https://dev.to/keploy/automatic-test-generation-enhancing-software-quality-and-speed-1fhn
**Description:** Implement automatic test generation techniques—such as AI/ML-based testing, fuzz testing, and model-based testing—to create test cases without manual intervention. Utilize AI-powered tools to capture real user API traffic and automatically generate corresponding test cases and API mocks, seamlessly integrating this workflow directly into the CI/CD pipeline.  
**Reasoning:** Manually writing tests is time-consuming, prone to human error, and often fails to cover complex edge cases. Automatically generating tests from actual system behavior and real-world traffic patterns improves comprehensive test coverage, minimizes manual oversight, and accelerates development cycles while keeping test maintenance manageable.  
**Example:** An engineering team uses an AI-driven tool like Keploy to record live or staging API traffic. The tool automatically converts these captured interactions into executable test cases and creates the necessary stubs and mocks, allowing the team to validate real-world usage patterns without writing the test scripts by hand.

#### Guideline 05

**Sources Explored:**  
- Larkin, G. (2024, December 5). How to generate unit tests with GitHub Copilot: Tips and examples. The GitHub Blog. https://github.blog/ai-and-ml/github-copilot/how-to-generate-unit-tests-with-github-copilot-tips-and-examples/ 
- Mahesh, H. (2025, October 29). How to keep human in the loop (HITL) during Gen AI testing? testRigor. Retrieved April 19, 2026, from https://testrigor.com/blog/how-to-keep-human-in-the-loop-hitl-during-gen-ai-testing/


**Guideline 5.D**: Review Suggestions Carefully  
**Source**: Larkin, G. (2024, December 5). How to generate unit tests with GitHub Copilot: Tips and examples. The GitHub Blog. https://github.blog/ai-and-ml/github-copilot/how-to-generate-unit-tests-with-github-copilot-tips-and-examples/   
 **Description:** Never blindly trust AI-generated tests. You must manually evaluate the output, check the code, and pass it through your standard review processes.    
**Reasoning:** Just like human-generated code, AI outputs can contain errors or misalign with your standards and need thorough validation.  
**Example:** Running the Copilot-generated tests through standard linters before accepting them.

**Guideline 5.E:** Be Flexible and Iterative  
**Source:** Larkin, G. (2024, December 5). How to generate unit tests with GitHub Copilot: Tips and examples. The GitHub Blog. https://github.blog/ai-and-ml/github-copilot/how-to-generate-unit-tests-with-github-copilot-tips-and-examples/  
**Description:** Treat test generation as a back-and-forth process. If the first output is incorrect, hallucinated, or missing elements, reframe your prompt and try again.    
**Reasoning:** Unit tests describe complex code behavior, and the AI's first iteration may not perfectly capture your needs. Iterating helps refine the output into something usable.    
**Example:** Reframing the prompt if Copilot fails to generate necessary mock objects on its first attempt.

**Guideline 5.G: Write clear and concise Tests**  
**Source:** Carlmax. (2025, September 30). Measuring the effectiveness of software unit tests. Medium. https://medium.com/@carlmax6632/measuring-the-effectiveness-of-software-unit-tests-3051d697c2ad   
**Description:** Ensure your test are easily readable. Descriptive test names, arranged setups, and concise assertions enhance maintainability and decrease errors.  
**Reasoning:** Easily readable tests are much simpler for the team to maintain and comprehend over time.  
**Example:** Not provided



---

### 2.3 Guidelines from LLM Experimentation

#### Guideline 01: Defining Testing Objectives

**Models Used:**  
- Claude 4.5 Sonnet

**Prompts Used:**  
- See `experimentation/guideline-objective-prompts.md` for full prompts

**Extracted Guidelines:**

**Guideline 01.I: Specify Exact Scenarios to Prevent Scope Creep and Improve Focus**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** Enumerate the exact test scenarios to cover (e.g., "valid credentials, invalid password, non-existent user, locked account, empty inputs") rather than generic requests ("generate tests for authentication"). Include scenario count when known.  
**Reasoning:** The vague prompt ("Generate tests for authentication") resulted in 24 tests covering 3 classes (User, hash_password, authenticate_user), with 7 out-of-scope tests (29%). The precise prompt specifying "authenticate_user() function" and listing 12 exact scenarios produced 13 focused tests with 0 out-of-scope tests. Precision reduced test count by 46% while maintaining 100% scenario coverage (vs 92% with vague prompt).  
**Evidence:**
- Vague prompt: 24 tests, 18 for authenticate_user, 11/12 scenarios (92%), 7 out-of-scope tests
- Precise prompt: 13 tests, 13 for authenticate_user, 12/12 scenarios (100%), 0 out-of-scope tests
- Improvement: -46% test count, +8% scenario coverage, -100% scope creep

**Example:**
```
❌ Vague: "Generate tests for authentication"
→ Result: 24 tests (User class, hash_password, authenticate_user)

✅ Precise: "Generate PyTest unit tests for authenticate_user() covering:
1. Valid credentials with active, unlocked account
2. Invalid password with existing user
3. Non-existent user
4. Locked account (user.is_locked = True)
5. Inactive account (user.is_active = False)
6-12. [Empty/None/whitespace inputs]"
→ Result: 13 tests (only authenticate_user, all scenarios covered)
```

**Guideline 01.J: Explicitly Request Security Testing for Security-Critical Functions**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** For security-critical functions (authentication, authorization, payment processing), explicitly request security-focused tests (e.g., "username enumeration prevention", "timing attack awareness") in the prompt. Do not rely on the LLM to infer security concerns from domain context alone.  
**Reasoning:** Despite "authentication" being a security-critical domain, the vague prompt resulted in 0 security tests and no timing attack awareness. Only when the precise prompt explicitly requested "Username enumeration prevention (same behavior for non-existent user vs wrong password)" and "Timing attack awareness (document in comments)" did the LLM generate dedicated security tests and documentation.  
**Evidence:**
- Vague prompt: 0 security tests, 0 timing attack mentions, no security documentation
- Precise prompt: 2 security tests (username enumeration prevention + verification), timing attack comments, module-level security docstring

**Example:**
```
❌ Without explicit security request:
"Generate tests for authentication"
→ Result: 0 security tests

✅ With explicit security request:
"Security Considerations:
- Username enumeration prevention (same behavior for non-existent user vs wrong password)
- Timing attack awareness (document in comments)"
→ Result: 
  - test_username_enumeration_prevention()
  - Module docstring: "In production, consider constant-time comparison..."
```

**Guideline 01.K: Specify Technical Practices to Enforce Code Quality Patterns**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** Include technical requirements in the objective (e.g., "Use @pytest.mark.parametrize for repeated scenarios", "Include docstrings", "Mock external dependencies") to enforce best practices and prevent redundant code.  
**Reasoning:** The vague prompt generated 7 individual test functions for empty/None input scenarios without parametrization. The precise prompt explicitly requested "Use @pytest.mark.parametrize for empty/None input tests", resulting in a single parametrized test covering all 7 scenarios, reducing redundancy and improving maintainability.  
**Evidence:**
- Vague: 7 separate test functions for empty/None scenarios (no parametrize)
- Precise: 1 parametrized test covering 7 scenarios
- Code reduction: 85% fewer functions for same coverage

**Example:**
```
❌ Without technical specification:
No parametrize usage → 7 individual test functions

✅ With technical specification:
"Use @pytest.mark.parametrize for empty/None input tests"
→ Result:
@pytest.mark.parametrize("username,password", [
    ("", "password"), ("username", ""), ("", ""),
    (None, "password"), ("username", None),
    ("   ", "password"), ("username", "   ")
])
def test_invalid_credentials_rejected(username, password, db):
    assert authenticate_user(username, password, db) is None
```

---

#### Guideline 02: Prompt Engineering Techniques

**Models Used:**  
- Claude 4.5 Sonnet

**Prompts Used:**  
- See `experimentation/guideline-role-assignment-logs.md` for role assignment experiments
- See `experimentation/guideline-iterative-refinement-logs.md` for iterative refinement experiments

**Extracted Guidelines:**

**Guideline 02.T: Role Assignment Improves Test Organization and Categorization**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** Role assignment ("You are a software tester") leads to better test organization with explicit section markers (e.g., "=== Security ===", "=== Happy Path ===") and logical categorization of test cases.  
**Reasoning:** Role assignment experiments showed that generic role prompts produced tests organized into clear sections with category labels, while no-role prompts produced flat test structures. The generic role organized tests with "=== Security ===" sections and "Security Test:" labels in docstrings, improving navigability and maintainability.  
**Evidence:**
- No role: Flat test structure, organized by test type only
- Generic role: Clear sections ("=== Security ===", "=== Authentication ==="), categorical organization
- Generic role added "Security Test:" labels in docstrings
- Better logical grouping of related test scenarios

**Example:**
```python
# With role "You are a software tester":
class TestAuthentication:
    # === Happy Path ===
    def test_valid_credentials(self): ...
    
    # === Security ===
    def test_username_enumeration_prevention(self):
        """Security Test: Verify identical behavior for invalid user vs wrong password."""
        ...
```

---

#### Guideline 03: Test Validation and Mutation Testing

**Models Used:**  
- Claude 4.5 Sonnet

**Prompts Used:**  
- See `experimentation/guideline-mutation-testing-prompts.md`

**Extracted Guidelines:**

**Guideline 03.S: Iterative LLM-in-the-Loop Feedback Improves Test Completeness**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** Feed test execution results, coverage reports, and identified gaps back to the LLM iteratively to progressively improve test suite completeness. Each iteration should build on previous findings rather than regenerating from scratch.  
**Reasoning:** The iterative refinement experiment demonstrated that feeding back gap analysis, quality issues, and security concerns through 6 iterations improved the test suite from 4 basic tests to 28 comprehensive tests with ~95% coverage. Each iteration built on the previous state, avoiding regression and systematically addressing identified weaknesses.  
**Evidence:**
- Iteration 1: 4 tests (baseline)
- Iteration 2: Gap analysis identified 15+ missing scenarios
- Iteration 3: Added 11 edge case tests
- Iteration 4: Quality review found 6 issue categories
- Iteration 5: Refactored to fix issues (cleanup, assertions, fixtures)
- Iteration 6: Security review added 9 security tests
- Final: 28 tests, ~95% coverage, 0 known issues

**Example:**
```
Iteration 2 feedback prompt:
"The test suite currently has 4 tests. Coverage analysis shows:
- Boundary conditions: 0% covered
- Security scenarios: 0% covered  
- Edge cases (empty, null, max values): 30% covered

Based on this gap analysis from Iteration 1, generate tests to address the missing scenarios."
```

**Guideline 03.T: "What Am I Not Testing?" Prompts Systematically Identify Test Gaps**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** Use explicit gap detection prompts ("What am I NOT testing? What edge cases, error conditions, or requirement verifications are missing?") to systematically identify test suite blind spots before iterative expansion. The LLM analyzes existing tests against the implementation and business rules to identify missing scenarios across all testing dimensions.  
**Reasoning:** The gap detection experiment started with 2 basic tests (40% coverage estimate) and identified 23 distinct gaps across 5 categories (boundary, error, edge, combinations, other). The LLM provided prioritized gaps (Critical/Important/Nice-to-Have) with explanations of why each matters. Implementing all identified gaps increased test count from 2 to 25 and coverage from 40% to 100%.  
**Evidence:**
- Initial suite: 2 tests, ~40% coverage, unknown gaps
- Gap detection: 23 gaps identified (6 boundary, 4 error, 5 edge, 4 combo, 4 other)
- After gap fixes: 25 tests, 100% coverage, 0 remaining gaps
- Improvement: +23 tests (+1150%), +60% coverage
- Prioritization: 5 Critical, 4 Important, 14 Nice-to-Have
- All gaps included "Why it matters" explanations

**Example:**
```
Gap Detection Prompt:
"Review this test suite and tell me: What am I NOT testing?
Analysis needed:
1. What edge cases are missing?
2. What error conditions are not tested?
3. What boundary conditions are missing?
4. What requirement verifications are absent?
5. What combinations of inputs are not covered?"

Result: 
- Identified critical gap: "VIP at exactly $100 → no discount"
- Explanation: "Business rule says > $100, need to verify $100 exactly does NOT trigger discount"
- Priority: Critical (Must Have)
```

**Guideline 03.U: LLM-Generated High-Order Mutants Simulate Realistic Multi-Bug Scenarios**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** Generate high-order mutants (combining 2-3 bug patterns) using LLMs to create more realistic bug scenarios than traditional single-change mutations. High-order mutants combine boundary errors, logic gate changes, and arithmetic mistakes that commonly occur together in real-world bugs.  
**Reasoning:** The mutation testing experiment generated 5 high-order mutants averaging 2 changes each. These mutants represented realistic bug scenarios like "requirement misinterpretation + logic inversion" or "condition weakening + calculation error." Against the initial 2-test suite, 4/5 mutants (80%) survived. After implementing gap-driven tests (11+ tests), all mutants were killed (0% survival). High-order mutants exposed weaknesses in the test suite that single-change mutants might miss, particularly at boundaries and error conditions.  
**Evidence:**
- 5 high-order mutants generated, avg 2.0 changes per mutant
- Realistic bug scenarios: 4/5 (80%)
- Survival against initial suite: 4/5 (80%)
- Survival against gap-enhanced suite: 0/5 (0%)
- Mutants matched gaps: zero validation (Mutant 3), boundary at $100 (Mutant 1, 3), discount verification (Mutant 2, 4)
- Mutant types: Boundary + Logic (2), Boundary + Arithmetic (2), Logic + Arithmetic (1)

**Example:**
```
High-Order Mutant: Relaxed Validation with Wrong Threshold
Changes:
1. Boundary: amount <= 0 → amount < 0 (allows zero)
2. Constant: 100 → 99 (wrong threshold)

Bug Scenario: Developer relaxed validation thinking "negative is bad enough" 
and misunderstood "$100" requirement as "$99"

Survival: High - survives unless tests check zero AND exact $100 boundary

Killed by: test_zero_amount() + test_vip_at_100()
```

**Guideline 03.V: Iterative Gap Detection + Targeted Generation Achieves Systematic Coverage**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** Use a multi-step approach: (1) generate initial basic tests, (2) run gap detection prompt, (3) generate tests targeting identified gaps, (4) repeat if necessary. This systematic approach builds comprehensive coverage through focused iterations rather than attempting complete generation in one shot.  
**Reasoning:** The iterative experiment demonstrated that starting with 2 basic tests (40% coverage) and running one gap detection iteration identified 23 missing scenarios. Generating targeted tests for these gaps resulted in 25 total tests with 100% coverage. The iterative approach avoided scope creep (no out-of-scope tests) and ensured systematic coverage by addressing gaps by category (boundary → error → edge → combinations).  
**Evidence:**
- Iteration 1: 2 tests, 40% coverage (baseline)
- Iteration 2: Gap detection identified 23 gaps categorized by priority
- Iteration 3: Generated 23 targeted tests addressing gaps
- Final: 25 tests, 100% coverage
- Total iterations: 2 (gap detection + targeted generation)
- Test efficiency: 0 redundant or out-of-scope tests
- Categories addressed: Input validation (8), Boundaries (5), Precision (5), State (3), Errors (2)

**Example:**
```
Iteration 1 Prompt: "Generate basic PyTest tests for apply_discount. Cover happy path and basic error cases."
→ Result: 2 tests

Iteration 2 Prompt: "What am I NOT testing? Identify gaps."
→ Result: 23 gaps identified (prioritized)

Iteration 3 Prompt: "Generate tests for these gaps: [list Critical + Important gaps]"
→ Result: +23 tests, 100% coverage

Total: 2 iterations, 25 tests, systematic coverage
```

---

#### Guideline 04

**Models Used:**  
- Claude 4.5 Sonnet
- Claude Code with Claude 4.5 Sonnet
- GPT 5.4

**Prompts Used:**  
- See `experimentation/guideline-framework-pinning-logs.md`
- See `experimentation/guideline-zero-shot-vs-few-shot-logs.md`

**Extracted Guidelines:**  
For each relevant guideline from readings:

**Guideline 04.L: Explicitly Pin Testing Frameworks and Assertion Styles in Prompts**  
**Source:** LLM Experimentation (Gemini 3)  
**Description:** Developers must explicitly state the exact testing framework (e.g., PyTest, JUnit 5) and the preferred assertion library (e.g., AssertJ, Chai) within the initial prompt's system instructions.  
**Reasoning:** Models frequently default to generic or outdated testing syntax when the specific framework is omitted. Gemini 3 defaulted to `unittest` when no framework was specified, but correctly used PyTest with `@pytest.mark.parametrize` when explicitly instructed. Explicitly pinning the framework reduces syntax hallucinations and compilation errors.  
**Example:** "Write a PyTest suite for this function utilizing `pytest.mark.parametrize` and strictly use standard Python `assert` statements."

**Guideline 04.M: Provide Few-Shot Examples for Project-Specific Conventions and Consistency**  
**Source:** LLM Experimentation (Cross-Model Comparison: Claude 4.5 Sonnet, Gemini 2.5 Pro, GPT-5)  
**Description:** For complex state-driven integration tests, provide few-shot examples showing project-specific fixture patterns, naming conventions, and test structure. While advanced models (Claude 4.5 Sonnet, Gemini 2.5 Pro) can infer authentication and database fixture patterns in zero-shot scenarios, few-shot examples ensure consistency and prevent incomplete outputs.  
**Reasoning:** Cross-model testing revealed that strong models can successfully generate state-driven tests without examples, but few-shot examples provide critical benefits: (1) ensure project-specific naming conventions, (2) prevent incomplete outputs (GPT-5 few-shot omitted fixture definitions entirely), and (3) make output more predictable across model updates. Few-shot is essential for weaker models and beneficial for consistency even with strong models.  
**Example:** Provide a complete working test showing the project's fixture pattern:
```python
@pytest.fixture
def authenticated_user(database):
    user = User("test_001", "testuser", "test@example.com")
    database.add_user(user)
    user.authenticate("testuser_pass")
    return user
```

**Guideline 04.N: Explicitly Specify Target Layer in Iterative Repair Prompts**  
**Source:** LLM Experimentation (Gemini 3)  
**Description:** When requesting test repairs, explicitly specify which layer to modify: "Fix the test assertion" vs "Fix the source code implementation." Use targeted tracebacks (specific failing test + error) rather than complete build logs, but clarify the expected fix location.  
**Reasoning:** Gemini 3 experiments revealed that ambiguous repair prompts ("fix the logic") led to source code modifications instead of test repairs, even with targeted tracebacks. Both full build logs and isolated tracebacks produced wrong-layer fixes when the prompt didn't explicitly state "modify the test code only." Prompt ambiguity is a larger issue than context size for iterative repair.  
**Example:** Instead of "Fix the logic for this test," use: "The test assertion is incorrect. Modify the test code to use the correct expected value. Do not modify the Payment class."

---

#### Guideline 05: Human in the Loop and Review

**Models Used:**  
- Claude 4.5 Sonnet

**Prompts Used:**  
- See `experimentation/guideline-iterative-refinement-logs.md`

**Extracted Guidelines:**

**Guideline 05.F: Human-Guided Iterative Refinement Outperforms Single-Shot Generation**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** Human review at each iteration to guide the next refinement step produces significantly higher quality test suites than single comprehensive prompts. The human should review outputs, identify priorities (gaps, quality, security), and direct the LLM's next focus area.  
**Reasoning:** The iterative refinement experiment demonstrated that human guidance at each step resulted in a 7x improvement in test count (4→28) and systematic coverage of all testing dimensions. Single-shot prompts attempting to specify everything upfront are harder to write, harder for LLMs to execute correctly, and miss emergent issues discovered during generation.  
**Evidence:**
- Single-shot attempt: 4 basic tests, incomplete coverage
- Human-guided iteration 1→2: Human decided gap analysis needed
- Human-guided iteration 2→3: Human prioritized edge cases over other gaps
- Human-guided iteration 3→4: Human requested quality review
- Human-guided iteration 4→5: Human directed refactoring focus
- Human-guided iteration 5→6: Human requested security review
- Result: 28 tests, systematic coverage, 0 rework needed

**Example:**
```
Human guidance at Iteration 3:
"The gap analysis identified 15 missing scenarios. Let's prioritize:
1. First, add all boundary condition tests (amounts: 0.01, 10000, etc.)
2. Then parametrize invalid amounts  
3. Skip the long description test for now - low priority

Generate tests for #1 and #2 only."
```

**Guideline 05.G: Human Review Catches Cross-Cutting Concerns LLMs Miss**  
**Source:** LLM Experimentation (Claude 4.5 Sonnet)  
**Description:** LLMs focus on explicitly requested aspects but miss cross-cutting concerns like security, performance, and maintainability unless specifically prompted. Human review should check for these concerns and add dedicated review iterations.  
**Reasoning:** The iterative refinement experiment showed that initial prompts requesting "error cases" produced 0 security tests. Only after human reviewer recognized the security gap and added a security-focused review iteration did the LLM generate critical authorization, enumeration, and injection tests. LLMs generate what is asked but don't proactively consider cross-cutting concerns.  
**Evidence:**
- Initial prompt included "error cases" → 0 security tests generated
- Human review (Iteration 5) noticed: "No authorization or injection tests"
- Human added security review iteration → 9 security tests generated
- Similar pattern for: quality issues (human noticed, prompted review), test organization (human requested categorization)

**Example:**
```
Human recognition of missing cross-cutting concern:
"The test suite has good functional coverage but I notice:
- Zero tests verify users can only access their own payments (authorization)
- Zero tests check for SQL injection in description field
- Zero tests verify payment enumeration protection

Let's add a dedicated security review iteration."
```

## 3. References

For a specific reference, refer to the **"Source"** field within each numbered raw guideline.

## 4. Appendix

- **A. Full Prompt Logs:** All prompt logs can be found in the **experimentation** directory.

---

*Template version: 1.0 | Last updated: 24 February 2026*
