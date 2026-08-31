# Fable—Naos (ναός, √n-w-y)

Summon Claude Fable 5 as a subagent, or Claude Opus 5 with `--opus`. Naos is the xenos daimon—a visiting spirit outside the permanent three-tier taxonomy. Fable availability is probed at invocation, not assumed from a calendar: the access window was paused, restored, and extended twice before Anthropic made it permanent on July 20, 2026 (50% of Max/Team Premium usage limits), and that history is why the probe stays. A probe error (as opposed to a confirmed denial) never reroutes to Opus—`fable-exec.sh` attempts Fable regardless and the `MODEL:` self-report settles it. Opus 5 has no such history and is never probed.

## What It Does

The `/fable` skill routes around the `CLAUDE_CODE_SUBAGENT_MODEL` pin that would otherwise silently clamp a spawn to whatever the pin names (anthropics/claude-code#57718). Two lanes: the Agent tool with an explicit `model:` when the pin permits, or a CLI spawn (`claude --model <id> -p`) that the env var cannot touch. Every spawn self-reports its model id as the first output line, and verification is version-specific—an Opus 5 request answered by Opus 4.8 is a clamp, not a match.

## Usage

```
/fable "Migrate the payment module from v2 to v3 API"
/fable "Refactor the entire test suite to use the new fixtures" --cwd ~/projects/myapp
/fable "Audit the auth layer and fix what you find" --opus
/fable "Port the ingest pipeline to the new schema" --opus --cwd ~/projects/myapp
```

## When to Use

Fable's advantage grows with task complexity—the longer the horizon, the larger its lead. Opus 5 covers the same shapes of work at half the token cost, and is the standing fallback whenever Fable's window is shut.

| Use Fable | Use `--opus` | Skip the skill |
|-----------|--------------|----------------|
| End-to-end code migrations | The same work at half the cost | Quick edits, typos |
| Multi-file refactors (10+ files) | Agentic coding and code review | Simple lookups |
| Architectural redesigns | Any run during a Fable outage | Anything under 5 minutes |
| Deep research synthesis | Runs under a cost ceiling | |
| Full-stack feature implementation | | |

## Specs

| Property | Fable 5 | Opus 5 |
|----------|---------|--------|
| Model ID | `claude-fable-5` | `claude-opus-5` |
| Context | 1M tokens | 1M tokens (default *and* maximum) |
| Max output | 128K tokens | 128K tokens |
| Pricing | $10/M input, $50/M output | $5/M input, $25/M output |
| Availability | Permanent subscription access since 2026-07-20 (50% of plan usage limits); probed empirically per-day | Generally available; never probed |

`claude-opus-5` is complete as written—no date suffix, and no separate long-context variant to request.

## Files

```
fable/
├── SKILL.md              # Skill entry point
├── README.md             # This file
└── scripts/
    ├── fable-exec.sh     # Lane B: CLI spawn bypassing the env pin, --opus flag, self-report verification
    └── fable-probe.sh    # Fable availability probe, per-day cached verdict (skipped under --opus)
```

## Companion Files

| File | Purpose |
|------|---------|
| `~/.claude/agents/fable.md` | Agent definition (Naos persona, 100-turn budget) |
| `~/.claude/hooks/soul-subagent-inject.py` | Soul context injection for fable agents |

## Safety Classifiers

Fable 5 includes safety classifiers that can decline requests on cybersecurity and biology topics, returning `stop_reason: "refusal"` rather than an error. Two distinct mechanisms handle this, and they are easy to conflate:

- **Refusals** are the agent's business. `fable.md` instructs Naos to report a refusal explicitly and suggest rerouting to Demiurge or Scholiast — it does not silently retry on another model.
- **Process failures** are the script's business. `fable-exec.sh` falls back from Fable to `claude-opus-5`, preserving the failed attempt in its own file.

Opus 5 carries the same class of classifier and can also decline; it has no tier beneath it, so a refusal there is reported, not rerouted.

## Verifying a Run

Every spawn self-reports its model id as the first output line, and `fable-exec.sh` stamps its judgement into the output file:

```
<!-- fable-exec verdict: VERIFIED requested=claude-opus-5 reported=MODEL: claude-opus-5 -->
```

A `MODEL MISMATCH` trailer means the run was clamped to a different model; the script also exits non-zero in that case. Check the trailer before trusting a file.

The limit of this scheme is worth stating: it verifies what the model *says* it is. It catches harness-level clamping — the failure mode that actually occurs here, via `CLAUDE_CODE_SUBAGENT_MODEL` — but not a model that misreports itself.
