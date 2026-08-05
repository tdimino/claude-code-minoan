# x-search — Twitter/X Research for Codex Agents

Cost-tracked X API v2 research CLI. Every read bills real money ($0.005/tweet) — probe cheap, read narrow.

**Prerequisite:** credentials already configured in `~/.claude/skills/twitter/.env` (never read this file).
**Invocation:** `bun run ~/.claude/skills/twitter/x-search/x-search.ts <command>` (abbreviated to `x-search.ts` below).

## Probe Volume First (cheapest signal)

```bash
# $0.005 flat — hourly histogram + what a full read would cost
x-search.ts counts "your query" --today
```

## Search

```bash
x-search.ts search "claude code" --today --quick          # since local midnight, ~10 results
x-search.ts search "minoan" --since 3h --sort likes       # rolling window
x-search.ts search "x api" --since yesterday              # bounded: midnight to midnight
x-search.ts search "query" --from username --quality      # one account, min 10 likes
x-search.ts search "query" --bird --today                 # FREE (session cookies, looser relevance)
x-search.ts search "query" --today --dry-run              # show final query + cost ceiling, no call
```

## Multi-Query Fan-Out

Expand the request into 3-4 variants yourself (literal · synonym/hashtag OR-group · `from:` principals · noise-negated — see `references/query-expansion.md`), then:

```bash
x-search.ts multi "anthropic fundraise" \
  'anthropic (raise OR funding OR "series F")' \
  '(from:AnthropicAI OR from:DarioAmodei) funding' --today --quick
```

Merges all variants, dedups by tweet ID, prints per-variant contribution + combined cost.

## Threads, Profiles, Spend

```bash
x-search.ts thread 1234567890 --pages 2      # full conversation
x-search.ts profile AnthropicAI --today      # user + recent tweets (--count N, default 20)
x-search.ts delete 1234567890                # delete own tweet ($0.01)
x-search.ts usage                            # billed reads vs 2M monthly cap (ground truth)
```

## Key Flags

- `--today` — since local midnight; `--since` accepts `Nm|Nh|Nd (e.g. 15m, 3h, 7d)|today|yesterday|ISO`; `--until` bounds the window
- `--quick` — 1 page, ≤10 results, noise filter, 1hr cache
- `--dry-run` — validate any search/multi/counts without spending
- `--bird` — free path via bird CLI; `--retweets` — include RTs (excluded by default)
- `--json` / `--markdown` / `--save` — output modes

## Strategy

1. `counts` the query ($0.005) — know the volume before reading.
2. `search --quick` or `multi --quick` the expanded variants.
3. Refine with `--from`, `--quality`, tighter windows; `thread` only high-value hits.
4. Check `usage` after heavy sessions. Posting/replying: NOT for autonomous use — text containing URLs bills at $0.20 and is refused without `--allow-url`; always `--dry-run` first.
