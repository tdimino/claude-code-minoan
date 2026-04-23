# Subagents Reference

Subagents let you define specialized agents for parallel or focused work.

## AgentDefinition

```python
@dataclass
class AgentDefinition:
    description: str                                    # When to use this agent
    prompt: str                                         # Agent's system prompt
    tools: list[str] | None = None                      # Allowed tools (inherits if None)
    model: Literal["sonnet", "opus", "haiku", "inherit"] | None = None
```

### Fields

| Field | Required | Description |
|-------|----------|-------------|
| `description` | Yes | Natural language description for routing |
| `prompt` | Yes | System prompt defining behavior |
| `tools` | No | Tool allowlist (inherits parent if None) |
| `model` | No | Model override (`sonnet`, `opus`, `haiku`, `inherit`) |

---

## Defining Subagents

```python
from claude_agent_sdk import ClaudeAgentOptions, AgentDefinition

options = ClaudeAgentOptions(
    agents={
        "researcher": AgentDefinition(
            description="Research topics using web search",
            prompt="You are a research assistant. Search the web for accurate, up-to-date information.",
            tools=["WebSearch", "WebFetch"],
            model="sonnet"
        ),
        "coder": AgentDefinition(
            description="Write and edit code files",
            prompt="You are an expert programmer. Write clean, well-documented code.",
            tools=["Read", "Write", "Edit", "Bash"],
            model="sonnet"
        ),
        "reviewer": AgentDefinition(
            description="Review code for bugs and improvements",
            prompt="You are a code reviewer. Focus on bugs, security issues, and best practices.",
            tools=["Read", "Glob", "Grep"],
            model="haiku"  # Faster for reviews
        )
    }
)
```

---

## How Subagents Work

1. **Task Tool** - The main agent uses the `Task` tool to spawn subagents
2. **Isolated Context** - Each subagent has its own conversation
3. **Result Return** - Subagent returns a result to the main agent
4. **Parallel Execution** - Multiple subagents can run simultaneously

### Task Tool Schema

```python
{
    "description": str,      # 3-5 word summary
    "prompt": str,           # Task for the subagent
    "subagent_type": str     # Agent name from your definitions
}
```

---

## Use Cases

### Parallelization

Run multiple searches or analyses simultaneously:

```python
options = ClaudeAgentOptions(
    agents={
        "web-searcher": AgentDefinition(
            description="Search the web for information",
            prompt="Search the web and return relevant findings.",
            tools=["WebSearch", "WebFetch"]
        ),
        "file-analyzer": AgentDefinition(
            description="Analyze files in the codebase",
            prompt="Analyze code files and report findings.",
            tools=["Read", "Glob", "Grep"]
        )
    }
)

# Main agent can spawn both in parallel
```

### Context Management

Subagents have isolated context - useful for:
- Processing large documents without bloating main context
- Running focused analyses
- Returning only relevant summaries

```python
options = ClaudeAgentOptions(
    agents={
        "summarizer": AgentDefinition(
            description="Summarize long documents",
            prompt="Read the document and provide a concise summary of key points.",
            tools=["Read"]
        )
    }
)
```

### Specialized Tools

Give different agents different capabilities:

```python
options = ClaudeAgentOptions(
    agents={
        "read-only": AgentDefinition(
            description="Analyze without making changes",
            prompt="Analyze the codebase. Do not make any changes.",
            tools=["Read", "Glob", "Grep"]  # No write tools
        ),
        "writer": AgentDefinition(
            description="Create and edit files",
            prompt="Create or edit files as needed.",
            tools=["Read", "Write", "Edit", "Bash"]
        )
    }
)
```

---

## Complete Example

```python
import asyncio
from claude_agent_sdk import (
    ClaudeSDKClient,
    ClaudeAgentOptions,
    AgentDefinition,
    AssistantMessage,
    TextBlock
)

async def main():
    options = ClaudeAgentOptions(
        agents={
            "researcher": AgentDefinition(
                description="Research topics on the web",
                prompt="""You are a research assistant.
                Search for accurate, current information.
                Return a summary with key facts and sources.""",
                tools=["WebSearch", "WebFetch"],
                model="sonnet"
            ),
            "writer": AgentDefinition(
                description="Write documents and reports",
                prompt="""You are a technical writer.
                Create clear, well-structured documents.
                Use proper formatting and citations.""",
                tools=["Read", "Write"],
                model="sonnet"
            ),
            "reviewer": AgentDefinition(
                description="Review and improve content",
                prompt="""You are an editor.
                Review content for clarity, accuracy, and completeness.
                Suggest improvements.""",
                tools=["Read"],
                model="haiku"
            )
        },
        allowed_tools=["Task", "Read", "Write"]  # Main agent tools
    )

    async with ClaudeSDKClient(options=options) as client:
        # Complex task - main agent will coordinate subagents
        await client.query("""
            Research the latest developments in AI agents,
            write a summary report, and review it for quality.
        """)

        async for message in client.receive_response():
            if isinstance(message, AssistantMessage):
                for block in message.content:
                    if isinstance(block, TextBlock):
                        print(block.text)

asyncio.run(main())
```

---

## Built-in Agent Types

Claude Code includes these built-in subagent types:

