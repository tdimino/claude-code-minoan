#!/usr/bin/env python3
"""phroura — CPU watchdog for user processes.

Polls ps(1) every N seconds, tracks per-PID CPU usage over a rolling window,
and alerts when any process sustains high CPU. Does NOT auto-kill.

Claude Code processes get extra enrichment (session ID, version, revoked FDs)
and an orphan-detection path for the known stdio-revocation bug cluster.

Usage:
    phroura.py                  # Run once (dry-run check)
    phroura.py --daemon         # Continuous monitoring (for launchd)
    phroura.py --status         # Show current tracked processes
    phroura.py --config         # Print effective config
    phroura.py --toggle-telegram  # Toggle Telegram alerts

Notifications:
    - macOS native (osascript) — always
    - Telegram (@claudicle_bot) — if TELEGRAM_BOT_TOKEN set
    - Log file — always

Depends: Python 3.9+ stdlib only (requests imported lazily for Telegram)
"""

import argparse
import json
import logging
import logging.handlers
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

# ─── Config ───────────────────────────────────────────────────────────────

SCRIPT_DIR = Path(__file__).parent
LOG_DIR = SCRIPT_DIR / "logs"
DATA_DIR = SCRIPT_DIR / "data"
CONFIG_FILE = SCRIPT_DIR / "config.json"
STATE_FILE = DATA_DIR / "state.json"
LOG_FILE = LOG_DIR / "cpu-watchdog.log"

DEFAULT_CONFIG = {
    "poll_interval_sec": 30,
    "cpu_threshold_pct": 90,
    "consecutive_checks": 3,
    "cooldown_min": 30,
    "enable_telegram": True,
    "enable_macos_notify": True,
    "enable_revoked_check": True,
    "telegram_chat_id": "633125581",
    "log_retention_days": 7,
    "max_tracked_pids": 500,
    # General process monitoring
    "monitor_all_processes": True,   # False = Claude-only (legacy behavior)
    "cpu_floor_pct": 5,              # Minimum CPU% for non-Claude processes to be tracked
    "exclude_commands": [            # Never alert on these (legitimate CPU spikes)
        # macOS system daemons
        "kernel_task", "WindowServer", "mdworker", "mds_stores", "mds",
        "photolibraryd", "photoanalysisd", "backupd", "Spotlight",
        "corespotlightd", "cloudd", "bird", "XprotectService",
        "installd", "softwareupdated", "logd", "fseventsd", "coreaudiod",
        # Compilers / build tools (expected to peg CPU)
        "cargo", "rustc", "clang", "clang++", "cc", "c++", "ld", "lld",
        # Media encoders
        "ffmpeg", "ffprobe", "HandBrakeCLI",
        # Local LLM inference
        "ollama", "llama-server", "llama-cli",
    ],
    # --- RAM watchdog (Claude Code memory leak detection) ---
    "enable_ram_watchdog": True,
    "rss_window_samples": 20,            # 10 min rolling window at 30s poll
    "rss_warn_mb": 800,                  # Log-only (shows up in status.sh + logs)
    "rss_alert_mb": 1200,                # macOS + Telegram (sustained consecutive_checks)
    "rss_critical_mb": 2000,             # Louder alert, suggests kill -9
    "rss_claude_floor_mb": 100,          # Skip RAM tracking for tiny helpers
    "rss_growth_mb_per_min": 60,         # Growth-slope alert threshold
    "rss_growth_min_samples": 5,         # Minimum samples before slope is trusted
    "rss_cooldown_min": 60,              # Cooldown shared across RAM alert types
    # --- Orphan MCP cluster detection ---
    "enable_orphan_mcp_watchdog": True,
    "orphan_mcp_threshold": 15,          # Alert when reparented MCP count > threshold
    "orphan_mcp_cooldown_min": 60,       # Independent of RAM cooldown
    "orphan_mcp_excludes": [             # Legitimate PPID=1 daemons to ignore
        "claude-peers", "claude-plugins-mcp",
    ],
}


# ─── Data Models ──────────────────────────────────────────────────────────

@dataclass
class ProcessInfo:
    """Snapshot of a single process."""
    pid: int
    cpu_pct: float
    mem_pct: float
    rss_kb: int
    tty: str
    command: str = ""           # Full command string
    is_claude: bool = False     # True if this is a Claude Code session
    elapsed: str = ""
    ppid: int = 0
    cwd: Optional[str] = None
    session_id: Optional[str] = None   # Claude-only
    version: Optional[str] = None      # Claude-only
    has_revoked_fds: bool = False      # Claude-only
    is_orphaned: bool = False          # Claude-only


@dataclass
class PIDTrackingState:
    """Rolling CPU + RAM state for a single PID."""
    pid: int
    hot_count: int = 0
    total_checks: int = 0
    first_seen: str = ""
    last_check: str = ""
    last_cpu: float = 0.0
    last_alert_time: Optional[str] = None
    cwd: Optional[str] = None
    session_id: Optional[str] = None
    # --- RAM tracking (extension) ---
    rss_samples: list = field(default_factory=list)      # [(iso_ts, rss_kb), ...]
    rss_hot_count: int = 0                               # consecutive checks over rss_alert_mb
    last_rss_kb: int = 0
    peak_rss_kb: int = 0
    last_rss_alert_time: Optional[str] = None            # highest-tier RSS alert cooldown
    last_rss_severity: Optional[str] = None              # "warn" | "alert" | "critical"
    last_growth_alert_time: Optional[str] = None         # growth-slope alert cooldown


