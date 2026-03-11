#!/usr/bin/env python3
"""PostToolUse hook: emit context when a plan file is written.

Matcher: Write
When the written file is in ~/.claude/plans/, extracts the H1 header and emits
additionalContext via hookSpecificOutput so Claude Code knows the plan file's
canonical (dated) name. Only fires on first write per slug (re-fires if the
H1 title changes).

NOTE: This hook previously also auto-renamed the session to match the plan H1
by injecting {"type": "custom-title"} events into the session JSONL. That
behavior was removed — session names should only change via explicit /rename.
Plan file renaming (random-name → dated-slug) is handled by plan-rename.py.
"""
import datetime
import json
import os
import pathlib
import re
import sys

PLANS_DIR = pathlib.Path.home() / ".claude" / "plans"
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

    dated_name = pathlib.Path(dated_path).name

    output = {
        "systemMessage": f"plan-session-rename: {basename} -> {dated_name}",
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
