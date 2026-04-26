# Speculator — Ghostty Tab Discovery Daemon

Polls every 5 minutes to discover Ghostty terminal tabs and map them to running Claude Code sessions.

## Files

| File | Purpose |
|------|---------|
| `speculator.py` | Main daemon script (stdlib only, zero deps) |
| `speculator` | Shell wrapper for launchd |
| `com.minoan.speculator.plist` | launchd plist (symlinked to ~/Library/LaunchAgents/) |
| `status.sh` | Health check script |
| `data/ghostty-sessions.json` | Latest snapshot (JSON) |
| `data/ghostty-sessions.md` | Latest snapshot (Markdown) |
| `logs/` | Daemon logs (stdout, stderr, app log with 7-day rotation) |

## Usage

```bash
# Single snapshot (prints JSON to stdout)
python3 speculator.py --once

# Run as daemon (5-minute polling loop)
python3 speculator.py --daemon

# Custom interval
python3 speculator.py --daemon --interval 60

# Check daemon status
bash status.sh
```

## Output

- `data/ghostty-sessions.json` — Structured JSON with session metadata
- `data/ghostty-sessions.md` — Markdown table for human/LLM consumption
- `~/.claude/agent_docs/ghostty-sessions.md` — Synced copy for CLAUDE.md reference

## Architecture

Discovery chain: Ghostty PID → child login shells (one per tab) → TTY assignment → Claude process on each TTY → session PID file → enrichment from soul registry, session summaries, and session tags.

Ghostty's native AppleScript API (PR #11208) is not available in the current tip build. The daemon auto-detects when it becomes available and upgrades to direct tab enumeration. Until then, System Events provides window names as bonus context.
