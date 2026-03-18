#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["aiohttp"]
# ///
"""
Shared image-well utilities — ImageResult dataclass, credential loading,
cache management, license normalization, rate limiting.

Credentials: Per-source env vars, falls back to ~/.config/env/secrets.env
Cache: ~/.cache/image-well/searches/ (24h TTL)
"""

import asyncio
import hashlib
import json
import os
import re
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRETS_ENV = Path.home() / ".config" / "env" / "secrets.env"
CACHE_DIR = Path.home() / ".cache" / "image-well" / "searches"
CACHE_TTL_HOURS = 24


# ── ImageResult ──────────────────────────────────────────────────────────

@dataclass
class ImageResult:
    source: str
    title: str
    url: str
    thumbnail_url: str
    license: str
    attribution: str
    width: int
    height: int
    tags: list[str]
    source_url: str
    score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def to_row(self) -> list[str]:
        dims = f"{self.width}x{self.height}" if self.width and self.height else "?"
        title_short = self.title[:40] + "..." if len(self.title) > 43 else self.title
        return [self.source, title_short, dims, self.license, self.url[:60]]


# ── Credentials ──────────────────────────────────────────────────────────

_secrets_cache: dict[str, str] | None = None


def _load_secrets_env() -> dict[str, str]:
    """Load key=value pairs from ~/.config/env/secrets.env."""
    global _secrets_cache
    if _secrets_cache is not None:
        return _secrets_cache
    if not _SECRETS_ENV.exists():
        _secrets_cache = {}
        return _secrets_cache
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
    _secrets_cache = env
    return env


def get_api_key(env_var: str) -> str | None:
    """
    Get API key via 2-tier fallback:
    1. Environment variable
    2. ~/.config/env/secrets.env
    Returns None if not found (graceful degradation).
    """
    key = os.environ.get(env_var)
    if key:
        return key
    secrets = _load_secrets_env()
    return secrets.get(env_var)


# ── License normalization ────────────────────────────────────────────────

_LICENSE_MAP: list[tuple[re.Pattern, str]] = [
    (re.compile(r"cc0|cc-?zero|public\s*domain\s*dedication", re.I), "CC0"),
    (re.compile(r"pdm|public\s*domain\s*mark", re.I), "PD"),
    (re.compile(r"public\s*domain", re.I), "PD"),
    (re.compile(r"cc[\s-]*by[\s-]*nc[\s-]*sa[\s/-]*([\d.]+)?", re.I), "CC-BY-NC-SA"),
    (re.compile(r"cc[\s-]*by[\s-]*nc[\s-]*nd[\s/-]*([\d.]+)?", re.I), "CC-BY-NC-ND"),
    (re.compile(r"cc[\s-]*by[\s-]*nc[\s/-]*([\d.]+)?", re.I), "CC-BY-NC"),
    (re.compile(r"cc[\s-]*by[\s-]*sa[\s/-]*([\d.]+)?", re.I), "CC-BY-SA"),
    (re.compile(r"cc[\s-]*by[\s-]*nd[\s/-]*([\d.]+)?", re.I), "CC-BY-ND"),
    (re.compile(r"cc[\s-]*by[\s/-]*([\d.]+)?", re.I), "CC-BY"),
]


def normalize_license(raw: str) -> str:
    """Normalize license strings from various APIs to canonical form."""
    if not raw:
        return "Unknown"
    raw = raw.strip()
    for pattern, canonical in _LICENSE_MAP:
        m = pattern.search(raw)
        if m:
            version = m.group(1) if m.lastindex and m.group(1) else ""
            return f"{canonical}-{version}" if version else canonical
    # Pass through known non-CC licenses
    lower = raw.lower()
    if "pexels" in lower:
        return "Pexels"
    if "unsplash" in lower:
        return "Unsplash"
    if "pixabay" in lower:
        return "Pixabay"
    return raw


