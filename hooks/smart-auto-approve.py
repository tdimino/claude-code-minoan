#!/usr/bin/env python3
"""
PermissionRequest hook — auto-approve safe tool patterns, deny dangerous ones.

Decision matrix:
  - ALLOW: read-only git commands, test runners, file inspection (grep/find/ls/cat)
  - DENY:  rm -rf /, sudo, chmod 777, curl|bash, fork bombs, --no-verify
  - PASS:  everything else → normal permission dialog

Only applies to Bash commands. Non-Bash tool permissions pass through.

Patterns are loaded from ~/.claude/config/auto-approve-whitelist.json if it exists,
falling back to hardcoded defaults. Edit the JSON file to add/remove patterns
without touching this script.
"""

import json
import os
import re
import sys

CONFIG_PATH = os.path.expanduser("~/.claude/config/auto-approve-whitelist.json")

# Hardcoded fallbacks (used when config file is missing or malformed)
_FALLBACK_ALLOW = [
    r"^git\s+(status|diff|log|show|branch|tag|stash\s+list|remote|config\s+--get|rev-parse|describe)",
    r"^git\s+ls-files",
    r"^git\s+blame\b",
    r"^(ls|stat|file|wc|du|df|head|tail|cat|less|more)\s",
    r"^(find|fd)\s",
    r"^(grep|rg|ag|ack)\s",
    r"^(npm|npx|bun|bunx)\s+(test|run\s+test|vitest|jest)",
    r"^(uv\s+run\s+)?pytest\b",
    r"^(uv\s+run\s+)?python3?\s+-m\s+pytest\b",
    r"^(npm|bun)\s+(list|ls|outdated|info|view|why)\b",
    r"^(uv\s+)?pip\s+(list|show|freeze)\b",
    r"^lsof\s+-i\b",
    r"^ps\s+(aux|ef|a)\b",
    r"^(which|where|command\s+-v|type)\s",
    r"^(pwd|whoami|hostname|uname|date|uptime|sw_vers)\b",
    r"^echo\s+\$",
    r"^(node|python3?|ruby|go|rustc|cargo|bun|deno)\s+(-v|--version)\b",
]

_FALLBACK_DENY = [
    r"sudo\b",
    r"rm\s+-rf\s+/\s*$",
    r"rm\s+-rf\s+/[^.]",
    r"rm\s+-rf\s+~",
    r"rm\s+-rf\s+\.\s*$",
    r"chmod\s+777\b",
    r"chown\s+-R\b.*/$",
    r"^\s*eval\s",
    r"^\s*dd\s",
    r"python3?\s+-c\s",
    r"curl\s.*\|\s*(ba)?sh",
    r"wget\s.*\|\s*(ba)?sh",
    r"curl\s.*\|\s*python",
    r":\(\)\s*\{",
    r"\|\s*xargs\s+rm\b",
    r"git\s+push\s+.*--force(?!-with-lease)",
    r"git\s+reset\s+--hard\b",
    r"git\s+clean\s+-f",
    r"--no-verify\b",
    r"--no-gpg-sign\b",
    r"DROP\s+(TABLE|DATABASE)\b",
    r"TRUNCATE\s+TABLE\b",
    r"DELETE\s+FROM\s+\w+\s*;?\s*$",
]


def load_patterns():
    """Load allow/deny patterns from JSON config, falling back to hardcoded defaults."""
    if not os.path.exists(CONFIG_PATH):
        return _FALLBACK_ALLOW, _FALLBACK_DENY

    try:
        with open(CONFIG_PATH) as f:
            config = json.load(f)
        allow = [entry["pattern"] for entry in config.get("allow", [])]
        deny = [entry["pattern"] for entry in config.get("deny", [])]
        if not allow and not deny:
            return _FALLBACK_ALLOW, _FALLBACK_DENY
        return allow or _FALLBACK_ALLOW, deny or _FALLBACK_DENY
    except (json.JSONDecodeError, KeyError, TypeError):
        return _FALLBACK_ALLOW, _FALLBACK_DENY


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    tool_name = hook_input.get("tool_name", "")

    # Only auto-approve/deny Bash commands
    if tool_name != "Bash":
        sys.exit(0)

    command = hook_input.get("tool_input", {}).get("command", "")
    if not command:
        sys.exit(0)

    # Strip leading whitespace and normalize
    command = command.strip()

    # Guard: reject any command with shell chaining operators.
    # A "safe" prefix like `git status` becomes dangerous with `; rm -rf ~` appended.
    # These commands fall through to the normal permission dialog (not denied, not allowed).
    if re.search(r'[;|&`]|\$\(|>\s|>>', command):
        sys.exit(0)

    allow_patterns, deny_patterns = load_patterns()

    # Check deny list first (safety takes priority)
    for pattern in deny_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "permissionDecision": "deny",
                    "reason": f"Blocked by safety rule: {pattern}",
                }
            }
            print(json.dumps(output))
            sys.exit(0)

    # Check allow list
    for pattern in allow_patterns:
        if re.search(pattern, command, re.IGNORECASE):
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PermissionRequest",
                    "permissionDecision": "allow",
                }
            }
            print(json.dumps(output))
            sys.exit(0)

    # Everything else: pass through to normal permission dialog
    sys.exit(0)


if __name__ == "__main__":
    main()
