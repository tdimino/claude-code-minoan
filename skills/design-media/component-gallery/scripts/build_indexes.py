#!/usr/bin/env python3
"""
Build static reference indexes from scraped component.gallery data.

Parses .staging/pages/ markdown files to generate:
  - references/component-index.md
  - references/design-system-index.md
  - references/component-taxonomy.md

Usage:
    python3 build_indexes.py
"""

import os
import re
import sys
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
STAGING_DIR = SKILL_DIR / ".staging"
PAGES_DIR = STAGING_DIR / "pages"
REFS_DIR = SKILL_DIR / "references"

# Functional categories for the taxonomy
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


def extract_component_data(filepath):
    """Extract component metadata from a scraped component page."""
    text = filepath.read_text(errors="replace")
    fm = extract_frontmatter(text)
    slug = filepath.stem.replace("components-", "")

    # Extract component name from first H1
    name_match = re.search(r"^#\s+(.+?)$", text, re.MULTILINE)
    name = name_match.group(1).strip() if name_match else slug.replace("-", " ").title()

    # Extract alternative names — look for "Also known as" or similar patterns
    alt_match = re.search(
        r"(?:Also known as|Alternative names?|Other names?)[:\s]*(.+?)(?:\n\n|\n#)",
        text, re.IGNORECASE | re.DOTALL,
    )
    alt_names = ""
    if alt_match:
        alt_names = alt_match.group(1).strip()
        alt_names = re.sub(r"\s+", " ", alt_names)

    # Extract example count
    count_match = re.search(r"(\d+)\s*(?:Examples?|examples?)", text)
    example_count = count_match.group(1) if count_match else "—"

    # Extract description — first real paragraph after the H1, skipping "Also known as" lines
    desc_match = re.search(
        r"^#\s+.+?\n\n(?:(?:Also known as|Alternative names?).*?\n\n)?(.+?)(?:\n\n|\n#)",
        text, re.MULTILINE | re.DOTALL,
    )
    description = ""
    if desc_match:
        candidate = desc_match.group(1).strip()
        # If we still got an "Also known as" line, skip it
        if not candidate.lower().startswith("also known as"):
            description = re.sub(r"\s+", " ", candidate)
            if len(description) > 200:
                description = description[:197] + "..."

    url = fm.get("url", f"https://component.gallery/components/{slug}/")

    return {
        "slug": slug,
        "name": name,
        "alt_names": alt_names,
        "example_count": example_count,
        "description": description,
        "url": url,
    }


def extract_design_systems(filepath):
    """Extract design system entries from the design-systems listing page."""
    text = filepath.read_text(errors="replace")
    systems = []

    # Split on H2 headers (each design system)
    sections = re.split(r"^##\s+", text, flags=re.MULTILINE)

    for section in sections[1:]:  # Skip preamble
        lines = section.strip().split("\n")
        if not lines:
            continue

        # First line is the name (possibly with link)
        name_line = lines[0].strip()
        name_match = re.match(r"\[(.+?)\]\((.+?)\)", name_line)
        if name_match:
            name = name_match.group(1)
            url = name_match.group(2)
        else:
            name = name_line.rstrip("#").strip()
            url = ""

        # Extract tech and features from remaining text
        rest = "\n".join(lines[1:])
        # Strip image tags to prevent garbage in parsed fields
        rest = re.sub(r"!\[.*?\]\(.*?\)", "", rest)
        tech = ""
        features = ""

        tech_match = re.search(r"(?:Tech|Technology|Stack)[:\s]*(.+?)(?:\n|$)", rest, re.IGNORECASE)
        if tech_match:
            tech = tech_match.group(1).strip()

        feat_match = re.search(r"(?:Features)[:\s]*(.+?)(?:\n|$)", rest, re.IGNORECASE)
        if feat_match:
            features = feat_match.group(1).strip()

        if name:
            systems.append({
                "name": name,
                "url": url,
                "tech": tech,
                "features": features,
            })

    return systems


