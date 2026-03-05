#!/usr/bin/env python3
"""
PostToolUseFailure hook — inject contextual error hints after tool failures.

Pattern-matches common error messages and returns additionalContext with
actionable hints so Claude can self-correct faster.
"""

import json
import re
import sys


# Pattern → hint mapping. Patterns are checked in order; first match wins.
ERROR_HINTS = [
    # Network / port conflicts
    (r"EADDRINUSE.*?:(\d+)", lambda m: (
        f"Port {m.group(1)} is already in use. "
        f"Run `lsof -i :{m.group(1)}` to find the process, "
        f"then pick a different port or kill the process."
    )),
    (r"ECONNREFUSED", lambda m: (
        "Connection refused — the target server isn't running. "
        "Check if the service is started and on the expected port."
    )),

    # Python errors
    (r"ModuleNotFoundError: No module named '(\S+)'", lambda m: (
        f"Module '{m.group(1)}' not found. "
        f"Try `uv pip install {m.group(1)}` or check your venv is activated."
    )),
    (r"ImportError: cannot import name '(\S+)'", lambda m: (
        f"Cannot import '{m.group(1)}'. The module may be outdated — "
        f"try `uv pip install --upgrade` or check the API has changed."
    )),

    # File system
    (r"ENOENT|FileNotFoundError|No such file or directory", lambda m: (
        "File or directory not found. Verify the path exists with `ls` "
        "before retrying. Check for typos in the path."
    )),
    (r"EACCES|PermissionError|Permission denied", lambda m: (
        "Permission denied. Check file permissions with `ls -la`. "
        "Do NOT use sudo — consider if you're writing to the wrong location."
    )),

    # Git
    (r"CONFLICT.*Merge conflict", lambda m: (
        "Git merge conflict detected. Read the conflicting file to see the "
        "conflict markers (<<<<<<< / =======  / >>>>>>>), then resolve manually."
    )),
    (r"fatal: not a git repository", lambda m: (
        "Not inside a git repo. Check your working directory with `pwd`."
    )),
    (r"error: failed to push some refs", lambda m: (
        "Push rejected — remote has changes you don't have locally. "
        "Run `git pull --rebase` first, then push again."
    )),

    # Node.js / npm
    (r"ERR_MODULE_NOT_FOUND|Cannot find module", lambda m: (
        "Node module not found. Try `npm install` or `bun install` to "
        "restore dependencies."
    )),
    (r"SyntaxError: Unexpected token", lambda m: (
        "JavaScript syntax error. Check for missing commas, brackets, "
        "or unsupported syntax for the Node.js version."
    )),

    # Docker
    (r"Cannot connect to the Docker daemon", lambda m: (
        "Docker daemon isn't running. Start Docker Desktop or run "
        "`open -a Docker` on macOS."
    )),

    # Memory / resource
    (r"ENOMEM|JavaScript heap out of memory", lambda m: (
        "Out of memory. For Node.js, try `NODE_OPTIONS='--max-old-space-size=4096'`. "
        "Consider if the operation can be chunked."
    )),

    # Timeout
    (r"ETIMEDOUT|TimeoutError|timed? ?out", lambda m: (
        "Operation timed out. Check network connectivity, or increase the "
        "timeout if the operation is expected to take long."
    )),
]


def main():
    try:
        hook_input = json.load(sys.stdin)
    except (json.JSONDecodeError, EOFError):
        sys.exit(0)

    # Get the error output from the failed tool
    tool_output = hook_input.get("tool_output", "")
    tool_error = hook_input.get("tool_error", "")
    stderr = hook_input.get("stderr", "")

    # Combine all error text for matching
    error_text = f"{tool_output}\n{tool_error}\n{stderr}"

    if not error_text.strip():
        sys.exit(0)

    # Find first matching hint
    for pattern, hint_fn in ERROR_HINTS:
        match = re.search(pattern, error_text, re.IGNORECASE | re.MULTILINE)
        if match:
            hint = hint_fn(match)
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUseFailure",
                    "additionalContext": f"💡 **Hint**: {hint}",
                }
            }
            print(json.dumps(output))
            sys.exit(0)

    # No matching pattern — no hint
    sys.exit(0)


if __name__ == "__main__":
    main()
