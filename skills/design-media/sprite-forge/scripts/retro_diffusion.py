#!/usr/bin/env python3
"""Retro Diffusion v2 client for sprite-forge (pixel-art generation, animation, edit tools).

Implements the contract from Retro-Diffusion/api-examples llms.txt (verified 2026-09):
  auth   X-RD-Token: rdpk-...          (env RETRODIFFUSION_API_KEY)
  gen    POST /v2/inferences  -> {"task_id"}  -> poll GET /v2/inferences/tasks/{id} every 2 s
  tools  POST /v2/edit/tools/{tool_id}   and   POST /v2/edit/tools/{tool_id}/estimate
  cost   {"check_cost": true} is a FREE dry run that generates nothing and charges nothing

Every paid call is a dry run by default. Pass --yes to spend credits.
Results arrive in base64_images OR output_urls; both are handled.

Subcommands:
  generate  text/img2img/reference generation in any style
  animate   rd_advanced_animation__<action>: animate an uploaded start frame (GIF or spritesheet)
  rotate8   rd_animation__8_dir_rotation: 8-direction sprite from prompt + up to 5 refs (80x80)
  pixelate  rd_pro__pixelate: turn a raster image into native pixel art
  tool      free/cheap edit tools: pixel_correction, palette_converter, k_centroid_downscale,
            color_reducer, background_remover, rotate, ...
  styles    list styles from /v2/styles/selector (live limits)
  balance   show prepaid balance

Examples:
  retro_diffusion.py generate --prompt "goblin merchant" --style rd_pro__default --size 128x128
  retro_diffusion.py generate --prompt "goblin merchant" --style rd_pro__default --size 128x128 --yes
  retro_diffusion.py rotate8 --prompt "astromech droid" --ref droid.png --spritesheet --out ./rot --yes
  retro_diffusion.py animate --input-image idle.png --action walking --frames 8 --spritesheet --yes
  retro_diffusion.py tool palette_converter --input-image sprite.png --palette pal.png --yes
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _secrets import get_api_key  # noqa: E402
from _images import open_image  # noqa: E402

try:
    from PIL import Image
except ImportError:
    print("Pillow required: uv pip install Pillow", file=sys.stderr)
    sys.exit(1)

BASE_URL = "https://api.retrodiffusion.ai/v2"
ENV_VAR = "RETRODIFFUSION_API_KEY"
POLL_SECONDS = 2.0
ANIMATION_ACTIONS = ("walking", "idle", "jump", "crouch", "attack", "destroy",
                     "custom_action", "subtle_motion")
FREE_TOOLS = {"pixel_correction", "palette_converter", "k_centroid_downscale",
              "color_reducer", "rotate"}
# Style price notes from llms.txt; check_cost is authoritative.
PRICE_NOTES = {
    "rd_pro": "$0.18/image", "rd_advanced_animation": "$0.14 ($0.25 custom_action/subtle_motion)",
    "rd_animation": "$0.07 ($0.25 any_animation/8_dir_rotation)", "rd_tile__tileset": "$0.10",
    "rd_plus": ">= $0.025/image", "rd_fast": ">= $0.015/image",
}


class RDError(RuntimeError):
    pass


# ---------------------------------------------------------------- HTTP layer

def _request(method: str, path: str, key: str | None, body: dict | None = None) -> dict:
    url = f"{BASE_URL}{path}"
    data = json.dumps(body).encode() if body is not None else None
    headers = {"Content-Type": "application/json"}
    if key:
        headers["X-RD-Token"] = key
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode(errors="replace")
        try:
            err = json.loads(payload).get("error", {})
            msg = f"{err.get('code', exc.code)}: {err.get('message', payload)} (request_id={err.get('request_id')})"
        except json.JSONDecodeError:
            msg = f"{exc.code}: {payload[:300]}"
        raise RDError(msg) from None
    except urllib.error.URLError as exc:
        raise RDError(f"network error: {exc.reason}") from None


def poll_task(task_id: str, key: str, quiet: bool = False) -> dict:
    """Poll /v2/inferences/tasks/{id} until succeeded/failed; return result payload."""
    started = time.time()
    while True:
        task = _request("GET", f"/inferences/tasks/{task_id}", key)
        status = task.get("status")
        if status == "succeeded":
            return task.get("result") or {}
        if status == "failed":
            err = task.get("error") or {}
            raise RDError(f"task {task_id} failed: {err.get('status_code')} {err.get('detail')}")
        if not quiet:
            print(f"  [{status}] {time.time() - started:5.1f}s", file=sys.stderr, end="\r")
        time.sleep(POLL_SECONDS)


# ------------------------------------------------------------- image helpers

def parse_size(s: str) -> tuple[int, int]:
    w, h = s.lower().split("x")
    return int(w), int(h)


def encode_rgb(path: str, matte: str = "00FF00", size: tuple[int, int] | None = None) -> str:
    """Raw base64 PNG, RGB with no alpha (RD requirement). Alpha is composited onto `matte`."""
    img = open_image(path)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, tuple(int(matte.lstrip("#")[i:i + 2], 16) for i in (0, 2, 4)) + (255,))
        bg.alpha_composite(img)
        img = bg
    img = img.convert("RGB")
    if size and img.size != size:
        img = img.resize(size, Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


def encode_raw(path: str) -> str:
    open_image(path)  # validate before uploading bytes
    return base64.b64encode(Path(path).read_bytes()).decode()


def write_results(result: dict, out_dir: Path, stem: str, key: str | None) -> list[Path]:
    """Write base64_images and/or output_urls to disk. Returns written paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for i, b64 in enumerate(result.get("base64_images") or []):
        raw = base64.b64decode(b64)
        ext = ".gif" if raw[:3] == b"GIF" else ".png"
        p = out_dir / f"{stem}_{i:02d}{ext}"
        p.write_bytes(raw)
        written.append(p)
    for i, url in enumerate(result.get("output_urls") or [], start=len(written)):
        req = urllib.request.Request(url, headers={"X-RD-Token": key} if key else {})
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read()
        ext = ".gif" if raw[:3] == b"GIF" else ".png"
        p = out_dir / f"{stem}_{i:02d}{ext}"
        p.write_bytes(raw)
        written.append(p)
    return written


