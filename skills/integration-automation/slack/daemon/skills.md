# Available Skills & Tools

You have access to these tools via your `--allowedTools` configuration. Use them proactively.

## Direct Tools

| Tool | Purpose |
|------|---------|
| `Read` | Read files from the local filesystem |
| `Glob` | Find files by pattern (e.g., `**/*.py`) |
| `Grep` | Search file contents with regex |
| `Bash` | Run shell commands (git, npm, uv, etc.) |
| `WebFetch` | Fetch and analyze web content (prefer Firecrawl) |

## Web Scraping & Search

| Command | Purpose |
|---------|---------|
| `firecrawl scrape URL --only-main-content` | Scrape web page to markdown (preferred over WebFetch) |
| `firecrawl search "query"` | Web search with optional content scraping |
| `firecrawl crawl URL --wait --progress` | Crawl entire sites with progress tracking |
| `firecrawl map URL` | Discover all URLs on a site |
| `jina URL` | Fallback scraper; works on Twitter/X |

## Semantic Code & Document Search

| Command | Purpose |
|---------|---------|
| `rlama search BUCKET "query"` | Semantic search over local document/code collections (preferred) |
| `rlama list` | List available RAG buckets |

## Research

| Command | Purpose |
|---------|---------|
| `python3 ~/.claude/skills/exa-search/scripts/exa_search.py "query"` | Neural web search via Exa |
| `python3 ~/.claude/skills/exa-search/scripts/exa_research.py "query" --sources` | AI-powered research with citations |
| `python3 ~/.claude/skills/exa-search/scripts/exa_similar.py URL` | Find semantically similar pages |
| `python3 ~/.claude/skills/exa-search/scripts/exa_contents.py URL` | Extract clean content from URLs |
| `python3 ~/.claude/skills/exa-search/scripts/exa_search.py "query" --category "research paper"` | Academic paper search and literature review |

## Local ML

| Command | Purpose |
|---------|---------|
| `ollama run MODEL` / `ollama list` | Run local LLMs (Hermes, Qwen, Mistral) |
| `llama-server` / `llama-cli` | Direct llama.cpp inference with LoRA hot-loading |
| `python3 ~/.claude/skills/smolvlm/scripts/view_image.py IMAGE` | Local vision-language model (SmolVLM-2B) |
| `python3 ~/.claude/skills/nano-banana-pro/scripts/gemini_images.py` | Generate/edit images via Gemini |
| `bash ~/.claude/skills/speak-response/scripts/speak.sh "text"` | Text-to-speech via Qwen3-TTS |
| `python3 ~/.claude/skills/parakeet/scripts/transcribe.py FILE` | Speech-to-text via NVIDIA Parakeet |

## Browser & Testing

| Command | Purpose |
|---------|---------|
| `agent-browser` | Headless browser automation for live-testing web pages |
| `npx @anthropic-ai/markdown-preview FILE` | Preview markdown files rendered in browser |

## File Creation

| Command | Purpose |
|---------|---------|
| `node ~/.claude/skills/beautiful-mermaid/scripts/mermaid.mjs` | Render Mermaid diagrams as ASCII or SVG |
| `python3 -m docx` | Create Word documents |

## Infrastructure

| Command | Purpose |
|---------|---------|
| `uv run` / `uv pip` | Python package management (always use uv, never raw pip) |
| `git` | Version control |
| `gh` | GitHub CLI (PRs, issues, API) |
| `bd` | Beads task tracker (dependency-aware, cross-session) |

## Skills Repository

Your skills and configuration live in these repos:
- **Minoan (personal):** https://github.com/tdimino/claude-code-minoan
- **Aldea (work):** https://github.com/aldea-ai/Claude-Code-Aldea

Browse `skills/` in either repo for the full catalog of available SKILL.md files with detailed usage instructions.

### Skill Inventory (from claude-code-minoan)

**Core Development:**
architecture-md-builder, beads-task-tracker, claude-agent-sdk, claude-md-manager, react-best-practices, skill-optimizer

**Design & Media:**
aldea-slidedeck, frontend-design, gemini-claude-resonance, nano-banana-pro, rocaille-shader

**Local ML & Inference:**
smolvlm, speak-response, parakeet, llama-cpp, rlama

**Integration & Automation:**
agent-browser, beautiful-mermaid, codex-orchestrator, slack, twitter

**Planning & Productivity:**
claude-tracker-suite, crypt-librarian, minoan-swarm, super-ralph-wiggum

**Research:**
Firecrawl, academic-research, exa-search

### Check Installation Status

```bash
bash ~/.claude/skills/slack/daemon/check-skills.sh
```

## Important Notes

- Prefer RLAMA for semantic code/document search over all other search tools.
- Prefer Firecrawl over WebFetch for web content.
- Use `uv` for all Python operations.
- You operate as `claude -p` subprocesses — each Slack thread is a separate session.
- Your responses go back to Slack — keep them concise (2-4 sentences unless asked for more).
