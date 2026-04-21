# Figma MCP Server Setup Guide

This guide covers setting up Figma MCP server integration in Claude Code and other MCP clients. There are two main options: the official Figma Dev Mode MCP server and community-built servers.

## Option 1: Official Figma Dev Mode MCP Server (Recommended)

### Requirements

- **Figma Plan**: Professional, Organization, or Enterprise plan with Dev Mode access
- **Seat Type**: Dev or Full seat
- **MCP Client**: VS Code, Cursor, Windsurf, or Claude Code
- **Figma Desktop App**: Required for local server mode

### Connection Modes

The official server supports two connection modes:

#### Remote Mode (Recommended)
Connects directly to Figma's hosted endpoint without requiring the desktop app.

**Configuration for Claude Code:**

Add to your MCP settings configuration:

```json
{
  "mcpServers": {
    "figma-dev-mode": {
      "command": "figma-mcp-server",
      "args": ["--remote"],
      "env": {
        "FIGMA_ACCESS_TOKEN": "your-figma-access-token"
      }
    }
  }
}
```

#### Local Mode
Runs through the Figma desktop app on your machine.

**Setup Steps:**

1. Open Figma Desktop App
2. Go to Settings → Integrations → Dev Mode MCP Server
3. Enable the server
4. Configure in your MCP client

**Configuration for Claude Code:**

```json
{
  "mcpServers": {
    "figma-dev-mode-local": {
      "command": "figma-desktop-mcp",
      "args": []
    }
  }
}
```

### Getting Your Figma Access Token

For remote mode, you need a personal access token:

