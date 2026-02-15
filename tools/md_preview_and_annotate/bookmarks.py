"""Global Claude Code bookmarks — saves markdown snippets to ~/.claude/bookmarks/."""

import datetime
import os
import re

BOOKMARKS_DIR = os.path.expanduser("~/.claude/bookmarks")
SNIPPETS_DIR = os.path.join(BOOKMARKS_DIR, "snippets")
INDEX_PATH = os.path.join(BOOKMARKS_DIR, "INDEX.md")


def _ensure_dirs():
    os.makedirs(SNIPPETS_DIR, exist_ok=True)


def _slugify(text, max_len=40):
    slug = re.sub(r"[^\w\s-]", "", text.lower().strip())
    slug = re.sub(r"[\s_-]+", "-", slug)
    return slug[:max_len].rstrip("-")


def save(*, anchor_text, body, author, source_file, ann_id, heading=""):
    """Save a bookmark snippet and update the global index.

    Returns the path to the created snippet file.
    """
    _ensure_dirs()

    now = datetime.datetime.now(datetime.timezone.utc)
    date_str = now.strftime("%Y-%m-%d")
    time_str = now.strftime("%H:%M UTC")
    slug = _slugify(anchor_text[:60]) or ann_id
    filename = f"{date_str}-{slug}.md"
    snippet_path = os.path.join(SNIPPETS_DIR, filename)

    # Deduplicate filename if needed
    counter = 1
    while os.path.exists(snippet_path):
        filename = f"{date_str}-{slug}-{counter}.md"
        snippet_path = os.path.join(SNIPPETS_DIR, filename)
        counter += 1

    # Write snippet file
    source_basename = os.path.basename(source_file)
    heading_line = f"**Section:** {heading}\n" if heading else ""
    snippet_content = f"""# Bookmark: {anchor_text[:80]}

**Source:** `{source_file}`
**Author:** {author}
**Date:** {date_str} {time_str}
{heading_line}
## Snippet

> {anchor_text}

## Note

{body}
"""
    with open(snippet_path, "w") as f:
        f.write(snippet_content)

    # Update INDEX.md
    _update_index(
        filename=filename,
        anchor_text=anchor_text,
        body=body,
        author=author,
        source_basename=source_basename,
        source_file=source_file,
        date_str=date_str,
        time_str=time_str,
    )

    return snippet_path


def _update_index(*, filename, anchor_text, body, author, source_basename,
                  source_file, date_str, time_str):
    """Prepend a new entry to INDEX.md (most recent first)."""
    header = "# Bookmarked Snippets\n\n"

    snippet_preview = anchor_text[:80]
    if len(anchor_text) > 80:
        snippet_preview += "..."
    note_preview = body[:60] if body else ""
    if len(body) > 60:
        note_preview += "..."

    entry = (
        f"### [{date_str}] {snippet_preview}\n"
        f"- **Source:** `{source_basename}` — `{source_file}`\n"
        f"- **Note:** {note_preview}\n"
        f"- **Author:** {author} | {time_str}\n"
        f"- **File:** [`{filename}`](snippets/{filename})\n\n"
        f"---\n\n"
    )

    existing = ""
    if os.path.exists(INDEX_PATH):
        with open(INDEX_PATH) as f:
            existing = f.read()

    # Strip existing header if present
    if existing.startswith(header):
        existing = existing[len(header):]

    with open(INDEX_PATH, "w") as f:
        f.write(header + entry + existing)
