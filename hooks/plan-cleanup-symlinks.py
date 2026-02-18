#!/usr/bin/env python3
"""SessionEnd hook: clean up forwarding symlinks in ~/.claude/plans/.

After a session ends, no further writes will target old plan file names,
so symlinks left by plan-rename.py are safe to remove.
"""
import pathlib
import sys

PLANS_DIR = pathlib.Path.home() / ".claude" / "plans"


def main():
    # Consume stdin (required by hook protocol)
    try:
        sys.stdin.read()
    except OSError:
        pass

    if not PLANS_DIR.exists():
        return

    count = 0
    for entry in PLANS_DIR.iterdir():
        if entry.is_symlink():
            try:
                entry.unlink()
                count += 1
            except OSError:
                pass

    if count:
        print(f"plan-cleanup: removed {count} symlink(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
