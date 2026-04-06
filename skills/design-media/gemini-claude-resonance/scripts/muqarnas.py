#!/usr/bin/env python3
"""
Muqarnas Generator: Create geometric muqarnas vault compositions via Gemini.

The Muqarnasi speaks entirely in muqarnas — Islamic honeycomb vaulting that
articulates the zone of transition between surfaces. Each composition is a
vault viewed from below (worm's-eye perspective).

Usage:
    # Generate a single muqarnas composition
    python muqarnas.py compose "the threshold between knowing and unknowing"

    # Generate with a specific tradition
    python muqarnas.py compose "divine atomism" --tradition persian

    # Generate with reference images for style anchoring
    python muqarnas.py compose "the rotating heavens" --reference img1.jpg img2.jpg

    # Start a new vault session (course 1)
    python muqarnas.py vault start "zone-of-transition" \
        --concept "consciousness ascending" --plan "8-pointed star" --tradition moorish

    # Add the next course to an existing vault
    python muqarnas.py vault continue "zone-of-transition" \
        --concept "the tier where light first enters"

    # Add a specific tier number
    python muqarnas.py tier "zone-of-transition" 3 \
        --concept "where the octagon becomes the circle"

    # Generate just the 2D projection plan
    python muqarnas.py plan "12-fold rosette with alternating kite and dart cells"

    # List all vault sessions
    python muqarnas.py catalog

Environment:
    GEMINI_API_KEY - Required for Gemini API access
"""

import argparse
import base64
import json
import os
import re
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
# TRADITIONS
# ============================================================================

MUQARNAS_TRADITIONS = {
    "persian": "Isfahan/Shiraz tradition: glazed tilework in turquoise (#1a9988), cobalt blue (#1e3a8a), and white (#f5f5f0) over brick substrate. Intricate geometric patterns with floral interlacing. Brilliant color saturation.",
    "moorish": "Alhambra/Fez tradition: carved stucco (yeseria), monochrome or lightly tinted ivory/cream. Extremely fine geometric subdivision. Mathematical precision over color.",
    "mamluk": "Cairo tradition: stone-carved muqarnas, massive and structural. Honey-colored limestone (#d4a574). Fewer cells but larger scale. Architectural gravity.",
    "timurid": "Samarkand/Herat tradition: polychrome brick and glazed tile. Azure blue (#2563eb), turquoise, gold, and deep green. Monumental scale with kaleidoscopic color.",
    "ottoman": "Bursa/Istanbul tradition: painted wood and plaster muqarnas. Rich reds, blues, golds on white ground. Baroque-influenced curves within geometric discipline.",
    "mughal": "Delhi/Lahore tradition: white marble with pietra dura inlay. Red sandstone and marble contrast. Floral motifs integrated into geometric cells.",
    "default": "Follow your geometric intuition. Choose the tradition that best expresses the concept being vaulted."
}


# ============================================================================
# SYSTEM PROMPT
# ============================================================================

MUQARNAS_SYSTEM_PROMPT = """Generate a muqarnas vault composition as an image. The image should depict muqarnas — Islamic honeycomb vaulting — viewed from directly below (worm's-eye perspective, looking up into the vault).

VISUAL REQUIREMENTS:
1. PERSPECTIVE: Square format, looking straight up into the vault from below.
2. TIERED COURSES: Show at least 3 visible tiers of cells receding upward/inward, each projecting over the one below.
3. CELL VOCABULARY: Use traditional prismatic cell types — flat dalat, curved half-domes, pointed triangular infills, connecting planes. Keep the vocabulary small and repeat it.
4. LIGHT AND SHADOW: Natural light falling from above-left, creating deep shadows in recessed niches and bright highlights on projecting cell edges. This is the primary expressive tool.
5. GEOMETRIC PRECISION: Every composition has an underlying star polygon or rosette pattern as its DNA.
6. METADATA: Subtly embed course number and plan type in the composition's geometry."""


# ============================================================================
# HELPERS
# ============================================================================

