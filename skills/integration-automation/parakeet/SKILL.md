---
name: parakeet
description: >
  Local speech-to-text on Apple Silicon with two cross-checking MLX engines: NVIDIA
  Parakeet TDT v2 (parakeet-mlx) and Qwen3-ASR 1.7B (mlx-audio, hotword biasing).
  Batch JSONL with word timestamps, confidence, provenance, and an agreement verdict.
  No NeMo or PyTorch. Use when transcribing audio files, identifying game or legacy
  voice clips by content, telling speech from SFX, serving an OpenAI-compatible STT
  endpoint, or dictating. For push-to-talk into any text field, use the Handy app.
argument-hint: [audio-file | directory | "dictate" | "check"]
tools: [Bash, Read, Write]
---

# Parakeet: Local Speech-to-Text (MLX)

Two MLX engines run fully offline on the Metal GPU. Every script is a `uv run --script`
file with inline dependencies, so there is no venv to maintain.

| Engine | Model | Strength | Weakness |
|--------|-------|----------|----------|
| `parakeet` | `mlx-community/parakeet-tdt-0.6b-v2` | Fast, per-word confidence, returns empty on non-speech | No vocabulary biasing |
| `qwen3` | `mlx-community/Qwen3-ASR-1.7B-8bit` | Best open-weight WER (4.95, Open ASR Leaderboard 2026-09-19), `hotwords` | Hallucinates interjections on SFX; can loop without a token cap |

Run both on anything that becomes evidence. Their disagreement is the confidence signal.

## Commands

```bash
S=~/.claude/skills/parakeet/scripts

# One file -> text on stdout (parakeet engine; --engine both prints status<TAB>parakeet<TAB>qwen3)
$S/transcribe.py clip.wav

# Batch: files or directories -> JSONL manifest (both engines by default)
$S/batch_transcribe.py clips/ --out manifest.jsonl
$S/batch_transcribe.py clips/ --context-file vocab.txt       # Qwen3 hotwords, one per line
$S/batch_transcribe.py a.wav --engine qwen3 --language auto  # or a name / ISO code (fr, French)
$S/batch_transcribe.py a.wav --engine parakeet --beam 4      # beam search

# Setup check (fast), or full round trip with synthesized speech (downloads ~5 GB once)
$S/check_setup.py
$S/check_setup.py --load

# Terminal dictation: record until Enter, then transcribe
$S/dictate.py

# OpenAI-compatible server (warm models; model ids: parakeet-tdt-0.6b, qwen3-asr)
$S/parakeet_server.py --port 8384 --preload parakeet
```

Formats: anything ffmpeg decodes (wav incl. 8-bit/ADPCM, mp3, m4a, flac, ogg, aac, webm, aiff).

## Batch Output and Status

Each JSONL record holds the source `sha256`, `duration_s`, `sample_rate_src`, `codec`, the
decode check (`samples`, `peak_dbfs`, `gain_db`, `length_mismatch`), and per-engine `text`,
`model`, and HF `revision`. Parakeet adds `words[{w,start,end,conf}]` and `min_conf`. Qwen3
adds `truncated` and `echo_stripped` (with `raw_text` when it fired). With `--engine both`,
each record gets a `status`:

| Status | Meaning | Action |
|--------|---------|--------|
| `agreed` | Normalized transcripts match, Parakeet `min_conf` ≥ `--min-conf` (0.5), no flag set | Corroborated; still cite as ASR evidence |
| `needs_listen` | Anything else containing words: a disagreement, low or missing confidence, a truncated or echo-stripped Qwen3 result, a length mismatch | A person listens before citing |
| `sfx_likely` | Parakeet empty; Qwen3 produced only interjections ("Oh.", "Whoa.", a loop of them) or only recited its hotwords | Treat as non-speech |
| `silent` | Both engines empty | Non-speech |
| `error` | Decode or transcription failed; `error` carries ffmpeg's reason | Fix the file or exclude it |

One-word lines that are plausible speech ("Fire!", "Okay.") are never `sfx_likely`.
Normalization lowercases, strips punctuation, and folds number words ("One" → "1") and
spelling variants ("manoeuvre" → "maneuver").

With `--out`, records stream to `<out>.partial`. That file is renamed only when the run
completes, and `<out>.meta.json` records the parameters, model revisions, package versions, a
hotword-list hash, the script's sha256, timings, and counts. One bad file never ends a batch,
but the exit status is 1 if any clip errored. Schema and API notes: `references/parakeet-api.md`.

