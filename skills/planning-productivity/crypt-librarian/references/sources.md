# Curated Sources for Film Discovery

URLs, tool documentation, and search strategies for film recommendations.

---

## Exa Direct API Script (Recommended)

The skill includes `scripts/exa_film_search.py` which provides direct access to all Exa endpoints without MCP limitations.

**Requirements:**
```bash
pip install requests
export EXA_API_KEY="your-api-key"
```

### Commands

| Command | Purpose | Example |
|---------|---------|---------|
| `search` | Find film lists, articles | `python scripts/exa_film_search.py search "gothic horror films" -n 10` |
| `contents` | Extract full content from URL | `python scripts/exa_film_search.py contents "https://letterboxd.com/list/..."` |
| `similar` | Find pages similar to URL | `python scripts/exa_film_search.py similar "https://letterboxd.com/film/eyes-wide-shut/"` |
| `research` | AI-synthesized answer with citations | `python scripts/exa_film_search.py research "best occult ritual films"` |

### Search Options

```bash
# Basic search
python scripts/exa_film_search.py search "gothic vampire films" -n 10

# Filter to specific domains
python scripts/exa_film_search.py search "occult cinema" --domains letterboxd.com criterion.com mubi.com

# Exclude domains
python scripts/exa_film_search.py search "horror films" --exclude reddit.com

# Output raw JSON
python scripts/exa_film_search.py search "noir films" --json
```

### Film Discovery Patterns

```bash
# Find curated lists
python scripts/exa_film_search.py search "Letterboxd list gothic horror essentials" -n 10

# Find similar films to a reference
python scripts/exa_film_search.py similar "https://letterboxd.com/film/interview-with-the-vampire/" -n 15

# Extract full content from a found list
python scripts/exa_film_search.py contents "https://letterboxd.com/user/list/gothic-romance/"

# Deep research on a theme
python scripts/exa_film_search.py research "What are the best films featuring secret societies and occult rituals?"
```

---

## MCP Tool Reference (Fallback)

### Exa MCP Server (4 Tools)

The Exa MCP server provides 4 complementary tools for film discovery (availability depends on config):

#### 1. Web Search (`mcp__exa__web_search_exa`)

Real-time web search with content extraction. Best for finding curated lists, articles, and recommendations.

**Parameters:**
- `query` (required): Search query string
- `numResults` (optional): Number of results to return (default: 5)

**Best for film discovery:**
- Finding curated lists on Letterboxd, MUBI, Criterion
- "Films like X" and "best of" queries
- Quick discovery of thematic lists

**Example invocations:**
```
mcp__exa__web_search_exa(query="Letterboxd list gothic vampire films pre-2010", numResults=10)
mcp__exa__web_search_exa(query="Criterion Collection occult horror essays", numResults=8)
mcp__exa__web_search_exa(query="site:sensesofcinema.com Neil Jordan gothic", numResults=5)
```

#### 2. Deep Search (`mcp__exa__deep_search_exa`)

Advanced search with query refinement and AI-generated summaries. Best for complex research requiring synthesized information.

**Parameters:**
- `query` (required): Search query string

**Best for film discovery:**
- Complex thematic research ("gothic sensibility in 1980s horror")
- Finding obscure connections between films/directors
- Research requiring synthesized critical discourse

**Example invocations:**
```
mcp__exa__deep_search_exa(query="gothic horror films with romantic sensibility 1980s 1990s critical analysis")
mcp__exa__deep_search_exa(query="films influenced by Eyes Wide Shut secret society ritual aesthetic")
mcp__exa__deep_search_exa(query="underrated historical epics psychological depth pre-2010")
```

#### 3. Crawling (`mcp__exa__crawling_exa`)

Extract full content from a specific URL. Alternative to Firecrawl for known URLs.

**Parameters:**
- `url` (required): The URL to crawl and extract content from

**Best for film discovery:**
- Extracting full content from Letterboxd lists
- Scraping Criterion essays and collection pages
- Getting complete film lists from known URLs

**Example invocations:**
```
mcp__exa__crawling_exa(url="https://letterboxd.com/user/list/gothic-horror-essentials/")
mcp__exa__crawling_exa(url="https://www.criterion.com/shop/collection/gothic-horror")
mcp__exa__crawling_exa(url="https://sensesofcinema.com/2020/great-directors/neil-jordan/")
```

#### 4. Code Context (`mcp__exa__get_code_context_exa`)

Search code snippets, docs, GitHub repos. **Not typically relevant for film discovery** — included for completeness.

**Parameters:**
- `query` (required): Search query
- `tokensNum` (optional): "dynamic" (default) or 1000-50000

### Perplexity Search (`mcp__perplexity__search`)

AI-powered search for synthesized information and critical discourse.

**Parameters:**
- `query` (required): The search query
- `detail_level` (optional): "brief", "normal", or "detailed" — use "detailed" for comprehensive film lists