1. Log in to Figma (figma.com)
2. Click your profile icon → Settings
3. Navigate to "Access Tokens" section
4. Click "Generate new token"
5. Name your token (e.g., "Claude Code MCP")
6. Grant read-only access for all scopes
7. Click "Generate token"
8. **Copy the token immediately** (it's only shown once)
9. Store it securely - add it to your MCP configuration

### Enabling the MCP Server in Claude Code

1. Open Claude Code settings
2. Navigate to Tools and Integrations
3. Click "Add a custom MCP server"
4. Paste your configuration JSON
5. Save and restart Claude Code
6. Verify the server appears in MCP servers list

## Option 2: Community Figma MCP Server (Free)

### Framelink MCP for Figma (by GLips)

Popular community server with 14.5k+ GitHub stars (formerly "figma-developer-mcp", rebranded to Framelink in v0.11.0). Free to use, only requires a Figma API token.

**GitHub**: https://github.com/GLips/Figma-Context-MCP

**Recent updates (v0.11.0, Apr 2026):**
- Rebranded from "figma-developer-mcp" to "Framelink MCP for Figma"
- Stateless HTTP transport option (added in v0.8.0) for simpler deployment
- VS Code layer generation for direct code export
- Prompt injection defense scanner
- Progress notifications and performance improvements

### Requirements

- **Figma Plan**: Any plan (including free)
- **Figma API Token**: Personal access token
- **Node.js**: v16 or higher
- **MCP Client**: VS Code, Cursor, Windsurf, or Claude Code

### Installation

#### Step 1: Install the Package

```bash
npm install -g figma-developer-mcp
```

#### Step 2: Get Your Figma API Token

1. Log in to Figma (figma.com)
2. Click your profile icon → Settings
3. Scroll to "Personal access tokens"
4. Click "Generate new token"
5. Name your token (e.g., "MCP Integration")
6. Grant read-only access
7. Copy and save the token securely

#### Step 3: Configure in Claude Code

Add to your MCP configuration:

```json
{
  "mcpServers": {
    "figma-context-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "figma-developer-mcp",
        "--stdio",
        "--figma-api-key=YOUR_FIGMA_API_TOKEN"
      ]
    }
  }
}
```

Replace `YOUR_FIGMA_API_TOKEN` with your actual token.

#### Step 4: Enable and Verify

1. Save the configuration
2. Restart Claude Code
3. Check Tools and Integrations → MCP servers
4. Verify "figma-context-mcp" appears with available tools

### Using WSL (Windows Users)

If using Windows Subsystem for Linux, ensure you're using Cursor v0.50.4+ or Claude Code with remote workspace support:

```json
{
  "mcpServers": {
    "figma-context-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "figma-developer-mcp",
        "--stdio",
        "--figma-api-key=YOUR_FIGMA_API_TOKEN"
      ]
    }
  }
}
```

No need for `cmd /c` wrappers in newer versions.

## Verifying Installation

### Test the Connection

1. Open your MCP client (Claude Code, Cursor, etc.)
2. Start a new conversation
3. Send a test message: "List available Figma MCP tools"
4. You should see tools like:
   - `get_figma_data`
   - `get_figma_variables`
   - `get_figma_components`
   - `get_figma_styles`

### Test with a Design

1. Open any Figma file
2. Select a frame
3. Copy link to selection (right-click → Copy link to selection)
4. In your MCP client, paste the link and say: "Describe this Figma design"
5. The client should call the MCP server and retrieve design data

## Troubleshooting

### Server Not Appearing in MCP Client

**Check:**
- Configuration JSON syntax is valid
- Server name doesn't conflict with existing servers
- MCP client has been restarted
- Node.js is installed and accessible

**Solution:**
```bash
# Verify Node.js installation
node --version

# Reinstall the package
npm uninstall -g figma-developer-mcp
npm install -g figma-developer-mcp
```

### Authentication Errors

**Error:** "Invalid Figma access token" or "Authentication failed"

**Check:**
- Token is copied correctly (no extra spaces)
- Token has not expired
- Token has appropriate read permissions

**Solution:**
1. Generate a new Figma access token
2. Update your MCP configuration
3. Restart your MCP client

### Tools Not Available

**Check:**
- Server is enabled in MCP settings
- No errors in server logs
- Figma API is accessible (not blocked by firewall)

**Solution:**
```bash
# Test the server directly
npx figma-developer-mcp --stdio --figma-api-key=YOUR_TOKEN

# Check for error messages in the output
```

### Permission Denied Errors

**Error:** "Cannot access Figma file" or "Insufficient permissions"

**Check:**
- You have view access to the Figma file
- File is not in a restricted organization
- API token has correct scopes

**Solution:**
1. Verify file permissions in Figma
2. Ask file owner for access
3. Regenerate token with correct scopes

### Rate Limiting

**Error:** "Rate limit exceeded" or "Too many requests"

**Solution:**
- Official server: Check your organization's rate limits
- Community server: Wait a few minutes between requests
- Batch multiple requests when possible

## Best Practices

### Security

- **Never commit tokens**: Don't include tokens in git repositories
- **Use environment variables**: Store tokens in environment variables or secure vaults
- **Rotate tokens**: Periodically regenerate tokens for security
- **Minimal permissions**: Grant only read access, not write

### Performance

- **Cache design data**: Avoid repeatedly fetching the same design
- **Request specific frames**: Use node-id to fetch only what you need
- **Batch requests**: When possible, fetch multiple elements in one call

### Organization

- **Name tokens clearly**: "Claude Code MCP - Production" vs "Testing"
- **Document configuration**: Keep a README of your MCP setup
- **Version control**: Track MCP configuration (without tokens)

## Resources

- **Official Figma MCP Docs**: https://developers.figma.com/docs/figma-mcp-server/
- **Figma Help Center**: https://help.figma.com/hc/en-us/articles/32132100833559-Guide-to-the-Figma-MCP-server
- **Community Server GitHub**: https://github.com/GLips/Figma-Context-MCP
- **MCP Specification**: https://modelcontextprotocol.io/

## Getting Help

- **Figma Community Forum**: https://forum.figma.com/
- **MCP Discord**: https://discord.gg/mcp (check for server-specific channels)
- **GitHub Issues**: Report bugs to the respective server's repository
