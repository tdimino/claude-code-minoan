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
syspeek                       # Colored terminal snapshot (mem + disk bars, swap, pressure)
syspeek --top 15              # Show top N processes
syspeek --json                # Kothar-compatible JSON (adds ~1s iostat sample)
syspeek --disk                # Disk view: volumes, purgeable, hotspot dirs, Mole pointers
syspeek --record              # Persist to JSONL + memory.db
syspeek --kill PID            # SIGTERM with safety checks
syspeek --history             # Last 24h summaries (CPU/MEM/DISK)
syspeek --category claude     # Filter to one category
syspeek --daemon              # Loop every 5 min, record each
```

## Stale Session Alerts
- Daemon flags claude + codex sessions with no transcript activity for 10+ days (`STALE_SESSION_DAYS`)
- Signal: transcript/rollout mtime — claude via speculator's PID map (fallback: transcript birthtime ≈ process start), codex via lsof on its open rollout files (TTY atime is useless; agent TUIs poll constantly)
- Alerts: macOS notification, once per PID per day (marker: `data/.stale-alerts.json`); also in terminal output, JSON `staleSessions`, and `issues`

## Data Lifecycle
- `data/YYYY-MM-DD.jsonl` — one line per snapshot; gzipped after 7 days, archives deleted after 30
- Daemon writes memory.db at most hourly (marker: `data/.last-memdb-write`); JSONL gets every snapshot
- Deep disk analysis stays with Mole (`mo analyze`, `mo clean`) and `gdu-go` — syspeek only surfaces capacity and curated hotspots

## Daemon Setup
```bash
cp com.minoan.syspeek.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.minoan.syspeek.plist
```

## Memory Integration
- Ensouled: writes to `~/.claudicle/daemon/memory/memory.db` (channel: `system:syspeek`)
- Always: appends to `data/YYYY-MM-DD.jsonl`
- JSON output is a superset of Kothar's `SystemHealthReport` interface
