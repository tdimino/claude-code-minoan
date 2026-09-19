# Codex CLI Reference

> Last updated: 2026-09-19 | Covers Codex CLI through v0.155.1

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

#### Prompt and stdin resolution (`codex-rs/exec/src/lib.rs`, `StdinPromptBehavior`)

| Invocation | stdin is a terminal | stdin is piped or `/dev/null` |
|------------|---------------------|-------------------------------|
| No prompt argument | Error: "No prompt provided" | Reads stdin as the prompt (`Reading prompt from stdin...`); empty input exits 1 with `No prompt provided via stdin.` |
| Prompt is `-` | Reads stdin as the prompt | Reads stdin as the prompt |
| Prompt argument present | Ignores stdin | Reads stdin to EOF (`Reading additional input from stdin...`) and appends it as a `<stdin>` block; empty input is ignored |

Consequences for launchers: always redirect `</dev/null` so the read returns immediately (an open pipe with no EOF hangs, openai/codex#27019), and always terminate options with `--` before the prompt, because `-i/--image` is variadic (`num_args = 1..`, comma-delimited) and otherwise consumes the prompt as another image path:

```bash
codex exec --skip-git-repo-check -s read-only -i shot.png -- "Describe the screenshot" </dev/null
codex exec --skip-git-repo-check resume --last -i shot.png -- "Continue" </dev/null   # -i after the subcommand
```

Unchanged from v0.154.0 through v0.155.1 (the exec crate is byte-identical across those tags).

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
    --model gpt-5.6-sol                 # Flagship — reasoning, agentic workflows
    --model gpt-5.6-terra              # Balanced — everyday work, half Sol cost
    --model gpt-5.6-luna               # Cost-optimized, fastest throughput
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
    --ask-for-approval on-request      # Barely ever ask
    --ask-for-approval never           # Never ask for approval

--full-auto                            # DEPRECATED (PR #20133, 2026-04-29). Causes hangs (Issue #7852).
                                       # Use: -a never --sandbox workspace-write
```

**Important**: In `codex exec` mode, `--sandbox workspace-write` automatically sets `approval: never`. No separate approval flag is needed. Pipe `/dev/null` into stdin as a safety net against interactive prompts.

### Configuration

```bash
-c, --config <key=value>               # Override config
    -c model="gpt-5.6-sol"                # Set model
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
-i, --image <FILE>...                  # Attach image(s) to prompt; variadic and comma-split,
                                       # so follow it with `--` before a positional prompt
    --oss                              # Use local Ollama model
--enable <FEATURE>                     # Enable a feature flag
--disable <FEATURE>                    # Disable a feature flag
```

## Configuration File

Located at `~/.codex/config.toml`:

```toml
# Default settings
model = "gpt-5.6-sol"
sandbox = "workspace-write"

# Custom profiles
[profile.reviewer]
model = "gpt-5.6-sol"

[profile.quick]
model = "gpt-5.6-luna"
sandbox = "read-only"
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | API authentication |
| `CODEX_CONFIG` | Path to config file |
| `CODEX_HOME` | Codex home directory |

## AGENTS.md

Codex reads a layered instruction chain: global guidance from `CODEX_HOME`, then one project instruction file per directory from the project root down to the current directory. `AGENTS.override.md` takes precedence over `AGENTS.md` within a directory. The orchestrator adds its role without mutating that chain:

```bash
codex exec -c 'developer_instructions=# Reviewer persona' "Review this patch"
```

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
codex --model gpt-5.6-sol "Design a caching system"

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
| v0.155.0 | `/voice` conversations | Experimental live transcripts and microphone controls via `/experimental` |
| v0.155.0 | Touch ID for MCP | Secure Enclave user verification for MCP requests in local TUI sessions |
| v0.155.0 | Daemon update command | `codex app-server daemon update` plus configurable update schedules |
| v0.155.1 | TUI reasoning summary default | Only change in the release: new TUI sessions leave reasoning summaries off (#46467). No exec, stdin, or PTY changes |
