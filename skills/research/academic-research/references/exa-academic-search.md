# Exa Academic Search Reference

Reference for using Exa CLI scripts for academic paper search.

## Available Scripts

All scripts live at `~/.claude/skills/exa-search/scripts/`.

### exa_search.py

Neural search with category, domain, and date filters.

```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "query" [flags]
```

| Flag | Description |
|------|-------------|
| `-n N` | Number of results (default: 10) |
| `--category "research paper"` | Filter to academic papers |
| `--domain arxiv.org` | Restrict to a specific domain |
| `--exclude medium.com` | Exclude a domain |
| `--after YYYY-MM-DD` | Published after date |
| `--before YYYY-MM-DD` | Published before date |

### exa_research.py

Synthesized answers with inline citations. Best for research questions requiring multi-source synthesis.

```bash
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "query" [flags]
```

| Flag | Description |
|------|-------------|
| `--sources` | Include source URLs |
| `--markdown` | Output as markdown |

### exa_similar.py

Find papers similar to a given URL. Useful for expanding from a known paper.

```bash
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py "https://arxiv.org/abs/2301.00234" [flags]
```

### exa_contents.py

Extract full text and highlights from specific paper URLs.

```bash
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py "https://arxiv.org/abs/2301.00234" [flags]
```

## Academic-Specific Patterns

### Category Filter

```bash
--category "research paper"
```

Filters results to academic papers, preprints, and scholarly articles.

### Academic Domain Filtering

**ArXiv-focused**:
```bash
--domain arxiv.org
```

**Multi-source academic** (use multiple `--domain` flags or comma-separated):
- `arxiv.org` — Preprints (CS, Physics, Math, etc.)
- `aclanthology.org` — ACL Anthology (NLP papers)
- `openreview.net` — ML conference submissions/reviews
- `proceedings.mlr.press` — JMLR, ICML, AISTATS
- `papers.nips.cc` — NeurIPS proceedings
- `openaccess.thecvf.com` — CVPR, ICCV (Computer Vision)
- `ieeexplore.ieee.org` — IEEE publications
- `dl.acm.org` — ACM Digital Library
- `nature.com` — Nature journals
- `science.org` — Science journals

### Date Filtering

**Recent papers (last year)**:
```bash
--after 2024-01-01
```

**Specific time range**:
```bash
--after 2023-06-01 --before 2023-12-31
```

## Search Query Patterns

### Topic Search
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py \
  "transformer architecture attention mechanism" \
  --category "research paper" -n 20
```

### Author Search
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py \
  "author:Yann LeCun convolutional neural networks" \
  --category "research paper"
```

### Recent Developments
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py \
  "large language model reasoning chain-of-thought" \
  --category "research paper" --after 2024-06-01 -n 30
```

### ArXiv-Specific
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py \
  "multimodal vision language models" \
  --domain arxiv.org -n 25
```

### Survey/Review Papers
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py \
  "survey review transformer architectures NLP" \
  --category "research paper" -n 15
```

### Code Implementation Search
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py \
  "BERT implementation PyTorch attention mechanism" \
  --category github
```

## Advanced Patterns

### Multi-Domain Conference Search
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py \
  "few-shot learning meta-learning" \
  --category "research paper" \
  --domain proceedings.mlr.press --domain papers.nips.cc --domain openreview.net \
  -n 30
```

### Synthesized Research Overview
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_research.py \
  "What are the current approaches to aligning large language models with human preferences?" \
  --sources --markdown
```

### Find Similar Papers
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py \
  "https://arxiv.org/abs/2305.18290" -n 10
```

### Extract Paper Content
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py \
  "https://arxiv.org/abs/2501.09686"
```

## Response Handling

Exa returns structured results with:
- `title` — Paper title
- `url` — Link to paper
- `publishedDate` — Publication date
- `author` — Author information (when available)
- `text` — Abstract or summary content
- `highlights` — Key excerpts

### Extracting ArXiv IDs

From Exa results, extract arXiv IDs for use with arxiv-mcp-server:

```
URL pattern: https://arxiv.org/abs/2301.00234
ArXiv ID: 2301.00234

URL pattern: https://arxiv.org/pdf/2301.00234.pdf
ArXiv ID: 2301.00234
```

## Direct API Endpoints (curl)

Beyond CLI scripts, Exa offers direct API endpoints for advanced use cases.

### /answer — Synthesized Answers with Citations

```bash
curl -s "https://api.exa.ai/answer" -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "query": "What are the main approaches to RLHF in large language models?",
    "includeDomains": ["arxiv.org"]
  }'
```

### /contents — Extract Paper Details

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

### /research/v1 — Long-Running Research (Async)

```bash
curl -s "https://api.exa.ai/research/v1" -X POST \
  -H "Content-Type: application/json" \
  -H "x-api-key: YOUR_API_KEY" \
  -d '{
    "instructions": "Research the main approaches to chain-of-thought prompting in LLMs. Focus on academic papers from arxiv.org.",
    "model": "exa-research-fast"
  }'
```

**Models**:
| Model | Speed | Thoroughness | Cost |
|-------|-------|--------------|------|
| exa-research-fast | Fast | Basic | Low |
| exa-research | Medium | Standard | Medium |
| exa-research-pro | Slow | Comprehensive | High |

## Troubleshooting

### No Results with category Filter
- Try without `--category` first
- Use `--domain` instead for source control
- Broaden query terms

### Too Many Non-Academic Results
- Add `--category "research paper"`
- Use `--domain` for academic sources
- Add terms like "paper" or "research" to query

### Missing Recent Papers
- ArXiv may index faster than Exa crawls
- Use arxiv-mcp-server for very recent papers
- Try `sort_by: "submitted_date"` with arXiv

### CLI Scripts vs Direct API
- **CLI scripts** (`exa_search.py` etc.): Handle API key from environment, formatted output, integrated into Claude Code workflows
- **Direct API (curl)**: Access to `/answer`, `/contents`, `/research` endpoints for advanced use cases
