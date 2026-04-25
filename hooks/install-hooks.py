#!/usr/bin/env python3
"""Install hook scripts and merge hook configuration into settings.json."""

import argparse
import json
import os
import shutil
import sys
import tempfile

HOOKS_DIR = os.path.expanduser("~/.claude/hooks")
SOUNDS_DIR = os.path.expanduser("~/.claude/sounds")
SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")

SKIP_FILES = {"README.md", "INDEX.md", "hooks.json", "install-hooks.py", "HANDOFF-MODEL-EVAL.md"}
SKIP_DIRS = {"tests", "__pycache__"}

GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
NC = "\033[0m"


def print_green(msg):
    print(f"{GREEN}✓ {msg}{NC}")


def print_yellow(msg):
    print(f"{YELLOW}⚠ {msg}{NC}")


def print_blue(msg):
    print(f"{BLUE}ℹ {msg}{NC}")


def copy_hook_scripts(repo_dir):
    """Copy all hook scripts (.py, .sh) to ~/.claude/hooks/."""
    hooks_src = os.path.join(repo_dir, "hooks")
    os.makedirs(HOOKS_DIR, exist_ok=True)

    copied = 0
    for entry in os.listdir(hooks_src):
        if entry in SKIP_FILES:
            continue
        src = os.path.join(hooks_src, entry)
        if os.path.isdir(src):
            if entry not in SKIP_DIRS:
                dst = os.path.join(HOOKS_DIR, entry)
                shutil.copytree(src, dst, dirs_exist_ok=True)
            continue
        if not (entry.endswith(".py") or entry.endswith(".sh")):
            continue
        if os.path.islink(src):
            link_target = os.readlink(src)
            dst = os.path.join(HOOKS_DIR, entry)
            if os.path.lexists(dst):
                os.remove(dst)
            os.symlink(link_target, dst)
        else:
            shutil.copy2(src, os.path.join(HOOKS_DIR, entry))
        copied += 1

    return copied


def set_permissions():
    """Make all hook scripts executable."""
    made_exec = 0
    for entry in os.listdir(HOOKS_DIR):
        path = os.path.join(HOOKS_DIR, entry)
        if os.path.isfile(path) and (entry.endswith(".py") or entry.endswith(".sh")):
            os.chmod(path, 0o755)
            made_exec += 1
    return made_exec


def create_symlinks():
    """Create on-thinking.sh and on-ready.sh symlinks."""
    target = os.path.join(HOOKS_DIR, "terminal-title.sh")
    if not os.path.exists(target):
        print_yellow("terminal-title.sh not found — skipping symlink creation")
        return
    for name in ("on-thinking.sh", "on-ready.sh"):
        link_path = os.path.join(HOOKS_DIR, name)
        if os.path.lexists(link_path):
            os.remove(link_path)
        os.symlink("terminal-title.sh", link_path)


def copy_sounds(repo_dir):
    """Copy notification sounds to ~/.claude/sounds/."""
    sounds_src = os.path.join(repo_dir, "sounds")
    if not os.path.isdir(sounds_src):
        return
    os.makedirs(SOUNDS_DIR, exist_ok=True)
    for entry in os.listdir(sounds_src):
        src = os.path.join(sounds_src, entry)
        if os.path.isfile(src):
            shutil.copy2(src, os.path.join(SOUNDS_DIR, entry))


def load_settings():
    """Load existing settings.json or return empty dict."""
    if not os.path.exists(SETTINGS_PATH):
        return {}
    try:
        with open(SETTINGS_PATH) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print_yellow(f"settings.json is malformed: {e}")
        backup = SETTINGS_PATH + ".bak"
        try:
            shutil.copy2(SETTINGS_PATH, backup)
            print_blue(f"Backup saved to {backup}")
        except OSError as backup_err:
            print_yellow(f"Could not create backup: {backup_err}")
        print_yellow("Starting fresh for hooks config")
        return {}
    except OSError as e:
        print_yellow(f"Cannot read {SETTINGS_PATH}: {e}")
        return {}


def save_settings(settings):
    """Atomic write to settings.json."""
    os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
    dir_ = os.path.dirname(SETTINGS_PATH)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, suffix=".tmp") as f:
            tmp_path = f.name
            json.dump(settings, f, indent=2)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, SETTINGS_PATH)
    except OSError as e:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        raise RuntimeError(f"Failed to write {SETTINGS_PATH}: {e}") from e


