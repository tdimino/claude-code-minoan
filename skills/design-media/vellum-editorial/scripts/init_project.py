#!/usr/bin/env python3
"""Scaffold a new Vellum Editorial project."""

import argparse
import re
import shutil
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = SKILL_DIR / "assets"
REQUIRED_ASSETS = ["_shared.css", "_components.css", "template.html", "template-subpage.html"]


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

    shutil.copy2(ASSETS_DIR / "_shared.css", project_dir / "_shared.css")
    shutil.copy2(ASSETS_DIR / "_components.css", project_dir / "_components.css")

    if args.auth:
        shutil.copy2(ASSETS_DIR / "_auth.js", project_dir / "_auth.js")

    landing_template = (ASSETS_DIR / "template.html").read_text()
    subpage_template = (ASSETS_DIR / "template-subpage.html").read_text()
    project_title = title_case(args.project_name)
    year = str(datetime.now().year)
    auth_line = '<script src="_auth.js"></script>' if args.auth else ""

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
            "FOOTER_NAV": footer_nav,
            "YEAR": year,
        }

        template_text = landing_template if is_index else subpage_template
        html = render_template(template_text, variables)
        (project_dir / f"{page}.html").write_text(html)

    print(f"Created {project_dir}/")
    print(f"  CSS:   _shared.css, _components.css")
    if args.auth:
        print(f"  Auth:  _auth.js (password: subqcode)")
    print(f"  Pages: {', '.join(p + '.html' for p in pages)}")
    print()
    print("Next steps:")
    print(f"  1. Open {project_dir / 'index.html'} in a browser")
    print("  2. Edit section content, add components from the catalog")
    print("  3. Customize :root variables in _shared.css for your brand")


def main():
    parser = argparse.ArgumentParser(description="Scaffold a Vellum Editorial project")
    parser.add_argument("project_name", help="Project directory name (kebab-case)")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages (default: 1)")
    parser.add_argument("--auth", action=argparse.BooleanOptionalAction, default=True,
                        help="Include auth gate (default: enabled)")
    parser.add_argument("--output-dir", default=".", help="Parent directory for the project (default: cwd)")
    args = parser.parse_args()

    if args.pages < 1:
        parser.error("--pages must be at least 1")

    create_project(args)


if __name__ == "__main__":
    main()
