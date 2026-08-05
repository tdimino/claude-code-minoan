# Query Expansion Protocol

Turn a research request into the set of queries it might be touching — synonyms, hashtags, cashtags, principals, community slang — then fan them out mechanically with `x-search multi`. The expansion happens here, in your reasoning, not inside the CLI: you already understand the user's intent, and a second LLM call would only dilute it.

Grounded in the convergent pattern across production implementations (musharna/data-aggregator-mcp, OiiOAI/Query-Amplifier, rohunvora/x-research-skill, Elastic query-rewriting): 3-4 variants, original always preserved, parallel fan-out, dedup by tweet ID, results anchored on the original intent.

## The Protocol

Given a request like *"what are people saying about the Anthropic fundraise?"*, generate 3-4 query variants, each ≤512 chars (X API limit):

| # | Variant | Example |
|---|---------|---------|
| 0 | **Literal** — the request's own key phrase, verbatim. Never skip; this is the recall floor. | `anthropic fundraise` |
| 1 | **Synonym/hashtag OR-group** — lexical alternatives AND'd with an intent qualifier | `anthropic (raise OR funding OR "series F" OR valuation)` |
| 2 | **Principals** — `from:`/`to:`/`@mention` the accounts closest to the event | `(from:AnthropicAI OR from:DarioAmodei) funding` |
| 3 | **Noise-negated** (optional) — variant 1 minus predictable junk | `anthropic funding -giveaway -airdrop -hiring` |

Boolean shape follows social-listening convention: **anchor term AND (OR-group of expansions) NOT exclusions**. Use `#hashtags` and `$cashtags` where the domain warrants (`$TSLA`, `#LinearA`); include community slang when searching a subculture (what insiders call the thing, not its official name).

## Execution

```bash
# 1. Probe volume first — $0.005 tells you whether variant 1 returns 40 tweets or 40,000
x-search.ts counts 'anthropic (raise OR funding OR "series F")' --today

# 2. Fan out. Dedup by tweet ID is automatic; per-variant footer shows what each contributed
x-search.ts multi "anthropic fundraise" \
  'anthropic (raise OR funding OR "series F" OR valuation)' \
  '(from:AnthropicAI OR from:DarioAmodei) funding' \
  --today --quick

# 3. Validate before spending: --dry-run prints each final query + window + cost ceiling
x-search.ts multi "q1" "q2" --today --dry-run
```

Read the footer: a variant contributing `0 new` on a second pass is exhausted — drop it and refine. A variant erroring fails soft; the run continues without it.

## Rules

- **Variant 0 is sacred.** Expansion adds recall; it never replaces the literal query.
- **Judge merged results against the original request**, not against whichever variant found them — a tweet matching variant 2 can still be off-topic.
- **3-4 variants, not 10.** Each variant costs up to a page of reads; breadth beyond 4 buys noise, not recall.
- **Bird dialect differs.** With `--bird`, the CLI translates its own filters to web operators (`-filter:retweets`) automatically, but operators you write into the query text are NOT translated: `is:retweet`, `is:reply`, `has:media`, `has:links`, `has:images`, `context:`, and `entity:` are API-only and silently ignored by bird's web search. Portable across both: keywords, quoted phrases, `OR`, `-exclusions`, `#hashtags`, `$cashtags`, `from:`/`to:`/`@mentions`, `lang:`.
- **Full-archive variants** (beyond 7 days) go to the xapi MCP `search_posts_all`, not multi.
