#!/usr/bin/env python3
"""
Fetch Biblical texts from Sefaria API with Hebrew and English.

Usage:
    python3 fetch_sefaria.py "Genesis 1:1-3"
    python3 fetch_sefaria.py "Genesis 1:2" --hebrew-only
    python3 fetch_sefaria.py "Genesis 1:2" --with-rashi
    python3 fetch_sefaria.py --search "תהום"
    python3 fetch_sefaria.py --search "leviathan"
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.parse
from typing import Optional, List


# Pre-indexed Hebrew term references for ANE research
TERM_INDEX = {
    # Tehom - the Deep (cognate of Tiamat)
    "תהום": [
        "Genesis.1.2", "Genesis.7.11", "Genesis.8.2", "Genesis.49.25",
        "Exodus.15.5", "Exodus.15.8", "Deuteronomy.8.7", "Deuteronomy.33.13",
        "Job.28.14", "Job.38.16", "Job.38.30", "Job.41.24",
        "Psalms.33.7", "Psalms.36.7", "Psalms.42.8", "Psalms.71.20",
        "Psalms.77.17", "Psalms.78.15", "Psalms.104.6", "Psalms.106.9",
        "Psalms.107.26", "Psalms.135.6", "Psalms.148.7",
        "Proverbs.3.20", "Proverbs.8.24", "Proverbs.8.27", "Proverbs.8.28",
        "Isaiah.51.10", "Isaiah.63.13",
        "Ezekiel.26.19", "Ezekiel.31.4", "Ezekiel.31.15",
        "Amos.7.4", "Jonah.2.6", "Habakkuk.3.10",
    ],
    "tehom": "תהום",  # English alias
    "deep": "תהום",
    "the deep": "תהום",

    # Asherah/Asherim
    "אשרה": [
        "Exodus.34.13", "Deuteronomy.7.5", "Deuteronomy.12.3", "Deuteronomy.16.21",
        "Judges.3.7", "Judges.6.25", "Judges.6.26", "Judges.6.28", "Judges.6.30",
        "1_Kings.14.15", "1_Kings.14.23", "1_Kings.15.13", "1_Kings.16.33", "1_Kings.18.19",
        "2_Kings.13.6", "2_Kings.17.10", "2_Kings.17.16", "2_Kings.18.4",
        "2_Kings.21.3", "2_Kings.21.7", "2_Kings.23.4", "2_Kings.23.6", "2_Kings.23.7", "2_Kings.23.14", "2_Kings.23.15",
        "2_Chronicles.14.2", "2_Chronicles.15.16", "2_Chronicles.17.6", "2_Chronicles.19.3",
        "2_Chronicles.24.18", "2_Chronicles.31.1", "2_Chronicles.33.3", "2_Chronicles.33.19", "2_Chronicles.34.3", "2_Chronicles.34.4", "2_Chronicles.34.7",
        "Isaiah.17.8", "Isaiah.27.9",
        "Jeremiah.17.2",
        "Micah.5.13",
    ],
    "asherah": "אשרה",
    "asherim": "אשרה",

    # Leviathan
    "לויתן": [
        "Job.3.8", "Job.40.25",
        "Psalms.74.14", "Psalms.104.26",
        "Isaiah.27.1",
    ],
    "leviathan": "לויתן",

    # Ruach Elohim (Spirit of God)
    "רוח אלהים": [
        "Genesis.1.2", "Genesis.41.38",
        "Exodus.31.3", "Exodus.35.31",
        "Numbers.24.2",
        "1_Samuel.10.10", "1_Samuel.11.6", "1_Samuel.19.20", "1_Samuel.19.23",
        "Ezekiel.11.24",
    ],
    "ruach elohim": "רוח אלהים",
    "spirit of god": "רוח אלהים",

    # Yam (Sea) - important for Ugaritic parallels
    "ים": [
        "Genesis.1.10", "Genesis.1.22", "Genesis.1.26", "Genesis.1.28",
        "Exodus.14.16", "Exodus.14.21", "Exodus.14.27", "Exodus.15.1", "Exodus.15.4", "Exodus.15.8", "Exodus.15.10", "Exodus.15.19",
        "Job.7.12", "Job.26.12", "Job.38.8",
        "Psalms.74.13", "Psalms.89.10", "Psalms.93.4", "Psalms.104.25",
        "Isaiah.27.1", "Isaiah.51.10",
    ],
    "yam": "ים",
    "sea": "ים",

    # Tanninim (Sea monsters/dragons)
    "תנינים": [
        "Genesis.1.21",
        "Exodus.7.9", "Exodus.7.10", "Exodus.7.12",
        "Deuteronomy.32.33",
        "Job.7.12",
        "Psalms.74.13", "Psalms.91.13", "Psalms.148.7",
        "Isaiah.27.1", "Isaiah.51.9",
        "Jeremiah.51.34",
        "Ezekiel.29.3", "Ezekiel.32.2",
    ],
    "tannin": "תנינים",
    "tanninim": "תנינים",
    "dragon": "תנינים",
    "sea monster": "תנינים",

    # Ba'al (בעל) - Canaanite storm deity
    "בעל": [
        # Judges
        "Judges.2.11", "Judges.2.13", "Judges.3.7", "Judges.6.25", "Judges.6.28",
        "Judges.6.30", "Judges.6.31", "Judges.6.32", "Judges.8.33", "Judges.9.4",
        "Judges.10.6", "Judges.10.10",
        # 1 Samuel
        "1_Samuel.7.4", "1_Samuel.12.10",
        # 1 Kings
        "1_Kings.16.31", "1_Kings.16.32", "1_Kings.18.18", "1_Kings.18.19",
        "1_Kings.18.21", "1_Kings.18.22", "1_Kings.18.25", "1_Kings.18.26",
        "1_Kings.18.40", "1_Kings.19.18", "1_Kings.22.54",
        # 2 Kings
        "2_Kings.1.2", "2_Kings.1.3", "2_Kings.1.6", "2_Kings.1.16",
        "2_Kings.3.2", "2_Kings.10.18", "2_Kings.10.19", "2_Kings.10.20",
        "2_Kings.10.21", "2_Kings.10.22", "2_Kings.10.23", "2_Kings.10.25",
        "2_Kings.10.26", "2_Kings.10.27", "2_Kings.10.28",
        "2_Kings.11.18", "2_Kings.17.16", "2_Kings.21.3",
        "2_Kings.23.4", "2_Kings.23.5",
        # Prophets
        "Jeremiah.2.8", "Jeremiah.2.23", "Jeremiah.7.9", "Jeremiah.9.13",
        "Jeremiah.11.13", "Jeremiah.11.17", "Jeremiah.12.16", "Jeremiah.19.5",
        "Jeremiah.23.13", "Jeremiah.23.27", "Jeremiah.32.29", "Jeremiah.32.35",
        "Hosea.2.10", "Hosea.2.15", "Hosea.2.18", "Hosea.2.19",
        "Hosea.9.10", "Hosea.11.2", "Hosea.13.1",
        "Zephaniah.1.4",
        # Chronicles
        "2_Chronicles.17.3", "2_Chronicles.21.6", "2_Chronicles.23.17",
        "2_Chronicles.24.7", "2_Chronicles.28.2", "2_Chronicles.33.3", "2_Chronicles.34.4",
    ],
    "baal": "בעל",
    "ba'al": "בעל",

    # Nacheshet (נחשת) - bronze/copper
    "נחשת": [
        "Genesis.4.22",
        "Exodus.25.3", "Exodus.26.11", "Exodus.26.37", "Exodus.27.2", "Exodus.27.3",
        "Exodus.27.4", "Exodus.27.6", "Exodus.27.10", "Exodus.27.11", "Exodus.27.17",
        "Exodus.27.18", "Exodus.27.19", "Exodus.30.18", "Exodus.31.4", "Exodus.35.5",
        "Exodus.35.24", "Exodus.35.32", "Exodus.36.18", "Exodus.36.38", "Exodus.38.2",
        "Exodus.38.3", "Exodus.38.4", "Exodus.38.5", "Exodus.38.6", "Exodus.38.8",
        "Exodus.38.10", "Exodus.38.11", "Exodus.38.17", "Exodus.38.19", "Exodus.38.20",
        "Exodus.38.29", "Exodus.38.30",
        "Numbers.16.39", "Numbers.21.9",
        "Deuteronomy.8.9", "Deuteronomy.28.23",
        "Joshua.6.19", "Joshua.6.24", "Joshua.22.8",
        "Judges.16.21",
        "1_Samuel.17.5", "1_Samuel.17.6", "1_Samuel.17.38",
        "2_Samuel.8.8", "2_Samuel.21.16", "2_Samuel.22.35",
        "1_Kings.7.14", "1_Kings.7.15", "1_Kings.7.16", "1_Kings.7.27", "1_Kings.7.30",
        "1_Kings.7.38", "1_Kings.7.45", "1_Kings.7.47",
        "2_Kings.18.4", "2_Kings.25.7", "2_Kings.25.13", "2_Kings.25.14",
        "2_Kings.25.16", "2_Kings.25.17",
        "1_Chronicles.15.19", "1_Chronicles.18.8", "1_Chronicles.22.3",
        "1_Chronicles.22.14", "1_Chronicles.22.16", "1_Chronicles.29.2", "1_Chronicles.29.7",
        "2_Chronicles.1.5", "2_Chronicles.4.9", "2_Chronicles.4.16", "2_Chronicles.4.18",
        "2_Chronicles.6.13", "2_Chronicles.12.10", "2_Chronicles.24.12", "2_Chronicles.36.18",
        "Job.6.12", "Job.28.2", "Job.40.18", "Job.41.19",
        "Psalms.18.35",
        "Isaiah.45.2", "Isaiah.48.4", "Isaiah.60.17",
        "Jeremiah.1.18", "Jeremiah.6.28", "Jeremiah.15.12", "Jeremiah.52.17",
        "Jeremiah.52.18", "Jeremiah.52.20", "Jeremiah.52.22",
        "Ezekiel.1.7", "Ezekiel.16.36", "Ezekiel.22.18", "Ezekiel.22.20",
        "Ezekiel.24.11", "Ezekiel.27.13",
        "Daniel.2.32", "Daniel.2.35", "Daniel.2.39", "Daniel.2.45",
        "Daniel.4.12", "Daniel.4.20", "Daniel.5.4", "Daniel.5.23",
        "Daniel.7.19", "Daniel.10.6",
        "Micah.4.13", "Zechariah.6.1",
        "Ezra.8.27",
    ],
    "nacheshet": "נחשת",
    "bronze": "נחשת",
    "copper": "נחשת",

    # Qadeshah (קדשה) - "holy woman" / cult prostitute
    "קדשה": [
        "Genesis.38.21", "Genesis.38.22",
        "Deuteronomy.23.18",
        "Hosea.4.14",
        # Male qadesh (קדש)
        "1_Kings.14.24", "1_Kings.15.12", "1_Kings.22.47",
        "2_Kings.23.7",
        "Job.36.14",
    ],
    "qadeshah": "קדשה",
    "qadesh": "קדשה",

    # Gad as deity (fortune)
    "גד_deity": [
        "Isaiah.65.11",
        "Genesis.30.11",
    ],
    "gad deity": "גד_deity",

    # Meni (מני) - destiny deity
    "מני": [
        "Isaiah.65.11",
    ],
    "meni": "מני",

    # Molech/Moloch (מלך as deity)
    "מלך_deity": [
        "Leviticus.18.21", "Leviticus.20.2", "Leviticus.20.3", "Leviticus.20.4", "Leviticus.20.5",
        "1_Kings.11.7", "2_Kings.23.10",
        "Jeremiah.32.35",
    ],
    "molech": "מלך_deity",
    "moloch": "מלך_deity",

    # Queen of Heaven (מלכת השמים)
    "מלכת השמים": [
        "Jeremiah.7.18", "Jeremiah.44.17", "Jeremiah.44.18", "Jeremiah.44.19", "Jeremiah.44.25",
    ],
    "queen of heaven": "מלכת השמים",

    # Chemosh (כמוש)
    "כמוש": [
        "Numbers.21.29", "Judges.11.24",
        "1_Kings.11.7", "1_Kings.11.33",
        "2_Kings.23.13",
        "Jeremiah.48.7", "Jeremiah.48.13", "Jeremiah.48.46",
    ],
    "chemosh": "כמוש",

    # Dagon (דגון)
    "דגון": [
        "Judges.16.23",
        "1_Samuel.5.2", "1_Samuel.5.3", "1_Samuel.5.4", "1_Samuel.5.5", "1_Samuel.5.7",
        "1_Chronicles.10.10",
    ],
    "dagon": "דגון",

    # Tammuz (תמוז)
    "תמוז": [
        "Ezekiel.8.14",
    ],
    "tammuz": "תמוז",

    # Resheph (רשף) - plague/flame deity
    "רשף": [
        "Deuteronomy.32.24",
        "Job.5.7",
        "Psalms.76.4", "Psalms.78.48",
        "Song_of_Songs.8.6",
        "Habakkuk.3.5",
    ],
    "resheph": "רשף",

    # Eilat/Ayyelet - hind, possible goddess epithet
    "אילת": [
        "Psalms.22.1",
        "Genesis.49.21",
        "2_Samuel.22.34",
        "Psalms.18.34",
        "Habakkuk.3.19",
        "Song_of_Songs.2.7", "Song_of_Songs.3.5",
        # City of Eilat/Elath
        "Deuteronomy.2.8",
        "2_Kings.14.22", "2_Kings.16.6",
        "2_Chronicles.8.17", "2_Chronicles.26.2",
    ],
    "eilat": "אילת",
    "ayyelet": "אילת",

    # Rahab (mythological sea monster)
    "רהב": [
        "Job.9.13", "Job.26.12",
        "Psalms.87.4", "Psalms.89.11",
        "Isaiah.30.7", "Isaiah.51.9",
    ],
    "rahab": "רהב",

    # Tohu va-Vohu (formless and void)
    "תהו ובהו": [
        "Genesis.1.2",
        "Isaiah.34.11",
        "Jeremiah.4.23",
    ],
    "tohu": "תהו ובהו",
    "formless and void": "תהו ובהו",
}


def normalize_reference(ref: str) -> str:
    """Convert human-readable reference to API format."""
    expansions = {
        'gen': 'Genesis', 'ex': 'Exodus', 'exod': 'Exodus',
        'lev': 'Leviticus', 'num': 'Numbers', 'deut': 'Deuteronomy',
        'josh': 'Joshua', 'judg': 'Judges', 'sam': 'Samuel',
        'kgs': 'Kings', 'kings': 'Kings', 'isa': 'Isaiah',
        'jer': 'Jeremiah', 'ezek': 'Ezekiel', 'hos': 'Hosea',
        'ps': 'Psalms', 'psalm': 'Psalms', 'prov': 'Proverbs',
        'job': 'Job', 'song': 'Song_of_Songs', 'eccl': 'Ecclesiastes',
        'lam': 'Lamentations', 'dan': 'Daniel', 'ezra': 'Ezra',
        'neh': 'Nehemiah', 'chron': 'Chronicles', 'chr': 'Chronicles',
    }

    ref = ref.strip()
    match = re.match(r'^(\d?\s*[A-Za-z]+)\s*(.*)$', ref)
    if match:
        book = match.group(1).strip()
        rest = match.group(2).strip()

        book_num = ""
        if book[0].isdigit():
            book_num = book[0] + "_"
            book = book[1:].strip()

        book_lower = book.lower()
        if book_lower in expansions:
            book = expansions[book_lower]

        book = book_num + book
        rest = rest.replace(':', '.').replace(' ', '')

        return f"{book}.{rest}" if rest else book

    return ref.replace(' ', '.').replace(':', '.')


def fetch_text(ref: str, with_commentary: Optional[str] = None) -> dict:
    """Fetch text from Sefaria API."""
    api_ref = normalize_reference(ref)

    if with_commentary:
        commentary_map = {
            'rashi': 'Rashi',
            'ibn_ezra': 'Ibn_Ezra',
            'ramban': 'Ramban',
            'onkelos': 'Targum_Onkelos',
            'neofiti': 'Targum_Neofiti',
        }
        comm_name = commentary_map.get(with_commentary.lower(), with_commentary)
        book = api_ref.split('.')[0]
        verse_ref = '.'.join(api_ref.split('.')[1:])
        api_ref = f"{comm_name}_on_{book}.{verse_ref}"

    url = f"https://www.sefaria.org/api/v3/texts/{urllib.parse.quote(api_ref)}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "ref": ref}
    except Exception as e:
        return {"error": str(e), "ref": ref}


def search_term(term: str) -> List[str]:
    """Look up references for a Hebrew term."""
    term_lower = term.lower().strip()

    # Check if it's an alias pointing to Hebrew term
    if term_lower in TERM_INDEX:
        result = TERM_INDEX[term_lower]
        if isinstance(result, str):
            # It's an alias, look up the Hebrew term
            return TERM_INDEX.get(result, [])
        return result

    # Check Hebrew terms directly
    if term in TERM_INDEX:
        result = TERM_INDEX[term]
        if isinstance(result, list):
            return result

    return []


def format_output(data: dict, hebrew_only: bool = False, as_json: bool = False) -> str:
    """Format the API response for display."""
    if as_json:
        return json.dumps(data, ensure_ascii=False, indent=2)

    if "error" in data:
        return f"Error fetching {data.get('ref', 'text')}: {data['error']}"

    lines = []

    he_ref = data.get('heRef', '')
    en_ref = data.get('ref', '')
    lines.append(f"## {en_ref}")
    if he_ref:
        lines.append(f"### {he_ref}")
    lines.append("")

    versions = data.get('versions', [])

    hebrew_text = None
    english_text = None

    for v in versions:
        lang = v.get('language', '')
        text = v.get('text', '')

        if isinstance(text, list):
            text = '\n'.join(str(t) for t in text if t)

        if lang == 'he' and not hebrew_text:
            hebrew_text = text
        elif lang == 'en' and not english_text:
            english_text = text

    if hebrew_text:
        lines.append("**Hebrew:**")
        lines.append(f"> {hebrew_text}")
        lines.append("")

    if english_text and not hebrew_only:
        lines.append("**English:**")
        lines.append(f"> {english_text}")
        lines.append("")

    lines.append(f"*Source: Sefaria ({en_ref})*")

    return '\n'.join(lines)


def list_available_terms():
    """List all searchable terms."""
    hebrew_terms = [k for k, v in TERM_INDEX.items() if isinstance(v, list)]
    print("Available Hebrew terms for search:\n")
    for term in sorted(hebrew_terms):
        refs = TERM_INDEX[term]
        print(f"  {term} ({len(refs)} passages)")
    print("\nEnglish aliases also work (e.g., 'tehom', 'asherah', 'leviathan')")


def main():
    parser = argparse.ArgumentParser(
        description='Fetch Biblical texts from Sefaria API',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s "Genesis 1:1-3"
    %(prog)s "Gen 1:2" --hebrew-only
    %(prog)s "Isaiah 45:7" --with-rashi
    %(prog)s --search "תהום"
    %(prog)s --search "tehom"
    %(prog)s --search "asherah" --fetch-all
    %(prog)s --list-terms
        """
    )

    parser.add_argument('reference', nargs='?', help='Biblical reference (e.g., "Genesis 1:1-3")')
    parser.add_argument('--hebrew-only', action='store_true',
                        help='Only output Hebrew text')
    parser.add_argument('--with-rashi', action='store_true',
                        help='Include Rashi commentary')
    parser.add_argument('--with-commentary', type=str, metavar='NAME',
                        help='Include specific commentary (rashi, ibn_ezra, ramban, onkelos, neofiti)')
    parser.add_argument('--json', action='store_true',
                        help='Output raw JSON response')
    parser.add_argument('--search', '-s', type=str, metavar='TERM',
                        help='Search for Hebrew term (e.g., "תהום" or "tehom")')
    parser.add_argument('--fetch-all', '-a', action='store_true',
                        help='Fetch full text for all search results')
    parser.add_argument('--list-terms', action='store_true',
                        help='List all available searchable terms')

    args = parser.parse_args()

    # List available terms
    if args.list_terms:
        list_available_terms()
        return

    # Search mode
    if args.search:
        refs = search_term(args.search)
        if not refs:
            print(f"No indexed passages found for '{args.search}'")
            print("Use --list-terms to see available terms")
            return

        # Determine display term
        display_term = args.search
        if args.search.lower() in TERM_INDEX:
            alias_target = TERM_INDEX[args.search.lower()]
            if isinstance(alias_target, str):
                display_term = alias_target

        print(f"# Biblical Passages Containing {display_term}\n")
        print(f"Found **{len(refs)}** passages\n")
        print("---\n")

        if args.fetch_all:
            # Fetch and display all passages
            for ref in refs:
                data = fetch_text(ref)
                output = format_output(data, hebrew_only=args.hebrew_only, as_json=args.json)
                print(output)
                print("\n---\n")
        else:
            # Just list references
            for i, ref in enumerate(refs, 1):
                # Convert API format back to readable
                readable = ref.replace('.', ' ').replace('_', ' ')
                print(f"{i}. {readable}")
            print("\nUse --fetch-all to retrieve full text of all passages")
        return

    # Single reference mode
    if not args.reference:
        parser.print_help()
        return

    commentary = None
    if args.with_rashi:
        commentary = 'rashi'
    elif args.with_commentary:
        commentary = args.with_commentary

    data = fetch_text(args.reference, with_commentary=commentary)
    output = format_output(data, hebrew_only=args.hebrew_only, as_json=args.json)
    print(output)


if __name__ == "__main__":
    main()
