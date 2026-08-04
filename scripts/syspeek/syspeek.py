#!/usr/bin/env python3
"""syspeek — macOS system resource monitor. Claudicle-aware.

Single-command system snapshot: categorizes processes, shows resource usage,
records physical state as durable memory. JSON output is a superset of
Kothar's SystemHealthReport interface.

Usage:
    syspeek                       # Colored terminal snapshot
    syspeek --top 15              # Show top N processes (default: 10)
    syspeek --json                # JSON output (Kothar-compatible)
    syspeek --record              # Snapshot + persist to memory + JSONL
    syspeek --kill PID            # SIGTERM with safety checks
    syspeek --history             # Last 24h from JSONL
    syspeek --daemon              # Loop every N minutes, record each
    syspeek --category claude     # Filter to one category
"""

import argparse
import fcntl
import gzip
import json
import logging
import os
import re
import signal
import sqlite3
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, date, timedelta
from enum import Enum
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
LOG_DIR = SCRIPT_DIR / "logs"
LOG_FILE = LOG_DIR / "syspeek.log"

SOUL_MD = Path.home() / ".claudicle" / "soul" / "soul.md"
MEMORY_DB = Path.home() / ".claudicle" / "daemon" / "memory" / "memory.db"

SCHEMA_VERSION = 2
DEFAULT_TOP_N = 10
DEFAULT_INTERVAL_MIN = 5
ROTATION_DAYS = 7           # gzip .jsonl older than this
ARCHIVE_RETENTION_DAYS = 30  # delete .jsonl.gz older than this
MEMDB_MIN_INTERVAL_SEC = 3600  # daemon: at most one memory.db row per hour
DATA_VOLUME = "/System/Volumes/Data"

# Stale Claude session detection: transcript mtime is the activity signal
# (TTY atime is useless — the Claude TUI polls the terminal constantly).
STALE_SESSION_DAYS = 10
SPECULATOR_SESSIONS = Path.home() / ".claude" / "scripts" / "speculator" / "data" / "ghostty-sessions.json"
PROJECTS_DIR = Path.home() / ".claude" / "projects"
STALE_ALERT_COOLDOWN_SEC = 86400  # one notification per session per day

# Curated directories for `--disk` hotspot listing. Deep scans belong to
# Mole (`mo analyze`) and gdu-go — this list is intentionally shallow.
DISK_HOTSPOT_DIRS = [
    "~/Library/Caches",
    "~/Library/Developer",
    "~/.ollama",
    "~/.claude",
    "~/Desktop/Programming",
]

# ---------------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------------

class Category(Enum):
    """Process categories with display metadata."""
    #       (label,      icon, ansi_color)
    CLAUDE  = ("Claude Code",  ">>", "\033[38;5;141m")
    CHROME  = ("Browsers",     "@@", "\033[38;5;214m")
    IDE     = ("IDEs/Terms",   "[]", "\033[38;5;156m")
    ML      = ("ML/Inference", "**", "\033[38;5;196m")
    DEVSERV = ("Dev Servers",  "//", "\033[38;5;39m")
    SYSTEM  = ("System",       "..", "\033[38;5;245m")
    OTHER   = ("Other",        "--", "\033[38;5;252m")

    def __init__(self, label: str, icon: str, color: str):
        self.label = label
        self.icon = icon
        self.color = color


@dataclass
class ProcessInfo:
    pid: int
    ppid: int
    cpu: float
    mem: float
    rss_kb: int
    comm: str
    category: Category = Category.OTHER


@dataclass
class MemoryInfo:
    total_bytes: int
    page_size: int
    pages_active: int
    pages_inactive: int
    pages_wired: int
    pages_compressed: int
    pages_free: int
    pages_speculative: int

    @property
    def used_bytes(self) -> int:
        # macOS memory: total minus truly free pages.
        # Compressor pages are already counted within active/inactive/wired,
        # so we must NOT add them again. Use: total - (free + speculative) * page_size.
        free_bytes = (self.pages_free + self.pages_speculative) * self.page_size
        return max(0, self.total_bytes - free_bytes)

    @property
    def used_pct(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100

    @property
    def app_bytes(self) -> int:
        """Application memory (active + inactive, excludes wired/kernel)."""
        return (self.pages_active + self.pages_inactive) * self.page_size


@dataclass
class DiskInfo:
    total_bytes: int
    used_bytes: int
    avail_bytes: int
    # APFS container free space (includes purgeable); 0 if diskutil unavailable
    container_free_bytes: int = 0

    @property
    def used_pct(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100

    @property
    def purgeable_bytes(self) -> int:
        return max(0, self.container_free_bytes - self.avail_bytes)


@dataclass
class SwapInfo:
    total_bytes: int
    used_bytes: int

    @property
    def used_pct(self) -> float:
        if self.total_bytes == 0:
            return 0.0
        return (self.used_bytes / self.total_bytes) * 100


@dataclass
class CategorySummary:
    category: Category
    count: int
    total_cpu: float
    total_mem: float
    total_rss_kb: int


@dataclass
class SystemSnapshot:
    timestamp: str
    hostname: str
    cpu_count: int
    memory: MemoryInfo
    processes: list
    thermal_level: str = "normal"
    network_available: bool = True
    disk: Optional[DiskInfo] = None
    swap: Optional[SwapInfo] = None
    memory_pressure: str = "normal"
    disk_io: Optional[dict] = None
    stale_sessions: list = field(default_factory=list)
    schema_version: int = SCHEMA_VERSION
    snapshot_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])


# ---------------------------------------------------------------------------
# Classification
# ---------------------------------------------------------------------------

