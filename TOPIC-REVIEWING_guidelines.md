# Topic-XX_Guidelines.md

> **Template for Student Guideline Packages**  
> *Fill in the bracketed sections `[...]` with your team's curated content.*

---

## Team Information

**Team Name:** `[Your Team Name/ID]`  
**Topic:** Reviewing
**Date:** `[Submission Date]`  
**Authors:** Maximilian Alp Grüder, 

---
use ICE Score as an example !!!!!
two reviewing tasks. reviewing ai generated code, and reviewing in general 
2.11 could be conflicting with some other guidelines
2.15 using llms here instead of static code. llms can also do locally what static code do for a whole pull request. 

to do: 
which guidelines conflict? 
which idea is repeated the most? 
## 1. Unified Guidelines

> **Note:** These are the merged, refined guidelines that your team recommends to the class. Each guideline should be actionable, specific, and usable during real SE/coding tasks.

### Guideline 1: Combine Static Analysis with LLM Reviews (Hybrid Approach)

**Description:**  
Developers should execute static analysis tools (e.g., linters, CodeQL, PMD) first, and inject their outputs into the LLM's prompt to generate context-aware and standards-compliant code review comments.

**Reasoning:**  
Relying solely on LLMs for code review can provide broad issue coverage but often at the expense of precision and functional correctness (1, 2). Conversely, Knowledge-Based Systems (KBS) like static analyzers provide highly precise, rule-based feedback but are limited in scope (1). Combining them using Retrieval-Augmented Generation (RAG) allows the LLM to ground its natural language feedback in deterministic, structured knowledge, significantly improving the accuracy and comprehensiveness of the review(1). Furthermore, starting reviews with functional checks and automated tests ensures the code compiles before the AI attempts to review logic (3).

**Example:**  
[Static Analyzer Output]: 
Line 42: Potential null pointer dereference.
[Code Diff]: 
+ return user.getAddress().getZipCode();

Prompt for Hybrid Code Review
You are an expert code reviewer. 
Review the following code diff. 
Use the provided static analyzer warnings to guide your feedback.

**When to Apply:**  
Apply this guideline in continuous integration (CI) pipelines where static analysis tools are already integrated, and you want to provide human-readable, contextual explanations for the flagged warnings.
**When to Avoid:**  
Avoid this if the static analyzer produces excessive false positives (noise), as feeding these into the LLM might cause it to hallucinate or generate overly pedantic review comments.

---

### Guideline N: `[Title]`

(Repeat the same structure for each guideline.)

---

## 2. Raw Guidelines (Source Documents)

> **Note:** Include the original guidelines from each of the three sources before merging. This shows your curation process.

### 2.1 Guidelines from Literature Readings

**Readings Assigned:**  
- 1.  Taufiqul Islam Khan, Shaowei Wang, Haoxiang Zhang, and Tse-Hsun Chen. (2026). A Survey of Code Review Benchmarks and Evaluation Practices in Pre-LLM and LLM Era. ACM. 
- 2. Imen Jaoua, Oussama Ben Sghaier, and Houari Sahraoui. "Combining Large Language Models with Static Analyzers for Code Review Generation." (2025).
- 3. Jiwon Moon, Yerin Hwang, Dongryeol Lee, Taegwan Kang, Yongil Kim, and Kyomin Jung. "Don’t Judge Code by Its Cover: Exploring Biases in LLM Judges for Code Evaluation." (2025).
- 4. Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).

**Extracted Guidelines:**  
For each relevant guideline from readings:

**Guideline 2.1.1: Integrate Static Analysis with LLMs**  
**Source:** Imen Jaoua, Oussama Ben Sghaier, and Houari Sahraoui. "Combining Large Language Models with Static Analyzers for Code Review Generation." (2025).
**Description:** Combine knowledge-based systems (KBS) like static code analyzers with learning-based systems (LBS) like LLMs by injecting the analyzer's output directly into the LLM's prompt.
**Reasoning:** Combine Knowledge-Based Systems (KBS), such as static code analyzers, with Learning-Based Systems (LBS), such as LLMs. Dynamically retrieve the outputs of static analyzers (e.g., Checkstyle or PMD) and inject them into the LLM's prompt using a Retrieval-Augmented Generation (RAG) approach.
**Example:** Provide a prompt structured as: ### Static code analyzer output: {static_analyzer_output} ### Code difference: {code_diff} to guide the LLM to output a robust review.  

