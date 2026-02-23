# Scrapling Python API Reference

## Fetchers

### Fetcher -- HTTP Requests

Fast HTTP fetching with TLS fingerprint impersonation via curl_cffi. No JavaScript.

```python
from scrapling.fetchers import Fetcher, FetcherSession, AsyncFetcher

# One-shot request
page = Fetcher.get('https://example.com', impersonate='chrome')
page = Fetcher.post('https://api.example.com/data', data={'key': 'value'})

# Session (keeps cookies, connection pool)
with FetcherSession(impersonate='chrome', http3=True) as session:
    page1 = session.get('https://example.com/page1')
    page2 = session.get('https://example.com/page2')

# Async
page = await AsyncFetcher.get('https://example.com')
```

**Parameters:** `impersonate` (chrome, firefox, safari), `timeout`, `proxy`, `headers`, `cookies`, `follow_redirects`, `http3`

### DynamicFetcher -- Playwright

Launches Playwright Chromium for JavaScript-rendered pages.

```python
from scrapling.fetchers import DynamicFetcher, DynamicSession, AsyncDynamicSession

page = DynamicFetcher.fetch('https://spa-app.com', headless=True, network_idle=True)

# Session
async with AsyncDynamicSession(headless=True) as session:
    page = await session.fetch('https://spa-app.com')
```

**Parameters:** `headless`, `network_idle`, `timeout`, `proxy`, `page_action` (callable)

### StealthyFetcher -- Patchright (Maximum Stealth)

Patched Playwright with anti-detection bypasses.

```python
from scrapling.fetchers import StealthyFetcher, StealthySession, AsyncStealthySession

page = StealthyFetcher.fetch('https://protected.site',
    headless=True,
    solve_cloudflare=True,
    hide_canvas=True,
    block_webrtc=True,
    google_search=True,      # Spoof Google referer (default: True)
)

# Real Chrome instead of Chromium
page = StealthyFetcher.fetch('https://site.com', real_chrome=True)

# Connect to existing browser via CDP
page = StealthyFetcher.fetch('https://site.com', cdp_url='http://localhost:9222')

# Page automation
def my_action(page):
    page.click('#login-button')
    page.fill('#username', 'user')
    page.fill('#password', 'pass')
    page.click('#submit')

page = StealthyFetcher.fetch('https://app.example.com', page_action=my_action)
```

**Parameters:** `headless`, `solve_cloudflare`, `hide_canvas`, `block_webrtc`, `google_search`, `real_chrome`, `cdp_url`, `network_idle`, `timeout`, `proxy`, `page_action`

**Stealth features injected on page creation:**
- `navigator_plugins.js` -- Spoof navigator.plugins
- `playwright_fingerprint.js` -- Hide Playwright detection
- `webdriver_fully.js` -- Remove webdriver flag
- `window_chrome.js` -- Fake window.chrome
- `screen_props.js` -- Spoof screen dimensions
- `notification_permission.js` -- Normalize notification API

## Response Object

All fetchers return a response with these properties:

```python
page.status          # HTTP status code
page.url             # Final URL (after redirects)
page.cookies         # Dict of cookies
page.headers         # Response headers
page.text            # Raw HTML text
page.json()          # Parse as JSON
```

The response is also a `Selector`, supporting all parsing methods below.

## Parser / Selector

```python
from scrapling.parser import Selector

page = Selector("<html>...</html>")
```

### CSS Selectors

Scrapy pseudo-elements supported:

```python
page.css('.product h2::text').getall()          # Text content
page.css('.product::attr(href)').get()           # Attribute value
page.css('.product').get_all_text()               # All text, cleaned
```

### XPath

```python
page.xpath('//div[@class="item"]')
page.xpath('//h1/text()').get()
```

### BeautifulSoup-Style

```python
page.find_all('div', class_='product')
page.find_all('div', {'data-id': '123'})
page.find('a', id='main-link')
```

### Text and Regex Search

```python
page.find_by_text('Add to Cart', partial=True)
page.find_by_regex(r'Price: \$\d+')
```

### Navigation

```python
el.parent / el.children / el.siblings
el.next / el.previous
el.iterancestors()
el.find_ancestor(lambda a: a.tag == 'section')
el.below_elements   # All descendants
```

### Similarity

```python
similar = el.find_similar(similarity_threshold=0.2)
```

### Text Processing

```python
el.text                                          # TextHandler object
el.text.clean()                                  # Cleaned text
el.text.re(r'\d+')                              # Regex extract
el.text.json()                                   # Parse as JSON
el.get_all_text(separator="\n", strip=True, ignore_tags=('script', 'style'))
```

## Adaptive Element Tracking

```python
from scrapling.fetchers import Fetcher

Fetcher.adaptive = True
page = Fetcher.get('https://example.com')

# Save element fingerprint (CSS way)
products = page.css('.product', auto_save=True)

# Later, relocate after site redesign
products = page.css('.product', adaptive=True)

# Manual save/retrieve/relocate
page.save(element, 'my_identifier')
data = page.retrieve('my_identifier')
relocated = page.relocate(data, selector_type=True)
```

## Spider Framework

Scrapy-like concurrent crawling with pause/resume and multi-session routing.

```python
from scrapling.spiders import Spider, Response, Request
from scrapling.fetchers import FetcherSession, AsyncStealthySession

class MySpider(Spider):
    name = "demo"
    start_urls = ["https://example.com/"]
    concurrent_requests = 10

    def configure_sessions(self, manager):
        manager.add("fast", FetcherSession(impersonate="chrome"))
        manager.add("stealth", AsyncStealthySession(headless=True), lazy=True)

    async def parse(self, response: Response):
        for link in response.css('a::attr(href)').getall():
            if "protected" in link:
                yield Request(link, sid="stealth")   # Route to stealth session
            else:
                yield Request(link, sid="fast")
        for item in response.css('.article'):
            yield {"title": item.css('h2::text').get(), "url": response.url}

# Start with pause/resume
result = MySpider().start(crawldir="./data")
result.items.to_json("output.json")
result.items.to_jsonl("output.jsonl")

# Streaming mode
async for item in MySpider().stream():
    print(item)
```

**Spider features:**
- Multi-session routing (mix HTTP and browser sessions)
- Pause/resume via `crawldir` (Ctrl+C saves state, restart resumes)
- Streaming with `async for item in spider.stream()`
- Blocked request auto-detection and retry
- Built-in export (`to_json`, `to_jsonl`)

## Proxy Rotation

```python
from scrapling.core import ProxyRotator

rotator = ProxyRotator([
    "http://proxy1:8080",
    "http://proxy2:8080",
    "socks5://proxy3:1080",
])

page = Fetcher.get('https://example.com', proxy=rotator.next())
```
