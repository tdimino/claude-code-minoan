#!/usr/bin/env python3
"""
li_export.py — Export LinkedIn data to Markdown files.

Subcommands:
    uv run li_export.py messages --output ~/linkedin-archive/messages/
    uv run li_export.py connections --output ~/linkedin-archive/connections.md
    uv run li_export.py all --output ~/linkedin-archive/
    uv run li_export.py rlama --output ~/linkedin-archive/rlama/

Requires: Run li_parse.py first to generate parsed.json
"""

import argparse
import json
import re
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
PARSED_FILE = DATA_DIR / "parsed.json"


def load_data(path: Path | None = None) -> dict:
    """Load parsed LinkedIn data."""
    target = path or PARSED_FILE
    if not target.exists():
        print(f"Error: No parsed data found at {target}", file=sys.stderr)
        print("Run li_parse.py first to parse your LinkedIn export.", file=sys.stderr)
        sys.exit(1)

    with open(target) as f:
        return json.load(f)


def safe_filename(name: str) -> str:
    """Create a safe filename from a string."""
    clean = re.sub(r"[^\w\s-]", "", name.lower())
    clean = re.sub(r"[\s]+", "-", clean.strip())
    return clean[:80] or "untitled"


def export_messages(data: dict, output_dir: Path) -> int:
    """Export messages as Markdown, one file per conversation."""
    output_dir.mkdir(parents=True, exist_ok=True)
    conversations = data.get("messages", {}).get("conversations", [])
    profile = data.get("profile", {})
    my_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()

    count = 0
    for conv in conversations:
        title = conv.get("title") or "Untitled"
        participants = conv.get("participants", [])
        messages = conv.get("messages", [])

        if not messages:
            continue

        # Create filename from participants (excluding self)
        others = [p for p in participants if p.lower() != my_name.lower()] or participants
        filename = safe_filename("-".join(others[:3]))
        filepath = output_dir / f"{filename}.md"

        # Handle duplicate filenames with counter
        if filepath.exists():
            filepath = output_dir / f"{filename}-{conv['id'][:8]}.md"
        suffix = 2
        while filepath.exists():
            filepath = output_dir / f"{filename}-{conv['id'][:8]}-{suffix}.md"
            suffix += 1

        dates = [m.get("date", "") for m in messages if m.get("date")]
        date_range = f"{dates[0][:10]} — {dates[-1][:10]}" if dates else "unknown"

        lines = [
            f"# Conversation with {', '.join(others)}",
            "",
            f"**Messages**: {len(messages)}",
            f"**Date range**: {date_range}",
            f"**Participants**: {', '.join(participants)}",
            "",
            "---",
            "",
        ]

        for msg in messages:
            date = (msg.get("date") or msg.get("date_raw") or "unknown")[:19]
            sender = msg.get("from", "unknown")
            content = msg.get("content", "").strip()
            subject = msg.get("subject", "").strip()

            lines.append(f"### {date} — {sender}")
            if subject:
                lines.append(f"**Subject**: {subject}")
            lines.append("")
            lines.append(content if content else "*[empty message]*")
            lines.append("")
            lines.append("---")
            lines.append("")

        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        count += 1

    return count


