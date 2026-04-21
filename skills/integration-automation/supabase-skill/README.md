# Supabase Skill

The database skill. PostgreSQL schema design, Row Level Security, database patterns, and MCP server integration for Supabase---with production patterns from the Twilio-Aldea SMS platform covering session management, dual persistence, and multi-tenant isolation.

**Last updated:** 2026-04-21

**Reflects:** Supabase MCP server (including mcp-lite on Edge Functions and self-hosted Docker), PostgreSQL 15+ best practices, Row Level Security patterns, and production database architectures from Twilio-Aldea.

---

## Why This Skill Exists

Supabase gives you a Postgres database with auth, realtime, and edge functions. The MCP server lets Claude Code operate on it directly---run SQL, manage migrations, create branches. But knowing *which* patterns to use for a given problem (multi-tenancy, soft deletes, temporal data, event sourcing) requires experience that most projects learn the hard way.

This skill encodes that experience: 10+ database design patterns with decision matrices, 10+ Row Level Security policies ready for production, session management with load-or-create semantics, dual persistence for soul memory, and MCP tool documentation for every operation. The production patterns come from Twilio-Aldea, where these designs handle real SMS traffic.

---

## Structure

```
supabase-skill/
  SKILL.md                                     # Setup, patterns, key concepts
  README.md                                    # This file
  assets/
    examples/
      supabase-client.ts                       # Singleton client pattern
      session-management.ts                    # Session management with timeout
      memory-store.ts                          # Dual persistence (soul + process memory)
      rls-policies.sql                         # 10 production-ready RLS policies
  references/
    mcp-setup.md                               # MCP server configuration guide
    database-patterns.md                       # Architectural patterns for scalable apps
    schema-design.md                           # PostgreSQL best practices
    security.md                                # RLS and authentication patterns
    tools-reference.md                         # MCP tools documentation
    production-patterns.md                     # Real patterns from Twilio-Aldea
    official-docs/
      row-level-security.md                    # Official Supabase RLS guide
      migrations.md                            # Official database migrations guide
```

Note: `references/github/` contains upstream Supabase JS client docs (README, issues, changelog, releases) for authoritative reference.

---

## What It Covers

### MCP Server Setup

Configure the Supabase MCP server for Claude Code, Cursor, or Claude Desktop. Two modes:

| Mode | Setup | Best For |
|------|-------|----------|
| **Remote (hosted)** | OAuth or Personal Access Token | Most users |
| **mcp-lite (Edge Functions)** | Zero config, global deployment | Zero cold starts |
| **Self-hosted (Docker)** | `supabase/mcp-server:latest` | Air-gapped or custom setups |

See `references/mcp-setup.md` for the full configuration guide.

### Database Patterns

`references/database-patterns.md` covers 10+ patterns with a decision matrix:

| Pattern | When to Use |
|---------|-------------|
| **OLTP** | Standard transactional apps |
| **Data Lakehouse** | Analytics over operational data |
| **Microservices** | Service-per-database isolation |
| **Event Sourcing** | Full audit trail, temporal queries |
| **CQRS** | Separate read/write optimization |
| **Single Table Inheritance** | Few subtypes, simple queries |
| **Class Table Inheritance** | Many subtypes, normalized storage |
| **Polymorphic Associations** | Flexible type relationships |
| **Temporal Data (SCD Type 2)** | Point-in-time queries, price history |
| **Multi-Tenancy** | SaaS with org-level isolation |
| **Soft Delete** | Recoverable data, audit compliance |

### Row Level Security

`assets/examples/rls-policies.sql` provides 10 production-ready policies:

| Policy | Description |
|--------|-------------|
| User-owned rows | Users see only their own data |
| Public read, private write | Anyone reads, only owner modifies |
| Organization-based | Org members share access |
| Role-based (RBAC) | Admin/editor/viewer hierarchy |
| Hierarchical | Parent org sees child org data |
| Time-based | Access expires after date |
| Multi-tenant composite | Tenant ID + user ID compound key |
| Service role bypass | Backend services skip RLS |
| Audit trail | Insert-only append logs |
| Polymorphic | Type-dependent access rules |

### Production Patterns

From `references/production-patterns.md` (Twilio-Aldea):

| Pattern | What It Solves |
|---------|---------------|
| Session load-or-create | Handle "no rows returned" errors gracefully |
| Dual persistence | Soul memory (personality) + process memory (state) |
| Upsert key-value | Configuration storage with conflict resolution |
| Materialized views | Analytics without query overhead |
| Audit triggers | Automatic change tracking |
| `pg_notify` events | Real-time event propagation |
| Temporal tracking | `valid_from`/`valid_to` for point-in-time queries |

---

## Examples

| Example | Purpose |
|---------|---------|
| `supabase-client.ts` | Singleton client initialization pattern |
| `session-management.ts` | Session create/load with timeout and error handling |
| `memory-store.ts` | Dual persistence for soul and process memory |
| `rls-policies.sql` | 10 copy-paste RLS policies |

---

## MCP Tools

| Tool | Purpose |
|------|---------|
| `execute_sql` | Run arbitrary SQL |
| `list_tables` | Browse schema |
| `describe_table` | Column types, constraints, indexes |
| `list_migrations` | View migration history |
| `generate_migration` | Create migration from description |
| `apply_migration` | Run pending migrations |
| `rollback_migration` | Revert last migration |
| `create_branch` | Database branching for safe testing |

See `references/tools-reference.md` for complete documentation with examples.

---

## Requirements

- Supabase account (free tier sufficient)
- Supabase MCP server configured (see `references/mcp-setup.md`)
- Node.js 18+ / TypeScript for examples
- `@supabase/supabase-js` (`npm install @supabase/supabase-js`)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/supabase-skill ~/.claude/skills/
```
