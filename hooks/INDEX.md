# Hooks Index

*27 hooks in `~/.claude/hooks/` — 15 bound in settings.json, 5 statusline widgets, 7 standalone/legacy*

## Event Bindings (settings.json)

### SessionStart
| Hook | Description |
|------|-------------|
| `soul-activate.py` | Register session in soul registry, set ensouled state |

### UserPromptSubmit
| Hook | Description |
|------|-------------|
| `multi-response-prompt.py` | Inject multi-response sampling instructions into prompts |
| `slack_inbox_hook.py` *(skill)* | Check Slack inbox for unread messages |

### Stop
| Hook | Description |
|------|-------------|
| `on-ready.sh` → `terminal-title.sh` | Update terminal title with ready state icon |
| `propagate-rename.py` | Sync `customTitle` from sessions-index.json to terminal title |
| `stop-handoff.py` | Throttled handoff (5min cooldown, 10min idle gate) + session tag inference |
| `slack-stop-hook.py` | Process pending Slack messages on stop |
| `plan-rename.py stop` | Rename random-named plans to dated slugs with origin-aware dedup, symlink for write-through, open in dabarat |

### SessionEnd
| Hook | Description |
|------|-------------|
| `precompact-handoff.py` | Generate handoff YAML via OpenRouter (Gemini Flash Lite) |
| `soul-deregister.py` | Remove session from soul registry |
| `git-track-rebuild.py` | Rebuild git tracking state from accumulated diffs |
| `plan-rename.py session_end` | Final cleanup of forwarding symlinks, prune stale origins |

### PreCompact
| Hook | Description |
|------|-------------|
| `precompact-handoff.py` | Same handoff generation (shared with SessionEnd) |

### PreToolUse
| Hook | Description |
|------|-------------|
| `git-track.sh` *(Bash)* | Snapshot git state before Bash command execution |
| `block-websearch.sh` *(WebSearch)* | Block WebSearch — redirect to exa-search skill |
| `block-webfetch.sh` *(WebFetch)* | Block WebFetch — redirect to Firecrawl skill |
| `on-thinking.sh` → `terminal-title.sh` *(\*)* | Update terminal title with thinking state icon |

### PostToolUse
| Hook | Description |
|------|-------------|
| `git-track-post.sh` *(Bash)* | Diff git state after Bash command, log file changes |

## StatusLine Widgets

Called by `statusline-monitor.sh` (the StatusLine command in settings.json) or ccstatusline config.

| Widget | Description |
|--------|-------------|
| `statusline-monitor.sh` | Main StatusLine wrapper — hand-built Line 1 (ANSI passthrough) + delegates Lines 2-3 to ccstatusline |
| `context-bar.sh` | Dynamic context window usage bar with gradient coloring |
| `ensouled-status.sh` | Display `𓂀 ensouled` / `mortal` based on soul registry state |
| `soul-name.sh` | Display active soul name (e.g., "Claudius") |
| `session-tags-display.sh` | Display 3 rainbow-pastel session tags from sidecar JSON |

## Standalone / Subprocess

Not directly bound in settings.json but called by other hooks.

| Hook | Description |
|--------|-------------|
| `session-tags-infer.py` | Infer session tags via OpenRouter, write sidecar JSON, auto-rename session |
| `soul-registry.py` | Soul registry daemon — heartbeat, query, cleanup (called by stop-handoff, soul-activate) |

## Legacy / Utility

| Hook | Description |
|--------|-------------|
| `debug-hook-input.sh` | Debug script — dumps hook JSON input to stderr |
| `terminal-title.sh` | Two-tier terminal title with repo icons (target of on-ready.sh and on-thinking.sh symlinks) |
| `session-name.sh` | Extract session slug from transcript path |
| `crab-model.sh` | Output model name with crab emoji for statusline |
| `plan-cleanup-symlinks.py` | Standalone symlink cleanup (superseded by plan-rename.py session_end) |
| `update-agent-docs.sh` | Background update of agent_docs/active-projects.md |

## Architecture

```
SessionStart ─→ soul-activate.py ─→ soul-registry.py
                                          ↑
UserPromptSubmit ─→ multi-response-prompt.py    │ heartbeat
                 ─→ slack_inbox_hook.py         │
                                                │
PreToolUse ─→ git-track.sh (Bash)               │
           ─→ block-websearch.sh (WebSearch)    │
           ─→ block-webfetch.sh (WebFetch)      │
           ─→ terminal-title.sh (*)             │
                                                │
PostToolUse ─→ git-track-post.sh (Bash)         │
                                                │
Stop ─→ terminal-title.sh                       │
     ─→ propagate-rename.py                     │
     ─→ stop-handoff.py ──→ precompact-handoff.py (OpenRouter)
     │                   ──→ session-tags-infer.py (OpenRouter, fire-and-forget)
     │                   ──→ soul-registry.py heartbeat
     ─→ slack-stop-hook.py
     ─→ plan-rename.py stop ──→ dabarat (fire-and-forget)
                                                │
PreCompact ─→ precompact-handoff.py             │
                                                │
SessionEnd ─→ precompact-handoff.py             │
           ─→ soul-deregister.py ─→ soul-registry.py
           ─→ git-track-rebuild.py
           ─→ plan-rename.py session_end

StatusLine ─→ statusline-monitor.sh
              ├─ context-bar.sh (Line 1, hand-built)
              ├─ ensouled-status.sh (ccstatusline Line 2)
              ├─ soul-name.sh (ccstatusline Line 2)
              ├─ session-tags-display.sh (ccstatusline Line 2)
              └─ ccstatusline (Lines 2-3: timers)
```
