#!/usr/bin/env python3
"""One-time batch rename of randomly-named plan files to dated slugs.

Usage:
    python3 batch-rename-plans.py [--dry-run]

Uses file birth time (macOS stat) for date instead of today's date.
Creates symlinks from old names for safety.
"""
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys

PLANS_DIR = pathlib.Path.home() / ".claude" / "plans"

RANDOM_NAME_RE = re.compile(
    r"^([a-z]+-[a-z]+-[a-z]+)"
    r"(-agent-a[0-9a-f]{5,7})?"
    r"\.md$"
)

H1_RE = re.compile(r"^#\s+(.+)", re.MULTILINE)


def slugify(text, max_len=60):
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
    try:
        with open(filepath, "r") as f:
            head = f.read(2048)
        m = H1_RE.search(head)
        return m.group(1).strip() if m else ""
    except (OSError, UnicodeDecodeError):
        return ""


def get_birth_date(filepath):
    """Get file birth date using macOS stat."""
    try:
        result = subprocess.run(
            ["stat", "-f", "%SB", "-t", "%Y-%m-%d", str(filepath)],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            date_str = result.stdout.strip()
            # Validate format
            datetime.date.fromisoformat(date_str)
            return date_str
    except (subprocess.TimeoutExpired, ValueError, OSError):
        pass
    # Fallback: file mtime
    try:
        mtime = os.path.getmtime(filepath)
        return datetime.date.fromtimestamp(mtime).isoformat()
    except (OSError, FileNotFoundError):
        return datetime.date.today().isoformat()


def main():
    dry_run = "--dry-run" in sys.argv

    # Collect all random-named files, grouped by base slug
    groups = {}  # base_slug -> {parent: Path|None, agents: [Path]}
    for entry in sorted(PLANS_DIR.iterdir()):
        if entry.is_symlink() or not entry.is_file():
            continue
        m = RANDOM_NAME_RE.match(entry.name)
        if not m:
            continue
        base_slug = m.group(1)
        agent_suffix = m.group(2) or ""

        if base_slug not in groups:
            groups[base_slug] = {"parent": None, "agents": []}
        if agent_suffix:
            groups[base_slug]["agents"].append(entry)
        else:
            groups[base_slug]["parent"] = entry

    renames = []
    skipped = []

    for base_slug, group in sorted(groups.items()):
        parent = group["parent"]
        agents = group["agents"]

        # Get H1 from parent (or first agent if no parent)
        h1 = ""
        source_file = parent or (agents[0] if agents else None)
        if source_file:
            h1 = extract_h1(source_file)

        if not h1:
            skipped.append((base_slug, "no H1 header found"))
            continue

        slug = slugify(h1)
        if not slug:
            skipped.append((base_slug, "empty slug after processing"))
            continue

        # Get date from parent (or first agent)
        date_prefix = get_birth_date(source_file)

        # Rename parent
        if parent:
            new_name = f"{date_prefix}-{slug}.md"
            new_path = PLANS_DIR / new_name
            if new_path.exists() and new_path != parent:
                for i in range(2, 10):
                    candidate = PLANS_DIR / f"{date_prefix}-{slug}-{i}.md"
                    if not candidate.exists():
                        new_path = candidate
                        new_name = candidate.name
                        break
            renames.append((parent, new_path))

        # Rename agents
        for agent_file in agents:
            am = RANDOM_NAME_RE.match(agent_file.name)
            if am:
                agent_suffix = am.group(2)
                new_agent_name = f"{date_prefix}-{slug}{agent_suffix}.md"
                new_agent_path = PLANS_DIR / new_agent_name
                if new_agent_path.exists():
                    skipped.append((agent_file.name, f"collision: {new_agent_name} already exists"))
                else:
                    renames.append((agent_file, new_agent_path))

    # Report
    print(f"\n{'DRY RUN — ' if dry_run else ''}Plan File Renames")
    print(f"{'=' * 60}")
    print(f"Files to rename: {len(renames)}")
    print(f"Skipped (no H1): {len(skipped)}")

    if skipped:
        print(f"\nSkipped:")
        for slug, reason in skipped:
            print(f"  {slug}.md — {reason}")

    print(f"\nRenames:")
    for old, new in renames:
        print(f"  {old.name}")
        print(f"    -> {new.name}")

    if dry_run:
        print(f"\nDry run complete. Run without --dry-run to execute.")
        return

    # Execute
    print(f"\nExecuting...")
    success = 0
    for old, new in renames:
        try:
            os.rename(old, new)
            os.symlink(new, old)
            success += 1
        except OSError as e:
            print(f"  ERROR: {old.name} -> {new.name}: {e}")

    print(f"Renamed {success}/{len(renames)} files. Symlinks created for session continuity.")
    print(f"Symlinks will be cleaned up by plan-cleanup-symlinks.py on next SessionEnd.")


if __name__ == "__main__":
    main()