# Ordered rules: first match wins. Each rule is (Category, [substrings]).
# Matched case-insensitively against the full comm path.
CLASSIFY_RULES: list[tuple[Category, list[str]]] = [
    (Category.CLAUDE, [
        "claude",
        "anthropic",
        ".local/share/claude",
    ]),
    (Category.CHROME, [
        "Google Chrome",
        "Arc.app",
        "Firefox",
        "Safari.app",
        "Brave",
        "Chromium",
        "Microsoft Edge",
        "WebKit",
    ]),
    (Category.IDE, [
        "Visual Studio Code",
        "Cursor.app",
        "Ghostty",
        "Terminal.app",
        "iTerm",
        "Alacritty",
        "WezTerm",
        "Pencil.app",
        "Zed.app",
        "tmux",
    ]),
    (Category.ML, [
        "ollama",
        "llama-server",
        "llama.cpp",
        "mlx",
        "ggml",
        "huggingface",
        "pytorch",
        "parakeet",
        "whisper",
        "qwen",
    ]),
    (Category.DEVSERV, [
        "node",
        "npm",
        "next-server",
        "webpack",
        "vite",
        "esbuild",
        "turbopack",
        "uvicorn",
        "gunicorn",
        "flask",
        "django",
        "cargo",
        "rustc",
        "java",
        "gradle",
        "maven",
        "python3",
        "python",
        "ruby",
        "rails",
    ]),
    (Category.SYSTEM, [
        "/usr/libexec/",
        "/System/",
        "/sbin/",
        "launchd",
        "kernel_task",
        "WindowServer",
        "Dock",
        "Finder.app",
        "SystemUIServer",
        "CoreServices",
        "mds_stores",
        "mdworker",
        "coreaudiod",
        "bluetoothd",
        "cfprefsd",
        "distnoted",
        "logd",
        "opendirectoryd",
        "sandboxd",
        "syslogd",
        "UserEventAgent",
        "nsurlsessiond",
        "trustd",
        "securityd",
        "sharingd",
        "airportd",
        "fseventsd",
        "notifyd",
        "powerd",
        "thermald",
        "coreduetd",
        "rapportd",
        "diagnosticd",
        "symptomsd",
        "runningboardd",
        "loginwindow",
        "backboardd",
        "dasd",
        "remoted",
        "corespeechd",
        "containermanagerd",
    ]),
]


def classify(comm: str) -> Category:
    """Classify a process by substring match on comm. First match wins."""
    comm_lower = comm.lower()
    for category, patterns in CLASSIFY_RULES:
        for pattern in patterns:
            if pattern.lower() in comm_lower:
                return category
    return Category.OTHER


# ---------------------------------------------------------------------------
# Data Capture
# ---------------------------------------------------------------------------

def capture_processes() -> list[ProcessInfo]:
    """Capture all processes via a single ps call."""
    result = subprocess.run(
        ["ps", "-eo", "pid=,ppid=,pcpu=,pmem=,rss=,comm="],
        capture_output=True, text=True, timeout=10
    )
    if result.returncode != 0:
        raise RuntimeError(f"ps failed (rc={result.returncode}): {result.stderr.strip()}")
    procs = []
    # Each line: numeric fields then comm (which may contain spaces)
    pat = re.compile(r"^\s*(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(.+)$")
    for line in result.stdout.strip().splitlines():
        m = pat.match(line)
        if not m:
            continue
        comm = m.group(6).strip()
        proc = ProcessInfo(
            pid=int(m.group(1)),
            ppid=int(m.group(2)),
            cpu=float(m.group(3)),
            mem=float(m.group(4)),
            rss_kb=int(m.group(5)),
            comm=comm,
            category=classify(comm),
        )
        procs.append(proc)
    return procs


