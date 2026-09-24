# MLX Speech-to-Text API Reference

Engines used by `scripts/batch_transcribe.py`. Verified against parakeet-mlx 0.5.2,
mlx-audio 0.5.5–0.5.6, and mlx 0.32.2 on an M4 Max (2026-09-24).

## Default Models

| Engine | Repo | Disk | Notes |
|--------|------|------|-------|
| parakeet | `mlx-community/parakeet-tdt-0.6b-v2` | 2.5 GB (fp32 weights, bf16 at runtime) | English; beats v3 on English (Open ASR avg 5.48 vs ~6.3) |
| qwen3 | `mlx-community/Qwen3-ASR-1.7B-8bit` | 2.5 GB | Best open-weight model on Open ASR (4.95); hotword biasing |

Alternates: `mlx-community/parakeet-tdt-0.6b-v3` (25 European languages),
`mlx-community/Qwen3-ASR-1.7B-bf16` / `-4bit`. Pass with `--parakeet-model` / `--qwen3-model`.

## parakeet-mlx

```python
import mlx.core as mx
from parakeet_mlx import from_pretrained
from parakeet_mlx.audio import get_logmel
from parakeet_mlx.parakeet import Beam, DecodingConfig, Greedy

model = from_pretrained("mlx-community/parakeet-tdt-0.6b-v2")      # dtype=mx.bfloat16
# From a file (parakeet-mlx decodes with ffmpeg internally):
result = model.transcribe("clip.wav", chunk_duration=None)          # -> AlignedResult
# From a 16 kHz mono float32 array (what batch_transcribe.py does):
mel = get_logmel(mx.array(audio), model.preprocessor_config)
result = model.generate(mel, decoding_config=DecodingConfig(decoding=Beam(beam_size=4)))[0]
```

`AlignedResult(text, sentences)`, `.tokens` flattens to `AlignedToken(id, text, start,
duration, end, confidence)`. Tokens are SentencePiece pieces; a leading space starts a
word. `AlignedSentence.confidence` is the geometric mean of its token confidences.

For long audio, use `chunk_duration=120, overlap_duration=15`. `transcribe_stream()` gives a
streaming context. CLI: `uv tool install parakeet-mlx`, then
`parakeet-mlx file.wav --output-format json --highlight-words`.

## mlx-audio Qwen3-ASR

```python
from mlx_audio.stt.utils import load_model

model = load_model("mlx-community/Qwen3-ASR-1.7B-8bit")
out = model.generate(audio,                  # path, np.ndarray, mx.array, or a list of them
                     language="English",     # full name only; None = auto-detect
                                             # ("en" is NOT mapped; use qwen3_language())
                     hotwords=["Mon Calamari", "Ackbar"],
                     temperature=0.0)        # -> STTOutput(text, segments, language, ...)
```

`hotwords` are merged into the model's system prompt (`mlx_audio.stt.utils.merge_hotwords`).
The upstream model is reported to accept about 10k tokens of context, and the biasing effect
is not strictly predictable (QwenLM/Qwen3-ASR#106). Word timestamps need the separate
`Qwen3-ForcedAligner-0.6B` model, which `batch_transcribe.py` does not load.

## batch_transcribe.py JSONL Record

```json
{"path": "...", "sha256": "...", "duration_s": 1.283, "sample_rate_src": 11025,
 "codec": "pcm_u8", "samples": 20528, "peak_dbfs": -0.4, "gain_db": -0.6,
 "length_mismatch": false, "pad_s": 0.75, "hotwords": 0,
 "results": {
   "parakeet": {"model": "...", "revision": "<hf commit>", "text": "...",
                "words": [{"w": "Stay", "start": 0.08, "end": 0.32, "conf": 0.97}],
                "min_conf": 0.91},
   "qwen3": {"model": "...", "revision": "...", "text": "...", "words": [], "min_conf": null,
             "truncated": false, "echo_stripped": false}},
 "status": "agreed | needs_listen | sfx_likely | silent | null", "similarity": 1.0}
```

A clip that fails becomes `{"path": "...", "status": "error", "error": "<ffmpeg reason>"}`.
`similarity` (word-level SequenceMatcher ratio) is `null` when no comparison was made
(`silent`, `sfx_likely`, one engine). Word times are relative to the original, unpadded clip
and are clamped to its duration. `raw_text` appears on the Qwen3 result only when
`echo_stripped` fired.

Sidecar `<out>.meta.json`: `complete`, `clips`, `counts`, `audio_s`, `load_s`,
`transcribe_s`, `engines{name: {model, revision}}`, `params{language, beam, min_conf, pad,
pad_under}`, `hotwords{count, sha256}`, `versions`, `script_sha256`.

## Measured Behavior (351 Star Wars Rebellion WAVE resources)

- Input: 276 clips are 8-bit unsigned PCM and 71 are 16-bit, all at 11,025 Hz mono, plus 4
  that are 16-bit at 44.1 kHz. ffmpeg decodes them all with no special handling. When
  concatenating mixed-format clips for a test, convert each one first: the ffmpeg concat
  demuxer assumes the first file's sample format and turns the rest into noise.
- Parakeet throughput: 351 clips (975 s of audio) in about 44 s. Per-clip ffprobe and ffmpeg
  calls dominate, not the model.
- Padding clips under 2 s with 0.75 s of silence lost no words on 30 short speech clips, and
  it cut hallucinated text on short TACTICAL SFX from 23 of 42 clips to 2.
- An empty Parakeet transcript is a strong signal that a clip is SFX. Qwen3 emits a filler
  ("Oh.", "Whoa.", "Shh.") on nearly every SFX clip, and on TACTICAL 13056 it looped "Oh, oh,
  oh, ..." for about 4.7 minutes up to its 8192-token default. batch_transcribe.py caps Qwen3
  at `12 * duration_s + 32` tokens, sets `truncated` when the cap is hit, and labels a clip
  `sfx_likely` only when Parakeet is empty and Qwen3's words are all fillers.
- parakeet-mlx 0.5.2 `transcribe(chunk_duration=120, overlap_duration=15)` corrupted a 418 s
  file at a chunk boundary: it dropped "Green Group reporting...", duplicated two "Task Force"
  lines, and deleted two more. batch_transcribe.py instead cuts audio over 5 minutes at quiet
  points about every 60 s and decodes each segment independently (0.985 word similarity to
  per-clip ground truth).
- MLX 0.32 streams are thread-local. A model loaded on one thread fails on another with
  "There is no Stream(cpu, 1) in current thread", so the server runs all MLX work on a single
  dedicated thread.
