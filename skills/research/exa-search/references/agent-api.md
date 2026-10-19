# Exa Agent API: `exa_agent.py`

Async research runs: list building, enrichment of known records, multi-hop questions, structured output with field-level citations. Replaces the retired Research API (`/research/v0`, `/research/v1` → 410 `RESEARCH_RETIRED`). Source: `exa-docs-2026-10-19/agent_*.md`, spec `/agent/runs`.

## When to use Agent vs Search

| Need | Use |
|---|---|
| Pages for Claude to read and reason over | `exa_search.py` (~1s) |
| One synthesized answer, single retrieval pass | `exa_search.py --text-output` or `exa_research.py` |
| List of unknown size from criteria ("find 10 X that Y") | `exa_agent.py run --effort auto --max-items N` |
| Add fields to records you already have | `exa_agent.py run --input-file rows.json` |
| Several retrieval steps or per-entity verification | `exa_agent.py run` |
| Schema >10 properties in total or >2 nesting levels | `exa_agent.py` (`/search` schemas cap there) |

## Effort

| Effort | Price | Use for |
|---|---|---|
| `minimal` | $0.012 | Narrow lookups (one fact) |
| `low` | $0.025 | Simple lookups, short answers |
| `medium` | $0.10 | **Script default.** Standard research |
| `high` | $0.50 | Harder research, more citations |
| `xhigh` | $1.00 | High-value tasks, complex schemas |
| `auto` | Metered, $5 cap | Variable-scope lists (the API's own default—the script never relies on it) |
| `ultra` | Metered, $20 cap | Exhaustive lists; `--max-duration`, `stop` |

Metered usage: $0.10/ACU, $0.005/search, $0.02/email, $0.07/phone. `--max-cost` ($1–100) applies only to `auto`/`ultra`; fixed efforts reject a budget (the script refuses before sending). Raise effort only after tightening the query.

## Writing the task

- `query` is a task spec: the entity, target count, qualification criteria, evidence bar, and what "complete" means.
- Rows to enrich go in `--input-file` (`input.data`); records to skip go in `--exclude-file` (`input.exclusion`). Never paste tables into the query. Both files accept a JSON array of objects or JSONL.
- Response shape goes in the schema, not the query. Bound every array (`--max-items N` sets `maxItems` on top-level arrays; presets have none). Do not add citation or confidence fields—`output.grounding` already carries them.
- Follow-ups continue a completed run with `--previous-run RUN_ID` instead of re-sending its output.
- `--system-prompt` holds source preferences and novelty or duplication constraints.
- Fields may come back `null` when evidence is missing, even if the schema marks them required; `stopReason: schema_satisfied` means the shape is complete, not that every fact is verified.

## Commands

```bash
A=~/.claude/skills/exa-search/scripts/exa_agent.py
python3 $A run "Who founded Anthropic and when?" --effort low
python3 $A run "Find 10 AI infra startups that raised a Series A in 2026; include only companies with a public announcement" \
  --schema-preset company --max-items 10 --effort auto --max-cost 3
python3 $A run "Add CEO and HQ city for each company" --input-file rows.json --exclude-file seen.json
python3 $A run "..." --effort ultra --max-cost 30 --max-duration 1800 --no-wait   # prints run ID
python3 $A status RUN_ID --wait      # poll a run started with --no-wait
python3 $A list --limit 5
python3 $A cancel RUN_ID             # queued/running run; no results, bills usage so far
python3 $A stop RUN_ID               # ultra only; keeps results so far, bills usage so far
```

`run` (and `status --wait`) polls every 4s until `completed`, `failed`, or `cancelled`. `--timeout` (default 600s) exits 3 if the run is still going; resume with `status RUN_ID --wait`. A `failed` run exits 1. Input files may be a JSON array, a single object, or JSONL. `--json` prints the raw run object.

## Output

- `output.text`: prose answer (always)
- `output.structured`: schema-shaped JSON (`null` without a schema)
- `output.grounding[]`: `{field, citations[{url,title}], confidence: low|medium|high}`; shown as `[H]/[M]/[L]`
- `stopReason`: `schema_satisfied`, `budget_reached`, `time_limit_reached`, `stopped`, `error`, `cancelled`
- `usage`: `agentComputeUnits`, `searches`, `emails`, `phoneNumbers`
- `costDollars`: `total`, `agentCompute`, `search`, `emails`, `phoneNumbers`

## Errors

Agent errors use `{"error": {"type", "code", "message", "detail"}}`, unlike search's `{"error": "text", "tag"}`; the script prints `code`, `message`, and the flattened `detail`. Codes worth knowing: `CONCURRENCY_LIMIT_REACHED` (429—wait or cancel a run), `INVALID_OUTPUT_SCHEMA`, `PREVIOUS_RUN_NOT_COMPLETED`, `RUN_NOT_FOUND`.

## Not wrapped

SSE streaming (`Accept: text/event-stream`) and `/agent/runs/{id}/events`—polling suffices for captured stdout. Exa Connect providers are exposed as `--data-source NAME` (billed per provider call; see `exa-docs-2026-10-19/agent_quickstart.md`).