**Guideline 2.1.2: Mitigate "Self-Declared Correctness" Bias in AI Judges**  
**Source:** Don’t Judge Code by Its Cover- Exploring Biases in LLM Judges for
**Description:** Scrub or rigorously review code submissions for comments where the author explicitly claims the code is correct or optimized before passing it to an LLM evaluator.
**Reasoning:** LLMs exhibit a strong positive bias toward "self-declared correctness" and "authority cues," often judging functionally incorrect code as correct simply because a comment claims it is.
**Example:** An LLM might approve a buggy algorithm if the snippet begins with # Correct implementation or // Optimized by expert

**Guideline 2.1.3: Prevent Misleading Task Descriptions**  
**Source:** Don’t Judge Code by Its Cover- Exploring Biases in LLM Judges for
**Description:** Ensure that the task description provided to the LLM for evaluation is highly precise and free of irrelevant or misleading information
**Reasoning:** Misleading task descriptions act as a severe negative bias, strongly impairing the LLM's evaluative accuracy and causing it to falsely penalize functionally and architecturally correct code.
**Example:** A description that unnecessarily mentions arrays when only single integers are processed can confuse the LLM into rejecting a valid implementation

**Guideline 2.1.4: Utilize Structured Prompting**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Giving the LLMs a detailed, structured prompt that clearly defines the task, the evaluation criteria, the scoring scale, the required output format, and instructing the LLM to follow specific steps to evaluate code proved to be more reliable than simple and direct prompts. 
**Reasoning:** Simple, direct prompts yield unreliable judgments; structured steps explicitly guiding the LLM through analytical reasoning significantly improve the model's accuracy
**Example:** Using the ICE-Score approach, which instructs the LLM to follow a numbered list of steps to evaluate code against specific criteria like readability and correctness before outputting a verdict

**Guideline 2.1.5: Adopt Multi-Perspective Evaluation Personas**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Instruct the LLM to evaluate subjective artifacts (like code summaries or documentation) from multiple professional viewpoints, such as a code reviewer, the original author, or a system analyst.
**Reasoning:** Code readability and summary usefulness are subjective; aggregating perspectives helps the LLM align more closely with human consensus
**Example:** Using the CODERPE framework to generate separate viewpoints from the perspective of a code reviewer, author, or system analyst.

**Guideline 2.1.6: Weight Critical Facts Over Trivial Facts**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Explicitly instruct the LLM to categorize its findings into "Critical Facts," "Supporting Facts," and "Trivial Facts" to establish a weighting system
**Reasoning:** LLMs frequently overemphasize minor, trivial details in code or documentation, penalizing valid code for minor omissions; establishing weights prevents this misalignment.
**Example:** no explicit example provided. 
-> Agents could be prompted to ignore "Trivial Facts" like slightly unoptimized variable declarations if the "Critical Fact" of the business logic is entirely correct

**Guideline 2.1.7: Transition to Dynamic Execution Validation**  
**Source:** Taufiqul Islam Khan, Shaowei Wang, Haoxiang Zhang, and Tse-Hsun Chen. (2026). A Survey of Code Review Benchmarks and Evaluation Practices in Pre-LLM and LLM Era. ACM. 
**Description:** Do not rely solely on static LLM text evaluations; integrate automated runtime environments (e.g., Docker sandboxes) to compile and test LLM-proposed revisions.
**Reasoning:** LLMs often suggest fixes that appear grammatically perfect and pass text-matching metrics but introduce logical deadlocks or fail to compile in reality
**Example:** Automatically attempting to build a project with an LLM's suggested code revision to verify if it breaks existing functionality before presenting it to a human reviewer.

**Guideline 2.1.8: Enforce Human-in-the-Loop, especially for Low-Confidence Judgements**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Have LLM agents automatically flag nuanced, architectural, or high-stakes code changes for manual human review.
**Reasoning:** While LLMs excel at high-volume routine checks (e.g., style formatting), they struggle with complex, subjective evaluations; flagging low-confidence items optimizes expert human time.
**Example:** An automated review agent auto-approves a typo fix in a comment but pauses the pipeline and assigns a senior developer when it detects an uncertain change to the database schema.

