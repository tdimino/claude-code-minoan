#!/usr/bin/env python3
"""
Fetch cuneiform texts and data from CDLI and ORACC databases.

Usage:
    python3 fetch_cuneiform.py cdli P123456              # Fetch CDLI artifact by P-number
    python3 fetch_cuneiform.py cdli-inscription P123456  # Fetch inscription text
    python3 fetch_cuneiform.py oracc-projects            # List ORACC projects
    python3 fetch_cuneiform.py oracc-text rimanum P295625  # Fetch text from project
    python3 fetch_cuneiform.py oracc-glossary rimanum akk  # Fetch glossary
    python3 fetch_cuneiform.py deity tiamat              # Look up deity in AMGG
    python3 fetch_cuneiform.py search "tiamat"           # Search CDLI catalogue
"""

import argparse
import json
import sys
import urllib.request
import urllib.parse
import urllib.error
from typing import Optional, Dict, Any, List


# Base URLs
CDLI_BASE = "https://cdli.earth"
ORACC_BASE = "http://oracc.museum.upenn.edu"

# Pre-indexed deity names for AMGG lookups
DEITIES = {
    "tiamat": "tiamat",
    "ti'amat": "tiamat",
    "marduk": "marduk",
    "ea": "ea",
    "enki": "enki",
    "enlil": "enlil",
    "anu": "anu",
    "ishtar": "ishtar",
    "inanna": "inanna",
    "shamash": "shamash",
    "utu": "shamash",
    "sin": "sin",
    "nanna": "sin",
    "adad": "adad",
    "hadad": "adad",
    "asherah": "asherah",
    "athirat": "athirat",
    "baal": "baal",
    "ba'al": "baal",
    "dagan": "dagan",
    "dagon": "dagan",
}


def fetch_json(url: str) -> Optional[Dict[str, Any]]:
    """Fetch JSON from URL."""
    headers = {
        "Accept": "application/json",
        "User-Agent": "ANE-Research-Script/1.0"
    }
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        return None
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}", file=sys.stderr)
        return None


def fetch_text(url: str) -> Optional[str]:
    """Fetch plain text from URL."""
    headers = {
        "User-Agent": "ANE-Research-Script/1.0"
    }
    request = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching text: {e}", file=sys.stderr)
        return None


def cdli_artifact(p_number: str) -> None:
    """Fetch CDLI artifact metadata by P-number."""
    # Normalize P-number
    if not p_number.upper().startswith('P'):
        p_number = f"P{p_number}"
    p_number = p_number.upper()

    url = f"{CDLI_BASE}/artifacts/{p_number}.json"
    data = fetch_json(url)

    if not data:
        print(f"Could not fetch artifact {p_number}")
        return

    print(f"# CDLI Artifact: {p_number}")
    print()

    # Display key fields
    fields = [
        ("designation", "Designation"),
        ("collection", "Collection"),
        ("museum_no", "Museum No."),
        ("provenience", "Provenience"),
        ("period", "Period"),
        ("genre", "Genre"),
        ("language", "Language"),
        ("material", "Material"),
    ]

    for key, label in fields:
        if key in data and data[key]:
            print(f"**{label}:** {data[key]}")

    print()
    print(f"*URL: {CDLI_BASE}/artifacts/{p_number}*")


def cdli_inscription(p_number: str) -> None:
    """Fetch CDLI inscription text (ATF format) via JSON endpoint."""
    if not p_number.upper().startswith('P'):
        p_number = f"P{p_number}"
    p_number = p_number.upper()

    # Use the main JSON endpoint which includes ATF in the inscription field
    # The /inscription/latest endpoint is unreliable (often returns HTTP 500)
    url = f"{CDLI_BASE}/artifacts/{p_number}.json"
    data = fetch_json(url)

    if not data:
        print(f"Could not fetch artifact {p_number}")
        return

    print(f"# Inscription: {p_number}")

    # Get designation if available
    if "designation" in data and data["designation"]:
        print(f"**{data['designation']}**")
    print()

    # Extract ATF from inscription field
    inscription = data.get("inscription", {})
    if isinstance(inscription, dict):
        atf = inscription.get("atf", "")
    elif isinstance(inscription, str):
        atf = inscription
    else:
        atf = ""

    if atf:
        print("```atf")
        print(atf)
        print("```")
    else:
        print("*No inscription text available for this artifact.*")

    print()
    print(f"*URL: {CDLI_BASE}/artifacts/{p_number}*")


