#!/usr/bin/env python3
"""
li_parse.py — Parse LinkedIn GDPR data export ZIP into structured JSON.

Usage:
    uv run li_parse.py <path-to-linkedin-export.zip>
    uv run li_parse.py <path-to-linkedin-export.zip> --output /custom/path/parsed.json

Produces: ~/.claude/skills/linkedin-export/data/parsed.json
"""

import csv
import io
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
DEFAULT_OUTPUT = DATA_DIR / "parsed.json"


def strip_bom(text: str) -> str:
    """Remove UTF-8 BOM if present."""
    return text.lstrip("\ufeff")


def parse_csv_from_zip(zf: zipfile.ZipFile, filename: str) -> list[dict]:
    """Extract and parse a CSV file from the ZIP, returning list of dicts.

    Handles LinkedIn's special format where some CSVs (e.g. Connections.csv)
    have preamble lines before the actual CSV header.
    """
    try:
        raw = zf.read(filename).decode("utf-8-sig")
        raw = strip_bom(raw)

        # Try standard parse first
        reader = csv.DictReader(io.StringIO(raw))
        rows = list(reader)

        # Detect LinkedIn's preamble format: if the first field name looks
        # like a note (e.g. "Notes:") and has only 1 column, scan for the
        # real header line containing multiple comma-separated columns.
        if rows and len(reader.fieldnames or []) <= 1:
            lines = raw.split("\n")
            for i, line in enumerate(lines):
                stripped = line.strip()
                if not stripped:
                    continue
                # Real CSV headers have multiple commas
                if stripped.count(",") >= 2:
                    rejoined = "\n".join(lines[i:])
                    reader2 = csv.DictReader(io.StringIO(rejoined))
                    rows2 = list(reader2)
                    if rows2 and len(reader2.fieldnames or []) > 1:
                        return rows2

        return rows
    except KeyError:
        return []
    except Exception as e:
        print(f"  Warning: Failed to parse {filename}: {e}", file=sys.stderr)
        return []


def find_csv_files(zf: zipfile.ZipFile) -> dict[str, str]:
    """Map canonical names to actual paths in the ZIP.

    LinkedIn exports may nest files in a subdirectory or use varying names.
    Returns {canonical_key: zip_path}.
    """
    mapping = {}
    csv_files = [n for n in zf.namelist() if n.lower().endswith(".csv")]

    # Known file patterns (case-insensitive basename matching)
    known = {
        "messages": "messages",
        "connections": "connections",
        "profile": "profile",
        "positions": "positions",
        "education": "education",
        "skills": "skills",
        "endorsement_received_info": "endorsements",
        "invitations": "invitations",
        "recommendations_received": "recommendations",
        "reactions": "reactions",
        "shares": "shares",
        "certifications": "certifications",
        "contacts": "contacts",
        "company_follows": "company_follows",
        "member_follows": "member_follows",
        "search_queries": "search_queries",
        "registration": "registration",
        # New types
        "comments": "comments",
        "projects": "projects",
        "honors": "honors",
        "organizations": "organizations",
        "volunteering": "volunteering",
        "languages": "languages",
        "events": "events",
        "recommendations_given": "recommendations_given",
        "inferences_about_you": "inferences",
        "hashtag_follows": "hashtag_follows",
        "votes": "votes",
        "instantreposts": "instant_reposts",
        "saved_items": "saved_items",
        "endorsement_given_info": "endorsements_given",
    }

    for csv_path in csv_files:
        basename = Path(csv_path).stem.lower()
        # Normalize: strip trailing _1, _2 etc. (LinkedIn splits large CSVs)
        basename_norm = basename.rstrip("_0123456789") if basename != basename.rstrip("_0123456789") else basename
        matched = False
        for pattern, key in known.items():
            # Prefer exact match on basename or normalized basename
            if basename == pattern or basename_norm == pattern:
                if key not in mapping:
                    mapping[key] = csv_path
                matched = True
                break
        if not matched:
            # Fallback: substring match but only if pattern equals the full basename
            # This prevents "messages" from matching "guide_messages"
            for pattern, key in known.items():
                if basename == pattern or basename.replace(" ", "_") == pattern:
                    if key not in mapping:
                        mapping[key] = csv_path
                    matched = True
                    break
        if not matched:
            mapping[f"_unknown_{basename}"] = csv_path

    return mapping


