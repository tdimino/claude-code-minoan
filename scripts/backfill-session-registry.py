#!/usr/bin/env python3
"""One-time migration: backfill session-registry.json from existing sidecar files."""
import json
import pathlib

TAGS_DIR = pathlib.Path.home() / ".claude" / "session-tags"
REGISTRY = pathlib.Path.home() / ".claude" / "session-registry.json"
SKIP_FILES = {"smoke.json", "test.json", "test-prompt-v2.json"}


def main():
    registry = {"sessions": {}}
    if REGISTRY.exists():
        try:
            registry = json.loads(REGISTRY.read_text())
        except (json.JSONDecodeError, OSError):
            registry = {"sessions": {}}

    count = 0
    for sidecar in TAGS_DIR.glob("*.json"):
        if sidecar.name in SKIP_FILES:
            continue
        try:
            data = json.loads(sidecar.read_text())
        except (json.JSONDecodeError, OSError):
            continue

        sid = data.get("session_id", sidecar.stem)
        registry["sessions"][sid] = {
            "title": data.get("title", ""),
            "display_tags": data.get("display_tags", []),
            "tags": data.get("tags", []),
            "summary": data.get("summary", ""),
            "updated": data.get("updated", ""),
        }
        count += 1

    tmp = REGISTRY.with_suffix(".tmp")
    tmp.write_text(json.dumps(registry, indent=2))
    tmp.rename(REGISTRY)
    print(f"Backfilled {count} sessions into {REGISTRY}")


if __name__ == "__main__":
    main()
