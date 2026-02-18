# Unified Launcher Architecture — Claudius, Artifex Maximus

The unified launcher (`claudius.py`) replaces the standalone `bot.py` daemon as the primary way to run Claudius. It starts an interactive terminal session alongside a Slack Socket Mode bot in a single process, with per-channel session isolation via the Claude Agent SDK.

## What Makes This Novel

Every existing Claude Code + Slack integration (mpociot/claude-code-slack-bot, sleepless-agent, Anthropic's official Claude Code in Slack) spawns a separate `claude -p` subprocess per message. This means:

- Each message burns separate API credits
- No terminal visibility into Slack conversations
- No shared context between terminal and Slack

The unified launcher is architecturally different: **one process, multiple input channels, per-channel sessions via the Agent SDK's `resume` parameter, shared soul engine and memory.**

## Installation

### 1. Prerequisites

- Python 3.10+
- `claude` CLI in PATH: verify with `which claude`
- Slack Bot Token (`SLACK_BOT_TOKEN` / `xoxb-...`)
- Slack App Token (`SLACK_APP_TOKEN` / `xapp-...`) — Socket Mode must be enabled
- Bot event subscriptions: `app_mention`, `message.im`, `app_home_opened`

See SKILL.md "First-Time Setup" for full Slack app creation steps.

### 2. Install Dependencies

```bash
cd ~/.claude/skills/slack/daemon
uv pip install --system slack-bolt claude-agent-sdk
```

The unified launcher requires the Claude Agent SDK (`claude-agent-sdk`) in addition to Slack dependencies. The legacy daemon (`bot.py`) does not need the SDK.

### 3. Verify Environment

```bash
which claude              # must return a path
echo $SLACK_BOT_TOKEN     # should start with xoxb-
echo $SLACK_APP_TOKEN     # should start with xapp-
python3 -c "from claude_code_sdk import query; print('SDK OK')"
```

### 4. First Launch

```bash
cd ~/.claude/skills/slack/daemon && python3 claudius.py --verbose
```

On first launch, Claudius will:
- Connect to Slack via Socket Mode
- Initialize SQLite databases (`memory.db`, `sessions.db`) if not present
- Display the terminal prompt (`You > `)
- Log all Slack activity to the terminal

Test by sending a DM to the bot in Slack — you should see the message logged in the terminal and a response posted back to the thread.

### 5. Terminal-Only Mode (No Slack)

```bash
python3 claudius.py --no-slack
```

Useful for testing the Agent SDK integration without Slack connectivity.

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                    claudius.py                         │
│                                                        │
│  ┌──────────────────┐      ┌────────────────────────┐ │
│  │   Terminal UI      │      │   Slack Adapter         │ │
│  │   (async stdin)    │      │   (Socket Mode, bolt)   │ │
│  │                    │      │                          │ │
│  │  terminal_ui.py    │      │  slack_adapter.py        │ │
│  │  User types here   │      │  @mentions + DMs         │ │
│  └────────┬───────────┘      └───────────┬─────────────┘ │
│           │                               │               │
│           ▼                               ▼               │
│  ┌────────────────────────────────────────────────────┐  │
│  │              Async Message Queue                    │  │
│  │                                                      │  │
│  │   { origin: "terminal"|"slack",                     │  │
│  │     text, channel, thread_ts, user_id, ... }        │  │
│  └────────────────────────┬───────────────────────────┘  │
│                           │                               │
│                           ▼                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │          claude_handler.async_process()              │  │
│  │                                                      │  │
│  │  Claude Agent SDK query(prompt, options)             │  │
│  │    • resume=session_id  (per-channel continuity)    │  │
│  │    • permission_mode=bypassPermissions               │  │
│  │    • allowed_tools per origin (Slack vs Terminal)    │  │
│  │                                                      │  │
│  │  Soul engine (Slack messages only by default):       │  │
│  │    • soul_engine.build_prompt()  → wrap with XML     │  │
│  │    • soul_engine.parse_response() → extract dialogue │  │
│  └────────────────────────┬───────────────────────────┘  │
│                           │                               │
│                           ▼                               │
│  ┌────────────────────────────────────────────────────┐  │
│  │               Response Router                       │  │
│  │                                                      │  │
│  │  Slack origin:                                       │  │
│  │    → slack.post(channel, response, thread_ts)        │  │
│  │    → slack.react() hourglass add/remove              │  │
│  │    → terminal_ui.log_slack_out()                     │  │
│  │                                                      │  │
│  │  Terminal origin:                                    │  │
│  │    → terminal_ui.log_terminal_response()             │  │
│  └────────────────────────────────────────────────────┘  │
│                                                           │
│  ┌────────────────────────────────────────────────────┐  │
│  │          Shared State (SQLite)                      │  │
│  │                                                      │  │
│  │  memory.db:                                          │  │
│  │    • soul_memory    — global state (project, mood)   │  │
│  │    • user_models    — per-user personality profiles   │  │
│  │    • working_memory — per-thread metadata store       │  │
│  │                                                      │  │
│  │  sessions.db:                                        │  │
│  │    • sessions       — channel+thread → session_id     │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
```

## Per-Channel Session Model

Each channel/thread maintains its own Claude Code session. The Agent SDK's `resume` parameter reloads prior conversation context.

| Source | Channel Key | Thread Key | Session ID | Soul Engine | Tools |
|--------|------------|-----------|-----------|-------------|-------|
| Terminal | `terminal` | `terminal` | Persisted in sessions.db | Off by default | `Read,Glob,Grep,Bash,WebFetch,Edit,Write` |
| Slack @mention in #general | `C0123ABCD` | `1234567890.123456` | Persisted in sessions.db | On | `Read,Glob,Grep,Bash,WebFetch` |
| Slack DM from user | `D0456EFGH` | `1234567890.789012` | Persisted in sessions.db | On | `Read,Glob,Grep,Bash,WebFetch` |

- **Terminal** gets more tools (`Edit,Write`) since it's the operator's direct interface.
- **Slack** gets read-heavy tools to prevent unintended writes from external users.
- **Soul engine** is off for terminal by default (direct Claude access). Toggle with `SLACK_DAEMON_TERMINAL_SOUL=true`.

## Data Flow: Slack Message

```
1. User @mentions Claudius in #general thread:abc
2. slack_adapter.py receives app_mention event
3. _strip_mention() cleans text, _resolve_display_name() gets user name
4. _dispatch() schedules async callback via run_coroutine_threadsafe()
5. Message enqueued: {origin: "slack", text, channel, thread_ts, user_id, display_name}
6. process_loop picks up message
7. terminal_ui.log_slack_in() → "[12:34:56] [Slack ← #general] Tom: hello"
8. slack.react(channel, thread_ts, "hourglass_flowing_sand")
9. claude_handler.async_process():
   a. session_store.get(channel, thread_ts) → existing session_id or None
   b. soul_engine.build_prompt(text, user_id, ...) → XML-wrapped prompt
   c. soul_engine.store_user_message(text, user_id, ...)
   d. SDK query(prompt, options={resume, allowed_tools, cwd, ...})
   e. Collect AssistantMessage TextBlocks → full_response
   f. ResultMessage → new session_id
   g. session_store.save(channel, thread_ts, new_session_id)
   h. soul_engine.parse_response(full_response, ...) → external_dialogue
10. slack.post(channel, external_dialogue, thread_ts)
11. slack.react(channel, thread_ts, "hourglass_flowing_sand", remove=True)
12. terminal_ui.log_slack_out() → "[12:34:59] [Slack → #general] <response>"
```

## Data Flow: Terminal Message

```
1. User types "explain the session model" at "You > " prompt
2. terminal_ui.input_loop() reads via run_in_executor()
3. Message enqueued: {origin: "terminal", text: "explain the session model"}
4. process_loop picks up message
5. claude_handler.async_process():
   a. session_store.get("terminal", "terminal") → existing session_id or None
   b. No soul engine wrapping (TERMINAL_SOUL_ENABLED=false)
   c. SDK query(prompt, options={resume, TERMINAL_SESSION_TOOLS, cwd, ...})
   d. Collect response text
   e. session_store.save("terminal", "terminal", new_session_id)
6. terminal_ui.log_terminal_response() → full response displayed
```

## Claude Agent SDK Integration

The launcher uses the Python `claude-agent-sdk` package (v0.1.36+).

### Key API: `query()`

```python
from claude_agent_sdk import query, ClaudeAgentOptions

async for message in query(
    prompt=prompt,
    options=ClaudeAgentOptions(
        allowed_tools=["Read", "Glob", "Grep", "Bash", "WebFetch"],
        cwd="/Users/tom/Desktop/Programming",
        permission_mode="bypassPermissions",
        resume="existing-session-id",  # session continuity
    ),
):
    if isinstance(message, AssistantMessage):
        for block in message.content:
            if isinstance(block, TextBlock):
                response += block.text
    elif isinstance(message, ResultMessage):
        session_id = message.session_id
```

### Message Types

| Type | Contains | Used For |
|------|----------|----------|
| `AssistantMessage` | `content: list[TextBlock\|ToolUseBlock\|...]` | Collecting response text |
| `ResultMessage` | `session_id`, `is_error`, `result`, `total_cost_usd` | Session persistence, error handling |
| `SystemMessage` | `subtype`, `data` | Init events, session metadata |
| `UserMessage` | `content` | (Not used — we provide prompt as string) |

### ClaudeAgentOptions

| Field | Value | Purpose |
|-------|-------|---------|
| `allowed_tools` | `["Read","Glob",...]` | Restrict tool access per origin |
| `cwd` | `~/Desktop/Programming` | Working directory |
| `permission_mode` | `"bypassPermissions"` | No interactive prompts (daemon mode) |
| `resume` | session ID string | Resume prior conversation context |
| `env` | (optional) dict | Environment overrides |

## Soul Engine Integration

The soul engine runs identically to the legacy daemon. The only change is transport: SDK `query()` replaces `subprocess.run(["claude", "-p", ...])`.

### Cognitive Steps (unchanged)

```
soul_engine.build_prompt(text, user_id, channel, thread_ts)
  │
  ├── Load soul.md personality blueprint (first message only)
  ├── Load skills.md capabilities (first message only)
  ├── Load soul_memory state (always)
  ├── Load user_model (gated — Samantha-Dreams pattern)
  ├── Inject cognitive instructions (XML output format)
  └── Fence user message as untrusted input

  ↓ Claude processes ↓

soul_engine.parse_response(raw_response, user_id, channel, thread_ts)
  │
  ├── Extract <internal_monologue> → store in working_memory (not sent to user)
  ├── Extract <external_dialogue>  → returned as the response
  ├── Extract <user_model_check>   → boolean gate
  ├── Extract <user_model_update>  → save new profile if check=true
  ├── Extract <soul_state_check>   → boolean gate (every Nth turn)
  └── Extract <soul_state_update>  → persist to soul_memory if check=true
```

### Three-Tier Memory (unchanged)

| Tier | Scope | Shared Across Sessions | Storage |
|------|-------|----------------------|---------|
| Working memory | Per-thread | No | `memory.db` → `working_memory` |
| User models | Per-user | Yes | `memory.db` → `user_models` |
| Soul memory | Global | Yes | `memory.db` → `soul_memory` |

All sessions (terminal + all Slack threads) read/write the same SQLite databases. This means:
- Claudius's emotional state updates from a Slack conversation are visible in the terminal session's soul context
- User model updates from a DM carry over to channel mentions
- The Soul Monitor TUI shows activity from all channels

## Threading Model

```
Main thread (asyncio event loop):
  ├── process_loop()     — sequential message processing
  └── input_loop()       — terminal stdin (via run_in_executor)

Slack bolt thread (daemon):
  └── SocketModeHandler  — WebSocket → event handlers → run_coroutine_threadsafe()
```

The Slack adapter runs Socket Mode in a daemon thread. When events arrive, `run_coroutine_threadsafe()` bridges them to the async event loop on the main thread. Messages are processed sequentially from the queue to avoid concurrent SDK calls.

## Comparison: Unified Launcher vs Legacy Daemon

| Aspect | `claudius.py` (unified) | `bot.py` (legacy) |
|--------|------------------------|-------------------|
| Transport | Claude Agent SDK `query()` | `subprocess.run(["claude", "-p"])` |
| Terminal access | Yes — interactive input | No |
| Session management | SDK `resume=` parameter | CLI `--resume` flag |
| Soul engine | Same (`soul_engine.py`) | Same (`soul_engine.py`) |
| Memory | Same SQLite DBs | Same SQLite DBs |
| Error handling | Async, structured `ResultMessage` | JSON parse of stdout |
| Activity visibility | All channels in terminal | Logs only |
| launchd compatible | Not yet (needs stdin) | Yes |
| Process model | One process, async | One process, sync threads |

## File Map

```
daemon/
├── claudius.py          # Unified launcher — main entry point
│   ├── Claudius class   #   async queue, process loop, lifecycle
│   ├── _enqueue_slack() #   Slack → queue bridge
│   ├── _enqueue_terminal() # terminal → queue bridge
│   ├── _handle_slack_message() # process + post to Slack
│   ├── _handle_terminal_message() # process + display
│   └── _shutdown()      #   graceful cleanup
│
├── slack_adapter.py     # Slack Socket Mode adapter (extracted from bot.py)
│   ├── SlackAdapter class
│   ├── _setup_handlers() # app_mention, message.im, app_home_opened
│   ├── _dispatch()      #   run_coroutine_threadsafe bridge
│   ├── start()          #   background daemon thread
│   ├── stop()           #   handler.close()
│   ├── post()           #   chat_postMessage
│   └── react()          #   reactions_add/remove
│
├── terminal_ui.py       # Async terminal interface
│   ├── TerminalUI class
│   ├── input_loop()     #   async stdin via run_in_executor
│   ├── log_slack_in()   #   "[Slack ← #ch] user: text"
│   ├── log_slack_out()  #   "[Slack → #ch] response"
│   └── log_terminal_response() # full response display
│
├── claude_handler.py    # Claude invocation (dual mode)
│   ├── process()        #   legacy: subprocess claude -p
│   └── async_process()  #   new: SDK query(resume=)
│
├── soul_engine.py       # Cognitive architecture (unchanged)
├── working_memory.py    # Per-thread metadata (unchanged)
├── user_models.py       # Per-user profiles (unchanged)
├── soul_memory.py       # Global soul state (unchanged)
├── session_store.py     # Thread→session mapping (unchanged)
├── config.py            # Settings + new TERMINAL_* configs
├── bot.py               # Legacy standalone daemon (preserved)
├── monitor.py           # Soul Monitor TUI (unchanged, reads same DBs)
└── watcher.py           # DB file watcher (unchanged)
```

## Configuration

| Setting | Env Var | Default | Applies To |
|---------|---------|---------|-----------|
| Claude timeout | `SLACK_DAEMON_TIMEOUT` | `120` s | Both |
| Working directory | `SLACK_DAEMON_CWD` | `~/Desktop/Programming` | Both |
| Slack tools | `SLACK_DAEMON_TOOLS` | `Read,Glob,Grep,Bash,WebFetch` | Slack only |
| Terminal tools | `SLACK_DAEMON_TERMINAL_TOOLS` | `Read,Glob,Grep,Bash,WebFetch,Edit,Write` | Terminal only |
| Terminal soul | `SLACK_DAEMON_TERMINAL_SOUL` | `false` | Terminal only |
| Soul engine | `SLACK_DAEMON_SOUL_ENGINE` | `true` | Slack (Terminal if above=true) |
| Session TTL | `SLACK_DAEMON_SESSION_TTL` | `24` hours | Both |
| Memory window | `SLACK_DAEMON_MEMORY_WINDOW` | `20` entries | Soul engine |
| Memory TTL | `SLACK_DAEMON_MEMORY_TTL` | `72` hours | Soul engine |
| Soul state interval | `SLACK_DAEMON_SOUL_STATE_INTERVAL` | `3` interactions | Soul engine |

## Launch Commands

```bash
# Unified launcher (terminal + Slack)
cd ~/.claude/skills/slack/daemon && python3 claudius.py

# With debug logging to console
python3 claudius.py --verbose

# Terminal only (no Slack bot)
python3 claudius.py --no-slack

# Legacy daemon (Slack only, subprocess mode)
python3 bot.py --verbose

# Soul Monitor TUI (separate terminal)
uv run python monitor.py
```

## Prior Art

| Project | Architecture | Limitation |
|---------|-------------|-----------|
| mpociot/claude-code-slack-bot | Node.js SDK, per-message `query()` | No terminal, no soul engine |
| sleepless-agent | Python daemon, task queue, subprocess | No terminal, no personality |
| Anthropic Claude Code in Slack | Cloud-only, managed | No local control |
| **Claudius unified launcher** | **SDK `query(resume=)`, multiplexed I/O, soul engine** | **Novel: no prior art** |