# --------------------------------------------------------------- operations

def run_inference(body: dict, key: str | None, yes: bool, out_dir: Path, stem: str,
                  as_json: bool) -> dict:
    """Dry run (check_cost) unless --yes; on --yes submit, poll, write files."""
    family = body["prompt_style"].split("__")[0]
    if not yes:
        probe = {**body, "check_cost": True}
        if key:
            est = _request("POST", "/inferences", key, probe)
            cost = est.get("balance_cost")
            bal = est.get("remaining_balance")
            summary = {"dry_run": True, "style": body["prompt_style"], "size": f"{body['width']}x{body['height']}",
                       "num_images": body["num_images"], "estimated_cost_usd": cost, "balance_usd": bal}
        else:
            summary = {"dry_run": True, "style": body["prompt_style"], "size": f"{body['width']}x{body['height']}",
                       "num_images": body["num_images"], "estimated_cost_usd": None,
                       "note": f"no {ENV_VAR}; price guide {PRICE_NOTES.get(family, 'see llms.txt')}"}
        cost_line = (f"est ${summary['estimated_cost_usd']} (balance ${summary.get('balance_usd')})"
                     if summary["estimated_cost_usd"] is not None else summary["note"])
        print(json.dumps(summary, indent=2) if as_json else
              f"[dry run] {body['prompt_style']} {summary['size']} x{body['num_images']} -> {cost_line}. "
              f"Re-run with --yes to generate.")
        return summary
    if not key:
        get_api_key(ENV_VAR)  # exits with instructions
    accepted = _request("POST", "/inferences", key, body)
    task_id = accepted.get("task_id")
    if not task_id:  # sync-shaped response (v1 compatibility)
        result = accepted
    else:
        print(f"  task {task_id} accepted", file=sys.stderr)
        result = poll_task(task_id, key, quiet=as_json)
    paths = write_results(result, out_dir, stem, key)
    summary = {"dry_run": False, "style": body["prompt_style"], "model": result.get("model"),
               "cost_usd": result.get("balance_cost"), "balance_usd": result.get("remaining_balance"),
               "files": [str(p) for p in paths], "task_id": task_id}
    print(json.dumps(summary, indent=2) if as_json else
          f"Generated {len(paths)} file(s) for ${summary['cost_usd']} -> {', '.join(summary['files'])}")
    return summary


def run_tool(tool_id: str, fields: dict, key: str | None, yes: bool, out_dir: Path, stem: str,
             as_json: bool) -> dict:
    if not yes:
        if key:
            est = _request("POST", f"/edit/tools/{tool_id}/estimate", key, fields)
        else:
            est = {"note": f"no {ENV_VAR}; {'free tool' if tool_id in FREE_TOOLS else 'paid tool, see llms.txt'}"}
        summary = {"dry_run": True, "tool": tool_id, **{k: v for k, v in est.items() if k != "input_image"}}
        print(json.dumps(summary, indent=2, default=str) if as_json else
              f"[dry run] {tool_id}: {json.dumps({k: v for k, v in summary.items() if k not in ('dry_run', 'tool')}, default=str)}. Re-run with --yes.")
        return summary
    if not key:
        get_api_key(ENV_VAR)
    result = _request("POST", f"/edit/tools/{tool_id}", key, fields)
    paths = write_results(result, out_dir, stem, key)
    summary = {"dry_run": False, "tool": tool_id, "cost_usd": result.get("balance_cost"),
               "charged": result.get("charged"), "files": [str(p) for p in paths]}
    print(json.dumps(summary, indent=2) if as_json else
          f"{tool_id}: {len(paths)} file(s), cost ${summary['cost_usd']} -> {', '.join(summary['files'])}")
    return summary


