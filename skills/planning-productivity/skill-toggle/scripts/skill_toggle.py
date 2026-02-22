#!/usr/bin/env python3
"""skill-toggle: Enable, disable, and manage Claude Code skills."""

import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

SKILLS_DIR = Path.home() / ".claude" / "skills"
DISABLED_DIR = SKILLS_DIR / "disabled"
ORPHANS_DIR = DISABLED_DIR / "orphans"
COLLECTIONS_DIR = Path(__file__).resolve().parent.parent / "collections"
SETTINGS_FILE = Path.home() / ".claude" / "settings.json"
PROTECTED_NAMES = {"disabled", "skill-toggle"}
VALID_NAME_RE = re.compile(r"^[a-zA-Z0-9_\-]+$")


def validate_skill_name(name):
    """Reject names containing path separators or traversal components."""
    if not VALID_NAME_RE.match(name):
        print(f"  ERROR: Invalid skill name '{name}'")
        return False
    return True


def load_settings():
    """Load and parse settings.json with error handling."""
    if not SETTINGS_FILE.exists():
        return {}
    try:
        return json.loads(SETTINGS_FILE.read_text())
    except json.JSONDecodeError as e:
        print(f"  ERROR: settings.json is malformed: {e}")
        sys.exit(1)


def atomic_write_json(path, data):
    """Atomically write a JSON file via temp file + rename."""
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2) + "\n"
    fd, tmp_path = tempfile.mkstemp(dir=path.parent, suffix=".json.tmp")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)
        Path(tmp_path).replace(path)
    except Exception:
        os.unlink(tmp_path)
        raise


def save_settings(settings):
    """Atomically write settings.json."""
    atomic_write_json(SETTINGS_FILE, settings)


def safe_move(src, dest, label):
    """Move src to dest with collision check and error handling."""
    if dest.exists():
        print(f"  WARNING: {dest.name} already exists at destination, skipping")
        return False
    try:
        shutil.move(str(src), str(dest))
        return True
    except (shutil.Error, OSError) as e:
        print(f"  ERROR: could not move '{label}': {e}")
        return False


def extract_frontmatter(skill_path):
    """Extract name and description from SKILL.md frontmatter."""
    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return None, None
    text = skill_md.read_text(errors="replace")
    if not text.startswith("---"):
        return None, None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, None
    fm = parts[1]
    name = None
    desc = None
    for line in fm.splitlines():
        m = re.match(r"^name:\s*(.+)", line)
        if m:
            name = m.group(1).strip().strip("'\"")
        m = re.match(r"^description:\s*(.+)", line)
        if m:
            desc = m.group(1).strip().strip("'\"")
    return name, desc


def get_personal_skills():
    """Return list of (name, status, description) for personal skills."""
    skills = []
    # Enabled skills
    for d in sorted(SKILLS_DIR.iterdir()):
        if not d.is_dir() or d.name in ("disabled", "skill-toggle"):
            continue
        skill_md = d / "SKILL.md"
        if not skill_md.exists():
            continue
        _, desc = extract_frontmatter(d)
        skills.append((d.name, "enabled", desc or ""))
    # Disabled skills
    if DISABLED_DIR.exists():
        for d in sorted(DISABLED_DIR.iterdir()):
            if not d.is_dir() or d.name == "orphans":
                continue
            _, desc = extract_frontmatter(d)
            skills.append((d.name, "disabled", desc or ""))
    return skills


def get_plugin_skills():
    """Return list of (name, status, marketplace) for plugins."""
    settings = load_settings()
    plugins = settings.get("enabledPlugins", {})
    result = []
    for key, enabled in sorted(plugins.items()):
        name, marketplace = key.split("@", 1) if "@" in key else (key, "")
        status = "enabled" if enabled else "disabled"
        result.append((name, status, marketplace))
    return result


