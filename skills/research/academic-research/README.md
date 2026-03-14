# Academic Research

The literature review skill. Search academic papers, download from ArXiv, and synthesize findings using Exa's neural search for broad discovery and ArXiv MCP for deep paper analysis.

**Last updated:** 2026-01-02

**Reflects:** Exa AI search API (research_paper category), ArXiv MCP server tools, and academic search patterns across 6+ reputable sources.

---

## Why This Skill Exists

Academic search requires two different tools for two different tasks: broad discovery across the web (Exa) and deep analysis of specific papers (ArXiv MCP). Exa finds papers by meaning rather than keywords and filters by category and date. ArXiv MCP downloads full papers, reads their content, and enables citation network analysis. Using the wrong tool for the job wastes time---Exa for paper content, ArXiv for discovery outside its corpus.

This skill provides the decision matrix: when to use which tool, how to combine them for literature reviews, and how to filter by domain (cs.AI, cs.CL, cs.CV, cs.LG, cs.NE, stat.ML).

---

## Structure

```
academic-research/
  SKILL.md                                 # Tool selection guide and workflows
  README.md                                # This file
  references/
    exa-academic-search.md                 # Exa parameters for academic search
    arxiv-mcp-tools.md                     # ArXiv MCP tool reference
```

---

## What It Covers

### Tool Selection Matrix

| Task | Use Exa | Use ArXiv MCP |
|------|---------|--------------|
| Broad topic discovery | Yes | No |
| Find papers by meaning | Yes | No |
| Filter by date range | Yes | Limited |
| Download full paper | No | Yes |
| Read paper content | No | Yes |
| Citation analysis | No | Yes |
| Non-ArXiv sources | Yes | No |
| Category filtering | Yes (6+ sources) | Yes (ArXiv categories) |

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
