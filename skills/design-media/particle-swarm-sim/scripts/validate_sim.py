#!/usr/bin/env python3
"""Validate a particle swarm behavior function body.

Checks API compliance, security constraints, and performance rules.
Does NOT execute the code (that requires a browser). Static analysis only.

Usage:
    python3 validate_sim.py <file.js>
    python3 validate_sim.py --stdin < code.js
"""

import re
import sys
from pathlib import Path

FORBIDDEN_PATTERNS = [
    (r'\bdocument\b', 'DOM access: document'),
    (r'\bwindow\b', 'Global scope: window'),
    (r'\bfetch\b', 'Network: fetch'),
    (r'\bXMLHttpRequest\b', 'Network: XMLHttpRequest'),
    (r'\bWebSocket\b', 'Network: WebSocket'),
    (r'\beval\b', 'Code injection: eval'),
    (r'\bFunction\s*\(', 'Code injection: Function constructor'),
    (r'\bimport\s*\(', 'Module: dynamic import'),
    (r'\brequire\s*\(', 'Module: require'),
    (r'\bprocess\b', 'System: process'),
    (r'\b__proto__\b', 'Prototype pollution: __proto__'),
    (r'\.prototype\b', 'Prototype chain: .prototype'),
    (r'\bglobalThis\b', 'Global scope: globalThis'),
    (r'\bself\b', 'Global scope: self'),
    (r'\blocation\b', 'Browser: location'),
    (r'\bnavigator\b', 'Browser: navigator'),
    (r'\blocalStorage\b', 'Storage: localStorage'),
    (r'\bsessionStorage\b', 'Storage: sessionStorage'),
    (r'\bindexedDB\b', 'Storage: indexedDB'),
    (r'\bcrypto\b', 'System: crypto'),
    (r'\bsetTimeout\b', 'Async: setTimeout'),
    (r'\bsetInterval\b', 'Async: setInterval'),
    (r'\balert\s*\(', 'UI hijack: alert'),
    (r'\bconfirm\s*\(', 'UI hijack: confirm'),
    (r'\bprompt\s*\(', 'UI hijack: prompt'),
    (r'\.constructor\b', 'Constructor chain escape'),
    (r'\bReflect\b', 'Metaprogramming: Reflect'),
    (r'\bProxy\b', 'Metaprogramming: Proxy'),
    (r'\bthis\s*\[', 'Dynamic property: this[...]'),
    (r'\bwhile\s*\(\s*true\s*\)', 'Infinite loop: while(true)'),
    (r'\bfor\s*\(\s*;\s*;\s*\)', 'Infinite loop: for(;;)'),
]

REQUIRED_PATTERNS = [
    (r'target\.set\s*\(', 'Must write particle position via target.set(x, y, z)'),
    (r'color\.set(HSL|RGB)?\s*\(', 'Must write particle color via color.setHSL() or color.set()'),
    (r'addControl\s*\(', 'Must have at least one interactive control'),
    (r'setInfo\s*\(', 'Must have a title/description via setInfo()'),
    (r'\btime\b', 'Must use time variable for animation'),
]

ALLOCATION_PATTERNS = [
    (r'\bnew\s+THREE\.Vector3\b', 'Zero-alloc violation: new THREE.Vector3 (use target.set)'),
    (r'\bnew\s+THREE\.Color\b', 'Zero-alloc violation: new THREE.Color (use color.setHSL)'),
    (r'\bnew\s+Array\b', 'Zero-alloc violation: new Array'),
    (r'\bnew\s+Object\b', 'Zero-alloc violation: new Object'),
]

RECOMMENDED_PATTERNS = [
    (r'if\s*\(\s*i\s*===\s*0\s*\)', 'Recommended: guard setInfo/annotate with if (i === 0)'),
    (r'Math\.(sin|cos)\b', 'Recommended: use trigonometric functions for smooth motion'),
    (r'\+\s*0\.0+1', 'Recommended: epsilon guard for divisions'),
]


def validate(code: str) -> tuple[list[str], list[str], list[str]]:
    """Returns (errors, warnings, notes)."""
    errors = []
    warnings = []
    notes = []

    for pattern, message in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            errors.append(f'SECURITY: {message}')

    for pattern, message in REQUIRED_PATTERNS:
        if not re.search(pattern, code):
            errors.append(f'API: {message}')

    for pattern, message in ALLOCATION_PATTERNS:
        if re.search(pattern, code):
            warnings.append(f'PERF: {message}')

    # Check for array literals inside what looks like per-particle code
    # (not at the top level before any target.set)
    lines = code.split('\n')
    found_target_set = False
    for line in lines:
        if 'target.set' in line:
            found_target_set = True
        if found_target_set and re.search(r'\[.*,.*\]', line):
            if not re.search(r'addControl|setInfo|annotate', line):
                warnings.append(f'PERF: Array literal after target.set (possible per-particle allocation)')
                break

    # Check for undeclared variables (heuristic: assignments without const/let)
    bare_assignments = re.findall(r'^\s*([a-zA-Z_]\w*)\s*=\s*(?!==)', code, re.MULTILINE)
    declared = set(re.findall(r'\b(?:const|let|var)\s+(\w+)', code))
    declared.update(['i', 'count', 'time', 'THREE', 'target', 'color'])
    for var in bare_assignments:
        if var not in declared:
            warnings.append(f'STYLE: Possible undeclared variable: {var}')

    for pattern, message in RECOMMENDED_PATTERNS:
        if not re.search(pattern, code):
            notes.append(message)

    return errors, warnings, notes


def main():
    if '--stdin' in sys.argv:
        code = sys.stdin.read()
        filename = '<stdin>'
    elif len(sys.argv) > 1:
        filepath = Path(sys.argv[1])
        if not filepath.exists():
            print(f'Error: File not found: {filepath}')
            sys.exit(1)
        code = filepath.read_text()
        filename = str(filepath)
    else:
        print(__doc__)
        sys.exit(1)

    errors, warnings, notes = validate(code)

    print(f'Validating: {filename}')
    print(f'Lines: {len(code.splitlines())}')
    print()

    if errors:
        print(f'ERRORS ({len(errors)}):')
        for e in errors:
            print(f'  ✗ {e}')
        print()

    if warnings:
        print(f'WARNINGS ({len(warnings)}):')
        for w in warnings:
            print(f'  ⚠ {w}')
        print()

    if notes:
        print(f'NOTES ({len(notes)}):')
        for n in notes:
            print(f'  ○ {n}')
        print()

    if not errors and not warnings:
        print('✓ All checks passed')
    elif not errors:
        print(f'✓ Passed with {len(warnings)} warning(s)')
    else:
        print(f'✗ FAILED: {len(errors)} error(s), {len(warnings)} warning(s)')
        sys.exit(1)


if __name__ == '__main__':
    main()
