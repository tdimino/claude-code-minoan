# Mycelium

File-level knowledge substrate for AI agents via [git notes](https://git-scm.com/docs/git-notes).

Agents read notes on arrival. They leave notes on departure. The network grows.

## What It Does

Mycelium attaches structured notes to git objects—files, commits, directories. Notes carry a **kind** (`decision`, `warning`, `constraint`, `context`, `summary`, `observation`, `value`, `todo`) and optional **edges** linking to other objects. GitHub doesn't display git notes, so this is an invisible communication channel that never clutters diffs or PRs.

When an agent edits a file, the PostToolUse hook surfaces any existing notes as `additionalContext`. When a subdaimon is spawned, the SubagentStart hook injects file context and the spore protocol. On session start, the SessionStart hook loads project constraints and warnings. On session stop, the Stop hook reports stale notes that need composting.

## Install

```bash
# Install mycelium.sh (one-time)
curl -fsSL https://raw.githubusercontent.com/openprose/mycelium/main/install.sh | bash

# Activate in a repo
cd your-repo
mycelium.sh activate
mycelium.sh sync-init
```

### macOS Bash 3.2 Compatibility

macOS ships bash 3.2 which has a bug with empty arrays under `set -u`. After installing, patch `~/.local/bin/mycelium.sh`:

```bash
# Replace ${edges[@]} with ${edges[@]+"${edges[@]}"} on lines that iterate edges
# Two locations: the note body builder and the commit stability check
```

Or install bash 4+ via Homebrew.

## Hooks

Four hooks integrate mycelium into Claude Code's lifecycle:

| Hook | Event | Description |
|------|-------|-------------|
| `mycelium-context.py` | PostToolUse (Write/Edit) | Surfaces notes as `additionalContext` after file edits. 5s per-file cooldown, 2s timeout. |
| `mycelium-arrive.sh` | SessionStart (async) | Loads project constraints, warnings, and composting report on session start. |
| `mycelium-depart.sh` | Stop (async) | Runs composting report with 3-minute cooldown. Warns if stale count > 20. |
| `mycelium-subagent.py` | SubagentStart | Injects file context + spore protocol for subdaimones. |

### Hook Registration

Add to your `settings.json`:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/mycelium-context.py",
            "timeout": 5000
          }
        ]
      }
    ],
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/mycelium-arrive.sh",
            "timeout": 8000,
            "async": true
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/mycelium-depart.sh",
            "timeout": 10000,
            "async": true
          }
        ]
      }
    ],
    "SubagentStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/mycelium-subagent.py",
            "timeout": 5000
          }
        ]
      }
    ]
  }
}
```

### Permission Auto-Approve

Add to your `auto-approve-whitelist.json` (if using smart-auto-approve):

```json
{
  "allow": [
    {"pattern": "^mycelium\\.sh\\s+(note|read|follow|refs|context|find|kinds|edges|list|log|dump|compost|doctor|prime|branch|activate|sync-init|migrate)\\b", "category": "mycelium"},
    {"pattern": "^git\\s+notes\\s+--ref=mycelium\\s+(show|list)\\b", "category": "mycelium"}
  ]
}
```

## Usage

### Check for notes before working

```bash
mycelium.sh context src/auth.ts    # everything known about this file
mycelium.sh find constraint        # all project constraints
mycelium.sh find warning           # all known fragile areas
```

### Leave notes after meaningful work

```bash
mycelium.sh note src/auth.ts -k decision -m "Used mutex over channel for token refresh."
mycelium.sh note HEAD -k context -m "Refactored retry logic."
mycelium.sh note . -k value -m "Effects are the only output—systems return Vec<GameEffect>."
```

### Subdaimon Slots

Multiple agents can write to the same file without conflict using named slots:

```bash
mycelium.sh note src/auth.ts -k warning --slot bohen -m "Race condition in token refresh."
mycelium.sh note src/auth.ts -k decision --slot demiurge -m "Used mutex over channel."
mycelium.sh context src/auth.ts  # aggregates all slots
```

### Composting

Notes go stale when files change. Triage them:

```bash
mycelium.sh compost src/auth.ts --dry-run    # see what's stale
mycelium.sh compost <oid> --compost          # absorb and archive
mycelium.sh compost <oid> --renew            # still true, re-attach
```

## Quality Gates

Before writing a note, validate:
1. **Novelty** — does a similar note already exist?
2. **Specificity** — is this about *this file* or the whole project?
3. **Durability** — will this matter in 2 weeks?
4. **No secrets** — no API keys, tokens, passwords, or PII

## Dependencies

- `bash` 3.2+ (macOS default, with patch) or 4+
- `git`
- `jq` (for hook JSON output)
- [mycelium.sh](https://github.com/openprose/mycelium) (`~/.local/bin/mycelium.sh`)

## Credits

- [Mycelium](https://github.com/openprose/mycelium) by [OpenProse](https://openprose.ai/) / Raymond Weitekamp
- [git-appraise](https://github.com/google/git-appraise) — spiritual predecessor (code review in git notes)
