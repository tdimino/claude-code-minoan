# Codex CLI Reference

> Last updated: 2026-04-21 | Covers Codex CLI through v0.122.0

Complete reference for OpenAI Codex CLI commands and options.

## Installation

```bash
npm install -g @openai/codex
# or
brew install --cask codex
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
codex exec --model gpt-5-mini "Review this file"
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
codex fork <session_id>                # Fork a previous session
codex cloud                            # Browse Codex Cloud tasks
codex features                         # Inspect feature flags
codex review                           # Non-interactive code review
codex sandbox                          # Run commands in sandbox
codex plugins                          # List installed plugins
codex plugin install <name>            # Install a Codex plugin
```

## Options

### Model Selection

```bash
-m, --model <MODEL>                    # Select model
    --model gpt-5.4                    # Flagship — coding + reasoning unified
    --model gpt-5.4-pro                # Deeper reasoning, hardest problems
    --model gpt-5-mini                 # Cost-optimized, fast iteration
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
    --ask-for-approval untrusted       # Ask for non-trusted commands (default)
    --ask-for-approval on-failure      # Only ask if command fails
    --ask-for-approval on-request      # Barely ever ask (used by --full-auto)
    --ask-for-approval never           # Never ask for approval

--full-auto                            # Convenience: -a on-request + --sandbox workspace-write
```

**Important**: In non-interactive `exec` mode, the default `untrusted` policy blocks writes since there's no TUI to approve them. Use `--full-auto` for unattended write operations.

### Configuration

```bash
-c, --config <key=value>               # Override config
    -c model="gpt-5.4"                   # Set model
    -c 'sandbox_permissions=["disk-full-read-access"]'
```

### Profile Selection

```bash
-p, --profile <PROFILE>                # Use config profile
    --profile reviewer                 # From config.toml [profile.reviewer]
```

### Exec-Specific Options

```bash
--add-dir <DIR>                        # Additional writable directories alongside workspace
-C, --cd <DIR>                         # Set agent working root directory
--output-schema <FILE>                 # JSON Schema for structured model output
--skip-git-repo-check                  # Allow running outside git repos
--progress-cursor                      # Force cursor-based progress display
--ephemeral                            # Don't save session state
-o, --output <FILE>                    # Write output to file
```

### Other Options

```bash
-i, --image <FILE>                     # Attach image(s) to prompt
    --oss                              # Use local Ollama model
--enable <FEATURE>                     # Enable a feature flag
--disable <FEATURE>                    # Disable a feature flag
```

## Configuration File

Located at `~/.codex/config.toml`:

```toml
# Default settings
model = "gpt-5.4"
sandbox = "workspace-write"

# Custom profiles
[profile.reviewer]
model = "gpt-5.4"

[profile.quick]
model = "gpt-5-mini"
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
codex --model gpt-5.4 "Design a caching system"

# Read-only analysis
codex --sandbox read-only "Analyze the codebase architecture"
```

## Recent Features (v0.110.0–v0.122.0)

| Version | Feature | Description |
|---------|---------|-------------|
| v0.110.0 | Plugin system | `codex plugins` / `codex plugin install <name>` — extensible plugin architecture |
| v0.110.0 | `/fast` toggle | Switch to faster output mode mid-session |
| v0.110.0 | Improved memories | Better cross-session context recall |
| v0.115.0 | Smart Approvals | Guardian subagent evaluates command safety before prompting |
| v0.115.0 | Full-resolution `view_image` | Vision input at native resolution (no downscaling) |
| v0.116.0 | `userpromptsubmit` hook | Hook fires when user submits a prompt (for preprocessing/logging) |
| v0.117.0 | Sub-agent addressing | Send messages to specific sub-agents by name |
| v0.122.0 | `/side` conversations | Start parallel side conversations without losing main context |
| v0.122.0 | Plan Mode improvements | Better plan editing, approval flow, and execution tracking |
| v0.122.0 | Deny-read glob policies | `deny_file_read_patterns` in config blocks reads of sensitive file paths |
