> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Deep Search

> Use iterative search, reasoning, and grounded synthesis for complex research tasks.

Deep Search is the research mode of the Search API. It uses the same `/search` endpoint, but the retrieval process can issue multiple searches, inspect the evidence, refine its approach, and synthesize a grounded result.

Use standard Search when you need ranked pages for a well-formed query. Use Deep when finding the answer requires research.

## How Deep Search works

Deep Search adds a research loop before the final response:

<Steps>
  <Step title="Plan the search">
    Exa starts with your `query` and may expand it into searches that cover different parts of the
    request. You can supply starting variations with `additionalQueries`.
  </Step>

  <Step title="Search and inspect">
    Deep searches for evidence, compares the findings with the request, and determines what is
    supported or still missing.
  </Step>

  <Step title="Refine">
    When the evidence is incomplete or contradictory, Deep can issue a more targeted search instead
    of returning the first plausible pages.
  </Step>

  <Step title="Select and synthesize">
    Deep selects the useful results and then uses the same synthesis path as other search types.
    When you provide `outputSchema`, the response includes structured `output.content` and
    field-level citations in `output.grounding`.
  </Step>
</Steps>

This process is especially useful for lists and structured outputs. Each requested item may require a different search, and Deep can gather and check those results before producing the final structure.

## Choose a Deep mode

| Type | Use it when |
| - | - |
| `deep-lite` | You need lightweight query expansion and synthesis |
| `deep` | The task needs iterative search, evidence gathering, or multiple structured items |

Start with `deep` for research workflows. Move to `deep-lite` when the task is simpler and latency matters.

