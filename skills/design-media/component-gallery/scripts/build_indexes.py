#!/usr/bin/env python3
"""
Build static reference indexes from scraped component.gallery data.

Parses .staging/pages/ markdown files into a single normalized dataset,
then generates all four reference outputs:
  - references/component-index.md
  - references/design-system-index.md
  - references/component-taxonomy.md
  - references/index.json

Usage:
    python3 build_indexes.py
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = SKILL_DIR / ".staging"
PAGES_DIR = STAGING_DIR / "pages"
REFS_DIR = SKILL_DIR / "references"

TAXONOMY = {
    "Forms": [
        "checkbox", "combobox", "color-picker", "date-input", "datepicker",
        "fieldset", "file-upload", "form", "label", "radio-button",
        "search-input", "select", "slider", "stepper", "text-input", "textarea", "toggle",
    ],
    "Navigation": [
        "breadcrumbs", "dropdown-menu", "footer", "header", "link",
        "navigation", "pagination", "skip-link", "tabs",
    ],
    "Feedback": [
        "alert", "empty-state", "progress-bar", "progress-indicator",
        "skeleton", "spinner", "toast",
    ],
    "Layout": [
        "accordion", "card", "carousel", "drawer", "hero", "modal", "popover",
        "separator", "stack",
    ],
    "Data Display": [
        "avatar", "badge", "heading", "icon", "image", "list", "quote",
        "rating", "table", "tree-view", "video", "visually-hidden",
    ],
    "Actions": [
        "button", "button-group", "file", "rich-text-editor",
        "segmented-control", "tooltip",
    ],
}


def extract_frontmatter(text):
    """Extract YAML frontmatter from markdown text."""
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}
    fm = {}
    for line in match.group(1).split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            fm[key.strip()] = val.strip().strip('"')
    return fm


def truncate_at_word(text, max_len):
    """Truncate text at a word boundary with a real ellipsis character."""
    if len(text) <= max_len:
        return text
    truncated = text[:max_len]
    last_space = truncated.rfind(" ")
    if last_space > max_len // 2:
        truncated = truncated[:last_space]
    return truncated.rstrip(",:;") + "…"


def get_crawl_date():
    """Determine the crawl date from crawl-meta.json or file mtime."""
    meta_path = STAGING_DIR / "crawl-meta.json"
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text())
            if "crawl_date" in meta:
                return meta["crawl_date"]
        except (json.JSONDecodeError, KeyError):
            pass
    ds_file = PAGES_DIR / "design-systems.md"
    if ds_file.exists():
        text = ds_file.read_text(errors="replace")
        fm = extract_frontmatter(text)
        if "scraped_date" in fm:
            return fm["scraped_date"]
        mtime = os.path.getmtime(ds_file)
        return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d")
    return "unknown"


def extract_component_data(filepath):
    """Extract component metadata from a scraped component page."""
    text = filepath.read_text(errors="replace")
    fm = extract_frontmatter(text)
    slug = filepath.stem.replace("components-", "")

    name_match = re.search(r"^#\s+(.+?)$", text, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else slug.replace("-", " ").title()

    alt_match = re.search(
        r"(?:Also known as|Alternative names?|Other names?)[:\s]*(.+?)(?:\n\n|\n#)",
        text, re.IGNORECASE | re.DOTALL,
    )
    alt_names = ""
    if alt_match:
        alt_names = alt_match.group(1).strip()
        alt_names = re.sub(r"\s+", " ", alt_names)

    count_match = re.search(r"(\d+)\s*(?:Examples?|examples?)", text)
    example_count = int(count_match.group(1)) if count_match else 0

    desc_match = re.search(
        r"^#\s+.+?\n\n(?:(?:Also known as|Alternative names?).*?\n\n)?(.+?)(?:\n\n|\n#)",
        text, re.MULTILINE | re.DOTALL,
    )
    description = ""
    if desc_match:
        candidate = desc_match.group(1).strip()
        if not candidate.lower().startswith("also known as"):
            description = re.sub(r"\s+", " ", candidate)

    url = fm.get("url", f"https://component.gallery/components/{slug}/")

    return {
        "slug": slug,
        "name": name,
        "alt_names": alt_names,
        "example_count": example_count,
        "description": description,
        "url": url,
    }


def collect_bullets_under_header(text, header_name):
    """Collect all bullet items under a ### header, anchored to the header line."""
    pattern = (
        r"^###\s+" + re.escape(header_name) + r"\s*\n"
        r"((?:\s*\n)*(?:\s*-\s+.+\n?)*)"
    )
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        return []
    block = match.group(1)
    items = re.findall(r"^\s*-\s+(.+)", block, re.MULTILINE)
    return [item.strip() for item in items]


