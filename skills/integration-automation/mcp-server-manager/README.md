# MCP Server Manager

Configure and manage MCP (Model Context Protocol) servers in Claude Code. Add, remove, list, and troubleshoot MCP servers across three scopes (local, project, user) with support for HTTP, SSE, and stdio transports, OAuth authentication, and environment variable expansion.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

MCP servers connect Claude Code to external tools, databases, and APIs, but the configuration surface is wide: three transport types, three scopes, OAuth flows, header auth, environment variables, and JSON imports. This skill consolidates the full `claude mcp` CLI reference and troubleshooting into one place.

---

## Structure

```
mcp-server-manager/
  SKILL.md                          # Full usage guide with all commands
  README.md                         # This file
  references/
    mcp_documentation.md            # Complete MCP docs (server directory, protocols, enterprise)
```

---

## Quick Reference

```bash
# List all configured servers
claude mcp list

# Add remote server (HTTP)
claude mcp add --transport http notion https://mcp.notion.com/mcp

# Add remote server (SSE) with auth header
claude mcp add --transport sse webflow https://mcp.webflow.com/sse \
  --header "Authorization: Bearer TOKEN"

# Add local server (stdio) with env vars
claude mcp add --transport stdio airtable \
  --env AIRTABLE_API_KEY=YOUR_KEY \
  -- npx -y airtable-mcp-server

# Get server details
claude mcp get <server-name>

# Remove a server
claude mcp remove <server-name>

# Import from Claude Desktop
claude mcp add-from-claude-desktop

# Check status (inside Claude Code)
/mcp
```

---

## Transport Types

| Transport | Use Case | Example |
|-----------|----------|---------|
| `http` | Cloud-based services with HTTP endpoints | Notion, Stripe, HubSpot |
| `sse` | Remote servers using Server-Sent Events | Webflow |
| `stdio` | Local processes communicating via stdin/stdout | Custom Python/Node servers |

---

## Configuration Scopes

| Scope | Stored In | Shared | Best For |
|-------|-----------|--------|----------|
| `local` (default) | `.claude/settings.local.json` | No | Personal dev servers, sensitive credentials |
| `project` | `.mcp.json` (project root) | Yes (version-controlled) | Team-shared tools |
| `user` | `~/.claude/settings.json` | No | Cross-project utilities |

Precedence: **local > project > user** (same-name servers).

---

## Authentication

| Method | Transport | How |
|--------|-----------|-----|
| OAuth 2.0 | HTTP, SSE | Automatic browser flow on first use; credentials stored in `~/.mcp-auth/` |
| Bearer token | HTTP, SSE | `--header "Authorization: Bearer TOKEN"` |
| API key | HTTP, SSE | `--header "X-API-Key: KEY"` |
| Env vars | stdio | `--env KEY=VALUE` (passed to the subprocess) |

---

## Setup

### Prerequisites

- Claude Code CLI (`claude`)
- No additional dependencies---this is a reference skill for Claude Code's built-in `claude mcp` commands

---

## Related Skills

- **`cloudflare`**: Wrangler CLI and Browser Rendering---one of many services you might connect via MCP.
- **`slack`**: Uses an MCP server for Slack integration.

---

## Requirements

- Claude Code CLI

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/mcp-server-manager ~/.claude/skills/
```
