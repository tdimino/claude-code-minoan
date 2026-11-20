#!/usr/bin/env python3
"""
first_world.py: have a Gemini 4 model paint the first draft of a world, through OpenRouter.

The session folder is the memory. Every world a model returns is saved as
NNN_<model>.html beside a JSON sidecar, and `revise` sends the latest world,
a critique and optional screenshots back for the next one.

Usage:
    python3 first_world.py models
    python3 first_world.py paint "A fishing village on a tidal estuary at dusk" --model neon
    python3 first_world.py paint "Terraced olive hills above a harbor" --only neon hydrogen --session olives
    python3 first_world.py revise olives "The far shore is flat fill. Water needs moving strokes." \
        --shots shots/noon.png shots/dusk.png
    python3 first_world.py list

A bare model name resolves to google/gemini-4-<name> (neon, hydrogen, carbon,
argon, and any later member of the series). A name with a slash is used as given.

Environment:
    OPENROUTER_API_KEY   required for paint and revise

Exit codes: 0 ok, 1 API failure or no document returned, 2 usage,
3 a world was saved but is truncated or fails check_world.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_world import check_html, format_report  # noqa: E402

SKILL = Path(__file__).resolve().parent.parent
API = "https://openrouter.ai/api/v1"
SERIES_PREFIX = "google/gemini-4-"
BRIEF_FILE = SKILL / "assets" / "prompts" / "first-world.md"

SEED_FILES = {
    "none": [],
    "starter": ["assets/painterly-starter.html"],
    "full": [
        "assets/painterly-starter.html",
        "references/stroke-engine.md",
        "references/world-pipeline.md",
        "references/living-details.md",
    ],
}

MODES = {
    "still": "One composed view, breathing in place. No input, no chunk streaming.",
    "scene": "A bounded place to look around and walk through.",
    "world": "Endless terrain generated in chunks as the walker moves, with distinct regions and landmarks.",
}

CSP_MARK = "data-painterly-csp"
CSP_META = (
    '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
    "script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; "
    f"media-src data: blob:; font-src data:\" {CSP_MARK}>"
)

_print_lock = threading.Lock()


def say(message: str) -> None:
    with _print_lock:
        print(message, file=sys.stderr, flush=True)


def die(message: str, code: int = 2) -> None:
    print(message, file=sys.stderr)
    sys.exit(code)


# --- OpenRouter -------------------------------------------------------------

def load_key() -> str:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    env_file = Path.home() / ".config" / "env" / "global.env"
    if env_file.is_file():
        for line in env_file.read_text(errors="replace").splitlines():
            m = re.match(r"\s*(?:export\s+)?OPENROUTER_API_KEY\s*=\s*[\"']?([^\"'\s]+)", line)
            if m:
                return m.group(1)
    die("OPENROUTER_API_KEY is not set. Create a key at https://openrouter.ai/settings/keys")


def fetch_catalog() -> dict:
    """OpenRouter's public model list, keyed by model id."""
    try:
        with urllib.request.urlopen(f"{API}/models", timeout=60) as resp:
            return {m["id"]: m for m in json.load(resp)["data"]}
    except (urllib.error.URLError, OSError, ValueError, KeyError) as e:
        die(f"Could not read the OpenRouter model list: {e}", 1)


def series(catalog: dict) -> list[str]:
    return sorted(i for i in catalog if i.startswith(SERIES_PREFIX) and ":" not in i)


def resolve_model(name: str, catalog: dict) -> tuple[str, str]:
    """Return (model id, short alias used in filenames)."""
    model_id = name if "/" in name else SERIES_PREFIX + name.lower()
    if model_id not in catalog:
        known = ", ".join(i.removeprefix(SERIES_PREFIX) for i in series(catalog))
        die(f"OpenRouter has no model '{model_id}'. Gemini 4 series: {known}")
    alias = model_id.split("/")[-1].removeprefix("gemini-4-")
    return model_id, re.sub(r"[^a-z0-9.]+", "-", alias.lower()).strip("-")