# ----------------------------------------------------------------- commands

def cmd_generate(a, key):
    w, h = parse_size(a.size)
    body = {"prompt": a.prompt, "prompt_style": a.style, "width": w, "height": h, "num_images": a.n}
    if a.seed is not None:
        body["seed"] = a.seed
    if a.input_image:
        body["input_image"] = encode_rgb(a.input_image, a.matte)
        body["strength"] = a.strength
    if a.ref:
        body["reference_images"] = [encode_rgb(r, a.matte) for r in a.ref]
    if a.palette:
        body["input_palette"] = encode_raw(a.palette)
    if a.remove_bg:
        body["remove_bg"] = True
    if a.frames:
        body["frames_duration"] = a.frames
    if a.spritesheet:
        body["return_spritesheet"] = True
    if a.no_expand:
        body["bypass_prompt_expansion"] = True
    if a.tile:
        body["tile_x"] = body["tile_y"] = True
    return run_inference(body, key, a.yes, Path(a.out), a.stem or a.style, a.json)


def cmd_animate(a, key):
    if a.action not in ANIMATION_ACTIONS:
        sys.exit(f"--action must be one of {ANIMATION_ACTIONS}")
    src = open_image(a.input_image)
    w, h = parse_size(a.size) if a.size else src.size
    if not (32 <= w <= 256 and 32 <= h <= 256):
        sys.exit("advanced animation styles accept 32-256 px start frames")
    body = {"prompt": a.prompt or a.action.replace("_", " "),
            "prompt_style": f"rd_advanced_animation__{a.action}", "width": w, "height": h,
            "num_images": 1, "frames_duration": a.frames,
            "input_image": encode_rgb(a.input_image, a.matte, (w, h))}
    if a.seed is not None:
        body["seed"] = a.seed
    if a.spritesheet:
        body["return_spritesheet"] = True
    return run_inference(body, key, a.yes, Path(a.out), a.stem or f"anim_{a.action}", a.json)


def cmd_rotate8(a, key):
    if len(a.ref or []) > 5:
        sys.exit("rd_animation__8_dir_rotation accepts at most 5 reference images")
    body = {"prompt": a.prompt, "prompt_style": "rd_animation__8_dir_rotation", "width": 80,
            "height": 80, "num_images": 1}
    if a.ref:
        body["reference_images"] = [encode_rgb(r, a.matte) for r in a.ref]
    if a.seed is not None:
        body["seed"] = a.seed
    if a.spritesheet:
        body["return_spritesheet"] = True
    if a.remove_bg:
        body["remove_bg"] = True
    return run_inference(body, key, a.yes, Path(a.out), a.stem or "rotate8", a.json)


def cmd_pixelate(a, key):
    w, h = parse_size(a.size)
    body = {"prompt": a.prompt or "pixelate faithfully, keep colors and silhouette",
            "prompt_style": "rd_pro__pixelate", "width": w, "height": h, "num_images": a.n,
            "input_image": encode_rgb(a.input_image, a.matte)}
    if a.seed is not None:
        body["seed"] = a.seed
    if a.remove_bg:
        body["remove_bg"] = True
    return run_inference(body, key, a.yes, Path(a.out), a.stem or "pixelate", a.json)


def cmd_tool(a, key):
    fields: dict = {"input_image": encode_raw(a.input_image)}
    if a.palette:
        fields["input_palette"] = encode_raw(a.palette)
    if a.extra_image:
        fields["extra_input_image"] = encode_raw(a.extra_image)
    for kv in a.field or []:
        k, _, v = kv.partition("=")
        try:
            fields[k] = json.loads(v)
        except json.JSONDecodeError:
            fields[k] = v
    return run_tool(a.tool, fields, key, a.yes, Path(a.out), a.stem or a.tool, a.json)


def cmd_styles(a, key):
    if not key:
        get_api_key(ENV_VAR)
    q = []
    if a.model:
        q.append(f"model={a.model}")
    if a.tab:
        q.append(f"tab={a.tab}")
    data = _request("GET", "/styles/selector" + ("?" + "&".join(q) if q else ""), key)
    items = data if isinstance(data, list) else data.get("styles") or data.get("items") or data
    if a.json:
        print(json.dumps(items, indent=2))
        return
    for s in items:
        print(f"{s.get('prompt_style'):45s} {s.get('min_width')}-{s.get('max_width')}px "
              f"batch<={s.get('max_number_of_images')} "
              f"{'IMG_REQ ' if s.get('require_input_image') else ''}{'refs ' if s.get('supports_reference_images') else ''}"
              f"| {s.get('name')}")


