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

## Shared CLI Tools Reference

### Exa CLI Scripts (`~/.claude/skills/exa-search/scripts/`)

| Script | Purpose | Film Discovery Use |
|--------|---------|-------------------|
| `exa_search.py` | Neural search with filters | Find curated lists, articles, recommendations |
| `exa_research.py` | Synthesized answers with citations | Critical discourse, thematic analysis, content verification |
| `exa_similar.py` | Find pages similar to a URL | Discover films similar to a Letterboxd entry |
| `exa_contents.py` | Extract full text from URLs | Pull complete content from found lists |

**Example invocations:**
```bash
# Find curated lists
python3 ~/.claude/skills/exa-search/scripts/exa_search.py \
  "Letterboxd list gothic vampire films pre-2010" -n 10

# Synthesized critical discourse
python3 ~/.claude/skills/exa-search/scripts/exa_research.py \
  "gothic horror films romantic sensibility 1980s 1990s" --sources --markdown

# Find similar films from a reference
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py \
  "https://letterboxd.com/film/eyes-wide-shut/" -n 15

# Extract full content from a found list
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py \
  "https://letterboxd.com/user/list/gothic-horror-essentials/"
```

### Firecrawl CLI

Scrapes full page content when Exa finds a promising URL.

```bash
firecrawl scrape <url> --only-main-content
```

For autonomous multi-source research:
```bash
python3 ~/.claude/skills/firecrawl/scripts/firecrawl_api.py agent \
  "best gothic horror films pre-2010 with occult themes"
```

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

### For Exa Search (`exa_search.py`)

```bash
# Gothic/Occult
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "Criterion Collection gothic horror films" -n 10
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "best occult films 1970s 1980s" -n 10
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "films like Eyes Wide Shut secret society" -n 10

# Literary
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "literary adaptations Criterion Collection" -n 10

# Noir
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "neo-noir films 1990s underrated" -n 10
```

### For Exa Research (`exa_research.py`)

```bash
# Discourse/Analysis
python3 ~/.claude/skills/exa-search/scripts/exa_research.py \
  "Eyes Wide Shut occult symbolism analysis" --sources --markdown
python3 ~/.claude/skills/exa-search/scripts/exa_research.py \
  "gothic horror films romantic sensibility" --sources --markdown

# Recommendations
python3 ~/.claude/skills/exa-search/scripts/exa_research.py \
  "films similar to Interview with the Vampire gothic atmosphere" --sources
python3 ~/.claude/skills/exa-search/scripts/exa_research.py \
  "underrated historical epics pre-2010" --sources
```