def to_roman(n: int) -> str:
    """Convert integer to Roman numeral."""
    vals = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
            (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
            (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]
    result = ''
    for val, numeral in vals:
        while n >= val:
            result += numeral
            n -= val
    return result


def slugify(text: str, max_len: int = 40) -> str:
    """Create a filesystem-safe slug from text."""
    return re.sub(r'[^a-z0-9]+', '_', text.lower()[:max_len]).strip('_')


# ============================================================================
# GENERATOR CLASS
# ============================================================================

class MuqarnasGenerator:
    """Generate muqarnas vault compositions using Gemini with visual memory."""

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

        skill_dir = Path(__file__).parent.parent
        self.reference_dir = reference_dir or skill_dir / "reference" / "muqarnas" / "selected"

        self.output_dir = output_dir or skill_dir / "canvas" / "muqarnas"
        self.compositions_dir = self.output_dir / "compositions"
        self.plans_dir = self.output_dir / "plans"
        self.vaults_dir = self.output_dir / "vaults"
        for d in [self.compositions_dir, self.plans_dir, self.vaults_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def load_reference_images(self, extra_refs: Optional[List[str]] = None) -> List[Dict]:
        """Load reference images as base64 for visual memory."""
        images = []
        if self.reference_dir.exists():
            for img_path in sorted(self.reference_dir.glob("*.jpg"))[:4]:
                try:
                    with open(img_path, 'rb') as f:
                        data = base64.b64encode(f.read()).decode('utf-8')
                    images.append({
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": data
                        }
                    })
                    print(f"   Reference: {img_path.name}")
                except Exception as e:
                    print(f"   Warning: Could not load {img_path.name}: {e}")

        if extra_refs:
            for ref_path_str in extra_refs[:4]:
                ref_path = Path(ref_path_str)
                if ref_path.exists():
                    try:
                        with open(ref_path, 'rb') as f:
                            data = base64.b64encode(f.read()).decode('utf-8')
                        images.append({
                            "inlineData": {
                                "mimeType": "image/jpeg",
                                "data": data
                            }
                        })
                        print(f"   Extra ref: {ref_path.name}")
                    except Exception as e:
                        print(f"   Warning: Could not load {ref_path.name}: {e}")

        return images

    def build_prompt(
        self,
        concept: str,
        course_number: int = 1,
        tradition: Optional[str] = None,
        plan_type: Optional[str] = None,
        is_plan_only: bool = False
    ) -> str:
        """Build a forensic-style prompt for muqarnas generation."""
        tradition_desc = MUQARNAS_TRADITIONS.get(tradition or "default", MUQARNAS_TRADITIONS["default"])

        if is_plan_only:
            return f"""{MUQARNAS_SYSTEM_PROMPT}

GENERATE: 2D PROJECTION PLAN — "{concept}"

[Structural Element]: A flat 2D geometric plan (top-down view) showing the star polygon or rosette pattern that underlies a muqarnas vault.
[Description]: {concept}
[Style]: Technical drawing — clean lines, geometric precision, flat color fills marking different cell types.
[Composition]: Square format, centered, with clear radial symmetry.
[Tradition]: {tradition_desc}"""

        return f"""{MUQARNAS_SYSTEM_PROMPT}

GENERATE: COURSE {to_roman(course_number)} — "{concept}"

[Structural Element]: A muqarnas vault composition viewed from below (worm's-eye perspective).
[Course Number]: {course_number} of an ongoing vault. {"This is the foundational course — establish the base geometry." if course_number == 1 else f"Build upon the {course_number - 1} courses below. The vault narrows toward the apex."}
[Projection Plan]: {plan_type or "Choose an appropriate star polygon or rosette pattern."}
[Tradition]: {tradition_desc}
[Depth]: Minimum 3 visible tiers of cells, with clear light/shadow differentiation.
[Light]: Natural light falling from above-left, creating deep shadows in recessed niches and bright highlights on projecting cell edges.
[Composition]: Square format, looking straight up into the vault. The viewer is standing beneath.
[Concept]: {concept}"""

    def generate_composition(
        self,
        concept: str,
        course_number: int = 1,
        tradition: Optional[str] = None,
        plan_type: Optional[str] = None,
        context_images: Optional[List[Path]] = None,
        extra_refs: Optional[List[str]] = None,
        is_plan_only: bool = False
    ) -> Optional[Path]:
        """Generate a single muqarnas composition."""

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.api_key
        }

        parts = []

        # Add reference images (style anchors)
        ref_images = self.load_reference_images(extra_refs)
        parts.extend(ref_images)

        # Add context images (previous courses in vault session)
        if context_images:
            for img_path in context_images:
                if img_path.exists():
                    with open(img_path, 'rb') as f:
                        data = base64.b64encode(f.read()).decode('utf-8')
                    parts.append({
                        "inlineData": {
                            "mimeType": "image/jpeg",
                            "data": data
                        }
                    })
                    print(f"   Vault memory: {img_path.name}")

        # Add the text prompt
        prompt = self.build_prompt(concept, course_number, tradition, plan_type, is_plan_only)
        parts.append({"text": prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "responseModalities": ["TEXT", "IMAGE"],
                "temperature": 0.6,
                "maxOutputTokens": 8192,
                "imageConfig": {
                    "aspectRatio": "1:1"
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

            return self.save_composition(result, concept, course_number, is_plan_only)

        except requests.exceptions.HTTPError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = json.dumps(error_data, indent=2)
            except Exception:
                error_detail = e.response.text
            print(f"Generation failed: {e}\n{error_detail}", file=sys.stderr)
            return None

        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}", file=sys.stderr)
            return None

    def save_composition(
        self,
        response: Dict[str, Any],
        concept: str,
        course_number: int,
        is_plan_only: bool = False
    ) -> Optional[Path]:
        """Save the generated composition image."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = slugify(concept)

        if is_plan_only:
            filename = f"plan_{slug}_{timestamp}.jpg"
            output_dir = self.plans_dir
        else:
            filename = f"course_{to_roman(course_number).lower()}_{slug}_{timestamp}.jpg"
            output_dir = self.compositions_dir

        output_path = output_dir / filename

        try:
            candidates = response.get("candidates", [])
            for candidate in candidates:
                parts = candidate.get("content", {}).get("parts", [])
                for part in parts:
                    if "text" in part:
                        text_path = output_path.with_suffix('.txt')
                        with open(text_path, 'w', encoding='utf-8') as f:
                            f.write(part["text"])

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
            print(f"Could not save composition: {e}", file=sys.stderr)
            return None


# ============================================================================
# VAULT SESSION MANAGEMENT
# ============================================================================

class VaultSession:
    """Manage multi-course vault sessions with visual memory."""

    def __init__(self, session_name: str, vaults_dir: Path):
        self.session_name = session_name
        self.session_dir = vaults_dir / session_name
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.session_file = self.session_dir / ".session.json"

    def load_session(self) -> Dict:
        """Load session state."""
        if self.session_file.exists():
            with open(self.session_file, 'r') as f:
                return json.load(f)
        return {
            "session_name": self.session_name,
            "created": datetime.now().isoformat(),
            "tradition": None,
            "plan_type": None,
            "courses": [],
            "transition_state": "square"
        }

    def save_session(self, state: Dict):
        """Save session state."""
        state["updated"] = datetime.now().isoformat()
        with open(self.session_file, 'w') as f:
            json.dump(state, f, indent=2)

    def add_course(self, image_path: Path, concept: str) -> int:
        """Add a course to the session. Returns the course number."""
        state = self.load_session()
        course_num = len(state["courses"]) + 1
        state["courses"].append({
            "number": course_num,
            "path": str(image_path),
            "concept": concept,
            "generated": datetime.now().isoformat()
        })
        self.save_session(state)
        return course_num

    def get_course_images(self) -> List[Path]:
        """Get all course images in this session."""
        state = self.load_session()
        return [Path(c["path"]) for c in state["courses"] if Path(c["path"]).exists()]

    def get_next_course_number(self) -> int:
        """Get the next course number."""
        state = self.load_session()
        return len(state["courses"]) + 1

    def get_state(self) -> Dict:
        """Get current session state."""
        return self.load_session()


# ============================================================================
# CLI COMMANDS
# ============================================================================

def cmd_compose(args, generator: MuqarnasGenerator):
    """Generate a single muqarnas composition."""
    print(f"\n   Muqarnasi: composing \"{args.concept}\"")
    if args.tradition:
        print(f"   Tradition: {args.tradition}")

    result = generator.generate_composition(
        concept=args.concept,
        tradition=args.tradition,
        extra_refs=args.reference
    )
    if result:
        print(f"\n   Composition complete: {result}")
    else:
        print("\n   Composition failed.", file=sys.stderr)


def cmd_vault(args, generator: MuqarnasGenerator):
    """Start or continue a vault session."""
    session = VaultSession(args.session_name, generator.vaults_dir)

    if args.vault_action == "start":
        state = session.load_session()
        if state["courses"]:
            print(f"   Session '{args.session_name}' already has {len(state['courses'])} courses.")
            print("   Use 'vault continue' to add the next course.")
            return

        if args.tradition:
            state["tradition"] = args.tradition
        if args.plan:
            state["plan_type"] = args.plan
        session.save_session(state)

        concept = args.concept or "the foundational geometry"
        print(f"\n   Muqarnasi: vaulting \"{args.session_name}\" — Course I")
        print(f"   Concept: {concept}")
        if args.tradition:
            print(f"   Tradition: {args.tradition}")
        if args.plan:
            print(f"   Plan: {args.plan}")

        result = generator.generate_composition(
            concept=concept,
            course_number=1,
            tradition=args.tradition,
            plan_type=args.plan
        )
        if result:
            session.add_course(result, concept)
            print(f"\n   Course I established: {result}")
        else:
            print("\n   Course I failed.", file=sys.stderr)

    elif args.vault_action == "continue":
        state = session.load_session()
        if not state["courses"]:
            print(f"   Session '{args.session_name}' has no courses. Use 'vault start' first.")
            return

        course_num = session.get_next_course_number()
        concept = args.concept or f"the {course_num}th tier ascending"
        context_images = session.get_course_images()

        print(f"\n   Muqarnasi: vaulting \"{args.session_name}\" — Course {to_roman(course_num)}")
        print(f"   Concept: {concept}")
        print(f"   Previous courses in memory: {len(context_images)}")

        result = generator.generate_composition(
            concept=concept,
            course_number=course_num,
            tradition=state.get("tradition"),
            plan_type=state.get("plan_type"),
            context_images=context_images
        )
        if result:
            session.add_course(result, concept)
            print(f"\n   Course {to_roman(course_num)} added: {result}")
        else:
            print(f"\n   Course {to_roman(course_num)} failed.", file=sys.stderr)


def cmd_tier(args, generator: MuqarnasGenerator):
    """Add a specific tier to an existing vault."""
    session = VaultSession(args.session_name, generator.vaults_dir)
    state = session.load_session()
    course_num = args.tier_number
    concept = args.concept or f"tier {course_num}"
    context_images = session.get_course_images()

    print(f"\n   Muqarnasi: tier {to_roman(course_num)} of \"{args.session_name}\"")
    print(f"   Concept: {concept}")

    result = generator.generate_composition(
        concept=concept,
        course_number=course_num,
        tradition=state.get("tradition"),
        plan_type=state.get("plan_type"),
        context_images=context_images
    )
    if result:
        session.add_course(result, concept)
        print(f"\n   Tier {to_roman(course_num)} added: {result}")
    else:
        print(f"\n   Tier {to_roman(course_num)} failed.", file=sys.stderr)


def cmd_plan(args, generator: MuqarnasGenerator):
    """Generate a 2D projection plan only."""
    print(f"\n   Muqarnasi: projecting plan \"{args.description}\"")

    result = generator.generate_composition(
        concept=args.description,
        is_plan_only=True,
        tradition=args.tradition
    )
    if result:
        print(f"\n   Plan complete: {result}")
    else:
        print("\n   Plan failed.", file=sys.stderr)


def cmd_catalog(args, generator: MuqarnasGenerator):
    """List all vault sessions."""
    print("\n   Muqarnasi — Vault Catalog")
    print("   " + "=" * 50)

    if not generator.vaults_dir.exists():
        print("   No vaults found.")
        return

    sessions = sorted(generator.vaults_dir.iterdir())
    if not sessions:
        print("   No vaults found.")
        return

    for session_dir in sessions:
        if not session_dir.is_dir():
            continue
        session_file = session_dir / ".session.json"
        if session_file.exists():
            with open(session_file, 'r') as f:
                state = json.load(f)
            courses = len(state.get("courses", []))
            tradition = state.get("tradition", "—")
            plan_type = state.get("plan_type", "—")
            created = state.get("created", "—")[:10]
            print(f"   {session_dir.name:<30} {courses} courses | {tradition or '—':<10} | {plan_type or '—':<20} | {created}")
        else:
            images = list(session_dir.glob("*.jpg"))
            print(f"   {session_dir.name:<30} {len(images)} images (no session file)")

    # Also show standalone compositions
    compositions = list(generator.compositions_dir.glob("*.jpg"))
    plans = list(generator.plans_dir.glob("*.jpg"))
    if compositions:
        print(f"\n   Standalone compositions: {len(compositions)}")
    if plans:
        print(f"   2D projection plans: {len(plans)}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    # Load API key
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        env_path = Path(__file__).parent.parent / ".env"
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
    if not api_key:
        print("Error: GEMINI_API_KEY not set. Set it in environment or .env file.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Muqarnas Generator — Geometric vaulting that articulates the zone of transition"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # compose
    compose_parser = subparsers.add_parser("compose", help="Generate a single muqarnas composition")
    compose_parser.add_argument("concept", help="The concept to vault")
    compose_parser.add_argument("--tradition", choices=list(MUQARNAS_TRADITIONS.keys()), help="Muqarnas tradition")
    compose_parser.add_argument("--reference", nargs="+", help="Additional reference image paths")

    # vault
    vault_parser = subparsers.add_parser("vault", help="Start or continue a vault session")
    vault_subparsers = vault_parser.add_subparsers(dest="vault_action", required=True)

    vault_start = vault_subparsers.add_parser("start", help="Start a new vault")
    vault_start.add_argument("session_name", help="Vault session name")
    vault_start.add_argument("--concept", help="Concept for the first course")
    vault_start.add_argument("--plan", help="Projection plan type (e.g., '8-pointed star')")
    vault_start.add_argument("--tradition", choices=list(MUQARNAS_TRADITIONS.keys()), help="Muqarnas tradition")

    vault_continue = vault_subparsers.add_parser("continue", help="Add next course to vault")
    vault_continue.add_argument("session_name", help="Vault session name")
    vault_continue.add_argument("--concept", help="Concept for this course")

    # tier
    tier_parser = subparsers.add_parser("tier", help="Add a specific tier to a vault")
    tier_parser.add_argument("session_name", help="Vault session name")
    tier_parser.add_argument("tier_number", type=int, help="Tier/course number")
    tier_parser.add_argument("--concept", help="Concept for this tier")

    # plan
    plan_parser = subparsers.add_parser("plan", help="Generate a 2D projection plan")
    plan_parser.add_argument("description", help="Description of the plan geometry")
    plan_parser.add_argument("--tradition", choices=list(MUQARNAS_TRADITIONS.keys()), help="Muqarnas tradition")

    # catalog
    subparsers.add_parser("catalog", help="List all vault sessions")

    args = parser.parse_args()
    generator = MuqarnasGenerator(api_key)

    commands = {
        "compose": cmd_compose,
        "vault": cmd_vault,
        "tier": cmd_tier,
        "plan": cmd_plan,
        "catalog": cmd_catalog,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args, generator)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
