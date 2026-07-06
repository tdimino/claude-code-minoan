---
name: twitter
description: "Search, post, monitor, and archive on Twitter/X via five tools: the official hosted X MCP server (full-archive search, trends, bookmarks, Articles via xurl bridge), x-search CLI (cost-tracked API v2 research, feeds, watchlists, posting), xurl (official CLI for any endpoint incl. media/DMs), bird CLI (free session-based reads/writes, frozen at 0.8.0), and Smaug bookmark archival. Triggers on: search tweets, post to X, reply on Twitter, full-archive search, what's trending, check mentions, timeline, DMs, monitor account, research topic on Twitter, archive bookmarks."
---

# Twitter/X — Multi-Mode Integration

Five tools; choose by task:

| Mode | Tool | Auth | Cost | Use For |
|------|------|------|------|---------|
| **Hosted MCP** | `xapi` MCP server (via xurl bridge) — *setup pending* | OAuth 2.0 | pay-per-use | Full-archive search, trends, bookmarks, Articles, timelines |
| **Official API** | `x-search` | Bearer + OAuth 1.0a | pay-per-use, tracked | Cost-governed research, feeds, watchlists, posting |
| **Official CLI** | `xurl` | OAuth 1.0a + 2.0 | pay-per-use | Any endpoint: media upload, DMs, raw API calls |
| **Session** | `bird` | Browser cookies | Free | Casual reads, mentions, media posts — while it lasts |
| **Archival** | `smaug` | Via bird | Free | Bookmark/likes processing, AI-powered filing |

Pricing changes often (twice in 2026 already) — full rate card and billing mechanics in `references/pricing.md`. Headline numbers: post read $0.005, post create $0.015, **post with URL $0.200**, owned reads $0.001, 24h-UTC dedup, 2M reads/month cap.

## When to Use Which

| Task | Tool | Why |
|------|------|-----|
| Full-archive search (beyond 7 days) | xapi MCP | Only mode that reaches X's full history |
| Trends, news by location | xapi MCP | X-proprietary, not in x-search |
| Search recent tweets by topic | x-search | Cost-tracked, cached, quality filters |
| Daily feed from followed accounts | x-search feed | Batched OR-queries, cheap |
| Monitor specific accounts | x-search watchlist | Batch check with cost tracking |
| Post a text tweet or reply | x-search post/reply | URL-surcharge guard built in |
| Post with media, DMs, Articles | xurl | Official CLI, chunked upload |
| Check actual billed spend | x-search usage | `GET /2/usage/tweets` ground truth |
| Free casual reads / mentions | bird | Free while cookies + GraphQL hold |
| Archive bookmarks | smaug | AI categorization, markdown output |

## Hosted X MCP (`xapi`)

X's first-party MCP server at `https://api.x.com/mcp` (launched June 2026). Six tool groups: Posts, Search (incl. full-archive), Users/timelines, Bookmarks, Trends by WOEID, Articles.

**Not yet wired** — blocked on OAuth 2.0 client credentials (`CLIENT_ID`/`CLIENT_SECRET` in the skill `.env`). Once present, run the `claude mcp add xapi` command in `references/xurl-mcp-setup.md`, and verify with `claude mcp list` before directing work at xapi tools.

Every tool call bills standard pay-per-use rates — treat agentic MCP loops with the same cost discipline as x-search deep searches. Setup, re-auth, and the read-only Bearer fallback: `references/xurl-mcp-setup.md`.

Never read `~/.xurl` (live OAuth tokens) or the skill `.env` values into context.

## x-search — Cost-Governed Research

Run via: `bun run ~/.claude/skills/twitter/x-search/x-search.ts <command>` — the examples below abbreviate this prefix to `x-search.ts`; always use the full `bun run` invocation.

```bash
# Quick search (default for exploration): 1 page, max 10, noise filter, 1hr cache, ~$0.50
x-search.ts search "AI agents" --quick

# Full search
x-search.ts search "Claude Code" --pages 3 --sort likes --since 1d
x-search.ts search "Minoan archaeology" --markdown --save

# Profiles, threads, single tweets
x-search.ts profile AnthropicAI --count 10
x-search.ts thread 1234567890 --pages 3
x-search.ts tweet 1234567890

# Feeds from named account groups (geopolitics, palestine, all-feeds)
x-search.ts feed geopolitics --since 1d
x-search.ts feed all-feeds --since 7d --markdown --save
x-search.ts feed imetatronink,Megatron_ron --since 1d --bird   # free via bird
x-search.ts feedgroup add tech kaboreas "K8s/infra"            # manage groups

# Watchlist (profile API — pricier)
x-search.ts watchlist add kikismith "Ancient art"
x-search.ts watchlist check

# Posting (OAuth 1.0a). URL posts are REFUSED unless --allow-url ($0.20 vs $0.015)
x-search.ts post "Hello from x-search!"
x-search.ts post "test text" --dry-run          # validate + show cost WITHOUT posting
x-search.ts reply 1234567890 "Great thread!"
x-search.ts delete 1234567890                    # delete own tweet ($0.01)

# Billed consumption (real spend, not estimates)
x-search.ts usage
```

