#!/usr/bin/env python3
"""External skill freshness validation via Exa search + Firecrawl scraping."""

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# Tool paths
EXA_SCRIPT = Path.home() / ".claude/skills/exa-search/scripts/exa_search.py"
FIRECRAWL_CMD = "firecrawl"
FILTER_SCRIPT = Path.home() / ".claude/skills/firecrawl/scripts/filter_web_results.py"

# ANSI colors
RED = "\033[91m"
YELLOW = "\033[93m"
GREEN = "\033[92m"
DIM = "\033[2m"
BOLD = "\033[1m"
CYAN = "\033[96m"
RESET = "\033[0m"

STALENESS_KEYWORDS = re.compile(
    r'\b(breaking\s+change|deprecated|end[- ]of[- ]life|sunset|migration\s+guide|'
    r'major\s+release|major\s+update|new\s+version|renamed|replaced\s+by)\b',
    re.IGNORECASE
)


def load_registry(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    return _parse_registry_yaml(text)


def _parse_registry_yaml(text: str) -> dict:
    """Minimal YAML parser sufficient for freshness-registry.yaml schema."""
    result = {"meta": {}, "skills": {}}
    current_skill = None
    current_upstream = None
    in_upstreams = False

    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue

        if line.startswith("meta:"):
            continue
        if line.startswith("skills:"):
            continue

        indent = len(line) - len(line.lstrip())

        # Meta fields
        if indent == 2 and ":" in stripped and current_skill is None:
            key, _, val = stripped.partition(":")
            key, val = key.strip(), val.strip().strip('"')
            if key in ("generated", "total_skills", "has_upstream", "internal"):
                result["meta"][key] = val
                continue

        # Skill name (indent=2 under skills:)
        if indent == 2 and stripped.endswith(":") and not stripped.startswith("-"):
            current_skill = stripped[:-1].strip()
            result["skills"][current_skill] = {}
            in_upstreams = False
            current_upstream = None
            continue

        if current_skill is None:
            continue

        # Skill properties (indent=4)
        if indent == 4 and ":" in stripped and not stripped.startswith("-"):
            key, _, val = stripped.partition(":")
            key, val = key.strip(), val.strip().strip('"')
            if key == "upstreams":
                in_upstreams = True
                result["skills"][current_skill]["upstreams"] = []
                continue
            if val == "null":
                val = None
            result["skills"][current_skill][key] = val
            in_upstreams = False
            continue

        # Upstream list item (indent=6, starts with -)
        if indent == 6 and stripped.startswith("- ") and in_upstreams:
            current_upstream = {}
            result["skills"][current_skill]["upstreams"].append(current_upstream)
            rest = stripped[2:]
            if ":" in rest:
                key, _, val = rest.partition(":")
                key, val = key.strip(), val.strip().strip('"')
                if val == "null":
                    val = None
                current_upstream[key] = val
            continue

        # Upstream properties (indent=8)
        if indent == 8 and ":" in stripped and current_upstream is not None:
            key, _, val = stripped.partition(":")
            key = key.strip()
            val = val.strip().strip('"')
            if "#" in val:
                val = val[:val.index("#")].strip().strip('"')
            if val == "null":
                val = None
            current_upstream[key] = val
            continue

    return result


def run_exa_search(query: str, *, domains: list[str] | None = None,
                   days_back: int = 90, num_results: int = 5,
                   deep: bool = False) -> dict:
    after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    mode = "--deep" if deep else "--fast"

    cmd = [
        sys.executable, str(EXA_SCRIPT), query,
        mode, "--json", "-n", str(num_results),
        "--after", after_date, "--no-text",
    ]
    if domains:
        cmd.extend(["--domains"] + domains)

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode == 0 and r.stdout.strip():
            return json.loads(r.stdout)
    except (subprocess.TimeoutExpired, json.JSONDecodeError, OSError) as e:
        return {"error": str(e), "results": []}

    return {"results": []}


def run_firecrawl_scrape(url: str) -> str | None:
    cmd = [FIRECRAWL_CMD, "scrape", url, "--only-main-content"]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=45)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    except (subprocess.TimeoutExpired, OSError):
        pass
    return None


