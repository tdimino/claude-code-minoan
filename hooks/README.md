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

Plan file written ──→ PostToolUse ─────────→ plan-rename.py (random→dated slug)
  (Write/Edit/MultiEdit on ~/.claude/plans/)

Context full ────────→ PreCompact ──────────→ precompact-handoff.py (full handoff)

Session exits ───────→ SessionEnd ──────────→ precompact-handoff.py (full handoff)
                                            → plan-cleanup-symlinks.py (remove forwarding symlinks)

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

### `terminal-title.sh` — Two-Tier Terminal Title with Repo Icons

Dynamic terminal tab title with repo-type emoji icons, two-tier naming (persistent main title + dynamic subtitle), desktop notifications, and duration tracking.

**Fires on**: PreToolUse (via `on-thinking.sh` symlink), Stop (via `on-ready.sh` symlink)

**Title format**: `STATUS REPO_ICON MAIN_TITLE: SUBTITLE`

```
🔴 🐍 claudius: Building test suite     ← thinking
🟢 ⚛️ knossot: Ready                    ← ready
🔴 🦀 bg3se-macos: Debugging init hooks
🟢 📜 Thera-Paper: Reviewing cognates
```

| Component | Source | Persistence |
|-----------|--------|-------------|
| `🔴/🟢` | Hook event (PreToolUse/Stop) | Per-event |
| Repo icon | CWD heuristics (CLAUDE.md keywords, then file detection) | Cached per CWD in `/tmp/` |
| Main title | `customTitle` via `/rename`, else `basename $CWD` | Persistent — only changes via `/rename` |
| Subtitle | Last assistant message from transcript JSONL | Updated on each Stop event |

**Repo icon detection** (priority order):

| Indicator | Emoji | Detection |
|-----------|-------|-----------|
| Soul/daimonic | 👁 | CLAUDE.md contains "soul", "daimonic", "daimon" |
| Research/ancient | 📜 | CLAUDE.md contains "research", "Minoan", "Semitic", "Linear A" |
| Game modding | 🎮 | CLAUDE.md contains "game", "BG3", "modding", "Script Extender" |
| Events/community | 🏛 | CLAUDE.md contains "event", "communit" |
| React | ⚛️ | `package.json` with `react` dep |
| Astro | 🚀 | `package.json` with `astro` dep |
| Next.js | ▲ | `package.json` with `next` dep |
| Svelte | 🔥 | `package.json` with `svelte` dep |
| Vue | 💚 | `package.json` with `vue` dep |
| JavaScript/Node | 🟨 | `package.json` (no framework match) |
| Rust | 🦀 | `Cargo.toml` |
| Python | 🐍 | `pyproject.toml`, `setup.py`, `requirements.txt` |
| Ruby | 💎 | `Gemfile` |
| Go | 🔵 | `go.mod` |
| Docker | 🐳 | `Dockerfile` (no package.json/pyproject.toml) |
| Swift | 🐦 | `Package.swift`, `.swift-version` |
| C/C++ | 🔧 | `CMakeLists.txt`, `Makefile` |
| Default | 📁 | Fallback |

Features:
- **Two-tier title**: Main title never changes unless user runs `/rename`; subtitle auto-updates from transcript
- **Repo icons**: Emoji derived from CLAUDE.md semantic keywords or project file heuristics, cached per CWD
- **Desktop notification** via `terminal-notifier` with repo icon and subtitle (click to focus VS Code)
- **Duration tracking** (e.g., "2m 34s")
- **Sound alert** (`sounds/soft-ui.mp3`)

**Requires**: `brew install terminal-notifier`

**VS Code setting** (enable dynamic tab titles):
```json
{ "terminal.integrated.tabs.title": "${sequence}" }
```

---

### `plan-rename.py` — Auto-Rename Plan Files

Renames randomly-named plan files (`tingly-humming-simon.md`) to dated slugs (`2026-02-17-auto-rename-plan-files-hook.md`). Extracts the H1 header for the slug, prepends today's date.

**Fires on**: PostToolUse (Write, Edit, MultiEdit — only when file is in `~/.claude/plans/`)

**Fast-path exits** (~1ms for non-plan files):
1. Check `file_path` is in `~/.claude/plans/`
2. Check filename matches random pattern (`adj-gerund-noun.md`)
3. Extract H1 header — skip if none yet
4. Slugify, rename, create forwarding symlink

**Symlink strategy**: After rename, creates a relative symlink from old name → new name so Claude Code can still write to the old path mid-session. Agent files sharing the same base slug are also cascaded.

**Locking**: `fcntl.flock(LOCK_NB)` prevents concurrent hook invocations from racing.

---

### `plan-cleanup-symlinks.py` — Remove Plan Forwarding Symlinks

Removes all symlinks from `~/.claude/plans/` after a session ends. Safe because once the session is over, no further writes target the old random names.

**Fires on**: SessionEnd

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
| Git command in any directory | PreToolUse/Bash (git-track) | Yes |
| Git commit result (hash) | PostToolUse/Bash (git-track-post) | Yes |
| Cross-repo session discovery | SessionEnd (git-track-rebuild) | Yes |
| Plan file auto-naming | PostToolUse/Write,Edit,MultiEdit (plan-rename) | Yes |
| Plan symlink cleanup | SessionEnd (plan-cleanup-symlinks) | Yes |
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
          {"type": "command", "command": "~/.claude/hooks/precompact-handoff.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/git-track-rebuild.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/plan-cleanup-symlinks.py", "timeout": 5000}
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
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/git-track.sh"}
        ]
      },
      {
        "matcher": "*",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/on-thinking.sh"}
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/git-track-post.sh"}
        ]
      },
      {
        "matcher": "Write",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/plan-rename.py", "timeout": 5000}
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/plan-rename.py", "timeout": 5000}
        ]
      },
      {
        "matcher": "MultiEdit",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/plan-rename.py", "timeout": 5000}
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