def resolve_plugin_key(name):
    """Find the full plugin key in settings.json matching a name or skill prefix."""
    settings = load_settings()
    plugins = settings.get("enabledPlugins", {})
    # Strip skill suffix (e.g., "compound-engineering:deepen-plan" -> "compound-engineering")
    plugin_name = name.split(":")[0]
    for key in plugins:
        if key.startswith(plugin_name + "@"):
            return key
    return None


def toggle_plugin(name, enable):
    """Set a plugin's enabled state in settings.json."""
    key = resolve_plugin_key(name)
    if not key:
        print(f"  Plugin '{name}' not found in settings.json")
        return False
    settings = load_settings()
    current = settings["enabledPlugins"].get(key, False)
    if current == enable:
        state = "enabled" if enable else "disabled"
        print(f"  Plugin '{name}' is already {state}")
        return False
    settings["enabledPlugins"][key] = enable
    save_settings(settings)
    state = "enabled" if enable else "disabled"
    print(f"  Plugin '{name}' -> {state}")
    return True


def regenerate_index():
    """Regenerate disabled/INDEX.md from current contents."""
    if not DISABLED_DIR.exists():
        return
    skills = []
    for d in sorted(DISABLED_DIR.iterdir()):
        if not d.is_dir() or d.name == "orphans":
            continue
        _, desc = extract_frontmatter(d)
        if desc:
            desc = desc[:80] + "..." if len(desc) > 80 else desc
        else:
            desc = "\u2014"
        skills.append((d.name, desc))

    lines = [
        "# Disabled Skills",
        "",
        f"*{len(skills)} skills parked here \u2014 not loaded by Claude Code.*",
        "",
        "| # | Skill | Description |",
        "|---|-------|-------------|",
    ]
    for i, (name, desc) in enumerate(skills, 1):
        lines.append(f"| {i} | `{name}` | {desc} |")

    (DISABLED_DIR / "INDEX.md").write_text("\n".join(lines) + "\n")


def cmd_list(args):
    """List all skills with status."""
    show_enabled = "--enabled" in args
    show_disabled = "--disabled" in args
    show_plugins = "--plugins" in args
    show_all = not (show_enabled or show_disabled or show_plugins)

    personal = get_personal_skills()
    plugins = get_plugin_skills()

    rows = []
    if show_all or show_enabled or show_disabled:
        for name, status, desc in personal:
            if show_enabled and status != "enabled":
                continue
            if show_disabled and status != "disabled":
                continue
            trunc = (desc[:50] + "...") if len(desc) > 50 else desc
            rows.append((status, "personal", name, trunc))

    if show_all or show_plugins or show_enabled or show_disabled:
        for name, status, marketplace in plugins:
            if show_enabled and status != "enabled":
                continue
            if show_disabled and status != "disabled":
                continue
            rows.append((status, "plugin", name, marketplace))

    # Print table
    print(f"{'#':>3}  {'Status':<9} {'Source':<9} {'Skill':<30} {'Description'}")
    print(f"{'':>3}  {'':=<9} {'':=<9} {'':=<30} {'':=<40}")
    for i, (status, source, name, desc) in enumerate(rows, 1):
        marker = "+" if status == "enabled" else "-"
        print(f"{i:>3}  {marker} {status:<7} {source:<9} {name:<30} {desc}")
    print(f"\nTotal: {len(rows)} ({sum(1 for r in rows if r[0] == 'enabled')} enabled, {sum(1 for r in rows if r[0] == 'disabled')} disabled)")


def cmd_disable(names):
    """Disable one or more skills."""
    if not names:
        print("Usage: skill-toggle disable <name> [name...]")
        return
    DISABLED_DIR.mkdir(parents=True, exist_ok=True)
    personal_changed = False
    for name in names:
        if not validate_skill_name(name):
            continue
        if name in PROTECTED_NAMES:
            print(f"  Cannot disable '{name}'")
            continue
        skill_dir = SKILLS_DIR / name
        disabled_dest = DISABLED_DIR / name
        if skill_dir.exists() and skill_dir.is_dir():
            if safe_move(skill_dir, disabled_dest, name):
                print(f"  {name} -> disabled (personal)")
                personal_changed = True
        elif resolve_plugin_key(name):
            toggle_plugin(name, False)
        elif disabled_dest.exists():
            print(f"  {name} is already disabled")
        else:
            print(f"  {name} not found")
    if personal_changed:
        regenerate_index()


