#!/usr/bin/env python3
"""
Manage Codex CLI sessions with agent profiles.

Usage:
  codex-session.py start <profile> "<prompt>"     Start new session with profile
  codex-session.py interactive <profile>          Start interactive session
  codex-session.py list                           List available profiles
  codex-session.py info <profile>                 Show profile details

Examples:
  codex-session.py start reviewer "Review auth.ts"
  codex-session.py interactive debugger
  codex-session.py list
"""

import subprocess
import sys
import os
import shutil
import tempfile
from pathlib import Path

# Get the agents directory relative to this script
SCRIPT_DIR = Path(__file__).parent.resolve()
AGENTS_DIR = SCRIPT_DIR.parent / "agents"

PROFILES = {
    "reviewer": "Code review specialist - quality, bugs, performance",
    "debugger": "Bug hunting specialist - root cause analysis, fixes",
    "architect": "System design specialist - architecture, patterns",
    "security": "Security audit specialist - vulnerabilities, OWASP",
    "refactor": "Code refactoring specialist - cleanup, modernization",
    "docs": "Documentation specialist - comments, READMEs, guides",
}


def get_agents_path(profile: str) -> Path:
    """Get the path to an agent profile's AGENTS.md file."""
    return AGENTS_DIR / f"{profile}.md"


def validate_profile(profile: str) -> bool:
    """Check if a profile exists."""
    return get_agents_path(profile).exists()


def list_profiles():
    """List all available profiles."""
    print("Available Codex Agent Profiles:\n")
    for profile, description in PROFILES.items():
        path = get_agents_path(profile)
        status = "✓" if path.exists() else "✗"
        print(f"  {status} {profile:12} - {description}")
    print("\nUsage: codex-session.py start <profile> \"<prompt>\"")


def show_profile_info(profile: str):
    """Show detailed info about a profile."""
    if not validate_profile(profile):
        print(f"Error: Profile '{profile}' not found")
        sys.exit(1)

    path = get_agents_path(profile)
    print(f"Profile: {profile}")
    print(f"Path: {path}")
    print(f"Description: {PROFILES.get(profile, 'Unknown')}")
    print("\n--- AGENTS.md Content ---\n")
    print(path.read_text())


def start_session(profile: str, prompt: str, interactive: bool = False):
    """Start a Codex session with the specified profile."""
    if not validate_profile(profile):
        print(f"Error: Profile '{profile}' not found")
        print("Available profiles:", ", ".join(PROFILES.keys()))
        sys.exit(1)

    agents_path = get_agents_path(profile)
    work_dir = Path.cwd()

    # Check if AGENTS.md exists and back it up
    existing_agents = work_dir / "AGENTS.md"
    backup_path = None
    if existing_agents.exists():
        backup_path = work_dir / f"AGENTS.md.backup.{os.getpid()}"
        shutil.move(str(existing_agents), str(backup_path))

    # Create symlink to the profile's AGENTS.md
    existing_agents.symlink_to(agents_path)

    try:
        print(f"Starting Codex with profile: {profile}")
        print(f"Working directory: {work_dir}")

        if interactive:
            # Interactive mode - just launch codex with the profile
            cmd = ["codex", "--model", "codex-mini"]
            if prompt:
                cmd.append(prompt)
        else:
            # Non-interactive exec mode
            cmd = [
                "codex", "exec",
                "--model", "codex-mini",
                "--sandbox", "workspace-write",
                prompt
            ]

        # Run from current directory so Codex can access project files
        result = subprocess.run(cmd, text=True)

        return result.returncode

    finally:
        # Cleanup: remove symlink and restore backup
        if existing_agents.is_symlink():
            existing_agents.unlink()
        if backup_path and backup_path.exists():
            shutil.move(str(backup_path), str(existing_agents))


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "list":
        list_profiles()

    elif cmd == "info":
        if len(sys.argv) < 3:
            print("Usage: codex-session.py info <profile>")
            sys.exit(1)
        show_profile_info(sys.argv[2])

    elif cmd == "start":
        if len(sys.argv) < 4:
            print("Usage: codex-session.py start <profile> \"<prompt>\"")
            sys.exit(1)
        profile = sys.argv[2]
        prompt = sys.argv[3]
        sys.exit(start_session(profile, prompt, interactive=False))

    elif cmd == "interactive":
        if len(sys.argv) < 3:
            print("Usage: codex-session.py interactive <profile> [initial_prompt]")
            sys.exit(1)
        profile = sys.argv[2]
        prompt = sys.argv[3] if len(sys.argv) > 3 else ""
        sys.exit(start_session(profile, prompt, interactive=True))

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)


if __name__ == "__main__":
    main()
