> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Batch API

> Run Exa API requests asynchronously in batches.

<Info>
  The Batch API is available for Enterprise customers after Exa enables it for your team. Contact [sales@exa.ai](mailto:sales@exa.ai) to discuss Enterprise access and enablement.
</Info>

The Batch API lets you submit many Exa API requests at once and retrieve their results later as a JSONL file. Instead of sending thousands of individual requests and managing rate limits and retries yourself, you send a single batch, poll its status, and download all the results in one file.

Use it for offline enrichment, backfills, or any other job that does not need an immediate response. Full request and response schemas are in the [API reference](/docs/reference/batches/create-a-batch).

<Note>
  The Batch API is in beta. Include the `Exa-Beta: batches-2026-06-06` header on every request.
</Note>

## Supported requests

Each batch item must be a `POST` request to one of these routes:

| Route | Use case |
| - | - |
| `/search` | Run Exa search requests asynchronously |
| `/agent/runs` | Run Exa Agent requests asynchronously |

Each item needs a batch-unique `customId`. The same `customId` is returned in the results file so you can map output rows back to your input data.

## Create a batch

<CodeGroup>
  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/batches" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -H "Exa-Beta: batches-2026-06-06" \
    -H "Content-Type: application/json" \
    -d '{
      "requests": [
        {
          "customId": "row-1",
          "method": "POST",
          "url": "/search",
          "body": {
            "query": "Latest AI infrastructure funding rounds"
          }
        },
        {
          "customId": "row-2",
          "method": "POST",
          "url": "/agent/runs",
          "body": {
            "query": "Summarize recent vector database launches"
          }
        }
      ],
      "metadata": {
        "project": "weekly-digest"
      }
    }'
  ```
</CodeGroup>

The response contains the batch ID and initial status:

<Accordion title="Example response">
  ```json theme={null}
  {
    "id": "batch_01j7x9v0m2n4p6q8r0s2t4v6w8",
    "object": "batch",
    "status": "in_progress",
    "requestCounts": {
      "total": 2,
      "completed": 0,
      "failed": 0
    },
    "createdAt": "2026-06-06T12:00:00.000Z",
    "expiresAt": null,
    "endedAt": null,
    "resultsUrl": null,
    "metadata": {
      "project": "weekly-digest"
    }
  }
  ```
</Accordion>

## Check status

Poll the batch until it reaches a terminal status:

<CodeGroup>
  ```bash cURL theme={null}
  curl -s "https://api.exa.ai/batches/batch_01j7x9v0m2n4p6q8r0s2t4v6w8" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -H "Exa-Beta: batches-2026-06-06"
  ```
</CodeGroup>

Batch statuses are:

| Status | Meaning |
| - | - |
| `in_progress` | The batch is running |
| `completed` | All requests have finished and results are available |
| `cancelling` | Cancellation was requested and in-flight work is draining |
| `cancelled` | The batch was cancelled |
| `expired` | Results are no longer available |

When the batch completes, `resultsUrl` contains a download URL for the JSONL results file, and `expiresAt` is set to the end of the results retention window.

<Warning>
  `resultsUrl` is a short-lived presigned URL. Re-fetch the batch to get a fresh URL whenever you need to download results again.
</Warning>

## List batches

<CodeGroup>
  ```bash cURL theme={null}
  curl -s "https://api.exa.ai/batches?limit=100" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -H "Exa-Beta: batches-2026-06-06"
  ```
</CodeGroup>

The response is cursor-paginated: `data` holds up to `limit` batches, and when `hasMore` is `true`, pass `nextCursor` as the `cursor` query parameter to fetch the next page.

Pass `status=completed` to list only completed batches:

```bash theme={null}
curl -s "https://api.exa.ai/batches?status=completed" \
  -H "Authorization: Bearer $EXA_API_KEY" \
  -H "Exa-Beta: batches-2026-06-06"
```

`completed` is the only supported value; any other value returns an error. Completed listings are ordered by expiry and use their own cursor, so keep sending `status=completed` on every page — completed and unfiltered cursors are not interchangeable.

```json theme={null}
{
  "object": "list",
  "data": [],
  "hasMore": false,
  "nextCursor": null
}
```

## Download results

<CodeGroup>
  ```bash cURL theme={null}
  curl "$RESULTS_URL" -o results.jsonl
  ```
</CodeGroup>

Each JSONL line contains the original `customId` and either a `response` or an `error`:

```json theme={null}
{ "customId": "row-1", "response": { "statusCode": 200, "body": { "results": [] } } }
{ "customId": "row-2", "error": { "code": "API_ERROR", "message": "request failed" } }
```

## Cancel a batch

<CodeGroup>
  ```bash cURL theme={null}
  curl -X POST "https://api.exa.ai/batches/batch_01j7x9v0m2n4p6q8r0s2t4v6w8/cancel" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -H "Exa-Beta: batches-2026-06-06"
  ```
</CodeGroup>

## Delete a batch

<CodeGroup>
  ```bash cURL theme={null}
  curl -X DELETE "https://api.exa.ai/batches/batch_01j7x9v0m2n4p6q8r0s2t4v6w8" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -H "Exa-Beta: batches-2026-06-06"
  ```
</CodeGroup>

## Access

To enable the Batch API for a team, contact [sales@exa.ai](mailto:sales@exa.ai).
