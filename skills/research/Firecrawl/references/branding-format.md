# Firecrawl Branding Format Reference

The `branding` format extracts brand identity elements from a webpage, including colors, fonts, typography, and UI components. This is useful for design analysis, competitive research, and brand audits.

## Overview

When you include `branding` in the formats array, Firecrawl analyzes the page's CSS and visual elements to extract brand-related information.

## Usage

### CLI

```bash
python3 ~/.claude/skills/Firecrawl/scripts/firecrawl_api.py scrape "https://example.com" --formats branding
```

### Python

```python
from firecrawl import FirecrawlApp

app = FirecrawlApp(api_key="fc-YOUR_API_KEY")

result = app.scrape_url(
    "https://stripe.com",
    params={"formats": ["branding"]}
)

print(result["data"]["branding"])
```

## Output Structure

The branding format returns a structured object with the following sections:

### Colors

```json
{
  "colors": {
    "primary": ["#635BFF", "#0A2540"],
    "secondary": ["#00D4FF", "#7A73FF"],
    "background": ["#FFFFFF", "#F6F9FC"],
    "text": ["#425466", "#0A2540"],
    "accent": ["#FF5E62", "#00D4FF"]
  }
}
```

### Typography

```json
{
  "typography": {
    "fonts": {
      "heading": "Inter, system-ui, sans-serif",
      "body": "Inter, system-ui, sans-serif",
      "monospace": "Menlo, Monaco, monospace"
    },
    "sizes": {
      "h1": "48px",
      "h2": "36px",
      "h3": "24px",
      "body": "16px",
      "small": "14px"
    },
    "weights": ["400", "500", "600", "700"]
  }
}
```

### UI Components

```json
{
  "components": {
    "buttons": {
      "borderRadius": "6px",
      "padding": "12px 24px",
      "primaryColor": "#635BFF",
      "textColor": "#FFFFFF"
    },
    "cards": {
      "borderRadius": "8px",
      "shadow": "0 2px 8px rgba(0,0,0,0.08)",
      "padding": "24px"
    },
    "inputs": {
      "borderRadius": "4px",
      "borderColor": "#E3E8EE",
      "focusColor": "#635BFF"
    }
  }
}
```

### Logo

```json
{
  "logo": {
    "url": "https://example.com/logo.svg",
    "type": "svg",
    "colors": ["#635BFF", "#FFFFFF"]
  }
}
```

## Use Cases

### 1. Competitive Design Analysis

```python
competitors = [
    "https://stripe.com",
    "https://square.com",
    "https://paypal.com"
]

brands = []
for url in competitors:
    result = app.scrape_url(url, params={"formats": ["branding"]})
    brands.append({
        "url": url,
        "branding": result["data"]["branding"]
    })

# Compare color palettes, typography choices, etc.
```

### 2. Design System Documentation

Extract branding from your own site to document the design system:

```python
result = app.scrape_url(
    "https://your-site.com",
    params={"formats": ["branding", "screenshot"]}
)

# Generate design tokens from extracted branding
branding = result["data"]["branding"]
```

### 3. Brand Consistency Audit

Check if different pages maintain consistent branding:

```python
pages = [
    "https://example.com",
    "https://example.com/about",
    "https://example.com/pricing"
]

brandings = [
    app.scrape_url(url, params={"formats": ["branding"]})["data"]["branding"]
    for url in pages
]

# Compare for consistency
```

## Combining with Other Formats

Branding works well with other formats:

```bash
# Get branding + screenshot for visual reference
python3 firecrawl_api.py scrape "https://example.com" --formats branding screenshot

# Get branding + markdown for full context
python3 firecrawl_api.py scrape "https://example.com" --formats branding markdown
```

## Limitations

- Branding extraction works best on well-structured modern websites
- Inline styles and CSS-in-JS may not be fully captured
- Dynamic themes (dark mode) may only show current state
- Logo detection requires common patterns (img, svg with logo-related classes)
- Results may vary based on page complexity

## Best Practices

1. **Scrape homepage** - Usually has the most complete brand representation
2. **Check multiple pages** - Verify consistency across the site
3. **Combine with screenshot** - Visual verification of extracted colors
4. **Use for inspiration** - Extract patterns from sites you admire
5. **Respect copyright** - Don't copy brand assets, use for analysis only
