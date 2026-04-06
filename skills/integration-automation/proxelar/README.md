# Proxelar

MITM proxy skill for Claude Code. Intercept, inspect, and modify HTTP/HTTPS traffic between applications and APIs using Lua scripting hooks.

**Last updated:** 2026-04-06

**Reflects:** [Proxelar](https://github.com/emanuele-em/proxelar) v0.4.1 (Rust, MIT, Homebrew)

---

## Why This Skill Exists

Claude Code agents have no native visibility into HTTP traffic flowing between applications and external APIs. Agent-browser's `network requests` command is browser-scoped only. This skill fills the gap with a programmable proxy that sits between any app and the internet, giving agents full request/response inspection and the ability to transform traffic on the fly via Lua hooks.

Key use cases: debug API calls from local dev servers, capture LLM API request/response pairs for eval datasets, mock endpoints without touching application code, inject CORS headers during frontend development, add artificial latency for resilience testing, and block telemetry during focused work.

---

## Structure

```
proxelar/
  SKILL.md                          # Usage guide: modes, CLI, Lua scripting, agent integration
  README.md                         # This file
  references/
    lua-scripting-api.md            # Complete Lua hook API reference with limitations
  scripts/
    log_to_jsonl.lua                # Log traffic as JSONL to ~/.proxelar/traffic.jsonl
    capture_for_eval.lua            # Capture LLM API calls (Anthropic/OpenAI/Gemini/OpenRouter)
    mock_api.lua                    # Template for mocking API endpoints
    inject_cors.lua                 # Reflect-based CORS injection with credential support
    latency_inject.lua              # Configurable artificial latency per URL pattern
    block_telemetry.lua             # Block analytics/tracking domains
    frametime_bench.js              # Browser frametime percentile measurement (p50-p99.9)
```

---

## Prerequisites

```bash
brew install proxelar
```

For HTTPS interception, trust the auto-generated CA certificate (one-time):

```bash
# Run proxelar once to generate the cert, then:
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain \
  ~/.proxelar/proxelar-ca.pem
```

Without CA trust, the proxy still works for HTTP traffic and HTTPS with `--insecure` / `NODE_TLS_REJECT_UNAUTHORIZED=0`.

---

## Quick Start

```bash
# Forward proxy (intercept outbound traffic)
proxelar

# Reverse proxy (inspect traffic to a local dev server)
proxelar -m reverse --target http://localhost:3000

# Web GUI for agent-visible inspection
proxelar -i gui

# With Lua hooks
proxelar --script ~/.claude/skills/proxelar/scripts/log_to_jsonl.lua

# Combined: reverse + GUI + logging
proxelar -m reverse --target http://localhost:3000 -i gui \
  --script ~/.claude/skills/proxelar/scripts/log_to_jsonl.lua
```

Configure clients to use `http://127.0.0.1:8080` as their HTTP/HTTPS proxy.

---

## Bundled Scripts

| Script | What it does |
|--------|-------------|
| `log_to_jsonl.lua` | Appends every request/response as a JSON line to `~/.proxelar/traffic.jsonl` with timestamps, method, URL, status, and response headers |
| `capture_for_eval.lua` | Filters for LLM API domains (Anthropic, OpenAI, Gemini, OpenRouter) and writes captures to `~/.proxelar/llm_captures.jsonl` for eval pipelines |
| `mock_api.lua` | Editable mock table---add method + URL pattern + response body to short-circuit requests without hitting the real server |
| `inject_cors.lua` | Reflects the `Origin` header, echoes `Access-Control-Request-Headers/Method`, sets `Allow-Credentials: true`. Handles OPTIONS preflight |
| `latency_inject.lua` | Adds configurable delay (in ms) to requests matching URL patterns. Edit the `rules` table |
| `block_telemetry.lua` | Returns 204 for requests matching analytics/tracking domain patterns (Google Analytics, Segment, Mixpanel, Hotjar, etc.) |
| `frametime_bench.js` | Injectable browser script that reports frame time percentiles (p50/p95/p99/p99.9) every ~16s. Read via `read_console_messages` with pattern `FRAMETIME` |

---

## Agent Integration

### With agent-browser

Route browser automation through Proxelar for combined page rendering + network visibility:

```bash
proxelar -m reverse --target http://localhost:3000 -i gui &
agent-browser --proxy "http://127.0.0.1:8080" open http://127.0.0.1:8080
agent-browser snapshot
```

### With Claude-in-Chrome

Start Proxelar with `-i gui`, then screenshot `http://localhost:8081` via `mcp__claude-in-chrome__computer` to give the agent network-layer visibility.

### Frametime + Network Correlation

Inject `frametime_bench.js` into a page, run `latency_inject.lua` on the proxy, and correlate network latency spikes with rendering frame drops.

---

## Lua API Summary

Two hooks: `on_request(request)` and `on_response(request, response)`.

- `on_request` receives: `request.method`, `request.url`, `request.headers` (table), `request.body` (string)
- `on_response` receives: `request.method`, `request.url` (headers/body are nil in this callback), `response.status`, `response.headers` (writable table), `response.body`
- Return the object to forward it (modified or not), return a response table from `on_request` to mock, return nil to pass through unchanged

Proxelar embeds Lua 5.4 in safe mode---standard library only, no C module loading. `io.open`, `os.getenv`, `os.date`, `print` all work. See `references/lua-scripting-api.md` for the full reference.

---

## Limitations

- Lua scripts load once at startup; edits require proxy restart
- `request.headers` and `request.body` are nil in `on_response`---use `on_request` to capture those
- WebSocket traffic passes through but Lua hooks only fire on HTTP request/response, not WS frames
- No C module loading (cjson, etc.)---use string manipulation for JSON transforms
- TUI and Web GUI support interactive request editing and dropping beyond what Lua hooks provide