def parse_date_flexible(date_str: str) -> str | None:
    """Parse various LinkedIn date formats to ISO 8601."""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    formats = [
        "%Y-%m-%d %H:%M:%S %Z",  # 2024-01-15 14:30:00 UTC
        "%Y-%m-%d %H:%M:%S",  # 2024-01-15 14:30:00
        "%Y-%m-%dT%H:%M:%S",  # 2024-01-15T14:30:00
        "%Y-%m-%d",  # 2024-01-15
        "%d %b %Y",  # 15 Jan 2024
        "%b %d, %Y",  # Jan 15, 2024
        "%m/%d/%Y",  # 01/15/2024
        "%m/%d/%y, %I:%M %p",  # 3/20/20, 12:31 PM (LinkedIn job apps)
        "%m/%d/%y",  # 01/15/24
        "%b %Y",  # Jan 2024
        "%Y",  # 2024
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).isoformat()
        except ValueError:
            continue

    return date_str  # Return raw if no format matches


def col(row: dict, *candidates: str) -> str:
    """Get column value by trying multiple possible column names (case-insensitive)."""
    lower_row = {k.lower().strip(): v for k, v in row.items() if k is not None}
    for c in candidates:
        val = lower_row.get(c.lower().strip(), "")
        if val:
            return val.strip()
    return ""


def parse_messages(rows: list[dict]) -> dict:
    """Parse messages.csv into structured conversations."""
    conversations: dict[str, dict] = {}

    for row in rows:
        conv_id = col(row, "conversation id", "conversationid")
        if not conv_id:
            continue

        if conv_id not in conversations:
            conversations[conv_id] = {
                "id": conv_id,
                "title": col(row, "conversation title", "conversationtitle"),
                "messages": [],
                "participants": set(),
            }

        conv = conversations[conv_id]
        sender = col(row, "from", "sender")
        recipient = col(row, "to", "recipient")
        date = col(row, "date", "sent at", "timestamp")

        conv["messages"].append(
            {
                "from": sender,
                "from_url": col(row, "sender profile url", "senderprofileurl"),
                "to": recipient,
                "date": parse_date_flexible(date),
                "date_raw": date,
                "subject": col(row, "subject"),
                "content": col(row, "content", "body", "message"),
                "folder": col(row, "folder"),
            }
        )

        if sender:
            conv["participants"].add(sender)
        if recipient:
            for r in recipient.split(","):
                r = r.strip()
                if r:
                    conv["participants"].add(r)

    # Sort messages within each conversation by date
    for conv in conversations.values():
        conv["messages"].sort(key=lambda m: m.get("date") or "")
        conv["participants"] = sorted(conv["participants"])
        conv["message_count"] = len(conv["messages"])

    all_messages = [m for c in conversations.values() for m in c["messages"]]
    dates = [m["date"] for m in all_messages if m.get("date")]

    return {
        "conversations": sorted(
            conversations.values(), key=lambda c: c["messages"][-1].get("date") or "" if c["messages"] else "", reverse=True
        ),
        "total_messages": len(all_messages),
        "total_conversations": len(conversations),
        "date_range": [min(dates), max(dates)] if dates else [],
    }


def parse_connections(rows: list[dict]) -> dict:
    """Parse Connections.csv into structured contacts."""
    contacts = []
    companies: Counter = Counter()

    for row in rows:
        company = col(row, "company", "organization")
        contact = {
            "first_name": col(row, "first name", "firstname"),
            "last_name": col(row, "last name", "lastname"),
            "url": col(row, "url", "profile url", "profileurl"),
            "email": col(row, "email address", "emailaddress", "email"),
            "company": company,
            "position": col(row, "position", "title"),
            "connected_on": parse_date_flexible(col(row, "connected on", "connectedon")),
            "connected_on_raw": col(row, "connected on", "connectedon"),
        }
        contacts.append(contact)
        if company:
            companies[company] += 1

    dates = [c["connected_on"] for c in contacts if c.get("connected_on")]

    return {
        "contacts": sorted(contacts, key=lambda c: c.get("connected_on") or "", reverse=True),
        "total": len(contacts),
        "companies": dict(companies.most_common()),
        "date_range": [min(dates), max(dates)] if dates else [],
    }