# ─── Process Discovery ────────────────────────────────────────────────────

# Always exclude these — internal Claude infrastructure, not sessions
CLAUDE_INFRA_EXCLUDE = re.compile(r"claude-peers|claude-plugins|grep.*claude")

# Heuristic for MCP server command-line fragments. Matches the
# anthropics/claude-code #33947 / #26658 orphan-accumulation pattern.
MCP_HINTS_RE = re.compile(
    r"@modelcontextprotocol/|/mcp-server|/mcp/|"
    r"\bclaude[- ]mcp\b|\bmcp-proxy\b|\bmcp_server\b"
)


def _is_claude_session(command: str) -> bool:
    """Detect a Claude Code CLI session from its command string."""
    if CLAUDE_INFRA_EXCLUDE.search(command):
        return False
    return bool(re.search(r"\bclaude\b", command))


def _command_basename(command: str) -> str:
    """Extract the basename from a command string for exclude matching."""
    first_token = command.split()[0] if command else ""
    return first_token.rsplit("/", 1)[-1]


class ProcessPoller:
    """Discovers and enriches user processes for CPU monitoring."""

    def poll(self, config: dict) -> list[ProcessInfo]:
        """Run ps and return candidate processes.

        Claude sessions are always included. When monitor_all_processes is on,
        any other process above cpu_floor_pct is also included (minus excludes).
        """
        try:
            result = subprocess.run(
                ["ps", "aux"],
                capture_output=True, text=True, timeout=10
            )
        except (subprocess.TimeoutExpired, OSError):
            return []

        monitor_all = config.get("monitor_all_processes", True)
        cpu_floor = float(config.get("cpu_floor_pct", 5))
        excludes = set(config.get("exclude_commands", []))

        processes = []
        for line in result.stdout.strip().split("\n")[1:]:
            parts = line.split()
            if len(parts) < 11:
                continue
            command = " ".join(parts[10:])
            is_claude = _is_claude_session(command)

            # Decide whether to include this process
            if not is_claude:
                if not monitor_all:
                    continue
                try:
                    cpu_pct = float(parts[2])
                except (ValueError, IndexError):
                    continue
                if cpu_pct < cpu_floor:
                    continue
                # Skip excluded commands (basename match)
                basename = _command_basename(command)
                if basename in excludes:
                    continue
                # Skip our own watchdog and grep noise
                if "phroura" in command or "ps aux" in command:
                    continue

            try:
                processes.append(ProcessInfo(
                    pid=int(parts[1]),
                    cpu_pct=float(parts[2]),
                    mem_pct=float(parts[3]),
                    rss_kb=int(parts[5]),
                    tty=parts[6],
                    command=command,
                    is_claude=is_claude,
                ))
            except (ValueError, IndexError):
                continue
        return processes

    def enrich(self, proc: ProcessInfo, config: dict) -> ProcessInfo:
        """Add cwd, elapsed, and (for Claude) session_id, version, revoked-fd."""
        # Elapsed time and PPID — cheap, always run
        try:
            result = subprocess.run(
                ["ps", "-o", "ppid=,etime=", "-p", str(proc.pid)],
                capture_output=True, text=True, timeout=5
            )
            line = result.stdout.strip()
            if line:
                parts = line.split()
                if len(parts) >= 2:
                    proc.ppid = int(parts[0])
                    proc.elapsed = parts[1]
        except (subprocess.TimeoutExpired, OSError, ValueError):
            pass

        # Full lsof scan — only for Claude processes (expensive, Claude-specific signals)
        if proc.is_claude:
            try:
                result = subprocess.run(
                    ["lsof", "-p", str(proc.pid)],
                    capture_output=True, text=True, timeout=5
                )
                for line in result.stdout.split("\n"):
                    # CWD
                    if " cwd " in line:
                        parts = line.split()
                        if len(parts) >= 9:
                            proc.cwd = parts[-1]

                    # Version from binary path
                    if "share/claude/versions/" in line:
                        m = re.search(r"versions/([\d.]+)", line)
                        if m:
                            proc.version = m.group(1)

                    # Session JSONL files
                    if ".jsonl" in line and "projects" in line:
                        m = re.search(r"/([a-f0-9-]{36})\.jsonl", line)
                        if m:
                            proc.session_id = m.group(1)

                    # Task directory (fallback session ID)
                    if not proc.session_id and "/tasks/" in line:
                        m = re.search(r"/tasks/([a-f0-9-]{36})", line)
                        if m:
                            proc.session_id = m.group(1)

                    # Revoked file descriptors (Claude stdio-revocation bug signal)
                    if config.get("enable_revoked_check", True):
                        if "(revoked)" in line:
                            proc.has_revoked_fds = True

            except (subprocess.TimeoutExpired, OSError):
                pass

            # Orphaned: no TTY (Claude-specific — the revocation loop signal)
            if proc.tty in ("??", "-"):
                proc.is_orphaned = True

        return proc

    def find_orphan_mcp_processes(self, config: dict) -> list[dict]:
        """Return list of PPID=1 node/python MCP servers that look reparented.

        Each entry: {pid, rss_kb, command}. Uses a single `ps` scan and
        filters the excludes list (claude-peers, claude-plugins-mcp, etc.).
        """
        excludes = set(config.get("orphan_mcp_excludes", []))
        orphans: list[dict] = []

        try:
            result = subprocess.run(
                ["ps", "-eo", "pid=,ppid=,rss=,command="],
                capture_output=True, text=True, timeout=10,
            )
        except (subprocess.TimeoutExpired, OSError):
            return orphans

        for line in result.stdout.strip().split("\n"):
            parts = line.split(None, 3)
            if len(parts) < 4:
                continue
            try:
                pid = int(parts[0])
                ppid = int(parts[1])
                rss_kb = int(parts[2])
            except ValueError:
                continue
            if ppid != 1:
                continue
            command = parts[3]

            # Exclude legit long-running PPID=1 daemons
            basename = _command_basename(command)
            if basename in excludes:
                continue
            if any(ex in command for ex in excludes):
                continue

            # Must look like an MCP server — node or python process
            # whose command matches the hint regex.
            if not MCP_HINTS_RE.search(command):
                continue

            orphans.append({
                "pid": pid,
                "rss_kb": rss_kb,
                "command": command[:200],
            })
        return orphans


