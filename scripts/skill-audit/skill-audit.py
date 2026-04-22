#!/usr/bin/env python3
"""Local skill inventory and staleness report. Zero external dependencies."""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

SKIP_DIRS = {"_archive", ".venv", "node_modules", "__pycache__", ".git"}
# ANSI colors
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
DIM = "\033[2m"
BOLD = "\033[1m"
RESET = "\033[0m"


def discover_skills(skills_dir: Path) -> list[Path]:
    results = []
    for category_dir in sorted(skills_dir.iterdir()):
        if not category_dir.is_dir() or category_dir.name in SKIP_DIRS:
            continue
        for skill_dir in sorted(category_dir.iterdir()):
            if not skill_dir.is_dir() or skill_dir.name in SKIP_DIRS:
                continue
            if (skill_dir / "SKILL.md").exists():
                results.append(skill_dir)
    return results


def parse_frontmatter(path: Path) -> dict:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return {}

    if not text.startswith("---"):
        return {}

    end = text.find("---", 3)
    if end == -1:
        return {}

    fm_block = text[3:end].strip()
    result = {}

    name_m = re.search(r'^name:\s*(.+)', fm_block, re.MULTILINE)
    if name_m:
        result["name"] = name_m.group(1).strip().strip('"').strip("'")

    desc_m = re.search(r'^description:\s*(.+?)(?=\n\w|\Z)', fm_block, re.MULTILINE | re.DOTALL)
    if desc_m:
        desc = desc_m.group(1).strip().strip('"').strip("'")
        desc = re.sub(r'\s+', ' ', desc)
        result["description"] = desc

    return result


def parse_readme_metadata(readme_path: Path) -> dict:
    result = {"last_updated": None, "reflects": None, "reflects_full": None}
    if not readme_path.exists():
        return result

    try:
        text = readme_path.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return result

    date_patterns = [
        r'\*\*Last updated:\*\*\s*(\d{4}-\d{2}-\d{2})',
        r'>\s*Last updated:\s*(\d{4}-\d{2}-\d{2})',
        r'Last updated:\s*(\d{4}-\d{2}-\d{2})',
    ]
    for pat in date_patterns:
        m = re.search(pat, text)
        if m:
            result["last_updated"] = m.group(1)
            break

    reflects_patterns = [
        r'\*\*Reflects:\*\*\s*(.+?)(?=\n\n|\n\*\*|\n##|\Z)',
        r'>\s*Reflects:\s*(.+?)(?=\n\n|\n>|\Z)',
    ]
    for pat in reflects_patterns:
        m = re.search(pat, text, re.DOTALL)
        if m:
            reflects = re.sub(r'\s+', ' ', m.group(1).strip())
            result["reflects"] = reflects[:200] if len(reflects) > 200 else reflects
            result["reflects_full"] = reflects
            break

    return result