def export_connections(data: dict, output_path: Path) -> int:
    """Export connections as a Markdown table."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    contacts = data.get("connections", {}).get("contacts", [])

    lines = [
        "# LinkedIn Connections",
        "",
        f"**Total**: {len(contacts)}",
        "",
        "| Name | Company | Position | Connected On |",
        "|------|---------|----------|-------------|",
    ]

    for c in contacts:
        name = f"{c.get('first_name', '')} {c.get('last_name', '')}".strip()
        company = c.get("company", "") or ""
        position = c.get("position", "") or ""
        date = (c.get("connected_on") or "")[:10]

        # Escape pipes in table cells
        company = company.replace("|", "\\|")
        position = position.replace("|", "\\|")
        name = name.replace("|", "\\|")

        lines.append(f"| {name} | {company} | {position} | {date} |")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))

    return len(contacts)


def export_profile(data: dict, output_path: Path) -> None:
    """Export profile, positions, education as Markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    profile = data.get("profile", {})
    positions = data.get("positions", [])
    education = data.get("education", [])
    skills = data.get("skills", [])
    endorsements = data.get("endorsements", [])
    recommendations = data.get("recommendations", [])
    certifications = data.get("certifications", [])

    name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()

    lines = [
        f"# {name or 'LinkedIn Profile'}",
        "",
    ]

    if profile.get("headline"):
        lines.append(f"**{profile['headline']}**")
        lines.append("")

    if profile.get("summary"):
        lines.append("## About")
        lines.append("")
        lines.append(profile["summary"])
        lines.append("")

    if profile.get("industry"):
        lines.append(f"**Industry**: {profile['industry']}")
    if profile.get("location"):
        lines.append(f"**Location**: {profile['location']}")
    lines.append("")

    if positions:
        lines.append("## Experience")
        lines.append("")
        for p in positions:
            title = p.get("title", "")
            company = p.get("company", "")
            start = (p.get("started_on") or "")[:7]
            end = (p.get("finished_on") or "Present")[:7]
            lines.append(f"### {title} at {company}")
            lines.append(f"*{start} — {end}*")
            if p.get("location"):
                lines.append(f"Location: {p['location']}")
            if p.get("description"):
                lines.append("")
                lines.append(p["description"])
            lines.append("")

    if education:
        lines.append("## Education")
        lines.append("")
        for e in education:
            school = e.get("school", "")
            degree = e.get("degree", "")
            start = (e.get("start_date") or "")[:4]
            end = (e.get("end_date") or "")[:4]
            lines.append(f"### {school}")
            if degree:
                lines.append(f"**{degree}**")
            if start or end:
                lines.append(f"*{start} — {end}*")
            if e.get("activities"):
                lines.append(f"Activities: {e['activities']}")
            lines.append("")

    if skills:
        lines.append("## Skills")
        lines.append("")
        lines.append(", ".join(skills))
        lines.append("")

    if endorsements:
        lines.append("## Endorsements")
        lines.append("")
        lines.append("| Skill | Endorser | Date |")
        lines.append("|-------|----------|------|")
        for e in endorsements:
            endorser = f"{e.get('endorser_first', '')} {e.get('endorser_last', '')}".strip()
            date = (e.get("date") or "")[:10]
            lines.append(f"| {e.get('skill', '')} | {endorser} | {date} |")
        lines.append("")

    if recommendations:
        lines.append("## Recommendations")
        lines.append("")
        for r in recommendations:
            name_r = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
            title = r.get("title", "")
            company = r.get("company", "")
            lines.append(f"### From {name_r}")
            if title or company:
                lines.append(f"*{title}, {company}*")
            lines.append("")
            lines.append(r.get("body", ""))
            lines.append("")

    if certifications:
        lines.append("## Certifications")
        lines.append("")
        for c in certifications:
            lines.append(f"- **{c.get('name', '')}** — {c.get('authority', '')}")
        lines.append("")

    with open(output_path, "w") as f:
        f.write("\n".join(lines))


