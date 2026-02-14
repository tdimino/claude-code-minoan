---
name: exa-search
description: Advanced Exa AI search with 5 specialized scripts for neural web search, content extraction, similar page discovery, quick research with citations, and async pro research with structured output. This skill should be used when performing web searches, extracting content from URLs, finding similar pages, or conducting AI-powered research. Provides full access to all Exa API endpoints including /search, /contents, /findSimilar, /answer, and /research/v1.
---

# Exa Search Skill

This skill provides comprehensive access to the Exa AI search API through 5 specialized scripts, each targeting a specific endpoint with full parameter support.

## When to Use This Skill

Use this skill when:
- Performing neural web searches with AI-powered relevance ranking
- Searching specific categories (research papers, companies, news, GitHub, people, etc.)
- Extracting clean content from known URLs
- Finding pages similar to a reference URL (competitive analysis, related research)
- Conducting AI-powered research with automatic source citations
- Building datasets from web content
- Performing domain-filtered searches for authoritative sources
- Need date-filtered results for recent information

## Prerequisite

All scripts require the `EXA_API_KEY` environment variable. Get your key at https://dashboard.exa.ai

```bash
# Verify API key is set
echo $EXA_API_KEY
```

## Available Scripts

### 1. exa_search.py - Neural Web Search

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_search.py`

The most comprehensive search script with full access to Exa's `/search` endpoint.

**Search Types:**
- `auto` (default) - Intelligently combines search methods
- `instant` - Sub-150ms latency, optimized for real-time apps (Feb 2026)
- `neural` - Pure embeddings-based semantic search
- `fast` - ~500ms latency, balance of speed and quality
- `deep` - Comprehensive search with query expansion

**Categories:**
- `company` - Company pages and profiles
- `research paper` - Academic papers (arXiv, etc.)
- `news` - News articles
- `pdf` - PDF documents
- `github` - GitHub repositories and code
- `tweet` - Twitter/X posts
- `personal site` - Personal websites and blogs
- `people` - LinkedIn profiles and people pages
- `financial report` - Financial documents

**Examples:**

```bash
# Basic search
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "AI agent frameworks"

# Category-filtered search
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "transformer architecture" --category "research paper" -n 20

# Deep search with multiple query variations
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "web scraping Python" --deep --additional-queries "Python crawler" "BeautifulSoup Scrapy"

# Domain-filtered search
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "Python tutorials" --domains docs.python.org realpython.com github.com

# Date-filtered search for recent content
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "OpenAI announcements" --after 2024-06-01 --category news

# Search with content for RAG applications
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "React hooks best practices" --context --context-chars 10000

# Search with summaries and highlights
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "startup funding" --category company --summary "funding history and investors" --highlights

# Instant search for real-time apps (sub-150ms)
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "JavaScript fetch API" --instant -n 5

# Fast search for quick lookups
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "JavaScript fetch API" --fast -n 5

# Search for people/profiles
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "machine learning engineers" --category people

# Search with subpage crawling
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "React documentation" --subpages 3 --domains react.dev

# Output as JSON
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "GraphQL vs REST" --json
```

**Key Parameters:**
- `-n, --num` - Number of results (max 100)
- `--neural/--instant/--fast/--deep` - Search type
- `--category, -c` - Filter by category
- `--domains` - Only include these domains
- `--exclude-domains` - Exclude these domains
- `--after/--before` - Date filtering (YYYY-MM-DD)
- `--context` - Combine results into RAG context string
- `--summary` - Generate AI summaries
- `--highlights` - Include key excerpts
- `--subpages` - Crawl subpages
- `--json` - Output raw JSON

---

### 2. exa_contents.py - URL Content Extraction

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_contents.py`

Extract clean, formatted content from specific URLs using Exa's `/contents` endpoint.

**Examples:**

```bash
# Basic content extraction
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

# JSON output
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py URLs --json
```

**Key Parameters:**
- `--summary` - Generate AI summary with query
- `--highlights` - Extract key excerpts
- `--subpages` - Crawl linked subpages
- `--livecrawl` - Fresh content mode: `always`, `preferred`, `fallback`, `never`
- `--context` - Combine contents into RAG context string
- `--context-chars` - Limit context string length
- `--links/--images` - Extract links/images
- `--max-chars` - Limit text length
- `--json` - Output raw JSON

