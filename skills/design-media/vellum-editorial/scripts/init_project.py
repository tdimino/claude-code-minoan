#!/usr/bin/env python3
"""Scaffold a new Vellum Editorial project."""

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
REQUIRED_ASSETS = ["_shared.css", "_components.css", "template.html", "template-subpage.html", "template-one-pager.html"]

FONT_EDITORIAL = '<link href="https://fonts.googleapis.com/css2?family=Bodoni+Moda:ital,wght@0,400;0,500;0,700;1,400;1,500&family=Inconsolata:wght@400;500;600;700&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap" rel="stylesheet">'
FONT_INSTRUMENT = '<link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700&family=Inconsolata:wght@400;500;600;700&display=swap" rel="stylesheet">'

DARK_PALETTE = """\
  /* Core palette — dark space */
  --copper: oklch(0.72 0.14 85);
  --ink: oklch(0.92 0.01 80);
  --bg: oklch(0.10 0.03 265);
  --bg-warm: oklch(0.12 0.025 265);
  --bg-card: oklch(0.15 0.02 265 / 0.85);
  --border: oklch(0.30 0.03 270 / 0.5);
  --border-strong: oklch(0.40 0.04 270 / 0.6);
  --text: oklch(0.90 0.01 80);
  --text-body: oklch(0.82 0.01 80);
  --text-dim: oklch(0.60 0.015 260);
  --text-muted: oklch(0.58 0.02 260);
  --text-label: oklch(0.63 0.015 260);
  --nav-active: oklch(0.72 0.12 160);
  --nav-active-bg: oklch(0.72 0.12 160 / 0.06);
  --nav-active-border: oklch(0.72 0.12 160 / 0.25);
  --ghost: oklch(0.30 0.02 270 / 0.4);
  --dossier-bg: oklch(0.16 0.02 260 / 0.9);
  --dossier-bg-secondary: oklch(0.14 0.025 260 / 0.85);\
"""

DARK_AUTH_OVERLAY = (
    "position:fixed;inset:0;z-index:9999;"
    "background:radial-gradient(ellipse 800px 400px at 40% 45%,"
    "oklch(0.25 0.08 260/0.35) 0%,transparent 65%),"
    "oklch(0.10 0.03 265);"
    "display:flex;align-items:center;justify-content:center;"
    "font-family:Inconsolata,monospace"
)

WARM_AUTH_OVERLAY = (
    "position:fixed;inset:0;z-index:9999;"
    "background:oklch(0.96 0.008 80);"
    "display:flex;align-items:center;justify-content:center;"
    "font-family:Inconsolata,monospace"
)

HEADERS_CONTENT = """\
/*
  X-Robots-Tag: noindex, nofollow
  X-Content-Type-Options: nosniff
  X-Frame-Options: DENY
  Referrer-Policy: no-referrer
  Permissions-Policy: camera=(), microphone=(), geolocation=(), interest-cohort=()
  Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://cdn.jsdelivr.net; font-src https://fonts.gstatic.com https://cdn.jsdelivr.net; img-src 'self' data:; connect-src 'self'
"""

ROBOTS_CONTENT = """\
User-agent: *
Disallow: /
"""

LIGHT_OVERRIDE_CSS = """
/* ─── LIGHT THEME OVERRIDE ─── */
:root[data-theme="light"] {
  --copper: oklch(0.45 0.12 55);
  --ink: oklch(0.22 0.04 270);
  --bg: oklch(0.96 0.008 80);
  --bg-warm: oklch(0.94 0.012 80);
  --bg-card: oklch(0.98 0.005 80);
  --border: oklch(0.82 0.015 75);
  --border-strong: oklch(0.68 0.02 70);
  --text: oklch(0.22 0.02 55);
  --text-body: oklch(0.32 0.015 55);
  --text-dim: oklch(0.45 0.01 55);
  --text-muted: oklch(0.42 0.01 55);
  --text-label: oklch(0.52 0.01 55);
  --nav-active: oklch(0.38 0.12 160);
  --nav-active-bg: oklch(0.38 0.12 160 / 0.06);
  --nav-active-border: oklch(0.38 0.12 160 / 0.22);
  --ghost: oklch(0.82 0.015 75);
  --dossier-bg: oklch(0.98 0.008 82);
  --dossier-bg-secondary: oklch(0.965 0.006 82);
}
:root[data-theme="light"] body::before,
:root[data-theme="light"] body::after { content: none; }
:root[data-theme="light"] body { background: oklch(0.96 0.008 80); }
.theme-toggle .ph-moon { display: none; }
:root[data-theme="light"] .theme-toggle .ph-sun { display: none; }
:root[data-theme="light"] .theme-toggle .ph-moon { display: block; }
"""

