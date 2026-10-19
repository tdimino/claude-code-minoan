> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Search

> The search endpoint lets you search the web and extract contents from the results.

<Card title="Get your Exa API key" icon="key" horizontal href="https://dashboard.exa.ai/api-keys">
  Create a key in the dashboard. New accounts start with free credits.
</Card>


## OpenAPI

````yaml exa-spec.yaml POST /search
openapi: 3.1.0
info:
  title: Exa Public API
  version: 2.0.0
servers:
  - url: https://api.exa.ai
security:
  - apiKey: []
  - bearer: []
paths:
  /search:
    post:
      summary: Search
      description: >-
        Perform a search with an Exa prompt-engineered query and retrieve a list
        of relevant results. Optionally get contents.
      operationId: search
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/SearchRequest'
      responses:
        '200':
          description: OK
          headers:
            x-request-id:
              $ref: '#/components/headers/XRequestId'
            x-exa-queued:
              $ref: '#/components/headers/XExaQueued'
            x-exa-queue-ms:
              $ref: '#/components/headers/XExaQueueMs'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SearchResponse'
            text/event-stream:
              schema:
                $ref: '#/components/schemas/SearchStreamChunk'
        '400':
          $ref: '#/components/responses/BadRequestResponse'
        '401':
          $ref: '#/components/responses/UnauthorizedResponse'
        '402':
          description: >-
            Payment required. API-key requests receive the standard error
            envelope when the team is out of credits or a spending budget is
            exceeded. On x402-priced endpoints, requests without an API key
            receive an x402 payment challenge with tag `X402_PAYMENT_REQUIRED`
            that describes how to pay.
          headers:
            x-request-id:
              $ref: '#/components/headers/XRequestId'
          content:
            application/json:
              schema:
                oneOf:
                  - $ref: '#/components/schemas/ErrorResponse'
                  - $ref: '#/components/schemas/X402PaymentChallenge'
        '403':
          $ref: '#/components/responses/ForbiddenResponse'
        '429':
          $ref: '#/components/responses/TooManyRequestsResponse'
        '500':
          $ref: '#/components/responses/InternalServerErrorResponse'
        '503':
          $ref: '#/components/responses/ServiceUnavailableResponse'
      x-codeSamples:
        - lang: bash
          source: |-
            curl -X POST https://api.exa.ai/search \
              -H "x-api-key: $EXA_API_KEY" \
              -H "Content-Type: application/json" \
              -d '{
              "query": "<query>",
              "type": "auto",
              "contents": {
                "highlights": true
              }
            }'
        - lang: javascript
          source: |-
            import Exa from "exa-js";

            const exa = new Exa(process.env.EXA_API_KEY);

            const result = await exa.search("<query>", {
              type: "auto",
              contents: { highlights: true },
            });
        - lang: python
          source: |-
            from exa_py import Exa

            exa = Exa(api_key="YOUR_API_KEY")

            result = exa.search(
                "<query>",
                type="auto",
                contents={"highlights": True},
            )
