#!/usr/bin/env python3
"""Atlas Cloud text-to-image client with guarded async polling."""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any, Callable

import requests


ATLAS_API_BASE = "https://api.atlascloud.ai"
DEFAULT_ATLAS_MODEL = "google/nano-banana-pro/text-to-image-developer"


def _iter_objects(value: Any):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _iter_objects(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_objects(item)


def _data_object(payload: dict[str, Any]) -> dict[str, Any]:
    data = payload.get("data")
    return data if isinstance(data, dict) else payload


class AtlasImageClient:
    """Generate one image through Atlas Cloud without retrying the billable POST."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = DEFAULT_ATLAS_MODEL,
        request: Callable[..., requests.Response] = requests.request,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.api_key = api_key or os.environ.get("ATLASCLOUD_API_KEY", "")
        if not self.api_key:
            raise EnvironmentError(
                "Atlas Cloud API key required. Set ATLASCLOUD_API_KEY or pass --atlas-api-key"
            )
        self.model = model
        self._request = request
        self._sleep = sleep

    @property
    def _auth_headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "User-Agent": "claude-code-minoan-nano-banana-pro/1.0",
        }

    def _json_request(
        self,
        method: str,
        path: str,
        *,
        authenticated: bool = True,
        json: dict[str, Any] | None = None,
        timeout: int = 120,
    ) -> dict[str, Any]:
        headers = self._auth_headers if authenticated else {"Accept": "application/json"}
        response = self._request(
            method,
            f"{ATLAS_API_BASE}{path}",
            headers=headers,
            json=json,
            timeout=timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise RuntimeError("Atlas Cloud returned a non-object response")
        return payload

    def validate_model(self) -> None:
        """Confirm the configured model is present and enabled in the live catalog."""
        catalog = self._json_request("GET", "/api/v1/models", authenticated=False)
        model = next(
            (
                item
                for item in _iter_objects(catalog)
                if (item.get("model") or item.get("id")) == self.model
            ),
            None,
        )
        if model is None:
            raise RuntimeError(f"Atlas Cloud model not found: {self.model}")
        if model.get("display_console") is not True:
            raise RuntimeError(f"Atlas Cloud model is not enabled: {self.model}")

    def _poll_prediction(self, prediction_id: str, timeout: int = 240) -> str:
        deadline = time.monotonic() + timeout
        transient_errors = 0

        while time.monotonic() < deadline:
            try:
                result = self._json_request(
                    "GET", f"/api/v1/model/prediction/{prediction_id}"
                )
                transient_errors = 0
            except (requests.ConnectionError, requests.Timeout):
                transient_errors += 1
                if transient_errors > 3:
                    raise
                self._sleep(2 ** (transient_errors - 1))
                continue
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else 0
                if status < 500:
                    raise
                transient_errors += 1
                if transient_errors > 3:
                    raise
                self._sleep(2 ** (transient_errors - 1))
                continue

            data = _data_object(result)
            status = str(data.get("status", "")).lower()
            if status in {"completed", "succeeded"}:
                outputs = data.get("outputs") or []
                if not outputs or not isinstance(outputs[0], str):
                    raise RuntimeError("Atlas Cloud completed without an output URL")
                return outputs[0]
            if status in {"failed", "timeout", "canceled", "cancelled"}:
                raise RuntimeError(data.get("error") or f"Atlas generation ended with {status}")
            self._sleep(3)

        raise TimeoutError(f"Atlas prediction {prediction_id} did not finish in time")

    def _download(self, url: str, output_base: Path) -> Path:
        if not url.startswith(("https://", "http://")):
            raise RuntimeError("Atlas Cloud returned an unsupported output URL")
        response = self._request("GET", url, timeout=120)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0]
        extension = {
            "image/jpeg": ".jpg",
            "image/png": ".png",
            "image/webp": ".webp",
        }.get(content_type, ".png")
        output_path = output_base.with_suffix(extension)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        return output_path

    def generate_to_file(
        self,
        prompt: str,
        output_base: Path,
        *,
        aspect_ratio: str = "16:9",
        resolution: str = "1k",
        temperature: float = 1.0,
        timeout: int = 240,
    ) -> Path:
        self.validate_model()
        # This billable generation POST is intentionally attempted exactly once.
        result = self._json_request(
            "POST",
            "/api/v1/model/generateImage",
            json={
                "model": self.model,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
                "temperature": temperature,
            },
        )
        prediction_id = str(_data_object(result).get("id") or "")
        if not prediction_id:
            raise RuntimeError(result.get("message") or "Atlas Cloud returned no prediction ID")
        output_url = self._poll_prediction(prediction_id, timeout=timeout)
        return self._download(output_url, output_base)
