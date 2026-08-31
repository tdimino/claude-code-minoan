---
name: fable
description: "Summon Claude Fable 5 (Mythos-class, xenos daimon) or Claude Opus 5 (--opus) for long-horizon tasks. Handles model override, cost awareness, and task routing. Fable availability probed at invocation—permanent subscription access since July 2026."
argument-hint: "<task description> [--opus] [--cwd /path/to/dir]"
user-invocable: true
---

# Summon Fable 5 (or Opus 5)

Invoke Naos (ναός, √n-w-y)—Claude Fable 5, the visiting Mythos-class spirit—or, with `--opus`, Claude Opus 5 at half the cost and no availability window.

## Model Selection

Parse the arguments before any pre-flight check: **`--opus` selects `claude-opus-5`; its absence selects `claude-fable-5`.** Every step below branches on that choice.

| | Fable 5 (default) | Opus 5 (`--opus`) |
|---|---|---|
| Model ID | `claude-fable-5` | `claude-opus-5` |
| Agent tool alias | `fable` | `opus` |
| Pricing | $10/M in, $50/M out | $5/M in, $25/M out |
| Context / max output | 1M / 128K | 1M / 128K |
| Availability | permanent subscription access since 2026-07-20—**probe anyway** | generally available—**no probe** |
| Lane A subagent | `fable` (Naos persona) | `claude` (no daimon persona) |
| Output file | `.subdaimon-output/fable-*.md` | `.subdaimon-output/opus-*.md` |

`claude-opus-5` is the complete model ID—it takes no date suffix, and 1M context is both its default and its maximum, so there is no separate long-context variant to request.

## Pre-Flight Checks

### 1. Availability Probe (Fable only)

**Skip this entirely in Opus mode**—Opus 5 is generally available, so a probe burns tokens on a foregone answer.

Fable 5 has been permanently included in Max/Team Premium subscriptions since July 20, 2026 (at 50% of plan usage limits)—but its history (export-control pause June 2026, restored July 1, extended twice, made permanent July 20) is exactly why availability is probed empirically, never assumed:

```bash
bash ~/.claude/skills/fable/scripts/fable-probe.sh
```

The verdict is three-way, and only definitive verdicts are cached per-day in `~/.claude/cache/fable-availability.json`:

- **Exit 0**—available. Proceed.
- **Exit 1**—confirmed unavailable: the CLI affirmatively denied access, or another model answered the probe. Say so, and offer `--opus` as the standing alternative rather than stopping cold. If the user disputes a cached verdict, re-probe with `--force`.
- **Exit 2**—probe error (empty reply, transient CLI failure): indeterminate and **never cached**. Do NOT reroute to Opus on this—proceed with **Lane B**, which attempts Fable regardless and self-verifies via the `MODEL:` line, with its own fallback on genuine failure.

The probe informs; it never blocks a Fable attempt on its own. The `MODEL:` self-report is the verification that actually counts.

### 2. Pin Detection

Read the subagent model pin—it decides the invocation lane. Compare it against the **selected** model, not against Fable unconditionally:

```bash
~/bin/subagent-model
```

- **Pin absent, or pinned to the selected model** → use **Lane A** (Agent tool) below.
- **Pinned to anything else** → use **Lane B** (CLI) directly. Do NOT attempt Lane A: `CLAUDE_CODE_SUBAGENT_MODEL` silently overrides the Agent tool's `model:` parameter (anthropics/claude-code#57718)—the spawn would run on the pinned model with no signal in the tool result.

The configured default pin is `claude-opus-4-8` and `subagent-model` has no Opus 5 preset, so an active pin sends **Opus mode to Lane B too**—a clamp from Opus 5 down to Opus 4.8 is exactly the silent degradation the self-report step exists to catch.

If you need to change the pin, pass the full id: `subagent-model claude-opus-5`. **`subagent-model opus-5` does not error**—`resolve_preset` has no such preset, so the argument falls through unchanged and pins the literal string `opus-5`, reporting success while leaving an invalid model id in `settings.json`.

### 3. Task Routing

Assess what tier the task actually warrants before spending on it.

**Summon Fable for:**
- End-to-end code migrations or framework upgrades
- Complex multi-file refactors (10+ files, interconnected logic)
- Architectural redesigns requiring full-system context
- Deep research synthesis with sustained reasoning
- Full-stack feature implementation from spec to tests
- Linear A decipherment pipeline work

**Use `--opus` for:**
- The same shapes of work at half the token cost, when the horizon is long but not extreme
- Anything during a Fable outage—Opus 5 is the standing fallback tier
- Agentic coding and code review, where Opus 5 is strongest
- Runs where a cost ceiling matters more than the last increment of capability

**Skip this skill entirely for:**
- Quick edits, typo fixes, single-line changes
- Simple file lookups or grep searches
- Anything under 5 minutes of work

If the task is trivially small, suggest a regular agent instead of either model. If it sits between tiers, proceed with `--opus`—the cheaper spawn is the better default when the call is close.

## Invocation

### Parse Arguments

The skill accepts a task description and optional flags:
- First argument (or everything before `--`): the task description
- `--opus`: run on `claude-opus-5` instead of `claude-fable-5`
- `--cwd <path>`: working directory (default: `/Users/tomdimino/Desktop/Programming/Fable-Test`)

### Lane A—Agent Tool (pin absent or pinned to the selected model)

**Fable mode.** The `fable` agent definition carries the Naos persona and a boot sequence that already emits the self-report:

