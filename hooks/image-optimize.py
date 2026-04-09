#!/usr/bin/env python3
"""PreToolUse hook: optimize images before Read injects them into context.

Matcher: Read
Detects image files, resizes to 1568px max edge (API's auto-resize target),
converts PNG->JPEG for size reduction, and injects token estimates as
additionalContext. Optimized copies go to ~/.claude/.screenshot-cache/.

Token formula: (width * height) / 750
API auto-resize: 1568px long edge
API limits: 8000x8000 max (2000x2000 if >20 images in request)
"""

import fcntl
import hashlib
import json
import os
import re
import subprocess
import sys

# --- Constants ---

IMAGE_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".bmp", ".tiff", ".tif", ".heic",
}
MAX_LONG_EDGE = 1568
MAX_FILE_SIZE = 3 * 1024 * 1024       # 3MB — resize threshold
PNG_CONVERT_THRESHOLD = 500 * 1024     # 500KB — convert PNG->JPEG if larger
MIN_EDGE = 200                         # Below this, quality degrades
JPEG_QUALITY = 80
CACHE_DIR = os.path.expanduser("~/.claude/.screenshot-cache")
SIPS = "/usr/bin/sips"
TOKEN_DIVISOR = 750


# --- Helpers ---

def is_image(path: str) -> bool:
    _, ext = os.path.splitext(path)
    return ext.lower() in IMAGE_EXTENSIONS


def get_dimensions(path: str) -> tuple[int, int] | None:
    """Get image dimensions via sips (macOS native, ~50ms)."""
    try:
        result = subprocess.run(
            [SIPS, "-g", "pixelWidth", "-g", "pixelHeight", path],
            capture_output=True, text=True, timeout=3,
        )
        if result.returncode != 0:
            return None
        w = h = 0
        for line in result.stdout.splitlines():
            line = line.strip()
            if "pixelWidth" in line:
                m = re.search(r"(\d+)", line.split(":")[-1])
                if m:
                    w = int(m.group(1))
            elif "pixelHeight" in line:
                m = re.search(r"(\d+)", line.split(":")[-1])
                if m:
                    h = int(m.group(1))
        return (w, h) if w > 0 and h > 0 else None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None


def calc_tokens(w: int, h: int) -> int:
    return (w * h) // TOKEN_DIVISOR


