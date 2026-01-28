# Firecrawl Page Actions Reference

Page actions allow you to interact with dynamic content before scraping. This is essential for pages that require clicks, scrolling, or form input to reveal content.

## Overview

Actions are specified as a JSON array in the `actions` parameter of the scrape endpoint. They execute sequentially before content extraction begins.

## Available Actions

### 1. Click

Click an element on the page.

```json
{
  "type": "click",
  "selector": "#load-more-button"
}
```

**Parameters:**
- `selector` (required): CSS selector for the element to click

**Use cases:**
- Load more buttons
- Expand/collapse sections
- Tab navigation
- Accept cookie banners

### 2. Write (Type)

Type text into an input field.

```json
{
  "type": "write",
  "selector": "#search-input",
  "text": "search query"
}
```

**Parameters:**
- `selector` (required): CSS selector for the input element
- `text` (required): Text to type

**Use cases:**
- Search forms
- Login forms (username only - never automate passwords)
- Filter inputs

### 3. Wait

Wait for a specified amount of time.

```json
{
  "type": "wait",
  "milliseconds": 2000
}
```

**Parameters:**
- `milliseconds` (required): Time to wait in milliseconds

**Use cases:**
- Wait for AJAX content to load
- Allow animations to complete
- Rate limiting between actions

### 4. Scroll

Scroll the page in a direction.

```json
{
  "type": "scroll",
  "direction": "down",
  "amount": 500
}
```

**Parameters:**
- `direction` (required): "up", "down", "left", or "right"
- `amount` (optional): Pixels to scroll (default varies)

**Use cases:**
- Infinite scroll pages
- Lazy-loaded images
- Reveal below-the-fold content

### 5. Screenshot

Take a screenshot during the action sequence.

```json
{
  "type": "screenshot"
}
```

**Parameters:** None

**Use cases:**
- Debug action sequences
- Capture state before/after actions
- Document visual changes

### 6. Wait for Selector

Wait until an element appears on the page.

```json
{
  "type": "waitForSelector",
  "selector": ".loaded-content",
  "timeout": 5000
}
```

**Parameters:**
- `selector` (required): CSS selector to wait for
- `timeout` (optional): Maximum wait time in milliseconds

**Use cases:**
- Wait for dynamic content to load
- Ensure element exists before clicking
- Handle asynchronous page updates

## Example Sequences

### Load More Content

```json
[
  {"type": "scroll", "direction": "down", "amount": 1000},
  {"type": "wait", "milliseconds": 1000},
  {"type": "click", "selector": "#load-more"},
  {"type": "wait", "milliseconds": 2000}
]
```

### Search and Extract

```json
[
  {"type": "write", "selector": "#search", "text": "python tutorials"},
  {"type": "click", "selector": "#search-button"},
  {"type": "waitForSelector", "selector": ".search-results"},
  {"type": "wait", "milliseconds": 1000}
]
```

### Infinite Scroll (3 pages)

```json
[
  {"type": "scroll", "direction": "down", "amount": 2000},
  {"type": "wait", "milliseconds": 1500},
  {"type": "scroll", "direction": "down", "amount": 2000},
  {"type": "wait", "milliseconds": 1500},
  {"type": "scroll", "direction": "down", "amount": 2000},
  {"type": "wait", "milliseconds": 1500}
]
```

### Accept Cookies and Expand Sections

```json
[
  {"type": "click", "selector": "#accept-cookies"},
  {"type": "wait", "milliseconds": 500},
  {"type": "click", "selector": ".expand-all"},
  {"type": "wait", "milliseconds": 1000}
]
```

## CLI Usage

Pass actions as a JSON string:

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" \
  --actions '[{"type": "click", "selector": "#load-more"}, {"type": "wait", "milliseconds": 2000}]'
```

## Python SDK Usage

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-YOUR_API_KEY")

result = app.scrape_url(
    "https://example.com",
    params={
        "formats": ["markdown"],
        "actions": [
            {"type": "click", "selector": "#load-more"},
            {"type": "wait", "milliseconds": 2000}
        ]
    }
)
```

## Best Practices

1. **Use waits after clicks** - Dynamic content needs time to load
2. **Be specific with selectors** - Use IDs over classes when possible
3. **Test incrementally** - Build action sequences step by step
4. **Handle failures gracefully** - Actions may fail on changed pages
5. **Avoid authentication** - Never automate password entry
6. **Respect rate limits** - Add waits between rapid actions
7. **Use screenshot for debugging** - Insert screenshots to verify state

## Limitations

- Actions execute in browser context (Playwright)
- Some anti-bot protections may block automated actions
- Complex JavaScript interactions may not work
- Actions add to scrape time and credit cost
- Maximum action sequence length may be limited
