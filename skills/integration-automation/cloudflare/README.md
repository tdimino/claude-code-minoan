# Cloudflare

Manage Cloudflare infrastructure and build AI agents from the terminal: Pages deploys, Workers, KV, R2, D1, Queues, Vectorize, Hyperdrive, the full Agents SDK stack (Agent, AIChatAgent, Think, Voice, sub-agents, fibers, HITL, Code Mode), and budget web scraping via Browser Rendering.

**Last updated:** 2026-05-29 | **Agents SDK:** v0.13.2

---

## Why This Skill Exists

Cloudflare's platform spans a dozen services with different CLI patterns and config formats. The Agents SDK alone has evolved rapidly (v0.3 → v0.13 in 4 months) with layered agent classes, durable execution, sub-agents, voice, and Code Mode. This skill consolidates the Wrangler CLI reference, Pages deployment workflows, the full Agents SDK API surface, and a Python script for Browser Rendering---the budget alternative to Firecrawl for scraping, screenshots, and PDFs.

---

## Structure

```
cloudflare/
  SKILL.md                                 # Full usage guide
  README.md                                # This file
  references/
    wrangler-commands.md                   # Full Wrangler CLI command reference
    pages-config.md                        # _headers, _redirects, build presets
    browser-rendering-api.md               # Browser Rendering REST API reference
    agents-sdk-core.md                     # Agent base class, scheduling, fibers, HITL, workflows, observability, MCP
    agents-sdk-chat-voice.md               # AIChatAgent, Think, Voice, sub-agents, agent tools, chat recovery
    codemode.md                            # Code Mode, Dynamic Workers (open beta), sandbox security
  scripts/
    cf_browser.py                          # Browser Rendering CLI (scrape, crawl, screenshot, PDF)
```

---

## Quick Reference

### Platform Management (Wrangler)

```bash
wrangler pages deploy out --project-name mysite    # Deploy static site
wrangler deploy                                     # Deploy Worker
wrangler dev                                        # Local dev server
wrangler tail my-worker                             # Stream live logs
wrangler kv namespace list                          # List KV namespaces
wrangler r2 bucket list                             # List R2 buckets
wrangler d1 list                                    # List D1 databases
wrangler secret put API_KEY                         # Set encrypted secret
```

### Agents SDK

```bash
# Scaffold a new agent project
npx create-cloudflare@latest --template cloudflare/agents-starter

# Install packages individually
npm install agents @cloudflare/ai-chat @cloudflare/think @cloudflare/voice @cloudflare/codemode
```

| Class | Package | Purpose |
|-------|---------|---------|
| `Agent` | `agents` | Base: state, scheduling, fibers, sub-agents, RPC, MCP |
| `AIChatAgent` | `@cloudflare/ai-chat` | Chat: persistence, streaming, tool approval |
| `Think` | `@cloudflare/think` | Opinionated chat: full agentic loop, extensions |
| `withVoice(Agent)` | `@cloudflare/voice` | Mixin: real-time STT/TTS over WebSocket (beta) |

### Browser Rendering (cf_browser.py)

```bash
python3 cf_browser.py markdown https://example.com              # Page → markdown
python3 cf_browser.py markdown https://example.com --no-render  # Free static fetch
python3 cf_browser.py crawl https://docs.example.com --limit 50 # Multi-page crawl
python3 cf_browser.py screenshot https://example.com -o page.png
python3 cf_browser.py pdf https://example.com -o page.pdf
python3 cf_browser.py json https://example.com --prompt "Extract prices"
```

### Scraping Tool Comparison

| Need | Best Tool |
|------|-----------|
| Clean markdown, reliable | Firecrawl |
| Cheap/free JS-rendered scrape | `cf_browser.py` (free 10 min/day) |
| Free static fetch | `cf_browser.py --no-render` (free during beta) |
| Anti-bot bypass | Scrapling |
| Twitter/X | Jina |

---

## Setup

### Prerequisites

- `npm install -g wrangler` + `wrangler login` (platform management)
- Python 3.9+ and `requests` (Browser Rendering script)
- `CLOUDFLARE_ACCOUNT_ID` + `CLOUDFLARE_API_TOKEN` in `~/.config/env/secrets.env`

---

## Related Skills

- **`firecrawl`**: Higher-quality markdown extraction, web search + scrape.
- **`scrapling`**: Local anti-bot scraping without API keys.

---

## Requirements

- Node.js + Wrangler CLI (platform management)
- Python 3.9+ + `requests` (Browser Rendering)
- Cloudflare account with API token

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/cloudflare ~/.claude/skills/
```
