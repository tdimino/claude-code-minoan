#!/usr/bin/env python3
"""ccstatusline custom-command widget: display session tags with rainbow-pastel ANSI colors.

Reads session_id from stdin JSON, loads tags from sidecar, outputs up to 3 display_tags
with per-tag ANSI true-color separated by dim |. Requires preserveColors: true in
ccstatusline widget config.
"""
import json
import pathlib
import sys

TAGS_DIR = pathlib.Path.home() / ".claude" / "session-tags"

# Rainbow-pastel palette (one color per tag, cycling)
PASTEL_COLORS = [
    (255, 154, 162),  # Rose
    (255, 183, 148),  # Peach
    (253, 216, 132),  # Gold
    (155, 226, 172),  # Mint
    (162, 210, 255),  # Sky
    (205, 180, 255),  # Lilac
]

RESET = "\033[0m"
DIM = "\033[2m"


def fg(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return

    session_id = data.get("session_id", "")
    if not session_id:
        return

    sidecar = TAGS_DIR / f"{session_id}.json"
    if not sidecar.exists():
        return

    try:
        tags_data = json.loads(sidecar.read_text())
    except (json.JSONDecodeError, OSError):
        return

    display_tags = tags_data.get("display_tags", [])[:3]
    if not display_tags:
        return

    # Build output: tag1 · tag2 · tag3 (each in its own pastel color, grouped with dots)
    parts = []
    for i, tag in enumerate(display_tags):
        color = PASTEL_COLORS[i % len(PASTEL_COLORS)]
        parts.append(f"{fg(*color)}{tag}{RESET}")

    # Middle dot (·) as inter-tag separator, visually grouping them as one unit
    dot_color = fg(120, 120, 140)  # Muted lavender-gray
    sep = f" {dot_color}·{RESET} "
    sys.stdout.write(sep.join(parts))


if __name__ == "__main__":
    main()
