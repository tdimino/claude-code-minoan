#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#     "parakeet-mlx>=0.5.2",
#     "mlx-audio>=0.5.5",
#     "numpy>=1.26",
# ]
# ///
"""Batch speech-to-text on Apple Silicon with two cross-checking MLX engines.

Engines (each model loads once per run):
  parakeet  NVIDIA Parakeet TDT via parakeet-mlx: fast, per-token confidence
  qwen3     Qwen3-ASR via mlx-audio: strongest open-weight model, accepts hotwords

Every clip is decoded by ffmpeg to 16 kHz mono float32, peak-normalized (unless
near-silent), and, when shorter than --pad-under seconds, padded with silence on
both sides. Measured on 351 Star Wars Rebellion WAVE resources: padding lost no
words on short speech and suppressed most hallucinated text on short SFX.

Output is JSONL, one record per clip. With --engine both, `status` is:
  agreed        normalized transcripts match, Parakeet confidence >= --min-conf,
                and no engine flag (truncated, echo stripped, length mismatch)
  needs_listen  anything else with speech in it
  sfx_likely    Parakeet empty; Qwen3 produced only interjections ("Oh.", a loop
                of them) or only a recitation of the hotword list
  silent        both engines returned no text
  error         the clip could not be decoded or transcribed (see `error`)
ASR output is evidence to verify by listening, never an authoritative label.

With --out, records stream to <out>.partial, which is renamed to <out> only when
the run finishes; <out>.meta.json records parameters, versions, and counts. The
exit status is 1 if any clip errored.

Usage:
  batch_transcribe.py clips/ --out manifest.jsonl
  batch_transcribe.py a.wav b.wav --engine parakeet --text
  batch_transcribe.py voices/ --context-file vocab.txt --engine both
"""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

import numpy as np

SAMPLE_RATE = 16_000
QWEN3_TOKENS_PER_S = 12  # about 2x the fastest speech rate
NEAR_SILENT_PEAK = 1e-3  # -60 dBFS: below this, amplifying only feeds hallucination
LONG_AUDIO_S = 300.0  # above this, Parakeet decodes ~60 s segments cut at quiet points
AUDIO_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".oga", ".aac", ".webm", ".aif", ".aiff"}
DEFAULT_MODELS = {
    "parakeet": "mlx-community/parakeet-tdt-0.6b-v2",
    "qwen3": "mlx-community/Qwen3-ASR-1.7B-8bit",
}
# Qwen3-ASR matches full language names only; map ISO 639-1 codes onto them.
QWEN3_LANGUAGES = {
    "zh": "Chinese", "en": "English", "yue": "Cantonese", "ar": "Arabic", "de": "German",
    "fr": "French", "es": "Spanish", "pt": "Portuguese", "id": "Indonesian", "it": "Italian",
    "ko": "Korean", "ru": "Russian", "th": "Thai", "vi": "Vietnamese", "ja": "Japanese",
    "tr": "Turkish", "hi": "Hindi", "ms": "Malay", "nl": "Dutch", "sv": "Swedish",
    "da": "Danish", "fi": "Finnish", "pl": "Polish", "cs": "Czech", "fil": "Filipino",
    "tl": "Filipino", "fa": "Persian", "el": "Greek", "ro": "Romanian", "hu": "Hungarian",
    "mk": "Macedonian",
}
# Non-speech fillers Qwen3 emits on SFX. Deliberately excludes words that are
# plausible one-word lines ("okay", "yeah", "no", "fire").
INTERJECTIONS = {"oh", "ah", "aah", "ooh", "whoa", "wow", "hmm", "huh", "uh", "um", "shh",
                 "splat", "ha", "the", "so"}


class ClipError(Exception):
    """A clip that cannot be decoded; carries the tool's own explanation."""


@dataclass
class Clip:
    path: Path
    sha256: str
    duration_s: float
    sample_rate_src: int
    codec: str
    audio: np.ndarray  # 16 kHz mono float32, normalized and padded
    pad_s: float
    samples: int  # decoded samples before padding
    peak_dbfs: float | None
    gain_db: float
    length_mismatch: bool  # decoded length differs from the container duration by > 5%


