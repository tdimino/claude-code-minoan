#!/usr/bin/env python3
"""Validate a Mode 5 (vinyl showcase) HTML file for structural correctness."""

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
        "name": "PerspectiveCamera setup",
        "pattern": r"PerspectiveCamera\s*\(",
        "required": True,
    },
    {
        "name": "WebGLRenderer setup",
        "pattern": r"WebGLRenderer\s*\(",
        "required": True,
    },
    {
        "name": "ACESFilmic tone mapping",
        "pattern": r"ACESFilmicToneMapping",
        "required": True,
    },
    {
        "name": "Camera reflection: getUserMedia",
        "pattern": r"getUserMedia",
        "required": True,
    },
    {
        "name": "Camera reflection: VideoTexture",
        "pattern": r"VideoTexture\s*\(",
        "required": True,
    },
    {
        "name": "Camera reflection: CubeCamera",
        "pattern": r"CubeCamera\s*\(",
        "required": True,
    },
    {
        "name": "Camera reflection: PMREMGenerator",
        "pattern": r"PMREMGenerator\s*\(",
        "required": True,
    },
    {
        "name": "Camera reflection: envSphere (BackSide SphereGeometry)",
        "pattern": r"SphereGeometry\s*\(50|BackSide",
        "required": True,
    },
    {
        "name": "Camera fallback for missing webcam",
        "pattern": r"Camera unavailable|fallback",
        "required": True,
    },
    {
        "name": "Procedural groove normal map generator",
        "pattern": r"generateGrooveNormalMap",
        "required": True,
    },
    {
        "name": "Procedural scratch normal map generator",
        "pattern": r"generateScratchNormalMap",
        "required": True,
    },
    {
        "name": "Normal map color space (128,128,255)",
        "pattern": r"rgb\(128,128,255\)",
        "required": True,
    },
    {
        "name": "MeshPhysicalMaterial for vinyl disc",
        "pattern": r"MeshPhysicalMaterial\s*\(",
        "required": True,
    },
    {
        "name": "Clearcoat property",
        "pattern": r"clearcoat\s*:",
        "required": True,
    },
    {
        "name": "IOR 1.8 property",
        "pattern": r"ior\s*:\s*1\.8",
        "required": True,
    },
    {
        "name": "Iridescence on labels",
        "pattern": r"iridescence\s*:",
        "required": True,
    },
    {
        "name": "CylinderGeometry for disc",
        "pattern": r"CylinderGeometry\s*\(\s*2\s*,\s*2",
        "required": True,
    },
    {
        "name": "Label CircleGeometry",
        "pattern": r"CircleGeometry\s*\(\s*0\.5",
        "required": True,
    },
    {
        "name": "Scroll keyframe interpolation (smoothstep)",
        "pattern": r"t\s*\*\s*t\s*\*\s*\(3\s*-\s*2\s*\*\s*t\)",
        "required": True,
    },
    {
        "name": "getScrollProgress function",
        "pattern": r"getScrollProgress",
        "required": True,
    },
    {
        "name": "Raycaster for hit testing",
        "pattern": r"Raycaster\s*\(",
        "required": True,
    },
    {
        "name": "Pointer capture for drag",
        "pattern": r"setPointerCapture",
        "required": True,
    },
    {
        "name": "Scratch friction constant",
        "pattern": r"SCRATCH_FRICTION|0\.92",
        "required": True,
    },
    {
        "name": "spinPivot group hierarchy",
        "pattern": r"spinPivot",
        "required": True,
    },
    {
        "name": "Fixed canvas layout (position: fixed)",
        "pattern": r"position:\s*fixed",
        "required": True,
    },
    {
        "name": "Scrollable sections (min-height: 100vh)",
        "pattern": r"min-height:\s*100vh",
        "required": True,
    },
    {
        "name": "Pointer events management",
        "pattern": r"pointer-events:\s*(none|auto)",
        "required": True,
    },
    {
        "name": "requestAnimationFrame loop",
        "pattern": r"requestAnimationFrame\s*\(",
        "required": True,
    },
    {
        "name": "Window resize handler",
        "pattern": r'addEventListener\s*\(\s*[\'"]resize[\'"]',
        "required": True,
    },
    {
        "name": "Touch event handlers",
        "pattern": r'addEventListener\s*\(\s*[\'"]touch(start|move|end)[\'"]',
        "required": True,
    },
    {
        "name": "Mobile viewport meta",
        "pattern": r'<meta\s+[^>]*viewport[^>]*>',
        "required": True,
    },
    {
        "name": "WebGL error handling",
        "pattern": r"webgl-fallback|catch\s*\(",
        "required": True,
    },
    {
        "name": "5-light rig (ambient + directional + fill + rim + top)",
        "pattern": r"AmbientLight.*DirectionalLight.*PointLight",
        "required": True,
    },
    {
        "name": "Luminance-adaptive lighting",
        "pattern": r"smoothLum|analyzeLuminance|luminance",
        "required": True,
    },
    {
        "name": "Seeded random for label art",
        "pattern": r"seededRandom",
        "required": True,
    },
    {
        "name": "Edge wear effect",
        "pattern": r"drawEdgeWear|destination-out",
        "required": True,
    },
    {
        "name": "Section dots navigation",
        "pattern": r"section-dot",
        "required": True,
    },
    # ─── Anti-pattern checks ──────────────────────────────
    {
        "name": "No React/JSX contamination",
        "pattern": r"from\s+['\"]react['\"]|useState|useFrame|<Canvas\b",
        "required": True,
        "invert": True,
    },
    {
        "name": "No pure-black background",
        "pattern": r"background:\s*#000\b|background:\s*#000000\b|new\s+THREE\.Color\(\s*0x000000\s*\)",
        "required": True,
        "invert": True,
    },
    {
        "name": "No OrbitControls import",
        "pattern": r"OrbitControls",
        "required": True,
        "invert": True,
    },
]

# Optional checks for audio engine
AUDIO_CHECKS = [
    {
        "name": "AudioContext initialization",
        "pattern": r"AudioContext|webkitAudioContext",
        "required": False,
    },
    {
        "name": "Crackle noise buffer",
        "pattern": r"crackle|createNoiseBuffer",
        "required": False,
    },
    {
        "name": "Wow/flutter modulation",
        "pattern": r"wowPhase|flutterPhase|WOW_RATE|FLUTTER_RATE|0\.0015|0\.0004",
        "required": False,
    },
    {
        "name": "Lowpass filter sweep",
        "pattern": r"musicLPF|lowpass",
        "required": False,
    },
    {
        "name": "Reverse playback buffer",
        "pattern": r"getReversedBuffer|reversedBuffer",
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

    has_audio = bool(re.search(r"AudioContext|createNoiseBuffer", content))
    all_checks = CHECKS + (AUDIO_CHECKS if has_audio else [])

    passed = 0
    failed = 0
    warnings = 0

    print(f"Validating Mode 5 (Vinyl Showcase): {filepath}")
    print(f"Audio engine detected: {'yes' if has_audio else 'no'}")
    print()

    for check in all_checks:
        match = re.search(check["pattern"], content, re.IGNORECASE | re.DOTALL)
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
