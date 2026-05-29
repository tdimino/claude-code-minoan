# Cloudflare Code Mode & Dynamic Workers Reference

*Last verified: 2026-05-29 | SDK: `@cloudflare/codemode@0.2.1` | [Docs](https://github.com/cloudflare/agents/blob/main/docs/codemode.md) | [npm](https://www.npmjs.com/package/@cloudflare/codemode)*

---

## Code Mode Overview

Code Mode converts MCP/AI SDK tools into TypeScript APIs that LLMs write code against. The generated code runs in isolated V8 Worker sandboxes (Dynamic Workers) with millisecond cold starts.

LLMs have millions of real-world TypeScript examples in training data but only contrived tool-calling formats. Writing code is their native competency. Code Mode also eliminates intermediate LLM roundtrips when chaining tools — the LLM writes orchestration logic once. Can save up to 80% in inference tokens vs. sequential tool calls.

### Installation

```bash
npm install @cloudflare/codemode
# ai and zod are optional — only needed for the /ai entry point
```

The main entry point (`@cloudflare/codemode`) is zero-dependency. The `/ai` entry point requires `ai` and `zod` as peer dependencies.

---

## Core API

| Export | Package | Purpose |
|--------|---------|---------|
| `createCodeTool(options)` | `@cloudflare/codemode/ai` | Wraps tools into an AI SDK-compatible code tool |
| `DynamicWorkerExecutor` | `@cloudflare/codemode` | Executes LLM-generated code in isolated V8 sandbox |
| `generateTypes(tools)` | `@cloudflare/codemode` | Auto-generates TypeScript declarations from tool definitions |
| `sanitizeToolName(name)` | `@cloudflare/codemode` | Normalizes MCP tool names to valid JS identifiers |
| `codeMcpServer(opts)` | `@cloudflare/codemode/mcp` | Wraps an existing MCP server with a single `code` tool |
| `openApiMcpServer(opts)` | `@cloudflare/codemode/mcp` | Creates MCP tools from an OpenAPI spec with host-side proxying |

### Creating and Using a Code Tool

```typescript
import { createCodeTool } from "@cloudflare/codemode/ai";
import { DynamicWorkerExecutor } from "@cloudflare/codemode";
import { tool } from "ai";
import { z } from "zod";

const tools = {
  getWeather: tool({
    description: "Get weather for a location",
    parameters: z.object({ location: z.string() }),
    execute: async ({ location }) => `Weather in ${location}: 72F, sunny`
  }),
};

const executor = new DynamicWorkerExecutor({
  loader: env.LOADER,
  timeout: 30000,
  globalOutbound: null,  // block all fetch/connect (default)
});

const codemode = createCodeTool({ tools, executor });

const result = streamText({
  model,
  messages,
  tools: { codemode },  // LLM writes code calling codemode.*
});
```

### MCP Barrel Export (v0.2.1+)

Wrap an existing MCP server — all its tools become typed `codemode.*` methods:

```typescript
import { codeMcpServer } from "@cloudflare/codemode/mcp";
const server = await codeMcpServer({ server: upstreamMcp, executor });
```

Create MCP tools from an OpenAPI spec with host-side request proxying:

```typescript
import { openApiMcpServer } from "@cloudflare/codemode/mcp";
const server = await openApiMcpServer({ spec, executor, request });
```

### Custom Sandbox Modules (v0.2.1+)

Inject custom modules into the sandbox for LLM-generated code to import:

```typescript
const executor = new DynamicWorkerExecutor({
  loader: env.LOADER,
  modules: {
    "utils": `export function formatDate(d) { return d.toISOString(); }`,
  },
});
```

### Using with MCP Tools

```typescript
const codemode = createCodeTool({
  tools: {
    ...myLocalTools,
    ...(await this.mcp.getAITools()),  // MCP tools auto-converted
  },
  executor,
});
```

---

## Dynamic Workers (Open Beta)

Workers that spin up other Workers at runtime for on-demand code execution. Millisecond cold starts, isolated V8 sandboxes.

### Two Loading Modes

```typescript
// One-time execution
const result = await env.LOADER.load({
  compatibilityDate: "2026-01-01",
  mainModule: "src/index.js",
  modules: {
    "src/index.js": `export default { async fetch(req) { return new Response("hello"); } }`,
  },
});

// Cached by ID — stays warm across requests
const worker = await env.LOADER.get("my-worker-id", () => ({
  compatibilityDate: "2026-01-01",
  mainModule: "src/index.js",
  modules: { /* ... */ },
}));
```

### wrangler.jsonc

```jsonc
{
  "worker_loaders": [{ "binding": "LOADER" }],
  "compatibility_flags": ["nodejs_compat"]
}
```

---

## Sandbox Security

### Default Isolation

- Each execution runs in an isolated V8 isolate (millisecond startup, single-digit MB memory)
- `fetch()` and `connect()` are blocked by default at the Workers runtime level
- Code can only interact with host through `codemode.*` tool calls
- API keys are held by the supervisor Worker, never exposed to generated code
- Console output captured separately

### Credential Injection (Apr 2026)

Outbound Workers for Sandboxes inject secrets the sandbox never sees:

```typescript
export class MySandbox extends Sandbox {}

MySandbox.outboundByHost = {
  "github.com": (request: Request, env: Env, ctx: OutboundHandlerContext) => {
    const requestWithAuth = new Request(request);
    requestWithAuth.headers.set("x-auth-token", env.SECRET);
    return fetch(requestWithAuth);
  },
};
```

### Dynamic Egress Policies

Per-instance allow/deny lists, TLS interception, and unique credentials per `ctx.containerId`.

---

## Status

| Component | Status |
|-----------|--------|
| `@cloudflare/codemode` package | GA on npm |
| Dynamic Workers (sandbox execution) | **Open beta** for all paid Workers users |
| `codeMcpServer` / `openApiMcpServer` | GA |
| Custom sandbox modules | GA |
| Credential injection / dynamic egress | GA |

---

## Links

- SDK docs: https://developers.cloudflare.com/agents/
- Code Mode blog: https://blog.cloudflare.com/code-mode-mcp/
- npm: https://www.npmjs.com/package/@cloudflare/codemode
- Dynamic Workers docs: https://developers.cloudflare.com/workers/runtime-apis/dynamic-workers/
