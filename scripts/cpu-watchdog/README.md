# phroura

A macOS launchd daemon that catches runaway processes stuck at 100% CPU and warns you before they burn a full core for days.

Named for φρουρά (phrourá) — "the watch, the sentinel post." The Watchman on the roof of Atreus's palace in Aeschylus's *Agamemnon*, waiting for the signal fire.

## What It Does

Polls `ps aux` every 30 seconds. Tracks per-PID CPU usage over a rolling window. When any user process sustains >90% CPU for three consecutive checks (~90 seconds), sends a native macOS alert and an optional Telegram message. **Never auto-kills** — the user decides.

Claude Code sessions get extra enrichment: full `lsof` scan extracts the working directory, session ID (from open `.jsonl` handles), Claude version, and revoked file descriptors (the signal of the stdio-revocation loop bug that causes many Claude Code hangs). Everything else gets basename + command line + elapsed time.

Built because a Claude Code session was found pegged at 100% CPU for 3 days straight. Then, during validation, phroura found a TradingView Electron crashpad handler running at 316% CPU **for eight days**.

## Why This Exists

Claude Code's 100% CPU hang is a [well-documented, multi-root-cause bug cluster](https://github.com/anthropics/claude-code/issues?q=cpu+100%25) — stdio revocation loops after terminal disconnect ([#22313](https://github.com/anthropics/claude-code/issues/22313)), `TaskStop` runaway `posix_spawn` loops ([#27415](https://github.com/anthropics/claude-code/issues/27415)), `statusLine` zombie accumulation ([#34092](https://github.com/anthropics/claude-code/issues/34092)), compaction hangs ([#19567](https://github.com/anthropics/claude-code/issues/19567)), MCP server orphan accumulation ([#26658](https://github.com/anthropics/claude-code/issues/26658)). None of these are fixed as of v2.1.100. The stuck processes ignore `SIGTERM` — only `kill -9` works.

Phroura doesn't fix the bugs. It just makes sure you *notice* them before they waste a week of CPU time.

## Install

```bash
# 1. Install alerter (notification tool with its own bundle ID)
brew install vjeantet/tap/alerter

# 2. Copy phroura into place
mkdir -p ~/.claude/scripts/cpu-watchdog/{logs,data}
cp -r scripts/cpu-watchdog/* ~/.claude/scripts/cpu-watchdog/
chmod +x ~/.claude/scripts/cpu-watchdog/phroura.py \
         ~/.claude/scripts/cpu-watchdog/status.sh \
         ~/.claude/scripts/cpu-watchdog/minoan-cpu-watchdog

# 3. Install launchd agent
ln -sf ~/.claude/scripts/cpu-watchdog/com.minoan.cpu-watchdog.plist \
       ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.minoan.cpu-watchdog.plist

# 4. Trigger the alerter permission prompt (grant when it appears)
alerter --title "Phroura test" --message "Grant permission in System Settings" --timeout 5

# 5. Verify
bash ~/.claude/scripts/cpu-watchdog/status.sh
```

On first alert, macOS will ask you to grant notification permission for `alerter` (bundle ID `fr.vjeantet.alerter`). This is intentionally a different tool from `terminal-notifier` so phroura's alerts are independently controllable from any other notification sources on your system.

## Usage

```bash
# Daemon status (launchctl state, tracked PIDs, last alert, recent log)
bash ~/.claude/scripts/cpu-watchdog/status.sh

# Single dry-run poll + current status
python3 ~/.claude/scripts/cpu-watchdog/phroura.py

# Show rolling state for all tracked PIDs
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --status

# Print effective configuration
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --config

# Toggle Telegram alerts on/off (hot-reloaded on next poll cycle)
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --toggle-telegram

# Manual daemon mode (for debugging)
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --daemon --interval 5 --threshold 50
```

## Configuration

`config.json` is hot-reloaded every poll cycle — edit without restarting the daemon.

| Key | Default | Meaning |
|---|---|---|
| `poll_interval_sec` | `30` | How often to run `ps aux` |
| `cpu_threshold_pct` | `90` | CPU % considered "hot" |
| `consecutive_checks` | `3` | Hot checks needed before alerting (90s at default interval) |
| `cooldown_min` | `30` | Minutes before re-alerting the same PID |
| `enable_telegram` | `true` | Send Telegram messages |
| `enable_macos_notify` | `true` | Send macOS notifications via `alerter` |
| `enable_revoked_check` | `true` | Detect Claude orphans with revoked file descriptors |
| `telegram_chat_id` | `"633125581"` | Chat ID for Telegram alerts |
| `monitor_all_processes` | `true` | Monitor all user processes (`false` = Claude only) |
| `cpu_floor_pct` | `5` | Minimum CPU% for a non-Claude process to enter tracking |
| `exclude_commands` | (see below) | Basename list of processes to never alert on |
| `max_tracked_pids` | `500` | Cap on rolling-state entries |
| `log_retention_days` | `7` | Log rotation backup count |