| Type | Model | Purpose |
|------|-------|---------|
| **Main Agent** | sonnet/opus | Primary orchestrator |
| **Plan Subagent** | sonnet | Planning and design |
| **Explore Subagent** | haiku | Fast codebase navigation |

The **Explore Subagent** is particularly useful for quick searches:

```python
# Explore uses Haiku for fast, cost-effective navigation
options = ClaudeAgentOptions(
    agents={
        "explorer": AgentDefinition(
            description="Quick codebase exploration",
            prompt="Find relevant files and return summaries.",
            tools=["Glob", "Grep", "Read"],
            model="haiku"  # Fast navigation
        )
    }
)
```

---

## Parallel Execution

### Multiple Perspectives Pattern

Spawn multiple subagents with different viewpoints:

```python
# Parallel code review with specialized perspectives
options = ClaudeAgentOptions(
    agents={
        "security-reviewer": AgentDefinition(
            description="Security and vulnerability analysis",
            prompt="Analyze code for security vulnerabilities, injection risks, data leaks.",
            tools=["Read", "Glob", "Grep"],
            model="haiku"
        ),
        "performance-reviewer": AgentDefinition(
            description="Performance analysis",
            prompt="Identify performance bottlenecks, memory issues, inefficient algorithms.",
            tools=["Read", "Glob", "Grep"],
            model="haiku"
        ),
        "maintainability-reviewer": AgentDefinition(
            description="Code quality review",
            prompt="Review for code smells, duplication, complexity, naming.",
            tools=["Read", "Glob", "Grep"],
            model="haiku"
        )
    }
)

# Main agent spawns all three, then synthesizes findings
```

### Research Coordination Pattern

Coordinate multiple researchers on subtopics:

```python
options = ClaudeAgentOptions(
    agents={
        "researcher": AgentDefinition(
            description="Research a specific topic",
            prompt="""Research the assigned topic thoroughly.
            Save findings to research_output/notes/{topic}.md
            Include key facts, statistics, and sources.""",
            tools=["WebSearch", "WebFetch", "Write", "Read"],
            model="sonnet"
        ),
        "synthesizer": AgentDefinition(
            description="Synthesize research into reports",
            prompt="""Read all research notes and create a comprehensive report.
            Structure with Executive Summary, Key Findings, Analysis.""",
            tools=["Glob", "Read", "Write"],
            model="sonnet"
        )
    }
)

# Main agent: 1) spawn researchers in parallel, 2) spawn synthesizer
```

---

## Background Agents

Run agents asynchronously without blocking:

```python
options = ClaudeAgentOptions(
    agents={
        "background-checker": AgentDefinition(
            description="Run background checks and analysis",
            prompt="Perform analysis and report when complete.",
            tools=["Read", "Glob", "Grep", "Bash"],
            model="haiku"
        )
    }
)

# Main agent can spawn background agent and continue working
# Background agent sends wake message when complete
```

---

## Agent Resumption

Resume previously spawned subagents for stateful interactions:

```python
# TypeScript V2 Session API
const sessionId = session.id;  // Save this

// Later: resume the session
await using session = unstable_v2_resumeSession(sessionId, {
    model: 'sonnet'
});

// Context is preserved
await session.send('What was that file you found earlier?');
```

This is useful for:
- Multi-turn subagent conversations
- Continuing interrupted work
- Building on previous analysis

---

## Subagent Hooks

Track subagent lifecycle with hooks:

### SubagentStart

Called when a subagent is spawned:

```python
async def subagent_start_hook(input_data, tool_use_id, context):
    agent_type = input_data.get("agent_type", "unknown")
    task = input_data.get("task", "")

    print(f"Spawning {agent_type}: {task[:100]}")

    # Track spawned agents
    spawned_agents[tool_use_id] = {
        "type": agent_type,
        "started_at": datetime.now().isoformat()
    }

    return {}
```

### SubagentStop

Called when a subagent completes:

```python
async def subagent_stop_hook(input_data, tool_use_id, context):
    # Access the subagent's transcript
    transcript_path = input_data.get("agent_transcript_path")

    if tool_use_id in spawned_agents:
        agent = spawned_agents[tool_use_id]
        agent["ended_at"] = datetime.now().isoformat()
        agent["transcript"] = transcript_path

    return {}
```

### Hook Registration

```python
hooks = {
    "SubagentStart": [HookMatcher(hooks=[subagent_start_hook])],
    "SubagentStop": [HookMatcher(hooks=[subagent_stop_hook])]
}

options = ClaudeAgentOptions(hooks=hooks)
```

---

## Skills Auto-Loading

Subagents can declare skills to load via YAML frontmatter:

```yaml
# In agent definition or skill file
---
skills:
  - code-review
  - security-analysis
---
```

The agent will automatically have access to these skills.

---

## Best Practices

1. **Clear descriptions** - Help the main agent route tasks correctly
2. **Focused prompts** - Each subagent should have a specific role
3. **Appropriate tools** - Only give tools needed for the task
4. **Model selection** - Use faster models for simple tasks
5. **Context isolation** - Use subagents to manage large contexts
6. **Parallel when possible** - Spawn multiple subagents for independent tasks
7. **Track lifecycle** - Use SubagentStart/SubagentStop hooks for monitoring
8. **File coordination** - Use shared directories for multi-agent output
