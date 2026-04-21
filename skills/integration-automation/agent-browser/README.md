# agent-browser

Headless browser automation from the command line. Navigate pages, interact with elements via snapshot refs, fill forms, take screenshots, record video, manage cookies/storage, intercept network requests, and run parallel sessions. Ships as a standalone binary for macOS ARM64.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Claude Code needs browser automation for testing web apps, filling forms, taking screenshots, and extracting data. `agent-browser` provides a CLI-first workflow: snapshot a page to get element refs (`@e1`, `@e2`), then interact using those refs. No Playwright/Puppeteer boilerplate---just shell commands.

---

## Structure

```
agent-browser/
  SKILL.md                              # Full command reference
  README.md                             # This file
  bin/
    agent-browser                       # CLI entry point
    agent-browser-darwin-arm64          # macOS ARM64 binary
  scripts/
    build-all-platforms.sh              # Cross-platform build script
    check-update.sh                     # Version check
    sync-repos.sh                       # Repo sync utility
```

---

## Core Workflow

```bash
agent-browser open https://example.com     # 1. Navigate
agent-browser snapshot -i                  # 2. Get interactive elements with refs
agent-browser fill @e1 "user@test.com"     # 3. Interact using refs
agent-browser click @e2                    # 4. Click buttons
agent-browser snapshot -i                  # 5. Re-snapshot after DOM changes
```

---

## Command Groups

| Group | Commands | Purpose |
|-------|----------|---------|
| Navigation | `open`, `back`, `forward`, `reload`, `close` | Page navigation |
| Snapshot | `snapshot -i`, `snapshot -c` | Element discovery with refs |
| Interaction | `click`, `fill`, `type`, `press`, `select`, `hover`, `drag` | DOM interaction |
| Information | `get text/html/value/attr/title/url/count/styles` | Data extraction |
| Screenshots | `screenshot`, `pdf` | Visual capture |
| Recording | `record start/stop/restart` | Video capture |
| Wait | `wait @ref`, `wait --text`, `wait --url`, `wait --load` | Synchronization |
| Semantic | `find role/text/label/placeholder/testid` | Locator-based interaction |
| Network | `network route/unroute/requests` | Request interception |
| State | `cookies`, `storage`, `state save/load` | Persistence |
| Tabs | `tab new/close`, `tab N` | Multi-tab management |
| Settings | `set viewport/device/geo/offline/media` | Browser configuration |

---

## Setup

### Prerequisites

- macOS ARM64 (binary included)
- No additional dependencies

### Global Options

| Option | Description |
|--------|-------------|
| `--session <name>` | Isolated browser session |
| `--json` | Machine-readable JSON output |
| `--headed` | Show browser window (not headless) |
| `--proxy <url>` | Route through proxy server |
| `--cdp <port>` | Connect via Chrome DevTools Protocol |

---

## Related Skills

- **`scrapling`**: Local web scraping with anti-bot bypass---for data extraction rather than UI interaction.
- **`cloudflare`**: Browser Rendering on Cloudflare's edge---headless Chrome without local binaries.

---

## Requirements

- macOS ARM64 (binary ships in `bin/`)
- No runtime dependencies

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/agent-browser ~/.claude/skills/
```