Default `exclude_commands` covers macOS system daemons (`kernel_task`, `WindowServer`, `mdworker`, `Spotlight`, `XprotectService`, `logd`, `fseventsd`, `coreaudiod`, …), compilers and build tools (`cargo`, `rustc`, `clang`, `ld`, `lld`, …), media encoders (`ffmpeg`, `ffprobe`, `HandBrakeCLI`), and local LLM inference (`ollama`, `llama-server`, `llama-cli`). These are expected to peg CPU legitimately — extend the list in `config.json` for anything else in your workflow that should be ignored.

## Notifications

**macOS** — native alert via `alerter`. Bundle ID `fr.vjeantet.alerter` shows as a distinct entry in System Settings → Notifications, so you can grant/deny phroura independently from other notifier tools (phroura specifically avoids `terminal-notifier` to prevent collisions with Claude Code hooks that may already use it).

**Telegram** — optional. Reads `TELEGRAM_BOT_TOKEN` from `~/.config/env/secrets.env` or the environment. Send plain text to the configured `telegram_chat_id`.

**Log** — `~/.claude/scripts/cpu-watchdog/logs/cpu-watchdog.log`, rotated daily, 7-day retention.

Alert body shows PID, CPU %, elapsed time, memory, TTY, working directory, command basename + short command line, the kill command, and for Claude sessions: session ID, version, and a "revoked file descriptors" warning when the stdio loop is detected.

## Example Output

```
Phroura CPU Watchdog

  RUNNING  PID 32809
  Config: poll=30s, threshold=90%, checks=3
  Active Claude sessions: 22
  Tracked PIDs: 29 (1 hot)

  Last alert:
    2026-04-10 16:58:19 [WARNING] CPU WATCHDOG: Electron PID 28044 stuck at 316% CPU

  Recent log:
    Elapsed: 08-16:44:42
    Memory: 0.0% (0MB RSS)
    Command: /tmp/tradingview-re/mount/TradingView.app/...
    Action: kill -9 28044
```

## File Layout

```
cpu-watchdog/
├── phroura.py                     # Main daemon (single file, stdlib + requests)
├── config.json                    # User-editable thresholds (hot-reloaded)
├── status.sh                      # Quick status check script
├── minoan-cpu-watchdog            # Shell wrapper for launchd
├── com.minoan.cpu-watchdog.plist  # launchd agent
├── logs/                          # TimedRotatingFileHandler output
└── data/
    └── state.json                 # Rolling per-PID state (atomic writes)
```

## Architecture

One Python file, four classes, stdlib only (`requests` lazy-imported for Telegram):

- **`ProcessPoller`** — Runs `ps aux`, filters to Claude sessions + any non-Claude process above the CPU floor, enriches Claude processes via `lsof` (session ID from `.jsonl` handles, version from binary path, revoked FDs from stdio). Non-Claude processes get a cheap `ps -o ppid=,etime=` lookup only.
- **`StateTracker`** — Maintains per-PID `hot_count` (consecutive hot checks), `total_checks`, `first_seen`, `last_alert_time`. Atomic writes to `data/state.json` via temp-file + rename (SIGKILL-safe). Prunes dead PIDs every cycle, caps at 500 tracked.
- **`Alerter`** — Multi-channel dispatch. Single `_dispatch(log_msg, title, body, sound)` pipes to macOS (`alerter` subprocess), Telegram (REST), and the log. Orphan path bypasses `hot_count` and uses cooldown only.
- **`Phroura`** — Main loop. SIGTERM/SIGINT handlers for clean shutdown. Hot-reloads `config.json` every cycle.

The launchd plist uses `KeepAlive: {SuccessfulExit: false}` and `ThrottleInterval: 30` — restarts on crash, stays down on clean shutdown, throttles crash-restart loops.

## Requirements

- macOS (uses `ps`, `lsof`, `launchctl`, `osascript`-free notifications via `alerter`)
- Python 3.9+ (stdlib only, `requests` lazy for Telegram)
- [`alerter`](https://github.com/vjeantet/alerter) via `brew install vjeantet/tap/alerter` — provides notifications with an independent bundle ID
- Optional: `TELEGRAM_BOT_TOKEN` in `~/.config/env/secrets.env` for Telegram alerts

## Known Limitations

- `ps aux` reports CPU as a lifetime average, not instantaneous. A long-lived process that just started spiking may take one or two polls to cross the floor. Once tracked, it's polled every cycle regardless.
- PID recycling across polls is rare but possible. The tracker prunes dead PIDs every cycle to minimize window.
- Chrome renderers and other multi-process apps get one cooldown per PID. A heavy video call on Chrome could theoretically fire multiple alerts for different renderer PIDs — in practice the tight exclude list and 30-minute cooldown keep this manageable.
- The orphan-detection path (revoked file descriptors) only fires for Claude processes, since the stdio revocation bug is Claude-specific.
