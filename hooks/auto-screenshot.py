#!/usr/bin/env python3
"""PostToolUse hook: auto-screenshot after frontend file writes.

Matcher: Write, Edit
Fires after Claude Code writes/edits frontend files (.tsx/.jsx/.css/.html/.svelte/.vue/.scss).
If a portless dev server is running and a Chrome CDP target is available,
takes a screenshot after HMR settles and returns the path as additionalContext.
"""

import json
import os
import subprocess
import sys
import time

FRONTEND_EXTS = {".tsx", ".jsx", ".css", ".html", ".svelte", ".vue", ".scss"}
CDP_SCRIPT = os.path.expanduser("~/.claude/skills/chrome-cdp/scripts/cdp.mjs")
HMR_SETTLE_SECONDS = 1.5
SCREENSHOT_DIR = ".visual-feedback"


def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    tool_name = data.get("tool_name", "")
    if tool_name not in ("Write", "Edit"):
        return

    tool_input = data.get("tool_input", {})
    filepath = tool_input.get("file_path", "")
    if not filepath:
        return

    _, ext = os.path.splitext(filepath)
    if ext.lower() not in FRONTEND_EXTS:
        return

    # Check if portless has any active routes
    try:
        result = subprocess.run(
            ["portless", "list"],
            capture_output=True, text=True, timeout=3,
        )
        if not result.stdout.strip() or "No active" in result.stdout:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return

    # Get first CDP target matching a localhost dev server
    try:
        result = subprocess.run(
            ["node", CDP_SCRIPT, "list"],
            capture_output=True, text=True, timeout=5,
        )
        lines = [
            l for l in result.stdout.strip().split("\n")
            if l.strip() and "localhost" in l
        ]
        if not lines:
            return
        # First column is the target ID
        target = lines[0].split()[0]
    except (FileNotFoundError, subprocess.TimeoutExpired, IndexError):
        return

    # Wait for HMR to settle
    time.sleep(HMR_SETTLE_SECONDS)

    # Take screenshot into project's .visual-feedback/ directory
    cwd = data.get("cwd", os.getcwd())
    screenshot_dir = os.path.join(cwd, SCREENSHOT_DIR)
    os.makedirs(screenshot_dir, exist_ok=True)
    screenshot_path = os.path.join(screenshot_dir, "latest.png")

    try:
        result = subprocess.run(
            ["node", CDP_SCRIPT, "shot", target, screenshot_path],
            capture_output=True, timeout=10,
        )
        if result.returncode != 0:
            return
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return

    if os.path.exists(screenshot_path):
        output = {
            "additionalContext": (
                f"Auto-screenshot after editing {os.path.basename(filepath)}: {screenshot_path}"
            ),
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
