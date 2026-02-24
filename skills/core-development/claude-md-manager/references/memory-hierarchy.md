# Memory Hierarchy for CLAUDE.md Writers

Where an instruction lives determines who sees it and when it loads. This reference covers the tiers a CLAUDE.md writer directly interacts with. For the complete system, see [Anthropic's memory docs](https://code.claude.com/docs/en/memory).

## Where to Put an Instruction

| Instruction applies to... | Place it in... |
|---------------------------|----------------|
| All developers on this project | Project memory (`./CLAUDE.md`) |
| Only when editing specific file paths | Project rules (`.claude/rules/`) |
| All sessions across all projects | User memory (`~/.claude/CLAUDE.md`) |
| Personal project preferences (not committed) | `CLAUDE.local.md` |
| Deterministic enforcement (not advisory) | Hooks (`.claude/hooks/`), not memory |
| Domain knowledge relevant only sometimes | Skills (`.claude/skills/`) |
| Agent-specific behavior | Agent definitions (`.claude/agents/`) |

All memory tiers are **advisory** — the agent reads them as guidance but may deviate under context pressure. For deterministic enforcement, use hooks.

## .claude/rules/ — Path-Scoped Instructions

The `.claude/rules/` directory holds modular, conditionally-loaded instructions as an alternative to a monolithic CLAUDE.md. Each `.md` file supports optional YAML frontmatter with `paths:` glob patterns.

### Frontmatter Format

```yaml
---
paths:
  - "src/api/**/*.ts"
  - "src/routes/**"
---

# API Development Rules
- Return consistent error shapes: `{ error: string, code: number }`
- Validate all inputs with Zod schemas
```

Rules without a `paths:` field load unconditionally (same priority as `.claude/CLAUDE.md`).

### Glob Patterns

Standard glob syntax with brace expansion:
- `**/*.ts` — all TypeScript files
- `src/**/*` — everything under src/
- `src/**/*.{ts,tsx}` — TypeScript and TSX files
- `tests/**` — everything under tests/

### Organization

```
.claude/rules/
├── code-style.md        # No paths: → loads always
├── api.md               # paths: ["src/api/**"] → loads conditionally
├── testing.md            # paths: ["tests/**", "**/*.test.*"]
├── frontend/
│   └── react.md          # paths: ["src/components/**"]
└── backend/
    └── database.md       # paths: ["src/db/**", "migrations/**"]
```

Subdirectories are discovered recursively. Symlinks are supported for sharing rules across projects.

### User-Level Rules

Personal rules at `~/.claude/rules/` load before project rules. Project rules take higher priority.

## CLAUDE.local.md

A gitignored personal override file placed alongside `CLAUDE.md`. Discovered automatically when present.

**Use cases:**
- Personal tool preferences (editor, terminal, aliases)
- Local environment paths and sandbox URLs
- Preferred test data or fixtures
- Workflow overrides that differ from team defaults
