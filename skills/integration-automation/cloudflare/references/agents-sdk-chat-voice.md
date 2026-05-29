# Cloudflare Agents SDK — Chat, Voice & Sub-Agents Reference

*Last verified: 2026-05-29 | SDK: `agents@0.13.2` | [Docs](https://developers.cloudflare.com/agents/)*

---

## AIChatAgent (`@cloudflare/ai-chat`)

Chat agent with automatic message persistence (SQLite), resumable streaming, real-time WebSocket sync, and tool support.

```typescript
import { AIChatAgent } from "@cloudflare/ai-chat";
import { streamText, convertToModelMessages } from "ai";

export class ChatAgent extends AIChatAgent {
  async onChatMessage() {
    const result = streamText({
      model,
      system: "You are a helpful assistant.",
      messages: await convertToModelMessages(this.messages),
      tools: { /* server-side tools */ },
    });
    return result;
  }
}
```

### Key Features

- **Message persistence** — conversations stored in SQLite, survive restarts
- **Resumable streaming** — disconnected clients resume mid-stream without data loss
- **Real-time sync** — messages broadcast to all connected clients via WebSocket
- **Tool support** — server-side, client-side (`onToolCall`), and human-in-the-loop (`needsApproval`)
- **Data parts** — attach typed JSON (citations, progress, usage) alongside text
- **Row size protection** — automatic compaction when messages approach SQLite limits

### needsApproval (HITL)

Mark sensitive tools for human approval before execution:

```typescript
async onChatMessage() {
  return streamText({
    model,
    tools: {
      deleteAccount: tool({
        description: "Delete user account",
        parameters: z.object({ userId: z.string() }),
        execute: async ({ userId }) => deleteUser(userId),
      }),
    },
    needsApproval: (toolCall) => toolCall.toolName === "deleteAccount",
  });
}
```

Client-side approval via `useAgentChat`:

```typescript
const { pendingToolCalls, addToolApprovalResponse } = useAgentChat({ agent, name });
// pendingToolCalls contains tools awaiting approval
addToolApprovalResponse(toolCallId, true);  // approve
addToolApprovalResponse(toolCallId, false, "Too risky"); // deny with message
```

### Client Hook (React)

```typescript
import { useAgentChat } from "@cloudflare/ai-chat/react";

const { messages, input, setInput, handleSubmit, isLoading } = useAgentChat({
  agent: "chat-agent",
  name: "session-123",
});
```

---

## Think (`@cloudflare/think`)

Opinionated chat base class that handles the full lifecycle: agentic loop, message persistence, streaming, tool execution, client tools, stream resumption, and extensions.

Works as both a top-level agent (WebSocket to browser) and a sub-agent (RPC streaming from parent).

```typescript
import { Think } from "@cloudflare/think";
import { createWorkersAI } from "workers-ai-provider";

export class MyAgent extends Think<Env> {
  getModel() {
    return createWorkersAI({ binding: this.env.AI })("@cf/moonshotai/kimi-k2.6");
  }
}
```

Think handles everything AIChatAgent does, plus:
- Automatic agentic loop (tool call → execute → continue)
- Auto-continuation for multi-step tool chains
- Extensions system for adding capabilities
- Durable submissions (v0.12.4+) — fibers wrap chat turns for recovery

---

## Voice Agents (`@cloudflare/voice`) — Beta

Real-time speech agents over WebSocket. Audio streams as binary frames; no SFU or meeting infrastructure needed.

### Server

```typescript
import { Agent } from "agents";
import { withVoice, WorkersAIFluxSTT, WorkersAITTS } from "@cloudflare/voice";

const VoiceAgent = withVoice(Agent);

export class MyAgent extends VoiceAgent {
  transcriber = new WorkersAIFluxSTT(this.env.AI);
  tts = new WorkersAITTS(this.env.AI);

  async onTurn(transcript, context) {
    return "Hello! I heard you say: " + transcript;
  }
}
```

### Client (React)

```typescript
import { useVoiceAgent } from "@cloudflare/voice/react";

const { isConnected, isListening, startListening, stopListening } = useVoiceAgent({
  agent: "voice-agent",
  name: "call-1",
});
```

### Capabilities

| Export | Purpose |
|--------|---------|
| `withVoice` | Full voice agent: STT → LLM → TTS → persistence |
| `withVoiceInput` | STT-only: transcription without response |
| `useVoiceAgent` | React hook for `withVoice` agents |
| `useVoiceInput` | React hook for `withVoiceInput` agents |
| `VoiceClient` | Framework-agnostic client |

Features: streaming TTS (sentence-chunked), interruption handling (user speech cancels response), continuous STT (per-call transcriber session), pipeline hooks for transform at every stage.

---

## Sub-Agents

Spawn child agents as co-located DOs with isolated SQLite storage. Parent gets a typed RPC stub.

```typescript
import { Agent } from "agents";

export class Orchestrator extends Agent {
  async delegateWork() {
    const researcher = await this.subAgent(Researcher, "research-1");
    const findings = await researcher.search("cloudflare agents sdk");
    return findings;
  }
}

export class Researcher extends Agent {
  async search(query: string) {
    const results = await fetch(`https://api.example.com/search?q=${query}`);
    return results.json();
  }
}
```

Sub-agents support all alarm-backed APIs: `schedule()`, `scheduleEvery()`, `keepAlive()`, `runFiber()`. Schedules are scoped — siblings cannot cancel each other's schedules.

### Client-Side Routing

Address sub-agents directly from the client:

```typescript
const agent = useAgent({
  agent: "orchestrator",
  name: "user-1",
  sub: [{ agent: "Chat", name: chatId }],
});
```

### Lifecycle Hooks

```typescript
async onBeforeSubAgent(className, id) {
  // Access control, logging, resource limits
}
```

---

## Agent Tools

Run sub-agents as retained, streaming tools from a parent. Built on sub-agents but adds run registry, streaming `agent-tool-event` frames, replay, cancellation, and cleanup.

```typescript
import { runAgentTool, agentTool } from "agents";

// Define a tool that runs a sub-agent
const researchTool = agentTool({
  agent: Researcher,
  description: "Research a topic",
  parameters: z.object({ query: z.string() }),
});

// Use in streamText — parent renders child progress inline
const result = streamText({
  model,
  tools: { research: researchTool },
});
```

---

## Chat Recovery (v0.12.4+)

Server turns continue running when a client stream is interrupted (refresh, tab close, lost connection). The turn resumes on reconnect.

```typescript
const chat = useAgentChat({
  agent: "assistant",
  name: "user-123",
  cancelOnClientAbort: true,  // opt-in: browser abort also cancels server turn
});
```

Default behavior: server keeps running. Call `stop()` to explicitly cancel.

---

## Chat SDK State Adapter (v0.13.2+)

`agents/chat-sdk` provides a Chat SDK `StateAdapter` backed by sub-agents, storing subscriptions, locks, queues, cache, thread state, and message history in DO SQLite.

```typescript
export { ChatSdkStateAgent } from "agents/chat-sdk";
import { createChatSdkState } from "agents/chat-sdk";

const chat = new Chat({
  adapters,
  state: createChatSdkState(),
});
```

---

## Choosing the Right Level

| Need | Class |
|------|-------|
| Custom protocol, non-chat | `Agent` |
| Chat with full control over the agentic loop | `AIChatAgent` |
| Chat with minimal boilerplate | `Think` |
| Voice interaction | `withVoice(Agent)` or `withVoice(AIChatAgent)` |
| Orchestrating multiple agents | `Agent` + `subAgent()` |
| Sub-agent as a streaming tool | `agentTool()` / `runAgentTool()` |
