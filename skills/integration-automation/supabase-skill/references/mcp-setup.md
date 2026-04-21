# Supabase MCP Server Setup Guide

## Overview

The Model Context Protocol (MCP) enables AI assistants like Cursor and Claude Desktop to interact directly with your Supabase projects. This guide covers both remote (hosted) and local (self-hosted) MCP server configurations.

## What is Supabase MCP?

Supabase MCP is an implementation of the Model Context Protocol that allows AI assistants to:
- Query databases using natural language
- Design and modify database schemas
- Generate migrations automatically
- Manage authentication and security policies
- Retrieve project configuration
- Analyze logs and debug issues

## Prerequisites

### Required
- Active Supabase account with at least one project
- Supabase CLI version 1.100.0+ (for local development)
- Compatible AI client: Cursor, Claude Desktop, or ChatGPT
- API keys from Supabase dashboard:
  - Service role key (for administrative operations)
  - Anon key (for restricted access)

### System Requirements
- **macOS**, **Linux**, or **Windows with WSL2**
- **Internet connectivity** (for remote MCP)
- **Docker** (optional, for containerized local MCP)

## Remote MCP Installation (Hosted)

### Step 1: Security Best Practices

Before connecting MCP, understand these security considerations:

**Prompt Injection Risk:**
- LLMs can be tricked by malicious prompts embedded in data
- Always enable manual approval for tool calls
- Review each operation before execution
- Use read-only mode for exploration

**Recommendations:**
1. **Don't connect to production** - Use development projects only
2. **Use read-only mode** - Enable when possible to prevent writes
3. **Project scoping** - Limit access to specific projects
4. **Branching** - Test on development branches before production
5. **Feature groups** - Disable unnecessary tool groups

### Step 2: Configure Your AI Client

#### For Cursor

**One-Click Installation:**
```bash
# Click the "Add to Cursor" link from Supabase MCP docs
# Or manually configure:
```

**Manual Configuration (`·cursor/mcp.json`):**
```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```

**With Project Scoping:**
```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp",
      "env": {
        "SUPABASE_PROJECT_REF": "your-project-ref"
      }
    }
  }
}
```

**With Read-Only Mode:**
```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp",
      "env": {
        "SUPABASE_PROJECT_REF": "your-project-ref",
        "SUPABASE_READ_ONLY": "true"
      }
    }
  }
}
```

#### For Claude Desktop

**Configuration Location:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

**Configuration:**
```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```

#### For Claude Code CLI

**Installation via CLI:**
```bash
# Basic installation (local scope)
claude mcp add --transport stdio \
  --env SUPABASE_ACCESS_TOKEN=your_personal_access_token \
  --scope local \
  supabase -- npx -y @supabase/mcp-server-supabase@latest \
  --project-ref=your_project_ref

# With read-only mode
claude mcp add --transport stdio \
  --env SUPABASE_ACCESS_TOKEN=your_personal_access_token \
  --scope local \
  supabase -- npx -y @supabase/mcp-server-supabase@latest \
  --project-ref=your_project_ref \
  --read-only

# User scope (available across all projects)
claude mcp add --transport stdio \
  --env SUPABASE_ACCESS_TOKEN=your_personal_access_token \
  --scope user \
  supabase -- npx -y @supabase/mcp-server-supabase@latest \
  --project-ref=your_project_ref
```

**CLI Syntax Reference:**
```bash
claude mcp add [options] <name> <command> [args...]

Options:
  -s, --scope <scope>          Configuration scope (local, user, or project)
  -t, --transport <transport>  Transport type (stdio, sse, http)
  -e, --env <env...>           Set environment variables (e.g. -e KEY=value)
  -H, --header <header...>     Set WebSocket headers
  --                           Separator before command (required for stdio)
```

**Verify Installation:**
```bash
# List configured MCP servers
claude mcp list

# Get server details
claude mcp get supabase

# Remove server
claude mcp remove supabase -s local
```

**HTTP Transport (Remote):**
```bash
# Connect to remote Supabase MCP
claude mcp add --transport http \
  supabase https://mcp.supabase.com/mcp
```

#### For ChatGPT (Custom GPT)

1. Create a new Custom GPT
2. Add MCP endpoint as an action:
   - URL: `https://mcp.supabase.com/mcp`
   - Authentication: Bearer token (your PAT)
