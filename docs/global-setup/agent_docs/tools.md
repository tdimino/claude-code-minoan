# Tool Reference

## Web Scraping
- **Firecrawl**: `firecrawl --help` for web scraping to Markdown (cloud API, `FIRECRAWL_API_KEY`)
- **Jina**: `jina --help` -- use for Twitter/X (Firecrawl blocks Twitter)
- **Scrapling**: Local stealth scraping with anti-bot bypass -- `scrapling extract --help`

## Search
- **exa-search skill**: Neural web search with content extraction
- **MCP servers**: Use context7 for library docs (resolve-library-id first)

## Python
- Use `uv` for everything: `uv run`, `uv pip`, `uv venv`

## Image Editing
- **ImageMagick 7**: `magick` for resize, composite, convert, annotate
- **rembg**: Background removal -- `rembg i input.png output.png`
- **sips**: macOS built-in for quick format conversion and resize

## PDF Extraction
- **PyMuPDF**: `uv run --with pymupdf python3 -c "import fitz; ..."`
- Zoom factor: 1=96DPI, 2=192DPI, 3=288DPI

## Port Management
- **portless**: `portless <name> <cmd>` for dev server routing with `.localhost` URLs
- **port-whisperer**: `ports` for port inspection, `ports kill <port>` to free ports

## Remote Agent Dispatch
- **Takopi** (banteg/takopi): Bridges coding agents to Telegram. Send tasks from phone, stream live progress, resume sessions. Multi-engine (Claude, Codex, OpenCode, Pi), multi-project routing, git worktrees, voice transcription, file transfer.
  - Install: `uv tool install -U takopi && takopi --onboard`
  - Config: `~/.takopi/takopi.toml`
  - Core flow: Telegram message → Takopi spawns `claude -p --output-format stream-json --verbose` → streams progress → resume line for follow-ups
  - Claude runner config (`[claude]` in takopi.toml): `model`, `allowed_tools`, `dangerously_skip_permissions`, `use_api_billing`
  - Voice notes: local STT via Parakeet server at `skills/parakeet/scripts/parakeet_server.py` (OpenAI-compatible `/v1/audio/transcriptions`)
  - Docs: https://takopi.dev/

## API Keys
- All secrets in `~/.config/env/secrets.env` (chmod 600, sourced by `.zshrc`)
- Never put API keys directly in `.zshrc`
- Per-project `.env` files checked as fallback

## Temporary File Hosting
- **tmpfiles.org**: Free, no-auth temp hosting for MMS/webhooks
  - Direct download URL: replace `/12345/` with `/dl/12345/`
