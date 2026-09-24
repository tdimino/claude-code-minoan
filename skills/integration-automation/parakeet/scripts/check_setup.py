#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11,<3.14"
# dependencies = [
#     "parakeet-mlx>=0.5.2",
#     "mlx-audio>=0.5.5",
#     "numpy>=1.26",
# ]
# ///
"""Verify the MLX speech-to-text stack and, with --load, round-trip real speech.

Checks ffmpeg/ffprobe, the Metal device, and the Hugging Face cache for both
default models. `--load` synthesizes a phrase with macOS `say`, transcribes it
with each engine, and fails if a key word is missing.

Usage:
    check_setup.py            # fast: tools, device, cache (no downloads)
    check_setup.py --load     # also load models (downloads ~5 GB on first run)
"""

import argparse
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location("batch", Path(__file__).with_name("batch_transcribe.py"))
batch = importlib.util.module_from_spec(spec)
sys.modules["batch"] = batch  # @dataclass resolves annotations via sys.modules
spec.loader.exec_module(batch)

PHRASE = "Star Destroyer approaching the Rebel base on Hoth."
KEY_WORDS = {"destroyer", "rebel", "base"}


def report(label: str, ok: bool, detail: str = "") -> bool:
    print(f"  [{'OK' if ok else 'FAIL'}] {label}{f': {detail}' if detail else ''}")
    return ok


def cache_state(repo_id: str) -> str:
    from huggingface_hub import scan_cache_dir

    for repo in scan_cache_dir().repos:
        if repo.repo_id == repo_id:
            return f"cached ({repo.size_on_disk / 1e9:.2f} GB) at {repo.repo_path}"
    return "not cached (downloads on first use)"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--load", action="store_true", help="load both models and transcribe a spoken phrase")
    args = parser.parse_args()

    import mlx.core as mx

    ok = True
    print("Tools")
    for tool in ("ffmpeg", "ffprobe", "uv"):
        ok &= report(tool, shutil.which(tool) is not None, shutil.which(tool) or "missing")
    print("Runtime")
    ok &= report("Metal", mx.metal.is_available(), str(mx.default_device()))
    for package, installed in batch.package_versions().items():
        ok &= report(package, installed != "missing", installed)
    print("Models (informational; missing models download on first use)")
    for engine, repo_id in batch.DEFAULT_MODELS.items():
        print(f"  [info] {engine} {repo_id}: {cache_state(repo_id)}")

    if args.load:
        print("Round trip")
        say = shutil.which("say")
        if say is None:
            ok &= report("say", False, "macOS `say` unavailable; skipped")
        else:
            with tempfile.TemporaryDirectory() as tmp:
                sample = Path(tmp) / "phrase.aiff"
                subprocess.run([say, "-o", str(sample), PHRASE], check=True)
                clip = batch.load_clip(sample, pad_under=2.0, pad_s=0.75)
                loaders = {"parakeet": lambda: batch.ParakeetEngine(batch.DEFAULT_MODELS["parakeet"], beam=1),
                           "qwen3": lambda: batch.Qwen3Engine(batch.DEFAULT_MODELS["qwen3"], [], "English")}
                for name, load in loaders.items():
                    try:
                        text = load().transcribe(clip)["text"]
                    except Exception as error:
                        ok &= report(name, False, f"{type(error).__name__}: {error}")
                        continue
                    hit = KEY_WORDS <= set(batch.normalize(text).split())
                    ok &= report(name, hit, repr(text))

    print("RESULT:", "OK" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
