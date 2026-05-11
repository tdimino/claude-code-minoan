#!/usr/bin/env python3
"""Validate a particle swarm sandbox runtime HTML file.

Checks for required structural elements, anti-patterns, and completeness.

Usage:
    python3 validate_sandbox.py <file.html>
"""

import re
import sys
from pathlib import Path

REQUIRED_CHECKS = [
    (r'three.*\.module\.js|from\s+["\']three["\']', 'Three.js module import'),
    (r'BufferGeometry|buffergeometry', 'BufferGeometry for particles'),
    (r'Float32Array', 'Float32Array for position/color buffers'),
    (r'requestAnimationFrame', 'requestAnimationFrame loop'),
    (r'addEventListener\s*\(\s*["\']resize["\']', 'Window resize handler'),
    (r'Math\.sin\(.*phi|Math\.cos\(.*theta|spherical', 'Spherical camera coordinates'),
    (r'addEventListener\s*\(\s*["\']pointer|addEventListener\s*\(\s*["\']touch', 'Touch/pointer event handlers'),
    (r'WebGLRenderer|webglrenderer', 'WebGL renderer'),
    (r'particleCount|PARTICLE_COUNT|particle_count', 'Particle count configuration'),
    (r'new\s+Function\s*\(|Function\s*\(', 'Function injection mechanism'),
    (r'FORBIDDEN_PATTERNS|forbidden|blacklist', 'Security validation patterns'),
    (r'addControl', 'addControl API implementation'),
    (r'setInfo', 'setInfo API implementation'),
    (r'annotate', 'annotate API implementation'),
    (r'needsUpdate\s*=\s*true', 'Buffer attribute update flag'),
    (r'PointsMaterial|pointsmaterial', 'Points material for particles'),
    (r'AdditiveBlending|additiveblending', 'Additive blending mode'),
    (r'devicePixelRatio|dpr', 'DPR handling'),
]

OPTIONAL_CHECKS = [
    (r'mediapipe|MediaPipe|Hands', 'MediaPipe Hands (gesture OS)'),
    (r'gesture|GESTURE', 'Gesture control system'),
    (r'textarea|code-editor', 'Code editor textarea'),
    (r'FogExp2|fogexp2', 'Exponential fog'),
    (r'auto.?orbit|autoOrbit', 'Camera auto-orbit'),
]

ANTI_PATTERNS = [
    (r'from\s+["\']react["\']|import\s+React|ReactDOM', 'No React/framework imports'),
    (r'#000000|0x000000', 'No pure black (use #050508)'),
    (r'OrbitControls|orbitcontrols', 'No OrbitControls (implement spherical camera directly)'),
    (r'setInterval\s*\(\s*animate|setInterval\s*\(\s*render', 'No setInterval for animation (use rAF)'),
    (r'THREE\.Geometry\b', 'No deprecated THREE.Geometry (use BufferGeometry)'),
    (r'from\s+["\']vue["\']|from\s+["\']svelte["\']|from\s+["\']angular["\']', 'No framework imports'),
]


def validate(html: str) -> tuple[list[str], list[str], list[str], list[str]]:
    """Returns (passed, failed, optional_passed, anti_pattern_violations)."""
    passed = []
    failed = []
    optional_passed = []
    violations = []

    for pattern, description in REQUIRED_CHECKS:
        if re.search(pattern, html, re.IGNORECASE):
            passed.append(description)
        else:
            failed.append(description)

    for pattern, description in OPTIONAL_CHECKS:
        if re.search(pattern, html, re.IGNORECASE):
            optional_passed.append(description)

    for pattern, description in ANTI_PATTERNS:
        if re.search(pattern, html, re.IGNORECASE):
            violations.append(description)

    return passed, failed, optional_passed, violations


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    filepath = Path(sys.argv[1])
    if not filepath.exists():
        print(f'Error: File not found: {filepath}')
        sys.exit(1)

    html = filepath.read_text()

    print(f'Validating sandbox: {filepath}')
    print(f'Lines: {len(html.splitlines())}')
    print(f'Size: {len(html) // 1024}KB')
    print()

    passed, failed, optional, violations = validate(html)

    print(f'REQUIRED ({len(passed)}/{len(passed) + len(failed)}):')
    for p in passed:
        print(f'  ✓ {p}')
    for f in failed:
        print(f'  ✗ {f}')
    print()

    if optional:
        print(f'OPTIONAL ({len(optional)}/{len(OPTIONAL_CHECKS)}):')
        for o in optional:
            print(f'  ✓ {o}')
        print()

    if violations:
        print(f'ANTI-PATTERN VIOLATIONS ({len(violations)}):')
        for v in violations:
            print(f'  ✗ {v}')
        print()

    total_required = len(passed) + len(failed)
    score = len(passed) / total_required * 100 if total_required else 0

    if not failed and not violations:
        print(f'✓ All {len(passed)} required checks passed')
    elif not failed:
        print(f'⚠ Required checks passed but {len(violations)} anti-pattern(s) found')
    else:
        print(f'✗ FAILED: {len(failed)}/{total_required} required checks missing ({score:.0f}%)')
        sys.exit(1)


if __name__ == '__main__':
    main()
