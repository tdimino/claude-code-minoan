> ## Documentation Index
> Fetch the complete documentation index at: https://exa.ai/docs/llms.txt
> Use this file to discover all available pages before exploring further.

> ## Agent Instructions
> The Exa API is served at https://api.exa.ai. Authenticate with `Authorization: Bearer $EXA_API_KEY` (or `x-api-key: $EXA_API_KEY`); create keys at https://dashboard.exa.ai/api-keys.
> Prefer the official SDKs, `exa-py` (`pip install exa-py`) and `exa-js` (`npm install exa-js`); both read `EXA_API_KEY` from the environment.
> Tool-using agents can call Exa without writing code through the hosted MCP server at https://mcp.exa.ai/mcp, or install the Exa agent skill with `npx skills add exa-labs/agent-skills` (skill file: https://exa.ai/docs/skill.md).
> The OpenAPI specs at https://exa.ai/docs/exa-spec.yaml and https://exa.ai/docs/team-management-spec.yaml are the source of truth for request and response schemas.

# Create a run

> Create an asynchronous Agent run. The response returns the run object immediately unless you request server-sent events.

Create a run with a natural-language `query`. Add `outputSchema` for validated structured JSON, `input.data` for rows to process, `input.exclusion` for records or entities to avoid, or `previousRunId` to continue from a completed run.

Set `Accept: text/event-stream` to stream run events as the run is created, started, and completed.

