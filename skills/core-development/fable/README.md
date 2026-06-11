# Fable — Naos (ναός, √n-w-y)

Summon Claude Fable 5 as a subagent. Naos is the xenos daimon — a visiting spirit outside the permanent three-tier taxonomy, available until June 22, 2026.

## What It Does

The `/fable` skill spawns a Fable 5 (Mythos-class) subagent with `model: "fable"`, handling the `CLAUDE_CODE_SUBAGENT_MODEL` override that would otherwise pin it to Opus. Includes a date gate, task routing guidance, and a CLI fallback script.

## Usage

```
/fable "Migrate the payment module from v2 to v3 API"
/fable "Refactor the entire test suite to use the new fixtures" --cwd ~/projects/myapp
```

## When to Use

Fable's advantage grows with task complexity. The longer the horizon, the larger its lead.

| Use Fable | Use Opus/Sonnet Instead |
|-----------|------------------------|
| End-to-end code migrations | Quick edits, typos |
| Multi-file refactors (10+ files) | Simple lookups |
| Architectural redesigns | Routine code review |
| Deep research synthesis | Anything under 5 minutes |
| Full-stack feature implementation | |

## Specs

| Property | Value |
|----------|-------|
| Model ID | `claude-fable-5` |
| Context | 1M tokens |
| Max output | 128K tokens |
| Pricing | $10/M input, $50/M output |
| Available until | June 22, 2026 |

## Files

```
fable/
├── SKILL.md              # Skill entry point
├── README.md             # This file
└── scripts/
    └── fable-exec.sh     # CLI fallback for model override bypass
```

## Companion Files

| File | Purpose |
|------|---------|
| `~/.claude/agents/fable.md` | Agent definition (Naos persona, 100-turn budget) |
| `~/.claude/hooks/soul-subagent-inject.py` | Soul context injection for fable agents |

## Safety Classifiers

Fable 5 includes safety classifiers that can decline requests on cybersecurity and biology topics, falling back to Opus 4.6. The agent definition instructs Naos to report refusals explicitly rather than silently degrading.
