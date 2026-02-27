#!/usr/bin/env python3
"""Claude Code plugin profile manager. Keeps total agents under the ~40 limit.

Usage:
    cplugins status              Show current profile and agent counts
    cplugins soul                Switch to soul profile (all subdaimones)
    cplugins compound            Switch to compound-engineering profile
    cplugins lean                Switch to lean profile (minimal plugins)
    cplugins <profile> --launch  Switch profile and launch claude
    cplugins --only P1 P2 ...   Enable only named plugins (ad-hoc)

Background:
    Claude Code has an undocumented ~37-40 agent limit. When total agents
    (built-in + plugin + custom) exceed this, agents are silently dropped.
    See: https://github.com/anthropics/claude-code/issues/18993

    This tool manages plugin profiles to keep the total under the limit
    by editing enabledPlugins in ~/.claude/settings.json.
"""

import json
import os
import sys
import tempfile

SETTINGS_PATH = os.path.expanduser("~/.claude/settings.json")
PROFILES_PATH = os.path.expanduser("~/.claude/scripts/plugin-profiles.json")

# Agent counts per plugin — update when plugins change
AGENT_COUNTS = {
    "compound-engineering@every-marketplace": 28,
    "pr-review-toolkit@claude-code-plugins": 6,
    "agent-evaluation@context-engineering-marketplace": 5,
    "feature-dev@claude-code-plugins": 3,
    "llm-application-dev@claude-code-workflows": 3,
    "agent-sdk-dev@claude-code-plugins": 2,
    "model-trainer@huggingface-skills": 0,
    "exa-mcp-server@exa-mcp-server": 0,
    "frontend-mobile-development@claude-code-workflows": 0,
    "multi-platform-apps@claude-code-workflows": 0,
    "example-skills@anthropic-agent-skills": 0,
    "frontend-design@claude-code-plugins": 0,
    "osgrep@osgrep": 0,
    "dev-browser@dev-browser-marketplace": 0,
    "ralph-wiggum@claude-code-plugins": 0,
    "commit-commands@claude-code-plugins": 0,
}

BUILTIN_AGENTS = 5
CUSTOM_AGENTS = 12
AGENT_LIMIT = 40

# ANSI colors
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"


def load_settings():
    if not os.path.exists(SETTINGS_PATH):
        return {}
    try:
        with open(SETTINGS_PATH) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"{RED}Error: settings.json is malformed: {e}{RESET}")
        print(f"  Path: {SETTINGS_PATH}")
        sys.exit(1)


def save_settings(settings):
    dir_ = os.path.dirname(SETTINGS_PATH)
    with tempfile.NamedTemporaryFile("w", dir=dir_, delete=False, suffix=".tmp") as f:
        tmp_path = f.name
        json.dump(settings, f, indent=2)
        f.write("\n")
    os.replace(tmp_path, SETTINGS_PATH)


def load_profiles():
    if not os.path.exists(PROFILES_PATH):
        print(f"{RED}Error: plugin-profiles.json not found at:{RESET}")
        print(f"  {PROFILES_PATH}")
        sys.exit(1)
    try:
        with open(PROFILES_PATH) as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"{RED}Error: plugin-profiles.json is malformed: {e}{RESET}")
        sys.exit(1)


def get_enabled_plugins(settings):
    return settings.get("enabledPlugins", {})


def count_plugin_agents(enabled_plugins):
    total = 0
    for plugin, enabled in enabled_plugins.items():
        if enabled:
            total += AGENT_COUNTS.get(plugin, 0)
    return total


def resolve_plugin_name(name, enabled_plugins):
    """Resolve a short or full plugin name against enabledPlugins and AGENT_COUNTS."""
    # Exact match in enabledPlugins
    if name in enabled_plugins:
        return name
    # Short name match in enabledPlugins
    for plugin in enabled_plugins:
        if plugin.startswith(name + "@"):
            return plugin
    # Fall back to AGENT_COUNTS as known-plugin registry
    if name in AGENT_COUNTS:
        return name
    for plugin in AGENT_COUNTS:
        if plugin.startswith(name + "@"):
            return plugin
    return None


def detect_profile(enabled_plugins, profiles):
    for name, profile in profiles.items():
        if profile["plugins"] == enabled_plugins:
            return name
    # Fuzzy match: check only plugins that contribute agents
    for name, profile in profiles.items():
        match = True
        checked = 0
        for plugin, state in profile["plugins"].items():
            if AGENT_COUNTS.get(plugin, 0) > 0:
                checked += 1
                if enabled_plugins.get(plugin, False) != state:
                    match = False
                    break
        if match and checked > 0:
            return f"{name}~"
    return "custom"


