# Claude Code Hooks

Scripts that run in response to Claude Code lifecycle events. Together they provide terminal UX, session handoffs, and crash resilience.

## How It Works

```
Claude Code Lifecycle                          What Fires
────────────────────                          ──────────────────────────────────
Session starts ──────→ SessionStart ────────→ soul-activate.py (register soul daemon)

User types message ──→ UserPromptSubmit ────→ multi-response-prompt.py (/5x)
                                            → slack_inbox_hook.py (check Slack DMs)

Claude uses a tool ──→ PreToolUse ──────────→ on-thinking.sh (🔴 tab title)
                                            → block-websearch.sh / block-webfetch.sh (guards)

Claude responds ─────→ Stop ────────────────→ on-ready.sh (🟢 tab + sound + notification)
                                            → propagate-rename.py (sync /rename → caches)
                                            → stop-handoff.py (checkpoint every 5 min)
                                            → session-tags-infer.py (AI-powered session tags)
                                            → slack-stop-hook.py (notify Slack channels)
                                            → plan-rename.py (random→dated slug + dabarat)

Plan/md file written → PostToolUse ────────→ plan-rename.py (random→dated slug + dabarat)
  (Write on ~/.claude/plans/)              → dabarat-open.py (auto-open new .md in preview)
                                           → plan-session-rename.py (auto-title session from H1)

Frontend file edit ──→ PostToolUse ────────→ auto-screenshot.py (CDP screenshot after HMR)
  (Write/Edit on .tsx/.jsx/.css/.html)

Any code file edit ─→ PostToolUse ────────→ lint-on-write.py (ESLint/Clippy/Ruff + custom rules)
  (Write/Edit on .ts/.tsx/.js/.rs/.py/.css)    → custom-lint.sh (grep-based project conventions)

Context full ────────→ PreCompact ──────────→ precompact-handoff.py (full handoff)

Session exits ───────→ SessionEnd ──────────→ precompact-handoff.py (full handoff)
                                            → soul-deregister.py (unregister soul daemon)
                                            → git-track-rebuild.py (cross-repo session index)
                                            → plan-rename.py (cleanup symlinks)

Every turn ──────────→ StatusLine ──────────→ statusline-monitor.sh (ANSI context bar)
                                              ├─ session-name.sh (session title)
                                              ├─ session-tags-display.sh (AI tags)
                                              ├─ context-bar.sh (gradient usage bar)
                                              ├─ soul-name.sh (active soul)
                                              ├─ ensouled-status.sh (daemon indicator)
                                              └─ crab-model.sh (model display)
```

## Hooks

### `precompact-handoff.py` — Session Handoff

The core of the handoff system. Reads the transcript JSONL, summarizes it via OpenRouter (Qwen 3 235B MoE, ~$0.008/call), and writes a structured YAML to `~/.claude/handoffs/{session_id}.yaml`. See [HANDOFF-MODEL-EVAL.md](HANDOFF-MODEL-EVAL.md) for the model comparison that led to this choice.

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

Propagates session titles from `session-registry.json` (our self-maintained index) to `session-summaries.json` (global cache) and triggers `active-projects.md` rebuild.

**Fires on**: Stop (after every Claude response)

**Data flow**:
1. Read `session_id` and `transcript_path` from hook stdin JSON
2. Look up `title` in `~/.claude/session-registry.json`
3. Compare against `title` in `~/.claude/session-summaries.json`
4. If mismatch: update cache, atomic write, fire `update-active-projects.py` in background
5. If already in sync or no title: fast path exit (~20ms)