3. Configure action schema (provided by Supabase)

### Step 3: Authentication

**Using OAuth Flow (Recommended):**
1. Start your AI client
2. MCP client will prompt for authentication
3. Browser opens to Supabase login
4. Authorize access and select organization
5. Return to AI client (automatically authenticated)

**Legacy Personal Access Token (PAT):**
```bash
# Generate PAT from Supabase Dashboard
# Account Settings > Access Tokens > Generate New Token

# Add to environment
export SUPABASE_ACCESS_TOKEN=sbp_your_token_here
```

### Step 4: Verify Installation

Test the connection:

**In Cursor:**
```
Ask: "List my Supabase projects"
```

**In Claude Desktop:**
```
Ask: "Show me the schema for my users table"
```

Expected output: List of projects or table schema

## Local MCP Installation (Self-Hosted)

### Option 1: NPM Installation

**Install Globally:**
```bash
npm install -g @supabase/mcp-server-supabase
```

**Configure with Environment Variables:**
```bash
export SUPABASE_URL=https://your-project.supabase.co
export SUPABASE_SERVICE_KEY=your-service-role-key
export SUPABASE_READ_ONLY=false  # Optional: enable read-only mode
```

**Run Server:**
```bash
supabase-mcp --access-token YOUR_PAT
```

**Configure AI Client (stdio transport):**
```json
{
  "mcpServers": {
    "supabase-local": {
      "command": "supabase-mcp",
      "args": ["--access-token", "YOUR_PAT"],
      "env": {
        "SUPABASE_URL": "https://your-project.supabase.co",
        "SUPABASE_SERVICE_KEY": "your-service-key"
      }
    }
  }
}
```

### Option 2: Docker Installation

**Run Container:**
```bash
docker run -d \
  --name supabase-mcp \
  -e SUPABASE_URL=https://your-project.supabase.co \
  -e SUPABASE_SERVICE_KEY=your-service-key \
  -e SUPABASE_READ_ONLY=false \
  -p 8080:8080 \
  supabase/mcp-server:latest
```

**Configure AI Client (HTTP transport):**
```json
{
  "mcpServers": {
    "supabase-docker": {
      "url": "http://localhost:8080"
    }
  }
}
```

### Option 3: Source Installation

**Clone Repository:**
```bash
git clone https://github.com/supabase-community/supabase-mcp.git
cd supabase-mcp
npm install
```

**Build:**
```bash
npm run build
```

**Configure:**
```bash
cp .env.example .env
# Edit .env with your credentials
```

**Run:**
```bash
npm start
```

## Configuration Options

### Project Scoping

Limit MCP access to specific projects:

**Environment Variable:**
```bash
export SUPABASE_PROJECT_REF=abcdefghijklmnop
```

**Configuration:**
```json
{
  "scoping": {
    "project_ref": "abcdefghijklmnop"
  }
}
```

### Read-Only Mode

Execute all queries as read-only:

**Environment Variable:**
```bash
export SUPABASE_READ_ONLY=true
```

**Configuration:**
```json
{
  "read_only": true
}
```

**What it does:**
- All SQL queries run with read-only transaction
- Prevents INSERT, UPDATE, DELETE, TRUNCATE, DROP
- Safe for exploration and analysis
- Ideal for development environments

### Feature Groups

Control which MCP tools are available:

**Configuration:**
```json
{
  "feature_groups": {
    "sql": true,           // SQL operations
    "migrations": true,    // Schema migrations
    "auth": false,         // Authentication management (disabled)
    "storage": false,      // File storage (disabled)
    "logs": true           // Log analysis
  }
}
```

**Available Groups:**
- **sql**: Database queries and schema introspection
- **migrations**: Schema changes and migration generation
- **auth**: User management and authentication
- **storage**: File and bucket operations (future)
- **logs**: Log retrieval and analysis
- **functions**: Edge Functions management (future)

### Rate Limiting

Prevent excessive API calls:

**Configuration:**
```json
{
  "rate_limit": {
    "max_requests": 100,
    "window_ms": 60000  // 1 minute
  }
}
```

## MCP Protocol & Transport

### Transport Methods

**stdio (Standard Input/Output):**
- Lowest latency for local deployments
- Used by default for NPM installations
- Sub-millisecond command processing overhead