def parse_profile(rows: list[dict]) -> dict:
    """Parse Profile.csv into a profile dict."""
    if not rows:
        return {}
    row = rows[0]
    return {
        "first_name": col(row, "first name", "firstname"),
        "last_name": col(row, "last name", "lastname"),
        "maiden_name": col(row, "maiden name"),
        "headline": col(row, "headline"),
        "summary": col(row, "summary", "about"),
        "industry": col(row, "industry"),
        "location": col(row, "geo location", "geolocation", "address", "location"),
        "twitter": col(row, "twitter handles", "twitterhandles"),
        "websites": col(row, "websites"),
    }


def parse_positions(rows: list[dict]) -> list[dict]:
    """Parse Positions.csv into work history."""
    positions = []
    for row in rows:
        positions.append(
            {
                "company": col(row, "company name", "companyname", "company"),
                "title": col(row, "title", "position"),
                "description": col(row, "description"),
                "location": col(row, "location"),
                "started_on": parse_date_flexible(col(row, "started on", "startedon", "start date")),
                "finished_on": parse_date_flexible(col(row, "finished on", "finishedon", "end date")),
            }
        )
    return sorted(positions, key=lambda p: p.get("started_on") or "", reverse=True)


def parse_education(rows: list[dict]) -> list[dict]:
    """Parse Education.csv."""
    return [
        {
            "school": col(row, "school name", "schoolname", "school"),
            "degree": col(row, "degree name", "degreename", "degree"),
            "start_date": parse_date_flexible(col(row, "start date", "startdate")),
            "end_date": parse_date_flexible(col(row, "end date", "enddate")),
            "activities": col(row, "activities"),
            "notes": col(row, "notes"),
        }
        for row in rows
    ]


def parse_skills(rows: list[dict]) -> list[str]:
    """Parse Skills.csv."""
    return sorted(set(col(row, "name", "skill name", "skillname") for row in rows if col(row, "name", "skill name", "skillname")))


def parse_endorsements(rows: list[dict]) -> list[dict]:
    """Parse Endorsement_Received_Info.csv."""
    return [
        {
            "skill": col(row, "skill name", "skillname", "skill"),
            "endorser_first": col(row, "endorser first name", "endorserfirstname"),
            "endorser_last": col(row, "endorser last name", "endorserlastname"),
            "date": parse_date_flexible(col(row, "endorsement date", "endorsementdate", "date")),
        }
        for row in rows
    ]


def parse_invitations(rows: list[dict]) -> list[dict]:
    """Parse Invitations.csv."""
    return [
        {
            "from": col(row, "from", "sender"),
            "to": col(row, "to", "recipient"),
            "date": parse_date_flexible(col(row, "sent at", "sentat", "date")),
            "message": col(row, "message", "body"),
            "direction": col(row, "direction"),
        }
        for row in rows
    ]


def parse_recommendations(rows: list[dict]) -> list[dict]:
    """Parse Recommendations_Received.csv."""
    return [
        {
            "first_name": col(row, "first name", "firstname"),
            "last_name": col(row, "last name", "lastname"),
            "company": col(row, "company"),
            "title": col(row, "title"),
            "body": col(row, "body", "text", "recommendation"),
            "date": parse_date_flexible(col(row, "created date", "createddate", "date")),
        }
        for row in rows
    ]


def parse_shares(rows: list[dict]) -> list[dict]:
    """Parse Shares.csv."""
    return [
        {
            "date": parse_date_flexible(col(row, "date", "timestamp")),
            "link": col(row, "sharelink", "share link", "link"),
            "commentary": col(row, "sharecommentary", "share commentary", "commentary", "text"),
            "shared_url": col(row, "sharedurl", "shared url"),
            "media_url": col(row, "mediaurl", "media url"),
        }
        for row in rows
    ]


