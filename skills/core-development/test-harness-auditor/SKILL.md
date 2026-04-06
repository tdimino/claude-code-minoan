---
name: test-harness-auditor
description: "This skill should be used when auditing a repo's test, lint, type-check, static analysis, build, and debug infrastructure for AI coding agents. Use when entering a new repo, when asked to 'audit tests', 'audit harness', 'check test infrastructure', 'lint audit', 'what testing tools are configured', or when a repo has no .claude/lint-rules.json. Generates optimized configs for the lint-on-write hook."
argument-hint: "[path]"
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
---

# Test Harness Auditor

Audit any repo's feedback infrastructure across six layers and generate optimized configs for AI coding agents.

## When to Run

- Entering a new repo with no `.claude/lint-rules.json`
- User asks to audit tests, lint setup, or agent infrastructure
- After cloning a repo to check what feedback loops exist
- Periodically to catch configuration drift

## Two-Phase Workflow

### Phase 1: Audit (read-only)

Run the audit script to scan the current repo:

```bash
uv run ~/.claude/skills/test-harness-auditor/scripts/audit.py
```

Or target a specific directory:

```bash
uv run ~/.claude/skills/test-harness-auditor/scripts/audit.py /path/to/repo
```

For machine-readable output (consumed by Phase 2):

```bash
uv run ~/.claude/skills/test-harness-auditor/scripts/audit.py --json > /tmp/audit.json
```

To save a snapshot for drift detection (tracks score changes over time):

```bash
uv run ~/.claude/skills/test-harness-auditor/scripts/audit.py --save
```

Combine flags: `--json --save` saves the snapshot AND outputs JSON. On subsequent `--save` runs, the report includes a drift section showing score regressions, config changes, and residue file changes.

The script produces a structured Markdown report (or JSON with `--json`) with:
- **Stack summary**: detected language, frameworks, package manager, actual scripts from package.json
- **Scorecard**: 0-3 score for each of the six layers (test, lint, type-check, SA, build, debug)
- **Findings**: per-layer details on what was detected
- **Debugging residue**: files matching `*_v2.*`, `*_backup.*`, `*_fixed.*` patterns
- **Recommendations**: prioritized by impact on agent feedback quality (P0-P3)

Present the report to the user. Ask which recommendations to implement before proceeding to Phase 2.

### Phase 1.5: Convention Extraction (optional)

Extract "never X"/"always Y" constraints from CLAUDE.md into candidate lint rules:

```bash
uv run ~/.claude/skills/test-harness-auditor/scripts/extract_conventions.py
```

Outputs JSON with candidate lint-rules.json entries derived from project constraints. Present candidates to the user for approval before merging.

### Phase 2: Config Generation (after user approval)

Run the generation script (optionally with audit JSON for accurate commands):

```bash
uv run ~/.claude/skills/test-harness-auditor/scripts/generate.py --audit /tmp/audit.json
```

Or without audit data (re-detects stack):

```bash
uv run ~/.claude/skills/test-harness-auditor/scripts/generate.py
```

When `--audit` is used, generate.py uses actual commands from package.json (vitest, playwright, biome, etc.) instead of generic templates, and detects separate E2E vs unit test runners.

This produces three outputs:

1. **`.claude/lint-rules.json`** — custom grep-based rules for the lint-on-write hook
   - Stack-specific rules (security, debugging residue, error boundaries, observability)
   - Auto-includes matching rule packs from `rule-library/` (react, rust-workspace, python-cli)
   - Merges with existing config if present (preserves user customizations)
   - Tagged rules (`_tag` field) enable idempotent re-runs

2. **CLAUDE.md testing section** — test/lint/typecheck/build/SA commands
   - Follows claude-md-manager conventions (command-first, concise)
   - **Section-aware merge**: when existing CLAUDE.md is found, surgically replaces only `## Commands` and `## Testing` sections, preserving all other content
   - Present as a proposal — do not overwrite existing CLAUDE.md content

3. **Hook recommendations** — which PostToolUse hooks to enable
   - lint-on-write (primary), test-on-fix, type-check-on-write

For each generated config, present it to the user and ask for approval before writing.

## Scoring System

| Score | Meaning |
|-------|---------|
| 0 | Absent — agent is flying blind on this layer |
| 1 | Minimal — basic tool present but not configured for agents |
| 2 | Adequate — tool configured and runnable |
| 3 | Excellent — strict mode, mutation testing, or advanced config |

## Six Assessment Layers

1. **Test suite**: framework, runner command, coverage config, mutation testing
2. **Linting**: standard linter, custom rules, agent-specific rules
3. **Type checking**: type checker, strict mode, CI integration
4. **Static analysis**: security scanners, complexity checkers, dependency audit
5. **Build/compilation**: build command, incremental build, CI validation
6. **Debugger/REPL**: debugger availability, REPL access

## Integration

- **lint-on-write hook**: generated `lint-rules.json` is consumed by `~/.claude/hooks/lint-on-write.py` (violations are severity-tiered: BLOCKING > HIGH > MEDIUM)
- **claude-md-manager**: generated CLAUDE.md sections follow its conventions (WHAT/WHY/HOW, command-first)
- **agents-md-manager**: for cross-agent compatibility, consider also generating AGENTS.md
- **agnix**: complementary tool — validates the *agent config files* themselves (385 rules for CLAUDE.md/AGENTS.md/SKILL.md stale paths, dead commands, context rot). Our skill validates the *codebase infrastructure*.

## Rule Library

Domain-specific rule packs in `rule-library/` are auto-loaded by generate.py based on detected frameworks and stack:

| Pack | Matches | Rules |
|------|---------|-------|
| `react.json` | react, next frameworks | fetch-in-effect, excessive-useState, inline-style, direct-DOM, indexOf |
| `functional-ts.json` | react, next + typescript | 21 rules: immutability (array-mutation, sort-reverse, delete-operator), const-by-default (let-binding, var), declarative (for-loop, forEach, while, switch), React (class-component, class-state-props, effect-mutation), type safety (any-type), async (raw-promise), testability (nondeterministic-call, console-residue) |
| `rust-workspace.json` | rust stack | chained-clone, box-dyn, allow-dead-code, todo-macro, relative-path-dep |
| `python-cli.json` | python stack | os.path-vs-pathlib, bare-print, subprocess-call, Optional-vs-union |

To add a custom rule pack, create a JSON file in `rule-library/` with `_frameworks` (list) and/or `_stack` (string) matching fields, plus a `rules` array. Pack rules use `pack:` prefix in `_tag` for dedup.

## References

Load these on-demand when deeper context is needed:

- `references/stack-profiles.md` — per-stack detection rules and tool recommendations
- `references/factory-lint-categories.md` — 7 Factory.ai agent lint categories with grep patterns
- `references/anti-patterns.md` — 10 AI-specific anti-patterns with detection heuristics

## Scope

- First-class stacks: JavaScript/TypeScript, Rust, Python, Go, Ruby
- Other stacks get basic detection with generic recommendations
- Does not write or modify test files
- Does not install tools (recommends what to install)
- Does not modify CI/CD pipelines
