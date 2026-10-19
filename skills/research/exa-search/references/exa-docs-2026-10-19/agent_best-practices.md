> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Agent Best Practices

> Tune query quality, structured output, effort, and cost for production Exa Agent integrations.

Use this guide after the [Exa Agent quickstart](/docs/agent/quickstart) to improve query quality, structure outputs, and control runtime and cost. For complete requests, start with [Agent examples](/docs/agent/examples).

## Core principles

Treat `query` as a task specification. Name what Agent should find, the scope of the work, the evidence required, and what a complete result looks like.

<CodeGroup>
  ```python Python theme={null}
  run = exa.agent.runs.create(
      query="Find up to 10 current engineering leaders at AI infrastructure companies that raised a Series A or B in the last 6 months. Include only people whose current role and company funding can be verified from public sources.",
  )
  ```

  ```javascript JavaScript theme={null}
  const run = await exa.agent.runs.create({
    query:
      "Find up to 10 current engineering leaders at AI infrastructure companies that raised a Series A or B in the last 6 months. Include only people whose current role and company funding can be verified from public sources."
  });
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/agent/runs" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Find up to 10 current engineering leaders at AI infrastructure companies that raised a Series A or B in the last 6 months. Include only people whose current role and company funding can be verified from public sources."
    }'
  ```
</CodeGroup>

Without an `outputSchema`, Agent returns prose in `output.text` and citations in `output.grounding`. Add another field only when it has a clear job:

