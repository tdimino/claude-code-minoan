#!/usr/bin/env python3
"""Validate a Three.js particle canvas HTML file for structural correctness."""

import re
import sys
from pathlib import Path


CHECKS = [
    {
        "name": "Three.js import",
        "pattern": r'<script\s+src="[^"]*three[^"]*"',
        "required": True,
    },
    {
        "name": "Canvas container",
        "pattern": r'id=["\']canvas-container["\']|getElementById\(["\']canvas|appendChild\(renderer\.domElement\)',
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
        "name": "Phase definitions (2+)",
        "pattern": r"(phases|PHASES)\s*[=:]\s*\[",
        "required": True,
    },
    {
        "name": "Touch event handlers",
        "pattern": r"addEventListener\s*\(\s*['\"]touch(start|move|end)['\"]",
        "required": True,
    },
    {
        "name": "WebGL error handling",
        "pattern": r"(WebGL|webgl|getContext|failIfMajor|showWebGLError|catch\s*\()",
        "required": True,
    },
    {
        "name": "BufferGeometry particle system",
        "pattern": r"BufferGeometry|Float32Array",
        "required": True,
    },
    {
        "name": "PerspectiveCamera setup",
        "pattern": r"PerspectiveCamera\s*\(",
        "required": True,
    },
    {
        "name": "Additive blending",
        "pattern": r"AdditiveBlending|additive",
        "required": False,
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
        if match:
            print(f"  \u2713 {check['name']}")
            passed += 1
        elif check["required"]:
            print(f"  \u2717 {check['name']} (MISSING)")
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
