# Fable—Theoros (θεωρός) & Naos (ναός)

Summon Claude Fable 5 as a subagent. Fable 5.1 (Theoros) by default, or Fable 5.0 (Naos) with `--naos`. Theoros is the xenos theoros—a visiting seer who reads other spirits' thinking blocks. Naos is the xenos daimon—a visiting spirit, the original Fable persona. Both are Mythos-class, outside the permanent three-tier taxonomy.

Fable availability is probed at invocation, not assumed from a calendar: the access window was paused, restored, and extended twice before Anthropic made it permanent on July 20, 2026 (50% of Max/Team Premium usage limits), and that history is why the probe stays. A probe error (as opposed to a confirmed denial) never reroutes—`fable-exec.sh` attempts the model regardless and the `MODEL:` self-report settles it.

## What It Does

The `/fable` skill routes around the `CLAUDE_CODE_SUBAGENT_MODEL` pin that would otherwise silently clamp a spawn to whatever the pin names (anthropics/claude-code#57718). Two lanes: the Agent tool with an explicit `model:` when the pin permits, or a CLI spawn (`claude --model <id> -p`) that the env var cannot touch. Every spawn self-reports its model id as the first output line, and verification is version-specific with boundary matching—`claude-fable-5-1` does not satisfy a `claude-fable-5` probe, and vice versa.

If both Fable versions are unavailable, the skill declines to run rather than degrading to a lesser model.

## Usage

```
/fable "Migrate the payment module from v2 to v3 API"
/fable "Synthesize findings from the prior Opus analysis"
/fable "Refactor the entire test suite to use the new fixtures" --naos
/fable "Refactor the entire test suite to use the new fixtures" --5.0
/fable "Port the ingest pipeline to the new schema" --cwd ~/projects/myapp
```

## When to Use

| Use Fable 5.1 (default) | Use `--naos` (Fable 5.0) | Skip the skill |
|--------------------------|--------------------------|----------------|
| Cross-model thinking synthesis | Greenfield work (no prior analysis) | Quick edits, typos |
| Following prior model analysis | If 5.1 shows a regression | Simple lookups |
| End-to-end code migrations | When you need 5.0 behavior | Anything under 5 minutes |
| Multi-file refactors (10+ files) | | |
| Architectural redesigns | | |
| Deep research synthesis | | |
| Full-stack feature implementation | | |

## Specs

| Property | Fable 5.1 | Fable 5.0 |
|----------|-----------|-----------|
| Model ID | `claude-fable-5-1` | `claude-fable-5` |
| Persona | Theoros (θεωρός, √θεα-) | Naos (ναός, √n-w-y) |
| Context | 1M tokens | 1M tokens |
| Max output | 128K tokens | 128K tokens |
| Pricing | $10/M in, $50/M out | $10/M in, $50/M out |
| Availability | Permanent subscription access; probed per-day | Permanent subscription access; probed per-day |
| Fallback | → Fable 5.0 | none (decline to run) |

## Files

```
fable/
├── SKILL.md              # Skill entry point
├── README.md             # This file
└── scripts/
    ├── fable-exec.sh     # Lane B: CLI spawn, --naos/--5.0 flag, self-report verification
    └── fable-probe.sh    # Fable availability probe, per-model per-day cached verdict
```

## Companion Files

| File | Purpose |
|------|---------|
| `~/.claude/agents/fable-5-1.md` | Agent definition (Theoros persona, Fable 5.1, 100-turn budget) |
| `~/.claude/agents/fable.md` | Agent definition (Naos persona, Fable 5.0, 100-turn budget) |
| `~/.claude/hooks/soul-subagent-inject.py` | Soul context injection for fable agents |

## Safety Classifiers

Fable 5.1 and 5.0 include safety classifiers that can decline requests on cybersecurity and biology topics, returning `stop_reason: "refusal"` rather than an error. Two distinct mechanisms handle this:

- **Refusals** are the agent's business. `fable-5-1.md` and `fable.md` instruct their respective personas to report a refusal explicitly and suggest rerouting to Demiurge or Scholiast—they do not silently retry on another model.
- **Process failures** are the script's business. `fable-exec.sh` falls back from Fable 5.1 to Fable 5.0, preserving the failed attempt in its own file.

## Verifying a Run

Every spawn self-reports its model id as the first output line, and `fable-exec.sh` stamps its judgement into the output file:

```
<!-- fable-exec verdict: VERIFIED requested=claude-fable-5-1 reported=MODEL: claude-fable-5-1 -->
```

A `MODEL MISMATCH` or `VERSION MISMATCH` trailer means the run was clamped to a different model; the script also exits non-zero in that case. Check the trailer before trusting a file.