```
Agent(
  description: "Fable: <short task summary>",
  subagent_type: "fable",
  model: "fable",
  prompt: "<full task description with context>"
)
```

**Opus mode.** Opus 5 is not Naos—the xenos-daimon framing belongs to Fable alone, so spawn the catch-all agent. The `claude` agent has no boot sequence and no output-persistence protocol of its own (both live in `fable.md`, Fable-only), so the prompt must supply them:

```
Agent(
  description: "Opus: <short task summary>",
  subagent_type: "claude",
  model: "opus",
  prompt: "First line of your output: 'MODEL: ' followed by the exact model id powering you.

Before your final message, write your full report to .subdaimon-output/opus-<unix timestamp>.md and return only a pointer to it plus a 1-2 sentence summary.

<full task description with context>"
)
```

Both instructions are load-bearing. Without the first, there is nothing to verify against. Without the second, **no `opus-*.md` is produced at all** and the Output Retrieval step below finds nothing—the Fable path only works because `fable.md` carries that protocol in its own definition.

`claude` also declares no `maxTurns`, so an Opus Lane A spawn takes the harness default rather than Fable's 100. For long-horizon work, prefer Lane B, which passes `--turns 100` explicitly.

In both lanes, if the user specified `--cwd`, note the working directory in the prompt so the spawn operates there.

**Verify the spawn.** Check the first line of output against the model you asked for:

- Fable mode: contains `claude-fable-5` → genuine Fable, proceed.
- Opus mode: contains `claude-opus-5` → genuine Opus 5, proceed. `claude-opus-4-8` is a **clamp**, not a match—the pin won.
- Anything else → the harness clamped the model silently. State the clamp explicitly to the user, then re-run the task via Lane B.

**Alias caveat.** Lane A passes the bare alias `model: "opus"` and relies on the harness binding it to Opus 5 rather than to whatever the current default Opus happens to be. That binding is not verifiable from inside the skill. If Lane A Opus runs start reporting `claude-opus-4-8` while no pin is set, the alias—not a clamp—is the likely cause; switch to Lane B, which passes the unambiguous `claude-opus-5`.

This is also why the verification above is version-specific rather than a substring match on `opus`: a downgrade from Opus 5 to Opus 4.8 is exactly the failure worth catching, and a loose check would wave it through.

### Lane B—CLI (pin set to another model, or Lane A clamped)

```bash
bash ~/.claude/skills/fable/scripts/fable-exec.sh "<task description>" [--opus] --cwd "<working directory>" [--turns <N>]
```

`--turns` caps the spawn's tool calls (default 100—matching the agent definition's budget).

This spawns a fresh Claude Code process with an explicit `--model`. The env var only governs *subagent* model resolution—it cannot touch a spawned process's main model, so this lane works from any parent without a restart. The script prepends its own self-report instruction, skips the Fable probe under `--opus`, and verifies the `MODEL:` line against the requested model version.

An unrecognized flag is a hard error rather than prompt text—a `--opuss` typo would otherwise run on Fable at 2x the cost, silently defeating the flag's whole purpose.

**The exit status is meaningful.** A failed verification exits non-zero even when the spawn itself succeeded, so a clamped run never reads as success. Every run also appends a verdict trailer to its output file:

```
<!-- fable-exec verdict: VERIFIED requested=claude-opus-5 reported=MODEL: claude-opus-5 -->
<!-- fable-exec verdict: MODEL MISMATCH requested=claude-opus-5 reported=MODEL: claude-opus-4-8 -->
```

Check that trailer before trusting a file's contents. Without it, a clamped run and a clean one are indistinguishable on disk.

On failure the routing differs by mode. Fable preserves its partial output, stamps it `RUN FAILED`, and falls back to Opus 5 **in a separate `opus-<ts>.md`**—so the evidence of why Fable failed survives, and Opus content never lands under the `fable-` prefix. Opus 5 has no tier beneath it, so a failure is stamped and the script exits non-zero rather than degrading further.

## Output Retrieval

After the spawn completes, check for output in the working directory—the prefix names the model that produced it:

```bash
ls -lt <cwd>/.subdaimon-output/fable-*.md 2>/dev/null | head -1   # Fable mode
ls -lt <cwd>/.subdaimon-output/opus-*.md 2>/dev/null | head -1    # Opus mode
```

A Fable run that fell back leaves **both**: a `fable-*.md` holding the failed attempt and an `opus-*.md` holding the delivered work. Read the verdict trailer to confirm which is which, then summarize the output for the user.

Lane A produces these files only if the spawn was told to write one—guaranteed by `fable.md` in Fable mode, and by the explicit instruction in the Opus prompt above.

## Reference

| Property | Fable 5 | Opus 5 |
|----------|---------|--------|
| Model ID | `claude-fable-5` | `claude-opus-5` |
| Alias | `fable` (official—`best` also resolves to Fable 5 where the org has access) | `opus` |
| Context | 1M tokens | 1M tokens (default *and* maximum) |
| Max output | 128K tokens | 128K tokens |
| Pricing | $10/M input, $50/M output | $5/M input, $25/M output |
| Availability | Permanent subscription access since 2026-07-20 (50% of Max/Team Premium usage limits)—probe, don't assume | Generally available—no probe |
| Agent definition | `~/.claude/agents/fable.md` | none—uses the `claude` catch-all |
| Persona | Naos (ναός, √n-w-y)—xenos daimon | none |
