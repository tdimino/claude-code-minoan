# syspeek

macOS system resource monitor with process categorization, disk/swap/pressure tracking, stale-agent-session alerts, and optional Claudicle memory integration.

Single command, zero dependencies, <0.5s.

## What It Does

Captures a system snapshot via `ps`, `vm_stat`, `sysctl`, `df`, and `diskutil`, classifies every process into one of 7 categories, and renders a colored terminal table (memory + disk bars, swap, memory-pressure and thermal warnings) or Kothar-compatible JSON. v2 adds disk capacity, swap, memory pressure, real iostat rates, a `--disk` volume/hotspot view, and daemon notifications for stale Claude/Codex sessions.

**Categories:**
| Icon | Category | Matches |
|------|----------|---------|
| `>>` | Claude Code | `claude`, `anthropic` |
| `@@` | Browsers | Chrome, Arc, Firefox, Safari, Brave, Edge |
| `[]` | IDEs/Terms | VS Code, Cursor, Ghostty, Terminal, Zed, tmux |
| `**` | ML/Inference | `ollama`, `llama-server`, `mlx`, `parakeet` |
| `//` | Dev Servers | `node`, `next-server`, `vite`, `webpack`, `uvicorn`, `cargo`, `java`, `python` |
| `..` | System | ~40 known macOS daemons (`kernel_task`, `WindowServer`, `launchd`, etc.) |
| `--` | Other | Everything else |

## Install

```bash
# Copy to ~/.claude/scripts/
cp -r syspeek ~/.claude/scripts/syspeek
chmod +x ~/.claude/scripts/syspeek/syspeek ~/.claude/scripts/syspeek/syspeek.py

# Add alias
echo "alias syspeek='~/.claude/scripts/syspeek/syspeek'" >> ~/.zshrc
```

## Usage

```bash
syspeek                       # Colored terminal snapshot
syspeek --top 15              # Show top N processes (default: 10)
syspeek --json                # JSON output (Kothar SystemHealthReport superset; adds ~1s iostat sample)
syspeek --disk                # Disk view: volumes, APFS purgeable, hotspot dirs
syspeek --no-color            # Strip ANSI codes
syspeek --category claude     # Filter to one category
syspeek --record              # Persist to JSONL + memory.db (if ensouled)
syspeek --kill PID            # SIGTERM with safety checks
syspeek --history             # Last 24h of recorded snapshots
syspeek --daemon              # Loop every N minutes, record each
syspeek --interval 5          # Daemon interval in minutes (default: 5)
```

## Example Output

```
  ┌────────────────────────────────────────────────────────────────────┐
  │  syspeek · Kothar · 2026-03-15T14:32:00                           │
  │  14 cores · 36 GB · 868 procs                                     │
  └────────────────────────────────────────────────────────────────────┘

  [████████████████████████████░░] 93.2% MEM (33.5 / 36.0 GB)

  >> Claude Code      7 procs    5.2% CPU   4.6 GB
  @@ Browsers        47 procs    8.7% CPU   2.5 GB
  ** ML/Inference      2 procs    6.2% CPU   3.2 GB
  // Dev Servers       3 procs    3.1% CPU   0.6 GB
  .. System           89 procs    2.1% CPU   1.8 GB
  -- Other           342 procs    1.8% CPU   8.9 GB

  TOP 10 BY CPU
      PID    CPU%    MEM%       RSS  CAT  COMMAND
    14523     8.2     1.4    512 MB  >>  claude
    29811     6.1     8.9    3.2 GB  **  ollama
    ...
```

## Memory Integration

When `--record` is passed, syspeek persists the snapshot in two ways:

**JSONL (always):** Appends compact JSON to `data/YYYY-MM-DD.jsonl`. Daily files, gzipped after 7 days, archives deleted after 30 (atomic rotation). In daemon mode, memory.db writes are throttled to hourly while JSONL gets every snapshot.

**Canonical memory.db (Claudicle ensouled only):** If `~/.claudicle/soul/soul.md` exists, writes directly to the `working_memory` table in `~/.claudicle/daemon/memory/memory.db`:
- Channel: `system:syspeek`
- Entry type: `systemSnapshot`
- Region: `system-monitoring`
- Content: human-readable one-liner
- Metadata: full JSON snapshot

This makes system state a first-class memory — any Claude session or Kothar subprocess can query "what was the machine doing on March 15?" the same way it queries conversation history.

Without Claudicle, syspeek works identically minus the memory.db write.

## Kothar Integration

The JSON output is a superset of Kothar's `SystemHealthReport` interface (`lib/types/kothar.ts`). Top-level fields match exactly:

```typescript
interface SystemHealthReport {
  cpuUsage: number;
  memoryUsage: number;
  gpuUsage: number;
  thermalLevel: 'normal' | 'elevated' | 'critical';
  diskIO: { readsPerSec: number; writesPerSec: number };
  networkAvailable: boolean;
  topProcesses: { pid: number; name: string; cpu: number; memory: number }[];
  issues: string[];
  timestamp: string;
}
```

Extended fields (`categories`, `memory`, `total_processes`, `top_cpu`, `top_mem`) are additive.

## Daemon Mode

Run continuously and record snapshots every N minutes:

```bash
# Manual
syspeek --daemon --interval 5

# Via launchd (persistent)
cp com.minoan.syspeek.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.minoan.syspeek.plist

# Check status
bash status.sh
```

## Stale Session Alerts

The daemon flags Claude Code and OpenAI Codex CLI sessions with no transcript activity for 10+ days and fires a macOS notification (once per PID per day). Idle time comes from transcript/rollout mtimes — Claude via a PID→session map (fallback: transcript birthtime ≈ process start), Codex via `lsof` on its open rollout files. TTY atime is deliberately not used: agent TUIs poll the terminal constantly. Stale sessions also appear in terminal output, JSON `staleSessions`, and `issues`.

## Kill Command

```bash
syspeek --kill 16879
```

Looks up the process, shows its category and resource usage, and asks for confirmation before sending SIGTERM. Refuses to kill PID 0 and 1. Warns on SYSTEM category processes.

## Requirements

- macOS (uses `ps`, `vm_stat`, `sysctl`, `pmset`)
- Python 3.9+ (stdlib only, zero external dependencies)
- Optional: Claudicle soul for memory.db integration
