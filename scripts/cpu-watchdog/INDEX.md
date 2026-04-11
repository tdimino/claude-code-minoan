# Phroura — CPU + RAM Watchdog for Claude Code Sessions

Monitoring daemon that detects stuck, memory-leaking, or orphaned Claude Code sessions and alerts via macOS notifications + Telegram. Polls every user process on a 30s cycle, tracks per-PID CPU and RSS in a rolling window, and enriches Claude sessions with `lsof`-derived session IDs and revoked-fd signals.

## Alert types

| Alert | Trigger | Channels |
|---|---|---|
| **CPU stuck** | Any PID ≥ `cpu_threshold_pct` for `consecutive_checks` polls | macOS + Telegram (Basso) |
| **Claude orphan** | `is_claude` + `has_revoked_fds` + CPU ≥ 1% (stdio revocation bug) | macOS + Telegram (Purr) |
| **RAM warn** | RSS ≥ `rss_warn_mb` (800 MB default) | **Log-only** — visible in `status.sh` and `cpu-watchdog.log` |
| **RAM alert** | RSS ≥ `rss_alert_mb` (1200 MB) for `consecutive_checks` polls | macOS + Telegram (Basso) |
| **RAM critical** | RSS ≥ `rss_critical_mb` (2000 MB) for `consecutive_checks` polls | macOS + Telegram (Sosumi, louder) |
| **RAM leak** | Slope ≥ `rss_growth_mb_per_min` (60 MB/min) over ≥5 samples | macOS + Telegram (Basso) |
| **Orphan MCP cluster** | `>= orphan_mcp_threshold` (15) PPID=1 MCP server processes | macOS + Telegram (Purr) |

All alerts respect per-type cooldowns. RAM thresholds are calibrated to this machine — 641 MB is the highest RSS ever observed for a live Claude session here, so 800 MB / 1200 MB / 2000 MB form 1.25× / 1.9× / 3.1× headroom tiers.

## Files

| File | Purpose |
|------|---------|
| `phroura.py` | Main daemon — polls ps, tracks CPU + RSS, orphan MCP sweep, alerts |
| `config.json` | Thresholds: poll interval, CPU %, RSS tiers, growth slope, orphan MCP |
| `status.sh` | Quick status check (daemon state, tracked PIDs, last alert) |
| `minoan-cpu-watchdog` | Shell wrapper for launchd |
| `com.minoan.cpu-watchdog.plist` | launchd config (symlink to ~/Library/LaunchAgents/) |
| `logs/` | TimedRotatingFileHandler, 7-day retention |
| `data/state.json` | Persistent rolling state — `{pids: {...}, global: {...}}` schema |

## Usage

```bash
# Status (shows CPU, RSS, peak, growth, orphan MCP summary)
bash ~/.claude/scripts/cpu-watchdog/status.sh

# Dry run (single poll)
python3 ~/.claude/scripts/cpu-watchdog/phroura.py

# Show tracked PIDs
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --status

# Manual daemon mode
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --daemon

# Override thresholds
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --daemon --interval 10 --threshold 80

# Toggle alerts on/off (persisted to config.json, hot-reloaded)
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --toggle-telegram
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --toggle-ram-watchdog
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --toggle-orphan-mcp

# Reload daemon after editing phroura.py
launchctl kickstart -k gui/$(id -u)/com.minoan.cpu-watchdog
```

## Config (RAM-related keys)

| Key | Default | Meaning |
|---|---|---|
| `enable_ram_watchdog` | `true` | Master switch for all RAM alerts |
| `rss_window_samples` | `20` | Rolling window size (20 × 30s = 10 min) |
| `rss_warn_mb` | `800` | Log-only early warning |
| `rss_alert_mb` | `1200` | Sustained-breach alert tier |
| `rss_critical_mb` | `2000` | Hard-ceiling critical tier |
| `rss_claude_floor_mb` | `100` | Skip RAM tracking for tiny processes |
| `rss_growth_mb_per_min` | `60` | Growth-slope alert trigger |
| `rss_growth_min_samples` | `5` | Minimum samples before slope is trusted |
| `rss_cooldown_min` | `60` | Shared cooldown for all RAM alert types |
| `enable_orphan_mcp_watchdog` | `true` | Master switch for orphan MCP detection |
| `orphan_mcp_threshold` | `15` | Alert when reparented MCP count exceeds this |
| `orphan_mcp_excludes` | `[claude-peers, claude-plugins-mcp]` | Legitimate PPID=1 daemons to ignore |

## Install

```bash
ln -sf ~/.claude/scripts/cpu-watchdog/com.minoan.cpu-watchdog.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.minoan.cpu-watchdog.plist
```

## Etymology

Phroura (φρουρά) — "watch, guard, sentinel post." The Watchman on the roof in Aeschylus's *Agamemnon*.