def cmd_enable(names):
    """Enable one or more skills."""
    if not names:
        print("Usage: skill-toggle enable <name> [name...]")
        return
    personal_changed = False
    for name in names:
        if not validate_skill_name(name):
            continue
        disabled_src = DISABLED_DIR / name
        skill_dest = SKILLS_DIR / name
        if disabled_src.exists() and disabled_src.is_dir():
            if safe_move(disabled_src, skill_dest, name):
                print(f"  {name} -> enabled (personal)")
                personal_changed = True
        elif resolve_plugin_key(name):
            toggle_plugin(name, True)
        elif skill_dest.exists():
            print(f"  {name} is already enabled")
        else:
            print(f"  {name} not found in disabled/ or plugins")
    if personal_changed:
        regenerate_index()


def cmd_status(names):
    """Show details for a specific skill."""
    if not names:
        print("Usage: skill-toggle status <name>")
        return
    name = names[0]
    skill_dir = SKILLS_DIR / name
    disabled_dir = DISABLED_DIR / name

    if skill_dir.exists() and skill_dir.is_dir():
        _, desc = extract_frontmatter(skill_dir)
        print(f"  Skill:  {name}")
        print(f"  Status: enabled (personal)")
        print(f"  Path:   {skill_dir}")
        if desc:
            print(f"  Desc:   {desc}")
        contents = [f.name for f in skill_dir.iterdir() if not f.name.startswith(".")]
        print(f"  Files:  {', '.join(sorted(contents))}")
    elif disabled_dir.exists():
        _, desc = extract_frontmatter(disabled_dir)
        print(f"  Skill:  {name}")
        print(f"  Status: disabled (personal)")
        print(f"  Path:   {disabled_dir}")
        if desc:
            print(f"  Desc:   {desc}")
    elif (key := resolve_plugin_key(name)):
        settings = load_settings()
        enabled = settings.get("enabledPlugins", {}).get(key, False)
        print(f"  Plugin: {name}")
        print(f"  Status: {'enabled' if enabled else 'disabled'}")
        print(f"  Key:    {key}")
    else:
        print(f"  '{name}' not found")


def cmd_search(args):
    """Fuzzy match across all skill names and descriptions."""
    if not args:
        print("Usage: skill-toggle search <query>")
        return
    query = " ".join(args).lower()
    personal = get_personal_skills()
    plugins = get_plugin_skills()

    matches = []
    for name, status, desc in personal:
        if query in name.lower() or query in desc.lower():
            matches.append((name, status, "personal", desc))
    for name, status, marketplace in plugins:
        if query in name.lower() or query in marketplace.lower():
            matches.append((name, status, "plugin", marketplace))

    if not matches:
        print(f"  No skills matching '{query}'")
        return
    print(f"{'#':>3}  {'Status':<9} {'Source':<9} {'Skill':<30} {'Info'}")
    for i, (name, status, source, info) in enumerate(matches, 1):
        trunc = (info[:50] + "...") if len(info) > 50 else info
        marker = "+" if status == "enabled" else "-"
        print(f"{i:>3}  {marker} {status:<7} {source:<9} {name:<30} {trunc}")


