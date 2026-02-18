# Exa Search Scripts — Full Reference

Detailed parameter reference for all 5 Exa search scripts.

---

## exa_search.py — Neural Web Search

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_search.py`

### All Parameters

| Parameter | Description |
|-----------|-------------|
| `-n, --num` | Number of results (max 100) |
| `--neural` | Pure embeddings-based semantic search |
| `--instant` | Sub-150ms latency (Feb 2026) |
| `--fast` | ~500ms latency, balanced |
| `--deep` | Comprehensive with query expansion |
| `--category, -c` | Filter: company, research paper, news, pdf, github, tweet, personal site, people, financial report |
| `--domains` | Only include these domains |
| `--exclude-domains` | Exclude these domains |
| `--after` | Start date (YYYY-MM-DD) |
| `--before` | End date (YYYY-MM-DD) |
| `--must-include` | Results must contain these strings |
| `--must-exclude` | Results must NOT contain these strings |
| `--additional-queries` | Extra queries for deep search |
| `--context` | Combine results into RAG context string |
| `--context-chars` | Limit context string length |
| `--summary` | Generate AI summaries with query |
| `--highlights` | Include key excerpts |
| `--subpages` | Crawl linked subpages (count) |
| `--no-text` | Don't retrieve page text |
| `--safe` | Content moderation filter |
| `--json` | Output raw JSON |

### Examples

```bash
# Basic search
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "AI agent frameworks"

# Category-filtered
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "transformer architecture" --category "research paper" -n 20

# Deep search with additional queries
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "web scraping Python" --deep --additional-queries "Python crawler" "BeautifulSoup Scrapy"

# Domain-filtered
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "Python tutorials" --domains docs.python.org realpython.com github.com

# Date-filtered for recent content
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "OpenAI announcements" --after 2024-06-01 --category news

# With content for RAG
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "React hooks best practices" --context --context-chars 10000

# With summaries and highlights
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "startup funding" --category company --summary "funding history" --highlights

# Instant search (sub-150ms)
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "JavaScript fetch API" --instant -n 5

# People/profiles
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "machine learning engineers" --category people

# With subpage crawling
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "React documentation" --subpages 3 --domains react.dev
```

---

## exa_contents.py — URL Content Extraction

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_contents.py`

### All Parameters

| Parameter | Description |
|-----------|-------------|
| `--summary` | Generate AI summary with query |
| `--highlights` | Extract key excerpts |
| `--subpages` | Crawl linked subpages (count) |
| `--livecrawl` | Fresh content: always, preferred, fallback, never |
| `--context` | Combine contents into RAG string |
| `--context-chars` | Limit context string length |
| `--links` | Extract N links |
| `--images` | Extract N images |
| `--max-chars` | Limit text length per result |
| `--json` | Output raw JSON |

### Examples

```bash
# Basic extraction
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py "https://arxiv.org/abs/2307.06435"

# Multiple URLs
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py URL1 URL2 URL3

# With AI summary
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py "https://docs.example.com" --summary "Key API methods"

# With highlights and subpages
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py "https://docs.python.org/3/tutorial" --highlights --subpages 5

# Livecrawl for fresh content
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py "https://news.ycombinator.com" --livecrawl always

# Extract links and images
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py "https://example.com" --links 10 --images 5

# Limit text length
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py "https://long-article.com" --max-chars 5000
```

---

## exa_similar.py — Find Similar Pages

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_similar.py`

### All Parameters

| Parameter | Description |
|-----------|-------------|
| `-n, --num` | Number of results (max 100) |
| `--category` | Filter by category |
| `--domains` | Only these domains |
| `--exclude-source` | Exclude source URL's domain |
| `--after` / `--before` | Date filtering |
| `--must-include` | Required strings |
| `--must-exclude` | Excluded strings |
| `--safe` | Content moderation |
| `--context` | RAG context string |
| `--context-chars` | Context length limit |
| `--summary` | Comparison summaries |
| `--highlights` | Key excerpts |
| `--json` | Output raw JSON |

### Examples

```bash
# Find similar pages
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://arxiv.org/abs/2307.06435"