def price(entry: dict) -> tuple[float, float]:
    """(input, output) in dollars per token."""
    p = entry.get("pricing", {})
    return float(p.get("prompt") or 0), float(p.get("completion") or 0)


def stream_completion(key: str, body: dict, label: str) -> dict:
    """POST a streaming chat completion. Partial text survives a mid-stream failure."""
    request = urllib.request.Request(
        f"{API}/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        },
    )
    out = {"text": "", "finish": None, "usage": None, "id": None, "error": None, "reasoning_chars": 0}
    parts: list[str] = []
    last_report = time.monotonic()
    try:
        response = urllib.request.urlopen(request, timeout=600)
    except urllib.error.HTTPError as e:
        out["error"] = f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:600]}"
        return out
    except (urllib.error.URLError, OSError) as e:
        out["error"] = f"connection failed: {e}"
        return out

    try:
        with response:
            for raw in response:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue  # blank separators and ": OPENROUTER PROCESSING" keep-alives
                data = line[5:].strip()
                if data == "[DONE]":
                    break
                try:
                    chunk = json.loads(data)
                except ValueError:
                    continue
                if chunk.get("error"):
                    err = chunk["error"]
                    out["error"] = f"{err.get('code', '')} {err.get('message', err)}".strip()
                    break
                out["id"] = chunk.get("id") or out["id"]
                if chunk.get("usage"):
                    out["usage"] = chunk["usage"]
                for choice in chunk.get("choices") or []:
                    delta = choice.get("delta") or {}
                    if delta.get("content"):
                        parts.append(delta["content"])
                    if delta.get("reasoning"):
                        out["reasoning_chars"] += len(delta["reasoning"])
                    if choice.get("finish_reason"):
                        out["finish"] = choice["finish_reason"]
                now = time.monotonic()
                if now - last_report > 10:
                    last_report = now
                    written = sum(len(p) for p in parts)
                    say(f"  [{label}] {written:,} chars written, {out['reasoning_chars']:,} chars of reasoning")
    except (OSError, ValueError) as e:
        out["error"] = f"stream broke: {e}"
    out["text"] = "".join(parts)
    return out


# --- Documents and sessions -------------------------------------------------

def extract_html(text: str) -> tuple[str | None, bool, str]:
    """Return (html, complete, text outside the document)."""
    start = re.search(r"<!doctype html|<html[\s>]", text, re.I)
    if not start:
        return None, False, text.strip()
    # The first </html>, not the last: a model may keep talking after the document,
    # and quote the closing tag while it does.
    end = text.lower().find("</html>", start.start())
    if end == -1:
        return text[start.start():], False, text[:start.start()].strip()
    outside = (text[:start.start()] + text[end + 7:]).strip().strip("`").strip()
    return text[start.start():end + 7] + "\n", True, outside


def inject_csp(html: str) -> str:
    """Add a no-network Content-Security-Policy. The model's code is untrusted."""
    if CSP_MARK in html:
        return html
    head = re.search(r"<head[^>]*>", html, re.I)
    if head:
        return html[:head.end()] + "\n" + CSP_META + html[head.end():]
    top = re.search(r"<html[^>]*>", html, re.I) or re.search(r"<!doctype html[^>]*>", html, re.I)
    at = top.end() if top else 0
    return html[:at] + "\n" + CSP_META + "\n" + html[at:]


def next_index(session_dir: Path) -> int:
    if not session_dir.is_dir():
        return 1
    taken = [int(m.group(1)) for p in session_dir.iterdir() if (m := re.match(r"(\d{3})_", p.name))]
    return max(taken, default=0) + 1


def latest_world(session_dir: Path) -> Path | None:
    worlds = sorted(p for p in session_dir.glob("[0-9][0-9][0-9]_*.html") if ".partial." not in p.name)
    return worlds[-1] if worlds else None


def read_seed_files(seed: str) -> str:
    blocks = []
    for rel in SEED_FILES[seed]:
        path = SKILL / rel
        if not path.is_file():
            die(f"Seed file missing: {path}")
        blocks.append(f'<file name="{rel}">\n{path.read_text(encoding="utf-8")}\n</file>')
    return "\n\n".join(blocks)


