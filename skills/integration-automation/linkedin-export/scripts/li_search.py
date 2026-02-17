#!/usr/bin/env python3
"""
li_search.py — Search LinkedIn messages by person, keyword, date range.

Usage:
    uv run li_search.py --person "Jane Doe"
    uv run li_search.py --keyword "project proposal"
    uv run li_search.py --person "Jane" --keyword "meeting" --after 2025-06-01
    uv run li_search.py --conversation "CONVERSATION_ID"
    uv run li_search.py --list-partners
    uv run li_search.py --list-partners --json

Requires: Run li_parse.py first to generate parsed.json
"""

import argparse
import json
import sys
from collections import Counter
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


def matches_person(message: dict, person: str) -> bool:
    """Check if a message involves a person (case-insensitive)."""
    person_lower = person.lower()
    return (
        person_lower in message.get("from", "").lower()
        or person_lower in message.get("to", "").lower()
    )


def matches_keyword(message: dict, keyword: str) -> bool:
    """Check if a message contains a keyword (case-insensitive)."""
    keyword_lower = keyword.lower()
    return (
        keyword_lower in message.get("content", "").lower()
        or keyword_lower in message.get("subject", "").lower()
    )


def matches_date_range(message: dict, after: str | None, before: str | None) -> bool:
    """Check if a message falls within the date range."""
    date = message.get("date", "")
    if not date:
        return True  # Include messages without dates when filtering

    # Compare date portion only (YYYY-MM-DD) to avoid ISO datetime
    # string comparison issues where "2025-06-01T14:30:00" > "2025-06-01"
    date_day = date[:10]
    if after and date_day < after:
        return False
    if before and date_day > before:
        return False
    return True


def format_message(msg: dict, full: bool = False) -> str:
    """Format a single message for display."""
    date = (msg.get("date") or msg.get("date_raw") or "unknown date")[:19]
    sender = msg.get("from", "unknown")
    recipient = msg.get("to", "")
    subject = msg.get("subject", "")
    content = msg.get("content", "")

    header = f"  [{date}] {sender}"
    if recipient:
        header += f" → {recipient}"
    if subject:
        header += f" | Subject: {subject}"

    if full or len(content) <= 200:
        body = content
    else:
        body = content[:197] + "..."

    return f"{header}\n    {body}" if body else header


def cmd_search(data: dict, args: argparse.Namespace) -> None:
    """Search messages with filters."""
    conversations = data.get("messages", {}).get("conversations", [])
    results = []

    for conv in conversations:
        matching_messages = []
        for msg in conv.get("messages", []):
            if args.person and not matches_person(msg, args.person):
                continue
            if args.keyword and not matches_keyword(msg, args.keyword):
                continue
            if not matches_date_range(msg, args.after, args.before):
                continue
            matching_messages.append(msg)

        if matching_messages:
            results.append({
                "conversation": conv,
                "matches": matching_messages,
            })

    if args.json:
        output = []
        for r in results:
            output.append({
                "conversation_id": r["conversation"]["id"],
                "title": r["conversation"].get("title", ""),
                "match_count": len(r["matches"]),
                "messages": r["matches"],
            })
        print(json.dumps(output, indent=2))
        return

    # Display results
    total_matches = sum(len(r["matches"]) for r in results)
    filters = []
    if args.person:
        filters.append(f"person=\"{args.person}\"")
    if args.keyword:
        filters.append(f"keyword=\"{args.keyword}\"")
    if args.after:
        filters.append(f"after={args.after}")
    if args.before:
        filters.append(f"before={args.before}")

    print(f"Search: {', '.join(filters)}")
    print(f"Found: {total_matches} messages in {len(results)} conversations\n")

    limit = args.limit or 50
    shown = 0

    for r in results:
        conv = r["conversation"]
        title = conv.get("title", conv["id"])
        print(f"── {title} ({len(r['matches'])} matches) ──")

        messages_to_show = r["matches"]
        if args.context and args.context > 0:
            # Show context messages around matches
            all_msgs = conv.get("messages", [])
            match_indices = set()
            for match in r["matches"]:
                for i, m in enumerate(all_msgs):
                    if m is match:
                        for j in range(max(0, i - args.context), min(len(all_msgs), i + args.context + 1)):
                            match_indices.add(j)
            messages_to_show = [all_msgs[i] for i in sorted(match_indices)]

        for msg in messages_to_show:
            print(format_message(msg, full=args.full))
            shown += 1
            if shown >= limit:
                remaining = total_matches - shown
                if remaining > 0:
                    print(f"\n... +{remaining} more (use --limit to show more)")
                return

        print()


