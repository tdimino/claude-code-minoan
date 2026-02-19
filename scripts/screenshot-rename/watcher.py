#!/usr/bin/env python3
"""Screenshot Auto-Rename Daemon.

Triggered by launchd WatchPaths when the screenshots directory changes.
Scans for CleanShot/macOS screenshots, describes them with a vision model,
and renames to YYYY-MM-DD-slug[@Nx].ext.

Usage:
    python watcher.py                      # Process all pending screenshots
    python watcher.py --test path.png      # Test mode: process one file
    python watcher.py --provider openai    # Override provider
    python watcher.py --dry-run            # Preview renames without executing
"""

import argparse
import base64
import fcntl
import io
import logging
import os
import re
import sys
import time
import unicodedata
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).parent
WATCH_DIR = Path.home() / "Desktop" / "Screencaps & Chats" / "Screenshots"
INDEX_PATH = WATCH_DIR / "INDEX.md"
LOG_PATH = SCRIPT_DIR / "logs" / "screenshot-rename.log"

CLEANSHOT_RE = re.compile(
    r"^CleanShot (\d{4}-\d{2}-\d{2}) at (\d{2})\.(\d{2})\.(\d{2})(@\d+x)?\.(\w+)$"
)
MACOS_SCREENSHOT_RE = re.compile(
    r"^Screenshot (\d{4}-\d{2}-\d{2}) at (\d{2})\.(\d{2})\.(\d{2})(@\d+x)?\.(\w+)$"
)

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
VIDEO_EXTS = {".mp4", ".gif", ".mov"}

VISION_PROMPT = (
    "Describe this screenshot in 3-8 words for a filename. "
    "Focus on the main subject: app name, content type, or key visual element. "
    "Be specific: include app names, visible text, data types. "
    "Never say 'screenshot', 'image', or 'photo'. "
    "Return ONLY the description, no quotes or punctuation."
)

SYSTEM_PROMPT = (
    "You are a file naming assistant. You receive screenshots and output ONLY "
    "a short descriptive filename slug.\n"
    "Rules:\n"
    "- 3 to 8 words, lowercase, separated by hyphens\n"
    "- Describe the CONTENT, not the medium\n"
    "- Be specific: include app names, visible text, data types\n"
    "- No articles (a, an, the), no file extensions\n"
    "- Output ONLY the slug, nothing else\n"
    "Examples:\n"
    "- vscode-python-debugger-breakpoints\n"
    "- slack-team-standup-thread\n"
    "- chrome-github-pull-request-diff\n"
    "- terminal-pytest-output-failures\n"
    "- figma-dashboard-wireframe-layout"
)

MAX_SLUG_LENGTH = 60
STABILIZE_POLL = 0.5  # seconds between size checks
STABILIZE_ROUNDS = 3  # consecutive stable readings required

logger = logging.getLogger("screenshot-rename")


# ---------------------------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------------------------

def preprocess_image(path: Path, max_dim: int = 1024, quality: int = 85) -> bytes:
    """Downscale + JPEG compress for API efficiency.

    Reduces ~5MB Retina PNG to ~150KB JPEG. No quality loss for naming tasks.
    """
    from PIL import Image

    img = Image.open(path).convert("RGB")
    if max(img.size) > max_dim:
        ratio = max_dim / max(img.size)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Vision Providers
# ---------------------------------------------------------------------------

class GeminiProvider:
    """Google Gemini Flash/Pro via google-genai SDK."""

    def __init__(self, model: str = "gemini-2.0-flash"):
        from google import genai
        from google.genai import types
        self._client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self._types = types
        self._model = model

    def describe(self, image_bytes: bytes) -> str:
        part = self._types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
        text_part = self._types.Part.from_text(text=VISION_PROMPT)
        resp = self._client.models.generate_content(
            model=self._model,
            contents=[part, text_part],
            config=self._types.GenerateContentConfig(
                max_output_tokens=30,
                temperature=0.0,
                system_instruction=SYSTEM_PROMPT,
            ),
        )
        if not resp or not resp.text:
            raise ValueError("Empty response from Gemini")
        return resp.text.strip()


class OpenAIProvider:
    """OpenAI GPT-4o-mini with detail:low for cost savings."""

    def __init__(self, model: str = "gpt-4o-mini"):
        import openai
        self._client = openai.OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self._model = model

    def describe(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": [
                    {"type": "image_url", "image_url": {
                        "url": f"data:image/jpeg;base64,{b64}",
                        "detail": "low",
                    }},
                    {"type": "text", "text": VISION_PROMPT},
                ]},
            ],
            max_tokens=30,
            temperature=0,
        )
        if not resp.choices or not resp.choices[0].message.content:
            raise ValueError("Empty response from OpenAI")
        return resp.choices[0].message.content.strip()


