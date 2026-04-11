# phroura

A macOS launchd daemon that catches runaway processes—stuck at 100% CPU, leaking RAM, or leaving orphaned MCP servers—and warns you before they burn a core for days or swap your machine into paging oblivion.

Named for φρουρά (phrourá)—"the watch, the sentinel post." The Watchman on the roof of Atreus's palace in Aeschylus's *Agamemnon*, waiting for the signal fire.

## What It Does

Polls `ps aux` every 30 seconds, tracks per-PID CPU and RSS over a rolling window, and runs three kinds of detection:

1. **CPU stuck**—any process sustaining >90% CPU for three consecutive checks (~90 seconds).
2. **RAM bloat**—three-tier thresholds on resident set size: an 800 MB `warn` line (log-only), a 1200 MB `alert` line (macOS + Telegram), and a 2000 MB `critical` line (louder alert). Plus a growth-rate detector: any process gaining ≥60 MB/min over a 10-minute rolling window triggers a RAM-leak alert before it reaches the absolute ceiling.
3. **Orphan MCP cluster**—counts MCP server processes reparented to `PID 1` (the [#33947 / #26658](https://github.com/anthropics/claude-code/issues/33947) pattern) and alerts when the cluster exceeds 15 stragglers.

All alerts go to macOS notifications (via [`alerter`](https://github.com/vjeantet/alerter) with an independent bundle ID) and optionally to Telegram. **Never auto-kills**—the user decides.

Claude Code sessions get extra enrichment: full `lsof` scan extracts the working directory, session ID (from open `.jsonl` handles), Claude version, and revoked file descriptors (the signal of the stdio-revocation loop bug). Everything else gets basename + command line + elapsed time.

Built because a Claude Code session was found pegged at 100% CPU for 3 days straight. Extended with RAM detection after finding open GitHub issues reporting Claude sessions leaking from [181 MB per API turn](https://github.com/anthropics/claude-code/issues/33447) to [44 GB of RSS](https://github.com/anthropics/claude-code/issues/24644). Within minutes of enabling the RAM watchdog, it also caught a Slack helper renderer at 869 MB and rising.

## Why This Exists

Claude Code has two well-documented bug clusters that phroura targets.

**CPU hangs**—[multi-root-cause 100% CPU loops](https://github.com/anthropics/claude-code/issues?q=cpu+100%25): stdio revocation after terminal disconnect ([#22313](https://github.com/anthropics/claude-code/issues/22313)), `TaskStop` runaway `posix_spawn` loops ([#27415](https://github.com/anthropics/claude-code/issues/27415)), `statusLine` zombie accumulation ([#34092](https://github.com/anthropics/claude-code/issues/34092)), compaction hangs ([#19567](https://github.com/anthropics/claude-code/issues/19567)), MCP server orphan accumulation ([#26658](https://github.com/anthropics/claude-code/issues/26658)). Stuck processes ignore `SIGTERM`—only `kill -9` works.

**Memory leaks**—a separate thick dossier of open issues:

| Issue | Pattern | Magnitude |
|---|---|---|
| [#33594](https://github.com/anthropics/claude-code/issues/33594) | Native addon leak (suspected `node-pty`) | 1.77 GB RSS fresh, 281 MB/hr growth |
| [#33447](https://github.com/anthropics/claude-code/issues/33447) | SSE Response retained by `PromiseReaction` | ~181 MB per API turn, 1.27 GB in 5.5 min |
| [#32920](https://github.com/anthropics/claude-code/issues/32920) | 14K `ArrayBuffer`s from streaming responses | ~480 MB/hour, 6.83 GB after 14.5 hrs |
| [#24644](https://github.com/anthropics/claude-code/issues/24644) | Unbounded `toolUseResult.stdout` in transcript | 44.4 GB RSS, GC thrash, SIGTERM unresponsive |
| [#31414](https://github.com/anthropics/claude-code/issues/31414) | Idle runaway (unknown trigger) | 860 MB → 11.8 GB in 2 min with no input |
| [#33947](https://github.com/anthropics/claude-code/issues/33947) | Orphan MCP accumulation—PPID reparented to 1 after session exit | 107 orphans → 7.75 GB after 1 workday |
| [#36204](https://github.com/anthropics/claude-code/issues/36204) | Orphan `lsof` zombies | 1000+ PPID=1 zombies |

None of these are fixed as of v2.1.100. Phroura doesn't fix them. It just makes sure you *notice* them before they waste a week of CPU time or paw half your system RAM.

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

# Toggle individual alert channels (hot-reloaded on next poll cycle)
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --toggle-telegram
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --toggle-ram-watchdog
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --toggle-orphan-mcp

# Manual daemon mode (for debugging)
python3 ~/.claude/scripts/cpu-watchdog/phroura.py --daemon --interval 5 --threshold 50

# Reload the launchd daemon after editing phroura.py
launchctl kickstart -k gui/$(id -u)/com.minoan.cpu-watchdog
```

## Configuration

`config.json` is hot-reloaded every poll cycle—edit without restarting the daemon.

### Core + CPU

| Key | Default | Meaning |
|---|---|---|
| `poll_interval_sec` | `30` | How often to run `ps aux` |
| `cpu_threshold_pct` | `90` | CPU % considered "hot" |
| `consecutive_checks` | `3` | Hot checks needed before alerting (90s at default interval) |
| `cooldown_min` | `30` | Minutes before re-alerting on CPU |
| `enable_telegram` | `true` | Send Telegram messages |
| `enable_macos_notify` | `true` | Send macOS notifications via `alerter` |
| `enable_revoked_check` | `true` | Detect Claude orphans with revoked file descriptors |
| `telegram_chat_id` | `"…"` | Chat ID for Telegram alerts |
| `monitor_all_processes` | `true` | Monitor all user processes (`false` = Claude only) |
| `cpu_floor_pct` | `5` | Minimum CPU% for a non-Claude process to enter tracking |
| `exclude_commands` | (see below) | Basename list of processes to never alert on |
| `max_tracked_pids` | `500` | Cap on rolling-state entries |
| `log_retention_days` | `7` | Log rotation backup count |

### RAM watchdog

| Key | Default | Meaning |
|---|---|---|
| `enable_ram_watchdog` | `true` | Master switch for all RAM alerts |
| `rss_window_samples` | `20` | Rolling window size (20 × 30s = 10 min) |
| `rss_warn_mb` | `800` | Log-only early warning line |
| `rss_alert_mb` | `1200` | Sustained-breach alert tier (macOS + Telegram) |
| `rss_critical_mb` | `2000` | Hard-ceiling critical tier (louder alert) |
| `rss_claude_floor_mb` | `100` | Skip RAM tracking for tiny helper processes |
| `rss_growth_mb_per_min` | `60` | Growth-slope alert trigger |
| `rss_growth_min_samples` | `5` | Minimum samples before slope is trusted |
| `rss_cooldown_min` | `60` | Cooldown shared across RAM alert types |
| `enable_orphan_mcp_watchdog` | `true` | Master switch for orphan MCP detection |
| `orphan_mcp_threshold` | `15` | Alert when PPID=1 MCP count exceeds this |
| `orphan_mcp_cooldown_min` | `60` | Independent cooldown for orphan MCP alerts |
| `orphan_mcp_excludes` | `[claude-peers, claude-plugins-mcp]` | Legitimate PPID=1 daemons to ignore |

RAM thresholds are calibrated to catch sustained bloat without flagging normal warm-up. On a 36 GB machine a live Claude session typically peaks around 500–700 MB—the 800 MB warn line sits one standard deviation above observed maximums, 1200 MB is ~2× peak (unambiguously pathological), and 2000 MB is the "drop everything" line. Tune all three in `config.json` for your machine.

Default `exclude_commands` covers macOS system daemons (`kernel_task`, `WindowServer`, `mdworker`, `Spotlight`, `XprotectService`, `logd`, `fseventsd`, `coreaudiod`, …), compilers and build tools (`cargo`, `rustc`, `clang`, `ld`, `lld`, …), media encoders (`ffmpeg`, `ffprobe`, `HandBrakeCLI`), and local LLM inference (`ollama`, `llama-server`, `llama-cli`). These are expected to peg CPU legitimately—extend the list in `config.json` for anything else in your workflow that should be ignored.

## Notifications

**macOS**—native alert via `alerter`. Bundle ID `fr.vjeantet.alerter` shows as a distinct entry in System Settings → Notifications, so you can grant/deny phroura independently from other notifier tools (phroura specifically avoids `terminal-notifier` to prevent collisions with Claude Code hooks that may already use it).

**Telegram**—optional. Reads `TELEGRAM_BOT_TOKEN` from `~/.config/env/secrets.env` or the environment. Send plain text to the configured `telegram_chat_id`.

**Log**—`~/.claude/scripts/cpu-watchdog/logs/cpu-watchdog.log`, rotated daily, 7-day retention.

Alert body shows PID, CPU %, elapsed time, memory, TTY, working directory, command basename + short command line, the kill command, and for Claude sessions: session ID, version, and a "revoked file descriptors" warning when the stdio loop is detected.

## Example Output

### Status

```
Phroura Status
============================================================
Active: 23 Claude sessions, 5 other tracked
Orphan MCPs: 0

  PID  31755  CPU:  17.8%  RSS:   619 MB (peak 619 MB)  Hot: 0/3  Checks: 48
           CWD: ~/Desktop/Programming
           Session: f3b90ac7
  PID  72992  CPU:   5.7%  RSS:   622 MB (peak 622 MB)  Hot: 0/3  Checks: 199
           CWD: ~/Desktop/Programming
           Session: 664a8e7c
  PID   1575  CPU:  14.1%  RSS:   890 MB (peak 890 MB)  Hot: 0/3  Checks: 199
           CWD: ~
           Last RAM alert: 2026-04-11T11:44:31 (warn)
```

### CPU alert

```
2026-04-10 16:58:19 [WARNING] CPU WATCHDOG: Electron PID 28044 stuck at 316% CPU
  Elapsed: 08-16:44:42
  Memory: 0.0% (0MB RSS)
  Command: /tmp/tradingview-re/mount/TradingView.app/...
  Action: kill -9 28044
```

### RAM warn (log-only, early signal)

```
2026-04-11 11:39:19 [INFO] RAM WARN: Slack PID 1575 at 869 MB
  Peak: 881 MB  |  CPU: 14%
  Elapsed: 16-00:41:43
  Command: /Applications/Slack.app/Contents/Frameworks/Slack Helper (Renderer).app/...
```

### RAM leak (growth-rate)

```
2026-04-11 12:03:08 [WARNING] RAM LEAK: Claude PID 47112 growing +187 MB/min
  Current: 2340 MB  |  Window start: 410 MB
  Samples: 12 (since 2026-04-11T11:57:45)
  CWD: ~/Desktop/Programming/worldwarwatcher
  Session: 29e25b0f
```

### Orphan MCP cluster

```
2026-04-11 14:22:01 [WARNING] ORPHAN MCP CLUSTER: 23 reparented MCP servers (847 MB total)
  Sample PIDs: 18234, 18291, 18302, 18311, 18355, 18402, 18445, 18501...
  PID 18234: 124 MB  node /path/to/@modelcontextprotocol/server-filesystem
  PID 18291: 87 MB   node /path/to/mcp-server-github
  PID 18302: 62 MB   python -m mcp_server.weather
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

- **`ProcessPoller`**—Runs `ps aux`, filters to Claude sessions + any non-Claude process above the CPU floor, enriches Claude processes via `lsof` (session ID from `.jsonl` handles, version from binary path, revoked FDs from stdio). Non-Claude processes get a cheap `ps -o ppid=,etime=` lookup only. Also runs `find_orphan_mcp_processes` once per cycle—a separate `ps -eo pid,ppid,rss,command` scan that matches MCP command patterns against the reparented-to-init process set.
- **`StateTracker`**—Maintains per-PID rolling state in `{pids, global}` schema atomically serialized to `data/state.json`. Per-PID: `hot_count` (consecutive CPU breaches), `rss_samples` (bounded FIFO window), `rss_hot_count`, `peak_rss_kb`, and separate cooldown stamps for CPU alerts, RSS alerts, and growth alerts. `global` holds system-wide cooldowns (orphan MCP). Three detection methods: `classify_rss_severity` returns the highest-tier breach using a severity-rank map, `rss_growth_slope` computes MB/minute from the oldest→newest sample pair, and `should_alert_orphan_mcp` gates on the `orphan_mcp_threshold`. Prunes dead PIDs every cycle, caps at 500 tracked.
- **`Alerter`**—Multi-channel dispatch. Single `_dispatch(log_msg, title, body, sound)` pipes to macOS (`alerter` subprocess), Telegram (REST), and the log. Seven alert methods routed through it: `alert` (CPU), `alert_orphaned` (Claude stdio revocation), `alert_rss` (three-tier severity, warn is log-only and bypasses `_dispatch`), `alert_rss_growth` (slope-based), and `alert_orphan_mcp` (global MCP cluster).
- **`Phroura`**—Main loop. SIGTERM/SIGINT handlers for clean shutdown. Hot-reloads `config.json` every cycle so every threshold can be tuned without a daemon restart.

The launchd plist uses `KeepAlive: {SuccessfulExit: false}` and `ThrottleInterval: 30`—restarts on crash, stays down on clean shutdown, throttles crash-restart loops.

## Requirements

- macOS (uses `ps`, `lsof`, `launchctl`, `osascript`-free notifications via `alerter`)
- Python 3.9+ (stdlib only, `requests` lazy for Telegram)
- [`alerter`](https://github.com/vjeantet/alerter) via `brew install vjeantet/tap/alerter`—provides notifications with an independent bundle ID
- Optional: `TELEGRAM_BOT_TOKEN` in `~/.config/env/secrets.env` for Telegram alerts

## Known Limitations

- `ps aux` reports CPU as a lifetime average, not instantaneous. A long-lived process that just started spiking may take one or two polls to cross the floor. Once tracked, it's polled every cycle regardless.
- PID recycling across polls is rare but possible. The tracker prunes dead PIDs every cycle to minimize window.
- Chrome renderers and other multi-process apps get one cooldown per PID. A heavy video call on Chrome could theoretically fire multiple alerts for different renderer PIDs—in practice the tight exclude list and 30-minute cooldown keep this manageable.
- The orphan-detection path (revoked file descriptors) only fires for Claude processes, since the stdio revocation bug is Claude-specific.
