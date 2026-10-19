> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Answer

> Get an LLM answer to a question informed by Exa search results. `/answer` performs an Exa search and uses an LLM to generate either:
1. A direct answer for specific queries. (i.e. "What is the capital of France?" would return "Paris")
2. A detailed summary with citations for open-ended queries (i.e. "What is the state of ai in healthcare?" would return a summary with citations to relevant sources)

The response includes both the generated answer and the sources used to create it. The endpoint also supports streaming (as `stream: true`), which will return tokens as they are generated.

Alternatively, you can use the OpenAI compatible [chat completions interface](https://exa.ai/docs/integrations/openai-sdk#answer).


<Card title="Get your Exa API key" icon="key" horizontal href="https://dashboard.exa.ai/api-keys">
  Create a key in the dashboard. New accounts start with free credits.
</Card>

<Info>
  `/answer` supports structured output via the `outputSchema` parameter. Pass a [JSON Schema](https://json-schema.org/draft-07) object and the answer will be returned as structured JSON matching your schema instead of a plain string.
</Info>


## OpenAPI

````yaml exa-spec.yaml POST /answer
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
  /answer:
    post:
      summary: Answer
      description: >-
        Performs a search based on the query and generates either a direct
        answer or a detailed summary with citations, depending on the query
        type.
      operationId: answer
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/AnswerRequest'
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
                $ref: '#/components/schemas/AnswerResponse'
            text/event-stream:
              schema:
                $ref: '#/components/schemas/AnswerStreamChunk'
        '400':
          $ref: '#/components/responses/BadRequestResponse'
        '401':
          $ref: '#/components/responses/UnauthorizedResponse'
        '402':
          $ref: '#/components/responses/PaymentRequiredResponse'
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
            curl -X POST https://api.exa.ai/answer \
              -H "x-api-key: $EXA_API_KEY" \
              -H "Content-Type: application/json" \
              -d '{"query":"<query>"}'
        - lang: javascript
          source: |-
            import Exa from "exa-js";

            const exa = new Exa(process.env.EXA_API_KEY);

            const result = await exa.answer("<query>");
        - lang: python
          source: |-
            from exa_py import Exa

            exa = Exa(api_key="YOUR_API_KEY")

            result = exa.answer("<query>")
components:
  schemas:
    AnswerRequest:
      type: object
      properties:
        query:
          type: string
          minLength: 1
          description: Natural-language question or instructions for the request.
        stream:
          type: boolean
          description: >-
            If true, the response is returned as a server-sent events (SSE)
            stream.
          default: false
        text:
          type: boolean
          title: Simple text retrieval
          description: >-
            If true, returns full page text with default settings. If false,
            disables text return.
          default: false
        model:
          description: The model used to generate the answer.
          default: exa
          type: string
          enum:
            - exa
            - exa-pro
            - exa-research
            - exa-fast
        systemPrompt:
          type: string
          description: >-
            Additional instructions that guide generated output or agent
            behavior. Use this for source preferences, novelty constraints,
            duplication constraints, or other behavior guidance.
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
        outputSchema:
          type: object
          properties:
            type:
              type: string
              description: The root schema type (typically "object").
            properties:
              type: object
              propertyNames:
                type: string
              additionalProperties:
                $ref: '#/components/schemas/JsonValue'
              description: >-
                An object where each key is a property name and each value is a
                JSON Schema describing that property (with `type`,
                `description`, etc).
            required:
              type: array
              items:
                type: string
              description: List of required property names.
            description:
              type: string
              description: A description of the schema.
            additionalProperties:
              type: boolean
              description: Whether to allow properties not listed in `properties`.
              default: false
          additionalProperties:
            $ref: '#/components/schemas/JsonValue'
          description: >-
            A [JSON Schema Draft 7](https://json-schema.org/draft-07)
            specification for the desired answer structure. When provided, the
            answer is returned as a structured object matching the schema
            instead of a plain string.
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
      required:
        - query
    AnswerResponse:
      type: object
      properties:
        requestId:
          type: string
          description: Unique identifier for the request.
        answer:
          description: >-
            The generated answer based on search results. Returns a string by
            default, or a structured object matching the provided outputSchema.
          oneOf:
            - type: string
            - type: object
              propertyNames:
                type: string
              additionalProperties:
                $ref: '#/components/schemas/JsonValue'
        citations:
          description: Search results used to generate the answer.
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
              text:
                description: >-
                  The full text content of each source. Only present when text
                  contents are requested.
                type: string
            required:
              - title
              - url
            additionalProperties: false
        costDollars:
          $ref: '#/components/schemas/CostDollarsOutput'
      required:
        - answer
      additionalProperties: false
    AnswerStreamChunk:
      description: >-
        Schema for each JSON payload emitted in an `/answer` server-sent event
        stream. Each event is emitted as `data: <json>`.
      oneOf:
        - $ref: '#/components/schemas/AnswerStreamTextDeltaChunk'
        - $ref: '#/components/schemas/AnswerStreamCitationsChunkOutput'
        - $ref: '#/components/schemas/AnswerStreamCostChunkOutput'
        - $ref: '#/components/schemas/AnswerStreamErrorChunkOutput'
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
    AnswerStreamTextDeltaChunk:
      type: object
      properties:
        choices:
          type: array
          items:
            type: object
            properties:
              index:
                type: integer
                minimum: 0
                description: Index of this streamed choice.
              delta:
                type: object
                properties:
                  role:
                    type: string
                    const: assistant
                  content:
                    type: string
                  refusal:
                    anyOf:
                      - type: string
                      - type: 'null'
                additionalProperties:
                  $ref: '#/components/schemas/JsonValue'
                description: Incremental answer content emitted by the model.
              finish_reason:
                description: Reason this streamed choice finished, when present.
                oneOf:
                  - type: string
                  - type: 'null'
            required:
              - index
              - delta
            additionalProperties:
              $ref: '#/components/schemas/JsonValue'
          description: Streamed completion choices in the OpenAI chat completions format.
      required:
        - choices
      additionalProperties:
        $ref: '#/components/schemas/JsonValue'
    AnswerStreamCitationsChunkOutput:
      type: object
      properties:
        citations:
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
              text:
                description: >-
                  The full text content of each source. Only present when text
                  contents are requested.
                type: string
            required:
              - title
              - url
            additionalProperties: false
          description: Search results cited by the final streamed answer.
      required:
        - citations
      additionalProperties: false
    AnswerStreamCostChunkOutput:
      type: object
      properties:
        costDollars:
          $ref: '#/components/schemas/CostDollarsOutput'
        requestId:
          type: string
          description: Unique identifier for the request.
      required:
        - costDollars
      additionalProperties: false
    AnswerStreamErrorChunkOutput:
      type: object
      properties:
        tag:
          type: string
          const: ERROR
        payload:
          type: object
          properties:
            error:
              type: object
              properties:
                code:
                  type: integer
                message:
                  type: string
              required:
                - code
                - message
              additionalProperties: false
            requestId:
              type: string
              description: Unique identifier for the request.
          required:
            - error
          additionalProperties: false
      required:
        - tag
        - payload
      additionalProperties: false
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
    PaymentRequiredResponse:
      description: The team is out of credits or a spending budget has been exceeded.
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