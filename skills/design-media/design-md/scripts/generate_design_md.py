#!/usr/bin/env python3
"""Generate a DESIGN.md scaffold from an existing project's CSS tokens.

Scans a project directory for CSS files containing design tokens (custom
properties, font declarations, color values, spacing, shadows, breakpoints)
and organizes them into the Google Stitch 9-section DESIGN.md format.

Prose sections (Visual Theme, Do's/Don'ts) are left as TODO placeholders
for human or Claude completion.

Usage:
    python3 generate_design_md.py <project-path>
    python3 generate_design_md.py <project-path> --output DESIGN.md
    python3 generate_design_md.py . --output DESIGN.md
"""

import argparse
import os
import re
import sys
from collections import defaultdict
from pathlib import Path


# ── CSS file discovery ─────────────────────────────────────────────────────

PRIORITY_FILENAMES = [
    "globals.css",
    "global.css",
    "theme.css",
    "tokens.css",
    "variables.css",
    "design-tokens.css",
    "app.css",
    "style.css",
    "styles.css",
    "index.css",
]

SKIP_DIRS = {
    "node_modules",
    ".next",
    "dist",
    "build",
    "out",
    ".git",
    ".cache",
    "__pycache__",
    "vendor",
    ".worktrees",
}


def find_css_files(project_path: Path) -> list[Path]:
    """Find CSS files likely to contain design tokens, prioritized."""
    found = []
    for root_str, dirs, files in os.walk(project_path):
        root = Path(root_str)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if f.endswith(".css") and not f.startswith("_"):
                found.append(root / f)

    # Sort: priority filenames first, then by depth (shallower = more likely tokens)
    priority_set = set(PRIORITY_FILENAMES)

    def sort_key(p: Path) -> tuple[int, int, str]:
        name = p.name.lower()
        priority = PRIORITY_FILENAMES.index(name) if name in priority_set else 100
        depth = len(p.relative_to(project_path).parts)
        return (priority, depth, str(p))

    found.sort(key=sort_key)
    return found


# ── Token extraction ───────────────────────────────────────────────────────

COLOR_HEX_RE = re.compile(r"(#[0-9a-fA-F]{3,8})\b")
COLOR_RGB_RE = re.compile(r"(rgba?\([^)]+\))")
COLOR_HSL_RE = re.compile(r"(hsla?\([^)]+\))")
COLOR_OKLCH_RE = re.compile(r"(oklch\([^)]+\))")
CUSTOM_PROP_RE = re.compile(r"--([\w-]+)\s*:\s*([^;]+);")
FONT_FAMILY_RE = re.compile(r"font-family\s*:\s*([^;]+);")
FONT_SIZE_RE = re.compile(r"font-size\s*:\s*([^;]+);")
BOX_SHADOW_RE = re.compile(r"box-shadow\s*:\s*([^;]+);")
BORDER_RADIUS_RE = re.compile(r"border-radius\s*:\s*([^;]+);")
BREAKPOINT_RE = re.compile(r"@media[^{]*\(\s*(?:min|max)-width\s*:\s*(\d+)px\s*\)")
THEME_BLOCK_RE = re.compile(r"@theme\s*\{([^}]+)\}", re.DOTALL)


def classify_color_prop(name: str) -> str:
    """Classify a custom property name into a color category."""
    name_lower = name.lower()
    if any(k in name_lower for k in ("bg", "background", "surface", "void", "console", "screen")):
        return "Background Surfaces"
    if any(k in name_lower for k in ("text", "foreground", "heading", "body", "muted")):
        return "Text & Content"
    if any(k in name_lower for k in ("accent", "brand", "primary", "cta", "phosphor")):
        return "Brand & Accent"
    if any(k in name_lower for k in ("status", "success", "error", "warning", "danger", "ok", "critical", "degraded")):
        return "Status"
    if any(k in name_lower for k in ("border", "divider", "separator", "line", "grid", "wire")):
        return "Border & Divider"
    return "Other"


