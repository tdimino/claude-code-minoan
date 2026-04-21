# RLAMA

Build and query fully local RAG knowledge bases from documents---PDF, Markdown, code, HTML, CSV, and more---using RLAMA and Ollama. No cloud, no data leaving the machine. Retrieve-only mode returns raw chunks for Claude to synthesize; optional local or cloud synthesis for standalone use.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Semantic search over local documents is a common need---research papers, project docs, personal notes, codebases. RLAMA provides fully offline RAG with Ollama as the embedding and inference backend. This skill adds retrieve-only mode (best quality when Claude is in the loop), benchmarking, resilient indexing, batch ingestion, deduplication, and progress monitoring on top of the core RLAMA CLI.

---

## Structure

```
rlama/
  SKILL.md                          # Full usage guide with all commands
  README.md                         # This file
  references/
    rlama-commands.md               # Complete CLI reference
  scripts/
    rlama_retrieve.py               # Retrieve chunks (default mode) + optional synthesis
    rlama_query.py                  # Local LLM query wrapper
    rlama_manage.py                 # Create/delete/manage RAGs programmatically
    rlama_batch_ingest.py           # Batch ingest multiple folders
    rlama_resilient.py              # Resilient indexing (skips problem files)
    rlama_dedupe.py                 # Deduplicate chunks in a collection
    rlama_rebuild_deduped.py        # Rebuild collection after deduplication
    rlama_bench.py                  # Benchmark retrieval and synthesis quality
    rlama_list.py                   # List collections with details
    rlama_status.py                 # Monitor active operations
    rlama_logger.py                 # Structured logging utilities
```

---

## Usage

### Query (Default: Retrieve-Only)

Retrieve-only is the default---Claude synthesizes far better answers than local 7B models.

```bash
# Retrieve top 10 chunks for Claude to read
python3 rlama_retrieve.py <rag-name> "your query"

# More chunks for broad queries
python3 rlama_retrieve.py <rag-name> "your query" -k 20

# JSON output
python3 rlama_retrieve.py <rag-name> "your query" --json

# List collections with cache status
python3 rlama_retrieve.py --list
```

### Create a RAG

```bash
# Index a folder
rlama rag llama3.2 my-docs ~/Documents

# With exclusions
rlama rag llama3.2 codebase ./src --exclude-dir=node_modules,dist

# Semantic chunking
rlama rag llama3.2 papers ~/Papers --chunking=semantic

# Resilient mode (skips files that fail)
python3 rlama_resilient.py create research ~/Papers
```

### Manage Documents

```bash
rlama add-docs my-docs ~/Notes/new-notes    # Add documents
rlama remove-doc my-docs old-note.md         # Remove a document
rlama list                                    # List all RAGs
rlama list-docs my-docs                       # List documents in a RAG
```

---

## Synthesis Tiers

| Tier | Method | Quality |
|------|--------|---------|
| **Best** | Retrieve-only, Claude synthesizes | Strongest (default) |
| Good | `--synthesize` via OpenRouter/Claude | Strong, cited |
| Decent | `--synthesize` via TogetherAI | Solid for factual |
| Reasoning | `--synthesize --reasoning` (Qwen 3.5 9B) | Best local option |
| Local | `--synthesize --provider ollama` | Basic |
| Baseline | `rlama_query.py` (built-in) | Weakest |

```bash
# Cloud synthesis via OpenRouter
python3 rlama_retrieve.py <rag> "query" --synthesize --synth-model anthropic/claude-sonnet-4

# Local reasoning mode (Qwen 3.5 9B, strict citations)
python3 rlama_retrieve.py <rag> "query" --synthesize --reasoning
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `rlama_retrieve.py` | Retrieve chunks + optional synthesis (primary interface) |
| `rlama_query.py` | Local LLM query wrapper (fallback) |
| `rlama_manage.py` | Programmatic RAG creation and management |
| `rlama_batch_ingest.py` | Ingest multiple folders in one run |
| `rlama_resilient.py` | Index with file-level error skipping |
| `rlama_dedupe.py` | Find and remove duplicate chunks |
| `rlama_rebuild_deduped.py` | Rebuild collection post-deduplication |
| `rlama_bench.py` | Benchmark retrieval precision and synthesis quality |
| `rlama_list.py` | List collections with document counts |
| `rlama_status.py` | Monitor active indexing operations |
| `rlama_logger.py` | Structured JSON logging utilities |

---

## Supported File Types

Text (`.txt`, `.md`), Documents (`.pdf`, `.docx`), Code (`.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.rb`, `.cpp`, `.c`, `.h`), Data (`.json`, `.yaml`, `.csv`), Web (`.html`), Org-mode (`.org`).

---

## Setup

### Prerequisites

- Ollama running locally (`brew services start ollama` or `ollama serve`)
- RLAMA CLI (`go install` or binary)
- Python 3.9+ (for skill scripts)
- `pip install requests numpy` (for `rlama_retrieve.py`)

### Data Storage

RAG collections stored in `~/.rlama/` by default. Override with `RLAMA_DATA_DIR` or `--data-dir`.

---

## Related Skills

- **`linkedin-export`**: Ingests LinkedIn data into an RLAMA collection via `li_ingest.py`.
- **`llama-cpp`**: Direct GGUF inference---pairs with RLAMA for custom model configs.
- **`scrapling`**: Web scraping to feed documents into RLAMA collections.

---

## Requirements

- Ollama
- RLAMA CLI
- Python 3.9+
- `requests`, `numpy`

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/rlama ~/.claude/skills/
```