def qwen3_language(value: str | None) -> str | None:
    """Map 'auto', ISO codes, or names onto a Qwen3 language name; None means auto-detect."""
    if value is None or value.lower() in {"", "auto"}:
        return None
    if value.lower() in QWEN3_LANGUAGES:
        return QWEN3_LANGUAGES[value.lower()]
    names = {name.lower(): name for name in QWEN3_LANGUAGES.values()}
    if value.lower() in names:
        return names[value.lower()]
    raise ValueError(f"unsupported Qwen3 language {value!r}; use a name, an ISO 639-1 code, or 'auto'")


def run_tool(cmd: list[str], text: bool) -> subprocess.CompletedProcess:
    result = subprocess.run(cmd, capture_output=True, text=text)
    if result.returncode != 0:
        stderr = result.stderr if text else result.stderr.decode(errors="replace")
        raise ClipError(f"{cmd[0]} failed: {stderr.strip() or f'exit {result.returncode}'}")
    return result


def probe(path: Path) -> tuple[int, str, float | None]:
    """Return (sample_rate, codec, duration_s or None) of the first audio stream."""
    out = run_tool(["ffprobe", "-v", "error", "-select_streams", "a:0",
                    "-show_entries", "stream=sample_rate,codec_name:format=duration",
                    "-of", "json", str(path)], text=True)
    info = json.loads(out.stdout)
    if not info.get("streams"):
        raise ClipError("no audio stream")
    stream = info["streams"][0]
    try:
        duration = float(info.get("format", {}).get("duration"))
    except (TypeError, ValueError):
        duration = None  # e.g. "N/A"; fall back to the decoded length
    return int(stream["sample_rate"]), stream["codec_name"], duration


