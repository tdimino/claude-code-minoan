#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#     "fastapi>=0.115",
#     "uvicorn>=0.30",
#     "python-multipart>=0.0.9",
#     "parakeet-mlx>=0.5.2",
#     "mlx-audio>=0.5.5",
#     "numpy>=1.26",
# ]
# ///
"""OpenAI-compatible transcription server over the MLX engines in batch_transcribe.py.

Models stay warm in-process. Requests are serialized because both engines share one GPU.
Takopi and any OpenAI-compatible client can use POST /v1/audio/transcriptions.

Usage:
    parakeet_server.py [--port 8384] [--preload parakeet]

Model ids (the `model` form field):
    parakeet-tdt-0.6b, parakeet   Parakeet TDT v2 via parakeet-mlx (default)
    qwen3-asr, qwen3              Qwen3-ASR 1.7B via mlx-audio

Takopi config:
    voice_transcription_base_url = "http://localhost:8384/v1"
    voice_transcription_api_key = "local"
    voice_transcription_model = "parakeet-tdt-0.6b"
"""

import argparse
import importlib.util
import sys
import logging
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import PlainTextResponse

spec = importlib.util.spec_from_file_location("batch", Path(__file__).with_name("batch_transcribe.py"))
batch = importlib.util.module_from_spec(spec)
sys.modules["batch"] = batch  # @dataclass resolves annotations via sys.modules
spec.loader.exec_module(batch)

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("parakeet-server")

ALLOWED_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".oga", ".webm"}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MODEL_ALIASES = {"parakeet-tdt-0.6b": "parakeet", "parakeet": "parakeet",
                 "qwen3-asr": "qwen3", "qwen3": "qwen3"}

app = FastAPI(title="Parakeet STT Server", version="2.0.0")
_engines: dict[str, object] = {}
# MLX streams are thread-local: a model built on one thread fails on another
# ("There is no Stream(cpu, 1) in current thread"). One worker owns all MLX work,
# which also serializes requests on the shared GPU.
_mlx = ThreadPoolExecutor(max_workers=1, thread_name_prefix="mlx")


def engine_for(name: str):
    if name not in _engines:
        log.info("Loading %s engine", name)
        if name == "parakeet":
            _engines[name] = batch.ParakeetEngine(batch.DEFAULT_MODELS["parakeet"], beam=1)
        else:
            _engines[name] = batch.Qwen3Engine(batch.DEFAULT_MODELS["qwen3"], [], None)
    return _engines[name]


def run(name: str, clip, hotwords: list[str] | None, language: str | None) -> dict:
    engine = engine_for(name)
    if name == "qwen3":
        engine.hotwords = hotwords
        engine.language = language  # already a Qwen3 language name or None
    return engine.transcribe(clip)


def prompt_hotwords(prompt: str | None) -> list[str] | None:
    """Use OpenAI's `prompt` as Qwen3 hotwords only when it is a vocabulary list.

    Prose prompts ("A meeting about X, Y, and Z") would become sentence-fragment
    hotwords, so any comma piece longer than four words means: ignore the prompt.
    """
    pieces = [piece.strip() for piece in (prompt or "").split(",") if piece.strip()]
    if not pieces or any(len(piece.split()) > 4 for piece in pieces):
        if pieces:
            log.info("Ignoring prose prompt; send a comma-separated vocabulary list for hotwords")
        return None
    return pieces


@app.get("/v1/models")
def list_models():
    return {"object": "list",
            "data": [{"id": alias, "object": "model", "owned_by": "local"} for alias in MODEL_ALIASES]}


@app.post("/v1/audio/transcriptions")
def transcribe(
    file: UploadFile = File(...),
    model: str = Form("parakeet-tdt-0.6b"),
    language: str = Form(None),
    prompt: str = Form(None),
    response_format: str = Form("json"),
):
    name = MODEL_ALIASES.get(model)
    if name is None:
        raise HTTPException(status_code=400, detail=f"unknown model {model!r}; see /v1/models")
    content = file.file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Audio file too large")
    raw_suffix = Path(file.filename or "").suffix.lower()
    suffix = raw_suffix if raw_suffix in ALLOWED_SUFFIXES else ".ogg"

    with tempfile.NamedTemporaryFile(suffix=suffix) as tmp:
        tmp.write(content)
        tmp.flush()
        try:
            clip = batch.load_clip(Path(tmp.name), pad_under=2.0, pad_s=0.75)
        except Exception as error:
            raise HTTPException(status_code=400, detail=f"could not decode audio: {error}") from error
        try:
            qwen3_language = batch.qwen3_language(language)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        try:
            result = _mlx.submit(run, name, clip, prompt_hotwords(prompt), qwen3_language).result()
        except Exception as error:
            log.exception("Transcription failed")
            raise HTTPException(status_code=500,
                                detail=f"transcription failed: {type(error).__name__}: {error}") from error

    text = result["text"]
    log.info("Transcribed %s (%.1fs, %s): %s", file.filename, clip.duration_s, name, text[:100])
    if response_format == "text":
        return PlainTextResponse(content=text)
    if response_format == "verbose_json":
        return {"task": "transcribe", "language": language, "duration": clip.duration_s,
                "text": text, "segments": [],
                "words": [{"word": w["w"], "start": w["start"], "end": w["end"]} for w in result["words"]],
                # Non-standard fields: flags that mark the transcript as unreliable.
                "truncated": result.get("truncated", False),
                "echo_stripped": result.get("echo_stripped", False)}
    return {"text": text}


@app.get("/health")
def health():
    return {"status": "ok", "loaded": sorted(_engines)}


def main():
    parser = argparse.ArgumentParser(description="MLX OpenAI-compatible STT server")
    parser.add_argument("--port", type=int, default=8384)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--preload", choices=["parakeet", "qwen3"], action="append", default=[],
                        help="load an engine at startup instead of on first request")
    args = parser.parse_args()
    for name in args.preload:
        _mlx.submit(engine_for, name).result()
    log.info("Starting STT server on %s:%d", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
