#!/usr/bin/env python3
"""OpenAI-compatible transcription server wrapping Parakeet TDT 0.6B.

Exposes POST /v1/audio/transcriptions so Takopi (or any OpenAI-compatible
client) can transcribe voice notes locally via Parakeet NeMo.

Usage:
    uv run --with fastapi,uvicorn,python-multipart parakeet_server.py
    # or: python3 parakeet_server.py --port 8384

Takopi config:
    voice_transcription_base_url = "http://localhost:8384/v1"
    voice_transcription_api_key = "local"
    voice_transcription_model = "parakeet-tdt-0.6b"
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, PlainTextResponse

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("parakeet-server")

TRANSCRIBE_SCRIPT = Path(__file__).parent / "transcribe.py"
PARAKEET_HOME = os.environ.get(
    "PARAKEET_HOME",
    os.path.expanduser("~/Programming/parakeet-dictate"),
)
ALLOWED_SUFFIXES = {".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".oga", ".webm"}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB

app = FastAPI(title="Parakeet STT Server", version="1.0.0")


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": "parakeet-tdt-0.6b",
                "object": "model",
                "owned_by": "nvidia",
            }
        ],
    }


@app.post("/v1/audio/transcriptions")
async def transcribe(
    file: UploadFile = File(...),
    model: str = Form("parakeet-tdt-0.6b"),
    language: str = Form(None),
    response_format: str = Form("json"),
):
    raw_suffix = Path(file.filename).suffix.lower() if file.filename else ".ogg"
    suffix = raw_suffix if raw_suffix in ALLOWED_SUFFIXES else ".ogg"

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            content = await file.read()
            if len(content) > MAX_UPLOAD_BYTES:
                raise HTTPException(status_code=413, detail="Audio file too large")
            tmp.write(content)
            tmp_path = tmp.name

        log.info("Transcribing %s (%d bytes, model=%s)", file.filename, len(content), model)

        result = subprocess.run(
            [sys.executable, str(TRANSCRIBE_SCRIPT), tmp_path],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ, "PARAKEET_HOME": PARAKEET_HOME},
        )

        if result.returncode != 0:
            log.error("Transcription failed: %s", result.stderr.strip())
            return JSONResponse(
                status_code=500,
                content={"error": {"message": result.stderr.strip(), "type": "transcription_error"}},
            )

        text = result.stdout.strip()
        log.info("Transcribed: %s", text[:100])

        if response_format == "text":
            return PlainTextResponse(content=text)
        if response_format == "verbose_json":
            return {
                "task": "transcribe",
                "language": language or "en",
                "duration": 0.0,
                "text": text,
                "segments": [],
                "words": [],
            }
        return {"text": text}

    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


@app.get("/health")
async def health():
    return {"status": "ok", "model": "parakeet-tdt-0.6b"}


def main():
    parser = argparse.ArgumentParser(description="Parakeet OpenAI-compatible STT server")
    parser.add_argument("--port", type=int, default=8384, help="Port to listen on")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    log.info("Starting Parakeet STT server on %s:%d", args.host, args.port)
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