def load_clip(path: Path, pad_under: float, pad_s: float) -> Clip:
    sample_rate, codec, probed = probe(path)
    raw = run_tool(["ffmpeg", "-nostdin", "-v", "error", "-i", str(path),
                    "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "f32le", "-"], text=False).stdout
    audio = np.frombuffer(raw, dtype=np.float32).copy()
    if audio.size == 0:
        raise ClipError("decoded 0 samples")
    decoded = audio.size / SAMPLE_RATE
    duration = probed if probed is not None else decoded
    peak = float(np.max(np.abs(audio)))
    gain = 1.0
    if peak >= NEAR_SILENT_PEAK:
        gain = 0.89 / peak  # -1 dBFS
        audio *= gain
    applied_pad = pad_s if duration < pad_under else 0.0
    if applied_pad:
        silence = np.zeros(int(applied_pad * SAMPLE_RATE), dtype=np.float32)
        audio = np.concatenate([silence, audio, silence])
    return Clip(path, hashlib.sha256(path.read_bytes()).hexdigest(), round(duration, 3), sample_rate,
                codec, audio, applied_pad, int(decoded * SAMPLE_RATE),
                round(20 * np.log10(peak), 1) if peak > 0 else None, round(20 * np.log10(gain), 1),
                abs(decoded - duration) > 0.05 * max(duration, 1e-9))


def model_revision(repo_id: str) -> str | None:
    """Commit hash of the cached Hugging Face snapshot, if resolvable offline."""
    from huggingface_hub import snapshot_download
    from huggingface_hub.errors import LocalEntryNotFoundError

    try:
        return Path(snapshot_download(repo_id, local_files_only=True)).name
    except (LocalEntryNotFoundError, OSError) as error:
        print(f"warning: no revision for {repo_id}: {error}", file=sys.stderr)
        return None


class ParakeetEngine:
    name = "parakeet"

    def __init__(self, repo_id: str, beam: int):
        from parakeet_mlx import from_pretrained
        from parakeet_mlx.parakeet import Beam, DecodingConfig, Greedy

        self.repo_id = repo_id
        self.model = from_pretrained(repo_id)
        self.config = DecodingConfig(decoding=Beam(beam_size=beam) if beam > 1 else Greedy())
        self.revision = model_revision(repo_id)

    def _decode(self, audio: np.ndarray):
        import mlx.core as mx
        from parakeet_mlx.audio import get_logmel

        mel = get_logmel(mx.array(audio), self.model.preprocessor_config)
        return self.model.generate(mel, decoding_config=self.config)[0]

    def transcribe(self, clip: Clip) -> dict:
        # Long recordings are cut at quiet points and decoded independently. parakeet-mlx
        # 0.5.2's own overlap chunking dropped, duplicated, and reordered sentences at
        # chunk boundaries in a 431 s test, so it is not used.
        texts, tokens = [], []
        for offset, segment in split_at_quiet_points(clip.audio):
            result = self._decode(segment)
            texts.append(result.text)
            tokens.extend((token, offset) for token in result.tokens)
        words: list[dict] = []
        for token, offset in tokens:
            # SentencePiece marks word starts with a leading space.
            if not words or token.text.startswith(" "):
                words.append({"w": token.text.strip(), "start": token.start + offset,
                              "end": token.end + offset, "conf": token.confidence})
            else:
                words[-1]["w"] += token.text
                words[-1]["end"] = token.end + offset
                words[-1]["conf"] = min(words[-1]["conf"], token.confidence)
        for word in words:
            # Map back to the unpadded clip; a final token can run into the trailing pad.
            word["start"] = round(min(max(0.0, word["start"] - clip.pad_s), clip.duration_s), 3)
            word["end"] = round(min(max(0.0, word["end"] - clip.pad_s), clip.duration_s), 3)
            word["conf"] = round(float(word["conf"]), 4)
        words = [w for w in words if w["w"]]
        confidence = min((w["conf"] for w in words), default=None)
        return {"model": self.repo_id, "revision": self.revision,
                "text": " ".join(t for t in texts if t), "words": words, "min_conf": confidence}


def split_at_quiet_points(audio: np.ndarray, target_s: float = 60.0,
                          search_s: float = 10.0) -> list[tuple[float, np.ndarray]]:
    """Split audio longer than LONG_AUDIO_S into ~target_s segments, cutting at the quietest
    100 ms frame within ±search_s of each target so cuts land between words. Returns
    (offset_seconds, segment) pairs; shorter audio is returned whole.
    """
    if audio.size <= LONG_AUDIO_S * SAMPLE_RATE:
        return [(0.0, audio)]
    frame = SAMPLE_RATE // 10
    cuts, start = [0], 0
    while audio.size - start > (target_s + search_s) * SAMPLE_RATE:
        lo = start + int((target_s - search_s) * SAMPLE_RATE)
        hi = start + int((target_s + search_s) * SAMPLE_RATE)
        window = audio[lo:hi][: (hi - lo) // frame * frame].reshape(-1, frame)
        quietest = int(np.argmin(np.sqrt(np.mean(window ** 2, axis=1))))
        start = lo + quietest * frame + frame // 2
        cuts.append(start)
    cuts.append(audio.size)
    return [(a / SAMPLE_RATE, audio[a:b]) for a, b in zip(cuts, cuts[1:], strict=False)]


class Qwen3Engine:
    name = "qwen3"

    def __init__(self, repo_id: str, hotwords: list[str], language: str | None):
        from mlx_audio.stt.utils import load_model

        self.repo_id = repo_id
        self.model = load_model(repo_id)
        self.hotwords = hotwords or None
        self.language = qwen3_language(language)
        self.revision = model_revision(repo_id)

    def transcribe(self, clip: Clip) -> dict:
        # Qwen3 can loop on non-speech ("Oh, oh, oh, ..." to the 8192-token default).
        # Speech stays under ~6 tokens/s, so a duration-scaled cap bounds the damage.
        max_tokens = int(QWEN3_TOKENS_PER_S * clip.duration_s) + 32
        out = self.model.generate(clip.audio, hotwords=self.hotwords, language=self.language,
                                  max_tokens=max_tokens)
        raw = out.text.strip()
        echoed = is_context_echo(raw, self.hotwords or [])
        result = {"model": self.repo_id, "revision": self.revision, "text": "" if echoed else raw,
                  "words": [], "min_conf": None, "truncated": out.generation_tokens >= max_tokens,
                  "echo_stripped": echoed}
        if echoed:
            result["raw_text"] = raw
        return result


def is_context_echo(text: str, hotwords: list[str]) -> bool:
    """True when the output recites the hotword prompt instead of transcribing (QwenLM/Qwen3-ASR#106).

    Only whole outputs are judged, never words inside them: an echo is at least five
    list segments, 80% of which are hotword entries ("0 Points Available, 1 Construction
    Yards, ..."). Short spoken lists ("Hoth, Endor, Yavin.") stay intact.
    """
    if not hotwords or not text:
        return False

    def key(phrase: str) -> str:
        return re.sub(r"^\d+ ", "", normalize(phrase))  # "1 Construction Yards" ~ "Construction Yards"

    segments = [key(s) for s in re.split(r"[,\n;]", text) if key(s)]
    known = {key(h) for h in hotwords}
    return len(segments) >= 5 and sum(s in known for s in segments) >= 0.8 * len(segments)


NUMBER_WORDS = {word: str(n) for n, word in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve thirteen "
    "fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}


# British/American and spacing variants the two engines disagree on without meaning to.
SPELLING_VARIANTS = {"manoeuvre": "maneuver", "manoeuvres": "maneuvers", "manoeuvring": "maneuvering",
                     "defence": "defense", "armour": "armor", "colour": "color",
                     "anytime": "any time", "okay": "ok", "superlaser": "super laser"}


def normalize(text: str) -> str:
    """Lowercase, strip punctuation, and fold number words and spelling variants."""
    text = text.lower().replace("-", " ")
    text = re.sub(r"[^\w\s']", " ", text)
    words = (SPELLING_VARIANTS.get(word, word) for word in text.split())
    return " ".join(NUMBER_WORDS.get(word, word) for word in " ".join(words).split())


def judge(results: dict[str, dict], min_conf: float,
          suspect: bool = False) -> tuple[str | None, float | None]:
    """Status and word-level similarity for a two-engine result; (None, None) for one engine.

    `suspect` marks a clip whose decode looked wrong (length mismatch); it never agrees.
    """
    if len(results) < 2:
        return None, None
    parakeet, qwen3 = results["parakeet"], results["qwen3"]
    a, b = normalize(parakeet["text"]), normalize(qwen3["text"])
    if not a and not b:
        return ("sfx_likely" if qwen3.get("echo_stripped") else "silent"), None
    if not a and set(b.split()) <= INTERJECTIONS:
        return "sfx_likely", None  # Parakeet hears nothing; Qwen3 fills in "Oh." or loops on it
    similarity = round(difflib.SequenceMatcher(None, a.split(), b.split()).ratio(), 4)
    conf = parakeet.get("min_conf")
    flagged = suspect or qwen3.get("truncated") or qwen3.get("echo_stripped")
    agreed = a == b and conf is not None and conf >= min_conf and not flagged
    return ("agreed" if agreed else "needs_listen"), similarity


def collect(inputs: list[str]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        path = Path(item).expanduser()
        if path.is_dir():
            paths.extend(sorted(p for p in path.rglob("*")
                                if p.suffix.lower() in AUDIO_SUFFIXES and not p.name.startswith("._")))
        elif path.is_file():
            paths.append(path)
        else:
            sys.exit(f"error: not found: {item}")
    if not paths:
        sys.exit("error: no audio files found")
    return paths


def read_context(path: Path | None) -> list[str]:
    if path is None:
        return []
    lines = (line.split("#", 1)[0].strip() for line in path.read_text().splitlines())
    return list(dict.fromkeys(line for line in lines if line))


def package_versions() -> dict[str, str]:
    from importlib.metadata import PackageNotFoundError, version

    versions = {}
    for package in ("mlx", "parakeet-mlx", "mlx-audio"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "missing"
    return versions


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("inputs", nargs="+", help="audio files or directories (recursive)")
    parser.add_argument("--engine", choices=["parakeet", "qwen3", "both"], default="both")
    parser.add_argument("--parakeet-model", default=DEFAULT_MODELS["parakeet"])
    parser.add_argument("--qwen3-model", default=DEFAULT_MODELS["qwen3"])
    parser.add_argument("--context-file", type=Path, help="hotwords for qwen3, one per line, # comments")
    parser.add_argument("--language", default="English",
                        help="qwen3 language: name, ISO 639-1 code, or 'auto' to detect")
    parser.add_argument("--beam", type=int, default=1, help="parakeet beam size (1 = greedy)")
    parser.add_argument("--pad-under", type=float, default=2.0, help="pad clips shorter than this (s)")
    parser.add_argument("--pad", type=float, default=0.75, help="silence added to each side (s); 0 disables")
    parser.add_argument("--min-conf", type=float, default=0.5, help="parakeet word confidence floor for 'agreed'")
    parser.add_argument("--out", type=Path, help="JSONL output path (default: stdout)")
    parser.add_argument("--text", action="store_true",
                        help="print transcripts only; with two engines: status<TAB>parakeet<TAB>qwen3")
    args = parser.parse_args()

    paths = collect(args.inputs)
    hotwords = read_context(args.context_file)
    names = ["parakeet", "qwen3"] if args.engine == "both" else [args.engine]
    try:
        language = qwen3_language(args.language)
    except ValueError as error:
        parser.error(str(error))

    # Open the output before the slow model load so a bad path fails immediately.
    partial = None
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        partial = args.out.with_name(args.out.name + ".partial")
        sink = partial.open("w")
    else:
        sink = sys.stdout

    started = time.perf_counter()
    engines = []
    for name in names:
        print(f"loading {name}...", file=sys.stderr)
        if name == "parakeet":
            engines.append(ParakeetEngine(args.parakeet_model, args.beam))
        else:
            engines.append(Qwen3Engine(args.qwen3_model, hotwords, language))
    load_s = time.perf_counter() - started

    counts: dict[str, int] = {}
    audio_s = 0.0
    try:
        for index, path in enumerate(paths, 1):
            try:
                clip = load_clip(path, args.pad_under, args.pad)
                results = {engine.name: engine.transcribe(clip) for engine in engines}
            except Exception as error:  # one bad clip must not end the batch
                message = str(error) if isinstance(error, ClipError) else f"{type(error).__name__}: {error}"
                counts["error"] = counts.get("error", 0) + 1
                print(json.dumps({"path": str(path), "status": "error", "error": message}),
                      file=sink, flush=True)
                print(f"[{index}/{len(paths)}] {path.name} error: {message}", file=sys.stderr)
                continue
            audio_s += clip.duration_s
            status, similarity = judge(results, args.min_conf, suspect=clip.length_mismatch)
            counts[status or "done"] = counts.get(status or "done", 0) + 1
            if args.text:
                texts = [results[name]["text"] for name in names]
                line = "\t".join([status, *texts]) if status else texts[0]
                print(line, file=sink, flush=True)
            else:
                record = {"path": str(path), "sha256": clip.sha256, "duration_s": clip.duration_s,
                          "sample_rate_src": clip.sample_rate_src, "codec": clip.codec,
                          "samples": clip.samples, "peak_dbfs": clip.peak_dbfs, "gain_db": clip.gain_db,
                          "length_mismatch": clip.length_mismatch, "pad_s": clip.pad_s,
                          "results": results, "status": status, "similarity": similarity,
                          "hotwords": len(hotwords)}
                print(json.dumps(record, ensure_ascii=False), file=sink, flush=True)
            print(f"[{index}/{len(paths)}] {path.name} {status or ''}", file=sys.stderr)
    finally:
        if partial:
            sink.close()

    run_s = time.perf_counter() - started - load_s
    summary = ", ".join(f"{k}={v}" for k, v in sorted(counts.items()))
    print(f"done: {len(paths)} clips, {audio_s:.1f}s audio, load {load_s:.1f}s, "
          f"transcribe {run_s:.1f}s ({audio_s / max(run_s, 1e-9):.1f}x realtime); {summary}",
          file=sys.stderr)
    if args.out:
        partial.replace(args.out)
        meta = {
            "complete": True, "clips": len(paths), "counts": counts, "audio_s": round(audio_s, 1),
            "load_s": round(load_s, 1), "transcribe_s": round(run_s, 1),
            "engines": {e.name: {"model": e.repo_id, "revision": e.revision} for e in engines},
            "params": {"language": language, "beam": args.beam, "min_conf": args.min_conf,
                       "pad": args.pad, "pad_under": args.pad_under},
            "hotwords": {"count": len(hotwords),
                         "sha256": hashlib.sha256("\n".join(hotwords).encode()).hexdigest() if hotwords else None},
            "versions": package_versions(),
            "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        }
        args.out.with_name(args.out.name + ".meta.json").write_text(json.dumps(meta, indent=2) + "\n")
    sys.exit(1 if counts.get("error") else 0)


if __name__ == "__main__":
    main()