def data_url(path: Path) -> str:
    mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}.get(
        path.suffix.lower()
    )
    if not mime:
        die(f"Unsupported screenshot type: {path} (use png, jpg or webp)")
    return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode('ascii')}"


def build_body(model_id: str, entry: dict, user_content, args) -> dict:
    ceiling = (entry.get("top_provider") or {}).get("max_completion_tokens") or args.max_tokens
    body = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": BRIEF_FILE.read_text(encoding="utf-8")},
            {"role": "user", "content": user_content},
        ],
        "stream": True,
        "max_tokens": min(args.max_tokens, ceiling),
        "usage": {"include": True},
    }
    if args.effort != "none":
        body["reasoning"] = {"effort": args.effort}
    if args.temperature is not None:
        body["temperature"] = args.temperature
    return body


def cost_ceiling(body: dict, entry: dict) -> float:
    """Upper bound in dollars: the whole prompt at ~3 chars a token, plus every output token."""
    p_in, p_out = price(entry)
    prompt_chars = len(json.dumps(body["messages"]))
    return prompt_chars / 3 * p_in + body["max_tokens"] * p_out


def run_job(key: str, job: dict, args) -> dict:
    """One model call: stream, save the document and its sidecar, check it."""
    label, session_dir, stem = job["alias"], job["session_dir"], job["stem"]
    say(f"  [{label}] calling {job['model_id']} (max {job['body']['max_tokens']:,} tokens)")
    started = time.monotonic()
    result = stream_completion(key, job["body"], label)
    html, complete, outside = extract_html(result["text"])

    record = {
        "model": job["model_id"],
        "created": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": job["command"],
        "mode": job.get("mode"),
        "seed": job.get("seed"),
        "brief": job.get("brief"),
        "critique": job.get("critique"),
        "parent": job.get("parent"),
        "shots": job.get("shots"),
        "effort": args.effort,
        "max_tokens": job["body"]["max_tokens"],
        "seconds": round(time.monotonic() - started, 1),
        "generation_id": result["id"],
        "finish_reason": result["finish"],
        "error": result["error"],
        "usage": result["usage"],
        "cost_usd": (result["usage"] or {}).get("cost"),
        "outside_document": outside[:2000] or None,
    }

    status = 0
    if html is None:
        path = session_dir / f"{stem}.response.txt"
        path.write_text(result["text"], encoding="utf-8")
        status = 1
    else:
        truncated = not complete  # a closed document followed by cut-off chatter is whole
        path = session_dir / (f"{stem}.partial.html" if truncated else f"{stem}.html")
        record["sha256_as_returned"] = hashlib.sha256(html.encode("utf-8")).hexdigest()
        record["csp_injected"] = not args.no_csp
        if not args.no_csp:
            html = inject_csp(html)
        path.write_text(html, encoding="utf-8")
        record["check"] = check_html(html)
        if truncated or record["check"]["errors"]:
            status = 3
    if result["error"] and status == 0:
        status = 1
    record["file"] = path.name
    (session_dir / f"{stem}.json").write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return {"path": path, "record": record, "status": status, "label": label}


def report(outcomes: list[dict]) -> int:
    total = 0.0
    for o in outcomes:
        rec = o["record"]
        usage = rec["usage"] or {}
        cost = rec["cost_usd"]
        total += cost or 0
        print(f"\n{o['label']}: {o['path']}")
        print(
            f"  {usage.get('prompt_tokens', '?')} in, {usage.get('completion_tokens', '?')} out, "
            f"{'$%.4f' % cost if cost is not None else 'cost not reported'}, "
            f"{rec['seconds']}s, finish: {rec['finish_reason']}"
        )
        if rec["error"]:
            print(f"  API error: {rec['error']}")
        if rec["finish_reason"] == "length":
            print(
                "  Stopped at the output cap. A .partial.html file is cut short: raise --max-tokens "
                "or narrow the brief. A .html file is whole, and the model was cut off after it."
            )
        if "check" in rec:
            print("  " + format_report(rec["check"], "check_world").replace("\n", "\n  "))
        elif not rec["error"]:
            print("  No HTML document in the response: see the .response.txt file.")
    if len(outcomes) > 1:
        print(f"\nTotal: ${total:.4f}")
    return max(o["status"] for o in outcomes)