# ─── State Tracker ────────────────────────────────────────────────────────

class StateTracker:
    """Maintains rolling per-PID CPU state with persistence."""

    def __init__(self, state_file: Path, max_pids: int = 100):
        self.state_file = state_file
        self.max_pids = max_pids
        self.states: dict[int, PIDTrackingState] = {}
        # System-wide cooldown stamps keyed by alert-type (orphan-MCP, etc.).
        self.global_state: dict[str, str] = {}
        self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                # The new schema stores per-PID state under "pids" with a
                # sibling "global" blob for system-wide signals. Legacy state
                # files stored PIDs at the top level — detect and migrate.
                if "pids" in data and isinstance(data["pids"], dict):
                    pid_blob = data["pids"]
                    self.global_state = data.get("global", {})
                else:
                    pid_blob = data
                    self.global_state = {}

                for pid_str, s in pid_blob.items():
                    if not pid_str.isdigit():
                        continue
                    pid = int(pid_str)
                    # rss_samples stored as [[ts, rss_kb], ...] in JSON.
                    # Tolerate corrupt samples (non-int, None, missing fields)
                    # rather than crashing the whole state load.
                    raw_samples = s.get("rss_samples") or []
                    samples: list = []
                    for pair in raw_samples:
                        if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                            continue
                        try:
                            samples.append((str(pair[0]), int(pair[1])))
                        except (TypeError, ValueError):
                            continue
                    self.states[pid] = PIDTrackingState(
                        pid=pid,
                        hot_count=s.get("hot_count", 0),
                        total_checks=s.get("total_checks", 0),
                        first_seen=s.get("first_seen", ""),
                        last_check=s.get("last_check", ""),
                        last_cpu=s.get("last_cpu", 0.0),
                        last_alert_time=s.get("last_alert_time"),
                        cwd=s.get("cwd"),
                        session_id=s.get("session_id"),
                        rss_samples=samples,
                        rss_hot_count=s.get("rss_hot_count", 0),
                        last_rss_kb=s.get("last_rss_kb", 0),
                        peak_rss_kb=s.get("peak_rss_kb", 0),
                        last_rss_alert_time=s.get("last_rss_alert_time"),
                        last_rss_severity=s.get("last_rss_severity"),
                        last_growth_alert_time=s.get("last_growth_alert_time"),
                    )
            except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                # Corrupt state file — start clean rather than crashing the daemon.
                self.states = {}
                self.global_state = {}
        else:
            self.global_state = {}

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._prune_dead()
        pid_blob = {str(pid): asdict(s) for pid, s in self.states.items()}
        data = {"pids": pid_blob, "global": self.global_state}
        # Atomic write: temp file + rename (safe under SIGKILL)
        tmp = self.state_file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2))
        tmp.replace(self.state_file)

    def _prune_dead(self):
        """Remove PIDs that no longer exist."""
        try:
            result = subprocess.run(
                ["ps", "-o", "pid=", "-A"],
                capture_output=True, text=True, timeout=5
            )
            alive = set()
            for line in result.stdout.strip().split("\n"):
                line = line.strip()
                if line.isdigit():
                    alive.add(int(line))
            dead = [pid for pid in self.states if pid not in alive]
            for pid in dead:
                del self.states[pid]
        except (subprocess.TimeoutExpired, OSError):
            return

        if len(self.states) > self.max_pids:
            sorted_states = sorted(
                self.states.items(),
                key=lambda x: x[1].last_check,
                reverse=True,
            )
            self.states = dict(sorted_states[: self.max_pids])

    def update(
        self,
        proc: "ProcessInfo",
        cpu_threshold: float,
        config: Optional[dict] = None,
    ) -> PIDTrackingState:
        now = datetime.now().isoformat()

        if proc.pid not in self.states:
            self.states[proc.pid] = PIDTrackingState(
                pid=proc.pid,
                first_seen=now,
            )

        state = self.states[proc.pid]
        state.last_check = now
        state.last_cpu = proc.cpu_pct
        state.total_checks += 1
        state.cwd = proc.cwd or state.cwd
        state.session_id = proc.session_id or state.session_id

        if proc.cpu_pct >= cpu_threshold:
            state.hot_count += 1
        else:
            state.hot_count = 0

        # --- RAM sampling ---
        state.last_rss_kb = proc.rss_kb
        if proc.rss_kb > state.peak_rss_kb:
            state.peak_rss_kb = proc.rss_kb

        state.rss_samples.append((now, int(proc.rss_kb)))
        window = int((config or {}).get("rss_window_samples", 20))
        if len(state.rss_samples) > window:
            # Drop oldest until we fit (FIFO). Slicing is cheap at this scale.
            state.rss_samples = state.rss_samples[-window:]

        rss_alert_kb = int((config or {}).get("rss_alert_mb", 1200)) * 1024
        if proc.rss_kb >= rss_alert_kb:
            state.rss_hot_count += 1
        else:
            state.rss_hot_count = 0

        return state

    def should_alert(self, state: PIDTrackingState, config: dict) -> bool:
        if state.hot_count < config["consecutive_checks"]:
            return False

        if state.last_alert_time:
            try:
                last = datetime.fromisoformat(state.last_alert_time)
                cooldown = timedelta(minutes=config["cooldown_min"])
                if datetime.now() - last < cooldown:
                    return False
            except ValueError:
                pass

        return True

    def mark_alerted(self, pid: int):
        if pid in self.states:
            self.states[pid].last_alert_time = datetime.now().isoformat()

    # ─── RAM detection ────────────────────────────────────────────────────

    _SEVERITY_RANK = {"warn": 0, "alert": 1, "critical": 2}

    def classify_rss_severity(
        self, state: PIDTrackingState, config: dict
    ) -> Optional[str]:
        """Return 'warn' | 'alert' | 'critical' | None for this process.

        Picks the highest tier whose threshold is breached. The `alert`
        and `critical` tiers require `rss_hot_count >= consecutive_checks`
        (sustained breach), while `warn` fires on any single sample above
        the warn line.

        All three tiers share a single cooldown (`rss_cooldown_min`) and
        the tier-rank map: a cooldown suppresses only same-or-lower-tier
        re-alerts, so an escalation from `alert` to `critical` still fires.
        """
        rss_kb = state.last_rss_kb
        warn_kb = int(config.get("rss_warn_mb", 800)) * 1024
        alert_kb = int(config.get("rss_alert_mb", 1200)) * 1024
        critical_kb = int(config.get("rss_critical_mb", 2000)) * 1024
        consecutive = int(config.get("consecutive_checks", 3))

        # Highest tier first — "critical" wins when multiple thresholds apply.
        if rss_kb >= critical_kb and state.rss_hot_count >= consecutive:
            severity = "critical"
        elif rss_kb >= alert_kb and state.rss_hot_count >= consecutive:
            severity = "alert"
        elif rss_kb >= warn_kb:
            severity = "warn"
        else:
            return None

        # Cooldown suppression: rank-based so escalation always fires.
        # Example: last was "alert", now "critical" → rank 2 > rank 1 → fire.
        #          last was "critical", now "alert" → rank 1 < rank 2 → suppress.
        #          last was "warn", now "warn" → rank 0 == rank 0 → suppress.
        if state.last_rss_alert_time:
            try:
                last = datetime.fromisoformat(state.last_rss_alert_time)
                cooldown = timedelta(minutes=int(config.get("rss_cooldown_min", 60)))
                if datetime.now() - last < cooldown:
                    prev = state.last_rss_severity or ""
                    prev_rank = self._SEVERITY_RANK.get(prev, -1)
                    cur_rank = self._SEVERITY_RANK.get(severity, 0)
                    if prev_rank >= cur_rank:
                        return None
            except (ValueError, TypeError):
                pass

        return severity

    def mark_rss_alerted(self, pid: int, severity: str):
        if pid in self.states:
            st = self.states[pid]
            st.last_rss_alert_time = datetime.now().isoformat()
            st.last_rss_severity = severity

    def rss_growth_slope(
        self, state: PIDTrackingState, config: dict
    ) -> Optional[float]:
        """MB/minute slope across the oldest→newest sample pair, or None.

        Returns None when we lack enough samples or the elapsed window is
        too narrow to compute a meaningful slope.
        """
        min_samples = int(config.get("rss_growth_min_samples", 5))
        if len(state.rss_samples) < min_samples:
            return None

        first_ts, first_kb = state.rss_samples[0]
        last_ts, last_kb = state.rss_samples[-1]
        try:
            t0 = datetime.fromisoformat(first_ts)
            t1 = datetime.fromisoformat(last_ts)
            seconds = (t1 - t0).total_seconds()
        except (ValueError, TypeError):
            # TypeError catches mixed naive/aware datetimes (e.g., from a
            # state.json written by a different Python version). Silently
            # skip slope for this cycle rather than crashing the poll.
            return None

        if seconds < 30:
            return None  # window too short (or clock moved backward)

        delta_mb = (last_kb - first_kb) / 1024.0
        minutes = seconds / 60.0
        return delta_mb / minutes

    def should_alert_rss_growth(
        self, state: PIDTrackingState, config: dict, slope_mb_per_min: float
    ) -> bool:
        if slope_mb_per_min < float(config.get("rss_growth_mb_per_min", 60)):
            return False

        if state.last_growth_alert_time:
            try:
                last = datetime.fromisoformat(state.last_growth_alert_time)
                cooldown = timedelta(minutes=int(config.get("rss_cooldown_min", 60)))
                if datetime.now() - last < cooldown:
                    return False
            except ValueError:
                pass
        return True

    def mark_growth_alerted(self, pid: int):
        if pid in self.states:
            self.states[pid].last_growth_alert_time = datetime.now().isoformat()

    # ─── Orphan MCP detection ─────────────────────────────────────────────

    def should_alert_orphan_mcp(self, orphan_count: int, config: dict) -> bool:
        threshold = int(config.get("orphan_mcp_threshold", 15))
        if orphan_count < threshold:
            return False

        last_ts = self.global_state.get("last_orphan_mcp_alert_time")
        if last_ts:
            try:
                last = datetime.fromisoformat(last_ts)
                cooldown = timedelta(
                    minutes=int(config.get("orphan_mcp_cooldown_min", 60))
                )
                if datetime.now() - last < cooldown:
                    return False
            except (ValueError, TypeError):
                pass
        return True

    def mark_orphan_mcp_alerted(self):
        self.global_state["last_orphan_mcp_alert_time"] = datetime.now().isoformat()


