# RLAMA CLI Reference

Complete command reference for RLAMA v0.1.39+.

## Global Flags

These flags work with any command:

| Flag | Description |
|------|-------------|
| `--data-dir <path>` | Custom directory for RLAMA data (default: `~/.rlama`) |
| `--host <host>` | Ollama host (overrides `OLLAMA_HOST`) |
| `--port <port>` | Ollama port |
| `-m, --model <model>` | Model for LLM operations (default: `qwen3:8b`) |
| `--num-thread <n>` | Number of threads for Ollama |
| `-v, --verbose` | Enable verbose output |
| `--version` | Display version |

## Core Commands

### `rlama rag` - Create RAG

Create a new RAG system by indexing documents.

```bash
rlama rag <model> <rag-name> <folder-path> [flags]
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `--chunking` | `hybrid` | Strategy: `fixed`, `semantic`, `hybrid`, `hierarchical` |
| `--chunk-size` | `1000` | Characters per chunk |
| `--chunk-overlap` | `200` | Overlap between chunks |
| `--exclude-dir` | - | Directories to exclude (comma-separated) |
| `--exclude-ext` | - | File extensions to exclude |
| `--process-ext` | - | Only process these extensions |
| `--disable-reranker` | - | Disable reranking |
| `--reranker-model` | - | Model for reranking |
| `--reranker-threshold` | - | Minimum score threshold |
| `--reranker-weight` | `0.7` | Weight for reranker vs vector scores |
| `--profile` | - | API profile for OpenAI models |

**Examples:**

```bash
# Basic
rlama rag llama3.2 my-docs ~/Documents

# With exclusions
rlama rag llama3.2 codebase ./src --exclude-dir=node_modules,dist --exclude-ext=.log

# Semantic chunking
rlama rag llama3.2 papers ./research --chunking=semantic --chunk-size=1500

# Hugging Face model
rlama rag hf.co/username/repo:Q4_K_M my-rag ./docs

# OpenAI model (requires OPENAI_API_KEY)
rlama rag gpt-4-turbo my-rag ./docs
```

---

### `rlama run` - Query RAG

Run queries against a RAG system.

```bash
rlama run <rag-name> [flags]
```

**Flags:**

| Flag | Default | Description |
|------|---------|-------------|
| `-q, --query` | - | Non-interactive query |
| `--context-size` | `20` | Number of chunks for context |
| `--show-context` | - | Show retrieved chunks |
| `--print-chunks` | - | Print chunks used |
| `--temperature` | `0.7` | Sampling temperature |
| `--max-tokens` | - | Max tokens to generate |
| `--stream` | `true` | Stream output |
| `--auto-retrieval` | - | Use model's built-in retrieval |
| `-g, --gui` | - | Use GUI mode |
| `--prompt` | - | Custom prompt template |
| `--profile` | - | API profile for OpenAI |

**Examples:**

```bash
# Interactive mode
rlama run my-docs

# Non-interactive query
rlama run my-docs --query "What is the main idea?"

# High context for complex questions
rlama run my-docs --query "Explain the architecture" --context-size=30

# Show sources
rlama run my-docs --query "What are the steps?" --show-context

