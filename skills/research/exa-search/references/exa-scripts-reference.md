# Exa Search Scripts: Full Reference

Exa 3.0, OpenAPI spec 2.0.0 (synced 2026-10-19). All scripts live in `~/.claude/skills/exa-search/scripts/`, need `EXA_API_KEY`, and share `_exa_common.py` (auth, error envelopes, warnings/notices, cost, categories, presets). In `--json` mode stdout is exactly one JSON document; hints, warnings, and notes go to stderr. List flags (`--domains`, `--exclude-domains`, `--must-include`, `--additional-queries`, sections) accumulate across repeats; domain flags also split on commas.

---

## exa_search.py: `/search`

| Flag | API field | Notes |
|---|---|---|
| `query` | `query` | Required |
| `--lite` / `--deep-lite` / `--deep` | `type` | Default `auto`. See type table in SKILL.md |
| `--fast` / `--instant` / `--deep-reasoning` / `--neural` | `type` | Legacy; stderr hint |
| `--additional-queries Q...` | `additionalQueries` | deep-lite/deep/deep-reasoning only; max 10 |
| `--text-output DESC` | `outputSchema {type:text}` | Any type but lite |
| `--output-schema JSON` / `--schema-file F` / `--schema-preset P` | `outputSchema` | ≤10 properties in total (nested and array items count), ≤2 levels |
| `--system-prompt S` | `systemPrompt` | Guides synthesized output; not lite |
| `--objective S` | `objective` | What the search is for |
| `--category, -c` | `category` | company, publication, news, personal site, financial report, people (`research paper` → publication; pdf/github soft hints) |
| `-n, --num` | `numResults` | Default 10, max 100; >10 adds $1/1k results |
| `--domains` / `--exclude-domains` | `includeDomains` / `excludeDomains` | |
| `--after` / `--before` | `startPublishedDate` / `endPublishedDate` | YYYY-MM-DD or full ISO |
| `--location` | `userLocation` | `US`, `LAT,LON`, or `US,LAT,LON` |
| `--safe` | `moderation` | |
| `--no-text` | omit `contents.text` | Text is on by default |
| `--max-chars N` | `contents.text.maxCharacters` | |
| `--verbosity` / `--include-sections` / `--exclude-sections` | `contents.text.*` | Need `--max-age-hours 0` |
| `--highlights` | `contents.highlights: true` | |
| `--highlights-query Q` / `--highlights-max-chars N` | `contents.highlights.{query,maxCharacters}` | Imply highlights |
| `--dynamic` | `contents.highlights.dynamic` + `Exa-Beta` header | Beta; not with `--highlights-max-chars` |
| `--summary Q` | `contents.summary.query` | +$1/1k pages; not lite |
| `--max-age-hours N` | `contents.maxAgeHours` | 0 fresh, -1 cache only, max 720 |
| `--snapshot-as-of DATE` | `contents.snapshotAsOf` | PAYG: 100-request trial, ≤5 months back; excludes freshness, `--subpages`, `--category`, `--deep` |
| `--links N` / `--images N` | `contents.extras` | Not lite |
| `--json` / `--cost` | — | Raw JSON / cost breakdown |
| Deprecated: `--must-include`, `--must-exclude`, `--context`, `--context-chars`, `--subpages`, `--subpage-target`, `--livecrawl` | | Sent (livecrawl mapped) with a hint |

Text output order: request ID, notices, results (title, URL, author, date, summary, highlights, text, subpages, extras, entities), structured output with grounding, cost. Entities render for `company`, `person`, and `publication` (title, authors, year, citations, DOI); unknown types print generically.

```bash
python3 exa_search.py "python requests timeout" --lite --highlights --no-text -n 5
python3 exa_search.py "sparse autoencoders" --category publication --after 2026-01-01 --no-text --highlights
python3 exa_search.py "React useEffect cleanup" --domains react.dev,developer.mozilla.org --highlights --no-text
python3 exa_search.py "Who is the CEO of Stripe?" --text-output "One sentence"
python3 exa_search.py "Top AI infra startups 2026" --deep --schema-preset company
python3 exa_search.py "solar install cost trend" --dynamic --no-text -n 15
python3 exa_search.py "pricing page" --domains example.com --snapshot-as-of 2026-07-01
```

---

## exa_contents.py: `/contents`