def merge_hooks(existing_hooks, new_hooks):
    """Merge new hooks into existing, deduplicating by command string."""
    for event_name, matcher_groups in new_hooks.items():
        if event_name not in existing_hooks:
            existing_hooks[event_name] = matcher_groups
            continue
        if not matcher_groups:
            if event_name not in existing_hooks:
                existing_hooks[event_name] = []
            continue
        for new_group in matcher_groups:
            new_matcher = new_group.get("matcher", "")
            found = False
            for existing_group in existing_hooks[event_name]:
                if existing_group.get("matcher", "") == new_matcher:
                    existing_cmds = {h["command"] for h in existing_group["hooks"]}
                    for hook in new_group["hooks"]:
                        if hook["command"] not in existing_cmds:
                            existing_group["hooks"].append(hook)
                    found = True
                    break
            if not found:
                existing_hooks[event_name].append(new_group)
    return existing_hooks


def check_dependencies(tier):
    """Warn about missing optional dependencies."""
    warnings = []

    if shutil.which("terminal-notifier") is None:
        warnings.append("terminal-notifier not found — install with: brew install terminal-notifier")

    if shutil.which("ccstatusline") is None:
        warnings.append("ccstatusline not found — install with: npm install -g ccstatusline")

    if tier == "full":
        if not os.environ.get("OPENROUTER_API_KEY"):
            warnings.append("OPENROUTER_API_KEY not set — needed for session handoffs and AI-powered tags")
        claudicle_dir = os.path.expanduser("~/.claudicle")
        if not os.path.isdir(claudicle_dir):
            warnings.append("Claudicle framework not found at ~/.claudicle/ — soul hooks will be inactive")

    return warnings


def main():
    parser = argparse.ArgumentParser(description="Install claude-code-minoan hooks")
    parser.add_argument("--tier", choices=["essential", "full"], required=True)
    parser.add_argument("--repo", required=True, help="Path to claude-code-minoan repo root")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    args = parser.parse_args()

    hooks_json_path = os.path.join(args.repo, "hooks", "hooks.json")
    if not os.path.exists(hooks_json_path):
        print(f"Error: hooks.json not found at {hooks_json_path}", file=sys.stderr)
        sys.exit(1)

    try:
        with open(hooks_json_path) as f:
            template = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: hooks.json is malformed at line {e.lineno}: {e.msg}", file=sys.stderr)
        print(f"  File: {hooks_json_path}", file=sys.stderr)
        sys.exit(1)

    if args.tier not in template:
        print(f"Error: tier '{args.tier}' not found in hooks.json", file=sys.stderr)
        sys.exit(1)

    tier_config = template[args.tier]

    if args.dry_run:
        print_blue(f"[dry-run] Would install {args.tier} tier hooks")
        print_blue(f"[dry-run] Events: {', '.join(tier_config['hooks'].keys())}")
        hook_count = sum(
            len(h["hooks"]) for groups in tier_config["hooks"].values() for h in groups
        )
        print_blue(f"[dry-run] Total hook handlers: {hook_count}")
        return

    try:
        print_blue(f"Installing {args.tier} tier hooks...")

        copied = copy_hook_scripts(args.repo)
        print_green(f"{copied} hook scripts copied to {HOOKS_DIR}")

        set_permissions()
        create_symlinks()
        print_green("Symlinks and permissions set")

        copy_sounds(args.repo)

        settings = load_settings()
        existing_hooks = settings.get("hooks", {})
        settings["hooks"] = merge_hooks(existing_hooks, tier_config["hooks"])
        if "statusLine" not in settings:
            settings["statusLine"] = tier_config["statusLine"]
        save_settings(settings)
        print_green("Hook configuration merged into settings.json")
    except Exception as e:
        print(f"\n{YELLOW}Error during hook installation: {e}{NC}", file=sys.stderr)
        print(f"  Installation may be incomplete. Re-run to retry.", file=sys.stderr)
        sys.exit(1)

    hook_count = sum(
        len(h["hooks"]) for groups in tier_config["hooks"].values() for h in groups
    )
    event_count = len([k for k, v in tier_config["hooks"].items() if v])
    print_green(f"Installed: {hook_count} hook handlers across {event_count} events")

    warnings = check_dependencies(args.tier)
    if warnings:
        print()
        print_yellow("Optional dependencies:")
        for w in warnings:
            print(f"  {w}")


if __name__ == "__main__":
    main()
