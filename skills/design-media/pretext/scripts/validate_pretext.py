#!/usr/bin/env python3
"""Validate a Pretext-generated HTML file for common issues."""
import re
import sys
import os

# ANSI colors (disabled when not a tty)
_tty = sys.stdout.isatty()
GREEN  = "\033[32m" if _tty else ""
RED    = "\033[31m" if _tty else ""
YELLOW = "\033[33m" if _tty else ""
RESET  = "\033[0m"  if _tty else ""
BOLD   = "\033[1m"  if _tty else ""


def pass_label():  return f"{GREEN}PASS{RESET}"
def fail_label():  return f"{RED}FAIL{RESET}"
def warn_label():  return f"{YELLOW}WARN{RESET}"


def check(name, result, detail=None, warn_only=False):
    """Return a result dict."""
    return {
        "name": name,
        "passed": bool(result),
        "warn_only": warn_only,
        "detail": detail,
    }


def validate(html: str) -> list[dict]:
    results = []

    # 1. ESM import from esm.sh/@chenglou/pretext
    esm_import = bool(re.search(
        r'import\s+[^"\']*["\']https://esm\.sh/@chenglou/pretext',
        html
    ))
    results.append(check(
        "ESM import from esm.sh/@chenglou/pretext",
        esm_import,
        detail=None if esm_import else "Expected: import ... from 'https://esm.sh/@chenglou/pretext'",
    ))

    # 2. <script type="module"> present
    module_script = bool(re.search(r'<script[^>]+type=["\']module["\']', html, re.IGNORECASE))
    results.append(check(
        '<script type="module"> tag present',
        module_script,
        detail=None if module_script else 'Expected: <script type="module">',
    ))

    # 3. Named font declaration — no `system-ui` in font strings
    # Look for font-family declarations or font strings and flag system-ui
    system_ui = bool(re.search(r'system-ui', html, re.IGNORECASE))
    results.append(check(
        "Named font declaration (no system-ui)",
        not system_ui,
        detail="Found 'system-ui' in font declaration — use an explicit named font instead" if system_ui else None,
    ))

    # 4. <meta name="viewport" present
    viewport = bool(re.search(r'<meta\s[^>]*name=["\']viewport["\']', html, re.IGNORECASE))
    results.append(check(
        '<meta name="viewport"> present',
        viewport,
        detail=None if viewport else 'Expected: <meta name="viewport" content="...">',
    ))

    # 5. Window resize handler
    resize_handler = bool(re.search(
        r"addEventListener\s*\(\s*['\"]resize['\"]|\.onresize\s*=",
        html
    ))
    results.append(check(
        "Window resize handler (addEventListener('resize') or onresize)",
        resize_handler,
        detail=None if resize_handler else "No resize handler found — canvas/renderer won't adapt to window changes",
    ))

    # 6. document.fonts.ready awaited (.then or await)
    fonts_ready = bool(re.search(
        r'document\.fonts\.ready\s*\.(then|catch)|await\s+document\.fonts\.ready',
        html
    ))
    results.append(check(
        "document.fonts.ready awaited (.then or await)",
        fonts_ready,
        detail=None if fonts_ready else "Expected: document.fonts.ready.then(...) or await document.fonts.ready",
    ))

    # 7. requestAnimationFrame present (WARN only — not a hard fail)
    raf = bool(re.search(r'requestAnimationFrame', html))
    results.append(check(
        "requestAnimationFrame present (for animated effects)",
        raf,
        detail="No requestAnimationFrame — OK for static effects, but required for animations" if not raf else None,
        warn_only=True,
    ))

    # 8. Touch event handlers present (WARN only)
    touch = bool(re.search(
        r"addEventListener\s*\(\s*['\"]touch(start|end|move|cancel)['\"]",
        html
    ))
    results.append(check(
        "Touch event handlers present (for interactive effects)",
        touch,
        detail="No touch handlers — OK for non-interactive effects, required for touch interaction" if not touch else None,
        warn_only=True,
    ))

    # 9. setInterval used alongside requestAnimationFrame (fail if both present)
    has_set_interval = bool(re.search(r'\bsetInterval\b', html))
    if raf and has_set_interval:
        # Both present — that's the violation
        results.append(check(
            "No setInterval used for animation (when requestAnimationFrame present)",
            False,
            detail="setInterval found alongside requestAnimationFrame — use rAF exclusively for animation timing",
        ))
    else:
        results.append(check(
            "No setInterval used for animation (when requestAnimationFrame present)",
            True,
        ))

    # 10. No framework imports (react, vue, svelte, angular)
    frameworks = ["react", "vue", "svelte", "angular"]
    found_frameworks = []
    for fw in frameworks:
        if re.search(
            r"""(import\s+[^"']*['"](https?://[^"']*?/)?""" + fw + r"""[/"']|require\s*\(\s*['"]""" + fw + r"""['"]\s*\))""",
            html,
            re.IGNORECASE,
        ):
            found_frameworks.append(fw)
    no_frameworks = len(found_frameworks) == 0
    results.append(check(
        "No framework imports (react, vue, svelte, angular)",
        no_frameworks,
        detail=f"Found framework import(s): {', '.join(found_frameworks)}" if found_frameworks else None,
    ))

    return results


def main():
    if len(sys.argv) != 2:
        print(f"Usage: {os.path.basename(sys.argv[0])} <path-to-html-file>")
        sys.exit(2)

    path = sys.argv[1]
    if not os.path.isfile(path):
        print(f"Error: file not found: {path}")
        sys.exit(2)

    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        html = fh.read()

    print(f"\n{BOLD}Pretext HTML Validator{RESET} — {path}\n")

    results = validate(html)

    required_checks = [r for r in results if not r["warn_only"]]
    warn_checks     = [r for r in results if r["warn_only"]]

    passed  = sum(1 for r in required_checks if r["passed"])
    total   = len(required_checks)
    any_fail = any(not r["passed"] for r in required_checks)

    for r in results:
        if r["warn_only"]:
            label = pass_label() if r["passed"] else warn_label()
        else:
            label = pass_label() if r["passed"] else fail_label()

        print(f"  [{label}] {r['name']}")
        if not r["passed"] and r["detail"]:
            print(f"         {YELLOW if r['warn_only'] else RED}{r['detail']}{RESET}")

    print()
    warn_count = sum(1 for r in warn_checks if not r["passed"])
    warn_suffix = f"  ({warn_count} warning{'s' if warn_count != 1 else ''})" if warn_count else ""
    summary_color = GREEN if not any_fail else RED
    print(f"{summary_color}{BOLD}{passed}/{total} required checks passed{RESET}{warn_suffix}\n")

    sys.exit(0 if not any_fail else 1)


if __name__ == "__main__":
    main()