| Flag | API field | Notes |
|---|---|---|
| `urls...` | `urls` | Required, one or more |
| `--no-text` / `--max-chars N` / `--html` | `text` / `text.maxCharacters` / `text.includeHtmlTags` | |
| `--verbosity` / `--include-sections` / `--exclude-sections` | `text.*` | Need `--max-age-hours 0` |
| `--summary Q` / `--summary-schema JSON` | `summary.{query,schema}` | |
| `--highlights` / `--highlights-query Q` / `--highlights-max-chars N` | `highlights` | |
| `--dynamic` | `highlights.dynamic` + `Exa-Beta` | One budget across all URLs |
| `--subpages N` / `--subpage-target T` | `subpages` / `subpageTarget` | The supported home for subpage crawling |
| `--links N` / `--images N` | `extras` | |
| `--max-age-hours N` / `--timeout MS` | `maxAgeHours` / `livecrawlTimeout` | |
| `--snapshot-as-of DATE` | `snapshotAsOf` | PAYG: 1 URL per request; excludes freshness, `--timeout`, `--subpages` |
| `--json` / `--cost` / `--text-limit N` | — | Display only |
| Ignored with hint: `--sentences`, `--highlights-per-url` | | Exa deprecated them |
| Deprecated: `--livecrawl` (mapped), `--context`, `--context-chars` | | |

Billing: $1/1k pages per content type. Per-URL failures (`statuses[]`) print as a WARNING block and as `Failed:` lines on stderr; exit 1 when every URL failed.

---

## exa_research.py: `/answer` (or `/search` when filtered)

| Flag | Route | Notes |
|---|---|---|
| `query` | both | |
| `--model exa\|exa-pro\|exa-fast\|exa-research` | /answer | All $5/1k (probed 2026-10-19) |
| `--system-prompt S` | both | |
| `--location` | both | `US`, `LAT,LON`, `US,LAT,LON` |
| `--output-schema` / `--schema-file` | both | Structured `answer`; /search route caps at 10 properties, 2 levels |
| `--stream` | /answer | Prints deltas live (UTF-8); citations and cost follow; no `[DONE]` → STREAM_TRUNCATED, exit 1 |
| `--no-text` | both | Omit source text |
| `--highlights` | /search | Ignored with a hint on /answer |
| `--domains`, `--exclude-domains`, `--after`, `--before`, `-n` | → /search | `type auto` + text schema, $7/1k, ~2s slower; stderr note |
| `--sources` / `--markdown` / `--answer-only` / `--json` / `--cost` / `--text-limit` | display | Empty answer → stderr error, exit 4 |

JSON shape (both routes): `answer`, `citations[]` (url, title, author, publishedDate, text…), `costDollars`, `requestId`; the /search route adds `route: "search"`, `grounding[]`, and any `warnings`/`notices`.

---

## exa_agent.py: `/agent/runs`

See `agent-api.md` for effort choice and task writing.

| Command / flag | API | Notes |
|---|---|---|
| `run QUERY` | `POST /agent/runs` | Polls `GET /agent/runs/{id}` every 4s |
| `--effort` | `effort` | minimal, low, medium (default, always sent), high, xhigh, auto, ultra |
| `--output-schema` / `--schema-file` / `--schema-preset` | `outputSchema` | No /search size cap |
| `--max-items N` | `maxItems` on top-level arrays | Needs a schema; keeps list cost bounded |
| `--system-prompt` | `systemPrompt` | |
| `--input-file F` / `--exclude-file F` | `input.data` / `input.exclusion` | JSON array or JSONL of objects |
| `--previous-run ID` | `previousRunId` | Continue a completed run |
| `--data-source P` (repeatable) | `dataSources[].provider` | Exa Connect, ≤5; billed per provider call |
| `--max-cost $` | `budget.maxCostDollars` | 1–100; auto/ultra only |
| `--max-duration S` | `budget.maxDurationSeconds` | 300–10800; ultra only |
| `--user-id ID` | `userIdentifier` | Opaque, no PII |
| `--no-wait` / `--timeout S` / `--json` | — | Timeout or lost polling exits 3 with the resume command; failed/cancelled exit 1 |
| `status ID [--wait]` / `list [--limit --cursor]` / `cancel ID` / `stop ID` | GET / GET / POST cancel / POST stop | Polling retries 3 transient errors; `stop` refuses runs known to be non-ultra |

