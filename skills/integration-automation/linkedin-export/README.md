# LinkedIn Export

Parse, search, analyze, and export LinkedIn GDPR data from the terminal. Search messages by person or keyword, analyze your connection network, export to Markdown, and ingest into RLAMA for semantic search---all from a single parsed JSON file.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

LinkedIn's GDPR data export is a ZIP of 23 CSV files with inconsistent formats, preamble headers, and split files. This skill parses them once into structured JSON, then provides search, network analysis, Markdown export, and RLAMA ingestion on top of that single source of truth.

---

## Structure

```
linkedin-export/
  SKILL.md                          # Full usage guide with all flags
  README.md                         # This file
  references/
    linkedin-export-format.md       # CSV column documentation
  scripts/
    li_parse.py                     # Parse GDPR ZIP → structured JSON
    li_search.py                    # Search messages by person, keyword, date
    li_network.py                   # Network analysis (companies, roles, timeline)
    li_export.py                    # Export to Markdown files
    li_ingest.py                    # RLAMA ingestion for semantic search
```

---

## Workflow

```bash
# 1. Parse the export ZIP (run once)
python3 li_parse.py ~/Downloads/Basic_LinkedInDataExport_*.zip

# 2. Query the parsed data
python3 li_search.py --person "Jane Doe"
python3 li_network.py summary
python3 li_export.py all --output ~/linkedin-archive/
python3 li_ingest.py
```

---

## Scripts

| Script | Purpose | Example |
|--------|---------|---------|
| `li_parse.py` | Parse GDPR ZIP into `data/parsed.json` | `li_parse.py <export.zip>` |
| `li_search.py` | Search messages by person, keyword, date range | `li_search.py --person "Jane" --keyword "meeting"` |
| `li_network.py` | Analyze connections (companies, roles, timeline) | `li_network.py companies --top 20` |
| `li_export.py` | Export to Markdown (messages, connections, all) | `li_export.py all --output ~/archive/` |
| `li_ingest.py` | Create RLAMA collection for semantic search | `li_ingest.py` |

### Key Flags

| Flag | Script | Description |
|------|--------|-------------|
| `--person` | search | Filter by contact name |
| `--keyword` | search | Full-text message search |
| `--after`, `--before` | search | Date range filter |
| `--list-partners` | search | List all contacts sorted by message count |
| `--context N` | search | Show N messages around each match |
| `--full`, `--json` | search | Full message content, JSON output |
| `--top N` | network | Limit results (companies, roles) |
| `--by year/month` | network | Timeline grouping |
| `--format csv/json` | network export | Export format |

---

## Parsed Data

Parses 23 CSV types from the LinkedIn export:

**Core**: messages, connections, profile, positions, education, skills, endorsements, invitations, recommendations, shares, reactions, certifications

**Extended**: comments, projects, honors, organizations, volunteering, languages, events, member follows, job applications, recommendations given, inferences

---

## Setup

### Prerequisites

- Python 3.10+ (via `uv`)
- LinkedIn GDPR export ZIP (request at: LinkedIn > Settings > Data Privacy > Get a copy of your data)
- RLAMA + Ollama (optional, for semantic search via `li_ingest.py`)

---

## Related Skills

- **`rlama`**: Local RAG for semantic search over the ingested LinkedIn collection.
- **`scrapling`**: Web scraping if you need to supplement export data with public profile info.

---

## Requirements

- Python 3.10+
- `requests` (for `li_ingest.py`)
- LinkedIn GDPR export ZIP

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/linkedin-export ~/.claude/skills/
```
