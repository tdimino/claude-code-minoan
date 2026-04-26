#!/usr/bin/env python3
"""Speculator — Ghostty Tab Discovery Daemon.

Polls every 5 minutes to discover Ghostty terminal tabs and map them to
running Claude Code sessions. Writes JSON + Markdown snapshots for
consumption by agent_docs and other Claude sessions.
"""

import argparse
import json
import logging
import os
import re
import signal
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR / "data"
LOG_DIR = SCRIPT_DIR / "logs"
HOME = Path.home()
CLAUDE_DIR = HOME / ".claude"
SESSIONS_DIR = CLAUDE_DIR / "sessions"
SOUL_REGISTRY = CLAUDE_DIR / "soul-sessions" / "registry.json"
SESSION_SUMMARIES = CLAUDE_DIR / "session-summaries.json"
SESSION_TAGS_DIR = CLAUDE_DIR / "session-tags"
AGENT_DOCS_DIR = CLAUDE_DIR / "agent_docs"
OUTPUT_JSON = DATA_DIR / "ghostty-sessions.json"
OUTPUT_MD = DATA_DIR / "ghostty-sessions.md"
AGENT_DOCS_MD = AGENT_DOCS_DIR / "ghostty-sessions.md"
DEFAULT_INTERVAL = 300

log = logging.getLogger("speculator")
_shutdown = False


def setup_logging(daemon_mode: bool):
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    log.setLevel(logging.INFO)
    if daemon_mode:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        from logging.handlers import TimedRotatingFileHandler
        fh = TimedRotatingFileHandler(LOG_DIR / "speculator.log", when="midnight", backupCount=7)
        fh.setFormatter(fmt)
        log.addHandler(fh)
    else:
        sh = logging.StreamHandler()
        sh.setFormatter(fmt)
        log.addHandler(sh)


def handle_signal(sig, _frame):
    global _shutdown
    log.info("received signal %s, shutting down", sig)
    _shutdown = True


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_ghostty_pid() -> int | None:
    # pgrep can't find app-launched Ghostty on macOS; use ps + grep
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,comm"], text=True, timeout=5
        )
        for line in out.strip().splitlines()[1:]:
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and "Ghostty.app/Contents/MacOS/ghostty" in parts[1]:
                return int(parts[0])
        return None
    except subprocess.TimeoutExpired:
        log.warning("ps timed out while searching for Ghostty PID")
        return None
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.warning("failed to enumerate processes: %s", e)
        return None


def find_ghostty_ttys(ghostty_pid: int) -> list[dict]:
    """Find login children of Ghostty — one per tab/split, each with a unique TTY."""
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,ppid,tty,comm"],
            text=True, timeout=5
        )
    except subprocess.TimeoutExpired:
        log.warning("ps timed out enumerating Ghostty TTYs")
        return []
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.warning("failed to enumerate Ghostty TTYs: %s", e)
        return []

    results = []
    for line in out.strip().splitlines()[1:]:
        parts = line.strip().split(None, 3)
        if len(parts) < 4:
            continue
        try:
            pid = int(parts[0])
            ppid = int(parts[1])
        except ValueError:
            continue
        if ppid != ghostty_pid:
            continue
        tty = parts[2]
        if tty == "??":
            continue
        results.append({"pid": pid, "tty": tty})

    return sorted(results, key=lambda x: x["tty"])


def find_claude_processes() -> list[dict]:
    """Find all claude CLI processes with their TTYs."""
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,tty,args"],
            text=True, timeout=5
        )
    except subprocess.TimeoutExpired:
        log.warning("ps timed out enumerating Claude processes")
        return []
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        log.warning("failed to enumerate Claude processes: %s", e)
        return []

    results = []
    for line in out.strip().splitlines()[1:]:
        parts = line.split(None, 2)
        if len(parts) < 3:
            continue
        try:
            pid = int(parts[0])
        except ValueError:
            continue
        tty = parts[1]
        args = parts[2]
        if not re.search(r"(^|/)claude(\s|$)|\.claude/.*versions/\d", args):
            continue
        if "bun" in args or "node" in args or "python" in args:
            continue
        if tty == "??":
            continue
        results.append({"pid": pid, "tty": tty, "args": args})

    return results


