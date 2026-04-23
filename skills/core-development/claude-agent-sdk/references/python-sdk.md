# Python SDK Reference

## Installation

```bash
uv add claude-agent-sdk
```

## Core Functions

### `query()`

Creates a new session for each interaction. Returns an async iterator yielding messages.

```python
async def query(
    *,
    prompt: str | AsyncIterable[dict[str, Any]],
    options: ClaudeAgentOptions | None = None
) -> AsyncIterator[Message]
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `prompt` | `str \| AsyncIterable[dict]` | Input prompt or async stream |
| `options` | `ClaudeAgentOptions \| None` | Configuration (defaults if None) |

**Example:**

```python
import asyncio
from claude_agent_sdk import query, ClaudeAgentOptions

async def main():
    options = ClaudeAgentOptions(
        system_prompt="You are an expert Python developer",
        permission_mode='acceptEdits',
        cwd="/home/user/project"
    )

    async for message in query(
        prompt="Create a Python web server",
        options=options
    ):
        print(message)

asyncio.run(main())
```

### `tool()`

Decorator for defining MCP tools with type safety.

```python
def tool(
    name: str,
    description: str,
    input_schema: type | dict[str, Any]
) -> Callable[[Callable[[Any], Awaitable[dict[str, Any]]]], SdkMcpTool[Any]]
```

**Input Schema Options:**

1. **Simple type mapping** (recommended):
   ```python
   {"text": str, "count": int, "enabled": bool}
   ```

2. **JSON Schema format**:
   ```python
   {
       "type": "object",
       "properties": {
           "text": {"type": "string"},
           "count": {"type": "integer", "minimum": 0}
       },
       "required": ["text"]
   }
   ```

**Example:**

```python
from claude_agent_sdk import tool
from typing import Any

@tool("greet", "Greet a user", {"name": str})
async def greet(args: dict[str, Any]) -> dict[str, Any]:
    return {
        "content": [{
            "type": "text",
            "text": f"Hello, {args['name']}!"
        }]
    }
```

### `create_sdk_mcp_server()`

Create an in-process MCP server.

```python
def create_sdk_mcp_server(
    name: str,
    version: str = "1.0.0",
    tools: list[SdkMcpTool[Any]] | None = None
) -> McpSdkServerConfig
```

**Example:**

```python
from claude_agent_sdk import tool, create_sdk_mcp_server, ClaudeAgentOptions

@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {
        "content": [{
            "type": "text",
            "text": f"Sum: {args['a'] + args['b']}"
        }]
    }

calculator = create_sdk_mcp_server(
    name="calculator",
    version="2.0.0",
    tools=[add]
)

options = ClaudeAgentOptions(
    mcp_servers={"calc": calculator},
    allowed_tools=["mcp__calc__add"]
)
```

---

## ClaudeSDKClient Class

Maintains a conversation session across multiple exchanges.

### Methods

```python
class ClaudeSDKClient:
    def __init__(self, options: ClaudeAgentOptions | None = None)
    async def connect(self, prompt: str | AsyncIterable[dict] | None = None) -> None
    async def query(self, prompt: str | AsyncIterable[dict], session_id: str = "default") -> None
    async def receive_messages(self) -> AsyncIterator[Message]
    async def receive_response(self) -> AsyncIterator[Message]
    async def interrupt(self) -> None
    async def rewind_files(self, user_message_uuid: str) -> None
    async def disconnect(self) -> None
```

| Method | Description |
|--------|-------------|
| `__init__(options)` | Initialize with optional configuration |
| `connect(prompt)` | Connect with optional initial prompt |
| `query(prompt, session_id)` | Send new request in streaming mode |
| `receive_messages()` | Receive all messages as async iterator |
| `receive_response()` | Receive until ResultMessage |
| `interrupt()` | Send interrupt signal |
| `rewind_files(uuid)` | Restore files to state at message |
| `disconnect()` | Disconnect from Claude |

### Context Manager Support

```python
async with ClaudeSDKClient() as client:
    await client.query("Hello Claude")
    async for message in client.receive_response():
        print(message)
```

> **Important:** Avoid using `break` to exit early from message iteration - this can cause asyncio cleanup issues.

### Continuing Conversations

```python
async with ClaudeSDKClient() as client:
    # First question
    await client.query("What's the capital of France?")
    async for message in client.receive_response():
        if isinstance(message, AssistantMessage):
            for block in message.content:
                if isinstance(block, TextBlock):
                    print(f"Claude: {block.text}")

    # Follow-up - Claude remembers context
    await client.query("What's the population of that city?")
    async for message in client.receive_response():
        # ...
```

### Streaming Input

```python
async def message_stream():
    yield {"type": "text", "text": "Analyze this:"}
    await asyncio.sleep(0.5)
    yield {"type": "text", "text": "Temperature: 25C"}

async with ClaudeSDKClient() as client:
    await client.query(message_stream())
    async for message in client.receive_response():
        print(message)
```

### Using Interrupts

```python
async with ClaudeSDKClient(options) as client:
    await client.query("Count from 1 to 100 slowly")
    await asyncio.sleep(2)
    await client.interrupt()
    print("Task interrupted!")

    # Send new command
    await client.query("Just say hello")
    async for message in client.receive_response():
        pass
