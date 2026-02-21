#!/usr/bin/env python3
"""
Soul session registry — tracks active Claudicle sessions across Claude Code instances.

Provides a shared utility for session lifecycle hooks:
  - soul-activate.py (SessionStart) calls: register, cleanup, list
  - stop-handoff.py (Stop) calls: heartbeat
  - soul-deregister.py (SessionEnd) calls: deregister
  - /slack-sync command calls: bind

Registry stored as JSON at ~/.claude/soul-sessions/registry.json
with companion SESSIONS.md for human inspection.

Usage:
    soul-registry.py register <session_id> <cwd> [--pid PID] [--model MODEL]
    soul-registry.py deregister <session_id>
    soul-registry.py bind <session_id> <channel_id> <channel_name>
    soul-registry.py heartbeat <session_id> [--topic TOPIC]
    soul-registry.py list [--json | --md]
    soul-registry.py cleanup
"""

import argparse
import datetime
import fcntl
import json
import os
import sys
import tempfile

REGISTRY_DIR = os.path.expanduser("~/.claude/soul-sessions")
REGISTRY_FILE = os.path.join(REGISTRY_DIR, "registry.json")
SESSIONS_MD = os.path.join(REGISTRY_DIR, "SESSIONS.md")
STALE_HOURS = 2


def _ensure_dir():
    os.makedirs(REGISTRY_DIR, exist_ok=True)


def _load_registry():
    """Load registry with file locking."""
    _ensure_dir()
    if not os.path.exists(REGISTRY_FILE):
        return {"sessions": {}}
    try:
        with open(REGISTRY_FILE) as f:
            fcntl.flock(f, fcntl.LOCK_SH)
            data = json.load(f)
            fcntl.flock(f, fcntl.LOCK_UN)
        return data
    except (json.JSONDecodeError, OSError):
        return {"sessions": {}}