def cmd_clean(_args):
    """Move orphan directories, zip files, and stale scripts to disabled/orphans/."""
    ORPHANS_DIR.mkdir(parents=True, exist_ok=True)
    moved = []
    try:
        entries = sorted(SKILLS_DIR.iterdir())
    except OSError as e:
        print(f"  ERROR: Cannot read skills directory: {e}")
        return
    for item in entries:
        if item.name in PROTECTED_NAMES:
            continue
        dest = ORPHANS_DIR / item.name
        # Zip files
        if item.is_file() and item.suffix == ".zip":
            if safe_move(item, dest, item.name):
                moved.append(f"  {item.name} (zip file)")
            continue
        # Stale shell scripts
        if item.is_file() and item.suffix == ".sh":
            if safe_move(item, dest, item.name):
                moved.append(f"  {item.name} (shell script)")
            continue
        # Directories without SKILL.md
        if item.is_dir() and not (item / "SKILL.md").exists():
            if safe_move(item, dest, item.name):
                moved.append(f"  {item.name}/ (no SKILL.md)")
            continue

    if moved:
        print(f"Moved {len(moved)} items to {ORPHANS_DIR}:")
        for m in moved:
            print(m)
    else:
        print("Nothing to clean.")


# --- Collections ---

def load_collection(name):
    """Load a collection JSON file."""
    path = COLLECTIONS_DIR / f"{name}.json"
    if not path.exists():
        print(f"  Collection '{name}' not found")
        return None
    try:
        data = json.loads(path.read_text())
    except json.JSONDecodeError as e:
        print(f"  ERROR: {name}.json is malformed: {e}")
        return None
    return {
        "skills": data.get("skills", []),
        "plugins": data.get("plugins", []),
    }


def save_collection(name, data):
    """Atomically write a collection JSON file."""
    atomic_write_json(COLLECTIONS_DIR / f"{name}.json", data)


def get_enabled_personal():
    """Return set of currently-enabled personal skill names."""
    names = set()
    try:
        entries = sorted(SKILLS_DIR.iterdir())
    except OSError as e:
        print(f"  ERROR: Cannot read skills directory: {e}")
        return names
    for d in entries:
        if not d.is_dir() or d.name in ("disabled", "skill-toggle"):
            continue
        if (d / "SKILL.md").exists():
            names.add(d.name)
    return names


def get_enabled_plugins():
    """Return set of currently-enabled plugin name prefixes."""
    settings = load_settings()
    plugins = settings.get("enabledPlugins", {})
    names = set()
    for key, enabled in plugins.items():
        if enabled:
            name = key.split("@")[0] if "@" in key else key
            names.add(name)
    return names


def skill_status(name):
    """Return 'enabled', 'disabled', or 'unknown' for a skill/plugin name."""
    if (SKILLS_DIR / name).is_dir() and (SKILLS_DIR / name / "SKILL.md").exists():
        return "enabled"
    if (DISABLED_DIR / name).is_dir():
        return "disabled"
    if (key := resolve_plugin_key(name)):
        settings = load_settings()
        return "enabled" if settings.get("enabledPlugins", {}).get(key, False) else "disabled"
    return "unknown"


def collection_list():
    """Show all collections."""
    if not COLLECTIONS_DIR.exists():
        print("  No collections defined yet.")
        print(f"  Create one: skill-toggle collection create <name> <skills...>")
        return
    files = sorted(COLLECTIONS_DIR.glob("*.json"))
    if not files:
        print("  No collections defined yet.")
        return
    print(f"  {'#':>3}  {'Collection':<20} {'Skills':>6}  {'Plugins':>7}")
    print(f"  {'':>3}  {'':=<20} {'':=<6}  {'':=<7}")
    for i, f in enumerate(files, 1):
        try:
            data = json.loads(f.read_text())
        except json.JSONDecodeError as e:
            print(f"  {i:>3}  {f.stem:<20} ERROR: malformed JSON ({e})")
            continue
        except OSError as e:
            print(f"  {i:>3}  {f.stem:<20} ERROR: unreadable ({e})")
            continue
        skills = len(data.get("skills", []))
        plugins = len(data.get("plugins", []))
        print(f"  {i:>3}  {f.stem:<20} {skills:>6}  {plugins:>7}")


