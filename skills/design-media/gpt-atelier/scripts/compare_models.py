#!/usr/bin/env python3
"""
Generate the same prompt across multiple OpenAI image models and produce
an HTML comparison page.

Usage:
    python compare_models.py "prompt text" [options]
    python compare_models.py "prompt text" --models gpt-image-1 gpt-image-2 dall-e-3
    python compare_models.py "prompt text" --all

Env: OPENAI_API_KEY
"""

import argparse
import base64
import html
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from openai_images import GPTAtelierClient, VALID_QUALITIES, VALID_FORMATS

ALL_IMAGE_MODELS = [
    "dall-e-2", "dall-e-3",
    "gpt-image-1-mini", "gpt-image-1", "gpt-image-1.5",
    "gpt-image-2",
]

DEFAULT_COMPARE = ["gpt-image-1", "gpt-image-2"]

MODEL_NOTES = {
    "dall-e-2": "Legacy. 256/512/1024px.",
    "dall-e-3": "Legacy. Revised prompts. 1024/1792px.",
    "gpt-image-1-mini": "Cheapest ($0.006/img low). Fast iteration.",
    "gpt-image-1": "Multimodal native. Standard + high quality.",
    "gpt-image-1.5": "Region-aware editing. 4x faster than v2.",
    "gpt-image-2": "Reasoning-based. ~99% text rendering. 4K. Streaming.",
    "chatgpt-image-latest": "Alias for latest ChatGPT image model.",
}

DALLE_SIZES = {
    "dall-e-2": "1024x1024",
    "dall-e-3": "1024x1024",
}


def generate_one(model, prompt, size, quality, output_format, output_dir):
    """Generate one image, return (path, error, elapsed_ms)."""
    is_dalle = model.startswith("dall-e")
    effective_size = DALLE_SIZES.get(model, size) if is_dalle else size

    try:
        client = GPTAtelierClient(model=model)
    except ValueError as e:
        return None, str(e), 0

    t0 = time.time()
    try:
        kwargs = {"prompt": prompt, "n": 1, "output_format": output_format}
        if effective_size:
            kwargs["size"] = effective_size
        if not is_dalle:
            kwargs["quality"] = quality
        response = client.client.images.generate(model=model, **kwargs)
        elapsed = int((time.time() - t0) * 1000)

        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)
        ts = time.strftime("%Y%m%d_%H%M%S")
        safe_model = model.replace(".", "-")

        img_data = response.data[0]
        if hasattr(img_data, "b64_json") and img_data.b64_json:
            path = out / f"compare_{safe_model}_{ts}.{output_format}"
            path.write_bytes(base64.b64decode(img_data.b64_json))
            return path, None, elapsed
        elif hasattr(img_data, "url") and img_data.url:
            return img_data.url, None, elapsed
        else:
            return None, "No image data in response", elapsed

    except Exception as e:
        elapsed = int((time.time() - t0) * 1000)
        err_msg = str(e)
        if "verified" in err_msg.lower():
            err_msg = "Organization verification required"
        return None, err_msg, elapsed


