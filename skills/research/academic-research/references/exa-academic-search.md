# Exa Academic Search Reference

Exa for paper discovery, through the `exa-search` scripts (primary) or the hosted Exa MCP server. `S=~/.claude/skills/exa-search/scripts`.

## Scripts (Primary)

| Task | Command |
|------|---------|
| Topic search | `python3 $S/exa_search.py "query" --category publication --highlights --no-text -n 20` |
| Recent papers | `... --category publication --after 2026-01-01` |
| Date window | `... --after 2025-06-01 --before 2025-12-31` |
| arXiv only | `... --domains arxiv.org` (no `--category`) |
| Conference venues | `... --domains proceedings.mlr.press --domains papers.nips.cc --domains openreview.net` |
| Drop blogs | `... --exclude-domains medium.com --exclude-domains towardsdatascience.com` |
| Read known papers | `python3 $S/exa_contents.py https://arxiv.org/abs/2501.09686 --highlights-query "method and results" --no-text` |
| Cited answer from academic sources | `python3 $S/exa_research.py "question" --domains arxiv.org --sources` |
| Structured paper survey | `python3 $S/exa_search.py "question" --category publication --schema-preset paper-survey` |
| Code implementing a paper | `python3 $S/exa_search.py "BERT attention PyTorch implementation" --domains github.com` |
| Multi-hop literature review, paper lists | `python3 $S/exa_agent.py run "task" --effort medium` |

Repeated `--domains` and `--exclude-domains` flags accumulate. Full flag reference: `~/.claude/skills/exa-search/references/exa-scripts-reference.md`.

## Academic Domains

```
arxiv.org               Preprints (CS, physics, math)
aclanthology.org        ACL Anthology (NLP)
openreview.net          ML conference submissions and reviews
proceedings.mlr.press   JMLR, ICML, AISTATS
papers.nips.cc          NeurIPS
openaccess.thecvf.com   CVPR, ICCV
ieeexplore.ieee.org     IEEE
dl.acm.org              ACM Digital Library
nature.com              Nature journals
science.org             Science journals
```

## Query Patterns

- **Describe the paper, not keywords.** "a survey comparing linear attention approximations for long-context transformers" beats "linear attention survey".
- **Surveys:** add "survey" or "review" to the description.
- **Authors:** name them in the description ("papers by Yann LeCun on self-supervised learning"); there is no author filter.
- **`publication` vs `--domains`:** the category covers journals, preprints, and proceedings; domains pin exact venues. They cannot combine—`--category publication --domains X` returns 400 `UNSUPPORTED_PUBLICATION_INCLUDE_FILTER`. `--exclude-domains` does work with the category.

## Exa MCP Server (Alternative)

Hosted at `https://mcp.exa.ai/mcp` (not configured in this environment; checked against `exa-labs/exa-mcp-server` on 2026-10-19).

| Tool | Default | Parameters |
|------|---------|------------|
| `web_search_exa` | on | `query`, `numResults` only—no category, domain, or date filters |
| `web_fetch_exa` | on | `urls[]`, `maxCharacters` (default 3000) |
| `web_search_advanced_exa` | opt-in | `category` (`publication`, ...), `includeDomains`, `excludeDomains`, `startPublishedDate`, `endPublishedDate`, `type` (`auto`/`lite`), `enableHighlights`, `highlightsQuery`, `enableSummary`, `additionalQueries`, `maxAgeHours`, `subpages` |
| `agent_run` | opt-in, needs auth | Exa Agent: multi-step research, lists, structured output |

Enable opt-in tools on the URL (this replaces the defaults, so list every tool wanted): `https://mcp.exa.ai/mcp?tools=web_search_exa,web_fetch_exa,web_search_advanced_exa`.

Academic search through MCP needs `web_search_advanced_exa`:

```javascript
web_search_advanced_exa({
  query: "a survey of reasoning in large language models",
  category: "publication",          // cannot combine with includeDomains
  startPublishedDate: "2026-01-01",
  numResults: 20,
  enableHighlights: true
})
```

`get_code_context_exa`, `deep_search_exa`, and `deep_researcher_start`/`deep_researcher_check` are deprecated and disabled by default; use `web_search_exa` and `agent_run`. The category `research_paper` is now `publication`.

## Extracting arXiv IDs

Exa results feed `arxiv-mcp-server` (`download_paper`, `read_paper`):

```
https://arxiv.org/abs/2301.00234       → 2301.00234
https://arxiv.org/pdf/2301.00234.pdf   → 2301.00234
```

## Troubleshooting

- **Too many blogs:** add `--category publication` (plus `--exclude-domains`), or drop the category and pin venues with `--domains`.
- **400 `UNSUPPORTED_PUBLICATION_INCLUDE_FILTER`:** `--domains` was combined with `--category publication`; drop one.
- **Missing very recent papers:** arXiv indexes faster than Exa crawls; use `search_papers` with `sort_by: "submitted_date"`.
- **`--lite` returns fewer results than `-n`:** lite serves cached pages only; drop `--lite` for coverage.
- **The Research API (`/research/v1`) is retired** (410). Long-running literature reviews go through `exa_agent.py run` or the MCP `agent_run` tool.