## Short Clips and Legacy Game Audio

Measured on 351 Star Wars Rebellion WAVE resources: 276 are 8-bit PCM and 71 are 16-bit, all at
11,025 Hz, plus 4 that are 16-bit at 44.1 kHz.

- **Padding.** Clips under 2 s get 0.75 s of silence on each side. This lost no words across 30
  short speech clips. It cut Parakeet's hallucinations on short TACTICAL SFX from 23 of 42 clips
  to 2 (unpadded: "Me, me, me.", "Ha ha ha ha!"). Use `--pad 0` to disable.
- **Qwen3 loops.** On one 2.3 s SFX clip Qwen3 produced "Oh, oh, oh, ..." for about 4.7 minutes,
  up to its 8192-token default. Tokens are now capped at `12 * duration_s + 32`, and a clip that
  hits the cap is marked `truncated`.
- **Hotwords are a targeted tool, not a default.** Measured on the same corpus:
  - A 1,196-term dump of every game UI string made Qwen3 recite the list on SFX ("0 Points
    Available, 1 Construction Yards, ...") and doubled prefill time. Whole-output recitations
    are detected (`echo_stripped`), but words inside real speech are never removed.
  - A focused 43-term proper-noun primer made Qwen3 return *empty* on all 63 SFX clips, which is
    the cleanest speech/SFX split. On speech it changed "Censors" to "Sensors" but flipped three
    "There is" lines to "That is" (Parakeet and unprimed Qwen3 agree on "There is").
  - Workflow: run without hotwords first, then re-run only the `needs_listen` clips with a small
    primer as a third opinion. Use a primer on the full run when the goal is SFX triage.
- **Levels.** ffmpeg resamples to 16 kHz mono and peak-normalizes to -1 dBFS. Audio below
  -60 dBFS is left unamplified, because amplifying a noise floor feeds hallucination.

## Long Audio

Recordings over 5 minutes are cut at the quietest 100 ms frame near every 60 s, and each segment
is decoded independently. parakeet-mlx 0.5.2's own overlapping chunker is not used: on a 418 s
test file it dropped a sentence and duplicated two others at a chunk boundary. The segmented
path matched the per-clip ground truth at 0.985 word similarity, with no dropped or duplicated
lines, at 88x realtime. Qwen3 uses mlx-audio's internal chunking (20-minute windows).

## Performance (M4 Max, 36 GB)

| Run | Result |
|-----|--------|
| Parakeet only, 351 clips / 975 s audio | 44 s (22x realtime; per-clip ffmpeg dominates) |
| Both engines, 351 clips | 91 s (11x realtime): 270 agreed, 20 needs_listen, 61 sfx_likely |
| Both engines + 43-term primer | 124 s (8x realtime) |

These timings come from the runs' own summary lines. Newer runs also record them in `.meta.json`.
In the two-engine run, 20 clips were `needs_listen`: 5 TACTICAL SFX-or-speech calls (including
"Yeah." and "Okay.", held because they are plausible one-word lines) and 15 speech lines. In 13 of the 15, Parakeet's reading is implausible and Qwen3's is the plausible
one ("Goal Group" vs Gold Group, "Deaths are approaching" vs Death Star approaching). No one has
listened to those clips yet, so Qwen3's text is a strong hypothesis, not ground truth. In one
clip both were wrong ("Census"/"Censors" for Sensors), and one differed only in formatting
("Task Force V" vs "Five"). Parakeet's `min_conf` on those lines ran 0.65–0.98, so confidence
alone would have passed them.

Don't run two batch jobs at once: they share the GPU, and a contended run took 5x longer.
A cold first load downloads about 2.5 GB per model into `~/.cache/huggingface/hub`.

## Handy (Push-to-Talk Dictation)

[Handy](https://github.com/cjpais/Handy) handles system-wide push-to-talk (Option-Space).
Upgrade to 0.9.7 or later with `brew upgrade --cask handy`, then pick a model in Settings.
The `handy-computer` org publishes `parakeet-unified-en-0.6b-gguf` (NVIDIA 2026-04, offline and
streaming in one model); check whether your Handy version lists it. For live multilingual
streaming, `nvidia/nemotron-3.5-asr-streaming-0.6b` (2026-06, 40 locales) is the current NVIDIA
model. Handy is for dictation, not batch evidence.

## Legacy

`~/Programming/parakeet-dictate` (NeMo/PyTorch menubar app, Voxtral backend) is superseded and has
no venv. Nothing here depends on it or on `PARAKEET_HOME`.