# Different model
rlama run my-docs --query "Summarize" -m deepseek-r1:8b
```

---

### `rlama list` - List RAGs

List all available RAG systems.

```bash
rlama list
```

**Output format:**
```
NAME      MODEL     CREATED ON           DOCUMENTS  SIZE
my-docs   llama3.2  2026-01-29 11:23:17  5          4.06 KB
research  llama3.2  2026-01-28 09:15:00  12         125 KB
```

---

### `rlama list-docs` - List Documents

List documents in a RAG.

```bash
rlama list-docs <rag-name>
```

---

### `rlama list-chunks` - Inspect Chunks

View chunks for debugging.

```bash
rlama list-chunks <rag-name> [--document=<filename>]
```

---

### `rlama add-docs` - Add Documents

Add documents to an existing RAG.

```bash
rlama add-docs <rag-name> <folder-path> [flags]
```

**Flags:** Same chunking and exclusion flags as `rlama rag`.

**Examples:**

```bash
rlama add-docs my-docs ~/Notes/new-notes
rlama add-docs research ./paper.pdf
rlama add-docs codebase ./src --exclude-dir=tests
```

---

### `rlama remove-doc` - Remove Document

Remove a document from a RAG.

```bash
rlama remove-doc <rag-name> <doc-id> [--force]
```

**Examples:**

```bash
rlama remove-doc my-docs old-note.md
rlama remove-doc research outdated.pdf --force
```

---

### `rlama delete` - Delete RAG

Delete a RAG system.

```bash
rlama delete <rag-name>
```

---

### `rlama update-model` - Change Model

Update the model used by a RAG.

```bash
rlama update-model <rag-name> <new-model>
```

**Example:**

```bash
rlama update-model my-docs deepseek-r1:8b
```

---

## Web Commands

### `rlama crawl-rag` - Create from Website

Create a RAG from website content.

```bash
rlama crawl-rag <model> <rag-name> <url>
```

---

### `rlama crawl-add-docs` - Add Website Content

Add website content to existing RAG.

```bash
rlama crawl-add-docs <rag-name> <url>
```

---

## Watch Commands

### `rlama watch` - Enable Watching

Watch a directory for changes.

```bash
rlama watch <rag-name> <folder-path>
```

### `rlama check-watched` - Check for Updates

```bash
rlama check-watched <rag-name>
```

### `rlama watch-off` - Disable Watching

```bash
rlama watch-off <rag-name>
```

### `rlama web-watch` - Watch Website

```bash
rlama web-watch <rag-name> <url>
```

### `rlama web-watch-off` - Stop Website Watch

```bash
rlama web-watch-off <rag-name>
```

---

## Reranking Commands

### `rlama add-reranker` - Enable Reranking

```bash
rlama add-reranker <rag-name> [--reranker-model=<model>]
```

### `rlama update-reranker` - Configure Reranker

```bash
rlama update-reranker <rag-name> [--reranker-weight=0.8]
```

---

## API Server

### `rlama api` - Start API Server

```bash
rlama api --port 11249
```

**Endpoints:**

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rag` | Query a RAG |
| GET | `/health` | Health check |
| GET | `/list` | List RAGs |

**Example request:**

```bash
curl -X POST http://localhost:11249/rag \
  -H "Content-Type: application/json" \
  -d '{
    "rag_name": "my-docs",
    "prompt": "What is the main idea?",
    "context_size": 20
  }'
```

---

## Utility Commands

### `rlama wizard` - Interactive Setup

Guided RAG creation wizard.

```bash
rlama wizard
```

### `rlama agent` - AI Agent Mode

Run an AI agent with optional RAG.

```bash
rlama agent <rag-name>
```

### `rlama chunk-eval` - Evaluate Chunking

Evaluate chunking strategies for documents.

```bash
rlama chunk-eval <file-path>
```

### `rlama hf-browse` - Browse Hugging Face

Browse GGUF models on Hugging Face.

```bash
rlama hf-browse
```

### `rlama run-hf` - Run HF Model

Run a Hugging Face GGUF model with Ollama.

```bash
rlama run-hf <hf-repo>
```

### `rlama profile` - Manage Profiles

Manage API profiles for OpenAI models.

```bash
rlama profile list
rlama profile add <name>
rlama profile remove <name>
```

### `rlama install-dependencies` - Install Deps

Install optional Python dependencies (FlagEmbedding).

```bash
rlama install-dependencies
```

### `rlama update` - Update RLAMA

Check for and install updates.

```bash
rlama update
```

### `rlama uninstall` - Uninstall

Remove RLAMA and all data.

```bash
rlama uninstall
```

---

## Supported File Types

| Category | Extensions |
|----------|------------|
| Text | `.txt`, `.md`, `.markdown` |
| Documents | `.pdf`, `.docx`, `.doc` |
| Code | `.py`, `.js`, `.ts`, `.go`, `.rs`, `.java`, `.rb`, `.cpp`, `.c`, `.h`, `.cs`, `.php`, `.swift`, `.kt` |
| Data | `.json`, `.yaml`, `.yml`, `.csv`, `.xml` |
| Web | `.html`, `.htm` |
| Org | `.org` |

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OLLAMA_HOST` | Ollama server URL (e.g., `http://localhost:11434`) |
| `OPENAI_API_KEY` | OpenAI API key for GPT models |
| `RLAMA_DATA_DIR` | Custom data directory |

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | RAG not found |
| 4 | Ollama not available |
