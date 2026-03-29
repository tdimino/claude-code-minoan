#!/usr/bin/env python3
"""PostToolUse hook: surface mycelium notes after Write/Edit.

Matcher: Edit|Write
When a file is edited, checks for mycelium notes on that file and returns
them as additionalContext so the agent sees warnings, constraints, and
decisions left by prior sessions and subdaimones.

Follows the lint-on-write.py pattern: cooldown, file path extraction,
graceful degradation, timeout.
"""

import json
import os
import shutil
import subprocess
import sys
import time

COOLDOWN_FILE = "/tmp/mycelium-context-cooldown.json"
COOLDOWN_SECONDS = 5.0
PRUNE_AGE_SECONDS = 60.0
SUBPROCESS_TIMEOUT = 2  # mycelium.sh context should be fast


def load_cooldowns() -> dict:
    try:
        with open(COOLDOWN_FILE, "r") as f:
            data = json.load(f)
        now = time.time()
        return {k: v for k, v in data.items() if now - v < PRUNE_AGE_SECONDS}
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_cooldowns(data: dict):
    try:
        tmp = COOLDOWN_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(data, f)
        os.replace(tmp, COOLDOWN_FILE)
    except OSError:
        pass


def is_git_repo(path: str) -> bool:
    """Check if path is inside a git repo."""
    try:
        result = subprocess.run(
            ["git", "-C", os.path.dirname(path) or ".", "rev-parse", "--git-dir"],
            capture_output=True, timeout=2
        )
        return result.returncode == 0
    except (subprocess.SubprocessError, OSError):
        return False


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input", {})

    # Extract file path
    file_path = tool_input.get("file_path", "")
    if not file_path:
        sys.exit(0)

    # Skip non-code files
    _, ext = os.path.splitext(file_path)
    skip_exts = {".md", ".json", ".yaml", ".yml", ".toml", ".lock", ".env",
                 ".png", ".jpg", ".svg", ".gif", ".ico", ".woff", ".woff2"}
    if ext.lower() in skip_exts:
        sys.exit(0)

    # Check mycelium.sh is installed
    if not shutil.which("mycelium.sh"):
        sys.exit(0)

    # Check we're in a git repo
    if not is_git_repo(file_path):
        sys.exit(0)

    # Cooldown check
    cooldowns = load_cooldowns()
    now = time.time()
    if file_path in cooldowns and (now - cooldowns[file_path]) < COOLDOWN_SECONDS:
        sys.exit(0)

    cooldowns[file_path] = now
    save_cooldowns(cooldowns)

    # Get the repo root for running mycelium.sh
    try:
        result = subprocess.run(
            ["git", "-C", os.path.dirname(file_path) or ".", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=2
        )
        repo_root = result.stdout.strip()
        if not repo_root:
            sys.exit(0)
    except (subprocess.SubprocessError, OSError):
        sys.exit(0)

    # Make file path relative to repo root
    abs_path = os.path.abspath(file_path)
    try:
        rel_path = os.path.relpath(abs_path, repo_root)
    except ValueError:
        sys.exit(0)

    # Run mycelium.sh context
    try:
        result = subprocess.run(
            ["mycelium.sh", "context", rel_path],
            capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
            cwd=repo_root
        )
        output = result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        sys.exit(0)

    if not output or "no notes" in output.lower():
        sys.exit(0)

    # Return notes as additionalContext
    context = f"=== Mycelium Notes for {rel_path} ===\n{output}\n=== End Mycelium ==="
    json.dump({"additionalContext": context}, sys.stdout)


if __name__ == "__main__":
    main()