**HTTP/HTTPS:**
- Stateless REST-style operations
- Adds 10-50ms network round-trip latency
- Best for remote/hosted deployments

**SSE (Server-Sent Events):**
- Real-time streaming of results
- Maintains persistent connections
- Ideal for long-running queries or continuous monitoring

### Connection Example

**stdio Configuration:**
```json
{
  "mcpServers": {
    "supabase": {
      "command": "supabase-mcp",
      "args": ["--access-token", "YOUR_TOKEN"]
    }
  }
}
```

**HTTP Configuration:**
```json
{
  "mcpServers": {
    "supabase": {
      "url": "https://mcp.supabase.com/mcp"
    }
  }
}
```

## Architecture & Routing

### How Queries Are Processed

1. **Natural Language Input** → AI model interprets intent and extracts parameters
2. **MCP Server Validation** → Validates against schema and security rules
3. **SQL Generation** → Generates appropriate database operations
4. **Execution** → Runs on PostgreSQL with proper permissions
5. **Response** → Returns results in JSON format

### Schema Introspection

MCP automatically maintains awareness of your database through:
- **Automatic schema caching** - Refreshed after migrations
- **Relationship detection** - Understands foreign keys
- **Type awareness** - Knows data types and constraints
- **Index information** - Sees which columns are indexed

### Query Optimization

MCP performs intelligent optimizations:
- **Type matching** - Prevents type conversion errors
- **Join optimization** - Uses foreign key relationships
- **Index hints** - Suggests when indexes would help
- **Batch operations** - Combines multiple queries when possible

## Security Configuration

### Access Control

**Service Role Key (Admin):**
- Full database access, bypasses RLS
- Use for administrative operations
- Never expose to clients
- Rotate regularly

**Anon Key (Restricted):**
- Subject to RLS policies
- Safe for client-side use
- Limited permissions
- Use for application access

### Sandboxing

MCP provides security boundaries:

**Query Validation:**
```python
# Whitelisted operations
ALLOWED_OPERATIONS = ['SELECT', 'INSERT', 'UPDATE', 'DELETE']

# Blacklisted patterns (SQL injection prevention)
BLOCKED_PATTERNS = [
  '; DROP',
  'UNION SELECT',
  'EXEC(',
  'EXECUTE('
]
```

**Transaction Isolation:**
- Each query runs in isolated transaction
- Automatic rollback on suspicious patterns
- Rate limiting prevents abuse
- Audit logging tracks all operations

### Prompt Injection Mitigation

**Input Sanitization:**
```python
# Example defense
def sanitize_input(user_input):
    # Remove command sequences
    input = remove_sql_commands(user_input)

    # Wrap in quotes to prevent interpretation
    input = escape_quotes(input)

    # Validate against schema
    validate_schema_compatibility(input)

    return input
```

**Additional Protection:**
- Separation of data from commands
- Content wrapped with anti-injection instructions
- Multiple validation layers
- Manual approval checkpoints

## Monitoring & Logging

### Audit Logs

MCP logs every operation:

**Log Entry Structure:**
```json
{
  "timestamp": "2025-10-23T12:00:00Z",
  "user": "user@example.com",
  "operation": "SELECT",
  "query": "SELECT * FROM users WHERE...",
  "status": "success",
  "duration_ms": 42,
  "rows_affected": 10
}
```

### Access Through Supabase Dashboard

1. Navigate to Project Dashboard
2. Click "Logs" in sidebar
3. Filter by "MCP Operations"
4. Export logs for compliance

### Alerts Configuration

Set up alerts for:
- **Unauthorized access attempts**
- **Unusual query patterns**
- **Repeated authorization failures**
- **High query volume**
- **Slow query performance**

## Performance Considerations

### Latency Breakdown

| Component | Latency | Notes |
|-----------|---------|-------|
| MCP Protocol | <1ms | (stdio), 10-50ms (HTTP) |
| AI Inference | 100ms-3s | Query complexity dependent |
| Database Query | 10-500ms | Schema/data size dependent |
| **Total** | **110ms-4s** | End-to-end operation |

### Optimization Strategies

**1. Caching:**
```json
{
  "cache": {
    "schema": true,          // Cache schema info
    "query_results": true,   // Cache repeated queries
    "ttl_seconds": 300       // 5-minute cache TTL
  }
}
```

