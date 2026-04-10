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
                                            → image-optimize.py (resize + JPEG convert)

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

Image file read ────→ PostToolUse ────────→ image-budget.py (token budget tracking + warnings)
  (Read on image files)                      depends on image-optimize.py (PreToolUse) for state

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

### `image-optimize.py` — Screenshot Token Optimizer

PreToolUse guard that intercepts image file reads, optimizes oversized images, and injects token estimates into `additionalContext`. Addresses the fact that Claude's vision API charges `(width × height) / 750` tokens per image, auto-resizes at 1568px long edge, and silently caps resolution to 2000×2000px when >20 images are in a request.

**Fires on**: PreToolUse/Read (only image files: `.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`, `.bmp`, `.tiff`, `.heic`)

**How it works**:
1. Guard: file extension must be an image type
2. Guard: file must exist and not already be in the cache directory
3. Get dimensions via `/usr/bin/sips` (macOS native, ~50ms)
4. Decision matrix:
   - Long edge > 1568px → resize + convert to JPEG
   - PNG > 500KB → convert to JPEG (no resize)
   - Short edge < 200px → passthrough only (optimization degrades quality at this size)
   - Otherwise → passthrough with token estimate only
5. Optimized copies go to `~/.claude/.screenshot-cache/opt-{hash}.jpg` (keyed by path + mtime, idempotent)
6. Updates session state file for `image-budget.py` to read

**Output** (JSON on stdout):
```json
{
  "additionalContext": "[screenshot.png: optimized (resized 2560x1600 -> 1568x980, PNG -> JPEG, 7400KB -> 280KB on the wire), ~2043 tokens, 96% smaller payload]\nOptimized copy: ~/.claude/.screenshot-cache/opt-a1b2c3d4.jpg\nRead the optimized file for faster time-to-first-token."
}
```

**What this actually saves** — token count is **unchanged**. Anthropic resizes server-side regardless (`tokens = (w × h) / 750`, capped at 1568px long edge). The real wins are:

- **Upload bandwidth**: A 7.4MB Retina PNG drops to ~280KB JPEG (96% smaller on the wire). Across 15 screenshots in a session that's ~110MB of avoided transfer.
- **Time-to-first-token**: Per [Anthropic's vision docs](https://docs.anthropic.com/en/docs/build-with-claude/vision): *"If your input image is too large and needs to be resized, it increases latency of time-to-first-token, with no benefit to output quality."*
- **Session resilience**: The >20 images / 5MB base64 / 20MB request limits are all byte-bound. Client-side resize is the difference between a working session and one that's permanently bricked (see [#34566](https://github.com/anthropics/claude-code/issues/34566)).
- **Pre-context defense**: Claude Code's internal `sharp` pipeline can fail silently and pass the raw unresized image into context. This hook intercepts *before* that pipeline runs.

**Key numbers**:
- Token formula: `(width × height) / 750` (pixel-based, format-independent)
- 1568px max edge = Anthropic's server-side resize target (more aggressive than Claude Code's 2000px client target)
- PNG → JPEG at quality 80 typically saves 60–80% file size (varies by image content)
- Typical Retina screenshot: 2560×1600 (~7.4MB PNG) → 1568×980 (~280KB JPEG), same token count

**Cost**: Zero. No LLM calls — pure local `sips` subprocess.

#### Why not rely on Claude Code's built-in resize?

