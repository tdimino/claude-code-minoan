> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Agent Ultra

> Run Exa Agent at its highest effort for large list building and exhaustive research.

Agent Ultra is Exa Agent's highest-effort mode. It runs longer and spends more compute than any other effort to return the most complete results.

Use it for large list building, deep multi-source research, and criteria that are hard to verify, where completeness matters more than latency or cost. For a predictable price per request, use a [fixed effort](/docs/agent/quickstart#effort) instead.

<Info>
  Agent Ultra is metered at the standard [Agent usage rates](/docs/admin/pricing#agent), up to a
  default \$20 per run. Runs that finish early cost less.
</Info>

## Run Agent Ultra

Set `effort: "ultra"` on an [Agent run](/docs/agent/quickstart). The rest of the request works like any other run, including `outputSchema`, `input.data`, and streaming.

<CodeGroup>
  ```python Python theme={null}
  from exa_py import Exa

  exa = Exa()

  run = exa.agent.runs.create(
      query="Find all companies building browser automation tools in the United States.",
      effort="ultra",
  )
  run = exa.agent.runs.poll_until_finished(run.id, timeout_ms=3 * 60 * 60 * 1000)

  print(run.stop_reason)
  if run.output:
      print(run.output.text)
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();

  const run = await exa.agent.runs.create({
    query: "Find all companies building browser automation tools in the United States.",
    effort: "ultra"
  });
  const finished = await exa.agent.runs.pollUntilFinished(run.id, {
    timeoutMs: 3 * 60 * 60 * 1000
  });

  console.log(finished.stopReason);
  console.log(finished.output?.text);
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/agent/runs" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "Find all companies building browser automation tools in the United States.",
      "effort": "ultra"
    }'
  ```
</CodeGroup>

Ultra runs typically complete complex tasks in about 30 minutes, but can take up to three hours for very challenging ones.

By default, the SDK polling helpers time out after one hour, so use a longer timeout as shown above or [stream events](/docs/agent/quickstart#stream-events) for extended runs.

## Set a budget

Add `budget` to cap how much a run spends and how long it takes. Both fields are optional.

| Field | Accepts | Default |
| - | - | - |
| `maxCostDollars` | \$1 to \$100 | \$20 |
| `maxDurationSeconds` | 300 to 10,800 (5 minutes to 3 hours) | None |

```json theme={null}
{
  "query": "Find all companies building browser automation tools in the United States.",
  "effort": "ultra",
  "budget": {
    "maxCostDollars": 10,
    "maxDurationSeconds": 1800
  }
}
```

As a run approaches either limit, the agent stops starting new work and returns what it has found.

## Stop a run early

[Stop](/docs/reference/agent-api/stop-a-run) Agent Ultra run to end it now and keep what it has found. The run completes with `stopReason: "stopped"`, and you are billed for usage up to the stop.

```bash theme={null}
curl -s -X POST "https://api.exa.ai/agent/runs/$RUN_ID/stop" \
  -H "Authorization: Bearer $EXA_API_KEY"
```

## Stop reasons

`stopReason` on a finished run says why it ended. Every reason except `error` and `cancelled` means the run completed and returned what it found.

| `stopReason` | Meaning |
| - | - |
| `schema_satisfied` | The agent finished the task. |
| `budget_reached` | The run reached `budget.maxCostDollars`. |
| `time_limit_reached` | The run reached `budget.maxDurationSeconds`. |
| `stopped` | You stopped the run. |
| `error` | The run failed. |
| `cancelled` | The run was cancelled. |

## Limits and compatibility

<AccordionGroup>
  <Accordion title="Ultra-only controls">
    `budget.maxDurationSeconds` and stopping a run early work only with `effort: "ultra"`.
    `budget.maxCostDollars` also works with `auto`.
  </Accordion>

  <Accordion title="OpenAI Responses API">
    On [`/responses`](/docs/integrations/openai-sdk#agent-via-responses-api), set
    `reasoning.effort: "ultra"` with `stream: true` or `background: true`.
  </Accordion>
</AccordionGroup>

## Next steps

<Columns cols={2}>
  <Card title="Agent quickstart" icon="bot" href="/docs/agent/quickstart" cta="Open guide" arrow="true">
    Create runs, stream events, and read structured output.
  </Card>

  <Card title="Agent examples" icon="code" href="/docs/agent/examples" cta="Browse examples" arrow="true">
    Copy complete list-building, enrichment, and follow-up requests.
  </Card>
</Columns>
