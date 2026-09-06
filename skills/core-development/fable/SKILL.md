---
name: fable
description: "Summon Claude Fable 5.1 (Mythos-class, xenos theoros) by default, or Fable 5.0 (--naos). Handles model override, cost awareness, and task routing. Availability probed at invocation."
argument-hint: "<task description> [--naos|--5.0] [--cwd /path/to/dir]"
user-invocable: true
---

# Summon Fable 5

Invoke Theoros (θεωρός, √θεα-)—Claude Fable 5.1, the visiting Mythos-class seer—by default. With `--naos` or `--5.0`, invoke Naos (ναός, √n-w-y)—Fable 5.0.

## Model Selection

Parse the arguments before any pre-flight check: **`--naos` or `--5.0` selects `claude-fable-5`; their absence selects `claude-fable-5-1`.** Every step below branches on that choice.

| | Fable 5.1 (default) | Fable 5.0 (`--naos` / `--5.0`) |
|---|---|---|
| Model ID | `claude-fable-5-1` | `claude-fable-5` |
| Agent tool type | `fable-5-1` | `fable` |
| Pricing | $10/M in, $50/M out | $10/M in, $50/M out |
| Context / max output | 1M / 128K | 1M / 128K |
| Availability | permanent subscription access—**probe per-day** | permanent subscription access—**probe per-day** |
| Persona | Theoros (θεωρός) | Naos (ναός) |
| Agent definition | `fable-5-1.md` | `fable.md` |
| Output file | `.subdaimon-output/fable51-*.md` | `.subdaimon-output/fable-*.md` |

## Pre-Flight Checks

### 1. Availability Probe

Fable has been permanently included in Max/Team Premium subscriptions since July 20, 2026 (at 50% of plan usage limits)—but its history (export-control pause June 2026, restored July 1, extended twice, made permanent July 20) is exactly why availability is probed empirically, never assumed:

```bash
bash ~/.claude/skills/fable/scripts/fable-probe.sh --model claude-fable-5-1   # default
bash ~/.claude/skills/fable/scripts/fable-probe.sh --model claude-fable-5     # --naos
```

The probe accepts `--model <id>` and caches verdicts per model per day in `~/.claude/cache/fable-availability.json`. The verdict is three-way, and only definitive verdicts are cached:

- **Exit 0**—available. Proceed.
- **Exit 1**—confirmed unavailable: the CLI affirmatively denied access, or another model answered the probe. Say so, and offer the alternative Fable version rather than stopping cold. If the user disputes a cached verdict, re-probe with `--force`.
- **Exit 2**—probe error (empty reply, transient CLI failure): indeterminate and **never cached**. Do NOT reroute on this—proceed with **Lane B**, which attempts the model regardless and self-verifies via the `MODEL:` line, with its own fallback on genuine failure.

The probe informs; it never blocks an attempt on its own. The `MODEL:` self-report is the verification that actually counts.

### 2. Pin Detection

Read the subagent model pin—it decides the invocation lane. Compare it against the **selected** model:

```bash
~/bin/subagent-model
```

- **Pin absent, or pinned to the selected model** → use **Lane A** (Agent tool) below.
- **Pinned to anything else** → use **Lane B** (CLI) directly. Do NOT attempt Lane A: `CLAUDE_CODE_SUBAGENT_MODEL` silently overrides the Agent tool's `model:` parameter (anthropics/claude-code#57718)—the spawn would run on the pinned model with no signal in the tool result.

If you need to change the pin, pass the full id: `subagent-model claude-fable-5-1`. **`subagent-model fable-5-1` does not error**—`resolve_preset` has no such preset, so the argument falls through unchanged and pins the literal string `fable-5-1`, reporting success while leaving an invalid model id in `settings.json`.

### 3. Task Routing

Assess what the task actually warrants before spending on it.

**Summon Fable 5.1 (default) for:**
- Tasks requiring synthesis across multiple prior model outputs—paste their full reasoning into the prompt
- Work following prior analysis—include that analysis verbatim in the task prompt
- Iterative refinement sessions where the summoner can adjust effort per-message
- End-to-end code migrations or framework upgrades
- Complex multi-file refactors (10+ files, interconnected logic)
- Architectural redesigns requiring full-system context
- Deep research synthesis with sustained reasoning
- Full-stack feature implementation from spec to tests

**Use `--naos` (Fable 5.0) for:**
- Greenfield work with no prior analysis to synthesize
- Tasks where Fable 5.1 shows a regression or behavioral issue
- When you specifically need Fable 5.0's behavior

**Skip this skill entirely for:**
- Quick edits, typo fixes, single-line changes
- Simple file lookups or grep searches
- Anything under 5 minutes of work

If the task is trivially small, suggest a regular agent instead.

## Invocation

### Parse Arguments