def oracc_projects() -> None:
    """List available ORACC projects."""
    url = f"{ORACC_BASE}/projectlist.json"
    data = fetch_json(url)

    if not data or "projects" not in data:
        print("Could not fetch ORACC project list")
        return

    print("# ORACC Projects")
    print()

    for proj in data["projects"]:
        name = proj.get("name", "Unknown")
        pathname = proj.get("pathname", "")
        abbrev = proj.get("abbrev", "")

        print(f"## {name}")
        if abbrev:
            print(f"**Abbrev:** {abbrev}")
        print(f"**Path:** {pathname}")
        print(f"**URL:** {ORACC_BASE}/{pathname}/")
        print()


def oracc_text(project: str, text_id: str) -> None:
    """Fetch a text edition from ORACC project."""
    # Normalize text ID
    if not text_id.upper().startswith('P') and not text_id.upper().startswith('Q'):
        text_id = f"P{text_id}"
    text_id = text_id.upper()

    url = f"{ORACC_BASE}/{project}/corpusjson/{text_id}.json"
    data = fetch_json(url)

    if not data:
        print(f"Could not fetch text {text_id} from project {project}")
        return

    print(f"# ORACC Text: {text_id}")
    print(f"**Project:** {project}")
    print()

    # Extract and display text content
    def extract_text(cdl_node: Dict, indent: int = 0) -> List[str]:
        """Recursively extract text from CDL structure."""
        lines = []
        node_type = cdl_node.get("node")

        if node_type == "d":
            # Discontinuity (line break, surface, etc.)
            label = cdl_node.get("label", "")
            dtype = cdl_node.get("type", "")
            if dtype == "line-start":
                lines.append(f"\n{label}. ")
            elif dtype in ["obverse", "reverse", "edge"]:
                lines.append(f"\n\n**{dtype.title()}**\n")
        elif node_type == "l":
            # Lemma (word)
            frag = cdl_node.get("frag", "")
            lines.append(frag + " ")
        elif node_type == "c":
            # Chunk (contains children)
            for child in cdl_node.get("cdl", []):
                lines.extend(extract_text(child, indent + 1))

        return lines

    cdl = data.get("cdl", [])
    for node in cdl:
        text_parts = extract_text(node)
        print("".join(text_parts))

    print()
    print(f"*URL: {ORACC_BASE}/{project}/{text_id}*")


def oracc_glossary(project: str, lang: str) -> None:
    """Fetch glossary from ORACC project."""
    url = f"{ORACC_BASE}/{project}/glossary-{lang}.json"
    data = fetch_json(url)

    if not data:
        print(f"Could not fetch {lang} glossary from project {project}")
        return

    print(f"# ORACC Glossary: {project} ({lang})")
    print()

    entries = data.get("entries", [])
    for entry in entries[:50]:  # Limit output
        headword = entry.get("headword", "")
        cf = entry.get("cf", "")
        gw = entry.get("gw", "")
        pos = entry.get("pos", "")
        icount = entry.get("icount", 0)

        print(f"- **{cf}** [{gw}] ({pos}) — {icount} instances")

    if len(entries) > 50:
        print(f"\n*... and {len(entries) - 50} more entries*")


