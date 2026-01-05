#!/usr/bin/env python3
"""
Minoan Tarot Generator: Create tarot cards in Ellen Lorenzi-Prince's Minoan Tarot style.

This generator uses Gemini's image generation with visual memory (reference images)
to faithfully reproduce the Minoan Tarot aesthetic: flat colors, bold black outlines,
Egyptian-style poses, sky blue backgrounds, and Bronze Age Cretan iconography.

Usage:
    # Generate a specific card
    python minoan_tarot.py card "The Priestess" --number II

    # Generate with detailed description
    python minoan_tarot.py card "Bull Leaping" --number XV --description "Young acrobat mid-vault over sacred bull"

    # Generate card from archetype
    python minoan_tarot.py archetype strength

    # Continue a session (visual memory of previous cards)
    python minoan_tarot.py session "new-arcana" --card "The Dreamer"

    # Generate card back (labrys design)
    python minoan_tarot.py back

    # List all 78 traditional cards
    python minoan_tarot.py list

Environment:
    GEMINI_API_KEY - Required for Gemini API access
"""

import argparse
import base64
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import requests
except ImportError:
    print("Requires requests library. Install: pip install requests", file=sys.stderr)
    sys.exit(1)


# ============================================================================
# MINOAN TAROT DATA
# ============================================================================

MAJOR_ARCANA = {
    0: "The Fool",
    1: "The Magician",
    2: "The Priestess",
    3: "The Empress",
    4: "The Emperor",
    5: "The Priest",
    6: "The Lovers",
    7: "The Chariot",
    8: "Strength",
    9: "The Hermit",
    10: "Wheel of Fortune",
    11: "Justice",
    12: "The Hanged Man",
    13: "Death",
    14: "Temperance",
    15: "The Devil",
    16: "The Tower",
    17: "The Star",
    18: "The Moon",
    19: "The Sun",
    20: "Judgement",
    21: "The World"
}

# Minoan suit names (replacing traditional Wands, Cups, Swords, Pentacles)
SUITS = {
    "sky": "Sky",      # Wands - air/spirit
    "sea": "Sea",      # Cups - water/emotion
    "art": "Art",      # Swords - creativity/intellect
    "earth": "Earth"   # Pentacles - material/body
}

# Minoan court card names
COURT = {
    "worker": "Worker",       # Page
    "priestess": "Priestess", # Knight
    "mistress": "Mistress",   # Queen
    "master": "Master"        # King
}

# Archetype mappings for quick generation
ARCHETYPES = {
    "strength": {"number": 8, "name": "Strength", "desc": "A figure with a lion or beast, showing gentle mastery"},
    "priestess": {"number": 2, "name": "The Priestess", "desc": "The Snake Goddess holding serpents"},
    "lovers": {"number": 6, "name": "The Lovers", "desc": "Two figures in an embrace under a sacred tree"},
    "chariot": {"number": 7, "name": "The Chariot", "desc": "A figure driving a chariot pulled by griffins"},
    "fool": {"number": 0, "name": "The Fool", "desc": "A figure about to step off a cliff, carefree"},
    "death": {"number": 13, "name": "Death", "desc": "Transformation imagery with butterflies or snakes shedding skin"},
    "sun": {"number": 19, "name": "The Sun", "desc": "Radiant sun with a joyful figure, dolphins playing"},
    "moon": {"number": 18, "name": "The Moon", "desc": "Moon over water with octopi and mysterious sea creatures"},
    "star": {"number": 17, "name": "The Star", "desc": "A nude figure pouring water under stars"},
    "world": {"number": 21, "name": "The World", "desc": "A dancing figure surrounded by the four elements"},
}

