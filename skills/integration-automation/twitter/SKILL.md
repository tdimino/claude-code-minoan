---
name: twitter
description: "Search, post, monitor, and archive on Twitter/X via five tools: the official hosted X MCP server (full-archive search, trends, bookmarks, Articles via xurl bridge), x-search CLI (cost-tracked API v2 research with calendar-day windows, volume counts, multi-query fan-out, feeds, watchlists, posting), xurl (official CLI for any endpoint incl. media/DMs), bird CLI (free session-based reads/writes, frozen at 0.8.0), and Smaug bookmark archival. Triggers on: search tweets, tweets from today, what did X tweet, latest tweets from, tweet volume, expand a Twitter query, check Twitter for, post a tweet, tweet this, post to X, reply on Twitter, full-archive search, what's trending, check mentions, my mentions, timeline, DMs, monitor account, research topic on Twitter, my bookmarks, archive bookmarks."
---

# Twitter/X — Multi-Mode Integration

Five tools; choose by task:

| Mode | Tool | Auth | Cost | Use For |
|------|------|------|------|---------|
| **Hosted MCP** | `xapi` MCP server (via xurl bridge) | OAuth 2.0 | pay-per-use | Full-archive search, trends, bookmarks, Articles, timelines |
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
| Gauge tweet volume before reading | x-search counts | $0.005 flat vs $0.005/tweet for reads |
| Search recent tweets by topic | x-search | Cost-tracked, cached, quality filters |
| Broad topic, multiple phrasings | x-search multi | Fan out expanded variants, dedup merge |
| Read a single tweet from a URL | `jina URL` | Free; the one scraper that works on X |
| Daily feed from followed accounts | x-search feed | Batched OR-queries, cheap |
| Monitor specific accounts | x-search watchlist | Batch check with cost tracking |
| Post a text tweet or reply | x-search post/reply | URL-surcharge guard built in |
| Post with media, DMs, Articles | xurl | Official CLI, chunked upload |
| Check actual billed spend | x-search usage | `GET /2/usage/tweets` ground truth |
| Free casual reads / mentions | bird | Free while cookies + GraphQL hold |
| Archive bookmarks | smaug | AI categorization, markdown output |

## Hosted X MCP (`xapi`)

X's first-party MCP server at `https://api.x.com/mcp` (launched June 2026). Six tool groups: Posts, Search (incl. full-archive), Users/timelines, Bookmarks, Trends by WOEID, Articles.

**Wired 2026-07-15** at user scope: `xurl --app main mcp https://api.x.com/mcp`, authenticated as @IdaeanDaktyl via the `main` xurl app (OAuth 2.0, auto-refresh). Verify health with `claude mcp list` (should show `xapi ... ✔ Connected`); if auth breaks, re-run `xurl auth oauth2 --app main`.

Every tool call bills standard pay-per-use rates — treat agentic MCP loops with the same cost discipline as x-search deep searches. Setup, re-auth, and the read-only Bearer fallback: `references/xurl-mcp-setup.md`.

Never read `~/.xurl` (live OAuth tokens) or the skill `.env` values into context.

## x-search — Cost-Governed Research

Run via: `bun run ~/.claude/skills/twitter/x-search/x-search.ts <command>` — the examples below abbreviate this prefix to `x-search.ts`; always use the full `bun run` invocation.