def extract_design_systems(filepath):
    """Extract design system entries from the design-systems listing page."""
    text = filepath.read_text(errors="replace")
    systems = []

    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)

    for section in sections[1:]:
        lines = section.strip().split("\n")
        if not lines:
            continue

        name_line = lines[0].strip()
        name_match = re.match(r"\[(.+?)\]\((.+?)\)", name_line)
        if name_match:
            name = name_match.group(1)
            # Firecrawl backslash-escapes markdown metacharacters inside URLs
            # (e.g. fluentui\#/) — unescape them.
            url = re.sub(r"\\(.)", r"\1", name_match.group(2))
        else:
            name = name_line.rstrip("#").strip()
            url = ""

        rest = "\n".join(lines[1:])
        rest = re.sub(r"!\[.*?\]\(.*?\)", "", rest)

        tech = collect_bullets_under_header(rest, "Tech")
        features = collect_bullets_under_header(rest, "Features")

        if name:
            systems.append({
                "name": name,
                "url": url,
                "tech": tech,
                "features": features,
            })

    return systems


def load_ecosystem_currency():
    """Load the hand-written Ecosystem Currency section from the existing index."""
    ds_index_path = REFS_DIR / "design-system-index.md"
    if not ds_index_path.exists():
        return None
    text = ds_index_path.read_text(errors="replace")
    match = re.search(
        r"(## Ecosystem Currency.*?)(?=\n\||\n## [^E]|\Z)",
        text, re.DOTALL,
    )
    if match:
        return match.group(1).rstrip("\n") + "\n"
    return None


def build_component_index(components, crawl_date, today):
    """Generate references/component-index.md."""
    total_examples = sum(c["example_count"] for c in components)
    lines = [
        f"# Component Index",
        f"",
        f"{len(components)} UI component types, {total_examples:,} total examples"
        f" from [component.gallery](https://component.gallery/)."
        f" Source data: {crawl_date}. Indexes rebuilt: {today}.",
        f"",
        f"| Component | Alt Names | Examples | Description |",
        f"|-----------|-----------|----------|-------------|",
    ]

    for c in sorted(components, key=lambda x: x["name"].lower()):
        name_link = f"[{c['name']}]({c['url']})"
        alt = c["alt_names"] if c["alt_names"] else "—"
        count = str(c["example_count"]) if c["example_count"] else "—"
        desc = truncate_at_word(c["description"], 120)
        lines.append(f"| {name_link} | {alt} | {count} | {desc} |")

    lines.append("")
    return "\n".join(lines)


def build_design_system_index(systems, crawl_date, today, ecosystem_currency):
    """Generate references/design-system-index.md."""
    lines = [
        f"# Design System Index",
        f"",
        f"{len(systems)} design systems from [component.gallery](https://component.gallery/)."
        f" Source data: {crawl_date}. Indexes rebuilt: {today}.",
        f"",
    ]

    if ecosystem_currency:
        lines.append(ecosystem_currency)
        lines.append("")

    lines.append("| Design System | Tech | Features |")
    lines.append("|---------------|------|----------|")

    for s in sorted(systems, key=lambda x: x["name"].lower()):
        name_link = f"[{s['name']}]({s['url']})" if s["url"] else s["name"]
        tech = ", ".join(f"- {t}" for t in s["tech"]) if s["tech"] else "—"
        features = ", ".join(f"- {f}" for f in s["features"]) if s["features"] else "—"
        lines.append(f"| {name_link} | {tech} | {features} |")

    lines.append("")
    return "\n".join(lines)


def build_taxonomy(components, crawl_date, today):
    """Generate references/component-taxonomy.md."""
    comp_map = {c["slug"]: c for c in components}
    total_examples = sum(c["example_count"] for c in components)

    lines = [
        f"# Component Taxonomy",
        f"",
        f"{len(components)} components grouped by functional category,"
        f" {total_examples:,} total examples."
        f" Source data: {crawl_date}. Indexes rebuilt: {today}.",
        f"",
    ]

    assigned = set()

    for category, slugs in TAXONOMY.items():
        present = [s for s in slugs if s in comp_map]
        cat_examples = sum(comp_map[s]["example_count"] for s in present if s in comp_map)
        lines.append(f"## {category} ({len(slugs)} components, {cat_examples:,} examples)")
        lines.append("")
        lines.append("| Component | Examples | Description |")
        lines.append("|-----------|----------|-------------|")

        for slug in sorted(slugs):
            assigned.add(slug)
            c = comp_map.get(slug)
            if c:
                name_link = f"[{c['name']}]({c['url']})"
                count = str(c["example_count"]) if c["example_count"] else "—"
                desc = truncate_at_word(c["description"], 100)
                lines.append(f"| {name_link} | {count} | {desc} |")
            else:
                name = slug.replace("-", " ").title()
                lines.append(f"| {name} | — | — |")

        lines.append("")

    uncategorized = [c for c in components if c["slug"] not in assigned]
    if uncategorized:
        unc_examples = sum(c["example_count"] for c in uncategorized)
        lines.append(
            f"## Uncategorized (new upstream — assign a category)"
            f" ({len(uncategorized)} components, {unc_examples:,} examples)"
        )
        lines.append("")
        lines.append("| Component | Examples | Description |")
        lines.append("|-----------|----------|-------------|")
        for c in sorted(uncategorized, key=lambda x: x["name"].lower()):
            name_link = f"[{c['name']}]({c['url']})"
            count = str(c["example_count"]) if c["example_count"] else "—"
            desc = truncate_at_word(c["description"], 100)
            lines.append(f"| {name_link} | {count} | {desc} |")
        lines.append("")

    return "\n".join(lines)