def collection_show(name):
    """Show skills in a collection with current status."""
    data = load_collection(name)
    if not data:
        return
    skills = data["skills"]
    plugins = data["plugins"]
    print(f"  Collection: {name} ({len(skills)} skills, {len(plugins)} plugins)")
    if skills:
        print(f"\n  Skills:")
        for s in skills:
            st = skill_status(s)
            marker = "+" if st == "enabled" else "-" if st == "disabled" else "?"
            print(f"    {marker} {s:<35} ({st})")
    if plugins:
        print(f"\n  Plugins:")
        for p in plugins:
            st = skill_status(p)
            marker = "+" if st == "enabled" else "-" if st == "disabled" else "?"
            print(f"    {marker} {p:<35} ({st})")


def collection_create(name, items):
    """Create a new collection from an explicit skill list."""
    if not items:
        print("  Usage: skill-toggle collection create <name> <skill1> [skill2...]")
        return
    path = COLLECTIONS_DIR / f"{name}.json"
    if path.exists():
        print(f"  Collection '{name}' already exists. Use 'add' to modify it.")
        return
    skills = []
    plugins = []
    for item in items:
        if resolve_plugin_key(item):
            plugins.append(item.split(":")[0])
        else:
            skills.append(item)
    save_collection(name, {"skills": skills, "plugins": plugins})
    print(f"  Created collection '{name}': {len(skills)} skills, {len(plugins)} plugins")


def collection_save(name):
    """Snapshot all currently-enabled skills and plugins as a collection."""
    path = COLLECTIONS_DIR / f"{name}.json"
    if path.exists():
        print(f"  Collection '{name}' already exists. Delete it first or choose another name.")
        return
    skills = sorted(get_enabled_personal())
    plugins = sorted(get_enabled_plugins())
    save_collection(name, {"skills": skills, "plugins": plugins})
    print(f"  Saved collection '{name}': {len(skills)} skills, {len(plugins)} plugins")


def _collection_toggle(name, enable):
    """Enable or disable all skills/plugins in a collection."""
    data = load_collection(name)
    if not data:
        return
    if not data["skills"] and not data["plugins"]:
        print(f"  Collection '{name}' is empty")
        return
    action = "Enabling" if enable else "Disabling"
    state = "on" if enable else "off"
    cmd = cmd_enable if enable else cmd_disable
    print(f"  {action} collection '{name}'...")
    if data["skills"]:
        cmd(data["skills"])
    for plugin in data["plugins"]:
        toggle_plugin(plugin, enable)
    print(f"  Collection '{name}' {state}.")


def collection_on(name):
    """Enable all skills in a collection."""
    _collection_toggle(name, True)


def collection_off(name):
    """Disable all skills in a collection."""
    _collection_toggle(name, False)


def collection_delete(name):
    """Remove a collection definition."""
    path = COLLECTIONS_DIR / f"{name}.json"
    if not path.exists():
        print(f"  Collection '{name}' not found")
        return
    try:
        path.unlink()
    except OSError as e:
        print(f"  ERROR: Could not delete collection '{name}': {e}")
        return
    print(f"  Deleted collection '{name}'")


def collection_add(name, items):
    """Add skills to an existing collection."""
    if not items:
        print("  Usage: skill-toggle collection add <name> <skill1> [skill2...]")
        return
    data = load_collection(name)
    if not data:
        return
    added = 0
    for item in items:
        if resolve_plugin_key(item):
            pname = item.split(":")[0]
            if pname not in data["plugins"]:
                data["plugins"].append(pname)
                added += 1
            else:
                print(f"  '{pname}' already in collection '{name}'")
        else:
            if item not in data["skills"]:
                data["skills"].append(item)
                added += 1
            else:
                print(f"  '{item}' already in collection '{name}'")
    if added:
        save_collection(name, data)
    print(f"  Added {added} items to collection '{name}'")


