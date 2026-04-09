#!/usr/bin/env python3
"""PostToolUse hook: track cumulative image token budget per session.

Matcher: Read, mcp__computer-use__screenshot, mcp__claude-in-chrome__screenshot
Reads session state written by image-optimize.py (PreToolUse on Read) and
also directly tracks MCP screenshot tool invocations. Warns when cumulative
image load approaches dangerous thresholds.

Thresholds:
  - WARNING:  >= 15 images OR >= 20K tokens
  - CRITICAL: >= 20 images OR >= 40K tokens

The >20 images threshold is critical because the API silently switches
to a 2000x2000px resolution limit, which can brick sessions.

Note: additionalContext is broken for MCP tools (anthropics/claude-code#24788).
MCP screenshot warnings are tracked but only surface on the next Read tool call.
"""

import fcntl
import json
import os
import sys

# --- Constants ---

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".bmp", ".tiff", ".tif", ".heic",
}
CACHE_DIR = os.path.expanduser("~/.claude/.screenshot-cache")
STATE_FILE = os.path.join(CACHE_DIR, "session-state.json")

WARN_IMAGES = 15
CRITICAL_IMAGES = 20
WARN_TOKENS = 20000
CRITICAL_TOKENS = 40000
COOLDOWN_IMAGES = 5  # Only re-warn every N images after first warning

# MCP screenshot tools to track
MCP_SCREENSHOT_TOOLS = {
    "mcp__computer-use__screenshot",
    "mcp__claude-in-chrome__screenshot",
    "mcp__claude-in-chrome__computer",
}

# Estimated tokens for MCP screenshots (API auto-resizes to 1568px max edge)
# Typical display: 1568x~980 after resize = ~2043 tokens
MCP_SCREENSHOT_ESTIMATED_TOKENS = 2000


# --- Helpers ---

def update_state_for_mcp(session_id: str, tokens: int):
    """Increment image count for an MCP screenshot (no PreToolUse to do it)."""
    lock_file = STATE_FILE + ".lock"
    os.makedirs(CACHE_DIR, exist_ok=True)

    try:
        with open(lock_file, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            state = {}
            try:
                with open(STATE_FILE, "r") as f:
                    state = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                pass

            session = state.setdefault(session_id, {
                "image_count": 0, "total_tokens": 0,
            })
            session["image_count"] += 1
            session["total_tokens"] += tokens

            tmp = STATE_FILE + ".tmp"
            with open(tmp, "w") as f:
                json.dump(state, f)
            os.replace(tmp, STATE_FILE)
    except OSError:
        pass


# --- Main ---

def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    tool_name = data.get("tool_name", "")
    session_id = data.get("session_id", "unknown")
    is_mcp_screenshot = tool_name in MCP_SCREENSHOT_TOOLS

    if tool_name == "Read":
        # Existing path: check file extension, skip cache files
        tool_input = data.get("tool_input", {})
        file_path = tool_input.get("file_path", "")
        if not file_path:
            return
        if CACHE_DIR in file_path:
            return
        _, ext = os.path.splitext(file_path)
        if ext.lower() not in IMAGE_EXTENSIONS:
            return
        # State was already written by image-optimize.py (PreToolUse)

    elif is_mcp_screenshot:
        # MCP path: no PreToolUse hook wrote state, so we do it here
        update_state_for_mcp(session_id, MCP_SCREENSHOT_ESTIMATED_TOKENS)

    else:
        return

    # Read current state
    state = {}
    try:
        with open(STATE_FILE, "r") as f:
            state = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return

    session = state.get(session_id)
    if not session:
        return

    count = session.get("image_count", 0)
    tokens = session.get("total_tokens", 0)
    last_warned = session.get("last_warning_at", 0)

    # Determine warning level
    is_critical = count >= CRITICAL_IMAGES or tokens >= CRITICAL_TOKENS
    is_warning = count >= WARN_IMAGES or tokens >= WARN_TOKENS

    if not is_warning:
        return

    # Cooldown: only re-warn every COOLDOWN_IMAGES after first warning
    if last_warned is not None and last_warned > 0 and (count - last_warned) < COOLDOWN_IMAGES:
        return

    # Build warning message
    source = "MCP screenshot" if is_mcp_screenshot else "image"
    if is_critical:
        msg = (
            f"CRITICAL IMAGE BUDGET: {count} images loaded this session "
            f"(~{tokens:,} tokens). Approaching or past the 20-image API "
            f"threshold where resolution gets capped to 2000x2000px. "
            f"Stop taking screenshots or reading images. Use text descriptions "
            f"of what you've already seen. Consider running /compact."
        )
    else:
        msg = (
            f"IMAGE BUDGET WARNING: {count} images ({source}) loaded this session "
            f"(~{tokens:,} tokens). Approaching the 20-image API threshold "
            f"where resolution gets capped to 2000x2000px. "
            f"Avoid reading more images unless essential. "
            f"Use text descriptions of previous screenshots instead of re-reading them."
        )

    # Print warning BEFORE write-back so it survives timeout
    # Note: additionalContext is broken for MCP tools (#24788) —
    # MCP warnings are tracked but only surface on the next Read.
    output = {"additionalContext": msg}
    print(json.dumps(output))

    # Update last warning marker (best-effort)
    session["last_warning_at"] = count
    try:
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f)
        os.replace(tmp, STATE_FILE)
    except OSError:
        pass


if __name__ == "__main__":
    main()
