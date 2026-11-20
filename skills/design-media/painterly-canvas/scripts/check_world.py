#!/usr/bin/env python3
"""
check_world.py: static check of a painterly-canvas HTML file against the skill's rules.

It reads the file as text and never executes it. Errors are rule breaks that make
the page unsafe to open or impossible to verify (network access, WebGL, no
?frame=N, a truncated document). Warnings need a human or a browser to judge.

Usage:
    python3 check_world.py scene.html
    python3 check_world.py scene.html --json

Exit codes: 0 no errors, 1 errors found, 2 usage.
"""

import argparse
import json
import re
import sys
from pathlib import Path

# (pattern, message). Each match is an error, reported with its line number.
ERROR_PATTERNS = [
    (r"<script\b[^>]*\bsrc\s*=", "external script (<script src>): the page must be one file"),
    (r"<link\b[^>]*\brel\s*=\s*[\"']?[^\"'>]*(stylesheet|preload|modulepreload|prefetch|preconnect|dns-prefetch)",
     "external resource (<link>)"),
    (r"<(img|audio|video|source|iframe|embed|object)\b[^>]*\b(src|data)\s*=\s*[\"']?(?!data:|blob:)",
     "external media or frame element"),
    (r"url\(\s*[\"']?https?:", "remote url() in CSS"),
    (r"@import\b", "CSS @import"),
    (r"\bfetch\s*\(", "fetch() call"),
    (r"\bXMLHttpRequest\b", "XMLHttpRequest"),
    (r"\bnew\s+WebSocket\b", "WebSocket"),
    (r"\bEventSource\b", "EventSource"),
    (r"\bsendBeacon\b", "navigator.sendBeacon"),
    (r"\bimportScripts\b|\bnew\s+(Shared)?Worker\b", "worker"),
    (r"^\s*import\s+[\w{*\"']|\bimport\s*\(", "module import"),
    (r"\.src\s*=\s*[\"'`]https?:", "remote src assignment"),
    (r"getContext\(\s*[\"'](webgl2?|experimental-webgl|webgpu|bitmaprenderer)[\"']", "non-2D canvas context"),
    (r"\bnavigator\.gpu\b", "WebGPU"),
]

# (pattern, message). Each match is a warning.
WARNING_PATTERNS = [
    (r"\beval\s*\(|\bnew\s+Function\s*\(", "eval or new Function (blocked by the injected CSP)"),
    (r"\blocalStorage\b|\bsessionStorage\b|\bindexedDB\b|document\.cookie", "browser storage"),
    (r"\{[^}]*\brandom\b[^}]*\}\s*=\s*Math\b", "Math.random destructured into an alias: trace it to the paint path"),
]

# (pattern, name, is_error). The pattern must appear at least once.
REQUIRED = [
    (r"<canvas\b|createElement\(\s*[\"']canvas[\"']", "a <canvas>", True),
    (r"getContext\(\s*[\"']2d[\"']", "a 2D context", True),
    (r"[\"']frame[\"']", "the ?frame=N parameter", True),
    (r"[\"']tod[\"']", "the ?tod parameter", False),
    (r"[\"']px[\"']", "the ?px parameter", False),
    (r"[\"']pz[\"']", "the ?pz parameter", False),
    (r"[\"']yaw[\"']", "the ?yaw parameter", False),
    (r"__paintStats", "?stats=1 reporting (window.__paintStats)", False),
    (r"prefers-reduced-motion", "a prefers-reduced-motion branch", False),
    (r"requestAnimationFrame", "a requestAnimationFrame loop", False),
]

MAX_LINES_PER_FINDING = 8


def _lines_matching(pattern: str, text: str, flags: int = re.I | re.M) -> list[int]:
    """1-indexed line numbers of every match."""
    return [text.count("\n", 0, m.start()) + 1 for m in re.finditer(pattern, text, flags)]


def _fmt_lines(lines: list[int]) -> str:
    shown = ", ".join(str(n) for n in lines[:MAX_LINES_PER_FINDING])
    more = len(lines) - MAX_LINES_PER_FINDING
    return f"line {shown}" + (f" and {more} more" if more > 0 else "")


def check_html(text: str) -> dict:
    """Check one HTML document. Returns {"errors": [...], "warnings": [...], "stats": {...}}."""
    errors: list[str] = []
    warnings: list[str] = []

    if not re.search(r"</html\s*>", text, re.I):
        errors.append("no closing </html>: the document is truncated")
    if not re.search(r"<!doctype html|<html[\s>]", text, re.I):
        errors.append("no <!doctype html> or <html>: not an HTML document")

    for pattern, message in ERROR_PATTERNS:
        hits = _lines_matching(pattern, text)
        if hits:
            errors.append(f"{message} ({_fmt_lines(hits)})")

    for pattern, message in WARNING_PATTERNS:
        hits = _lines_matching(pattern, text)
        if hits:
            warnings.append(f"{message} ({_fmt_lines(hits)})")

    for pattern, name, is_error in REQUIRED:
        if not re.search(pattern, text, re.I):
            (errors if is_error else warnings).append(f"missing {name}")

    random_hits = _lines_matching(r"\bMath\.random\b", text, re.M)
    if random_hits:
        warnings.append(
            f"Math.random at {len(random_hits)} site(s) ({_fmt_lines(random_hits)}): "
            "a fault if reachable from the paint path or from world generation"
        )

    return {
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "bytes": len(text.encode("utf-8")),
            "lines": text.count("\n") + 1,
            "math_random_sites": len(random_hits),
        },
    }


def format_report(result: dict, name: str = "") -> str:
    stats = result["stats"]
    verdict = "FAIL" if result["errors"] else "ok"
    out = [f"{verdict}  {name}  ({stats['bytes']:,} bytes, {stats['lines']:,} lines)"]
    out += [f"  error    {e}" for e in result["errors"]]
    out += [f"  warning  {w}" for w in result["warnings"]]
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Static check of a painterly-canvas HTML file.")
    parser.add_argument("files", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="print one JSON object keyed by file")
    args = parser.parse_args()

    results = {}
    for path in args.files:
        if not path.is_file():
            print(f"not a file: {path}", file=sys.stderr)
            return 2
        results[str(path)] = check_html(path.read_text(encoding="utf-8", errors="replace"))

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print("\n".join(format_report(r, name) for name, r in results.items()))
    return 1 if any(r["errors"] for r in results.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
