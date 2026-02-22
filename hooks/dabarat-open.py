#!/usr/bin/env python3
"""PostToolUse hook: auto-open markdown files in dabarat.

Matcher: Write
Fires after Claude Code writes any .md file in watched dirs or the project dir.

If dabarat is running: adds as tab (or confirms already open).
If dabarat is not running: launches new window.
"""
import json
import os
import subprocess
import sys
import urllib.request

DABARAT_PORT = 3031

# Directories to watch for new .md files
WATCHED_DIRS = [
    os.path.expanduser("~/.claude/plans"),
    os.path.expanduser("~/.claude/hooks"),
    os.path.expanduser("~/.claude/agent_docs"),
    os.path.expanduser("~/.claude/commands"),
    os.path.expanduser("~/.claude/scripts"),
]

# Files to skip (auto-generated, ephemeral)
SKIP_PATTERNS = [
    "INDEX.md",          # We create these ourselves
    ".annotations.",     # Dabarat sidecars
    "sessions-index.",   # Auto-generated
]


def _server_running():
    """Check if dabarat is listening on its port."""
    try:
        req = urllib.request.Request(f"http://127.0.0.1:{DABARAT_PORT}/api/tabs")
        urllib.request.urlopen(req, timeout=1)
        return True
    except Exception:
        return False


def _add_tab(filepath):
    """Add file as tab to running dabarat server."""
    try:
        req_data = json.dumps({"filepath": filepath}).encode()
        req = urllib.request.Request(
            f"http://127.0.0.1:{DABARAT_PORT}/api/add",
            data=req_data,
            headers={
                "Content-Type": "application/json",
                "Origin": f"http://127.0.0.1:{DABARAT_PORT}",
            },
        )
        resp = urllib.request.urlopen(req, timeout=3)
        result = json.loads(resp.read())
        existing = result.get("existing", False)
        status = "already open" if existing else "added"
        print(f"dabarat-open: {status} {os.path.basename(filepath)}", file=sys.stdout)
        return not existing  # True if newly added
    except Exception as e:
        print(f"dabarat-open: add failed: {e}", file=sys.stdout)
        return False


def _launch_new(filepath):
    """Launch dabarat with new window."""
    try:
        subprocess.Popen(
            ["dabarat", filepath],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        print(f"dabarat-open: launched new window for {os.path.basename(filepath)}", file=sys.stdout)
    except FileNotFoundError:
        pass


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    # PostToolUse provides tool_input with the Write tool's parameters
    tool_input = data.get("tool_input", {})
    filepath = tool_input.get("file_path", "")

    if not filepath:
        return

    # Only .md files
    if not filepath.endswith(".md"):
        return

    # Skip patterns
    basename = os.path.basename(filepath)
    for pattern in SKIP_PATTERNS:
        if pattern in basename:
            return

    # Check if file is in a watched directory OR in the current working directory
    abs_path = os.path.abspath(filepath)
    in_watched = any(abs_path.startswith(d) for d in WATCHED_DIRS)

    # Also allow .md files in the project's working directory
    cwd = data.get("cwd", "")
    in_project = cwd and abs_path.startswith(cwd)

    if not in_watched and not in_project:
        return

    # File must exist
    if not os.path.isfile(filepath):
        return

    # Open in dabarat
    if _server_running():
        _add_tab(abs_path)
    else:
        _launch_new(abs_path)


if __name__ == "__main__":
    main()
