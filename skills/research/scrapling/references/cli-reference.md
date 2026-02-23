# Scrapling CLI Reference

## extract -- Content Extraction

Extract web content to file. Three fetcher tiers: `get` (HTTP), `fetch` (Playwright), `stealthy-fetch` (Patchright).

### get -- HTTP Fetch

Fast HTTP request with TLS fingerprint impersonation via curl_cffi. No JavaScript rendering.

```bash
scrapling extract get URL OUTPUT [options]
```

| Option | Description |
|--------|-------------|
| `--css-selector SELECTOR` | CSS selector for targeted extraction |
| `--impersonate BROWSER` | Browser to impersonate (chrome, firefox, safari) |
| `--timeout SECONDS` | Request timeout |
| `--method METHOD` | HTTP method (default: GET) |

**Supported HTTP methods:** `get`, `post`, `put`, `delete`

```bash
# Basic markdown extraction
scrapling extract get 'https://example.com' output.md

# With CSS selector
scrapling extract get 'https://example.com' output.md --css-selector '.main-content'

# With browser impersonation
scrapling extract get 'https://example.com' output.md --impersonate chrome

# Plain text output
scrapling extract get 'https://example.com' output.txt

# HTML output
scrapling extract get 'https://example.com' output.html

# POST request
scrapling extract post 'https://api.example.com/data' output.json
```

### fetch -- Dynamic Fetch (Playwright)

Launches Playwright Chromium for JavaScript-rendered pages. Medium stealth.

```bash
scrapling extract fetch URL OUTPUT [options]
```

| Option | Description |
|--------|-------------|
| `--css-selector SELECTOR` | CSS selector for targeted extraction |
| `--no-headless` | Show browser window (debugging) |
| `--network-idle` | Wait for network idle before extraction |
| `--timeout SECONDS` | Page load timeout |

```bash
# JS-rendered page
scrapling extract fetch 'https://spa-app.com' output.md

# Wait for network idle
scrapling extract fetch 'https://spa-app.com' output.md --network-idle

# Visible browser for debugging
scrapling extract fetch 'https://spa-app.com' output.md --no-headless
```

### stealthy-fetch -- Stealth Fetch (Patchright)

Maximum stealth via Patchright (patched Playwright). Built-in Cloudflare solver, canvas fingerprint noise, WebRTC leak prevention.

```bash
scrapling extract stealthy-fetch URL OUTPUT [options]
```

| Option | Description |
|--------|-------------|
| `--css-selector SELECTOR` | CSS selector for targeted extraction |
| `--solve-cloudflare` | Enable Cloudflare Turnstile solver |
| `--no-headless` | Show browser window (debugging) |
| `--network-idle` | Wait for network idle |
| `--hide-canvas` | Add canvas fingerprint noise |
| `--block-webrtc` | Prevent WebRTC IP leaks |
| `--real-chrome` | Use installed Chrome instead of Chromium |
| `--timeout SECONDS` | Page load timeout |

```bash
# Stealth with Cloudflare bypass
scrapling extract stealthy-fetch 'https://protected.site' output.md --solve-cloudflare

# Maximum stealth
scrapling extract stealthy-fetch 'https://site.com' output.md \
  --solve-cloudflare --hide-canvas --block-webrtc

# Use real Chrome browser
scrapling extract stealthy-fetch 'https://site.com' output.md --real-chrome

# With CSS selector
scrapling extract stealthy-fetch 'https://site.com' output.md --css-selector '#content'
```

## Output Formats

Determined by the output file extension:

| Extension | Format |
|-----------|--------|
| `.md` | Markdown (default) |
| `.txt` | Plain text |
| `.html` | Raw HTML |

## shell -- Interactive Shell

```bash
scrapling shell
```

IPython-based interactive shell with auto-imports. Supports converting curl commands to Scrapling requests.

## install -- Browser Setup

```bash
scrapling install
```

Downloads Chromium and installs system dependencies for Playwright/Patchright fetchers.