DARK_OVERRIDE_CSS = """
/* ─── DARK THEME OVERRIDE ─── */
:root[data-theme="dark"] {
  --copper: oklch(0.72 0.14 85);
  --ink: oklch(0.92 0.01 80);
  --bg: oklch(0.10 0.03 265);
  --bg-warm: oklch(0.12 0.025 265);
  --bg-card: oklch(0.15 0.02 265 / 0.85);
  --border: oklch(0.30 0.03 270 / 0.5);
  --border-strong: oklch(0.40 0.04 270 / 0.6);
  --text: oklch(0.90 0.01 80);
  --text-body: oklch(0.82 0.01 80);
  --text-dim: oklch(0.60 0.015 260);
  --text-muted: oklch(0.58 0.02 260);
  --text-label: oklch(0.63 0.015 260);
  --nav-active: oklch(0.72 0.12 160);
  --nav-active-bg: oklch(0.72 0.12 160 / 0.06);
  --nav-active-border: oklch(0.72 0.12 160 / 0.25);
  --ghost: oklch(0.30 0.02 270 / 0.4);
  --dossier-bg: oklch(0.16 0.02 260 / 0.9);
  --dossier-bg-secondary: oklch(0.14 0.025 260 / 0.85);
}
:root[data-theme="dark"] body::before {
  background: radial-gradient(circle at 1px 1px, oklch(0.25 0.004 85 / 0.12) 1px, transparent 0);
  background-size: 32px 32px;
}
.theme-toggle .ph-sun { display: none; }
:root[data-theme="dark"] .theme-toggle .ph-moon { display: none; }
:root[data-theme="dark"] .theme-toggle .ph-sun { display: block; }
"""


def fnv1a_hash(s: str) -> str:
    v = 0x811C9DC5
    for c in s:
        v = ((v ^ ord(c)) * 0x01000193) & 0xFFFFFFFF
    return format(v, "x")[:8]


def title_case(slug: str) -> str:
    return " ".join(w.capitalize() for w in slug.replace("-", " ").replace("_", " ").split())


def build_page_nav(pages: list[str], current: str = "") -> str:
    links = []
    for p in pages:
        name = title_case(p) if p != "index" else "Overview"
        href = f"{p}.html"
        if p == current:
            links.append(f'  <a href="{href}" aria-current="page">{name}</a>')
        else:
            links.append(f'  <a href="{href}">{name}</a>')
    return '<nav class="page-nav" aria-label="Pages">\n' + "\n".join(links) + "\n</nav>"


def render_template(template: str, variables: dict[str, str]) -> str:
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{{{key}}}}}", value)
    leftovers = re.findall(r"\{\{[A-Z_]+\}\}", result)
    if leftovers:
        raise ValueError(f"Unresolved template placeholders: {leftovers}")
    return result


def apply_dark_palette(css_text: str) -> str:
    """Replace the warm core palette block in _shared.css with dark space values."""
    lines = css_text.split("\n")
    output = []
    in_core = False
    replaced = False

    for line in lines:
        if not replaced and "/* Core palette" in line:
            in_core = True
            output.append(DARK_PALETTE)
            continue
        if in_core:
            if line.strip().startswith("--ghost:"):
                in_core = False
                replaced = True
            continue
        output.append(line)

    if not replaced:
        return css_text

    return "\n".join(output)