class AnthropicProvider:
    """Anthropic Claude via messages API."""

    def __init__(self, model: str = "claude-sonnet-4-6"):
        import anthropic
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._model = model

    def describe(self, image_bytes: bytes) -> str:
        b64 = base64.b64encode(image_bytes).decode()
        resp = self._client.messages.create(
            model=self._model,
            max_tokens=30,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": [
                {"type": "image", "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": b64,
                }},
                {"type": "text", "text": VISION_PROMPT},
            ]}],
        )
        if not resp.content or not resp.content[0].text:
            raise ValueError("Empty response from Anthropic")
        return resp.content[0].text.strip()


class SmolVLMProvider:
    """Local SmolVLM via subprocess to view_image.py."""

    def __init__(self):
        self._script = Path.home() / ".claude/skills/smolvlm/scripts/view_image.py"

    def describe(self, image_bytes: bytes) -> str:
        import subprocess
        import tempfile
        # Write preprocessed bytes to temp file for the CLI script
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(image_bytes)
            tmp_path = f.name
        try:
            result = subprocess.run(
                [sys.executable, str(self._script), tmp_path, VISION_PROMPT,
                 "--max-tokens", "30", "--temp", "0.0"],
                capture_output=True, text=True, timeout=60,
            )
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip())
            return result.stdout.strip()
        finally:
            os.unlink(tmp_path)


class OllamaProvider:
    """Local Ollama via HTTP API."""

    def __init__(self, model: str = "llava",
                 base_url: str = "http://localhost:11434"):
        self._model = model
        self._base_url = base_url.rstrip("/")

    def describe(self, image_bytes: bytes) -> str:
        import urllib.request
        import json
        b64 = base64.b64encode(image_bytes).decode()
        payload = json.dumps({
            "model": self._model,
            "prompt": VISION_PROMPT,
            "images": [b64],
            "stream": False,
            "options": {"temperature": 0, "num_predict": 30},
        }).encode()
        req = urllib.request.Request(
            f"{self._base_url}/api/generate",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
        if "error" in data:
            raise ValueError(f"Ollama error: {data['error']}")
        response = data.get("response", "").strip()
        if not response:
            raise ValueError("Empty response from Ollama")
        return response


# Provider registry
PROVIDERS = {
    "gemini-flash": lambda: GeminiProvider("gemini-2.0-flash"),
    "gemini-pro": lambda: GeminiProvider("gemini-2.5-pro-preview-06-05"),
    "openai": lambda: OpenAIProvider(),
    "anthropic": lambda: AnthropicProvider(),
    "smolvlm": lambda: SmolVLMProvider(),
    "ollama": lambda: OllamaProvider(
        model=os.environ.get("OLLAMA_MODEL", "llava"),
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
    ),
}


def get_provider(name: str):
    """Instantiate a vision provider by name."""
    if name not in PROVIDERS:
        raise ValueError(f"Unknown provider: {name}. Choose from: {list(PROVIDERS)}")
    return PROVIDERS[name]()


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------

def wait_stable(path: Path) -> bool:
    """Wait until file size is stable for STABILIZE_ROUNDS consecutive reads."""
    prev_size = -1
    stable_count = 0
    for _ in range(STABILIZE_ROUNDS + 20):  # max ~12s total
        try:
            size = path.stat().st_size
        except OSError:
            return False
        if size == prev_size and size > 0:
            stable_count += 1
            if stable_count >= STABILIZE_ROUNDS:
                return True
        else:
            stable_count = 0
        prev_size = size
        time.sleep(STABILIZE_POLL)
    return False


def slugify(text: str, max_length: int = MAX_SLUG_LENGTH) -> str:
    """Convert description to filename slug. Matches plan-rename.py pattern."""
    text = unicodedata.normalize("NFC", text)
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = text.strip("-")
    if len(text) > max_length:
        text = text[:max_length].rsplit("-", 1)[0]
    return text


def normalize(name: str) -> str:
    """Normalize filename to NFC Unicode."""
    return unicodedata.normalize("NFC", name)


def parse_screenshot(filename: str) -> dict | None:
    """Parse a CleanShot or macOS screenshot filename.

    Returns dict with date, retina, ext keys, or None if not a screenshot.
    """
    for pattern in (CLEANSHOT_RE, MACOS_SCREENSHOT_RE):
        m = pattern.match(filename)
        if m:
            date_str = m.group(1)
            retina = m.group(5) or ""
            ext = m.group(6).lower()
            return {"date": date_str, "retina": retina, "ext": ext}
    return None


def count_index_entries() -> int:
    """Count existing entries in INDEX.md for fallback numbering."""
    if not INDEX_PATH.exists():
        return 0
    count = 0
    with open(INDEX_PATH) as f:
        for line in f:
            if line.startswith("| 20"):  # date rows
                count += 1
    return count


def append_index(date: str, new_name: str, original: str, description: str):
    """Append an entry to INDEX.md with file locking."""
    header = (
        "# Screenshots\n\n"
        "| Date | Name | Original | Description |\n"
        "|------|------|----------|-------------|\n"
    )
    slug = Path(new_name).stem
    entry = f"| {date} | [{slug}]({new_name}) | {original} | {description} |\n"

    # a+ creates if missing; lock before any read/write
    with open(INDEX_PATH, "a+") as f:
        fcntl.flock(f, fcntl.LOCK_EX)
        f.seek(0)
        content = f.read()
        if not content:
            content = header
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if line.startswith("|---"):
                lines.insert(i + 1, entry.rstrip())
                break
        f.seek(0)
        f.truncate()
        f.write("\n".join(lines))


def resolve_collision(target: Path) -> Path:
    """Atomically claim a unique filename using O_CREAT|O_EXCL."""
    candidates = [target] + [
        target.parent / f"{target.stem}-{i}{target.suffix}"
        for i in range(2, 100)
    ]
    for candidate in candidates:
        try:
            fd = os.open(str(candidate), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.close(fd)
            return candidate
        except FileExistsError:
            continue
    raise RuntimeError(f"Too many collisions for {target.name}")


# ---------------------------------------------------------------------------
# Main processing
# ---------------------------------------------------------------------------

def process_file(path: Path, provider, dry_run: bool = False) -> bool:
    """Process a single screenshot file. Returns True if renamed."""
    info = parse_screenshot(path.name)
    if not info:
        return False

    date_str = info["date"]
    retina = info["retina"]
    ext = f".{info['ext']}"
    original_name = path.name

    # Wait for file to finish writing
    if not wait_stable(path):
        logger.warning(f"File not stable, skipping: {path.name}")
        return False

    description = ""

    if ext in VIDEO_EXTS:
        # Video/GIF—generic name without vision
        slug = "screen-recording" if ext == ".mp4" else "animation"
        description = slug
    else:
        # Image—send to vision provider
        try:
            image_bytes = preprocess_image(path)
            raw_desc = provider.describe(image_bytes)
            slug = slugify(raw_desc)
            description = raw_desc
            if not slug:
                raise ValueError("Empty slug from provider")
        except Exception as e:
            logger.warning(f"Vision API failed for {path.name}: {e}")
            # Fallback to generic name
            n = count_index_entries() + 1
            slug = f"screenshot-{n:03d}"
            description = "(vision failed)"

    new_name = normalize(f"{date_str}-{slug}{retina}{ext}")

    if dry_run:
        logger.info(f"[DRY RUN] {original_name} -> {new_name}")
        return True

    # Atomically claim unique filename, then rename
    new_path = resolve_collision(path.parent / new_name)
    new_name = new_path.name
    try:
        os.replace(str(path), str(new_path))
    except Exception:
        # Clean up placeholder on failure
        try:
            os.unlink(new_path)
        except OSError:
            pass
        raise
    logger.info(f"{original_name} -> {new_name}")

    # Update index
    try:
        append_index(date_str, new_name, original_name, description)
    except Exception as e:
        logger.warning(f"Failed to update INDEX.md: {e}")

    return True


def setup_logging():
    """Configure logging to file + stderr."""
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

    from logging.handlers import RotatingFileHandler
    file_handler = RotatingFileHandler(
        LOG_PATH, maxBytes=5 * 1024 * 1024, backupCount=3
    )
    file_handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    ))

    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))

    logger.addHandler(file_handler)
    logger.addHandler(stderr_handler)
    logger.setLevel(logging.INFO)


