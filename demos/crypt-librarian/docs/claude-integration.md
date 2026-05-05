# Claude Integration — VELVET CATALOGUE

The Claudius page (`/claudius`) provides an oracle chat interface. The backend spawns `claude -p` subprocesses (Claude Code's programmatic mode) and streams responses to the frontend via Server-Sent Events.

---

## Architecture

```
Browser                    FastAPI (server.py)              claude -p
──────                     ──────────────────               ─────────
POST /api/claudius/stream  spawn subprocess                 --output-format stream-json
  {prompt, chat_id}   ──►  asyncio.create_subprocess_exec  --allowedTools Read,Glob,Grep,Bash,WebFetch
                            │                               --resume <session_id>
                            │  stdout line by line
                            ◄──────────────────────────────
  data: {type, ...}\n\n
◄──────────────────────────
```

---

## SSE Event Types

| Type | Direction | Payload |
|------|-----------|---------|
| `session_init` | server → client | `{ chat_id }` — confirms session |
| `text` | server → client | `{ content }` — streaming text delta |
| `tool_use` | server → client | `{ id, name, input }` — tool invocation started |
| `tool_result` | server → client | `{ tool_use_id, content, is_error }` — tool completed |
| `result` | server → client | `{ session_id, result }` — final block |
| `error` | server → client | `{ message }` — subprocess error |
| `done` | server → client | `{}` — stream complete |

Example SSE frame:
```
data: {"type":"text","content":"Good evening. I see you've been watching..."}\n\n
```

---

## Backend: `POST /api/claudius/stream`

**Source:** `web/server.py`, function `stream_claudius`

1. Receives `{ prompt, chat_id? }` JSON body
2. Creates or retrieves chat session in SQLite
3. Spawns subprocess:
   ```python
   cmd = ["claude", "-p", prompt,
          "--output-format", "stream-json",
          "--allowedTools", "Read,Glob,Grep,Bash,WebFetch"]
   if claude_session_id:
       cmd.extend(["--resume", claude_session_id])
   ```
4. Pipes stdout line-by-line as `data: {json}\n\n` SSE events
5. Saves assistant message to SQLite on clean completion

**Environment sanitization** (`_build_claude_env`):
- All `CLAUDE_CODE_*` and `CLAUDECODE` vars stripped
- `CLAUDICLE_SOUL=1` injected (ensouled mode)
- `PATH` explicitly set to include `/opt/homebrew/bin`

**Response headers** include `X-Accel-Buffering: no` for nginx proxy compatibility.

---

## Frontend: SSE Consumer

**Source:** `app/claudius/page.tsx`, function `sendMessage`

Reads the response body as a `ReadableStream`, splits on `\n`, parses `data: ` lines as JSON. Dispatches by `event.type` in a switch statement.

**Tool event tracking:** `Map<string, ToolEvent>` keyed by tool ID. `tool_use` opens an entry, `tool_result` closes it. `ToolUseCard` components render during and after streaming. On `done`, finalized tool events are attached to the assistant message.

---

## Connection Status State Machine

```typescript
type ConnectionStatus = "idle" | "connecting" | "streaming" | "error";
```

| From | To | Trigger |
|------|----|---------|
| `idle` | `connecting` | `fetch` call starts |
| `connecting` | `streaming` | First SSE event parsed |
| `streaming` | `idle` | `finally` block (no prior error) |
| `any` | `error` | `catch` block (non-AbortError) |

The `finally` guard preserves error state:
```typescript
setConnectionStatus((prev) => prev === "error" ? "error" : "idle")
```

**Visual indicator** in header (always visible, not dev-mode only):

| Status | Style |
|--------|-------|
| idle | `bg-foxing/50` (dim dot) |
| connecting | `bg-amber animate-pulse` |
| streaming | `bg-amber` (solid) |
| error | `bg-oxblood` |

---

## Error Handling

Contextual messages instead of generic "oracle is silent":

| Condition | Message |
|-----------|---------|
| HTTP 400 | "I received your message but couldn't process it — the prompt may have been empty or malformed." |
| HTTP 500+ | "The oracle's flame has dimmed — the server encountered an error. Try again in a moment." |
| Network error | "I cannot reach the crypt's server. Check that the backend is running at {API_BASE}." |
| AbortError | Silently ignored (user cancelled) |

Errors appear as assistant messages in the chat flow (italic, foxing-colored) and are logged to the dev panel.

---

## Dev Mode

**Toggle:** Ctrl+Shift+D
**Component:** `components/claudius/DevPanel.tsx`

200px tall, full width, positioned at bottom. Shows:
- Connection status dot + label
- Active tool names
- Scrollable monospace event log (auto-scrolls to bottom)

**Ring buffer:** 100 `DevLogEntry` objects (`{ time, type, summary }`).

Color-coded event types:
- `text-oxblood` — errors
- `text-amber` — `tool_use` / `tool_result`
- `text-foxing` — everything else

Exports `DevLogEntry` interface and `ConnectionStatus` type (shared with page).

---

## Ensouled Mode

`CLAUDICLE_SOUL=1` in the subprocess environment activates Claudicle's ensouled personality. The oracle speaks as Kothar wa Khasis, the Canaanite craftsman-god. The `KotharPersonaModal` component displays the daimonic identity when the avatar is clicked.

---

## Session Management

**Storage:** SQLite at `web/sessions.db` via `web/session_store.py` (WAL mode).

| Endpoint | Returns |
|----------|---------|
| `GET /api/sessions` | Last 30 chat sessions (id, title, timestamps) |
| `GET /api/sessions/:id/messages` | Message history for a session |

Session continuity: `claude_session_id` (from the `result` event) is stored in SQLite and passed to `--resume` on subsequent turns. The frontend's `chat_id` is a VELVET CATALOGUE concept separate from Claude's internal session ID.

`SessionSidebar` component renders the session list with titles derived from first message content.

---

## Prompt Templates

| Label | Glyph | Purpose |
|-------|-------|---------|
| We just watched... | V | Record viewing, update films.json |
| Find films like... | ? | Discovery against taste profile |
| Add to queue | + | Add to to-watch list |
| Archive health | H | Maintenance and data integrity |
| Tonight's pick | T | Quick recommendation |

Each template pre-fills the input with a structured prompt that activates the crypt-librarian skill.