def parse_reactions(rows: list[dict]) -> list[dict]:
    """Parse Reactions.csv."""
    return [
        {
            "date": parse_date_flexible(col(row, "date", "timestamp")),
            "type": col(row, "type", "reaction"),
            "link": col(row, "link", "url"),
        }
        for row in rows
    ]


def parse_certifications(rows: list[dict]) -> list[dict]:
    """Parse Certifications.csv."""
    return [
        {
            "name": col(row, "name", "certification"),
            "authority": col(row, "authority", "issuer"),
            "url": col(row, "url"),
            "started_on": parse_date_flexible(col(row, "started on", "startedon")),
            "finished_on": parse_date_flexible(col(row, "finished on", "finishedon")),
            "license_number": col(row, "license number", "licensenumber"),
        }
        for row in rows
    ]


def parse_comments(rows: list[dict]) -> list[dict]:
    """Parse Comments.csv."""
    return [
        {
            "date": parse_date_flexible(col(row, "date", "timestamp")),
            "link": col(row, "link", "url"),
            "message": col(row, "message", "comment", "text"),
        }
        for row in rows
    ]


def parse_projects(rows: list[dict]) -> list[dict]:
    """Parse Projects.csv."""
    return [
        {
            "title": col(row, "title", "name"),
            "description": col(row, "description"),
            "url": col(row, "url"),
            "started_on": parse_date_flexible(col(row, "started on", "startedon")),
            "finished_on": parse_date_flexible(col(row, "finished on", "finishedon")),
        }
        for row in rows
    ]


def parse_honors(rows: list[dict]) -> list[dict]:
    """Parse Honors.csv."""
    return [
        {
            "title": col(row, "title", "name"),
            "description": col(row, "description"),
            "issued_on": parse_date_flexible(col(row, "issued on", "issuedon", "date")),
        }
        for row in rows
    ]


def parse_organizations(rows: list[dict]) -> list[dict]:
    """Parse Organizations.csv."""
    return [
        {
            "name": col(row, "name", "organization"),
            "description": col(row, "description"),
            "position": col(row, "position", "title"),
            "started_on": parse_date_flexible(col(row, "started on", "startedon")),
            "finished_on": parse_date_flexible(col(row, "finished on", "finishedon")),
        }
        for row in rows
    ]


def parse_volunteering(rows: list[dict]) -> list[dict]:
    """Parse Volunteering.csv."""
    return [
        {
            "company": col(row, "company name", "companyname", "company"),
            "role": col(row, "role", "title"),
            "cause": col(row, "cause"),
            "started_on": parse_date_flexible(col(row, "started on", "startedon")),
            "finished_on": parse_date_flexible(col(row, "finished on", "finishedon")),
            "description": col(row, "description"),
        }
        for row in rows
    ]


def parse_languages(rows: list[dict]) -> list[dict]:
    """Parse Languages.csv."""
    return [
        {
            "name": col(row, "name", "language"),
            "proficiency": col(row, "proficiency"),
        }
        for row in rows
    ]


def parse_events(rows: list[dict]) -> list[dict]:
    """Parse Events.csv."""
    return [
        {
            "name": col(row, "event name", "eventname", "name"),
            "time": parse_date_flexible(col(row, "event time", "eventtime", "time", "date")),
            "status": col(row, "status"),
            "url": col(row, "external url", "externalurl", "url"),
        }
        for row in rows
    ]


def parse_member_follows(rows: list[dict]) -> list[dict]:
    """Parse Member_Follows.csv."""
    return [
        {
            "full_name": col(row, "fullname", "full name", "name"),
            "date": parse_date_flexible(col(row, "date", "timestamp")),
            "status": col(row, "status"),
        }
        for row in rows
    ]


