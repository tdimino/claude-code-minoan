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


def format_html(results: list[ImageResult], query: str, output_path: Path | None = None) -> Path:
    """Generate a Daimon Chamber-inspired HTML preview page."""
    if output_path is None:
        output_path = Path.home() / ".cache" / "image-well" / "preview.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    from html import escape as esc

    def _safe_url(raw: str) -> str:
        stripped = raw.strip()
        if stripped.lower().startswith(("http://", "https://", "data:image/")):
            return stripped
        return ""

    source_colors = {
        "openverse": "#4ade80", "wikimedia": "#a78bfa", "met": "#f0c040",
        "nasa": "#38bdf8", "pexels": "#f472b6", "pixabay": "#fb923c",
        "rijksmuseum": "#818cf8", "unsplash": "#34d399", "smithsonian": "#fbbf24",
        "europeana": "#c084fc", "iconify": "#94a3b8", "pollinations": "#f43f5e",
    }

    cards = []
    for r in results:
        thumb = esc(_safe_url(r.thumbnail_url or r.url))
        full_url = _safe_url(r.url)
        if full_url.lower().startswith("data:"):
            full_url = ""
        full = esc(full_url)
        title = esc(r.title[:80])
        dims = f"{r.width}\u00d7{r.height}" if r.width and r.height else "?"
        tags_str = ", ".join(r.tags[:5]) if r.tags else ""
        sc = source_colors.get(r.source, "rgba(201,162,39,0.3)")
        idx = len(cards)
        cards.append(f"""<div class="card" data-source="{esc(r.source)}" style="border-left:3px solid {sc};--i:{idx}">
  <div class="card-img"><span class="source-badge" style="background:rgba(0,0,0,0.6);border:1px solid {sc};color:{sc}">{esc(r.source)}</span><img src="{thumb}" alt="{title}" loading="lazy" data-full="{full}" onerror="this.parentElement.innerHTML='<div class=\\'broken\\'>Failed to load</div>'"></div>
  <div class="card-meta">
    <div class="card-title">{title}</div>
    <div class="card-details"><span class="card-source" style="color:{sc}">{esc(r.source)}</span> · {esc(dims)} · {esc(r.license)}</div>
    {f'<div class="card-tags">{esc(tags_str)}</div>' if tags_str else ''}
    <div class="card-links"><a href="{full}" target="_blank">Full image</a><a href="{esc(_safe_url(r.source_url))}" target="_blank">Source page</a></div>
  </div>
</div>""")

    sources = sorted(set(r.source for r in results))
    pills = '<button class="pill active" data-filter="all">All</button>'
    for s in sources:
        count = sum(1 for r in results if r.source == s)
        sc = source_colors.get(s, "#a89f8a")
        pills += f'<button class="pill" data-filter="{esc(s)}" data-color="{sc}">{esc(s)} ({count})</button>'

    now = datetime.now().strftime("%H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Image Well — {esc(query)}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&family=Playfair+Display:wght@700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-deep: #0a0a12;
    --bg-surface: #141220;
    --bg-img: #08080e;
    --border-dim: rgba(201,162,39,0.15);
    --border-gold: #c9a227;
    --text-primary: #e8e4d9;
    --text-secondary: #a89f8a;
    --text-muted: #706858;
    --accent: #966a85;
    --gold: #d4a843;
  }}
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: var(--bg-deep); color: var(--text-primary); font-family: 'Inter', system-ui, sans-serif; padding: 32px; min-height: 100vh; }}
  .header {{ margin-bottom: 24px; }}
  h1 {{ font-size: 22px; font-weight: 600; letter-spacing: -0.02em; }}
  h1 span {{ color: var(--gold); }}
  .subtitle {{ font-size: 13px; color: var(--text-muted); font-family: 'JetBrains Mono', monospace; margin-top: 6px; }}
  .pills {{ display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 28px; }}
  .pill {{ background: #1a1825; color: var(--text-secondary); border: 1px solid rgba(201,162,39,0.25); border-radius: 20px; padding: 6px 14px; font-size: 12px; font-family: 'JetBrains Mono', monospace; cursor: pointer; transition: all 0.2s; }}
  .pill:hover {{ transform: translateY(-1px); border-color: rgba(201,162,39,0.5); color: var(--text-primary); }}
  .pill.active {{ background: var(--accent); color: #fff; border-color: var(--accent); }}
  .grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 20px; }}
  .card {{ background: var(--bg-surface); border: 1px solid var(--border-dim); border-radius: 12px; overflow: hidden; transition: border-color 0.3s, box-shadow 0.3s, transform 0.3s; }}
  .card:hover {{ border-color: var(--border-gold); box-shadow: 0 4px 24px rgba(201,162,39,0.12); transform: translateY(-2px); }}
  .card.hidden {{ display: none; }}
  .card-img {{ display: flex; align-items: center; justify-content: center; background: var(--bg-img); min-height: 220px; padding: 16px; cursor: pointer; }}
  .card-img img {{ max-width: 100%; max-height: 300px; object-fit: contain; border-radius: 6px; transition: transform 0.3s; }}
  .card:hover .card-img img {{ transform: scale(1.03); }}
  .broken {{ color: var(--text-muted); font-size: 12px; font-family: 'JetBrains Mono', monospace; }}
  .card-meta {{ padding: 14px 16px 16px; border-top: 1px solid var(--border-dim); }}
  .card-title {{ font-size: 14px; font-weight: 500; line-height: 1.4; margin-bottom: 6px; color: var(--text-primary); }}
  .card-details {{ font-size: 11px; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; margin-bottom: 6px; }}
  .card-source {{ font-weight: 500; }}
  .card-tags {{ font-size: 10px; color: var(--text-muted); margin-bottom: 6px; }}
  .card-links {{ display: flex; gap: 12px; font-size: 11px; }}
  .card-links a {{ color: var(--gold); text-decoration: none; transition: color 0.2s; }}
  .card-links a:hover {{ color: #f0d890; text-decoration: underline; }}
  .modal {{ display: none; position: fixed; inset: 0; background: rgba(5,3,10,0.94); backdrop-filter: blur(4px); z-index: 100; align-items: center; justify-content: center; cursor: pointer; }}
  .modal.open {{ display: flex; }}
  .modal img {{ max-width: 90vw; max-height: 90vh; object-fit: contain; border-radius: 8px; border: 2px solid var(--border-gold); box-shadow: 0 8px 40px rgba(201,162,39,0.2); }}
  @media (max-width: 700px) {{ .grid {{ grid-template-columns: 1fr; }} body {{ padding: 16px; }} }}
  ::-webkit-scrollbar {{ width: 8px; }}
  ::-webkit-scrollbar-track {{ background: var(--bg-deep); }}
  ::-webkit-scrollbar-thumb {{ background: rgba(201,162,39,0.3); border-radius: 4px; }}
  ::-webkit-scrollbar-thumb:hover {{ background: rgba(201,162,39,0.5); }}

  /* View toggle */
  .view-toggle {{ position: absolute; top: 32px; right: 32px; display: flex; gap: 4px; background: #1a1825; border: 1px solid rgba(201,162,39,0.25); border-radius: 20px; padding: 3px; }}
  .view-btn {{ background: none; color: var(--text-secondary); border: none; border-radius: 16px; padding: 5px 12px; font-size: 11px; font-family: 'JetBrains Mono', monospace; cursor: pointer; transition: all 0.2s; }}
  .view-btn.active {{ background: var(--accent); color: #fff; }}

  /* ═══ DARKROOM VIEW (Kotharat: Murex Darkroom) ═══ */
  body.darkroom {{ --bg-deep: #0f0d10; --bg-surface: #1a161c; --border-dim: #3a3240; --text-primary: #e0d8ce; --text-secondary: #8a7e90; --text-muted: #605468; }}
  body.darkroom::before {{ content: ''; position: fixed; top: -200px; left: 50%; transform: translateX(-50%); width: 800px; height: 600px; background: radial-gradient(ellipse, rgba(212,168,67,0.08) 0%, transparent 70%); pointer-events: none; z-index: 0; }}
  body.darkroom .header {{ position: relative; z-index: 1; }}
  body.darkroom h1 {{ font-family: 'Playfair Display', Georgia, serif; font-size: 28px; font-weight: 700; letter-spacing: -0.02em; }}
  body.darkroom .grid {{ position: relative; z-index: 1; }}

  /* Darkroom cards — spotlight border */
  body.darkroom .card {{ position: relative; border-left: none !important; border: 1px solid #3a3240; border-radius: 8px; }}
  body.darkroom .card::before {{ content: ''; position: absolute; inset: -1px; border-radius: 9px; background: radial-gradient(circle 200px at var(--mx, 50%) var(--my, 50%), rgba(212,168,67,0.25) 0%, transparent 60%); opacity: 0; transition: opacity 0.3s; pointer-events: none; z-index: 1; }}
  body.darkroom .card:hover::before {{ opacity: 1; }}
  body.darkroom .card:hover {{ border-color: #504560; box-shadow: 0 8px 32px rgba(212,168,67,0.08); transform: translateY(-2px) scale(1.01); }}

  /* Darkroom image area — flush, with source badge */
  body.darkroom .card-img {{ padding: 0; position: relative; min-height: 200px; }}
  body.darkroom .card-img img {{ border-radius: 0; max-height: 280px; width: 100%; object-fit: cover; }}
  body.darkroom .card:hover .card-img img {{ transform: scale(1.03); filter: brightness(1.05); }}

  /* Source badge overlay */
  body.darkroom .card-meta .card-source {{ display: none; }}
  .source-badge {{ display: none; }}
  body.darkroom .source-badge {{ display: block; position: absolute; top: 10px; right: 10px; padding: 3px 8px; border-radius: 4px; font-size: 10px; font-family: 'JetBrains Mono', monospace; font-weight: 500; text-transform: uppercase; letter-spacing: 0.05em; backdrop-filter: blur(8px); z-index: 2; }}

  /* Darkroom metadata */
  body.darkroom .card-meta {{ border-top: 1px solid #3a3240; }}
  body.darkroom .card-title {{ font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 500; }}
  body.darkroom .card-tags {{ text-transform: uppercase; letter-spacing: 0.03em; font-size: 10px; background: #5e3a52; color: #c9a0b8; padding: 2px 6px; border-radius: 3px; display: inline-block; }}
  body.darkroom .card-links a {{ color: #d4a843; }}
  body.darkroom .card-links a:hover {{ color: #f0d890; }}

  /* Darkroom filter pills */
  body.darkroom .pill {{ text-transform: uppercase; letter-spacing: 0.05em; }}
  body.darkroom .pill.active {{ background: #5e3a52; border-color: #966a85; }}

  /* Staggered entrance */
  body.darkroom .card {{ animation: card-enter 400ms cubic-bezier(0.25, 1, 0.5, 1) forwards; opacity: 0; }}
  @keyframes card-enter {{ from {{ opacity: 0; transform: translateY(12px); }} to {{ opacity: 1; transform: translateY(0); }} }}

  @media (max-width: 700px) {{ .view-toggle {{ top: 16px; right: 16px; }} }}
  @media (prefers-reduced-motion: reduce) {{ body.darkroom .card {{ animation: none; opacity: 1; }} }}
  @media (min-width: 1200px) {{ body.darkroom .grid {{ grid-template-columns: repeat(3, 1fr); }} }}
</style>
</head><body>
<div class="header">
  <h1>Image Well — <span>"{esc(query)}"</span></h1>
  <div class="subtitle">{len(results)} results from {len(sources)} source{'s' if len(sources) != 1 else ''} · updated {now}</div>
  <div class="view-toggle"><button class="view-btn active" data-view="gallery">Gallery</button><button class="view-btn" data-view="darkroom">Darkroom</button></div>
</div>
<div class="pills">{pills}</div>
<div class="grid">
{"".join(cards)}
</div>
<div class="modal" id="modal"><img id="modal-img" src=""></div>
<script>
document.querySelectorAll('.pill').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.pill').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    const f = btn.dataset.filter;
    document.querySelectorAll('.card').forEach(card => {{
      card.classList.toggle('hidden', f !== 'all' && card.dataset.source !== f);
    }});
  }});
}});
const modal = document.getElementById('modal');
const modalImg = document.getElementById('modal-img');
document.querySelectorAll('.card-img').forEach(wrap => {{
  wrap.addEventListener('click', () => {{
    const img = wrap.querySelector('img');
    if (img) {{ modalImg.src = img.dataset.full || img.src; modal.classList.add('open'); }}
  }});
}});
modal.addEventListener('click', () => {{ modal.classList.remove('open'); modalImg.src = ''; }});
document.addEventListener('keydown', e => {{ if (e.key === 'Escape') {{ modal.classList.remove('open'); modalImg.src = ''; }} }});
// View toggle
document.querySelectorAll('.view-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.view-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.body.classList.toggle('darkroom', btn.dataset.view === 'darkroom');
  }});
}});
// Darkroom spotlight — track mouse position on cards
document.querySelectorAll('.card').forEach(card => {{
  card.addEventListener('mousemove', e => {{
    const r = card.getBoundingClientRect();
    card.style.setProperty('--mx', (e.clientX - r.left) + 'px');
    card.style.setProperty('--my', (e.clientY - r.top) + 'px');
  }});
}});
</script>
</body></html>"""

    output_path.write_text(html)
    return output_path


def format_tunnel(results: list[ImageResult], query: str, output_path: Path | None = None) -> Path:
    """
    Generate a 3D scrollable tunnel gallery by injecting search-result URLs
    into the threejs-particle-canvas skill's Mode 3 template.

    Reads the sibling skill's `tunnel-gallery-source.html` template, replaces
    the `IMAGE_MANIFEST` sentinel line with a real URL array, and writes the
    result to `output_path` (default: ~/.cache/image-well/tunnel.html).

    Raises FileNotFoundError with a clear install hint if the threejs-particle-canvas
    skill isn't present on this machine.
    """
    if output_path is None:
        output_path = Path.home() / ".cache" / "image-well" / "tunnel.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    canvas_assets = (
        Path.home() / ".claude" / "skills" / "threejs-particle-canvas" / "assets"
    )
    template_path = canvas_assets / "tunnel-gallery-source.html"
    fx_module_path = canvas_assets / "phosphor-vigil.js"

    if not template_path.exists():
        raise FileNotFoundError(
            f"Tunnel template not found at {template_path}. "
            f"Install the threejs-particle-canvas skill to use --format tunnel."
        )
    if not fx_module_path.exists():
        raise FileNotFoundError(
            f"Required FX module not found at {fx_module_path}. "
            f"Reinstall threejs-particle-canvas — phosphor-vigil.js is missing from assets/."
        )

    template = template_path.read_text(encoding="utf-8")

    # Build the manifest array — use full URLs, fall back to thumbnail if full is absent
    def _pick_url(r: ImageResult) -> str:
        raw = (r.url or r.thumbnail_url or "").strip()
        if raw.lower().startswith(("http://", "https://")):
            return raw
        return ""

    urls = [u for u in (_pick_url(r) for r in results) if u]
    if not urls:
        raise ValueError("No usable image URLs in results — nothing to inject into tunnel.")

    # JSON-encoded list — safe for direct JS embedding
    manifest_json = json.dumps(urls, ensure_ascii=False, indent=2)
    replacement = f"const IMAGE_MANIFEST = {manifest_json};"

    # Replace the single sentinel line. The template declares:
    #     const IMAGE_MANIFEST = null;  // Replaced by injection; null → seed mode
    if "const IMAGE_MANIFEST = null;" not in template:
        raise RuntimeError(
            "Tunnel template sentinel not found. Expected exact line "
            "'const IMAGE_MANIFEST = null;'. The template may have been modified."
        )

    injected = template.replace(
        "const IMAGE_MANIFEST = null;",
        replacement,
        1,
    )

    # Update the title so the generated file identifies itself
    safe_query = query.strip() or "Image Well Tunnel"
    injected = injected.replace(
        "<title>Infinite Gallery Tunnel</title>",
        f"<title>{safe_query} — Image Well Tunnel</title>",
        1,
    )

    output_path.write_text(injected, encoding="utf-8")

    # The template imports './phosphor-vigil.js' as a static ES module —
    # the import resolves regardless of CONFIG.fx, so the FX module must
    # exist as a sibling of the output HTML or the page won't load.
    fx_dest = output_path.parent / "phosphor-vigil.js"
    fx_dest.write_text(fx_module_path.read_text(encoding="utf-8"), encoding="utf-8")

    return output_path


def warn(msg: str) -> None:
    """Print warning to stderr."""
    print(f"  \u26a0 {msg}", file=sys.stderr)