def cmd_conversation(data: dict, conv_id: str, args: argparse.Namespace) -> None:
    """Show a full conversation thread."""
    conversations = data.get("messages", {}).get("conversations", [])

    for conv in conversations:
        if conv["id"] == conv_id:
            if args.json:
                print(json.dumps(conv, indent=2))
                return

            title = conv.get("title", conv["id"])
            print(f"Conversation: {title}")
            print(f"Participants: {', '.join(conv.get('participants', []))}")
            print(f"Messages: {conv.get('message_count', len(conv.get('messages', [])))}")
            print()

            for msg in conv.get("messages", []):
                print(format_message(msg, full=True))
            return

    print(f"Error: Conversation '{conv_id}' not found.", file=sys.stderr)
    sys.exit(1)


def cmd_list_partners(data: dict, args: argparse.Namespace) -> None:
    """List all conversation partners sorted by message count."""
    conversations = data.get("messages", {}).get("conversations", [])
    partner_messages: Counter = Counter()
    partner_convs: Counter = Counter()

    # Get the user's own name from profile
    profile = data.get("profile", {})
    my_name = f"{profile.get('first_name', '')} {profile.get('last_name', '')}".strip().lower()

    for conv in conversations:
        participants = conv.get("participants", [])
        for p in participants:
            if p.lower() != my_name and p.strip():
                partner_convs[p] += 1

        for msg in conv.get("messages", []):
            sender = msg.get("from", "").strip()
            if sender and sender.lower() != my_name:
                partner_messages[sender] += 1

    if args.json:
        partners = [
            {"name": name, "messages": count, "conversations": partner_convs.get(name, 0)}
            for name, count in partner_messages.most_common()
        ]
        print(json.dumps(partners, indent=2))
        return

    print(f"Conversation Partners ({len(partner_messages)} people)\n")
    print(f"{'Name':<35} {'Messages':>10} {'Conversations':>15}")
    print(f"{'─'*35} {'─'*10} {'─'*15}")

    limit = args.limit or 50
    for i, (name, count) in enumerate(partner_messages.most_common()):
        if i >= limit:
            remaining = len(partner_messages) - limit
            print(f"\n... +{remaining} more (use --limit to show all)")
            break
        convs = partner_convs.get(name, 0)
        print(f"{name:<35} {count:>10} {convs:>15}")


def main():
    parser = argparse.ArgumentParser(description="Search LinkedIn messages")
    parser.add_argument("--person", "-p", help="Filter by person name (case-insensitive)")
    parser.add_argument("--keyword", "-k", help="Filter by keyword in content/subject")
    parser.add_argument("--after", help="Filter messages after date (YYYY-MM-DD)")
    parser.add_argument("--before", help="Filter messages before date (YYYY-MM-DD)")
    parser.add_argument("--conversation", "-c", help="Show full conversation by ID")
    parser.add_argument("--list-partners", action="store_true", help="List all conversation partners")
    parser.add_argument("--context", type=int, default=0, help="Show N messages before/after each match")
    parser.add_argument("--full", "-f", action="store_true", help="Show full message content")
    parser.add_argument("--limit", "-n", type=int, help="Max results to show (default: 50)")
    parser.add_argument("--json", "-j", action="store_true", help="Output as JSON")
    parser.add_argument("--data", help=f"Path to parsed.json (default: {PARSED_FILE})")
    args = parser.parse_args()

    if args.data:
        global PARSED_FILE
        PARSED_FILE = Path(args.data)

    data = load_data()

    if args.list_partners:
        cmd_list_partners(data, args)
    elif args.conversation:
        cmd_conversation(data, args.conversation, args)
    elif args.person or args.keyword or args.after or args.before:
        cmd_search(data, args)
    else:
        parser.print_help()
        print("\nExamples:")
        print('  li_search.py --person "Jane Doe"')
        print('  li_search.py --keyword "project" --after 2025-01-01')
        print("  li_search.py --list-partners")


if __name__ == "__main__":
    main()
