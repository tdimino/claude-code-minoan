#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Shared Meshy API utilities — credential loading, HTTP client, polling, logging.

Requires: requests
Credentials: MESHY_API_KEY env var, falls back to ~/.config/env/secrets.env
"""

import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

API_BASE = "https://api.meshy.ai/openapi/v2"
DEFAULT_POLL_INTERVAL = 5
DEFAULT_TIMEOUT = 600
DEFAULT_OUTPUT_DIR = "./output"

SKILL_DIR = Path(__file__).parent.parent
LOG_DIR = SKILL_DIR / "logs"

_SECRETS_ENV = Path.home() / ".config" / "env" / "secrets.env"


class MeshyError(Exception):
    """Raised when the Meshy API returns an error."""

    def __init__(self, status: int, message: str, task_id: str | None = None):
        self.status = status
        self.message = message
        self.task_id = task_id
        super().__init__(f"[{status}] {message}")


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


def get_api_key(cli_override: str | None = None) -> str:
    """
    Get Meshy API key via 3-tier fallback:
    1. cli_override (--api-key flag)
    2. MESHY_API_KEY environment variable
    3. ~/.config/env/secrets.env
    """
    if cli_override:
        return cli_override

    key = os.environ.get("MESHY_API_KEY")
    if key:
        return key

    secrets = _load_secrets_env()
    key = secrets.get("MESHY_API_KEY")
    if key:
        return key

    print(
        "Error: MESHY_API_KEY not found.\n"
        "Set it in one of:\n"
        "  1. --api-key flag\n"
        "  2. Environment variable: export MESHY_API_KEY=msy_xxx\n"
        "  3. ~/.config/env/secrets.env: export MESHY_API_KEY=msy_xxx",
        file=sys.stderr,
    )
    sys.exit(1)


def log_event(event: dict[str, Any]) -> None:
    """Append JSONL event to logs/meshy.jsonl with UTC timestamp."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / "meshy.jsonl"
    with open(log_file, "a") as f:
        f.write(json.dumps({**event, "ts": datetime.now(timezone.utc).isoformat()}) + "\n")


