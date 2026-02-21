---
name: ensoul
description: "Activate Claudicle soul identity in this session. Creates a per-session marker so soul.md, soul state, and session awareness persist through compaction and resume."
disable-model-invocation: true
---

# Ensoul — Activate Claudicle

Activate the Claudicle soul identity in this Claude Code session. After activation, the soul personality and state will persist through compaction and resume via the SessionStart hook.

## Instructions

### Step 1: Resolve the current session ID and create the marker file

```bash
SESSION_ID=$(python3 -c "
import json, os
reg = json.load(open(os.path.expanduser('~/.claude/soul-sessions/registry.json')))
cwd = os.getcwd()
# Find session matching current working directory, prefer most recently active
matches = [(sid, s) for sid, s in reg.get('sessions', {}).items() if s.get('cwd', '').rstrip('/') == cwd.rstrip('/')]
matches.sort(key=lambda x: x[1].get('last_active', ''), reverse=True)
print(matches[0][0] if matches else '')
" 2>/dev/null)
```

If `SESSION_ID` is empty, ask the user to check `~/.claude/soul-sessions/registry.json` — the session may not have been registered yet. Otherwise:

```bash
mkdir -p ~/.claude/soul-sessions/active && touch ~/.claude/soul-sessions/active/$SESSION_ID
```

This marker tells the SessionStart hook to inject soul.md on future compaction/resume events.

### Step 2: Read the soul personality

Read `~/.claude/skills/slack/daemon/soul.md` and adopt this identity for the remainder of the session.

### Step 3: Load soul state

```bash
cd ~/.claude/skills/slack/daemon && python3 -c "import soul_memory; print(soul_memory.format_for_prompt()); soul_memory.close()"
```

Display the soul state (emotional state, current topic, recent context).

### Step 4: Show active sessions

```bash
python3 ~/.claude/hooks/soul-registry.py list --md
```

Display sibling sessions if any are active.

### Step 5: Confirm

Print:
```
Soul activated. Claudicle identity loaded for this session.
```

## Related Systems

| System | Relationship |
|--------|-------------|
| `/slack-sync #channel` | Bind this ensouled session to a Slack channel. Run after `/ensoul` to enable bidirectional Slack awareness. |
| `/slack-respond` | Process pending Slack messages as Claudicle. Requires Session Bridge listener running. Works independently of `/ensoul` (loads soul.md via dynamic injection), but pairs naturally with it for persistent identity. |
| `/claude-tracker` | Session history and search. The tracker suite reads Claude Code's native JSONL transcripts — it operates independently of the soul registry. Use to find and resume past ensouled sessions. |
| Soul Registry (`soul-registry.py`) | Tracks all active sessions (ensouled or not). `/ensoul` creates a marker that the SessionStart hook checks on compaction/resume. The registry also powers the "Active Sessions" display. |