`deep-reasoning` is a [legacy search type](/docs/search/quickstart#legacy-search-types).

<Tip>
  For long-running research, list building and multi-hop enrichment, use
  [Exa Agent](/docs/agent/quickstart). Agent has more compute per run and returns grounded, structured
  results.
</Tip>

See [Pricing](/docs/admin/pricing#deep-search) for current cost and latency guidance.

## Make a Deep request

Set `type` on a normal Search API request:

<CodeGroup>
  ```python Python theme={null}
  from exa_py import Exa

  exa = Exa()

  result = exa.search(
      "Compare how major database vendors support vector, keyword, and hybrid retrieval",
      type="deep",
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();

  const result = await exa.search(
    "Compare how major database vendors support vector, keyword, and hybrid retrieval",
    {
      type: "deep",
      contents: { highlights: true }
    }
  );
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Compare how major database vendors support vector, keyword, and hybrid retrieval",
      "type": "deep",
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

Deep returns the selected search results under `results`. Add `outputSchema` when you also want a synthesized answer or structured dataset.

## Provide starting queries

Deep normally decides which searches to run. Use `additionalQueries` when you already know distinct terminology, perspectives, or subproblems that the research should cover:

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "Compare current approaches to inference-time scaling",
      additional_queries=[
          "inference-time compute scaling benchmark",
          "test-time reasoning methods survey",
          "adaptive compute language models",
      ],
      type="deep",
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search(
    "Compare current approaches to inference-time scaling",
    {
      additionalQueries: [
        "inference-time compute scaling benchmark",
        "test-time reasoning methods survey",
        "adaptive compute language models"
      ],
      type: "deep",
      contents: { highlights: true }
    }
  );
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Compare current approaches to inference-time scaling",
      "additionalQueries": [
        "inference-time compute scaling benchmark",
        "test-time reasoning methods survey",
        "adaptive compute language models"
      ],
      "type": "deep",
      "contents": { "highlights": true }
    }'
  ```
</CodeGroup>

The main `query` is always included. You can provide up to 10 additional queries, and the list is available only to Deep search types.

Do not provide minor rephrasings just to increase search volume. Add queries when each one contributes a meaningfully different search direction.

## Guide behavior and output separately

`systemPrompt` and `outputSchema` affect different parts of the request:

* `systemPrompt` guides source preferences, novelty, deduplication, and Deep's research behavior.
* `outputSchema` defines the final shape and triggers synthesis.

The query should describe what to research. The system prompt should describe how to conduct and present that research.

<CodeGroup>
  ```python Python theme={null}
  result = exa.search(
      "Find AI infrastructure companies that announced Series A or B funding in the last six months",
      type="deep",
      system_prompt="Prefer company announcements and investor portfolio pages. Exclude duplicate rounds.",
      output_schema={
          "type": "object",
          "required": ["companies"],
          "properties": {
              "companies": {
                  "type": "array",
                  "maxItems": 8,
                  "items": {
                      "type": "object",
                      "required": ["name", "round", "amount"],
                      "properties": {
                          "name": {"type": "string"},
                          "round": {"type": "string"},
                          "amount": {"type": "string"},
                      },
                  },
              }
          },
      },
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search(
    "Find AI infrastructure companies that announced Series A or B funding in the last six months",
    {
      type: "deep",
      systemPrompt:
        "Prefer company announcements and investor portfolio pages. Exclude duplicate rounds.",
      outputSchema: {
        type: "object",
        required: ["companies"],
        properties: {
          companies: {
            type: "array",
            maxItems: 8,
            items: {
              type: "object",
              required: ["name", "round", "amount"],
              properties: {
                name: { type: "string" },
                round: { type: "string" },
                amount: { type: "string" }
              }
            }
          }
        }
      }
    }
  );
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Find AI infrastructure companies that announced Series A or B funding in the last six months",
      "type": "deep",
      "systemPrompt": "Prefer company announcements and investor portfolio pages. Exclude duplicate rounds.",
      "outputSchema": {
        "type": "object",
        "required": ["companies"],
        "properties": {
          "companies": {
            "type": "array",
            "maxItems": 8,
            "items": {
              "type": "object",
              "required": ["name", "round", "amount"],
              "properties": {
                "name": { "type": "string" },
                "round": { "type": "string" },
                "amount": { "type": "string" }
              }
            }
          }
        }
      }
    }'
  ```
</CodeGroup>

Prefer Deep when you need more than two structured items or each item must satisfy several requirements. Standard search types use the same synthesis path, but they do not perform the same iterative research before synthesis.

## Output schema limits

`outputSchema` is validated before the search runs. A request that breaks any of these rules is rejected with a `400` error.

| Limit | Rule |
| - | - |
| Properties | At most **10 properties in total**, counted across every level of the schema. Properties inside nested objects and inside array `items` all count toward the 10. |
| Nesting | At most **2 levels** of nested objects below the root. `companies` → `items` → `name` is fine; an object inside that item object is not. |
| Arrays | Every `type: "array"` field must define `items`. |

The funding example above uses 4 of the 10 properties: `companies`, plus `name`, `round`, and `amount` inside its items. A schema with 3 top-level fields and a nested object holding 8 more uses 11 and fails with `output_schema exceeds maximum of 10 properties`.

If you need more than 10 fields, split the work into several Deep requests with focused schemas, or use [Exa Agent](/docs/agent/quickstart) for wide enrichment tables.

## Read the grounded response

Structured responses separate generated values from their evidence:

```json theme={null}
{
  "results": [
    {
      "title": "Acme AI raises $30M Series B",
      "url": "https://acme.example/news/series-b"
    }
  ],
  "output": {
    "content": {
      "companies": [
        {
          "name": "Acme AI",
          "round": "Series B",
          "amount": "$30M"
        }
      ]
    },
    "grounding": [
      {
        "field": "companies[0].amount",
        "citations": [
          {
            "title": "Acme AI raises $30M Series B",
            "url": "https://acme.example/news/series-b"
          }
        ],
        "confidence": "high"
      }
    ]
  }
}
```

Use `output.content` as the generated result and `output.grounding` to show or verify the sources supporting each field. Do not add citation or confidence fields to your own schema; Exa returns them automatically.

`numResults` controls how many selected pages are returned in `results`. It does not set the number of searches Deep may perform.

## Stream the synthesis

Set `stream: true` with `outputSchema` to receive the synthesized output over server-sent events:

<CodeGroup>
  ```python Python theme={null}
  import os
  import requests

  response = requests.post(
      "https://api.exa.ai/search",
      headers={"Authorization": f"Bearer {os.environ['EXA_API_KEY']}"},
      json={
          "query": "Explain the competing technical approaches to long-context retrieval",
          "type": "deep",
          "stream": True,
          "outputSchema": {
              "type": "text",
              "description": "A grounded comparison organized by approach",
          },
      },
      stream=True,
  )
  response.raise_for_status()

  for line in response.iter_lines(decode_unicode=True):
      if line:
          print(line)
  ```

  ```javascript JavaScript theme={null}
  const response = await fetch("https://api.exa.ai/search", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${process.env.EXA_API_KEY}`
    },
    body: JSON.stringify({
      query: "Explain the competing technical approaches to long-context retrieval",
      type: "deep",
      stream: true,
      outputSchema: {
        type: "text",
        description: "A grounded comparison organized by approach"
      }
    })
  });

  if (!response.ok || !response.body) {
    throw new Error(`Search failed: ${response.status}`);
  }

  const decoder = new TextDecoder();
  for await (const chunk of response.body) {
    process.stdout.write(decoder.decode(chunk, { stream: true }));
  }
  ```

  ```bash cURL theme={null}
  curl -N -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Explain the competing technical approaches to long-context retrieval",
      "type": "deep",
      "stream": true,
      "outputSchema": {
        "type": "text",
        "description": "A grounded comparison organized by approach"
      }
    }'
  ```
</CodeGroup>

Consume the typed events until `done`. The final event contains the completed output and search time, with cost information when available.

## When to stay with standard Search

Deep is unnecessary when one retrieval pass can satisfy the request:

* You need relevant pages, not a researched conclusion.
* The query already identifies a specific source or narrow topic.
* Your application performs its own reasoning and only needs retrieval.
* The request is on an interactive, autocomplete, or voice path.

Use `auto` for the default quality and speed balance, or `lite` when cost or latency matters most.

<Columns cols={2}>
  <Card title="Search API guide" icon="search" href="/docs/search/quickstart" cta="Review Search" arrow="true">
    Build requests, choose result content, and apply filters.
  </Card>

  <Card title="Search best practices" icon="sliders-horizontal" href="/docs/search/best-practices" cta="Tune retrieval" arrow="true">
    Improve quality, context, latency, and agent integrations.
  </Card>

  <Card title="Search API reference" icon="square-terminal" href="/docs/reference/search" cta="Open reference" arrow="true">
    See every request parameter and response field.
  </Card>

  <Card title="Pricing" icon="credit-card" href="/docs/admin/pricing#deep-search" cta="Compare modes" arrow="true">
    Review current Deep Search costs and latency.
  </Card>
</Columns>