class MeshyClient:
    """High-level client for the Meshy v2 API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = get_api_key(api_key)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    def _request(self, method: str, endpoint: str, **kwargs: Any) -> dict[str, Any]:
        """Authenticated request with error handling."""
        url = f"{API_BASE}{endpoint}"
        resp = self.session.request(method, url, **kwargs)

        if resp.status_code >= 400:
            try:
                err = resp.json()
                msg = err.get("message", resp.text)
            except (json.JSONDecodeError, ValueError):
                msg = resp.text
            raise MeshyError(resp.status_code, msg)

        if resp.status_code == 204 or not resp.text:
            return {}
        return resp.json()

    # ── Generation endpoints ──────────────────────────────────────────────

    def create_text_to_3d(
        self,
        prompt: str,
        *,
        mode: str = "preview",
        negative_prompt: str = "",
        model_type: str = "lowpoly",
        art_style: str = "",
        topology: str = "",
        target_polycount: int | None = None,
        should_remesh: bool = False,
        symmetry_mode: str = "",
        preview_task_id: str = "",
        enable_pbr: bool = True,
        texture_prompt: str = "",
    ) -> str:
        """Submit a text-to-3D task. Returns task_id."""
        payload: dict[str, Any] = {"mode": mode}

        if mode == "preview":
            payload["prompt"] = prompt
            if negative_prompt:
                payload["negative_prompt"] = negative_prompt
            payload["model_type"] = model_type
            if art_style:
                payload["art_style"] = art_style
            if topology:
                payload["topology"] = topology
            if target_polycount is not None:
                payload["target_polycount"] = target_polycount
            if should_remesh:
                payload["should_remesh"] = True
            if symmetry_mode:
                payload["symmetry_mode"] = symmetry_mode
        elif mode == "refine":
            payload["preview_task_id"] = preview_task_id
            payload["enable_pbr"] = enable_pbr
            if texture_prompt:
                payload["texture_prompt"] = texture_prompt

        resp = self._request("POST", "/text-to-3d", json=payload)
        task_id = resp.get("result", "")
        log_event({"action": f"text_to_3d_{mode}", "task_id": task_id, "prompt": prompt[:100]})
        return task_id

    def create_image_to_3d(
        self,
        image_url: str,
        *,
        model_type: str = "lowpoly",
        topology: str = "",
        target_polycount: int | None = None,
        should_remesh: bool = False,
    ) -> str:
        """Submit an image-to-3D task. Returns task_id."""
        payload: dict[str, Any] = {
            "image_url": image_url,
            "model_type": model_type,
        }
        if topology:
            payload["topology"] = topology
        if target_polycount is not None:
            payload["target_polycount"] = target_polycount
        if should_remesh:
            payload["should_remesh"] = True

        resp = self._request("POST", "/image-to-3d", json=payload)
        task_id = resp.get("result", "")
        log_event({"action": "image_to_3d", "task_id": task_id})
        return task_id

    def create_text_to_texture(
        self,
        model_url: str,
        *,
        prompt: str,
        negative_prompt: str = "",
        art_style: str = "",
        enable_pbr: bool = True,
    ) -> str:
        """Submit a text-to-texture task. Returns task_id."""
        payload: dict[str, Any] = {
            "model_url": model_url,
            "prompt": prompt,
            "enable_pbr": enable_pbr,
        }
        if negative_prompt:
            payload["negative_prompt"] = negative_prompt
        if art_style:
            payload["art_style"] = art_style

        resp = self._request("POST", "/text-to-texture", json=payload)
        task_id = resp.get("result", "")
        log_event({"action": "text_to_texture", "task_id": task_id, "prompt": prompt[:100]})
        return task_id

    # ── Task management ───────────────────────────────────────────────────

    def get_task(self, task_id: str, endpoint: str = "text-to-3d") -> dict[str, Any]:
        """GET /{endpoint}/{task_id} — returns full task object."""
        return self._request("GET", f"/{endpoint}/{task_id}")

    def list_tasks(
        self,
        endpoint: str = "text-to-3d",
        page_num: int = 1,
        page_size: int = 20,
        sort_by: str = "-created_at",
    ) -> list[dict[str, Any]]:
        """GET /{endpoint} — returns list of tasks."""
        params = {
            "page_num": page_num,
            "page_size": page_size,
            "sort_by": sort_by,
        }
        try:
            resp = self._request("GET", f"/{endpoint}", params=params)
        except MeshyError as e:
            if e.status == 404:
                return []
            raise
        return resp if isinstance(resp, list) else resp.get("result", resp.get("data", []))

    def poll_task(
        self,
        task_id: str,
        *,
        endpoint: str = "text-to-3d",
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        timeout: int = DEFAULT_TIMEOUT,
        quiet: bool = False,
        label: str = "",
    ) -> dict[str, Any]:
        """Poll until SUCCEEDED/FAILED/CANCELED or timeout. Returns final task dict."""
        prefix = f"  [{label}] " if label else "  "
        last_progress = -1
        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed > timeout:
                log_event({"action": "poll_timeout", "task_id": task_id, "elapsed": round(elapsed)})
                raise MeshyError(408, f"Task {task_id} timed out after {timeout}s", task_id)

            task = self.get_task(task_id, endpoint)
            status = task.get("status", "UNKNOWN")
            progress = task.get("progress", 0)

            if status == "SUCCEEDED":
                if not quiet:
                    print(f"{prefix}Complete!")
                return task

            if status in ("FAILED", "CANCELED"):
                error_msg = task.get("task_error", {}).get("message", "unknown error")
                if not quiet:
                    print(f"{prefix}FAILED: {error_msg}", file=sys.stderr)
                log_event({"action": "task_failed", "task_id": task_id, "error": error_msg})
                return task

            if not quiet and progress != last_progress:
                print(f"{prefix}{status}: {progress}%")
                last_progress = progress

            time.sleep(poll_interval)

    def download_model(
        self,
        task: dict[str, Any],
        *,
        output_dir: Path = Path(DEFAULT_OUTPUT_DIR),
        filename: str = "",
        format: str = "glb",
    ) -> Path | None:
        """Download model file from task's model_urls. Returns output path."""
        model_urls = task.get("model_urls", {})
        url = model_urls.get(format)
        if not url:
            available = list(model_urls.keys())
            print(f"  No '{format}' URL in response. Available: {available}", file=sys.stderr)
            return None

        output_dir.mkdir(parents=True, exist_ok=True)
        if not filename:
            filename = task.get("id", task.get("task_id", "model"))
        output_path = output_dir / f"{filename}.{format}"

        resp = requests.get(url, timeout=120)
        resp.raise_for_status()
        output_path.write_bytes(resp.content)

        size_kb = len(resp.content) / 1024
        log_event({"action": "downloaded", "file": str(output_path), "size_kb": round(size_kb, 1), "format": format})
        return output_path

    def get_balance(self) -> dict[str, Any]:
        """Check credit balance. Tries multiple known endpoints."""
        for path in ("/balance", "/credits", "/me"):
            try:
                return self._request("GET", path)
            except MeshyError as e:
                if e.status == 404:
                    continue
                raise
        return {"credit_balance": "unavailable (no balance endpoint found)"}

    # ── Convenience pipeline ──────────────────────────────────────────────

    def generate_full(
        self,
        prompt: str,
        *,
        negative_prompt: str = "",
        model_type: str = "lowpoly",
        skip_refine: bool = False,
        output_dir: Path = Path(DEFAULT_OUTPUT_DIR),
        output_name: str = "",
        format: str = "glb",
        poll_interval: int = DEFAULT_POLL_INTERVAL,
        timeout: int = DEFAULT_TIMEOUT,
        quiet: bool = False,
        enable_pbr: bool = True,
    ) -> tuple[bool, Path | None]:
        """
        Full pipeline: preview → poll → (optional refine → poll) → download.
        Falls back to preview GLB if refine fails.
        Returns (success, output_path).
        """
        label = output_name or "model"

        # Step 1: Preview
        if not quiet:
            print(f"  [{label}] Submitting preview...")
        try:
            preview_id = self.create_text_to_3d(
                prompt,
                mode="preview",
                negative_prompt=negative_prompt,
                model_type=model_type,
            )
            if not quiet:
                print(f"  [{label}] Preview task: {preview_id}")
        except (MeshyError, requests.HTTPError) as e:
            print(f"  [{label}] Preview submission failed: {e}", file=sys.stderr)
            return False, None

        preview_task = self.poll_task(
            preview_id,
            poll_interval=poll_interval,
            timeout=timeout,
            quiet=quiet,
            label=f"{label} preview",
        )
        if preview_task.get("status") != "SUCCEEDED":
            return False, None

        # Download preview
        preview_path = self.download_model(
            preview_task,
            output_dir=output_dir,
            filename=f"{output_name}-preview" if output_name else "",
            format=format,
        )
        if not quiet and preview_path:
            size_kb = preview_path.stat().st_size / 1024
            print(f"  [{label}] Preview downloaded: {preview_path.name} ({size_kb:.0f} KB)")

        if skip_refine:
            # Rename preview as final
            if preview_path:
                final_name = f"{output_name}.{format}" if output_name else f"model.{format}"
                final_path = output_dir / final_name
                preview_path.rename(final_path)
                if not quiet:
                    print(f"  [{label}] Using preview as final (skip-refine)")
                return True, final_path
            return False, None

        # Step 2: Refine
        if not quiet:
            print(f"  [{label}] Submitting refine...")
        try:
            refine_id = self.create_text_to_3d(
                prompt,
                mode="refine",
                preview_task_id=preview_id,
                enable_pbr=enable_pbr,
            )
            if not quiet:
                print(f"  [{label}] Refine task: {refine_id}")
        except (MeshyError, requests.HTTPError) as e:
            print(f"  [{label}] Refine submission failed: {e}", file=sys.stderr)
            # Fall back to preview
            if preview_path:
                final_name = f"{output_name}.{format}" if output_name else f"model.{format}"
                final_path = output_dir / final_name
                preview_path.rename(final_path)
                print(f"  [{label}] Falling back to preview GLB", file=sys.stderr)
                return False, final_path
            return False, None

        refine_task = self.poll_task(
            refine_id,
            poll_interval=poll_interval,
            timeout=timeout,
            quiet=quiet,
            label=f"{label} refine",
        )
        if refine_task.get("status") != "SUCCEEDED":
            # Fall back to preview
            if preview_path:
                final_name = f"{output_name}.{format}" if output_name else f"model.{format}"
                final_path = output_dir / final_name
                preview_path.rename(final_path)
                if not quiet:
                    print(f"  [{label}] Falling back to preview GLB")
                return False, final_path
            return False, None

        # Download refined as final
        final_path = self.download_model(
            refine_task,
            output_dir=output_dir,
            filename=output_name or "",
            format=format,
        )
        if not quiet and final_path:
            size_kb = final_path.stat().st_size / 1024
            print(f"  [{label}] Refined downloaded: {final_path.name} ({size_kb:.0f} KB)")

        # Clean up preview file
        if preview_path and preview_path.exists():
            preview_path.unlink()

        return True, final_path
