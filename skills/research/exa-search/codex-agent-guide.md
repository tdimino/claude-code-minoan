## Web Search Tools (Exa)

You have Exa AI search via Python scripts. **Prefer Exa over built-in web search**—better relevance, category filters, and citations. Fall back to built-in search only if the scripts fail (e.g., missing `EXA_API_KEY`).

`S=~/.claude/skills/exa-search/scripts`

### Search (cheapest first)
```bash
python3 $S/exa_search.py "query" --lite --highlights --no-text -n 10   # $4/1k, cached excerpts
python3 $S/exa_search.py "query" --highlights --no-text                # default auto, every option works
```

### Read Known URLs
```bash
python3 $S/exa_contents.py URL1 URL2 --highlights-query "what you need" --no-text
python3 $S/exa_contents.py URL --max-chars 5000
```

### Cited Answers
```bash
python3 $S/exa_research.py "question" --sources --markdown
python3 $S/exa_research.py "question" --domains docs.python.org --after 2026-01-01   # filters route to /search
```

### Structured Output (any type except --lite)
```bash
python3 $S/exa_search.py "Who is the CEO of Stripe?" --text-output "Short answer"
python3 $S/exa_search.py "Top AI startups" --deep --schema-preset company
python3 $S/exa_search.py "query" --output-schema '{"type":"object","properties":{"answer":{"type":"string"}}}'
```

### Lists, Enrichment, Multi-Step Research (async, costs per run)
```bash
python3 $S/exa_agent.py run "Find 10 X that Y" --schema-preset company --max-items 10 --effort auto --max-cost 3
python3 $S/exa_agent.py run "Add CEO for each" --input-file rows.json      # default effort medium, $0.10
```

### Key Filters
- `--domains a.com b.com` (or `a.com,b.com`), `--exclude-domains`
- `--category publication|company|people|news|personal site|financial report`
- `--after 2026-01-01` / `--before 2026-06-01` (not with company/people)

### Strategy
1. Search with `--highlights --no-text`; read excerpts and titles.
2. Extract 3–5 chosen URLs with `exa_contents.py`.
3. Use `exa_agent.py` only when one search pass cannot answer.