def launch(key: str, jobs: list[dict], args) -> int:
    ceiling = sum(cost_ceiling(j["body"], j["entry"]) for j in jobs)
    say(f"Cost ceiling for {len(jobs)} call(s): ${ceiling:.2f} (limit ${args.max_cost:.2f})")
    if ceiling > args.max_cost:
        die(f"Ceiling ${ceiling:.2f} is over --max-cost ${args.max_cost:.2f}. Lower --max-tokens or raise --max-cost.")
    if args.dry_run:
        for j in jobs:
            say(f"  [{j['alias']}] would write {j['session_dir'] / (j['stem'] + '.html')}")
        return 0
    with ThreadPoolExecutor(max_workers=max(1, len(jobs))) as pool:
        outcomes = list(pool.map(lambda j: run_job(key, j, args), jobs))
    return report(outcomes)


# --- Commands ---------------------------------------------------------------

def cmd_models(args) -> int:
    catalog = fetch_catalog()
    print(f"{'name':<12} {'model id':<30} {'$/M in':>8} {'$/M out':>8} {'context':>10} {'max out':>9}  images")
    for model_id in series(catalog):
        entry = catalog[model_id]
        p_in, p_out = price(entry)
        max_out = (entry.get("top_provider") or {}).get("max_completion_tokens") or 0
        sees = "yes" if "image" in (entry.get("architecture") or {}).get("input_modalities", []) else "no"
        print(
            f"{model_id.removeprefix(SERIES_PREFIX):<12} {model_id:<30} {p_in * 1e6:>8.2f} {p_out * 1e6:>8.2f} "
            f"{entry.get('context_length', 0):>10,} {max_out:>9,}  {sees}"
        )
    return 0


def cmd_paint(args) -> int:
    key = None if args.dry_run else load_key()
    catalog = fetch_catalog()
    names = args.only or [args.model]
    session = args.session or datetime.now().strftime("%Y%m%d-%H%M%S")
    session_dir = args.out / session
    if not args.dry_run:
        session_dir.mkdir(parents=True, exist_ok=True)

    user = f"Mode: {args.mode}. {MODES[args.mode]}\n\nBrief: {args.brief}"
    seeds = read_seed_files(args.seed)
    if seeds:
        user += (
            "\n\nReference material follows: a working kernel"
            + (" and notes on the technique" if args.seed == "full" else "")
            + ". Build on it or replace it. The output rules and the test contract hold either way.\n\n"
            + seeds
        )

    index = next_index(session_dir)
    jobs = []
    for offset, name in enumerate(dict.fromkeys(names)):
        model_id, alias = resolve_model(name, catalog)
        jobs.append({
            "command": "paint", "model_id": model_id, "alias": alias, "entry": catalog[model_id],
            "session_dir": session_dir, "stem": f"{index + offset:03d}_{alias}",
            "mode": args.mode, "seed": args.seed, "brief": args.brief,
            "body": build_body(model_id, catalog[model_id], user, args),
        })
    status = launch(key, jobs, args)
    if not args.dry_run:
        print(f"\nSession: {session}  ({session_dir})")
    return status


