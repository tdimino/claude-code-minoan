#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Shared utilities for non-Meshy 3D generation providers (fal.ai, WaveSpeed, Trellis).

Credential loading, JSONL event logging, polling helpers, file download.
Meshy-specific code stays in _meshy_utils.py — this module covers the rest.
"""

import base64
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SKILL_DIR = Path(__file__).parent.parent
LOG_DIR = SKILL_DIR / "logs"

_SECRETS_ENV = Path.home() / ".config" / "env" / "secrets.env"


class ProviderError(Exception):
    """Raised when a 3D generation provider returns an error."""

    def __init__(self, provider: str, status: int, message: str, task_id: str | None = None):
        self.provider = provider
        self.status = status
        self.message = message
        self.task_id = task_id
        super().__init__(f"[{provider}:{status}] {message}")


def _load_secrets_env() -> dict[str, str]:
    """Load key=value pairs from ~/.config/env/secrets.env."""
    if not _SECRETS_ENV.exists():
        return {}
    env: dict[str, str] = {}
    for line in _SECRETS_ENV.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:]
        if "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip("'\"")
    return env


def get_api_key(env_var: str, cli_override: str | None = None) -> str:
    """
    Get API key via 3-tier fallback:
    1. cli_override (--api-key flag)
    2. Environment variable
    3. ~/.config/env/secrets.env
    """
    if cli_override:
        return cli_override

    key = os.environ.get(env_var)
    if key:
        return key

    secrets = _load_secrets_env()
    key = secrets.get(env_var)
    if key:
        return key

    print(
        f"Error: {env_var} not found.\n"
        f"Set it in one of:\n"
        f"  1. --api-key flag\n"
        f"  2. Environment variable: export {env_var}=your_key\n"
        f"  3. ~/.config/env/secrets.env: export {env_var}=your_key",
        file=sys.stderr,
    )
    sys.exit(1)


def log_event(event: dict[str, Any]) -> None:
    """Append JSONL event to logs/providers.jsonl with UTC timestamp."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "providers.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps({**event, "ts": datetime.now(timezone.utc).isoformat()}) + "\n")


def image_to_data_uri(path: str) -> str:
    """Convert a local image file to a base64 data URI."""
    p = Path(path)
    suffix = p.suffix.lower()
    mime = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webp": "image/webp",
    }.get(suffix, "image/png")
    data = base64.b64encode(p.read_bytes()).decode()
    return f"data:{mime};base64,{data}"


def resolve_image_input(image_arg: str) -> str:
    """
    Resolve an image argument to a URL or data URI.
    If it's a local file path, convert to base64 data URI.
    If it's already a URL, return as-is.
    """
    if image_arg.startswith(("http://", "https://", "data:")):
        return image_arg
    p = Path(image_arg)
    if p.exists() and p.is_file():
        return image_to_data_uri(image_arg)
    if not image_arg.startswith(("http://", "https://")):
        print(f"  Warning: '{image_arg}' not found as local file, passing as-is", file=sys.stderr)
    return image_arg


def download_file(url: str, output_dir: Path, filename: str, quiet: bool = False) -> Path:
    """Download a file from URL to output_dir/filename."""
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / filename

    resp = requests.get(url, stream=True, timeout=120)
    resp.raise_for_status()

    with open(output_path, "wb") as f:
        for chunk in resp.iter_content(65536):
            f.write(chunk)

    size_kb = output_path.stat().st_size / 1024
    if not quiet:
        print(f"  Downloaded: {output_path.name} ({size_kb:.0f} KB)")
    log_event({"action": "downloaded", "file": str(output_path), "size_kb": round(size_kb, 1)})
    return output_path