Claude Code does resize images internally using [`sharp`/libvips](https://sharp.pixelplumbing.com/) with a 2000×2000px target ([#34566](https://github.com/anthropics/claude-code/issues/34566) confirms `WB=2000, ZB=2000`, still current as of v2.1.97). The [v2.1.97 changelog](https://github.com/anthropics/claude-code/blob/main/CHANGELOG.md) unified pasted/attached image compression to match the Read-tool budget — a real improvement.

So why bother with a client-side hook? **Several failure modes the built-in pipeline does not cover:**

- **[#34566](https://github.com/anthropics/claude-code/issues/34566) — Sharp silently fails on oversized images.** When `sharp` errors out (missing native module, Vips error, etc.), the *raw unresized image* passes into context. The session is then permanently bricked because the oversized bytes are re-sent on every turn. Our hook intercepts *before* `sharp` runs, so failures are survivable.
- **[#39194](https://github.com/anthropics/claude-code/issues/39194) — `sharp` native module missing on darwin-arm64** in the VSCode extension. Our hook uses `sips` (always present on macOS) and has no native-module dependency.
- **[#31208](https://github.com/anthropics/claude-code/issues/31208) — MCP `ImageContent` treated as text** (10–20x token waste, 15,000–25,000 tokens per image instead of ~1,600). Our `image-budget.py` tracks MCP screenshots against the same 20-image budget so you get a warning before the session bricks, even though the hook can't fix the root cause.
- **[#37418](https://github.com/anthropics/claude-code/issues/37418) — Session JSONL grows unboundedly from MCP screenshots** (117 screenshots → 64MB session file). Byte-bound, not token-bound.
- **[#27869](https://github.com/anthropics/claude-code/issues/27869) — Chrome MCP screenshots drain 17% of a Max plan in five turns.** Budget tracking catches this before it compounds.
- **[#42256](https://github.com/anthropics/claude-code/issues/42256) — Oversized images re-sent every turn.** Pre-resize caps the per-turn re-send cost at the 1568px optimum.

**The critical point:** the failure modes that brick sessions are **byte-bound, not token-bound**. The 5MB base64 per-image limit, the 20MB request size limit, and the 20-images-before-2000×2000px-cap are all about bytes on the wire. Server-side resize can't save you from any of them — the oversized bytes have to travel first. Pre-resizing client-side is the difference between a working session and one that's permanently broken.

Our 1568px target is also more aggressive than Claude Code's 2000px target — 1568 matches [Anthropic's documented server-side resize target](https://docs.anthropic.com/en/docs/build-with-claude/vision) exactly, so we avoid two resize passes on the same image.

---

### `image-budget.py` — Image Token Budget Tracker

PostToolUse hook that tracks cumulative image token consumption per session and warns when approaching dangerous thresholds. The critical threshold is 20 images — the API silently switches to a 2000×2000px resolution limit that can permanently brick sessions.

**Fires on**: PostToolUse/Read (image files), PostToolUse/mcp__computer-use__screenshot, PostToolUse/mcp__claude-in-chrome__screenshot

**How it works**:
1. For **Read**: reads session state written by `image-optimize.py` (PreToolUse)
2. For **MCP screenshots**: directly increments the session state (no PreToolUse companion needed). Estimates ~2,000 tokens per MCP screenshot (API auto-resizes to 1568px max edge).
3. Checks cumulative image count and token total against thresholds
4. Emits `additionalContext` warnings when thresholds are crossed

**Note**: `additionalContext` is broken for MCP tools (anthropics/claude-code#24788). MCP screenshot warnings are tracked in session state but only surface to the agent on the next Read tool call.

**Thresholds**:

| Level | Trigger | Message |
|-------|---------|---------|
| Silent | < 15 images, < 20K tokens | Track only |
| WARNING | ≥ 15 images OR ≥ 20K tokens | Advises caution, suggests text descriptions |
| CRITICAL | ≥ 20 images OR ≥ 40K tokens | Warns of API resolution cap, recommends `/compact` |

**Cooldown**: 5 images between warnings (prevents context spam).

**State file**: `~/.claude/.screenshot-cache/session-state.json` (shared with `image-optimize.py`)

**Cost**: Zero. Pure local file I/O.

---

### `subagent-spawn-log.py` / `subagent-stop-log.py` — Subagent Lifecycle Logger

Pure observability hooks for subagent spawning and completion. Built after a usage audit revealed 10,546 subagents spawned in 14 days with extreme outliers (one session spawned 466). The audit also found that **40% of subagents had at least one tool error** — a failure mode that was previously invisible.

Both hooks are async (`async: true`) — they never block the agentic loop. They write JSONL entries to `~/.claude/agent-spawn.log`.

**Fires on**:
- `subagent-spawn-log.py` → SubagentStart (every spawn)
- `subagent-stop-log.py` → SubagentStop (every completion)

#### What gets captured

**Start entries** include a per-session counter (atomic, fcntl-locked, self-expiring after 6 hours), `agent_type`, `task_preview`, and `cwd`. The counter answers "how many subagents has this session spawned so far?" — critical for spotting runaway sessions before they balloon.

**Stop entries** include `last_message_chars`, `total_output_tokens`, `n_tool_calls`, `n_tool_errors`, and an `issues` array with up to 7 failure flags:

| Flag | Trigger |
|------|---------|
| `empty_output` | `last_assistant_message` is empty |
| `tiny_output` | `last_assistant_message` < 100 chars |
| `no_assistant_message` | Field missing entirely |
| `max_tokens_truncation` | Subagent transcript ended with `stop_reason: "max_tokens"` (hit the 32K subagent output cap) |
| `output_at_cap` | Aggregate `output_tokens` ≥ 30,000 (near the cap) |
| `high_tool_error_rate` | >50% of tool calls returned `is_error` (≥4 calls) |
| `transcript_unreadable` | Couldn't open `agent_transcript_path` (race condition with JSONL flush) |

**Defensive field reads**: Both hooks fall back through `agent_type` → `subagent_type` → `subagent_name` and `agent_id` → `subagent_id` to survive Claude Code field-name drift across versions. The pattern matches `soul-subagent-inject.py`.

**Loop guard**: `subagent-stop-log.py` reads `stop_hook_active` and skips logging if true, preventing recursive hook firings.

#### Tool error detection schema

Tool errors live in user messages with content blocks:
```json
{"type": "user", "message": {"content": [
  {"type": "tool_result", "is_error": true, "tool_use_id": "toolu_...",
   "content": "<tool_use_error>InputValidationError: ..."}
]}}
```

The hook walks the subagent's transcript JSONL, counts every `tool_result` block, and increments `n_tool_errors` whenever `is_error` is `true`. Common causes seen in real transcripts: parameter validation failures, file-not-found, sibling-tool-errored cascades.

#### Triage queries

```bash
# All flagged subagents (excluding the benign transcript_unreadable)
jq 'select((.issues - ["transcript_unreadable"]) | length > 0)' ~/.claude/agent-spawn.log

# Tool error rate distribution by agent type
jq -r 'select(.event=="stop" and .n_tool_calls>0) |
  "\(.n_tool_errors)/\(.n_tool_calls) \(.agent_type)"' ~/.claude/agent-spawn.log \
  | sort | uniq -c | sort -rn

# Sessions ranked by spawn count
jq -r 'select(.event=="start") | "\(.session_id) \(.session_count)"' ~/.claude/agent-spawn.log \
  | awk '!seen[$1] || $2 > seen[$1] {seen[$1]=$2} END {for (s in seen) print seen[s], s}' \
  | sort -rn | head
```

#### Storage and privacy

~250 bytes per entry. At ~750 spawns/day, ~190 KB/day, ~5.5 MB/month. The log contains task descriptions (max 120 chars per `task_preview` and `last_message_preview`). Stays local — exclude from any backup/sync repos.

#### Wiring

```json
{
  "SubagentStart": [{
    "matcher": "",
    "hooks": [
      {"type": "command", "command": "python3 ~/.claude/hooks/soul-subagent-inject.py"},
      {"type": "command", "command": "python3 ~/.claude/hooks/mycelium-subagent.py"},
      {"type": "command", "command": "python3 ~/.claude/hooks/subagent-spawn-log.py", "async": true}
    ]
  }],
  "SubagentStop": [{
    "matcher": "",
    "hooks": [
      {"type": "command", "command": "python3 ~/.claude/hooks/subagent-stop-log.py", "async": true}
    ]
  }]
}
```

**Counter file**: `/tmp/claude-subagent-count-{session_id}` (self-expires after 6h)
**Log file**: `~/.claude/agent-spawn.log` (JSONL, append-only)
**Cost**: Zero. Pure local file I/O.

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
| Subagent spawn count per session | SubagentStart (subagent-spawn-log) | Yes |
| Subagent output truncation (32K cap) | SubagentStop (subagent-stop-log) | Yes |
| Subagent tool error rate | SubagentStop (subagent-stop-log) | Yes |
| Image read optimization | PreToolUse/Read (image-optimize) | Yes |
| Image token budget tracking | PostToolUse/Read (image-budget) | Yes |
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
    "SubagentStart": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/soul-subagent-inject.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/mycelium-subagent.py"},
          {"type": "command", "command": "python3 ~/.claude/hooks/subagent-spawn-log.py", "async": true}
        ]
      }
    ],
    "SubagentStop": [
      {
        "matcher": "",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/subagent-stop-log.py", "async": true}
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
        "matcher": "Read",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/image-optimize.py", "timeout": 8000}
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
      },
      {
        "matcher": "Read",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/image-budget.py", "timeout": 5000}
        ]
      },
      {
        "matcher": "mcp__computer-use__screenshot",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/image-budget.py", "timeout": 5000}
        ]
      },
      {
        "matcher": "mcp__claude-in-chrome__screenshot",
        "hooks": [
          {"type": "command", "command": "python3 ~/.claude/hooks/image-budget.py", "timeout": 5000}
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