def collection_remove(name, items):
    """Remove skills from an existing collection."""
    if not items:
        print("  Usage: skill-toggle collection remove <name> <skill1> [skill2...]")
        return
    data = load_collection(name)
    if not data:
        return
    removed = 0
    for item in items:
        pname = item.split(":")[0]
        if pname in data["plugins"]:
            data["plugins"].remove(pname)
            removed += 1
        elif pname in data["skills"]:
            data["skills"].remove(pname)
            removed += 1
        else:
            print(f"  '{item}' not in collection '{name}'")
    if removed:
        save_collection(name, data)
    print(f"  Removed {removed} items from collection '{name}'")


COLLECTION_COMMANDS = {
    "list": lambda args: collection_list(),
    "show": lambda args: collection_show(args[0]) if args else print("  Usage: skill-toggle collection show <name>"),
    "create": lambda args: collection_create(args[0], args[1:]) if args else print("  Usage: skill-toggle collection create <name> <skills...>"),
    "save": lambda args: collection_save(args[0]) if args else print("  Usage: skill-toggle collection save <name>"),
    "on": lambda args: collection_on(args[0]) if args else print("  Usage: skill-toggle collection on <name>"),
    "off": lambda args: collection_off(args[0]) if args else print("  Usage: skill-toggle collection off <name>"),
    "delete": lambda args: collection_delete(args[0]) if args else print("  Usage: skill-toggle collection delete <name>"),
    "add": lambda args: collection_add(args[0], args[1:]) if args else print("  Usage: skill-toggle collection add <name> <skills...>"),
    "remove": lambda args: collection_remove(args[0], args[1:]) if args else print("  Usage: skill-toggle collection remove <name> <skills...>"),
}


def cmd_collection(args):
    """Manage skill collections."""
    if not args or args[0] in ("-h", "--help"):
        print("Usage: skill-toggle collection <subcommand> [args]")
        print()
        print("Subcommands:")
        print("  list                          Show all collections")
        print("  show <name>                   Show skills in a collection")
        print("  create <name> <skills...>     Define a new collection")
        print("  save <name>                   Snapshot enabled skills as a collection")
        print("  on <name>                     Enable all skills in collection")
        print("  off <name>                    Disable all skills in collection")
        print("  add <name> <skills...>        Add skills to a collection")
        print("  remove <name> <skills...>     Remove skills from a collection")
        print("  delete <name>                 Delete a collection")
        return
    subcmd = args[0]
    subargs = args[1:]
    # Validate collection name for subcommands that take one
    if subcmd not in ("list",) and subargs:
        if not validate_skill_name(subargs[0]):
            return
    if subcmd in COLLECTION_COMMANDS:
        COLLECTION_COMMANDS[subcmd](subargs)
    else:
        print(f"  Unknown collection subcommand: {subcmd}")
        print(f"  Available: {', '.join(COLLECTION_COMMANDS)}")


COMMANDS = {
    "list": cmd_list,
    "disable": cmd_disable,
    "enable": cmd_enable,
    "status": cmd_status,
    "search": cmd_search,
    "clean": cmd_clean,
    "collection": cmd_collection,
}


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print("Usage: skill-toggle <command> [args]")
        print()
        print("Commands:")
        print("  list [--enabled|--disabled|--plugins]  Show skills with status")
        print("  disable <name> [name...]               Disable skill(s)")
        print("  enable <name> [name...]                Enable skill(s)")
        print("  status <name>                          Show skill details")
        print("  search <query>                         Fuzzy search skills")
        print("  clean                                  Move orphans to disabled/orphans/")
        print("  collection <subcommand>                Manage skill collections")
        sys.exit(0)

    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd in COMMANDS:
        COMMANDS[cmd](args)
    else:
        print(f"Unknown command: {cmd}")
        print(f"Available: {', '.join(COMMANDS)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
