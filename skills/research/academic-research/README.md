# Academic Research

The literature review skill. Search academic papers, download from ArXiv, and synthesize findings using Exa's neural search for broad discovery and ArXiv MCP for deep paper analysis.

**Last updated:** 2026-04-25

**Reflects:** Exa AI search API (research_paper category), ArXiv MCP server tools, Obscura stealth browser for bot-protected academic sites, and academic search patterns across 6+ reputable sources.

---

## Why This Skill Exists

Academic search requires different tools for different tasks: broad discovery (Exa), deep paper analysis (ArXiv MCP), and stealth extraction from bot-protected sources (Obscura). Exa finds papers by meaning rather than keywords. ArXiv MCP downloads full papers and enables citation analysis. Obscura's anti-fingerprinting reaches sites that block standard headless browsers---JSTOR, Google Scholar, Persée, PubMed, Academia.edu.

This skill provides the decision matrix and a 5-tier escalation ladder: ArXiv MCP → Exa → Firecrawl → Obscura → Scrapling.

---

## Structure

```
academic-research/
  SKILL.md                                 # Tool selection guide and workflows
  README.md                                # This file
  references/
    exa-academic-search.md                 # Exa parameters for academic search
    arxiv-mcp-tools.md                     # ArXiv MCP tool reference
    obscura-academic-patterns.md           # Site-specific Obscura extraction patterns
  scripts/
    academic_stealth_fetch.sh              # Stealth fetch wrapper (auto-detects site type)
```

---

## What It Covers

### Tool Selection Matrix

| Task | Exa | ArXiv MCP | Obscura |
|------|-----|-----------|---------|
| Broad topic discovery | Yes | No | No |
| Find papers by meaning | Yes | No | No |
| Filter by date range | Yes | Limited | No |
| Download full paper | No | Yes | No |
| Read paper content | No | Yes | No |
| Citation analysis | No | Yes | No |
| Non-ArXiv sources | Yes | No | Yes |
| Category filtering | Yes (6+ sources) | Yes (ArXiv) | No |
| Bot-protected sites | No | No | Yes |
| Batch stealth scrape | No | No | Yes |

### Exa Academic Search

Key parameters for academic queries:
- `category: "research_paper"` --- filter to academic content
- `includeDomains: ["arxiv.org", "scholar.google.com", "semanticscholar.org"]`
- `startPublishedDate` / `endPublishedDate` --- time-bounded discovery
- `numResults` --- control breadth (5 for focused, 20 for survey)

### ArXiv Categories

| Category | Domain |
|----------|--------|
| `cs.AI` | Artificial Intelligence |
| `cs.CL` | Computation and Language (NLP) |
| `cs.CV` | Computer Vision |
| `cs.LG` | Machine Learning |
| `cs.NE` | Neural and Evolutionary Computing |
| `stat.ML` | Statistics: Machine Learning |

### Workflow: Literature Review

```
1. Exa broad search (20 results, research_paper category)
2. Filter by relevance and date
3. ArXiv MCP download top candidates
4. Read full papers for depth
5. Trace citations for related work
6. Synthesize findings
```

---

## Requirements

- Exa API key (`EXA_API_KEY` environment variable)
- ArXiv MCP server configured
- No additional dependencies

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/research/academic-research ~/.claude/skills/
```
