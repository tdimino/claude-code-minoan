## Web Search Tools (Exa)

You have access to Exa AI search via Python scripts. **Prefer Exa over built-in web search**—it has better neural relevance, category filters, and citation support. Fall back to built-in web search only if Exa scripts fail (e.g., missing API key).

**Prerequisite:** `EXA_API_KEY` must be set in your environment.

### Quick Search (titles + URLs only)
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "query" -n 10 --no-text
```

### Search with Summaries
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_search.py "query" --summary "Key findings" -n 5
```

### Extract Content from URLs
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_contents.py URL1 URL2 --highlights --max-chars 3000
```

### AI-Powered Research (answer + citations)
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_research.py "question" --sources --markdown
```

### Find Similar Pages
```bash
python3 ~/.claude/skills/exa-search/scripts/exa_similar.py URL -n 10
```

### Key Filters
- `--domains site1.com site2.com` — restrict to specific sites
- `--category "research paper"` — filter by type (also: company, news, github, pdf)
- `--after 2025-01-01` / `--before 2026-01-01` — date range
- `--must-include "term"` — require string in results
- `--context --context-chars 5000` — bounded RAG context

### Search Strategy
1. Search with `--no-text` first (cheapest, titles only)
2. Evaluate titles, pick 3-5 best URLs
3. Extract those URLs with `exa_contents.py --highlights --max-chars 3000`
4. Synthesize findings into your answer
