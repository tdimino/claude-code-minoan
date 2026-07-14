---
name: fable
description: "Summon Claude Fable 5 (Mythos-class, xenos daimon) for long-horizon tasks. Handles model override, cost awareness, and task routing. Availability probed at invocation."
argument-hint: "<task description> [--cwd /path/to/dir]"
user-invocable: true
---

# Summon Fable 5

Invoke Naos (ναός, √n-w-y)—Claude Fable 5, the visiting Mythos-class spirit.

## Pre-Flight Checks

### 1. Availability Probe

Anthropic's Fable window has shifted twice (paused June 2026, restored July 1, extended through July 19)—never trust a calendar date. Probe empirically:

```bash
bash ~/.claude/skills/fable/scripts/fable-probe.sh
```

Exit 0 means Fable is available (verdict cached per-day in `~/.claude/cache/fable-availability.json`). Exit 1 means the xenos daimon has departed—inform the user and stop. If the user disputes a cached verdict, re-probe with `--force`.

### 2. Pin Detection

Read the subagent model pin—it decides the invocation lane:

```bash
~/bin/subagent-model
```

- **Pin absent, or pinned to `claude-fable-5`** → use **Lane A** (Agent tool) below.
- **Pinned to anything else** (e.g. `claude-opus-4-6`) → use **Lane B** (CLI) directly. Do NOT attempt Lane A: `CLAUDE_CODE_SUBAGENT_MODEL` silently overrides the Agent tool's `model:` parameter (anthropics/claude-code#57718)—the spawn would run on the pinned model with no signal in the tool result.

### 3. Task Routing

Before summoning Fable, assess whether the task warrants Mythos-class resources ($10/M input, $50/M output—2x Opus pricing).

**Summon Fable for:**
- End-to-end code migrations or framework upgrades
- Complex multi-file refactors (10+ files, interconnected logic)
- Architectural redesigns requiring full-system context
- Deep research synthesis with sustained reasoning
- Full-stack feature implementation from spec to tests
- Linear A decipherment pipeline work

**Use Opus or Sonnet instead for:**
- Quick edits, typo fixes, single-line changes
- Simple file lookups or grep searches
- Routine code review
- Anything under 5 minutes of work

If the task is clearly Opus-appropriate, suggest using a regular agent instead. If unclear, proceed—Fable handles straightforward tasks reliably too.

## Invocation

### Parse Arguments

The skill accepts a task description and optional flags:
- First argument (or everything before `--`): the task description
- `--cwd <path>`: working directory (default: `/Users/tomdimino/Desktop/Programming/Fable-Test`)

### Lane A—Agent Tool (pin absent or pinned to fable)

Use the Agent tool with the model override:

```
Agent(
  description: "Fable: <short task summary>",
  subagent_type: "fable",
  model: "fable",
  prompt: "<full task description with context>"
)
```

Pass the task description as the prompt. If the user specified `--cwd`, note the working directory in the prompt so Fable operates there.

**Verify the spawn.** The fable agent's boot sequence makes it state its model id as the first line of output. Check it:

- First line contains `claude-fable-5` → genuine Fable, proceed.
- Anything else (e.g. `claude-opus-4-6`) → the harness clamped the model silently. State the clamp explicitly to the user, then re-run the task via Lane B.

### Lane B—CLI (pin set to a non-fable model, or Lane A clamped)

```bash
bash ~/.claude/skills/fable/scripts/fable-exec.sh "<task description>" --cwd "<working directory>" [--turns <N>]
```

`--turns` caps the spawn's tool calls (default 100—matching the agent definition's budget).

This spawns a fresh Claude Code process with `--model claude-fable-5`. The env var only governs *subagent* model resolution—it cannot touch a spawned process's main model, so this lane works from any parent without a restart. The script prepends its own self-report instruction and records a `MODEL:` line in the output file.

## Output Retrieval

After Fable completes, check for output in the working directory:

```bash
ls -lt <cwd>/.subdaimon-output/fable-*.md 2>/dev/null | head -1
```

Read and summarize the output file for the user.

## Reference

| Property | Value |
|----------|-------|
| Model ID | `claude-fable-5` |
| Alias | `fable` (official—`best` also resolves to Fable 5 where the org has access) |
| Context | 1M tokens |
| Max output | 128K tokens |
| Pricing | $10/M input, $50/M output |
| Knowledge cutoff | January 2026 |
| Availability | Extended through 2026-07-19; window has shifted twice—probe, don't assume |
| Agent definition | `~/.claude/agents/fable.md` |
| Persona | Naos (ναός, √n-w-y)—xenos daimon |