def get_ghostty_windows() -> list[str]:
    """Get Ghostty window names via System Events accessibility API."""
    script = '''
    tell application "System Events"
        if not (exists process "ghostty") then return ""
        tell process "ghostty"
            set out to ""
            repeat with w in windows
                set out to out & (name of w) & linefeed
            end repeat
            return out
        end tell
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            log.debug("System Events query failed (expected in daemon context): %s", result.stderr.strip())
            return []
        names = [n.strip() for n in result.stdout.strip().splitlines() if n.strip()]
        if not names:
            log.debug("System Events returned no windows (may lack GUI access in launchd)")
        return names
    except subprocess.TimeoutExpired:
        log.warning("System Events query timed out")
        return []


def get_ghostty_version() -> str | None:
    try:
        result = subprocess.run(
            ["/Applications/Ghostty.app/Contents/MacOS/ghostty", "+version"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.startswith("Ghostty"):
                    return line.replace("Ghostty", "").strip()
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def try_native_api() -> dict | None:
    """Attempt Ghostty's native AppleScript API. Returns None if unavailable."""
    try:
        result = subprocess.run(
            ["osascript", "-e", 'tell application "Ghostty" to return id of window 1'],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            log.info("native Ghostty AppleScript API available — using direct enumeration")
            return _enumerate_native()
    except subprocess.TimeoutExpired:
        pass
    return None


def _enumerate_native() -> dict | None:
    """Full tab enumeration via native Ghostty AppleScript (when sdef is present)."""
    script = '''
    tell application "Ghostty"
        set out to ""
        repeat with w in windows
            set wId to id of w
            set selTab to selected tab of w
            repeat with t in tabs of w
                set tIdx to index of t
                set tName to name of t
                set tSel to (t is selTab)
                repeat with term in terminals of t
                    set tCwd to working directory of term
                    set tId to id of term
                    set out to out & wId & "|" & tIdx & "|" & tName & "|" & tSel & "|" & tCwd & "|" & tId & linefeed
                end repeat
            end repeat
        end repeat
        return out
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode != 0:
            return None
        tabs = []
        for line in result.stdout.strip().splitlines():
            parts = line.split("|")
            if len(parts) >= 6:
                tabs.append({
                    "window_id": parts[0],
                    "tab_index": int(parts[1]),
                    "tab_name": parts[2],
                    "active": parts[3].lower() == "true",
                    "cwd": parts[4],
                    "terminal_id": parts[5],
                })
        return {"tabs": tabs}
    except subprocess.TimeoutExpired:
        return None


# ---------------------------------------------------------------------------
# Enrichment
# ---------------------------------------------------------------------------

def read_session_pid_file(pid: int) -> dict | None:
    path = SESSIONS_DIR / f"{pid}.json"
    if not path.exists():
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log.warning("corrupt session file %s: %s", path, e)
        return None
    except OSError as e:
        log.warning("cannot read session file %s: %s", path, e)
        return None


