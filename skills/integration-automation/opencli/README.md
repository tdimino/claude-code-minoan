# opencli

Universal CLI for 80+ websites, desktop apps, and browser automation via Chrome session reuse.

Wraps [jackwener/opencli](https://github.com/jackwener/opencli) (13.6K stars, Apache 2.0) as a Claude Code skill with integrated tool routing, security policy, and custom adapter creation guide.

## Install

```bash
npm install -g @jackwener/opencli
```

Then install the [Browser Bridge extension](https://github.com/jackwener/opencli/releases) in Chrome (`chrome://extensions` > Load unpacked).

```bash
opencli doctor    # Verify CLI + daemon + extension connectivity
```

## What It Does

- **80+ website adapters** -- Twitter, Reddit, YouTube, HackerNews, Instagram, Spotify, Amazon, Google, Wikipedia, and dozens more. Deterministic, structured output (JSON/YAML/CSV/table/markdown). Zero LLM cost.
- **Browser automation** -- `opencli operate` provides state-based element selection with `[N]` indices, command chaining with `&&`, and session persistence via a micro-daemon on `localhost:19825`.
- **CLI Hub** -- Register any local CLI (`opencli register mycli`) so AI agents can discover all tools via `opencli list`.
- **Custom adapters** -- Create YAML or TypeScript adapters for any website or your own apps. See `references/adapter-creation.md`.
- **Desktop app control** -- Cursor, Codex, ChatGPT, Notion, Discord via Chrome DevTools Protocol.

## Tool Routing

When multiple tools overlap, prefer opencli for supported sites:

| Task | Use | Over |
|------|-----|------|
| Twitter post/read/bookmarks | `opencli twitter` | bird CLI |
| Reddit/HN/YouTube data | `opencli <site>` | firecrawl |
| Browser multi-step workflow | `opencli operate` | agent-browser |
| General scraping (unknown sites) | firecrawl | opencli |
| Anti-bot / Cloudflare | scrapling | opencli |
| Twitter deep research | x-search | opencli |

## Security Policy

The skill includes a tiered security policy since opencli accesses authenticated browser sessions:

- **Blocked**: Banking, email, cloud consoles, password managers
- **Read-only**: Social media, news, forums (no write actions without user approval)
- **Full**: Developer tools, search engines (with confirmation for destructive actions)

## Structure

```
opencli/
├── SKILL.md                     # Main skill (auto-loaded when triggered)
├── references/
│   └── adapter-creation.md      # Creating custom adapters (English, from Chinese upstream)
└── README.md
```

## How It Works

OpenCLI runs a micro-daemon (`localhost:19825`) that bridges CLI commands to a Chrome extension via WebSocket. The extension controls browser tabs using the Chrome DevTools Protocol. Your existing Chrome login sessions are reused -- no API keys needed for most sites.

```
CLI command → HTTP → daemon → WebSocket → Chrome extension → browser tab
```

The daemon auto-spawns on first browser command and auto-exits after 4 hours of idle.

## Quick Start

```bash
opencli list                               # See all 80+ adapters
opencli hackernews top --limit 5 -f json   # Public API (no browser needed)
opencli twitter trending --limit 10        # Browser command (needs Chrome + login)
opencli operate open https://example.com   # Browser automation
opencli operate state                      # Inspect page with element indices
```

## Prerequisites

- Node.js >= 20
- Chrome/Chromium running and logged into target sites
- Browser Bridge extension installed
