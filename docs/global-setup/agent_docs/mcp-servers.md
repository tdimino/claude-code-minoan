# MCP Servers

## Key Facts
- Claude Code ignores `mcpServers` in `settings.json`--use `claude mcp add` CLI instead
- `claude mcp list` to check status, `claude mcp get <name>` for details
- After adding/changing MCP servers, **restart Claude Code** for changes to take effect

## Configured Servers

| Server | Transport | Purpose |
|--------|-----------|---------|
| context7 | stdio | Library/framework documentation lookup |
| supabase | stdio | Database management and queries |
| playwright | stdio | Browser automation for testing |

## Adding a New Server

```bash
# stdio transport (most common)
claude mcp add my-server -c npx -a "@my-org/mcp-server" -s user

# HTTP transport
claude mcp add my-server --transport http --url http://localhost:8080/mcp -s user

# With environment variables
claude mcp add my-server -c npx -a "@my-org/mcp-server" -e API_KEY=your-key -s user
```

Scopes: `user` (global), `project` (repo-local), `local` (gitignored).

## Troubleshooting

1. **Server not showing tools**: Run `claude mcp list` -- status should be "connected"
2. **Connection refused**: Check the server process is running (`ps aux | grep mcp`)
3. **Tools available but failing**: Check `claude mcp get <name>` for error output
4. **Stale state**: Restart Claude Code after config changes

## Tool Search

Claude Code's MCP Tool Search loads tools on-demand, reducing context pollution by ~85%. Deferred tools appear by name in system reminders--use `ToolSearch` to fetch their schemas before calling them.
