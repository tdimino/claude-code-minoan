---
name: exa-search
description: Searches the web through Exa 3.0 with six Python scripts—lite/auto/deep search with category, domain, and date filters, Dynamic Highlights, structured output with field-level citations, clean extraction from known URLs, cited answers, and the async Agent API for list building, enrichment, and multi-hop research. This skill should be used for any web search, fact lookup, current events, finding papers, companies, people, or news, reading known URLs, questions that need cited answers, building lists of entities that match criteria, or enriching records with web data. It is the default web search tool (built-in WebSearch is blocked). Triggers on search the web, look up, find pages, research with citations, Exa, list of companies, enrich.
---

# Exa Search

Six scripts over Exa 3.0 (API spec 2.0.0, synced 2026-10-19). `S=~/.claude/skills/exa-search/scripts`.

**Prerequisite:** `EXA_API_KEY` (https://dashboard.exa.ai).

## Pick the Script

| Task | Command |
|---|---|
| Quick lookup, cheapest | `python3 $S/exa_search.py "query" --lite --highlights --no-text` |
| General web search | `python3 $S/exa_search.py "query" --highlights --no-text` |
| Papers / companies / people / news | `... exa_search.py "query" --category publication` (or `company`, `people`, `news`) |
| Read known URLs | `python3 $S/exa_contents.py URL1 URL2 --highlights --no-text` |
| Cited answer | `python3 $S/exa_research.py "question" --sources` |
| Cited answer from specific sites/dates | `... exa_research.py "question" --domains a.org --after 2026-01-01` (routes to /search) |
| One synthesized answer or JSON from a search | `... exa_search.py "question" --text-output "Short answer"` / `--schema-preset company` |
| Multi-step research, lists, enrichment | `python3 $S/exa_agent.py run "task" --effort medium` (see `references/agent-api.md`) |
| Pages like a URL | `python3 $S/exa_similar.py URL` (deprecated endpoint; prefer a descriptive `exa_search.py` query) |

## Token-Efficient Recipe

Search cheaply → pick URLs → extract selectively → reason.

```bash
python3 $S/exa_search.py "query" --lite --highlights --no-text -n 10      # ranked excerpts, no full text
python3 $S/exa_contents.py URL1 URL2 --highlights-query "what I need" --no-text
python3 $S/exa_contents.py URL1 --max-chars 5000                          # full text only when needed
```

- Highlights beat full text: 500 chars of highlights match 8,000 chars of text on SimpleQA.
- Text is **on by default** in `exa_search.py`; `--no-text` saves context, not dollars (lite and auto bundle contents for 10 results).
- `--dynamic` (Dynamic Highlights) shares one budget across all results—use it when the results feed one context.
- Filter at the API: `--domains`, `--exclude-domains`, `--category`, `--after/--before`.
- Post-filter JSON: `... --json | python3 ~/.claude/skills/firecrawl/scripts/filter_web_results.py --fields "title,url,highlights" --max-chars 3000`.

## Search Types and Cost

| Flag | Latency | $/1k requests | Notes |
|---|---|---|---|
| `--lite` | ~450ms | $4 | Cache only. Accepts query, `--objective`, category, `-n`, domains, dates, text, highlights, `--snapshot-as-of`, `--location`, `--safe`—nothing else |
| (default `auto`) | ~1s | $7 | Best balance; full parameter set |
| `--deep-lite` | ~4s | $12 | Lightweight synthesis; `--additional-queries` |
| `--deep` | 4–15s | $12 | Multi-step search and synthesis |
| legacy `--fast` / `--instant` / `--deep-reasoning` / `--neural` | — | $7 / $4 / $15 / — | Still accepted with a stderr hint |

Extras: results above 10 add $1/1k; `--summary` adds $1/1k pages; `exa_contents.py` is $1/1k pages per content type; `exa_research.py` is $5/1k. Agent runs: `medium` $0.10 (script default), `auto` metered ≤$5, `ultra` metered ≤$20; full effort table in `references/agent-api.md`.

## Structured Output

`--text-output "desc"`, `--output-schema JSON`, `--schema-file F`, or `--schema-preset` (`company`, `paper-survey`, `competitor-analysis`, `person`, `news-digest`) work on **every type except lite**, within **10 properties in total** (nested and array-item properties count) and 2 levels; every array needs `items`. The answer arrives in `output.content`; `output.grounding` gives per-field citations with `[H]/[M]/[L]` confidence. Add `--system-prompt` for format or tone.

## Gotchas

- **`/answer` has no source filters.** `exa_research.py` sends `--domains`, `--exclude-domains`, `--after`, `--before`, and `-n` to `/search` (auto + text schema, $7/1k) and says so on stderr. Without them it uses `/answer`, where `--model exa|exa-pro|exa-fast|exa-research` and `--stream` apply.
- **Lite rejects** summary, schemas, system prompts, freshness, context, subpages, and extras with a 400 that names the field. Drop `--lite`.
- **Lite drops uncached pages** when text or highlights are requested, so fewer than `-n` results is normal; rerun without `--lite` when coverage matters.
- **`/search` object schemas cap at 10 properties in total and 2 nesting levels.** Larger shapes go to `exa_agent.py`. Never add citation or confidence fields—grounding has them.
- **`--dynamic`** sends the `Exa-Beta: dynamic-highlights-2026-08-28` header and cannot combine with `--highlights-max-chars`.
- **`--category company`/`people`** reject `--after/--before`; `people` also rejects `--exclude-domains`.
- **Categories:** `research paper` is now `publication` (auto-mapped); `pdf`/`github` were deprecated in Exa's 2026-07-23 changelog and now pass as soft hints; `tweet` is rejected.
- **Warnings vs notices:** warnings (ignored or deprecated fields) go to stderr; notices (e.g. restrictions relaxed) print with the results—read them before trusting the results.
- **Repeated list flags accumulate:** `--domains a.com --domains b.com` and `--domains a.com,b.com` both send both domains.
- **Freshness:** `--max-age-hours 0` always fetches fresh, `-1` is cache only. `--livecrawl` still works but is mapped (always→0, preferred→1, never→-1). `--snapshot-as-of DATE` returns historical versions: pay-as-you-go gets a 100-request trial, a rolling 5-month window, and 10 results or 1 contents URL per request; Free gets 403. It excludes freshness flags, `--subpages`, `--category`, and `--deep`.
- **Deprecated but sent:** `--must-include/--must-exclude` (approximate word matching), `--context`, and `--subpages` on search (use `exa_contents.py --subpages`).
- **Retired:** `exa_research_async.py` (Research API returns 410, probed 2026-10-19) prints the `exa_agent.py` equivalent and exits 2.
- **Agent runs are async and cost money:** the script always sends `--effort` (default `medium`) and polls to completion. Pair `--effort auto`/`ultra` with `--max-cost` (otherwise the cap is $5/$20); fixed efforts reject it. If polling is lost, the run continues and the script prints `status RUN_ID --wait` (exit 3).
- **Exit codes:** 0 ok; 1 API, network, or failed/cancelled run; 2 usage; 3 agent run still going; 4 `exa_research.py` got no answer. `exa_contents.py` exits 1 when every URL failed.

## Exa vs Other Tools

| Need | Tool |
|---|---|
| Semantic search, papers, companies, people | Exa `exa_search.py` |
| Researched lists, enrichment, multi-hop | Exa `exa_agent.py` |
| Single page → clean markdown | Firecrawl `scrape --only-main-content` |
| Crawl an entire site | Firecrawl `crawl` |
| Twitter/X content | `jina URL` |
| Exa inside an MCP client | `https://mcp.exa.ai/mcp` (`web_search_exa`, `web_fetch_exa`, `web_search_advanced_exa`, `agent_run`) |

## References

| File | Contents |
|---|---|
| `references/exa-scripts-reference.md` | Every flag of every script, legacy-flag map, output shapes, tests |
| `references/agent-api.md` | Agent API: effort choice, task writing, schemas, budgets, run lifecycle |
| `references/exa-docs-2026-10-19/` | Exa docs and OpenAPI spec snapshot (source of truth for this sync) |

## Tests

```bash
python3 $S/test_exa.py --quick              # offline: no key, no network
python3 $S/test_exa.py                      # offline + live (~$0.15)
python3 $S/test_exa.py --endpoint agent     # live, one endpoint
```
