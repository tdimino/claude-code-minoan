"""Build the Phase 2 pilot's input files. Every input is public material, since it is sent to OpenRouter.

  prose.md       codex-orchestrator's README and SKILL.md (public repository)        English prose
  models.json    the first records of OpenRouter's own public model list             JSON
  hebrew.txt     Genesis 1-15, pointed Hebrew, from Sefaria's public API             Hebrew with niqqud
  translit.txt   the head of semitic_roots.json (published in kaphtor)               transliteration, diacritics
  big.json       a longer run of the model list, sized by --big-bytes                the over-200k-token call
  doc.pdf        three pages printed from prose.md                                   PDF tokens per page
  page.png       the PDF's first page as an image                                    tokens per image
  schema.json    a two-field strict schema

    uv run python build_pilot_inputs.py [--big-bytes N]
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent / "inputs"
SKILLS = Path.home() / ".claude/skills"
MODELS = Path.home() / ".claude/data/gemini-orchestrator/models-cache.json"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--big-bytes", type=int, default=0, help="write big.json with about this many bytes")
    args = ap.parse_args()
    HERE.mkdir(parents=True, exist_ok=True)

    prose = "\n\n".join((SKILLS / "codex-orchestrator" / n).read_text(encoding="utf-8") for n in ("README.md", "SKILL.md"))
    (HERE / "prose.md").write_text(prose, encoding="utf-8")

    models = json.loads(MODELS.read_text(encoding="utf-8"))["data"]
    (HERE / "models.json").write_text(json.dumps(models[:22], indent=1), encoding="utf-8")
    if args.big_bytes:
        text = json.dumps(models, indent=1)
        (HERE / "big.json").write_text(text[:args.big_bytes], encoding="utf-8")

    if not (HERE / "hebrew.txt").exists():
        verses = []
        for chapter in range(1, 16):
            req = urllib.request.Request(f"https://www.sefaria.org/api/texts/Genesis.{chapter}?context=0&commentary=0",
                                         headers={"User-Agent": "gemini-orchestrator/0.1"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                he = json.load(resp)["he"]
            verses.extend(f"{chapter}:{n} {re.sub(r'<[^>]+>|&[a-z]+;', '', v)}" for n, v in enumerate(he, 1))
        (HERE / "hebrew.txt").write_text("\n".join(verses) + "\n", encoding="utf-8")

    roots = (SKILLS / "linear-a-decipherment/data/semitic_roots.json").read_text(encoding="utf-8")
    (HERE / "translit.txt").write_text(roots[:60000], encoding="utf-8")

    page_source = HERE / "pdf-source.txt"
    page_source.write_text("\n".join(prose.splitlines()[:150]) + "\n", encoding="utf-8")
    with open(HERE / "doc.pdf", "wb") as out:
        subprocess.run(["cupsfilter", str(page_source)], stdout=out, stderr=subprocess.DEVNULL, check=True)
    subprocess.run(["sips", "-s", "format", "png", str(HERE / "doc.pdf"), "--out", str(HERE / "page.png")],
                   capture_output=True, check=True)

    (HERE / "schema.json").write_text(json.dumps({
        "type": "object", "additionalProperties": False, "required": ["language", "word_count"],
        "properties": {"language": {"type": "string"}, "word_count": {"type": "integer"}}}, indent=1), encoding="utf-8")

    for p in sorted(HERE.iterdir()):
        print(f"{p.stat().st_size:>9,}  {p.name}")


if __name__ == "__main__":
    main()
