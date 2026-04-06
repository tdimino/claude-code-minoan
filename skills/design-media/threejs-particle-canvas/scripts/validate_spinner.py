#!/usr/bin/env python3
"""Validate a Three.js WebGPU spinner output file for structural correctness."""

import re
import sys
from pathlib import Path


CHECKS = [
    {
        "name": "Three.js TSL imports",
        "pattern": r"""(from\s+["']three/tsl["']|import\s+.*\bfrom\s+["']three/tsl["'])""",
        "required": True,
    },
    {
        "name": "Three.js WebGPU imports",
        "pattern": r"""(from\s+["']three/webgpu["']|import\s+.*\bfrom\s+["']three/webgpu["']|from\s+["']three["'])""",
        "required": True,
    },
    {
        "name": "PointsNodeMaterial",
        "pattern": r"PointsNodeMaterial",
        "required": True,
    },
    {
        "name": "BufferGeometry setup",
        "pattern": r"BufferGeometry|Float32Array",
        "required": True,
    },
    {
        "name": "Additive blending",
        "pattern": r"AdditiveBlending",
        "required": True,
    },
    {
        "name": "plotFunction defined",
        "pattern": r"(plotFunction|plot_function|plotFn)\s*[=:]",
        "required": True,
    },
    {
        "name": "Progress parameter (0-1 curve mapping)",
        "pattern": r"progress",
        "required": True,
    },
    {
        "name": "TSL time node (animation)",
        "pattern": r"\btime\b",
        "required": True,
    },
    {
        "name": "vec3 output",
        "pattern": r"vec3\s*\(",
        "required": True,
    },
    {
        "name": "Spinner class or instantiation",
        "pattern": r"(class\s+Spinner|new\s+\w*Spinner|export\s+.*spinner)",
        "required": True,
    },
    {
        "name": "Config object",
        "pattern": r"(strokeWidth|particleCount|config\s*[=:{])",
        "required": True,
    },
    # HTML-specific checks (only for self-contained HTML output)
    {
        "name": "Import map (HTML output)",
        "pattern": r"importmap",
        "required": False,
    },
    {
        "name": "WebGPURenderer (HTML output)",
        "pattern": r"WebGPURenderer",
        "required": False,
    },
    {
        "name": "Viewport meta (HTML output)",
        "pattern": r'<meta\s+[^>]*viewport[^>]*>',
        "required": False,
    },
    {
        "name": "Resize handler (HTML output)",
        "pattern": r"addEventListener\s*\(\s*['\"]resize['\"]",
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

    is_html = content.strip().startswith("<!DOCTYPE") or content.strip().startswith("<html")
    print(f"Detected format: {'HTML (self-contained)' if is_html else 'ES Module'}")
    print()

    passed = 0
    failed = 0
    warnings = 0

    for check in CHECKS:
        match = re.search(check["pattern"], content, re.IGNORECASE)
        required = check["required"]

        # HTML-specific checks become required for HTML output
        if not required and is_html and "HTML output" in check["name"]:
            required = True

        if match:
            print(f"  \u2713 {check['name']}")
            passed += 1
        elif required:
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
        print(f"Usage: {sys.argv[0]} <js-or-html-file>")
        sys.exit(1)
    sys.exit(validate(sys.argv[1]))