def apply_instrument_style(css_text: str) -> str:
    """Swap editorial typography for instrument-panel (Manrope) style."""
    css_text = css_text.replace(
        "--display: 'Bodoni Moda', serif;",
        "--display: 'Manrope', sans-serif;"
    )
    css_text = css_text.replace(
        "--body: 'Source Serif 4', serif;",
        "--body: 'Manrope', sans-serif;"
    )
    css_text = css_text.replace(
        "font-weight: 400; font-style: italic;",
        "font-weight: 700;"
    )
    css_text = css_text.replace(
        "url(\"data:image/svg+xml,%3Csvg width='60' height='60' xmlns='http://www.w3.org/2000/svg'%3E%3Cpath d='M0 30h60M30 0v60' stroke='%23c4b99a' stroke-width='0.4' opacity='0.28'/%3E%3C/svg%3E\")",
        "radial-gradient(circle at 1px 1px, oklch(0.55 0.004 85 / 0.10) 1px, transparent 0);\n  background-size: 32px 32px"
    )
    return css_text


def generate_auth_js(project_name: str, project_title: str, password: str, theme: str) -> str:
    """Generate auth gate JS with project-specific key and custom password hash."""
    pw_hash = fnv1a_hash(password)
    key = f"vellum_auth_{project_name}"

    if theme == "dark":
        overlay_style = DARK_AUTH_OVERLAY
        inner_html = (
            '<div style="text-align:center">'
            '<h2 style="font-family:Bodoni Moda,serif;font-style:italic;'
            "color:oklch(0.92 0.01 80);margin-bottom:1rem;font-size:2rem\">"
            f"{project_title}</h2>"
            '<p style="color:oklch(0.55 0.02 260);font-size:0.82rem;margin-bottom:1.25rem">'
            "Authentication Required</p>"
            '<input id="pw" type="password" aria-label="Password" placeholder="Password" '
            'style="font-family:Inconsolata,monospace;padding:0.6rem 1rem;'
            "border:1px solid oklch(0.30 0.03 270/0.5);border-radius:6px;"
            "font-size:1rem;width:220px;text-align:center;"
            'background:oklch(0.15 0.02 265);color:oklch(0.92 0.01 80)">'
            "<br>"
            '<button id="go" style="margin-top:0.75rem;padding:0.5rem 1.5rem;'
            "font-family:Inconsolata,monospace;font-size:0.85rem;"
            "background:oklch(0.72 0.14 85);color:oklch(0.10 0.03 265);"
            'border:none;border-radius:6px;cursor:pointer;font-weight:600">Enter</button>'
            '<p id="err" style="color:oklch(0.50 0.16 25);font-size:0.8rem;'
            'margin-top:0.5rem;display:none">Incorrect password</p></div>'
        )
    else:
        overlay_style = WARM_AUTH_OVERLAY
        inner_html = (
            '<div style="text-align:center">'
            '<h2 style="font-family:Bodoni Moda,serif;font-style:italic;'
            f'color:oklch(0.22 0.04 270);margin-bottom:1rem">{project_title}</h2>'
            '<input id="pw" type="password" aria-label="Password" placeholder="Password" '
            'style="font-family:Inconsolata,monospace;padding:0.6rem 1rem;'
            "border:1px solid oklch(0.82 0.015 75);border-radius:6px;"
            'font-size:1rem;width:220px;text-align:center">'
            "<br>"
            '<button id="go" style="margin-top:0.75rem;padding:0.5rem 1.5rem;'
            "font-family:Inconsolata,monospace;font-size:0.85rem;"
            "background:oklch(0.38 0.12 160);color:#fff;"
            'border:none;border-radius:6px;cursor:pointer">Enter</button>'
            '<p id="err" style="color:oklch(0.50 0.16 25);font-size:0.8rem;'
            'margin-top:0.5rem;display:none">Incorrect password</p></div>'
        )

    return f"""(function() {{
  var KEY = '{key}';
  var HASH = '{pw_hash}';
  function h(s) {{
    for (var i = 0, v = 0x811c9dc5; i < s.length; i++)
      v = (v ^ s.charCodeAt(i)) * 0x01000193 >>> 0;
    return (v >>> 0).toString(16).slice(0, 8);
  }}
  try {{
    if (sessionStorage.getItem(KEY) === HASH) return;
  }} catch (e) {{}}
  var overlay = document.createElement('div');
  overlay.style.cssText = '{overlay_style}';
  overlay.setAttribute('role', 'dialog');
  overlay.setAttribute('aria-label', 'Authentication required');
  overlay.innerHTML = '{inner_html}';
  document.body.appendChild(overlay);
  function check() {{
    if (h(document.getElementById('pw').value) === HASH) {{
      try {{
        sessionStorage.setItem(KEY, HASH);
      }} catch (e) {{}}
      overlay.remove();
      window.dispatchEvent(new CustomEvent('vellum:authenticated'));
    }} else {{
      document.getElementById('err').style.display = 'block';
    }}
  }}
  document.getElementById('go').onclick = check;
  document.getElementById('pw').onkeydown = function(e) {{ if (e.key === 'Enter') check(); }};
  document.getElementById('pw').focus();
}})();
"""


