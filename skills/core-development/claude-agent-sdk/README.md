# Claude Agent SDK

The agent builder's toolkit. Teaches Claude how to create autonomous AI agents using the Claude Agent SDK---the same tools that power Claude Code, packaged for programmatic use.

**Last updated:** 2026-02-18

**Reflects:** Claude Agent SDK v1.x (Python + TypeScript), Anthropic's Claude 4.6 agent patterns, and production agent architectures from Claudicle and Aldea.

---

## Why This Skill Exists

The Claude Agent SDK lets you build agents that read files, run commands, search the web, edit code, and verify their work---all using the same tool infrastructure as Claude Code itself. But the SDK surface is broad: two query paradigms, 12+ built-in tools, hooks, permissions, subagents, browser control, MCP servers, and thinking configuration. Without a map, builders waste time discovering what's available and how the pieces fit together.

This skill provides that map: 10 reference docs covering every SDK feature, 7 ready-to-run templates, and 3 step-by-step workflow guides. The SKILL.md routes users to the right document based on what they're trying to build.

---

## Structure

```
claude-agent-sdk/
  SKILL.md                                 # Intake routing + quick reference
  README.md                                # This file
  references/
    best-practices.md                      # Agent design patterns and anti-patterns
    browser-control.md                     # Chrome extension, dev-browser, Browserbase
    built-in-tools.md                      # All 12+ tools with parameters and examples
    custom-tools.md                        # @tool decorator, MCP server integration
    hooks.md                               # PreToolUse, PostToolUse, stop hooks
    message-types.md                       # Message, ContentBlock, streaming types
    permissions.md                         # Permission modes and can_use_tool callbacks
    python-sdk.md                          # Full Python API reference
    subagents.md                           # AgentDefinition, parallel agents, Task tool
    troubleshooting.md                     # Error types, common issues, debugging
  templates/
    simple-agent-python.py                 # Minimal query() example
    continuous-chat-python.py              # ClaudeSDKClient with follow-ups
    custom-tool-python.py                  # @tool decorator pattern
    hook-example-python.py                 # PreToolUse/PostToolUse hooks
    research-agent-python.py               # WebSearch + WebFetch agent
    agent-with-tracking-python.py          # Agent with progress tracking
    session-api-typescript.ts              # TypeScript session API example
  workflows/
    create-agent.md                        # Build an agent from scratch
    add-custom-tools.md                    # Add tools via @tool or MCP
    add-hooks.md                           # Add behavior hooks
```

---

## What It Covers

### Two Query Paradigms

| Paradigm | Session | Hooks | Custom Tools | Best For |
|----------|---------|-------|-------------|----------|
| `query()` | New each call | No | No | One-off tasks, automation scripts |
| `ClaudeSDKClient` | Continuous | Yes | Yes | Conversations, follow-ups, complex agents |

`query()` is simpler but stateless. `ClaudeSDKClient` maintains context across turns and supports the full feature set.

### Built-in Tools

| Tool | Purpose |
|------|---------|
| `Read` | Read files (text, images, PDFs, notebooks) |
| `Write` | Create new files |
| `Edit` | Modify existing files with search/replace |
| `Bash` | Run terminal commands |
| `Glob` | Find files by pattern (`**/*.ts`) |
| `Grep` | Search file contents with regex |
| `WebSearch` | Search the web |
| `WebFetch` | Fetch and parse web pages |
| `Task` | Spawn subagents for parallel work |
| `NotebookEdit` | Edit Jupyter notebooks |
| `TodoWrite` | Manage task lists |
| `KillShell` | Kill background shells |

Control via `allowed_tools` (whitelist) or `disallowed_tools` (blacklist) in `ClaudeAgentOptions`.

### Permission Modes

| Mode | Behavior |
|------|----------|
| `default` | Prompts user for tool approval |
| `acceptEdits` | Auto-approves file edits, prompts for Bash |
| `plan` | Requires plan approval before execution |
| `bypassPermissions` | No prompts (use for trusted automation only) |

Fine-grained control via `can_use_tool` callback for custom permission logic.

### Hooks

Intercept and modify tool behavior at two points:
- **PreToolUse**: Validate, modify, or block tool calls before execution
- **PostToolUse**: Process results, log actions, trigger side effects

### Subagents

Define specialized agents via `AgentDefinition` and spawn them with the `Task` tool. Each subagent gets its own context, tools, and system prompt. Use for parallel research, code review, or any task that benefits from isolation.

### Browser Control

Three approaches: Chrome extension (control user's browser), dev-browser skill (headless automation), and Browserbase (cloud browser instances). See `references/browser-control.md`.

### Thinking Configuration

| Use Case | Effort Level |
|----------|-------------|
| Quick lookups, simple edits | `low` |
| Standard development | `medium` |
| Complex architecture, security | `high` |
| Deep research, long-horizon | `max` |

Avoid "think carefully" in system prompts---Claude 4.6 calibrates thinking depth automatically.

### Error Types

| Error | Cause |
|-------|-------|
| `CLINotFoundError` | Claude Code CLI not installed |
| `CLIConnectionError` | Connection to CLI failed |
| `ProcessError` | CLI process exited with error |
| `CLIJSONDecodeError` | Response JSON parsing failed |

---

## Templates

| Template | Language | Pattern |
|----------|----------|---------|
| `simple-agent-python.py` | Python | Minimal `query()` one-shot |
| `continuous-chat-python.py` | Python | `ClaudeSDKClient` with follow-ups |
| `custom-tool-python.py` | Python | `@tool` decorator |
| `hook-example-python.py` | Python | PreToolUse/PostToolUse |
| `research-agent-python.py` | Python | WebSearch + WebFetch |
| `agent-with-tracking-python.py` | Python | Progress tracking |
| `session-api-typescript.ts` | TypeScript | Session API |

---

## Workflows

Three step-by-step guides for common tasks:

| Workflow | What It Covers |
|----------|---------------|
| `create-agent.md` | Build an agent from scratch: choose paradigm, configure tools, set permissions |
| `add-custom-tools.md` | Create tools via `@tool` decorator or connect MCP servers |
| `add-hooks.md` | Add PreToolUse/PostToolUse hooks for logging, validation, modification |

---

## Requirements

- Claude Code CLI installed (`npm install -g @anthropic-ai/claude-code`)
- `ANTHROPIC_API_KEY` environment variable set
- Python 3.10+ or Node.js 18+ depending on language choice
- `claude-agent-sdk` package (`uv add claude-agent-sdk` or `npm install @anthropic-ai/claude-agent-sdk`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/core-development/claude-agent-sdk ~/.claude/skills/
```
