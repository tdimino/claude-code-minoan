> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# SDK Quickstart

> Install and use the Exa Python and JavaScript SDKs

The official Exa SDKs. Search the web, get page contents, and get answers with citations.

<Card title="Get your Exa API key" icon="key" horizontal href="https://dashboard.exa.ai/api-keys">
  Create a key in the dashboard. New accounts start with free credits.
</Card>

## Install

<CodeGroup>
  ```bash pip theme={null}
  pip install exa-py
  ```

  ```bash uv theme={null}
  uv add exa-py
  ```

  ```bash npm theme={null}
  npm install exa-js
  ```

  ```bash pnpm theme={null}
  pnpm add exa-js
  ```
</CodeGroup>

The Python SDK requires Python 3.9+.

## Authentication

Set your API key as an environment variable:

<Tabs>
  <Tab title="macOS/Linux">
    ```bash theme={null}
    export EXA_API_KEY="your-api-key"
    ```
  </Tab>

  <Tab title="Windows">
    ```powershell theme={null}
    setx EXA_API_KEY "your-api-key"
    ```
  </Tab>
</Tabs>

## Getting started

Initialize the client and run your first search:

<CodeGroup>
  ```python Python theme={null}
  from exa_py import Exa

  exa = Exa()

  results = exa.search(
      "latest developments in fusion energy",
      type="auto",
      contents={"highlights": True},
  )

  for source in results.results:
      print(source.url, source.highlights)
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();

  const results = await exa.search("latest developments in fusion energy", {
    type: "auto",
    contents: {
      highlights: true,
    },
  });

  for (const source of results.results) {
    console.log(source.url, source.highlights);
  }
  ```
</CodeGroup>

<Note>
  Both clients read your key from the `EXA_API_KEY` environment variable. To set it explicitly
  instead, pass it inline: `Exa(api_key="your-api-key")` or `new Exa("your-api-key")`.
</Note>

## Recommended defaults