def optimize(path: str, w: int, h: int) -> tuple[str, int, int] | None:
    """Optimize image via sips. Returns (output_path, new_w, new_h) or None."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    # Cache key includes mtime so changed files at the same path don't get stale results
    mtime = int(os.path.getmtime(path))
    cache_key = hashlib.md5(f"{path}:{mtime}".encode()).hexdigest()[:12]
    output = os.path.join(CACHE_DIR, f"opt-{cache_key}.jpg")

    # If cache hit, derive dimensions from math and return
    if os.path.exists(output) and os.path.getsize(output) > 0:
        long_edge = max(w, h)
        if long_edge > MAX_LONG_EDGE:
            scale = MAX_LONG_EDGE / long_edge
            new_w, new_h = round(w * scale), round(h * scale)
        else:
            new_w, new_h = w, h
        return (output, new_w, new_h)

    long_edge = max(w, h)
    needs_resize = long_edge > MAX_LONG_EDGE

    try:
        if needs_resize:
            result = subprocess.run(
                [SIPS, "-Z", str(MAX_LONG_EDGE),
                 "-s", "format", "jpeg",
                 "-s", "formatOptions", str(JPEG_QUALITY),
                 path, "--out", output],
                capture_output=True, timeout=5,
            )
        else:
            # Format conversion only (PNG->JPEG)
            result = subprocess.run(
                [SIPS, "-s", "format", "jpeg",
                 "-s", "formatOptions", str(JPEG_QUALITY),
                 path, "--out", output],
                capture_output=True, timeout=5,
            )
        if result.returncode != 0:
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None

    if not os.path.exists(output) or os.path.getsize(output) == 0:
        return None

    # Derive new dimensions from math — avoids a second sips call and saves ~3s
    if needs_resize:
        scale = MAX_LONG_EDGE / long_edge
        new_w, new_h = round(w * scale), round(h * scale)
    else:
        new_w, new_h = w, h

    return (output, new_w, new_h)


def update_session_state(path: str, tokens: int, session_id: str):
    """Track image reads for budget hook. Uses fcntl.flock for concurrency safety."""
    state_file = os.path.join(CACHE_DIR, "session-state.json")
    lock_file = state_file + ".lock"
    os.makedirs(CACHE_DIR, exist_ok=True)

    try:
        with open(lock_file, "w") as lf:
            fcntl.flock(lf, fcntl.LOCK_EX)
            state = {}
            try:
                with open(state_file, "r") as f:
                    state = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                pass

            session = state.setdefault(session_id, {
                "image_count": 0, "total_tokens": 0,
            })
            session["image_count"] += 1
            session["total_tokens"] += tokens

            tmp = state_file + ".tmp"
            with open(tmp, "w") as f:
                json.dump(state, f)
            os.replace(tmp, state_file)
            # flock released on context exit
    except OSError:
        pass


# --- Main ---

def main():
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    if data.get("tool_name") != "Read":
        return

    tool_input = data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path or not is_image(file_path):
        return

    # Skip files already in the cache
    if CACHE_DIR in file_path:
        return

    # Skip if file doesn't exist (let Read report the error)
    if not os.path.isfile(file_path):
        return

    dims = get_dimensions(file_path)
    if not dims:
        return  # Not a valid image (corrupt, wrong extension, etc.)

    w, h = dims
    file_size = os.path.getsize(file_path)
    basename = os.path.basename(file_path)
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    orig_tokens = calc_tokens(w, h)
    long_edge = max(w, h)
    session_id = data.get("session_id", "unknown")

    # Decision: should we optimize?
    should_resize = long_edge > MAX_LONG_EDGE
    should_convert = (ext == ".png" and file_size > PNG_CONVERT_THRESHOLD)
    too_small = min(w, h) < MIN_EDGE
    too_large_file = file_size > MAX_FILE_SIZE

    if too_small and not should_resize:
        # Image is tiny — just report tokens, don't resize
        update_session_state(file_path, orig_tokens, session_id)
        output = {
            "additionalContext": f"[{basename}: {w}x{h}, ~{orig_tokens} tokens — small image, no optimization]"
        }
        print(json.dumps(output))
        return

    if should_resize or should_convert or too_large_file:
        result = optimize(file_path, w, h)
        if result:
            opt_path, new_w, new_h = result
            new_tokens = calc_tokens(new_w, new_h)
            saved_pct = round((1 - new_tokens / orig_tokens) * 100) if orig_tokens > 0 else 0
            opt_size = os.path.getsize(opt_path)

            update_session_state(file_path, new_tokens, session_id)

            reasons = []
            if should_resize:
                reasons.append(f"resized {w}x{h} -> {new_w}x{new_h}")
            if ext == ".png":
                reasons.append("PNG -> JPEG")
            if too_large_file and not should_resize:
                reasons.append(f"{file_size // 1024}KB -> {opt_size // 1024}KB")

            context = (
                f"[{basename}: optimized ({', '.join(reasons)}), "
                f"~{new_tokens} tokens (was ~{orig_tokens}), saved {saved_pct}%]\n"
                f"Optimized copy: {opt_path}\n"
                f"Read the optimized file instead to save tokens."
            )
            output = {"additionalContext": context}
            print(json.dumps(output))
            return

    # No optimization needed — just report token count
    update_session_state(file_path, orig_tokens, session_id)
    output = {
        "additionalContext": f"[{basename}: {w}x{h}, ~{orig_tokens} tokens]"
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