# Convert number to Roman numeral
def to_roman(num: int) -> str:
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
    ]
    syms = [
        'M', 'CM', 'D', 'CD',
        'C', 'XC', 'L', 'XL',
        'X', 'IX', 'V', 'IV',
        'I'
    ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syms[i]
            num -= val[i]
        i += 1
    return roman_num


# ============================================================================
# MINOAN STYLE SYSTEM PROMPT
# ============================================================================

MINOAN_SYSTEM_PROMPT = """You are creating a tarot card in the exact style of Ellen Lorenzi-Prince's Minoan Tarot deck, based on Bronze Age Cretan art from the Palace of Knossos.

ABSOLUTE STYLE REQUIREMENTS - YOU MUST FOLLOW THESE EXACTLY:

1. FLAT COLORS - No gradients, no shading, no 3D effects, no photorealism
   - Colors should be solid blocks like ancient frescoes
   - Use vivid, saturated hues

2. BOLD BLACK OUTLINES - Every figure, object, and shape has thick black contours
   - Like stained glass or ancient murals
   - Outlines should be consistent weight throughout

3. EGYPTIAN-STYLE POSES - Frontal torsos with profile faces
   - This is the signature Minoan artistic convention
   - Figures have stylized, elongated proportions

4. COLOR PALETTE - Use these exact colors:
   - Sky Blue (#87CEEB) - Backgrounds, sky areas
   - Vivid Red (#DC3545) - Figures, accents
   - Golden Yellow (#FFD700) - Decorations, sun
   - Ochre/Terracotta (#CC7722) - Earth, animals
   - Dark Blue (#1E3A5F) - Card border frame
   - Cream/White (#FFFDD0) - Highlights
   - Black (#000000) - All outlines

5. CARD STRUCTURE:
   - Dark blue border around entire card
   - Decorative bands at top and bottom (rosettes, waves, or wheat patterns)
   - Main imagery in center against sky blue or colored background
   - Roman numeral and title at bottom in elegant serif font

6. MINOAN ICONOGRAPHY - Include authentic Bronze Age Cretan symbols:
   - Labrys (double-headed axe)
   - Horns of Consecration
   - Snake Goddess imagery
   - Bull leaping
   - Dolphins, octopi
   - Griffins (lion-eagle hybrids)
   - Swallows in spiral flight
   - Sacred lilies, papyrus, olive branches

7. COMPOSITION:
   - Central figure or scene dominates
   - Symmetrical or balanced layout
   - Clear silhouettes against solid backgrounds
   - No complex perspectives - mostly flat, frontal

The card must look like it belongs in the original 78-card Minoan Tarot deck. Study the reference images carefully and match their style EXACTLY."""


# ============================================================================
# GENERATOR CLASS
# ============================================================================

class MinoanTarotGenerator:
    """Generate Minoan Tarot cards using Gemini with visual memory."""

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
    MODEL = "gemini-3-pro-image-preview"

    def __init__(
        self,
        api_key: str,
        reference_dir: Optional[Path] = None,
        output_dir: Optional[Path] = None
    ):
        self.api_key = api_key
        self.endpoint = f"{self.BASE_URL}/{self.MODEL}:generateContent"

        # Set up directories
        skill_dir = Path(__file__).parent.parent
        self.reference_dir = reference_dir or skill_dir / "reference" / "minoan" / "selected"
        self.output_dir = output_dir or skill_dir / "canvas" / "minoan"
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def load_reference_images(self) -> List[Dict]:
        """Load reference images as base64 for visual memory."""
        images = []
        if not self.reference_dir.exists():
            print(f"Warning: Reference directory not found: {self.reference_dir}")
            return images

        for img_path in sorted(self.reference_dir.glob("*.jpg")):
            try:
                with open(img_path, 'rb') as f:
                    data = base64.b64encode(f.read()).decode('utf-8')
                images.append({
                    "inlineData": {
                        "mimeType": "image/jpeg",
                        "data": data
                    }
                })
                print(f"   Loaded reference: {img_path.name}")
            except Exception as e:
                print(f"   Warning: Could not load {img_path}: {e}")

        return images

    def build_prompt(
        self,
        card_name: str,
        number: Optional[str] = None,
        description: Optional[str] = None,
        is_back: bool = False
    ) -> str:
        """Build the generation prompt for a specific card."""

        if is_back:
            return f"""{MINOAN_SYSTEM_PROMPT}

Generate the BACK of a Minoan Tarot card.

Design requirements:
- Feature the Labrys (double-headed axe) as the central sacred symbol
- Intricate border with wave patterns and rosettes
- Deep blue or terracotta background
- Symmetrical, mandala-like composition
- This design appears on ALL card backs in the deck

The back should be recognizably Minoan but without any specific card imagery."""

        # Build card-specific prompt
        title_line = f"{number} {card_name.upper()}" if number else card_name.upper()

        desc_text = ""
        if description:
            desc_text = f"\n\nScene description: {description}"

        return f"""{MINOAN_SYSTEM_PROMPT}

Generate a Minoan Tarot card: {title_line}
{desc_text}

CRITICAL: Match the reference images exactly in style:
- Same flat color treatment
- Same bold black outlines
- Same decorative border patterns
- Same Egyptian-style figure poses
- Include "{title_line}" at the bottom of the card in the same style as reference cards

This card must look like it was created by the same artist who made the reference images."""

    def generate_card(
        self,
        card_name: str,
        number: Optional[str] = None,
        description: Optional[str] = None,
        session_images: Optional[List[Path]] = None,
        is_back: bool = False,
        temperature: float = 0.5
    ) -> Optional[Path]:
        """Generate a single tarot card."""

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        # Build message parts
        parts = []

        # Add reference images first (core visual memory)
        ref_images = self.load_reference_images()
        parts.extend(ref_images)

        # Add session images if continuing a session
        if session_images:
            for img_path in session_images:
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        data = base64.b64encode(f.read()).decode('utf-8')
                    parts.append({
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": data
                        }
                    })
                    print(f"   Session memory: {img_path.name}")

        # Add the text prompt
        prompt = self.build_prompt(card_name, number, description, is_back)
        parts.append({"text": prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": temperature,
                "maxOutputTokens": 8192,
                "imageConfig": {
                    "aspectRatio": "3:4"  # Standard tarot proportions
                }
            }
        }

        try:
            print("   Generating...")
            response = requests.post(
                self.endpoint,
                headers=headers,
                json=payload,
                timeout=300
            )
            response.raise_for_status()
            result = response.json()

            # Save the generated card
            return self.save_card(result, card_name, number, is_back)

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = json.dumps(error_data, indent=2)
            except:
                error_detail = e.response.text
            print(f"Generation failed: {e}\n{error_detail}", file=sys.stderr)
            return None

        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}", file=sys.stderr)
            return None

    def save_card(
        self,
        response: Dict[str, Any],
        card_name: str,
        number: Optional[str],
        is_back: bool
    ) -> Optional[Path]:
        """Save the generated card image."""

        # Create filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = card_name.lower().replace(" ", "_").replace("'", "")

        if is_back:
            filename = f"card_back_{timestamp}.jpg"
        elif number:
            filename = f"{number.lower()}_{safe_name}_{timestamp}.jpg"
        else:
            filename = f"{safe_name}_{timestamp}.jpg"

        output_path = self.output_dir / filename

        try:
            candidates = response.get("candidates", [])

            for candidate in candidates:
                parts = candidate.get("content", {}).get("parts", [])

                for part in parts:
                    # Save any text commentary
                    if "text" in part:
                        text_path = output_path.with_suffix('.txt')
                        with open(text_path, 'w', encoding='utf-8') as f:
                            f.write(part["text"])
                        print(f"   Commentary: {text_path.name}")

                    # Save the image
                    if "inlineData" in part:
                        inline = part["inlineData"]
                        image_data = inline.get("data", "")

                        if image_data:
                            image_bytes = base64.b64decode(image_data)
                            with open(output_path, 'wb') as f:
                                f.write(image_bytes)
                            print(f"   Saved: {output_path}")
                            return output_path

            print("   No image in response")
            return None

        except Exception as e:
            print(f"Could not save card: {e}", file=sys.stderr)
            return None