def main():
    parser = argparse.ArgumentParser(description="Screenshot Auto-Rename Daemon")
    parser.add_argument("--test", metavar="PATH", help="Test mode: process one file")
    parser.add_argument("--provider", default=None,
                        help=f"Vision provider (default: from .env). Options: {list(PROVIDERS)}")
    parser.add_argument("--dry-run", action="store_true", help="Preview renames")
    args = parser.parse_args()

    setup_logging()

    # Load .env
    from dotenv import load_dotenv
    env_path = SCRIPT_DIR / ".env"
    if env_path.exists():
        load_dotenv(env_path)
    else:
        logger.warning(f"No .env file at {env_path}")

    # Determine provider
    provider_name = args.provider or os.environ.get("PROVIDER", "gemini-flash")
    try:
        provider = get_provider(provider_name)
    except Exception as e:
        logger.error(f"Failed to initialize provider '{provider_name}': {e}")
        sys.exit(1)

    logger.info(f"Provider: {provider_name}")

    if args.test:
        # Test mode: process one specific file
        test_path = Path(args.test).expanduser().resolve()
        if not test_path.exists():
            logger.error(f"File not found: {test_path}")
            sys.exit(1)
        success = process_file(test_path, provider, dry_run=args.dry_run)
        sys.exit(0 if success else 1)

    # Normal mode: scan watch directory for unprocessed screenshots
    if not WATCH_DIR.exists():
        logger.error(f"Watch directory not found: {WATCH_DIR}")
        sys.exit(1)

    # Brief cooldown to let launchd settle after WatchPaths trigger
    time.sleep(0.5)

    count = 0
    for path in sorted(WATCH_DIR.iterdir()):
        if path.is_file() and parse_screenshot(path.name):
            if process_file(path, provider, dry_run=args.dry_run):
                count += 1

    if count:
        logger.info(f"Processed {count} screenshot(s)")
    else:
        logger.info("No unprocessed screenshots found")


if __name__ == "__main__":
    main()
