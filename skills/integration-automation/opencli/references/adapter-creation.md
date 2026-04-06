# Creating Custom OpenCLI Adapters

Create adapters for any website or your own applications. Adapters are placed in `~/.opencli/clis/<site>/<command>.ts` or `.yaml` and auto-register on save.

## Quick Path (4 Steps)

```bash
# 1. Open target page and inspect
opencli operate open https://example.com/page && opencli operate state

# 2. Discover APIs via network capture
opencli operate network                    # See JSON API requests
opencli operate network --detail 0         # Inspect first response body

# 3. Generate scaffold
opencli operate init mysite/mycommand      # Creates ~/.opencli/clis/mysite/mycommand.ts

# 4. Test
opencli operate verify mysite/mycommand
```

## One-Shot Generation

```bash
opencli generate https://example.com --goal "hot posts"   # explore + synthesize + register
```

## Full Exploration Workflow

For complex sites, use the systematic 6-step browser exploration:

| Step | Action | What to Look For |
|------|--------|-----------------|
| 1. Navigate | `opencli operate open <url>` | Target page loads |
| 2. Initial capture | `opencli operate network` | JSON API endpoints, URL patterns |
| 3. Interact | `opencli operate click <N>` on tabs/buttons | Triggers lazy-loaded APIs |
| 4. Second capture | `opencli operate network` | New APIs triggered by interaction |
| 5. Verify API | `opencli operate eval "fetch('/api/endpoint', {credentials:'include'}).then(r=>r.json())"` | Confirm data structure |
| 6. Write adapter | Based on confirmed API | YAML or TS file |

Key insight: Many APIs are lazy-loaded — they only fire when the user clicks a tab, expands comments, or scrolls. If you don't interact with the page, you won't discover them.

## Authentication Strategy Tiers

Use `opencli cascade <api-url>` to auto-detect, or test manually:

```
fetch(url) works directly?                    → Tier 1: public   (YAML, browser: false)
fetch(url, {credentials:'include'}) works?    → Tier 2: cookie   (YAML, most common)
Adding Bearer/CSRF header works?              → Tier 3: header   (TS)
XHR/Store intercept needed?                   → Tier 4: intercept (TS)
DOM-only, no API available?                   → Tier 5: ui       (TS, last resort)
```

| Tier | Speed | Complexity | Examples |
|------|-------|-----------|----------|
| 1 public | ~1s | Minimal | HackerNews, V2EX, arXiv |
| 2 cookie | ~7s | Simple | Bilibili, Zhihu, Reddit |
| 3 header | ~7s | Medium | Twitter (ct0 + Bearer) |
| 4 intercept | ~10s | High | Xiaohongshu (Pinia + XHR) |
| 5 ui | ~15s+ | Highest | Legacy sites |

## YAML vs TypeScript

```
Pipeline needs embedded JS (evaluate step)?
  → Yes: Use TypeScript (.ts)
  → No: Pure declarative (navigate/fetch/map/limit)?
       → Yes: Use YAML (.yaml)
```

Rule of thumb: If YAML embeds more than 10 lines of JS, switch to TypeScript.

## YAML Adapter Template (Tier 1 — Public API)

```yaml
# ~/.opencli/clis/mysite/hot.yaml
site: mysite
name: hot
description: "Get hot posts from MySite"
domain: mysite.com
browser: false
columns: [title, url, score]
args:
  - name: limit
    type: int
    required: false
    default: 10
pipeline:
  - fetch:
      url: "https://api.mysite.com/hot?limit={{limit}}"
      method: GET
  - map:
      title: "item.title"
      url: "item.url"
      score: "item.score"
  - limit: "{{limit}}"
```

## YAML Adapter Template (Tier 2 — Cookie Auth)

```yaml
site: mysite
name: feed
description: "Get my feed (requires login)"
domain: mysite.com
browser: true
columns: [title, author, time]
pipeline:
  - navigate:
      url: "https://mysite.com/feed"
  - evaluate: |
      (async () => {
        const res = await fetch('/api/feed', { credentials: 'include' });
        const data = await res.json();
        return JSON.stringify(data.items);
      })()
  - map:
      title: "item.title"
      author: "item.author.name"
      time: "item.created_at"
  - limit: "{{limit}}"
```

## TypeScript Adapter Template

```typescript
// ~/.opencli/clis/mysite/search.ts
import type { CliAdapter } from '@jackwener/opencli/types';

const adapter: CliAdapter = {
  site: 'mysite',
  name: 'search',
  description: 'Search MySite',
  domain: 'mysite.com',
  browser: true,
  columns: ['title', 'url', 'snippet'],
  args: [
    { name: 'query', type: 'string', required: true, help: 'Search query' },
    { name: 'limit', type: 'int', required: false, default: 10, help: 'Max results' },
  ],
  func: async (page, kwargs) => {
    const query = encodeURIComponent(kwargs.query);
    const limit = kwargs.limit ?? 10;
    const payload = await page.evaluate(async (q: string, n: number) => {
      const res = await fetch(`/api/search?q=${q}&limit=${n}`, {
        credentials: 'include',
      });
      return res.json();
    }, query, limit);
    return (payload.data?.items || []).map((item: any) => ({
      title: item.title,
      url: item.url,
      snippet: item.excerpt,
    }));
  },
};

export default adapter;
```

## Discovery Heuristics

Before complex network interception, try these shortcuts:

1. **`.json` suffix trick**: Sites like Reddit serve clean JSON when you append `.json` to the URL (e.g., `/r/all.json`). Works with cookie auth.
2. **`__INITIAL_STATE__`**: SSR sites (React, Vue) often embed data in `window.__INITIAL_STATE__`. Use `page.evaluate('() => window.__INITIAL_STATE__')`.
3. **Active interaction**: Click tabs, expand sections, scroll — lazy-loaded APIs only fire on user interaction.
4. **Framework store access**: Vue + Pinia sites can have their store actions called directly, bypassing complex auth signatures.

## Creating Adapters for Your Own Apps

The same patterns work for any web application you build:

1. Run your app locally (e.g., `localhost:3000`)
2. `opencli operate open http://localhost:3000 && opencli operate network`
3. Identify your API endpoints
4. Write a YAML or TS adapter targeting your domain
5. `opencli operate init myapp/status` to scaffold

For Electron apps, opencli connects via CDP. See `docs/guide/electron-app-cli.md` in the opencli repo for the connection setup.

## Testing

```bash
opencli mysite mycommand --limit 3           # Quick test
opencli mysite mycommand --limit 3 -f json   # Verify JSON output structure
opencli mysite mycommand --limit 3 -v        # Verbose: see pipeline debug steps
```
