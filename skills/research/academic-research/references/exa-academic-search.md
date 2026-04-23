# Exa Academic Search Reference

Comprehensive reference for using Exa MCP tools for academic paper search.

## Available Tools

### web_search_exa

Real-time web search with academic filtering capabilities.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search query (required) |
| `numResults` | number | Number of results (default: 10, max: 100) |
| `category` | string | Content type filter |
| `includeDomains` | string[] | Restrict to specific domains |
| `excludeDomains` | string[] | Exclude specific domains |
| `startPublishedDate` | string | ISO date (e.g., "2024-01-01") |
| `endPublishedDate` | string | ISO date |
| `startCrawlDate` | string | ISO date for crawl time |
| `endCrawlDate` | string | ISO date |

### get_code_context_exa

Search for code implementations and technical documentation.

**Best for**: Finding code that implements concepts from papers.

**Parameters**:
| Parameter | Type | Description |
|-----------|------|-------------|
| `query` | string | Search query (required) |
| `tokensNum` | number/"dynamic" | Token limit (default: "dynamic") |

### deep_search_exa

Advanced search with query expansion and summaries.

**Best for**: Complex research questions requiring synthesis.

## Academic-Specific Parameters

### Category Filter

```javascript
category: "research_paper"
```

Filters results to academic papers, preprints, and scholarly articles.

### Academic Domain Filtering

**ArXiv-focused**:
```javascript
includeDomains: ["arxiv.org"]
```

**Multi-source academic**:
```javascript
includeDomains: [
  "arxiv.org",           // Preprints (CS, Physics, Math, etc.)
  "aclanthology.org",    // ACL Anthology (NLP papers)
  "openreview.net",      // ML conference submissions/reviews
  "proceedings.mlr.press", // JMLR, ICML, AISTATS
  "papers.nips.cc",      // NeurIPS proceedings
  "openaccess.thecvf.com", // CVPR, ICCV (Computer Vision)
  "ieeexplore.ieee.org", // IEEE publications
  "dl.acm.org",          // ACM Digital Library
  "nature.com",          // Nature journals
  "science.org"          // Science journals
]
```

### Date Filtering

**Recent papers (last year)**:
```javascript
startPublishedDate: "2024-01-01"
```

**Specific time range**:
```javascript
startPublishedDate: "2023-06-01",
endPublishedDate: "2023-12-31"
```

## Search Query Patterns

### Topic Search
```javascript
mcp__exa__web_search_exa({
  query: "transformer architecture attention mechanism",
  category: "research_paper",
  numResults: 20
})
```

### Author Search
```javascript
mcp__exa__web_search_exa({
  query: "author:Yann LeCun convolutional neural networks",
  category: "research_paper"
})
```

### Recent Developments
```javascript
mcp__exa__web_search_exa({
  query: "large language model reasoning chain-of-thought",
  category: "research_paper",
  startPublishedDate: "2024-06-01",
  numResults: 30
})
```

### ArXiv-Specific
```javascript
mcp__exa__web_search_exa({
  query: "multimodal vision language models",
  includeDomains: ["arxiv.org"],
  numResults: 25
})
```

### Survey/Review Papers
```javascript
mcp__exa__web_search_exa({
  query: "survey review transformer architectures NLP",
  category: "research_paper",
  numResults: 15
})
```

### Code Implementation Search
```javascript
mcp__exa__get_code_context_exa({
  query: "BERT implementation PyTorch attention mechanism",
  tokensNum: 5000
})
```

## Advanced Patterns

### Multi-Domain Conference Search
```javascript
mcp__exa__web_search_exa({
  query: "few-shot learning meta-learning",
  category: "research_paper",
  includeDomains: [
    "proceedings.mlr.press",
    "papers.nips.cc",
    "openreview.net"
  ],
  numResults: 30
})
```

### Exclude Non-Academic Sources
```javascript
mcp__exa__web_search_exa({
  query: "deep learning optimization",
  category: "research_paper",
  excludeDomains: [
    "medium.com",
    "towardsdatascience.com",
    "blog.*"
  ]
})
```

### Deep Research on Complex Topic
```javascript
mcp__exa__deep_search_exa({
  query: "What are the current approaches to aligning large language models with human preferences?",
  numResults: 15
})
```

## Response Handling

Exa returns structured results with:
- `title` - Paper title
- `url` - Link to paper
- `publishedDate` - Publication date
- `author` - Author information (when available)
- `text` - Abstract or summary content
- `highlights` - Key excerpts

### Extracting ArXiv IDs

From Exa results, extract arXiv IDs for use with arxiv-mcp-server:

```
URL pattern: https://arxiv.org/abs/2301.00234
ArXiv ID: 2301.00234

URL pattern: https://arxiv.org/pdf/2301.00234.pdf
ArXiv ID: 2301.00234
```

## Direct API Endpoints (curl)

Beyond MCP tools, Exa offers powerful direct API endpoints for academic research.

### /answer - Synthesized Answers with Citations

Get AI-synthesized answers with academic citations. Excellent for research questions.

```bash
curl -s "https://api.exa.ai/answer" -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "query": "What are the main approaches to RLHF in large language models?",
    "includeDomains": ["arxiv.org"]
  }'
```

**Returns**: Comprehensive answer with inline citations and source list.

### /contents - Extract Paper Details

Get full text and highlights from specific papers by URL.

```bash
curl -s "https://api.exa.ai/contents" -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "ids": ["https://arxiv.org/abs/2501.09686"],
    "text": true,
    "highlights": {"numSentences": 3}
  }'
```

**Parameters**:
- `ids` - Array of URLs to extract content from
- `text` - Include full text (boolean)
- `highlights` - Extract key sentences

### /research/v1 - Long-Running Research (Async)

For comprehensive literature reviews and complex research tasks.

```bash
curl -s "https://api.exa.ai/research/v1" -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "instructions": "Research the main approaches to chain-of-thought prompting in LLMs. Focus on academic papers from arxiv.org.",
    "model": "exa-research-fast"
  }'
```

**Parameters**:
- `instructions` - Research instructions (max 4096 chars)
- `model` - `exa-research-fast`, `exa-research`, or `exa-research-pro`
- `outputSchema` - Optional JSON schema for structured output

**Returns**: `researchId` for polling completion.

**Models**:
| Model | Speed | Thoroughness | Cost |
|-------|-------|--------------|------|
| exa-research-fast | Fast | Basic | Low |
| exa-research | Medium | Standard | Medium |
| exa-research-pro | Slow | Comprehensive | High |

## Troubleshooting

### No Results with category Filter
- Try without category filter first
- Use includeDomains instead for source control
- Broaden query terms

### Too Many Non-Academic Results
- Add `category: "research_paper"`
- Use `includeDomains` for academic sources
- Add terms like "paper" or "research" to query

### Missing Recent Papers
- ArXiv may index faster than Exa crawls
- Use arxiv-mcp-server for very recent papers
- Try `sort_by: "submitted_date"` with arXiv

### MCP vs Direct API
- **MCP tools**: Integrated into Claude Code, no API key handling needed
- **Direct API (curl)**: Access to `/answer`, `/contents`, `/research` endpoints not in MCP