**Strengths:**
- Synthesizes information from multiple sources
- Excellent for critical discourse and thematic analysis
- Good for "explain" and "compare" queries

**Example invocations:**
```
mcp__perplexity__search(query="gothic horror films romantic sensibility 1980s 1990s", detail_level="detailed")
mcp__perplexity__search(query="films influenced by Eyes Wide Shut secret society ritual aesthetic")
mcp__perplexity__search(query="revisionist noir movement 1970s Altman Polanski", detail_level="detailed")
```

### Perplexity Documentation (`mcp__perplexity__get_documentation`)

Retrieves documentation and detailed information about specific topics.

**Parameters:**
- `query` (required): The topic to get documentation for
- `context` (optional): Additional context to focus the search

**Example invocations:**
```
mcp__perplexity__get_documentation(query="Ken Russell filmography", context="gothic visionary films")
mcp__perplexity__get_documentation(query="Criterion Collection gothic horror", context="available titles streaming")
```

### Firecrawl (CLI)

Scrapes full page content when Exa/Perplexity find a promising URL.

**Usage:**
```bash
firecrawl scrape <url>
```

**When to use:** After Exa finds a valuable list or article, scrape it for complete content.

---

## Criterion Collection

### Curated Collections
- `https://www.criterion.com/shop/browse/list?sort=popularity` — Popular titles
- `https://www.criterion.com/current/posts/category/essays` — Critical essays

### Thematic Collections (scrape these for thematic searches)
- Gothic/Horror collection pages
- World Cinema collection pages
- Classic Hollywood collection pages

## MUBI

### Curated Lists
MUBI lists require browsing, but these patterns work:
- `https://mubi.com/lists/*` — User-created lists
- `https://mubi.com/notebook` — MUBI Notebook critical writing

### Search Patterns for Exa
- "site:mubi.com gothic horror list"
- "site:mubi.com noir classics"
- "site:mubi.com occult cinema"

## Letterboxd

### High-Value Lists (examples)
- `https://letterboxd.com/*/list/*/` — User lists
- Search for lists by theme: "gothic", "occult", "noir", "literary adaptations"

### Search Patterns for Exa
- "site:letterboxd.com list gothic horror"
- "site:letterboxd.com list eyes wide shut similar"
- "site:letterboxd.com list criterion collection"

## Critical Sources

### Senses of Cinema
- `https://www.sensesofcinema.com/` — Deep critical essays
- Great for auteur analysis and thematic explorations

### Bright Lights Film Journal
- `https://brightlightsfilm.com/` — Academic film criticism

### Film Comment
- `https://www.filmcomment.com/` — Lincoln Center publication

### Sight & Sound
- `https://www.bfi.org.uk/sight-and-sound` — BFI publication
- Historical lists and retrospectives

## Content Warning Resources

### DoesTheDogDie.com
- `https://www.doesthedogdie.com/` — Comprehensive trigger warnings
- Search by film title to verify content

### IMDb Parents Guide
- `https://www.imdb.com/title/[ID]/parentalguide` — Content breakdown
- Check "Frightening & Intense Scenes" and "Violence & Gore" sections

### Common Sense Media
- `https://www.commonsensemedia.org/` — Content ratings
- Useful for violence/disturbing content assessments

## Streaming Availability

### JustWatch
- `https://www.justwatch.com/` — Multi-platform availability checker
- Scrape to find where films are streaming

### Reelgood
- `https://reelgood.com/` — Alternative availability checker

## Specialty Sources

### Gothic/Horror Specific
- `https://bloody-disgusting.com/` — Horror coverage (filter for non-gore)
- `https://www.dreadcentral.com/` — Horror news and retrospectives

### Arthouse/Classic
- `https://www.rogerebert.com/` — Reviews archive (pre-2013 for Ebert himself)
- `https://www.vulture.com/` — Contemporary criticism

## Search Strategy Examples

### For Exa (`mcp__exa__web_search_exa`)

```
# Gothic/Occult
"Criterion Collection gothic horror films"
"best occult films 1970s 1980s"
"films like Eyes Wide Shut secret society"

# Literary
"literary adaptations Criterion Collection"
"Merchant Ivory films list"
"Pasolini trilogy of life films"

# Noir
"neo-noir films 1990s underrated"
"revisionist noir 1970s best films"
"Chinatown Long Goodbye similar films"

# Historical Epic
"historical epics psychological depth"
"Ridley Scott director's cut films"
"underrated historical epics 2000s"
```

### For Perplexity (`mcp__perplexity__search`)

```
# Discourse/Analysis
"Eyes Wide Shut occult symbolism analysis"
"gothic horror films romantic sensibility"
"revisionist noir movement 1970s"

# Recommendations
"films similar to Interview with the Vampire gothic atmosphere"
"underrated historical epics pre-2010"
"occult ritual films not horror"
```
