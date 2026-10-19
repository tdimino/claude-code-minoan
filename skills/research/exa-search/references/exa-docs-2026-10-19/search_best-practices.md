> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Search Best Practices

> Tune retrieval quality, latency, context, and synthesis for production Search API integrations.

This guide assumes you already have a working [Search API request](/docs/search/quickstart). It covers how to improve that request following Exa's recommended best practices.

## Start with the smallest useful request

The best baseline is a natural-language query with `highlights: true`. Exa sizes each result's excerpts to its relevance, so there is no character budget to tune:

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "Recent technical articles comparing hybrid and semantic retrieval for RAG systems",
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search(
    "Recent technical articles comparing hybrid and semantic retrieval for RAG systems",
    { contents: { highlights: true } }
  );
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Recent technical articles comparing hybrid and semantic retrieval for RAG systems",
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

This gives you ranked pages and token-efficient context per page, relevant to the query.

Add additional parameters only as needed:

| Parameter | Add it when |
| - | - |
| `type` | Adjusting to meet a latency budget or depth requirement |
| `numResults` | Fewer pages for a smaller context window, or more for broader recall |
| `objective` | An agent is searching as one step of a larger task; pass the goal that step serves |
| `outputSchema` | Synthesizing results or structuring them into JSON |
| `maxAgeHours` | Cached page content may be too old |
| `highlights.maxCharacters` | Your application requires a fixed excerpt limit per page |
| Domain or date filters | Results outside the constraint would be unusable |

## Search vs. Deep Search

Standard search retrieves and ranks pages for a query. Deep Search runs a research process that can
search iteratively, inspect what it found, refine the search, and synthesize a grounded result.

| Need | Start with |
| - | - |
| Ranked pages for a well-formed query | `auto`, or `lite` when cost or latency matters most |
| Difficult searches, synthesis across many results, or structured outputs that cannot be filled with a single search (3+ fields) | `deep` |
| Long-running research, list building, or multi-hop enrichment | [Exa Agent](/docs/agent/quickstart) |

Deep modes are recommended by default when using `outputSchema`. Read the [Deep Search guide](/docs/search/deep-search) for full instructions and examples.

## Improve retrieval quality

When results need improvement, change one part of the request at a time.

<Steps>
  <Step title="Clarify the query">
    Describe the pages you want, not a bag of keywords. Include the subject and any source type,
    time period, or other detail that changes what a relevant result looks like.

    ```text theme={null}
    Benchmark papers evaluating long-context retrieval methods on legal documents
    ```
  </Step>

  <Step title="Read the response in layers">
    Look at the titles, URLs, publication dates, and highlights before changing the request.

    ```json theme={null}
    {
      "results": [
        {
          "title": "Long-Context Retrieval Methods on Legal Documents",
          "url": "https://arxiv.org/abs/2608.00000",
          "publishedDate": "2026-08-26T00:00:00.000Z",
          "highlights": [
            "We compare long-context retrieval methods across legal document benchmarks..."
          ]
        }
      ]
    }
    ```

    The title and URL show the kind of source Exa retrieved, `publishedDate` shows
    its recency, and the highlight shows the evidence that matched the query. Refine the query to
    retrieve different pages, add date filters to narrow the time period, or fetch full text when
    you need more context from a useful result.
  </Step>

  <Step title="Add only hard constraints">
    Use `includeDomains`, `excludeDomains`, and publication-date filters only when a result that
    violates the constraint cannot be used. Put retrieval preferences in the query and, when
    synthesizing, put response instructions in `systemPrompt`.
  </Step>

  <Step title="Change the search mode last">
    Use a faster mode for a latency requirement or a deep mode when the retrieval process itself
    needs iteration and reasoning. A different mode cannot repair an underspecified query.
  </Step>
</Steps>

### Pass the objective from agents

`objective` is the broader goal behind a search: the task the search is one step of. The query says what to retrieve; the objective says what that task needs from the results, such as which documents should rank first, which to exclude, and which facts or figures to pull. It is most useful when a model picks the `query` as part of a larger task.

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "H100 hourly pricing on major cloud providers",
      objective="Compare H100 cloud pricing across providers for a cost report; prefer official pricing pages over blog posts and pull the on-demand hourly rate from each.",
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("H100 hourly pricing on major cloud providers", {
    objective:
      "Compare H100 cloud pricing across providers for a cost report; prefer official pricing pages over blog posts and pull the on-demand hourly rate from each.",
    contents: { highlights: true },
  });
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "H100 hourly pricing on major cloud providers",
      "objective": "Compare H100 cloud pricing across providers for a cost report; prefer official pricing pages over blog posts and pull the on-demand hourly rate from each.",
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

When you expose Search to a model as a tool, add `objective` as a required string parameter with a description that tells the model what the search turn is trying to achieve. We recommend the wording below verbatim, which is what the [Exa MCP server](/docs/get-started/exa-mcp) uses:

```text theme={null}
Goal for this search turn; say which documents should rank first, which should be excluded, and what specific facts or figures to pull from them.
```

