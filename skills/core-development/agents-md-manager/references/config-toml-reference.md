# Codex config.toml Reference

## Locations

| Scope | Path | Notes |
|-------|------|-------|
| Global | `~/.codex/config.toml` | User-level defaults |
| Project | `.codex/config.toml` | Project-scoped overrides (trusted projects only) |

Project configs walk from project root to CWD. Closest file wins for conflicting keys.

## Core Settings

| Key | Type | Description |
|-----|------|-------------|
| `model` | string | Model to use (e.g., `gpt-5.3-codex`) |
| `model_reasoning_effort` | `minimal\|low\|medium\|high\|xhigh` | Reasoning depth for supported models |
| `model_reasoning_summary` | `auto\|concise\|detailed\|none` | Reasoning summary detail |
| `model_verbosity` | `low\|medium\|high` | Response length (Responses API only) |
| `model_context_window` | number | Context window size in tokens |
| `personality` | `none\|friendly\|pragmatic` | Communication style |
| `approval_policy` | `untrusted\|on-failure\|on-request\|never` | When to pause for approval |
| `sandbox_mode` | `read-only\|workspace-write\|danger-full-access` | Filesystem/network access |
| `file_opener` | `vscode\|cursor\|windsurf\|vscode-insiders\|none` | URI scheme for citations |

## Profiles

Named configuration presets. Switch via `codex --profile <name>`.

```toml
model = "gpt-5-codex"
approval_policy = "on-request"

[profiles.deep-review]
model = "gpt-5-pro"
model_reasoning_effort = "high"
approval_policy = "never"

[profiles.lightweight]
model = "gpt-4.1"
approval_policy = "untrusted"
```

Set a default profile: `profile = "deep-review"` at top level.

## Model Providers

```toml
model_provider = "proxy"

[model_providers.proxy]
name = "OpenAI via LLM proxy"
base_url = "http://proxy.example.com"
env_key = "OPENAI_API_KEY"
wire_api = "responses"          # or "chat"
request_max_retries = 4
stream_max_retries = 10
stream_idle_timeout_ms = 300000
```

OSS mode: `codex --oss` uses `oss_provider` (default: `ollama` or `lmstudio`).

## MCP Servers

```toml
[mcp_servers.playwright]
command = "/opt/homebrew/bin/npx"
args = ["-y", "@playwright/mcp@latest"]
startup_timeout_ms = 20000
enabled = true
required = false

[mcp_servers.custom]
url = "https://example.com/mcp"     # Streamable HTTP transport
bearer_token_env_var = "MCP_TOKEN"
```

Keys: `command`, `args`, `cwd`, `env`, `url`, `enabled`, `required`, `startup_timeout_ms`, `tool_timeout_sec`, `enabled_tools`, `disabled_tools`, `env_vars`, `http_headers`, `env_http_headers`.

## Project Trust

```toml
[projects."/path/to/repo"]
trust_level = "trusted"    # or "untrusted"
```

Untrusted projects skip `.codex/config.toml` loading.

## Sandbox Settings

```toml
[sandbox_workspace_write]
exclude_tmpdir_env_var = false
exclude_slash_tmp = false
writable_roots = ["/Users/YOU/.pyenv/shims"]
network_access = false
```

## Shell Environment

```toml
[shell_environment_policy]
inherit = "none"                          # or "core"
set = { PATH = "/usr/bin", MY_FLAG = "1" }
exclude = ["AWS_*", "AZURE_*"]
include_only = ["PATH", "HOME"]
ignore_default_excludes = false
```

## AGENTS.md Discovery

```toml
project_doc_max_bytes = 32768
project_doc_fallback_filenames = ["TEAM_GUIDE.md", ".agents.md"]
project_root_markers = [".git", ".hg"]
```

## Skills Configuration

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = false
```

## Notifications

```toml
notify = ["python3", "/path/to/notify.py"]

[tui]
notifications = true
notification_method = "auto"    # or "osc9", "bel"
animations = true
alternate_screen = "auto"       # or "never"
```

## Observability

```toml
[otel]
environment = "staging"
exporter = "none"               # or otlp-http, otlp-grpc
log_user_prompt = false

[analytics]
enabled = true

[feedback]
enabled = true
```

## History

```toml
[history]
persistence = "save-all"    # or "none"
max_bytes = 104857600       # 100 MiB cap
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `CODEX_HOME` | Override config directory (default `~/.codex`) |
| `OPENAI_API_KEY` | API authentication |
| `OPENAI_BASE_URL` | Override default endpoint |