def _load_json_file(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


_soul_registry_cache = None
_soul_registry_mtime = 0

def enrich_from_soul_registry(session_id: str) -> dict:
    global _soul_registry_cache, _soul_registry_mtime
    try:
        mtime = SOUL_REGISTRY.stat().st_mtime
    except OSError:
        return {}
    if _soul_registry_cache is None or mtime != _soul_registry_mtime:
        _soul_registry_cache = _load_json_file(SOUL_REGISTRY)
        _soul_registry_mtime = mtime
    sessions = _soul_registry_cache.get("sessions", {})
    entry = sessions.get(session_id, {})
    return {k: entry[k] for k in ("topic", "summary", "slack_channel_name") if k in entry and entry[k]}


_summaries_cache = None
_summaries_mtime = 0

def enrich_from_summaries(session_id: str) -> dict:
    if not session_id:
        return {}
    global _summaries_cache, _summaries_mtime
    try:
        mtime = SESSION_SUMMARIES.stat().st_mtime
    except OSError:
        return {}
    if _summaries_cache is None or mtime != _summaries_mtime:
        _summaries_cache = _load_json_file(SESSION_SUMMARIES)
        _summaries_mtime = mtime
    # Exact match first, then prefix fallback
    entry = _summaries_cache.get(session_id)
    if not entry:
        for k, v in _summaries_cache.items():
            if k.startswith(session_id) or session_id.startswith(k):
                entry = v
                break
    if entry:
        return {key: entry[key] for key in ("title", "summary") if key in entry and entry[key]}
    return {}


def enrich_from_tags(session_id: str) -> list[str]:
    path = SESSION_TAGS_DIR / f"{session_id}.json"
    data = _load_json_file(path)
    return data.get("displayTags", data.get("tags", []))


def get_git_branch(cwd: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", cwd, "branch", "--show-current"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            return result.stdout.strip() or None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass
    return None


def extract_project_name(cwd: str) -> str:
    home = str(HOME)
    if cwd.startswith(home):
        rel = cwd[len(home):].strip("/")
        parts = rel.split("/")
        if len(parts) >= 2 and parts[0] == "Desktop":
            if len(parts) >= 3 and parts[1] == "Programming":
                return parts[2]
            if len(parts) >= 2:
                return parts[1] if parts[1] != "Programming" else "Programming"
        return parts[-1] if parts else "~"
    return Path(cwd).name


# ---------------------------------------------------------------------------
# Snapshot Builder
# ---------------------------------------------------------------------------

def build_snapshot() -> dict:
    ghostty_pid = find_ghostty_pid()
    ghostty_running = ghostty_pid is not None
    ghostty_version = get_ghostty_version() if ghostty_running else None
    windows = get_ghostty_windows() if ghostty_running else []

    ghostty_ttys = find_ghostty_ttys(ghostty_pid) if ghostty_pid else []
    ghostty_tty_set = {t["tty"] for t in ghostty_ttys}

    claude_procs = find_claude_processes()
    claude_by_tty = {}
    for proc in claude_procs:
        claude_by_tty.setdefault(proc["tty"], []).append(proc)

    sessions = []
    for tab_info in ghostty_ttys:
        tty = tab_info["tty"]
        claude_list = claude_by_tty.get(tty, [])
        if not claude_list:
            sessions.append({
                "tty": tty,
                "claude_session": None,
            })
            continue

        for cproc in claude_list:
            pid_data = read_session_pid_file(cproc["pid"])
            if not pid_data:
                sessions.append({
                    "tty": tty,
                    "claude_session": {
                        "pid": cproc["pid"],
                        "sessionId": None,
                        "shortId": None,
                        "cwd": None,
                        "project": None,
                        "status": None,
                        "kind": None,
                        "entrypoint": None,
                        "version": None,
                        "startedAt": None,
                        "title": None,
                        "summary": None,
                        "topic": None,
                        "tags": [],
                        "gitBranch": None,
                    },
                })
                continue

            session_id = pid_data.get("sessionId", "")
            cwd = pid_data.get("cwd", "")
            started_epoch = pid_data.get("startedAt")
            started_str = None
            if started_epoch:
                try:
                    started_str = datetime.fromtimestamp(started_epoch / 1000, tz=timezone.utc).isoformat()
                except (ValueError, OSError):
                    pass

            soul_data = enrich_from_soul_registry(session_id)
            summary_data = enrich_from_summaries(session_id)
            tags = enrich_from_tags(session_id)
            git_branch = get_git_branch(cwd) if cwd else None

            sessions.append({
                "tty": tty,
                "claude_session": {
                    "pid": cproc["pid"],
                    "sessionId": session_id,
                    "shortId": session_id[:8] if session_id else None,
                    "cwd": cwd,
                    "project": extract_project_name(cwd) if cwd else None,
                    "status": pid_data.get("status"),
                    "kind": pid_data.get("kind"),
                    "entrypoint": pid_data.get("entrypoint"),
                    "version": pid_data.get("version"),
                    "startedAt": started_str,
                    "title": summary_data.get("title") or soul_data.get("topic"),
                    "summary": summary_data.get("summary") or soul_data.get("summary"),
                    "topic": soul_data.get("topic"),
                    "tags": tags,
                    "gitBranch": git_branch,
                },
            })

    # Sessions on non-Ghostty TTYs
    other_sessions = []
    for tty, cprocs in claude_by_tty.items():
        if tty not in ghostty_tty_set:
            for cproc in cprocs:
                pid_data = read_session_pid_file(cproc["pid"])
                other_sessions.append({
                    "tty": tty,
                    "pid": cproc["pid"],
                    "cwd": pid_data.get("cwd") if pid_data else None,
                    "sessionId": pid_data.get("sessionId") if pid_data else None,
                })

    # Orphan TTYs (Ghostty tabs without Claude)
    orphan_ttys = [t["tty"] for t in ghostty_ttys if t["tty"] not in claude_by_tty]

    # Stats
    statuses = {}
    total_with_claude = 0
    for s in sessions:
        cs = s.get("claude_session")
        if cs:
            total_with_claude += 1
            st = cs.get("status") or "unknown"
            statuses[st] = statuses.get(st, 0) + 1

    return {
        "schema_version": 1,
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "ghostty": {
            "running": ghostty_running,
            "pid": ghostty_pid,
            "version": ghostty_version,
            "windows": windows,
        },
        "sessions": sessions,
        "other_sessions": other_sessions,
        "orphan_ttys": orphan_ttys,
        "stats": {
            "total_ttys": len(ghostty_ttys),
            "ttys_with_claude": total_with_claude,
            "other_claude_sessions": len(other_sessions),
            "sessions_by_status": statuses,
        },
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def atomic_write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    try:
        os.write(fd, content.encode())
        os.close(fd)
        fd = -1
        os.replace(tmp, path)
    except BaseException:
        if fd >= 0:
            try:
                os.close(fd)
            except OSError:
                pass
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def write_json_output(snapshot: dict):
    atomic_write(OUTPUT_JSON, json.dumps(snapshot, indent=2) + "\n")


def write_markdown_output(snapshot: dict):
    ts = snapshot["timestamp"][:19].replace("T", " ")
    g = snapshot["ghostty"]
    stats = snapshot["stats"]

    lines = ["# Ghostty Terminal Map", ""]

    if not g["running"]:
        lines.append(f"*Updated: {ts} | Ghostty not running*")
        lines.append("")
        lines.append("No Ghostty process detected.")
    else:
        win_str = f"{len(g['windows'])} windows" if g["windows"] else ""
        header_parts = [f"Updated: {ts}", f"Ghostty PID {g['pid']}"]
        if win_str:
            header_parts.append(win_str)
        header_parts.append(f"{stats['total_ttys']} tabs")
        lines.append(f"*{' | '.join(header_parts)}*")
        lines.append("")

        lines.append("| TTY | PID | Status | Project | Branch | Title | Session |")
        lines.append("|-----|-----|--------|---------|--------|-------|---------|")

        for entry in snapshot["sessions"]:
            tty = entry["tty"].replace("ttys", "s")
            cs = entry.get("claude_session")
            if not cs:
                lines.append(f"| {tty} | — | — | *(no claude)* | — | — | — |")
                continue

            pid = cs["pid"]
            status = cs.get("status") or "—"
            if status == "busy":
                status = "**busy**"
            project = cs.get("project") or "—"
            branch = cs.get("gitBranch") or "—"
            title = cs.get("title") or "—"
            if len(title) > 40:
                title = title[:37] + "..."
            short_id = cs.get("shortId") or "—"
            sid_str = f"`{short_id}`" if short_id != "—" else "—"

            lines.append(f"| {tty} | {pid} | {status} | {project} | {branch} | {title} | {sid_str} |")

        if snapshot.get("orphan_ttys"):
            for tty in snapshot["orphan_ttys"]:
                tty_short = tty.replace("ttys", "s")
                lines.append(f"| {tty_short} | — | — | *(no claude)* | — | — | — |")

    if snapshot.get("other_sessions"):
        lines.extend(["", "### Non-Ghostty Sessions", ""])
        for s in snapshot["other_sessions"]:
            lines.append(f"- TTY {s['tty']}: PID {s['pid']} ({s.get('cwd', '?')})")

    if g.get("windows"):
        lines.extend(["", f"**Windows:** {' | '.join(g['windows'])}"])

    status_parts = []
    for st, count in sorted(stats.get("sessions_by_status", {}).items()):
        status_parts.append(f"{count} {st}")
    status_summary = ", ".join(status_parts) if status_parts else "none"
    orphan_count = len(snapshot.get("orphan_ttys", []))
    lines.append(
        f"**Summary:** {stats['ttys_with_claude']} Claude sessions ({status_summary})"
        + (f", {orphan_count} empty tab{'s' if orphan_count != 1 else ''}" if orphan_count else "")
    )
    lines.append("")

    atomic_write(OUTPUT_MD, "\n".join(lines))


def sync_to_agent_docs():
    if OUTPUT_MD.exists():
        content = OUTPUT_MD.read_text()
        atomic_write(AGENT_DOCS_MD, content)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_once():
    log.info("building snapshot")
    snapshot = build_snapshot()
    write_json_output(snapshot)
    write_markdown_output(snapshot)
    try:
        sync_to_agent_docs()
    except Exception:
        log.exception("failed to sync to agent_docs (snapshot still written)")
    sc = snapshot["stats"]["ttys_with_claude"]
    tt = snapshot["stats"]["total_ttys"]
    log.info("snapshot complete: %d Claude sessions across %d tabs", sc, tt)
    return snapshot


def run_daemon(interval: int = DEFAULT_INTERVAL):
    log.info("speculator daemon starting (interval=%ds)", interval)
    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    while not _shutdown:
        try:
            run_once()
        except Exception:
            log.exception("snapshot failed")
        for _ in range(interval):
            if _shutdown:
                break
            time.sleep(1)

    log.info("speculator daemon stopped")


def main():
    parser = argparse.ArgumentParser(description="Speculator — Ghostty Tab Discovery Daemon")
    parser.add_argument("--once", action="store_true", help="Run once and exit")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon with polling loop")
    parser.add_argument("--interval", type=int, default=DEFAULT_INTERVAL, help="Poll interval in seconds")
    parser.add_argument("--json", action="store_true", help="Print snapshot JSON to stdout")
    args = parser.parse_args()

    setup_logging(daemon_mode=args.daemon)

    if args.once or args.json:
        snapshot = run_once()
        if args.json:
            print(json.dumps(snapshot, indent=2))
    elif args.daemon:
        run_daemon(args.interval)
    else:
        snapshot = run_once()
        print(json.dumps(snapshot, indent=2))


if __name__ == "__main__":
    main()