def run_filter(text: str, *, sections: list[str] | None = None,
               keywords: list[str] | None = None,
               max_chars: int = 3000) -> str:
    cmd = [sys.executable, str(FILTER_SCRIPT), "--max-chars", str(max_chars), "--compact"]
    if sections:
        cmd.extend(["--sections", ",".join(sections)])
    if keywords:
        cmd.extend(["--keywords", ",".join(keywords)])

    try:
        r = subprocess.run(cmd, input=text, capture_output=True, text=True, timeout=15)
        if r.returncode == 0:
            return r.stdout
    except (subprocess.TimeoutExpired, OSError):
        pass
    return text[:max_chars]


def extract_versions_from_results(exa_results: dict, version_pattern: str | None) -> list[str]:
    if not version_pattern:
        return []
    pat = re.compile(version_pattern)
    found = set()
    for result in exa_results.get("results", []):
        title = result.get("title", "")
        text = result.get("text", "")
        summary = result.get("summary", "")
        combined = f"{title} {text} {summary}"
        found.update(pat.findall(combined))
    return sorted(found)


def has_staleness_signals(exa_results: dict) -> list[str]:
    signals = []
    for result in exa_results.get("results", []):
        title = result.get("title", "")
        text = result.get("text", "")
        summary = result.get("summary", "")
        combined = f"{title} {text} {summary}"
        matches = STALENESS_KEYWORDS.findall(combined)
        signals.extend(matches)
    return list(set(signals))


def should_scrape(exa_results: dict, upstream: dict) -> bool:
    if not upstream.get("url"):
        return False
    if not exa_results.get("results"):
        return True  # Scrape as fallback
    if has_staleness_signals(exa_results):
        return True
    current = upstream.get("current_version")
    if current and upstream.get("version_pattern"):
        found = extract_versions_from_results(exa_results, upstream["version_pattern"])
        if found and any(v != current for v in found):
            return True
    return False


def compare_versions(current: str | None, found: list[str]) -> str:
    """Returns 'current', 'stale', or 'unknown'."""
    if not current or not found:
        return "unknown"

    def parse_ver(v: str) -> tuple[int, ...]:
        nums = re.findall(r'\d+', v)
        return tuple(int(n) for n in nums)

    try:
        cur = parse_ver(current)
        if not cur:
            return "unknown"

        # Filter found versions to same major series (same first number)
        # to avoid false positives from unrelated version strings in results
        same_series = []
        for v in found:
            pv = parse_ver(v)
            if pv and pv[0] == cur[0]:
                same_series.append(pv)

        if not same_series:
            return "unknown"

        best = max(same_series)
        if best == cur:
            return "current"
        if best > cur:
            return "stale"
        return "current"
    except (ValueError, IndexError):
        return "unknown"


def assess_staleness(skill_name: str, upstream: dict,
                     exa_results: dict, scraped_text: str | None) -> dict:
    current_version = upstream.get("current_version")
    version_pattern = upstream.get("version_pattern")
    recent_titles = [r.get("title", "")[:80] for r in exa_results.get("results", [])[:5]]
    signals = has_staleness_signals(exa_results)

    found_versions = extract_versions_from_results(exa_results, version_pattern)
    if scraped_text and version_pattern:
        pat = re.compile(version_pattern)
        found_versions.extend(pat.findall(scraped_text))
        found_versions = sorted(set(found_versions))

    result = {
        "upstream_name": upstream.get("name", "unknown"),
        "upstream_url": upstream.get("url"),
        "recent_titles": recent_titles,
        "found_versions": found_versions,
        "skill_version": current_version,
        "staleness_signals": signals,
    }

    if version_pattern and current_version:
        cmp = compare_versions(current_version, found_versions)
        if cmp == "stale":
            result["status"] = "STALE"
            result["reason"] = f"Newer version available: {current_version} → {found_versions[-1] if found_versions else '?'}"
            result["recommendation"] = "Update version references and check for new features."
        elif cmp == "current":
            result["status"] = "CURRENT"
            result["reason"] = f"Version {current_version} is up to date."
            result["recommendation"] = "No action needed."
        else:
            if signals:
                result["status"] = "MAJOR_UPDATE"
                result["reason"] = f"Staleness signals: {', '.join(signals)}"
                result["recommendation"] = "Investigate flagged changes."
            else:
                result["status"] = "UNKNOWN"
                result["reason"] = "Could not extract version from search results."
                result["recommendation"] = "Manual check recommended."
    elif not version_pattern:
        # API-type: no discrete version, check signals
        if signals:
            result["status"] = "MAJOR_UPDATE"
            result["reason"] = f"Staleness signals: {', '.join(signals)}"
            result["recommendation"] = "Investigate flagged changes."
        elif exa_results.get("results"):
            result["status"] = "CURRENT"
            result["reason"] = "Recent results found, no breaking change signals."
            result["recommendation"] = "Likely current—verify if needed."
        else:
            result["status"] = "UNKNOWN"
            result["reason"] = "No search results found."
            result["recommendation"] = "Manual check recommended."
    else:
        result["status"] = "UNKNOWN"
        result["reason"] = "No current_version set in registry."
        result["recommendation"] = "Add current_version to registry for automated checking."

    return result


