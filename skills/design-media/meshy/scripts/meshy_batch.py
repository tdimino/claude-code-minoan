#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["requests"]
# ///
"""
Batch 3D model generation from a JSON manifest file.

Usage:
    uv run meshy_batch.py manifest.json                              # generate all
    uv run meshy_batch.py manifest.json --models fighter carrier     # specific models
    uv run meshy_batch.py manifest.json --list                       # show model IDs
    uv run meshy_batch.py manifest.json --dry-run                    # preview without API calls
    uv run meshy_batch.py manifest.json --status                     # check last run status
    uv run meshy_batch.py manifest.json --skip-refine --output ./staging/
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from _meshy_utils import LOG_DIR, MeshyClient, log_event


def load_manifest(path: str) -> dict:
    """Load and validate a batch manifest JSON file."""
    manifest_path = Path(path)
    if not manifest_path.exists():
        print(f"ERROR: Manifest not found: {path}", file=sys.stderr)
        sys.exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    if "models" not in manifest or not manifest["models"]:
        print("ERROR: Manifest must contain a non-empty 'models' array.", file=sys.stderr)
        sys.exit(1)

    return manifest


def get_model_config(model: dict, defaults: dict) -> dict:
    """Merge per-model config with defaults."""
    return {
        "id": model["id"],
        "prompt": model["prompt"],
        "negative_prompt": model.get("negative_prompt", defaults.get("negative_prompt", "")),
        "model_type": model.get("model_type", defaults.get("model_type", "lowpoly")),
        "skip_refine": model.get("skip_refine", defaults.get("skip_refine", False)),
        "enable_pbr": model.get("enable_pbr", defaults.get("enable_pbr", True)),
        "format": model.get("format", defaults.get("format", "glb")),
        "output_name": model.get("output_name", f"{model['id']}.{model.get('format', defaults.get('format', 'glb'))}"),
    }


def cmd_list(manifest: dict):
    """List model IDs and prompts from manifest."""
    defaults = manifest.get("defaults", {})
    print("Models in manifest:\n")
    for model in manifest["models"]:
        cfg = get_model_config(model, defaults)
        print(f"  {cfg['id']:24s}  {cfg['prompt'][:60]}...")
    total = len(manifest["models"])
    print(f"\n  Total: {total} models")
    credits_preview = total * 5
    credits_full = total * 15
    print(f"  Credits needed: ~{credits_preview} (preview only) / ~{credits_full} (preview + refine)")


def cmd_dry_run(manifest: dict, output_dir: str):
    """Preview what would be generated without calling API."""
    defaults = manifest.get("defaults", {})
    print("Dry run — no API calls:\n")
    for model in manifest["models"]:
        cfg = get_model_config(model, defaults)
        mode = "preview only" if cfg["skip_refine"] else "preview + refine"
        print(f"  {cfg['id']:24s}  → {output_dir}/{cfg['output_name']}  ({mode})")


def cmd_status(manifest: dict):
    """Check status of tasks from last batch run log."""
    log_files = sorted(LOG_DIR.glob("batch-*.jsonl"), reverse=True)
    if not log_files:
        print("No batch run logs found.")
        return

    latest = log_files[0]
    print(f"Latest batch log: {latest.name}\n")

    entries = []
    with open(latest) as f:
        for line in f:
            entries.append(json.loads(line))

    # Show last status per model
    model_status: dict[str, dict] = {}
    for e in entries:
        mid = e.get("model_id", "?")
        model_status[mid] = e

    for mid, e in model_status.items():
        status = e.get("status", e.get("action", "?"))
        task_id = e.get("task_id", "?")
        print(f"  {mid:24s}  {status:16s}  {task_id}")


def cmd_generate(manifest: dict, args):
    """Generate models from manifest."""
    defaults = manifest.get("defaults", {})
    output_dir = Path(args.output or defaults.get("output_dir", "./output"))

    models = manifest["models"]
    if args.models:
        model_ids = set(args.models)
        models = [m for m in models if m["id"] in model_ids]
        missing = model_ids - {m["id"] for m in models}
        if missing:
            print(f"WARNING: Model IDs not in manifest: {missing}", file=sys.stderr)

    total = len(models)
    if total == 0:
        print("No models to generate.")
        return

    # Batch run log
    batch_ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    batch_log = LOG_DIR / f"batch-{batch_ts}.jsonl"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    def batch_log_event(event: dict):
        with open(batch_log, "a") as f:
            f.write(json.dumps({**event, "ts": datetime.now(timezone.utc).isoformat()}) + "\n")

    client = MeshyClient(api_key=args.api_key)

    skip_refine_override = args.skip_refine

    if not args.quiet:
        mode = "preview only" if skip_refine_override else "manifest settings"
        print(f"Meshy Batch Generator")
        print(f"=====================")
        print(f"Models: {total}")
        print(f"Output: {output_dir}")
        print(f"Mode: {mode}")
        print()

    succeeded = 0
    failed = 0

    for i, model in enumerate(models, 1):
        cfg = get_model_config(model, defaults)
        skip = skip_refine_override or cfg["skip_refine"]

        # Strip extension from output_name for generate_full (it adds the extension)
        name_base = cfg["output_name"]
        for ext in (".glb", ".gltf", ".usdz", ".fbx"):
            if name_base.endswith(ext):
                name_base = name_base[:-len(ext)]
                break

        if not args.quiet:
            print(f"\n[{i}/{total}] {cfg['id']}")

        batch_log_event({"action": "start", "model_id": cfg["id"], "prompt": cfg["prompt"][:100]})

        fmt = args.format if args.format else cfg["format"]

        success, path = client.generate_full(
            cfg["prompt"],
            negative_prompt=cfg["negative_prompt"],
            model_type=cfg["model_type"],
            skip_refine=skip,
            output_dir=output_dir,
            output_name=name_base,
            format=fmt,
            poll_interval=args.poll_interval,
            timeout=args.timeout,
            quiet=args.quiet,
            enable_pbr=cfg["enable_pbr"],
        )

        if success:
            succeeded += 1
            batch_log_event({"action": "succeeded", "model_id": cfg["id"], "path": str(path)})
        else:
            failed += 1
            batch_log_event({"action": "failed", "model_id": cfg["id"]})

    # Summary
    if args.json:
        print(json.dumps({
            "succeeded": succeeded,
            "failed": failed,
            "total": total,
            "output_dir": str(output_dir),
            "batch_log": str(batch_log),
        }))
    else:
        print(f"\n{'='*50}")
        print(f"  Batch complete!")
        print(f"  Succeeded: {succeeded}/{total}")
        if failed:
            print(f"  Failed: {failed}/{total}")
        print(f"  Output: {output_dir}/")
        print(f"  Log: {batch_log}")
        print(f"{'='*50}")


def main():
    parser = argparse.ArgumentParser(description="Batch 3D model generation from JSON manifest")
    parser.add_argument("manifest", help="Path to JSON manifest file")
    parser.add_argument("--models", nargs="+", help="Generate specific model IDs only")
    parser.add_argument("--list", action="store_true", help="List model IDs and prompts")
    parser.add_argument("--dry-run", action="store_true", help="Preview without API calls")
    parser.add_argument("--status", action="store_true", help="Check status of last batch run")
    parser.add_argument("--skip-refine", action="store_true", help="Override: preview only for all models")
    parser.add_argument("--output", default="", help="Override manifest output directory")
    parser.add_argument("--format", default="", help="Override manifest format")
    parser.add_argument("--api-key", help="Override MESHY_API_KEY")
    parser.add_argument("--poll-interval", type=int, default=5, help="Seconds between polls")
    parser.add_argument("--timeout", type=int, default=600, help="Max wait seconds per model")
    parser.add_argument("--quiet", action="store_true", help="Minimal output")
    parser.add_argument("--json", action="store_true", help="Machine-readable output")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest)

    if args.list:
        cmd_list(manifest)
    elif args.dry_run:
        cmd_dry_run(manifest, args.output or manifest.get("defaults", {}).get("output_dir", "./output"))
    elif args.status:
        cmd_status(manifest)
    else:
        cmd_generate(manifest, args)


if __name__ == "__main__":
    main()