# ─── Alerter ──────────────────────────────────────────────────────────────

class Alerter:
    """Multi-channel alert dispatch."""

    def __init__(self, config: dict, logger: logging.Logger):
        self.config = config
        self.logger = logger

    def _dispatch(self, log_msg: str, title: str, body: str, sound: str = "Basso"):
        """Send alert through all enabled channels."""
        self.logger.warning(log_msg)
        if self.config.get("enable_macos_notify", True):
            self._macos_notify(title, body, sound)
        if self.config.get("enable_telegram", True):
            self._telegram_notify(log_msg)

    def alert(self, proc: ProcessInfo, state: PIDTrackingState):
        msg = self._format_message(proc, state)
        label = "Claude" if proc.is_claude else _command_basename(proc.command)
        body_lines = [
            f"{proc.cpu_pct:.0f}% CPU for "
            f"{state.hot_count * self.config['poll_interval_sec']}s+",
        ]
        if proc.cwd:
            body_lines.append(f"CWD: {proc.cwd.replace(str(Path.home()), '~')}")
        body_lines.append(f"kill -9 {proc.pid}")
        body = "\n".join(body_lines)
        self._dispatch(msg, f"Phroura: {label} {proc.pid} stuck", body, "Basso")

    def alert_orphaned(self, proc: ProcessInfo):
        msg = self._format_orphan_message(proc)
        body = f"Terminal closed, process persists.\nkill -9 {proc.pid}"
        self._dispatch(msg, f"Phroura: Claude {proc.pid} orphaned", body, "Purr")

    # ─── RAM alerts ───────────────────────────────────────────────────────

    def alert_rss(
        self, proc: ProcessInfo, state: PIDTrackingState, severity: str
    ):
        """Absolute-RSS alert.

        severity='warn'    → log only, no notification (observe in logs)
        severity='alert'   → log + macOS + Telegram (Basso)
        severity='critical'→ log + macOS + Telegram (Sosumi), louder title
        """
        rss_mb = proc.rss_kb // 1024
        peak_mb = state.peak_rss_kb // 1024
        label = "Claude" if proc.is_claude else _command_basename(proc.command)[:40]

        lines = [
            f"RAM {severity.upper()}: {label} PID {proc.pid} at {rss_mb} MB",
            f"  Peak: {peak_mb} MB  |  CPU: {proc.cpu_pct:.0f}%",
            f"  Elapsed: {proc.elapsed}",
        ]
        if not proc.is_claude and proc.command:
            lines.append(f"  Command: {proc.command[:120]}")
        if proc.cwd:
            lines.append(f"  CWD: {proc.cwd.replace(str(Path.home()), '~')}")
        if proc.session_id:
            lines.append(f"  Session: {proc.session_id[:8]}")
        if proc.version:
            lines.append(f"  Version: {proc.version}")
        if severity == "critical":
            lines.append(f"  Action: kill -9 {proc.pid}")
        msg = "\n".join(lines)

        if severity == "warn":
            # Log-only — shows up in cpu-watchdog.log and status.sh trails.
            self.logger.info(msg)
            return

        title_prefix = "CRITICAL" if severity == "critical" else ""
        title = (
            f"Phroura: {title_prefix} {label} {proc.pid} RAM {rss_mb} MB"
        ).strip()
        body_lines = [f"RSS {rss_mb} MB (peak {peak_mb} MB)"]
        if proc.cwd:
            body_lines.append(f"CWD: {proc.cwd.replace(str(Path.home()), '~')}")
        if severity == "critical":
            body_lines.append(f"kill -9 {proc.pid}")
        sound = "Sosumi" if severity == "critical" else "Basso"
        self._dispatch(msg, title, "\n".join(body_lines), sound)

    def alert_rss_growth(
        self,
        proc: ProcessInfo,
        state: PIDTrackingState,
        slope_mb_per_min: float,
    ):
        """Growth-rate alert — catches leaks before they reach the ceiling."""
        rss_mb = proc.rss_kb // 1024
        label = "Claude" if proc.is_claude else _command_basename(proc.command)[:40]

        # Rough window span for context in the message.
        first_ts = state.rss_samples[0][0] if state.rss_samples else ""
        window_mb_start = (
            state.rss_samples[0][1] // 1024 if state.rss_samples else rss_mb
        )

        lines = [
            f"RAM LEAK: {label} PID {proc.pid} growing +{slope_mb_per_min:.0f} MB/min",
            f"  Current: {rss_mb} MB  |  Window start: {window_mb_start} MB",
            f"  Samples: {len(state.rss_samples)} (since {first_ts[:19]})",
        ]
        if proc.cwd:
            lines.append(f"  CWD: {proc.cwd.replace(str(Path.home()), '~')}")
        if proc.session_id:
            lines.append(f"  Session: {proc.session_id[:8]}")
        msg = "\n".join(lines)

        body = (
            f"+{slope_mb_per_min:.0f} MB/min\n"
            f"Now: {rss_mb} MB  (start: {window_mb_start} MB)"
        )
        self._dispatch(
            msg, f"Phroura: {label} {proc.pid} RAM leak (+{slope_mb_per_min:.0f} MB/min)",
            body, "Basso",
        )

    def alert_orphan_mcp(self, orphans: list[dict]):
        """Orphan MCP cluster alert (advisory — no pkill suggestion)."""
        count = len(orphans)
        total_mb = sum(o["rss_kb"] for o in orphans) // 1024
        sample_pids = ", ".join(str(o["pid"]) for o in orphans[:8])

        lines = [
            f"ORPHAN MCP CLUSTER: {count} reparented MCP servers ({total_mb} MB total)",
            f"  Sample PIDs: {sample_pids}" + ("..." if count > 8 else ""),
        ]
        # Show a couple of representative command strings so Tom can
        # spot which MCP is leaking.
        for o in orphans[:3]:
            lines.append(
                f"  PID {o['pid']}: {o['rss_kb']//1024} MB  {o['command'][:100]}"
            )
        msg = "\n".join(lines)

        body = (
            f"{count} orphan MCP servers, {total_mb} MB total\n"
            f"PIDs: {sample_pids}"
        )
        self._dispatch(
            msg, f"Phroura: {count} orphaned MCP servers ({total_mb} MB)",
            body, "Purr",
        )

    def _format_message(self, proc: ProcessInfo, state: PIDTrackingState) -> str:
        interval = self.config["poll_interval_sec"]
        label = "Claude" if proc.is_claude else _command_basename(proc.command)[:40]
        lines = [
            f"CPU WATCHDOG: {label} PID {proc.pid} stuck at {proc.cpu_pct:.0f}% CPU",
            f"  Duration: {state.hot_count} consecutive checks ({state.hot_count * interval}s+)",
            f"  Elapsed: {proc.elapsed}",
            f"  Memory: {proc.mem_pct:.1f}% ({proc.rss_kb // 1024}MB RSS)",
            f"  TTY: {proc.tty}",
        ]
        if not proc.is_claude and proc.command:
            lines.append(f"  Command: {proc.command[:120]}")
        if proc.cwd:
            cwd = proc.cwd.replace(str(Path.home()), "~")
            lines.append(f"  CWD: {cwd}")
        if proc.session_id:
            lines.append(f"  Session: {proc.session_id[:8]}")
        if proc.version:
            lines.append(f"  Version: {proc.version}")
        if proc.has_revoked_fds:
            lines.append("  WARNING: Has revoked file descriptors (terminal closed?)")
        lines.append(f"  Action: kill -9 {proc.pid}")
        return "\n".join(lines)

    def _format_orphan_message(self, proc: ProcessInfo) -> str:
        lines = [
            f"ORPHAN DETECTED: Claude PID {proc.pid} has revoked fds",
            f"  CPU: {proc.cpu_pct:.0f}%  |  Memory: {proc.mem_pct:.1f}%",
            f"  Elapsed: {proc.elapsed}",
        ]
        if proc.cwd:
            cwd = proc.cwd.replace(str(Path.home()), "~")
            lines.append(f"  CWD: {cwd}")
        lines.append("  Terminal closed but process persists.")
        lines.append(f"  Action: kill -9 {proc.pid}")
        return "\n".join(lines)

    def _macos_notify(self, title: str, body: str, sound: str):
        """Send macOS notification via alerter (vjeantet/alerter).

        Uses alerter instead of terminal-notifier so Phroura has an independent
        bundle ID (fr.vjeantet.alerter) from any other notification source on
        the system (e.g. terminal-notifier used by the terminal-title hook).
        This lets the user grant/deny each tool independently in
        System Settings > Notifications.

        alerter posts persistent alert-style notifications by default. Use
        --timeout to auto-dismiss so the process doesn't block waiting for
        user interaction.
        """
        try:
            subprocess.run(
                [
                    "alerter",
                    "--title", title,
                    "--message", body,
                    "--sound", "default" if sound else "",
                    "--timeout", "10",
                ],
                timeout=15, capture_output=True,
            )
        except (subprocess.TimeoutExpired, OSError, FileNotFoundError) as e:
            self.logger.debug(f"macOS notify failed: {e}")

    def _telegram_notify(self, msg: str):
        token = self._get_telegram_token()
        chat_id = self.config.get("telegram_chat_id")
        if not token or not chat_id:
            return

        try:
            import requests
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            resp = requests.post(url, json={
                "chat_id": chat_id,
                "text": msg,
                "disable_notification": False,
            }, timeout=10)
            result = resp.json()
            if not result.get("ok"):
                self.logger.warning(f"Telegram API error: {result}")
        except Exception as e:
            self.logger.debug(f"Telegram notify failed: {e}")

    def _get_telegram_token(self) -> Optional[str]:
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if token:
            return token
        secrets = Path.home() / ".config" / "env" / "secrets.env"
        if secrets.exists():
            for line in secrets.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, val = line.partition("=")
                key = key.strip()
                if key.startswith("export "):
                    key = key[7:].strip()
                if key == "TELEGRAM_BOT_TOKEN":
                    return val.strip().strip("'\"")
        return None


