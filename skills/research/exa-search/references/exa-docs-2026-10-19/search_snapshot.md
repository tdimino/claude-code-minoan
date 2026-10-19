> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Exa Snapshot

> Pin Search and Contents to a stored version of a page at a datetime you choose.

Exa Snapshot keeps stored versions of pages Exa has crawled. Send `snapshotAsOf` to pin the request to a datetime.

Use this to backtest agents, run reproducible evals, and compare earlier versions of docs, pricing pages, policies, and filings.

<Info>
  Exa Snapshot is available on pay as you go at 10 QPS, with a rolling 5-month index window.
  After 100 requests, [talk to sales](https://exa.ai/contact/sales) to continue. Enterprise plans
  include Snapshot when the contract covers it.
  The Free tier does not include Snapshot, whatever its credit balance. Add a card and buy credits
  on the [Billing dashboard](https://dashboard.exa.ai/billing) to move to a pay-as-you-go plan.
</Info>

## Search at a datetime

On `/search`, put `snapshotAsOf` inside `contents`.

<CodeGroup>
  ```python Python theme={null}
  from exa_py import Exa

  exa = Exa()

  result = exa.search(
      "latest stable Python release notes",
      num_results=3,
      contents={
          "snapshot_as_of": "2026-07-01T00:00:00Z",
          "highlights": True,
      },
  )

  for r in result.results:
      print(r.title, r.url)
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();

  const result = await exa.search("latest stable Python release notes", {
    numResults: 3,
    contents: {
      snapshotAsOf: "2026-07-01T00:00:00Z",
      highlights: true
    }
  });

  for (const r of result.results) {
    console.log(r.title, r.url);
  }
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/search" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "query": "latest stable Python release notes",
      "numResults": 3,
      "contents": {
        "snapshotAsOf": "2026-07-01T00:00:00Z",
        "highlights": true
      }
    }'
  ```
</CodeGroup>

Exa discovers candidate URLs, then keeps only pages with a stored version at or before `snapshotAsOf`.

<Accordion title="Example response">
  ```json theme={null}
  {
    "requestId": "211fc1f57b87a792de082309ef3bce95",
    "results": [
      {
        "id": "https://docs.python.org/3/whatsnew/changelog.html",
        "url": "https://docs.python.org/3/whatsnew/changelog.html",
        "title": "Changelog — Python 3.14.6 documentation",
        "highlights": [
          "Changelog — Python 3.14.6 documentation\n...\n## Python 3.14.6 final¶\n...\nRelease date: 2026-06-10"
        ],
        "image": "https://docs.python.org/3.14/_images/social_previews/..."
      },
      {
        "id": "https://docs.python.org/3/whatsnew/index.html",
        "url": "https://docs.python.org/3/whatsnew/index.html",
        "title": "What's New in Python — Python 3.14.6 documentation",
        "highlights": ["What's new in Python\n...\n- Python 3.14.6 final\n- Python 3.14.5 final"]
      },
      {
        "id": "https://docs.python.org/3/whatsnew/3.14.html",
        "url": "https://docs.python.org/3/whatsnew/3.14.html",
        "title": "What's new in Python 3.14 — Python 3.14.6 documentation",
        "highlights": ["Python 3.14 is the latest stable release of the Python programming language..."]
      }
    ]
  }
  ```
</Accordion>

## Pin contents to a datetime

Add `snapshotAsOf` at the top level of a `/contents` request.

<CodeGroup>
  ```python Python theme={null}
  from exa_py import Exa

  exa = Exa()

  result = exa.get_contents(
      ["https://en.wikipedia.org/wiki/2026"],
      snapshot_as_of="2026-06-01T00:00:00Z",
      text=True,
  )

  print(result.results[0].text[:300])
  ```

  ```javascript JavaScript theme={null}
  import Exa from "exa-js";

  const exa = new Exa();

  const result = await exa.getContents(
    ["https://en.wikipedia.org/wiki/2026"],
    {
      snapshotAsOf: "2026-06-01T00:00:00Z",
      text: true
    }
  );

  console.log(result.results[0].text.slice(0, 300));
  ```

  ```bash cURL theme={null}
  curl -s -X POST "https://api.exa.ai/contents" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer $EXA_API_KEY" \
    -d '{
      "ids": ["https://en.wikipedia.org/wiki/2026"],
      "snapshotAsOf": "2026-06-01T00:00:00Z",
      "text": true
    }'
  ```
</CodeGroup>

Exa returns the newest stored version at or before that datetime.

<Accordion title="Example response">
  ```json theme={null}
  {
    "requestId": "c05151f7df9cd9d8785e0acf0935355d",
    "results": [
      {
        "id": "https://en.wikipedia.org/wiki/2026",
        "url": "https://en.wikipedia.org/wiki/2026",
        "title": "2026",
        "author": null,
        "text": "2026\n\n2026 (MMXXVI) is the current year, and is a common year starting on Thursday of the Gregorian calendar...",
        "image": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/..."
      }
    ],
    "statuses": [
      {
        "id": "https://en.wikipedia.org/wiki/2026",
        "status": "success",
        "source": "cached"
      }
    ]
  }
  ```
</Accordion>

<Tip>
  IDs with no eligible version are omitted from `results` and reported in `statuses` with
  `"status": "error"` and an `error` object whose `tag` is `CONTENT_NOT_CACHED`:
  `{"status": "error", "error": {"tag": "CONTENT_NOT_CACHED", "httpStatusCode": 404}}`.
</Tip>

## How snapshots work

| Field | Where | Meaning |
| - | - | - |
| `snapshotAsOf` | Request | Cutoff instant as an ISO 8601 date-time (`2026-06-01T00:00:00Z`) or date (`2026-06-01`, midnight UTC). Exa returns the newest stored version at or before this instant. |

For both endpoints:

* Returned page content comes from that stored version.
* Title, author, publication date, text, highlights, and summaries are generated only from that version.
* Pages without an eligible version in the 5-month window are omitted.

<Note>
  On Search, the cutoff bounds content, not ranking. Exa still uses current retrieval signals to
  discover candidate URLs. Use the results as evidence bounded by `snapshotAsOf`, not as an exact
  reconstruction of what a search would have ranked at that time.
</Note>

## Limits and compatibility

<AccordionGroup>
  <Accordion title="Access, rate limit, and lookback">
    Pay as you go includes 10 QPS and a rolling 5 months of index access. A `snapshotAsOf` older
    than that window is rejected. After 100 requests, [talk to sales](https://exa.ai/contact/sales)
    to continue.

    | Plan | Snapshot access |
    | - | - |
    | Free | Not included. Requests return `403` `SNAPSHOT_NOT_ON_PLAN`, and the Snapshot control on the playground is disabled. Add a card and buy credits on the [Billing dashboard](https://dashboard.exa.ai/billing) to move to a pay-as-you-go plan. |
    | Pay as you go | 100 requests at 10 QPS, up to 10 search results or 1 contents URL per request. Past that, requests return `403` `SNAPSHOT_TRIAL_EXHAUSTED` or `SNAPSHOT_TRIAL_CAP_EXCEEDED`. |
    | Enterprise | Included when your contract covers it; otherwise requests return `403` `SNAPSHOT_NOT_IN_CONTRACT`. [Talk to sales](https://exa.ai/contact/sales) to add it to your contract. |
  </Accordion>

  <Accordion title="Historical requests use stored content">
    Do not combine `snapshotAsOf` with options that can reach the live web or expand to other pages.
    Omit `livecrawl`, `livecrawlTimeout`, `maxAgeHours`, and `subpages` entirely; requests that set
    any of them alongside `snapshotAsOf` are rejected with `INVALID_REQUEST`.
  </Accordion>

  <Accordion title="Supported Search requests">
    Exa Snapshot on Search supports `auto`, `fast`, and `instant`. `deep-lite` is supported on teams
    where it is enabled; [talk to sales](https://exa.ai/contact/sales) to turn it on. It does not
    support `deep` or `deep-reasoning`. It also supports `lite`. `fast` and `instant` are
    [legacy search types](/docs/search/quickstart#legacy-search-types).

    Exa Snapshot does not support the `category` parameter on Search.
  </Accordion>
</AccordionGroup>

## Common uses

Use Exa Snapshot when the task depends on what Exa had stored by a specific datetime:

* Backtest an agent without exposing it to later page updates.
* Run an evaluation against a repeatable content boundary.
* Compare earlier versions of documentation, pricing, policies, or filings.
