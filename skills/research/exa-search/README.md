# Exa Search

Web search, URL extraction, cited answers, and async Agent research through the [Exa API](https://exa.ai). Six Python scripts, raw `requests`, no SDK. Synced to Exa 3.0 / OpenAPI spec 2.0.0 (2026-10-19).

## Prerequisites

```bash
export EXA_API_KEY=your-key-here  # https://dashboard.exa.ai
pip install requests
```

## Scripts

| Script | Endpoint | Purpose |
|--------|----------|---------|
| `exa_search.py` | `/search` | lite/auto/deep-lite/deep search, 6 categories, filters, highlights, structured output |
| `exa_contents.py` | `/contents` | Clean text, highlights, and summaries from known URLs |
| `exa_research.py` | `/answer` | Cited answers; source filters route to `/search` |
| `exa_agent.py` | `/agent/runs` | Async list building, enrichment, multi-hop research |
| `exa_similar.py` | `/findSimilar` | Similar pages (endpoint deprecated by Exa) |
| `exa_research_async.py` | — | Retired stub; points to `exa_agent.py` |
| `_exa_common.py` | — | Shared auth, errors, warnings/notices, cost, presets |

## Quick Start

```bash
python3 scripts/exa_search.py "python requests timeout" --lite --highlights --no-text
python3 scripts/exa_search.py "Top AI infra startups" --deep --schema-preset company
python3 scripts/exa_contents.py URL1 URL2 --highlights-query "pricing" --no-text
python3 scripts/exa_research.py "How does RAG work?" --sources
python3 scripts/exa_research.py "EU AI Act news" --domains europa.eu --after 2026-06-01
python3 scripts/exa_agent.py run "Find 10 Series A AI infra startups from 2026" \
  --schema-preset company --max-items 10 --effort auto --max-cost 3
```

Usage guidance, costs, and gotchas: `SKILL.md`. Every flag: `references/exa-scripts-reference.md`. Agent API: `references/agent-api.md`.

## Directory Structure

```
exa-search/
├── SKILL.md                         # Skill definition (start here)
├── README.md
├── codex-agent-guide.md             # Drop-in guide for Codex CLI agents
├── evals/evals.json                 # skill-optimizer evals
├── references/
│   ├── exa-scripts-reference.md     # Every flag, legacy map, response fields
│   ├── agent-api.md                 # Agent API guide
│   └── exa-docs-2026-10-19/         # Exa docs + OpenAPI spec snapshot
└── scripts/
    ├── _exa_common.py
    ├── exa_search.py  exa_contents.py  exa_research.py  exa_agent.py
    ├── exa_similar.py  exa_research_async.py
    ├── test_exa.py                  # Runner: --quick (offline) or full (live)
    ├── test_offline.py              # Offline tests (patched requests, fixtures)
    └── fixtures/                    # Real API responses captured 2026-10-19
```

## Testing

```bash
python3 scripts/test_exa.py --quick            # Offline: no key, no network
python3 scripts/test_exa.py                    # Offline + live (~$0.15)
python3 scripts/test_exa.py --endpoint agent   # Live tests for one endpoint
```

## References

- [Exa docs](https://exa.ai/docs) · [OpenAPI spec](https://exa.ai/docs/exa-spec.yaml) · [Changelog](https://exa.ai/docs/changelog) · [Exa 3.0](https://exa.ai/blog/exa-3) · [Dashboard](https://dashboard.exa.ai)
