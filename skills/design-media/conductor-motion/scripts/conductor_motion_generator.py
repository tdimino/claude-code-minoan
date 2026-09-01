#!/usr/bin/env python3
"""
Conductor Motion Generator

Generates self-contained HTML files with behavioral animation patterns.
Reads from template files and applies composition parameters.

Usage:
    python3 conductor_motion_generator.py --mode typewriter --output out.html
    python3 conductor_motion_generator.py --mode progress --pacing fast --accent "#FF6B6B" --output out.html
    python3 conductor_motion_generator.py --mode file-review --files "Report.xlsx,Contract.pdf" --output out.html
"""

import argparse
import html as html_lib
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
TEMPLATES_DIR = SKILL_DIR / "assets" / "templates"

MODES = [
    "typewriter", "progress", "file-review", "stagger-reveal",
    "terminal", "lottie-compose", "streaming-text", "top-layer",
    "full-page", "catalog"
]

PACING_MULTIPLIERS = {"slow": 1.5, "medium": 1.0, "fast": 0.6}
STAGGER_SCALE = 0.8

DARK_TOKENS = {
    "--cm-bg": "#0B0F1A",
    "--cm-surface": "#141824",
    "--cm-elevated": "#1C2133",
    "--cm-card": "#242A3D",
    "--cm-text": "#E8ECF4",
    "--cm-text-70": "rgba(232, 236, 244, 0.7)",
    "--cm-text-40": "rgba(232, 236, 244, 0.4)",
    "--cm-text-20": "rgba(232, 236, 244, 0.2)",
    "--cm-border": "rgba(232, 236, 244, 0.15)",
    "--cm-border-subtle": "rgba(232, 236, 244, 0.08)",
}

LIGHT_TOKENS = {
    "--cm-bg": "#FFFFFF",
    "--cm-surface": "#F8F9FB",
    "--cm-elevated": "#F1F3F7",
    "--cm-card": "#E8ECF4",
    "--cm-text": "#0B0F1A",
    "--cm-text-70": "rgba(11, 15, 26, 0.7)",
    "--cm-text-40": "rgba(11, 15, 26, 0.4)",
    "--cm-text-20": "rgba(11, 15, 26, 0.2)",
    "--cm-border": "rgba(11, 15, 26, 0.12)",
    "--cm-border-subtle": "rgba(11, 15, 26, 0.06)",
}


HEX_COLOR_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
SAFE_FONT_RE = re.compile(r"^[a-zA-Z0-9 _\-]+$")


def escape_html(s: str) -> str:
    return html_lib.escape(s, quote=True)


def escape_js_string(s: str) -> str:
    return (
        s.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
        .replace("</", "<\\/")
    )


def validate_accent(accent: str) -> str:
    if not HEX_COLOR_RE.match(accent):
        sys.exit(f"Error: --accent must be a 6-digit hex color (e.g. #4F7BF7), got: {accent}")
    return accent


def validate_font(font: str) -> str:
    if not SAFE_FONT_RE.match(font):
        sys.exit(f"Error: --font contains invalid characters: {font}")
    return font


def read_template(mode: str) -> str:
    template_path = TEMPLATES_DIR / f"{mode}.html"
    if not template_path.exists():
        sys.exit(f"Error: Template not found: {template_path}")
    return template_path.read_text()


def apply_color_scheme(html: str, scheme: str) -> str:
    tokens = LIGHT_TOKENS if scheme == "light" else DARK_TOKENS
    for prop, value in tokens.items():
        pattern = rf"({re.escape(prop)}:\s*)[^;]+"
        safe_value = value
        html = re.sub(pattern, lambda m, v=safe_value: m.group(1) + v, html)
    return html


def apply_accent(html: str, accent: str) -> str:
    accent = validate_accent(accent)
    r, g, b = int(accent[1:3], 16), int(accent[3:5], 16), int(accent[5:7], 16)
    html = re.sub(r"(--cm-brand:\s*)[^;]+", lambda m: m.group(1) + accent, html)
    html = re.sub(
        r"(--cm-brand-40:\s*)[^;]+",
        lambda m: f"{m.group(1)}rgba({r}, {g}, {b}, 0.4)",
        html,
    )
    html = re.sub(
        r"(--cm-brand-20:\s*)[^;]+",
        lambda m: f"{m.group(1)}rgba({r}, {g}, {b}, 0.2)",
        html,
    )
    return html