def build_component_index(components):
    """Generate references/component-index.md."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# Component Index",
        f"",
        f"60 UI component types from [component.gallery](https://component.gallery/). Updated {today}.",
        f"",
        f"| Component | Alt Names | Examples | Description |",
        f"|-----------|-----------|----------|-------------|",
    ]

    for c in sorted(components, key=lambda x: x["name"].lower()):
        name_link = f"[{c['name']}]({c['url']})"
        alt = c["alt_names"] if c["alt_names"] else "—"
        lines.append(f"| {name_link} | {alt} | {c['example_count']} | {c['description'][:120]} |")

    lines.append("")
    return "\n".join(lines)


def build_design_system_index(systems):
    """Generate references/design-system-index.md."""
    today = datetime.now().strftime("%Y-%m-%d")
    lines = [
        f"# Design System Index",
        f"",
        f"95 design systems from [component.gallery](https://component.gallery/). Updated {today}.",
        f"",
        f"| Design System | Tech | Features |",
        f"|---------------|------|----------|",
    ]

    for s in sorted(systems, key=lambda x: x["name"].lower()):
        name_link = f"[{s['name']}]({s['url']})" if s["url"] else s["name"]
        tech = s["tech"] if s["tech"] else "—"
        features = s["features"] if s["features"] else "—"
        lines.append(f"| {name_link} | {tech} | {features} |")

    lines.append("")
    return "\n".join(lines)


def build_taxonomy(components):
    """Generate references/component-taxonomy.md."""
    today = datetime.now().strftime("%Y-%m-%d")
    comp_map = {c["slug"]: c for c in components}

    lines = [
        f"# Component Taxonomy",
        f"",
        f"Components grouped by functional category. Updated {today}.",
        f"",
    ]

    # Track assigned components to find any uncategorized ones
    assigned = set()

    for category, slugs in TAXONOMY.items():
        lines.append(f"## {category} ({len(slugs)} components)")
        lines.append("")
        lines.append("| Component | Examples | Description |")
        lines.append("|-----------|----------|-------------|")

        for slug in sorted(slugs):
            assigned.add(slug)
            c = comp_map.get(slug)
            if c:
                name_link = f"[{c['name']}]({c['url']})"
                lines.append(f"| {name_link} | {c['example_count']} | {c['description'][:100]} |")
            else:
                name = slug.replace("-", " ").title()
                lines.append(f"| {name} | — | — |")

        lines.append("")

    # Check for uncategorized components
    uncategorized = [c for c in components if c["slug"] not in assigned]
    if uncategorized:
        lines.append(f"## Uncategorized ({len(uncategorized)} components)")
        lines.append("")
        lines.append("| Component | Examples | Description |")
        lines.append("|-----------|----------|-------------|")
        for c in sorted(uncategorized, key=lambda x: x["name"].lower()):
            name_link = f"[{c['name']}]({c['url']})"
            lines.append(f"| {name_link} | {c['example_count']} | {c['description'][:100]} |")
        lines.append("")

    return "\n".join(lines)


def main():
    REFS_DIR.mkdir(parents=True, exist_ok=True)

    if not PAGES_DIR.exists():
        print(f"ERROR: {PAGES_DIR} not found. Run ingest.py first.")
        sys.exit(1)

    # Collect component pages
    component_files = sorted(PAGES_DIR.glob("components-*.md"))
    # Exclude the components listing page itself
    component_files = [f for f in component_files if f.stem != "components"]

    print(f"Found {len(component_files)} component page files")
    components = []
    for f in component_files:
        try:
            data = extract_component_data(f)
            components.append(data)
        except Exception as e:
            print(f"  WARNING: Failed to parse {f.name}: {e}")

    # Extract design systems
    ds_file = PAGES_DIR / "design-systems.md"
    systems = []
    if ds_file.exists():
        systems = extract_design_systems(ds_file)
        print(f"Found {len(systems)} design systems")
    else:
        print("WARNING: design-systems.md not found — skipping design system index")

    # Build indexes
    comp_index = build_component_index(components)
    (REFS_DIR / "component-index.md").write_text(comp_index)
    print(f"Wrote references/component-index.md ({len(components)} components)")

    if systems:
        ds_index = build_design_system_index(systems)
        (REFS_DIR / "design-system-index.md").write_text(ds_index)
        print(f"Wrote references/design-system-index.md ({len(systems)} systems)")

    taxonomy = build_taxonomy(components)
    (REFS_DIR / "component-taxonomy.md").write_text(taxonomy)
    print(f"Wrote references/component-taxonomy.md")

    print("\nDone.")


if __name__ == "__main__":
    main()