def extract_tokens(css_files: list[Path]) -> dict:
    """Extract design tokens from CSS files."""
    tokens = {
        "colors": defaultdict(list),  # category -> [(name, value, source)]
        "fonts": [],  # [(name_or_role, value)]
        "font_sizes": [],  # [(context, value)]
        "shadows": [],  # [value]
        "radii": [],  # [value]
        "breakpoints": set(),  # {px_value}
        "spacing": [],  # [value]
        "custom_props": defaultdict(list),  # category -> [(name, value)]
    }

    seen_colors = set()
    seen_fonts = set()

    for css_file in css_files:
        try:
            content = css_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        # Extract from @theme blocks (Tailwind CSS 4)
        for theme_match in THEME_BLOCK_RE.finditer(content):
            block = theme_match.group(1)
            for prop_match in CUSTOM_PROP_RE.finditer(block):
                name, value = prop_match.group(1), prop_match.group(2).strip()
                if "font" in name.lower():
                    if value not in seen_fonts:
                        seen_fonts.add(value)
                        tokens["fonts"].append((name, value))
                elif any(c_re.search(value) for c_re in [COLOR_HEX_RE, COLOR_RGB_RE, COLOR_HSL_RE, COLOR_OKLCH_RE]):
                    key = (name, value)
                    if key not in seen_colors:
                        seen_colors.add(key)
                        category = classify_color_prop(name)
                        tokens["colors"][category].append((name, value, css_file.name))

        # Extract from :root blocks
        root_blocks = re.findall(r":root\s*\{([^}]+)\}", content, re.DOTALL)
        for block in root_blocks:
            for prop_match in CUSTOM_PROP_RE.finditer(block):
                name, value = prop_match.group(1), prop_match.group(2).strip()
                if "font" in name.lower():
                    if value not in seen_fonts:
                        seen_fonts.add(value)
                        tokens["fonts"].append((name, value))
                elif any(c_re.search(value) for c_re in [COLOR_HEX_RE, COLOR_RGB_RE, COLOR_HSL_RE, COLOR_OKLCH_RE]):
                    key = (name, value)
                    if key not in seen_colors:
                        seen_colors.add(key)
                        category = classify_color_prop(name)
                        tokens["colors"][category].append((name, value, css_file.name))

        # Standalone font-family declarations
        for match in FONT_FAMILY_RE.finditer(content):
            value = match.group(1).strip().rstrip(",")
            if value not in seen_fonts and "var(" not in value:
                seen_fonts.add(value)
                tokens["fonts"].append(("font-family", value))

        # Font sizes
        for match in FONT_SIZE_RE.finditer(content):
            tokens["font_sizes"].append(match.group(1).strip())

        # Shadows
        for match in BOX_SHADOW_RE.finditer(content):
            val = match.group(1).strip()
            if val not in ("none", "inherit") and val not in tokens["shadows"]:
                tokens["shadows"].append(val)

        # Border radii
        for match in BORDER_RADIUS_RE.finditer(content):
            val = match.group(1).strip()
            if val not in ("0", "inherit") and val not in tokens["radii"]:
                tokens["radii"].append(val)

        # Breakpoints
        for match in BREAKPOINT_RE.finditer(content):
            tokens["breakpoints"].add(int(match.group(1)))

    return tokens


# ── Markdown generation ────────────────────────────────────────────────────

def format_prop_name(name: str) -> str:
    """Convert CSS custom property name to a readable title."""
    return name.replace("-", " ").replace("color ", "").title()