def deity_lookup(deity_name: str) -> None:
    """Look up deity in ORACC AMGG (Ancient Mesopotamian Gods and Goddesses)."""
    # Normalize deity name
    deity_lower = deity_name.lower()
    if deity_lower in DEITIES:
        deity_name = DEITIES[deity_lower]

    # AMGG deity page
    url = f"{ORACC_BASE}/amgg/listofdeities/{deity_name}/"

    print(f"# Deity: {deity_name.title()}")
    print()
    print(f"**AMGG URL:** {url}")
    print()
    print("To view full scholarly information, visit the URL above.")
    print()
    print("For web scraping, use:")
    print(f"```bash")
    print(f"firecrawl {url}")
    print(f"```")


def cdli_search(query: str, limit: int = 20) -> None:
    """Search CDLI catalogue (provides search URL - actual search requires web interface)."""
    encoded_query = urllib.parse.quote(query)
    search_url = f"{CDLI_BASE}/search?q={encoded_query}"

    print(f"# CDLI Search: {query}")
    print()
    print(f"**Search URL:** {search_url}")
    print()
    print("CDLI search requires the web interface. Visit the URL above to search.")
    print()
    print("For programmatic access, use specific P-numbers:")
    print("```bash")
    print(f"python3 fetch_cuneiform.py cdli P123456")
    print("```")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch cuneiform texts from CDLI and ORACC',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s cdli P123456              # Fetch CDLI artifact metadata
    %(prog)s cdli-inscription P123456  # Fetch inscription (ATF)
    %(prog)s oracc-projects            # List ORACC projects
    %(prog)s oracc-text rimanum P295625  # Fetch text edition
    %(prog)s oracc-glossary rimanum akk  # Fetch Akkadian glossary
    %(prog)s deity tiamat              # Look up deity in AMGG
    %(prog)s search "enuma elish"      # Search CDLI

Key ORACC Projects for ANE Research:
    amgg     - Ancient Mesopotamian Gods and Goddesses
    etcsl    - Electronic Text Corpus of Sumerian Literature
    saao     - State Archives of Assyria online
    rinap    - Royal Inscriptions of Neo-Assyrian Period
        """
    )

    parser.add_argument('command', choices=[
        'cdli', 'cdli-inscription',
        'oracc-projects', 'oracc-text', 'oracc-glossary',
        'deity', 'search'
    ], help='Command to execute')

    parser.add_argument('args', nargs='*', help='Command arguments')
    parser.add_argument('--json', action='store_true', help='Output raw JSON')
    parser.add_argument('--limit', type=int, default=20, help='Limit results')

    args = parser.parse_args()

    if args.command == 'cdli':
        if not args.args:
            print("Usage: fetch_cuneiform.py cdli P123456")
            return
        cdli_artifact(args.args[0])

    elif args.command == 'cdli-inscription':
        if not args.args:
            print("Usage: fetch_cuneiform.py cdli-inscription P123456")
            return
        cdli_inscription(args.args[0])

    elif args.command == 'oracc-projects':
        oracc_projects()

    elif args.command == 'oracc-text':
        if len(args.args) < 2:
            print("Usage: fetch_cuneiform.py oracc-text PROJECT TEXT_ID")
            return
        oracc_text(args.args[0], args.args[1])

    elif args.command == 'oracc-glossary':
        if len(args.args) < 2:
            print("Usage: fetch_cuneiform.py oracc-glossary PROJECT LANG")
            print("Languages: sux (Sumerian), akk (Akkadian), etc.")
            return
        oracc_glossary(args.args[0], args.args[1])

    elif args.command == 'deity':
        if not args.args:
            print("Usage: fetch_cuneiform.py deity DEITY_NAME")
            print("Examples: tiamat, marduk, ishtar, enlil")
            return
        deity_lookup(args.args[0])

    elif args.command == 'search':
        if not args.args:
            print("Usage: fetch_cuneiform.py search QUERY")
            return
        cdli_search(' '.join(args.args), args.limit)


if __name__ == "__main__":
    main()
