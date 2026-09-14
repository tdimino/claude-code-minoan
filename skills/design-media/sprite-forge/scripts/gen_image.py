#!/usr/bin/env python3
"""Provider router for still-image generation and edits (fal genmedia CLI or Retro Diffusion).

Jobs map to default endpoints (override with --model):
  anchor  identity anchor / HD still    openai/gpt-image-2.5/sunburst        (alt: fal-ai/nano-banana-2)
  edit    pose/direction edit from refs openai/gpt-image-2.5/sunburst/edit   (alt: fal-ai/nano-banana-2/edit)
  draft   cheap draft still             openai/gpt-image-2.5/flare
  pixel   pixel-art still               Retro Diffusion rd_pro__default (refs <= 9)

Every call is a dry run unless --yes: it prints the exact command, uploads nothing, spends nothing.
genmedia is invoked as a subprocess; local reference images are uploaded with `genmedia upload`.
Endpoint parameter names vary per model; use `genmedia schema <endpoint>` to confirm and pass
extras with --param key=value.

Install genmedia once:
  curl https://genmedia.sh/install -fsS | bash && genmedia setup --non-interactive --api-key "$FAL_KEY"

Examples:
  gen_image.py --job anchor --prompt "full-body astromech droid, neutral pose" --transparent --out ./anchor
  gen_image.py --job edit --prompt "same droid, back view" --image anchor.png --out ./dirs --yes
  gen_image.py --job pixel --prompt "astromech droid" --image anchor.png --size 96x96 --yes
"""

from __future__ import annotations

import argparse
import json
import shlex
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _secrets import get_api_key  # noqa: E402

DEFAULT_ENDPOINTS = {
    "anchor": "openai/gpt-image-2.5/sunburst",
    "edit": "openai/gpt-image-2.5/sunburst/edit",
    "draft": "openai/gpt-image-2.5/flare",
}
# Which input field an endpoint expects for reference images. Verified against
# fal schemas where noted; others follow the fal convention (image_urls for edits).
IMAGE_FIELD = {
    "openai/gpt-image-2.5/sunburst/edit": "image_urls",
    "openai/gpt-image-2.5/flare/edit": "image_urls",
    "fal-ai/nano-banana-2/edit": "image_urls",
    "fal-ai/nano-banana-pro/edit": "image_urls",   # verified in fal docs
}
# Static price notes (USD) for the estimate line when `genmedia pricing` is unavailable.
PRICE_NOTES = {
    "openai/gpt-image-2.5/sunburst": "per image, see `genmedia pricing`",
    "openai/gpt-image-2.5/sunburst/edit": "per image, see `genmedia pricing`",
    "openai/gpt-image-2.5/flare": "per image (cheapest GPT Image tier)",
    "fal-ai/nano-banana-2": "~$0.04-0.08/image",
    "fal-ai/nano-banana-2/edit": "~$0.04-0.08/image",
    "alibaba/wan-3.0/image-to-video": "$0.05-0.20 per second",
    "fal-ai/kling-video/v3/pro/image-to-video": "$0.112 per second ($0.224 with @Element refs)",
    "bytedance/seedance-2.5/image-to-video": "per second, see `genmedia pricing`",
    "bytedance/seedance-2.5/reference-to-video": "per second, see `genmedia pricing`",
    "minimax/hailuo-03/image-to-video": "per second, see `genmedia pricing`",
    "fal-ai/veo3.1/image-to-video": "per second, see `genmedia pricing`",
}
INSTALL_HINT = ('genmedia not found. Install: curl https://genmedia.sh/install -fsS | bash '
                '&& genmedia setup --non-interactive --api-key "$FAL_KEY"')


# ---------------------------------------------------------------- genmedia

def genmedia_available() -> bool:
    return shutil.which("genmedia") is not None


def genmedia_upload(path: str) -> str:
    """Upload a local file to the fal CDN and return its URL. URLs pass through."""
    if path.startswith(("http://", "https://")):
        return path
    out = subprocess.run(["genmedia", "upload", path, "--json"], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"genmedia upload failed for {path}: {out.stderr.strip()}")
    try:
        return json.loads(out.stdout)["url"]
    except (json.JSONDecodeError, KeyError):
        sys.exit(f"genmedia upload returned unexpected output: {out.stdout[:200]}")


