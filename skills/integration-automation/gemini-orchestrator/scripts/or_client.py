"""OpenRouter chat-completions client for gemini-orchestrator. Standard library only.

Knows the API and nothing about files: key loading, the live model list (cached for a day), alias and effort
checks, max_tokens sizing, request bodies, and a streaming reader.

Environment:
  OPENROUTER_API_KEY     inference key (falls back to ~/.config/env/secrets.env, then global.env)
  OPENROUTER_BASE_URL    override for tests (default https://openrouter.ai/api/v1)
  GEMINI_ORCH_DATA_DIR   state folder (default ~/.claude/data/gemini-orchestrator)
  GEMINI_ORCH_BACKOFF    seconds before the first retry (default 2)
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

BASE_URL_DEFAULT = "https://openrouter.ai/api/v1"
USER_AGENT = "gemini-orchestrator/0.1"  # the project's name and nothing else: no contact detail leaves this machine
MODELS_MAX_AGE = 24 * 3600

ALIASES = {
    "neon": "google/gemini-4-neon",
    "hydrogen": "google/gemini-4-hydrogen",
    "carbon": "google/gemini-4-carbon",
    "argon": "google/gemini-4-argon",
    "flash": "google/gemini-3.8-flash",
}

# Tokens set aside for reasoning at each effort, on top of the answer. On Gemini 4 an effort is a level, not a share
# of max_tokens: in the 2026-11-20 pilot Neon spent the whole budget reasoning at low (622 of 625) and at high
# (2,497 of 2,500) and returned nothing, and used 6,329 reasoning tokens on a small puzzle at xhigh. In first
# real use the same day, Hydrogen at high used 15,262 on a design over 35,000 input tokens, and Neon at high used
# all of a 24,000 budget reviewing 76,592 and returned nothing ($0.59). The allowances were tripled at high after
# that. Nothing here caps reasoning: the model list gives Gemini 4 no token-budget control. An unused allowance
# costs nothing; one that is too small costs the whole call. --reasoning-tokens overrides.
REASONING_ALLOWANCE = {"minimal": 4000, "low": 8000, "medium": 16000, "high": 48000, "xhigh": 64000, "max": 64000}

RETRYABLE = {408, 429, 500, 502, 503, 504, 529}


class ClientError(Exception):
    """A request that failed before any answer text arrived, or a usage mistake the API would reject."""

    def __init__(self, message: str, *, status: int | None = None, usage: bool = False):
        super().__init__(message)
        self.status = status
        self.usage = usage  # True when the caller asked for something the model list rules out


@dataclass
class Result:
    content: str = ""
    model: str = ""
    provider: str = ""
    finish_reason: str = ""
    usage: dict = field(default_factory=dict)
    generation_id: str = ""
    error: str = ""
    partial: bool = False


def base_url() -> str:
    return os.environ.get("OPENROUTER_BASE_URL", BASE_URL_DEFAULT).rstrip("/")


def data_dir() -> Path:
    d = Path(os.environ.get("GEMINI_ORCH_DATA_DIR", Path.home() / ".claude/data/gemini-orchestrator"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def load_api_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    for env_file in (Path.home() / ".config/env/secrets.env", Path.home() / ".config/env/global.env"):
        if not env_file.exists():
            continue
        for line in env_file.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip().removeprefix("export ").strip()
            if line.startswith("OPENROUTER_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise ClientError("OPENROUTER_API_KEY is not set and was not found in ~/.config/env/secrets.env")


# --- models -----------------------------------------------------------------------------------------------------

def fetch_models(*, force: bool = False) -> list[dict]:
    """Today's model list. Prices, context sizes and effort lists are read from here and never hardcoded."""
    cache = data_dir() / "models-cache.json"
    if not force and cache.exists() and time.time() - cache.stat().st_mtime < MODELS_MAX_AGE:
        try:
            cached = json.loads(cache.read_text(encoding="utf-8"))
            if cached.get("base_url") == base_url():
                return cached["data"]
        except (json.JSONDecodeError, KeyError):
            pass
    req = urllib.request.Request(f"{base_url()}/models", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.load(resp)["data"]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError, TimeoutError) as e:
        raise ClientError(f"could not fetch the model list: {e}") from e
    tmp = cache.with_suffix(".tmp")
    tmp.write_text(json.dumps({"base_url": base_url(), "data": data}), encoding="utf-8")
    os.replace(tmp, cache)
    return data


def resolve_model(name: str, models: list[dict]) -> dict:
    """An alias, a full OpenRouter id, or a bare Gemini name -> that model's record from the live list."""
    by_id = {m["id"]: m for m in models}
    wanted = ALIASES.get(name.lower(), name)
    for candidate in (wanted, f"google/{wanted}", f"google/gemini-{wanted}"):
        if candidate in by_id:
            return by_id[candidate]
    near = sorted(i for i in by_id if name.lower().split("/")[-1] in i.lower())[:8]
    hint = f" Close matches: {', '.join(near)}." if near else ""
    raise ClientError(f"model '{name}' is not in today's OpenRouter list.{hint} Aliases: {', '.join(ALIASES)}.",
                      usage=True)