def add_starfield_css(css_text: str) -> str:
    """Replace the crosshatch texture with a CSS starfield for dark themes."""
    import random
    random.seed(42)

    small_stars = []
    for _ in range(55):
        x = random.randint(50, 1440)
        y = random.randint(30, 1800)
        a = round(random.uniform(0.4, 0.7), 2)
        small_stars.append(f"    {x}px {y}px 0 0 rgba(255,255,255,{a})")

    bright_stars = []
    tints = [
        "255,255,255", "200,220,255", "220,200,255", "200,210,255"
    ]
    for _ in range(25):
        x = random.randint(100, 1400)
        y = random.randint(50, 1800)
        spread = random.choice([0, 1, 1, 2])
        blur = random.choice([0, 1, 1])
        a = round(random.uniform(0.8, 0.95), 2)
        tint = random.choice(tints)
        bright_stars.append(f"    {x}px {y}px {blur}px {spread}px rgba({tint},{a})")

    starfield = f"""
/* ─── STARFIELD + NEBULA ─── */
body {{
  position: relative;
  background:
    radial-gradient(ellipse 900px 450px at 15% 25%, oklch(0.30 0.10 290 / 0.28) 0%, transparent 70%),
    radial-gradient(ellipse 700px 350px at 80% 55%, oklch(0.25 0.08 260 / 0.35) 0%, transparent 65%),
    radial-gradient(ellipse 500px 600px at 45% 85%, oklch(0.28 0.06 210 / 0.18) 0%, transparent 60%),
    var(--bg);
  background-attachment: fixed;
}}
@keyframes twinkle {{
  0%, 100% {{ opacity: 1; }}
  50% {{ opacity: 0.4; }}
}}
body::before, body::after {{
  content: '';
  position: fixed;
  top: 0; left: 0;
  pointer-events: none;
  z-index: 0;
}}
body::before {{
  width: 1px; height: 1px;
  box-shadow:
{',\\n'.join(small_stars)};
}}
body::after {{
  width: 2px; height: 2px;
  border-radius: 50%;
  box-shadow:
{',\\n'.join(bright_stars)};
  animation: twinkle 8s ease-in-out infinite;
}}
body > * {{ position: relative; z-index: 1; }}
"""

    lines = css_text.split("\n")
    output = []
    skip_body = False

    for line in lines:
        if "body::before" in line and "crosshatch" not in line.lower():
            continue
        if skip_body:
            if line.strip() == "}":
                skip_body = False
            continue
        if "body::before {" in line or ("body {" in line and "background" in css_text[css_text.index(line):css_text.index(line) + 200] if line in css_text else False):
            pass
        output.append(line)

    crosshatch_start = css_text.find("body::before")
    if crosshatch_start == -1:
        output.append(starfield)
    else:
        idx = next((i for i, l in enumerate(output) if "body::before" in l), len(output))
        output.insert(idx, starfield)

    return "\n".join(output)


def build_fouc_script(project_name: str, theme: str) -> str:
    key = f"vellum-theme-{project_name}"
    if theme == "dark":
        return (
            f"<script>(function(){{var t=localStorage.getItem('{key}');"
            "if(t==='light')document.documentElement.setAttribute('data-theme','light')"
            "})()</script>"
        )
    return (
        f"<script>(function(){{var t=localStorage.getItem('{key}');"
        "if(t==='dark')document.documentElement.setAttribute('data-theme','dark')"
        "})()</script>"
    )


