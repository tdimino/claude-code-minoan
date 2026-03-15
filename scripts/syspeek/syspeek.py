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

SCHEMA_VERSION = 1
DEFAULT_TOP_N = 10
DEFAULT_INTERVAL_MIN = 5
ROTATION_DAYS = 7

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


def take_snapshot() -> SystemSnapshot:
    """Capture a full system snapshot."""
    procs = capture_processes()
    mem = capture_memory()
    thermal = capture_thermal()
    network = capture_network()

    return SystemSnapshot(
        timestamp=datetime.now().isoformat(timespec="seconds"),
        hostname=os.uname().nodename,
        cpu_count=os.cpu_count() or 1,
        memory=mem,
        processes=procs,
        thermal_level=thermal,
        network_available=network,
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

    # Thermal
    if snapshot.thermal_level != "normal":
        t_color = "\033[33m" if snapshot.thermal_level == "elevated" else "\033[31m"
        lines.append(f"  {_colored(f'THERMAL: {snapshot.thermal_level.upper()}', t_color, nc)}")

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
        "gpuUsage": 0,  # requires IOKit — v2
        "thermalLevel": snapshot.thermal_level,
        "diskIO": {"readsPerSec": 0, "writesPerSec": 0},  # requires iostat — v2
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
    parts = [f"{mem.used_pct:.1f}% mem, {agg['total_cpu']:.1f}% CPU, {agg['total_processes']} procs"]
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


def record(snapshot: SystemSnapshot, agg: dict, snapshot_json: str):
    """Persist snapshot to JSONL (always) and memory.db (if ensouled)."""
    jsonl_path = record_to_jsonl(snapshot_json)
    summary = one_line_summary(snapshot, agg)

    ensouled = is_ensouled()
    if ensouled:
        ok = record_to_memory_db(snapshot_json, snapshot.snapshot_id, summary)
        _log(f"Recorded {snapshot.snapshot_id}: JSONL={jsonl_path.name}, memory.db={'ok' if ok else 'failed'}")
    else:
        _log(f"Recorded {snapshot.snapshot_id}: JSONL={jsonl_path.name} (not ensouled)")


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
        print(f"  {'TIMESTAMP':<20}  {'CPU%':>6}  {'MEM%':>6}  {'PROCS':>6}  {'THERMAL'}")
        print(f"  {'─' * 20}  {'─' * 6}  {'─' * 6}  {'─' * 6}  {'─' * 8}")
        for snap in snapshots:
            ts = snap.get("timestamp", "")[:19]
            cpu = snap.get("cpuUsage", 0)
            mem_pct = snap.get("memoryUsage", 0)
            n_procs = snap.get("total_processes", 0)
            thermal = snap.get("thermalLevel", "normal")
            print(f"  {ts:<20}  {cpu:>6.1f}  {mem_pct:>6.1f}  {n_procs:>6}  {thermal}")


# ---------------------------------------------------------------------------
# Daemon
# ---------------------------------------------------------------------------

def rotate_logs():
    """Gzip JSONL files older than ROTATION_DAYS."""
    if not DATA_DIR.exists():
        return
    cutoff = date.today() - timedelta(days=ROTATION_DAYS)
    for jsonl_file in DATA_DIR.glob("*.jsonl"):
        try:
            file_date = date.fromisoformat(jsonl_file.stem)
            if file_date < cutoff:
                gz_path = jsonl_file.with_suffix(".jsonl.gz")
                if not gz_path.exists():
                    with open(jsonl_file, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                        f_out.writelines(f_in)
                    jsonl_file.unlink()
        except ValueError:
            continue


def run_daemon(interval_min: int, top_n: int):
    """Daemon mode: snapshot + record every interval_min minutes."""
    _log(f"syspeek daemon started (interval: {interval_min}m, ensouled: {is_ensouled()})")

    while True:
        try:
            snapshot = take_snapshot()
            agg = aggregate(snapshot)
            snapshot_json = format_json_compact(snapshot, agg, top_n, None)

            record(snapshot, agg, snapshot_json)
            rotate_logs()

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

    if args.daemon:
        run_daemon(args.interval, args.top)
        return

    # Main path: snapshot + display
    snapshot = take_snapshot()
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