def check_effort(model: dict, effort: str | None) -> str | None:
    """The effort to send. Rejects one the model does not list, before any request is made."""
    r = model.get("reasoning") or {}
    supported = r.get("supported_efforts")
    if effort is None:
        if r.get("default_effort"):
            return r["default_effort"]
        if not supported:
            return None
        return "medium" if "medium" in supported else supported[-1]  # the list runs from highest to lowest
    if effort == "none" and r.get("mandatory"):
        raise ClientError(f"{model['id']} cannot run without reasoning; accepted efforts: "
                          f"{', '.join(supported or [])}", usage=True)
    if supported and effort not in supported:
        raise ClientError(f"{model['id']} does not accept effort '{effort}'; accepted: {', '.join(supported)}",
                          usage=True)
    return effort


def max_completion(model: dict) -> int:
    return int((model.get("top_provider") or {}).get("max_completion_tokens") or 65536)


def max_tokens_for(answer_tokens: int, effort: str | None, model: dict, reasoning_tokens: int | None = None) -> int:
    """max_tokens: the answer plus an allowance for reasoning, which is billed as output and shares the budget."""
    allowance = reasoning_tokens if reasoning_tokens is not None else REASONING_ALLOWANCE.get(effort or "", 0)
    return min(answer_tokens + allowance, max_completion(model))


def prices(model: dict) -> tuple[float, float]:
    """(dollars per input token, dollars per output or reasoning token)."""
    p = model.get("pricing") or {}
    return float(p.get("prompt") or 0), float(p.get("completion") or 0)


# --- request ----------------------------------------------------------------------------------------------------

def build_body(model_id: str, messages: list[dict], *, effort: str | None, max_tokens: int,
               schema: dict | None = None, has_pdf: bool = False, data_collection: str = "deny",
               zdr: bool = False) -> dict:
    body: dict = {"model": model_id, "messages": messages, "max_tokens": max_tokens, "stream": True}
    if effort:
        # exclude: the reasoning is still done and billed, but its text is not returned.
        body["reasoning"] = {"effort": effort, "exclude": True}
    provider: dict = {"data_collection": data_collection, "require_parameters": True}
    if zdr:
        provider["zdr"] = True
    body["provider"] = provider
    if has_pdf:
        # Pinned so a PDF is never silently sent to the paid OCR engine.
        body["plugins"] = [{"id": "file-parser", "pdf": {"engine": "native"}}]
    if schema is not None:
        body["response_format"] = {"type": "json_schema",
                                   "json_schema": {"name": "answer", "strict": True, "schema": schema}}
    return body


def _error_message(raw: bytes) -> str:
    try:
        err = json.loads(raw).get("error") or {}
        return str(err.get("message") or err or raw[:300])
    except (json.JSONDecodeError, AttributeError):
        return raw[:300].decode("utf-8", "replace")


def chat(body: dict, api_key: str, *, timeout: float = 900, retries: int = 2, on_text=None) -> Result:
    """POST the body and read the stream.

    Retries only failures that arrive before any answer text (HTTP 408/429/5xx, connection errors): those are not
    billed. A stream that breaks or reports an error midway is returned as a partial Result and never retried.
    """
    req = urllib.request.Request(
        f"{base_url()}/chat/completions", data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json",
                 "User-Agent": USER_AGENT, "X-Title": "gemini-orchestrator"})
    backoff = float(os.environ.get("GEMINI_ORCH_BACKOFF", "2"))
    attempt = 0
    while True:
        try:
            resp = urllib.request.urlopen(req, timeout=timeout)
            break
        except urllib.error.HTTPError as e:
            message = _error_message(e.read())
            if e.code in RETRYABLE and attempt < retries:
                attempt += 1
                time.sleep(backoff * attempt)
                continue
            raise ClientError(f"HTTP {e.code}: {message}", status=e.code) from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt < retries:
                attempt += 1
                time.sleep(backoff * attempt)
                continue
            raise ClientError(f"connection failed: {e}") from e

    result = Result()
    parts: list[str] = []
    try:
        with resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line or line.startswith(":"):  # blank separators and keep-alive comments
                    continue
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    chunk = json.loads(payload)
                except json.JSONDecodeError:
                    continue
                if chunk.get("error"):
                    err = chunk["error"]
                    result.error = str(err.get("message") if isinstance(err, dict) else err)
                    result.partial = True
                result.generation_id = chunk.get("id") or result.generation_id
                result.model = chunk.get("model") or result.model
                result.provider = chunk.get("provider") or result.provider
                if chunk.get("usage"):
                    result.usage = chunk["usage"]
                for choice in chunk.get("choices") or []:
                    text = (choice.get("delta") or {}).get("content")
                    if text:
                        parts.append(text)
                        if on_text:
                            on_text(text)
                    if choice.get("finish_reason"):
                        result.finish_reason = choice["finish_reason"]
    except (OSError, ValueError) as e:  # dropped connection, read timeout, truncated chunk
        result.error = result.error or f"stream broke: {e}"
        result.partial = True
    result.content = "".join(parts)
    if not result.finish_reason and not result.error:
        result.error = "stream ended without a finish reason"
        result.partial = True
    return result


def cost_of(usage: dict) -> float | None:
    """Dollars OpenRouter charged, when the reply reported it."""
    cost = usage.get("cost")
    return float(cost) if cost is not None else None