**Guideline 2.1.9: Utilize agent based frameworks where the agent acts as an orchestrator**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Building on the initial success of tool-augmented agents, a significant opportunity lies in creating frameworks where the LLM judge acts as an orchestrator, intelligently leveraging a wider array of external SE tools to form its judgments. This practice is still in its early stages and not yet widespread.
**Reasoning:** agent-based could be used to create an evaluation pipeline and incorporate formal verification frameworks, model checkers, and performance profilers to assess code efficiency, including execution time and memory usage.
**Example:** pioneering work like CodeVisionary has already integrated foundational tools like static linters and execution environments.

**Guideline 2.1.10: Maintain the Original Context of the PR**  
**Source:** Automated Code Review In Practice.pdf
**Description:** Ensure that automated reviews do not suggest changes that alter the original intent or context of the pull request.
**Reasoning:** Applying out-of-scope or irrelevant suggestions without careful consideration can introduce severe bugs or feature creep.
**Example:** Rejecting an AI suggestion to refactor an entire database schema when the PR was simply meant to update a UI button color.

**Guideline 2.1.11: Use AI Primarily for Quality and Standard Enforcement**  
**Source:** Automated Code Review In Practice.pdf
**Description:** Leverage LLM tools primarily for detecting quality problems and maintaining coding standards, rather than complex architectural judgments.
**Reasoning:** Developers perceive automated code review tools as highly beneficial for these specific tasks, whereas they distrust AI for high-level logic.
**Example:** Using the AI to automatically flag missing docstrings or hardcoded credentials.

**Guideline 2.1.12: Address Variable Renaming Bias**  
**Source:** 3. Jiwon Moon, Yerin Hwang, Dongryeol Lee, Taegwan Kang, Yongil Kim, and Kyomin Jung. "Don’t Judge Code by Its Cover: Exploring Biases in LLM Judges for Code Evaluation." (2025)
**Description:** Standardize variable names or ensure the LLM judge is robust to stylistically different but functionally equivalent naming conventions.
**Reasoning:** Evaluators should remain robust to surface-level stylistic variations that do not affect underlying correctness.
**Example:** Ensuring the LLM does not fail a code snipplet simply because it uses num_list instead of array_x.

**Guideline 2.1.13: Expand Evaluation Beyond Functional Correctness**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:**  Prompt LLM judges to assess non-functional properties like readability, stylistic consistency, and fault tolerance.
**Reasoning:** Code quality encompasses more than just functional output; maintainability and edge-case handling are equally important for long-term health.
**Example:** Asking the LLM to evaluate how code manages unexpected exceptions and whether it adheres to specific formatting guidelines.

**Guideline 2.1.14: Use pseudocode to perform high level reviews.**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Convert code into pseudocode, then recursively decomposes the pseudocode to assess the algorithm.  
**Reasoning:** This allows the LLM judge to assess the core algorithm without being confused by complex, language-specific syntax.
**Example:** MCTS-Judge reframes evaluation as a search problem, where the goal is to find the most reliable reasoning path. It uses Monte Carlo Tree Search to explore a tree of possible reasoning trajectories, where each path represents a unique sequence of evaluation sub-tasks (e.g., analyzing logic, then checking functionality).

**Guideline 2.1.15: Use Advanced Prompting for Commit Messages**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Combine Chain-of-Thought reasoning and few-shot examples when asking an LLM to evaluate commit message quality.
**Reasoning:** Good commit messages must explain both "what" a change does and "why" it was made; advanced prompting helps the LLM distinguish between superficial summaries and deeply informative messages. This also overcomes the problem where multiple, lexically different commit messages can be equally valid for a single code change.
**Example:** Providing the LLM with internal documentation on commit messages, also three examples of good vs. bad commit messages before asking it to evaluate a new one.

**Guideline 2.1.16: Use LLM-as-a-Judge agents in meta-evaluation roles**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge" for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Instead of making direct and high-stakes vulnerability judgments, as explored in prior studies, LLM-as-a-Judge are increasingly employed in meta-evaluation roles. 
**Reasoning:** LLMs serve less as ultimate arbiters of security and more as scalable reviewers that enhance the reliability and interpretability of automated vulnerability analysis.
**Example:** recent work demonstrates that LLMs can assess whether vulnerability explanations are logically consistent, sufficiently detailed, and clearly articulated. 

