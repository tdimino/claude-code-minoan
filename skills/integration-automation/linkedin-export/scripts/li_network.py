#!/usr/bin/env python3
"""
li_network.py — LinkedIn connection network analysis.

Subcommands:
    uv run li_network.py summary
    uv run li_network.py companies [--top 20]
    uv run li_network.py timeline [--by year|month]
    uv run li_network.py roles [--top 20]
    uv run li_network.py search "query"
    uv run li_network.py export [--format csv|json]

Requires: Run li_parse.py first to generate parsed.json
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter
from io import StringIO
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
PARSED_FILE = DATA_DIR / "parsed.json"


def load_data() -> dict:
    """Load parsed LinkedIn data."""
    if not PARSED_FILE.exists():
        print(f"Error: No parsed data found at {PARSED_FILE}", file=sys.stderr)
        print("Run li_parse.py first to parse your LinkedIn export.", file=sys.stderr)
        sys.exit(1)

    with open(PARSED_FILE) as f:
        return json.load(f)


def extract_year_month(date_str: str | None) -> tuple[str, str]:
    """Extract year and year-month from an ISO date string."""
    if not date_str:
        return ("unknown", "unknown")
    # Handle ISO dates: 2024-01-15T00:00:00
    match = re.match(r"(\d{4})-(\d{2})", date_str)
    if match:
        year, month = match.groups()
        return (year, f"{year}-{month}")
    return ("unknown", "unknown")


ROLE_CATEGORIES = {
    "Engineering": ["engineer", "developer", "programmer", "devops", "sre", "swe", "software", "backend", "frontend", "fullstack", "full-stack", "data engineer"],
    "Product": ["product manager", "product owner", "product lead", "pm"],
    "Design": ["designer", "ux", "ui", "creative director", "art director"],
    "Data/ML": ["data scientist", "machine learning", "ml engineer", "ai ", "analyst", "data analyst", "research scientist"],
    "Leadership": ["ceo", "cto", "coo", "cfo", "vp ", "vice president", "director", "head of", "chief"],
    "Management": ["manager", "lead", "supervisor", "team lead"],
    "Marketing": ["marketing", "growth", "brand", "content", "seo", "social media"],
    "Sales": ["sales", "account", "business development", "bd", "revenue"],
    "Operations": ["operations", "ops", "project manager", "program manager", "scrum"],
    "Consulting": ["consultant", "advisor", "freelance", "independent"],
    "Research": ["researcher", "professor", "academic", "postdoc", "phd"],
    "Recruiting": ["recruiter", "talent", "hr", "human resources", "people"],
}


def categorize_role(position: str) -> str:
    """Categorize a job title into a broad role category."""
    pos_lower = position.lower()
    for category, keywords in ROLE_CATEGORIES.items():
        if any(kw in pos_lower for kw in keywords):
            return category
    return "Other"


def cmd_summary(data: dict) -> None:
    """Print high-level network summary."""
    connections = data.get("connections", {})
    messages = data.get("messages", {})
    profile = data.get("profile", {})

    name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()

    print(f"LinkedIn Network Summary")
    if name:
        print(f"  Profile: {name}")
    if profile.get("headline"):
        print(f"  Headline: {profile['headline']}")
    print()

    print(f"  Connections: {connections.get('total', 0)}")
    if connections.get("date_range"):
        print(f"    Earliest: {connections['date_range'][0][:10]}")
        print(f"    Latest:   {connections['date_range'][1][:10]}")

    # Top 5 companies
    companies = connections.get("companies", {})
    if companies:
        top5 = list(companies.items())[:5]
        print(f"\n  Top Companies:")
        for company, count in top5:
            print(f"    {company}: {count}")

    # Role distribution
    contacts = connections.get("contacts", [])
    roles = Counter()
    for c in contacts:
        pos = c.get("position", "")
        if pos:
            roles[categorize_role(pos)] += 1

    if roles:
        print(f"\n  Role Distribution:")
        for role, count in roles.most_common(8):
            bar = "█" * min(count, 40)
            print(f"    {role:<15} {count:>4} {bar}")

    print(f"\n  Messages: {messages.get('total_messages', 0)} in {messages.get('total_conversations', 0)} conversations")
    if messages.get("date_range"):
        print(f"    Earliest: {messages['date_range'][0][:10]}")
        print(f"    Latest:   {messages['date_range'][1][:10]}")

    print(f"\n  Positions: {len(data.get('positions', []))}")
    print(f"  Skills: {len(data.get('skills', []))}")
    print(f"  Endorsements: {len(data.get('endorsements', []))}")
    print(f"  Recommendations: {len(data.get('recommendations', []))}")


def cmd_companies(data: dict, top: int, as_json: bool) -> None:
    """Show company distribution."""
    companies = data.get("connections", {}).get("companies", {})

    if as_json:
        print(json.dumps(dict(list(companies.items())[:top]), indent=2))
        return

    items = list(companies.items())[:top]
    if not items:
        print("No company data found.")
        return

    max_count = items[0][1] if items else 1
    print(f"Top {min(top, len(items))} Companies by Connection Count\n")
    print(f"{'Company':<40} {'Count':>6}  Bar")
    print(f"{'─'*40} {'─'*6}  {'─'*30}")

    for company, count in items:
        bar_len = int((count / max_count) * 30)
        bar = "█" * bar_len
        name = company[:38] + ".." if len(company) > 40 else company
        print(f"{name:<40} {count:>6}  {bar}")


def cmd_timeline(data: dict, by: str, as_json: bool) -> None:
    """Show connection timeline."""
    contacts = data.get("connections", {}).get("contacts", [])

    period_counts: Counter = Counter()
    for c in contacts:
        year, yearmonth = extract_year_month(c.get("connected_on"))
        key = year if by == "year" else yearmonth
        period_counts[key] += 1

    # Sort chronologically
    sorted_periods = sorted(period_counts.items(), key=lambda x: x[0])

    if as_json:
        print(json.dumps(dict(sorted_periods), indent=2))
        return

    if not sorted_periods:
        print("No connection date data found.")
        return

    max_count = max(period_counts.values())
    label = "Year" if by == "year" else "Month"
    print(f"Connections by {label}\n")
    print(f"{label:<12} {'Count':>6}  Bar")
    print(f"{'─'*12} {'─'*6}  {'─'*40}")

    for period, count in sorted_periods:
        if period == "unknown":
            continue
        bar_len = int((count / max_count) * 40)
        bar = "█" * bar_len
        print(f"{period:<12} {count:>6}  {bar}")

    unknowns = period_counts.get("unknown", 0)
    if unknowns:
        print(f"\n{'(no date)':<12} {unknowns:>6}")


def cmd_roles(data: dict, top: int, as_json: bool) -> None:
    """Show role/title distribution."""
    contacts = data.get("connections", {}).get("contacts", [])
    roles = Counter()

    for c in contacts:
        pos = c.get("position", "").strip()
        if pos:
            roles[pos] += 1

    if as_json:
        print(json.dumps(dict(roles.most_common(top)), indent=2))
        return

    items = roles.most_common(top)
    if not items:
        print("No position data found.")
        return

    print(f"Top {min(top, len(items))} Job Titles\n")
    print(f"{'Title':<50} {'Count':>6}")
    print(f"{'─'*50} {'─'*6}")

    for title, count in items:
        name = title[:48] + ".." if len(title) > 50 else title
        print(f"{name:<50} {count:>6}")


def cmd_search(data: dict, query: str, as_json: bool) -> None:
    """Search connections by name, company, or position."""
    contacts = data.get("connections", {}).get("contacts", [])
    query_lower = query.lower()

    results = []
    for c in contacts:
        searchable = " ".join([
            c.get("first_name", ""),
            c.get("last_name", ""),
            c.get("company", ""),
            c.get("position", ""),
            c.get("email", ""),
        ]).lower()

        if query_lower in searchable:
            results.append(c)

    if as_json:
        print(json.dumps(results, indent=2))
        return

    print(f'Search: "{query}" — {len(results)} connections found\n')

    if not results:
        return

    print(f"{'Name':<30} {'Company':<25} {'Position':<30} {'Connected':<12}")
    print(f"{'─'*30} {'─'*25} {'─'*30} {'─'*12}")

    for c in results[:50]:
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
        company = (c.get("company", "") or "")[:23]
        position = (c.get("position", "") or "")[:28]
        date = (c.get("connected_on") or "")[:10]
        name = name[:28] + ".." if len(name) > 30 else name
        print(f"{name:<30} {company:<25} {position:<30} {date:<12}")

    if len(results) > 50:
        print(f"\n... +{len(results) - 50} more")


def cmd_export(data: dict, fmt: str, output: str | None) -> None:
    """Export connections to CSV or JSON."""
    contacts = data.get("connections", {}).get("contacts", [])

    if fmt == "json":
        content = json.dumps(contacts, indent=2)
        ext = ".json"
    else:
        buf = StringIO()
        writer = csv.DictWriter(buf, fieldnames=[
            "first_name", "last_name", "company", "position", "email", "url", "connected_on"
        ])
        writer.writeheader()
        for c in contacts:
            writer.writerow({
                "first_name": c.get("first_name", ""),
                "last_name": c.get("last_name", ""),
                "company": c.get("company", ""),
                "position": c.get("position", ""),
                "email": c.get("email", ""),
                "url": c.get("url", ""),
                "connected_on": (c.get("connected_on") or "")[:10],
            })
        content = buf.getvalue()
        ext = ".csv"

    if output:
        out_path = Path(output)
    else:
        out_path = DATA_DIR / f"connections_export{ext}"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        f.write(content)

    print(f"Exported {len(contacts)} connections to {out_path}")


def main():
    parser = argparse.ArgumentParser(description="LinkedIn connection network analysis")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--data", help=f"Path to parsed.json (default: {PARSED_FILE})")

    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("summary", help="Network summary stats")

    p_companies = subparsers.add_parser("companies", help="Company distribution")
    p_companies.add_argument("--top", type=int, default=20, help="Number of companies (default: 20)")

    p_timeline = subparsers.add_parser("timeline", help="Connection timeline")
    p_timeline.add_argument("--by", choices=["year", "month"], default="year", help="Group by (default: year)")

    p_roles = subparsers.add_parser("roles", help="Role/title distribution")
    p_roles.add_argument("--top", type=int, default=20, help="Number of roles (default: 20)")

    p_search = subparsers.add_parser("search", help="Search connections")
    p_search.add_argument("query", help="Search query (name, company, position)")

    p_export = subparsers.add_parser("export", help="Export connections")
    p_export.add_argument("--format", "-f", choices=["csv", "json"], default="csv", help="Export format (default: csv)")
    p_export.add_argument("--output", "-o", help="Output file path")

    args = parser.parse_args()

    if args.data:
        global PARSED_FILE
        PARSED_FILE = Path(args.data)

    data = load_data()

    if args.command == "summary":
        cmd_summary(data)
    elif args.command == "companies":
        cmd_companies(data, args.top, args.json)
    elif args.command == "timeline":
        cmd_timeline(data, args.by, args.json)
    elif args.command == "roles":
        cmd_roles(data, args.top, args.json)
    elif args.command == "search":
        cmd_search(data, args.query, args.json)
    elif args.command == "export":
        cmd_export(data, args.format, args.output)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  li_network.py summary")
        print("  li_network.py companies --top 10")
        print("  li_network.py timeline --by month")
        print('  li_network.py search "Anthropic"')
        print("  li_network.py export --format csv")


if __name__ == "__main__":
    main()