def cmd_balance(a, key):
    if not key:
        get_api_key(ENV_VAR)
    print(json.dumps(_request("GET", "/inferences/credits", key), indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--api-key", help=f"override {ENV_VAR}")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp, n=True):
        sp.add_argument("--out", default="./rd-out", help="output directory")
        sp.add_argument("--stem", help="output filename stem")
        sp.add_argument("--seed", type=int)
        sp.add_argument("--matte", default="00FF00",
                        help="hex colour composited under transparent inputs (RD needs RGB, no alpha)")
        sp.add_argument("--yes", action="store_true", help="spend credits (default is a free cost check)")
        sp.add_argument("--json", action="store_true", help="machine-readable summary")
        if n:
            sp.add_argument("--n", type=int, default=1, help="num_images")

    g = sub.add_parser("generate", help="generate images in a style")
    g.add_argument("--prompt", required=True, help="subject only; never write 'pixel art'")
    g.add_argument("--style", default="rd_pro__default", help="prompt_style id (see `styles`)")
    g.add_argument("--size", default="128x128")
    g.add_argument("--input-image", help="img2img source")
    g.add_argument("--strength", type=float, default=0.75)
    g.add_argument("--ref", action="append", help="reference image (RD Pro, up to 9); repeatable")
    g.add_argument("--palette", help="PNG palette image for input_palette")
    g.add_argument("--remove-bg", action="store_true")
    g.add_argument("--frames", type=int, choices=(4, 6, 8, 10, 12, 16), help="animation styles only")
    g.add_argument("--spritesheet", action="store_true", help="animation styles: PNG sheet instead of GIF")
    g.add_argument("--no-expand", action="store_true", help="bypass LLM prompt expansion")
    g.add_argument("--tile", action="store_true")
    common(g)
    g.set_defaults(fn=cmd_generate)

    an = sub.add_parser("animate", help="animate an uploaded start frame")
    an.add_argument("--input-image", required=True)
    an.add_argument("--action", required=True, help="|".join(ANIMATION_ACTIONS))
    an.add_argument("--prompt", help="motion description (required for custom_action)")
    an.add_argument("--frames", type=int, default=8, choices=(4, 6, 8, 10, 12, 16))
    an.add_argument("--size", help="WxH override (default: start frame size, 32-256)")
    an.add_argument("--spritesheet", action="store_true")
    common(an, n=False)
    an.set_defaults(fn=cmd_animate)

    r = sub.add_parser("rotate8", help="8-direction rotation sheet (80x80)")
    r.add_argument("--prompt", required=True)
    r.add_argument("--ref", action="append", help="up to 5 reference images")
    r.add_argument("--spritesheet", action="store_true")
    r.add_argument("--remove-bg", action="store_true")
    common(r, n=False)
    r.set_defaults(fn=cmd_rotate8)

    px = sub.add_parser("pixelate", help="raster -> native pixel art (rd_pro__pixelate)")
    px.add_argument("--input-image", required=True)
    px.add_argument("--size", default="64x64", help="target pixel size 16-256")
    px.add_argument("--prompt")
    px.add_argument("--remove-bg", action="store_true")
    common(px)
    px.set_defaults(fn=cmd_pixelate)

    t = sub.add_parser("tool", help="edit tool: pixel_correction | palette_converter | k_centroid_downscale | "
                                    "color_reducer | background_remover | rotate | image_edit | ...")
    t.add_argument("tool")
    t.add_argument("--input-image", required=True)
    t.add_argument("--palette", help="palette PNG (palette_converter)")
    t.add_argument("--extra-image", help="extra_input_image (color_style_transfer)")
    t.add_argument("--field", action="append", help="key=value (JSON parsed), e.g. width=64 color_count=16")
    common(t, n=False)
    t.set_defaults(fn=cmd_tool)

    st = sub.add_parser("styles", help="list live styles and limits")
    st.add_argument("--model", choices=("rd_fast", "rd_plus", "rd_pro", "rd_mini"))
    st.add_argument("--tab", help="tab:image|tab:animation|tab:advanced-animation|tab:tileset")
    st.add_argument("--json", action="store_true")
    st.set_defaults(fn=cmd_styles)

    b = sub.add_parser("balance", help="prepaid balance")
    b.set_defaults(fn=cmd_balance)

    a = p.parse_args()
    key = get_api_key(ENV_VAR, a.api_key, required=False)
    try:
        a.fn(a, key)
    except RDError as exc:
        print(f"Retro Diffusion error: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
