# Firecrawl Interact API Reference

Interact allows you to take actions on a previously scraped page—click buttons, fill forms, extract dynamic content, or navigate deeper. Two modes: AI prompts (natural language) and code execution (Node.js/Python/Bash).

**API version:** v2
**Docs:** https://docs.firecrawl.dev/features/interact

---

## Lifecycle

1. **Scrape** — `POST /v2/scrape` returns a `scrapeId` in `data.metadata.scrapeId`
2. **Interact** — `POST /v2/scrape/{scrapeId}/interact` with `prompt` or `code`
3. **Stop** — `DELETE /v2/scrape/{scrapeId}/interact` when done

Sessions auto-expire after 10 min total or 5 min inactivity.

---

## Execute Interact

```
POST /v2/scrape/{scrapeId}/interact
```

### Request Body

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `prompt` | string | — | Natural language task for AI agent. Max 10,000 chars. Required if `code` not set. |
| `code` | string | — | Code to execute. Max 100,000 chars. Required if `prompt` not set. |
| `language` | string | `"node"` | `"node"`, `"python"`, or `"bash"`. Only used with `code`. |
| `timeout` | number | `30` | Timeout in seconds (1–300). |
| `origin` | string | — | Caller identifier for activity tracking. |

`prompt` and `code` are **mutually exclusive**—provide one, not both.

### Response Fields

| Field | Mode | Description |
|-------|------|-------------|
| `success` | Both | `true` if execution completed without errors |
| `liveViewUrl` | Both | Read-only live view URL for browser session |
| `interactiveLiveViewUrl` | Both | Interactive live view URL (viewers can control browser) |
| `output` | Prompt | AI agent's natural language answer |
| `stdout` | Code | Standard output from code execution |
| `stderr` | Code | Standard error output |
| `result` | Code | Raw return value from sandbox |
| `exitCode` | Code | Exit code (0 = success) |
| `killed` | Code | `true` if terminated due to timeout |

---

## Stop Interact

```
DELETE /v2/scrape/{scrapeId}/interact
```

Stops the browser session and releases resources. If using a persistent profile with `saveChanges=true` (default), browser state is saved before the session ends.

---

## Code Execution Languages

### Node.js (default)

Implicit `page` variable — a Playwright Page object. Full async/await support.

```javascript
// Get page title
const title = await page.title();
console.log(title);

// Click a button
await page.click('.load-more');
await page.waitForTimeout(2000);

// Extract text content
const text = await page.locator('.content').textContent();
console.log(text);
```

### Python

Playwright Python API. Set `language: "python"`.

```python
# Navigate and extract
title = await page.title()
print(title)

content = await page.locator('.main').text_content()
print(content)
```

### Bash (agent-browser)

Pre-installed CLI with 60+ commands. Uses element refs (`@e1`, `@e2`).

```bash
snapshot            # Get current page snapshot
click @e3           # Click element ref
fill @e5 "search"   # Fill input field
get text @e1        # Extract text content
get url             # Get current URL
```

---

## Persistent Profiles

Pass on the initial **scrape** call (not on interact):

| Parameter | Default | Description |
|-----------|---------|-------------|
| `profile.name` | — | Named profile. Scrapes with same name share browser state (cookies, localStorage). |
| `profile.saveChanges` | `true` | Save browser state when session stops. Set to `false` for read-only sessions. |

**Profile workflow:**
```
scrape(url, profile={"name": "my-app"})  → scrapeId (state saved)
interact(scrapeId, prompt="...")          → actions in session
interact_stop(scrapeId)                  → state persisted to profile
# Later:
scrape(other_url, profile={"name": "my-app"})  → cookies/storage restored
```

---

## Pricing

| Mode | Cost |
|------|------|
| Code-only (no `prompt`) | 2 credits per session minute |
| AI prompts | 7 credits per session minute |
| Initial scrape | Billed separately (standard scrape rates) |

---

## CLI Usage

```bash
SCRIPT=~/.claude/skills/firecrawl/scripts/firecrawl_api.py

# Step 1: Scrape and get the scrapeId
python3 $SCRIPT scrape "https://example.com/pricing" --json | python3 -c "
import sys, json
d = json.load(sys.stdin)
print(d.get('data', {}).get('metadata', {}).get('scrapeId', 'NOT FOUND'))
"

# Step 2: Interact with AI prompt
python3 $SCRIPT interact SCRAPE_ID --prompt "Click the 'Enterprise' tab"

# Step 3: Interact with code
python3 $SCRIPT interact SCRAPE_ID --code "const text = await page.locator('.pricing-table').textContent(); console.log(text);"

# Step 4: Stop the session
python3 $SCRIPT interact-stop SCRAPE_ID
```

### CLI Parameters

#### `interact`

| Parameter | Description |
|-----------|-------------|
| `scrape_id` | Scrape ID from a prior scrape (positional, required) |
| `-p, --prompt` | Natural language task (mutually exclusive with --code) |
| `-c, --code` | Code to execute (mutually exclusive with --prompt) |
| `-l, --language` | Code language: node, python, bash (default: node) |
| `-t, --timeout` | Timeout in seconds, 1-300 (default: 30) |
| `--origin` | Caller identifier |
| `--json` | Output raw JSON |

#### `interact-stop`

| Parameter | Description |
|-----------|-------------|
| `scrape_id` | Scrape ID of the session to stop (positional, required) |

---

## Actions vs. Interact

| Need | Use | Why |
|------|-----|-----|
| Click/wait before a single scrape | `--actions` on scrape | Fire-and-forget, no session overhead |
| Multiple interactions with same page | `interact` | Persistent session, back-and-forth |
| Fill forms, log in, navigate | `interact` | Stateful, multi-step |
| Simple "wait for JS to load" | `--actions` with `wait` | Cheaper, no session |

---

## Important Notes

- **Interact does NOT return page content.** The response contains `output` (prompt mode) or `stdout` (code mode), not the page's markdown/HTML. To get updated page content after interacting, use code mode to extract specific elements, or issue a follow-up scrape.
- **Sessions are server-side.** No local state to manage. The browser runs on Firecrawl's infrastructure.
- **First interact call may be slower** as the session resumes from the scrape snapshot.
- **Do not parallelize** interact calls on the same scrapeId. Calls are sequential per session.
- **SDK does not yet support interact.** The Python wrapper uses direct HTTP via `requests`.