```bash
# Volume probe FIRST: $0.005 flat, histogram + read-cost projection
x-search.ts counts "claude code" --today

# Quick search (default for exploration): 1 page, max 10, noise filter, 1hr cache, ~$0.50
x-search.ts search "AI agents" --quick

# Calendar-day windows: --today = since local midnight; yesterday = bounded day
x-search.ts search "Claude Code" --today --quick
x-search.ts search "Claude Code" --since yesterday
x-search.ts search "query" --today --dry-run          # final query + cost ceiling, no API call

# Multi-query fan-out: expand per references/query-expansion.md, then merge + dedup
x-search.ts multi "anthropic fundraise" 'anthropic (raise OR funding OR "series F")' --today --quick

# Free search via bird session (looser relevance, $0.00)
x-search.ts search "query" --bird --today

# Full search
x-search.ts search "Claude Code" --pages 3 --sort likes --since 1d
x-search.ts search "Minoan archaeology" --markdown --save

# Profiles, threads, single tweets
x-search.ts profile AnthropicAI --count 10
x-search.ts thread 1234567890 --pages 3
x-search.ts tweet 1234567890

# Feeds from named account groups (geopolitics, palestine, all-feeds)
x-search.ts feed geopolitics --today
x-search.ts feed all-feeds --since 7d --markdown --save
x-search.ts feed imetatronink,Megatron_ron --since 1d --bird   # free via bird
x-search.ts feedgroup add tech kaboreas "K8s/infra"            # manage groups
# Feed flags: --today/--since, --limit N (default 4), --bird (free), --dry-run, --no-cache, --markdown, --save

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

Key flags (search + multi):
- **Time**: `--today`, `--since Nm|Nh|Nd (e.g. 15m, 3h, 7d)|today|yesterday|ISO`, `--until <same specs>` — profile and watchlist check take `--today`/`--since` too
- **Scope**: `--quick`, `--pages 1-5`, `--from user`, `--quality`, `--min-likes N`, `--min-impressions N`, `--no-replies`, `--retweets` (RTs excluded by default)
- **Mode**: `--bird` (free), `--dry-run` (no API call), `--json`, `--markdown`, `--save`; counts adds `--granularity minute|hour|day`

Typo'd flags error out instead of leaking into the query. Command aliases exist (`s`, `m`, `c`, `t`, `p`, `f`, `fg`, `wl`, `u`, `rm` for delete). Cache: 15min TTL (1hr quick), auto-pruned on every run; `cache clear` to flush.

When testing or demonstrating post/reply, always use `--dry-run` — the success path publishes a live tweet otherwise.

Setup (Bearer + OAuth 1.0a keys in `~/.claude/skills/twitter/.env`) is done on this machine. Re-setup walkthrough and credential troubleshooting: `references/setup.md`.

### Research methodology

1. **Expand** the request into 3-4 query variants per `references/query-expansion.md` (literal · synonym/hashtag OR-group · `from:` principals · noise-negated), 2. **counts** the broadest variant ($0.005 — know the volume before paying for reads), 3. **multi `--quick`** to fan out and assess signal, 4. **refine** with `--from`/`--quality`/`--today`/`--since`, 5. **thread** high-value conversations, 6. **deep-dive** best queries with `--pages 3 --markdown --save`, 7. **synthesize** against the original request, not the variant that matched. Reach for the xapi MCP when the answer predates the 7-day window (`search_posts_all`; `get_posts_counts_recent` is the MCP twin of counts).

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

## Bundled Files

| File | Contents |
|------|----------|
| `references/pricing.md` | Full July 2026 rate card, Owned Reads endpoints, rebates, dedup, worked estimates |
| `references/query-expansion.md` | Protocol: abstract a request into 3-4 query variants, fan out with `multi` |
| `references/xurl-mcp-setup.md` | OAuth 2.0 app setup, MCP bridge wiring, xurl usage, self-hosted xMCP |
| `references/setup.md` | Bearer + OAuth 1.0a credential setup, bird/smaug install, credential troubleshooting |
| `codex-agent-guide.md` | Self-contained x-search guide for Codex CLI agents (exa-search pattern) |

## Adjacent Tools

Leave this skill when: a single tweet URL needs reading (`jina URL` — free, and the only scraper X doesn't block), a social sweep spans Reddit/Instagram too (omnisearch's Xpoz route), or a free browser-session action beats an API call (opencli's twitter commands; its docs already defer deep research back to x-search).