**Guideline 2.1.17: Use LLM-as-a-Judge agents in meta-evaluation roles**  
**Source:** Junda He, Jieke Shi, Terry Yue Zhuo, Christoph Treude, Jiamou Sun, Zhenchang Xing, Xiaoning Du, and David Lo. "LLM-as-a-Judge" for Software Engineering: Literature Review, Vision, and the Road Ahead." (2025).
**Description:** Design the LLM judge as an orchestrator that interacts with external tools like performance profilers and formal verification frameworks.
**Reasoning:** Relying exclusively on internal model knowledge is insufficient; runtime, linting, and visual information are crucial for comprehensive evaluation.
**Example:** The LLM queries a performance profiler to assess the memory efficiency of a new sorting algorithm before writing its review.


---

### 2.2 Guidelines from Grey Literature / Practitioner Sources

**Sources Explored:**  
- `[Blog post 1]`  
- `[Documentation 1]`  
- `[Tool guide 1]`  
- `[Community discussion 1]`

**Extracted Guidelines:**  
**Guideline 2.2.1: Perform Functional Checks First**  
**Source:** Review AI-generated code - GitHub Docs 
**Description:** Ensure code compiles and all automated tests and static analysis tools (e.g., CodeQL, Dependabot) pass before manually reviewing AI-generated code.
**Reasoning:** Automated tools provide an objective baseline and catch simple erros more efficiently than human or artificial cognitive effort.
**Example:** 
What functional tests to validate this code change do not exist or are missing?
What functional tests to validate this code change do not exist or are missing?

**Guideline 2.2.2: Verify context and intent** 
**Source:** Review AI-generated code - GitHub Docs 
**Description:** Check that the AI-generated code fits the purpose and architecture of your project.
Ask yourself: “Does this code solve the right problem? Does it follow our conventions?”
Use your README, docs, and recent pull requests as a starting point for context for AI. Tell AI what sources to trust, what not to use, and give it good examples to work with.
Try Synthesizing research to see how Copilot uses documentation and research to inform code generation.
When asking AI to perform research and planning tasks, consider distilling the AI output into structured artifacts to then become context for future AI tasks such as code generation.
**Reasoning:** Review the AI output to check if the output aligns with your requirements and design patterns.
**Example Prompts**
How does this refactored code section align with our project architecture?
What similar features or established design patterns did you identify and model your code after?
When examining this code, what assumptions about business logic, design preferences, or user behaviors have been made?
What are the potential issues or limitations with this approach?

**Guideline 2.2.3: Assess code quality**  
**Source:** Review AI-generated code - GitHub Docs 
**Description:** Look for readability, maintainability, and clear naming.
Avoid accepting code that is hard to follow or would take longer to refactor than to rewrite.
Prefer code that is well-documented and includes clear comments.
**Reasoning:** Code should adhere to with human and organizational standards. 
**Example Prompts:** 
What are some readability and maintainability issues in this code?
How can this code be improved for clarity and simplicity? Suggest an alternative structure or variable names to enhance clarity.
How could this code be broken down into smaller, testable units?

