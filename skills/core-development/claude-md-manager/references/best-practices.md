# CLAUDE.md Best Practices Deep Dive

Comprehensive patterns for creating effective CLAUDE.md files based on research from Anthropic, HumanLayer, Abnormal Security, and production implementations across enterprise and open-source codebases.

## Table of Contents
- [Context Window Economics](#context-window-economics)
- [The WHAT/WHY/HOW Framework](#the-whatwhyhow-framework)
- [Progressive Disclosure Mastery](#progressive-disclosure-mastery)
- [File Import Patterns](#file-import-patterns)
- [Measuring Effectiveness](#measuring-effectiveness)
- [Maintenance Strategies](#maintenance-strategies)
- [Advanced Patterns](#advanced-patterns)

## Context Window Economics

### Why Every Line Matters

Claude Code's system prompt contains ~50 baseline instructions. Frontier LLMs can reliably follow 150-200 instructions. This leaves ~100-150 instruction slots for CLAUDE.md content and conversation.

**Token cost calculation:**
- Average CLAUDE.md line: ~15 tokens
- 100-line file: ~1,500 tokens
- 300-line file: ~4,500 tokens
- Conversation history: 2,000-10,000+ tokens
- System prompt: ~2,000 tokens

**Impact of bloat:**
- Instructions compete for attention
- Irrelevant context degrades all instruction-following
- Claude explicitly ignores instructions marked "may or may not be relevant"

### Right-Sizing by Project Complexity

| Project Type | Target Lines | Pattern |
|-------------|--------------|---------|
| Simple script/CLI | 20-40 | Single CLAUDE.md |
| Standard app | 60-100 | CLAUDE.md + 1-2 imports |
| Complex monorepo | 60-80 + agent_docs/ | Progressive disclosure |
| Enterprise codebase | 40-60 + heavy imports | Hierarchical files |

## The WHAT/WHY/HOW Framework

### WHAT: Technical Reality

Document only what Claude cannot infer from the code itself:

**Include:**
- Non-obvious tech stack choices (e.g., "Next.js App Router, NOT Pages")
- Architecture boundaries (service ownership, data flow)
- Non-standard file locations
- Build tool specifics (bun vs npm vs pnpm)

**Exclude:**
- Obvious framework usage (if there's a React component, Claude knows it's React)
- Standard directory structures
- Common patterns visible in code

### WHY: Context and Purpose

Explain the reasoning behind non-obvious decisions:

```markdown
## Why We Use Sessions Instead of JWT

Sessions (not JWT) because:
- SSR requires server-readable auth state
- No mobile clients planned
- Simpler revocation
```

### HOW: Practical Workflows

Focus on commands and procedures Claude must execute correctly:

```markdown
## Commands
- Dev: `pnpm dev` (NOT npm - pnpm workspaces required)
- Test: `pnpm test --coverage` (required >80%)
- Deploy: `pnpm deploy:staging` then `pnpm deploy:prod`

## Workflow
- Always pull before pushing
- Squash before merge to main
- Run tests locally before PR
```

## Progressive Disclosure Mastery

### When to Split

**Split when:**
- CLAUDE.md exceeds 100 lines
- The project has 3+ distinct workflow areas
- Team members work on isolated areas
- Instructions are highly task-specific

**Keep unified when:**
- File is under 60 lines
- All developers need all context
- Instructions are universally applicable

### Directory Structure Patterns

**By workflow stage:**
```
agent_docs/
├── setup.md          # Initial project setup
├── development.md    # Day-to-day development
├── testing.md        # Test writing and running
├── deployment.md     # Release process
└── troubleshooting.md # Common issues
```

**By domain:**
```
agent_docs/
├── frontend.md       # React/UI concerns
├── backend.md        # API/server concerns
├── database.md       # Schema and queries
├── infra.md          # DevOps/cloud
└── security.md       # Auth and access
```

**By team:**
```
agent_docs/
├── onboarding.md     # New team members
├── code-review.md    # PR standards
├── on-call.md        # Incident response
└── architecture.md   # Design decisions
```

### Reference Syntax in CLAUDE.md

```markdown
# Task-Specific Guides
- Setting up dev environment: @agent_docs/setup.md
- Writing tests: @agent_docs/testing.md
- Deploying changes: @agent_docs/deployment.md

Claude reads these when the task requires it.
```

### Beyond agent_docs/: Rules, Skills, and Agents

The `agent_docs/` pattern is not the only progressive disclosure mechanism. Three additional systems complement it:

**`.claude/rules/` — Path-Scoped Instructions**

The `.claude/rules/` directory holds modular instructions that load conditionally based on which files are in context. Each `.md` file supports YAML frontmatter with `paths:` glob patterns:

```yaml
---
paths:
  - "src/api/**/*.ts"
  - "src/routes/**"
---
# API Conventions
- Return consistent error shapes: `{ error: string, code: number }`
- Validate all inputs with Zod schemas
```

Rules without a `paths:` field load unconditionally. Use rules instead of CLAUDE.md for instructions that apply only to specific file paths. See `references/memory-hierarchy.md` for the full rules reference.

**Skills — Domain Knowledge Overflow**

CLAUDE.md loads every session, consuming context on every task. For domain knowledge that is only sometimes relevant, use skills (`.claude/skills/`) instead. Skills load on demand with zero context cost when inactive — only the skill name and description (~100 tokens) are present until triggered.

**Custom Subagents (`.claude/agents/`)**

Agent-specific instructions belong in agent definition files (`.claude/agents/*.md`), not in CLAUDE.md. Agent files support YAML frontmatter with tool restrictions and model selection. Reserve CLAUDE.md for project-wide instructions that apply regardless of which agent is active.

## File Import Patterns

### Basic Imports

```markdown
# Import sibling files
@README.md
@CONTRIBUTING.md

# Import from subdirectories
@docs/api.md
@.github/PULL_REQUEST_TEMPLATE.md

# Import personal preferences (not committed)
@~/.claude/work-preferences.md
```

### Advanced Import Patterns

**Conditional documentation:**
```markdown
# When working on auth, see @docs/auth-architecture.md
# When working on payments, see @docs/payment-flow.md
# When debugging, see @docs/troubleshooting.md
```

**Team vs personal split:**
```markdown
# Team conventions (in repo)
@docs/conventions.md

# Personal preferences (in ~/.claude/)
# Add your own: @~/.claude/my-project-prefs.md
```

### Pitch Files, Not Just Reference Them

A bare `@path/to/file` import often gets ignored — the agent has no reason to read it unless the current task clearly requires it. Explain **when** and **why** to consult each import.

```markdown
# Bad — bare references without context
@agent_docs/testing.md
@agent_docs/deployment.md
@agent_docs/auth-architecture.md

# Good — pitched imports that explain relevance
- @agent_docs/testing.md — test conventions, coverage thresholds, and E2E patterns. Read when writing or modifying tests.
- @agent_docs/deployment.md — Railway deploy checklist and rollback procedures. Read before any production deploy.
- @agent_docs/auth-architecture.md — session-based auth flow and token lifecycle. Read when debugging auth issues or modifying login.
```

This pattern is especially valuable for large `agent_docs/` directories where the file names alone do not convey enough context. Even a short clause after the path ("Read when...") significantly increases the probability that the agent consults the right file at the right time.

### Imported File Heading Levels

Start imported files at `##` (not `#`) to avoid heading hierarchy conflicts with the main CLAUDE.md. The root CLAUDE.md owns the `#` level; imported files are subsections and should begin one level down. This prevents the table of contents from flattening into a confusing list of competing top-level headings.

## Measuring Effectiveness

### Signs of Effective CLAUDE.md

- Claude rarely asks for clarification on conventions
- Code reviews show consistent style adherence
- The same instructions stop being repeated across sessions
- Claude catches violations proactively
- New workflows execute correctly on first attempt

### Red Flags

- Claude ignores documented conventions (file may be too long, rule is getting lost)
- `#` instructions are added mid-conversation frequently
- Claude asks questions already answered in the file (phrasing may be ambiguous)
- Generated code does not match project style
- Build/test commands fail consistently

### Iteration Using #

Press `#` during conversations to append instructions being repeated:
1. Note instructions given more than twice
2. Add them via `#` (appends to CLAUDE.md)
3. Review and organize quarterly
4. Move task-specific items to agent_docs/

## Maintenance Strategies

### Quarterly Review Checklist

- [ ] Remove outdated tech stack references
- [ ] Update changed commands
- [ ] Verify file references still exist
- [ ] Consolidate repeated patterns
- [ ] Move grown sections to agent_docs/
- [ ] Test all documented commands
- [ ] Remove instructions Claude now follows automatically

### Trigger-Based Updates

Update CLAUDE.md when:
- Major dependency upgrade
- Architecture refactor
- Team convention change
- New developer joins (test their experience)
- Claude repeatedly makes same mistake

### Version Control Best Practices

```bash
# Track as code
git add CLAUDE.md agent_docs/
git commit -m "docs: update CLAUDE.md for React 19 upgrade"

# Review in PRs like code
# Include CLAUDE.md in PR templates
```

## Advanced Patterns

### Context-Aware Instructions

```markdown
# When modifying database schema
1. Create migration: `pnpm db:migrate:create`
2. Apply locally: `pnpm db:migrate:dev`
3. Update types: `pnpm db:generate`
4. Test with: `pnpm test:db`

# When adding API endpoints
1. Add route in src/routes/
2. Add types in src/types/api.ts
3. Add tests in tests/api/
4. Update OpenAPI spec if public
```

### Negative Instructions: Pair with Alternatives

Bare prohibitions ("never do X") cause the agent to get stuck when it encounters the prohibited situation with no fallback path. Every negative instruction should end with the preferred alternative.

```markdown
# Bad — agent has no fallback when it needs to do the prohibited thing
- Never modify migration files
- Do not create utility files
- Never use console.log

# Good — every prohibition includes the alternative
- Never modify migration files after merge to main — create a new migration instead
- Do not create new utility files without first checking /lib for existing ones
- Never use console.log — use the project logger at src/lib/logger.ts
```

Rule of thumb: every "never X" ends with "— do Y instead."

### Advisory vs Deterministic: CLAUDE.md vs Hooks

CLAUDE.md instructions are **advisory** — the agent reads them as guidance but may deviate under context pressure. Hooks (`.claude/hooks/`) are **deterministic** — they execute automatically regardless of agent judgment.

| Behavior Type | Place In | Reason |
|---------------|----------|--------|
| Linting, formatting, secret scanning | Hooks | Requires guaranteed execution |
| Pre-commit checks, post-push notifications | Hooks | Side effects that must happen |
| Architecture decisions, workflow preferences | CLAUDE.md | Guidance the agent should internalize |
| "When working on X, follow Y pattern" | CLAUDE.md | Context-dependent instructions |

If the agent repeatedly ignores a CLAUDE.md instruction, consider whether it should be a hook instead.

### Integration with Hooks

```markdown
# Pre-commit (automated, not in CLAUDE.md)
# See .claude/hooks/pre-commit for lint/format

# Post-implementation (Claude should do)
- Run type check: `pnpm typecheck`
- Update affected tests
- Check bundle size: `pnpm analyze`
```

### Emphasis Tuning

Use **bold markdown** and section headings to draw attention to critical instructions. Avoid ALL CAPS or stacking multiple emphasis markers — if everything is emphasized, nothing stands out.

- Bold a key term within a sentence: "Use `pnpm` (**not** npm) for all package operations"
- Use section headings to create visual hierarchy rather than inline capitalization
- Reserve emphasis for instructions that would cause real damage if ignored
- If emphasis is not working, the file may be too long — the instruction is getting lost in noise, not being under-emphasized

### CLAUDE.md as Tooling Forcing Function

If the CLAUDE.md section for an internal tool requires extensive explanation, the tool itself is too complex. Write a bash wrapper with a clear, intuitive API and document *that* instead. Keeping CLAUDE.md short forces tooling improvement.

### PR-Driven CLAUDE.md Evolution

When a PR changes project conventions, update CLAUDE.md in the same PR. Include CLAUDE.md in the PR review scope. This creates a feedback loop: real-world issues inform instructions, which prevent future issues.

Add to PR templates: "If this PR changes conventions or workflow, update CLAUDE.md accordingly."

### Team Synchronization

For teams, establish CLAUDE.md governance:
- Single owner for root CLAUDE.md
- PRs required for changes
- Document rationale for each instruction
- Regular team review of effectiveness

## Anti-Pattern Examples

### Too Verbose

```markdown
# BAD - 40 lines that could be 5
When you need to create a new React component, you should first
navigate to the src/components directory. Then create a new file
with the .tsx extension. The file name should be PascalCase...
[continues for 35 more lines]

# GOOD
## Components
- Location: src/components/{ComponentName}.tsx
- Style: Functional with hooks, no class components
- Tests: Required in __tests__/{ComponentName}.test.tsx
```

### Duplicating Code

```markdown
# BAD - copied code that will go stale
Here's our auth middleware:
\`\`\`typescript
export const authMiddleware = async (req, res, next) => {
  // 50 lines of code
}
\`\`\`

# GOOD - reference that stays current
Auth middleware: src/middleware/auth.ts:15-45
```

### Linting via LLM

```markdown
# BAD - waste of context and unreliable
Always ensure:
- 2 space indentation
- Trailing commas
- Single quotes
- Semicolons

# GOOD - use tools
# (No mention in CLAUDE.md - handled by .eslintrc and hooks)
```
