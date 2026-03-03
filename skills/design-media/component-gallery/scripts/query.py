#!/usr/bin/env python3
"""
Component Gallery query — semantic search across 60 UI components and 95 design systems.

Usage:
    python3 query.py "accordion accessibility patterns"
    python3 query.py "flyout panel" -k 20
    python3 query.py "drawer vs modal" --json
"""

import subprocess
import sys
import os

RLAMA_RETRIEVE = os.path.expanduser("~/.claude/skills/rlama/scripts/rlama_retrieve.py")
RAG_NAME = "component-gallery"


def main():
    args = sys.argv[1:]
    if not args or args[0] in ("-h", "--help"):
        print("Usage: query.py <query> [-k N] [--json] [--rebuild-cache]")
        print()
        print("Semantic search across component.gallery data.")
        print(f"RLAMA collection: {RAG_NAME}")
        print()
        print("Examples:")
        print('  query.py "accordion accessibility patterns"')
        print('  query.py "flyout panel slide from edge"')
        print('  query.py "responsive table patterns" -k 20')
        print('  query.py "shadcn React Tailwind" --json')
        sys.exit(0)

    cmd = ["python3", RLAMA_RETRIEVE, RAG_NAME] + args
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
