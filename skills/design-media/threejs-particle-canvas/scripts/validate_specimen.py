#!/usr/bin/env python3
"""Validate a Mode 4 (living specimen) HTML file for structural correctness."""

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
        "name": "GLTFLoader import",
        "pattern": r"from\s+['\"]three/addons/loaders/GLTFLoader\.js['\"]|GLTFLoader",
        "required": True,
    },
    {
        "name": "SkeletonUtils import",
        "pattern": r"from\s+['\"]three/addons/utils/SkeletonUtils\.js['\"]|SkeletonUtils",
        "required": True,
    },
    {
        "name": "PhosphorVigil FX import",
        "pattern": r"from\s+['\"][^'\"]*phosphor-vigil\.js['\"]",
        "required": True,
    },
    {
        "name": "modelUrl config",
        "pattern": r"modelUrl\s*:",
        "required": True,
    },
    {
        "name": "specimenCount config",
        "pattern": r"specimenCount\s*:",
        "required": True,
    },
    {
        "name": "AnimationMixer usage",
        "pattern": r"new\s+THREE\.AnimationMixer\s*\(",
        "required": True,
    },
    {
        "name": "Specimen class",
        "pattern": r"class\s+Specimen\s*\{",
        "required": True,
    },
    {
        "name": "Mouse unproject to z=0 plane",
        "pattern": r"\.unproject\s*\(\s*camera",
        "required": True,
    },
    {
        "name": "Follow/wander behavior branch",
        "pattern": r"followMouse|'followMouse'",
        "required": True,
    },
    {
        "name": "Soft-wall repulsion (quadratic)",
        "pattern": r"r\s*\*\s*r\s*\*\s*25|Math\.sign\s*\(.*\)",
        "required": True,
    },
    {
        "name": "Velocity clamp",
        "pattern": r"velocity\.length\s*\(\)|vLen\s*>\s*maxV",
        "required": True,
    },
    {
        "name": "Velocity → timeScale modulation",
        "pattern": r"action\.timeScale\s*=",
        "required": True,
    },
    {
        "name": "Shared velocity channel",
        "pattern": r"sharedVelocity",
        "required": True,
    },
    {
        "name": "fx.setVelocity call",
        "pattern": r"fx\.setVelocity\s*\(",
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
        "name": "Touch event handlers",
        "pattern": r"addEventListener\s*\(\s*['\"]touch(start|move|end)['\"]",
        "required": True,
    },
    {
        "name": "Mobile scale handling",
        "pattern": r"mobileScale|matchMedia\s*\(\s*['\"]\s*\(\s*max-width",
        "required": True,
    },
    {
        "name": "Mobile viewport meta",
        "pattern": r'<meta\s+[^>]*viewport[^>]*>',
        "required": True,
    },
    {
        "name": "WebGL error handling",
        "pattern": r"(showWebGLError|webgl-fallback|catch\s*\()",
        "required": True,
    },
    {
        "name": "PerspectiveCamera setup",
        "pattern": r"PerspectiveCamera\s*\(",
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
        "name": "No drei imports",
        "pattern": r"from\s+['\"]@react-three/drei['\"]|useGLTF\b|useAnimations\b",
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