def build_toggle_button() -> str:
    return (
        '<button class="theme-toggle" aria-label="Toggle light/dark mode" type="button">\n'
        '  <i class="ph ph-moon" aria-hidden="true"></i>\n'
        '  <i class="ph ph-sun" aria-hidden="true"></i>\n'
        '</button>'
    )


def build_toggle_script(project_name: str, theme: str) -> str:
    key = f"vellum-theme-{project_name}"
    alt = "light" if theme == "dark" else "dark"
    return (
        "<script>\n"
        "document.querySelector('.theme-toggle').addEventListener('click', function() {\n"
        f"  var r = document.documentElement, alt = '{alt}';\n"
        "  var current = r.getAttribute('data-theme');\n"
        "  if (current === alt) {\n"
        "    r.removeAttribute('data-theme');\n"
        f"    localStorage.removeItem('{key}');\n"
        "  } else {\n"
        "    r.setAttribute('data-theme', alt);\n"
        f"    localStorage.setItem('{key}', alt);\n"
        "  }\n"
        "});\n"
        "</script>"
    )


def create_project(args):
    output_path = Path(args.output_dir)
    if output_path.exists() and not output_path.is_dir():
        print(f"Error: --output-dir {output_path} exists but is not a directory.")
        raise SystemExit(1)

    project_dir = (output_path / args.project_name).resolve()
    if not str(project_dir).startswith(str(output_path.resolve())):
        print("Error: project-name must not contain path separators or traversal sequences.")
        raise SystemExit(1)

    if project_dir.exists():
        print(f"Error: {project_dir} already exists.")
        raise SystemExit(1)

    for asset in REQUIRED_ASSETS:
        if not (ASSETS_DIR / asset).exists():
            print(f"Error: required asset not found: {ASSETS_DIR / asset}")
            raise SystemExit(1)

    project_dir.mkdir(parents=True)

    shared_css = (ASSETS_DIR / "_shared.css").read_text()
    if args.style == "instrument":
        shared_css = apply_instrument_style(shared_css)
    if args.theme == "dark":
        shared_css = apply_dark_palette(shared_css)
        shared_css = add_starfield_css(shared_css)
        shared_css += LIGHT_OVERRIDE_CSS
    else:
        shared_css += DARK_OVERRIDE_CSS
    (project_dir / "_shared.css").write_text(shared_css)

    shutil.copy2(ASSETS_DIR / "_components.css", project_dir / "_components.css")

    project_title = title_case(args.project_name)

    if args.auth:
        auth_js = generate_auth_js(args.project_name, project_title, args.password, args.theme)
        (project_dir / "_auth.js").write_text(auth_js)

    if args.audio:
        shutil.copy2(ASSETS_DIR / "_audio-player.js", project_dir / "_audio-player.js")

    if args.deploy_ready:
        (project_dir / "_headers").write_text(HEADERS_CONTENT)
        (project_dir / "robots.txt").write_text(ROBOTS_CONTENT)

    font_import = FONT_INSTRUMENT if args.style == "instrument" else FONT_EDITORIAL

    if args.template == "one-pager":
        landing_template = (ASSETS_DIR / "template-one-pager.html").read_text()
    else:
        landing_template = (ASSETS_DIR / "template.html").read_text()
    subpage_template = (ASSETS_DIR / "template-subpage.html").read_text()
    year = str(datetime.now().year)
    auth_line = '<script src="_auth.js"></script>' if args.auth else ""
    audio_line = '<script src="_audio-player.js"></script>' if args.audio else ""

    pages = ["index"]
    if args.pages > 1:
        for i in range(1, args.pages):
            pages.append(f"page-{i}")

    for idx, page in enumerate(pages):
        page_nav = build_page_nav(pages, current=page)
        is_index = page == "index"

        footer_links = []
        if idx > 0:
            prev_name = "Overview" if pages[idx - 1] == "index" else title_case(pages[idx - 1])
            footer_links.append(f'<a href="{pages[idx - 1]}.html">&larr; {prev_name}</a>')
        if idx < len(pages) - 1:
            next_name = title_case(pages[idx + 1])
            footer_links.append(f'<a href="{pages[idx + 1]}.html">{next_name} &rarr;</a>')
        footer_nav = '<div class="footer__nav">\n    ' + "\n    ".join(footer_links) + "\n  </div>" if footer_links else ""

        variables = {
            "PROJECT_TITLE": project_title,
            "HEADLINE": project_title if is_index else title_case(page),
            "SUBTITLE": "Replace this subtitle with your own.",
            "PAGE_NAV": page_nav,
            "AUTH_SCRIPT": auth_line,
            "AUDIO_SCRIPT": audio_line,
            "FOOTER_NAV": footer_nav,
            "YEAR": year,
            "OG_DESCRIPTION": f"{project_title} — built with Vellum Editorial",
            "OG_IMAGE_URL": "og-image.png",
            "FOUC_SCRIPT": build_fouc_script(args.project_name, args.theme),
            "THEME_TOGGLE": build_toggle_button(),
            "TOGGLE_SCRIPT": build_toggle_script(args.project_name, args.theme),
            "FONT_IMPORT": font_import,
        }

        template_text = landing_template if is_index else subpage_template
        html = render_template(template_text, variables)
        (project_dir / f"{page}.html").write_text(html)

    print(f"Created {project_dir}/")
    print(f"  Style: {args.style}")
    print(f"  Theme: {args.theme}")
    print(f"  Template: {args.template}")
    print(f"  CSS:   _shared.css, _components.css")
    if args.auth:
        pw_hash = fnv1a_hash(args.password)
        print(f"  Auth:  _auth.js (hash: {pw_hash})")
    if args.audio:
        print(f"  Audio: _audio-player.js")
    if args.deploy_ready:
        print(f"  Deploy: _headers, robots.txt")
    print(f"  Toggle: light/dark theme toggle included")
    print(f"  Pages: {', '.join(p + '.html' for p in pages)}")
    print()
    print("Next steps:")
    print(f"  1. Open {project_dir / 'index.html'} in a browser")
    print("  2. Edit section content, add components from the catalog")
    print("  3. Customize :root variables in _shared.css for your brand")
    if args.audio:
        print("  4. Replace 'archive/track.mp3' in _audio-player.js with your audio file")
    if args.deploy_ready:
        print(f"  {'5' if args.audio else '4'}. Deploy: wrangler pages deploy {project_dir} --project-name {args.project_name}")