# ============================================================================
# SESSION MANAGEMENT
# ============================================================================

class SessionManager:
    """Manage visual memory across multiple card generations."""

    def __init__(self, session_name: str, output_dir: Path):
        self.session_name = session_name
        self.session_dir = output_dir / "sessions" / session_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / ".session.json"

    def load_session(self) -> Dict:
        """Load session state."""
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                return json.load(f)
        return {"cards": [], "created": datetime.now().isoformat()}

    def save_session(self, state: Dict):
        """Save session state."""
        with open(self.session_file, 'w') as f:
            json.dump(state, f, indent=2)

    def add_card(self, card_path: Path) -> List[Path]:
        """Add a card to the session and return all session cards."""
        state = self.load_session()
        state["cards"].append(str(card_path))
        state["updated"] = datetime.now().isoformat()
        self.save_session(state)
        return [Path(p) for p in state["cards"]]

    def get_session_cards(self) -> List[Path]:
        """Get all cards in this session."""
        state = self.load_session()
        return [Path(p) for p in state["cards"] if Path(p).exists()]


# ============================================================================
# CLI
# ============================================================================

def cmd_card(args, generator: MinoanTarotGenerator):
    """Generate a single card."""
    print()
    print("=" * 60)
    print("  MINOAN TAROT GENERATOR")
    print("=" * 60)
    print()
    print(f"   Card: {args.name}")
    if args.number:
        print(f"   Number: {args.number}")
    if args.description:
        print(f"   Description: {args.description}")
    print()

    card_path = generator.generate_card(
        card_name=args.name,
        number=args.number,
        description=args.description,
        temperature=args.temperature
    )

    if card_path:
        print()
        print("=" * 60)
        print(f"  Card manifested: {card_path}")
        print("=" * 60)
    else:
        print("  Generation failed.")
        sys.exit(1)


def cmd_archetype(args, generator: MinoanTarotGenerator):
    """Generate a card from an archetype."""
    archetype = ARCHETYPES.get(args.type.lower())
    if not archetype:
        print(f"Unknown archetype: {args.type}", file=sys.stderr)
        print(f"Available: {', '.join(ARCHETYPES.keys())}")
        sys.exit(1)

    print()
    print("=" * 60)
    print("  MINOAN TAROT - ARCHETYPE")
    print("=" * 60)
    print()
    print(f"   Archetype: {args.type}")
    print(f"   Card: {archetype['name']}")
    print(f"   Description: {archetype['desc']}")
    print()

    card_path = generator.generate_card(
        card_name=archetype['name'],
        number=to_roman(archetype['number']),
        description=archetype['desc'],
        temperature=args.temperature
    )

    if card_path:
        print()
        print("=" * 60)
        print(f"  Card manifested: {card_path}")
        print("=" * 60)
    else:
        print("  Generation failed.")
        sys.exit(1)