def get_git_last_modified(skill_dir: Path, repo_root: Path) -> str | None:
    try:
        rel = skill_dir.relative_to(repo_root)
        r = subprocess.run(
            ["git", "log", "-1", "--format=%aI", "--", str(rel)],
            capture_output=True, text=True, cwd=str(repo_root), timeout=10
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()[:10]
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def classify_upstream(reflects: str | None, description: str) -> tuple[str, list[str]]:
    refs = []
    text = f"{reflects or ''} {description}"

    urls = re.findall(r'https?://github\.com/[\w.-]+/[\w.-]+', text)
    refs.extend(urls)

    urls2 = re.findall(r'https?://[\w.-]+\.[\w.-]+(?:/[\w./-]*)?', text)
    for u in urls2:
        if u not in refs and "github.com" not in u:
            refs.append(u)

    versions = re.findall(r'(?:v\d+\.\d+(?:\.\d+)?)', text)
    refs.extend(versions)

    api_names = re.findall(r'(\w[\w\s-]{2,30})\s+(?:v\d+\s+)?API', text)
    refs.extend([n.strip() for n in api_names])

    sdk_names = re.findall(r'(\w[\w\s-]{2,30})\s+SDK', text)
    refs.extend([n.strip() for n in sdk_names])

    lib_patterns = re.findall(r'\[([^\]]+)\]\(https?://(?:github\.com|pypi\.org|npmjs\.com)[^\)]+\)', text)
    refs.extend(lib_patterns)

    if refs:
        return ("has_upstream", list(dict.fromkeys(refs)))

    upstream_signals = [
        r'(?:Slack|Telegram|Supabase|Cloudflare|Telnyx|Twilio|Resend|Netlify|Figma)',
        r'(?:Gemini|OpenAI|Anthropic|Ollama|HuggingFace)',
        r'(?:React|Next\.js|Tailwind|shadcn)',
        r'(?:Exa|Firecrawl|Scrapling)',
        r'(?:Codex|GPT-\d)',
    ]
    for pat in upstream_signals:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            refs.append(m.group(0))
            return ("has_upstream", refs)

    return ("internal", [])


def compute_flags(record: dict) -> list[str]:
    flags = []
    if not (record["skill_dir"] / "README.md").exists():
        flags.append("no_readme")
    if record["readme_date"] is None:
        flags.append("no_readme_date")
    if record["reflects"] is None:
        flags.append("no_reflects")

    if record["readme_date"] and record["git_date"]:
        try:
            rd = datetime.strptime(record["readme_date"], "%Y-%m-%d")
            gd = datetime.strptime(record["git_date"], "%Y-%m-%d")
            if gd - rd > timedelta(days=7):
                flags.append("readme_stale")
        except ValueError:
            pass

    return flags


def audit_skill(skill_dir: Path, repo_root: Path) -> dict:
    fm = parse_frontmatter(skill_dir / "SKILL.md")
    readme_meta = parse_readme_metadata(skill_dir / "README.md")
    git_date = get_git_last_modified(skill_dir, repo_root)
    desc = fm.get("description", "")
    classification, upstream_refs = classify_upstream(
        readme_meta.get("reflects_full"), desc
    )

    record = {
        "name": fm.get("name", skill_dir.name),
        "slug": skill_dir.name,
        "category": skill_dir.parent.name,
        "description": desc[:150],
        "readme_date": readme_meta["last_updated"],
        "reflects": readme_meta["reflects"],
        "git_date": git_date,
        "classification": classification,
        "upstream_refs": upstream_refs,
        "skill_dir": skill_dir,
    }
    record["flags"] = compute_flags(record)
    return record


def render_table(records: list[dict], *, flagged_only: bool = False) -> None:
    if flagged_only:
        records = [r for r in records if r["flags"]]

    records.sort(key=lambda r: r.get("git_date") or "0000-00-00")

    name_w = max(len(r["name"][:24]) for r in records) if records else 20
    cat_w = max(len(r["category"][:18]) for r in records) if records else 15
    name_w = max(name_w, 4)
    cat_w = max(cat_w, 8)

    header = (
        f"{'Name':<{name_w}}  {'Category':<{cat_w}}  {'README Date':>11}  "
        f"{'Git Date':>10}  {'Type':<12}  {'Flags'}"
    )
    print(f"\n{BOLD}{header}{RESET}")
    print("─" * len(header))

    for r in records:
        name = r["name"][:name_w]
        cat = r["category"][:cat_w]
        rd = r["readme_date"] or "—"
        gd = r["git_date"] or "—"
        cls = r["classification"][:12]

        flag_strs = []
        for f in r["flags"]:
            if f in ("no_readme", "readme_stale"):
                flag_strs.append(f"{RED}{f}{RESET}")
            elif f == "no_readme_date":
                flag_strs.append(f"{YELLOW}{f}{RESET}")
            elif f == "no_reflects":
                flag_strs.append(f"{DIM}{f}{RESET}")
            else:
                flag_strs.append(f)
        flags = ", ".join(flag_strs) if flag_strs else f"{GREEN}✓{RESET}"

        print(f"{name:<{name_w}}  {cat:<{cat_w}}  {rd:>11}  {gd:>10}  {cls:<12}  {flags}")

    # Summary
    total = len(records)
    flagged = sum(1 for r in records if r["flags"])
    upstream = sum(1 for r in records if r["classification"] == "has_upstream")
    internal = total - upstream
    print(f"\n{BOLD}Total:{RESET} {total}  "
          f"{BOLD}Flagged:{RESET} {RED}{flagged}{RESET}  "
          f"{BOLD}Upstream:{RESET} {upstream}  "
          f"{BOLD}Internal:{RESET} {internal}")


def generate_registry_skeleton(records: list[dict]) -> str:
    lines = [
        "# freshness-registry.yaml",
        "# Generated by skill-audit.py --generate-registry-skeleton",
        f"# Date: {datetime.now().strftime('%Y-%m-%d')}",
        "#",
        "# Hand-curate: verify URLs, write search_query values, mark internal skills.",
        "",
        "meta:",
        f"  generated: \"{datetime.now().strftime('%Y-%m-%d')}\"",
        f"  total_skills: {len(records)}",
        f"  has_upstream: {sum(1 for r in records if r['classification'] == 'has_upstream')}",
        f"  internal: {sum(1 for r in records if r['classification'] == 'internal')}",
        "",
        "skills:",
    ]

    for r in sorted(records, key=lambda x: (x["category"], x["slug"])):
        lines.append(f"  {r['slug']}:")
        lines.append(f"    type: {r['classification']}")
        lines.append(f"    category: {r['category']}")

        if r["classification"] == "has_upstream":
            lines.append("    upstreams:")

            github_urls = [ref for ref in r["upstream_refs"] if "github.com" in ref]
            versions = [ref for ref in r["upstream_refs"] if re.match(r'^v\d+', ref)]
            other_refs = [ref for ref in r["upstream_refs"]
                          if ref not in github_urls and ref not in versions]

            if github_urls:
                for url in github_urls[:2]:
                    repo_name = url.rstrip("/").split("/")[-1]
                    lines.append(f"      - name: \"{repo_name}\"")
                    lines.append(f"        url: \"{url}\"")
                    lines.append(f"        search_query: \"{repo_name} release changelog\"  # CURATE")
                    if versions:
                        lines.append(f"        version_pattern: \"v\\\\d+\\\\.\\\\d+(\\\\.\\\\d+)?\"")
                        lines.append(f"        current_version: \"{versions[0]}\"")
                    else:
                        lines.append("        version_pattern: null")
                        lines.append("        current_version: null")
            elif other_refs:
                ref_name = other_refs[0]
                lines.append(f"      - name: \"{ref_name}\"")
                lines.append("        url: null  # CURATE: add upstream URL")
                lines.append(f"        search_query: \"{ref_name} latest release update\"  # CURATE")
                if versions:
                    lines.append(f"        version_pattern: \"v\\\\d+\\\\.\\\\d+(\\\\.\\\\d+)?\"")
                    lines.append(f"        current_version: \"{versions[0]}\"")
                else:
                    lines.append("        version_pattern: null")
                    lines.append("        current_version: null")
            elif versions:
                lines.append(f"      - name: \"{r['name']}\"")
                lines.append("        url: null  # CURATE: add upstream URL")
                lines.append(f"        search_query: \"{r['name']} latest release\"  # CURATE")
                lines.append(f"        version_pattern: \"v\\\\d+\\\\.\\\\d+(\\\\.\\\\d+)?\"")
                lines.append(f"        current_version: \"{versions[0]}\"")
            else:
                lines.append(f"      - name: \"{r['name']}\"")
                lines.append("        url: null  # CURATE: add upstream URL")
                lines.append(f"        search_query: \"{r['name']} latest update\"  # CURATE")
                lines.append("        version_pattern: null")
                lines.append("        current_version: null")
        else:
            if r.get("reflects"):
                lines.append(f"    # reflects: {r['reflects'][:80]}")

        lines.append("")

    return "\n".join(lines)


def to_json(records: list[dict]) -> str:
    out = []
    for r in records:
        entry = {k: v for k, v in r.items() if k != "skill_dir"}
        entry["skill_path"] = str(r["skill_dir"])
        out.append(entry)
    return json.dumps(out, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Skill inventory and staleness report")
    parser.add_argument("--skills-dir", type=Path,
                        default=Path.home() / "Desktop/claude-code-minoan/skills")
    parser.add_argument("--json", action="store_true", help="Output JSON to stdout")
    parser.add_argument("--category", help="Filter to one category")
    parser.add_argument("--flagged-only", action="store_true", help="Only show flagged skills")
    parser.add_argument("--generate-registry-skeleton", action="store_true",
                        help="Output YAML skeleton for freshness-registry.yaml")
    args = parser.parse_args()

    skills_dir = args.skills_dir.resolve()
    if not skills_dir.exists():
        print(f"Skills directory not found: {skills_dir}", file=sys.stderr)
        sys.exit(1)

    repo_root = skills_dir.parent
    skill_dirs = discover_skills(skills_dir)

    if args.category:
        skill_dirs = [d for d in skill_dirs if d.parent.name == args.category]

    records = []
    for sd in skill_dirs:
        records.append(audit_skill(sd, repo_root))

    if args.generate_registry_skeleton:
        print(generate_registry_skeleton(records))
    elif args.json:
        print(to_json(records))
    else:
        render_table(records, flagged_only=args.flagged_only)


if __name__ == "__main__":
    main()