# Similar companies (exclude source)
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://stripe.com" --category company --exclude-source

# From specific domains
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://medium.com/article" --domains medium.com substack.com

# With comparison summaries
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://product.com" --summary "How is this different?"
```

---

## exa_research.py — AI-Powered Deep Research

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_research.py`

### All Parameters

| Parameter | Description |
|-----------|-------------|
| `-n, --num` | Number of sources (default: 5, max: 20) |
| `--domains` | Only use these domains |
| `--after` / `--before` | Date filtering |
| `--stream` | Stream answer in real-time |
| `--sources` | Show detailed source info |
| `--highlights` | Include key excerpts |
| `--markdown` | Output as markdown with citations |
| `--answer-only` | Only output the answer |
| `--json` | Output raw JSON |

### Examples

```bash
# Basic research
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "What are the main differences between React and Vue?"

# With sources
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "SpaceX latest achievements" --sources

# Streaming
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "Explain quantum computing" --stream

# Domain-filtered
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "Python async best practices" --domains docs.python.org realpython.com

# Markdown with citations
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "Compare cloud providers" --markdown

# Answer only (for piping)
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "What is RLHF?" --answer-only
```

---

## exa_research_async.py — Async Research with Pro Models

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py`

### All Parameters

| Parameter | Description |
|-----------|-------------|
| `--fast` | Use exa-research-fast (quicker/cheaper) |
| `--pro` | Use exa-research-pro (enhanced synthesis) |
| `--schema` | JSON schema for structured output |
| `--wait` | Wait for completion |
| `--timeout` | Max seconds to wait (default: 300) |
| `list` | List all research jobs |
| `status <id>` | Check job status |

### Examples

```bash
# Basic async research
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py "What species of ant are similar to honeypot ants?"

# Pro model, wait for completion
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py "Compare top 5 AI agent frameworks" --pro --wait

# Fast model
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py "Quick market overview" --fast

# Structured output
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py "Analyze AI startup funding" \
  --schema '{"startups": [{"name": "string", "funding": "number", "focus": "string"}]}'

# Job management
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py status r_abc123
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py list --limit 20
```

---

## Cost Considerations

| Operation | Approximate Cost |
|-----------|-----------------|
| Neural search (1-25 results) | $0.005 |
| Neural search (26-100 results) | $0.025 |
| Deep search (1-25 results) | $0.015 |
| Deep search (26-100 results) | $0.075 |
| Content text per page | $0.001 |
| Highlights per page | $0.001 |
| Summary per page | $0.001 |

**Optimization tips:**
- Use `--instant` for real-time lookups (sub-150ms, cheapest)
- Use `--fast` for quick lookups (~500ms)
- Limit results with `-n`
- Use `--no-text` if content not needed
- Filter by domains to reduce irrelevant results

---

## Comparison with Exa MCP Tools

| Feature | MCP Tools | Skill Scripts |
|---------|-----------|---------------|
| Web Search | `mcp__exa__web_search_exa` | `exa_search.py` (more options) |
| Code Context | `mcp__exa__get_code_context_exa` | `exa_search.py --category github` |
| Contents | N/A | `exa_contents.py` |
| Find Similar | N/A | `exa_similar.py` |
| Quick Answer | N/A | `exa_research.py` |
| Async Research | N/A | `exa_research_async.py` |
| Deep Search | N/A | `exa_search.py --deep` |
| Instant Search | N/A | `exa_search.py --instant` |
| 9 Categories | Limited | Full support |
| Date Filtering | Limited | Full support |
| Domain Filtering | Limited | Full support |
| Subpage Crawling | N/A | Full support |
| Livecrawling | N/A | Full support |
| Structured Output | N/A | Full support |

---

## Test Suite

```bash
# Run all tests
python3 ~/.claude/skills/exa-search/scripts/test_exa.py

# Quick validation only
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --quick

# Verbose output
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --verbose

# Test specific endpoint
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint search
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint contents
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint similar
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint answer
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint research
```
