#!/usr/bin/env python3
"""
Shared client library for GPT Image generation and editing.

Wraps both OpenAI API surfaces:
  - Image API (one-shot generate/edit via client.images)
  - Responses API (multi-turn conversational via client.responses)

Env: OPENAI_API_KEY
"""

import base64
import os
import sys
import time
from pathlib import Path
from typing import Optional, Union

try:
    from openai import OpenAI
except ImportError:
    print("Error: openai library not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)


DEFAULT_MODEL = "gpt-image-2"
FAST_MODEL = "gpt-image-1.5"
MINI_MODEL = "gpt-image-1-mini"

SIZE_PRESETS = {
    "square": "1024x1024",
    "landscape": "1536x1024",
    "portrait": "1024x1536",
    "wide": "2048x1152",
    "2k": "2048x2048",
    "4k": "3840x2160",
    "4k-portrait": "2160x3840",
    "auto": "auto",
}

VALID_QUALITIES = ("low", "medium", "high", "auto")
VALID_FORMATS = ("png", "jpeg", "webp")


def resolve_model(model: Optional[str] = None, fast: bool = False, mini: bool = False) -> str:
    if model:
        return model
    if mini:
        return MINI_MODEL
    if fast:
        return FAST_MODEL
    return DEFAULT_MODEL


def resolve_size(size_input: Optional[str]) -> Optional[str]:
    if not size_input:
        return None
    key = size_input.lower().strip()
    if key in SIZE_PRESETS:
        return SIZE_PRESETS[key]
    if "x" in key:
        return key
    return size_input


def save_images(response, output_dir: str = "./output", filename: str = "generated",
                output_format: str = "png") -> list[Path]:
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    saved = []
    for i, img_data in enumerate(response.data):
        b64 = img_data.b64_json
        if not b64:
            alt = getattr(img_data, "url", None)
            reason = f"has url={alt!r}" if alt else "no b64_json or url"
            print(f"Warning: Image {i} skipped — {reason}", file=sys.stderr)
            continue
        suffix = f"_{i}" if len(response.data) > 1 else ""
        path = out / f"{filename}{suffix}_{ts}.{output_format}"
        path.write_bytes(base64.b64decode(b64))
        saved.append(path)
    return saved


def open_image_file(path: Union[str, Path]):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Image not found: {p}")
    return open(p, "rb")


class GPTAtelierClient:
    """Image API wrapper — one-shot generation and editing."""

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OPENAI_API_KEY not set.\n"
                "Set it with: export OPENAI_API_KEY='sk-...'\n"
                "Or pass api_key to the constructor."
            )
        self.client = OpenAI(api_key=key)
        self.model = model

    def generate(self, prompt: str, size: Optional[str] = None, quality: str = "high",
                 n: int = 1, output_format: str = "png", output_compression: Optional[int] = None,
                 background: Optional[str] = None, moderation: Optional[str] = None):
        kwargs = {
            "model": self.model,
            "prompt": prompt,
            "n": n,
        }
        if size:
            kwargs["size"] = resolve_size(size)
        if quality:
            kwargs["quality"] = quality
        if output_format:
            kwargs["output_format"] = output_format
        if output_compression is not None:
            kwargs["output_compression"] = output_compression
        if background:
            kwargs["background"] = background
        if moderation:
            kwargs["moderation"] = moderation
        return self.client.images.generate(**kwargs)

    def edit(self, prompt: str, image_paths: list[str], mask_path: Optional[str] = None,
             size: Optional[str] = None, quality: str = "high", n: int = 1,
             output_format: str = "png", output_compression: Optional[int] = None):
        files = []
        mask_file = None
        try:
            for p in image_paths:
                files.append(open_image_file(p))
            image_input = files if len(files) > 1 else files[0]

            kwargs = {
                "model": self.model,
                "image": image_input,
                "prompt": prompt,
                "n": n,
            }
            if mask_path:
                mask_file = open_image_file(mask_path)
                kwargs["mask"] = mask_file
            if size:
                kwargs["size"] = resolve_size(size)
            if quality:
                kwargs["quality"] = quality
            if output_format:
                kwargs["output_format"] = output_format
            if output_compression is not None:
                kwargs["output_compression"] = output_compression

            return self.client.images.edit(**kwargs)
        finally:
            for f in files:
                f.close()
            if mask_file:
                mask_file.close()


class GPTAtelierChat:
    """Responses API wrapper — multi-turn conversational image editing."""

    def __init__(self, api_key: Optional[str] = None, orchestrator: str = "gpt-5.4"):
        key = api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise ValueError(
                "OPENAI_API_KEY not set.\n"
                "Set it with: export OPENAI_API_KEY='sk-...'\n"
                "Or pass api_key to the constructor."
            )
        self.client = OpenAI(api_key=key)
        self.orchestrator = orchestrator
        self.previous_response_id = None
        self.history = []

    def send(self, message: str, image_paths: Optional[list[str]] = None,
             action: str = "auto", quality: Optional[str] = None,
             size: Optional[str] = None, output_format: str = "png",
             partial_images: int = 0):
        content = []
        if image_paths:
            for p in image_paths:
                img_bytes = Path(p).read_bytes()
                b64 = base64.b64encode(img_bytes).decode()
                ext = Path(p).suffix.lstrip(".").lower()
                mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                        "png": "image/png", "webp": "image/webp"}.get(ext, "image/png")
                content.append({
                    "type": "input_image",
                    "image_url": f"data:{mime};base64,{b64}",
                })
        content.append({"type": "input_text", "text": message})

        tool_config = {"type": "image_generation"}
        if action != "auto":
            tool_config["action"] = action
        if quality:
            tool_config["quality"] = quality
        if size:
            tool_config["size"] = resolve_size(size)
        if output_format != "png":
            tool_config["output_format"] = output_format
        if partial_images > 0:
            tool_config["partial_images"] = partial_images

        kwargs = {
            "model": self.orchestrator,
            "input": [{"role": "user", "content": content}],
            "tools": [tool_config],
        }
        if self.previous_response_id:
            kwargs["previous_response_id"] = self.previous_response_id

        response = self.client.responses.create(**kwargs)
        self.previous_response_id = response.id
        self.history.append({"role": "user", "message": message})
        self.history.append({
            "role": "assistant",
            "images": len(self.extract_images(response)),
            "text": self.extract_text(response)[:200],
        })
        return response

    def extract_images(self, response) -> list[str]:
        images = []
        for output in response.output:
            if output.type == "image_generation_call":
                images.append(output.result)
        return images

    def extract_text(self, response) -> str:
        parts = []
        for output in response.output:
            if output.type == "message":
                for content in output.content:
                    if hasattr(content, "text"):
                        parts.append(content.text)
        return "\n".join(parts)

    def save_images(self, response, output_dir: str = "./output", filename: str = "converse",
                    output_format: str = "png") -> list[Path]:
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        saved = []
        for i, b64 in enumerate(self.extract_images(response)):
            suffix = f"_{i}" if i > 0 else ""
            path = out / f"{filename}{suffix}_{ts}.{output_format}"
            path.write_bytes(base64.b64decode(b64))
            saved.append(path)
        return saved

    def reset(self):
        self.previous_response_id = None
        self.history = []
