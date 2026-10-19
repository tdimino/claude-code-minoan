> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Exa Search API

> Search the web in natural language and get clean, relevant page content in one request.

Exa Search takes a natural language query and returns ranked web results with clean page content.

## Make your first request

Start with a `query` in natural language and `contents: { highlights: true }`, which returns excerpts sized to each result's relevance. Other fields control how Exa searches and what each result includes; the rest of this page covers the ones you will actually use.

<CodeGroup>
  ```python Python theme={null}
  from exa_py import Exa

  exa = Exa()

  result = exa.search(
      "recent techniques for improving retrieval in RAG systems",
      type="auto",
      contents={"highlights": True},
  )

  for item in result.results:
      print(item.title, item.url)
      print(item.highlights)
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();

  const result = await exa.search(
    "recent techniques for improving retrieval in RAG systems",
    {
      type: "auto",
      contents: { highlights: true }
    }
  );

  for (const item of result.results) {
    console.log(item.title, item.url);
    console.log(item.highlights);
  }
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "recent techniques for improving retrieval in RAG systems",
      "type": "auto",
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

Search returns up to 10 results by default. Set `numResults` to request up to 100 results; fewer may be returned when fewer relevant pages are available. Search does not support pagination.

<Accordion title="Example response">
  Highlights and the list below are shortened.

  ```json theme={null}
  {
    "requestId": "c3174df2b9cd5afbc64cdf79f3719b19",
    "resolvedSearchType": "",
    "results": [
      {
        "id": "https://arxiv.org/html/2608.21702",
        "title": "From Association to Causation: Improving Retrieval Precision ofRetrieval-Augmented Generation via Causal Relations and an Attention Mechanism",
        "url": "https://arxiv.org/html/2608.21702",
        "highlights": [
          "Retrieval-Augmented Generation (RAG) grounds LLM generation on retrieved documents, but the standard terminal retrieval stage—dense-vector similarity, optionally followed by reranking—often returns documents that merely share keywords with the query without containing the needed information...\n..."
        ],
        "image": "https://arxiv.org/static/base/1.0.1/images/icons/smileybones-small.svg",
        "favicon": "https://arxiv.org/static/browse/0.3.4/images/icons/favicon-32x32.png"
      },
      {
        "id": "https://www.thoughtworks.com/en-us/insights/blog/generative-ai/four-retrieval-techniques-improve-rag",
        "title": "Four retrieval techniques to improve RAG you need to know",
        "url": "https://www.thoughtworks.com/en-us/insights/blog/generative-ai/four-retrieval-techniques-improve-rag",
        "publishedDate": "2025-04-14T00:00:00.000Z",
        "highlights": [
          "It's not surprising, then, that we've seen a range of different approaches emerge that attempt to address RAG's limitations over the last year or so.\n..."
        ],
        "image": "https://www.thoughtworks.com/content/dam/thoughtworks/images/illustration/brand/tw_illustration_5.jpg"
      }
    ],
    "searchTime": 1324.3,
    "costDollars": {
      "total": 0.007,
      "search": {
        "neural": 0.007
      }
    }
  }
  ```
</Accordion>

Results are ranked by relevance. Each one carries metadata such as title, URL, and publication date, plus whatever you requested under `contents`.

## Writing queries

The `query` field is the only required field when using the Search API.

Write queries in natural language. Include the subject and, when useful, the kind of source and time period you want.

Queries can be broad and exploratory. `"Latest news on EU battery policy"` gives Exa enough intent to discover relevant pages; `"news"` does not. When the source type matters, name it in the query:

```text theme={null}
Recent technical articles comparing hybrid and semantic retrieval for RAG systems
```

See [What's in Exa's Index](/docs/search/data/overview) for what Exa's index includes and how to search those content types.

<h2 id="search-types">
  Choose a search type
</h2>

`type` selects a search mode, each tuned for a different balance of speed, search depth, and synthesis. `auto` is the default and works for most searches.

| Type | Use it when | Typical latency |
| - | - | - |
| `auto` | You want the best default balance of quality and speed | \~1 second |
| `lite` | Cost or latency matters most, such as high-volume or real-time workloads | \~450 ms |
| `deep-lite` | The task needs lightweight research and synthesis | \~4 seconds |
| `deep` | The task requires multi-step search and stronger synthesis | 4–15 seconds |

See [Lite](#lite) for the parameters `lite` accepts. [Pricing](/docs/admin/pricing) lists the price of every type.

Latency figures are approximate and cover the search itself with cached content. `outputSchema` adds a synthesis step and a low `contents.maxAgeHours` adds a fresh page fetch; see [Budget latency and context](/docs/search/best-practices#budget-latency-and-context).

Deep modes run a research process rather than a single retrieval pass. See [Deep Search](/docs/search/deep-search) for how that process works and how to use its additional controls.

<h3 id="lite">
  Lite
</h3>

`lite` is Exa's low-cost search type, at \$4 per 1,000 requests with up to 10 results. Use it for high-volume or cost-sensitive workloads that need ranked results and page content, without synthesis. It accepts a smaller set of parameters than `auto`.

`lite` serves page content from Exa's cache and never fetches a page live. When you request `text` or `highlights`, results with no cached copy are left out of the response.

| Parameter | On `lite` |
| - | - |
| `query` | A single query string |
| `numResults` | Up to 100. Each result above 10 costs \$1 per 1,000 results |
| `contents.highlights`, `contents.text` | Supported with all of their options |
| `contents.snapshotAsOf` | Supported. See [Exa Snapshot](/docs/search/snapshot) |
| `category` | Every category, including `company` and `people`, at the `lite` price |
| `includeDomains`, `excludeDomains` | Supported |
| `startPublishedDate`, `endPublishedDate` | Supported |
| `userLocation` | Supported |
| `moderation` | Supported |
| `objective`, `userIdentifier` | Supported |
| `compliance` | `"hipaa"`. See [HIPAA](/docs/admin/security/hipaa) |

Any other `/search` parameter returns `400 INVALID_REQUEST_BODY` naming each unsupported parameter you set, instead of being ignored. These include:

* `outputSchema`, `systemPrompt`, and `stream`
* `additionalQueries`
* `contents.summary`, `contents.extras`, `contents.subpages`, and `contents.subpageTarget`
* `contents.maxAgeHours`, `contents.livecrawl`, and `contents.livecrawlTimeout`, with any value, including `maxAgeHours: -1`
* The deprecated `includeText`, `excludeText`, `startCrawlDate`, `endCrawlDate`, and `contents.context`

A parameter set to `null` counts as unset. Any other value, including `false` and an empty list, counts as set. Use `auto` when a request needs one of these parameters.

```json theme={null}
{
  "requestId": "0c3a6f1e2b9d4c8a9e7f6d5c4b3a2918",
  "error": "Invalid request body | Not supported with type \"lite\": contents.summary. Use type \"auto\" for other parameters.",
  "tag": "INVALID_REQUEST_BODY"
}
```

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "latest chip export rules",
      type="lite",
      num_results=5,
      start_published_date="2026-01-01T00:00:00.000Z",
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("latest chip export rules", {
    type: "lite",
    numResults: 5,
    startPublishedDate: "2026-01-01T00:00:00.000Z",
    contents: { highlights: true }
  });
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "latest chip export rules",
      "type": "lite",
      "numResults": 5,
      "startPublishedDate": "2026-01-01T00:00:00.000Z",
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

The response has the same shape as other search types.

<h3 id="legacy-search-types">
  Legacy search types
</h3>

`fast`, `instant`, and `deep-reasoning` are legacy search types. They still work at their [current prices](/docs/admin/pricing). For new requests, use the alternative below.

| Legacy type | Use instead |
| - | - |
| `instant` | `lite` |
| `fast` | `lite`, which runs the same search as `fast`. Use `auto` when the request needs a parameter `lite` does not support. |
| `deep-reasoning` | `deep`, or [Exa Agent](/docs/agent/quickstart) for long-running research, list building and multi-hop enrichment |

## Output shapes

Every result includes metadata such as its title, URL, and publication date. Use `contents` to add highlights, full text, or a summary from the page.

<Tabs>
  <Tab title="Highlights">
    Highlights return the excerpts most relevant to your query. They give models and agents the
    evidence they need without filling the context window with unrelated parts of each page.

    This is the recommended output shape for most tasks.

    Start with bare `highlights: true`. Exa uses the query to select an appropriate amount of
    content from each result.

    <CodeGroup>
      ```python Python theme={null}
      result = exa.search(
          "How are inference providers reducing transformer latency?",
          contents={"highlights": True},
      )
      ```

      ```javascript JavaScript theme={null}
      const result = await exa.search(
        "How are inference providers reducing transformer latency?",
        { contents: { highlights: true } }
      );
      ```

      ```bash cURL theme={null}
      curl -s -X POST "https://api.exa.ai/search" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $EXA_API_KEY" \
        -d '{
          "query": "How are inference providers reducing transformer latency?",
          "contents": { "highlights": true }
        }'
      ```
    </CodeGroup>

    See [Highlights](/docs/search/highlights) for Dynamic Highlights and guidance on when to enable it.
  </Tab>

  <Tab title="Full text">
    Full text returns the clean page body. Use it when the task depends on broader context, document
    structure, or details that may fall outside query-focused excerpts.

    Full pages can be large. Limit both the number of results and the text returned per page.

    <CodeGroup>
      ```python Python theme={null}
      result = exa.search(
          "Technical postmortems of large-scale inference outages",
          num_results=5,
          contents={"text": {"max_characters": 10000}},
      )
      ```

      ```javascript JavaScript theme={null}
      const result = await exa.search(
        "Technical postmortems of large-scale inference outages",
        {
          numResults: 5,
          contents: { text: { maxCharacters: 10000 } }
        }
      );
      ```

      ```bash cURL theme={null}
      curl -s -X POST "https://api.exa.ai/search" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $EXA_API_KEY" \
        -d '{
          "query": "Technical postmortems of large-scale inference outages",
          "numResults": 5,
          "contents": {
            "text": { "maxCharacters": 10000 }
          }
        }'
      ```
    </CodeGroup>
  </Tab>
</Tabs>

Pick one content view per request. Requesting both highlights and text returns and bills two views of the same page. `summary` is a third option, but it adds a language model call for every result.

<Warning>
  `/search` and `/contents` accept the same content options in different places:

  * **`/search`** nests `highlights`, `text`, and `summary` inside the `contents` object:
    `"contents": { "highlights": true }`
  * **`/contents`** has no `contents` wrapper. Its body is the content options themselves, so the
    same fields sit at the top level next to `urls`: `"urls": [...], "highlights": true`
</Warning>

## Output schema

Add `outputSchema` when you want Exa to synthesize the search results. It works with every search type and adds an `output` object to the response.

The ranked pages remain in `results`. The generated value is returned in `output.content`, with field-level sources and confidence in `output.grounding`.

<Tabs>
  <Tab title="Freeform Text">
    Use `type: "text"` for generated prose. Add a `description` to specify its format or length.

    <CodeGroup>
      ```python Python theme={null}
      result = exa.search(
          "What changed in the latest EU battery policy?",
          output_schema={
              "type": "text",
              "description": "Summarize the changes in three concise bullets",
          },
      )
      ```

      ```javascript JavaScript theme={null}
      const result = await exa.search(
        "What changed in the latest EU battery policy?",
        {
          outputSchema: {
            type: "text",
            description: "Summarize the changes in three concise bullets"
          }
        }
      );
      ```

      ```bash cURL theme={null}
      curl -s -X POST "https://api.exa.ai/search" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $EXA_API_KEY" \
        -d '{
          "query": "What changed in the latest EU battery policy?",
          "outputSchema": {
            "type": "text",
            "description": "Summarize the changes in three concise bullets"
          }
        }'
      ```
    </CodeGroup>
  </Tab>

  <Tab title="Structured JSON">
    Use `type: "object"` for JSON that follows the properties and requirements you define.

    <CodeGroup>
      ```python Python theme={null}
      result = exa.search(
          "AI infrastructure companies that announced Series A or B funding in the past six months",
          output_schema={
              "type": "object",
              "properties": {
                  "companies": {
                      "type": "array",
                      "maxItems": 10,
                      "items": {
                          "type": "object",
                          "properties": {
                              "name": {"type": "string"},
                              "round": {"type": "string"},
                              "amount": {"type": "string"},
                              "announcedDate": {
                                  "type": "string",
                                  "description": "The funding announcement date",
                              },
                              "leadInvestors": {
                                  "type": "array",
                                  "items": {"type": "string"},
                              },
                          },
                          "required": ["name", "round", "amount", "announcedDate"],
                      },
                  }
              },
              "required": ["companies"],
          },
      )
      ```

      ```javascript JavaScript theme={null}
      const result = await exa.search(
        "AI infrastructure companies that announced Series A or B funding in the past six months",
        {
          outputSchema: {
            type: "object",
            properties: {
              companies: {
                type: "array",
                maxItems: 10,
                items: {
                  type: "object",
                  properties: {
                    name: { type: "string" },
                    round: { type: "string" },
                    amount: { type: "string" },
                    announcedDate: {
                      type: "string",
                      description: "The funding announcement date"
                    },
                    leadInvestors: {
                      type: "array",
                      items: { type: "string" }
                    }
                  },
                  required: ["name", "round", "amount", "announcedDate"]
                }
              }
            },
            required: ["companies"]
          }
        }
      );
      ```

      ```bash cURL theme={null}
      curl -s -X POST "https://api.exa.ai/search" \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $EXA_API_KEY" \
        -d '{
          "query": "AI infrastructure companies that announced Series A or B funding in the past six months",
          "outputSchema": {
            "type": "object",
            "properties": {
              "companies": {
                "type": "array",
                "maxItems": 10,
                "items": {
                  "type": "object",
                  "properties": {
                    "name": { "type": "string" },
                    "round": { "type": "string" },
                    "amount": { "type": "string" },
                    "announcedDate": {
                      "type": "string",
                      "description": "The funding announcement date"
                    },
                    "leadInvestors": {
                      "type": "array",
                      "items": { "type": "string" }
                    }
                  },
                  "required": ["name", "round", "amount", "announcedDate"]
                }
              }
            },
            "required": ["companies"]
          }
        }'
      ```
    </CodeGroup>
  </Tab>
</Tabs>

Use `systemPrompt` for instructions such as source preferences or emphasis; use `outputSchema` for the response shape. Python uses `system_prompt` and `output_schema`.

<Note>
  Object schemas are capped at 10 properties in total (nested and array `items` properties count) and
  2 levels of nesting. See [Output schema limits](/docs/search/deep-search#output-schema-limits). Do not add
  citation or confidence fields to the schema; Exa returns them automatically in `output.grounding`.
</Note>

## Filter results

Filters are hard constraints: add one when a result outside it would be unusable to you, and keep softer source preferences in the query text instead. The [API reference](/docs/reference/search) has the full set.

### Include domains or paths

`includeDomains` restricts results to sources you trust. It accepts full domains, path prefixes such as `anthropic.com/news`, and subdomain wildcards such as `*.substack.com`.

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "new model releases",
      include_domains=["openai.com", "anthropic.com/news"],
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("new model releases", {
    includeDomains: ["openai.com", "anthropic.com/news"],
    contents: { highlights: true }
  });
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "new model releases",
      "includeDomains": ["openai.com", "anthropic.com/news"],
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

Put the path in the filter rather than repeating it as a `site:` operator in the query.

### Exclude domains or paths

`excludeDomains` removes results from specific domains or paths. It supports the same path prefixes and subdomain wildcards as `includeDomains`. Use it when those sources would make a result unusable, not to express a preference.

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "primary research on retrieval-augmented generation benchmarks",
      exclude_domains=["medium.com", "dev.to"],
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search(
    "primary research on retrieval-augmented generation benchmarks",
    {
      excludeDomains: ["medium.com", "dev.to"],
      contents: { highlights: true }
    }
  );
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "primary research on retrieval-augmented generation benchmarks",
      "excludeDomains": ["medium.com", "dev.to"],
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

## Localize results

`userLocation` tells Exa where the end user is so results favor their region. Pass a two-letter ISO 3166-1 country code such as `"US"`, or an object with `country` and/or `latitude` and `longitude` in decimal degrees. Coordinates help queries that depend on where the user is without naming a place, such as "coffee shops near me" or "weather today". Send `latitude` and `longitude` together, and only the precision your use case needs.

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "coffee shops near me",
      user_location={"country": "US", "latitude": 37.7749, "longitude": -122.4194},
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("coffee shops near me", {
    userLocation: { country: "US", latitude: 37.7749, longitude: -122.4194 },
    contents: { highlights: true }
  });
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "coffee shops near me",
      "userLocation": { "country": "US", "latitude": 37.7749, "longitude": -122.4194 },
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

## Content freshness

`contents.maxAgeHours` controls how fresh the content extracted from each result must be. It does not filter results by publication date.

| Value | Behavior |
| - | - |
| Omit | Use cached content when available and fetch the page when needed |
| Positive integer | Use cached content if it is newer than this many hours; otherwise fetch the page |
| `0` | Always fetch fresh content |
| `-1` | Only use cached content |

Most searches should omit this field. Set it when stale page content would be unusable, such as for prices, availability, or a page that changes frequently.

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "current pricing for serverless GPU providers",
      contents={
          "highlights": True,
          "max_age_hours": 24,
      },
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("current pricing for serverless GPU providers", {
    contents: {
      highlights: true,
      maxAgeHours: 24
    }
  });
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "current pricing for serverless GPU providers",
      "contents": {
        "highlights": true,
        "maxAgeHours": 24
      }
    }'
  ```
</CodeGroup>

## Next steps

<Columns cols={2}>
  <Card title="Best practices" icon="sparkles" href="/docs/search/best-practices" cta="Read guide" arrow="true">
    Token budgets, content freshness, structured output, and system prompts.
  </Card>

  <Card title="API reference" icon="square-terminal" href="/docs/reference/search" cta="Open reference" arrow="true">
    Every request parameter and response field, with a live playground.
  </Card>

  <Card title="Contents" icon="file-text" href="/docs/contents/quickstart" cta="Open guide" arrow="true">
    You already have the URLs and want clean text, highlights, or summaries.
  </Card>

  <Card title="Exa Agent" icon="bot" href="/docs/agent/quickstart" cta="Open guide" arrow="true">
    You need long-running research, list building, or enrichment.
  </Card>
</Columns>
