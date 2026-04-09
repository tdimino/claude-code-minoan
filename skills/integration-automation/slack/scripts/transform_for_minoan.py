#!/usr/bin/env python3
"""
Transform Slack skill files for the Minoan (personal) distribution repo.

Performs URL replacement and content scoping:
1. aldea-ai/Claude-Code-Aldea → tdimino/claude-code-minoan (all .md and .py files)
2. Remove "Open Souls paradigm" link from App Home footer
3. "Aldea workspace" → "your workspace" in soul.md

Usage:
    python3 transform_for_minoan.py /path/to/minoan/skills/integration-automation
"""

import os
import re
import sys


def transform_file(path: str, replacements: list[tuple[str, str]]) -> int:
    """Apply replacements to a single file. Returns count of changes."""
    with open(path, "r") as f:
        original = f.read()

    content = original
    for old, new in replacements:
        content = content.replace(old, new)

    if content != original:
        with open(path, "w") as f:
            f.write(content)
        return sum(original.count(old) for old, _ in replacements)
    return 0


def scope_app_home(path: str) -> bool:
    """Remove Open Souls paradigm link from App Home footer."""
    with open(path, "r") as f:
        content = f.read()

    # Remove the " · <link|Open Souls paradigm>" portion from footer
    scoped = re.sub(
        r'\s*" \\u00b7 <https://github\.com/[^|]+\|Open Souls paradigm>"',
        '',
        content
    )

    if scoped != content:
        with open(path, "w") as f:
            f.write(scoped)
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print("Usage: transform_for_minoan.py MINOAN_BASE", file=sys.stderr)
        sys.exit(1)

    base = sys.argv[1]
    if not os.path.isdir(base):
        print(f"Error: {base} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Global URL replacements
    replacements = [
        ("github.com/aldea-ai/Claude-Code-Aldea", "github.com/tdimino/claude-code-minoan"),
        ("Claude-Code-Aldea", "claude-code-minoan"),
    ]

    # Walk all .md and .py files
    total_files = 0
    total_changes = 0

    for root, _, files in os.walk(base):
        for fname in files:
            if not fname.endswith((".md", ".py")):
                continue
            fpath = os.path.join(root, fname)
            changes = transform_file(fpath, replacements)
            if changes:
                rel = os.path.relpath(fpath, base)
                print(f"  {rel}: {changes} replacement(s)")
                total_files += 1
                total_changes += changes

    # Content scoping: soul.md
    soul_path = os.path.join(base, "slack", "daemon", "soul.md")
    if os.path.exists(soul_path):
        with open(soul_path, "r") as f:
            content = f.read()
        scoped = content.replace("the Aldea workspace", "your workspace")
        if scoped != content:
            with open(soul_path, "w") as f:
                f.write(scoped)
            print(f"  slack/daemon/soul.md: scoped 'Aldea workspace' → 'your workspace'")
            total_files += 1

    # Content scoping: App Home footer
    app_home_path = os.path.join(base, "slack", "scripts", "slack_app_home.py")
    if os.path.exists(app_home_path):
        if scope_app_home(app_home_path):
            print(f"  slack/scripts/slack_app_home.py: removed Open Souls paradigm link")

    print(f"\nTransformed {total_files} files, {total_changes} URL replacements")


if __name__ == "__main__":
    main()