def check_skill(skill_name: str, skill_config: dict, skills_dir: Path, *,
                deep: bool = False, batch_delay: float = 1.0,
                skip_scrape: bool = False, verbose: bool = False) -> dict:
    category = skill_config.get("category", "unknown")
    upstreams = skill_config.get("upstreams", [])
    skill_dir = skills_dir / category / skill_name

    if not skill_dir.exists():
        return {
            "skill": skill_name,
            "category": category,
            "status": "ERROR",
            "reason": f"Skill directory not found: {skill_dir}",
            "assessments": [],
        }

    assessments = []
    worst_status = "CURRENT"
    status_rank = {"CURRENT": 0, "UNKNOWN": 1, "STALE": 2, "MAJOR_UPDATE": 3, "ERROR": 4}

    for upstream in upstreams:
        query = upstream.get("search_query")
        if not query:
            continue

        if verbose:
            print(f"  {DIM}Searching: {query}{RESET}", file=sys.stderr)

        domains = upstream.get("check_domains")
        if isinstance(domains, str):
            domains = [domains]

        exa_results = run_exa_search(query, domains=domains, deep=deep)
        time.sleep(batch_delay)

        scraped_text = None
        if not skip_scrape and should_scrape(exa_results, upstream):
            url = upstream.get("url")
            if url and verbose:
                print(f"  {DIM}Scraping: {url}{RESET}", file=sys.stderr)
            if url:
                raw = run_firecrawl_scrape(url)
                if raw:
                    scraped_text = run_filter(
                        raw,
                        sections=["Changelog", "Release", "Version", "What's New", "Breaking"],
                        keywords=["release", "version", "breaking", "deprecated", "new"],
                        max_chars=3000
                    )
                time.sleep(batch_delay)

        assessment = assess_staleness(skill_name, upstream, exa_results, scraped_text)
        assessments.append(assessment)

        if status_rank.get(assessment["status"], 0) > status_rank.get(worst_status, 0):
            worst_status = assessment["status"]

    return {
        "skill": skill_name,
        "category": category,
        "status": worst_status,
        "assessments": assessments,
    }


def render_summary(results: list[dict]) -> None:
    status_colors = {
        "CURRENT": GREEN,
        "STALE": YELLOW,
        "MAJOR_UPDATE": RED,
        "UNKNOWN": DIM,
        "ERROR": RED,
    }

    results.sort(key=lambda r: {"MAJOR_UPDATE": 0, "STALE": 1, "ERROR": 2,
                                 "UNKNOWN": 3, "CURRENT": 4}.get(r["status"], 5))

    name_w = max((len(r["skill"][:24]) for r in results), default=20)
    cat_w = max((len(r["category"][:18]) for r in results), default=15)
    name_w = max(name_w, 5)
    cat_w = max(cat_w, 8)

    header = f"{'Skill':<{name_w}}  {'Category':<{cat_w}}  {'Status':<14}  {'Version':<20}  {'Recommendation'}"
    print(f"\n{BOLD}{header}{RESET}")
    print("─" * min(len(header) + 20, 120))

    for r in results:
        name = r["skill"][:name_w]
        cat = r["category"][:cat_w]
        color = status_colors.get(r["status"], RESET)
        status = f"{color}{r['status']:<14}{RESET}"

        version_str = ""
        rec_str = ""
        if r["assessments"]:
            a = r["assessments"][0]
            sv = a.get("skill_version", "")
            fv = a.get("found_versions", [])
            if sv and fv:
                version_str = f"{sv} → {fv[-1]}"
            elif sv:
                version_str = sv
            elif fv:
                version_str = f"? → {fv[-1]}"
            rec_str = a.get("recommendation", "")[:40]

        print(f"{name:<{name_w}}  {cat:<{cat_w}}  {status}  {version_str:<20}  {rec_str}")

    # Summary counts
    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1

    print(f"\n{BOLD}Checked:{RESET} {len(results)}  ", end="")
    for status in ["MAJOR_UPDATE", "STALE", "UNKNOWN", "CURRENT"]:
        if status in counts:
            color = status_colors.get(status, RESET)
            print(f"{color}{status}: {counts[status]}{RESET}  ", end="")
    print()