components:
  schemas:
    SearchRequest:
      type: object
      properties:
        includeDomains:
          anyOf:
            - maxItems: 1200
              type: array
              items:
                type: string
              description: >-
                List of domains or domain paths to include in the search. Each
                entry can be a hostname (for example, `example.com`), a hostname
                with a path prefix (for example, `example.com/docs`), or a
                wildcard subdomain (for example, `*.example.com`). If specified,
                results will only come from the matching domains or paths. Use
                this parameter for domain or path filtering instead of adding a
                `site:` operator to the query.
            - type: 'null'
        excludeDomains:
          anyOf:
            - maxItems: 1200
              type: array
              items:
                type: string
              description: >-
                List of domains or domain paths to exclude from search results.
                Each entry can be a hostname (for example, `example.com`), a
                hostname with a path prefix (for example, `example.com/docs`),
                or a wildcard subdomain (for example, `*.example.com`). If
                specified, no results will be returned from the matching domains
                or paths. Use this parameter for domain or path filtering
                instead of adding a `site:` operator to the query.
            - type: 'null'
        startPublishedDate:
          anyOf:
            - type: string
              description: >-
                Only links with a published date after this will be returned.
                Must be specified in ISO 8601 format.
              format: date-time
            - type: 'null'
        endPublishedDate:
          anyOf:
            - type: string
              description: >-
                Only links with a published date before this will be returned.
                Must be specified in ISO 8601 format.
              format: date-time
            - type: 'null'
        numResults:
          anyOf:
            - type: integer
              minimum: 1
              maximum: 100
              description: >-
                Number of results to return. Limits vary by search type. The
                maximum public limit is 100 results. Contact sales
                (hello@exa.ai) to discuss higher limits.
              default: 10
            - type: 'null'
        moderation:
          anyOf:
            - type: boolean
              description: >-
                Enable content moderation to filter unsafe content from search
                results.
              default: false
            - type: 'null'
        contents:
          anyOf:
            - $ref: '#/components/schemas/ContentsOptions'
              description: >-
                Content options for text, highlights, summary, extras, and
                freshness controls.
            - type: 'null'
        query:
          type: string
          minLength: 1
          description: The query string for the search.
        additionalQueries:
          anyOf:
            - minItems: 1
              maxItems: 10
              type: array
              items:
                type: string
              description: >-
                Additional query variations for deep-search variants. Only works
                with a deep-search type. When provided, these queries are used
                alongside the main query for broader results.
            - type: 'null'
        type:
          anyOf:
            - type: string
              const: auto
              description: >-
                The default. A balanced mode that optimizes for both quality and
                speed and is recommended for most applications.
              title: auto
            - type: string
              const: lite
              description: >-
                Low-cost, low-latency search for real-time and interactive
                experiences such as chat, voice agents, and autocomplete.
                Accepts only `query` (a single string), `objective`,
                `userIdentifier`, `metadata`, `category`, `numResults`,
                `contents.highlights`, `contents.text`, `contents.snapshotAsOf`,
                `userLocation`, `includeDomains`, `excludeDomains`,
                `startPublishedDate`, `endPublishedDate`, `moderation`, and
                `compliance`; a request that sets any other parameter is
                rejected. Serves cached content only; it never fetches live, so
                the freshness options are rejected.
              title: lite
            - type: string
              const: deep-lite
              description: >-
                Performs lightweight research with synthesized results and a
                consistent 4-second latency, lower than full deep search.
              title: deep-lite
            - type: string
              const: deep
              description: Conducts comprehensive multi-step research with synthesis.
              title: deep
            - type: string
              const: instant
              description: >-
                Legacy. Use `lite` instead. Runs a minimum-latency search that
                trades some search depth for speed. Unlike `lite`, it accepts
                every search parameter.
              x-exa-lifecycle: legacy
              x-exa-replacement: lite
              x-mint:
                post:
                  - Legacy
              title: instant
            - type: string
              const: fast
              description: >-
                Legacy. Use `lite` instead. Runs a reduced-latency search for
                user-facing and interactive workflows. Unlike `lite`, it accepts
                every search parameter.
              x-exa-lifecycle: legacy
              x-exa-replacement: lite
              x-mint:
                post:
                  - Legacy
              title: fast
            - type: string
              const: deep-reasoning
              description: >-
                Legacy. Use `deep` instead. Runs `deep` with stronger reasoning
                at each step, for complex analysis and decision-making tasks.
                For agentic, multi-step research, use the Agent API.
              x-exa-lifecycle: legacy
              x-exa-replacement: deep
              x-mint:
                post:
                  - Legacy
              title: deep-reasoning
            - type: string
              title: Other values
            - type: 'null'
          description: >-
            The search mode to use. Defaults to `auto`, a balanced mode
            recommended for most applications.


            - `auto`: The default. A balanced mode that optimizes for both
            quality and speed and is recommended for most applications.

            - `lite`: Low-cost, low-latency search for real-time and interactive
            experiences such as chat, voice agents, and autocomplete. Accepts
            only `query` (a single string), `objective`, `userIdentifier`,
            `metadata`, `category`, `numResults`, `contents.highlights`,
            `contents.text`, `contents.snapshotAsOf`, `userLocation`,
            `includeDomains`, `excludeDomains`, `startPublishedDate`,
            `endPublishedDate`, `moderation`, and `compliance`; a request that
            sets any other parameter is rejected. Serves cached content only; it
            never fetches live, so the freshness options are rejected.

            - `deep-lite`: Performs lightweight research with synthesized
            results and a consistent 4-second latency, lower than full deep
            search.

            - `deep`: Conducts comprehensive multi-step research with synthesis.

            - `instant`: Legacy. Use `lite` instead. Runs a minimum-latency
            search that trades some search depth for speed. Unlike `lite`, it
            accepts every search parameter.

            - `fast`: Legacy. Use `lite` instead. Runs a reduced-latency search
            for user-facing and interactive workflows. Unlike `lite`, it accepts
            every search parameter.

            - `deep-reasoning`: Legacy. Use `deep` instead. Runs `deep` with
            stronger reasoning at each step, for complex analysis and
            decision-making tasks. For agentic, multi-step research, use the
            Agent API.
          default: auto
          x-exa-enum-open: true
        category:
          anyOf:
            - type: string
              enum:
                - company
                - publication
                - news
                - personal site
                - financial report
                - people
              description: >-
                A data category to focus on. Other strings are accepted and used
                as category hints. `people` and `company` return higher-quality
                people profiles and company pages. `publication` returns
                scholarly publications such as research papers, preprints, and
                journal articles, with metadata like authors, venue, and
                citations. `company` and `people` do not support
                `startPublishedDate` or `endPublishedDate`, and `people` also
                does not support `excludeDomains`. Requests that set an
                unsupported filter return a 400 error.
            - type: 'null'
        userLocation:
          anyOf:
            - description: >-
                The end user's location, as a two-letter ISO 3166-1 country code
                (e.g. `US`) or an object with `country`, a `latitude` and
                `longitude` pair, or both. The country localizes results.
                Coordinates are used only for queries that name no place but
                depend on where the user is, such as "coffee near me". They do
                not set a country, so send `country` with them to localize
                results. Send only the precision your use case needs.
              oneOf:
                - type: string
                  description: >-
                    The two-letter ISO 3166-1 country code of the user, e.g.
                    `US`.
                - type: object
                  properties:
                    country:
                      type: string
                      description: >-
                        The two-letter ISO 3166-1 country code of the user, e.g.
                        `US`.
                  required:
                    - country
                  additionalProperties: false
                  description: The user's country only. Equivalent to the string form.
                - type: object
                  properties:
                    country:
                      type: string
                      description: >-
                        The two-letter ISO 3166-1 country code of the user, e.g.
                        `US`.
                    latitude:
                      type: number
                      minimum: -90
                      maximum: 90
                      description: The user's latitude in decimal degrees.
                    longitude:
                      type: number
                      minimum: -180
                      maximum: 180
                      description: The user's longitude in decimal degrees.
                  required:
                    - latitude
                    - longitude
                  additionalProperties: false
                  description: The user's coordinates, with an optional country.
            - type: 'null'
        compliance:
          anyOf:
            - type: string
              enum:
                - hipaa
              description: >-
                Enterprise-only compliance mode. Set to `hipaa` for HIPAA mode.
                Requires cache-only retrieval with supported parameters. See the
                HIPAA docs for details.
            - type: 'null'
        outputSchema:
          anyOf:
            - oneOf:
                - $ref: '#/components/schemas/OutputSchemaText'
                - $ref: '#/components/schemas/OutputSchemaObject'
              description: >-
                JSON schema for synthesized output. Supported root types are
                "text" and "object". When provided, the response includes an
                output object whose content matches this schema. Works with
                every search type and adds about 2 seconds of synthesis latency
                on top of the selected search type. Object schemas are limited
                to 10 properties in total (nested and array items properties
                count toward the limit) and 2 levels of nesting, and every array
                must define items.
              type: object
              discriminator:
                propertyName: type
                mapping:
                  text: '#/components/schemas/OutputSchemaText'
                  object: '#/components/schemas/OutputSchemaObject'
            - type: 'null'
        objective:
          anyOf:
            - type: string
              maxLength: 4096
            - type: 'null'
          description: >-
            The broader goal this search serves: the task the caller is working
            on, beyond the query itself. When exposing this field to an agent as
            a tool parameter, describe it as: "Goal for this search turn; say
            which documents should rank first, which should be excluded, and
            what specific facts or figures to pull from them."
        userIdentifier:
          anyOf:
            - type: string
              minLength: 1
              maxLength: 64
              pattern: ^[A-Za-z0-9_-]+$
            - type: 'null'
          description: >-
            An opaque ID your platform assigns to the end user this request is
            made for, such as a UUID. Lets Exa attribute usage to that end user
            rather than your whole team. Must not contain personal information
            such as an email address, phone number, username, or name. Hash such
            values before sending them. 1 to 64 characters: letters, digits,
            underscores, and hyphens. Retained even when your team has Zero Data
            Retention enabled. Does not affect results.
          example: 7f3a9c52-1d4e-4b8a-9e60-2c5d8a1f0b37
        systemPrompt:
          anyOf:
            - type: string
              description: >-
                Additional instructions that guide generated output or agent
                behavior. Use this for source preferences, novelty constraints,
                duplication constraints, or other behavior guidance.
            - type: 'null'
        stream:
          anyOf:
            - type: boolean
              description: >-
                Requests server-sent events for synthesized output streaming.
                Streaming is currently used only when outputSchema is provided;
                otherwise the endpoint returns the normal JSON search response.
              default: false
            - type: 'null'
        startCrawlDate:
          anyOf:
            - type: string
              format: date-time
              description: >-
                Deprecated. Ignored by the API. Setting it adds an
                `IGNORED_FIELD` warning to the response's `warnings`.
              x-exa-lifecycle: deprecated
              deprecated: true
            - type: 'null'
        endCrawlDate:
          anyOf:
            - type: string
              format: date-time
              description: >-
                Deprecated. Ignored by the API. Setting it adds an
                `IGNORED_FIELD` warning to the response's `warnings`.
              x-exa-lifecycle: deprecated
              deprecated: true
            - type: 'null'
        includeText:
          anyOf:
            - maxItems: 50
              type: array
              items:
                type: string
                maxLength: 4096
            - type: 'null'
          description: >-
            Deprecated. List of strings that must be present in the webpage text
            of results. Matching is approximate (word-level rather than exact
            phrase), so a multi-word entry can match pages where its words
            appear separately. Up to 50 strings, each up to 4096 characters.
          x-exa-lifecycle: deprecated
          deprecated: true
        excludeText:
          anyOf:
            - maxItems: 50
              type: array
              items:
                type: string
                maxLength: 4096
            - type: 'null'
          description: >-
            Deprecated. List of strings that must not be present in the webpage
            text of results. Matching is approximate (word-level rather than
            exact phrase). Up to 50 strings, each up to 4096 characters.
          x-exa-lifecycle: deprecated
          deprecated: true
        context:
          anyOf:
            - description: >-
                Deprecated. Use `highlights` or `text` instead. Returns page
                contents as a combined context string.
              x-exa-lifecycle: deprecated
              deprecated: true
              x-exa-replacement:
                - highlights
                - text
              oneOf:
                - type: boolean
                  description: >-
                    Deprecated. Use `highlights` or `text` instead. Returns page
                    contents as a combined context string.
                  x-exa-lifecycle: deprecated
                  deprecated: true
                  x-exa-replacement:
                    - highlights
                    - text
                - type: object
                  properties:
                    maxCharacters:
                      type: integer
                      minimum: 1
                      maximum: 1000000
                      description: Maximum character limit for the context string.
                  description: >-
                    Deprecated. Use `highlights` or `text` instead. Returns page
                    contents as a combined context string.
                  x-exa-lifecycle: deprecated
                  deprecated: true
                  x-exa-replacement:
                    - highlights
                    - text
            - type: 'null'
      required:
        - query
    SearchResponse:
      oneOf:
        - $ref: '#/components/schemas/SearchSynthesisResponse'
        - $ref: '#/components/schemas/SearchResultsResponse'
    SearchStreamChunk:
      oneOf:
        - $ref: '#/components/schemas/SearchStreamTextDeltaChunkOutput'
        - $ref: '#/components/schemas/SearchStreamGroundingChunkOutput'
        - $ref: '#/components/schemas/SearchStreamResultsChunkOutput'
        - $ref: '#/components/schemas/SearchStreamResetChunkOutput'
        - $ref: '#/components/schemas/SearchStreamDoneChunkOutput'
        - $ref: '#/components/schemas/SearchStreamErrorChunkOutput'
      description: >-
        Schema for each JSON payload emitted in a `/search` server-sent event
        stream. Each event is emitted as `data: <json>` and the stream
        terminates with `data: [DONE]`, which is not represented by this JSON
        schema.
      type: object
      discriminator:
        propertyName: type
        mapping:
          text-delta: '#/components/schemas/SearchStreamTextDeltaChunkOutput'
          grounding: '#/components/schemas/SearchStreamGroundingChunkOutput'
          results: '#/components/schemas/SearchStreamResultsChunkOutput'
          stream-reset: '#/components/schemas/SearchStreamResetChunkOutput'
          done: '#/components/schemas/SearchStreamDoneChunkOutput'
          error: '#/components/schemas/SearchStreamErrorChunkOutput'
    ErrorResponse:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        error:
          type: string
          description: Human-readable message describing the error.
        tag:
          type: string
          description: >-
            Machine-readable error tag identifying the failure. The set of tags
            is open-ended: new tags may be added at any time, so treat
            unrecognized tags as a generic error of the response's HTTP status.
            Known tags are listed as examples.
      required:
        - requestId
        - error
        - tag
      additionalProperties: false
      description: Standard error envelope returned by the Exa API for failed requests.
    X402PaymentChallenge:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        error:
          type: string
          description: Human-readable message describing the error.
        tag:
          type: string
          description: >-
            Machine-readable error tag identifying the failure. The set of tags
            is open-ended: new tags may be added at any time, so treat
            unrecognized tags as a generic error of the response's HTTP status.
            Known tags are listed as examples.
        x402Version:
          type: number
          description: Version of the x402 protocol used to build this challenge.
        resource:
          type: object
          properties:
            url:
              type: string
              description: URL of the priced resource being requested.
            description:
              type: string
              description: Human-readable resource description.
            mimeType:
              type: string
              description: MIME type of the priced resource.
          required:
            - url
            - description
            - mimeType
          additionalProperties: false
          description: The priced resource this challenge applies to.
        accepts:
          type: array
          items:
            type: object
            propertyNames:
              type: string
            additionalProperties: {}
            description: >-
              An accepted x402 payment requirement (scheme, network, amount,
              payTo, asset, maxTimeoutSeconds, and scheme-specific `extra`
              fields).
          description: Payment requirements the server accepts, one per supported rail.
        extensions:
          description: >-
            Optional x402 protocol extensions (e.g. Bazaar or AgentKit discovery
            metadata).
          type: object
          propertyNames:
            type: string
          additionalProperties: {}
      required:
        - requestId
        - error
        - tag
        - x402Version
        - resource
        - accepts
      additionalProperties: false
      description: >-
        x402 payment challenge: the standard error envelope extended with x402
        payment metadata.
    ContentsOptions:
      type: object
      properties:
        text:
          anyOf:
            - description: Text extraction options for each result.
              oneOf:
                - type: boolean
                  title: Simple text retrieval
                  description: >-
                    If true, returns full page text with default settings. If
                    false, disables text return.
                  default: false
                - type: object
                  properties:
                    maxCharacters:
                      anyOf:
                        - type: integer
                          minimum: 1
                          maximum: 1000000
                          description: >-
                            Maximum character limit for the full page text.
                            Useful for controlling response size and API costs.
                        - type: 'null'
                    includeHtmlTags:
                      anyOf:
                        - type: boolean
                          description: >-
                            If true, include lightweight HTML tags in returned
                            text instead of plain markdown-style text.
                          default: false
                        - type: 'null'
                    verbosity:
                      anyOf:
                        - type: string
                          enum:
                            - compact
                            - standard
                            - full
                          description: >-
                            Controls text rendering verbosity. compact focuses
                            on main content, standard includes more surrounding
                            page context, and full requests the most complete
                            rendered text. Some pages may produce identical
                            standard and full output.
                          default: compact
                        - type: 'null'
                    includeSections:
                      anyOf:
                        - type: array
                          items:
                            type: string
                            enum:
                              - header
                              - navigation
                              - banner
                              - body
                              - sidebar
                              - footer
                              - metadata
                          description: >-
                            Best-effort. Only include content classified into
                            these semantic page sections. Section classification
                            may be unavailable or incomplete for some pages;
                            validate output if strict filtering is required.
                        - type: 'null'
                    excludeSections:
                      anyOf:
                        - type: array
                          items:
                            type: string
                            enum:
                              - header
                              - navigation
                              - banner
                              - body
                              - sidebar
                              - footer
                              - metadata
                          description: >-
                            Exclude content classified into these semantic page
                            sections. Section classification is best-effort.
                        - type: 'null'
                  title: Advanced text options
                  description: >-
                    Advanced options for controlling text extraction. Use this
                    when you need to limit text length or include HTML
                    structure. Set `maxAgeHours: 0` to apply `includeHtmlTags`,
                    `verbosity`, and section filters to freshly fetched content.
            - type: 'null'
        highlights:
          anyOf:
            - description: >-
                Text snippets the LLM identifies as most relevant from each
                page.
              oneOf:
                - type: boolean
                  title: Simple highlights retrieval
                  description: >-
                    If true, returns highlights with default settings. If false,
                    disables highlights.
                  default: false
                - type: object
                  properties:
                    query:
                      anyOf:
                        - type: string
                          description: >-
                            Custom query that guides which highlights the LLM
                            picks.
                        - type: 'null'
                    verbosity:
                      anyOf:
                        - type: string
                          enum:
                            - low
                            - medium
                            - high
                          description: >-
                            Preset highlight length: `low`, `medium`, and `high`
                            allocate progressively larger token budgets for the
                            returned highlights. With highlights.dynamic, the
                            preset sets a single shared budget across the whole
                            result set instead of a per-URL budget. Exact
                            budgets are tuned by Exa and may change. Not
                            compatible with maxCharacters or numSentences. Beta:
                            requires the `Exa-Beta:
                            dynamic-highlights-2026-08-28` request header;
                            requests setting `verbosity` without it are
                            rejected.
                          x-exa-lifecycle: beta
                          x-exa-beta-flag: dynamic-highlights-2026-08-28
                          x-mint:
                            post:
                              - Beta
                        - type: 'null'
                    dynamic:
                      anyOf:
                        - type: boolean
                          description: >-
                            Enable Dynamic Highlights (research preview):
                            considers all results together and allocates a
                            single shared context budget across the result set
                            instead of a per-document budget. Not compatible
                            with maxCharacters. Beta: requires the `Exa-Beta:
                            dynamic-highlights-2026-08-28` request header;
                            requests setting `dynamic` without it are rejected.
                          x-exa-lifecycle: beta
                          x-exa-beta-flag: dynamic-highlights-2026-08-28
                          x-mint:
                            post:
                              - Beta
                        - type: 'null'
                    maxCharacters:
                      anyOf:
                        - type: integer
                          minimum: 1
                          maximum: 1000000
                          description: >-
                            Maximum number of characters to return for
                            highlights. Controls the total length of highlight
                            text returned per URL. Not compatible with
                            highlights.dynamic.
                        - type: 'null'
                    numSentences:
                      anyOf:
                        - type: integer
                          minimum: 1
                          description: >-
                            Deprecated. Use `maxCharacters` instead. Currently
                            mapped to a character budget of about 1333
                            characters per sentence. Pass highlights: true for
                            default highlights, or { query } to guide selection
                            with your own query.
                          x-exa-lifecycle: deprecated
                          deprecated: true
                          x-exa-replacement: maxCharacters
                        - type: 'null'
                    highlightsPerUrl:
                      anyOf:
                        - type: integer
                          minimum: 1
                          description: >-
                            Deprecated. Currently ignored. Pass highlights: true
                            for default highlights, or { query } to guide
                            selection with your own query.
                          x-exa-lifecycle: deprecated
                          deprecated: true
                        - type: 'null'
                  title: Advanced highlights options
                  description: >-
                    Advanced options for steering highlight extraction. Pass
                    highlights: true for the highest-quality default; supply
                    this object only when you need to guide selection with your
                    own query.
            - type: 'null'
        summary:
          anyOf:
            - type: object
              properties:
                query:
                  anyOf:
                    - type: string
                      description: Custom query for the LLM-generated summary.
                    - type: 'null'
                schema:
                  anyOf:
                    - type: object
                      propertyNames:
                        type: string
                      additionalProperties:
                        $ref: '#/components/schemas/JsonValue'
                      description: >-
                        JSON schema for structured output from summary. See
                        https://json-schema.org/overview/what-is-jsonschema for
                        JSON Schema documentation.
                    - type: 'null'
              description: Summary of the webpage.
            - type: 'null'
        extras:
          anyOf:
            - type: object
              properties:
                links:
                  anyOf:
                    - type: integer
                      minimum: 0
                      maximum: 1000
                      description: Number of URLs to return from each webpage.
                      default: 0
                    - type: 'null'
                imageLinks:
                  anyOf:
                    - type: integer
                      minimum: 0
                      maximum: 1000
                      description: Number of images to return for each result.
                      default: 0
                    - type: 'null'
                richImageLinks:
                  anyOf:
                    - type: integer
                      minimum: 0
                      maximum: 1000
                      description: Number of rich image links to return for each result.
                      default: 0
                    - type: 'null'
                richLinks:
                  anyOf:
                    - type: integer
                      minimum: 0
                      maximum: 1000
                      default: 0
                      description: >-
                        Deprecated. Number of rich links to return for each
                        result.
                      x-exa-lifecycle: deprecated
                      deprecated: true
                    - type: 'null'
                codeBlocks:
                  anyOf:
                    - type: integer
                      minimum: 0
                      maximum: 1000
                      default: 0
                      description: >-
                        Deprecated. Number of code blocks to return for each
                        result.
                      x-exa-lifecycle: deprecated
                      deprecated: true
                    - type: 'null'
              description: Extra parameters to pass.
            - type: 'null'
        livecrawlTimeout:
          anyOf:
            - type: integer
              exclusiveMinimum: 0
              maximum: 90000
              description: The timeout for livecrawling in milliseconds.
              default: 10000
            - type: 'null'
        maxAgeHours:
          anyOf:
            - type: integer
              minimum: -1
              maximum: 720
              description: >-
                Maximum age of cached content, in hours, up to 720. Cached
                content younger than this is used, and older pages are fetched
                fresh. `0` always fetches fresh content and `-1` always uses the
                cache. When omitted, cached content is used when available and
                pages without it are fetched live.
            - type: 'null'
        snapshotAsOf:
          anyOf:
            - description: >-
                Return the newest stored version of each page as of this
                instant. Accepts an ISO 8601 date-time (`2026-01-15T00:00:00Z`)
                or a date-only value (`2026-01-15`), which is interpreted as
                midnight UTC. Historical requests are served from stored
                versions only and never fetch the live page.
              oneOf:
                - type: string
                  description: ISO 8601 date-time.
                  format: date-time
                - type: string
                  description: ISO 8601 date (`YYYY-MM-DD`), interpreted as midnight UTC.
                  format: date
            - type: 'null'
        context:
          anyOf:
            - description: >-
                Deprecated. Use `highlights` or `text` instead. Returns page
                contents as a combined context string.
              x-exa-lifecycle: deprecated
              deprecated: true
              x-exa-replacement:
                - highlights
                - text
              oneOf:
                - type: boolean
                  description: >-
                    Deprecated. Use `highlights` or `text` instead. Returns page
                    contents as a combined context string.
                  x-exa-lifecycle: deprecated
                  deprecated: true
                  x-exa-replacement:
                    - highlights
                    - text
                - type: object
                  properties:
                    maxCharacters:
                      type: integer
                      minimum: 1
                      maximum: 1000000
                      description: Maximum character limit for the context string.
                  description: >-
                    Deprecated. Use `highlights` or `text` instead. Returns page
                    contents as a combined context string.
                  x-exa-lifecycle: deprecated
                  deprecated: true
                  x-exa-replacement:
                    - highlights
                    - text
            - type: 'null'
        livecrawl:
          anyOf:
            - type: string
              enum:
                - never
                - always
                - fallback
                - preferred
              description: >-
                Deprecated. Use `maxAgeHours` instead. Does not guarantee
                freshly fetched content. Cannot be combined with `maxAgeHours`.
              x-exa-lifecycle: deprecated
              deprecated: true
              x-exa-replacement: maxAgeHours
            - type: 'null'
        crawledBeforeDate:
          anyOf:
            - type: string
            - type: 'null'
          format: date-time
          description: >-
            Deprecated. Use `snapshotAsOf` instead. Alias of snapshotAsOf with
            identical behavior.
          x-exa-lifecycle: deprecated
          deprecated: true
          x-exa-replacement: snapshotAsOf
        subpages:
          anyOf:
            - type: integer
              minimum: 0
              maximum: 100
              default: 0
              description: >-
                Deprecated. The number of subpages to crawl for each result. The
                actual number crawled may be limited by system constraints. To
                crawl subpages, send the result URLs to `/contents` with
                `subpages`.
              x-exa-lifecycle: deprecated
              deprecated: true
            - type: 'null'
        subpageTarget:
          anyOf:
            - description: >-
                Deprecated. Term to find specific subpages of search results.
                Can be a single string or an array of strings. To target
                subpages, send the result URLs to `/contents` with
                `subpageTarget`.
              x-exa-lifecycle: deprecated
              deprecated: true
              oneOf:
                - type: string
                  minLength: 1
                  maxLength: 100
                - minItems: 0
                  maxItems: 100
                  type: array
                  items:
                    type: string
                    minLength: 1
                    maxLength: 100
            - type: 'null'
    OutputSchemaText:
      type: object
      properties:
        type:
          type: string
          const: text
        description:
          type: string
      required:
        - type
    OutputSchemaObject:
      type: object
      properties:
        type:
          type: string
          const: object
        description:
          type: string
        properties:
          type: object
          propertyNames:
            type: string
          additionalProperties:
            $ref: '#/components/schemas/JsonValue'
        required:
          type: array
          items:
            type: string
        additionalProperties:
          type: boolean
      required:
        - type
      additionalProperties:
        $ref: '#/components/schemas/JsonValue'
    SearchSynthesisResponse:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        results:
          type: array
          items:
            $ref: '#/components/schemas/SearchResultOutput'
          description: >-
            A list of search results containing title, URL, published date, and
            author.
        costDollars:
          $ref: '#/components/schemas/CostDollarsOutput'
        searchTime:
          type: number
          description: >-
            Server-side processing time in milliseconds. May exclude output
            synthesis time, so it can be lower than end-to-end latency.
        warnings:
          description: >-
            Warnings about the request, such as a field that has no effect. Log
            them; do not pass them to a model. Omitted when there are none.
          type: array
          items:
            $ref: '#/components/schemas/SearchWarningOutput'
        notices:
          description: >-
            Notices about how the results were produced. Pass them to your model
            with the results. Omitted when there are none.
          type: array
          items:
            $ref: '#/components/schemas/SearchNoticeOutput'
        output:
          $ref: '#/components/schemas/SearchSynthesisOutputOutput'
        resolvedSearchType:
          description: Deprecated. May be an empty string. Do not branch on this value.
          x-exa-lifecycle: deprecated
          deprecated: true
          type: string
        context:
          type: string
          description: >-
            Deprecated. Use `results[].highlights` or `results[].text` instead.
            Combined context string from search results.
          x-exa-lifecycle: deprecated
          deprecated: true
          x-exa-replacement:
            - results[].highlights
            - results[].text
      required:
        - results
        - output
      additionalProperties: false
    SearchResultsResponse:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        results:
          type: array
          items:
            $ref: '#/components/schemas/SearchResultOutput'
          description: >-
            A list of search results containing title, URL, published date, and
            author.
        costDollars:
          $ref: '#/components/schemas/CostDollarsOutput'
        searchTime:
          type: number
          description: >-
            Server-side processing time in milliseconds. May exclude output
            synthesis time, so it can be lower than end-to-end latency.
        warnings:
          description: >-
            Warnings about the request, such as a field that has no effect. Log
            them; do not pass them to a model. Omitted when there are none.
          type: array
          items:
            $ref: '#/components/schemas/SearchWarningOutput'
        notices:
          description: >-
            Notices about how the results were produced. Pass them to your model
            with the results. Omitted when there are none.
          type: array
          items:
            $ref: '#/components/schemas/SearchNoticeOutput'
        resolvedSearchType:
          description: Deprecated. May be an empty string. Do not branch on this value.
          x-exa-lifecycle: deprecated
          deprecated: true
          type: string
        context:
          type: string
          description: >-
            Deprecated. Use `results[].highlights` or `results[].text` instead.
            Combined context string from search results.
          x-exa-lifecycle: deprecated
          deprecated: true
          x-exa-replacement:
            - results[].highlights
            - results[].text
      required:
        - results
      additionalProperties: false
    SearchStreamTextDeltaChunkOutput:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        type:
          type: string
          const: text-delta
        delta:
          type: string
        choices:
          type: array
          items:
            type: object
            properties:
              index:
                type: integer
                minimum: 0
              delta:
                type: object
                properties:
                  role:
                    type: string
                    const: assistant
                  content:
                    type: string
                  citations:
                    type: array
                    items:
                      type: object
                      properties:
                        url:
                          type: string
                          format: uri
                          description: Source URL.
                        title:
                          type: string
                          description: Source title.
                        id:
                          type: string
                      required:
                        - url
                        - title
                        - id
                      additionalProperties: false
                additionalProperties: false
              finish_reason:
                oneOf:
                  - type: string
                    const: stop
                  - type: 'null'
            required:
              - index
              - delta
              - finish_reason
            additionalProperties: false
      required:
        - type
        - delta
      additionalProperties: false
    SearchStreamGroundingChunkOutput:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        type:
          type: string
          const: grounding
        grounding:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
                description: >-
                  Field path in output.content, for example content or
                  companies[0].funding.
              citations:
                type: array
                items:
                  type: object
                  properties:
                    url:
                      type: string
                      format: uri
                      description: Source URL.
                    title:
                      type: string
                      description: Source title.
                  required:
                    - url
                    - title
                  additionalProperties: false
                description: Sources supporting this output field.
              confidence:
                type: string
                enum:
                  - low
                  - medium
                  - high
                description: Model-reported reliability for this field.
            required:
              - field
              - citations
              - confidence
            additionalProperties: false
          description: Field-level grounding for synthesized output.
        citations:
          type: array
          items:
            type: object
            properties:
              url:
                type: string
                format: uri
                description: Source URL.
              title:
                type: string
                description: Source title.
              id:
                type: string
            required:
              - url
              - title
              - id
            additionalProperties: false
        choices:
          type: array
          items:
            type: object
            properties:
              index:
                type: integer
                minimum: 0
              delta:
                type: object
                properties:
                  role:
                    type: string
                    const: assistant
                  content:
                    type: string
                  citations:
                    type: array
                    items:
                      type: object
                      properties:
                        url:
                          type: string
                          format: uri
                          description: Source URL.
                        title:
                          type: string
                          description: Source title.
                        id:
                          type: string
                      required:
                        - url
                        - title
                        - id
                      additionalProperties: false
                additionalProperties: false
              finish_reason:
                oneOf:
                  - type: string
                    const: stop
                  - type: 'null'
            required:
              - index
              - delta
              - finish_reason
            additionalProperties: false
      required:
        - type
        - grounding
      additionalProperties: false
    SearchStreamResultsChunkOutput:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        type:
          type: string
          const: results
        results:
          type: array
          items:
            $ref: '#/components/schemas/SearchResultOutput'
        warnings:
          description: >-
            Warnings about the request, such as a field that has no effect. Log
            them; do not pass them to a model. Omitted when there are none.
          type: array
          items:
            $ref: '#/components/schemas/SearchWarningOutput'
        notices:
          description: >-
            Notices about how the results were produced. Pass them to your model
            with the results. Omitted when there are none.
          type: array
          items:
            $ref: '#/components/schemas/SearchNoticeOutput'
      required:
        - type
        - results
      additionalProperties: false
    SearchStreamResetChunkOutput:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        type:
          type: string
          const: stream-reset
        streamReset:
          type: boolean
          const: true
      required:
        - type
        - streamReset
      additionalProperties: false
    SearchStreamDoneChunkOutput:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        type:
          type: string
          const: done
        output:
          anyOf:
            - $ref: '#/components/schemas/SearchSynthesisOutputOutput'
            - type: 'null'
        searchTime:
          type: number
          description: >-
            Server-side processing time in milliseconds. May exclude output
            synthesis time, so it can be lower than end-to-end latency.
        costDollars:
          $ref: '#/components/schemas/CostDollarsOutput'
        choices:
          type: array
          items:
            type: object
            properties:
              index:
                type: integer
                minimum: 0
              delta:
                type: object
                properties:
                  role:
                    type: string
                    const: assistant
                  content:
                    type: string
                  citations:
                    type: array
                    items:
                      type: object
                      properties:
                        url:
                          type: string
                          format: uri
                          description: Source URL.
                        title:
                          type: string
                          description: Source title.
                        id:
                          type: string
                      required:
                        - url
                        - title
                        - id
                      additionalProperties: false
                additionalProperties: false
              finish_reason:
                oneOf:
                  - type: string
                    const: stop
                  - type: 'null'
            required:
              - index
              - delta
              - finish_reason
            additionalProperties: false
      required:
        - type
        - output
        - searchTime
      additionalProperties: false
    SearchStreamErrorChunkOutput:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        type:
          type: string
          const: error
        error:
          type: object
          properties:
            message:
              type: string
          required:
            - message
          additionalProperties: false
      required:
        - type
        - error
      additionalProperties: false
    JsonValue:
      description: Any JSON value.
      oneOf:
        - type: 'null'
        - type: boolean
        - type: number
        - type: string
        - type: array
          items:
            $ref: '#/components/schemas/JsonValue'
        - type: object
          propertyNames:
            type: string
          additionalProperties:
            $ref: '#/components/schemas/JsonValue'
    SearchResultOutput:
      type: object
      properties:
        title:
          type: string
          description: The title of the search result.
        url:
          type: string
          description: The URL of the search result.
          format: uri
        publishedDate:
          description: >-
            An estimate of the creation date, from parsing HTML content. Format
            is YYYY-MM-DD.
          format: date-time
          type: string
        author:
          description: If available, the author of the content.
          anyOf:
            - type: string
            - type: 'null'
        id:
          description: >-
            The temporary ID for the document. Useful for the /contents
            endpoint.
          type: string
        image:
          description: The URL of an image associated with the search result, if available.
          format: uri
          type: string
        favicon:
          description: The URL of the favicon for the search result's domain.
          format: uri
          type: string
        text:
          description: The full content text of the search result.
          type: string
        highlights:
          description: Array of highlights extracted from the search result content.
          type: array
          items:
            type: string
        highlightScores:
          description: Array of cosine similarity scores for each highlighted snippet.
          type: array
          items:
            type: number
            format: float
        summary:
          description: Summary of the webpage.
          type: string
        subpages:
          description: Array of subpages for the search result.
          type: array
          items:
            type: object
            properties:
              title:
                type: string
                description: The title of the search result.
              url:
                type: string
                description: The URL of the search result.
                format: uri
              publishedDate:
                description: >-
                  An estimate of the creation date, from parsing HTML content.
                  Format is YYYY-MM-DD.
                format: date-time
                type: string
              author:
                description: If available, the author of the content.
                anyOf:
                  - type: string
                  - type: 'null'
              id:
                description: >-
                  The temporary ID for the document. Useful for the /contents
                  endpoint.
                type: string
              image:
                description: >-
                  The URL of an image associated with the search result, if
                  available.
                format: uri
                type: string
              favicon:
                description: The URL of the favicon for the search result's domain.
                format: uri
                type: string
            required:
              - title
              - url
            additionalProperties: false
        entities:
          description: >-
            Structured entity data for company, person, publication, or product
            search results. Returned for supported entity-backed categories and
            for product listing pages.
          type: array
          items:
            oneOf:
              - $ref: '#/components/schemas/SearchCompanyEntityOutput'
              - $ref: '#/components/schemas/SearchPersonEntityOutput'
              - $ref: '#/components/schemas/SearchPublicationEntityOutput'
            type: object
            discriminator:
              propertyName: type
              mapping:
                company: '#/components/schemas/SearchCompanyEntityOutput'
                person: '#/components/schemas/SearchPersonEntityOutput'
                publication: '#/components/schemas/SearchPublicationEntityOutput'
        extras:
          description: >-
            Results from extras. Each field is returned only when requested via
            contents.extras.
          type: object
          properties:
            links:
              description: Array of links from the search result.
              type: array
              items:
                type: string
            imageLinks:
              description: Array of image URLs from the search result.
              type: array
              items:
                type: string
            richImageLinks:
              description: >-
                Array of images with their alt text, in the order the images
                appear on the page.
              type: array
              items:
                type: object
                properties:
                  url:
                    type: string
                    description: The URL of the image.
                  alt:
                    description: The alt text of the image, when the page provides one.
                    type: string
                required:
                  - url
                additionalProperties: false
            richLinks:
              description: >-
                Array of links with their anchor text, in the order they appear
                on the page.
              type: array
              items:
                type: object
                properties:
                  url:
                    type: string
                    description: The URL of the link.
                  anchor:
                    description: The anchor text of the link, when the page provides one.
                    type: string
                required:
                  - url
                additionalProperties: false
            codeBlocks:
              description: Array of code blocks from the search result.
              type: array
              items:
                type: object
                properties:
                  text:
                    type: string
                    description: The contents of the code block.
                  source:
                    type: string
                    description: The language the code block is annotated with, if any.
                required:
                  - text
                  - source
                additionalProperties: false
          additionalProperties: false
      required:
        - title
        - url
      additionalProperties: false
    CostDollarsOutput:
      type: object
      properties:
        total:
          description: >-
            Estimated total dollar cost for the completed request. This response
            value is not an invoice record.
          format: float
          type: number
        search:
          description: >-
            Estimated search cost by retrieval mode. Some search types report
            their cost only in `total`.
          type: object
          properties:
            neural:
              description: Cost of neural search operations.
              format: float
              type: number
            keyword:
              description: Cost of keyword search operations.
              format: float
              type: number
          additionalProperties: false
        summary:
          description: Cost of synthesized summary generation for search requests.
          format: float
          type: number
        contents:
          description: >-
            Estimated cost breakdown for standalone content retrieval (text,
            highlights, and summaries billed outside the bundled search price).
          type: object
          properties:
            text:
              description: Cost of text extraction.
              format: float
              type: number
            highlights:
              description: Cost of highlight extraction.
              format: float
              type: number
            summary:
              description: Cost of per-result summary generation.
              format: float
              type: number
          additionalProperties: false
      additionalProperties: false
      description: >-
        Estimated dollar cost of the request. Which fields appear depends on the
        endpoint.
    SearchWarningOutput:
      type: object
      properties:
        code:
          type: string
          description: >-
            Machine-readable warning code, UPPER_SNAKE. `IGNORED_FIELD`: the
            field at `path` is accepted and has no effect. Codes are an open
            set: tolerate codes you do not recognize.
          example: IGNORED_FIELD
        path:
          type: string
          description: JSON Pointer to the request field the warning is about.
          example: /startCrawlDate
        message:
          type: string
          description: >-
            Human-readable and complete on its own: what to change in the
            request.
      required:
        - code
        - path
        - message
      additionalProperties: false
      description: >-
        A note about the request itself, for whoever maintains the code that
        builds it. Log it; do not pass it to a model. A warning never changes
        the status code or the results.
    SearchNoticeOutput:
      type: object
      properties:
        code:
          type: string
          description: >-
            Machine-readable notice code, UPPER_SNAKE. `RESTRICTIONS_RELAXED`:
            the `site:` or exact-phrase restrictions written in the query
            matched nothing, so the results come from a search with them
            removed; filters set in the request body were kept. Codes are an
            open set: tolerate codes you do not recognize.
          example: RESTRICTIONS_RELAXED
        path:
          type: string
          description: JSON Pointer to the request field the notice is about.
          example: /query
        message:
          type: string
          description: >-
            Human-readable and complete on its own; written to be shown to a
            model.
        details:
          description: >-
            Optional extra context for a harness or model. An open object: no
            schema is promised for its keys, and it never carries information
            that `message` lacks.
          type: object
          propertyNames:
            type: string
          additionalProperties: {}
      required:
        - code
        - path
        - message
      additionalProperties: false
      description: >-
        A note about how the results were produced, written to be passed to a
        model with the results.
    SearchSynthesisOutputOutput:
      type: object
      properties:
        content:
          description: >-
            Synthesized content. String by default, or object when outputSchema
            is provided.
          oneOf:
            - type: string
            - type: object
              propertyNames:
                type: string
              additionalProperties:
                $ref: '#/components/schemas/JsonValue'
        grounding:
          type: array
          items:
            type: object
            properties:
              field:
                type: string
                description: >-
                  Field path in output.content, for example content or
                  companies[0].funding.
              citations:
                type: array
                items:
                  type: object
                  properties:
                    url:
                      type: string
                      format: uri
                      description: Source URL.
                    title:
                      type: string
                      description: Source title.
                  required:
                    - url
                    - title
                  additionalProperties: false
                description: Sources supporting this output field.
              confidence:
                type: string
                enum:
                  - low
                  - medium
                  - high
                description: Model-reported reliability for this field.
            required:
              - field
              - citations
              - confidence
            additionalProperties: false
          description: Field-level grounding for synthesized output.
      required:
        - content
        - grounding
      additionalProperties: false
      description: Synthesized output. Returned when outputSchema is provided.
    SearchCompanyEntityOutput:
      type: object
      properties:
        id:
          type: string
          description: Stable company entity identifier.
        type:
          type: string
          const: company
          description: Entity discriminator.
        version:
          type: integer
          minimum: 1
          description: Entity schema version.
        properties:
          type: object
          properties:
            name:
              anyOf:
                - type: string
                - type: 'null'
              description: Company name.
            foundedYear:
              anyOf:
                - type: integer
                - type: 'null'
              description: Year the company was founded.
            description:
              anyOf:
                - type: string
                - type: 'null'
              description: Short company description.
            workforce:
              anyOf:
                - type: object
                  properties:
                    total:
                      anyOf:
                        - type: number
                        - type: 'null'
                      description: Total estimated employee count.
                  required:
                    - total
                  additionalProperties: false
                - type: 'null'
              description: Company workforce information.
            headquarters:
              anyOf:
                - type: object
                  properties:
                    address:
                      anyOf:
                        - type: string
                        - type: 'null'
                      description: Company headquarters street address.
                    city:
                      anyOf:
                        - type: string
                        - type: 'null'
                      description: Company headquarters city.
                    postalCode:
                      anyOf:
                        - type: string
                        - type: 'null'
                      description: Company headquarters postal code.
                    country:
                      anyOf:
                        - type: string
                        - type: 'null'
                      description: Company headquarters country.
                  required:
                    - address
                    - city
                    - postalCode
                    - country
                  additionalProperties: false
                - type: 'null'
              description: Company headquarters information.
            financials:
              anyOf:
                - type: object
                  properties:
                    revenueAnnual:
                      anyOf:
                        - type: number
                        - type: 'null'
                      description: Estimated annual revenue in USD.
                    fundingTotal:
                      anyOf:
                        - type: number
                        - type: 'null'
                      description: Total funding raised in USD.
                    fundingLatestRound:
                      anyOf:
                        - type: object
                          properties:
                            name:
                              anyOf:
                                - type: string
                                - type: 'null'
                              description: Funding round name.
                            date:
                              anyOf:
                                - type: string
                                - type: 'null'
                              description: Funding round date.
                            amount:
                              anyOf:
                                - type: number
                                - type: 'null'
                              description: Funding round amount in USD.
                          required:
                            - name
                            - date
                            - amount
                          additionalProperties: false
                        - type: 'null'
                      description: Most recent funding round, when available.
                  required:
                    - revenueAnnual
                    - fundingTotal
                    - fundingLatestRound
                  additionalProperties: false
                - type: 'null'
              description: Company financial information.
            webTraffic:
              anyOf:
                - type: object
                  properties:
                    visitsMonthly:
                      anyOf:
                        - type: number
                        - type: 'null'
                      description: Estimated monthly website visits.
                    countryRank:
                      anyOf:
                        - type: integer
                        - type: 'null'
                      description: >-
                        Estimated website traffic rank within the company's
                        primary country.
                    avgDurationSeconds:
                      anyOf:
                        - type: number
                        - type: 'null'
                      description: Estimated average visit duration, in seconds.
                    history:
                      type: array
                      items:
                        type: object
                        properties:
                          value:
                            type: number
                            description: Estimated monthly visits for this period.
                          dateFrom:
                            type: string
                            description: Start month for this value, formatted as YYYY-MM.
                          dateTo:
                            type: string
                            description: End month for this value, formatted as YYYY-MM.
                        required:
                          - value
                          - dateFrom
                          - dateTo
                        additionalProperties: false
                      description: Historical monthly website visits.
                  required:
                    - visitsMonthly
                    - countryRank
                    - avgDurationSeconds
                    - history
                  additionalProperties: false
                - type: 'null'
              description: Company web traffic information.
            research:
              anyOf:
                - type: object
                  properties:
                    worksCount:
                      anyOf:
                        - type: integer
                        - type: 'null'
                      description: Number of works with an affiliated author.
                    citationCount:
                      anyOf:
                        - type: integer
                        - type: 'null'
                      description: Lifetime citation count.
                    areas:
                      type: array
                      items:
                        type: string
                      description: Ranked research areas, most active first.
                    notableWorks:
                      type: array
                      items:
                        type: object
                        properties:
                          title:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Publication title.
                          year:
                            anyOf:
                              - type: integer
                              - type: 'null'
                            description: Publication year.
                          venue:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Publication venue.
                          citationCount:
                            anyOf:
                              - type: integer
                              - type: 'null'
                            description: Number of works citing this publication.
                          doi:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Digital Object Identifier.
                          id:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: >-
                              Resolved publication entity identifier, when
                              available.
                          type:
                            anyOf:
                              - type: string
                                enum:
                                  - article
                                  - book
                                  - book-chapter
                                  - dataset
                                  - dissertation
                                  - preprint
                                  - report
                                  - review
                              - type: 'null'
                            description: Publication type.
                        required:
                          - title
                          - year
                          - venue
                          - citationCount
                          - doi
                          - id
                          - type
                        additionalProperties: false
                      description: Most-cited notable works.
                    topResearchers:
                      type: array
                      items:
                        type: object
                        properties:
                          person:
                            anyOf:
                              - type: object
                                properties:
                                  name:
                                    anyOf:
                                      - type: string
                                      - type: 'null'
                                    description: Referenced person name.
                                  id:
                                    anyOf:
                                      - type: string
                                      - type: 'null'
                                    description: Referenced person entity identifier.
                                required:
                                  - name
                                  - id
                                additionalProperties: false
                              - type: 'null'
                            description: Referenced researcher.
                          worksCount:
                            anyOf:
                              - type: integer
                              - type: 'null'
                            description: Number of works produced at the organization.
                          citationCount:
                            anyOf:
                              - type: integer
                              - type: 'null'
                            description: >-
                              Number of citations for works produced at the
                              organization.
                        required:
                          - person
                          - worksCount
                          - citationCount
                        additionalProperties: false
                      description: >-
                        Researchers ordered by works produced at the
                        organization.
                  required:
                    - worksCount
                    - citationCount
                    - areas
                    - notableWorks
                    - topResearchers
                  additionalProperties: false
                - type: 'null'
              description: Company research information.
          required:
            - name
            - foundedYear
            - description
            - workforce
            - headquarters
            - financials
            - webTraffic
            - research
          additionalProperties: false
          description: Company-specific entity fields.
      required:
        - id
        - type
        - version
        - properties
      additionalProperties: false
    SearchPersonEntityOutput:
      type: object
      properties:
        id:
          type: string
          description: Stable person entity identifier.
        type:
          type: string
          const: person
          description: Entity discriminator.
        version:
          type: integer
          minimum: 1
          description: Entity schema version.
        properties:
          type: object
          properties:
            name:
              anyOf:
                - type: string
                - type: 'null'
              description: Person name.
            firstName:
              anyOf:
                - type: string
                - type: 'null'
              description: Person first name.
            lastName:
              anyOf:
                - type: string
                - type: 'null'
              description: Person last name.
            location:
              anyOf:
                - type: string
                - type: 'null'
              description: Person location.
            workHistory:
              type: array
              items:
                type: object
                properties:
                  title:
                    anyOf:
                      - type: string
                      - type: 'null'
                    description: Role title.
                  location:
                    anyOf:
                      - type: string
                      - type: 'null'
                    description: Role location.
                  dates:
                    anyOf:
                      - type: object
                        properties:
                          from:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Start date for the date range.
                          to:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: End date for the date range.
                        required:
                          - from
                          - to
                        additionalProperties: false
                      - type: 'null'
                    description: Role date range.
                  company:
                    anyOf:
                      - type: object
                        properties:
                          id:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Referenced company identifier.
                          name:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Referenced company name.
                        required:
                          - id
                          - name
                        additionalProperties: false
                      - type: 'null'
                    description: Company for this role.
                required:
                  - title
                  - location
                  - dates
                  - company
                additionalProperties: false
              description: Known professional roles for this person.
            educationHistory:
              type: array
              items:
                type: object
                properties:
                  degree:
                    anyOf:
                      - type: string
                      - type: 'null'
                    description: Degree or credential.
                  dates:
                    anyOf:
                      - type: object
                        properties:
                          from:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Start date for the date range.
                          to:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: End date for the date range.
                        required:
                          - from
                          - to
                        additionalProperties: false
                      - type: 'null'
                    description: Education date range.
                  institution:
                    anyOf:
                      - type: object
                        properties:
                          id:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Referenced institution identifier.
                          name:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Referenced institution name.
                        required:
                          - id
                          - name
                        additionalProperties: false
                      - type: 'null'
                    description: Education institution.
                required:
                  - degree
                  - dates
                  - institution
                additionalProperties: false
              description: Known education history for this person.
            research:
              anyOf:
                - type: object
                  properties:
                    worksCount:
                      anyOf:
                        - type: integer
                        - type: 'null'
                      description: Lifetime number of works.
                    citationCount:
                      anyOf:
                        - type: integer
                        - type: 'null'
                      description: Lifetime citation count.
                    hIndex:
                      anyOf:
                        - type: integer
                        - type: 'null'
                      description: Research h-index.
                    firstPublicationYear:
                      anyOf:
                        - type: integer
                        - type: 'null'
                      description: Year of the first publication.
                    latestPublicationYear:
                      anyOf:
                        - type: integer
                        - type: 'null'
                      description: Year of the latest publication.
                    areas:
                      type: array
                      items:
                        type: string
                      description: Ranked research areas, most active first.
                    notableWorks:
                      type: array
                      items:
                        type: object
                        properties:
                          title:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Publication title.
                          year:
                            anyOf:
                              - type: integer
                              - type: 'null'
                            description: Publication year.
                          venue:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Publication venue.
                          citationCount:
                            anyOf:
                              - type: integer
                              - type: 'null'
                            description: Number of works citing this publication.
                          doi:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: Digital Object Identifier.
                          id:
                            anyOf:
                              - type: string
                              - type: 'null'
                            description: >-
                              Resolved publication entity identifier, when
                              available.
                          type:
                            anyOf:
                              - type: string
                                enum:
                                  - article
                                  - book
                                  - book-chapter
                                  - dataset
                                  - dissertation
                                  - preprint
                                  - report
                                  - review
                              - type: 'null'
                            description: Publication type.
                        required:
                          - title
                          - year
                          - venue
                          - citationCount
                          - doi
                          - id
                          - type
                        additionalProperties: false
                      description: Most-cited notable works.
                  required:
                    - worksCount
                    - citationCount
                    - hIndex
                    - firstPublicationYear
                    - latestPublicationYear
                    - areas
                    - notableWorks
                  additionalProperties: false
                - type: 'null'
              description: Person research information.
          required:
            - name
            - firstName
            - lastName
            - location
            - workHistory
            - educationHistory
            - research
          additionalProperties: false
          description: Person-specific entity fields.
      required:
        - id
        - type
        - version
        - properties
      additionalProperties: false
    SearchPublicationEntityOutput:
      type: object
      properties:
        id:
          type: string
          description: Stable publication entity identifier.
        type:
          type: string
          const: publication
          description: Entity discriminator.
        version:
          type: integer
          minimum: 1
          description: Entity schema version.
        properties:
          type: object
          properties:
            title:
              anyOf:
                - type: string
                - type: 'null'
              description: Publication title.
            year:
              anyOf:
                - type: integer
                - type: 'null'
              description: Publication year.
            date:
              anyOf:
                - type: string
                - type: 'null'
              description: Publication date.
            type:
              anyOf:
                - type: string
                  enum:
                    - article
                    - book
                    - book-chapter
                    - dataset
                    - dissertation
                    - preprint
                    - report
                    - review
                - type: 'null'
              description: Publication type.
            language:
              anyOf:
                - type: string
                - type: 'null'
              description: Publication language.
            citationCount:
              anyOf:
                - type: integer
                - type: 'null'
              description: Number of works citing this publication (incoming references).
            authors:
              type: array
              items:
                type: object
                properties:
                  name:
                    anyOf:
                      - type: string
                      - type: 'null'
                    description: Author display name.
                  id:
                    anyOf:
                      - type: string
                      - type: 'null'
                    description: Resolved person entity identifier, when available.
                required:
                  - name
                  - id
                additionalProperties: false
              description: Ordered list of authors.
            referenceCount:
              anyOf:
                - type: integer
                - type: 'null'
              description: Number of works this publication cites (outgoing references).
            abstract:
              anyOf:
                - type: string
                - type: 'null'
              description: Publication abstract text.
            doi:
              anyOf:
                - type: string
                - type: 'null'
              description: Bare DOI identifier (e.g. 10.1234/abcd).
          required:
            - title
            - year
            - date
            - type
            - language
            - citationCount
            - authors
            - referenceCount
            - abstract
            - doi
          additionalProperties: false
          description: Publication-specific entity fields.
      required:
        - id
        - type
        - version
        - properties
      additionalProperties: false
  headers:
    XRequestId:
      description: >-
        Unique identifier for the request. Matches the `requestId` field
        returned in response bodies that carry one.
      schema:
        type: string
    XExaQueued:
      description: >-
        Whether the request waited in the customer rate-limit queue before being
        admitted.
      schema:
        type: string
        enum:
          - 'true'
          - 'false'
    XExaQueueMs:
      description: Total milliseconds the request waited in the customer rate-limit queue.
      schema:
        type: string
  responses:
    BadRequestResponse:
      description: The request body or query parameters failed validation.
      headers:
        x-request-id:
          $ref: '#/components/headers/XRequestId'
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    UnauthorizedResponse:
      description: The API key is missing or invalid.
      headers:
        x-request-id:
          $ref: '#/components/headers/XRequestId'
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    ForbiddenResponse:
      description: >-
        The team is not permitted to use this endpoint (`TEAM_BLOCKED`), or the
        feature is not enabled for it (`FEATURE_DISABLED`).
      headers:
        x-request-id:
          $ref: '#/components/headers/XRequestId'
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    TooManyRequestsResponse:
      description: A rate limit for this API key, team, or network was exceeded.
      headers:
        x-request-id:
          $ref: '#/components/headers/XRequestId'
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    InternalServerErrorResponse:
      description: An unexpected error occurred while processing the request.
      headers:
        x-request-id:
          $ref: '#/components/headers/XRequestId'
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    ServiceUnavailableResponse:
      description: >-
        Exa is temporarily over capacity or unavailable. The request was not
        processed; retry with exponential backoff.
      headers:
        x-request-id:
          $ref: '#/components/headers/XRequestId'
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
  securitySchemes:
    apiKey:
      type: apiKey
      name: x-api-key
      in: header
      description: >-
        Pass your Exa API key in the x-api-key header. You can also authenticate
        with Authorization: Bearer <key>.
    bearer:
      type: http
      scheme: bearer
      description: >-
        Pass your Exa API key in the x-api-key header. You can also authenticate
        with Authorization: Bearer <key>.

````