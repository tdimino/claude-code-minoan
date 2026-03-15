# syspeek

macOS system resource monitor. Claudicle-aware.

## Files
- `syspeek.py` — Main script (stdlib only, zero deps)
- `syspeek` — Shell wrapper
- `status.sh` — Daemon status check
- `com.minoan.syspeek.plist` — launchd plist for daemon mode
- `data/` — JSONL snapshot logs (daily, auto-rotated)
- `logs/` — Daemon and stdout/stderr logs

## Quick Reference
```bash
syspeek                       # Colored terminal snapshot
syspeek --top 15              # Show top N processes
syspeek --json                # Kothar-compatible JSON
syspeek --record              # Persist to JSONL + memory.db
syspeek --kill PID            # SIGTERM with safety checks
syspeek --history             # Last 24h summaries
syspeek --category claude     # Filter to one category
syspeek --daemon              # Loop every 5 min, record each
```

## Daemon Setup
```bash
cp com.minoan.syspeek.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.minoan.syspeek.plist
```

## Memory Integration
- Ensouled: writes to `~/.claudicle/daemon/memory/memory.db` (channel: `system:syspeek`)
- Always: appends to `data/YYYY-MM-DD.jsonl`
- JSON output is a superset of Kothar's `SystemHealthReport` interface
