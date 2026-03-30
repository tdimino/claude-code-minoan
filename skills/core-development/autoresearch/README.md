# Autoresearch

Scaffold and run Karpathy-style autoresearch loops in any git repo. Hypothesis, implement, eval, keep or discard—autonomous code improvement driven by adversarial programmatic gates.

## What It Does

Setting up an autoresearch loop from scratch takes ~2 hours: writing an eval script, a runner, a program.md, configuring git branches, wiring the `claude -p` subprocess pipeline. This skill reduces that to 5 minutes.

```
/autoresearch init       # detect stack, scaffold .lab/, generate eval gates
/autoresearch run        # launch the loop (50 iterations default)
/autoresearch status     # composite, timeline, convergence signals
/autoresearch resume     # recover interrupted runs
```

## How It Works

The loop runs on a dedicated git branch. Each iteration:

1. **Hypothesis** — `claude -p` reads `program.md` and proposes one change
2. **Implement** — `claude -p` implements the hypothesis
3. **Commit** — git commit the change
4. **Eval** — run adversarial programmatic gates (build, test, lint, behavioral, pipeline, docs)
5. **Keep/Discard** — if composite improved, keep. Otherwise `git reset --hard HEAD~1`

All experiment knowledge lives in `.lab/` (gitignored). Git reverts never corrupt the research record.

## The Five Invariants

1. **Single mutable surface** — one hypothesis per iteration
2. **Fixed eval budget** — deterministic, bounded-time eval with no network calls
3. **One scalar metric** — composite score drives keep/discard
4. **Binary keep/discard** — improved or reverted, no partial keeps
5. **Git-as-memory** — every experiment is a commit, history is the log

## Eval Gate Architecture

Gates are organized in 4 tiers with configurable weights:

| Tier | Default Weight | What It Measures |
|------|---------------|-----------------|
| T1: Build+Test | 0.20 | Compiles, tests pass, lint clean |
| T2: Behavioral | 0.40 | Integration tests, CLI output, real behavior |
| T3: Pipeline | 0.25 | Build artifacts, installs, real I/O |
| T4: Documentation | 0.15 | Test count floor, doc coverage |

Gates are adversarial: stub implementations cannot pass. The eval generator produces gates that run real commands, validate output content (not file existence), and use percentage thresholds (not hardcoded numbers).

## Extended Status Vocabulary

Beyond binary keep/discard:

| Status | Meaning |
|--------|---------|
| KEEP | Composite improved >= threshold |
| KEEP* | Primary improved but secondary metric regressed |
| DISCARD | No improvement, reverted |
| INTERESTING | Informative negative—logged to dead-ends, code reverted |
| CRASH | Eval infrastructure failure |
| TIMEOUT | Experiment exceeded time budget |

## Stack Support

Auto-detects language and toolchain from build files:

- **Rust** — Cargo.toml, cargo test, clippy
- **Python** — pyproject.toml/setup.py, pytest, ruff/flake8
- **Node/TypeScript** — package.json, npm test, eslint
- **Go** — go.mod, go test, go vet

## Installation

**Personal (recommended):**
```bash
# Already installed at ~/.claude/skills/autoresearch/
```

**From claude-code-minoan:**
```bash
cp -r skills/core-development/autoresearch ~/.claude/skills/autoresearch
```

**Or symlink:**
```bash
ln -s "$(pwd)/skills/core-development/autoresearch" ~/.claude/skills/autoresearch
```

## File Layout

```
autoresearch/
├── SKILL.md                              # Claude Code skill definition
├── README.md                             # This file
├── scripts/
│   ├── detect_stack.py                   # Language/toolchain detection
│   ├── scaffold.py                       # /autoresearch init
│   ├── eval_gen.py                       # Generate adversarial eval gates
│   ├── runner_template.py                # Template copied to .lab/runner.py
│   └── report.py                         # /autoresearch status
├── assets/
│   ├── eval_base.py                      # Base eval framework (gate registration, scoring)
│   ├── config.json.tmpl                  # Config template
│   └── program.md.tmpl                   # Program constraints template
└── references/
    ├── five-invariants.md                # The 5 non-negotiable rules
    ├── eval-gate-design.md               # How to write adversarial gates
    └── convergence-signals.md            # 9 soft signals for strategy adjustment
```

## Proven Results

- **shadow-engine** (Rust game engine): 34 keeps from 50 iterations, eval composite 0.69 to 1.0 across 5 runs
- **perplexity-clone** (Python search): search quality optimization, the original pattern

## Design Influences

- [Karpathy's autoresearch pattern](https://x.com/kaboroevsky/status/1891922030892458257) — the core loop
- [ResearcherSkill](https://github.com/krzysztofdudek/ResearcherSkill) — `.lab/` gitignored store, session resume, extended statuses, convergence signals
- [SubQ Eval](https://github.com/subquadratic-ai/cli-tool) — three-tier output protocol (GATE/METRIC/TRACE), adversarial friction tests
- [Agent Skills](https://agentskills.io/) — skill packaging standard

## Requirements

- Claude Code with `claude -p` (subscription auth, not API)
- Python 3.10+
- Git
- A repo with a build system and tests

## License

MIT