def cmd_session(args, generator: MinoanTarotGenerator):
    """Continue a session with visual memory."""
    session = SessionManager(args.name, generator.output_dir)
    existing_cards = session.get_session_cards()

    print()
    print("=" * 60)
    print("  MINOAN TAROT - SESSION")
    print("=" * 60)
    print()
    print(f"   Session: {args.name}")
    print(f"   Previous cards: {len(existing_cards)}")
    print(f"   New card: {args.card}")
    print()

    card_path = generator.generate_card(
        card_name=args.card,
        number=args.number,
        description=args.description,
        session_images=existing_cards[-3:],  # Use last 3 for context
        temperature=args.temperature
    )

    if card_path:
        session.add_card(card_path)
        print()
        print("=" * 60)
        print(f"  Card added to session: {card_path}")
        print("=" * 60)
    else:
        print("  Generation failed.")
        sys.exit(1)


def cmd_back(args, generator: MinoanTarotGenerator):
    """Generate a card back design."""
    print()
    print("=" * 60)
    print("  MINOAN TAROT - CARD BACK")
    print("=" * 60)
    print()

    card_path = generator.generate_card(
        card_name="Card Back",
        is_back=True,
        temperature=args.temperature
    )

    if card_path:
        print()
        print("=" * 60)
        print(f"  Card back designed: {card_path}")
        print("=" * 60)
    else:
        print("  Generation failed.")
        sys.exit(1)


def cmd_list(args):
    """List all traditional tarot cards."""
    print()
    print("=" * 60)
    print("  MINOAN TAROT - 78 CARD DECK")
    print("=" * 60)
    print()

    print("MAJOR ARCANA (22 cards)")
    print("-" * 40)
    for num, name in MAJOR_ARCANA.items():
        roman = to_roman(num) if num > 0 else "0"
        print(f"  {roman:>4}  {name}")

    print()
    print("MINOR ARCANA (56 cards)")
    print("-" * 40)

    for suit_key, suit_name in SUITS.items():
        print(f"\n  {suit_name.upper()} (14 cards)")
        # Pip cards
        for i in range(1, 11):
            num_name = "Ace" if i == 1 else str(i)
            print(f"    {num_name} of {suit_name}")
        # Court cards
        for court_key, court_name in COURT.items():
            print(f"    {court_name} of {suit_name}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Generate tarot cards in the Minoan Tarot style",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--api-key", help="Gemini API key (or use GEMINI_API_KEY env)")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # card command
    card_parser = subparsers.add_parser("card", help="Generate a specific card")
    card_parser.add_argument("name", help="Card name (e.g., 'The Priestess')")
    card_parser.add_argument("--number", "-n", help="Roman numeral (e.g., II)")
    card_parser.add_argument("--description", "-d", help="Scene description")
    card_parser.add_argument("--temperature", "-t", type=float, default=0.5,
                            help="Temperature (default: 0.5 for faithful style)")

    # archetype command
    arch_parser = subparsers.add_parser("archetype", help="Generate from archetype")
    arch_parser.add_argument("type", help=f"Archetype: {', '.join(ARCHETYPES.keys())}")
    arch_parser.add_argument("--temperature", "-t", type=float, default=0.5)

    # session command
    sess_parser = subparsers.add_parser("session", help="Continue a session with visual memory")
    sess_parser.add_argument("name", help="Session name")
    sess_parser.add_argument("--card", "-c", required=True, help="Card to generate")
    sess_parser.add_argument("--number", "-n", help="Roman numeral")
    sess_parser.add_argument("--description", "-d", help="Scene description")
    sess_parser.add_argument("--temperature", "-t", type=float, default=0.5)

    # back command
    back_parser = subparsers.add_parser("back", help="Generate card back design")
    back_parser.add_argument("--temperature", "-t", type=float, default=0.5)

    # list command
    subparsers.add_parser("list", help="List all 78 traditional cards")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # List doesn't need API key
    if args.command == "list":
        cmd_list(args)
        return

    # Get API key
    api_key = args.api_key or os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("Requires GEMINI_API_KEY environment variable or --api-key", file=sys.stderr)
        sys.exit(1)

    # Initialize generator
    generator = MinoanTarotGenerator(api_key)

    # Dispatch to command
    if args.command == "card":
        cmd_card(args, generator)
    elif args.command == "archetype":
        cmd_archetype(args, generator)
    elif args.command == "session":
        cmd_session(args, generator)
    elif args.command == "back":
        cmd_back(args, generator)


if __name__ == "__main__":
    main()