**2. Batching:**
```javascript
// Group related operations
const batch = [
  { operation: 'SELECT', table: 'users' },
  { operation: 'SELECT', table: 'posts' },
  { operation: 'SELECT', table: 'comments' }
];

// Execute together, reducing overhead
await mcp.executeBatch(batch);
```

**3. Connection Pooling:**
```json
{
  "connection_pool": {
    "min_connections": 2,
    "max_connections": 10,
    "idle_timeout_ms": 30000
  }
}
```

## High Availability & Fault Tolerance

### Redundancy

**Multiple MCP Instances:**
```bash
# Behind load balancer
docker run -d --name mcp-1 supabase/mcp-server
docker run -d --name mcp-2 supabase/mcp-server
docker run -d --name mcp-3 supabase/mcp-server

# Configure load balancer (nginx, HAProxy, etc.)
```

**Health Checks:**
```bash
# Endpoint for monitoring
curl http://localhost:8080/health

# Expected response
{
  "status": "healthy",
  "database": "connected",
  "uptime": 3600
}
```

### Retry Logic

**Client-Side Retries:**
```json
{
  "retry": {
    "max_attempts": 3,
    "backoff": "exponential",  // 1s, 2s, 4s
    "timeout_ms": 5000
  }
}
```

**Circuit Breaker:**
```json
{
  "circuit_breaker": {
    "failure_threshold": 5,    // Trip after 5 failures
    "timeout_ms": 60000,       // Wait 1 minute
    "half_open_after": 30000   // Test after 30 seconds
  }
}
```

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to MCP server

**Solutions:**
1. Verify network connectivity: `ping mcp.supabase.com`
2. Check firewall rules allow HTTPS/8080
3. Confirm API key is valid and not expired
4. Test with curl: `curl -H "Authorization: Bearer TOKEN" https://mcp.supabase.com/mcp/health`

### Authentication Failures

**Problem:** "Invalid credentials" or "Unauthorized"

**Solutions:**
1. Regenerate Personal Access Token
2. Verify correct organization selected during OAuth
3. Check token expiration date
4. Ensure service role key matches project
5. Confirm user has project permissions

### Schema Synchronization Issues

**Problem:** MCP doesn't see recent schema changes

**Solutions:**
1. Force schema refresh: Send migration notification
2. Restart MCP server to clear cache
3. Check migration was successfully applied
4. Verify supabase CLI version is up to date

### Performance Problems

**Problem:** Queries are slow through MCP

**Solutions:**
1. Enable query plan logging
2. Check for missing indexes
3. Monitor connection pool utilization
4. Review AI inference latency separately
5. Test query directly in Supabase dashboard

## Alternative Deployment Options

### mcp-lite on Edge Functions

Supabase MCP is also available via **mcp-lite on Edge Functions**, providing zero cold starts and global deployment. This option runs the MCP server as a Supabase Edge Function, eliminating the need for a separate server process.

Benefits:
- Zero cold starts (always warm at the edge)
- Global deployment across Supabase's edge network
- No Docker or npm installation required
- Managed by Supabase infrastructure

### Self-Hosted MCP (Docker)

For teams requiring full control, the MCP server can be self-hosted via Docker:

```bash
docker run -d \
  --name supabase-mcp \
  -e SUPABASE_URL=https://your-project.supabase.co \
  -e SUPABASE_SERVICE_KEY=your-service-key \
  -p 8080:8080 \
  supabase/mcp-server:latest
```

Connect your AI client to the self-hosted instance:

```json
{
  "mcpServers": {
    "supabase-self-hosted": {
      "url": "http://localhost:8080"
    }
  }
}
```

Self-hosted deployments support the same configuration options (read-only mode, project scoping, feature groups) as the hosted version.

## Next Steps

After successful MCP setup:

1. **Explore Tools** - Review `tools-reference.md` for available operations
2. **Design Schema** - Use `schema-design.md` for best practices
3. **Implement Security** - Follow `security.md` for RLS patterns
4. **Learn Patterns** - Study `database-patterns.md` for advanced designs

## Additional Resources

- **Supabase MCP GitHub**: https://github.com/supabase-community/supabase-mcp
- **MCP Specification**: https://modelcontextprotocol.io
- **Supabase CLI Docs**: https://supabase.com/docs/guides/cli
- **Community Discord**: https://discord.supabase.com
