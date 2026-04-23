# Permissions Reference

Control what tools can do with permission modes and custom handlers.

## Permission Modes

```python
PermissionMode = Literal[
    "default",           # Standard permission behavior
    "acceptEdits",       # Auto-accept file edits
    "plan",              # Planning mode - no execution
    "bypassPermissions"  # Bypass all checks (use with caution)
]
```

### Mode Descriptions

| Mode | Description | Use Case |
|------|-------------|----------|
| `default` | Standard prompts for permissions | Interactive applications |
| `acceptEdits` | Auto-approve file operations | Automated scripts |
| `plan` | Read-only, no execution | Planning and analysis |
| `bypassPermissions` | Skip all checks | Trusted automation |

### Usage

```python
from claude_agent_sdk import query, ClaudeAgentOptions

options = ClaudeAgentOptions(
    permission_mode="acceptEdits",  # Auto-approve file edits
    allowed_tools=["Read", "Write", "Edit"]
)
```

---

## Custom Permission Handler: can_use_tool

For fine-grained control, implement a custom permission callback:

```python
async def can_use_tool(
    tool_name: str,
    input_data: dict,
    context: dict
) -> dict:
    # Return permission decision
    return {
        "behavior": "allow" | "deny",
        "message": str | None,        # Reason for deny
        "interrupt": bool | None,     # Stop execution on deny
        "updatedInput": dict | None   # Modified tool input
    }
```

### Return Values

| Key | Type | Description |
|-----|------|-------------|
| `behavior` | `"allow" \| "deny"` | Permission decision |
| `message` | `str` | Reason (shown to user) |
| `interrupt` | `bool` | Stop execution if denied |
| `updatedInput` | `dict` | Modified input (for redirects) |

---

## Examples

### Block System Directories

```python
async def safe_file_handler(
    tool_name: str,
    input_data: dict,
    context: dict
):
    if tool_name in ["Write", "Edit"]:
        path = input_data.get("file_path", "")

        # Block system directories
        blocked_paths = ["/system/", "/etc/", "/usr/", "/bin/"]
        if any(path.startswith(p) for p in blocked_paths):
            return {
                "behavior": "deny",
                "message": "System directory modification not allowed",
                "interrupt": True
            }

    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(
    can_use_tool=safe_file_handler,
    allowed_tools=["Read", "Write", "Edit"]
)
```

### Sandbox File Operations

Redirect writes to a sandbox directory:

```python
async def sandbox_handler(
    tool_name: str,
    input_data: dict,
    context: dict
):
    if tool_name in ["Write", "Edit"]:
        original_path = input_data.get("file_path", "")

        # Skip if already in sandbox
        if original_path.startswith("./sandbox/"):
            return {"behavior": "allow", "updatedInput": input_data}

        # Redirect to sandbox
        safe_path = f"./sandbox/{original_path.lstrip('/')}"
        return {
            "behavior": "allow",
            "updatedInput": {**input_data, "file_path": safe_path}
        }

    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(can_use_tool=sandbox_handler)
```

### Rate Limiting

```python
from datetime import datetime, timedelta

call_history = {}

async def rate_limit_handler(
    tool_name: str,
    input_data: dict,
    context: dict
):
    now = datetime.now()

    # Clean old entries
    cutoff = now - timedelta(minutes=1)
    call_history[tool_name] = [
        t for t in call_history.get(tool_name, [])
        if t > cutoff
    ]

    # Check rate limit (10 calls per minute per tool)
    if len(call_history.get(tool_name, [])) >= 10:
        return {
            "behavior": "deny",
            "message": f"Rate limit exceeded for {tool_name}",
            "interrupt": False  # Allow retry later
        }

    # Record this call
    call_history.setdefault(tool_name, []).append(now)
    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(can_use_tool=rate_limit_handler)
```

### Allowlist Pattern

```python
ALLOWED_COMMANDS = [
    "ls", "cat", "grep", "find", "pwd",
    "git status", "git log", "git diff"
]

async def command_allowlist(
    tool_name: str,
    input_data: dict,
    context: dict
):
    if tool_name == "Bash":
        command = input_data.get("command", "")

        # Check if command starts with allowed prefix
        allowed = any(
            command.startswith(cmd)
            for cmd in ALLOWED_COMMANDS
        )

        if not allowed:
            return {
                "behavior": "deny",
                "message": f"Command not in allowlist: {command}",
                "interrupt": True
            }

    return {"behavior": "allow", "updatedInput": input_data}

options = ClaudeAgentOptions(can_use_tool=command_allowlist)
```

---

## Combining with Hooks

Use `can_use_tool` for permission decisions and hooks for logging/modification:

```python
async def permission_handler(tool_name, input_data, context):
    # Permission logic
    return {"behavior": "allow", "updatedInput": input_data}

async def audit_hook(input_data, tool_use_id, context):
    # Logging logic
    print(f"Tool: {input_data['tool_name']}")
    return {}

options = ClaudeAgentOptions(
    can_use_tool=permission_handler,
    hooks={
        "PreToolUse": [HookMatcher(hooks=[audit_hook])]
    }
)
```

---

## Best Practices

1. **Fail closed** - Deny by default for sensitive operations
2. **Log decisions** - Keep audit trail of denials
3. **Provide reasons** - Help users understand denials
4. **Use interrupt wisely** - Only stop execution for critical issues
5. **Validate paths** - Canonicalize paths before checking
6. **Combine approaches** - Use modes + can_use_tool + hooks together
