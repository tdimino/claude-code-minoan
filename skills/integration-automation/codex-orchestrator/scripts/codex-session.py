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
import platform
import shlex
from pathlib import Path

# Get the agents directory relative to this script
SCRIPT_DIR = Path(__file__).parent.resolve()
AGENTS_DIR = SCRIPT_DIR.parent / "agents"

READ_ONLY_PROFILES = {"researcher", "adjudicator", "chat"}


def _pty_wrap(cmd: list[str]) -> list[str]:
    """Wrap command with script(1) if no controlling TTY (Codex CLI v0.124.0+ fix)."""
    if sys.stdout.isatty():
        return cmd
    if platform.system() == "Darwin":
        return ["script", "-q", "/dev/null"] + cmd
    else:
        return ["script", "-qfc", " ".join(shlex.quote(c) for c in cmd), "/dev/null"]


PROFILES = {
    "reviewer": "Code review specialist - quality, bugs, performance",
    "debugger": "Bug hunting specialist - root cause analysis, fixes",
    "architect": "System design specialist - architecture, patterns",
    "security": "Security audit specialist - vulnerabilities, OWASP",
    "refactor": "Code refactoring specialist - cleanup, modernization",
    "docs": "Documentation specialist - comments, READMEs, guides",
    "planner": "ExecPlan design document specialist",
    "syseng": "Infrastructure/DevOps/CI-CD specialist",
    "builder": "Greenfield implementation specialist",
    "researcher": "Read-only Q&A and analysis (no file changes)",
    "adjudicator": "Read-only comparative evidence weighing and hypothesis adjudication",
    "chat": "Open-ended conversation (read-only, ephemeral)",
    "goal": "Goal specification writer for autonomous /goal runs",
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
    developer_instructions = agents_path.read_text()

    print(f"Starting Codex with profile: {profile}")
    print(f"Working directory: {work_dir}")

    # developer_instructions is process-local. Codex still discovers the
    # project's untouched root-to-cwd AGENTS.md chain for this run.
    profile_args = ["-c", f"developer_instructions={developer_instructions}"]
    if interactive:
        cmd = ["codex", "--model", "gpt-5.6-sol", *profile_args]
        if profile in READ_ONLY_PROFILES:
            cmd.extend(["--sandbox", "read-only"])
        if prompt:
            cmd.append(prompt)
    elif profile in READ_ONLY_PROFILES:
        cmd = [
            "codex", "exec",
            "--skip-git-repo-check",
            "--model", "gpt-5.6-sol",
            "--sandbox", "read-only",
            "--ephemeral",
            *profile_args,
            prompt,
        ]
    else:
        cmd = [
            "codex", "exec",
            "--skip-git-repo-check",
            "--model", "gpt-5.6-sol",
            "--sandbox", "workspace-write",
            *profile_args,
            prompt,
        ]

    stdin_arg = None if interactive else subprocess.DEVNULL
    run_cmd = cmd if interactive else _pty_wrap(cmd)
    result = subprocess.run(run_cmd, text=True, stdin=stdin_arg)
    return result.returncode


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
