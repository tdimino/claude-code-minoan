# Skill Categories

Source: Thariq (Anthropic), "Lessons from Building Claude Code: How We Use Skills" (March 2026). These 9 categories represent how Anthropic internally classifies hundreds of skills in active use.

## The 9 Categories

### 1. Library & API Reference

Skills that explain how to correctly use a library, CLI, or SDK. These often include a folder of reference code snippets and a list of gotchas for Claude to avoid.

**When to build**: Claude consistently misuses an API, forgets options, or produces outdated patterns for a library.

**Structural pattern**: Reference/Guidelines -- heavy on `references/` with code examples, schemas, and gotchas.

**Eval strategy**: Compare output correctness with and without skill. Test on real API calls or known-correct code patterns.

**Examples**: `shadcn`, `react-best-practices`, `claude-agent-sdk`, `dspy-ruby`

---

### 2. Product Verification

Skills that test or verify code is working. Often paired with an external tool like Playwright, tmux, or headless browsers. Thariq: "It can be worth having an engineer spend a week just making your verification skills excellent."

**When to build**: You need Claude to prove its output is correct, not just claim it.

**Structural pattern**: Workflow-Based -- sequential verification steps with `scripts/` for programmatic assertions.

**Techniques**:
- Have Claude record a video of its output so you can see exactly what it tested
- Enforce programmatic assertions on state at each step
- Include a variety of scripts in the skill for different verification scenarios

**Eval strategy**: Measure false positive/negative rates on known-good and known-bad code.

**Examples**: `minoan-frontend-design` eval infrastructure, signup-flow-driver, checkout-verifier

---

### 3. Data Fetching & Analysis

Skills that connect to data and monitoring stacks. Include helper libraries with credentials, specific dashboard IDs, and instructions on common workflows.

**When to build**: Claude needs to query internal databases, dashboards, or APIs with specific schemas.

**Structural pattern**: Task-Based -- multiple query types with `scripts/` for data access functions.

**Eval strategy**: Verify query correctness against known results. Test with sample datasets.

**Examples**: `openrouter-usage`, `exa-search`, `claude-usage`, funnel-query, grafana

---

### 4. Code Scaffolding & Templates

Skills that generate framework boilerplate for specific functions in the codebase. Especially useful when scaffolding has natural language requirements that can't be purely covered by code.

**When to build**: You repeatedly create the same project structure, file layouts, or boilerplate.

**Structural pattern**: Capabilities-Based -- `assets/` with boilerplate templates, `scripts/` for scaffolding automation.

**Eval strategy**: Compare scaffold completeness and correctness against expected output structure.

**Examples**: `gemini-forge`, new-migration, create-app

---

### 5. Code Quality & Review

Skills that enforce code quality and help review code. Can include deterministic scripts or tools for maximum robustness. Consider running these automatically via hooks or inside a GitHub Action.

**When to build**: You have style rules, testing practices, or review standards Claude doesn't follow by default.

**Structural pattern**: Reference/Guidelines with `scripts/` for automated checks.

**Techniques**:
- Spawn a fresh-eyes subagent to critique (adversarial-review pattern)
- Use session-scoped hooks for enforcement (see `advanced-patterns.md`)
- Combine deterministic checks with LLM-based review

**Eval strategy**: Measure detection rate on intentionally flawed code.

**Examples**: `stop-slop`, adversarial-review, code-style, testing-practices

---

### 6. CI/CD & Deployment

Skills that fetch, push, and deploy code. These may reference other skills to collect data.

**When to build**: Deployment involves multiple steps, environment-specific configuration, or safety checks.

**Structural pattern**: Workflow-Based with `scripts/` for deployment automation.

**Eval strategy**: Verify deployment success and rollback capability in a test environment.

**Examples**: babysit-pr (monitor -> retry flaky CI -> resolve conflicts -> auto-merge), deploy-service, cherry-pick-prod

---

### 7. Runbooks

Skills that take a symptom (Slack thread, alert, error signature), walk through a multi-tool investigation, and produce a structured report.

**When to build**: Oncall or debugging involves repeatable investigative patterns.

**Structural pattern**: Workflow-Based -- decision tree from symptom to diagnosis, `scripts/` for querying systems.

**Eval strategy**: Measure diagnostic accuracy on known-symptom scenarios with expected findings.

**Examples**: `worldwarwatcher-update`, service-debugging, oncall-runner, log-correlator

---

### 8. Business Process & Team Automation

Skills that automate repetitive workflows into one command. Usually fairly simple instructions but may have complicated dependencies on other skills or MCPs. Saving previous results in log files helps the model stay consistent and reflect on previous executions.

**When to build**: A workflow involves gathering data from multiple sources and formatting a standard output.

**Structural pattern**: Task-Based with persistence (see `advanced-patterns.md` on skill memory).

**Eval strategy**: Compare workflow consistency and output format across multiple runs.

**Examples**: `receipt-invoice-bundler`, standup-post, create-ticket, weekly-recap

---

### 9. Infrastructure Operations

Skills that perform routine maintenance and operational procedures -- some involving destructive actions that benefit from guardrails.

**When to build**: Engineers need to perform potentially dangerous operations that should follow strict procedures.

**Structural pattern**: Workflow-Based with session-scoped hooks for guardrails (see `advanced-patterns.md`).

**Eval strategy**: Verify guardrails activate on destructive operations. Test both happy path and abort scenarios.

**Examples**: `cloudflare`, resource-orphan cleanup, dependency-management, cost-investigation

---

## Category Confirmation Protocol

During Step 2 of the Skill Creation Process, present the 9 categories above and ask:

> "Based on what you've described, this sounds like a **[Category]** skill. Does that match your intent?"

**If the skill straddles two categories**, flag it:

> "This skill straddles [X] and [Y]. The best skills fit cleanly into one category. Can we narrow the scope, or is there a reason it needs to cover both?"

Straddling is a signal the skill may need to be split into two skills.

**If none fit**, the skill may represent a new category or may not be a skill at all (perhaps it's better handled by CLAUDE.md instructions or a hook).

## Category-to-Structure Mapping

Each category has a natural structural affinity:

| Category | Primary Pattern | Key Directories |
|----------|----------------|-----------------|
| Library & API Reference | Reference/Guidelines | `references/` heavy |
| Product Verification | Workflow-Based | `scripts/` heavy |
| Data Fetching & Analysis | Task-Based | `scripts/` + `references/` |
| Code Scaffolding & Templates | Capabilities-Based | `assets/` + `scripts/` |
| Code Quality & Review | Reference/Guidelines | `references/` + `scripts/` |
| CI/CD & Deployment | Workflow-Based | `scripts/` heavy |
| Runbooks | Workflow-Based | `scripts/` + `references/` |
| Business Process & Automation | Task-Based | `scripts/` + persistence |
| Infrastructure Operations | Workflow-Based | `scripts/` + hooks |

These are defaults, not constraints. A Library skill that also scaffolds might use Capabilities-Based structure. Match the structure to how the skill is actually used.
