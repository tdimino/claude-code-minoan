# Parakeet

Local speech-to-text via NVIDIA Parakeet TDT 0.6B V3---100% offline, 25 languages with auto-detection, 6% WER, ~30x realtime on Apple Silicon. Two modes: Handy app for push-to-talk dictation into any text field, and CLI scripts for file transcription and terminal dictation within Claude Code.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

Cloud STT APIs cost money and send audio off-machine. Parakeet V3 runs entirely locally at ~30x realtime on M4 Max with 6% word error rate---competitive with cloud services for English and 24 other European languages. The Handy app provides system-wide push-to-talk; the CLI scripts integrate transcription into Claude Code workflows.

---

## Structure

```
parakeet/
  SKILL.md                          # Full usage guide with troubleshooting
  README.md                         # This file
  references/
    parakeet-api.md                 # API reference
  scripts/
    transcribe.py                   # Transcribe audio files (NeMo backend)
    dictate.py                      # Live microphone dictation (NeMo backend)
    check_setup.py                  # Verify installation and model
    parakeet_server.py              # OpenAI-compatible STT server
```

---

## Two Modes

### 1. Handy App (Push-to-Talk)

System-wide dictation into any text field via [Handy](https://handy.computer/)---a free, open-source Tauri app with Parakeet V3 built in.

```bash
brew install --cask handy
```

- **Hotkey**: Option-Space (hold or toggle)
- Select **Parakeet V3** in Settings > Models (auto-downloads ~478 MB)
- Grant microphone + accessibility permissions

### 2. CLI Scripts (File Transcription)

```bash
# Transcribe an audio file
python3 transcribe.py ~/recordings/interview.mp3

# Live dictation from microphone
python3 dictate.py

# Check installation
python3 check_setup.py
```

Supports `.wav`, `.mp3`, `.m4a`, `.flac`, `.ogg`, `.aac`.

### 3. Server Mode (OpenAI-Compatible API)

```bash
uv run --with fastapi,uvicorn,python-multipart parakeet_server.py --port 8384
```

Exposes `POST /v1/audio/transcriptions` for integration with API clients.

---

## Performance

| System | Speed | Engine |
|--------|-------|--------|
| Handy (M4 Max) | ~30x realtime | transcribe-rs / ONNX int8 |
| Handy (Zen 3) | ~20x realtime | transcribe-rs / ONNX int8 |
| Handy (Skylake i5) | ~5x realtime | transcribe-rs / ONNX int8 |
| NeMo CLI (MPS) | varies | NeMo / PyTorch |

---

## Setup

### Handy (Push-to-Talk)

```bash
brew install --cask handy
```

No other dependencies---standalone app.

### CLI Scripts

- Python 3.10+ with NeMo toolkit (`nemo_toolkit[asr]>=2.0.0`)
- PyTorch 2.0+ (for MPS acceleration on Apple Silicon)
- Parakeet Dictate repo at `$PARAKEET_HOME` (default: `~/Programming/parakeet-dictate`)

---

## Related Skills

- **`smolvlm`**: Local vision-language model---same philosophy (offline, Apple Silicon, no API key).
- **`llama-cpp`**: Local LLM inference---pairs with Parakeet for voice-to-text-to-LLM pipelines.

---

## Requirements

- macOS with Apple Silicon (Handy + CLI) or any platform (CLI only with CPU fallback)
- Handy: `brew install --cask handy`
- CLI: Python 3.10+, NeMo, PyTorch 2.0+

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/parakeet ~/.claude/skills/
```
