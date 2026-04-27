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
import signal
import shutil
from pathlib import Path

# Get the agents directory relative to this script
SCRIPT_DIR = Path(__file__).parent.resolve()
AGENTS_DIR = SCRIPT_DIR.parent / "agents"

BACKUP_NAME = ".AGENTS.md.codex-orchestrator-backup"


def is_our_injection(path: Path) -> bool:
    """Check if an AGENTS.md is one we injected (symlink into our agents dir)."""
    if path.is_symlink():
        target = str(path.resolve())
        if "/codex-orchestrator/agents/" in target:
            return True
    return False


def _signal_handler(signum, frame):
    """Re-raise as SystemExit so the finally block executes."""
    sys.exit(128 + signum)


signal.signal(signal.SIGTERM, _signal_handler)
signal.signal(signal.SIGHUP, _signal_handler)

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
    existing_agents = work_dir / "AGENTS.md"
    backup_path = work_dir / BACKUP_NAME
    had_existing_agents = False

    # Phase 0: Migrate old PID-based backups
    for old_backup in work_dir.glob("AGENTS.md.backup.*"):
        print(f"Warning: Found stale backup from previous run: {old_backup}")
        if not existing_agents.exists() and not existing_agents.is_symlink():
            if not old_backup.is_symlink():
                print(f"Restoring AGENTS.md from stale backup: {old_backup}")
                shutil.move(str(old_backup), str(existing_agents))
            else:
                print(f"Removing stale symlink backup: {old_backup}")
                old_backup.unlink()
        else:
            old_backup.unlink()

    # Phase 1: Startup crash recovery
    if backup_path.exists() or backup_path.is_symlink():
        print("Warning: Found backup from a previous crashed run.")
        if existing_agents.exists() or existing_agents.is_symlink():
            if is_our_injection(existing_agents):
                print("Current AGENTS.md is a stale injection. Restoring original from backup.")
                existing_agents.unlink()
                shutil.move(str(backup_path), str(existing_agents))
            else:
                print("Current AGENTS.md appears to be user content. Removing orphaned backup.")
                backup_path.unlink()
        else:
            print("Restoring AGENTS.md from backup after previous crash.")
            shutil.move(str(backup_path), str(existing_agents))

    # Phase 2: Concurrent-run guard
    if backup_path.exists() or backup_path.is_symlink():
        print("Error: Backup still exists after recovery. Another instance may be running.")
        print(f"If not, manually remove: {backup_path}")
        sys.exit(1)

    # Phase 3: Verify working directory is writable
    test_file = work_dir / ".codex-orchestrator-write-test"
    try:
        test_file.touch()
        test_file.unlink()
    except OSError:
        print(f"Error: Working directory is not writable: {work_dir}")
        sys.exit(1)

    # Phase 4: Backup existing AGENTS.md
    if existing_agents.exists() or existing_agents.is_symlink():
        had_existing_agents = True
        if existing_agents.is_symlink():
            backup_path.symlink_to(os.readlink(existing_agents))
        else:
            shutil.copy2(str(existing_agents), str(backup_path))

    # Phase 5: Create profile AGENTS.md
    if existing_agents.exists() or existing_agents.is_symlink():
        existing_agents.unlink()
    existing_agents.symlink_to(agents_path)

    try:
        print(f"Starting Codex with profile: {profile}")
        print(f"Working directory: {work_dir}")

        if interactive:
            # Interactive mode - just launch codex with the profile
            cmd = ["codex", "--model", "gpt-5.5"]
            if prompt:
                cmd.append(prompt)
        else:
            # Non-interactive exec mode
            # Researcher: read-only sandbox, ephemeral, no --full-auto
            if profile == "researcher":
                cmd = [
                    "codex", "exec",
                    "--skip-git-repo-check",
                    "--model", "gpt-5.5",
                    "--sandbox", "read-only",
                    "--ephemeral",
                    prompt
                ]
            else:
                # All write-capable profiles: --full-auto enables unattended writes.
                # Without it, codex exec cannot approve writes (no TUI) and writes
                # fail silently.
                cmd = [
                    "codex", "exec",
                    "--skip-git-repo-check",
                    "--model", "gpt-5.5",
                    "--sandbox", "workspace-write",
                    "--full-auto",
                    prompt
                ]

        # Run from current directory so Codex can access project files
        result = subprocess.run(cmd, text=True)

        return result.returncode

    finally:
        # Remove our injected AGENTS.md
        if existing_agents.is_symlink() or existing_agents.exists():
            existing_agents.unlink()
        # Restore backup
        if had_existing_agents and (backup_path.exists() or backup_path.is_symlink()):
            shutil.move(str(backup_path), str(existing_agents))
        elif backup_path.exists() or backup_path.is_symlink():
            backup_path.unlink()


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