| Decision | Recommended default |
| - | - |
| Starting point | Use `search` |
| Search type | Keep `auto` unless latency or synthesis needs require another type |
| Page content | Start with `highlights: true` |
| Known URLs | Use `get_contents` / `getContents` |
| Freshness | Set `max_age_hours` / `maxAgeHours` only when stale content would be unusable |
| Requests for your own users | Set `user_identifier` / `userIdentifier` to an opaque ID for that user; see [end-user attribution](/docs/search/best-practices#user-identifier) |

<Warning>
  The two request types take the same content options in different places:

  | Method | Content option placement |
  | - | - |
  | `search` | Inside `contents`, as in `exa.search(query, contents={"highlights": True})` |
  | `get_contents` / `getContents` | Directly on the request, as in `exa.get_contents(urls, highlights=True)` |
</Warning>

## Search

Search finds relevant pages and returns their contents in one call.

<Tip>
  Use `highlights: true` for AI answers, RAG, and search previews. Exa sizes each result's
  excerpts to its relevance; set `max_characters` / `maxCharacters` only when your application
  requires a fixed limit.
</Tip>

Filters, date ranges, and result counts:

<CodeGroup>
  ```python Python theme={null}
  results = exa.search(
      "climate tech news",
      num_results=20,
      start_published_date="2024-01-01",
      include_domains=["techcrunch.com", "wired.com"],
      contents={"highlights": True}
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("interesting articles about space", {
    numResults: 10,
    includeDomains: ["nasa.gov", "space.com"],
    startPublishedDate: "2024-01-01",
    contents: {
      highlights: true,
    },
  });
  ```
</CodeGroup>

When an agent chooses the query, pass the goal that search serves as `objective` alongside it:

<CodeGroup>
  ```python Python theme={null}
  results = exa.search(
      "H100 hourly pricing on major cloud providers",
      objective="Compare H100 cloud pricing across providers for a cost report; prefer official pricing pages and pull the on-demand hourly rate from each.",
      contents={"highlights": True},
  )
  ```

  ```javascript JavaScript theme={null}
  const result = await exa.search("H100 hourly pricing on major cloud providers", {
    objective:
      "Compare H100 cloud pricing across providers for a cost report; prefer official pricing pages and pull the on-demand hourly rate from each.",
    contents: { highlights: true },
  });
  ```
</CodeGroup>

See [Pass the objective from agents](/docs/search/best-practices#pass-the-objective-from-agents) for when to use it and how to describe it to a model.

### Output schema

<CodeGroup>
  ```python Python theme={null}
  structured_results = exa.search(
      "Who is the CEO of OpenAI?",
      type="deep",
      system_prompt="Prefer official sources and avoid duplicate results",
      output_schema={
          "type": "object",
          "properties": {
              "leader": {"type": "string"},
              "title": {"type": "string"},
              "source_count": {"type": "number"}
          },
          "required": ["leader", "title"]
      },
      contents={"highlights": True}
  )

  print(structured_results.output.content if structured_results.output else None)
  ```

  ```javascript JavaScript theme={null}
  const structuredResult = await exa.search("Who is the CEO of OpenAI?", {
    type: "deep",
    systemPrompt: "Prefer official sources and avoid duplicate results",
    outputSchema: {
      type: "object",
      properties: {
        leader: { type: "string" },
        title: { type: "string" },
        sourceCount: { type: "number" },
      },
      required: ["leader", "title"],
    },
    contents: {
      highlights: true,
    },
  });

  console.log(structuredResult.output?.content);
  ```
</CodeGroup>

<Note>
  `output_schema` / `outputSchema` works with every search type and returns the synthesized value
  in `output.content`. Use `system_prompt` / `systemPrompt` for source preferences or emphasis.
  Grounding is returned automatically in `output.grounding`, so do not duplicate citations or
  confidence in your schema.
</Note>

Deep modes are recommended when the output requires research across several searches. Use `deep-lite` for lightweight research or `deep` for multi-step search and stronger synthesis. See the [Search guide](/docs/search/quickstart) for the full request options.

## Contents

Extract highlights, full text, or summaries from URLs you already know. Start with highlights and
add a query to focus them on the information you need.

<CodeGroup>
  ```python Python theme={null}
  results = exa.get_contents(
      ["https://exa.ai/blog/dynamic-highlights"],
      highlights={"query": "token efficiency and result quality"},
  )
  ```

  ```javascript JavaScript theme={null}
  const results = await exa.getContents(["https://exa.ai/blog/dynamic-highlights"], {
    highlights: {
      query: "token efficiency and result quality",
    },
  });
  ```
</CodeGroup>

Use full text when you need broader context or document structure. See the [Contents guide](/docs/contents/quickstart) for output shapes, freshness controls, and subpage crawling.

## Answer

Get answers to questions with citations.

<CodeGroup>
  ```python Python theme={null}
  response = exa.answer("What caused the 2008 financial crisis?")
  print(response.answer)

  for chunk in exa.stream_answer("Explain quantum computing"):
      print(chunk, end="", flush=True)
  ```

  ```javascript JavaScript theme={null}
  const response = await exa.answer("What caused the 2008 financial crisis?");
  console.log(response.answer);

  for await (const chunk of exa.streamAnswer("Explain quantum computing")) {
    if (chunk.content) {
      process.stdout.write(chunk.content);
    }
  }
  ```
</CodeGroup>

## Warnings

The SDKs log the `warnings` a `/search` response returns, such as a field the API ignores, so you can fix a request before it reaches production. Warning logging needs `exa-py` or `exa-js` 2.26.0 or later. Silence warnings or send them to your own logger:

<CodeGroup>
  ```python Python theme={null}
  import logging
  import warnings

  from exa_py import ExaWarning

  # Each warning is an ExaWarning, shown once per calling line.
  warnings.filterwarnings("ignore", category=ExaWarning)  # silence them
  logging.captureWarnings(True)  # or send them to the "py.warnings" logger
  ```

  ```typescript TypeScript theme={null}
  import Exa from "exa-js";

  // Each warning prints once per process. Pass warnings: "silent" to print nothing.
  const exa = new Exa(process.env.EXA_API_KEY, undefined, {
    warnings: (warning, { endpoint, requestId }) => {
      console.error(`Exa ${endpoint} ${warning.code} at ${warning.path}: ${warning.message}`, { requestId });
    },
  });
  ```
</CodeGroup>

## Async and types

Python exposes `AsyncExa` for async operations, and the JavaScript SDK ships TypeScript types for
every method.

<CodeGroup>
  ```python Python theme={null}
  from exa_py import AsyncExa

  exa = AsyncExa()

  results = await exa.search(
      "machine learning startups",
      contents={"highlights": True}
  )
  ```

  ```typescript TypeScript theme={null}
  import Exa from "exa-js";
  import type { SearchResponse, RegularSearchOptions } from "exa-js";
  ```
</CodeGroup>

## Resources

Python: [exa-py source](https://github.com/exa-labs/exa-py) and [PyPI package](https://pypi.org/project/exa-py/). JavaScript: [exa-js source](https://github.com/exa-labs/exa-js) and [npm package](https://www.npmjs.com/package/exa-js).

## Continue

<Columns cols={3}>
  <Card title="Search guide" icon="search" href="/docs/search/quickstart" cta="Open guide" arrow="true">
    Return to the main Search guide for request patterns, filters, and deeper modes.
  </Card>

  <Card title="Search reference" icon="square-terminal" href="/docs/reference/search" cta="Open reference" arrow="true">
    Jump to the full `/search` request and response schema.
  </Card>

  <Card title="Contents guide" icon="file-text" href="/docs/contents/quickstart" cta="Open guide" arrow="true">
    Use Contents when you already know the URLs and want direct extraction.
  </Card>
</Columns>