<Tip>
  The exa-py and exa-js `web_search` [tool-calling helpers](/docs/integrations/tool-calling/openai) do this automatically.

  If you define the tool manually, use the schema above.
</Tip>

Keep a small set of representative queries while tuning. Compare result relevance and downstream task success across the set instead of optimizing for one example. Record `requestId`, `searchTime`, and `costDollars` so regressions are reproducible.

## Budget latency and context

Each control spends a different resource:

| Control | What it adds |
| - | - |
| More results | More pages, response data, and downstream context |
| Full text | Broader page context and a larger payload |
| `summary` | One additional language model call per result |
| `outputSchema` | Synthesis across the retrieved results |
| `contents.maxAgeHours: 0` | A fresh page fetch instead of cached content |
| Deep search types | Iterative search, synthesis, and reasoning |

`lite` serves cached content only and rejects `contents.maxAgeHours` with any value, including `-1`. For a real-time path where cached content is acceptable, use `lite` with highlights and no freshness options:

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "Recent product updates from major AI labs",
      type="lite",
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("Recent product updates from major AI labs", {
    type: "lite",
    contents: {
      highlights: true
    }
  });
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Recent product updates from major AI labs",
      "type": "lite",
      "contents": {
        "highlights": true
      }
    }'
  ```
</CodeGroup>

Do not use this recipe when page freshness is part of correctness. Start from `auto` and default freshness unless the product has a measured latency target.

To let Exa allocate one context budget across the whole result set — more from strong sources, less from redundant ones — see the [Dynamic Highlights research preview](/docs/search/highlights#dynamic-highlights).

## Tips for common use cases

| If you need | Use | Avoid |
| - | - | - |
| Newer publications | Put the time window in the query or use publication-date filters | `maxAgeHours` |
| Fresh content from pages that change | `contents.maxAgeHours` | Publication-date filters |
| A preferred kind of source | Query phrasing; `systemPrompt` when synthesizing | A hard domain allowlist |
| The task an agent's search serves | `objective` | Pasting the whole task description into `query` |
| Results only from approved sources | `includeDomains` | Repeating `site:` in the query |
| A small structured output | `outputSchema` with standard Search | Choosing Deep only because the output is JSON |
| A multi-item researched output | `deep` with `outputSchema`, or [Exa Agent](/docs/agent/quickstart) | Expecting one retrieval pass to gather every item |
| More context from a few pages | Search with highlights, then call Contents | Full text for every result |
| Lower latency | Measure `lite` with compact content | Adding freshness or synthesis controls by default |

<h2 id="user-identifier">
  Attribute requests to your end users
</h2>

When your application calls Exa on behalf of its own users, set `userIdentifier` to an identifier for the user each request is for. Exa records it with the request so usage, and any abuse, can be attributed to one end user instead of your whole team.

* Send an opaque value your platform generates, such as a UUID or a hash of your internal user ID. Never send an email address, phone number, username, or name.
* Use 1 to 64 characters: letters, digits, `_`, and `-`. Any other string returns a `400` error; `null` is the same as omitting the field.
* It is telemetry only. It does not change results or caching, is not returned in the response, and does not authenticate the user.
* Exa keeps it even when your team has [Zero Data Retention](/docs/admin/security/zero-data-retention) enabled, which is why it must not contain personal information.

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "hottest AI startups",
      contents={"highlights": True},
      user_identifier="7f3a9c52-1d4e-4b8a-9e60-2c5d8a1f0b37",
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("hottest AI startups", {
    contents: { highlights: true },
    userIdentifier: "7f3a9c52-1d4e-4b8a-9e60-2c5d8a1f0b37"
  });
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "hottest AI startups",
      "contents": { "highlights": true },
      "userIdentifier": "7f3a9c52-1d4e-4b8a-9e60-2c5d8a1f0b37"
    }'
  ```
</CodeGroup>

`/contents`, `/answer`, and `/agent/runs` take the same top-level field. In the SDKs it is `user_identifier` (Python) or `userIdentifier` (JavaScript) on `search`, `get_contents` / `getContents`, `answer`, `stream_answer` / `streamAnswer`, and `agent.runs.create`. An Agent run attributes the searches it makes to the same user, and a follow-up run (`previousRunId`) that sends no `userIdentifier` keeps the one from the run it continues.

## Common mistakes

Requests copied from older examples often include parameters that are removed, deprecated, or belong somewhere else in the request. The [API reference](/docs/reference/search) is the source of truth for the current schema.