def cmd_revise(args) -> int:
    key = None if args.dry_run else load_key()
    catalog = fetch_catalog()
    session_dir = args.out / args.session
    if not session_dir.is_dir():
        die(f"No session at {session_dir}. Run `list` to see sessions.")
    source = args.source or latest_world(session_dir)
    if not source or not source.is_file():
        die(f"No complete world to revise in {session_dir}.")
    model_id, alias = resolve_model(args.model, catalog)
    entry = catalog[model_id]

    shots = args.shots or []
    for shot in shots:
        if not shot.is_file():
            die(f"Screenshot not found: {shot}")
    if shots and "image" not in (entry.get("architecture") or {}).get("input_modalities", []):
        die(f"{model_id} does not take images. Drop --shots or pick another model.")

    text = (
        "Revise the world below. Return the complete revised document under the same output rules "
        "and test contract, keeping what already works.\n\n"
        f"Critique: {args.critique}\n\n"
        + (f"{len(shots)} screenshot(s) of the current world are attached.\n\n" if shots else "")
        + f'<file name="{source.name}">\n{source.read_text(encoding="utf-8")}\n</file>'
    )
    content = [{"type": "text", "text": text}] + [
        {"type": "image_url", "image_url": {"url": data_url(shot)}} for shot in shots
    ]
    job = {
        "command": "revise", "model_id": model_id, "alias": alias, "entry": entry,
        "session_dir": session_dir, "stem": f"{next_index(session_dir):03d}_{alias}",
        "critique": args.critique, "parent": source.name, "shots": [str(s) for s in shots],
        "body": build_body(model_id, entry, content, args),
    }
    return launch(key, [job], args)


def cmd_list(args) -> int:
    if not args.out.is_dir():
        print(f"No sessions in {args.out}")
        return 0
    for session_dir in sorted(p for p in args.out.iterdir() if p.is_dir()):
        sidecars = sorted(session_dir.glob("[0-9][0-9][0-9]_*.json"))
        if not sidecars:
            continue
        print(session_dir.name)
        for sidecar in sidecars:
            rec = json.loads(sidecar.read_text())
            check = rec.get("check")
            verdict = "no document" if check is None else ("FAIL" if check["errors"] else "ok")
            cost = rec.get("cost_usd")
            note = rec.get("brief") or rec.get("critique") or ""
            print(
                f"  {rec.get('file', sidecar.stem):<28} {rec['command']:<7} {verdict:<12}"
                f"{'$%.2f' % cost if cost is not None else '   -':>7}  {note[:60]}"
            )
    return 0


def add_call_options(p: argparse.ArgumentParser) -> None:
    p.add_argument("--out", type=Path, default=Path("painted-worlds"), help="sessions folder (default ./painted-worlds)")
    p.add_argument("--max-tokens", type=int, default=96000, help="output cap, reasoning included (default 96000)")
    p.add_argument("--effort", choices=["none", "low", "medium", "high"], default="high", help="reasoning effort")
    p.add_argument("--temperature", type=float)
    p.add_argument("--max-cost", type=float, default=5.0, help="refuse to start above this cost ceiling in dollars")
    p.add_argument("--no-csp", action="store_true", help="save the document without the no-network CSP")
    p.add_argument("--dry-run", action="store_true", help="resolve models and print the cost ceiling, call nothing")


def main() -> int:
    parser = argparse.ArgumentParser(description="Have a Gemini 4 model paint the first draft of a world.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("models", help="list the Gemini 4 series on OpenRouter").set_defaults(func=cmd_models)

    paint = sub.add_parser("paint", help="generate a first world from a brief")
    paint.add_argument("brief")
    paint.add_argument("--model", default="neon", help="series name or full OpenRouter id (default neon)")
    paint.add_argument("--only", nargs="+", metavar="MODEL", help="several models in parallel on the same brief")
    paint.add_argument("--mode", choices=list(MODES), default="scene")
    paint.add_argument("--seed", choices=list(SEED_FILES), default="none",
                       help="none: the model's own engine. starter: send the kernel. full: kernel plus references")
    paint.add_argument("--session", help="session name (default: a timestamp)")
    add_call_options(paint)
    paint.set_defaults(func=cmd_paint)

    revise = sub.add_parser("revise", help="send the latest world back with a critique")
    revise.add_argument("session")
    revise.add_argument("critique")
    revise.add_argument("--model", default="neon")
    revise.add_argument("--from", dest="source", type=Path, help="revise this file instead of the session's latest")
    revise.add_argument("--shots", nargs="+", type=Path, metavar="IMAGE", help="screenshots of the current world")
    add_call_options(revise)
    revise.set_defaults(func=cmd_revise)

    lister = sub.add_parser("list", help="list sessions")
    lister.add_argument("--out", type=Path, default=Path("painted-worlds"))
    lister.set_defaults(func=cmd_list)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
