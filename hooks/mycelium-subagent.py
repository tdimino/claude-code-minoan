#!/usr/bin/env python3
"""SubagentStart hook: inject mycelium file context for subdaimones.

Follows soul-subagent-inject.py pattern. When a subdaimon is spawned,
extracts file paths from its task description and surfaces any mycelium
notes on those files as additionalContext, plus the spore protocol
instruction.
"""

import json
import os
import re
import shutil
import subprocess
import sys


def extract_file_paths(text: str) -> list[str]:
    """Extract plausible file paths from task description text."""
    patterns = [
        r'(?:^|\s)([a-zA-Z0-9_./-]+\.[a-zA-Z]{1,6})(?:\s|$|[,;:\)])',
        r'`([a-zA-Z0-9_./-]+\.[a-zA-Z]{1,6})`',
    ]
    paths = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            path = match.group(1)
            if not path.startswith(("http", "www.", "//")):
                paths.add(path)
    return list(paths)[:5]  # cap at 5 files


def main():
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Check mycelium.sh is installed
    if not shutil.which("mycelium.sh"):
        sys.exit(0)

    # Check we're in a git repo
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=2
        )
        repo_root = result.stdout.strip()
        if not repo_root:
            sys.exit(0)
    except (subprocess.SubprocessError, OSError):
        sys.exit(0)

    # Check mycelium is activated
    try:
        result = subprocess.run(
            ["git", "notes", "--ref=mycelium", "list"],
            capture_output=True, timeout=2, cwd=repo_root
        )
        if result.returncode != 0:
            sys.exit(0)
    except (subprocess.SubprocessError, OSError):
        sys.exit(0)

    # Extract task description from the event
    prompt = event.get("prompt", "")
    agent_name = event.get("agent_name", event.get("subagent_type", "agent"))

    # Find file paths in the prompt
    file_paths = extract_file_paths(prompt)

    # Collect mycelium context for referenced files
    notes_output = []
    for fp in file_paths:
        try:
            result = subprocess.run(
                ["mycelium.sh", "context", fp],
                capture_output=True, text=True, timeout=2,
                cwd=repo_root
            )
            if result.stdout.strip() and "no notes" not in result.stdout.lower():
                notes_output.append(result.stdout.strip())
        except (subprocess.SubprocessError, OSError):
            continue

    # Also get project-level constraints
    try:
        result = subprocess.run(
            ["mycelium.sh", "find", "constraint"],
            capture_output=True, text=True, timeout=2,
            cwd=repo_root
        )
        constraints = result.stdout.strip()
    except (subprocess.SubprocessError, OSError):
        constraints = ""

    # Build context
    parts = []

    if constraints:
        parts.append(f"=== Project Constraints ===\n{constraints}")

    if notes_output:
        parts.append("=== File Notes ===\n" + "\n---\n".join(notes_output))

    # Add spore protocol
    parts.append(
        "=== Mycelium Spore Protocol ===\n"
        "Before working on any file, check for notes: mycelium.sh context <file>\n"
        f"After meaningful work, leave a spore: mycelium.sh note <file> -k <kind> --slot {agent_name} -m \"<insight>\"\n"
        "Kinds: decision, warning, constraint, context, summary, observation"
    )

    if parts:
        context = "\n\n".join(parts)
        output = {
            "hookSpecificOutput": {
                "hookEventName": "SubagentStart",
                "additionalContext": context,
            }
        }
        print(json.dumps(output))


if __name__ == "__main__":
    main()