def generate_design_md(project_path: Path, tokens: dict) -> str:
    """Generate DESIGN.md content from extracted tokens."""
    project_name = project_path.resolve().name
    lines = [f"# Design System — {project_name}", ""]

    # Section 1: Visual Theme & Atmosphere
    lines.extend([
        "## 1. Visual Theme & Atmosphere",
        "",
        "<!-- TODO: Describe the overall mood, design philosophy, and visual density. -->",
        "<!-- What does this interface feel like? What is the native medium? -->",
        "<!-- Name the conceptual direction (e.g., 'PHOSPHOR VIGIL command center', -->",
        "<!-- 'warm editorial', 'dark precision engineering'). -->",
        "",
        "**Key Characteristics:**",
    ])

    # Auto-detect characteristics
    all_color_values = [v for cat_colors in tokens["colors"].values() for _, v, _ in cat_colors]
    dark_bg = any(v.startswith("#0") or v.startswith("#1") for v in all_color_values if v.startswith("#"))
    if dark_bg:
        lines.append("- Dark-mode-native design")
    if tokens["fonts"]:
        font_names = [v.split(",")[0].strip().strip("'\"") for _, v in tokens["fonts"] if "var(" not in v]
        if font_names:
            lines.append(f"- Typography: {', '.join(dict.fromkeys(font_names))}")
    color_count = sum(len(v) for v in tokens["colors"].values())
    lines.append(f"- {color_count} design tokens extracted from CSS")
    lines.append("")

    # Section 2: Color Palette & Roles
    lines.extend(["## 2. Color Palette & Roles", ""])
    if tokens["colors"]:
        # Preferred category order
        category_order = ["Background Surfaces", "Text & Content", "Brand & Accent", "Status", "Border & Divider", "Other"]
        for category in category_order:
            colors = tokens["colors"].get(category, [])
            if not colors:
                continue
            lines.append(f"### {category}")
            for name, value, source in colors:
                readable = format_prop_name(name)
                lines.append(f"- **{readable}** (`{value}`): `--{name}` — <!-- role description -->")
            lines.append("")
    else:
        lines.extend(["<!-- No color tokens found. Add colors manually. -->", ""])

    # Section 3: Typography Rules
    lines.extend(["## 3. Typography Rules", ""])
    if tokens["fonts"]:
        lines.append("### Font Family")
        for name, value in tokens["fonts"]:
            role = format_prop_name(name)
            lines.append(f"- **{role}**: `{value}`")
        lines.append("")

    lines.extend([
        "### Hierarchy",
        "",
        "| Role | Font | Size | Weight | Line Height | Letter Spacing | Notes |",
        "|------|------|------|--------|-------------|----------------|-------|",
        "| Display | <!-- font --> | <!-- size --> | <!-- weight --> | <!-- lh --> | <!-- ls --> | Hero headlines |",
        "| Heading 1 | <!-- font --> | <!-- size --> | <!-- weight --> | <!-- lh --> | <!-- ls --> | Section titles |",
        "| Body | <!-- font --> | <!-- size --> | <!-- weight --> | <!-- lh --> | <!-- ls --> | Standard reading |",
        "| Caption | <!-- font --> | <!-- size --> | <!-- weight --> | <!-- lh --> | <!-- ls --> | Metadata |",
        "| Mono | <!-- font --> | <!-- size --> | <!-- weight --> | <!-- lh --> | <!-- ls --> | Code, data |",
        "",
    ])

    if tokens["font_sizes"]:
        def _size_sort_key(s):
            try:
                return float(s.replace("rem", "").replace("px", "").replace("em", ""))
            except ValueError:
                return float("inf")

        unique_sizes = sorted(set(tokens["font_sizes"]), key=_size_sort_key)
        lines.extend([
            "**Detected font sizes**: " + ", ".join(f"`{s}`" for s in unique_sizes[:15]),
            "",
        ])

    # Section 4: Component Stylings
    lines.extend([
        "## 4. Component Stylings",
        "",
        "### Buttons",
        "",
        "**Primary Button**",
        "- Background: <!-- color -->",
        "- Text: <!-- color -->",
        "- Padding: <!-- value -->",
        "- Radius: <!-- value -->",
        "- Hover: <!-- treatment -->",
        "- Use: Primary CTAs",
        "",
        "**Secondary Button**",
        "- Background: <!-- color -->",
        "- Text: <!-- color -->",
        "- Border: <!-- value -->",
        "- Use: Secondary actions",
        "",
        "### Cards & Containers",
        "- Background: <!-- color -->",
        "- Border: <!-- value -->",
        "- Radius: <!-- value -->",
        "- Shadow: <!-- value -->",
        "",
        "### Inputs & Forms",
        "- Background: <!-- color -->",
        "- Text: <!-- color -->",
        "- Border: <!-- value -->",
        "- Focus: <!-- treatment -->",
        "",
    ])

    # Section 5: Layout Principles
    lines.extend([
        "## 5. Layout Principles",
        "",
        "### Spacing System",
        "- Base unit: <!-- e.g., 8px -->",
        "- Scale: <!-- e.g., 4px, 8px, 12px, 16px, 24px, 32px, 48px, 64px -->",
        "",
        "### Grid & Container",
        "- Max content width: <!-- value -->",
        "",
        "### Whitespace Philosophy",
        "<!-- How does this design use space? What's the rhythm? -->",
        "",
        "### Border Radius Scale",
    ])

    if tokens["radii"]:
        unique_radii = sorted(set(tokens["radii"]))
        for r in unique_radii:
            lines.append(f"- `{r}`: <!-- use -->")
    else:
        lines.extend([
            "- Micro (2px): <!-- use -->",
            "- Standard (6px): <!-- use -->",
            "- Card (8px): <!-- use -->",
            "- Full Pill (9999px): <!-- use -->",
        ])
    lines.append("")

    # Section 6: Depth & Elevation
    lines.extend([
        "## 6. Depth & Elevation",
        "",
        "| Level | Treatment | Use |",
        "|-------|-----------|-----|",
    ])

    if tokens["shadows"]:
        for i, shadow in enumerate(tokens["shadows"][:6]):
            truncated = shadow[:80] + "..." if len(shadow) > 80 else shadow
            lines.append(f"| Level {i} | `{truncated}` | <!-- use --> |")
    else:
        lines.extend([
            "| Flat (0) | No shadow | Page background |",
            "| Surface (1) | <!-- shadow --> | Cards, inputs |",
            "| Elevated (2) | <!-- shadow --> | Dropdowns, popovers |",
            "| Dialog (3) | <!-- shadow --> | Modals |",
        ])
    lines.append("")

    # Section 7: Do's and Don'ts
    lines.extend([
        "## 7. Do's and Don'ts",
        "",
        "### Do",
        "- <!-- Design guardrails specific to this system -->",
        "- <!-- What makes this design distinctive? -->",
        "",
        "### Don't",
        "- <!-- Common mistakes to avoid -->",
        "- <!-- What breaks the visual language? -->",
        "",
    ])

    # Section 8: Responsive Behavior
    lines.extend([
        "## 8. Responsive Behavior",
        "",
        "### Breakpoints",
        "| Name | Width | Key Changes |",
        "|------|-------|-------------|",
    ])

    if tokens["breakpoints"]:
        sorted_bp = sorted(tokens["breakpoints"])
        bp_names = ["Mobile", "Tablet", "Desktop Small", "Desktop", "Large Desktop"]
        for i, bp in enumerate(sorted_bp[:5]):
            name = bp_names[i] if i < len(bp_names) else f"Breakpoint {i + 1}"
            lines.append(f"| {name} | {bp}px | <!-- changes --> |")
    else:
        lines.extend([
            "| Mobile | <640px | Single column |",
            "| Tablet | 640-1024px | Two-column grids |",
            "| Desktop | >1024px | Full layout |",
        ])

    lines.extend([
        "",
        "### Touch Targets",
        "- Minimum touch target: 44x44px",
        "",
        "### Collapsing Strategy",
        "- <!-- How layouts adapt from desktop to mobile -->",
        "",
    ])

    # Section 9: Agent Prompt Guide
    lines.extend([
        "## 9. Agent Prompt Guide",
        "",
        "### Quick Color Reference",
    ])

    # Pull the most important colors for quick reference
    quick_ref_map = {
        "Primary CTA": None,
        "Page Background": None,
        "Surface": None,
        "Heading text": None,
        "Body text": None,
        "Muted text": None,
        "Accent": None,
        "Border": None,
    }

    for category, colors in tokens["colors"].items():
        for name, value, _ in colors:
            name_lower = name.lower()
            if "primary" in name_lower and "text" not in name_lower and quick_ref_map["Primary CTA"] is None:
                quick_ref_map["Primary CTA"] = value
            if any(k in name_lower for k in ("void", "background", "bg")) and quick_ref_map["Page Background"] is None:
                quick_ref_map["Page Background"] = value
            if any(k in name_lower for k in ("surface", "screen", "console")) and quick_ref_map["Surface"] is None:
                quick_ref_map["Surface"] = value
            if "text-primary" in name_lower and quick_ref_map["Heading text"] is None:
                quick_ref_map["Heading text"] = value
            if any(k in name_lower for k in ("text-body", "text-secondary")) and quick_ref_map["Body text"] is None:
                quick_ref_map["Body text"] = value
            if "muted" in name_lower and quick_ref_map["Muted text"] is None:
                quick_ref_map["Muted text"] = value
            if any(k in name_lower for k in ("accent", "phosphor", "brand")) and quick_ref_map["Accent"] is None:
                quick_ref_map["Accent"] = value
            if any(k in name_lower for k in ("border", "grid", "wire")) and quick_ref_map["Border"] is None:
                quick_ref_map["Border"] = value

    for role, value in quick_ref_map.items():
        if value:
            lines.append(f"- {role}: `{value}`")
        else:
            lines.append(f"- {role}: <!-- value -->")

    lines.append("")
    return "\n".join(lines)


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a DESIGN.md scaffold from project CSS tokens"
    )
    parser.add_argument("project_path", type=Path, help="Path to the project directory")
    parser.add_argument("--output", "-o", type=Path, help="Output file path (default: stdout)")
    args = parser.parse_args()

    project_path = args.project_path.resolve()
    if not project_path.is_dir():
        print(f"Error: {project_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    css_files = find_css_files(project_path)
    if not css_files:
        print(f"No CSS files found in {project_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {len(css_files)} CSS file(s)...", file=sys.stderr)
    for f in css_files[:10]:
        print(f"  {f.relative_to(project_path)}", file=sys.stderr)
    if len(css_files) > 10:
        print(f"  ... and {len(css_files) - 10} more", file=sys.stderr)

    tokens = extract_tokens(css_files)
    content = generate_design_md(project_path, tokens)

    if args.output:
        args.output.write_text(content, encoding="utf-8")
        print(f"Written to {args.output}", file=sys.stderr)
    else:
        print(content)


if __name__ == "__main__":
    main()
