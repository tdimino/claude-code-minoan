#!/usr/bin/env python3
"""Validate a userModel folder for structural correctness and quote accuracy.

Usage:
    uv run scripts/validate_usermodel.py ~/.claude/userModels/mary/
    uv run scripts/validate_usermodel.py ~/.claude/userModels/tom/ --verbose
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    # Inline YAML frontmatter parser (no dependency required)
    yaml = None


def parse_frontmatter(filepath: Path) -> dict | None:
    """Extract YAML frontmatter from a markdown file."""
    try:
        text = filepath.read_text(encoding="utf-8")
    except Exception:
        return None
    if not text.startswith("---"):
        return None
    end = text.find("---", 3)
    if end == -1:
        return None
    raw = text[3:end].strip()
    if yaml:
        try:
            return yaml.safe_load(raw)
        except Exception:
            return None
    # Minimal key-value parser for simple frontmatter
    result = {}
    for line in raw.splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if val.startswith("[") and val.endswith("]"):
                val = [v.strip().strip('"').strip("'") for v in val[1:-1].split(",")]
            elif val == "~":
                val = None
            result[key] = val
    return result


def extract_body(filepath: Path) -> str:
    """Return markdown body (after frontmatter)."""
    text = filepath.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("---", 3)
        if end != -1:
            return text[end + 3:].strip()
    return text


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

VALID_TYPES = {"user-model", "social-dossier", "voice-model", "index", "archive-index"}
VALID_CATEGORIES = {"persona", "twitter-analysis", "substack-analysis", "blog-archive", "pet-model"}
VALID_STATUSES = {"active", "archived", "verified", "draft"}

REQUIRED_FIELDS = {
    "user-model": ["type", "subject", "category", "tags", "created", "updated", "status"],
    "social-dossier": ["type", "subject", "category", "tags", "created", "updated", "corpus", "status"],
    "voice-model": ["type", "subject", "category", "tags", "created", "updated", "status"],
    "index": ["type", "created", "updated", "status"],
    "archive-index": ["type", "subject", "created", "updated", "status"],
}


class Issue:
    def __init__(self, severity: str, filepath: str, message: str):
        self.severity = severity  # CRITICAL, MODERATE, MINOR
        self.filepath = filepath
        self.message = message

    def __str__(self):
        return f"[{self.severity}] {self.filepath}: {self.message}"


def check_frontmatter(filepath: Path, issues: list[Issue]):
    """Validate frontmatter schema."""
    fm = parse_frontmatter(filepath)
    if fm is None:
        issues.append(Issue("CRITICAL", str(filepath.name), "Missing or unparseable YAML frontmatter"))
        return
    ftype = fm.get("type", "")
    if ftype not in VALID_TYPES:
        issues.append(Issue("CRITICAL", str(filepath.name), f"Invalid type: '{ftype}' (expected one of {VALID_TYPES})"))
        return
    required = REQUIRED_FIELDS.get(ftype, [])
    for field in required:
        if field not in fm or fm[field] is None:
            # email and phone can be ~ (null)
            if field in ("email", "phone"):
                continue
            issues.append(Issue("MODERATE", str(filepath.name), f"Missing required field: '{field}' for type '{ftype}'"))
    status = fm.get("status", "")
    if status and status not in VALID_STATUSES:
        issues.append(Issue("MINOR", str(filepath.name), f"Invalid status: '{status}' (expected one of {VALID_STATUSES})"))


def check_index_consistency(folder: Path, issues: list[Issue]):
    """Check that INDEX.md references match actual files on disk."""
    index_path = folder / "INDEX.md"
    if not index_path.exists():
        # Check parent userModels INDEX
        return

    body = extract_body(index_path)

    # Find all .md file references in the INDEX
    md_refs = set(re.findall(r'`([^`]+\.md)`', body))
    # Also find archive/ directory references
    archive_refs = set(re.findall(r'`(archive/[^`]*)`', body))

    for ref in md_refs:
        ref_path = folder / ref
        if not ref_path.exists():
            issues.append(Issue("MODERATE", "INDEX.md", f"References non-existent file: '{ref}'"))

    # Check for orphaned .md files (not in INDEX)
    for f in folder.glob("*.md"):
        if f.name == "INDEX.md":
            continue
        if f.name not in [os.path.basename(r) for r in md_refs] and f.name not in body:
            issues.append(Issue("MINOR", "INDEX.md", f"Orphaned file not referenced in INDEX: '{f.name}'"))


def check_archive_index(folder: Path, issues: list[Issue]):
    """Check archive/INDEX.md matches actual archived files."""
    archive_dir = folder / "archive"
    if not archive_dir.exists():
        return
    archive_index = archive_dir / "INDEX.md"
    if not archive_index.exists():
        issues.append(Issue("MODERATE", "archive/", "Archive directory exists but no INDEX.md"))
        return

    body = extract_body(archive_index)

    # Count actual archive files across subdirectories
    actual_files = []
    for subdir in archive_dir.iterdir():
        if subdir.is_dir():
            for f in subdir.glob("*.md"):
                actual_files.append(f"{subdir.name}/{f.name}")

    # Check each actual file is mentioned in the index
    for af in actual_files:
        filename = os.path.basename(af)
        if filename not in body and af not in body:
            issues.append(Issue("MINOR", "archive/INDEX.md", f"Archive file not in index: '{af}'"))


def check_cross_references(folder: Path, issues: list[Issue]):
    """Check that all file references in dossiers and core model resolve."""
    home = Path.home()
    for mdfile in folder.glob("*.md"):
        if mdfile.name == "INDEX.md":
            continue
        body = extract_body(mdfile)
        # Find backtick-quoted file references
        refs = re.findall(r'`([^`]*\.md)`', body)
        for ref in refs:
            # Skip references that are clearly template/example text
            if "{" in ref or "}" in ref:
                continue
            # Try multiple resolution strategies
            candidates = [
                folder / ref,                          # Relative to folder
                folder.parent / ref,                   # Relative to userModels root
            ]
            # Resolve ~/... and ~/.claude/... paths
            if ref.startswith("~/") or ref.startswith("~/.claude/"):
                candidates.append(home / ref[2:])
            # Strip userModels/{name}/ prefix if present
            folder_name = folder.name
            prefix = f"~/.claude/userModels/{folder_name}/"
            if ref.startswith(prefix):
                candidates.append(folder / ref[len(prefix):])
            # Also try just the basename within the folder
            candidates.append(folder / os.path.basename(ref))

            if not any(c.exists() for c in candidates):
                issues.append(Issue("MINOR", mdfile.name, f"Cross-reference to non-existent file: '{ref}'"))


def _normalize_for_comparison(text: str) -> str:
    """Normalize text for fuzzy quote matching: curly→straight quotes, collapse single/double quotes, strip markdown emphasis."""
    # Curly quotes → straight
    text = text.replace("\u2018", "'").replace("\u2019", "'")  # ' '
    text = text.replace("\u201c", '"').replace("\u201d", '"')  # " "
    # Strip all quotation marks — single and double quotes are interchangeable
    # in dossiers vs archive text, and scrape artifacts may drop adjacent spaces
    text = text.replace('"', "").replace("'", "")
    # Strip stray backslashes (from escaped quotes in markdown)
    text = text.replace("\\", "")
    # Strip markdown bold/italic markers (both * and _ forms)
    text = text.replace("**", "").replace("__", "")
    text = text.replace("*", "").replace("_", "")
    # Strip all whitespace — archive scrapes may lose/add spaces near punctuation
    text = re.sub(r'\s+', '', text)
    return text


def check_calibration_quotes(folder: Path, issues: list[Issue], verbose: bool = False):
    """Spot-check that calibration quotes appear verbatim in the archive."""
    archive_dir = folder / "archive"
    if not archive_dir.exists():
        if verbose:
            print("  [SKIP] No archive/ directory — cannot verify quotes")
        return

    # Load all archive content into memory for substring search
    archive_texts: dict[str, str] = {}
    for subdir in archive_dir.iterdir():
        if subdir.is_dir():
            for f in subdir.glob("*.md"):
                try:
                    raw = f.read_text(encoding="utf-8")
                    archive_texts[str(f.relative_to(folder))] = _normalize_for_comparison(raw)
                except Exception:
                    pass

    if not archive_texts:
        if verbose:
            print("  [SKIP] No archived files found")
        return

    # Extract calibration quotes from dossiers
    for mdfile in folder.glob("*.md"):
        if mdfile.name == "INDEX.md":
            continue
        fm = parse_frontmatter(mdfile)
        if not fm or fm.get("type") not in ("social-dossier", "voice-model"):
            continue

        body = extract_body(mdfile)

        # Find the Calibration Quotes section
        cal_match = re.search(r'##\s*Calibration Quotes', body)
        if not cal_match:
            continue

        # Extract all blockquoted text after the section header
        cal_section = body[cal_match.start():]
        # Stop at the next ## heading
        next_section = re.search(r'\n##\s+[^#]', cal_section[1:])
        if next_section:
            cal_section = cal_section[:next_section.start() + 1]

        # Extract quotes (lines starting with >)
        quotes = []
        current_quote = []
        for line in cal_section.splitlines():
            if line.startswith("> ") and not line.startswith("> —"):
                # Strip the > prefix and leading/trailing quote marks
                qtext = line[2:].strip().strip('"').strip('\u201c').strip('\u201d').strip('"')
                current_quote.append(qtext)
            elif current_quote and (not line.startswith(">") or line.startswith("> —")):
                quotes.append(" ".join(current_quote))
                current_quote = []
        if current_quote:
            quotes.append(" ".join(current_quote))

        checked = 0
        failed = 0
        for quote in quotes:
            if len(quote) < 20:
                continue  # Skip very short fragments
            # Normalize and search for a substantial substring in archive
            search_text = _normalize_for_comparison(quote[:80]).replace("…", "").strip()
            if len(search_text) < 15:
                continue
            found = False
            for _apath, atext in archive_texts.items():
                if search_text in atext:
                    found = True
                    break
            checked += 1
            if not found:
                failed += 1
                preview = quote[:60] + ("..." if len(quote) > 60 else "")
                issues.append(Issue("CRITICAL", mdfile.name, f"Calibration quote not found verbatim in archive: \"{preview}\""))

        if verbose and checked > 0:
            print(f"  [{mdfile.name}] Checked {checked} quotes, {checked - failed} verified, {failed} not found")


def check_content_quality(folder: Path, issues: list[Issue]):
    """Basic content quality checks for dossiers."""
    for mdfile in folder.glob("*.md"):
        if mdfile.name == "INDEX.md":
            continue
        fm = parse_frontmatter(mdfile)
        if not fm or fm.get("type") != "social-dossier":
            continue

        body = extract_body(mdfile)

        # Check for register table
        if "Register" not in body or "Frequency" not in body:
            issues.append(Issue("MINOR", mdfile.name, "Missing voice register table (Register | Frequency)"))

        # Check for worldview markers
        wv_match = re.search(r'##\s*Worldview Markers', body)
        if wv_match:
            wv_section = body[wv_match.start():]
            next_sec = re.search(r'\n##\s+[^#]', wv_section[1:])
            if next_sec:
                wv_section = wv_section[:next_sec.start() + 1]
            # Count ### subsections
            themes = len(re.findall(r'###\s+', wv_section))
            if themes < 5:
                issues.append(Issue("MINOR", mdfile.name, f"Worldview markers has only {themes} themes (minimum 5)"))

        # Check for calibration quotes section (expected in voice-focused dossiers)
        if "Calibration Quotes" not in body:
            # Downgrade to MINOR for taxonomy/network dossiers that aren't voice-focused
            cat = fm.get("category", "") if fm else ""
            has_voice_section = "Voice Analysis" in body or "Writing Registers" in body
            severity = "MODERATE" if has_voice_section else "MINOR"
            issues.append(Issue(severity, mdfile.name, "Missing Calibration Quotes section"))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def validate(folder: Path, verbose: bool = False) -> list[Issue]:
    issues: list[Issue] = []

    if not folder.exists():
        issues.append(Issue("CRITICAL", str(folder), "Folder does not exist"))
        return issues

    if verbose:
        print(f"Validating: {folder}")
        print(f"  Files: {list(f.name for f in folder.glob('*.md'))}")

    # Check all .md files for frontmatter
    md_files = list(folder.glob("*.md"))
    if not md_files:
        issues.append(Issue("CRITICAL", str(folder), "No .md files found"))
        return issues

    for mdfile in md_files:
        check_frontmatter(mdfile, issues)

    # Core model exists?
    model_files = [f for f in md_files if f.name.endswith("Model.md")]
    if not model_files:
        issues.append(Issue("MODERATE", str(folder.name), "No core persona file (*Model.md) found"))

    # INDEX consistency
    check_index_consistency(folder, issues)

    # Archive INDEX
    check_archive_index(folder, issues)

    # Cross-references
    check_cross_references(folder, issues)

    # Calibration quote verification
    check_calibration_quotes(folder, issues, verbose)

    # Content quality
    check_content_quality(folder, issues)

    return issues


def main():
    parser = argparse.ArgumentParser(description="Validate a userModel folder")
    parser.add_argument("folder", help="Path to the userModel folder")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    issues = validate(folder, verbose=args.verbose)

    if not issues:
        print(f"PASS: {folder.name} — no issues found")
        sys.exit(0)

    # Sort by severity
    severity_order = {"CRITICAL": 0, "MODERATE": 1, "MINOR": 2}
    issues.sort(key=lambda i: severity_order.get(i.severity, 3))

    critical = sum(1 for i in issues if i.severity == "CRITICAL")
    moderate = sum(1 for i in issues if i.severity == "MODERATE")
    minor = sum(1 for i in issues if i.severity == "MINOR")

    print(f"\n{'=' * 60}")
    print(f"RESULTS: {folder.name} — {len(issues)} issues ({critical} critical, {moderate} moderate, {minor} minor)")
    print(f"{'=' * 60}\n")

    for issue in issues:
        print(f"  {issue}")

    print()
    if critical > 0:
        print("FAIL: Critical issues must be resolved.")
        sys.exit(1)
    else:
        print("WARN: Non-critical issues found. Review recommended.")
        sys.exit(0)


if __name__ == "__main__":
    main()
