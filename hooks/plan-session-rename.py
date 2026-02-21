#!/usr/bin/env python3
"""PostToolUse hook: auto-rename session when a plan file is written.

Matcher: Write
When the written file is in ~/.claude/plans/, extracts the H1 header and sets
customTitle in sessions-index.json if none exists. No LLM call, pure local, ~10ms.
"""
import fcntl
import json
import os
import pathlib
import re
import sys

PLANS_DIR = str(pathlib.Path.home() / ".claude" / "plans")
SUMMARY_CACHE = pathlib.Path.home() / ".claude" / "session-summaries.json"
PENDING_DIR = pathlib.Path.home() / ".claude" / "session-tags"

H1_RE = re.compile(r"^#\s+([A-Z].+)", re.MULTILINE)


def extract_h1_from_content(content):
    """Extract first H1 header from markdown content."""
    head = content[:2048]
    m = H1_RE.search(head)
    if not m:
        return ""
    title = m.group(1).strip()
    title = re.sub(r"^Plan:\s*", "", title, flags=re.IGNORECASE)
    return title


def derive_index_path(cwd):
    """Convert cwd to Claude Code's sessions-index.json path."""
    name = cwd.replace("/", "-")
    if not name.startswith("-"):
        name = "-" + name
    return pathlib.Path.home() / ".claude" / "projects" / name / "sessions-index.json"


def set_session_title(session_id, index_path, title):
    """Set customTitle in sessions-index.json if none exists.

    Returns: True=wrote, False=already titled or error, None=session not in index.
    """
    if not index_path.exists():
        return None

    lock_path = pathlib.Path("/tmp") / f"claude-{os.getuid()}" / "sessions-index.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        lock_fd = open(lock_path, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        return None  # Lock contended — treat as unavailable

    try:
        index_data = json.loads(index_path.read_text())

        for entry in index_data.get("entries", []):
            if entry.get("sessionId") == session_id:
                if entry.get("customTitle"):
                    return False  # Already has a title
                entry["customTitle"] = title
                break
        else:
            return None  # Session not in index yet

        tmp = index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(index_data, indent=2))
        tmp.rename(index_path)
        return True
    except (json.JSONDecodeError, OSError):
        return None
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
        except OSError:
            pass


def propagate_to_summary_cache(session_id, title):
    """Sync title to session-summaries.json immediately."""
    cache = {}
    if SUMMARY_CACHE.exists():
        try:
            cache = json.loads(SUMMARY_CACHE.read_text())
        except (json.JSONDecodeError, OSError):
            cache = {}

    if session_id not in cache:
        cache[session_id] = {}
    if cache[session_id].get("title") == title:
        return

    cache[session_id]["title"] = title

    try:
        tmp = SUMMARY_CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, indent=2))
        tmp.rename(SUMMARY_CACHE)
    except OSError:
        pass


def save_pending_title(session_id, title):
    """Write breadcrumb for session-tags-infer.py to pick up on next Stop."""
    PENDING_DIR.mkdir(parents=True, exist_ok=True)
    pending_path = PENDING_DIR / f"{session_id}.pending-title"
    try:
        pending_path.write_text(title)
        print(f"plan-session-rename: saved pending title '{title}' for {session_id[:8]}", file=sys.stderr)
    except OSError:
        pass


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    tool_input = data.get("tool_input", {})
    filepath = tool_input.get("file_path", "")

    if not filepath:
        return

    try:
        pathlib.Path(os.path.abspath(filepath)).relative_to(PLANS_DIR)
    except ValueError:
        return

    content = tool_input.get("content", "")
    if not content:
        # Fallback: read from disk
        try:
            content = pathlib.Path(filepath).read_text()[:2048]
        except (OSError, UnicodeDecodeError):
            return

    title = extract_h1_from_content(content)
    if not title:
        return

    session_id = data.get("session_id", "")
    cwd = data.get("cwd", "")
    if not session_id or not cwd:
        return

    index_path = derive_index_path(cwd)

    result = set_session_title(session_id, index_path, title)
    if result is True:
        print(f"plan-session-rename: '{title}' for {session_id[:8]}", file=sys.stderr)
        propagate_to_summary_cache(session_id, title)
    elif result is None:
        # Session not in index yet or lock contended — save breadcrumb
        save_pending_title(session_id, title)


if __name__ == "__main__":
    main()
