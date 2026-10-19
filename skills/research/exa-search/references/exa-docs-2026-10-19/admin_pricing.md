> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Pricing

> Pay-as-you-go rates for Exa Search, Contents, Answer, Monitors, and the Agent API

***

Exa is pay-as-you-go. There is no subscription and no minimum spend: you load credits and are charged per request, at the rates below.

<Check>
  **Start for free.** The Free Tier gives you \$10 in credits (up to 2,500 Lite searches) the day you sign up, and your free balance resets to \$10 on the first of every month. No payment method required. Complete onboarding in the dashboard and your first team earns a one-time \$10 bonus. Get an API key and start building.

  **Scaling up?** For high volume, custom indexes, higher rate limits, SLAs, or Zero Data Retention, [talk to us](https://exa.ai/contact/sales) about an [Enterprise plan](#enterprise) with volume discounts.
</Check>

<Card title="Get your Exa API key" icon="key" horizontal href="https://dashboard.exa.ai/api-keys">
  Create a key in the dashboard. New accounts start with free credits.
</Card>

## Products

<Columns cols={3}>
  <Card title="Search" icon="search" href="/docs/search/quickstart">
    From **\$4** / 1k requests

    Real-time search with token-efficient page contents.
  </Card>

  <Card title="Deep Search" icon="microscope" href="/docs/search/deep-search">
    **\$12–15** / 1k requests

    Multi-step research with structured outputs and citations.
  </Card>

  <Card title="Contents" icon="file-text" href="/docs/contents/quickstart">
    **\$1** / 1k pages

    Full page text, highlights, and summaries for known URLs.
  </Card>

  <Card title="Answer" icon="message-circle" href="/docs/reference/answer">
    **\$5** / 1k requests

    An LLM answer to a question, with citations.
  </Card>

  <Card title="Monitors" icon="bell" href="/docs/monitors/quickstart">
    **\$15** / 1k requests

    Scheduled searches that surface new events on the web.
  </Card>

  <Card title="Agent" icon="bot" href="/docs/agent/quickstart">
    **\$0.012–\$1.00** / fixed-effort run, or usage-based

    Async deep research, list building, and enrichment.
  </Card>
</Columns>

## Search, Contents, Answer, and Monitors

Each endpoint has a base price per request that includes up to 10 results. Additional results and Exa-generated page summaries are billed on top.

| Endpoint | Base price<br />(up to 10 results) | Each result above 10 | AI page summaries |
| - | - | - | - |
| `/search` (`lite`) | \$4 / 1k requests | \$1 / 1k results | — |
| `/search` (`instant`) | \$4 / 1k requests | \$1 / 1k results | \$1 / 1k pages |
| `/search` (`auto`, `fast`) | \$7 / 1k requests | \$1 / 1k results | \$1 / 1k pages |
| `/answer` | \$5 / 1k requests | — | — |
| `/monitors` | \$15 / 1k requests | \$1 / 1k results | \$1 / 1k pages |
| `/contents` | \$1 / 1k pages, per content type | — | \$1 / 1k pages |

`instant` and `fast` are [legacy search types](/docs/search/quickstart#legacy-search-types) and keep these prices.

## Agent

Set a fixed `effort` on [Agent](/docs/agent/quickstart) for a predictable per-request price. `auto` is the default metered mode; [`ultra`](/docs/agent/agent-ultra) is also metered and uses the same usage rates:

| Effort | Price |
| - | - |
| `minimal` | \$0.012 / request |
| `low` | \$0.025 / request |
| `medium` | \$0.10 / request |
| `high` | \$0.50 / request |
| `xhigh` | \$1.00 / request |

Metered runs bill actual usage up to their per-run cap. `auto` defaults to a \$5 cap; `ultra` defaults to a \$20 cap:

| Usage component | Price |
| - | - |
| Agent Compute Units | \$0.10 / ACU |
| Search tool calls | \$0.005 / search |
| Email contact enrichment | \$0.02 / email |
| Phone contact enrichment | \$0.07 / phone number |

### Connect providers

Runs that use [Exa Connect](/docs/agent/connect/overview) data sources
additionally bill each provider call — for example
[Fiber.ai](/docs/agent/connect/fiber#pricing) at \$0.02 per credit and
[Baselayer](/docs/agent/connect/baselayer#pricing) at \$0.15–\$4.00 per
order depending on the operation. See
[Connect pricing](/docs/agent/connect/overview#pricing) for all
provider rates.

## Deep Search

Set with `type` on [`/search`](/docs/search/deep-search). Additional results and AI page summaries cost the same as standard search.

| Type | Base price<br />(up to 10 results) | Latency | Best for |
| - | - | - | - |
| `deep-lite` | \$12 / 1k requests | \~4 seconds | Lightweight synthesis |
| `deep` | \$12 / 1k requests | 4–15 seconds | Multi-step reasoning with structured outputs |
| `deep-reasoning` | \$15 / 1k requests | 12–40 seconds | Harder research tasks |

`deep-reasoning` is a [legacy search type](/docs/search/quickstart#legacy-search-types) and keeps this price.

## Enterprise

For high volume, custom datasets, and stricter security requirements.

<Columns cols={3}>
  <Card title="Powerful search" icon="gauge">
    Up to 1,000 results per search, requests above 25 results, custom rate limits (QPS), tailored moderation, and custom indexes.
  </Card>

  <Card title="Enterprise support" icon="headphones">
    SLAs and MSAs, 1:1 onboarding and support, and [Zero Data Retention](/docs/admin/security/zero-data-retention).
  </Card>

  <Card title="Custom pricing" icon="tag">
    Volume discounts and postpaid invoice billing.
  </Card>
</Columns>

<Card title="Talk to us" icon="mail" horizontal href="https://exa.ai/contact/sales">
  Get a quote for enterprise volume and terms
</Card>

## Cost glossary

<AccordionGroup>
  <Accordion title="Request">
    One API call to an endpoint. Prices are quoted per 1,000 requests, so a \$7 / 1k rate is \$0.007 per call.
  </Accordion>

  <Accordion title="Result">
    One search result returned in a response. The base price covers the first 10 results in a request; every result above 10 adds \$1 / 1k results. Requesting `numResults: 20` therefore costs the base price plus 10 additional results.
  </Accordion>

  <Accordion title="Page and content type">
    A page is one URL that Exa returns content for. A content type is one view of that page: `text`, `highlights`, or `summary`. `/contents` bills each content type separately, so one page with `text` and `highlights` counts as two.
  </Accordion>

  <Accordion title="AI page summary">
    An Exa-generated summary of a page, produced by an extra LLM call on our side. Billed at \$1 / 1k pages on any endpoint that returns one.
  </Accordion>

  <Accordion title="Agent Compute Unit (ACU)">
    The unit of model computation an Agent run consumes, reported as `usage.agentComputeUnits`. Longer runs, larger `input.data`, and more reasoning steps consume more ACUs.
  </Accordion>

  <Accordion title="Effort">
    The Agent parameter that trades cost and latency against thoroughness. `auto` bills by consumption (ACUs plus tool calls) up to a default \$5 cap; `ultra` uses the same usage rates up to a default \$20 cap. Fixed efforts bill a flat price per request. See [Agent effort modes](/docs/agent/quickstart#effort).
  </Accordion>

  <Accordion title="Contact enrichment">
    An Agent lookup that returns an email address or phone number for a person or company. Billed per contact found, on top of the run's other costs.
  </Accordion>

  <Accordion title="Credits">
    Prepaid dollar balance on your account. Usage draws down credits at the rates above.
  </Accordion>
</AccordionGroup>

<Card title="Billing" icon="credit-card" horizontal href="/docs/admin/billing">
  Add credits, set up auto recharge, and find your invoices
</Card>
