# Twitter

Search, post, monitor, and archive on Twitter/X via three modes: official API v2 search via x-search (pay-per-use, cost-tracked, cached), session-based posting/reading via bird CLI (free, browser cookies), and bookmark archival via Smaug. Includes feed groups, watchlists, and a structured research methodology.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Twitter/X is essential for monitoring topics, researching discourse, and posting---but the API is pay-per-use and the web UI is noisy. This skill provides three complementary tools: x-search for cost-tracked official API research, bird CLI for free session-based operations, and Smaug for AI-powered bookmark archival.

---

## Structure

```
twitter/
  SKILL.md                          # Full usage guide with all modes
  README.md                         # This file
  x-search/
    x-search.ts                     # Official API v2 search CLI
    lib/
      api.ts                        # API client
      cache.ts                      # File-based caching (15min TTL)
      format.ts                     # Output formatting
    data/
      feedgroups.json               # Named account collections
      watchlist.json                # Monitored accounts
```

---

## Three Modes

| Mode | Tool | Auth | Cost | Best For |
|------|------|------|------|----------|
| Official API | `x-search` | Bearer token | $0.005/read | Search, research, profiles, feeds |
| Session | `bird` | Browser cookies | Free | Posting, mentions, bookmarks |
| Archival | `smaug` | Via bird | Free | Bookmark/likes processing |

> **Alternative**: `opencli twitter` provides 25 free session-based commands (post, reply, search, bookmarks, follow, block, etc.) via Chrome session reuse. Prefer opencli for routine operations; use x-search for deep research with cost tracking.

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

# Post and reply (requires OAuth 1.0a)
bun run x-search.ts post "Hello from x-search!"
bun run x-search.ts reply 1234567890 "Great thread!"

# Watchlist monitoring
bun run x-search.ts watchlist check
```

### bird CLI (Free)

```bash
bird tweet "Hello world"
bird search "query" -n 10
bird mentions -n 10
bird bookmarks -n 20
```

### Smaug (Archival)

```bash
cd ~/tools/smaug && npx smaug run    # Fetch + process with AI categorization
```

---

## Cost Reference

| Resource | Cost |
|----------|------|
| Post read | $0.005 |
| User lookup | $0.010 |
| Post create | $0.010 |
| Quick search (~100 tweets) | ~$0.50 |
| Cached repeat | Free |

---

## Setup

### x-search (Official API)

- X API Bearer token from console.x.com
- `X_BEARER_TOKEN` in env or `~/.claude/skills/twitter/.env`
- OAuth 1.0a credentials for posting (`X_API_KEY`, `X_API_SECRET`, `X_ACCESS_TOKEN`, `X_ACCESS_TOKEN_SECRET`)
- Bun runtime (`brew install oven-sh/bun/bun`)

### bird CLI

- `brew install steipete/tap/bird`
- Uses browser cookies (log into Twitter in browser first)

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
- bird CLI (optional, for free operations)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/twitter ~/.claude/skills/
```