def main():
    parser = argparse.ArgumentParser(description="Scaffold a Vellum Editorial project")
    parser.add_argument("project_name", help="Project directory name (kebab-case)")
    parser.add_argument("--style", choices=["editorial", "instrument"], default="editorial",
                        help="Visual style: editorial (Bodoni Moda, crosshatch) or instrument (Manrope, grid dots)")
    parser.add_argument("--template", choices=["landing", "one-pager"], default="landing",
                        help="Content template: landing (simple sections) or one-pager (8-section TOC with cards)")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages (default: 1)")
    parser.add_argument("--theme", choices=["warm", "dark"], default="warm",
                        help="Color theme (default: warm)")
    parser.add_argument("--auth", action=argparse.BooleanOptionalAction, default=True,
                        help="Include auth gate (default: enabled)")
    parser.add_argument("--password", default=None,
                        help="Auth gate password (required when --auth is enabled)")
    parser.add_argument("--deploy-ready", action=argparse.BooleanOptionalAction, default=True,
                        help="Generate _headers and robots.txt for CF Pages (default: enabled)")
    parser.add_argument("--audio", action=argparse.BooleanOptionalAction, default=False,
                        help="Include audio player (default: disabled)")
    parser.add_argument("--output-dir", default=".", help="Parent directory for the project (default: cwd)")
    args = parser.parse_args()

    if args.pages < 1:
        parser.error("--pages must be at least 1")

    if args.auth and not args.password:
        parser.error("--password is required when --auth is enabled")

    if args.password and len(args.password) < 12:
        print(f"Warning: password is {len(args.password)} chars. 12+ recommended for FNV-1a courtesy gates.")

    create_project(args)


if __name__ == "__main__":
    main()
