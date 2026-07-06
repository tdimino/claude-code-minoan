# Twitter

Search, post, monitor, and archive on Twitter/X via five tools: the official hosted X MCP server (full-archive search, trends, bookmarks — via xurl bridge), x-search CLI (pay-per-use, cost-tracked, cached), xurl (X's official CLI for any endpoint), bird CLI (free session-based operations, frozen at 0.8.0), and Smaug bookmark archival. Includes feed groups, watchlists, a URL-surcharge guard on posting, and a structured research methodology.

**Last updated:** 2026-07-05

---

## Why This Skill Exists

Twitter/X is essential for monitoring topics, researching discourse, and posting—but the API is pay-per-use (repriced twice in 2026) and the web UI is noisy. This skill layers cost discipline over the official API (x-search), wires in X's first-party agent surface (hosted MCP at `api.x.com/mcp`, launched June 2026), and keeps free session-based fallbacks (bird) while they last.

---

## Structure

```
twitter/
  SKILL.md                          # Full usage guide with all modes
  README.md                         # This file
  references/
    pricing.md                      # July 2026 rate card, Owned Reads, rebates
    xurl-mcp-setup.md               # OAuth 2.0 + hosted MCP bridge wiring
    setup.md                        # Bearer/OAuth 1.0a setup, troubleshooting
  x-search/
    x-search.ts                     # Official API v2 CLI
    lib/
      api.ts                        # API client (search, post, usage endpoint)
      cache.ts                      # File-based caching (15min TTL, auto-prune)
      format.ts                     # Output formatting
    data/
      feedgroups.json               # Named account collections
      watchlist.json                # Monitored accounts
```

---

## Five Tools

| Mode | Tool | Auth | Cost | Best For |
|------|------|------|------|----------|
| Hosted MCP | `xapi` via `xurl mcp` | OAuth 2.0 | pay-per-use | Full-archive search, trends, bookmarks |
| Official API | `x-search` | Bearer token | pay-per-use, tracked | Search, research, profiles, feeds |
| Official CLI | `xurl` | OAuth 1.0a + 2.0 | pay-per-use | Media upload, DMs, raw endpoints |
| Session | `bird` | Browser cookies | Free | Casual reads, mentions — while it lasts |
| Archival | `smaug` | Via bird | Free | Bookmark/likes processing |

---

## Usage

### x-search (Official API)

```bash
# Quick search (cost-conscious, cached)
bun run x-search.ts search "AI agents" --quick

# Full search with sorting and filtering
bun run x-search.ts search "Claude Code" --pages 3 --sort likes --since 1d

# Profile and threads
bun run x-search.ts profile AnthropicAI --count 10
bun run x-search.ts thread 1234567890

# Feed from account groups
bun run x-search.ts feed geopolitics --since 1d

# Post and reply (OAuth 1.0a). URL posts refused without --allow-url ($0.20 vs $0.015)
bun run x-search.ts post "Hello from x-search!"
bun run x-search.ts post "test" --dry-run          # validate without posting
bun run x-search.ts reply 1234567890 "Great thread!"

# Actual billed consumption
bun run x-search.ts usage

# Watchlist monitoring
bun run x-search.ts watchlist check
```

### bird CLI (Free, Frozen)

Upstream deleted Feb 2026; npm serves the final 0.8.0. Works until X rotates GraphQL internals.

```bash
bird --cookie-source chrome tweet "Hello world"
bird --cookie-source chrome search "query" -n 10
bird --cookie-source chrome mentions -n 10
bird --cookie-source chrome bookmarks -n 20
```

### Smaug (Archival)

```bash
cd ~/tools/smaug && npx smaug run    # Fetch + process with AI categorization
```

---

## Cost Reference (July 2026)

| Resource | Cost |
|----------|------|
| Post read | $0.005 |
| User lookup | $0.010 |
| Post create | $0.015 |
| Post create (with URL) | $0.200 |
| Owned reads (own posts/bookmarks/mentions) | $0.001 |
| Quick search (~100 tweets) | ~$0.50 |
| Cached / deduped repeat | Free |

Full rate card, rebate tiers, and dedup rules: `references/pricing.md`.

---

## Setup

### x-search (Official API)

- X API Bearer token from console.x.com
- `X_BEARER_TOKEN` in env or `~/.claude/skills/twitter/.env`
- OAuth 1.0a credentials for posting (`X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`)
- Bun runtime (`brew install oven-sh/bun/bun`)
- Full walkthrough: `references/setup.md`

### xurl + hosted X MCP

- `npm install -g @xdevplatform/xurl`
- OAuth 2.0 app credentials (`CLIENT_ID`, `CLIENT_SECRET`), callback `http://localhost:8080/callback`
- Bridge wiring: `references/xurl-mcp-setup.md`

### bird CLI

- `npm install -g @steipete/bird` (0.8.0, final release; mirror: `LaceLetho/bird-cli-backup`)
- Uses browser cookies (log into Twitter in Chrome first)

### Smaug

- `npx smaug setup` in `~/tools/smaug`

---

## Related Skills

- **`exa-search`**: Neural web search---complements Twitter research with broader web context.
- **`scrapling`**: Web scraping for pages linked from tweets.

---

## Requirements

- Bun runtime (for x-search)
- X API Bearer token (for x-search)
- xurl (optional, for hosted MCP and media/DM endpoints)
- bird CLI (optional, for free operations)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/twitter ~/.claude/skills/
```