def build_html(prompt, results, output_dir, available_models=None):
    """Build the comparison HTML page."""
    date = time.strftime("%Y-%m-%d")
    escaped_prompt = html.escape(prompt)

    cards = []
    for model, path, error, elapsed_ms in results:
        notes = MODEL_NOTES.get(model, "")
        elapsed_str = f"{elapsed_ms / 1000:.1f}s" if elapsed_ms else ""

        if error:
            error_escaped = html.escape(error)
            verify_link = ""
            if "verification" in error.lower():
                verify_link = (
                    '<div style="font-size:0.75rem;color:#888;margin-top:0.5rem;">'
                    '<a href="https://platform.openai.com/settings/organization/general" '
                    'style="color:#f87171;">Verify organization &rarr;</a></div>'
                )
            cards.append(f'''  <div class="card" style="border-color:#3a1e1e;">
    <div style="height:480px;display:flex;align-items:center;justify-content:center;background:#1a1010;">
      <div style="text-align:center;color:#f87171;">
        <div style="font-size:2rem;margin-bottom:1rem;">&#x1F512;</div>
        <div style="font-size:0.9rem;">{error_escaped}</div>
        {verify_link}
      </div>
    </div>
    <div class="card-meta">
      <h2>{model}</h2>
      <span class="tag blocked">error</span>
      <p>{notes}</p>
    </div>
  </div>''')
        else:
            if isinstance(path, Path):
                src = path.name
            else:
                src = str(path)
            size_str = ""
            if isinstance(path, Path) and path.exists():
                size_mb = path.stat().st_size / (1024 * 1024)
                size_str = f" &middot; {size_mb:.1f} MB"
            cards.append(f'''  <div class="card">
    <img src="{src}" alt="{model} output">
    <div class="card-meta">
      <h2>{model}</h2>
      <span class="tag">{elapsed_str}</span>
      <p>{notes}{size_str}</p>
    </div>
  </div>''')

    cards_html = "\n".join(cards)

    model_rows = []
    if available_models:
        for m in available_models:
            notes = MODEL_NOTES.get(m, "")
            result_entry = next((r for r in results if r[0] == m), None)
            if result_entry and not result_entry[2]:
                status = '<span class="status-dot green"></span>Generated'
            elif result_entry and result_entry[2]:
                status = '<span class="status-dot red"></span>Error'
            else:
                status = '<span class="status-dot yellow"></span>Not tested'
            model_rows.append(f"    <tr><td>{m}</td><td>{status}</td><td>{notes}</td></tr>")

    models_table = ""
    if model_rows:
        rows = "\n".join(model_rows)
        models_table = f'''
<h2 style="font-size:1rem;margin-bottom:1rem;color:#fff;">Available Image Models</h2>
<table class="models-table">
  <thead><tr><th>Model</th><th>Status</th><th>Notes</th></tr></thead>
  <tbody>
{rows}
  </tbody>
</table>'''

    page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GPT Atelier — Model Comparison</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family:'SF Mono','Fira Code',monospace; background:#0a0a0a; color:#e0e0e0; padding:2rem; }}
  h1 {{ font-size:1.5rem; margin-bottom:0.5rem; color:#fff; }}
  .subtitle {{ color:#888; margin-bottom:2rem; font-size:0.85rem; }}
  .prompt {{ background:#1a1a1a; border:1px solid #333; border-radius:8px; padding:1rem; margin-bottom:2rem; font-style:italic; color:#ccc; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(480px,1fr)); gap:2rem; margin-bottom:2rem; }}
  .card {{ background:#111; border:1px solid #222; border-radius:12px; overflow:hidden; }}
  .card img {{ width:100%; display:block; }}
  .card-meta {{ padding:1rem; }}
  .card-meta h2 {{ font-size:1rem; color:#fff; margin-bottom:0.5rem; }}
  .card-meta .tag {{ display:inline-block; background:#1e3a2f; color:#4ade80; padding:2px 8px; border-radius:4px; font-size:0.75rem; margin-right:0.5rem; }}
  .card-meta .tag.blocked {{ background:#3a1e1e; color:#f87171; }}
  .card-meta p {{ color:#888; font-size:0.8rem; margin-top:0.5rem; }}
  .models-table {{ width:100%; border-collapse:collapse; margin-top:2rem; }}
  .models-table th, .models-table td {{ text-align:left; padding:0.5rem 1rem; border-bottom:1px solid #222; font-size:0.85rem; }}
  .models-table th {{ color:#888; font-weight:normal; text-transform:uppercase; font-size:0.7rem; letter-spacing:0.05em; }}
  .models-table td {{ color:#ccc; }}
  .status-dot {{ width:8px; height:8px; border-radius:50%; display:inline-block; margin-right:0.5rem; }}
  .status-dot.green {{ background:#4ade80; }}
  .status-dot.yellow {{ background:#facc15; }}
  .status-dot.red {{ background:#f87171; }}
</style>
</head>
<body>

<h1>GPT Atelier — Model Comparison</h1>
<p class="subtitle">{date} &middot; Subquadratic AI Workspace</p>

<div class="prompt">Prompt: "{escaped_prompt}"</div>

<div class="grid">
{cards_html}
</div>

{models_table}

</body>
</html>'''

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    html_path = out / f"compare_{ts}.html"
    html_path.write_text(page)
    return html_path


def main():
    parser = argparse.ArgumentParser(description="Compare image models side-by-side")
    parser.add_argument("prompt", help="Text description of the image to generate")
    parser.add_argument("--models", nargs="+", default=None,
                        help=f"Models to compare (default: {', '.join(DEFAULT_COMPARE)})")
    parser.add_argument("--all", action="store_true",
                        help="Compare all known image models")
    parser.add_argument("--size", default="1024x1024", help="Image size (WxH)")
    parser.add_argument("--quality", default="high", choices=VALID_QUALITIES)
    parser.add_argument("--format", dest="output_format", default="png", choices=VALID_FORMATS)
    parser.add_argument("--output", default="./output", help="Output directory")
    parser.add_argument("--open", action="store_true", help="Open HTML page after generation")
    parser.add_argument("--list-models", action="store_true", help="List available image models and exit")
    args = parser.parse_args()

    if args.list_models:
        try:
            from openai import OpenAI
            client = OpenAI()
            models = client.models.list()
            image_models = sorted([
                m.id for m in models
                if any(k in m.id.lower() for k in ["image", "dall"])
            ])
            for m in image_models:
                note = MODEL_NOTES.get(m, "")
                print(f"  {m:<30} {note}")
        except Exception as e:
            print(f"Error listing models: {e}", file=sys.stderr)
            for m in ALL_IMAGE_MODELS:
                print(f"  {m:<30} {MODEL_NOTES.get(m, '')}")
        return

    models = ALL_IMAGE_MODELS if args.all else (args.models or DEFAULT_COMPARE)

    print(f"Comparing {len(models)} models...", file=sys.stderr)
    print(f"Prompt: {args.prompt[:80]}{'...' if len(args.prompt) > 80 else ''}", file=sys.stderr)

    results = []
    for model in models:
        print(f"  [{model}] generating...", file=sys.stderr, end="", flush=True)
        path, error, elapsed = generate_one(
            model, args.prompt, args.size, args.quality, args.output_format, args.output
        )
        if error:
            print(f" error: {error[:60]}", file=sys.stderr)
        else:
            print(f" done ({elapsed}ms)", file=sys.stderr)
        results.append((model, path, error, elapsed))

    all_models = None
    try:
        from openai import OpenAI
        client = OpenAI()
        all_models = sorted([
            m.id for m in client.models.list()
            if any(k in m.id.lower() for k in ["image", "dall"])
        ])
    except Exception:
        all_models = ALL_IMAGE_MODELS

    html_path = build_html(args.prompt, results, args.output, all_models)
    print(f"\nComparison page: {html_path}")

    if args.open:
        import subprocess
        subprocess.run(["open", str(html_path)], check=False)


if __name__ == "__main__":
    main()