---

## exa_similar.py: `/findSimilar` (deprecated endpoint)

Prints a deprecation note to stderr on every run; prefer `exa_search.py` with a query describing the page. `--exclude-source` sends the native `excludeSourceDomain`; `--safe` is ignored (the endpoint has no moderation field). Flags: `url`, `-n`, `--category`, `--domains`, `--exclude-domains`, `--exclude-source`, `--after`, `--before`, `--no-text`, `--max-chars`, `--summary`, `--highlights`, `--highlights-query`, `--highlights-max-chars`, `--max-age-hours`, `--livecrawl` (mapped), `--verbosity`, sections, `--subpages`, `--subpage-target`, `--links`, `--images`, `--must-include`, `--must-exclude`, `--safe`, `--context`, `--context-chars`, `--json`, `--cost`, `--text-limit`.

---

## exa_research_async.py: retired

The Research API returns 410 `RESEARCH_RETIRED` (probed 2026-10-19; Exa changelog 2026-04-01). The stub prints the equivalent `exa_agent.py run '…' --effort medium|high` command (`--pro` → `high`; `status`/`list` point to `exa_agent.py list`) and exits 2.

---

## Legacy Flag Map

| Old usage | Now |
|---|---|
| `--fast`, `--instant` | Still sent; prefer `--lite` |
| `--deep-reasoning` | Still sent ($15/1k); prefer `--deep` or `exa_agent.py` |
| `--neural` | Sent as `auto` |
| `--livecrawl always/preferred/never/fallback` | `maxAgeHours` 0 / 1 / -1 / omitted (dropped under `--lite`) |
| `--category "research paper"` | `publication` |
| `--sentences`, `--highlights-per-url` | Ignored (Exa ignores them too) |
| Schema flags required `--deep` | Any type except lite |
| `exa_research.py --domains/--after/-n` silently ignored | Routed to /search and enforced |
| `exa_research.py --sources` printed nothing | Lists `citations` |
| `exa_research_async.py` | `exa_agent.py run` |
| `--domains a --domains b` kept only `b` | Accumulates |

---

## Errors

Search, contents, and answer: `{"error": "text", "tag": "TAG"}`. Agent: `{"error": {"type", "code", "message", "detail"}}`. Both print as `API Error: HTTP <status> <TAG>: <message>` plus the request ID (body, else the `x-request-id` header) and exit 1. Network failures print `API Error: network error (<ExceptionName>): …`; a non-JSON success body prints `INVALID_JSON`. A `Hint:` keyed on the server message names known causes (lite parameter limits, schema size, company/people filter limits).

Exit codes: 0 ok; 1 API/network error, failed or cancelled agent run, or all `/contents` URLs failed; 2 usage error (including the retired stub); 3 agent run still going (timeout or lost polling); 4 `exa_research.py` returned no answer.

## Response Fields Worth Knowing

- `warnings[]` (`IGNORED_FIELD`, …): request problems → stderr.
- `notices[]` (`RESTRICTIONS_RELAXED`, …): how results were produced → printed with results; keep them in context.
- `costDollars`: `total` plus `search{…}`, `contents{…}`, `summary` (search) or `agentCompute`, `search`, `emails`, `phoneNumbers` (agent). There is no `breakDown` field.
- `resolvedSearchType` / `searchType`: deprecated; ignore.

## Exa MCP (for MCP clients, not used by these scripts)

`https://mcp.exa.ai/mcp` (verified 2026-10-19 against exa.ai/docs/get-started/exa-mcp and github.com/exa-labs/exa-mcp-server): default tools `web_search_exa`, `web_fetch_exa`; `agent_run` with OAuth or an API key; `web_search_advanced_exa` opt-in via `?tools=…` (an explicit list replaces the defaults). The scripts expose more of the API: categories, dates, schemas, Dynamic Highlights, snapshots, `/answer` models, and every Agent option.

## Tests

```bash
python3 test_exa.py --quick             # test_offline.py: payloads, routing, SSE/agent fixtures; no key
python3 test_exa.py                     # offline + live (~$0.15)
python3 test_exa.py --endpoint search   # search | contents | similar | answer | agent
```

Fixtures in `scripts/fixtures/` are real responses captured 2026-10-19.
