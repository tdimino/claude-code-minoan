# CLAUDE.md Manager

The configuration skill. Teaches Claude how to create, audit, and maintain the CLAUDE.md files that define how Claude Code behaves in every project.

**Last updated:** 2026-02-21

**Reflects:** Claude Code memory system (Feb 2026), Anthropic's CLAUDE.md best practices, HumanLayer's production patterns, and progressive disclosure architecture for monorepos and large codebases.

---

## Why This Skill Exists

CLAUDE.md is Claude Code's project memory—the file that tells Claude what the project is, how it works, and what conventions matter. Every project has one (or should). The difference between a 300-line dump and a 60-line surgical file is the difference between Claude following instructions and Claude ignoring them under context pressure.

This skill encodes the craft: the WHAT/WHY/HOW framework for deciding what goes in, conciseness rules grounded in context window economics, progressive disclosure patterns for scaling to monorepos, file import syntax, anti-patterns to avoid, and OSGrep-powered validation to catch stale claims. It also includes templates for 7 project types and an automated project analyzer.

---

## Structure

```
claude-md-manager/
  SKILL.md                              # Creation and maintenance guide (247 lines)
  README.md                             # This file
  scripts/
    analyze_project.py                  # Automated project analysis → JSON report
  references/
    best-practices.md                   # Deep dive: context economics, patterns, anti-patterns
    templates.md                        # 7 ready-to-customize templates by project type
```

---

## What It Covers

### The WHAT/WHY/HOW Framework

Every CLAUDE.md answers three questions:

| Layer | Content | Example |
|-------|---------|---------|
| **WHAT** | Technical reality Claude can't infer from code | "Next.js App Router, NOT Pages" |
| **WHY** | Reasoning behind non-obvious decisions | "Sessions not JWT because SSR needs server-readable auth" |
| **HOW** | Commands and procedures that must be exact | "`pnpm dev` (NOT npm—pnpm workspaces required)" |

The key discipline: exclude anything Claude can infer by reading the code. If there's a React component, Claude knows it's React. If `package.json` has scripts, Claude can read them. Document the non-obvious.

### Context Window Economics

Claude Code's system prompt uses ~50 instruction slots. Frontier LLMs reliably follow 150–200. That leaves ~100–150 for your CLAUDE.md and conversation history combined. Every line competes.

| Target | Lines | When |
|--------|-------|------|
| Ideal | Under 60 | Simple apps, clear conventions |
| Good | Under 100 | Standard projects |
| Maximum | 300 | Refactor immediately if exceeded |

Average line: ~15 tokens. A 300-line file costs 4,500 tokens—context that degrades all instruction-following, not just its own.

### Progressive Disclosure

When CLAUDE.md grows past 100 lines, split into focused files that Claude loads only when relevant:

```
agent_docs/
├── building.md          # Build process details
├── testing.md           # Test conventions
├── code-conventions.md  # Style and patterns
├── architecture.md      # Design decisions
└── deployment.md        # Release process
```

Reference in CLAUDE.md with `@agent_docs/testing.md`—Claude reads these on demand, not at startup.

### File Import Syntax

CLAUDE.md supports `@path/to/file` imports:

| Syntax | Scope |
|--------|-------|
| `@README.md` | Project root |
| `@docs/guide.md` | Subdirectory |
| `@~/.claude/personal.md` | Personal preferences (not committed) |

Recursive to 5 levels. Not evaluated inside code blocks.

### Hierarchical Files for Monorepos

```
/CLAUDE.md              # Repo-wide conventions
/frontend/CLAUDE.md     # Frontend-specific
/backend/CLAUDE.md      # Backend-specific
/services/auth/CLAUDE.md # Service-specific
```

Each file is concise and scope-appropriate. Claude discovers nested CLAUDE.md files when editing files in subdirectories.

### OSGrep Validation

After creating or refreshing CLAUDE.md, validate claims against the actual codebase:

```bash
# Verify documented commands exist
osgrep "dev server startup configuration" -p $REPO -m 3

# Verify directory contents match documentation
osgrep "API route handlers" -p $REPO/src/routes -m 3

# Verify conventions match actual code
osgrep "error handling patterns" -p $REPO -m 5
```

Catches stale commands, incorrect paths, and conventions that have drifted from reality.

---

## Scripts

### `analyze_project.py` — Automated project analysis

```bash
python3 ~/.claude/skills/claude-md-manager/scripts/analyze_project.py /path/to/project
```

Examines the project directory and produces a JSON report with:
- **Package manager and runtime** detection (pnpm, bun, uv, cargo, etc.)
- **Tech stack** identification from lockfiles and config files
- **Directory structure** mapping
- **Available commands** from package.json / Makefile / pyproject.toml
- **Testing framework** detection

Use the output to jumpstart CLAUDE.md creation with verified facts rather than guesses.

---

## Templates

`references/templates.md` includes ready-to-customize templates for 7 project types:

| Template | Stack | Target Lines |
|----------|-------|-------------|
| Minimal | Any | Under 30 |
| Node.js/TypeScript | Express/Fastify/Hono | ~40 |
| Python | FastAPI/Django/Flask | ~40 |
| Ruby/Rails | Rails 7.x + Hotwire | ~35 |
| Go | stdlib/Chi/Gin/Echo | ~30 |
| Rust | Axum/Actix/Rocket | ~35 |
| React/Next.js | App Router + TypeScript | ~35 |
| Monorepo | Turborepo/pnpm workspaces | ~40 |

Each template follows the WHAT/WHY/HOW framework and stays well under the 100-line target.

---

## Anti-Patterns

Things that waste context or degrade instruction-following:

| Anti-Pattern | Why It's Bad | Alternative |
|-------------|-------------|-------------|
| Linting rules in CLAUDE.md | Unreliable, wastes tokens | Pre-commit hooks |
| Auto-generated CLAUDE.md (`/init`) | Suboptimal, generic | Manual craft |
| Exhaustive style guides | Claude learns from code patterns | Document only non-obvious conventions |
| Inline code snippets | Go stale immediately | `file:line` references |
| Secrets or credentials | Treated as public | Environment variables |
| Task-specific instructions in root | Bloats the always-loaded file | `agent_docs/` with `@import` |

---

## Audit Checklist

For quarterly CLAUDE.md review:

- [ ] Under 100 lines? Identify extraction candidates if not
- [ ] Using `file:line` refs instead of inline code?
- [ ] Task-specific docs externalized to `agent_docs/`?
- [ ] No linting enforcement (handled by hooks)?
- [ ] No credentials or secrets?
- [ ] No obvious/inferable instructions?
- [ ] All documented commands actually work?
- [ ] Architecture claims still accurate?
- [ ] OSGrep validation run?
- [ ] All `@import` file references still valid?

---

## Best Practices Reference

`references/best-practices.md` covers:
- Context window economics with token cost calculations
- Right-sizing by project complexity (script → monorepo → enterprise)
- Progressive disclosure mastery (when to split, directory patterns)
- File import patterns (basic, conditional, team vs personal)
- Measuring effectiveness (success indicators, red flags)
- Maintenance strategies (quarterly review, trigger-based updates)
- Advanced patterns (context-aware instructions, negative instructions, hook integration)

---

## Requirements

- Python 3.9+
- No external dependencies
- OSGrep recommended for validation (but not required)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)—curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/claude-md-manager ~/.claude/skills/
```