def parse_job_applications(rows: list[dict]) -> list[dict]:
    """Parse Job Applications.csv (may be merged from multiple files)."""
    return [
        {
            "date": parse_date_flexible(col(row, "application date", "applicationdate", "date")),
            "company": col(row, "company name", "companyname", "company"),
            "title": col(row, "job title", "jobtitle", "title"),
            "url": col(row, "job url", "joburl", "url"),
            "resume": col(row, "resume name", "resumename"),
        }
        for row in rows
    ]


def parse_recommendations_given(rows: list[dict]) -> list[dict]:
    """Parse Recommendations_Given.csv."""
    return [
        {
            "first_name": col(row, "first name", "firstname"),
            "last_name": col(row, "last name", "lastname"),
            "company": col(row, "company"),
            "title": col(row, "job title", "jobtitle", "title"),
            "body": col(row, "text", "body", "recommendation"),
            "date": parse_date_flexible(col(row, "creation date", "creationdate", "date")),
            "status": col(row, "status"),
        }
        for row in rows
    ]


def parse_inferences(rows: list[dict]) -> list[dict]:
    """Parse Inferences_about_you.csv."""
    return [
        {
            "category": col(row, "category"),
            "type": col(row, "type of inference", "typeofinference", "type"),
            "description": col(row, "description"),
            "inference": col(row, "inference"),
        }
        for row in rows
    ]


