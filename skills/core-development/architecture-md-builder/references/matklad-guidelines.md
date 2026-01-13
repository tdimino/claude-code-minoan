# matklad's ARCHITECTURE.md Guidelines

Source: [rust-analyzer ARCHITECTURE.md](https://github.com/rust-lang/rust-analyzer/blob/master/docs/dev/architecture.md) and matklad's blog posts.

## The Problem with Documentation

Traditional documentation often fails because:
- README.md focuses on users, not contributors
- Code comments explain "what" not "why"
- Design docs get stale quickly
- No central place answers "how does this work?"

## The Solution: ARCHITECTURE.md

A single document that provides a **map** of the codebase. Not exhaustive documentation, but enough to orient a new contributor.

## Core Principles

### 1. Bird's Eye Overview

Start with the big picture:
- What problem does this software solve?
- What's the high-level approach?
- What are the key design principles?

**Example:**
```markdown
rust-analyzer is an implementation of Language Server Protocol for Rust.
It provides IDE features like completion, go-to-definition, and refactoring.

The core principle is "on-demand computation": we don't analyze everything
upfront, but compute information as needed using a query-based architecture.
```

### 2. Coarse-Grained Codemap

Think "country-level, not state-level":
- Major directories and their purposes
- How modules relate to each other
- Data flow between components

**Do:** "The `crates/` directory contains 20+ crates organized by concern"
**Don't:** List every file in every directory

### 3. Named Entities

Mention important files, types, and modules **by name**:
- No hyperlinks (they rot)
- Readers should use symbol search (Cmd+T, grep)
- Names are more stable than paths

**Example:**
```markdown
The `Database` trait in `base_db` defines the core query interface.
`Semantics` in `hir` provides a high-level API for semantic information.
```

### 4. Architectural Invariants

Document the rules that are **always** true:
- What the code never does
- What patterns are forbidden
- What guarantees are maintained

**Examples:**
- "We never block the main thread"
- "All file access goes through `vfs`"
- "Incremental computation is handled by salsa, modules don't cache manually"

### 5. Layer Boundaries

Explain how different parts of the system communicate:
- What interfaces exist between layers
- What data crosses boundaries
- Where transformations happen

**Example:**
```markdown
┌─────────────────────────────────────────┐
│              LSP Layer                   │  JSON-RPC, protocol types
├─────────────────────────────────────────┤
│              IDE Layer                   │  High-level IDE operations
├─────────────────────────────────────────┤
│              HIR Layer                   │  Semantic model
├─────────────────────────────────────────┤
│              Syntax Layer                │  Concrete syntax trees
└─────────────────────────────────────────┘
```

### 6. Cross-Cutting Concerns

Address issues that span multiple modules:
- Error handling strategy
- Logging and diagnostics
- Configuration management
- Testing approach

## What NOT to Include

- API documentation (that's rustdoc/JSDoc)
- User guides (that's README or docs/)
- Implementation details (that's code comments)
- Historical decisions (that's ADRs or commit messages)

## Maintenance

The document should be:
- **Concise**: 500-1000 lines for most projects
- **Stable**: High-level enough that it doesn't need frequent updates
- **Accurate**: Wrong information is worse than no information

Review quarterly or when major architectural changes occur.

## Example Structure

```
ARCHITECTURE.md
├── Bird's Eye View (problem, approach, principles)
├── Architecture Diagram (ASCII art)
├── Codemap
│   ├── Major Directory 1
│   ├── Major Directory 2
│   └── ...
├── Data Flow
├── Architectural Invariants
├── Cross-Cutting Concerns
├── Layer Boundaries
└── Key Files Reference
```

## References

- [rust-analyzer ARCHITECTURE.md](https://github.com/rust-lang/rust-analyzer/blob/master/docs/dev/architecture.md)
- [matklad's blog on documentation](https://matklad.github.io/2021/02/06/ARCHITECTURE.md.html)
- [Divio Documentation System](https://documentation.divio.com/)
