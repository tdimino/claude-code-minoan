# Phroura — CPU Watchdog for Claude Code Sessions

CPU monitoring daemon that detects stuck Claude Code sessions and alerts via macOS notifications + Telegram.

## Files

| File | Purpose |
|------|---------|
| `phroura.py` | Main daemon — polls ps, tracks CPU, alerts on stuck sessions |
| `config.json` | Thresholds: poll interval, CPU%, consecutive checks, cooldown |
| `status.sh` | Quick status check (daemon state, tracked PIDs, last alert) |
| `minoan-cpu-watchdog` | Shell wrapper for launchd |
| `com.minoan.cpu-watchdog.plist` | launchd config (symlink to ~/Library/LaunchAgents/) |
| `logs/` | TimedRotatingFileHandler, 7-day retention |
| `data/state.json` | Persistent rolling state across restarts |

## Usage

```bash
# Status
bash ~/.claude/scripts/cpu-watchdog/status.sh

# Dry run (single poll)
python3 ~/.claude/scripts/cpu-watchdog/phroura.py

# Show tracked PIDs
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --status

# Manual daemon mode
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --daemon

# Override thresholds
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --daemon --interval 10 --threshold 80
```

## Install

```bash
ln -sf ~/.claude/scripts/cpu-watchdog/com.minoan.cpu-watchdog.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.minoan.cpu-watchdog.plist
```

## Etymology

Phroura (φρουρά) — "watch, guard, sentinel post." The Watchman on the roof in Aeschylus's *Agamemnon*.