def export_rlama(data: dict, output_dir: Path) -> int:
    """Export RLAMA-optimized documents with category preambles.

    Following the twitter-rlama-bucket architecture:
    - Category preamble in each file header (survives chunking)
    - --- separators between entries for chunk boundaries
    - Inline metadata for BM25 keyword matching
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    file_count = 0

    profile = data.get("profile", {})
    my_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip()

    # 1. Message conversations grouped alphabetically by first participant
    conversations = data.get("messages", {}).get("conversations", [])
    alpha_groups: dict[str, list] = {}

    for conv in conversations:
        participants = conv.get("participants", [])
        others = [p for p in participants if p.lower() != my_name.lower()]
        if not others:
            others = participants
        first_letter = (others[0][0].upper() if others else "Z") if others else "Z"

        if first_letter <= "F":
            group = "a-f"
        elif first_letter <= "L":
            group = "g-l"
        elif first_letter <= "R":
            group = "m-r"
        else:
            group = "s-z"

        alpha_groups.setdefault(group, []).append((others, conv))

    for group, convs in sorted(alpha_groups.items()):
        lines = [
            f"CATEGORY: LinkedIn Messages — Conversations ({group.upper()})",
            f"OWNER: {my_name}",
            f"CONVERSATIONS: {len(convs)}",
            "",
            "---",
            "",
        ]

        for others, conv in convs:
            messages = conv.get("messages", [])
            if not messages:
                continue

            dates = [m.get("date", "") for m in messages if m.get("date")]
            date_range = f"{dates[0][:10]} to {dates[-1][:10]}" if dates else "unknown"

            lines.append(f"CONVERSATION: {', '.join(others)}")
            lines.append(f"MESSAGES: {len(messages)} | DATES: {date_range}")
            lines.append("")

            for msg in messages[-20:]:  # Last 20 messages per conversation for RLAMA
                date = (msg.get("date") or "")[:19]
                sender = msg.get("from", "unknown")
                content = msg.get("content", "").strip()
                if content:
                    lines.append(f"[{date}] {sender}: {content}")

            lines.append("")
            lines.append("---")
            lines.append("")

        filepath = output_dir / f"messages-conversations-{group}.md"
        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        file_count += 1

    # 2. Connections by company
    contacts = data.get("connections", {}).get("contacts", [])
    company_groups: dict[str, list] = {}
    for c in contacts:
        company = c.get("company", "Unknown") or "Unknown"
        company_groups.setdefault(company, []).append(c)

    lines = [
        f"CATEGORY: LinkedIn Connections — By Company",
        f"OWNER: {my_name}",
        f"TOTAL CONNECTIONS: {len(contacts)}",
        f"TOTAL COMPANIES: {len(company_groups)}",
        "",
        "---",
        "",
    ]

    for company, members in sorted(company_groups.items(), key=lambda x: -len(x[1])):
        lines.append(f"COMPANY: {company} ({len(members)} connections)")
        for m in members:
            name = f"{m.get('first_name', '')} {m.get('last_name', '')}".strip()
            position = m.get("position", "")
            date = (m.get("connected_on") or "")[:10]
            line = f"  - {name}"
            if position:
                line += f" | {position}"
            if date:
                line += f" | Connected {date}"
            lines.append(line)
        lines.append("")
        lines.append("---")
        lines.append("")

    filepath = output_dir / "connections-companies.md"
    with open(filepath, "w") as f:
        f.write("\n".join(lines))
    file_count += 1

    # 3. Connections by year
    year_groups: dict[str, list] = {}
    for c in contacts:
        date = c.get("connected_on", "")
        year = date[:4] if date and len(date) >= 4 else "Unknown"
        year_groups.setdefault(year, []).append(c)

    lines = [
        f"CATEGORY: LinkedIn Connections — By Year",
        f"OWNER: {my_name}",
        f"TOTAL CONNECTIONS: {len(contacts)}",
        "",
        "---",
        "",
    ]

    for year, members in sorted(year_groups.items()):
        lines.append(f"YEAR: {year} ({len(members)} connections)")
        for m in sorted(members, key=lambda x: x.get("connected_on") or ""):
            name = f"{m.get('first_name', '')} {m.get('last_name', '')}".strip()
            company = m.get("company", "")
            date = (m.get("connected_on") or "")[:10]
            line = f"  - {name}"
            if company:
                line += f" | {company}"
            if date:
                line += f" | {date}"
            lines.append(line)
        lines.append("")
        lines.append("---")
        lines.append("")

    filepath = output_dir / "connections-timeline.md"
    with open(filepath, "w") as f:
        f.write("\n".join(lines))
    file_count += 1

    # 4. Profile + positions + education
    positions = data.get("positions", [])
    education_list = data.get("education", [])

    lines = [
        f"CATEGORY: LinkedIn Profile — Resume Data",
        f"OWNER: {my_name}",
        "",
    ]

    if profile.get("headline"):
        lines.append(f"HEADLINE: {profile['headline']}")
    if profile.get("industry"):
        lines.append(f"INDUSTRY: {profile['industry']}")
    if profile.get("location"):
        lines.append(f"LOCATION: {profile['location']}")
    if profile.get("summary"):
        lines.append("")
        lines.append(f"SUMMARY: {profile['summary']}")

    lines.extend(["", "---", ""])

    if positions:
        lines.append("SECTION: Work Experience")
        lines.append("")
        for p in positions:
            start = (p.get("started_on") or "")[:7]
            end = (p.get("finished_on") or "Present")[:7]
            lines.append(f"POSITION: {p.get('title', '')} at {p.get('company', '')}")
            lines.append(f"DATES: {start} to {end}")
            if p.get("location"):
                lines.append(f"LOCATION: {p['location']}")
            if p.get("description"):
                lines.append(p["description"])
            lines.append("")
            lines.append("---")
            lines.append("")

    if education_list:
        lines.append("SECTION: Education")
        lines.append("")
        for e in education_list:
            lines.append(f"SCHOOL: {e.get('school', '')}")
            if e.get("degree"):
                lines.append(f"DEGREE: {e['degree']}")
            lines.append("")
            lines.append("---")
            lines.append("")

    filepath = output_dir / "profile-positions-education.md"
    with open(filepath, "w") as f:
        f.write("\n".join(lines))
    file_count += 1

    # 5. Skills + endorsements
    skills = data.get("skills", [])
    endorsements = data.get("endorsements", [])

    lines = [
        f"CATEGORY: LinkedIn Skills & Endorsements",
        f"OWNER: {my_name}",
        f"SKILLS: {len(skills)}",
        f"ENDORSEMENTS: {len(endorsements)}",
        "",
        "---",
        "",
    ]

    if skills:
        lines.append(f"SKILLS LIST: {', '.join(skills)}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Group endorsements by skill
    endo_by_skill: dict[str, list] = {}
    for e in endorsements:
        skill = e.get("skill", "Unknown")
        endo_by_skill.setdefault(skill, []).append(e)

    for skill, endos in sorted(endo_by_skill.items(), key=lambda x: -len(x[1])):
        lines.append(f"SKILL: {skill} ({len(endos)} endorsements)")
        for e in endos:
            name = f"{e.get('endorser_first', '')} {e.get('endorser_last', '')}".strip()
            date = (e.get("date") or "")[:10]
            lines.append(f"  - {name} ({date})")
        lines.append("")
        lines.append("---")
        lines.append("")

    filepath = output_dir / "endorsements-skills.md"
    with open(filepath, "w") as f:
        f.write("\n".join(lines))
    file_count += 1

    # 6. Shares + reactions
    shares = data.get("shares", [])
    reactions = data.get("reactions", [])

    if shares or reactions:
        lines = [
            f"CATEGORY: LinkedIn Activity — Shares & Reactions",
            f"OWNER: {my_name}",
            f"SHARES: {len(shares)}",
            f"REACTIONS: {len(reactions)}",
            "",
            "---",
            "",
        ]

        for s in shares:
            date = (s.get("date") or "")[:10]
            commentary = s.get("commentary", "").strip()
            link = s.get("link", "")
            lines.append(f"SHARE [{date}]: {commentary}")
            if link:
                lines.append(f"  LINK: {link}")
            if s.get("shared_url"):
                lines.append(f"  SHARED: {s['shared_url']}")
            lines.append("")
            lines.append("---")
            lines.append("")

        filepath = output_dir / "shares-reactions.md"
        with open(filepath, "w") as f:
            f.write("\n".join(lines))
        file_count += 1

    # 7. INDEX.md
    lines = [
        f"# LinkedIn RLAMA Collection — {my_name}",
        "",
        f"**Parsed**: {data.get('parse_date', 'unknown')[:10]}",
        f"**Messages**: {data.get('messages', {}).get('total_messages', 0)}",
        f"**Connections**: {data.get('connections', {}).get('total', 0)}",
        "",
        "## Files",
        "",
    ]

    for f in sorted(output_dir.glob("*.md")):
        if f.name != "INDEX.md":
            lines.append(f"- `{f.name}`")

    filepath = output_dir / "INDEX.md"
    with open(filepath, "w") as f:
        f.write("\n".join(lines))
    file_count += 1

    return file_count


def cmd_messages(data: dict, output: str) -> None:
    """Export messages to Markdown files."""
    output_dir = Path(output).expanduser()
    count = export_messages(data, output_dir)
    print(f"Exported {count} conversation files to {output_dir}")


def cmd_connections(data: dict, output: str) -> None:
    """Export connections to Markdown."""
    output_path = Path(output).expanduser()
    if output_path.is_dir():
        output_path = output_path / "connections.md"
    count = export_connections(data, output_path)
    print(f"Exported {count} connections to {output_path}")


def cmd_all(data: dict, output: str) -> None:
    """Export everything to Markdown."""
    output_dir = Path(output).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    msg_count = export_messages(data, output_dir / "messages")
    print(f"  Messages: {msg_count} conversation files")

    conn_count = export_connections(data, output_dir / "connections.md")
    print(f"  Connections: {conn_count} contacts")

    export_profile(data, output_dir / "profile.md")
    print(f"  Profile: exported")

    print(f"\nAll exports written to {output_dir}")


def cmd_rlama(data: dict, output: str) -> None:
    """Export RLAMA-optimized documents."""
    output_dir = Path(output).expanduser()
    count = export_rlama(data, output_dir)
    print(f"Exported {count} RLAMA-optimized files to {output_dir}")
    print(f"\nTo create RLAMA collection:")
    print(f"  rlama rag qwen2.5:7b linkedin-tdimino {output_dir} \\")
    print(f"    --chunking=fixed --chunk-size=600 --chunk-overlap=100")
    print(f"  rlama add-reranker linkedin-tdimino")


def main():
    parser = argparse.ArgumentParser(description="Export LinkedIn data to Markdown")
    parser.add_argument("--data", help=f"Path to parsed.json (default: {PARSED_FILE})")

    subparsers = parser.add_subparsers(dest="command")

    p_messages = subparsers.add_parser("messages", help="Export messages (one file per conversation)")
    p_messages.add_argument("--output", "-o", required=True, help="Output directory")

    p_connections = subparsers.add_parser("connections", help="Export connections as Markdown table")
    p_connections.add_argument("--output", "-o", required=True, help="Output file or directory")

    p_all = subparsers.add_parser("all", help="Export everything")
    p_all.add_argument("--output", "-o", required=True, help="Output directory")

    p_rlama = subparsers.add_parser("rlama", help="Export RLAMA-optimized documents")
    p_rlama.add_argument("--output", "-o", help=f"Output directory (default: {DATA_DIR / 'rlama'})")

    args = parser.parse_args()

    if args.data:
        global PARSED_FILE
        PARSED_FILE = Path(args.data)

    data = load_data()

    if args.command == "messages":
        cmd_messages(data, args.output)
    elif args.command == "connections":
        cmd_connections(data, args.output)
    elif args.command == "all":
        cmd_all(data, args.output)
    elif args.command == "rlama":
        output = args.output or str(DATA_DIR / "rlama")
        cmd_rlama(data, output)
    else:
        parser.print_help()
        print("\nExamples:")
        print("  li_export.py messages --output ~/linkedin-archive/messages/")
        print("  li_export.py connections --output ~/linkedin-archive/connections.md")
        print("  li_export.py all --output ~/linkedin-archive/")
        print("  li_export.py rlama --output ~/linkedin-archive/rlama/")


if __name__ == "__main__":
    main()
