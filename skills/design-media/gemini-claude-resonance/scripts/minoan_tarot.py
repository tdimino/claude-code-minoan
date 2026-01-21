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

# Pre-built forensic prompts for analyzed cards (from MINOAN_TAROT_PROMPTS.md)
# These are forensically precise descriptions optimized for Gemini 3 Pro
KNOWN_CARD_PROMPTS = {
    "earth worker": """[Subject + Adjectives]: An athletic Minoan male figure with reddish-brown skin, long black curly hair, and a yellow loincloth.
[Action]: Grappling with a large, reddish-brown bull, grasping the bull by its long, curved yellow horns in a display of bull-leaping acrobatics.
[Location/Context]: A solid light blue background representing the sky.
[Composition/Camera Angle]: Full shot, flat profile view. The scene is framed by horizontal decorative bands at the top and bottom featuring a repeating oval pattern in red, white, teal, and yellow.
[Lighting/Atmosphere]: Even, flat lighting typical of fresco art; clear and iconic.
[Style/Media]: Minoan fresco painting style, gouache on paper texture.""",

    "sea priestess": """[Subject + Adjectives]: A bare-breasted Minoan woman with white skin, wearing a tiered skirt with red and yellow horizontal stripes and a small tiara.
[Action]: Standing in a crescent-shaped yellow boat with a bird-head prow, using a long paddle to steer.
[Location/Context]: A blue sea and sky background. Behind the boat are stylized yellow rock formations topped with a white shrine structure and green plants.
[Composition/Camera Angle]: Full shot, profile view.
[Lighting/Atmosphere]: Bright, maritime atmosphere.
[Style/Media]: Minoan fresco painting style.""",

    "sky master": """[Subject + Adjectives]: A reddish-brown skinned male figure wearing a tall, cylindrical blue headdress, a gold necklace, and a white kilt with a central decorated flap.
[Action]: Standing symmetrically, holding two large waterfowl (ducks or geese) by their long necks; the birds are patterned in green, blue, and orange.
[Location/Context]: A solid light blue background.
[Composition/Camera Angle]: Frontal, symmetrical composition. Three gold bird symbols hover at the top edge; three gold solar discs line the bottom edge.
[Lighting/Atmosphere]: Divine, authoritative, airy.
[Style/Media]: Minoan fresco painting style.""",

    "art mistress": """[Subject + Adjectives]: A seated Minoan woman with white skin wearing a long red dress and blue headdress, facing a standing "Minoan Genius" (a mythological anthropomorphic lion/hippo figure) with tawny skin and a scaled back-cape.
[Action]: The woman holds out a hand to receive a tall yellow chalice that the Genius figure is pouring or offering to her.
[Location/Context]: A pale yellow background.
[Composition/Camera Angle]: Profile view. A red solar symbol with spokes floats at the top center. The bottom features a red decorative band with vertical yellow wheat stalks.
[Lighting/Atmosphere]: Ritualistic, ceremonial, warm.
[Style/Media]: Minoan fresco painting style.""",

    "earth priestess": """[Subject + Adjectives]: A pale-skinned Minoan Snake Goddess figure with an exposed chest and a commanding expression.
[Action]: Standing in a rigid, frontal pose with arms extended outward to the sides, elbows bent at 90 degrees, gripping a writhing snake in each hand.
[Location/Context]: Placed against a solid, warm terracotta-orange background.
[Composition/Camera Angle]: Eye-level, full-body frontal portrait centered in the frame.
[Lighting/Atmosphere]: Even, flat illumination highlighting the geometric patterns of the clothing.
[Style/Media]: Archaeological illustration style, flat vector-like coloring.
[Details]: She wears a tall, cylindrical blue hat topped with a small brown animal (cat or weasel). Her bodice is fitted, red and blue with lacing below the exposed breasts. She wears a distinctive floor-length tiered skirt featuring horizontal bands of yellow and brown stripes, overlaid by a rounded, patterned double-apron.""",

    "lily prince": """[Subject + Adjectives]: An athletic Minoan youth (The Prince of the Lilies) with tanned bronze skin, a slender waist, and long, curly black hair flowing over his shoulders.
[Action]: He is striding confidently in profile toward the right, his left arm extended backward holding a long-stemmed yellow lily flower, while his right hand rests on his hip.
[Location/Context]: Set against a flat, vibrant, solid orange background.
[Composition/Camera Angle]: Full-body profile view, centered strictly within the frame.
[Lighting/Atmosphere]: Flat, illustrative lighting with no cast shadows, evoking the aesthetic of a preserved wall fresco.
[Style/Media]: Minoan fresco reproduction style using gouache or tempera textures.
[Details]: He wears an ornate headdress featuring a large yellow plume and peacock feathers, a gold necklace, armbands, and a complex blue and gold loincloth with a codpiece. A decorative horizontal band with a geometric pattern runs near his feet.""",

    "the fool": """[Subject + Adjectives]: An athletic Minoan youth (The Prince of the Lilies) with tanned bronze skin, a slender waist, and long, curly black hair flowing over his shoulders.
[Action]: He is striding confidently in profile toward the right, his left arm extended backward holding a long-stemmed yellow lily flower, while his right hand rests on his hip.
[Location/Context]: Set against a flat, vibrant, solid orange background.
[Composition/Camera Angle]: Full-body profile view, centered strictly within the frame.
[Lighting/Atmosphere]: Flat, illustrative lighting with no cast shadows, evoking the aesthetic of a preserved wall fresco.
[Style/Media]: Minoan fresco reproduction style using gouache or tempera textures.
[Details]: He wears an ornate headdress featuring a large yellow plume and peacock feathers, a gold necklace, armbands, and a complex blue and gold loincloth with a codpiece. A decorative horizontal band with a geometric pattern runs near his feet.""",

    "the chariot": """[Subject + Adjectives]: A stylized Minoan profile figure with long black curly hair, wearing a blue bodice and yellow skirt, driving a yellow chariot drawn by two mythological griffins with cream bodies and blue-and-yellow wings.
[Action]: The griffins are marching in tandem to the left, while the charioteer holds reins, standing atop a large four-spoked wheel colored in yellow, red, and blue concentric circles.
[Location/Context]: Solid, vibrant red background.
[Composition/Camera Angle]: Flat, two-dimensional profile view. Framed by horizontal bands of blue rosettes on yellow at top and bottom.
[Lighting/Atmosphere]: Triumphant, driven, bold. Bright, flat, uniform lighting with no shadows.
[Style/Media]: Ancient Minoan fresco art style, using primary colors of terracotta red, ochre yellow, and turquoise blue.""",

    "strength": """[Subject + Adjectives]: An androgynous figure wearing a tall blue conical hat and blue tunic, standing next to a large lion.
[Action]: The figure holds a tall staff and gently touches the lion's head; the lion stands calmly on a leash.
[Location/Context]: An orange/terracotta background.
[Composition/Camera Angle]: Profile view. Framed by decorative bands of blue and yellow leaves/vines at the top and bottom.
[Lighting/Atmosphere]: Controlled, powerful, calm.
[Style/Media]: Minoan fresco painting style.""",

    "wheel of life": """[Subject + Adjectives]: An abstract geometric symbol featuring a large central turquoise circle containing a quadruple spiral (tetraskelion) motif in a lighter blue.
[Action]: Static, centered.
[Location/Context]: Solid terracotta red background, with four small turquoise crescent moon shapes nestled in the four corners of the red field.
[Composition/Camera Angle]: Top-down, flat geometric composition.
[Lighting/Atmosphere]: Flat, graphic lighting.
[Style/Media]: Ancient symbolic minimalism, bold and flat color fields.""",

    "wheel of fortune": """[Subject + Adjectives]: An abstract geometric symbol featuring a large central turquoise circle containing a quadruple spiral (tetraskelion) motif in a lighter blue.
[Action]: Static, centered.
[Location/Context]: Solid terracotta red background, with four small turquoise crescent moon shapes nestled in the four corners of the red field.
[Composition/Camera Angle]: Top-down, flat geometric composition.
[Lighting/Atmosphere]: Flat, graphic lighting.
[Style/Media]: Ancient symbolic minimalism, bold and flat color fields.""",

    "the sun": """[Subject + Adjectives]: Two women with white skin, black curly hair, and ornate patterned skirts (one blue/yellow, one red/blue).
[Action]: Sitting on the ground facing each other, engaged in conversation, with one hand resting on the ground and the other gesturing.
[Location/Context]: A cream background representing a floor or terrace.
[Composition/Camera Angle]: Profile view. Framed by stylized red and blue floral/cloud bands at the top and bottom.
[Lighting/Atmosphere]: Social, bright, peaceful.
[Style/Media]: Minoan fresco painting style.""",

    "transcendence": """[Subject + Adjectives]: A mythological Griffin (body of a lion, head/wings of an eagle) painted in yellow and red, and a small female figure.
[Action]: The griffin is leaping or flying mid-air toward the left; the small female figure floats effortlessly above the griffin's back, arms outstretched.
[Location/Context]: A solid, light sky-blue background.
[Composition/Camera Angle]: Side profile view of the creatures in motion.
[Lighting/Atmosphere]: Bright, airy, daylight atmosphere.
[Style/Media]: Ancient fresco style with bold outlines.
[Details]: The griffin has a yellow body, a red crested head, and wings detailed with red feathers. The woman wears a tiered yellow and red skirt and a blue bodice.""",

    "judgement": """[Subject + Adjectives]: A mythological Griffin (body of a lion, head/wings of an eagle) painted in yellow and red, and a small female figure.
[Action]: The griffin is leaping or flying mid-air toward the left; the small female figure floats effortlessly above the griffin's back, arms outstretched.
[Location/Context]: A solid, light sky-blue background.
[Composition/Camera Angle]: Side profile view of the creatures in motion.
[Lighting/Atmosphere]: Bright, airy, daylight atmosphere.
[Style/Media]: Ancient fresco style with bold outlines.
[Details]: The griffin has a yellow body, a red crested head, and wings detailed with red feathers. The woman wears a tiered yellow and red skirt and a blue bodice.""",

    "world tree": """[Subject + Adjectives]: A large, gnarled, terracotta-orange tree with thick stylized branches hosting small human figures in red and yellow loincloths.
[Action]: The figures are climbing the limbs and dancing at the roots. A yellow lion-like creature rests on a horizontal platform structure within the upper branches.
[Location/Context]: Deep indigo blue background.
[Composition/Camera Angle]: Full vertical shot, centered composition.
[Lighting/Atmosphere]: Mystic, nocturnal atmosphere with deep saturation.
[Style/Media]: Primitive folk art style with flat perspective and bold color blocking.""",

    "the world": """[Subject + Adjectives]: A large, gnarled, terracotta-orange tree with thick stylized branches hosting small human figures in red and yellow loincloths.
[Action]: The figures are climbing the limbs and dancing at the roots. A yellow lion-like creature rests on a horizontal platform structure within the upper branches.
[Location/Context]: Deep indigo blue background.
[Composition/Camera Angle]: Full vertical shot, centered composition.
[Lighting/Atmosphere]: Mystic, nocturnal atmosphere with deep saturation.
[Style/Media]: Primitive folk art style with flat perspective and bold color blocking.""",
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

# Color palette - forensically extracted from reference cards
MINOAN_COLORS = {
    "terracotta_red": "#C84C3C",      # Backgrounds, clothing, decorative bands
    "ochre_yellow": "#D4A542",         # Clothing, bulls, decorative elements
    "slate_blue": "#4A5D7A",           # Sky backgrounds, clothing
    "teal_turquoise": "#3D9CA8",       # Sea backgrounds, spirals, accents
    "cream": "#F5E6D0",                # Backgrounds, female skin
    "periwinkle_border": "#6B7DB3",    # Card borders (thick outer frame)
    "male_skin": "#8B4513",            # Reddish-brown male skin
    "female_skin": "#FFF8F0",          # White/pale female skin
    "deep_indigo": "#2C3E5C",          # Night backgrounds
    "violet_purple": "#6B4C8C",        # Ritual/mystical backgrounds
    "lime_green": "#7CB342",           # Nature backgrounds
    "black": "#000000",                # Bold outlines
}

MINOAN_SYSTEM_PROMPT = """The artistic style mimics ancient Minoan frescoes from Knossos and Akrotiri. It features flat two-dimensional perspective, profile faces with frontal eyes, bold outlines, and a specific color palette:

COLOR PALETTE (use these exact hex values):
- Terracotta Red (#C84C3C) - Backgrounds, clothing, decorative bands
- Ochre Yellow (#D4A542) - Clothing, bulls, decorative elements
- Slate Blue (#4A5D7A) - Sky backgrounds, clothing
- Teal/Turquoise (#3D9CA8) - Sea backgrounds, spirals, accents
- Cream (#F5E6D0) - Backgrounds, female skin
- Periwinkle Blue (#6B7DB3) - Card borders (thick outer frame)
- Reddish-Brown (#8B4513) - Male skin
- White/Pale (#FFF8F0) - Female skin
- Deep Indigo (#2C3E5C) - Night/mystical backgrounds
- Black (#000000) - All bold outlines

FIGURE CONVENTIONS:
- Figures have pinched waists and stylized elongated proportions
- Men typically have reddish-brown skin; women have white/pale skin
- Profile faces with frontal eyes (Egyptian-style poses)
- Bare-breasted women in tiered flounced skirts (common Minoan dress)
- Men in loincloths or kilts

CARD STRUCTURE:
- Thick periwinkle-blue border (#6B7DB3) around entire card
- Decorative horizontal bands at top and bottom (rosettes, spirals, waves, wheat)
- Card title in white sans-serif font at the bottom of the border
- Main imagery against solid color background (slate blue, terracotta, cream, or themed)

MINOAN ICONOGRAPHY:
- Labrys (double-headed axe)
- Horns of Consecration
- Snake Goddess (frontal pose, arms holding serpents)
- Bull leaping / bull heads with curved horns
- Dolphins, octopi (Marine Style)
- Griffins (lion body, eagle head/wings)
- Swallows in spiral flight
- Sacred lilies, papyrus, olive branches
- Spiral motifs (running spirals, tetraskelion)

ARTISTIC STYLE:
- Flat colors - NO gradients, NO shading, NO 3D effects, NO photorealism
- Colors are solid blocks like ancient frescoes or gouache on paper
- Bold black outlines around every figure, object, and shape
- Flat, even lighting with no cast shadows
- Two-dimensional composition typical of fresco art"""


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
        """Build the generation prompt for a specific card using Gemini 3 Pro formula.

        For known cards (analyzed from reference images), uses forensically precise prompts.
        For new cards, generates structured prompts using the Gemini 3 Pro formula.
        """

        if is_back:
            return f"""{MINOAN_SYSTEM_PROMPT}

GENERATE: Card Back Design

[Subject + Adjectives]: A symmetrical sacred design featuring a large central Labrys (double-headed axe) in gold/ochre yellow (#D4A542) with intricate carved details.

[Action]: The Labrys stands vertically as the central focal point, radiating sacred energy.

[Location/Context]: Set against a deep indigo (#2C3E5C) or terracotta red (#C84C3C) background.

[Composition/Camera Angle]: Perfectly symmetrical, mandala-like arrangement. The Labrys is surrounded by concentric bands of decorative patterns: running spirals, rosettes, and wave motifs in teal (#3D9CA8), ochre (#D4A542), and cream (#F5E6D0).

[Lighting/Atmosphere]: Flat, even illumination with no shadows. Sacred and iconic.

[Style/Media]: Minoan fresco style with bold black outlines, flat color blocks, gouache texture. Thick periwinkle-blue border (#6B7DB3) around entire card. This design appears on ALL card backs in the deck."""

        # Build card-specific prompt using the Gemini 3 Pro formula
        title_line = f"{number} {card_name.upper()}" if number else card_name.upper()

        # Check for known card with forensic prompt (case-insensitive lookup)
        card_key = card_name.lower().strip()
        if card_key in KNOWN_CARD_PROMPTS:
            known_prompt = KNOWN_CARD_PROMPTS[card_key]
            return f"""{MINOAN_SYSTEM_PROMPT}

GENERATE: {title_line}

{known_prompt}

[Border]: Thick periwinkle-blue outer border (#6B7DB3) with "{title_line}" in white sans-serif font at the bottom.

CRITICAL: Match the reference images exactly. This is a forensically precise description - reproduce it faithfully."""

        # If description provided, use it to build a structured prompt
        if description:
            return f"""{MINOAN_SYSTEM_PROMPT}

GENERATE: {title_line}

[Subject + Adjectives]: {description}

[Location/Context]: Appropriate solid color background - slate blue (#4A5D7A) for sky/air themes, teal (#3D9CA8) for sea themes, terracotta red (#C84C3C) for earth themes, cream (#F5E6D0) for neutral.

[Composition/Camera Angle]: Full shot, flat profile or frontal view typical of Minoan fresco art. Framed by horizontal decorative bands at top and bottom featuring running spirals, rosettes, wave patterns, or wheat motifs in complementary colors.

[Lighting/Atmosphere]: Flat, even lighting with no cast shadows, evoking the aesthetic of preserved wall frescoes.

[Style/Media]: Ancient Minoan fresco style using gouache or tempera textures. Bold black outlines around all figures and objects. Flat color blocks with no gradients.

[Border]: Thick periwinkle-blue outer border (#6B7DB3) with "{title_line}" in white sans-serif font at the bottom.

CRITICAL: Match the reference images exactly - same flat color treatment, same bold outlines, same decorative patterns. This card must look like it belongs in Ellen Lorenzi-Prince's Minoan Tarot deck."""

        # Generic prompt when no description provided
        return f"""{MINOAN_SYSTEM_PROMPT}

GENERATE: {title_line}

[Subject + Adjectives]: Create a scene appropriate for the "{card_name}" tarot card using Minoan Bronze Age imagery. Include appropriate figures (Minoan men with reddish-brown skin #8B4513, women with pale skin #FFF8F0), animals (bulls, griffins, dolphins, octopi), or sacred symbols (labrys, snakes, lilies).

[Action]: The subject should embody the meaning of "{card_name}" through gesture, composition, or symbolic arrangement.

[Location/Context]: Solid color background appropriate to the card's element and meaning - slate blue (#4A5D7A), terracotta red (#C84C3C), cream (#F5E6D0), teal (#3D9CA8), or deep indigo (#2C3E5C).

[Composition/Camera Angle]: Full shot, flat profile or frontal view. Framed by horizontal decorative bands at top and bottom featuring Minoan patterns (spirals, rosettes, waves).

[Lighting/Atmosphere]: Flat, even illumination typical of fresco art. No cast shadows.

[Style/Media]: Ancient Minoan fresco style. Bold black outlines, flat color blocks, gouache texture. Profile faces with frontal eyes, pinched waists, stylized proportions.

[Border]: Thick periwinkle-blue outer border (#6B7DB3) with "{title_line}" in white sans-serif font at the bottom.

CRITICAL: Match the reference images exactly. This card must look like it belongs in Ellen Lorenzi-Prince's Minoan Tarot deck."""

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