def print_status(settings, profiles):
    enabled_plugins = get_enabled_plugins(settings)
    plugin_agents = count_plugin_agents(enabled_plugins)
    total = BUILTIN_AGENTS + CUSTOM_AGENTS + plugin_agents
    profile = detect_profile(enabled_plugins, profiles)
    over = total > AGENT_LIMIT

    print(f"\n{BOLD}Claude Plugin Profile Manager{RESET}")
    print(f"{'─' * 50}")
    print(f"  Profile:        {CYAN}{profile}{RESET}")
    print(f"  Built-in:       {BUILTIN_AGENTS}")
    print(f"  Custom agents:  {CUSTOM_AGENTS}")
    print(f"  Plugin agents:  {plugin_agents}")
    total_color = RED if over else GREEN
    print(f"  {BOLD}Total:          {total_color}{total}{RESET}{BOLD} / {AGENT_LIMIT}{RESET}", end="")
    if over:
        print(f"  {RED}OVER LIMIT by {total - AGENT_LIMIT}{RESET}")
    else:
        print(f"  {GREEN}OK ({AGENT_LIMIT - total} slots free){RESET}")

    print(f"\n{BOLD}Enabled plugins:{RESET}")
    any_enabled = False
    for plugin, enabled in sorted(enabled_plugins.items()):
        if enabled:
            any_enabled = True
            agents = AGENT_COUNTS.get(plugin, "?")
            short_name = plugin.split("@")[0]
            print(f"  {GREEN}●{RESET} {short_name} {DIM}({agents} agents){RESET}")
    if not any_enabled:
        print(f"  {DIM}(none){RESET}")

    print(f"\n{BOLD}Disabled plugins:{RESET}")
    for plugin, enabled in sorted(enabled_plugins.items()):
        if not enabled:
            agents = AGENT_COUNTS.get(plugin, "?")
            short_name = plugin.split("@")[0]
            if agents and agents != "?" and agents > 0:
                print(f"  {DIM}○ {short_name} ({agents} agents){RESET}")
            else:
                print(f"  {DIM}○ {short_name}{RESET}")
    print()


def apply_profile(profile_name, profiles, settings, launch=False):
    if profile_name not in profiles:
        print(f"{RED}Unknown profile: {profile_name}{RESET}")
        print(f"Available: {', '.join(profiles.keys())}")
        sys.exit(1)

    profile = profiles[profile_name]
    enabled_plugins = get_enabled_plugins(settings)

    # Merge profile plugins into enabledPlugins (preserves unknown plugins)
    for plugin, state in profile["plugins"].items():
        enabled_plugins[plugin] = state

    settings["enabledPlugins"] = enabled_plugins
    save_settings(settings)

    plugin_agents = count_plugin_agents(enabled_plugins)
    total = BUILTIN_AGENTS + CUSTOM_AGENTS + plugin_agents
    over = total > AGENT_LIMIT

    total_color = RED if over else GREEN
    status = f"{RED}OVER LIMIT{RESET}" if over else f"{GREEN}OK{RESET}"

    print(f"\n{BOLD}Switched to profile: {CYAN}{profile_name}{RESET}")
    print(f"  {DIM}{profile['description']}{RESET}")
    print(f"  Total agents: {total_color}{total}{RESET} / {AGENT_LIMIT} — {status}")

    if over:
        print(f"  {YELLOW}Warning: {total - AGENT_LIMIT} agents over limit. Some may be silently dropped.{RESET}")

    # Warn about plugins enabled outside this profile
    profile_keys = set(profile["plugins"].keys())
    unknown_enabled = [p for p, v in enabled_plugins.items() if v and p not in profile_keys]
    if unknown_enabled:
        print(f"  {YELLOW}Note: {len(unknown_enabled)} plugin(s) enabled outside this profile{RESET}")
        for p in unknown_enabled:
            print(f"    + {p.split('@')[0]}")

    print(f"\n  {DIM}Restart Claude Code for changes to take effect.{RESET}\n")

    if launch:
        claude_path = os.path.expanduser("~/.local/bin/claude")
        if not os.path.exists(claude_path):
            claude_path = "claude"
        os.execvp(claude_path, [claude_path])


def apply_only(plugin_names, settings):
    enabled_plugins = get_enabled_plugins(settings)

    # Disable everything first
    for plugin in enabled_plugins:
        enabled_plugins[plugin] = False

    # Enable only the specified ones
    for name in plugin_names:
        resolved = resolve_plugin_name(name, enabled_plugins)
        if resolved:
            enabled_plugins[resolved] = True
        else:
            print(f"{YELLOW}Warning: plugin '{name}' not found{RESET}")

    settings["enabledPlugins"] = enabled_plugins
    save_settings(settings)

    plugin_agents = count_plugin_agents(enabled_plugins)
    total = BUILTIN_AGENTS + CUSTOM_AGENTS + plugin_agents
    total_color = RED if total > AGENT_LIMIT else GREEN

    print(f"\n{BOLD}Custom profile applied{RESET}")
    print(f"  Total agents: {total_color}{total}{RESET} / {AGENT_LIMIT}")
    enabled = [p.split("@")[0] for p, v in enabled_plugins.items() if v]
    print(f"  Enabled: {', '.join(enabled) if enabled else '(none)'}")
    print(f"\n  {DIM}Restart Claude Code for changes to take effect.{RESET}\n")


def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        print(__doc__)
        sys.exit(0)

    settings = load_settings()
    profiles = load_profiles()

    cmd = sys.argv[1]
    launch = "--launch" in sys.argv

    if cmd == "status":
        print_status(settings, profiles)
    elif cmd == "--only":
        plugin_names = [a for a in sys.argv[2:] if not a.startswith("--")]
        apply_only(plugin_names, settings)
    elif cmd in profiles:
        apply_profile(cmd, profiles, settings, launch=launch)
    else:
        print(f"{RED}Unknown command: {cmd}{RESET}")
        print(f"Available profiles: {', '.join(profiles.keys())}")
        print(f"Other commands: status, --only <plugins...>")
        sys.exit(1)


if __name__ == "__main__":
    main()