**Guideline 2.2.4: Scrutinize dependencies**  
**Source:** Review AI-generated code - GitHub Docs 
**Description:** Be vigilant with new packages and libraries.
Check if suggested dependencies exist and are actively maintained. Consider the origins and contributors of new dependencies to ensure they come from reputable, non-competing sources.
Review licensing. Avoid introducing code or dependencies that are incompatible with your project’s license (for example, AGPL-3.0 in a MIT licensed project, or dependencies with no declared license).
Creating templates demonstrates how Copilot can assist with dependency setup, however it is good practice to always verify suggested packages yourself.
Use GitHub Copilot code referencing to review matches with publicly available code.
**Reasoning:** LLMs are suspectible to adding hallucinated or suspicious packages (such as packages that don't actually exist), or slopsquatting (a theoretical attack on LLMs using fake or malicious packages).
**Example Prompts:** 
Analyze the attached package.json file and list all dependencies with their respective licenses.
Are each of the dependencies listed in this package.json file actively maintained (that is, not archived and have recent maintainer activity)?

**Guideline 2.2.5: Spot AI-specific pitfalls**  
**Source:** Review AI-generated code - GitHub Docs 
**Description:** Look for hallucinated APIs, ignored constraints, or incorrect logic.
Watch for tests that are deleted or skipped, instead of fixed.
Be skeptical of code that “looks right” but doesn’t match your intent.
**Reasoning:** AI tools can make unique mistakes.
**Example Prompts:** 
What was the reasoning behind the code change to delete the failing test? Suggest some alternatives that would fix the test instead of deleting it.
What potential complexities, edge cases, or scenarios are there that this code might not handle correctly?
What specific technical questions does this code raise that require human judgment or domain expertise to evaluate properly?

**Guideline 2.2.6: Use collaborative reviews**  
**Source:** Review AI-generated code - GitHub Docs 
**Description:** Ask teammates to review complex or sensitive changes.
Use checklists to ensure all key review points (functionality, security, maintainability) are covered.
Share successful prompts and patterns for AI use across your team.
**Reasoning:** Pairing and team input helps catch subtle issues.
**Examples:** 
Create templates to streamline your workflow and ensure consistency across your projects.
create diagrams to better understand your data and communicate insights.
create tables to organize information and present it clearly.
synthesize research findings and insights from multiple sources into a cohesive summary.
extract key information from issues and discussions.

**Guideline 2.2.7: Automate what you can and keep improving your workflow**  
**Source:** Review AI-generated code - GitHub Docs 
**Description:** Set up CI checks for style, linting, and security.
Use Dependabot for dependency updates and alerts.
Apply CodeQL or similar scanners for static analysis.
Document your best practices for reviewing AI-generated code.
Encourage “AI champions” on your team to share tips and workflows.
Update your onboarding and contribution guides to include your AI review techniques and resources. Use a CONTRIBUTING.md file in your repository to document your expectations for AI-generated source code
**Reasoning:** Let tools handle the repetitive work. Embracing new AI tools and techniques can make your workflow even more effective.
**Example:** build a self-reviewing agent that evaluates draft pull requests against your standards, checking for accuracy, appropriate tone, and business logic before requesting human review.

**Guideline 2.2.8: Use REVIEW.md for Custom Review Rules**  
**Source:** Code Review - Claude Code Docs 
**Description:** Create a specific REVIEW.md file in the repository to dictate how the AI agent should review code, including severity calibration and reporting format. Keep the REVIEW.md file focused. 
**Reasoning:** This overrides generic agent behavior, injecting review-only instructions directly into the pipeline with the highest priority.
**Example:** 
- Review instructions
- What Important means here
Reserve Important for findings that would break behavior, leak data,
or block a rollback: incorrect logic, unscoped database queries, PII
in logs or error messages, and migrations that aren't backward
compatible. Style, naming, and refactoring suggestions are Nit at
most.
- Cap the nits
Report at most five Nits per review. If you found more, say "plus N
similar items" in the summary instead of posting them inline. If
everything you found is a Nit, lead the summary with "No blocking
issues."
- Do not report
Anything CI already enforces: lint, formatting, type errors
Generated files under `src/gen/` and any `*.lock` file
Test-only code that intentionally violates production rules
- Always check
New API routes have an integration test
Log lines don't include email addresses, user IDs, or request bodies
Database queries are scoped to the caller's tenant

**Guideline 2.2.9: Separate General Context from Review Instructions**  
**Source:** Code Review - Claude Code Docs 
**Description:** Keep general project context in AGENT.md (or a similarly named general purpose .md file) and strict review rules in REVIEW.md.
**Reasoning:** Length has a cost; a long instructional file dilutes the rules that matter most.
**Example:** Putting coding style guidelines in AGENT.md, but placing instructions on "what triggers a blocking review" in REVIEW.md.

**Guideline 2.2.10: Monitor Code Review Spending and Usage**  
**Source:**  Code Review - Claude Code Docs 
**Description:** Use analytics dashboards to track auto-resolved comments, PRs reviewed, and weekly costs associated with the AI tool.
**Reasoning:** Helps organizations measure the ROI of the AI review tool and identify on which ares the technology is used more effectively.
**Example:** Critical for managing budget and tool adoption.

**Guideline 2.2.11: Configure Review Triggers and frequency**  
**Source:**  Code Review - Claude Code Docs 
**Description:** Configure when the AI review should be triggered (e.g., on every push, only on PRs) and how often it should run (e.g., daily, weekly).
**Reasoning:** Reviewing on every push runs the most reviews and costs the most. Manual mode is useful for high-traffic repos where you want to opt specific PRs into review, or to only start reviewing your PRs once they’re ready.
**Example:** 
Once after PR creation: review runs once when a PR is opened or marked ready for review
After every push: review runs on every push to the PR branch, catching new issues as the PR evolves and auto-resolving threads when you fix flagged issues
Manual: reviews start only when someone triggers a review.

**Guideline 2.2.12: Standardize the Summary Shape for Quick Triaging**  
**Source:**  Code Review - Claude Code Docs 
**Description:** Have the agent create summaries of the reviews. 
**Reasoning:** The author wants to know the shape of the work before the details.
**Example:** ask for the review body to open with a one-line tally such as 2 factual, 4 style, and to lead with “no factual issues” when that’s the case.

**Guideline 2.2.13: Standardize the Summary Shape for Quick Triaging**  
**Source:**  Code Review - Claude Code Docs 
**Description:** Have the agent create summaries of the reviews. 
**Reasoning:** The author wants to know the shape of the work before the details.
**Example:** ask for the review body to open with a one-line tally such as 2 factual, 4 style, and to lead with “no factual issues” when that’s the case.

**Guideline 2.2.14: Tune the Severity Levels**  
**Source:**  Code Review - Claude Code Docs 
**Description:** redefine what Important means for your repo. The default calibration targets production code; a docs repo, a config repo, or a prototype might want a much narrower definition. State explicitly which classes of finding are Important and which are Nit at most. You can also escalate in the other direction.
**Reasoning:** Tune the review agents to your and your teams needs. 
**Example:** Treat any AGENT.md violation as Important rather than the default nit. 

**Guideline 2.2.15: Leverage Local Reviews for Uncommitted Changes**  
**Source:** Using GitHub Copilot code review - GitHub Docs
**Description:** Utilize IDE integrations (such as Visual Studio Code, JetBrains, or Xcode) to request Copilot code reviews on highlighted code snippets or uncommitted/unstaged changes before pushing to a branch.
**Reasoning:** Reviewing code locally helps catch bugs, style violations, and potential issues earlier in the development lifecycle, reducing the volume of noisy commits and back-and-forth review cycles during the actual pull request phase.
**Example:** Tn Visual Studio Code, navigating to the Source Control view and clicking the "Copilot Code Review - Uncommitted Changes" button to get inline problem reports on local edits before running a git commit command.
---

### 2.3 Guidelines from LLM Experimentation

**Models Used:**  
- `[e.g., GPT-5.2, Claude 4.5 Sonnet, DeepSeek Coder, GitHub Copilot (Ask vs Agent etc.)]`

**Prompts Used:**  
- `[Prompt 1]`  
- `[Prompt 2]`  
- `[Prompt 3]`

**Extracted Guidelines:**  
Format same as above.

---

## 3. References

**Literature References:**  
[1] `[Full citation]`  
[2] `[Full citation]`  

**Grey Literature References:**  
[1] `[Blog post title and URL]`  
[2] `[Documentation title and URL]`  

**LLM Prompts (Full Log):**  
See Appendix A or provide a link to a separate file with full prompt-response logs.

---

## 4. Appendix (Optional)

- **A. Full Prompt Logs:** Link to detailed LLM interaction logs
- **B. Decision Matrix:** How you decided which guidelines to merge
- **C. Conflicts Resolved:** Examples of contradictory guidelines and how you resolved them

---

## Instructions for Use

1. **Replace all `[...]` placeholders** with your team's specific content
2. **Number guidelines consecutively** (Guideline 1, Guideline 2, etc.)
3. **Cite sources properly** using academic citation style (e.g., APA, ACM)
4. **Include concrete examples** - code or textual snippets (depending on SE task) are highly recommended
5. **Be specific about applicability** - when does this guideline work vs. fail?
6. **Submit as `Topic-XX_Guidelines.md`** where `XX` is your topic number

---

## Grading Criteria (for your reference)

- ✅ **Clarity:** Guidelines are specific and actionable
- ✅ **Evidence:** Each guideline is supported by reasoning and examples
- ✅ **Curation:** Shows thoughtful merging of multiple sources
- ✅ **Practicality:** Examples are relevant to real development tasks
- ✅ **Transparency:** Raw guidelines from all three sources are included

---

*Template version: 1.0 | Last updated: 24 February 2026*
