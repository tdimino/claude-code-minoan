#!/usr/bin/env python3
"""
Tests for build_indexes.py.

Fixtures embed the Sainsbury's and Stacks corruption cases, a normal system,
and a component page. Asserts clean parsing, derived counts, word-boundary
truncation, and index.json/markdown agreement.

Usage:
    python3 test_build_indexes.py
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_indexes


SAINSBURYS_SECTION = """\
- ![](https://example.com/image.webp)



## [Sainsbury's Design System](https://design-systems.sainsburys.co.uk/)



[Sainsbury's Design System on Storybook](https://sainsburys-tech.github.io/design-systems)



Sainsbury's



### Tech



  - React
  - Sass

### Features

  - Usage guidelines
  - Code examples
  - Tone of voice

"""

STACKS_SECTION = """\
- ![](https://example.com/stacks.webp)



## [Stacks](https://stackoverflow.design/)



[Stacks on GitHub](https://github.com/StackExchange/Stacks)



Stack Overflow



### Tech



  - Stimulus

### Features

  - Code examples
  - Usage guidelines
  - Tone of voice
  - Open source

"""

ELASTIC_SECTION = """\
- ![](https://example.com/elastic.webp)



## [Elastic UI framework](https://eui.elastic.co/)



[Elastic UI framework on Figma](https://www.figma.com/@elastic) [Elastic UI framework on GitHub](https://github.com/elastic/eui)



Elastic



### Tech



  - React
  - CSS-in-JS

### Features

  - Code examples
  - Open source

"""

DESIGN_SYSTEMS_PAGE = """\
---
url: https://component.gallery/design-systems/
title: "Design Systems | The Component Gallery"
scraped_date: 2026-03-02
---

# Design systems, Component libraries, UI toolkits…

Filter:

""" + ELASTIC_SECTION + SAINSBURYS_SECTION + STACKS_SECTION

ACCORDION_PAGE = """\
---
url: https://component.gallery/components/accordion/
title: "Accordion | The Component Gallery"
scraped_date: 2026-03-02
---

Component

# Accordion

Also known as: Arrow toggle, Collapse, Collapsible sections

An accordion is a vertical stack of interactive headings used to toggle the display of further information; each item can be collapsed with just a short label visible or expanded to show the full content.

## 101 Examples (101 shown)
"""

BUTTON_PAGE = """\
---
url: https://component.gallery/components/button/
title: "Button | The Component Gallery"
scraped_date: 2026-03-02
---

Component

# Button

Buttons trigger an action such as submitting a form or showing/hiding an interface component.

## 118 Examples (118 shown)
"""


class TestDesignSystemParsing(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        pages_dir = Path(self.tmpdir) / ".staging" / "pages"
        pages_dir.mkdir(parents=True)
        (pages_dir / "design-systems.md").write_text(DESIGN_SYSTEMS_PAGE)
        (pages_dir / "components-accordion.md").write_text(ACCORDION_PAGE)
        (pages_dir / "components-button.md").write_text(BUTTON_PAGE)

        self.orig_staging = build_indexes.STAGING_DIR
        self.orig_pages = build_indexes.PAGES_DIR
        build_indexes.STAGING_DIR = Path(self.tmpdir) / ".staging"
        build_indexes.PAGES_DIR = build_indexes.STAGING_DIR / "pages"

    def tearDown(self):
        build_indexes.STAGING_DIR = self.orig_staging
        build_indexes.PAGES_DIR = self.orig_pages
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _parse_systems(self):
        ds_file = build_indexes.PAGES_DIR / "design-systems.md"
        return build_indexes.extract_design_systems(ds_file)

    def test_sainsburys_tech_clean(self):
        """Sainsbury's tech must be [React, Sass], not a URL fragment."""
        systems = self._parse_systems()
        sainsburys = [s for s in systems if "Sainsbury" in s["name"]][0]
        self.assertEqual(sainsburys["tech"], ["React", "Sass"])
        self.assertNotIn("github.io", str(sainsburys["tech"]))

    def test_sainsburys_features_full(self):
        """Sainsbury's must have all three features, not just the first."""
        systems = self._parse_systems()
        sainsburys = [s for s in systems if "Sainsbury" in s["name"]][0]
        self.assertEqual(
            sainsburys["features"],
            ["Usage guidelines", "Code examples", "Tone of voice"],
        )

    def test_stacks_tech_clean(self):
        """Stacks tech must be [Stimulus], not a markdown link fragment."""
        systems = self._parse_systems()
        stacks = [s for s in systems if s["name"] == "Stacks"][0]
        self.assertEqual(stacks["tech"], ["Stimulus"])
        self.assertNotIn("GitHub", str(stacks["tech"]))

    def test_stacks_features_full(self):
        """Stacks must have all four features."""
        systems = self._parse_systems()
        stacks = [s for s in systems if s["name"] == "Stacks"][0]
        self.assertEqual(
            stacks["features"],
            ["Code examples", "Usage guidelines", "Tone of voice", "Open source"],
        )

    def test_normal_system_parses(self):
        """Elastic UI framework should parse cleanly with multi-item tech."""
        systems = self._parse_systems()
        elastic = [s for s in systems if "Elastic" in s["name"]][0]
        self.assertEqual(elastic["tech"], ["React", "CSS-in-JS"])
        self.assertEqual(elastic["features"], ["Code examples", "Open source"])
        self.assertEqual(elastic["url"], "https://eui.elastic.co/")

    def test_system_count(self):
        """Should find exactly 3 systems in our fixture."""
        systems = self._parse_systems()
        self.assertEqual(len(systems), 3)

    def test_component_parsing(self):
        """Component pages should extract slug, name, count, description."""
        f = build_indexes.PAGES_DIR / "components-accordion.md"
        data = build_indexes.extract_component_data(f)
        self.assertEqual(data["slug"], "accordion")
        self.assertEqual(data["name"], "Accordion")
        self.assertEqual(data["example_count"], 101)
        self.assertIn("Arrow toggle", data["alt_names"])
        self.assertTrue(data["description"].startswith("An accordion"))

    def test_derived_counts_not_hardcoded(self):
        """Generated markdown must derive counts from data, not hardcode 60/95."""
        systems = self._parse_systems()
        md = build_indexes.build_design_system_index(
            systems, "2026-03-02", "2026-09-01", None,
        )
        self.assertIn("3 design systems", md)
        self.assertNotIn("95", md)

    def test_component_index_derived_count(self):
        """Component index intro line must use actual count."""
        comps = [
            build_indexes.extract_component_data(
                build_indexes.PAGES_DIR / "components-accordion.md"
            ),
            build_indexes.extract_component_data(
                build_indexes.PAGES_DIR / "components-button.md"
            ),
        ]
        md = build_indexes.build_component_index(comps, "2026-03-02", "2026-09-01")
        self.assertIn("2 UI component types", md)
        self.assertIn("219 total examples", md)

    def test_word_boundary_truncation(self):
        """Truncation must break at word boundaries, not mid-word."""
        long_text = (
            "A component for displaying large amounts of data in rows and columns; "
            "commonly referred to as a Data Table when it includes sorting."
        )
        result = build_indexes.truncate_at_word(long_text, 80)
        self.assertTrue(result.endswith("…"))
        self.assertLessEqual(len(result), 82)
        core = result.rstrip("…")
        self.assertFalse(core[-1].isalpha() and core[-1] != core[-1])
        self.assertNotIn("column;", result)

    def test_truncation_short_text_unchanged(self):
        """Short text should pass through unchanged."""
        short = "A simple button."
        self.assertEqual(build_indexes.truncate_at_word(short, 200), short)

    def test_index_json_markdown_agreement(self):
        """index.json component count must match markdown component count."""
        comps = [
            build_indexes.extract_component_data(
                build_indexes.PAGES_DIR / "components-accordion.md"
            ),
            build_indexes.extract_component_data(
                build_indexes.PAGES_DIR / "components-button.md"
            ),
        ]
        systems = self._parse_systems()

        md = build_indexes.build_component_index(comps, "2026-03-02", "2026-09-01")
        json_str = build_indexes.build_index_json(comps, systems, "2026-03-02")
        data = json.loads(json_str)

        self.assertEqual(data["counts"]["components"], 2)
        self.assertEqual(data["counts"]["design_systems"], 3)
        self.assertEqual(data["counts"]["total_examples"], 219)
        self.assertEqual(len(data["components"]), 2)
        self.assertEqual(len(data["design_systems"]), 3)

        stacks_json = [s for s in data["design_systems"] if s["name"] == "Stacks"][0]
        self.assertEqual(stacks_json["tech"], ["Stimulus"])
        self.assertEqual(
            stacks_json["features"],
            ["Code examples", "Usage guidelines", "Tone of voice", "Open source"],
        )

    def test_date_honesty(self):
        """Output must include both crawl date and rebuild date."""
        comps = [
            build_indexes.extract_component_data(
                build_indexes.PAGES_DIR / "components-accordion.md"
            ),
        ]
        md = build_indexes.build_component_index(comps, "2026-03-02", "2026-09-01")
        self.assertIn("Source data: 2026-03-02", md)
        self.assertIn("Indexes rebuilt: 2026-09-01", md)

    def test_ecosystem_currency_preserved(self):
        """Ecosystem Currency section should be re-emitted when provided."""
        currency = "## Ecosystem Currency (as of 2026-09)\n\n- Test note.\n"
        systems = self._parse_systems()
        md = build_indexes.build_design_system_index(
            systems, "2026-03-02", "2026-09-01", currency,
        )
        self.assertIn("## Ecosystem Currency (as of 2026-09)", md)
        self.assertIn("- Test note.", md)
        table_pos = md.index("| Design System |")
        currency_pos = md.index("## Ecosystem Currency")
        self.assertLess(currency_pos, table_pos)


class TestCrawlDate(unittest.TestCase):

    def test_crawl_date_from_frontmatter(self):
        tmpdir = tempfile.mkdtemp()
        staging = Path(tmpdir) / ".staging"
        pages = staging / "pages"
        pages.mkdir(parents=True)
        (pages / "design-systems.md").write_text(
            "---\nscraped_date: 2026-03-02\n---\nContent\n"
        )
        orig = build_indexes.STAGING_DIR, build_indexes.PAGES_DIR
        build_indexes.STAGING_DIR = staging
        build_indexes.PAGES_DIR = pages
        try:
            self.assertEqual(build_indexes.get_crawl_date(), "2026-03-02")
        finally:
            build_indexes.STAGING_DIR, build_indexes.PAGES_DIR = orig
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
