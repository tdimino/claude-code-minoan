# Test Harness Auditor

Audit any repo's test, lint, type-check, static analysis, build, and debug infrastructure. Generates optimized configs for AI coding agents—`.claude/lint-rules.json`, CLAUDE.md command sections, and hook recommendations.

## Quick Start

```bash
# Phase 1: Audit (read-only)
uv run scripts/audit.py

# Machine-readable output
uv run scripts/audit.py --json

# Save snapshot for drift detection
uv run scripts/audit.py --save

# Phase 2: Generate configs (after audit)
uv run scripts/audit.py --json > /tmp/audit.json
uv run scripts/generate.py --audit /tmp/audit.json

# Extract conventions from CLAUDE.md
uv run scripts/extract_conventions.py
```

## What It Does

**Phase 1** scans 6 layers and scores each 0–3:

| Layer | What it checks |
|-------|---------------|
| Test suite | Framework, runner command, coverage, mutation testing |
| Linting | Standard linter, custom rules, agent-specific rules |
| Type checking | Type checker, strict mode |
| Static analysis | Security scanners, dependency audit |
| Build | Build command, workspace detection |
| Debugger/REPL | Debugger availability, REPL access |

Also detects debugging residue files (`*_v2.*`, `*_backup.*`, etc.) and generates prioritized recommendations (P0–P3).

**Phase 2** generates three outputs:
1. **`.claude/lint-rules.json`** — grep-based rules with severity tiers (BLOCKING > HIGH > MEDIUM)
2. **CLAUDE.md sections** — test/lint/typecheck/build commands (section-aware merge preserves existing content)
3. **Hook recommendations** — lint-on-write, test-on-fix, type-check-on-write

## Rule Library

Domain-specific rule packs auto-loaded by framework/stack detection:

| Pack | Rules | Matches |
|------|-------|---------|
| `react.json` | 5 | React/Next.js projects |
| `functional-ts.json` | 19 | TypeScript + React (FP anti-patterns) |
| `rust-workspace.json` | 5 | Rust projects |
| `python-cli.json` | 4 | Python projects |

Add custom packs: create a JSON file in `rule-library/` with `_frameworks` and/or `_stack` matching fields.

## Drift Detection

```bash
# First run saves baseline
uv run scripts/audit.py --save

# Subsequent runs show changes
uv run scripts/audit.py --save
# → Score changes, config additions/removals, new residue files
```

## Supported Stacks

First-class: JavaScript/TypeScript, Rust, Python, Go, Ruby. Other stacks get basic detection with generic recommendations.

## Scripts

| Script | Purpose |
|--------|---------|
| `audit.py` | Read-only 6-layer assessment with scoring |
| `generate.py` | Config generation from audit data |
| `extract_conventions.py` | Parse CLAUDE.md constraints into lint rule candidates |
