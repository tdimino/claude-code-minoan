# Obscura

Stealth headless browser with CDP server for anti-fingerprint browsing, parallel scraping, and low-memory automation. Fills the gap between Lightpanda (CDP, no stealth) and Scrapling (stealth, no CDP).

**Last updated:** 2026-04-25

**Reflects:** [h4ckf0r0day/obscura](https://github.com/h4ckf0r0day/obscura) --- Rust headless browser, V8 JS engine, 57MB binary, 30MB RAM.

---

## Why This Skill Exists

Academic and research sites (JSTOR, Google Scholar, Persée, PubMed, Academia.edu) detect headless browsers via canvas/WebGL fingerprinting---not Cloudflare Turnstile. Lightpanda has no anti-fingerprinting. Scrapling handles Cloudflare but has no CDP server. Obscura provides both: stealth browsing with a CDP WebSocket server for Puppeteer/Playwright integration.

---

## Structure

```
obscura/
  SKILL.md                                 # Tool selection, usage, gotchas
  README.md                                # This file
  references/
    cdp-coverage.md                        # CDP domain/method coverage table
  scripts/
    obscura_serve.sh                       # CDP server launcher with cleanup trap
    test_obscura.sh                        # 6 smoke tests (binary, checksum, fetch, stealth, CDP, ports)
    test_academic_sites.sh                 # 6 live academic site tests
    test_stealth_comparison.sh             # Stealth vs plain fingerprint comparison
  evals/
    evals.json                             # 10 trigger/no-trigger eval queries
```

---

## What It Covers

### Positioning

| Scenario | Tool |
|----------|------|
| Clean single-page markdown | Firecrawl |
| Cloudflare Turnstile bypass | Scrapling |
| Interactive CDP automation | agent-browser |
| **Stealth CDP automation** | **Obscura** |
| **Batch stealth scraping** | **Obscura** |
| **Low-RAM headless (30MB)** | **Obscura** |

### Key Capabilities

- **Anti-fingerprinting**: `navigator.webdriver = undefined`, canvas/audio/GPU randomization, tracker blocking (3,520 domains)
- **CDP server**: WebSocket on port 9224 for Puppeteer/Playwright (`ws://127.0.0.1:9224/devtools/browser`)
- **Parallel scraping**: `obscura scrape URL1 URL2 ... --concurrency N --format json`
- **Proxy chain**: `obscura --proxy http://127.0.0.1:8080 fetch/serve ...` (Proxelar defense-in-depth)

### Gotchas

- `--stealth` is off by default---pass it explicitly
- `--proxy` is a global flag---place before the subcommand, not after
- Port 9224 is convention, not default (binary defaults to 9222)
- `--quiet` suppresses the banner for piped output
- WebSocket path is `/devtools/browser` (differs from Lightpanda)
- Ad-hoc signed binary---SHA-256 at `~/tools/obscura/obscura.sha256`

### Test Suite

```bash
# Smoke tests (binary, stealth, CDP lifecycle)
bash ~/.claude/skills/obscura/scripts/test_obscura.sh

# Live academic site tests (requires internet)
bash ~/.claude/skills/obscura/scripts/test_academic_sites.sh

# Stealth fingerprint comparison
bash ~/.claude/skills/obscura/scripts/test_stealth_comparison.sh
```

---

## Requirements

- Obscura binary at `~/tools/obscura/obscura` (symlinked to `~/.local/bin/obscura`)
- No API keys required
- Optional: Proxelar on `:8080` for proxy chaining

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/obscura ~/.claude/skills/
```
