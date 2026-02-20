#!/usr/bin/env python3
"""Hook: rename randomly-named plan files to dated slugs.

Fires on Stop (rename + symlink so Claude Code can still write) and
SessionEnd (final cleanup of symlinks).

Usage in settings.json:
  Stop:       "python3 ~/.claude/hooks/plan-rename.py stop"
  SessionEnd: "python3 ~/.claude/hooks/plan-rename.py session_end"

On first rename, also opens the plan in dabarat for live preview.

Naming convention: YYYY-MM-DD-descriptive-slug.md
Agent variant:     YYYY-MM-DD-descriptive-slug-agent-HASH.md
"""
import datetime
import fcntl
import json
import os
import pathlib
import re
import subprocess
import sys
import time

PLANS_DIR = pathlib.Path.home() / ".claude" / "plans"

# Claude Code's random naming: adjective-gerund-noun (all lowercase alpha + hyphens)
# Examples: tingly-humming-simon, eager-twirling-storm, zesty-kindling-giraffe
RANDOM_NAME_RE = re.compile(
    r"^([a-z]+-[a-z]+-[a-z]+)"          # base: adj-gerund-noun
    r"(-agent-a[0-9a-f]{5,7})?"          # optional agent suffix
    r"\.md$"
)

# H1 header extraction — first line starting with "# "
H1_RE = re.compile(r"^#\s+([A-Z].+)", re.MULTILINE)


def slugify(text, max_len=60):
    """Convert H1 header text to kebab-case slug."""
    text = re.sub(r"^Plan:\s*", "", text, flags=re.IGNORECASE)
    text = text.replace("`", "").replace('"', "").replace("'", "")
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text)
    text = text.rstrip(" .:;,!?")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    if len(text) > max_len:
        text = text[:max_len].rsplit("-", 1)[0]
    return text


def extract_h1(filepath):
    """Extract first H1 header from a markdown file. Reads only first 2KB."""
    # Follow symlinks to read the actual content (POSIX symlink resolution)
    real_path = filepath.resolve() if filepath.is_symlink() else filepath
    try:
        with open(real_path, "r") as f:
            head = f.read(2048)
        m = H1_RE.search(head)
        return m.group(1).strip() if m else ""
    except (OSError, UnicodeDecodeError):
        return ""


def rename_file(filepath, base_slug, agent_suffix=""):
    """Rename a random-named file to a dated slug. Creates symlink for Claude Code."""
    h1 = extract_h1(filepath)
    if not h1:
        # For agent files, try the parent plan's H1
        if agent_suffix:
            parent_path = PLANS_DIR / f"{base_slug}.md"
            if parent_path.exists():
                h1 = extract_h1(parent_path)
        if not h1:
            return None  # No header — skip

    today = datetime.date.today().isoformat()
    slug = slugify(h1)
    if not slug:
        return None

    new_name = f"{today}-{slug}{agent_suffix}.md"
    new_path = PLANS_DIR / new_name

    # Avoid no-op
    if new_path.resolve() == filepath.resolve():
        return None

    # Handle collision
    if new_path.exists():
        for i in range(2, 10):
            candidate = PLANS_DIR / f"{today}-{slug}-{i}{agent_suffix}.md"
            if not candidate.exists():
                new_path = candidate
                break
        else:
            return None  # Too many collisions

    try:
        os.rename(filepath, new_path)
        print(f"plan-rename: {filepath.name} -> {new_path.name}", file=sys.stderr)
    except OSError as e:
        print(f"plan-rename: error renaming {filepath.name}: {e}", file=sys.stderr)
        return None

    # Create symlink: random-name.md → dated-name.md
    # Claude Code's Write tool follows symlinks (confirmed: Node.js fs.writeFile),
    # so subsequent plan writes reach the dated file via the symlink.
    # The relative target (new_path.name) resolves against the symlink's directory (PLANS_DIR).
    try:
        os.symlink(new_path.name, filepath)
        print(f"plan-rename: symlink {filepath.name} -> {new_path.name}", file=sys.stderr)
    except OSError:
        pass  # Non-critical — file is already renamed

    return new_path


def _dabarat_running(port=3031):
    """Check if dabarat is listening."""
    import urllib.request
    try:
        urllib.request.urlopen(f"http://127.0.0.1:{port}/api/tabs", timeout=1)
        return True
    except Exception:
        return False


def open_in_dabarat(filepath):
    """Open a plan file in dabarat for live preview (non-blocking).

    If dabarat is running: silently adds as tab via --add (no dialog, appropriate
    for automated Stop hook). If not running: launches new window.
    """
    try:
        if _dabarat_running():
            subprocess.Popen(
                ["dabarat", "--add", str(filepath)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            print(f"plan-rename: added {filepath.name} as dabarat tab", file=sys.stderr)
        else:
            subprocess.Popen(
                ["dabarat", str(filepath)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
            print(f"plan-rename: launched dabarat for {filepath.name}", file=sys.stderr)
    except FileNotFoundError:
        pass  # dabarat not installed


def main():
    # Determine trigger from CLI arg (not from stdin JSON — hook_event_name doesn't exist)
    trigger = sys.argv[1] if len(sys.argv) > 1 else "session_end"

    # Consume stdin (required by hook protocol)
    try:
        data = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        data = {}

    # Guard: don't rename during forced continuation (prevent mid-write interference)
    if data.get("stop_hook_active", False):
        return

    if not PLANS_DIR.exists():
        return

    # 1. Clean up broken symlinks (always safe)
    for entry in PLANS_DIR.iterdir():
        if entry.is_symlink() and not os.path.exists(str(entry)):
            try:
                entry.unlink()
            except OSError:
                pass

    # 2. On session_end only: clean up all forwarding symlinks (session is over)
    if trigger == "session_end":
        symlink_count = 0
        for entry in PLANS_DIR.iterdir():
            if entry.is_symlink():
                try:
                    entry.unlink()
                    symlink_count += 1
                except OSError:
                    pass
        if symlink_count:
            print(f"plan-rename: cleaned {symlink_count} symlink(s)", file=sys.stderr)

    # 3. Acquire lock (short retry to handle Stop/SessionEnd overlap)
    lock_path = pathlib.Path("/tmp/claude-plan-rename-session.lock")
    lock_fd = None
    for _ in range(5):
        try:
            lock_fd = open(lock_path, "w")
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except (OSError, BlockingIOError):
            if lock_fd:
                lock_fd.close()
                lock_fd = None
            time.sleep(0.2)

    if lock_fd is None:
        return  # Truly contended after 1s

    try:
        # 4. Scan for random-named files and rename them
        # Collect first so we don't modify while iterating
        to_rename = []
        for entry in PLANS_DIR.iterdir():
            if entry.is_symlink():
                continue  # Already renamed — symlink points to dated file
            m = RANDOM_NAME_RE.match(entry.name)
            if m and entry.is_file():
                to_rename.append((entry, m.group(1), m.group(2) or ""))

        for filepath, base_slug, agent_suffix in to_rename:
            new_path = rename_file(filepath, base_slug, agent_suffix)
            if new_path:
                open_in_dabarat(new_path)

    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    main()
