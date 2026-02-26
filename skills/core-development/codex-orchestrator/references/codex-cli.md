# Codex CLI Reference

Complete reference for OpenAI Codex CLI commands and options.

## Installation

```bash
npm install -g @openai/codex
```

## Authentication

Set the OpenAI API key:

```bash
export OPENAI_API_KEY=sk-...
```

Or use the login command:

```bash
codex login
```

## Commands

### Interactive Mode (default)

```bash
codex [PROMPT]
codex "Fix the bug in auth.ts"
```

Launches the interactive TUI with optional initial prompt.

### Non-Interactive Execution

```bash
codex exec "<prompt>"
codex exec --model gpt-5.3-codex-spark "Review this file"
codex e "Quick task"  # alias
```

Runs Codex without the TUI, outputs result to stdout.

### Session Management

```bash
codex resume <session_id>              # Resume previous session
codex resume <session_id> --message "Continue with..."
```

### MCP Server Mode

```bash
codex mcp                              # Start as MCP server
codex mcp-server                       # Alias
```

Exposes tools: `codex` (start session), `codex-reply` (continue session).

### Other Commands

```bash
codex apply                            # Apply latest diff to working tree
codex completion bash                  # Generate shell completions
codex debug                            # Internal debugging commands
```

## Options

### Model Selection

```bash
-m, --model <MODEL>                    # Select model
    --model gpt-5.3-codex              # Latest, fastest, most capable
    --model gpt-5.3-codex-spark        # Lighter, near-instant
    --model gpt-5.2-codex              # Previous generation
```

### Sandbox Modes

```bash
-s, --sandbox <MODE>
    --sandbox read-only                # Can only read files
    --sandbox workspace-write          # Can write to workspace
    --sandbox danger-full-access       # Full system access
```

### Approval Policies

```bash
-a, --ask-for-approval <POLICY>
    --ask-for-approval untrusted       # Ask for non-trusted commands
    --ask-for-approval on-failure      # Only ask if command fails
```

### Configuration

```bash
-c, --config <key=value>               # Override config
    -c model="gpt-5.3-codex"            # Set model
    -c 'sandbox_permissions=["disk-full-read-access"]'
```

### Profile Selection

```bash
-p, --profile <PROFILE>                # Use config profile
    --profile reviewer                 # From config.toml [profile.reviewer]
```

### Other Options

```bash
-i, --image <FILE>                     # Attach image(s) to prompt
    --oss                              # Use local Ollama model
```

## Configuration File

Located at `~/.codex/config.toml`:

```toml
# Default settings
model = "gpt-5.3-codex"
sandbox = "workspace-write"

# Custom profiles
[profile.reviewer]
model = "gpt-5.3-codex"

[profile.quick]
model = "gpt-5.3-codex-spark"
sandbox = "read-only"
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | API authentication |
| `CODEX_AGENTS_FILE` | Path to custom AGENTS.md |
| `CODEX_CONFIG` | Path to config file |
| `CODEX_HOME` | Codex home directory |

## AGENTS.md

Codex reads `AGENTS.md` from the current directory to customize agent behavior.

```markdown
# Agent Name

You are a specialized agent for...

## Focus Areas
- Area 1
- Area 2

## Output Format
How to structure responses
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Authentication error |
| 4 | API error |

## Examples

```bash
# Quick code review
codex exec "Review src/auth.ts for security issues"

# Interactive debugging session
codex "Help me debug the login failure"

# Full-auto mode (no approval prompts)
codex exec --ask-for-approval on-failure "Fix all lint errors"

# Use specific model
codex --model gpt-5.3-codex "Design a caching system"

# Read-only analysis
codex --sandbox read-only "Analyze the codebase architecture"
```