def build_index_json(components, systems, crawl_date):
    """Generate references/index.json."""
    comp_list = []
    for c in sorted(components, key=lambda x: x["slug"]):
        alt_list = [a.strip() for a in c["alt_names"].split(",") if a.strip()] if c["alt_names"] else []
        comp_list.append({
            "slug": c["slug"],
            "name": c["name"],
            "url": c["url"],
            "alt_names": alt_list,
            "example_count": c["example_count"],
            "description": truncate_at_word(c["description"], 200),
        })

    ds_list = []
    for s in sorted(systems, key=lambda x: x["name"].lower()):
        ds_list.append({
            "name": s["name"],
            "url": s["url"],
            "tech": s["tech"],
            "features": s["features"],
            "gallery_url": "https://component.gallery/design-systems/",
        })

    total_examples = sum(c["example_count"] for c in components)

    data = {
        "url_formula": "https://component.gallery/components/{slug}/",
        "scraped_date": crawl_date,
        "source": "https://component.gallery/",
        "counts": {
            "components": len(components),
            "design_systems": len(systems),
            "total_examples": total_examples,
        },
        "components": comp_list,
        "design_systems": ds_list,
    }
    return json.dumps(data, indent=2, ensure_ascii=False) + "\n"


def main():
    REFS_DIR.mkdir(parents=True, exist_ok=True)

    if not PAGES_DIR.exists():
        print(f"ERROR: {PAGES_DIR} not found. Run ingest.py first.")
        sys.exit(1)

    crawl_date = get_crawl_date()
    today = datetime.now().strftime("%Y-%m-%d")

    component_files = sorted(PAGES_DIR.glob("components-*.md"))
    component_files = [f for f in component_files if f.stem != "components"]

    print(f"Found {len(component_files)} component page files")
    components = []
    for f in component_files:
        try:
            data = extract_component_data(f)
            components.append(data)
        except Exception as e:
            print(f"  WARNING: Failed to parse {f.name}: {e}")

    ds_file = PAGES_DIR / "design-systems.md"
    systems = []
    if ds_file.exists():
        systems = extract_design_systems(ds_file)
        print(f"Found {len(systems)} design systems")
    else:
        print("WARNING: design-systems.md not found — skipping design system index")

    all_assigned = set()
    for slugs in TAXONOMY.values():
        all_assigned.update(slugs)
    unassigned = [c for c in components if c["slug"] not in all_assigned]
    if unassigned:
        slugs_str = ", ".join(c["slug"] for c in unassigned)
        print(f"  WARNING: {len(unassigned)} uncategorized slugs: {slugs_str}")

    ecosystem_currency = load_ecosystem_currency()

    total_examples = sum(c["example_count"] for c in components)
    print(f"\nCanonical dataset: {len(components)} components, {len(systems)} systems,"
          f" {total_examples:,} total examples")
    print(f"Crawl date: {crawl_date}, rebuild date: {today}")

    comp_index = build_component_index(components, crawl_date, today)
    (REFS_DIR / "component-index.md").write_text(comp_index)
    print(f"\nWrote references/component-index.md ({len(components)} components)")

    if systems:
        ds_index = build_design_system_index(systems, crawl_date, today, ecosystem_currency)
        (REFS_DIR / "design-system-index.md").write_text(ds_index)
        print(f"Wrote references/design-system-index.md ({len(systems)} systems)")

    taxonomy = build_taxonomy(components, crawl_date, today)
    (REFS_DIR / "component-taxonomy.md").write_text(taxonomy)
    print(f"Wrote references/component-taxonomy.md")

    index_json = build_index_json(components, systems, crawl_date)
    (REFS_DIR / "index.json").write_text(index_json)
    print(f"Wrote references/index.json")

    print("\nDone.")


if __name__ == "__main__":
    main()
