# Parakeet

Local speech-to-text on Apple Silicon with two engines that check each other: NVIDIA Parakeet TDT v2 (via parakeet-mlx) and Qwen3-ASR 1.7B (via mlx-audio). The batch mode writes JSONL with word timestamps, confidence, provenance, and a verdict for each clip. Everything runs offline on the Metal GPU, with no NeMo, no PyTorch, and no venv to maintain.

**Last updated:** 2026-09-24

---

## Why This Skill Exists

The previous version depended on a NeMo/PyTorch venv, a NeMo model cache, and Handy's downloaded models. When those went missing, every path failed, and a Codex session gave up on it mid-task.

The rebuild uses MLX-native engines in self-contained `uv run --script` files. It also runs a second model as a cross-check, which matters whenever a transcript becomes evidence. In one run on legacy game audio, Parakeet gave implausible readings of 13 proper-noun lines ("Goal Group" for Gold Group, "Deaths are approaching" for Death Star approaching) with confidence between 0.65 and 0.98. Its confidence alone would have passed them. The disagreement with Qwen3 flagged all 13 for a human to listen to.

---

## Structure

```
parakeet/
  SKILL.md                          # Usage, status semantics, measured behavior
  README.md                         # This file
  references/
    parakeet-api.md                 # Engine APIs, JSONL schema, measured pitfalls
  scripts/
    batch_transcribe.py             # Core: both engines, JSONL manifest + meta sidecar
    transcribe.py                   # One file -> text (wrapper)
    dictate.py                      # Record from the mic until Enter, then transcribe
    check_setup.py                  # Tools/device/cache check; --load round-trips real speech
    parakeet_server.py              # OpenAI-compatible STT server, warm models
```

---

## Engines

| Engine | Model | Strength | Weakness |
|--------|-------|----------|----------|
| `parakeet` | `mlx-community/parakeet-tdt-0.6b-v2` | Fast, per-word confidence, returns empty on non-speech | No vocabulary biasing |
| `qwen3` | `mlx-community/Qwen3-ASR-1.7B-8bit` | Best open-weight WER on the Open ASR Leaderboard (4.95, 2026-09-19), hotwords | Invents fillers ("Oh.") on SFX, and can loop without a token cap |

Parakeet v2 is used rather than v3 because v2 is more accurate on English.

---

## Usage

```bash
S=~/.claude/skills/parakeet/scripts

$S/transcribe.py clip.wav                                   # text to stdout
$S/batch_transcribe.py clips/ --out manifest.jsonl          # both engines, one record per clip
$S/batch_transcribe.py clips/ --context-file vocab.txt      # Qwen3 hotwords
$S/batch_transcribe.py talk.m4a --engine qwen3 --language fr
$S/check_setup.py --load                                    # full round trip (downloads ~5 GB once)
$S/dictate.py                                               # terminal dictation
$S/parakeet_server.py --port 8384 --preload parakeet        # POST /v1/audio/transcriptions
```

### Verdicts (`--engine both`)

| Status | Meaning |
|--------|---------|
| `agreed` | Transcripts match after normalization, Parakeet confidence ≥ 0.5, and no flags are set |
| `needs_listen` | Disagreement, low or missing confidence, truncated or echo-stripped Qwen3 output, or a decode length mismatch |
| `sfx_likely` | Parakeet is empty and Qwen3 produced only fillers or a recitation of its hotwords |
| `silent` | Both engines are empty |
| `error` | Decode failed; the record carries ffmpeg's reason |

With `--out`, results stream to `<out>.partial` and are renamed when the run finishes. `<out>.meta.json` records parameters, model revisions, package versions, a hotword-list hash, the script hash, timings, and counts. One bad file never aborts a batch, but the exit status is 1 if any clip failed.

---

## Measured Behavior

Benchmarked on 351 legacy game voice and SFX resources (8-bit and 16-bit PCM at 11 kHz) and a 418 s long-form file, on an M4 Max:

| Run | Result |
|-----|--------|
| Parakeet only, 351 clips (975 s of audio) | 44 s (22x realtime) |
| Both engines, 351 clips | 91 s (11x realtime): 270 agreed, 20 needs_listen, 61 sfx_likely |
| Parakeet, 418 s long-form file | 4.8 s (88x realtime), 0.985 word similarity to per-clip ground truth |

What the benchmarks changed:

- **Short clips are padded.** Clips under 2 s get 0.75 s of silence on each side. This cut Parakeet's hallucinations on short SFX from 23 of 42 clips to 2 and lost no words on short speech.
- **Qwen3 output is capped.** On one 2.3 s SFX clip, Qwen3 looped "Oh, oh, oh…" for about 4.7 minutes. Output is now capped at `12 × duration + 32` tokens, and a clip that hits the cap is flagged.
- **Hotwords are a scalpel, not a default.** A 1,196-term vocabulary dump made Qwen3 recite the list on SFX. A focused 43-term primer silenced Qwen3 on all SFX, but it also flipped three correct "There is" lines. The recommended flow is to run without hotwords, then re-run only the `needs_listen` clips with a small primer.
- **Long audio is segmented without overlap.** parakeet-mlx 0.5.2's overlapping chunker dropped and duplicated sentences at a chunk boundary. Recordings over 5 minutes are now cut at quiet points about every 60 s and decoded independently.
- **The server keeps MLX on one thread.** MLX streams are thread-local, so a model loaded on one thread fails on another.

---

## Handy (Push-to-Talk Dictation)

For system-wide push-to-talk into any text field, use [Handy](https://github.com/cjpais/Handy) (`brew install --cask handy`, Option-Space). Version 0.9.7 or later is current. Handy is for dictation; use `batch_transcribe.py` for anything that becomes evidence.

---

## Requirements

- macOS on Apple Silicon (MLX / Metal)
- [`uv`](https://docs.astral.sh/uv/) and `ffmpeg` (`brew install uv ffmpeg`)
- About 5 GB of disk for the two models, downloaded to `~/.cache/huggingface/hub` on first use
- Dependencies are declared inline in each script (`parakeet-mlx>=0.5.2`, `mlx-audio>=0.5.5`)

---

## Related Skills

- **`smolvlm`**: Local vision-language model with the same approach (offline, Apple Silicon, no API key).
- **`llama-cpp`**: Local LLM inference, which pairs with Parakeet for voice-to-text-to-LLM pipelines.

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/integration-automation/parakeet ~/.claude/skills/
```
