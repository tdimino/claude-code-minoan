---
name: exa
description: Use when building web search, content extraction, or long-running
  research workflows. Reach for Exa when you need to find relevant web pages,
  extract clean content from URLs, build structured lists from open-ended
  criteria, or enrich data with web research. Use Search for fast single-pass
  retrieval, Agent for async list building and multi-hop research, and Contents
  for extracting text from known URLs.
metadata:
  mintlify-proj: exa
  version: "1.0"
---

# Exa Skill

Exa is a web search and research API with three core endpoints: Search (fast retrieval with highlights), Agent (async list building and enrichment), and Contents (text extraction from URLs). Use it to power web search in applications, build research workflows, or enrich data with web context.

## Product summary

Exa provides three APIs for different tasks:

- **Search API** (`POST /search`): Fast web search returning ranked results with highlights, full text, or summaries. Default latency ~1 second. Use for single-pass retrieval.
- **Agent API** (`POST /agent/runs`): Async research orchestrator for list building, enrichment, and multi-hop tasks. Returns structured JSON with field-level citations. Runs take seconds to minutes.
- **Contents API** (`POST /contents`): Extract clean text, highlights, or summaries from known URLs. Use when you already have URLs.

All APIs require an `EXA_API_KEY` environment variable. Install SDKs: `pip install exa-py` (Python) or `npm install exa-js` (JavaScript). See the [primary docs](https://exa.ai/docs) and [API reference](https://exa.ai/docs/reference/search).

## When to use

**Use Search when:**
- You need web results in under 2 seconds
- A single retrieval pass answers the question
- You're building a search tool for an LLM or agent
- Results will be ranked and filtered by downstream logic

**Use Agent when:**
- Building a list from open-ended criteria (e.g., "find 10 companies matching X")
- Enriching existing records with web research
- Multi-hop research is needed (e.g., "find companies, then find their decision makers")
- Output must be structured JSON with field-level citations
- The task can wait seconds to minutes for completion

**Use Contents when:**
- You already have URLs and need clean text
- Extracting highlights or summaries from specific pages
- Following links from a starting URL (subpage crawling)

## Quick reference

### Search API essentials

```python
from exa_py import Exa
exa = Exa()  # reads EXA_API_KEY from environment

# Basic search with highlights
result = exa.search(
    "recent AI infrastructure funding announcements",
    contents={"highlights": True}
)

# With structured output
result = exa.search(
    "AI companies that raised Series A in 2026",
    output_schema={
        "type": "object",
        "properties": {
            "companies": {
                "type": "array",
                "items": {"type": "object", "properties": {"name": {"type": "string"}}}
            }
        }
    }
)
```

### Agent API essentials

```python
# Create a run (async)
run = exa.agent.runs.create(
    query="Find 10 engineering leaders at AI infrastructure companies that raised Series A in the last 6 months.",
    output_schema={...},
    effort="auto"  # or "low", "medium", "high", "xhigh", "ultra"
)

# Poll for completion
run = exa.agent.runs.poll_until_finished(run.id, poll_interval=4000)

# Or stream events
events = exa.agent.runs.create(query="...", stream=True)
for event in events:
    print(event.event, event.data)
```

### Contents API essentials

```python
# Extract highlights from URLs
result = exa.get_contents(
    ["https://example.com/page"],
    highlights={"query": "pricing and features"}
)

# Extract full text with character limit
result = exa.get_contents(
    ["https://example.com/page"],
    text={"max_characters": 10000}
)
```

### Search types and latency

| Type | Latency | Use when |
|------|---------|----------|
| `instant` | ~250ms | Real-time paths (autocomplete, voice) |
| `fast` | ~450ms | Latency-sensitive requests |
| `auto` | ~1s | Default; best quality/speed balance |
| `deep-lite` | ~4s | Lightweight research and synthesis |
| `deep` | 4–15s | Multi-step search and stronger synthesis |
| `deep-reasoning` | 12–40s | Completeness matters more than latency |

### Agent effort levels and cost

| Effort | Price | Best for |
|--------|-------|----------|
| `minimal` | $0.012/req | Lowest-cost lookups, narrow tasks |
| `low` | $0.025/req | Simple lookups, short answers |
| `medium` | $0.10/req | Standard research (default starting point) |
| `high` | $0.50/req | Harder research, more citations |
| `xhigh` | $1.00/req | High-value tasks, complex schemas |
| `auto` | Metered; $5 cap | Variable-scope work, list building |
| `ultra` | Metered; $20 cap | Large list building, exhaustive research |

## Decision guidance

### Search vs. Agent vs. Contents

| Need | Use | Why |
|------|-----|-----|
| Ranked web pages for a query | Search | Fast, single pass, no async overhead |
| Structured list from criteria | Agent | Orchestrates multiple searches, verifies results |
| Enrich existing records | Agent | Processes rows, adds fields, returns structured output |
| Extract text from known URLs | Contents | No search needed, direct extraction |
| Synthesis across many results | Deep Search or Agent | Single Search pass may not gather enough evidence |
| Real-time search tool | Search with `instant` | Lowest latency, cached content only |

### Search output shapes

| Shape | Use when | Token efficiency |
|-------|----------|------------------|
| `highlights: true` | Default for agents and RAG | 5x fewer tokens than full text |
| `text: {maxCharacters: N}` | Need broader context or document structure | Full page content, larger payload |
| `summary: {query: "..."}` | Need generated overview | Adds LLM call per result |

### Agent vs. Search for structured output

| Scenario | Use |
|----------|-----|
| Single search, extract fields from results | Search with `outputSchema` |
| Multiple searches needed to fill schema | Agent with `outputSchema` |
| Schema has 3+ fields or complex nesting | Agent (Search has limits) |
| Need per-entity verification | Agent |
| Need contact enrichment (email/phone) | Agent |

## Workflow

### Search workflow

1. **Write a natural-language query** — Include subject, source type, and time period if relevant. Example: "Recent technical articles on RAG retrieval optimization"
2. **Choose search type** — Use `auto` by default; pick `fast`/`instant` for latency, `deep` for synthesis
3. **Select output shape** — Use `highlights: true` for most tasks; add `outputSchema` only if you need synthesis
4. **Add filters only when necessary** — Use `includeDomains` or `excludeDomains` only when results outside the constraint are unusable
5. **Make the request** — Call `/search` and read `results[]` for ranked pages
6. **Check warnings and notices** — Pass `notices` to your model; log `warnings` for debugging

### Agent workflow

1. **Write a task specification** — Name what to find, scope, evidence required, and what complete looks like. Put existing rows in `input.data`, exclusions in `input.exclusion`
2. **Define output schema** — Use JSON Schema for structured fields; make uncertain fields nullable
3. **Choose effort** — Use `medium` for standard research; `auto` for variable-scope work; `low` for cost-sensitive tasks
4. **Create the run** — Call `/agent/runs` and save the returned `id`
5. **Wait for completion** — Poll `GET /agent/runs/{id}` or stream events with `Accept: text/event-stream`
6. **Read the result** — Extract `output.text` (prose), `output.structured` (JSON), and `output.grounding` (citations)
7. **Handle failures** — Check `stopReason` and `error` fields; retry with adjusted query or effort if needed

### Contents workflow

1. **Collect URLs** — From search results or external sources
2. **Choose content type** — `highlights` for excerpts, `text` for full page, `summary` for generated overview
3. **Add query for highlights** — Pass `highlights: {query: "..."}` to focus extraction
4. **Make the request** — Call `/contents` with URL list
5. **Check statuses** — Verify each URL succeeded in `statuses[]`
6. **Use the content** — Read `results[].highlights`, `results[].text`, or `results[].summary`

## Common gotchas

- **Confusing `/search` and `/contents` nesting** — Search nests content options under `contents: { highlights: true }`. Contents has no wrapper: `highlights: true` at top level.
- **Requesting multiple content views** — Highlights, text, and summary are billed separately. Request one per call unless you need both.
- **Forgetting to poll Agent runs** — Agent is async. The create response is not the final result. Always poll or stream until `completed`, `failed`, or `cancelled`.
- **Unbounded arrays in Agent schemas** — Always set `maxItems` on arrays to keep cost predictable. Without it, list building can return hundreds of items.
- **Putting everything in the query** — Keep research instructions in `query`, existing rows in `input.data`, exclusions in `input.exclusion`, and response shape in `outputSchema`.
- **Using `deep` when `auto` is enough** — Deep modes add latency and cost. Use them only when a single retrieval pass cannot gather enough evidence.
- **Ignoring warnings and notices** — Warnings describe request issues (e.g., ignored fields). Notices describe how results were produced (e.g., query restrictions relaxed). Log warnings; pass notices to models.
- **Not setting `userIdentifier`** — When calling Exa on behalf of end users, pass an opaque user ID so usage is attributed correctly. Never send email, phone, or name.
- **Stale content in Contents** — By default, cached content is used. Set `maxAgeHours: 0` only when freshness is critical (e.g., prices, availability).
- **Deprecated parameters** — Old examples use `useAutoprompt`, `includeUrls`, `livecrawl: "always"`, `tokensNum`. These are removed. Use current API reference.

## Verification checklist

Before submitting work with Exa:

- [ ] API key is set as `EXA_API_KEY` environment variable or passed explicitly
- [ ] Query is natural language, not a bag of keywords
- [ ] For Search: output shape matches the task (highlights for agents, text for broad context, summary for generated overview)
- [ ] For Agent: `outputSchema` is valid JSON Schema with bounded arrays (`maxItems`), and uncertain fields are nullable
- [ ] For Agent: `query` describes the task; rows go in `input.data`; exclusions go in `input.exclusion`
- [ ] Filters (`includeDomains`, `excludeDomains`, date ranges) are only used when results outside them are unusable
- [ ] Agent runs are polled or streamed to completion; create response is not the final result
- [ ] `userIdentifier` is set when calling on behalf of end users (opaque value only, no PII)
- [ ] Warnings are logged; notices are passed to models
- [ ] Cost is within budget (check `costDollars` in response; set `budget.maxCostDollars` for Agent if needed)
- [ ] No deprecated parameters are used (check API reference for current schema)

## Resources

- **Comprehensive navigation**: [llms.txt](https://exa.ai/docs/llms.txt) — Full page-by-page listing for agent navigation
- **Search API quickstart**: [exa.ai/docs/search/quickstart](https://exa.ai/docs/search/quickstart) — Core request shapes, filters, output, and freshness
- **Agent API quickstart**: [exa.ai/docs/agent/quickstart](https://exa.ai/docs/agent/quickstart) — Create runs, stream events, set effort, read structured output
- **Best practices**: [exa.ai/docs/search/best-practices](https://exa.ai/docs/search/best-practices) — Retrieval quality, latency, context, and synthesis tuning

---

> For additional documentation and navigation, see: https://exa.ai/docs/llms.txt