def license_matches(result_license: str, filter_license: str) -> bool:
    """Check if a result's license matches the requested filter."""
    if filter_license == "any":
        return True
    norm = result_license.upper().replace(" ", "")
    filt = filter_license.upper().replace(" ", "").replace("_", "-")
    if filt == "CC0":
        return norm in ("CC0", "PD")
    if filt == "CC-BY":
        return norm in ("CC0", "PD") or (norm.startswith("CC-BY") and "NC" not in norm and "ND" not in norm and "SA" not in norm)
    if filt == "CC-BY-SA":
        return norm.startswith("CC-BY-SA") or norm in ("CC0", "PD")
    return norm.startswith(filt)


# ── Rate limiter ─────────────────────────────────────────────────────────

class RateLimiter:
    """Simple per-source rate limiter using asyncio."""

    def __init__(self, min_interval: float):
        self.min_interval = min_interval
        self._lock = asyncio.Lock()
        self._last_request: float = 0.0

    async def wait(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self._last_request
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self._last_request = time.monotonic()


# ── Cache ────────────────────────────────────────────────────────────────

def _cache_key(query: str, sources: list[str], license_filter: str) -> str:
    raw = f"{query}|{','.join(sorted(sources))}|{license_filter}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def cache_get(query: str, sources: list[str], license_filter: str) -> list[ImageResult] | None:
    """Return cached results if they exist and haven't expired."""
    key = _cache_key(query, sources, license_filter)
    path = CACHE_DIR / f"{key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        ts = datetime.fromisoformat(data["timestamp"])
        age_hours = (datetime.now(timezone.utc) - ts).total_seconds() / 3600
        if age_hours > data.get("ttl_hours", CACHE_TTL_HOURS):
            path.unlink(missing_ok=True)
            return None
        return [ImageResult(**r) for r in data["results"]]
    except (json.JSONDecodeError, KeyError, TypeError):
        path.unlink(missing_ok=True)
        return None


def cache_put(query: str, sources: list[str], license_filter: str, results: list[ImageResult]) -> None:
    """Write results to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = _cache_key(query, sources, license_filter)
    path = CACHE_DIR / f"{key}.json"
    data = {
        "query": query,
        "sources": sorted(sources),
        "license": license_filter,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ttl_hours": CACHE_TTL_HOURS,
        "results": [r.to_dict() for r in results],
    }
    path.write_text(json.dumps(data, indent=2))


def cache_stats() -> dict[str, Any]:
    """Return cache statistics."""
    if not CACHE_DIR.exists():
        return {"entries": 0, "size_kb": 0}
    files = list(CACHE_DIR.glob("*.json"))
    total_size = sum(f.stat().st_size for f in files)
    return {"entries": len(files), "size_kb": round(total_size / 1024, 1)}


def cache_clear(older_than_days: int | None = None) -> int:
    """Clear cache entries. Returns count removed."""
    if not CACHE_DIR.exists():
        return 0
    removed = 0
    for f in CACHE_DIR.glob("*.json"):
        if older_than_days is not None:
            try:
                data = json.loads(f.read_text())
                ts = datetime.fromisoformat(data["timestamp"])
                age_days = (datetime.now(timezone.utc) - ts).total_seconds() / 86400
                if age_days < older_than_days:
                    continue
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        f.unlink()
        removed += 1
    return removed


# ── Output formatting ────────────────────────────────────────────────────

def format_table(results: list[ImageResult]) -> str:
    """Format results as a simple aligned table."""
    if not results:
        return "No results found."
    headers = ["Source", "Title", "Size", "License", "URL"]
    rows = [r.to_row() for r in results]
    # Calculate column widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))
    # Build table
    sep = "  "
    header_line = sep.join(h.ljust(widths[i]) for i, h in enumerate(headers))
    divider = sep.join("-" * w for w in widths)
    lines = [header_line, divider]
    for row in rows:
        lines.append(sep.join(cell.ljust(widths[i]) for i, cell in enumerate(row)))
    return "\n".join(lines)


def format_json(results: list[ImageResult]) -> str:
    """Format results as JSON array."""
    return json.dumps([r.to_dict() for r in results], indent=2)


def format_urls(results: list[ImageResult]) -> str:
    """One URL per line."""
    return "\n".join(r.url for r in results)


def warn(msg: str) -> None:
    """Print warning to stderr."""
    print(f"  \u26a0 {msg}", file=sys.stderr)