| Instead of | Use |
| - | - |
| `useAutoprompt` | Nothing. Exa interprets the query directly; remove the field. |
| `includeUrls`, `excludeUrls` | `includeDomains`, `excludeDomains`. Each entry can be a hostname, a hostname with a path prefix, or a wildcard subdomain. |
| Top-level `text`, `highlights`, or `summary` | The same fields nested under `contents` (for example, `contents: { highlights: true }`). |
| `numSentences`, `highlightsPerUrl` | `contents.highlights: true`. Exa sizes highlights to each result; set `highlights.maxCharacters` only for a fixed excerpt limit. |
| `tokensNum` | `contents.text.maxCharacters`. |
| `livecrawl: "always"` | `contents.maxAgeHours: 0`. Do not send `livecrawl` and `maxAgeHours` together. |
| `contents.crawledBeforeDate` | `contents.snapshotAsOf`. |
| `contents.context` | `contents.highlights` or `contents.text`; build the context string from `results[]`. |
| `includeText`, `excludeText` | The terms in the query itself. Both filters are deprecated. |
| `startCrawlDate`, `endCrawlDate` | `startPublishedDate`, `endPublishedDate`. The crawl-date fields are ignored. |

A few behaviors that are easy to miss:

* The Python SDK uses snake\_case for every key, including nested ones: `contents={"highlights": True, "max_age_hours": 24}`.
* `stream: true` returns server-sent events only when `outputSchema` is set. Without a schema, the response is the normal JSON body.
* `highlights`, `text`, and `summary` can be combined in one request, but each view is billed separately. Request one view unless the task needs both.

## Warnings and notices

Pass the `notices` in a `/search` response to your model with the results, and log the `warnings`. A notice describes how the results were produced and is written for the model that reads them. A warning describes the request, such as a field that has no effect, and is written for the developer who maintains the code that builds the request. Never pass a warning to a model.

The Python and JavaScript SDKs log warnings for you, and their web search tools pass notices to the model with the results. [SDK warnings](/docs/sdks/quickstart#warnings) shows how to silence warnings or send them to your own logger.

Neither array changes the status code, and each array is omitted when it is empty. With `stream: true`, `warnings` and `notices` arrive on the event with `type: "results"`.

Each warning and notice has a machine-readable `code`, a `path` that points to the request field as a JSON Pointer, and a `message` that is complete on its own. Codes are an open set. Handle a code you do not recognize by its `message` instead of failing. To keep a notice from your model, drop it by `code`, or forward only the codes your application handles. The [API reference](/docs/reference/search) describes every field, including the optional `details` object on a notice.

### Warning codes

| Code | Meaning |
| - | - |
| `IGNORED_FIELD` | The field at `path` has no effect on the search. The request set a field that the API accepts and ignores, such as `startCrawlDate`, or sent a `contents` option such as `text` at the top level instead of under `contents`. Each ignored field gets its own warning, whose `message` says what to remove or what to send instead. |

```json theme={null}
{
  "requestId": "ed09886aba86775df99b0b5cbc9d4bff",
  "results": [
    { "title": "Rust Release Notes", "url": "https://doc.rust-lang.org/releases.html" }
  ],
  "warnings": [
    {
      "code": "IGNORED_FIELD",
      "path": "/startCrawlDate",
      "message": "startCrawlDate is no longer supported and is ignored. Remove it from the request."
    }
  ]
}
```

### Notice codes

| Code | Meaning |
| - | - |
| `RESTRICTIONS_RELAXED` | No results matched the `site:` operators or quoted phrases in the query, so the results come from a search with those operators removed. Filters in the request body, such as `includeDomains`, still apply. `path` is `/query`, and `details.relaxed` lists the removed operators. |

```json theme={null}
{
  "requestId": "b3f5a7c1d2e94f6a8b0c1d2e3f4a5b6c",
  "results": [
    { "title": "Statistics About Diabetes", "url": "https://diabetes.org/about-diabetes/statistics/about-diabetes" }
  ],
  "notices": [
    {
      "code": "RESTRICTIONS_RELAXED",
      "path": "/query",
      "message": "No results matched the site restriction site:usa.diabetes.org in the query; these results come from a search with that restriction removed.",
      "details": {
        "relaxed": [{ "kind": "site", "operator": "site:usa.diabetes.org" }]
      }
    }
  ]
}
```

## When to use another endpoint

Use a different Exa endpoint when the task changes shape:

| Task | Use |
| - | - |
| Long-running research, list building, or enrichment | [Exa Agent](/docs/agent/quickstart) |
| The URLs are already known | [Contents](/docs/contents/quickstart) |
| Run a search on a schedule | [Monitors](/docs/monitors/quickstart) |

## Next steps

<Columns cols={2}>
  <Card title="Search API reference" icon="square-terminal" href="/docs/reference/search" cta="Open reference" arrow="true">
    Every request parameter and response field.
  </Card>

  <Card title="Search quickstart" icon="search" href="/docs/search/quickstart" cta="Review guide" arrow="true">
    Core request shapes, filters, output, and freshness.
  </Card>

  <Card title="Contents API" icon="file-text" href="/docs/contents/quickstart" cta="Open guide" arrow="true">
    Extract highlights or full text from pages you already know.
  </Card>

  <Card title="Exa Agent" icon="bot" href="/docs/agent/quickstart" cta="Open guide" arrow="true">
    Long-running research, list building, and enrichment.
  </Card>
</Columns>
