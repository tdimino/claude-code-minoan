# Hooks Index

*38 hooks in `~/.claude/hooks/` — 27 bound in settings.json, 4 statusline-only widgets, 1 standalone/subprocess, 6 legacy/utility*

## Event Bindings (settings.json)

### SessionStart (3 matchers)
| Hook | Matcher | Description |
|------|---------|-------------|
| `soul-activate.py` | `startup` | Register session in soul registry, write CLAUDE_ENV_FILE, inject soul identity when ensouled |
| `soul-reactivate-compact.py` | `compact` | Re-inject condensed soul + handoff YAML after context compaction |
| `soul-activate-resume.py` | `resume` | Re-inject full soul + session handoff when resuming via `claude --resume` |

### UserPromptSubmit
| Hook | Description |
|------|-------------|
| `multi-response-prompt.py` | Inject multi-response sampling instructions into prompts |
| `slack_inbox_hook.py` *(skill)* | Check Slack inbox for unread messages |

### PermissionRequest
| Hook | Matcher | Description |
|------|---------|-------------|
| `smart-auto-approve.py` | `Bash` | Auto-approve safe commands (git read, ls, test runners), deny dangerous ones (sudo, rm -rf, eval, dd, python -c, --no-verify). Shell chaining guard blocks `;`, `\|`, `&&`, backticks before allow/deny checks. |

### SubagentStart
| Hook | Description |
|------|-------------|
| `soul-subagent-inject.py` | Inject role-specific soul context into subdaimones (12 mapped roles + generic fallback) |

### Stop
| Hook | Description |
|------|-------------|
| `on-ready.sh` → `terminal-title.sh` | Update terminal title with ready state icon |
| `propagate-rename.py` | Sync title from session-registry.json to session-summaries.json |
| `stop-handoff.py` | Throttled handoff (3min cooldown, 10min idle gate) + soul registry heartbeat |
| `slack-stop-hook.py` | Process pending Slack messages on stop |
| `soul-reflect.py` *(async)* | Retrospective cognitive pipeline — monologue, user model, soul state updates via Groq/OpenRouter |
| `session-tags-infer.py` *(async)* | Infer session tags via llama-server (3-min cooldown), write sidecar JSON + session-registry.json |
| `plan-rename.py stop` | Rename random-named plans to dated slugs, symlink for write-through, open in dabarat |

### SessionEnd
| Hook | Description |
|------|-------------|
| `precompact-handoff.py` | Generate handoff YAML via OpenRouter (Gemini Flash Lite) |
| `soul-deregister.py` | Remove session from soul registry |
| `git-track-rebuild.py` | Rebuild git tracking state from accumulated diffs |
| `plan-rename.py session_end` | Final cleanup of forwarding symlinks in plans directory |

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
| `dabarat-open.py` *(Write)* | Auto-open written Markdown files in Dabarat preview |
| `plan-session-rename.py` *(Write)* | Emit plan canonical path as additionalContext when plans are written |
| `lint-on-write.py` *(Write, Edit)* | Run linters after file edits and return violations as additionalContext for agent self-correction. Dispatches to ESLint (TS/JS), Clippy (Rust), Ruff (Python) + custom-lint.sh (grep-based project convention checks). 5s cooldown, 10-violation cap, 8s subprocess timeout. Inspired by [Factory.ai](https://factory.ai/news/using-linters-to-direct-agents). |

### PostToolUseFailure
| Hook | Matcher | Description |
|------|---------|-------------|
| `error-context-hints.py` | `Bash` | Pattern-match 14 common errors (EADDRINUSE, ModuleNotFound, PermissionError, git conflicts, etc.) and inject recovery hints |

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
| `soul-registry.py` | Soul registry daemon — heartbeat, query, cleanup (called by stop-handoff, soul-activate) |

## Legacy / Utility

| Hook | Description |
|--------|-------------|
| `debug-hook-input.sh` | Debug script — dumps hook JSON input to stderr |
| `terminal-title.sh` | Two-tier terminal title with repo icons (target of on-ready.sh and on-thinking.sh symlinks) |
| `session-name.sh` | Extract session name (PID file → transcript slug → truncated ID) |
| `crab-model.sh` | Output model name with crab emoji for statusline |
| `plan-cleanup-symlinks.py` | Standalone symlink cleanup (superseded by plan-rename.py session_end) |
| `update-agent-docs.sh` | Background update of agent_docs/active-projects.md |

## Architecture

```
SessionStart (startup) ─→ soul-activate.py ─→ soul-registry.py
SessionStart (compact) ─→ soul-reactivate-compact.py      ↑
SessionStart (resume) ─→ soul-activate-resume.py           │
                         └─→ CLAUDE_ENV_FILE               │ heartbeat
                                                           │
UserPromptSubmit ─→ multi-response-prompt.py               │
                 ─→ slack_inbox_hook.py                    │
                                                           │
PermissionRequest ─→ smart-auto-approve.py (Bash)          │
                                                           │
SubagentStart ─→ soul-subagent-inject.py                   │
                                                           │
PreToolUse ─→ git-track.sh (Bash)                          │
           ─→ block-websearch.sh (WebSearch)               │
           ─→ block-webfetch.sh (WebFetch)                 │
           ─→ terminal-title.sh (*)                        │
                                                           │
PostToolUse ─→ git-track-post.sh (Bash)                    │
            ─→ dabarat-open.py (Write)                     │
            ─→ plan-session-rename.py (Write)              │
                                                           │
PostToolUseFailure ─→ error-context-hints.py (Bash)        │
                                                           │
Stop ─→ terminal-title.sh                                  │
     ─→ propagate-rename.py                                │
     ─→ stop-handoff.py ──→ precompact-handoff.py (OpenRouter)
     │                   ──→ soul-registry.py heartbeat    │
     ─→ slack-stop-hook.py                                 │
     ─→ soul-reflect.py (async, Groq/OpenRouter)           │
     ─→ session-tags-infer.py (async, OpenRouter)          │
     ─→ plan-rename.py stop ──→ dabarat (fire-and-forget)  │
                                                           │
PreCompact ─→ precompact-handoff.py                        │
                                                           │
SessionEnd ─→ precompact-handoff.py                        │
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

## Events Used: 10 of 18

SessionStart, UserPromptSubmit, PermissionRequest, SubagentStart, PreToolUse, PostToolUse, PostToolUseFailure, Stop, PreCompact, SessionEnd