def _save_registry(data):
    """Atomic write with file locking."""
    _ensure_dir()
    data["updated_at"] = datetime.datetime.now().isoformat(timespec="seconds")

    # Write to temp file then atomic rename
    fd, tmp_path = tempfile.mkstemp(dir=REGISTRY_DIR, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            json.dump(data, f, indent=2)
            f.write("\n")
            fcntl.flock(f, fcntl.LOCK_UN)
        os.rename(tmp_path, REGISTRY_FILE)
    except Exception:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    # Regenerate companion markdown
    _write_sessions_md(data)


def _write_sessions_md(data):
    """Regenerate SESSIONS.md from registry data."""
    sessions = data.get("sessions", {})
    if not sessions:
        md = "# Active Soul Sessions\n\n_No active sessions._\n"
    else:
        lines = [
            "# Active Soul Sessions",
            "",
            "_Auto-updated by soul hooks. Do not edit manually._",
            "",
            "| Session | Project | Directory | Started | Last Active | Slack | Topic |",
            "|---------|---------|-----------|---------|-------------|-------|-------|",
        ]
        for sid, info in sorted(sessions.items(), key=lambda x: x[1].get("started_at", "")):
            short = info.get("short_id", sid[:8])
            project = info.get("project", "?")
            cwd = info.get("cwd", "?")
            # Shorten home directory
            cwd = cwd.replace(os.path.expanduser("~"), "~")
            started = info.get("started_at", "?")
            if "T" in started:
                started = started.split("T")[1][:5]
            last = info.get("last_active", "?")
            if "T" in last:
                last = last.split("T")[1][:5]
            slack = info.get("slack_channel_name") or "--"
            topic = info.get("topic", "--") or "--"
            if len(topic) > 40:
                topic = topic[:37] + "..."
            lines.append(f"| `{short}` | {project} | {cwd} | {started} | {last} | {slack} | {topic} |")

        # Append summaries below the table
        summaries = []
        for sid, info in sorted(sessions.items(), key=lambda x: x[1].get("started_at", "")):
            summary = info.get("summary", "")
            if summary:
                short = info.get("short_id", sid[:8])
                summaries.append(f"- **`{short}`**: {summary}")
        if summaries:
            lines.append("")
            lines.append("### Summaries")
            lines.append("")
            lines.extend(summaries)

        md = "\n".join(lines) + "\n"

    with open(SESSIONS_MD, "w") as f:
        f.write(md)


def _is_process_alive(pid):
    """Check if a process with the given PID is running."""
    if pid is None:
        return False
    try:
        os.kill(pid, 0)
        return True
    except (OSError, TypeError):
        return False


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_register(args):
    """Register or re-register a session."""
    data = _load_registry()
    now = datetime.datetime.now().isoformat(timespec="seconds")

    existing = data["sessions"].get(args.session_id, {})
    entry = {
        "short_id": args.session_id[:8],
        "cwd": os.path.abspath(args.cwd),
        "project": os.path.basename(os.path.abspath(args.cwd)),
        "started_at": existing.get("started_at", now),
        "last_active": now,
        "pid": args.pid or os.getppid(),
        "slack_channel": existing.get("slack_channel"),
        "slack_channel_name": existing.get("slack_channel_name"),
        "topic": existing.get("topic", ""),
        "summary": existing.get("summary", ""),
        "model": args.model or existing.get("model", ""),
    }
    data["sessions"][args.session_id] = entry
    _save_registry(data)
    print(f"Registered session {args.session_id[:8]}", file=sys.stderr)


def cmd_deregister(args):
    """Remove a session from the registry."""
    data = _load_registry()
    if args.session_id in data["sessions"]:
        del data["sessions"][args.session_id]
        _save_registry(data)
        print(f"Deregistered session {args.session_id[:8]}", file=sys.stderr)
    else:
        print(f"Session {args.session_id[:8]} not in registry", file=sys.stderr)


def cmd_bind(args):
    """Bind a session to a Slack channel."""
    data = _load_registry()
    if args.session_id not in data["sessions"]:
        print(f"Session {args.session_id[:8]} not in registry", file=sys.stderr)
        sys.exit(1)
    data["sessions"][args.session_id]["slack_channel"] = args.channel_id
    data["sessions"][args.session_id]["slack_channel_name"] = args.channel_name
    _save_registry(data)
    print(f"Bound session {args.session_id[:8]} to {args.channel_name}", file=sys.stderr)


def cmd_heartbeat(args):
    """Update last_active timestamp for a session."""
    data = _load_registry()
    if args.session_id not in data["sessions"]:
        return  # Silent — session may not be registered yet
    now = datetime.datetime.now().isoformat(timespec="seconds")
    data["sessions"][args.session_id]["last_active"] = now
    if args.topic:
        data["sessions"][args.session_id]["topic"] = args.topic
    if args.summary:
        data["sessions"][args.session_id]["summary"] = args.summary
    _save_registry(data)


def cmd_list(args):
    """Print active sessions."""
    data = _load_registry()
    sessions = data.get("sessions", {})

    if args.json:
        print(json.dumps(sessions, indent=2))
        return

    if args.md:
        # Output just the table rows for embedding in additionalContext
        if not sessions:
            print("No active sessions.")
            return
        for sid, info in sorted(sessions.items(), key=lambda x: x[1].get("started_at", "")):
            short = info.get("short_id", sid[:8])
            project = info.get("project", "?")
            cwd = info.get("cwd", "?").replace(os.path.expanduser("~"), "~")
            slack = info.get("slack_channel_name")
            slack_str = f", bound to {slack}" if slack else ""
            topic = info.get("topic", "")
            topic_str = f" ({topic})" if topic else ""
            # Calculate duration
            started = info.get("started_at", "")
            duration_str = ""
            if started:
                try:
                    start_dt = datetime.datetime.fromisoformat(started)
                    elapsed = datetime.datetime.now() - start_dt
                    hours = int(elapsed.total_seconds() // 3600)
                    mins = int((elapsed.total_seconds() % 3600) // 60)
                    if hours > 0:
                        duration_str = f", {hours}h{mins}m"
                    elif mins > 0:
                        duration_str = f", {mins}m"
                except ValueError:
                    pass
            summary = info.get("summary", "")
            summary_str = f"\n  > {summary}" if summary else ""
            print(f"- `{short}` in {cwd}{topic_str}{slack_str}{duration_str}{summary_str}")
        return

    # Default: compact text
    if not sessions:
        print("No active sessions.")
        return
    for sid, info in sessions.items():
        short = info.get("short_id", sid[:8])
        project = info.get("project", "?")
        print(f"{short}  {project}  {info.get('last_active', '?')}")


def cmd_cleanup(args):
    """Remove stale sessions (dead PIDs or old timestamps)."""
    data = _load_registry()
    now = datetime.datetime.now()
    removed = []

    for sid in list(data["sessions"]):
        info = data["sessions"][sid]
        pid = info.get("pid")

        # Remove if PID is dead
        if not _is_process_alive(pid):
            removed.append(sid[:8])
            del data["sessions"][sid]
            continue

        # Remove if inactive for too long
        last = info.get("last_active", "")
        if last:
            try:
                last_dt = datetime.datetime.fromisoformat(last)
                if (now - last_dt).total_seconds() > STALE_HOURS * 3600:
                    removed.append(sid[:8])
                    del data["sessions"][sid]
                    continue
            except ValueError:
                pass

    if removed:
        _save_registry(data)
        print(f"Cleaned up {len(removed)} stale session(s): {', '.join(removed)}", file=sys.stderr)
    else:
        # Still regenerate MD in case it doesn't exist
        _write_sessions_md(data)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Soul session registry")
    sub = parser.add_subparsers(dest="command")

    # register
    p_reg = sub.add_parser("register", help="Register a session")
    p_reg.add_argument("session_id", help="Full session UUID")
    p_reg.add_argument("cwd", help="Working directory")
    p_reg.add_argument("--pid", type=int, help="Process ID (default: parent PID)")
    p_reg.add_argument("--model", help="Model name")

    # deregister
    p_dereg = sub.add_parser("deregister", help="Remove a session")
    p_dereg.add_argument("session_id", help="Full session UUID")

    # bind
    p_bind = sub.add_parser("bind", help="Bind session to Slack channel")
    p_bind.add_argument("session_id", help="Full session UUID")
    p_bind.add_argument("channel_id", help="Slack channel ID")
    p_bind.add_argument("channel_name", help="Slack channel name")

    # heartbeat
    p_hb = sub.add_parser("heartbeat", help="Update last_active")
    p_hb.add_argument("session_id", help="Full session UUID")
    p_hb.add_argument("--topic", help="Update session topic")
    p_hb.add_argument("--summary", help="Update session summary (2-4 sentences)")

    # list
    p_list = sub.add_parser("list", help="List active sessions")
    p_list.add_argument("--json", action="store_true", help="Output as JSON")
    p_list.add_argument("--md", action="store_true", help="Output as markdown lines")

    # cleanup
    sub.add_parser("cleanup", help="Remove stale sessions")

    args = parser.parse_args()

    commands = {
        "register": cmd_register,
        "deregister": cmd_deregister,
        "bind": cmd_bind,
        "heartbeat": cmd_heartbeat,
        "list": cmd_list,
        "cleanup": cmd_cleanup,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
