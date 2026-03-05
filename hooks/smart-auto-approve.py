#!/usr/bin/env python3
"""
PermissionRequest hook — auto-approve safe tool patterns, deny dangerous ones.

Decision matrix:
  - ALLOW: read-only git commands, test runners, file inspection (grep/find/ls/cat)
  - DENY:  rm -rf /, sudo, chmod 777, curl|bash, fork bombs, --no-verify
  - PASS:  everything else → normal permission dialog

Only applies to Bash commands. Non-Bash tool permissions pass through.
"""

import json
import re
import sys


# Patterns that are ALWAYS safe to auto-approve (anchored to command start)
ALLOW_PATTERNS = [
    # Git read-only
    r"^git\s+(status|diff|log|show|branch|tag|stash\s+list|remote|config\s+--get|rev-parse|describe)",
    r"^git\s+ls-files",
    r"^git\s+blame\b",

    # File inspection (read-only)
    r"^(ls|stat|file|wc|du|df|head|tail|cat|less|more)\s",
    r"^(find|fd)\s",
    r"^(grep|rg|ag|ack)\s",

    # Test runners
    r"^(npm|npx|bun|bunx)\s+(test|run\s+test|vitest|jest)",
    r"^(uv\s+run\s+)?pytest\b",
    r"^(uv\s+run\s+)?python3?\s+-m\s+pytest\b",

    # Package info (read-only)
    r"^(npm|bun)\s+(list|ls|outdated|info|view|why)\b",
    r"^(uv\s+)?pip\s+(list|show|freeze)\b",

    # Process inspection
    r"^lsof\s+-i\b",
    r"^ps\s+(aux|ef|a)\b",
    r"^(which|where|command\s+-v|type)\s",

    # System info
    r"^(pwd|whoami|hostname|uname|date|uptime|sw_vers)\b",
    r"^echo\s+\$",

    # Node/Python version checks
    r"^(node|python3?|ruby|go|rustc|cargo|bun|deno)\s+(-v|--version)\b",
]

# Patterns that should ALWAYS be denied
DENY_PATTERNS = [
    # Destructive system commands
    r"sudo\b",
    r"rm\s+-rf\s+/\s*$",
    r"rm\s+-rf\s+/[^.]",  # rm -rf /usr, /etc, etc.
    r"rm\s+-rf\s+~",       # rm -rf ~ (home directory)
    r"rm\s+-rf\s+\.\s*$",  # rm -rf . (current directory)
    r"chmod\s+777\b",
    r"chown\s+-R\b.*/$",  # recursive chown on root
    r"^\s*eval\s",         # eval with arbitrary input
    r"^\s*dd\s",           # dd can overwrite disks
    r"python3?\s+-c\s",    # arbitrary Python execution

    # Code execution from network
    r"curl\s.*\|\s*(ba)?sh",
    r"wget\s.*\|\s*(ba)?sh",
    r"curl\s.*\|\s*python",

    # Fork bombs and dangerous shell constructs
    r":\(\)\s*\{",
    r"\|\s*xargs\s+rm\b",

    # Git dangerous without confirmation
    r"git\s+push\s+.*--force(?!-with-lease)",
    r"git\s+reset\s+--hard\b",
    r"git\s+clean\s+-f",
    r"--no-verify\b",
    r"--no-gpg-sign\b",

    # Database destructive
    r"DROP\s+(TABLE|DATABASE)\b",
    r"TRUNCATE\s+TABLE\b",
    r"DELETE\s+FROM\s+\w+\s*;?\s*$",  # DELETE without WHERE
]


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

    # Check deny list first (safety takes priority)
    for pattern in DENY_PATTERNS:
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
    for pattern in ALLOW_PATTERNS:
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
