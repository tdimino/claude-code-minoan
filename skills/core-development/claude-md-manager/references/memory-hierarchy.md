# Claude Code Memory Hierarchy

The full configuration stack for Claude Code instructions, from broadest to most specific scope. All 6 tiers are individually documented by Anthropic at [code.claude.com/docs/en/memory](https://code.claude.com/docs/en/memory); the numbered hierarchy and composition sequence below is this skill's synthesis of their table.

## The 6 Tiers

| Tier | Location | Scope | Shared With | Loaded When |
|------|----------|-------|-------------|-------------|
| **Managed policy** | `/Library/Application Support/ClaudeCode/CLAUDE.md` (macOS) | Organization-wide | All org users | Always |
| **Project memory** | `./CLAUDE.md` or `./.claude/CLAUDE.md` | Project-wide | Team (via git) | Session start |
| **Project rules** | `./.claude/rules/*.md` | Path-scoped | Team (via git) | When matching files are in context |
| **User memory** | `~/.claude/CLAUDE.md` | All projects | Personal only | Always |
| **Project local** | `./CLAUDE.local.md` | This project | Personal only (auto-gitignored) | Session start |
| **Auto memory** | `~/.claude/projects/<project>/memory/` | Per-project | Personal only | First 200 lines of MEMORY.md at start; topic files on demand |

More specific tiers take precedence over broader ones. Child-directory CLAUDE.md files load on demand when editing files in those directories.

## Where to Put an Instruction

| Instruction applies to... | Place it in... |
|---------------------------|----------------|
| All sessions across all projects | User memory (`~/.claude/CLAUDE.md`) |
| All developers on this project | Project memory (`./CLAUDE.md`) |
| Only when editing specific file paths | Project rules (`.claude/rules/`) |
| Personal project preferences (not committed) | `CLAUDE.local.md` |
| Deterministic enforcement (not advisory) | Hooks (`.claude/hooks/`), not memory |
| Domain knowledge relevant only sometimes | Skills (`.claude/skills/`) |
| Agent-specific behavior | Agent definitions (`.claude/agents/`) |

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

## How Tiers Compose

1. Managed policy loads first (org-wide baseline)
2. User memory layers personal preferences
3. Project memory adds team conventions
4. Project rules add path-conditional instructions
5. Project local overrides with personal project preferences
6. Auto memory contributes learned patterns from prior sessions

All tiers are **advisory** — the agent reads them as guidance but may deviate under context pressure. For deterministic enforcement, use hooks (`.claude/hooks/`).