def parse_export(zip_path: str, output_path: str | None = None) -> dict:
    """Main entry point: parse LinkedIn export ZIP into structured JSON."""
    zip_path = Path(zip_path).expanduser().resolve()
    output = Path(output_path) if output_path else DEFAULT_OUTPUT

    if not zip_path.exists():
        print(f"Error: ZIP file not found: {zip_path}", file=sys.stderr)
        sys.exit(1)

    if not zipfile.is_zipfile(zip_path):
        print(f"Error: Not a valid ZIP file: {zip_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Parsing LinkedIn export: {zip_path}")

    with zipfile.ZipFile(zip_path, "r") as zf:
        # Discover CSV files
        csv_map = find_csv_files(zf)
        print(f"  Found {len(csv_map)} CSV files")

        for key, path in sorted(csv_map.items()):
            if not key.startswith("_unknown_"):
                print(f"    {key}: {path}")

        unknown = {k: v for k, v in csv_map.items() if k.startswith("_unknown_")}
        if unknown:
            print(f"  Unrecognized CSVs ({len(unknown)}):")
            for key, path in sorted(unknown.items()):
                print(f"    {path}")

        # Parse each known CSV type
        raw: dict[str, list[dict]] = {}
        for key, path in csv_map.items():
            if not key.startswith("_unknown_"):
                raw[key] = parse_csv_from_zip(zf, path)
                print(f"  Parsed {key}: {len(raw[key])} rows")

        # Merge multi-file Job Applications (LinkedIn splits at 200 rows)
        job_app_rows: list[dict] = []
        all_names = zf.namelist()
        job_app_files = sorted(
            n for n in all_names
            if "job application" in n.lower() and n.lower().endswith(".csv")
        )
        for jaf in job_app_files:
            rows = parse_csv_from_zip(zf, jaf)
            job_app_rows.extend(rows)
            print(f"  Parsed job_applications ({jaf}): {len(rows)} rows")
        if job_app_rows:
            print(f"  Total job applications: {len(job_app_rows)}")

        # Build structured output
        result = {
            "export_file": str(zip_path),
            "export_date": datetime.fromtimestamp(zip_path.stat().st_mtime).isoformat(),
            "parse_date": datetime.now().isoformat(),
            "csv_files_found": {k: v for k, v in csv_map.items() if not k.startswith("_unknown_")},
            "unknown_csv_files": {k.replace("_unknown_", ""): v for k, v in csv_map.items() if k.startswith("_unknown_")},
            # Original types
            "messages": parse_messages(raw.get("messages", [])),
            "connections": parse_connections(raw.get("connections", [])),
            "profile": parse_profile(raw.get("profile", [])),
            "positions": parse_positions(raw.get("positions", [])),
            "education": parse_education(raw.get("education", [])),
            "skills": parse_skills(raw.get("skills", [])),
            "endorsements": parse_endorsements(raw.get("endorsements", [])),
            "invitations": parse_invitations(raw.get("invitations", [])),
            "recommendations": parse_recommendations(raw.get("recommendations", [])),
            "shares": parse_shares(raw.get("shares", [])),
            "reactions": parse_reactions(raw.get("reactions", [])),
            "certifications": parse_certifications(raw.get("certifications", [])),
            # New types
            "comments": parse_comments(raw.get("comments", [])),
            "projects": parse_projects(raw.get("projects", [])),
            "honors": parse_honors(raw.get("honors", [])),
            "organizations": parse_organizations(raw.get("organizations", [])),
            "volunteering": parse_volunteering(raw.get("volunteering", [])),
            "languages": parse_languages(raw.get("languages", [])),
            "events": parse_events(raw.get("events", [])),
            "member_follows": parse_member_follows(raw.get("member_follows", [])),
            "job_applications": parse_job_applications(job_app_rows),
            "recommendations_given": parse_recommendations_given(raw.get("recommendations_given", [])),
            "inferences": parse_inferences(raw.get("inferences", [])),
        }

    # Write output
    output.parent.mkdir(parents=True, exist_ok=True)
    with open(output, "w") as f:
        json.dump(result, f, indent=2, default=str)

    # Print summary
    print(f"\n{'='*60}")
    print(f"LinkedIn Export Summary")
    print(f"{'='*60}")
    if result["profile"]:
        p = result["profile"]
        name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
        if name:
            print(f"  Profile: {name}")
        if p.get("headline"):
            print(f"  Headline: {p['headline']}")

    print(f"  Messages: {result['messages']['total_messages']} in {result['messages']['total_conversations']} conversations")
    if result["messages"]["date_range"]:
        print(f"    Date range: {result['messages']['date_range'][0][:10]} — {result['messages']['date_range'][1][:10]}")

    print(f"  Connections: {result['connections']['total']}")
    if result["connections"]["date_range"]:
        print(f"    Date range: {result['connections']['date_range'][0][:10]} — {result['connections']['date_range'][1][:10]}")

    top_companies = list(result["connections"]["companies"].items())[:5]
    if top_companies:
        print(f"    Top companies: {', '.join(f'{c} ({n})' for c, n in top_companies)}")

    print(f"  Positions: {len(result['positions'])}")
    print(f"  Education: {len(result['education'])}")
    print(f"  Skills: {len(result['skills'])}")
    print(f"  Endorsements: {len(result['endorsements'])}")
    print(f"  Recommendations: {len(result['recommendations'])}")
    print(f"  Invitations: {len(result['invitations'])}")
    print(f"  Shares: {len(result['shares'])}")
    print(f"  Reactions: {len(result['reactions'])}")
    print(f"  Certifications: {len(result['certifications'])}")
    print(f"  Comments: {len(result['comments'])}")
    print(f"  Projects: {len(result['projects'])}")
    print(f"  Honors: {len(result['honors'])}")
    print(f"  Organizations: {len(result['organizations'])}")
    print(f"  Volunteering: {len(result['volunteering'])}")
    print(f"  Languages: {len(result['languages'])}")
    print(f"  Events: {len(result['events'])}")
    print(f"  Member Follows: {len(result['member_follows'])}")
    print(f"  Job Applications: {len(result['job_applications'])}")
    print(f"  Recommendations Given: {len(result['recommendations_given'])}")
    print(f"  Inferences: {len(result['inferences'])}")
    print(f"{'='*60}")
    print(f"Output: {output}")

    return result


def main():
    if len(sys.argv) < 2:
        print("Usage: li_parse.py <linkedin-export.zip> [--output <path>]")
        print("\nParses LinkedIn GDPR data export ZIP into structured JSON.")
        print(f"Default output: {DEFAULT_OUTPUT}")
        sys.exit(1)

    zip_path = sys.argv[1]
    output_path = None

    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            output_path = sys.argv[idx + 1]

    parse_export(zip_path, output_path)


if __name__ == "__main__":
    main()
