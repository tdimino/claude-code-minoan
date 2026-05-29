# Cloudflare Agents SDK — Core Reference

*Last verified: 2026-05-29 | SDK: `agents@0.13.2` | [Docs](https://developers.cloudflare.com/agents/) | [GitHub](https://github.com/cloudflare/agents)*

---

## Architecture

The Agent class is layered: `DurableObject` > `Server` (partyserver) > `Agent` > `AIChatAgent` > `Think`. Each layer adds capabilities; extend the one that matches the job.

| Class | Package | Purpose |
|-------|---------|---------|
| `Agent` | `agents` | Base: state, scheduling, fibers, sub-agents, RPC, MCP |
| `AIChatAgent` | `@cloudflare/ai-chat` | Chat: message persistence, streaming, tool approval, data parts |
| `Think` | `@cloudflare/think` | Opinionated chat: full agentic loop, extensions, auto-continuation |
| `withVoice(Agent)` | `@cloudflare/voice` | Mixin: real-time STT/TTS over WebSocket |

## Agent Base Class

```typescript
import { Agent } from "agents";

export class MyAgent extends Agent<Env, MyState> {
  initialState = { count: 0 };

  async onStart() {
    // Called on first activation — set up MCP, schedules, etc.
  }

  async onRequest(request: Request): Promise<Response> {
    return Response.json(this.state);
  }
}
```

### Reactive State

`agent.state` is reactive on both server and client. `useAgent` (React) and `AgentClient` (vanilla JS) expose a `state` property that re-renders/fires callbacks on change.

```typescript
// React
const agent = useAgent<MyAgent, MyState>({ agent: "my-agent", name: "room-1" });
return <div>{agent.state?.count}</div>;

// Vanilla JS
const client = new AgentClient({ agent: "my-agent", name: "room-1", host: "..." });
client.addEventListener("stateupdate", () => console.log(client.state));
```

### keepAlive / keepAliveWhile

Prevent DO eviction during long-running work (default idle timeout: ~70-140s).

```typescript
const release = this.keepAlive();
try {
  await longOperation();
} finally {
  release();
}

// Or with a promise
await this.keepAliveWhile(longOperation());
```

### Retry

Built-in exponential backoff with jitter. Also available per-task on `schedule()`, `scheduleEvery()`, `queue()`, and `addMcpServer()`.

```typescript
const data = await this.retry(() => callUnreliableService(), {
  maxAttempts: 4,
  shouldRetry: (err) => !(err instanceof PermanentError),
});
```

---

## Scheduling

Four modes, all persisted to SQLite and surviving restarts.

| Mode | Syntax | Example |
|------|--------|---------|
| Delayed | `this.schedule(60, ...)` | Run in 60 seconds |
| Scheduled | `this.schedule(new Date(...), ...)` | Run at specific time |
| Cron | `this.schedule("0 8 * * *", ...)` | Recurring schedule |
| Interval | `this.scheduleEvery(30, ...)` | Every 30 seconds |

```typescript
await this.schedule(30, "sendReminder", { message: "Check email" });
await this.schedule("0 8 * * *", "dailyDigest", { userId: "abc" });
await this.scheduleEvery(60, "heartbeat");
```

Schedules are idempotent across DO restarts (v0.8.0+). Per-task retry:

```typescript
await this.schedule(Date.now() + 60_000, "sendReport", { userId: "abc" }, {
  retry: { maxAttempts: 5 },
});
```

---

## Durable Execution (Fibers)

Work that survives DO eviction. `runFiber()` registers a task in SQLite, holds a `keepAlive` ref, and enables recovery via `onFiberRecovered`.

```typescript
await this.runFiber("my-task", async (ctx) => {
  const step1 = await expensiveOperation();
  ctx.stash({ step1 });  // checkpoint — survives eviction
  const step2 = await anotherOperation(step1);
  this.setState({ ...this.state, result: step2 });
});

async onFiberRecovered(ctx: FiberRecoveryContext) {
  const snapshot = ctx.snapshot as { step1: unknown } | null;
  if (snapshot) {
    await anotherOperation(snapshot.step1);
  }
}
```

`startFiber()` returns immediately for durable acceptance, dedup, status inspection, and cancellation.

---

## Human-in-the-Loop

Five patterns, chosen by architecture:

| Pattern | Best For |
|---------|----------|
| `waitForApproval` (Workflows) | Multi-step processes, durable gates (hours/weeks) |
| `needsApproval` (AIChatAgent) | Chat-based tool calls, server-side approval |
| `onToolCall` (client-side) | Tools needing browser APIs or user interaction |
| Elicitation (MCP) | MCP tools requesting structured user input |
| State + WebSocket | Lightweight confirmations without AI chat |

Decision: Is this part of a multi-step workflow? → Workflow Approval. Building an MCP server? → Elicitation. Chat-based? → `needsApproval` (server) or `onToolCall` (client).

---

## Workflows Integration

`AgentWorkflow` bridges real-time Agent state with durable execution.

```typescript
import { AgentWorkflow } from "agents/workflows";

export class ProcessingWorkflow extends AgentWorkflow {
  async run(event, step) {
    await this.agent.updateStatus(event.payload.taskId, "processing");
    await this.reportProgress({ step: "process", percent: 0.5 });

    const result = await step.do("process", async () => {
      return processData(event.payload.data);
    });

    await step.reportComplete(result);
    return result;
  }
}
```

**Dynamic Workflows** (May 2026): Durable execution following the tenant — platforms can spin up per-tenant workflows at runtime, combining Dynamic Workers with Workflows.

---

## Observability

Structured events via `diagnostics_channel` (v0.7.0+). Silent by default, zero overhead when no listener.

| Channel | Event Types |
|---------|-------------|
| `agents:state` | state:update |
| `agents:rpc` | rpc, rpc:error |
| `agents:message` | message:request/response/clear/cancel/error, tool:result, tool:approval |
| `agents:schedule` | schedule:create/execute/cancel/retry/error, queue:retry/error |
| `agents:lifecycle` | connect, destroy |
| `agents:workflow` | workflow:start/event/approved/rejected/terminated/paused/resumed/restarted |
| `agents:mcp` | mcp:client:preconnect/connect/authorize/discover |

```typescript
import { subscribe } from "agents/observability";
const unsub = subscribe("rpc", (event) => {
  if (event.type === "rpc:error") console.error(event.payload);
});
```

---

## MCP Integration

Consume external MCP servers inside an Agent. Three connection modes:

```typescript
// HTTP/SSE (classic)
await this.addMcpServer("tools", "https://mcp.example.com/sse");

// RPC via DO binding (v0.6.0+) — no HTTP overhead
await this.addMcpServer("counter", env.MY_MCP, {
  props: { userId: "user-123", role: "admin" },
});

// Wait for connections before chat (v0.7.0+)
static options = { waitForMcpConnections: true };
```

Supports elicitation (MCP tools requesting structured user input) and optional OAuth.

---

## wrangler.jsonc (Agents)

```jsonc
{
  "name": "my-agent",
  "main": "src/index.ts",
  "compatibility_date": "2026-01-01",
  "compatibility_flags": ["nodejs_compat"],
  "durable_objects": {
    "bindings": [{ "name": "AGENT", "class_name": "MyAgent" }]
  },
  "migrations": [{ "tag": "v1", "new_sqlite_classes": ["MyAgent"] }]
}
```

---

## Package Ecosystem

| Package | Purpose | Status |
|---------|---------|--------|
| `agents` | Agent base class, routing, scheduling, fibers, sub-agents | GA |
| `@cloudflare/ai-chat` | AIChatAgent + useAgentChat React hook | GA |
| `@cloudflare/think` | Opinionated chat agent (Think) | GA |
| `@cloudflare/voice` | Voice agents (STT/TTS) | Beta |
| `@cloudflare/codemode` | Code Mode (LLM-generated code in sandbox) | GA (sandbox open beta) |
| `workers-ai-provider` | AI SDK provider for Workers AI | GA |

Starter: `npx create-cloudflare@latest --template cloudflare/agents-starter`
