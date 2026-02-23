# Screenshot Auto-Rename Daemon

A launchd daemon that watches for CleanShot and macOS screenshots, describes them with a vision model, and renames to `YYYY-MM-DD-slug[@Nx].ext`.

## How It Works

1. **launchd** watches `~/Desktop/Screencaps & Chats/` and its `Screenshots/` subfolder via `WatchPaths`
2. When a new file appears, it spawns `minoan-screenshot-rename`
3. The daemon scans both directories for unprocessed files matching CleanShot/macOS screenshot patterns
4. Renamed files are always moved into the `Screenshots/` subfolder
4. Each image is downscaled to 1024px JPEG and sent to a vision model
5. The model returns a 3-8 word description, which is slugified into a filename
6. The file is atomically renamed and logged to `INDEX.md`

```
CleanShot 2026-02-18 at 14.30.00@2x.png
    -> 2026-02-18-vscode-python-debugger-breakpoints@2x.png
```

## Quick Status Check

```bash
# Pulse check—daemon status, last rename, pending count, recent log
~/.claude/scripts/screenshot-rename/status.sh

# Or from Claude Code
uv run ~/.claude/scripts/screenshot-rename/watcher.py --dry-run
```

## Vision Providers

| Provider | Model | Cost/image | Setup |
|----------|-------|------------|-------|
| **`openrouter`** | Gemini Flash Lite (via OpenRouter) | ~$0.00005 | `OPENROUTER_API_KEY` (from `global.env`) |
| `openrouter-flash` | Gemini 2.0 Flash (via OpenRouter) | ~$0.0001 | `OPENROUTER_API_KEY` |
| `gemini-flash` | Gemini 2.0 Flash (direct) | ~$0.0001 | `GEMINI_API_KEY` |
| `gemini-pro` | Gemini 2.5 Pro (direct) | ~$0.001 | `GEMINI_API_KEY` |
| `openai` | GPT-4o-mini | ~$0.0003 | `OPENAI_API_KEY` |
| `anthropic` | Claude Sonnet 4.6 | ~$0.001 | `ANTHROPIC_API_KEY` |
| `smolvlm` | SmolVLM-2B (local) | Free | `~/.claude/skills/smolvlm/` + mlx-vlm |
| `ollama` | LLaVA (local) | Free | Ollama running on localhost |

Default: **`openrouter`** (paid tier, no rate limits, auto-resolves key from `~/.config/env/global.env`).

## Setup

```bash
# Install dependencies
cd ~/.claude/scripts/screenshot-rename
uv sync

# Configure (OpenRouter key auto-resolved from global.env or project .env files)
cp .env.example .env
# Edit .env: set PROVIDER=openrouter (default)

# Install launchd agent (replace __HOME__ with your home directory)
sed "s|__HOME__|$HOME|g" com.minoan.screenshot-rename.plist \
    > ~/Library/LaunchAgents/com.minoan.screenshot-rename.plist
mkdir -p ~/.claude/scripts/screenshot-rename/logs
launchctl load ~/Library/LaunchAgents/com.minoan.screenshot-rename.plist
```

**CleanShot X**: The daemon watches both `~/Desktop/Screencaps & Chats/` and its `Screenshots/` subfolder, so it works regardless of where CleanShot saves. Renamed files are always moved into `Screenshots/`.

## Usage

The daemon runs automatically. Take a screenshot with CleanShot or macOS, and it renames within ~5 seconds.

### Manual test

```bash
# Dry run (no actual rename)
uv run python watcher.py --test "CleanShot 2026-01-01 at 12.00.00@2x.png" --dry-run

# Process one file
uv run python watcher.py --test path/to/screenshot.png

# Override provider
uv run python watcher.py --provider openrouter-flash

# Re-process all pending screenshots
uv run python watcher.py
```

### Batch rename existing screenshots

```bash
# Preview what would be renamed (dry-run is default)
python batch-rename.py

# Actually rename all unrenamed screenshots
python batch-rename.py --execute

# Custom directory and provider
python batch-rename.py --dir ~/Desktop/Screenshots --provider gemini-flash --execute

# Rename in place (don't move to Screenshots/ subfolder)
python batch-rename.py --execute --in-place

# Parallel API calls (default: 3)
python batch-rename.py --execute --concurrency 5
```

### Legacy migration (organize.py)

```bash
python organize.py --dry-run
python organize.py --execute
```

## Files

| File | Purpose |
|------|---------|
| `watcher.py` | Main daemon: 6 vision providers, slugify, atomic rename, locked INDEX.md |
| `batch-rename.py` | Batch rename unrenamed screenshots with concurrency and dry-run support |
| `organize.py` | Legacy one-time migration of existing screenshots |
| `status.sh` | Quick pulse check: daemon state, last rename, pending count, recent errors |
| `minoan-screenshot-rename` | Shell wrapper (shows as process name in Activity Monitor) |
| `com.minoan.screenshot-rename.plist` | launchd agent config (WatchPaths, RunAtLoad) |
| `.env` | Provider selection + API keys (not committed) |
| `pyproject.toml` | Python dependencies |

## Architecture

- **Trigger-and-exit**: No resident process. launchd spawns the daemon on filesystem changes, it processes all pending files, then exits. Zero CPU/memory when idle.
- **RunAtLoad**: Catches any screenshots taken before the daemon was loaded (e.g., after reboot).
- **Atomic operations**: `O_CREAT|O_EXCL` for collision-safe filenames, `os.replace()` for atomic renames, `fcntl.flock()` for INDEX.md writes.
- **Fallback naming**: If the vision API fails, files get `screenshot-NNN` names instead of being skipped.
- **Image preprocessing**: Retina PNGs (~5MB) are downscaled to 1024px JPEG (~150KB) before API calls.
- **OpenRouter key resolution**: Auto-resolves from `OPENROUTER_API_KEY` env var, then checks `~/.config/env/global.env` and project `.env` files.

## Logs

```bash
# Daemon log (rotating, 5MB max)
tail -f ~/.claude/scripts/screenshot-rename/logs/screenshot-rename.log

# launchd stdout/stderr
tail -f ~/.claude/scripts/screenshot-rename/logs/stderr.log
```

## Daemon management

```bash
# Quick status
~/.claude/scripts/screenshot-rename/status.sh

# Check launchd state
launchctl list | grep screenshot-rename

# Manual trigger
launchctl kickstart gui/$(id -u)/com.minoan.screenshot-rename

# Reload after config changes
launchctl unload ~/Library/LaunchAgents/com.minoan.screenshot-rename.plist
launchctl load ~/Library/LaunchAgents/com.minoan.screenshot-rename.plist

# Uninstall
launchctl unload ~/Library/LaunchAgents/com.minoan.screenshot-rename.plist
rm ~/Library/LaunchAgents/com.minoan.screenshot-rename.plist
```
