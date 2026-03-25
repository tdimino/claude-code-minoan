# Cloudflare Agents SDK & Code Mode Reference

*Last verified: 2026-03-24 | SDK: `@cloudflare/codemode` | [Docs](https://developers.cloudflare.com/agents/) | [Blog](https://blog.cloudflare.com/code-mode)*

---

## Agents SDK

The Cloudflare Agents SDK provides stateful, durable AI agents running on Workers. Agents extend `DurableObject` with persistent SQLite-backed state, WebSocket connections, and MCP tool consumption.

### Agent Class

```typescript
import { Agent } from "@cloudflare/agents";
import { streamText, convertToModelMessages } from "ai";

export class MyAgent extends Agent<Env, AgentState> {
  initialState = { messages: [] };

  async onChatMessage() {
    const result = streamText({
      model,
      system: "You are a helpful assistant.",
      messages: await convertToModelMessages(this.state.messages),
      tools: { /* ... */ }
    });
    // Stream response back to client
  }
}
```

### MCP Integration

Consume external MCP servers inside an Agent:

```typescript
// Inside an Agent method
const mcpTools = await this.mcp.getAITools();
// mcpTools are AI SDK-compatible — pass to streamText/generateText
```

### wrangler.jsonc (Agents)

```jsonc
{
  "name": "my-agent",
  "main": "src/index.ts",
  "compatibility_date": "2025-09-01",
  "compatibility_flags": ["nodejs_compat"],
  "durable_objects": {
    "bindings": [{ "name": "AGENT", "class_name": "MyAgent" }]
  },
  "migrations": [{ "tag": "v1", "new_sqlite_classes": ["MyAgent"] }]
}
```

---

## Code Mode

Code Mode converts MCP/AI SDK tools into TypeScript APIs that LLMs write code against. The generated code runs in isolated V8 Worker sandboxes with millisecond cold starts.

**Why this works better than tool calling:** LLMs have millions of real-world TypeScript examples in training data but only contrived tool-calling formats. Writing code is their native competency. Code Mode also eliminates intermediate LLM roundtrips when chaining tools — the LLM writes orchestration logic once.

### Installation

```bash
npm install @cloudflare/codemode ai zod
```

### Core API

| Export | Package | Purpose |
|--------|---------|---------|
| `createCodeTool(options)` | `@cloudflare/codemode/ai` | Wraps tools into an AI SDK-compatible code tool |
| `DynamicWorkerExecutor` | `@cloudflare/codemode` | Executes LLM-generated code in isolated V8 sandbox |
| `generateTypes(tools)` | `@cloudflare/codemode` | Auto-generates TypeScript declarations from tool definitions |
| `sanitizeToolName(name)` | `@cloudflare/codemode` | Normalizes MCP tool names to valid JS identifiers |

### Creating and Using a Code Tool

```typescript
import { createCodeTool } from "@cloudflare/codemode/ai";
import { DynamicWorkerExecutor } from "@cloudflare/codemode";
import { tool } from "ai";
import { z } from "zod";

// 1. Define tools (standard AI SDK format)
const tools = {
  getWeather: tool({
    description: "Get weather for a location",
    parameters: z.object({ location: z.string() }),
    execute: async ({ location }) => `Weather in ${location}: 72F, sunny`
  }),
  sendEmail: tool({
    description: "Send an email",
    parameters: z.object({ to: z.string(), subject: z.string(), body: z.string() }),
    execute: async ({ to, subject, body }) => `Email sent to ${to}`
  })
};

// 2. Create executor (requires worker_loaders binding)
const executor = new DynamicWorkerExecutor({
  loader: env.LOADER,
  timeout: 30000,        // default 30s
  globalOutbound: null   // block all fetch/connect (default)
});

// 3. Wrap tools into a code tool
const codemode = createCodeTool({ tools, executor });

// 4. Pass to streamText — LLM writes code calling codemode.*
const result = streamText({
  model,
  system: "You are a helpful assistant.",
  messages,
  tools: { codemode }
});
```

The LLM then generates code like this (you don't write this — Code Mode produces it automatically):

```typescript
async () => {
  const weather = await codemode.getWeather({ location: "London" });
  if (weather.includes("sunny")) {
    await codemode.sendEmail({
      to: "team@example.com",
      subject: "Nice day!",
      body: `It's ${weather}`
    });
  }
  return { weather, notified: true };
};
```

### wrangler.jsonc (Code Mode)

Add the `worker_loaders` binding to enable sandbox execution:

```jsonc
{
  "worker_loaders": [{ "binding": "LOADER" }],
  "compatibility_flags": ["nodejs_compat"]
}
```

### Using with MCP Tools

```typescript
const codemode = createCodeTool({
  tools: {
    ...myLocalTools,
    ...(await this.mcp.getAITools())  // MCP tools auto-converted to TypeScript
  },
  executor
});
```

### Security Model

- Each execution runs in an **isolated V8 isolate** (millisecond startup, single-digit MB memory)
- `fetch()` and `connect()` are **blocked by default** at the Workers runtime level
- Code can only interact with host through `codemode.*` tool calls
- API keys are held by the supervisor Worker, never exposed to generated code
- Optional: pass a `Fetcher` via `globalOutbound` to allow controlled outbound access
- Console output is captured separately, does not leak to host

### Beta Status & Limitations

- `@cloudflare/codemode` package is **available on npm**
- Dynamic Worker Loader API is in **closed beta** for production deployment
- **Available locally** with `wrangler dev` for development and testing
- `needsApproval` on tools is **not yet supported** — tools execute immediately without pausing
- The Agent class and MCP integration are **generally available**

---

## Links

- SDK docs: https://developers.cloudflare.com/agents/
- Code Mode docs: https://github.com/cloudflare/agents/blob/main/docs/codemode.md
- Blog post: https://blog.cloudflare.com/code-mode
- npm: https://www.npmjs.com/package/@cloudflare/codemode
- Agents starter: `npm create cloudflare@latest -- --template agents`
- Beta signup (Worker Loader): https://forms.gle/MoeDxE9wNiqdf8ri9
