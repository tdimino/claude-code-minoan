# Claude Code Hooks

Scripts that run in response to Claude Code lifecycle events. Together they provide terminal UX, session handoffs, and crash resilience.

## How It Works

```
Claude Code Lifecycle                          What Fires
────────────────────                          ──────────────────────────────────
User types message ──→ UserPromptSubmit ────→ multi-response-prompt.py (/5x)

Claude uses a tool ──→ PreToolUse ──────────→ on-thinking.sh (🔴 tab title)

Claude responds ─────→ Stop ────────────────→ on-ready.sh (🟢 tab + sound + notification)
                                            → propagate-rename.py (sync /rename → caches)
                                            → stop-handoff.py (checkpoint every 5 min)

Context full ────────→ PreCompact ──────────→ precompact-handoff.py (full handoff)

Session exits ───────→ SessionEnd ──────────→ precompact-handoff.py (full handoff)

Every turn ──────────→ StatusLine ──────────→ statusline-monitor.sh (→ ccstatusline)
```

## Hooks

### `precompact-handoff.py` — Session Handoff

The core of the handoff system. Reads the transcript JSONL, summarizes it via OpenRouter (Gemini Flash Lite, ~$0.01/call), and writes a structured YAML to `~/.claude/handoffs/{session_id}.yaml`.

**Fires on**: PreCompact (context full), SessionEnd (graceful exit)

**Output** (`~/.claude/handoffs/{session_id}.yaml`):
```yaml
session_id: "e05a106c-9757-..."
session_short: "e05a106c"
timestamp: "2026-02-11T21:37:00"
trigger: "compact"                    # or "stop", "prompt_input_exit", "other"
cwd: "/Users/you/project"
project: "project"
handoff_count: 3                      # how many times this session checkpointed

objective: What the user was trying to accomplish
completed:
  - Item 1
  - Item 2
decisions:
  - Choice made and rationale
blockers: []
next_steps:
  - What should happen next
```

Also updates `~/.claude/handoffs/INDEX.md` — a running markdown table of all sessions, most recent first, deduped per session, capped at 50 entries.

**Requires**: `OPENROUTER_API_KEY` in environment or `.env` file.

---

### `propagate-rename.py` — Rename Reconciliation

Propagates `/rename` custom titles from `sessions-index.json` (ground truth) to `session-summaries.json` (global cache) and triggers `active-projects.md` rebuild.

**Fires on**: Stop (after every Claude response)

**Data flow**:
1. Read `session_id` and `transcript_path` from hook stdin JSON
2. Look up `customTitle` in `sessions-index.json` (per-project, written by `/rename`)
3. Compare against `title` in `~/.claude/session-summaries.json`
4. If mismatch: update cache, atomic write, fire `update-active-projects.py` in background
5. If already in sync or no custom title: fast path exit (~20ms)

**Why it exists**: `/rename` only updates `sessions-index.json`. Without this hook, `session-summaries.json` and `active-projects.md` never learn about the rename.

**Cost**: Zero. No LLM calls, no network — pure local JSON reconciliation.

---

### `stop-handoff.py` — Throttled Checkpoint

Thin wrapper around `precompact-handoff.py` with three guards:

1. **`stop_hook_active`** — prevents infinite loops (per Claude Code docs)
2. **5-minute cooldown** — skips if this session checkpointed less than 5 min ago
3. **10-minute idle gate** — skips if the transcript file hasn't been modified in >10 min

If all guards pass, calls `precompact-handoff.py` via subprocess with `trigger: "stop"`.

**Fires on**: Stop (after every Claude response)

**State file**: `~/.claude/handoffs/.last-stop-handoff` (JSON with timestamp + session_id)

**Cost**: With 5-min cooldown, ~6-12 handoffs/hour of active work. At ~$0.01 each: $0.06-0.12/hour. Idle sessions: $0.

---

### `terminal-title.sh` — Terminal UX

Dynamic terminal tab title with state indicators, desktop notifications, and duration tracking.

**Fires on**: PreToolUse (via `on-thinking.sh` symlink), Stop (via `on-ready.sh` symlink)

| State | Indicator | Action |
|-------|-----------|--------|
| Thinking | 🔴 `project-name` | Sets tab title, records start time |
| Ready | 🟢 `project-name` | Sets tab title, plays sound, sends notification with duration |

Features:
- Session name from `customTitle` in `sessions-index.json` (set by `/rename`)
- Project name from `package.json`, `Cargo.toml`, or `pyproject.toml`
- macOS desktop notification via `terminal-notifier` (click to focus VS Code)
- Duration tracking (e.g., "Ready for input (2m 34s)")
- Sound alert (`sounds/soft-ui.mp3`)

**Requires**: `brew install terminal-notifier`

**VS Code setting** (enable dynamic tab titles):
```json
{ "terminal.integrated.tabs.title": "${sequence}" }
```

---

### `on-thinking.sh` / `on-ready.sh` — Symlinks

Both are symlinks to `terminal-title.sh`. The script detects which name it was called as (`$0`) and sets the appropriate state (🔴 or 🟢).

---

### `multi-response-prompt.py` — Alternative Responses

Add `/5x` to any message to get 5 alternative responses sampled from the tails of the probability distribution (each with p < 0.10). Useful for creative exploration.

**Fires on**: UserPromptSubmit (only when `/5x` is in the prompt)

---

### `statusline-monitor.sh` — StatusLine Passthrough

Pipes StatusLine JSON to `ccstatusline` for terminal status display. Previously handled 5%-threshold handoff triggering, now simplified since PreCompact/SessionEnd/Stop hooks handle all handoffs natively.

**Requires**: `npm install -g ccstatusline`

---

## Handoff Coverage

| Scenario | Hook | Caught? |
|----------|------|---------|
| Session renamed | Stop (propagate-rename) | Yes |
| Context window full | PreCompact | Yes |
| Ctrl+C / terminal close | SessionEnd | Yes |
| VS Code exit / restart | SessionEnd | Yes |
| Active work (rolling) | Stop (5-min) | Yes |
| Idle session | Stop | Skipped (by design) |
| SIGKILL / force quit | — | No (5-min max gap) |
| System panic / OOM | — | No (5-min max gap) |

## `settings.json` Configuration

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/multi-response-prompt.py"}
        ]
      }
    ],
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/on-ready.sh"},
          {"type": "command", "command": "~/.claude/hooks/propagate-rename.py"},
          {"type": "command", "command": "~/.claude/hooks/stop-handoff.py"}
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/precompact-handoff.py"}
        ]
      }
    ],
    "PreCompact": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/precompact-handoff.py"}
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/on-thinking.sh"}
        ]
      }
    ]
  },
  "statusLine": {
    "type": "command",
    "command": "~/.claude/hooks/statusline-monitor.sh",
    "padding": 0
  }
}
```

## Installation

```bash
# Copy hooks and sounds
cp -r hooks/* ~/.claude/hooks/
cp -r sounds/ ~/.claude/sounds/
chmod +x ~/.claude/hooks/*.py ~/.claude/hooks/*.sh

# Create symlinks (if not already present)
cd ~/.claude/hooks/
ln -sf terminal-title.sh on-thinking.sh
ln -sf terminal-title.sh on-ready.sh

# Dependencies
brew install terminal-notifier    # desktop notifications
npm install -g ccstatusline       # terminal statusline

# Set OPENROUTER_API_KEY for handoffs
export OPENROUTER_API_KEY="sk-or-..."
```

Then add the `settings.json` configuration above to `~/.claude/settings.json`.