# ─── Main Loop ────────────────────────────────────────────────────────────

class Phroura:
    """Main watchdog daemon."""

    def __init__(self, config: dict):
        self.config = config
        self.poller = ProcessPoller()
        self.tracker = StateTracker(
            STATE_FILE,
            max_pids=config.get("max_tracked_pids", 100),
        )
        self.logger = self._setup_logging()
        self.alerter = Alerter(config, self.logger)
        self._running = True
        signal.signal(signal.SIGTERM, self._handle_signal)
        signal.signal(signal.SIGINT, self._handle_signal)

    def _setup_logging(self) -> logging.Logger:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        logger = logging.getLogger("phroura")
        logger.setLevel(logging.INFO)
        handler = logging.handlers.TimedRotatingFileHandler(
            LOG_FILE, when="midnight",
            backupCount=self.config.get("log_retention_days", 7),
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        ))
        logger.addHandler(handler)
        # Also log to stderr for launchd capture
        stderr_handler = logging.StreamHandler(sys.stderr)
        stderr_handler.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        logger.addHandler(stderr_handler)
        return logger

    def _handle_signal(self, signum, frame):
        self.logger.info(f"Received signal {signum}, shutting down")
        self._running = False

    def run_once(self):
        """Single poll-check-alert cycle."""
        processes = self.poller.poll(self.config)
        cpu_threshold = self.config["cpu_threshold_pct"]
        ram_enabled = self.config.get("enable_ram_watchdog", True)
        rss_floor_kb = int(self.config.get("rss_claude_floor_mb", 100)) * 1024

        for proc in processes:
            proc = self.poller.enrich(proc, self.config)
            state = self.tracker.update(proc, cpu_threshold, self.config)

            # Sustained high CPU alert
            if self.tracker.should_alert(state, self.config):
                self.alerter.alert(proc, state)
                self.tracker.mark_alerted(proc.pid)

            # Orphaned Claude process with revoked fds — alert on cooldown only,
            # no hot_count requirement (the stdio revocation loop is the signal)
            elif proc.is_claude and proc.has_revoked_fds and proc.cpu_pct >= 1.0:
                cooldown_ok = True
                if state.last_alert_time:
                    try:
                        last = datetime.fromisoformat(state.last_alert_time)
                        if datetime.now() - last < timedelta(minutes=self.config["cooldown_min"]):
                            cooldown_ok = False
                    except ValueError:
                        pass
                if cooldown_ok:
                    self.alerter.alert_orphaned(proc)
                    self.tracker.mark_alerted(proc.pid)

            # --- RAM checks (absolute + growth) ---
            # Skip processes below the floor to avoid log spam from tiny helpers.
            if ram_enabled and proc.rss_kb >= rss_floor_kb:
                severity = self.tracker.classify_rss_severity(state, self.config)
                if severity:
                    self.alerter.alert_rss(proc, state, severity)
                    # Stamp cooldown for every tier including warn — otherwise
                    # a process parked at 850 MB logs every poll forever.
                    self.tracker.mark_rss_alerted(proc.pid, severity)

                slope = self.tracker.rss_growth_slope(state, self.config)
                if slope is not None and self.tracker.should_alert_rss_growth(
                    state, self.config, slope
                ):
                    self.alerter.alert_rss_growth(proc, state, slope)
                    self.tracker.mark_growth_alerted(proc.pid)

        # --- Global orphan-MCP sweep (once per cycle) ---
        if self.config.get("enable_orphan_mcp_watchdog", True):
            orphans = self.poller.find_orphan_mcp_processes(self.config)
            if self.tracker.should_alert_orphan_mcp(len(orphans), self.config):
                self.alerter.alert_orphan_mcp(orphans)
                self.tracker.mark_orphan_mcp_alerted()

        self.tracker.save()

    def run_daemon(self):
        """Continuous monitoring loop."""
        interval = self.config["poll_interval_sec"]
        self.logger.info(
            f"Phroura starting: poll={interval}s, "
            f"threshold={self.config['cpu_threshold_pct']}%, "
            f"consecutive={self.config['consecutive_checks']}"
        )

        while self._running:
            # Hot-reload config each cycle (toggle telegram, adjust thresholds)
            self.config = load_config()
            self.alerter.config = self.config

            try:
                self.run_once()
            except Exception as e:
                self.logger.error(f"Poll cycle error: {e}", exc_info=True)

            # Interruptible sleep
            interval = self.config["poll_interval_sec"]
            for _ in range(interval):
                if not self._running:
                    break
                time.sleep(1)

        self.logger.info("Phroura stopped")
        self.tracker.save()

    def status(self) -> str:
        """Return human-readable status of tracked processes."""
        lines = ["Phroura Status", "=" * 60]

        # Current tracked processes
        processes = self.poller.poll(self.config)
        claude_count = sum(1 for p in processes if p.is_claude)
        other_count = len(processes) - claude_count
        lines.append(
            f"Active: {claude_count} Claude sessions, {other_count} other tracked"
        )

        # Orphan MCP summary (cheap single scan)
        if self.config.get("enable_orphan_mcp_watchdog", True):
            orphans = self.poller.find_orphan_mcp_processes(self.config)
            if orphans:
                total_mb = sum(o["rss_kb"] for o in orphans) // 1024
                lines.append(
                    f"Orphan MCPs: {len(orphans)} ({total_mb} MB total)"
                )
            else:
                lines.append("Orphan MCPs: 0")
        lines.append("")

        if not self.tracker.states:
            lines.append("No processes currently tracked.")
            return "\n".join(lines)

        for pid, state in sorted(self.tracker.states.items()):
            threshold = self.config["consecutive_checks"]
            if state.hot_count >= threshold:
                hot_indicator = "HOT"
            else:
                hot_indicator = f"{state.hot_count}/{threshold}"
            cwd = (state.cwd or "?").replace(str(Path.home()), "~")
            rss_mb = state.last_rss_kb // 1024
            peak_mb = state.peak_rss_kb // 1024
            lines.append(
                f"  PID {pid:>6}  CPU: {state.last_cpu:5.1f}%  "
                f"RSS: {rss_mb:>5} MB (peak {peak_mb} MB)  "
                f"Hot: {hot_indicator}  Checks: {state.total_checks}"
            )
            lines.append(f"           CWD: {cwd}")

            # Growth slope (if we have enough samples)
            slope = self.tracker.rss_growth_slope(state, self.config)
            if slope is not None and abs(slope) >= 1.0:
                arrow = "+" if slope >= 0 else ""
                lines.append(
                    f"           Growth: {arrow}{slope:.0f} MB/min "
                    f"({len(state.rss_samples)} samples)"
                )

            if state.session_id:
                lines.append(f"           Session: {state.session_id[:8]}")
            if state.last_alert_time:
                lines.append(f"           Last CPU alert: {state.last_alert_time}")
            if state.last_rss_alert_time:
                lines.append(
                    f"           Last RAM alert: {state.last_rss_alert_time} "
                    f"({state.last_rss_severity})"
                )

        return "\n".join(lines)