<Note>
  **Connect:** Pass `dataSources` to give the agent access to third-party data providers during the run. See the [Connect guide](/docs/agent/quickstart#connect-data-sources) for details.
</Note>

<Card title="Get your Exa API key" icon="key" horizontal href="https://dashboard.exa.ai/api-keys">
  Create a key in the dashboard. New accounts start with free credits.
</Card>


## OpenAPI

````yaml exa-spec.yaml POST /agent/runs
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
  /agent/runs:
    post:
      tags:
        - Agent
      summary: Create a run
      description: >-
        Create an asynchronous Agent run. By default, the API returns the run
        object immediately. Set `Accept: text/event-stream` to stream run
        lifecycle events until the run reaches a terminal status.
      operationId: createAgentRun
      parameters:
        - $ref: '#/components/parameters/AcceptHeader'
        - $ref: '#/components/parameters/ExaBetaHeader'
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateAgentRunRequest'
      responses:
        '200':
          description: Agent run created
          headers:
            x-request-id:
              $ref: '#/components/headers/XRequestId'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentRun'
            text/event-stream:
              schema:
                $ref: '#/components/schemas/AgentRunEvent'
        '400':
          description: Invalid request.
          headers:
            x-request-id:
              $ref: '#/components/headers/XRequestId'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentErrorResponse'
        '401':
          description: Team context or authentication was not found.
          headers:
            x-request-id:
              $ref: '#/components/headers/XRequestId'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentErrorResponse'
        '403':
          $ref: '#/components/responses/ForbiddenResponse'
        '429':
          description: Agent run concurrency limit reached.
          headers:
            x-request-id:
              $ref: '#/components/headers/XRequestId'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentErrorResponse'
        '500':
          description: Server error or run timeout.
          headers:
            x-request-id:
              $ref: '#/components/headers/XRequestId'
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentErrorResponse'
      x-codeSamples:
        - lang: bash
          source: |-
            curl -X POST https://api.exa.ai/agent/runs \
              -H "x-api-key: $EXA_API_KEY" \
              -H "Content-Type: application/json" \
              -d '{ ... }'
        - lang: javascript
          source: |-
            import Exa from "exa-js";

            const exa = new Exa(process.env.EXA_API_KEY);

            const result = await exa.agent.runs.create({ ... });
        - lang: python
          source: |-
            from exa_py import Exa

            exa = Exa(api_key="YOUR_API_KEY")

            result = exa.agent.runs.create(...)
components:
  parameters:
    AcceptHeader:
      in: header
      name: Accept
      schema:
        description: Set to `text/event-stream` to receive server-sent events.
        type: string
        enum:
          - application/json
          - text/event-stream
      description: Set to `text/event-stream` to receive server-sent events.
    ExaBetaHeader:
      in: header
      name: Exa-Beta
      schema:
        description: >-
          Comma-separated beta feature tokens for opting into experimental
          features.
        type: string
      description: >-
        Comma-separated beta feature tokens for opting into experimental
        features.
  schemas:
    CreateAgentRunRequest:
      type: object
      properties:
        query:
          type: string
          minLength: 1
          description: Natural-language question or instructions for the request.
        systemPrompt:
          type: string
          description: >-
            Additional instructions that guide generated output or agent
            behavior. Use this for source preferences, novelty constraints,
            duplication constraints, or other behavior guidance.
        effort:
          $ref: '#/components/schemas/AgentEffort'
        input:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                propertyNames:
                  type: string
                additionalProperties:
                  $ref: '#/components/schemas/JsonValue'
                description: A JSON object record.
              description: Records the agent should process or enrich.
            exclusion:
              type: array
              items:
                type: object
                propertyNames:
                  type: string
                additionalProperties:
                  $ref: '#/components/schemas/JsonValue'
                description: A JSON object record.
              description: Records or entities the agent should avoid returning.
          description: >-
            Records to process and records or entities to exclude from the
            answer.
        outputSchema:
          anyOf:
            - type: object
              propertyNames:
                type: string
              additionalProperties:
                $ref: '#/components/schemas/JsonValue'
              description: >-
                JSON Schema for validated structured output in
                `output.structured`. Fields unsupported by evidence may be
                returned as `null`. Supports draft-07, 2019-09, and 2020-12 via
                `$schema`.
            - type: 'null'
        previousRunId:
          $ref: '#/components/schemas/AgentRunId'
          description: Completed run ID to continue from. Must belong to the same team.
        metadata:
          type: object
          propertyNames:
            type: string
          additionalProperties:
            type: string
          description: Caller-provided metadata stored with the run.
        dataSources:
          maxItems: 5
          type: array
          items:
            $ref: '#/components/schemas/AgentDataSource'
          description: >-
            Exa Connect data providers to enable for the run. Each entry enables
            all of that provider's tools.
        budget:
          $ref: '#/components/schemas/AgentBudget'
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
    AgentRun:
      type: object
      properties:
        id:
          $ref: '#/components/schemas/AgentRunId'
        object:
          type: string
          const: agent_run
        status:
          $ref: '#/components/schemas/AgentRunStatus'
        stopReason:
          anyOf:
            - $ref: '#/components/schemas/AgentStopReason'
            - type: 'null'
          description: Why the run stopped. `null` while the run is queued or running.
        createdAt:
          type: string
          format: date-time
          description: When the run was created
        completedAt:
          anyOf:
            - type: string
              format: date-time
            - type: 'null'
          format: date-time
        request:
          anyOf:
            - $ref: '#/components/schemas/AgentRunRequest'
            - type: 'null'
        output:
          $ref: '#/components/schemas/AgentRunOutput'
        usage:
          $ref: '#/components/schemas/AgentUsage'
        costDollars:
          $ref: '#/components/schemas/AgentCostDollars'
      required:
        - id
        - object
        - status
        - stopReason
        - createdAt
        - completedAt
        - request
        - output
        - usage
        - costDollars
      additionalProperties: false
    AgentRunEvent:
      type: object
      properties:
        id:
          type: string
          description: Event ID within the run.
        event:
          type: string
          enum:
            - agent_run.created
            - agent_run.started
            - agent_run.completed
            - agent_run.failed
            - agent_run.cancelled
        data:
          $ref: '#/components/schemas/JsonValue'
        createdAt:
          type: string
          format: date-time
          description: When the event was created
      required:
        - id
        - event
        - data
        - createdAt
      additionalProperties: false
    AgentErrorResponse:
      type: object
      properties:
        error:
          $ref: '#/components/schemas/AgentError'
      required:
        - error
      additionalProperties: false
    AgentEffort:
      type: string
      enum:
        - minimal
        - low
        - medium
        - high
        - xhigh
        - auto
        - ultra
      description: >-
        Cost and reasoning effort preference for the run. `auto` lets Exa choose
        the appropriate effort. `ultra` is the highest-effort tier for work
        where completeness and thoroughness matter more than latency or cost,
        including large list building, deep multi-source research, and criteria
        that are hard to verify.
      default: auto
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
    AgentRunId:
      type: string
      minLength: 1
      maxLength: 200
      pattern: ^[A-Za-z0-9_.:-]+$
      description: Agent run ID. New run IDs are returned with the `agent_run_` prefix.
    AgentDataSource:
      type: object
      properties:
        provider:
          $ref: '#/components/schemas/AgentDataSourceProvider'
          description: >-
            Exa Connect data provider to enable for the run. All provider tools
            are available by default.
      required:
        - provider
    AgentBudget:
      type: object
      properties:
        maxCostDollars:
          type: number
          description: >-
            Maximum amount this run can spend in US dollars. Accepts $1–$100 and
            applies only to `auto` and `ultra`; when omitted, the default cap is
            $5 for `auto` and $20 for `ultra`.
        maxDurationSeconds:
          type: integer
          description: >-
            Soft wall-clock ceiling for the run in seconds. Accepts 300–10,800
            (5 minutes to 3 hours) and applies only to `ultra`. As the run
            approaches the limit, the agent stops starting new work and returns
            what it has found with `stopReason: "time_limit_reached"`.
      description: >-
        Optional per-run spending and duration limits for the metered `auto` and
        `ultra` efforts. Runs that finish early may cost less than the limit.
    AgentRunStatus:
      type: string
      enum:
        - queued
        - running
        - completed
        - failed
        - cancelled
    AgentStopReason:
      type: string
      enum:
        - schema_satisfied
        - budget_reached
        - time_limit_reached
        - stopped
        - error
        - cancelled
    AgentRunRequest:
      type: object
      properties:
        query:
          type: string
          minLength: 1
          description: Natural-language question or instructions for the request.
        systemPrompt:
          type: string
          description: >-
            Additional instructions that guide generated output or agent
            behavior. Use this for source preferences, novelty constraints,
            duplication constraints, or other behavior guidance.
        effort:
          $ref: '#/components/schemas/AgentEffort'
        input:
          type: object
          properties:
            data:
              type: array
              items:
                type: object
                propertyNames:
                  type: string
                additionalProperties:
                  $ref: '#/components/schemas/JsonValue'
                description: A JSON object record.
              description: Records the agent should process or enrich.
            exclusion:
              type: array
              items:
                type: object
                propertyNames:
                  type: string
                additionalProperties:
                  $ref: '#/components/schemas/JsonValue'
                description: A JSON object record.
              description: Records or entities the agent should avoid returning.
          additionalProperties: false
        outputSchema:
          anyOf:
            - type: object
              propertyNames:
                type: string
              additionalProperties:
                $ref: '#/components/schemas/JsonValue'
              description: >-
                JSON Schema for validated structured output in
                `output.structured`. Fields unsupported by evidence may be
                returned as `null`. Supports draft-07, 2019-09, and 2020-12 via
                `$schema`.
            - type: 'null'
        previousRunId:
          $ref: '#/components/schemas/AgentRunId'
        metadata:
          type: object
          propertyNames:
            type: string
          additionalProperties:
            type: string
          description: Caller-provided key-value metadata for your own tracking.
        dataSources:
          type: array
          items:
            $ref: '#/components/schemas/AgentDataSourceOutput'
          description: Exa Connect data providers configured for the run.
        budget:
          $ref: '#/components/schemas/AgentBudgetOutput'
      additionalProperties:
        $ref: '#/components/schemas/JsonValue'
      description: Canonicalized request fields stored with the run.
    AgentRunOutput:
      type: object
      properties:
        text:
          type: string
          description: Natural-language answer or summary.
        structured:
          anyOf:
            - $ref: '#/components/schemas/JsonValue'
            - type: 'null'
          description: >-
            JSON shaped by `outputSchema`; fields unsupported by evidence may be
            `null`. `null` when no schema was provided.
        grounding:
          type: array
          items:
            $ref: '#/components/schemas/AgentGrounding'
          description: Field-level citations emitted by the run.
      required:
        - text
        - structured
        - grounding
      additionalProperties: false
    AgentUsage:
      type: object
      properties:
        agentComputeUnits:
          type: number
          minimum: 0
        searches:
          type: integer
          minimum: 0
        emails:
          type: integer
          minimum: 0
        phoneNumbers:
          type: integer
          minimum: 0
        dataSources:
          $ref: '#/components/schemas/AgentDataSourceUsage'
      required:
        - agentComputeUnits
        - searches
        - emails
        - phoneNumbers
      additionalProperties: false
    AgentCostDollars:
      type: object
      properties:
        total:
          type: number
          minimum: 0
        agentCompute:
          type: number
          minimum: 0
        search:
          type: number
          minimum: 0
        emails:
          type: number
          minimum: 0
        phoneNumbers:
          type: number
          minimum: 0
        dataSources:
          $ref: '#/components/schemas/AgentDataSourceCost'
      required:
        - total
        - agentCompute
        - search
        - emails
        - phoneNumbers
      additionalProperties: false
    AgentError:
      type: object
      properties:
        type:
          type: string
          enum:
            - INVALID_REQUEST
            - AUTHENTICATION_ERROR
            - RATE_LIMIT_ERROR
            - NOT_FOUND
            - SERVER_ERROR
        code:
          type: string
          enum:
            - INVALID_REQUEST
            - TEAM_NOT_FOUND
            - RUN_NOT_FOUND
            - PREVIOUS_RUN_NOT_FOUND
            - PREVIOUS_RUN_NOT_COMPLETED
            - CONCURRENCY_LIMIT_REACHED
            - INVALID_OUTPUT_SCHEMA
            - INVALID_DATA_SOURCE
            - TIMEOUT
            - SERVER_ERROR
        message:
          type: string
      required:
        - type
        - code
        - message
      additionalProperties:
        $ref: '#/components/schemas/JsonValue'
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
    AgentDataSourceProvider:
      type: string
      enum:
        - fiber
        - financial_datasets
        - similarweb
        - baselayer
        - affiliate
        - particle
        - jinko
        - polymarket
        - macrobond
      description: Identifier of an Exa Connect data provider.
    AgentDataSourceOutput:
      type: object
      properties:
        provider:
          $ref: '#/components/schemas/AgentDataSourceProvider'
          description: >-
            Exa Connect data provider to enable for the run. All provider tools
            are available by default.
      required:
        - provider
      additionalProperties: false
    AgentBudgetOutput:
      type: object
      properties:
        maxCostDollars:
          type: number
          description: >-
            Maximum amount this run can spend in US dollars. Accepts $1–$100 and
            applies only to `auto` and `ultra`; when omitted, the default cap is
            $5 for `auto` and $20 for `ultra`.
        maxDurationSeconds:
          type: integer
          description: >-
            Soft wall-clock ceiling for the run in seconds. Accepts 300–10,800
            (5 minutes to 3 hours) and applies only to `ultra`. As the run
            approaches the limit, the agent stops starting new work and returns
            what it has found with `stopReason: "time_limit_reached"`.
      additionalProperties: false
      description: >-
        Optional per-run spending and duration limits for the metered `auto` and
        `ultra` efforts. Runs that finish early may cost less than the limit.
    AgentGrounding:
      type: object
      properties:
        field:
          type: string
          description: Output field the citations support.
        citations:
          type: array
          items:
            $ref: '#/components/schemas/AgentCitation'
        confidence:
          anyOf:
            - type: string
              enum:
                - low
                - medium
                - high
              description: Model-reported reliability for this field.
            - type: 'null'
      required:
        - field
        - citations
      additionalProperties: false
    AgentDataSourceUsage:
      type: object
      propertyNames:
        type: string
      additionalProperties:
        type: integer
        minimum: 0
      description: >-
        Per-provider tool call counts for Exa Connect data sources used during
        the run. Keys are provider names (e.g. `fiber`, `similarweb`). Only
        providers with non-zero usage are included.
    AgentDataSourceCost:
      type: object
      propertyNames:
        type: string
      additionalProperties:
        type: number
        minimum: 0
      description: >-
        Per-provider cost in dollars for Exa Connect data sources used during
        the run. Keys are provider names (e.g. `fiber`, `similarweb`). Only
        providers with non-zero usage are included.
    AgentCitation:
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
      additionalProperties: false
  headers:
    XRequestId:
      description: >-
        Unique identifier for the request. Matches the `requestId` field
        returned in response bodies that carry one.
      schema:
        type: string
  responses:
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