**Why it exists**: `session-tags-infer.py` writes titles to `session-registry.json`. Without this hook, `session-summaries.json` and `active-projects.md` never learn about the title.

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
🔴 🐍 claudicle: Building test suite     ← thinking
🟢 ⚛️ knossot: Ready                    ← ready
🔴 🦀 bg3se-macos: Debugging init hooks
🟢 📜 Thera-Paper: Reviewing cognates
```

| Component | Source | Persistence |
|-----------|--------|-------------|
| `🔴/🟢` | Hook event (PreToolUse/Stop) | Per-event |
| Repo icon | CWD heuristics (CLAUDE.md keywords, then file detection) | Cached per CWD in `/tmp/` |
| Main title | `title` from session-registry.json, else `basename $CWD` | Persistent — set by session-tags-infer.py |
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

**Fires on**: Stop (rename + symlink), SessionEnd (cleanup symlinks + prune stale origins)

**Origin tracking**: `.plan-origins.json` in `~/.claude/plans/` maps random names to their dated counterparts, preventing duplicates when the same plan is reopened across sessions. Seeded from existing symlinks on first run.

**Three-phase rename** (`rename_file()`):
1. **Phase A — Check origins**: If the random name was previously renamed, update the existing dated file (re-rename if H1 changed, merge if unchanged)
2. **Phase B — Content identity**: If no origin exists but a collision occurs, compare MD5 and H1 to detect same-plan duplicates. Same plan → merge via `os.replace()`. Different plan → increment suffix (`-2`, `-3`)
3. **Phase C — Execute**: `os.replace()` (atomic overwrite), create forwarding symlink, record origin

**Symlink strategy**: After rename, creates a relative symlink from old name → new name so Claude Code can still write to the old path mid-session.

**Locking**: `fcntl.flock(LOCK_NB)` prevents concurrent hook invocations from racing.

---

### `plan-session-rename.py` — Auto-Rename Session from Plan Title

When a plan file is written to `~/.claude/plans/`, extracts the H1 header and writes a `.pending-title` breadcrumb for `session-tags-infer.py` to pick up on the next Stop event. No LLM call—pure local, ~10ms.

**Fires on**: PostToolUse/Write (only when file is in `~/.claude/plans/`)

**How it works**:
1. Guard: only acts if `file_path` is inside `~/.claude/plans/`
2. Extract H1 from `tool_input.content`, strip "Plan: " prefix if present
3. Write a `.pending-title` breadcrumb to `~/.claude/session-tags/`
4. On next Stop, `session-tags-infer.py` reads the breadcrumb and writes the title to `session-registry.json`

**Interplay with `session-tags-infer.py`**: Pending breadcrumbs are checked before inference, so sessions get plan-derived titles even if the LLM server is unavailable.

**Cost**: Zero. No LLM calls, no network.

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

### `statusline-monitor.sh` — StatusLine Wrapper

Builds line 1 with ANSI true color passthrough (session name, model, gradient context bar, git branch), then pipes to `ccstatusline` for lines 2+. Six statusline widget scripts feed into it:

| Widget | What it shows |
|--------|---------------|
| `session-name.sh` | Session title (from `/rename` or auto-generated) |
| `session-tags-display.sh` | AI-generated session tags (3 tags, `·`-separated) |
| `context-bar.sh` | Gradient context usage bar (green→yellow→red) |
| `crab-model.sh` | Active model name |
| `soul-name.sh` | Active soul daemon name |
| `ensouled-status.sh` | Soul daemon status indicator |

**Requires**: `npm install -g ccstatusline`

---

### `session-tags-infer.py` — AI-Powered Session Tagging & Summaries

Reads the session transcript and generates 3 descriptive tags (3-5 words each) plus a 2-4 sentence summary of what happened. Tags update as the session evolves—early tags might be "project setup and configuration" while later tags shift to "debugging authentication middleware".

**Fires on**: Stop (via `stop-handoff.py`, fire-and-forget subprocess)

**How it works**:
1. Reads the last ~4000 chars of the transcript JSONL
2. Sends to Gemini Flash Lite via OpenRouter (~$0.004/call)
3. Returns 3 `display_tags`, up to 10 `tags`, a `title`, and a `summary`
4. Writes to `~/.claude/session-tags/{session_id}.json` (sidecar for statusline)
5. Updates `~/.claude/session-registry.json` (consolidated session index)
6. `session-tags-display.sh` reads sidecar for statusline display
7. Pushes `topic` and `summary` to the soul registry via `soul-registry.py heartbeat`

**Cooldown**: 5 minutes per session (shared with handoff cooldown). Tags don't re-infer if nothing has changed.

**Cost**: ~$0.004/call, ~$0.38/day max at continuous use.

**Display**: Tags appear in the statusline separated by `·` (middle dot) in muted lavender-gray.

```
kothar soul engine · dabarat live preview · session tag inference
```

---

### `dabarat-open.py` — Auto-Open Markdown in Live Preview

Companion hook for [Dabarat](https://github.com/tdimino/dabarat) (`md_preview_and_annotate`)—a zero-dependency Python markdown previewer with annotations, tagging, command palette, and 6 Catppuccin themes. This hook bridges Claude Code's file writes to Dabarat's live preview, so every `.md` file Claude touches appears instantly in the browser.

Fires on every `.md` write (create or edit). If Dabarat is already running, adds a tab via `/api/add` and prints the result to stdout. If not running, launches a new window. Messages are printed to stdout so they appear as visible hook feedback in Claude Code.

**Fires on**: PostToolUse/Write (all `.md` file writes)

**Watched directories**:
- `~/.claude/plans/`
- `~/.claude/hooks/`
- `~/.claude/agent_docs/`
- `~/.claude/commands/`
- `~/.claude/scripts/`
- Current project working directory

**Skips**: `INDEX.md`, `.annotations.` files, `session-registry`

**Why it exists**: When Claude writes or updates a plan, dossier, or documentation file, you instantly see the rendered markdown in a browser tab without switching context.

---

### `auto-screenshot.py` — Visual Dev Loop Screenshot

Automatically takes a Chrome DevTools Protocol screenshot after every frontend file edit, returning the image path as `additionalContext` so the agent can see what the page looks like after HMR settles. Part of the Visual Dev Loop pattern: portless dev server + Vite/Next.js HMR + CDP screenshot = closed feedback loop.

**Fires on**: PostToolUse/Write, PostToolUse/Edit (only `.tsx`, `.jsx`, `.css`, `.html`, `.svelte`, `.vue`, `.scss`)

**How it works**:
1. Guard: file extension must be a frontend type
2. Guard: `portless list` must show at least one active dev server
3. Guard: `cdp.mjs list` must find a Chrome tab matching `localhost`
4. Wait 1.5s for HMR to settle
5. `cdp.mjs shot <target> .visual-feedback/latest.png`
6. Return screenshot path as `additionalContext`

**Requires**: [chrome-cdp skill](../skills/chrome-cdp/) (`cdp.mjs`), Chrome with remote debugging enabled, `portless`

**Cost**: Zero. No LLM calls — pure local CDP + subprocess.

**Inspired by**: [Danielle Fong's vibecoding recommendations](https://x.com/DanielleFong/status/2033244721427140890) on hot-reloads + AI visual feedback loops.

---

### `lint-on-write.py` — Linter-Directed Agent Loop

Runs linters after every file edit and feeds violations back as `additionalContext`, enabling the agent to self-correct against machine-enforced rules rather than prose conventions. Implements the [Factory.ai "Using Linters to Direct Agents"](https://factory.ai/news/using-linters-to-direct-agents) pattern.

**Fires on**: PostToolUse/Write, PostToolUse/Edit (`.ts`, `.tsx`, `.js`, `.jsx`, `.rs`, `.py`, `.css`, `.astro`)

**How it works**:
1. Guard: file extension must be a lintable code type (skips `.md`, `.json`, `.yaml`, etc.)
2. Guard: 5-second per-file cooldown prevents rapid re-fires during multi-edit sequences
3. Walk up from edited file looking for `.claude/lint-rules.json` (config-driven)
4. Dispatch to standard linter declared in config (`"linter": "eslint"` / `"clippy"` / `"ruff"`)
5. Run custom grep rules from the config's `"rules"` array
6. Cap at 10 violations, return as `additionalContext`
7. Fallback: if no config file, auto-detect linter from extension (no custom rules)

#### Opting In: `.claude/lint-rules.json`

Any repo can opt into the lint-on-write system by creating `.claude/lint-rules.json` at the project root:

```json
{
  "linter": "eslint",
  "rules": [
    {
      "pattern": "#[0-9a-fA-F]{3,8}",
      "message": "Hardcoded hex — use CSS variable instead",
      "extensions": ["tsx", "jsx", "css"],
      "exclude_patterns": ["^\\s*//", "import "]
    },
    {
      "pattern": "from ['\"]lodash",
      "message": "Import from lodash — use native JS or lodash-es",
      "extensions": ["ts", "tsx"]
    },
    {
      "pattern": "scroll-behavior:\\s*smooth",
      "message": "scroll-behavior: smooth requires prefers-reduced-motion gate",
      "extensions": ["css"],
      "require_absent": "prefers-reduced-motion"
    }
  ]
}
```

#### Config Reference

| Field | Type | Description |
|-------|------|-------------|
| `linter` | `string` | Standard linter: `"eslint"`, `"clippy"`, `"ruff"`, or omit for custom rules only |
| `linter_options` | `object` | Optional. `path_prefix` for PATH override (e.g. `"/usr/bin"` for Cargo cc shadow workaround) |
| `rules` | `array` | Custom grep-based convention rules (see below) |

#### Rule Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `pattern` | `string` | Yes | ERE regex passed to `grep -En` |
| `message` | `string` | Yes | Violation message shown to the agent |
| `extensions` | `string[]` | No | File extensions to check (e.g. `["tsx", "css"]`). Omit to match all |
| `exclude_patterns` | `string[]` | No | Regex patterns — lines matching any of these are filtered out |
| `exclude_paths` | `string[]` | No | Glob patterns — files matching any of these are skipped (e.g. `"*/test/*"`) |
| `require_absent` | `string` | No | Only fire if this string is NOT present anywhere in the file |

**Output** (JSON on stdout, only when violations found):
```json
{
  "additionalContext": "Lint violations in Sparkline.tsx (3 issues):\n  1. [eslint/error] no-restricted-imports: ...\n  2. [custom] Hardcoded hex — use @theme CSS variable\n\nFix these violations before proceeding."
}
```

**Cooldown**: `/tmp/lint-on-write-cooldown.json` — tracks last lint time per file, prunes entries >60s old, atomic writes via `os.replace()`.

**Timeouts**: 8s subprocess timeout (covers clippy incremental builds), 10s settings.json timeout.

**Cost**: Zero. No LLM calls — pure local linter subprocess invocations.

**Legacy**: `custom-lint.sh` still exists as a standalone grep tool for manual testing but is no longer the primary mechanism. Config files drive everything.

**Inspired by**: [Factory.ai "Using Linters to Direct Agents"](https://factory.ai/news/using-linters-to-direct-agents) (Sep 2025) and ["Lint Against the Machine"](https://medium.com/@montes.makes/lint-against-the-machine-a-field-guide-to-catching-ai-coding-agent-anti-patterns-3c4ef7baeb9e) (Mar 2026).

---

### `soul-activate.py` / `soul-deregister.py` / `soul-registry.py` — Soul Daemon Lifecycle

Manages registration of [Claudicle](https://github.com/tdimino/claudicle) soul daemons—persistent AI personalities with identity, memory, and cognitive pipelines that survive across sessions.

| Hook | Event | What it does |
|------|-------|-------------|
| `soul-activate.py` | SessionStart | Registers the session with the soul daemon, loads personality from `soul.md`. Checks for active marker file or `CLAUDICLE_SOUL`/`CLAUDIUS_SOUL` env vars. |
| `soul-deregister.py` | SessionEnd | Unregisters the session, cleans up daemon state |
| `soul-registry.py` | Library | Shared registry logic: heartbeat (with `--topic` and `--summary`), lookup, multi-session coordination. `list --md` renders session summaries below the table. |

Claudicle's 4-layer architecture (Identity, Cognition, Memory, Channels) powers souls like Kothar—the Ugaritic craftsman god who serves as a coding companion. `ensouled-status.sh` and `soul-name.sh` display the active soul in the statusline. See the [Claudicle repo](https://github.com/tdimino/claudicle) for the full framework.

---

### `slack-stop-hook.py` — Slack Notifications

Posts session activity notifications to configured Slack channels when Claude completes a response. Useful for monitoring long-running sessions from mobile.

**Fires on**: Stop

---

### `block-websearch.sh` / `block-webfetch.sh` — Tool Guards

PreToolUse guards that intercept WebSearch and WebFetch calls, allowing you to redirect to preferred tools (Firecrawl, Exa, Jina) or block unwanted web access.

**Fires on**: PreToolUse (matcher: WebSearch, WebFetch)

---

## Handoff Coverage

| Scenario | Hook | Caught? |
|----------|------|---------|
| Session renamed | Stop (propagate-rename) | Yes |
| Context window full | PreCompact | Yes |
| Ctrl+C / terminal close | SessionEnd | Yes |
| VS Code exit / restart | SessionEnd | Yes |
| Active work (rolling) | Stop (5-min) | Yes |
| Session topic tracking | Stop (session-tags-infer) | Yes |
| Git command in any directory | PreToolUse/Bash (git-track) | Yes |
| Git commit result (hash) | PostToolUse/Bash (git-track-post) | Yes |
| Cross-repo session discovery | SessionEnd (git-track-rebuild) | Yes |
| Plan file auto-naming | Stop (plan-rename) | Yes |
| Plan symlink cleanup | SessionEnd (plan-rename) | Yes |
| New .md file created | PostToolUse/Write (dabarat-open) | Yes |
| Session auto-title from plan | PostToolUse/Write (plan-session-rename) | Yes |
| Frontend file visual feedback | PostToolUse/Write+Edit (auto-screenshot) | Yes |
| Soul daemon registration | SessionStart (soul-activate) | Yes |
| Soul daemon cleanup | SessionEnd (soul-deregister) | Yes |
| Slack channel notification | Stop (slack-stop-hook) | Yes |
| Idle session | Stop | Skipped (by design) |
| SIGKILL / force quit | — | No (5-min max gap) |
| System panic / OOM | — | No (5-min max gap) |

## `settings.json` Configuration

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/soul-activate.py"}
        ]
      }
    ],
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
          {"type": "command", "command": "~/.claude/hooks/stop-handoff.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/slack-stop-hook.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/plan-rename.py stop", "timeout": 10000}
        ]
      }
    ],
    "SessionEnd": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/precompact-handoff.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/soul-deregister.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/git-track-rebuild.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/plan-rename.py session_end", "timeout": 10000}
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
        "matcher": "WebSearch",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/block-websearch.sh"}
        ]
      },
      {
        "matcher": "WebFetch",
        "hooks": [
          {"type": "command", "command": "~/.claude/hooks/block-webfetch.sh"}
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
          {"type": "command", "command": "python3 ~/.claude/hooks/dabarat-open.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/plan-session-rename.py", "timeout": 5000},
          {"type": "command", "command": "python3 ~/.claude/hooks/auto-screenshot.py", "timeout": 15000},
          {"type": "command", "command": "python3 ~/.claude/hooks/lint-on-write.py", "timeout": 10000}
        ]
      },
      {
        "matcher": "Edit",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/auto-screenshot.py", "timeout": 15000},
          {"type": "command", "command": "python3 ~/.claude/hooks/lint-on-write.py", "timeout": 10000}
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
