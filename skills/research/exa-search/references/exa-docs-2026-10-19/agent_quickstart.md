> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Exa Agent

> Run deep research, list-building, and enrichment workflows that return structured outputs.

Exa Agent is an async, usage-based endpoint for high-compute tasks like list building, enrichment, and deep research. It handles complex reasoning and can return many structured output fields.

Think of it as a context agent: you describe the data you want and the shape it should come back in, and Exa Agent orchestrates the tool calls needed to get there. A single run can fan out many searches across different angles, read and condense the pages behind them, split list building into subtasks that run in parallel, verify each candidate against your criteria, enrich contacts, and query any [Exa Connect](/docs/agent/connect/overview) data partners you attach. You get the assembled context back as one grounded, structured result instead of orchestrating each `/search` and `/contents` call yourself.

Each run can return a natural-language answer, schema-validated JSON, field-level grounding, metadata, and a cost breakdown. You can retrieve completed runs later, list past runs, replay events, or continue from a previous run.

<Tip>
  Prefer MCP? Exa Agent and [Exa Connect](/docs/agent/connect/overview) are available in [Exa MCP](/docs/get-started/exa-mcp#exa-agent). Connect with OAuth or your API key and the `agent_run` tool is enabled by default, so you can run multi-step research, list-building, enrichment, and structured output from Claude, Cursor, and other MCP clients.
</Tip>

## When to use Exa Agent

Use Exa Agent when a workflow needs more than a single search or extraction call, or when you would otherwise write your own loop of searches, page reads, and verification steps to assemble the data:

* Build lists from open-ended criteria, then enrich each result
* Research entities across many fields with citations
* Run multi-hop tasks like "find companies, then find their decision makers"
* Produce structured JSON from a long-running web research task
* Combine web research with premium data partners in one grounded answer
* Continue from a previous run with a follow-up request like "find 10 more results"

Exa Agent is higher-latency and async by design. For a single low-latency search where you orchestrate the calls yourself, start with the [Search API](/docs/search/quickstart).

## Quickstart

This example starts a run that builds a structured list of people matching your criteria. It returns JSON in `output.structured`.

### 1. Install the Exa SDK

<CodeGroup>
  ```bash Python theme={null}
  pip install exa-py
  ```

  ```bash JavaScript theme={null}
  npm install exa-js
  ```
</CodeGroup>

### 2. Set your API key

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

### 3. Create a run

<CodeGroup>
  ```python Python theme={null}
  import json
  from exa_py import Exa

  exa = Exa()
  run = exa.agent.runs.create(
      query="Find engineering leaders at AI infrastructure companies that raised a Series A or B in the last 6 months.",
      output_schema={
          "type": "object",
          "properties": {
              "people": {
                  "type": "array",
                  "maxItems": 10,
                  "items": {
                      "type": "object",
                      "properties": {
                          "name": {"type": "string"},
                          "job_title": {"type": "string"},
                          "linkedin_url": {"type": "string", "format": "uri"},
                      },
                      "required": ["name", "job_title", "linkedin_url"],
                  },
              }
          },
          "required": ["people"],
      },
      effort="auto",
  )

  print(json.dumps(run.model_dump(), indent=2))
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();
  const run = await exa.agent.runs.create({
    query:
      "Find engineering leaders at AI infrastructure companies that raised a Series A or B in the last 6 months.",
    outputSchema: {
      type: "object",
      properties: {
        people: {
          type: "array",
          maxItems: 10,
          items: {
            type: "object",
            properties: {
              name: { type: "string" },
              job_title: { type: "string" },
              linkedin_url: { type: "string", format: "uri" }
            },
            required: ["name", "job_title", "linkedin_url"]
          }
        }
      },
      required: ["people"]
    },
    effort: "auto"
  });

  console.log(JSON.stringify(run, null, 2));
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/agent/runs" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Find engineering leaders at AI infrastructure companies that raised a Series A or B in the last 6 months.",
      "effort": "auto",
      "outputSchema": {
        "type": "object",
        "properties": {
          "people": {
            "type": "array",
            "maxItems": 10,
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": "string" },
                "job_title": { "type": "string" },
                "linkedin_url": { "type": "string", "format": "uri" }
              },
              "required": ["name", "job_title", "linkedin_url"]
            }
          }
        },
        "required": ["people"]
      }
    }'
  ```
</CodeGroup>

Add `Accept: text/event-stream` when creating a run to receive server-sent events as the run is queued, started, and completed. See [Stream events](#stream-events) for more details.

### 4. Poll for completion

If you do not stream events, save the returned `id` and poll the run until it reaches a terminal status.

<CodeGroup>
  ```python Python theme={null}
  import json
  from exa_py import Exa

  exa = Exa()
  run_id = "agent_run_01j..."
  run = exa.agent.runs.poll_until_finished(
      run_id,
      poll_interval=4000,
  )

  print(json.dumps(run.model_dump(), indent=2))
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();
  const runId = "agent_run_01j...";
  const run = await exa.agent.runs.pollUntilFinished(runId, {
    pollInterval: 4000
  });

  console.log(JSON.stringify(run, null, 2));
  ```

  ```bash cURL theme={null}
  RUN_ID="agent_run_01j..."

  while true; do
    RUN_JSON="$(curl -s "https://api.exa.ai/agent/runs/$RUN_ID" \
      -H "Authorization: Bearer $EXA_API_KEY")"

    STATUS="$(echo "$RUN_JSON" | python3 -c 'import json,sys; print(json.load(sys.stdin)["status"])')"
    echo "status=$STATUS"

    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ] || [ "$STATUS" = "cancelled" ]; then
      echo "$RUN_JSON"
      break
    fi

    sleep 4
  done
  ```
</CodeGroup>

Completed runs include:

* `output.text`: a natural-language answer
* `output.structured`: validated JSON when you provide `outputSchema`
* `output.grounding`: citations for text or structured fields, when emitted
* `costDollars`: the run's cost breakdown

<Note>
  Exa Agent is also available through the OpenAI-compatible Responses API. Point
  the OpenAI SDK at `https://api.exa.ai`, use `model: "exa-agent"`, and choose
  synchronous, streaming, or background execution. See [OpenAI SDK
  compatibility](/docs/integrations/openai-sdk#agent-via-responses-api).
</Note>

## Verify and enrich a specific entity

Beyond list building, use Exa Agent to inspect a single known entity, verify a claim against authoritative sources, and return structured enrichment. This example checks whether a company's official website has a publicly accessible pricing page, and enriches the result with pricing details when they are available. The schema requires only `domain` and `verdict`; everything else is optional enrichment.

<CodeGroup>
  ```python Python theme={null}
  import json
  from exa_py import Exa

  exa = Exa()
  run = exa.agent.runs.create(
      query="Inspect the official website redbarnrobotics.com and determine whether it has a publicly accessible pricing or plans page. A dedicated pricing page counts as present even if it only says 'Contact sales'.",
      system_prompt="Judge only the company specified in the query. Use present only when a public pricing or plans page is found. Use absent only after successfully inspecting the website and finding no such page. If the website is unreachable, blocked, fails to render, or cannot be inspected reliably, use cannot_verify. Never use absent when inspection failed. Use only the company's official website as evidence.",
      effort="low",
      output_schema={
          "type": "object",
          "additionalProperties": False,
          "required": ["domain", "verdict"],
          "properties": {
              "domain": {"type": "string", "const": "redbarnrobotics.com"},
              "verdict": {
                  "type": "string",
                  "enum": ["present", "absent", "cannot_verify"],
              },
              "pricing_page_url": {"type": ["string", "null"], "format": "uri"},
              "displays_numeric_prices": {"type": ["boolean", "null"]},
              "pricing_model": {
                  "type": ["string", "null"],
                  "enum": [
                      "free",
                      "subscription",
                      "usage_based",
                      "one_time",
                      "custom_quote",
                      "mixed",
                      "other",
                      None,
                  ],
              },
              "starting_price": {"type": ["number", "null"], "minimum": 0},
              "currency": {
                  "type": ["string", "null"],
                  "description": "ISO 4217 code such as USD or EUR.",
              },
              "billing_period": {
                  "type": ["string", "null"],
                  "enum": [
                      "monthly",
                      "annual",
                      "one_time",
                      "usage_based",
                      "variable",
                      "other",
                      None,
                  ],
              },
              "has_free_plan": {"type": ["boolean", "null"]},
              "has_free_trial": {"type": ["boolean", "null"]},
              "reasoning": {"type": ["string", "null"], "maxLength": 300},
          },
      },
  )
  run = exa.agent.runs.poll_until_finished(run.id)

  print(json.dumps(run.output.structured if run.output else None, indent=2))
  ```

  ```typescript TypeScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();
  const run = await exa.agent.runs.create({
    query:
      "Inspect the official website redbarnrobotics.com and determine whether it has a publicly accessible pricing or plans page. A dedicated pricing page counts as present even if it only says 'Contact sales'.",
    systemPrompt:
      "Judge only the company specified in the query. Use present only when a public pricing or plans page is found. Use absent only after successfully inspecting the website and finding no such page. If the website is unreachable, blocked, fails to render, or cannot be inspected reliably, use cannot_verify. Never use absent when inspection failed. Use only the company's official website as evidence.",
    effort: "low",
    outputSchema: {
      type: "object",
      additionalProperties: false,
      required: ["domain", "verdict"],
      properties: {
        domain: { type: "string", const: "redbarnrobotics.com" },
        verdict: {
          type: "string",
          enum: ["present", "absent", "cannot_verify"]
        },
        pricing_page_url: { type: ["string", "null"], format: "uri" },
        displays_numeric_prices: { type: ["boolean", "null"] },
        pricing_model: {
          type: ["string", "null"],
          enum: [
            "free",
            "subscription",
            "usage_based",
            "one_time",
            "custom_quote",
            "mixed",
            "other",
            null
          ]
        },
        starting_price: { type: ["number", "null"], minimum: 0 },
        currency: {
          type: ["string", "null"],
          description: "ISO 4217 code such as USD or EUR."
        },
        billing_period: {
          type: ["string", "null"],
          enum: [
            "monthly",
            "annual",
            "one_time",
            "usage_based",
            "variable",
            "other",
            null
          ]
        },
        has_free_plan: { type: ["boolean", "null"] },
        has_free_trial: { type: ["boolean", "null"] },
        reasoning: { type: ["string", "null"], maxLength: 300 }
      }
    }
  });
  const completedRun = await exa.agent.runs.pollUntilFinished(run.id);

  console.log(JSON.stringify(completedRun.output?.structured, null, 2));
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/agent/runs" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Inspect the official website redbarnrobotics.com and determine whether it has a publicly accessible pricing or plans page. A dedicated pricing page counts as present even if it only says '"'"'Contact sales'"'"'.",
      "systemPrompt": "Judge only the company specified in the query. Use present only when a public pricing or plans page is found. Use absent only after successfully inspecting the website and finding no such page. If the website is unreachable, blocked, fails to render, or cannot be inspected reliably, use cannot_verify. Never use absent when inspection failed. Use only the company'"'"'s official website as evidence.",
      "effort": "low",
      "outputSchema": {
        "type": "object",
        "additionalProperties": false,
        "required": ["domain", "verdict"],
        "properties": {
          "domain": { "type": "string", "const": "redbarnrobotics.com" },
          "verdict": {
            "type": "string",
            "enum": ["present", "absent", "cannot_verify"]
          },
          "pricing_page_url": { "type": ["string", "null"], "format": "uri" },
          "displays_numeric_prices": { "type": ["boolean", "null"] },
          "pricing_model": {
            "type": ["string", "null"],
            "enum": ["free", "subscription", "usage_based", "one_time", "custom_quote", "mixed", "other", null]
          },
          "starting_price": { "type": ["number", "null"], "minimum": 0 },
          "currency": {
            "type": ["string", "null"],
            "description": "ISO 4217 code such as USD or EUR."
          },
          "billing_period": {
            "type": ["string", "null"],
            "enum": ["monthly", "annual", "one_time", "usage_based", "variable", "other", null]
          },
          "has_free_plan": { "type": ["boolean", "null"] },
          "has_free_trial": { "type": ["boolean", "null"] },
          "reasoning": { "type": ["string", "null"], "maxLength": 300 }
        }
      }
    }'
  ```
</CodeGroup>

<Note>
  Schemas for verification workflows should account for uncertainty. Make
  fields that may not be verifiable nullable and leave them out of `required`,
  so the agent can return `null` instead of fabricating a value. The `verdict`
  enum distinguishes a failed inspection (`cannot_verify`) from actual negative
  evidence (`absent`): a site that could not be reached is not evidence that
  the page does not exist.
</Note>

## Stream events

Streaming keeps the create request open and sends Server-Sent Events (SSE) until the run completes. See [Event format](#event-format) for the event types and payloads.

Set `stream=True` in Python, `stream: true` in JavaScript, or send `Accept: text/event-stream` over HTTP:

<CodeGroup>
  ```python Python theme={null}
  from exa_py import Exa

  exa = Exa()
  events = exa.agent.runs.create(
      query="Find five recently launched developer tools for evaluating AI agents.",
      stream=True,
  )

  for event in events:
      print(event.event, event.data)
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();
  const events = await exa.agent.runs.create({
    query: "Find five recently launched developer tools for evaluating AI agents.",
    stream: true
  });

  for await (const event of events) {
    console.log(event.event, event.data);
  }
  ```

  ```bash cURL theme={null}
  curl -N -X POST "https://api.exa.ai/agent/runs" \
    -H "Content-Type: application/json" \
    -H "Accept: text/event-stream" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Find five recently launched developer tools for evaluating AI agents."
    }'
  ```
</CodeGroup>

### Event format

Each SSE frame contains an event ID, event name, and JSON payload:

```text theme={null}
id: 1
event: agent_run.created
data: {"id":"agent_run_01j...","status":"queued","createdAt":"2026-05-07T21:21:52.051Z"}
```

The stream may also contain comment lines such as `: keep-alive`. SSE clients ignore comments automatically; custom parsers should do the same.

### Event types

| Event | `data` payload | How to use it |
| - | - | - |
| `agent_run.created` | `{ id, status: "queued", createdAt }` | Save the run ID as soon as the request is accepted. |
| `agent_run.started` | `{ id, status: "running" }` | Mark the run as actively processing. |
| `agent_run.completed` | The completed Agent run object | Read the final answer from `data.output.text` or `data.output.structured`, and citations from `data.output.grounding`. |
| `agent_run.failed` | `{ id, status: "failed", error }` | Surface `error.code` and `error.message`; no completed output is available. |
| `agent_run.cancelled` | `{ id, status: "cancelled", ... }` | Stop consuming the stream and handle the run as cancelled. |

Events associated with the same research step include a `callId`. It corresponds to `item.call_id` in tool progress events. Use it to group search traces, sources, and tool progress. Some search-trace descriptions are generated asynchronously and can arrive after the source or tool event they describe, so do not correlate them by arrival order alone.

Treat `agent_run.source.added` as a live preview rather than a complete citation list. The terminal run's `output.grounding` is the authoritative grounding output.

### Replay stored events

For non-ZDR runs, [`GET /agent/runs/{id}/events`](/docs/reference/agent-api/list-run-events) returns stored events as paginated JSON. Send `Accept: text/event-stream` to replay the stored events as SSE, and `Last-Event-ID` to skip events your client has already processed:

```bash cURL theme={null}
curl -N "https://api.exa.ai/agent/runs/agent_run_01j.../events" \
  -H "Accept: text/event-stream" \
  -H "Last-Event-ID: 12" \
  -H "Authorization: Bearer $EXA_API_KEY"
```

The replay endpoint sends the events stored at request time and then closes; it does not continue following a running run. ZDR runs do not retain events and cannot be replayed.

For forward compatibility, ignore event names your application does not recognize and continue until a terminal event arrives.

## Return structured JSON

Use `outputSchema` to return schema-validated JSON in `output.structured`.

`outputSchema` supports the [JSON Schema specification](https://json-schema.org/).

Runs with a schema that no output can satisfy fail fast with a `400` `INVALID_OUTPUT_SCHEMA` error. For example, a root object with `additionalProperties: false` whose `required` list names a property missing from its `properties`.

To request contact information, describe the desired contact fields in `outputSchema`. Use standard JSON Schema shapes such as `{ "type": "string", "format": "email" }` for email addresses, `{ "type": "string", "format": "phone" }` for phone numbers, and `{ "type": "string", "format": "uri" }` for URLs. Bound list sizes with `maxItems` when possible so the maximum contact-enrichment cost is predictable.

<CodeGroup>
  ```python Python theme={null}
  import json
  from exa_py import Exa

  exa = Exa()
  run = exa.agent.runs.create(
      query="Find AI infrastructure companies that raised a Series A or B in the last 6 months.",
      effort="auto",
      output_schema={
          "type": "object",
          "properties": {
              "companies": {
                  "type": "array",
                  "items": {
                      "type": "object",
                      "properties": {
                          "name": {"type": "string"},
                          "round": {"type": "string"},
                          "website": {"type": "string"},
                      },
                      "required": ["name", "round"],
                  },
              }
          },
          "required": ["companies"],
      },
  )
  run = exa.agent.runs.poll_until_finished(
      run.id,
  )

  print(json.dumps(run.output.structured if run.output else None, indent=2))
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();
  const run = await exa.agent.runs.create({
    query:
      "Find AI infrastructure companies that raised a Series A or B in the last 6 months.",
    effort: "auto",
    outputSchema: {
      type: "object",
      properties: {
        companies: {
          type: "array",
          items: {
            type: "object",
            properties: {
              name: { type: "string" },
              round: { type: "string" },
              website: { type: "string" }
            },
            required: ["name", "round"]
          }
        }
      },
      required: ["companies"]
    }
  });
  const completedRun = await exa.agent.runs.pollUntilFinished(run.id);

  console.log(JSON.stringify(completedRun.output?.structured, null, 2));
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/agent/runs" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Find AI infrastructure companies that raised a Series A or B in the last 6 months.",
      "effort": "auto",
      "outputSchema": {
        "type": "object",
        "properties": {
          "companies": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": "string" },
                "round": { "type": "string" },
                "website": { "type": "string" }
              },
              "required": ["name", "round"]
            }
          }
        },
        "required": ["companies"]
      }
    }'
  ```
</CodeGroup>

## Process input rows

Use `input.data` when you have an existing set of data that you want to enrich. You can add more fields to each data entity, surface more entities based on the data you bring in, or both.

For complete row-enrichment examples, see [Agent examples](/docs/agent/examples#enrich-input-rows-code).

## Process exclusions

Use `input.exclusion` to exclude certain entries from being surfaced in the run. In the example below, we want to look for the top 10 cutest animals, but we exclude goats and pandas from the run because we already know how cute they are.

<CodeGroup>
  ```python Python theme={null}
  import json
  from exa_py import Exa

  exa = Exa()
  run = exa.agent.runs.create(
      query="Find the top 10 cutest animals. Return each animal's common name and a source URL.",
      input={
          "exclusion": [
              {"animal": "goat"},
              {"animal": "panda"},
          ]
      },
  )

  print(json.dumps(run.model_dump(), indent=2))
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();
  const run = await exa.agent.runs.create({
    query: "Find the top 10 cutest animals. Return each animal's common name and a source URL.",
    input: {
      exclusion: [
        { animal: "goat" },
        { animal: "panda" }
      ]
    }
  });

  console.log(JSON.stringify(run, null, 2));
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/agent/runs" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Find the top 10 cutest animals. Return each animal'"'"'s common name and a source URL.",
      "input": {
        "exclusion": [
          { "animal": "goat" },
          { "animal": "panda" }
        ]
      }
    }'
  ```
</CodeGroup>

## Connect data sources

The index is already available on every run. Use `dataSources` only to attach [Exa Connect](/docs/agent/connect/overview) partners. Each entry selects a `provider`. When a property in your `outputSchema` references a specific source (e.g., "from Similarweb"), Exa Agent calls the matching provider tool instead of guessing from a web page.

```json theme={null}
{
  "dataSources": [
    { "provider": "similarweb" },
    { "provider": "fiber" }
  ]
}
```

See [Exa Connect](/docs/agent/connect/overview) for the full list of data partners, with examples for each.

## Continue from a previous run

Use `previousRunId` to ask follow-ups to a previous response. Each follow-up starts a new run with its own ID. `previousRunId` carries context into the new run; it is not reused as the new run's ID.

<CodeGroup>
  ```python Python theme={null}
  import json
  from exa_py import Exa

  exa = Exa()
  run = exa.agent.runs.create(
      query="Narrow that list to companies hiring in San Francisco.",
      previous_run_id="agent_run_01j...",
  )

  print(json.dumps(run.model_dump(), indent=2))
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();
  const run = await exa.agent.runs.create({
    query: "Narrow that list to companies hiring in San Francisco.",
    previousRunId: "agent_run_01j..."
  });

  console.log(JSON.stringify(run, null, 2));
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/agent/runs" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Narrow that list to companies hiring in San Francisco.",
      "previousRunId": "agent_run_01j..."
    }'
  ```
</CodeGroup>

## Find a run ID

List recent runs and inspect their statuses:

<CodeGroup>
  ```python Python theme={null}
  from exa_py import Exa

  exa = Exa()
  runs = exa.agent.runs.list(
      limit=10,
  )

  for run in runs.data:
      query = (run.request or {}).get("query", "")
      print(f"{run.id}\t{run.status}\t{run.created_at}\t{query}")
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();
  const list = await exa.agent.runs.list({
    limit: 10
  });

  for (const run of list.data) {
    const query = run.request?.query ?? "";
    console.log(`${run.id}\t${run.status}\t${run.createdAt}\t${query}`);
  }
  ```

  ```bash cURL theme={null}
  curl -s "https://api.exa.ai/agent/runs?limit=10" \
    -H "Authorization: Bearer $EXA_API_KEY"
  ```
</CodeGroup>

## Pricing

Costs are usage-based and priced by component:

| Component | Price |
| - | - |
| Agent Compute Units | `1 ACU = $0.10` |
| Search tool calls | `$0.005 / search` |

<Note>
  Contact enrichment is separate from the core pricing components above: email contact enrichment is `$0.02 / email`, and phone number contact enrichment is `$0.07 / phone number`.
</Note>

`usage.agentComputeUnits` measures model computation across the full run. Complex queries, especially ones with a large `input.data` field, need more reasoning steps and tool calls and consume more ACUs.

See [Agent limits](/docs/admin/billing#agent-limits) for concurrency and rate limits.

### Effort

Use `effort` to choose a cost and reasoning level for each run. The supported values are `minimal`, `low`, `medium`, `high`, `xhigh`, `auto`, and `ultra`; the default is `auto`. Fixed efforts have a predictable per-request price, while `auto` and `ultra` are metered by usage:

| Effort | Price |
| - | - |
| `minimal` | `$0.012 / request` |
| `low` | `$0.025 / request` |
| `medium` | `$0.10 / request` |
| `high` | `$0.50 / request` |
| `xhigh` | `$1.00 / request` |
| `auto` | Metered; up to the default `$5` cap |
| `ultra` | Metered; up to the default `$20` cap |

`budget.maxCostDollars` sets a per-run ceiling for `auto` and `ultra`, from `$1` to `$100`. The default is `$5` for `auto` and `$20` for `ultra`. Runs that finish early cost less. Fixed efforts do not accept a budget.

### Choosing an effort mode

Fixed effort modes work well when you want predictable per-request pricing for standard research. Use `auto` for variable-scope work like list building, where the number of entities can vary from request to request.

| Effort | Best for | Suggested schema complexity | Runtime expectation |
| - | - | - | - |
| `minimal` | Lowest-cost lookups, very narrow factual tasks, short answers | One or two fields, shallow schema | Cheapest, least exhaustive |
| `low` | Simple lookups, narrow factual tasks, short answers | A few fields, shallow schema | Fast, light research |
| `medium` | Default starting point for most standard research tasks | Moderate field count, simple nested objects | Balanced quality/runtime |
| `high` | Harder research, more citations, stricter completeness | Larger schemas or more nuanced fields | Slower, more thorough |
| `xhigh` | High-value tasks where completeness matters more than cost/latency | Complex schemas, many fields, difficult verification | Slowest fixed effort |
| `auto` | Variable-scope work, list building, unknown task difficulty | Flexible; useful when entity count or work required is unknown | Variable |
| `ultra` | Large list building, exhaustive research, hard-to-verify criteria | Complex schemas, many fields, difficult verification | Longest-running |

Start with `medium` for standard single-entity research. Drop to `low` or `minimal` when cost and latency matter more than completeness. Move up to `high` or `xhigh` when the output schema is larger, fields need verification, or the task needs deeper reasoning. Use `auto` when you don't know the scope ahead of time, such as list building or workflows that may return many entities. Use [`ultra`](/docs/agent/agent-ultra) when completeness matters more than latency or cost.

Runtime varies by query difficulty, schema complexity, and external source availability. Treat effort modes as quality/cost/runtime tradeoffs rather than strict latency guarantees.

<Card title="Agent Ultra" icon="rocket" href="/docs/agent/agent-ultra" cta="Open guide" arrow="true">
  Run Exa Agent at its highest effort for large list building and exhaustive research.
</Card>

## Zero Data Retention

Exa Agent supports [Zero Data Retention](/docs/admin/security/zero-data-retention) (ZDR). ZDR is enabled per team. [Contact us](mailto:sales@exa.ai) to enable it for your account.

When ZDR is enabled for your team:

* Create runs with streaming (`Accept: text/event-stream`) to consume output live, or poll asynchronous runs within the retention window.
* Run data is available while the run executes and for up to 10 minutes after it reaches a terminal state. After that window, the run cannot be retrieved.
* `previousRunId` is not available; requests that include it return a `400` error.
* `dataSources` can include only [ZDR-eligible Exa Connect providers](/docs/agent/connect/overview#zero-data-retention): Fiber.ai (`fiber`), Baselayer (`baselayer`), Macrobond (`macrobond`), and Jinko (`jinko`). Requests that include any other provider return a `400` error that names it.

## Next steps

<Columns cols={2}>
  <Card title="What's in the index" icon="search" href="/docs/search/data/overview" cta="Open guide" arrow="true">
    Explore news, code, company, and people sources across the public web.
  </Card>

  <Card title="Exa Connect" icon="database" href="/docs/agent/connect/overview" cta="Open guide" arrow="true">
    Attach premium partner databases to a run.
  </Card>

  <Card title="Agent best practices" icon="lightbulb" href="/docs/agent/best-practices" cta="Open guide" arrow="true">
    Best practices for using Exa Agent.
  </Card>

  <Card title="Agent examples" icon="code" href="/docs/agent/examples" cta="Open guide" arrow="true">
    Examples of using Exa Agent.
  </Card>
</Columns>
