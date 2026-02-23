# Adaptive Element Tracking

Scrapling's signature feature. Elements are fingerprinted and stored in SQLite. When a page redesigns and CSS selectors break, Scrapling relocates elements via similarity scoring -- no AI, no LLM calls.

## How It Works

### Save Phase

When `auto_save=True`, Scrapling serializes the first matched element's fingerprint to SQLite:

- Tag name, text content, all attributes (names + values)
- DOM path (tag names of ancestors)
- Sibling tag names
- Parent's tag name, attributes, and text

Storage key: `(domain, identifier)` where identifier defaults to the CSS/XPath selector string.

### Match Phase

When `adaptive=True` and the selector finds nothing, Scrapling:

1. Retrieves the stored fingerprint from SQLite
2. Iterates every element in the current page
3. Computes a similarity score using `SequenceMatcher` on:
   - Tag name (exact match = 1 point)
   - Text content (ratio)
   - Attributes as key/value tuples (ratio)
   - High-signal attributes individually: `class`, `id`, `href`, `src` (ratio each)
   - DOM path (ratio)
   - Parent: tag name, attributes, text (ratio each)
   - Siblings (ratio)
4. Returns element(s) with the highest composite score

## Usage

### CSS/XPath Way (Recommended)

```python
from scrapling.fetchers import Fetcher

Fetcher.adaptive = True
page = Fetcher.get('https://example.com')

# First run: save fingerprint
products = page.css('.product-list', auto_save=True)

# After site redesign: auto-relocate
products = page.css('.product-list', adaptive=True)

# XPath works too
items = page.xpath('//div[@class="items"]', auto_save=True)
items = page.xpath('//div[@class="items"]', adaptive=True)
```

### Manual Way

```python
page = Fetcher.get('https://example.com')
element = page.css('.product-list').first

# Save with custom identifier
page.save(element, 'my_products')

# Later: retrieve and relocate
data = page.retrieve('my_products')
relocated = page.relocate(data, selector_type=True)
```

### Domain Scoping

Fingerprints are scoped to domain by default. Override with `adaptive_domain`:

```python
# Share fingerprints across subdomains
page.css('.product', auto_save=True, adaptive_domain='example.com')
```

## Storage Backend

Default: `SQLiteStorageSystem` (thread-safe, WAL mode, `RLock` for reentrancy).

The storage file is `elements_storage.db` in the Scrapling package directory by default. Upgrading or reinstalling scrapling wipes this database since it lives inside site-packages. Back up fingerprints before upgrades, or use a custom backend for long-running projects.

Custom backend: implement `save()` and `retrieve()` methods on the `StorageSystemMixin` ABC.

## When to Use Adaptive Mode

- Monitoring pages that redesign periodically
- Scraping sites with A/B testing that changes class names
- Long-running scraping projects where selectors may break
- When the target element's content and structure are more stable than its CSS classes

## Limitations

- The match phase iterates every element, so performance scales with page size
- Works best when the element's content/structure is distinctive
- Identical elements (e.g., multiple buttons with the same text) may match incorrectly
- Similarity scoring is heuristic -- not guaranteed to find the correct element after major redesigns