---

### 3. exa_similar.py - Find Similar Pages

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_similar.py`

Discover pages semantically similar to a reference URL using Exa's `/findSimilar` endpoint.

**Use Cases:**
- Find similar research papers
- Discover competitor products/companies
- Expand reading lists with related content
- Competitive analysis
- Content recommendations

**Examples:**

```bash
# Find similar pages
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://arxiv.org/abs/2307.06435"

# Find similar with more results
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://github.com/langchain-ai/langchain" -n 20

# Similar companies (exclude source domain)
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://stripe.com" --category company --exclude-source

# Similar from specific domains only
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://medium.com/article" --domains medium.com substack.com

# With comparison summaries
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://product.com" --summary "How is this different?"

# Recent similar content only
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://blog.example.com" --after 2024-01-01

# JSON output
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py URL --json
```

**Key Parameters:**
- `-n, --num` - Number of similar results (max 100)
- `--category` - Filter by category
- `--domains` - Only these domains
- `--exclude-source` - Exclude the source URL's domain
- `--after/--before` - Date filtering
- `--must-include` - Results must contain these strings
- `--must-exclude` - Results must NOT contain these strings
- `--safe` - Enable content moderation filter
- `--context` - Combine contents into RAG context string
- `--context-chars` - Limit context string length
- `--summary` - Generate comparison summaries
- `--highlights` - Key excerpts
- `--json` - Output raw JSON

---

### 4. exa_research.py - AI-Powered Deep Research

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_research.py`

Conduct deep research with AI-synthesized answers and automatic citations using Exa's `/answer` endpoint.

**Use Cases:**
- Quick research on any topic with citations
- Fact-checking with source verification
- Technical documentation queries
- Market research summaries
- Competitive analysis
- Current events synthesis

**Examples:**

```bash
# Basic research question
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "What are the main differences between React and Vue?"

# Research with source details
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "SpaceX latest achievements" --sources

# Streaming answer in real-time
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "Explain quantum computing" --stream

# Domain-filtered research (authoritative sources only)
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "Python async best practices" --domains docs.python.org realpython.com

# Recent information only
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "AI regulation news" --after 2024-06-01

# Markdown output with citations
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "Compare cloud providers" --markdown

# Answer only (for piping)
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "What is RLHF?" --answer-only

# With key excerpts from sources
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "Transformer architecture explained" --highlights --sources

# More sources for comprehensive research
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "GraphQL vs REST comparison" -n 10

# JSON output
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "query" --json
```

**Key Parameters:**
- `-n, --num` - Number of sources (default: 5, max: 20)
- `--domains` - Only use these domains as sources
- `--after/--before` - Date filtering
- `--stream` - Stream the answer in real-time
- `--sources` - Show detailed source information
- `--highlights` - Include key excerpts
- `--markdown` - Output as markdown with citations
- `--answer-only` - Only output the answer text
- `--json` - Output raw JSON

---

### 5. exa_research_async.py - Async Research with Pro Models

**Command**: `python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py`

Advanced async research using Exa's `/research/v1` endpoint with multiple models and structured output.

**Features:**
- Async job-based research (submit and poll)
- Model selection: `exa-research-fast`, `exa-research`, or `exa-research-pro`
- Structured JSON output with custom schemas
- Long-running research for complex topics
- Status tracking and job management

**Examples:**

```bash
# Create research job
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py "What species of ant are similar to honeypot ants?"

# Use pro model and wait for completion
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py "Compare top 5 AI agent frameworks" --pro --wait

# Use fast model for quick tasks
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py "Quick market overview" --fast

# Structured output with JSON schema
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py "Analyze AI startup funding" \
  --schema '{"startups": [{"name": "string", "funding": "number", "focus": "string"}]}'

# Check job status
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py status r_abc123

# List all research jobs
python3 ~/.claude/skills/exa-search/scripts/exa_research_async.py list --limit 20
```

**Key Parameters:**
- `--fast` - Use exa-research-fast model (quicker/cheaper)
- `--pro` - Use exa-research-pro model (enhanced synthesis)
- `--schema` - JSON schema for structured output
- `--wait` - Wait for job completion
- `--timeout` - Max seconds to wait (default: 300)
- `list` - List all research jobs
- `status <id>` - Check status of a job

---

## Script Selection Guide

