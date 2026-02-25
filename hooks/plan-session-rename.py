#!/usr/bin/env python3
"""PostToolUse hook: auto-rename session when a plan file is written.

Matcher: Write
When the written file is in ~/.claude/plans/, extracts the H1 header and appends
a {"type": "custom-title"} event to the session JSONL—the same authoritative
mechanism that /rename uses. Idempotent via 4KB tail-scan. ~5ms.

Also emits additionalContext via hookSpecificOutput so Claude Code knows the
plan file's canonical (dated) name. Only fires on first write per slug (re-fires
if the H1 title changes).
"""
import datetime
import json
import os
import pathlib
import re
import sys

PLANS_DIR = pathlib.Path.home() / ".claude" / "plans"
PENDING_DIR = pathlib.Path.home() / ".claude" / "session-tags"
CONTEXT_CACHE = PLANS_DIR / ".plan-context-cache.json"

# H1 header — accept any non-empty content after "# "
H1_RE = re.compile(r"^#\s+(.+)", re.MULTILINE)

# Claude Code's random naming: adjective-gerund-noun
RANDOM_NAME_RE = re.compile(
    r"^([a-z]+-[a-z]+-[a-z]+)"
    r"(-agent-a[0-9a-f]{5,19})?"
    r"\.md$"
)


def slugify(text, max_len=60):
    """Convert H1 header text to kebab-case slug (mirrors plan-rename.py)."""
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


def load_context_cache():
    """Load the context notification cache."""
    if CONTEXT_CACHE.exists():
        try:
            return json.loads(CONTEXT_CACHE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_context_cache(cache):
    """Atomically write the context notification cache."""
    try:
        tmp = CONTEXT_CACHE.with_suffix(".tmp")
        tmp.write_text(json.dumps(cache, indent=2))
        tmp.rename(CONTEXT_CACHE)
    except OSError:
        pass


def compute_dated_path(title, filepath):
    """Compute the future dated slug path for a random-named plan file."""
    basename = pathlib.Path(filepath).name
    m = RANDOM_NAME_RE.match(basename)
    if not m:
        return None

    slug = slugify(title)
    if not slug:
        return None

    agent_suffix = m.group(2) or ""
    today = datetime.date.today().isoformat()
    new_name = f"{today}-{slug}{agent_suffix}.md"
    return str(PLANS_DIR / new_name)


def apply_pending_titles(session_id, cwd):
    """Consume any .pending-title breadcrumbs from earlier writes."""
    pending = PENDING_DIR / f"{session_id}.pending-title"
    if not pending.exists():
        return
    try:
        title = pending.read_text().strip()
    except (OSError, UnicodeDecodeError):
        return
    if not title:
        pending.unlink(missing_ok=True)
        return

    jsonl = jsonl_path_for(session_id, cwd)
    if not jsonl.exists():
        return  # Still not ready

    if has_custom_title(jsonl):
        pending.unlink(missing_ok=True)
        return

    event = json.dumps({"type": "custom-title", "customTitle": title, "sessionId": session_id})
    try:
        with open(jsonl, "a") as f:
            f.write(event + "\n")
        print(f"plan-session-rename: applied pending '{title}' for {session_id[:8]}", file=sys.stderr)
    except OSError:
        pass
    pending.unlink(missing_ok=True)


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
        pathlib.Path(os.path.abspath(filepath)).relative_to(str(PLANS_DIR))
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

    # Write current title first (before consuming pending) so H1 changes take priority
    if not has_custom_title(jsonl):
        event = json.dumps({"type": "custom-title", "customTitle": title, "sessionId": session_id})
        try:
            with open(jsonl, "a") as f:
                f.write(event + "\n")
            print(f"plan-session-rename: '{title}' for {session_id[:8]}", file=sys.stderr)
        except OSError:
            pass

    # Consume any stale pending title breadcrumbs (harmless now — current title already written)
    apply_pending_titles(session_id, cwd)

    # Emit additionalContext for random-named plan files so Claude knows the
    # canonical path. Only fires on first write per slug (re-fires if H1 changes).
    dated_path = compute_dated_path(title, filepath)
    if not dated_path:
        return

    cache = load_context_cache()
    basename = pathlib.Path(filepath).name
    if cache.get(basename) == dated_path:
        return  # Already notified for this slug

    cache[basename] = dated_path
    save_context_cache(cache)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": dated_path,
        }
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