# ─── CLI ──────────────────────────────────────────────────────────────────

def load_config() -> dict:
    config = dict(DEFAULT_CONFIG)
    if CONFIG_FILE.exists():
        try:
            user_config = json.loads(CONFIG_FILE.read_text())
            config.update(user_config)
        except json.JSONDecodeError:
            pass
    return config


def toggle_config(key: str):
    """Toggle a boolean config value and save to config.json."""
    config = {}
    if CONFIG_FILE.exists():
        try:
            config = json.loads(CONFIG_FILE.read_text())
        except json.JSONDecodeError:
            pass
    current = config.get(key, DEFAULT_CONFIG.get(key))
    config[key] = not current
    CONFIG_FILE.write_text(json.dumps(config, indent=2) + "\n")
    state = "ON" if config[key] else "OFF"
    print(f"{key}: {state}")
    print("(takes effect on the next poll cycle, within 30s)")


def main():
    parser = argparse.ArgumentParser(
        description="Phroura — CPU watchdog for user processes"
    )
    parser.add_argument("--daemon", action="store_true",
                        help="Run continuously (for launchd)")
    parser.add_argument("--status", action="store_true",
                        help="Show tracked process status")
    parser.add_argument("--config", action="store_true",
                        help="Print effective configuration")
    parser.add_argument("--interval", type=int,
                        help="Override poll interval (seconds)")
    parser.add_argument("--threshold", type=float,
                        help="Override CPU threshold (percent)")
    parser.add_argument("--no-telegram", action="store_true",
                        help="Disable Telegram alerts")
    parser.add_argument("--toggle-telegram", action="store_true",
                        help="Toggle Telegram alerts on/off in config.json")
    parser.add_argument("--toggle-ram-watchdog", action="store_true",
                        help="Toggle RAM watchdog on/off in config.json")
    parser.add_argument("--toggle-orphan-mcp", action="store_true",
                        help="Toggle orphan MCP detection on/off in config.json")
    args = parser.parse_args()

    config = load_config()

    # CLI overrides
    if args.interval:
        config["poll_interval_sec"] = args.interval
    if args.threshold:
        config["cpu_threshold_pct"] = args.threshold
    if args.no_telegram:
        config["enable_telegram"] = False

    if args.toggle_telegram:
        toggle_config("enable_telegram")
        return

    if args.toggle_ram_watchdog:
        toggle_config("enable_ram_watchdog")
        return

    if args.toggle_orphan_mcp:
        toggle_config("enable_orphan_mcp_watchdog")
        return

    if args.config:
        print(json.dumps(config, indent=2))
        return

    phroura = Phroura(config)

    if args.status:
        print(phroura.status())
        return

    if args.daemon:
        phroura.run_daemon()
    else:
        # Single dry-run check
        print("Phroura — single poll (dry run)")
        print()
        phroura.run_once()
        print(phroura.status())


if __name__ == "__main__":
    main()