The skill accepts a task description and optional flags:
- First argument (or everything before `--`): the task description
- `--naos` or `--5.0`: run on `claude-fable-5` with the Naos persona
- `--cwd <path>`: working directory (default: `/Users/tomdimino/Desktop/Programming/Fable-Test`)

### Lane A—Agent Tool (pin absent or pinned to the selected model)

**Fable 5.1 mode (default).** The `fable-5-1` agent definition carries the Theoros persona and a boot sequence that already emits the self-report:

```
Agent(
  description: "Fable 5.1: <short task summary>",
  subagent_type: "fable-5-1",
  model: "fable",
  prompt: "<full task description with context>"
)
```

Note: the Agent tool's `model` parameter is an enum (`sonnet|opus|haiku|fable`); full model IDs like `"claude-fable-5-1"` cause `InputValidationError`. The `fable` alias resolves to `claude-fable-5-1`.

**Fable 5.0 mode (`--naos` / `--5.0`).** The `fable` agent definition carries the Naos persona:

```
Agent(
  description: "Fable 5.0: <short task summary>",
  subagent_type: "fable",
  prompt: "<full task description with context>"
)
```

In both lanes, if the user specified `--cwd`, note the working directory in the prompt so the spawn operates there.

**Verify the spawn.** The Agent tool returns only the final message. Check its first line against the model you asked for:

- Fable 5.1 mode: contains `claude-fable-5-1` → genuine Fable 5.1, proceed.
- Fable 5.0 mode: contains `claude-fable-5` but NOT `claude-fable-5-1` → genuine Fable 5.0, proceed. `claude-fable-5-1` is a **version mismatch**, not a match—the substring overlap is what boundary matching exists to catch.
- Anything else → the harness clamped the model silently. State the clamp explicitly to the user, then re-run the task via Lane B.

### Lane B—CLI (pin set to another model, or Lane A clamped)

```bash
bash ~/.claude/skills/fable/scripts/fable-exec.sh "<task description>" [--naos|--5.0] --cwd "<working directory>" [--turns <N>]
```

`--turns` caps the spawn's tool calls (default 100—matching the agent definition's budget).

This spawns a fresh Claude Code process with an explicit `--model`. The env var only governs *subagent* model resolution—it cannot touch a spawned process's main model, so this lane works from any parent without a restart. The script prepends its own self-report instruction, probes the selected model, and verifies the `MODEL:` line against the requested version.

An unrecognized flag is a hard error rather than prompt text—a `--naoss` typo would otherwise run on 5.1 when 5.0 was intended.

**The exit status is meaningful.** A failed verification exits non-zero even when the spawn itself succeeded, so a clamped run never reads as success. Every run also appends a verdict trailer to its output file:

```
<!-- fable-exec verdict: VERIFIED requested=claude-fable-5-1 reported=MODEL: claude-fable-5-1 -->
<!-- fable-exec verdict: VERSION MISMATCH requested=claude-fable-5 reported=MODEL: claude-fable-5-1 -->
```

Check that trailer before trusting a file's contents.

**Fallback chain.** Fable 5.1 → Fable 5.0 on failure. If both fail, exit non-zero and decline to run:

- **Fable 5.1 fails**: preserves partial output in `fable51-<ts>.md`, falls back to Fable 5.0 (Naos) in a separate `fable-<ts>.md`.
- **Fable 5.0 fails** (whether invoked directly via `--naos` or as a fallback): stamped and exits non-zero.

## Output Retrieval

After the spawn completes, check for output in the working directory—the prefix names the model that produced it:

```bash
ls -lt <cwd>/.subdaimon-output/fable51-*.md 2>/dev/null | head -1  # Fable 5.1 (default)
ls -lt <cwd>/.subdaimon-output/fable-*.md 2>/dev/null | head -1    # Fable 5.0 (--naos)
```

A Fable 5.1 run that fell back leaves **both**: a `fable51-*.md` holding the failed attempt and a `fable-*.md` holding the Naos fallback. Read the verdict trailer to confirm which is which, then summarize the output for the user.

Lane A produces these files only if the spawn was told to write one—guaranteed by the respective agent definitions (`fable-5-1.md` and `fable.md`), which carry the output persistence protocol.

## Reference

| Property | Fable 5.1 | Fable 5.0 |
|----------|-----------|-----------|
| Model ID | `claude-fable-5-1` | `claude-fable-5` |
| Alias | `fable` (resolves to 5.1) | — (use full ID in frontmatter) |
| Context | 1M tokens | 1M tokens |
| Max output | 128K tokens | 128K tokens |
| Pricing | $10/M input, $50/M output | $10/M input, $50/M output |
| Availability | Permanent subscription access—probe per-day | Permanent subscription access—probe per-day |
| Agent definition | `~/.claude/agents/fable-5-1.md` | `~/.claude/agents/fable.md` |
| Persona | Theoros (θεωρός, √θεα-)—xenos theoros | Naos (ναός, √n-w-y)—xenos daimon |