def main():
    parser = argparse.ArgumentParser(description="Skill freshness check via Exa + Firecrawl")
    parser.add_argument("--registry", type=Path,
                        default=Path(__file__).parent / "freshness-registry.yaml")
    parser.add_argument("--skills-dir", type=Path,
                        default=Path.home() / "Desktop/claude-code-minoan/skills")
    parser.add_argument("--skill", help="Check a single skill")
    parser.add_argument("--category", help="Check one category")
    parser.add_argument("--dry-run", action="store_true", help="Show plan without API calls")
    parser.add_argument("--deep", action="store_true", help="Use Exa --deep (slower, thorough)")
    parser.add_argument("--batch-delay", type=float, default=1.0, help="Seconds between API calls")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    parser.add_argument("--skip-scrape", action="store_true", help="Exa only, no Firecrawl")
    parser.add_argument("--max-skills", type=int, help="Cap number of skills to check")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show progress")
    args = parser.parse_args()

    if not args.registry.exists():
        print(f"Registry not found: {args.registry}", file=sys.stderr)
        print("Generate one: python3 skill-audit.py --generate-registry-skeleton > freshness-registry.yaml",
              file=sys.stderr)
        sys.exit(1)

    if not EXA_SCRIPT.exists():
        print(f"Exa search script not found: {EXA_SCRIPT}", file=sys.stderr)
        sys.exit(1)

    registry = load_registry(args.registry)
    skills = registry.get("skills", {})

    # Filter to upstream-only skills
    to_check = {name: cfg for name, cfg in skills.items()
                if cfg.get("type") == "has_upstream" and cfg.get("upstreams")}

    if args.skill:
        if args.skill in to_check:
            to_check = {args.skill: to_check[args.skill]}
        elif args.skill in skills:
            print(f"Skill '{args.skill}' is internal (no upstream to check).", file=sys.stderr)
            sys.exit(0)
        else:
            print(f"Skill '{args.skill}' not found in registry.", file=sys.stderr)
            sys.exit(1)

    if args.category:
        to_check = {n: c for n, c in to_check.items() if c.get("category") == args.category}

    if args.max_skills:
        to_check = dict(list(to_check.items())[:args.max_skills])

    if args.dry_run:
        print(f"\n{BOLD}Dry run — {len(to_check)} skills to check:{RESET}\n")
        for name, cfg in sorted(to_check.items()):
            upstreams = cfg.get("upstreams", [])
            queries = [u.get("search_query", "?") for u in upstreams]
            urls = [u.get("url", "—") for u in upstreams]
            print(f"  {CYAN}{name}{RESET} ({cfg.get('category', '?')})")
            for q, u in zip(queries, urls):
                print(f"    Exa: {q}")
                if u:
                    print(f"    URL: {u}")
        exa_calls = sum(len(c.get("upstreams", [])) for c in to_check.values())
        print(f"\n  Estimated Exa calls: {exa_calls}")
        print(f"  Estimated time: ~{exa_calls * (args.batch_delay + 1):.0f}s with --batch-delay {args.batch_delay}")
        return

    # Run checks
    results = []
    total = len(to_check)
    for i, (name, cfg) in enumerate(sorted(to_check.items()), 1):
        if args.verbose:
            print(f"\n{BOLD}[{i}/{total}] {name}{RESET}", file=sys.stderr)

        result = check_skill(
            name, cfg, args.skills_dir,
            deep=args.deep,
            batch_delay=args.batch_delay,
            skip_scrape=args.skip_scrape,
            verbose=args.verbose,
        )
        results.append(result)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        render_summary(results)


if __name__ == "__main__":
    main()
