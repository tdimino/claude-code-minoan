#!/usr/bin/env python3
"""Validator for scroll-cinema output HTML files.

Checks integration patterns, accessibility, performance, and anti-patterns
specific to Lenis + GSAP ScrollTrigger + Three.js cinematic scrolltelling.
"""

import re
import sys
from pathlib import Path


def check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    icon = "✅" if passed else "❌"
    msg = f"  {icon} {status}: {name}"
    if detail and not passed:
        msg += f" — {detail}"
    print(msg)
    return passed


def validate(filepath):
    content = Path(filepath).read_text(encoding="utf-8")
    content_lower = content.lower()

    results = []
    print(f"\nValidating: {filepath}")
    print("=" * 60)

    # --- CDN Imports ---
    print("\n[CDN Imports]")
    results.append(check(
        "Lenis CDN or import",
        "lenis" in content_lower,
        "Missing Lenis library import"
    ))
    results.append(check(
        "GSAP CDN or import",
        "gsap" in content_lower,
        "Missing GSAP library import"
    ))
    results.append(check(
        "ScrollTrigger import",
        "scrolltrigger" in content_lower,
        "Missing GSAP ScrollTrigger plugin"
    ))

    has_threejs = bool(re.search(r'three\.module\.js|from\s+["\']three["\']|THREE\.WebGLRenderer', content))

    # --- Critical Integration ---
    print("\n[Lenis + GSAP Integration]")
    has_autoraf_false = bool(re.search(r'autoRaf\s*:\s*false', content))
    results.append(check(
        "autoRaf: false",
        has_autoraf_false,
        "Lenis must have autoRaf: false when used with GSAP"
    ))
    results.append(check(
        "GSAP ticker drives Lenis",
        "gsap.ticker.add" in content and "lenis.raf" in content,
        "Missing gsap.ticker.add() with lenis.raf() — GSAP must drive Lenis"
    ))
    results.append(check(
        "ScrollTrigger.update in scroll callback",
        "ScrollTrigger.update" in content and "lenis.on" in content,
        "Missing lenis.on('scroll', ScrollTrigger.update)"
    ))
    results.append(check(
        "lagSmoothing(0)",
        "lagsmoothing(0)" in content_lower or "lagsmoothing( 0)" in content_lower,
        "Missing gsap.ticker.lagSmoothing(0) — causes scroll jumps"
    ))
    results.append(check(
        "time * 1000 in lenis.raf",
        "* 1000" in content and "lenis.raf" in content,
        "GSAP time is seconds, Lenis expects ms — need time * 1000"
    ))

    # --- Accessibility ---
    print("\n[Accessibility]")
    results.append(check(
        "prefers-reduced-motion",
        "prefers-reduced-motion" in content,
        "Missing prefers-reduced-motion media query or JS check"
    ))
    results.append(check(
        "Viewport meta tag",
        'name="viewport"' in content or "name='viewport'" in content,
        "Missing <meta name=\"viewport\"> tag"
    ))
    results.append(check(
        "Semantic <section> elements",
        "<section" in content_lower,
        "Chapters should use <section> elements"
    ))

    if has_threejs:
        results.append(check(
            "aria-hidden on canvas",
            'aria-hidden' in content_lower,
            "Three.js canvas should have aria-hidden=\"true\""
        ))

    # --- Performance ---
    print("\n[Performance]")
    results.append(check(
        "No setInterval for animation",
        "setinterval" not in content_lower or (
            "setinterval" in content_lower and
            content_lower.count("setinterval") == content_lower.count("clearinterval")
        ),
        "Use requestAnimationFrame via GSAP ticker, not setInterval"
    ))
    has_transition_all = bool(re.search(r'transition\s*:\s*all\b', content))
    results.append(check(
        "No transition: all",
        not has_transition_all,
        "Use explicit property transitions (opacity, transform), not 'all'"
    ))

    # --- Anti-Patterns ---
    print("\n[Anti-Patterns]")
    results.append(check(
        "No innerHTML for content",
        "innerhtml" not in content_lower or content_lower.count("innerhtml") <= 1,
        "Use textContent + DOM construction, not innerHTML (XSS risk)"
    ))
    results.append(check(
        "No Date.now() in animation",
        "date.now()" not in content_lower,
        "Use performance.now() — Date.now() is not monotonic"
    ))
    results.append(check(
        "No ScrollSmoother",
        "scrollsmoother" not in content_lower,
        "ScrollSmoother requires GSAP Club (paid). Use Lenis instead"
    ))

    # --- Additional Anti-Patterns ---
    has_standalone_raf = bool(re.search(r'requestAnimationFrame\s*\(', content))
    has_gsap_ticker = 'gsap.ticker.add' in content
    results.append(check(
        "No standalone requestAnimationFrame",
        not has_standalone_raf or has_gsap_ticker,
        "Use gsap.ticker.add() instead of standalone requestAnimationFrame"
    ))
    has_raw_scroll = bool(re.search(r'uniforms\.\w+\.value\s*=\s*scroll', content))
    results.append(check(
        "No raw scroll in uniforms",
        not has_raw_scroll,
        "Lerp scroll values — don't assign raw scroll to uniforms"
    ))
    has_bg_as_primary = (
        bool(re.search(r'backgroundColor\s*:', content)) and
        'gsap.to' in content and
        'oklch' not in content_lower and
        'hsl' not in content_lower
    )
    results.append(check(
        "No direct backgroundColor animation without color system",
        not has_bg_as_primary,
        "Use OKLCH/@property color system — backgroundColor is only acceptable as HSL fallback"
    ))

    # --- Entrance Patterns ---
    has_chapter_content = bool(re.search(r'class="chapter-title"', content))
    has_scroll_entrance = bool(re.search(r"gsap\.from\(.+scrollTrigger", content, re.DOTALL))
    has_toggle_actions = "toggleActions" in content
    if has_chapter_content:
        print("\n[Entrance Patterns]")
        results.append(check(
            "Scroll-driven entrance animations",
            has_scroll_entrance,
            "Sections should have GSAP ScrollTrigger-driven entrance animations"
        ))
        results.append(check(
            "toggleActions for reversible entrances",
            has_toggle_actions,
            "Use toggleActions for reversible section entrances, not once: true"
        ))
        has_reduced_motion_entrance = "reducedmotion" in content_lower or "reduced-motion" in content_lower
        results.append(check(
            "Entrance respects reduced-motion",
            has_reduced_motion_entrance,
            "Entrance animations must check prefers-reduced-motion"
        ))

    # --- SRI & Cleanup ---
    print("\n[SRI & Cleanup]")
    has_import_map = '"imports"' in content
    has_integrity = '"integrity"' in content or 'integrity="sha' in content
    if has_import_map:
        results.append(check(
            "SRI integrity hashes",
            has_integrity,
            "Add integrity hashes for SRI protection"
        ))
    has_cleanup = 'cleanup' in content_lower or 'destroy' in content_lower
    results.append(check(
        "Cleanup function present",
        has_cleanup,
        "Include cleanup/destroy function for SPA lifecycle"
    ))

    # --- Design Tokens ---
    print("\n[Design Tokens]")
    results.append(check(
        "--sc-* custom properties used",
        "--sc-" in content,
        "Use --sc-* token prefix for CSS custom properties"
    ))

    has_oklch = "oklch" in content_lower
    has_hsl_fallback = "hsl" in content_lower
    if has_oklch or has_hsl_fallback:
        results.append(check(
            "OKLCH or HSL color interpolation",
            True,
            ""
        ))
    else:
        results.append(check(
            "OKLCH or HSL color interpolation",
            False,
            "Chapter colors should use OKLCH interpolation (or HSL fallback)"
        ))

    # --- Summary ---
    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"\n{'=' * 60}")
    print(f"Results: {passed}/{total} passed, {failed} failed")

    if failed == 0:
        print("✅ All checks passed!")
    else:
        print(f"❌ {failed} check(s) failed — review above")

    return failed == 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 validate_scroll_cinema.py <output.html>")
        sys.exit(1)

    filepath = sys.argv[1]
    if not Path(filepath).exists():
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    success = validate(filepath)
    sys.exit(0 if success else 1)