| Field | Use it when |
| - | - |
| `outputSchema` | Downstream code needs structured fields |
| `input.data` | You already have rows to enrich |
| `input.exclusion` | Known records should not be returned |
| `dataSources` | A field should come from an [Exa Connect](/docs/agent/connect/overview) partner |
| `previousRunId` | The request continues a completed run |
| `effort` | Cost or research depth needs an explicit setting |
| `budget.maxCostDollars` | An `auto` or `ultra` run needs a hard cost ceiling |
| `userIdentifier` | The run is made on behalf of one of your users; see [end-user attribution](/docs/search/best-practices#user-identifier). A follow-up run that omits it keeps the previous run's value |

Keep rows, exclusions, and response shape in their dedicated fields rather than embedding them in `query`.

## Writing list-building and enrichment queries

For list building, define the entity, target count, qualification criteria, exclusions, and evidence bar. For enrichment, put the existing records in `input.data` and describe only the research Agent should add.

Ask for a rationale when qualification requires judgment. Give examples only when a criterion has multiple plausible interpretations.

<CodeGroup>
  ```text Query theme={null}
  Find up to 20 current engineering leaders at US-based AI infrastructure companies
  that announced a Series A or B between March 1 and August 31, 2026.

  Include CTOs, VPs of Engineering, and Heads of Engineering. Exclude founders without
  an operating engineering role and anyone whose current employment cannot be verified.
  For each person, return their name, current title, company, company website, funding
  announcement date, and a short explanation of why they qualify. Verify employment on
  the company website or another current source, and verify funding from the company
  announcement or a reputable business publication.
  ```
</CodeGroup>

See [Find all GTM members](/docs/agent/examples#find-all-code) for a discovery request and [Enrich input rows](/docs/agent/examples#enrich-input-rows-code) for the corresponding row-enrichment pattern.

## Handle asynchronous runs

Agent runs can take seconds to minutes while they search, read, and reason. Build around the lifecycle instead of holding an application request open.

<Steps>
  <Step title="Create and persist">
    Create the run and save its returned `id` with your request metadata. The create response is not the final result.
  </Step>

  <Step title="Wait for a terminal state">
    Use an SDK polling helper, poll `GET /agent/runs/{id}`, or consume the SSE stream. Continue while the run is `queued` or `running`.
  </Step>

  <Step title="Store the result">
    Stop waiting at `completed`, `failed`, or `cancelled`, then persist the terminal response and grounding.
  </Step>
</Steps>

Persisting the run ID lets your application recover after a restart, reconnect to a stream, and inspect failures. Keep latency down by narrowing the scope, limiting result count, keeping the schema focused, and choosing `minimal` or `low` when speed matters more than completeness.

For batches, benchmark representative tasks before estimating concurrency or putting Agent on a synchronous UI path. Runtime varies with item count, schema complexity, source availability, and effort.

For Zero Data Retention teams, consume the live stream or poll within the retention window. `previousRunId` is not available, and `dataSources` can include only [ZDR-eligible Connect providers](/docs/agent/connect/overview#zero-data-retention); any other provider returns a `400` error that names it. See [Zero Data Retention](/docs/admin/security/zero-data-retention).

## Write custom JSON schemas for structured output

Use `outputSchema` when downstream code needs machine-readable fields, normalized values, table rows, or enrichment records. If a prose answer is enough, omit it and read `output.text`; structured output adds formatting work and can increase latency.

Keep research instructions in `query` and response shape in `outputSchema`. Use clear property names and descriptions, choose the narrowest useful types, and bound arrays with `maxItems`.

<CodeGroup>
  ```json Output schema expandable theme={null}
  {
    "type": "object",
    "properties": {
      "people": {
        "type": "array",
        "maxItems": 10,
        "description": "Current engineering leaders who satisfy every criterion in the query.",
        "items": {
          "type": "object",
          "properties": {
            "name": {
              "type": "string",
              "description": "The person's full name."
            },
            "job_title": {
              "type": "string",
              "description": "Their current title at the qualifying company."
            },
            "company": {
              "type": "string",
              "description": "The qualifying company's canonical name."
            },
            "qualification_rationale": {
              "type": "string",
              "description": "A concise explanation of how the person satisfies the query criteria."
            }
          },
          "required": ["name", "job_title", "company", "qualification_rationale"]
        }
      }
    },
    "required": ["people"]
  }
  ```
</CodeGroup>

Schema adherence validates shape, not facts. Agent may return `null` when evidence does not support a field, even if the submitted schema marks it as required or non-nullable. `stopReason: schema_satisfied` means Agent considers the expected shape complete with those nulls allowed; it does not guarantee strict validation against the submitted schema.

Do not duplicate Exa's built-in citations or confidence in your schema. Add a rationale field only when each item should explain why it qualifies, and persist `output.grounding` with the structured result. Verify important claims against their sources and test schema changes on representative inputs before shipping.

Browse the [structured Agent examples](/docs/agent/examples) to compare schemas for list building, KYB, job postings, exclusions, and continued runs.

## Agent vs Search

| Need | Start with |
| - | - |
| Web results for your LLM | [Search](/docs/search/quickstart) |
| Fast research and synthesis | [Deep Search](/docs/search/deep-search) |
| Async list building, multi-hop research, or enrichment | [Agent](/docs/agent/quickstart) |

Use Agent when the work requires several retrieval steps, per-entity verification, or enrichment over known records. Use Search when you need pages quickly and your application will perform the remaining reasoning.

## Tips for common use cases

| If you need | Use | Avoid |
| - | - | - |
| A researched list of unknown size | `auto` and a bounded `outputSchema` | A fixed cheap effort and an unbounded array |
| Enrichment of records you already have | `input.data` plus fields to add | Pasting the table into `query` |
| A follow-up over the last result set | `previousRunId` | Re-sending the full previous output |
| Records that should not appear again | `input.exclusion` plus downstream deduplication | Treating exclusions as a strict identity guarantee |
| Premium provider data | [Exa Connect](/docs/agent/connect/overview) with `dataSources` | Asking Agent to infer provider-only fields from the open web |
| Predictable per-request cost | A fixed `effort` | `auto` or `ultra` without a budget |
| Completeness over latency & cost | `xhigh` or [`ultra`](/docs/agent/agent-ultra) | Raising effort before tightening the query |

## Next steps

<Columns cols={2}>
  <Card title="Agent quickstart" icon="bot" href="/docs/agent/quickstart" cta="Open guide" arrow="true">
    Create a run, stream events, set effort, and read structured output.
  </Card>

  <Card title="Agent examples" icon="layers" href="/docs/agent/examples" cta="Browse examples" arrow="true">
    Copy complete list-building, enrichment, KYB, exclusion, and follow-up requests.
  </Card>

  <Card title="Exa Connect" icon="database" href="/docs/agent/connect/overview" cta="Browse data partners" arrow="true">
    Add premium company, people, traffic, compliance, finance, and other provider data.
  </Card>

  <Card title="Search best practices" icon="sparkles" href="/docs/search/best-practices" cta="Read guide" arrow="true">
    Retrieval quality, latency, and synthesis when Search is enough.
  </Card>
</Columns>
