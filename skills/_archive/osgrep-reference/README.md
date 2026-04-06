# OSGrep Reference

The semantic search skill. Find code by meaning, not keywords---using local AI embeddings to search, compress files to signatures, browse API surfaces, and trace call graphs across any codebase.

**Last updated:** 2026-02-18

**Reflects:** [OSGrep](https://osgrep.app/) v0.5.16, including the search, skeleton, symbols, and trace commands.

---

## Why This Skill Exists

`grep` finds text. OSGrep finds *meaning*. Ask "where does authentication happen?" and it returns the auth middleware, token validation, and session management code---not every file that contains the string "auth". It builds a per-project index using local AI embeddings (no remote API), then provides four commands that cover the full spectrum of code navigation: semantic search, file compression, API browsing, and call graph analysis.

This skill documents all four commands with domain-specific query patterns, workflow recipes, and performance notes. The search-patterns reference includes tested queries for Open Souls, React/Next.js, backend APIs, databases, and testing---ready to use without prompt engineering.

---

## Structure

```
osgrep-reference/
  SKILL.md                                 # Overview, quick start, CLI reference
  README.md                                # This file
  references/
    search-patterns.md                     # Domain-specific query templates
    skeleton-command.md                    # File compression to signatures
    symbols-command.md                     # API surface browsing
    trace-command.md                       # Call graph analysis
```

---

## What It Covers

### Four Commands

| Command | Purpose | Key Benefit |
|---------|---------|-------------|
| `osgrep "query"` | Semantic code search | Find code by meaning, not keywords |
| `osgrep skeleton` | Compress files to signatures | 85% token reduction for LLM context |
| `osgrep symbols` | Browse API surface | Discover functions, classes, types |
| `osgrep trace` | Call graph analysis | Who calls what, impact assessment |

### Search

Natural-language queries against local embeddings with ColBERT reranking:

```bash
osgrep "where does authentication happen" -p ./src -m 5
osgrep "error handling patterns" -p ./src/api -m 10
osgrep "database connection pooling" -m 3
```

Indexes are stored per-project in `.osgrep/`. First run builds the index; subsequent searches are fast.

### Skeleton

Compress files to function/class signatures, stripping implementation details:

```bash
osgrep skeleton src/auth/middleware.ts     # File path mode
osgrep skeleton validateToken              # Symbol name mode
osgrep skeleton "session management" -n 5  # Search query mode
```

**85% token reduction** vs reading full files. Output includes complexity indicators (C:1-3 simple, C:4-7 moderate, C:8+ complex) and role detection (ORCH = orchestrator).

### Symbols

Browse the indexed API surface of a codebase:

```bash
osgrep symbols                             # List all symbols
osgrep symbols -p src/api/                 # Scope to directory
osgrep symbols --pattern "handle"          # Filter by name
osgrep symbols -l 50                       # Show 50 results
```

### Trace

Bidirectional call graph analysis:

```bash
osgrep trace validateToken                 # Who calls this? What does it call?
osgrep trace --upstream handleRequest      # Impact: what breaks if I change this?
osgrep trace --downstream createSession    # Dependencies: what does this rely on?
```

---

## Domain-Specific Patterns

`references/search-patterns.md` provides tested queries organized by domain:

| Domain | Example Queries |
|--------|----------------|
| **Open Souls** | "mental processes", "cognitive steps", "working memory mutation" |
| **React/Next.js** | "server components vs client", "data fetching patterns", "route handlers" |
| **Backend/API** | "request validation middleware", "rate limiting", "auth token refresh" |
| **Database** | "migration rollback", "connection pool", "ORM query builder" |
| **Testing** | "mock setup patterns", "integration test fixtures", "error case coverage" |

### When to Use OSGrep vs grep/ripgrep

| Task | Use OSGrep | Use grep/rg |
|------|-----------|-------------|
| "Where does X happen?" | Yes | No |
| Find exact string | No | Yes |
| Understand code structure | Yes (skeleton) | No |
| Discover API surface | Yes (symbols) | Partial |
| Assess change impact | Yes (trace) | No |
| Regex pattern matching | No | Yes |

---

## Requirements

- [OSGrep](https://osgrep.app/) installed (`brew install osgrep` or download from site)
- Per-project `.osgrep/` index (auto-created on first run)
- No external dependencies

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/core-development/osgrep-reference ~/.claude/skills/
```