def genmedia_price(endpoint: str) -> str:
    """Best-effort price line: `genmedia pricing` when available, else the static note."""
    if genmedia_available():
        out = subprocess.run(["genmedia", "pricing", endpoint, "--json"], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            try:
                data = json.loads(out.stdout)
                return json.dumps(data if not isinstance(data, dict) else
                                  {k: v for k, v in data.items() if k in ("price", "pricing", "unit", "cost", "description")}
                                  or data)
            except json.JSONDecodeError:
                pass
    return PRICE_NOTES.get(endpoint, "unknown; run `genmedia pricing <endpoint>`")


def genmedia_run_cmd(endpoint: str, params: dict, out_dir: Path, stem: str, run_async: bool = False) -> list[str]:
    """Build the genmedia run argv. List values become repeated flags."""
    cmd = ["genmedia", "run", endpoint]
    for k, v in params.items():
        if v is None or v is False:
            continue
        if isinstance(v, (list, tuple)):
            for item in v:
                cmd += [f"--{k}", str(item)]
        elif v is True:
            cmd += [f"--{k}"]
        else:
            cmd += [f"--{k}", str(v)]
    if run_async:
        cmd.append("--async")
    cmd += ["--json", "--download", str(out_dir / f"{stem}_{{request_id}}_{{index}}.{{ext}}")]
    return cmd


def genmedia_execute(cmd: list[str]) -> dict:
    out = subprocess.run(cmd, capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"genmedia run failed: {out.stderr.strip() or out.stdout.strip()}")
    try:
        return json.loads(out.stdout)
    except json.JSONDecodeError:
        return {"raw": out.stdout}


def run_genmedia(endpoint: str, params: dict, images: list[str], image_field: str | None,
                 out_dir: Path, stem: str, yes: bool, as_json: bool, run_async: bool = False) -> dict:
    """Shared by gen_image.py and video_to_spritesheet.py: dry-run by default."""
    price = genmedia_price(endpoint)
    field = image_field or IMAGE_FIELD.get(endpoint, "image_urls" if endpoint.endswith("/edit") else "image_url")
    if images:
        if field.endswith("s"):
            params[field] = images if yes else [f"<upload:{i}>" for i in images]
        else:
            params[field] = images[0] if yes else f"<upload:{images[0]}>"
    if not yes:
        preview = genmedia_run_cmd(endpoint, params, out_dir, stem, run_async)
        summary = {"dry_run": True, "endpoint": endpoint, "price": price,
                   "command": " ".join(shlex.quote(c) for c in preview),
                   "installed": genmedia_available()}
        print(json.dumps(summary, indent=2) if as_json else
              f"[dry run] {endpoint}\n  price: {price}\n  {summary['command']}\n"
              f"  {'' if summary['installed'] else INSTALL_HINT + chr(10) + '  '}Re-run with --yes to generate.")
        return summary
    if not genmedia_available():
        sys.exit(INSTALL_HINT)
    get_api_key("FAL_KEY")  # genmedia stores its own key, but fail early if none is configured anywhere
    if images:
        uploaded = [genmedia_upload(i) for i in images]
        params[field] = uploaded if field.endswith("s") else uploaded[0]
    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = genmedia_run_cmd(endpoint, params, out_dir, stem, run_async)
    print(f"  $ {' '.join(shlex.quote(c) for c in cmd)}", file=sys.stderr)
    result = genmedia_execute(cmd)
    files = sorted(str(p) for p in out_dir.glob(f"{stem}_*"))
    summary = {"dry_run": False, "endpoint": endpoint, "price": price, "files": files,
               "request_id": result.get("request_id"), "result": result}
    print(json.dumps({k: v for k, v in summary.items() if k != "result"}, indent=2) if as_json else
          f"{endpoint}: {len(files)} file(s) -> {', '.join(files) or out_dir}")
    return summary


# ---------------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--job", choices=("anchor", "edit", "draft", "pixel"), default="anchor")
    p.add_argument("--prompt", required=True)
    p.add_argument("--image", action="append", help="reference image (local path or URL); repeatable")
    p.add_argument("--provider", choices=("genmedia", "rd"), help="default: rd for --job pixel, else genmedia")
    p.add_argument("--model", help="fal endpoint id or RD prompt_style override")
    p.add_argument("--size", help="WxH (RD) or fal image_size token, e.g. 1024x1024 / square_hd")
    p.add_argument("--transparent", action="store_true", help="request a transparent background (GPT Image, RD remove_bg)")
    p.add_argument("--image-field", help="override the endpoint's reference-image field name")
    p.add_argument("--param", action="append", help="extra endpoint param key=value (JSON parsed)")
    p.add_argument("--n", type=int, default=1)
    p.add_argument("--seed", type=int)
    p.add_argument("--out", default="./gen-out")
    p.add_argument("--stem", help="output filename stem (default: job)")
    p.add_argument("--yes", action="store_true", help="spend credits (default: dry run)")
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    provider = a.provider or ("rd" if a.job == "pixel" else "genmedia")
    out_dir = Path(a.out)
    stem = a.stem or a.job

    if provider == "rd":
        rd = Path(__file__).parent / "retro_diffusion.py"
        cmd = ["python3", str(rd), "generate", "--prompt", a.prompt,
               "--style", a.model or "rd_pro__default", "--size", a.size or "128x128",
               "--n", str(a.n), "--out", str(out_dir), "--stem", stem]
        for img in a.image or []:
            cmd += ["--ref", img]
        if a.transparent:
            cmd.append("--remove-bg")
        if a.seed is not None:
            cmd += ["--seed", str(a.seed)]
        if a.yes:
            cmd.append("--yes")
        if a.json:
            cmd.append("--json")
        sys.exit(subprocess.run(cmd).returncode)

    endpoint = a.model or DEFAULT_ENDPOINTS[a.job]
    params: dict = {"prompt": a.prompt}
    if a.n > 1:
        params["num_images"] = a.n
    if a.seed is not None:
        params["seed"] = a.seed
    if a.size:
        params["image_size"] = a.size
    if a.transparent:
        params["background"] = "transparent"
        params["output_format"] = "png"
    for kv in a.param or []:
        k, _, v = kv.partition("=")
        try:
            params[k] = json.loads(v)
        except json.JSONDecodeError:
            params[k] = v
    if a.job == "edit" and not a.image:
        sys.exit("--job edit needs at least one --image reference")
    run_genmedia(endpoint, params, a.image or [], a.image_field, out_dir, stem, a.yes, a.json)


if __name__ == "__main__":
    main()
