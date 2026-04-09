#!/usr/bin/env python3
"""Validate a Mode 3 (tunnel gallery) HTML file for structural correctness."""

import re
import sys
from pathlib import Path


CHECKS = [
    {
        "name": "Three.js ESM import map",
        "pattern": r'<script\s+type="importmap"[^>]*>[\s\S]*?"three":\s*"[^"]*three[^"]*"',
        "required": True,
    },
    {
        "name": "Canvas container",
        "pattern": r'id=["\']canvas-container["\']|appendChild\(renderer\.domElement\)',
        "required": True,
    },
    {
        "name": "requestAnimationFrame loop",
        "pattern": r"requestAnimationFrame\s*\(",
        "required": True,
    },
    {
        "name": "Window resize handler",
        "pattern": r"addEventListener\s*\(\s*['\"]resize['\"]",
        "required": True,
    },
    {
        "name": "Mobile viewport meta",
        "pattern": r'<meta\s+[^>]*viewport[^>]*>',
        "required": True,
    },
    {
        "name": "Wheel scroll handler",
        "pattern": r"addEventListener\s*\(\s*['\"]wheel['\"]",
        "required": True,
    },
    {
        "name": "Touch scroll handlers",
        "pattern": r"addEventListener\s*\(\s*['\"]touch(start|move)['\"]",
        "required": True,
    },
    {
        "name": "Keyboard scroll handler (arrow keys)",
        "pattern": r"ArrowUp|ArrowDown|ArrowLeft|ArrowRight",
        "required": True,
    },
    {
        "name": "Catmull-Rom path generator",
        "pattern": r"function\s+catmullRom|catmullRom\s*\(",
        "required": True,
    },
    {
        "name": "Path interpolation function",
        "pattern": r"getInterpolatedData\s*\(",
        "required": True,
    },
    {
        "name": "Tunnel BufferGeometry",
        "pattern": r"BufferGeometry|Float32Array",
        "required": True,
    },
    {
        "name": "Ring-based image spawn loop",
        "pattern": r"imageDensity|maxImagesPerRing|spawn\s*\(.*distance",
        "required": True,
    },
    {
        "name": "Image cleanup behind camera",
        "pattern": r"scene\.remove\s*\([^)]*\)[\s\S]{0,200}?dispose\s*\(",
        "required": True,
    },
    {
        "name": "PerspectiveCamera setup",
        "pattern": r"PerspectiveCamera\s*\(",
        "required": True,
    },
    {
        "name": "WebGL error handling",
        "pattern": r"(showWebGLError|webgl-fallback|catch\s*\()",
        "required": True,
    },
    {
        "name": "IMAGE_MANIFEST injection sentinel",
        "pattern": r"IMAGES_INJECTION_POINT",
        "required": True,
    },
    {
        "name": "IMAGE_MANIFEST const (replaceable)",
        "pattern": r"const\s+IMAGE_MANIFEST\s*=",
        "required": True,
    },
    {
        "name": "phosphor-vigil FX hook",
        "pattern": r"PhosphorVigil|phosphor-vigil\.js",
        "required": True,
    },
    # ─── Anti-pattern checks (required: pattern must NOT match) ────
    {
        "name": "No React/JSX contamination",
        "pattern": r"from\s+['\"]react['\"]|useState|useFrame|<Canvas\b|\buseRef\s*<",
        "required": True,
        "invert": True,
    },
    {
        "name": "No pure-black background",
        "pattern": r"background:\s*#000\b|background:\s*#000000\b|new\s+THREE\.Color\(\s*0x000000\s*\)",
        "required": True,
        "invert": True,
    },
]


def validate(filepath: str) -> int:
    path = Path(filepath)
    if not path.exists():
        print(f"Error: File not found: {filepath}")
        return 1

    content = path.read_text(encoding="utf-8", errors="replace")
    if not content.strip():
        print(f"Error: File is empty: {filepath}")
        return 1

    passed = 0
    failed = 0
    warnings = 0

    for check in CHECKS:
        match = re.search(check["pattern"], content, re.IGNORECASE)
        inverted = check.get("invert", False)

        ok = (match is None) if inverted else (match is not None)

        if ok:
            print(f"  \u2713 {check['name']}")
            passed += 1
        elif check["required"]:
            label = "FORBIDDEN PATTERN PRESENT" if inverted else "MISSING"
            print(f"  \u2717 {check['name']} ({label})")
            failed += 1
        else:
            print(f"  ~ {check['name']} (optional, not found)")
            warnings += 1

    total = passed + failed
    print(f"\nResult: {passed}/{total} required checks passed", end="")
    if warnings:
        print(f" ({warnings} optional skipped)", end="")
    print()

    if failed > 0:
        print(f"FAIL: {failed} required check(s) missing")
        return 1
    else:
        print("PASS: All required checks satisfied")
        return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <html-file>")
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))