def capture_memory() -> MemoryInfo:
    """Capture memory info via vm_stat and sysctl."""
    # Total physical RAM
    result = subprocess.run(
        ["sysctl", "-n", "hw.memsize"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        raise RuntimeError(f"sysctl hw.memsize failed (rc={result.returncode}): {result.stderr.strip()}")
    total_bytes = int(result.stdout.strip())

    # vm_stat for page breakdown
    result = subprocess.run(
        ["vm_stat"],
        capture_output=True, text=True, timeout=5
    )
    if result.returncode != 0:
        raise RuntimeError(f"vm_stat failed (rc={result.returncode}): {result.stderr.strip()}")
    lines = result.stdout.strip().splitlines()

    # First line: "Mach Virtual Memory Statistics: (page size of NNNNN bytes)"
    page_size = 16384  # default for Apple Silicon
    m = re.search(r"page size of (\d+) bytes", lines[0])
    if m:
        page_size = int(m.group(1))

    def extract_pages(label: str) -> int:
        for line in lines:
            if label in line:
                m = re.search(r":\s+(\d+)", line)
                if m:
                    return int(m.group(1))
        return 0

    return MemoryInfo(
        total_bytes=total_bytes,
        page_size=page_size,
        pages_active=extract_pages("Pages active"),
        pages_inactive=extract_pages("Pages inactive"),
        pages_wired=extract_pages("Pages wired down"),
        pages_compressed=extract_pages("occupied by compressor"),
        pages_free=extract_pages("Pages free"),
        pages_speculative=extract_pages("Pages speculative"),
    )


def capture_thermal() -> str:
    """Get thermal level via pmset (nominal/fair/serious/critical -> normal/elevated/critical)."""
    try:
        result = subprocess.run(
            ["pmset", "-g", "therm"],
            capture_output=True, text=True, timeout=5
        )
        output = result.stdout.lower()
        if "critical" in output:
            return "critical"
        if "serious" in output:
            return "elevated"
        return "normal"
    except Exception:
        return "normal"


def capture_network() -> bool:
    """Quick network check."""
    try:
        result = subprocess.run(
            ["sysctl", "-n", "net.inet.tcp.stats"],
            capture_output=True, text=True, timeout=3
        )
        return result.returncode == 0
    except Exception:
        return True  # assume available


def capture_disk(path: str = DATA_VOLUME) -> Optional[DiskInfo]:
    """Capture data-volume capacity via df, plus APFS container free via diskutil."""
    try:
        result = subprocess.run(
            ["df", "-k", path],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode != 0:
            return None
        fields = result.stdout.strip().splitlines()[-1].split()
        total_kb, used_kb, avail_kb = int(fields[1]), int(fields[2]), int(fields[3])
    except Exception:
        return None

    container_free = 0
    try:
        info = subprocess.run(
            ["diskutil", "info", "-plist", "/"],
            capture_output=True, timeout=5
        )
        extract = subprocess.run(
            ["plutil", "-extract", "APFSContainerFree", "raw", "-"],
            input=info.stdout, capture_output=True, timeout=5
        )
        if extract.returncode == 0:
            container_free = int(extract.stdout.strip().decode())
    except Exception:
        pass

    return DiskInfo(
        total_bytes=total_kb * 1024,
        used_bytes=used_kb * 1024,
        avail_bytes=avail_kb * 1024,
        container_free_bytes=container_free,
    )


def capture_swap() -> Optional[SwapInfo]:
    """Capture swap usage via sysctl vm.swapusage."""
    try:
        result = subprocess.run(
            ["sysctl", "-n", "vm.swapusage"],
            capture_output=True, text=True, timeout=5
        )
        m = re.search(r"total = ([\d.]+)M.*used = ([\d.]+)M", result.stdout)
        if not m:
            return None
        return SwapInfo(
            total_bytes=int(float(m.group(1)) * 1048576),
            used_bytes=int(float(m.group(2)) * 1048576),
        )
    except Exception:
        return None


def capture_memory_pressure() -> str:
    """System memory pressure via memory_pressure -Q (normal/warn/critical)."""
    try:
        result = subprocess.run(
            ["memory_pressure", "-Q"],
            capture_output=True, text=True, timeout=5
        )
        m = re.search(r"free percentage:\s*(\d+)", result.stdout)
        if m:
            free_pct = int(m.group(1))
            if free_pct < 10:
                return "critical"
            if free_pct <= 20:
                return "warn"
        return "normal"
    except Exception:
        return "normal"


def capture_disk_io() -> Optional[dict]:
    """Current disk transfer rates via iostat (two 1s samples; costs ~1s).

    macOS iostat reports transfers/sec and MB/s but not a read/write split,
    so the Kothar readsPerSec/writesPerSec fields stay 0 and the real rates
    ride in superset keys.
    """
    try:
        result = subprocess.run(
            ["iostat", "-d", "-w", "1", "-c", "2"],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().splitlines()
        # Header: disk names; header: "KB/t tps MB/s" per disk; then samples.
        sample = lines[-1].split()
        tps = sum(float(sample[i]) for i in range(1, len(sample), 3))
        mbs = sum(float(sample[i]) for i in range(2, len(sample), 3))
        return {"transfersPerSec": round(tps, 1), "mbPerSec": round(mbs, 2)}
    except Exception:
        return None


def _agent_tty_procs() -> list[dict]:
    """Interactive claude and codex session processes: [{pid, tty, agent}].

    claude: comm is exactly `claude`. codex: the native binary (args end in
    /bin/codex, excluding the `node` wrapper around it).
    """
    procs = []
    try:
        result = subprocess.run(
            ["ps", "-axo", "pid=,tty=,args="],
            capture_output=True, text=True, timeout=10
        )
    except Exception:
        return []
    for line in result.stdout.strip().splitlines():
        fields = line.split(None, 2)
        if len(fields) < 3 or fields[1] in ("??", "-"):
            continue
        pid, tty, args = int(fields[0]), fields[1], fields[2]
        if args == "claude" or args.startswith("claude "):
            procs.append({"pid": pid, "tty": tty, "agent": "claude"})
        elif args.split()[0].endswith("/bin/codex") and not args.startswith("node"):
            procs.append({"pid": pid, "tty": tty, "agent": "codex"})
    return procs


def _proc_cwd(pid: int) -> Optional[str]:
    try:
        result = subprocess.run(
            ["lsof", "-a", "-p", str(pid), "-d", "cwd", "-Fn"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if line.startswith("n"):
                return line[1:]
    except Exception:
        pass
    return None


def _proc_start_epoch(pid: int) -> Optional[float]:
    try:
        result = subprocess.run(
            ["ps", "-o", "lstart=", "-p", str(pid)],
            capture_output=True, text=True, timeout=5
        )
        lstart = " ".join(result.stdout.split())  # normalize double spaces
        return time.mktime(time.strptime(lstart, "%a %b %d %H:%M:%S %Y"))
    except Exception:
        return None


def _speculator_session_map() -> dict:
    """pid -> {sessionId, project} from speculator's Ghostty tab map."""
    try:
        data = json.loads(SPECULATOR_SESSIONS.read_text())
    except Exception:
        return {}
    mapping = {}
    for entry in data.get("sessions", []):
        cs = entry.get("claude_session")
        if cs and cs.get("pid") and cs.get("sessionId"):
            mapping[cs["pid"]] = cs
    return mapping


def _claude_last_activity(pid: int, spec: dict) -> tuple[Optional[float], str]:
    """(transcript mtime, project label) for a claude PID.

    Speculator's pid->sessionId map first; when speculator missed the pid,
    match a transcript in the cwd's project dir whose birthtime is within
    ±180s of process start (a transcript is born when its session starts).
    """
    info = spec.get(pid)
    if info:
        transcripts = list(PROJECTS_DIR.glob(f"*/{info['sessionId']}.jsonl"))
        if transcripts:
            return (max(t.stat().st_mtime for t in transcripts),
                    info.get("project") or "")

    cwd = _proc_cwd(pid)
    start = _proc_start_epoch(pid)
    if not cwd or not start:
        return None, ""
    slug_dir = PROJECTS_DIR / cwd.replace("/", "-")
    if not slug_dir.is_dir():
        return None, ""
    # Two sessions can start in the same project within the window — take the
    # transcript born closest to process start, not the first glob hit.
    candidates = []
    for t in slug_dir.glob("*.jsonl"):
        try:
            st = t.stat()
            delta = abs(st.st_birthtime - start)
            if delta <= 180:
                candidates.append((delta, st.st_mtime))
        except OSError:
            continue
    if not candidates:
        return None, ""
    return min(candidates)[1], Path(cwd).name


def _codex_last_activity(pid: int) -> tuple[Optional[float], str]:
    """(newest open-rollout mtime, project label) for a codex PID.

    codex holds its rollout files open, so lsof is an exact join. A session
    with several open rollouts (subagent threads) is active if any moves.
    """
    try:
        result = subprocess.run(
            ["lsof", "-a", "-p", str(pid), "-Fn"],
            capture_output=True, text=True, timeout=5
        )
    except Exception:
        return None, ""
    mtimes = []
    for line in result.stdout.splitlines():
        if line.startswith("n") and "/.codex/sessions/" in line and line.endswith(".jsonl"):
            try:
                mtimes.append(os.stat(line[1:]).st_mtime)
            except OSError:
                continue
    if not mtimes:
        return None, ""
    cwd = _proc_cwd(pid)
    return max(mtimes), (Path(cwd).name if cwd else "")


def capture_stale_sessions(threshold_days: float = STALE_SESSION_DAYS) -> list[dict]:
    """Claude and Codex sessions idle (no transcript activity) >= threshold_days."""
    now = time.time()
    spec = _speculator_session_map()
    stale = []
    for proc in _agent_tty_procs():
        if proc["agent"] == "claude":
            mtime, project = _claude_last_activity(proc["pid"], spec)
        else:
            mtime, project = _codex_last_activity(proc["pid"])
        if mtime is None:
            continue
        idle_days = (now - mtime) / 86400
        if idle_days >= threshold_days:
            stale.append({
                "agent": proc["agent"],
                "pid": proc["pid"],
                "tty": proc["tty"],
                "project": project,
                "idle_days": round(idle_days, 1),
            })
    stale.sort(key=lambda s: s["idle_days"], reverse=True)
    return stale


def take_snapshot(with_io: bool = False) -> SystemSnapshot:
    """Capture a full system snapshot. with_io adds a ~1s iostat sample."""
    procs = capture_processes()
    mem = capture_memory()
    thermal = capture_thermal()
    network = capture_network()
    disk = capture_disk()
    swap = capture_swap()
    pressure = capture_memory_pressure()
    disk_io = capture_disk_io() if with_io else None
    stale = capture_stale_sessions()

    return SystemSnapshot(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        hostname=os.uname().nodename,
        cpu_count=os.cpu_count() or 1,
        memory=mem,
        processes=procs,
        thermal_level=thermal,
        network_available=network,
        disk=disk,
        swap=swap,
        memory_pressure=pressure,
        disk_io=disk_io,
        stale_sessions=stale,
    )


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------

def aggregate(snapshot: SystemSnapshot, category_filter: Optional[str] = None) -> dict:
    """Group processes by category, compute summaries and top-N lists."""
    procs = snapshot.processes
    if category_filter:
        try:
            cat = Category[category_filter.upper()]
            procs = [p for p in procs if p.category == cat]
        except KeyError:
            pass  # invalid filter, show all

    # Category summaries
    by_cat: dict[Category, list[ProcessInfo]] = {c: [] for c in Category}
    for proc in snapshot.processes:  # always group ALL for the breakdown
        by_cat[proc.category].append(proc)

    summaries = []
    for cat in Category:
        cat_procs = by_cat[cat]
        if not cat_procs:
            continue
        summaries.append(CategorySummary(
            category=cat,
            count=len(cat_procs),
            total_cpu=sum(p.cpu for p in cat_procs),
            total_mem=sum(p.mem for p in cat_procs),
            total_rss_kb=sum(p.rss_kb for p in cat_procs),
        ))

    summaries.sort(key=lambda s: s.total_rss_kb, reverse=True)

    # Top N (from filtered set if filter active)
    top_cpu = sorted(procs, key=lambda p: p.cpu, reverse=True)
    top_mem = sorted(procs, key=lambda p: p.rss_kb, reverse=True)

    return {
        "summaries": summaries,
        "top_cpu": top_cpu,
        "top_mem": top_mem,
        "total_processes": len(snapshot.processes),
        "total_cpu": sum(p.cpu for p in snapshot.processes),
    }


# ---------------------------------------------------------------------------
# Formatting: ANSI Terminal
# ---------------------------------------------------------------------------

RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"

# Box drawing
BOX_TL = "\u250c"
BOX_TR = "\u2510"
BOX_BL = "\u2514"
BOX_BR = "\u2518"
BOX_H = "\u2500"
BOX_V = "\u2502"

BLOCK_FULL = "\u2588"
BLOCK_EMPTY = "\u2591"


def _colored(text: str, color: str, no_color: bool) -> str:
    if no_color:
        return text
    return f"{color}{text}{RESET}"


def _bold(text: str, no_color: bool) -> str:
    if no_color:
        return text
    return f"{BOLD}{text}{RESET}"


def _dim(text: str, no_color: bool) -> str:
    if no_color:
        return text
    return f"{DIM}{text}{RESET}"


def format_bytes(kb: int) -> str:
    """Format kilobytes to human-readable."""
    if kb >= 1048576:  # 1 GB
        return f"{kb / 1048576:.1f} GB"
    if kb >= 1024:  # 1 MB
        return f"{kb / 1024:.0f} MB"
    return f"{kb} KB"


def format_bytes_from_bytes(b: int) -> str:
    """Format bytes to human-readable."""
    if b >= 1073741824:  # 1 GB
        return f"{b / 1073741824:.1f} GB"
    if b >= 1048576:  # 1 MB
        return f"{b / 1048576:.0f} MB"
    return f"{b / 1024:.0f} KB"


def get_terminal_width() -> int:
    try:
        return os.get_terminal_size().columns
    except (ValueError, OSError):
        return 120


def format_terminal(snapshot: SystemSnapshot, agg: dict, top_n: int,
                    category_filter: Optional[str], no_color: bool) -> str:
    """Build the full terminal output string."""
    nc = no_color
    w = min(get_terminal_width(), 72)
    lines = []

    # Header box
    ts = snapshot.timestamp[:19]
    header1 = f"  syspeek {DIM}\u00b7{RESET} {snapshot.hostname} {DIM}\u00b7{RESET} {ts}"
    if nc:
        header1 = f"  syspeek . {snapshot.hostname} . {ts}"
    mem = snapshot.memory
    total_gb = mem.total_bytes / 1073741824
    header2 = f"  {snapshot.cpu_count} cores {DIM}\u00b7{RESET} {total_gb:.0f} GB {DIM}\u00b7{RESET} {agg['total_processes']} procs"
    if nc:
        header2 = f"  {snapshot.cpu_count} cores . {total_gb:.0f} GB . {agg['total_processes']} procs"

    lines.append(f"  {BOX_TL}{BOX_H * (w - 4)}{BOX_TR}")
    lines.append(f"  {BOX_V}{header1:<{w - 4}}{BOX_V}" if nc else f"  {BOX_V}{header1}{' ' * max(0, w - 60)}{BOX_V}")
    lines.append(f"  {BOX_V}{header2:<{w - 4}}{BOX_V}" if nc else f"  {BOX_V}{header2}{' ' * max(0, w - 48)}{BOX_V}")
    lines.append(f"  {BOX_BL}{BOX_H * (w - 4)}{BOX_BR}")
    lines.append("")

    # Memory bar
    bar_width = 30
    used_pct = mem.used_pct
    filled = int(bar_width * used_pct / 100)
    bar = BLOCK_FULL * filled + BLOCK_EMPTY * (bar_width - filled)
    used_gb = mem.used_bytes / 1073741824
    mem_color = "\033[32m" if used_pct < 70 else ("\033[33m" if used_pct < 85 else "\033[31m")
    if nc:
        lines.append(f"  [{bar}] {used_pct:.1f}% MEM ({used_gb:.1f} / {total_gb:.0f} GB)")
    else:
        lines.append(f"  [{mem_color}{bar}{RESET}] {used_pct:.1f}% MEM ({used_gb:.1f} / {total_gb:.0f} GB)")

    # Disk bar (80/90 thresholds — high disk use is routine, unlike memory)
    disk = snapshot.disk
    if disk:
        d_pct = disk.used_pct
        d_filled = int(bar_width * d_pct / 100)
        d_bar = BLOCK_FULL * d_filled + BLOCK_EMPTY * (bar_width - d_filled)
        d_used_gb = disk.used_bytes / 1073741824
        d_total_gb = disk.total_bytes / 1073741824
        d_color = "\033[32m" if d_pct < 80 else ("\033[33m" if d_pct < 90 else "\033[31m")
        if nc:
            lines.append(f"  [{d_bar}] {d_pct:.1f}% DISK ({d_used_gb:.0f} / {d_total_gb:.0f} GB)")
        else:
            lines.append(f"  [{d_color}{d_bar}{RESET}] {d_pct:.1f}% DISK ({d_used_gb:.0f} / {d_total_gb:.0f} GB)")

    # Swap (only when in use)
    swap = snapshot.swap
    if swap and swap.used_bytes > 0:
        swap_line = (f"  swap {swap.used_bytes / 1073741824:.1f} / "
                     f"{swap.total_bytes / 1073741824:.1f} GB ({swap.used_pct:.0f}%)")
        lines.append(_dim(swap_line, nc))

    # Memory pressure
    if snapshot.memory_pressure != "normal":
        p_color = "\033[33m" if snapshot.memory_pressure == "warn" else "\033[31m"
        lines.append(f"  {_colored(f'PRESSURE: {snapshot.memory_pressure.upper()}', p_color, nc)}")

    # Thermal
    if snapshot.thermal_level != "normal":
        t_color = "\033[33m" if snapshot.thermal_level == "elevated" else "\033[31m"
        lines.append(f"  {_colored(f'THERMAL: {snapshot.thermal_level.upper()}', t_color, nc)}")

    # Stale agent sessions
    for s in snapshot.stale_sessions:
        stale_line = (f"  STALE: {s['agent']} PID {s['pid']} ({s['project']}, {s['tty']}) "
                      f"idle {s['idle_days']:.0f}d — syspeek --kill {s['pid']}")
        lines.append(_colored(stale_line, "\033[33m", nc))

    lines.append("")

    # Category breakdown
    for s in agg["summaries"]:
        cat = s.category
        rss_str = format_bytes(s.total_rss_kb)
        line = f"  {cat.icon} {cat.label:<14} {s.count:>4} procs  {s.total_cpu:>6.1f}% CPU  {rss_str:>8}"
        lines.append(_colored(line, cat.color, nc))

    lines.append("")

    # Top N by CPU
    lines.append(_bold(f"  TOP {top_n} BY CPU", nc))
    lines.append(_dim(f"  {'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  {'RSS':>8}  {'CAT':>2}  COMMAND", nc))
    cmd_width = max(20, w - 48)
    for proc in agg["top_cpu"][:top_n]:
        comm_short = proc.comm.rsplit("/", 1)[-1][:cmd_width]
        line = f"  {proc.pid:>7}  {proc.cpu:>6.1f}  {proc.mem:>6.1f}  {format_bytes(proc.rss_kb):>8}  {proc.category.icon}  {comm_short}"
        lines.append(_colored(line, proc.category.color, nc))

    lines.append("")

    # Top N by Memory
    lines.append(_bold(f"  TOP {top_n} BY MEMORY", nc))
    lines.append(_dim(f"  {'PID':>7}  {'CPU%':>6}  {'MEM%':>6}  {'RSS':>8}  {'CAT':>2}  COMMAND", nc))
    for proc in agg["top_mem"][:top_n]:
        comm_short = proc.comm.rsplit("/", 1)[-1][:cmd_width]
        line = f"  {proc.pid:>7}  {proc.cpu:>6.1f}  {proc.mem:>6.1f}  {format_bytes(proc.rss_kb):>8}  {proc.category.icon}  {comm_short}"
        lines.append(_colored(line, proc.category.color, nc))

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Formatting: JSON (Kothar SystemHealthReport superset)
# ---------------------------------------------------------------------------

def _proc_to_dict(p: ProcessInfo) -> dict:
    return {
        "pid": p.pid,
        "ppid": p.ppid,
        "cpu": p.cpu,
        "mem": p.mem,
        "rss_kb": p.rss_kb,
        "comm": p.comm.rsplit("/", 1)[-1],
        "full_comm": p.comm,
        "category": p.category.name,
    }


def format_json(snapshot: SystemSnapshot, agg: dict, top_n: int,
                category_filter: Optional[str]) -> str:
    """JSON output — superset of Kothar's SystemHealthReport."""
    mem = snapshot.memory
    issues = []
    if mem.used_pct > 90:
        issues.append("Memory usage above 90%")
    if agg["total_cpu"] > 90 * snapshot.cpu_count:
        issues.append("CPU usage above 90%")
    if snapshot.thermal_level != "normal":
        issues.append(f"Thermal: {snapshot.thermal_level}")
    if snapshot.disk and snapshot.disk.used_pct > 90:
        issues.append("Disk usage above 90%")
    if snapshot.memory_pressure != "normal":
        issues.append(f"Memory pressure: {snapshot.memory_pressure}")
    if snapshot.swap and snapshot.swap.used_pct > 90:
        issues.append("Swap usage above 90%")
    if snapshot.stale_sessions:
        issues.append(f"{len(snapshot.stale_sessions)} agent session(s) idle >{STALE_SESSION_DAYS}d")

    # Kothar-compatible topProcesses
    kothar_procs = [
        {"pid": p.pid, "name": p.comm.rsplit("/", 1)[-1], "cpu": p.cpu, "memory": p.mem}
        for p in agg["top_cpu"][:top_n]
    ]

    output = {
        # Identity
        "snapshot_id": snapshot.snapshot_id,
        "timestamp": snapshot.timestamp,
        "schema_version": snapshot.schema_version,
        "hostname": snapshot.hostname,
        "cpu_count": snapshot.cpu_count,

        # Kothar SystemHealthReport fields (kothar.ts:63-74)
        "cpuUsage": round(agg["total_cpu"], 1),
        "memoryUsage": round(mem.used_pct, 1),
        "diskUsage": round(snapshot.disk.used_pct, 1) if snapshot.disk else None,
        "gpuUsage": 0,  # requires IOKit — v3
        "thermalLevel": snapshot.thermal_level,
        "memoryPressure": snapshot.memory_pressure,
        # macOS iostat has no read/write split; real rates in superset keys
        "diskIO": {"readsPerSec": 0, "writesPerSec": 0, **(snapshot.disk_io or {})},
        "networkAvailable": snapshot.network_available,
        "topProcesses": kothar_procs,
        "issues": issues,

        # Extended: memory detail
        "memory": {
            "total_bytes": mem.total_bytes,
            "used_bytes": mem.used_bytes,
            "used_pct": round(mem.used_pct, 1),
            "app_bytes": mem.app_bytes,
        },

        # Extended: disk + swap detail
        "disk": {
            "total_bytes": snapshot.disk.total_bytes,
            "used_bytes": snapshot.disk.used_bytes,
            "avail_bytes": snapshot.disk.avail_bytes,
            "used_pct": round(snapshot.disk.used_pct, 1),
            "purgeable_bytes": snapshot.disk.purgeable_bytes,
            "container_free_bytes": snapshot.disk.container_free_bytes,
        } if snapshot.disk else None,
        "swap": {
            "total_bytes": snapshot.swap.total_bytes,
            "used_bytes": snapshot.swap.used_bytes,
            "used_pct": round(snapshot.swap.used_pct, 1),
        } if snapshot.swap else None,

        # Extended: categories
        "categories": {
            s.category.name: {
                "label": s.category.label,
                "count": s.count,
                "cpu": round(s.total_cpu, 1),
                "mem": round(s.total_mem, 1),
                "rss_kb": s.total_rss_kb,
                "rss_human": format_bytes(s.total_rss_kb),
            }
            for s in agg["summaries"]
        },

        # Extended: stale sessions
        "staleSessions": snapshot.stale_sessions,

        # Extended: process lists
        "total_processes": agg["total_processes"],
        "top_cpu": [_proc_to_dict(p) for p in agg["top_cpu"][:top_n]],
        "top_mem": [_proc_to_dict(p) for p in agg["top_mem"][:top_n]],
    }

    return output


def format_json_pretty(snapshot: SystemSnapshot, agg: dict, top_n: int,
                       category_filter: Optional[str]) -> str:
    """Pretty-printed JSON for terminal display."""
    return json.dumps(format_json(snapshot, agg, top_n, category_filter), indent=2)


def format_json_compact(snapshot: SystemSnapshot, agg: dict, top_n: int,
                        category_filter: Optional[str]) -> str:
    """Compact single-line JSON for JSONL storage."""
    return json.dumps(format_json(snapshot, agg, top_n, category_filter), separators=(",", ":"))


# ---------------------------------------------------------------------------
# Memory Integration (ensouled + JSONL)
# ---------------------------------------------------------------------------

def is_ensouled() -> bool:
    """Check if the Claudicle soul is active."""
    return SOUL_MD.exists()


def one_line_summary(snapshot: SystemSnapshot, agg: dict) -> str:
    """Human-readable one-liner for memory content field."""
    mem = snapshot.memory
    head = f"{mem.used_pct:.1f}% mem, {agg['total_cpu']:.1f}% CPU, {agg['total_processes']} procs"
    if snapshot.disk:
        head += f", {snapshot.disk.used_pct:.0f}% disk"
    parts = [head]
    cats = []
    for s in agg["summaries"][:4]:  # top 4 categories
        cats.append(f"{s.category.name}: {s.count} ({format_bytes(s.total_rss_kb)})")
    parts.append(" | ".join(cats))
    parts.append(snapshot.timestamp[:19])
    return " | ".join(parts)


def record_to_jsonl(snapshot_json: str) -> Path:
    """Append snapshot to daily JSONL file. File-locked for concurrent safety."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    path = DATA_DIR / f"{today}.jsonl"
    with open(path, "a") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.write(snapshot_json + "\n")
        f.flush()
        fcntl.flock(f, fcntl.LOCK_UN)
    return path


def record_to_memory_db(snapshot_json: str, snapshot_id: str, summary: str) -> bool:
    """Write snapshot to canonical working_memory table (ensouled only)."""
    if not MEMORY_DB.exists():
        return False
    try:
        with sqlite3.connect(str(MEMORY_DB), timeout=5) as conn:
            conn.execute(
                """INSERT INTO working_memory
                   (channel, thread_ts, user_id, entry_type, verb, content, metadata,
                    trace_id, display_name, region, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "system:syspeek",
                    "",
                    "syspeek",
                    "systemSnapshot",
                    "observed",
                    summary,
                    snapshot_json,
                    snapshot_id,
                    "syspeek",
                    "system-monitoring",
                    time.time(),
                )
            )
        return True
    except Exception as e:
        _log(f"Memory DB write failed: {e}")
        return False


MEMDB_MARKER = DATA_DIR / ".last-memdb-write"


def _memdb_due(min_interval_sec: float) -> bool:
    """True if enough time has passed since the last memory.db write."""
    if min_interval_sec <= 0:
        return True
    try:
        return (time.time() - MEMDB_MARKER.stat().st_mtime) >= min_interval_sec
    except FileNotFoundError:
        return True


def record(snapshot: SystemSnapshot, agg: dict, snapshot_json: str,
           memdb_min_interval: float = 0):
    """Persist snapshot to JSONL (always) and memory.db (if ensouled).

    memdb_min_interval throttles memory.db writes — the daemon passes an hour
    so canonical working memory gets 24 rows/day, not 288. JSONL is unthrottled.
    """
    jsonl_path = record_to_jsonl(snapshot_json)
    summary = one_line_summary(snapshot, agg)

    if not is_ensouled():
        _log(f"Recorded {snapshot.snapshot_id}: JSONL={jsonl_path.name} (not ensouled)")
        return

    if not _memdb_due(memdb_min_interval):
        _log(f"Recorded {snapshot.snapshot_id}: JSONL={jsonl_path.name} (memory.db throttled)")
        return

    ok = record_to_memory_db(snapshot_json, snapshot.snapshot_id, summary)
    if ok:
        MEMDB_MARKER.touch()
    _log(f"Recorded {snapshot.snapshot_id}: JSONL={jsonl_path.name}, memory.db={'ok' if ok else 'failed'}")


# ---------------------------------------------------------------------------
# Kill Command
# ---------------------------------------------------------------------------

def kill_process(pid: int):
    """Send SIGTERM to a process with safety checks."""
    if pid in (0, 1):
        print(f"Refused: PID {pid} is protected.", file=sys.stderr)
        sys.exit(1)

    # Find process in current snapshot
    procs = capture_processes()
    target = next((p for p in procs if p.pid == pid), None)
    if target is None:
        print(f"PID {pid} not found in process table.", file=sys.stderr)
        sys.exit(1)

    comm_short = target.comm.rsplit("/", 1)[-1]
    cat = target.category

    print(f"  Kill process?")
    print(f"    PID:      {pid}")
    print(f"    Command:  {comm_short}")
    print(f"    Category: {cat.icon} {cat.label}")
    print(f"    CPU:      {target.cpu:.1f}%")
    print(f"    MEM:      {format_bytes(target.rss_kb)}")
    print()

    if cat == Category.SYSTEM:
        print("  WARNING: This is a SYSTEM process.", file=sys.stderr)
        if sys.stdin.isatty():
            answer = input("  Type 'KILL' to confirm: ")
            if answer.strip() != "KILL":
                print("  Aborted.")
                return
        else:
            print("  Refused: cannot kill SYSTEM process in non-TTY mode.", file=sys.stderr)
            sys.exit(1)
    elif sys.stdin.isatty():
        answer = input("  Confirm [y/N]: ")
        if answer.strip().lower() != "y":
            print("  Aborted.")
            return
    else:
        print("  (non-TTY: skipping confirmation)")

    try:
        os.kill(pid, signal.SIGTERM)
        print(f"  SIGTERM sent to PID {pid} ({comm_short})")
    except PermissionError:
        print(f"  Permission denied. Try: sudo kill {pid}", file=sys.stderr)
        sys.exit(1)
    except ProcessLookupError:
        print(f"  PID {pid} already exited.", file=sys.stderr)


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------

def show_history(as_json: bool):
    """Show last 24h of recorded snapshots."""
    cutoff = datetime.now() - timedelta(hours=24)
    snapshots = []

    if not DATA_DIR.exists():
        print("No data directory found. Run syspeek --record first.", file=sys.stderr)
        return

    for jsonl_file in sorted(DATA_DIR.glob("*.jsonl")):
        try:
            file_date = date.fromisoformat(jsonl_file.stem)
        except ValueError:
            continue
        if file_date < cutoff.date():
            continue
        with open(jsonl_file) as f:
            for line in f:
                try:
                    snap = json.loads(line)
                    snap_time = datetime.fromisoformat(snap["timestamp"])
                    if snap_time >= cutoff:
                        snapshots.append(snap)
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue

    if not snapshots:
        print("No snapshots in the last 24 hours.", file=sys.stderr)
        return

    if as_json:
        print(json.dumps(snapshots, indent=2))
    else:
        print(f"  {'TIMESTAMP':<20}  {'CPU%':>6}  {'MEM%':>6}  {'DISK%':>6}  {'PROCS':>6}  {'THERMAL'}")
        print(f"  {'─' * 20}  {'─' * 6}  {'─' * 6}  {'─' * 6}  {'─' * 6}  {'─' * 8}")
        for snap in snapshots:
            ts = snap.get("timestamp", "")[:19]
            cpu = snap.get("cpuUsage", 0)
            mem_pct = snap.get("memoryUsage", 0)
            disk_pct = snap.get("diskUsage")  # absent in pre-v2 snapshots
            disk_str = f"{disk_pct:>6.1f}" if isinstance(disk_pct, (int, float)) else f"{'-':>6}"
            n_procs = snap.get("total_processes", 0)
            thermal = snap.get("thermalLevel", "normal")
            print(f"  {ts:<20}  {cpu:>6.1f}  {mem_pct:>6.1f}  {disk_str}  {n_procs:>6}  {thermal}")


# ---------------------------------------------------------------------------
# Disk View
# ---------------------------------------------------------------------------

def _capture_volumes() -> list[dict]:
    """All mounted /dev/disk* volumes via df -k."""
    volumes = []
    try:
        result = subprocess.run(
            ["df", "-k"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.strip().splitlines()[1:]:
            fields = line.split()
            if len(fields) < 9 or not fields[0].startswith("/dev/disk"):
                continue
            mount = " ".join(fields[8:])
            volumes.append({
                "device": fields[0],
                "mount": mount,
                "total_bytes": int(fields[1]) * 1024,
                "used_bytes": int(fields[2]) * 1024,
                "avail_bytes": int(fields[3]) * 1024,
                "used_pct": round(int(fields[2]) / int(fields[1]) * 100, 1) if int(fields[1]) else 0,
            })
    except Exception:
        pass
    return volumes


def _capture_hotspots() -> list[dict]:
    """du -sk over the curated hotspot list. Each dir capped at 15s."""
    hotspots = []
    for raw in DISK_HOTSPOT_DIRS:
        path = Path(raw).expanduser()
        if not path.exists():
            continue
        try:
            result = subprocess.run(
                ["du", "-sk", str(path)],
                capture_output=True, text=True, timeout=15
            )
            size_kb = int(result.stdout.split()[0])
            hotspots.append({"path": str(path), "bytes": size_kb * 1024})
        except Exception:
            hotspots.append({"path": str(path), "bytes": None})  # timed out / denied
    hotspots.sort(key=lambda h: h["bytes"] or 0, reverse=True)
    return hotspots


def show_disk(as_json: bool, no_color: bool):
    """Disk-focused view: volumes, purgeable space, curated hotspots."""
    nc = no_color
    disk = capture_disk()
    volumes = _capture_volumes()
    hotspots = _capture_hotspots()

    if as_json:
        print(json.dumps({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "data_volume": {
                "total_bytes": disk.total_bytes,
                "used_bytes": disk.used_bytes,
                "avail_bytes": disk.avail_bytes,
                "used_pct": round(disk.used_pct, 1),
                "purgeable_bytes": disk.purgeable_bytes,
                "container_free_bytes": disk.container_free_bytes,
            } if disk else None,
            "volumes": volumes,
            "hotspots": hotspots,
        }, indent=2))
        return

    lines = ["", _bold("  DISK", nc), ""]
    bar_width = 30
    for vol in volumes:
        pct = vol["used_pct"]
        filled = int(bar_width * pct / 100)
        bar = BLOCK_FULL * filled + BLOCK_EMPTY * (bar_width - filled)
        color = "\033[32m" if pct < 80 else ("\033[33m" if pct < 90 else "\033[31m")
        used = format_bytes_from_bytes(vol["used_bytes"])
        total = format_bytes_from_bytes(vol["total_bytes"])
        bar_str = bar if nc else f"{color}{bar}{RESET}"
        lines.append(f"  [{bar_str}] {pct:>5.1f}%  {used:>9} / {total:<9}  {vol['mount']}")

    if disk and disk.container_free_bytes:
        lines.append("")
        lines.append(_dim(f"  APFS container free: {format_bytes_from_bytes(disk.container_free_bytes)}"
                          f"  (purgeable: {format_bytes_from_bytes(disk.purgeable_bytes)})", nc))

    if hotspots:
        lines.append("")
        lines.append(_bold("  HOTSPOTS", nc))
        for spot in hotspots:
            size = format_bytes_from_bytes(spot["bytes"]) if spot["bytes"] is not None else "(skipped)"
            lines.append(f"  {size:>9}  {spot['path']}")

    lines.append("")
    lines.append(_dim("  Deep-dive: mo analyze (treemap) | mo clean --dry-run (cleanup) | gdu-go <path> (fast scan)", nc))
    lines.append("")
    print("\n".join(lines))


# ---------------------------------------------------------------------------
# Daemon
# ---------------------------------------------------------------------------

def rotate_logs():
    """Two-stage JSONL lifecycle: gzip after ROTATION_DAYS, delete archives
    after ARCHIVE_RETENTION_DAYS. Only touches strict YYYY-MM-DD-named files."""
    if not DATA_DIR.exists():
        return
    today = date.today()
    gzip_cutoff = today - timedelta(days=ROTATION_DAYS)
    delete_cutoff = today - timedelta(days=ARCHIVE_RETENTION_DAYS)

    for jsonl_file in DATA_DIR.glob("*.jsonl"):
        try:
            file_date = date.fromisoformat(jsonl_file.stem)
            if file_date < gzip_cutoff:
                gz_path = jsonl_file.with_suffix(".jsonl.gz")
                if not gz_path.exists():
                    # Write to a tmp file and rename so the archive is atomic:
                    # a crash mid-write never leaves a truncated .gz behind.
                    tmp_path = gz_path.with_suffix(".gz.tmp")
                    with open(jsonl_file, "rb") as f_in, gzip.open(tmp_path, "wb") as f_out:
                        f_out.writelines(f_in)
                    tmp_path.rename(gz_path)
                    jsonl_file.unlink()
                    _log(f"Rotated {jsonl_file.name} -> {gz_path.name}")
                else:
                    # Archive exists from a prior run that crashed before unlink
                    jsonl_file.unlink()
                    _log(f"Cleaned stale {jsonl_file.name} (archive already exists)")
        except ValueError:
            continue

    for gz_file in DATA_DIR.glob("*.jsonl.gz"):
        try:
            file_date = date.fromisoformat(gz_file.name.split(".")[0])
            if file_date < delete_cutoff:
                gz_file.unlink()
                _log(f"Recycled {gz_file.name} (older than {ARCHIVE_RETENTION_DAYS}d)")
        except ValueError:
            continue

    # Leftover tmp archives from a crash mid-rotation
    for tmp_file in DATA_DIR.glob("*.jsonl.gz.tmp"):
        tmp_file.unlink()
        _log(f"Removed incomplete archive {tmp_file.name}")


STALE_ALERTS_MARKER = DATA_DIR / ".stale-alerts.json"


def alert_stale_sessions(stale: list[dict]):
    """macOS notification for stale sessions, at most once per PID per day."""
    if not stale:
        return
    try:
        alerted = json.loads(STALE_ALERTS_MARKER.read_text())
    except Exception:
        alerted = {}

    now = time.time()
    due = [s for s in stale
           if now - alerted.get(str(s["pid"]), 0) >= STALE_ALERT_COOLDOWN_SEC]
    if not due:
        return

    detail = ", ".join(f"{s['agent']} PID {s['pid']} ({s['project']}, {s['idle_days']:.0f}d)" for s in due)
    msg = f"{len(due)} stale session(s): {detail}"
    osa_msg = msg.replace("\\", "\\\\").replace('"', '\\"')
    try:
        subprocess.run(
            ["osascript", "-e",
             f'display notification "{osa_msg}" with title "syspeek"'],
            capture_output=True, timeout=10
        )
    except Exception as e:
        _log(f"Stale alert notification failed: {e}")

    for s in due:
        alerted[str(s["pid"])] = now
    # Drop entries for sessions no longer stale (killed or resumed)
    current = {str(s["pid"]) for s in stale}
    alerted = {p: t for p, t in alerted.items() if p in current}
    try:
        tmp = STALE_ALERTS_MARKER.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(alerted))
        tmp.rename(STALE_ALERTS_MARKER)
    except Exception as e:
        _log(f"Stale alert marker write failed: {e}")
    _log(f"Stale session alert: {msg}")


def run_daemon(interval_min: int, top_n: int):
    """Daemon mode: snapshot + record every interval_min minutes."""
    _log(f"syspeek daemon started (interval: {interval_min}m, ensouled: {is_ensouled()})")

    while True:
        try:
            snapshot = take_snapshot(with_io=True)
            agg = aggregate(snapshot)
            snapshot_json = format_json_compact(snapshot, agg, top_n, None)

            record(snapshot, agg, snapshot_json, memdb_min_interval=MEMDB_MIN_INTERVAL_SEC)
            rotate_logs()
            alert_stale_sessions(snapshot.stale_sessions)

            _log(f"Snapshot {snapshot.snapshot_id}: "
                 f"CPU {agg['total_cpu']:.1f}%, "
                 f"MEM {snapshot.memory.used_pct:.1f}%, "
                 f"{agg['total_processes']} procs")
        except Exception as e:
            _log(f"Snapshot failed: {e}")

        time.sleep(interval_min * 60)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def _log(msg: str):
    """Append to log file."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().isoformat(timespec="seconds")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{ts}] {msg}\n")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="syspeek \u2014 macOS system resource monitor. Claudicle-aware.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--top", type=int, default=DEFAULT_TOP_N,
                        help=f"Number of top processes to show (default: {DEFAULT_TOP_N})")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="Output JSON (Kothar SystemHealthReport superset)")
    parser.add_argument("--no-color", action="store_true",
                        help="Disable ANSI color codes")
    parser.add_argument("--category", type=str, default=None,
                        help="Filter to category: claude, chrome, ide, ml, devserv, system, other")
    parser.add_argument("--record", action="store_true",
                        help="Persist snapshot to JSONL + memory.db")
    parser.add_argument("--kill", type=int, metavar="PID",
                        help="Send SIGTERM to a process")
    parser.add_argument("--history", action="store_true",
                        help="Show last 24h of recorded snapshots")
    parser.add_argument("--disk", action="store_true",
                        help="Disk view: volumes, purgeable space, hotspot dirs")
    parser.add_argument("--daemon", action="store_true",
                        help="Run in daemon mode (loop + record)")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL_MIN,
                        help=f"Daemon interval in minutes (default: {DEFAULT_INTERVAL_MIN})")

    args = parser.parse_args()

    # Respect NO_COLOR env var
    no_color = args.no_color or os.environ.get("NO_COLOR", "") != ""

    # Dispatch to sub-commands
    if args.kill is not None:
        kill_process(args.kill)
        return

    if args.history:
        show_history(args.as_json)
        return

    if args.disk:
        show_disk(args.as_json, no_color)
        return

    if args.daemon:
        run_daemon(args.interval, args.top)
        return

    # Main path: snapshot + display (iostat sample only on JSON/record paths)
    snapshot = take_snapshot(with_io=args.as_json or args.record)
    agg = aggregate(snapshot, args.category)

    if args.as_json:
        print(format_json_pretty(snapshot, agg, args.top, args.category))
        if args.record:
            compact = format_json_compact(snapshot, agg, args.top, args.category)
            record(snapshot, agg, compact)
    else:
        output = format_terminal(snapshot, agg, args.top, args.category, no_color)
        print(output)
        if args.record:
            compact = format_json_compact(snapshot, agg, args.top, args.category)
            record(snapshot, agg, compact)


if __name__ == "__main__":
    main()
