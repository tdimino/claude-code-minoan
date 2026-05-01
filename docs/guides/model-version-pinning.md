# Pinning Claude Code to Opus 4.6

Claude Code defaults to the latest Opus model (currently 4.7). If you want Opus 4.6 instead—for its output style, reasoning characteristics, or consistency with an existing setup—you need to pin the version explicitly. The alias `"opus"` always resolves to the newest Opus release; pinning requires the full model identifier.

## Model identifiers

| Alias | Resolves to | Pinned ID |
|-------|-------------|-----------|
| `opus` | Latest Opus (currently 4.7) | — |
| `sonnet` | Latest Sonnet | — |
| `haiku` | Latest Haiku | — |
| — | Opus 4.6 specifically | `claude-opus-4-6` |
| — | Opus 4.7 specifically | `claude-opus-4-7` |

Dated builds (e.g. `claude-opus-4-6-20260220`) also work but are rarely needed—the undated ID tracks the latest point release within that major version.

## Methods

### 1. Settings file (persistent, recommended)

Add the `"model"` key to your settings file. This applies to every session automatically.

**User-level** (`~/.claude/settings.json`):

```json
{
  "model": "claude-opus-4-6"
}
```

**Project-level** (`.claude/settings.json` in the repo root):

```json
{
  "model": "claude-opus-4-6"
}
```

Project-level settings override user-level. If your team checks `.claude/settings.json` into the repo, everyone on the project gets the same model.

### 2. CLI flag (per-session)

```bash
claude --model claude-opus-4-6
```

This overrides whatever is in settings for that single session. Useful for one-off testing on a different model without changing your config.

### 3. In-session command

Type `/model` inside a running session to switch models interactively. The change applies only to the current session.

### 4. Agent definitions

Custom agents in `.claude/agents/*.md` support a `model` field in YAML frontmatter. This controls which model the agent uses when spawned, independent of the parent session's model:

```yaml
---
name: my-agent
model: claude-opus-4-6
---
```

Note: the `model` field in agent frontmatter accepts both aliases (`opus`, `sonnet`, `haiku`) and pinned IDs (`claude-opus-4-6`). If you use the alias, the agent will follow whatever that alias resolves to at runtime.

### 5. Spawn command

When spawning new sessions via `/spawn`, pass the model flag:

```bash
/spawn ~/my-project --model claude-opus-4-6
```

## Precedence

**At session launch** (highest to lowest):

1. CLI `--model` flag
2. Project-level `.claude/settings.json`
3. User-level `~/.claude/settings.json`
4. Default (latest Opus)

**During a session**, the `/model` command overrides whatever the session launched with.

## Verifying your model

The status line shows the active model. If you use the [statusline setup](../global-setup/statusline/README.md), it appears as the crab widget (e.g. `🦀: Opus 4.6`).

You can also check programmatically:

```bash
grep '"model"' ~/.claude/settings.json
```

Or inside a session, the system prompt includes the line: `You are powered by the model named Opus 4.6. The exact model ID is claude-opus-4-6.`

## Why pin to 4.6?

Opus 4.7 is the default and generally the most capable model. Reasons to pin to 4.6:

- **Consistency**: If your CLAUDE.md, skills, and prompts were tuned for 4.6's behavior, switching models can change output style, tool-calling patterns, and reasoning strategies.
- **Fast mode**: `/fast` toggles faster output on Opus 4.6 without downgrading to a smaller model. Check current Claude Code release notes to confirm availability on newer versions.
- **Known behavior**: If your workflow depends on specific model characteristics (verbosity, code style, agent coordination patterns), pinning prevents surprises when Anthropic updates the `opus` alias.
