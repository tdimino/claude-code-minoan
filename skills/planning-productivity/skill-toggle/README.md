# skill-toggle

Manage Claude Code skills from the command line. Enable, disable, search, and organize skills into named collections that can be toggled as a unit.

## Why This Exists

Claude Code uses **progressive disclosure** to load skills into context ([docs](https://code.claude.com/docs/en/skills)):

1. **Metadata (always loaded)**: The `name:` and `description:` from every enabled skill's SKILL.md frontmatter are concatenated into the Skill tool's system prompt description. This list is present on **every API call** for the entire session. Cost: ~30--100 tokens per skill.

2. **Full SKILL.md body (loaded on invocation)**: The complete markdown content of a skill is injected into conversation context only when the skill is actually invoked---either by the user via `/skill-name` or by Claude's autonomous decision. Cost: varies by skill (typically 1,000--5,000 tokens), persists in conversation history.

3. **Supporting files (on demand)**: Files in `references/`, `scripts/`, etc. are never auto-loaded. Claude must explicitly read them via the Read tool during execution.

### The Scaling Problem

There is a **15,000-character limit** for the combined skill descriptions in the system prompt. With 56 enabled skills, the metadata overhead is:

| Component | Cost | Frequency |
|-----------|------|-----------|
| Skill listing (56 descriptions) | ~1,600--5,400 tokens | Every API call |
| Invoked skill body | ~1,000--5,000 tokens each | Once per invocation, persists in history |
| Description character budget | 15,000 chars shared across all skills | Hard limit |

The per-message metadata cost is relatively small, and prompt caching mitigates the dollar cost since the skill list is static. But the problems compound at scale:

- **Description budget pressure**: 56 skills with 80-character descriptions consume ~4,500 of the 15,000-character budget. Longer descriptions or more skills push toward the limit, causing truncation.
- **Invocation accumulation**: In a long session where Claude invokes 10--15 skills, the injected SKILL.md bodies consume 10K--75K tokens that persist in conversation history, accelerating compaction.
- **Signal-to-noise ratio**: Claude must reason over 56 skill descriptions on every turn to decide whether to invoke one. Irrelevant skills dilute the signal---a research session doesn't need `bg3-steam-launcher` or `receipt-invoice-bundler` cluttering the decision space.
- **No built-in batch toggle**: Claude Code has no mechanism to switch skill sets by project or task context.

### The Solution

`skill-toggle` lets you disable skills you don't need right now and re-enable them later. **Collections** let you define named groups (e.g., `research`, `comms`, `aldea`) and switch entire workflows on or off in one command.

```bash
# Starting a research session---disable unrelated skills
skill-toggle collection off comms
skill-toggle collection off gaming

# Done researching, switching to Aldea work
skill-toggle collection on aldea
skill-toggle collection off research
```

Disabling a skill removes it from the description listing entirely (personal skills are moved out of `~/.claude/skills/`; plugins are flipped to `false` in `settings.json`). This frees description budget, reduces per-turn reasoning noise, and prevents accidental invocation of irrelevant skills.

## Installation

```bash
# From the repo
cp -r skills/planning-productivity/skill-toggle ~/.claude/skills/skill-toggle

# Or if already in ~/.claude/skills/
# It's already installed.
```

Requires Python 3.8+. No dependencies beyond the standard library.

## Usage

```bash
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py <command> [args]
```

Or invoke via Claude Code: `/skill-toggle list`

### Commands

| Command | Action |
|---------|--------|
| `list` | Show all skills with status, source, description |
| `list --enabled` | Only enabled skills |
| `list --disabled` | Only disabled skills |
| `list --plugins` | Only plugin skills |
| `disable <name> [name...]` | Disable one or more skills |
| `enable <name> [name...]` | Enable one or more skills |
| `status <name>` | Show details for a specific skill |
| `search <query>` | Fuzzy match across names and descriptions |
| `clean` | Move orphan directories (no SKILL.md) to `disabled/orphans/` |
| `collection list` | Show all collections |
| `collection create <name> <skills...>` | Define a new collection |
| `collection save <name>` | Snapshot all currently-enabled skills as a collection |
| `collection show <name>` | List skills in a collection with current status |
| `collection on <name>` | Enable all skills in the collection |
| `collection off <name>` | Disable all skills in the collection |
| `collection delete <name>` | Remove a collection definition |
| `collection add <name> <skills...>` | Add skills to existing collection |
| `collection remove <name> <skills...>` | Remove skills from existing collection |

### How It Works

**Personal skills** are moved between `~/.claude/skills/<name>/` (enabled) and `~/.claude/skills/disabled/<name>/` (disabled). The `disabled/INDEX.md` is auto-regenerated after every operation.

**Plugin skills** are toggled via the `enabledPlugins` object in `~/.claude/settings.json`. Accepts both plugin names (`compound-engineering`) and namespaced skill names (`compound-engineering:deepen-plan`)---the suffix is stripped and the entire plugin is toggled.

**Collections** are named groups stored as JSON in `~/.claude/skills/skill-toggle/collections/`. Each file lists personal skills and/or plugins. `collection on research` enables everything in the `research` collection; `collection off research` disables them. Collections are additive---toggling one only touches the skills it lists.

### Safety

- **Atomic writes**: All JSON updates (settings.json, collection files) use temp-file-then-rename, so a crash mid-write never corrupts the file.
- **Path traversal protection**: Skill and collection names are validated against `^[a-zA-Z0-9_-]+$`.
- **Self-disable guard**: Cannot disable `skill-toggle` itself.
- **Collision detection**: Will not overwrite an existing directory when moving skills.

## Examples

```bash
# Disable two skills you don't need right now
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py disable smolvlm llama-cpp

# Re-enable them
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py enable smolvlm llama-cpp

# Disable a plugin
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py disable agent-evaluation

# Create a collection
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py collection create research \
  academic-research ancient-near-east-research rlama exa-search linear-a-decipherment

# Snapshot current state
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py collection save baseline

# Toggle collections
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py collection off research
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py collection on research

# See what a collection contains
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py collection show research

# Clean up orphan directories
python3 ~/.claude/skills/skill-toggle/scripts/skill_toggle.py clean
```

## How Claude Code Loads Skills

For reference, the three loading gates from the [official docs](https://code.claude.com/docs/en/skills):

| Frontmatter | You can invoke | Claude can invoke | Description in system prompt |
|---|---|---|---|
| *(default)* | Yes | Yes | Yes |
| `disable-model-invocation: true` | Yes | No | No |
| `user-invocable: false` | No | Yes | Yes |

Setting `disable-model-invocation: true` removes a skill's description from the system prompt entirely, saving description budget. But it also prevents Claude from invoking the skill autonomously---you must call it manually with `/skill-name`.

`skill-toggle` takes a different approach: it removes the skill from the filesystem entirely (or flips the plugin setting), so the skill is invisible until re-enabled. This is more appropriate for skills you genuinely don't need in a given session.
