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
from dataclasses import dataclass, asdict
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
    """Rolling CPU state for a single PID."""
    pid: int
    hot_count: int = 0
    total_checks: int = 0
    first_seen: str = ""
    last_check: str = ""
    last_cpu: float = 0.0
    last_alert_time: Optional[str] = None
    cwd: Optional[str] = None
    session_id: Optional[str] = None


# ─── Process Discovery ────────────────────────────────────────────────────

# Always exclude these — internal Claude infrastructure, not sessions
CLAUDE_INFRA_EXCLUDE = re.compile(r"claude-peers|claude-plugins|grep.*claude")


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


# ─── State Tracker ────────────────────────────────────────────────────────

class StateTracker:
    """Maintains rolling per-PID CPU state with persistence."""

    def __init__(self, state_file: Path, max_pids: int = 100):
        self.state_file = state_file
        self.max_pids = max_pids
        self.states: dict[int, PIDTrackingState] = {}
        self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                data = json.loads(self.state_file.read_text())
                for pid_str, s in data.items():
                    pid = int(pid_str)
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
                    )
            except (json.JSONDecodeError, KeyError):
                self.states = {}

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self._prune_dead()
        data = {str(pid): asdict(s) for pid, s in self.states.items()}
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

    def update(self, proc: "ProcessInfo", threshold: float) -> PIDTrackingState:
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

        if proc.cpu_pct >= threshold:
            state.hot_count += 1
        else:
            state.hot_count = 0

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
        threshold = self.config["cpu_threshold_pct"]

        for proc in processes:
            proc = self.poller.enrich(proc, self.config)
            state = self.tracker.update(proc, threshold)

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
            lines.append(
                f"  PID {pid:>6}  CPU: {state.last_cpu:5.1f}%  "
                f"Hot: {hot_indicator}  Checks: {state.total_checks}  "
                f"CWD: {cwd}"
            )
            if state.session_id:
                lines.append(f"           Session: {state.session_id[:8]}")
            if state.last_alert_time:
                lines.append(f"           Last alert: {state.last_alert_time}")

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