| Task | Best Script | Example |
|------|-------------|---------|
| Web search with filters | `exa_search.py` | Find recent AI papers |
| Research papers | `exa_search.py --category "research paper"` | Academic literature |
| Company/startup info | `exa_search.py --category company` | Market research |
| GitHub repos | `exa_search.py --category github` | Code discovery |
| Extract URL content | `exa_contents.py` | Known URLs |
| Find competitors | `exa_similar.py --exclude-source` | Competitive analysis |
| Related research | `exa_similar.py` | Expand literature |
| Quick answers | `exa_research.py` | Fact-finding |
| Research with citations | `exa_research.py --sources` | Report writing |
| Complex structured research | `exa_research_async.py --pro` | Multi-source synthesis |
| Real-time search | `exa_search.py --instant` | Chat, voice, autocomplete |
| RAG context | `exa_search.py --context` | LLM applications |

## Comparison with Exa MCP Tools

| Feature | MCP Tools | This Skill's Scripts |
|---------|-----------|---------------------|
| Web Search | `mcp__exa__web_search_exa` | `exa_search.py` (more options) |
| Code Context | `mcp__exa__get_code_context_exa` | `exa_search.py --category github` |
| Contents Extraction | N/A | `exa_contents.py` |
| Find Similar | N/A | `exa_similar.py` |
| Quick Answer | N/A | `exa_research.py` |
| Async Research (Pro) | N/A | `exa_research_async.py` |
| Deep Search | N/A | `exa_search.py --deep` |
| Instant Search | N/A | `exa_search.py --instant` |
| Category Filtering | Limited | All 9 categories |
| Date Filtering | Limited | Full support |
| Domain Filtering | Limited | Full support |
| Subpage Crawling | N/A | Full support |
| Livecrawling | N/A | Full support |
| Structured Output | N/A | Full support |

**This skill provides full Exa API access beyond what MCP tools offer.**

## Cost Considerations

Exa API pricing (approximate):
- Neural search (1-25 results): $0.005
- Neural search (26-100 results): $0.025
- Deep search (1-25 results): $0.015
- Deep search (26-100 results): $0.075
- Content text: $0.001/page
- Highlights: $0.001/page
- Summary: $0.001/page

To optimize costs:
- Use `--instant` for real-time lookups (sub-150ms, lowest latency)
- Use `--fast` for quick lookups (~500ms)
- Limit results with `-n`
- Use `--no-text` if content not needed
- Filter by domains to reduce irrelevant results

## Common Workflows

### Workflow 1: Research a Topic
```bash
# Quick research with citations
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "How does RAG work?" --sources --markdown
```

### Workflow 2: Literature Review
```bash
# Find research papers
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "transformer optimization techniques" \
  --category "research paper" -n 20 --summary "Key contributions"

# Find similar papers to a key reference
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://arxiv.org/abs/1706.03762" \
  --category "research paper" -n 15
```

### Workflow 3: Competitive Analysis
```bash
# Find similar companies
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://competitor.com" \
  --category company --exclude-source -n 10 --summary "Key differentiators"
```

### Workflow 4: Documentation Research
```bash
# Search docs with domain filtering
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "React useEffect cleanup" \
  --domains react.dev developer.mozilla.org --context

# Extract specific docs content
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py "https://react.dev/reference/react/useEffect" \
  --highlights --subpages 2
```

### Workflow 5: News Monitoring
```bash
# Recent news search
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "AI regulation" \
  --category news --after 2024-06-01 -n 15
```

### Workflow 6: Build RAG Context
```bash
# Get context string for LLM
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "Python async programming patterns" \
  --context --context-chars 15000 --domains docs.python.org realpython.com
```

---

## Test Suite

Run the test suite to verify API connectivity and feature functionality:

```bash
# Run all tests
python3 ~/.claude/skills/exa-search/scripts/test_exa.py

# Run quick validation only
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --quick

# Show detailed output
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --verbose

# Test specific endpoint
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint search
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint contents
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint similar
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint answer
python3 ~/.claude/skills/exa-search/scripts/test_exa.py --endpoint research
```

The test suite verifies:
- API key validation
- Basic search, category filtering, domain filtering, deep search
- Content extraction, livecrawl, context parameter
- Find similar pages, moderation filter
- Research/answer endpoint, streaming support
- Async research model validation, job listing
