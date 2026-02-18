#!/usr/bin/env python3
"""PostToolUse hook: auto-rename randomly-named plan files to dated slugs.

Matcher: Write, Edit — fires on plan file creation and updates.
Fast-path exits (~1ms) when file is not in ~/.claude/plans/ or already dated.

Naming convention: YYYY-MM-DD-descriptive-slug.md
Agent variant:     YYYY-MM-DD-descriptive-slug-agent-HASH.md
"""
import datetime
import fcntl
import json
import os
import pathlib
import re
import sys

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
    # Strip "Plan:" prefix
    text = re.sub(r"^Plan:\s*", "", text, flags=re.IGNORECASE)
    # Strip backticks, quotes
    text = text.replace("`", "").replace('"', "").replace("'", "")
    # Strip parenthetical suffixes
    text = re.sub(r"\s*\([^)]*\)\s*$", "", text)
    # Strip trailing punctuation
    text = text.rstrip(" .:;,!?")
    # Lowercase
    text = text.lower()
    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)
    # Collapse multiple hyphens and strip leading/trailing
    text = re.sub(r"-+", "-", text).strip("-")
    # Truncate at word boundary
    if len(text) > max_len:
        text = text[:max_len].rsplit("-", 1)[0]
    return text


def extract_h1(filepath):
    """Extract first H1 header from a markdown file. Reads only first 2KB."""
    try:
        with open(filepath, "r") as f:
            head = f.read(2048)
        m = H1_RE.search(head)
        return m.group(1).strip() if m else ""
    except (OSError, UnicodeDecodeError):
        return ""


def rename_agent_files(base_slug, date_prefix, topic_slug):
    """Rename all agent files sharing the same base slug.

    Called while parent lock is held, so no separate lock needed.
    Re-checks existence before rename to guard against TOCTOU races.
    """
    agent_re = re.compile(
        re.escape(base_slug) + r"(-agent-a[0-9a-f]{5,7})\.md$"
    )
    for entry in PLANS_DIR.iterdir():
        if entry.is_symlink():
            continue
        m = agent_re.match(entry.name)
        if m:
            agent_suffix = m.group(1)
            new_agent_name = f"{date_prefix}-{topic_slug}{agent_suffix}.md"
            new_agent_path = PLANS_DIR / new_agent_name
            if not new_agent_path.exists() and entry.exists() and not entry.is_symlink():
                try:
                    os.rename(entry, new_agent_path)
                    os.symlink(new_agent_path.name, entry)
                    print(f"plan-rename: {entry.name} -> {new_agent_name}", file=sys.stderr)
                except OSError:
                    pass


def main():
    # 1. Parse hook input
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    # 2. Fast path: extract file_path
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return

    filepath = pathlib.Path(file_path).resolve()

    # 3. Fast path: is this in ~/.claude/plans/?
    try:
        filepath.relative_to(PLANS_DIR.resolve())
    except ValueError:
        return

    # 4. Fast path: is the filename randomly named?
    filename = filepath.name
    m = RANDOM_NAME_RE.match(filename)
    if not m:
        return  # Already dated or doesn't match pattern

    base_slug = m.group(1)            # e.g., "tingly-humming-simon"
    agent_suffix = m.group(2) or ""   # e.g., "-agent-a86a410" or ""

    # 5. File must exist and not be a symlink (already renamed)
    if not filepath.exists() or filepath.is_symlink():
        return

    # 6. Extract H1 header
    h1 = extract_h1(filepath)
    if not h1:
        # For agent files, try the parent plan's H1
        if agent_suffix:
            parent_path = PLANS_DIR / f"{base_slug}.md"
            if parent_path.exists() and not parent_path.is_symlink():
                h1 = extract_h1(parent_path)
            elif parent_path.is_symlink():
                h1 = extract_h1(parent_path.resolve())
        if not h1:
            return  # No header yet — wait for next edit

    # 7. Generate the new filename
    today = datetime.date.today().isoformat()
    slug = slugify(h1)
    if not slug:
        return

    new_name = f"{today}-{slug}{agent_suffix}.md"
    new_path = PLANS_DIR / new_name

    # 8. Avoid no-op
    if new_path.resolve() == filepath.resolve():
        return

    # 9. Handle collision
    if new_path.exists():
        for i in range(2, 10):
            candidate = PLANS_DIR / f"{today}-{slug}-{i}{agent_suffix}.md"
            if not candidate.exists():
                new_path = candidate
                break
        else:
            return  # Too many collisions, bail

    # 10. Acquire lock (non-blocking)
    lock_path = pathlib.Path(f"/tmp/claude-plan-rename-{base_slug}.lock")
    try:
        lock_fd = open(lock_path, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        return

    try:
        # 11. Double-check (race guard)
        if not filepath.exists() or filepath.is_symlink():
            return

        # 12. Atomic rename
        os.rename(filepath, new_path)

        # 13. Create symlink: old name -> new name (forwarding pointer)
        os.symlink(new_path.name, filepath)

        # 14. Cascade: rename agent files sharing this base slug
        if not agent_suffix:
            rename_agent_files(base_slug, today, slug)

        print(f"plan-rename: {filename} -> {new_path.name}", file=sys.stderr)

    except OSError as e:
        print(f"plan-rename: error: {e}", file=sys.stderr)
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
            lock_path.unlink(missing_ok=True)
        except OSError:
            pass


if __name__ == "__main__":
    main()