```

---

## ClaudeAgentOptions

Complete configuration dataclass:

```python
@dataclass
class ClaudeAgentOptions:
    allowed_tools: list[str] = field(default_factory=list)
    system_prompt: str | SystemPromptPreset | None = None
    mcp_servers: dict[str, McpServerConfig] | str | Path = field(default_factory=dict)
    permission_mode: PermissionMode | None = None
    continue_conversation: bool = False
    resume: str | None = None
    max_turns: int | None = None
    disallowed_tools: list[str] = field(default_factory=list)
    enable_file_checkpointing: bool = False
    model: str | None = None
    output_format: OutputFormat | None = None
    permission_prompt_tool_name: str | None = None
    cwd: str | Path | None = None
    settings: str | None = None
    add_dirs: list[str | Path] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    extra_args: dict[str, str | None] = field(default_factory=dict)
    max_buffer_size: int | None = None
    stderr: Callable[[str], None] | None = None
    can_use_tool: CanUseTool | None = None
    hooks: dict[HookEvent, list[HookMatcher]] | None = None
    user: str | None = None
    include_partial_messages: bool = False
    fork_session: bool = False
    agents: dict[str, AgentDefinition] | None = None
    plugins: list[SdkPluginConfig] = field(default_factory=list)
    sandbox: SandboxSettings | None = None
    setting_sources: list[SettingSource] | None = None
```

### Key Properties

| Property | Type | Description |
|----------|------|-------------|
| `allowed_tools` | `list[str]` | Tools to enable |
| `system_prompt` | `str \| SystemPromptPreset` | Custom or preset prompt |
| `mcp_servers` | `dict[str, McpServerConfig]` | MCP server configs |
| `permission_mode` | `PermissionMode` | Permission handling |
| `max_turns` | `int` | Max conversation turns |
| `cwd` | `str \| Path` | Working directory |
| `can_use_tool` | `CanUseTool` | Permission callback |
| `hooks` | `dict[HookEvent, list[HookMatcher]]` | Hook configs |
| `agents` | `dict[str, AgentDefinition]` | Subagent definitions |
| `sandbox` | `SandboxSettings` | Sandbox configuration |
| `setting_sources` | `list[SettingSource]` | Settings to load |

### SystemPromptPreset

Use Claude Code's system prompt with optional additions:

```python
ClaudeAgentOptions(
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": "Focus on Python code"
    }
)
```

### SettingSource

Control which filesystem settings to load:

```python
SettingSource = Literal["user", "project", "local"]
```

| Value | Location |
|-------|----------|
| `"user"` | `~/.claude/settings.json` |
| `"project"` | `.claude/settings.json` |
| `"local"` | `.claude/settings.local.json` |

```python
# Load CLAUDE.md files
ClaudeAgentOptions(
    system_prompt={"type": "preset", "preset": "claude_code"},
    setting_sources=["project"]  # Required for CLAUDE.md
)
```

---

## Permission Modes

```python
PermissionMode = Literal[
    "default",           # Standard permission behavior
    "acceptEdits",       # Auto-accept file edits
    "plan",              # Planning mode - no execution
    "bypassPermissions"  # Bypass all checks (use with caution)
]
```

---

## AgentDefinition

Configuration for subagents:

```python
@dataclass
class AgentDefinition:
    description: str
    prompt: str
    tools: list[str] | None = None
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
```

---

## MCP Server Configs

### McpStdioServerConfig

```python
class McpStdioServerConfig(TypedDict):
    type: NotRequired[Literal["stdio"]]
    command: str
    args: NotRequired[list[str]]
    env: NotRequired[dict[str, str]]
```

### McpSSEServerConfig

```python
class McpSSEServerConfig(TypedDict):
    type: Literal["sse"]
    url: str
    headers: NotRequired[dict[str, str]]
```

### McpHttpServerConfig

```python
class McpHttpServerConfig(TypedDict):
    type: Literal["http"]
    url: str
    headers: NotRequired[dict[str, str]]
```

### McpSdkServerConfig

```python
class McpSdkServerConfig(TypedDict):
    type: Literal["sdk"]
    name: str
    instance: Any  # MCP Server instance
```

---

## Sandbox Settings

```python
class SandboxSettings(TypedDict, total=False):
    enabled: bool
    autoAllowBashIfSandboxed: bool
    excludedCommands: list[str]
    allowUnsandboxedCommands: bool
    network: SandboxNetworkConfig
    ignoreViolations: SandboxIgnoreViolations
    enableWeakerNestedSandbox: bool
```

### SandboxNetworkConfig

```python
class SandboxNetworkConfig(TypedDict, total=False):
    allowLocalBinding: bool
    allowUnixSockets: list[str]
    allowAllUnixSockets: bool
    httpProxyPort: int
    socksProxyPort: int
```

**Example:**

```python
sandbox_settings = {
    "enabled": True,
    "autoAllowBashIfSandboxed": True,
    "excludedCommands": ["docker"],
    "network": {
        "allowLocalBinding": True,
        "allowUnixSockets": ["/var/run/docker.sock"]
    }
}

options = ClaudeAgentOptions(sandbox=sandbox_settings)
```