Key search flags: `--quick`, `--sort likes|impressions|retweets|recent`, `--since 1h|3h|12h|1d|7d`, `--pages 1-5`, `--from user`, `--quality`, `--min-likes N`, `--min-impressions N`, `--no-replies`, `--json`, `--markdown`, `--save`. Profile: `--count N` (default 20), `--replies` to include replies. Cache: 15min TTL (1hr quick), auto-pruned on every run; `cache clear` to flush.

When testing or demonstrating post/reply, always use `--dry-run` — the success path publishes a live tweet otherwise.

Setup (Bearer + OAuth 1.0a keys in `~/.claude/skills/twitter/.env`) is done on this machine. Re-setup walkthrough and credential troubleshooting: `references/setup.md`.

### Research methodology

1. **Decompose** the topic into 2-3 query angles, 2. **search `--quick`** to assess signal, 3. **refine** with `--from`/`--quality`/`--since`, 4. **thread** high-value conversations, 5. **deep-dive** best queries with `--pages 3 --markdown --save`, 6. **synthesize**. Reach for the xapi MCP when the answer predates the 7-day window.

## xurl — Official CLI

```bash
xurl /2/users/me                                   # any endpoint, OAuth handled
xurl -X POST /2/tweets -d '{"text": "hello"}'
xurl media upload photo.png                        # chunked media upload
```

Installed (v1.2.2). Auth registration and the MCP bridge command: `references/xurl-mcp-setup.md`.

## bird CLI — Session-Based Operations (Frozen at 0.8.0)

Uses undocumented Twitter GraphQL APIs via browser cookies. Free, but **upstream is dead**: steipete deleted the repo and brew tap (Feb 2026). npm still serves the final 0.8.0 (`npm install -g @steipete/bird`); source mirror at `github.com/LaceLetho/bird-cli-backup`. Verified working 2026-07-05 — but when X rotates GraphQL internals there will be no fix. Fall back to xapi MCP / x-search for reads, xurl for writes. Smaug's fetching inherits this risk (migration path: Owned Reads at $0.001/resource, see `references/pricing.md`).

Always pass `--cookie-source chrome` to all bird commands to avoid EPERM warnings from Safari cookie access.

### Posting

```bash
bird --cookie-source chrome tweet "Hello world"
bird --cookie-source chrome reply 123456789 "Great thread!"
bird --cookie-source chrome tweet "With image" --media photo.png --alt "Description"
```

### Reading

```bash
bird --cookie-source chrome read 123456789
bird --cookie-source chrome thread https://x.com/user/status/123456789
bird --cookie-source chrome replies 123456789 --json
```

### Search (free, via GraphQL)

```bash
bird --cookie-source chrome search "query" -n 10
bird --cookie-source chrome search "from:anthropic" -n 20 --json
```

### Monitoring

```bash
bird --cookie-source chrome mentions -n 10
bird --cookie-source chrome bookmarks -n 20
bird --cookie-source chrome likes -n 20
bird --cookie-source chrome following -n 50
bird --cookie-source chrome followers -n 50
```

### Maintenance

```bash
bird --cookie-source chrome whoami          # verify auth
bird --cookie-source chrome check           # credential sources
bird --cookie-source chrome query-ids --fresh  # refresh when Twitter rotates IDs
```

### Troubleshooting

- **403 errors**: browser cookies expired — log into Twitter in Chrome, then `bird check`
- **Query ID errors**: `bird query-ids --fresh` (works until X changes the schema itself; then bird is done)
- **Rate limiting (429)**: wait a few minutes

## Smaug — Bookmark Archival

```bash
cd ~/tools/smaug
npx smaug run                    # fetch + process with Claude
npx smaug fetch 20               # fetch only
npx smaug fetch --source likes   # likes instead of bookmarks
npx smaug run -t                 # track token costs
npx smaug status
```

Output: `bookmarks.md`, `knowledge/tools/`, `knowledge/articles/`.

## Reference Files

| File | Contents |
|------|----------|
| `references/pricing.md` | Full July 2026 rate card, Owned Reads endpoints, rebates, dedup, worked estimates |
| `references/xurl-mcp-setup.md` | OAuth 2.0 app setup, MCP bridge wiring, xurl usage, self-hosted xMCP |
| `references/setup.md` | Bearer + OAuth 1.0a credential setup, bird/smaug install, credential troubleshooting |