def apply_pacing(html: str, pacing: str) -> str:
    mult = PACING_MULTIPLIERS.get(pacing, 1.0)
    stagger_mult = 1.0 + (mult - 1.0) * STAGGER_SCALE

    timing_patterns = [
        (r"(TYPE_MIN_MS\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(TYPE_MAX_MS\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(DELETE_MIN_MS\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(DELETE_MAX_MS\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(HOLD_MS\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(HOLD_FULL_MS\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(HOLD_EMPTY_MS\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(TYPE_SPEED\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(TYPE_VARIANCE\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(DELETE_SPEED\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(PROCESS_DURATION\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
        (r"(BETWEEN_WORDS_MS\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}"),
    ]

    stagger_patterns = [
        (r"(STAGGER_DELAY\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * stagger_mult)}"),
        (r"(REVEAL_STAGGER\s*=\s*)(\d+)", lambda m: f"{m.group(1)}{int(int(m.group(2)) * stagger_mult)}"),
    ]

    for pattern, repl in timing_patterns + stagger_patterns:
        html = re.sub(pattern, repl, html)

    html = re.sub(
        r"(--cm-stagger:\s*)(\d+)ms",
        lambda m: f"{m.group(1)}{int(int(m.group(2)) * stagger_mult)}ms",
        html,
    )
    html = re.sub(
        r"(--cm-hero-transition:\s*)(\d+)ms",
        lambda m: f"{m.group(1)}{int(int(m.group(2)) * mult)}ms",
        html,
    )

    return html


def apply_typing_speed(html: str, speed: int) -> str:
    s = str(int(speed))
    html = re.sub(r"(TYPE_SPEED\s*=\s*)\d+", lambda m: m.group(1) + s, html)
    html = re.sub(r"(TYPE_MIN_MS\s*=\s*)\d+", lambda m: m.group(1) + str(max(15, int(s) - 10)), html)
    html = re.sub(r"(TYPE_MAX_MS\s*=\s*)\d+", lambda m: m.group(1) + str(int(s) + 20), html)
    return html


def apply_stagger(html: str, stagger: int) -> str:
    s = str(int(stagger))
    html = re.sub(r"(--cm-stagger:\s*)\d+ms", lambda m: f"{m.group(1)}{s}ms", html)
    html = re.sub(r"(STAGGER_DELAY\s*=\s*)\d+", lambda m: m.group(1) + str(int(s) * 4), html)
    html = re.sub(r"(REVEAL_STAGGER\s*=\s*)\d+", lambda m: m.group(1) + s, html)
    return html


def apply_typewriter_content(html: str, base_text: str | None, words: str | None, cursor: str | None) -> str:
    if base_text:
        safe_html = escape_html(base_text)
        html = re.sub(r"(Accelerating)", lambda m: safe_html, html, count=1)
        html = re.sub(r"(rotator-base['\"]>)[^<]*", lambda m: m.group(1) + safe_html, html)

    if words:
        items = [w.strip() for w in words.split(",")]
        li_block = "\n".join(f"      <li>{escape_html(w)}</li>" for w in items)
        html = re.sub(
            r"(<ul[^>]*>).*?(</ul>)",
            lambda m: f"{m.group(1)}\n{li_block}\n    {m.group(2)}",
            html,
            count=1,
            flags=re.DOTALL,
        )
        js_array = "[" + ", ".join(f"'{escape_js_string(w)}'" for w in items) + "]"
        html = re.sub(
            r"(const (?:WORDS|TW_WORDS)\s*=\s*)\[[^\]]+\]",
            lambda m: m.group(1) + js_array,
            html,
        )

    if cursor and cursor != "|":
        safe_cursor = escape_html(cursor)
        html = html.replace(">|</span>", f">{safe_cursor}</span>")

    return html


def apply_progress_content(html: str, title: str | None, doc_count: int | None, rows: str | None) -> str:
    if title:
        safe_title = escape_html(title)
        html = re.sub(r"(search initialization)", lambda m: safe_title, html, count=2)

    if doc_count is not None:
        safe_count = str(int(doc_count))
        html = re.sub(r"(TARGET_DOC_COUNT\s*=\s*)\d+", lambda m: m.group(1) + safe_count, html, count=1)
        html = re.sub(r"(animateCounter\(\w+,\s*)\d+", lambda m: m.group(1) + safe_count, html, count=1)

    if rows:
        items = [r.strip() for r in rows.split(",")]
        js_array = "[" + ", ".join(f"'{escape_js_string(r)}'" for r in items) + "]"
        html = re.sub(
            r"(const (?:STATUS_ITEMS|STATUS|PROG_ITEMS)\s*=\s*)\[[^\]]+\]",
            lambda m: m.group(1) + js_array,
            html,
        )

    return html


def apply_file_review_content(html: str, files: str | None) -> str:
    if not files:
        return html
    items = [f.strip() for f in files.split(",")]
    js_array = "[" + ", ".join(f"'{escape_js_string(f)}'" for f in items) + "]"
    html = re.sub(
        r"(const (?:FILES|FR_FILES)\s*=\s*)\[[^\]]+\]",
        lambda m: m.group(1) + js_array,
        html,
    )
    return html


def apply_terminal_content(html: str, status_items: str | None, result_count: int | None, result_label: str | None) -> str:
    if status_items:
        items = [s.strip() for s in status_items.split(",")]
        js_array = "[" + ", ".join(f"'{escape_js_string(s)}'" for s in items) + "]"
        html = re.sub(
            r"(const STATUS_ITEMS\s*=\s*)\[[^\]]+\]",
            lambda m: m.group(1) + js_array,
            html,
        )

    if result_count is not None:
        safe_count = str(int(result_count))
        html = re.sub(r"(animateCounter\(\w+,\s*)\d+", lambda m: m.group(1) + safe_count, html, count=1)

    if result_label:
        safe_label = escape_html(result_label)
        html = re.sub(r"(>)Matches(<)", lambda m: m.group(1) + safe_label + m.group(2), html, count=1)

    return html


EASING_BODIES = {
    "cubic": "easeOutCubic",
    "quart": "t => 1 - Math.pow(1 - t, 4)",
    "linear": "t => t",
}


def apply_easing(html: str, easing: str) -> str:
    body = EASING_BODIES[easing]
    return re.sub(r"(const ease\s*=\s*)[^;]+;", lambda m: f"{m.group(1)}{body};", html)


def apply_progress_timing(html: str, duration: int | None, start_percent: int | None) -> str:
    if duration is not None:
        d = str(int(duration))
        html = re.sub(r"(TOTAL_MS\s*=\s*)\d+", lambda m: m.group(1) + d, html)
    if start_percent is not None:
        sp = int(start_percent)
        html = re.sub(r"(START_PROGRESS\s*=\s*)\d+", lambda m: m.group(1) + str(sp), html)
        html = re.sub(r'(aria-valuenow=")\d+(")', lambda m: f"{m.group(1)}{sp}{m.group(2)}", html, count=1)
        html = re.sub(r"scaleX\(0\.05\)", f"scaleX({sp / 100})", html)
    return html


def apply_hold_duration(html: str, hold: int) -> str:
    h = str(int(hold))
    html = re.sub(r"(HOLD_MS\s*=\s*)\d+", lambda m: m.group(1) + h, html)
    html = re.sub(r"(HOLD_FULL_MS\s*=\s*)\d+", lambda m: m.group(1) + h, html)
    return html


def apply_bool_const(html: str, const_name: str, value: bool) -> str:
    js_value = "true" if value else "false"
    return re.sub(
        rf"(const {const_name}\s*=\s*)(?:true|false)",
        lambda m: m.group(1) + js_value,
        html,
    )


def apply_lottie_config(html: str, src: str | None, loop: bool, autoplay: bool) -> str:
    if src:
        safe_src = escape_js_string(src)
        html = re.sub(r"(const LOTTIE_SRC\s*=\s*)'[^']*'", lambda m: f"{m.group(1)}'{safe_src}'", html)
    if not loop:
        html = apply_bool_const(html, "LOTTIE_LOOP", False)
    if not autoplay:
        html = apply_bool_const(html, "LOTTIE_AUTOPLAY", False)
    return html


LOTTIE_CDN_TAG = (
    '<script src="https://cdnjs.cloudflare.com/ajax/libs/lottie-web/5.12.2/lottie.min.js" '
    'integrity="sha512-jEnuIl4gMBNAxt8KPXGOO7TWnGfMCDkLfVKEME5WGqa/RjiVpKmQdv0YNGfDcCNnMg2iy9If3JOqYkIaW0GRQ==" '
    'crossorigin="anonymous" referrerpolicy="no-referrer"></script>'
)


def apply_lottie_cdn(html: str) -> str:
    if re.search(r'<script[^>]+lottie[^>]*\.js', html, re.IGNORECASE):
        return html
    return html.replace("</head>", f"{LOTTIE_CDN_TAG}\n</head>")


def apply_streaming_content(html: str, prompt: str | None, response: str | None) -> str:
    if prompt:
        safe_prompt = escape_html(prompt)
        html = re.sub(
            r'(id="stream-prompt">)[^<]*',
            lambda m: m.group(1) + safe_prompt,
            html,
        )
    if response:
        paragraphs = [p.strip() for p in response.split("||") if p.strip()]
        p_block = "".join(f"<p>{escape_html(p)}</p>" for p in paragraphs)
        html = re.sub(
            r'(id="stream-response">).*?(</div>)',
            lambda m: m.group(1) + p_block + m.group(2),
            html,
            flags=re.DOTALL,
        )
    return html


def apply_toast_messages(html: str, messages: str | None) -> str:
    if not messages:
        return html
    items = [m.strip() for m in messages.split(",")]
    js_array = "[\n    " + ",\n    ".join(f"'{escape_js_string(m)}'" for m in items) + ",\n  ]"
    html = re.sub(
        r"(const TOAST_MESSAGES\s*=\s*)\[[^\]]+\]",
        lambda m: m.group(1) + js_array,
        html,
    )
    return html


def apply_font(html: str, font: str) -> str:
    if font == "Geist":
        return html
    font = validate_font(font)
    font_url = font.replace(" ", "+")
    html = re.sub(
        r"family=Geist:wght@[^&]+&family=Geist\+Mono:wght@[^&]+",
        lambda m: f"family={font_url}:wght@300;400;500;600;700",
        html,
    )
    html = re.sub(
        r"(--cm-font:\s*)'Geist'",
        lambda m: f"{m.group(1)}'{font}'",
        html,
    )
    return html


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Generate Conductor Motion animation files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--mode", required=True, choices=MODES, help="Animation mode")
    p.add_argument("--output", "-o", required=True, help="Output HTML file path")
    p.add_argument("--pacing", choices=["slow", "medium", "fast"], default="medium")
    p.add_argument("--stagger", type=int, default=200, help="Base stagger ms (100-400)")
    p.add_argument("--typing-speed", type=int, default=45, help="Base typing ms per char (20-80)")
    p.add_argument("--color-scheme", choices=["dark", "light"], default="dark")
    p.add_argument("--accent", default="#4F7BF7", help="Brand accent hex color")
    p.add_argument("--font", default="Geist", help="Primary font name")
    p.add_argument("--easing", choices=["cubic", "quart", "linear"], default="cubic",
                   help="Primary rAF easing: easeOutCubic, easeOutQuart, or linear")
    p.add_argument("--typing-variance", type=int, help="Random ms variance added per typed char (0-40)")

    p.add_argument("--base-text", help="[typewriter] Static text before rotating words")
    p.add_argument("--words", help="[typewriter] Comma-separated rotating words")
    p.add_argument("--cursor", default="|", help="[typewriter] Cursor character")
    p.add_argument("--no-loop", action="store_true", help="[typewriter] Type the word list once, settle on the last word")
    p.add_argument("--hold-duration", type=int, help="[typewriter/terminal] Ms to hold a typed word before deleting")

    p.add_argument("--title", help="[progress] Header title text")
    p.add_argument("--doc-count", type=int, help="[progress] Document count target")
    p.add_argument("--rows", help="[progress/terminal] Comma-separated status labels")
    p.add_argument("--progress-duration", type=int, help="[progress] Total progress animation ms")
    p.add_argument("--start-percent", type=int, help="[progress] Initial bar percentage")

    p.add_argument("--files", help="[file-review] Comma-separated filenames")
    p.add_argument("--review-speed", type=int, default=2000, help="[file-review] Ms per file review")

    p.add_argument("--status-items", help="[terminal] Comma-separated status items")
    p.add_argument("--result-count", type=int, help="[terminal] Result counter target")
    p.add_argument("--result-label", help="[terminal] Result label text")
    p.add_argument("--no-timestamps", action="store_true", help="[terminal] Hide the timestamp column")

    p.add_argument("--prompt", help="[streaming-text] User message shown above the streamed response")
    p.add_argument("--response", help="[streaming-text] Response text; separate paragraphs with ||")
    p.add_argument("--toast-messages", help="[top-layer] Comma-separated toast messages")

    p.add_argument("--lottie-src", help="[lottie-compose] Lottie JSON URL loaded into data-lottie-slot containers")
    p.add_argument("--no-lottie-loop", action="store_true", help="[lottie-compose] Disable Lottie loop")
    p.add_argument("--no-lottie-autoplay", action="store_true", help="[lottie-compose] Disable autoplay")
    p.add_argument("--lottie-cdn", action="store_true", help="Include lottie-web CDN script in <head>")

    return p


def main():
    args = build_parser().parse_args()

    html = read_template(args.mode)

    if args.color_scheme != "dark":
        html = apply_color_scheme(html, args.color_scheme)

    if args.accent != "#4F7BF7":
        html = apply_accent(html, args.accent)

    if args.font != "Geist":
        html = apply_font(html, args.font)

    if args.pacing != "medium":
        html = apply_pacing(html, args.pacing)

    if args.typing_speed != 45:
        html = apply_typing_speed(html, args.typing_speed)

    if args.stagger != 200:
        html = apply_stagger(html, args.stagger)

    if args.easing != "cubic":
        html = apply_easing(html, args.easing)

    if args.typing_variance is not None:
        tv = str(int(args.typing_variance))
        html = re.sub(r"(TYPE_VARIANCE\s*=\s*)\d+", lambda m: m.group(1) + tv, html)

    if args.hold_duration is not None:
        html = apply_hold_duration(html, args.hold_duration)

    if args.no_loop:
        html = apply_bool_const(html, "LOOP", False)

    if args.no_timestamps:
        html = apply_bool_const(html, "SHOW_TIMESTAMPS", False)

    if args.mode == "typewriter":
        html = apply_typewriter_content(html, args.base_text, args.words, args.cursor)
    elif args.mode == "progress":
        html = apply_progress_content(html, args.title, args.doc_count, args.rows)
        html = apply_progress_timing(html, args.progress_duration, args.start_percent)
    elif args.mode == "file-review":
        html = apply_file_review_content(html, args.files)
        if args.review_speed != 2000:
            rs = str(int(args.review_speed))
            html = re.sub(r"(PROCESS_DURATION\s*=\s*)\d+", lambda m: m.group(1) + rs, html)
    elif args.mode == "terminal":
        html = apply_terminal_content(html, args.status_items, args.result_count, args.result_label)
    elif args.mode == "lottie-compose":
        html = apply_lottie_config(html, args.lottie_src, not args.no_lottie_loop, not args.no_lottie_autoplay)
    elif args.mode == "streaming-text":
        html = apply_streaming_content(html, args.prompt, args.response)
    elif args.mode == "top-layer":
        html = apply_toast_messages(html, args.toast_messages)
    elif args.mode == "full-page":
        html = apply_typewriter_content(html, args.base_text, args.words, args.cursor)
        html = apply_progress_content(html, args.title, args.doc_count, args.rows)
        html = apply_file_review_content(html, args.files)

    if args.lottie_cdn:
        html = apply_lottie_cdn(html)

    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(html)
    print(f"Generated: {out_path} ({len(html):,} bytes, mode={args.mode}, pacing={args.pacing})")


if __name__ == "__main__":
    main()
