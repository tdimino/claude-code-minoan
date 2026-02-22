#!/usr/bin/env python3
"""PostToolUse hook: auto-rename session when a plan file is written.

Matcher: Write
When the written file is in ~/.claude/plans/, extracts the H1 header and appends
a {"type": "custom-title"} event to the session JSONL—the same authoritative
mechanism that /rename uses. Idempotent via 4KB tail-scan. ~5ms.
"""
import json
import os
import pathlib
import re
import sys

PLANS_DIR = str(pathlib.Path.home() / ".claude" / "plans")
PENDING_DIR = pathlib.Path.home() / ".claude" / "session-tags"

# H1 header — accept any non-empty content after "# "
H1_RE = re.compile(r"^#\s+(.+)", re.MULTILINE)


def extract_h1(content):
    """Extract first H1 header from markdown content (first 2KB)."""
    m = H1_RE.search(content[:2048])
    if not m:
        return ""
    title = m.group(1).strip()
    return re.sub(r"^Plan:\s*", "", title, flags=re.IGNORECASE)


def has_custom_title(jsonl_path):
    """Check if a custom-title event exists by scanning the last 4KB."""
    try:
        with open(jsonl_path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            chunk = min(4096, size)
            f.seek(size - chunk)
            tail = f.read().decode("utf-8", errors="replace")
        for line in reversed(tail.splitlines()):
            line = line.strip()
            if not line:
                continue
            try:
                if json.loads(line).get("type") == "custom-title":
                    return True
            except (json.JSONDecodeError, ValueError):
                continue
    except OSError:
        pass
    return False


def jsonl_path_for(session_id, cwd):
    """Derive the session JSONL path from cwd and session ID."""
    project_dir = cwd.replace("/", "-")
    if not project_dir.startswith("-"):
        project_dir = "-" + project_dir
    return (
        pathlib.Path.home()
        / ".claude"
        / "projects"
        / project_dir
        / f"{session_id}.jsonl"
    )


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    # Guard: only act on writes to ~/.claude/plans/
    filepath = data.get("tool_input", {}).get("file_path", "")
    if not filepath:
        return
    try:
        pathlib.Path(os.path.abspath(filepath)).relative_to(PLANS_DIR)
    except ValueError:
        return

    # Extract title from plan content
    content = data.get("tool_input", {}).get("content", "")
    if not content:
        try:
            content = pathlib.Path(filepath).read_text()[:2048]
        except (OSError, UnicodeDecodeError):
            return

    title = extract_h1(content)
    if not title:
        return

    session_id = data.get("session_id", "")
    cwd = data.get("cwd", "")
    if not session_id or not cwd:
        return

    # Resolve JSONL path
    jsonl = jsonl_path_for(session_id, cwd)

    if not jsonl.exists():
        # Session JSONL not on disk yet (rare race) — save breadcrumb
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        pending = PENDING_DIR / f"{session_id}.pending-title"
        try:
            pending.write_text(title)
            print(f"plan-session-rename: pending '{title}' for {session_id[:8]}", file=sys.stderr)
        except OSError:
            pass
        return

    # Idempotency: skip if already titled
    if has_custom_title(jsonl):
        return

    # Append the authoritative custom-title event
    event = json.dumps({"type": "custom-title", "customTitle": title, "sessionId": session_id})
    try:
        with open(jsonl, "a") as f:
            f.write(event + "\n")
        print(f"plan-session-rename: '{title}' for {session_id[:8]}", file=sys.stderr)
    except OSError:
        pass


if __name__ == "__main__":
    main()
