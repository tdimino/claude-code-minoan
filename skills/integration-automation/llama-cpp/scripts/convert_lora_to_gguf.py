#!/usr/bin/env python3
"""
Convert a LoRA adapter to a merged, quantized GGUF model.

Supports two input formats:
  1. GGUF LoRA + GGUF base → llama-export-lora → llama-quantize
  2. HuggingFace LoRA + HF base → PEFT merge → convert_hf_to_gguf.py → llama-quantize

Usage:
  # GGUF LoRA (simplest — uses llama-export-lora directly)
  python3 convert_lora_to_gguf.py --base base.gguf --lora lora.gguf --output merged-q4.gguf --quantize q4_k_m

  # HuggingFace LoRA (full pipeline)
  python3 convert_lora_to_gguf.py --base NousResearch/Hermes-2-Mistral-7B-DPO --lora ./kothar-lora --output kothar-q4.gguf --quantize q4_k_m

  # Ollama base model + GGUF LoRA
  python3 convert_lora_to_gguf.py --base qwen2.5:7b --lora lora.gguf --output merged-q4.gguf --quantize q4_k_m

Environment:
  LLAMA_CPP_DIR   Path to llama.cpp source (for convert_hf_to_gguf.py). Auto-cloned if missing.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
LLAMA_CPP_DEFAULT = Path.home() / ".local" / "share" / "llama.cpp"
VALID_QUANT_TYPES = {
    "q2_k", "q3_k_s", "q3_k_m", "q3_k_l",
    "q4_0", "q4_1", "q4_k_s", "q4_k_m",
    "q5_0", "q5_1", "q5_k_s", "q5_k_m",
    "q6_k", "q8_0", "f16", "f32",
}


def run(cmd, **kwargs):
    """Run a command, printing it first."""
    print(f"  $ {' '.join(str(c) for c in cmd)}")
    result = subprocess.run(cmd, **kwargs)
    if result.returncode != 0:
        print(f"Error: command exited with {result.returncode}", file=sys.stderr)
        sys.exit(result.returncode)
    return result


def resolve_ollama_model(name):
    """Resolve an Ollama model name to its GGUF blob path."""
    result = subprocess.run(
        [str(SCRIPT_DIR / "ollama_model_path.sh"), name],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def is_gguf(path):
    """Check if a file is GGUF format (magic bytes)."""
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"GGUF"
    except (OSError, IOError):
        return False


def ensure_llama_cpp_source(llama_dir):
    """Ensure llama.cpp source is available for convert_hf_to_gguf.py."""
    converter = llama_dir / "convert_hf_to_gguf.py"
    if converter.exists():
        return converter

    print(f"\nllama.cpp source not found at {llama_dir}")
    print("Cloning llama.cpp (sparse — conversion scripts only)...")
    llama_dir.parent.mkdir(parents=True, exist_ok=True)
    run(["git", "clone", "--depth=1", "--filter=blob:none", "--sparse",
         "https://github.com/ggerganov/llama.cpp.git", str(llama_dir)])
    run(["git", "-C", str(llama_dir), "sparse-checkout", "set",
         "convert_hf_to_gguf.py", "convert_lora_to_gguf.py", "gguf-py"])

    # Install gguf Python package from source
    gguf_py = llama_dir / "gguf-py"
    if gguf_py.exists():
        run([sys.executable, "-m", "pip", "install", "-e", str(gguf_py), "-q"])

    if not converter.exists():
        print(f"Error: {converter} not found after clone", file=sys.stderr)
        sys.exit(1)
    return converter


def pipeline_gguf(base_gguf, lora_gguf, output, quantize):
    """Pipeline: GGUF base + GGUF LoRA → merged → quantized."""
    print("\n=== Pipeline: GGUF LoRA merge ===\n")

    if quantize:
        # Merge to F16 first, then quantize
        with tempfile.NamedTemporaryFile(suffix="-f16.gguf", delete=False) as f:
            merged_f16 = f.name
        try:
            print("Step 1: Merging LoRA into base (F16)...")
            run(["llama-export-lora",
                 "-m", str(base_gguf),
                 "--lora", str(lora_gguf),
                 "-o", merged_f16])

            print(f"\nStep 2: Quantizing to {quantize}...")
            run(["llama-quantize", merged_f16, str(output), quantize])
        finally:
            if os.path.exists(merged_f16):
                os.unlink(merged_f16)
    else:
        print("Merging LoRA into base (F16 output)...")
        run(["llama-export-lora",
             "-m", str(base_gguf),
             "--lora", str(lora_gguf),
             "-o", str(output)])

    print(f"\nDone: {output} ({os.path.getsize(output) / 1e9:.2f} GB)")


def pipeline_hf(base_hf, lora_hf, output, quantize, llama_cpp_dir):
    """Pipeline: HF base + HF LoRA → PEFT merge → GGUF convert → quantize."""
    print("\n=== Pipeline: HuggingFace LoRA merge ===\n")

    try:
        from peft import PeftModel
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        print("Error: peft and transformers are required for HuggingFace LoRA conversion.", file=sys.stderr)
        print("Install with: uv pip install --system peft transformers torch", file=sys.stderr)
        sys.exit(1)

    converter = ensure_llama_cpp_source(llama_cpp_dir)

    with tempfile.TemporaryDirectory(prefix="llama-merge-") as tmpdir:
        merged_hf_dir = Path(tmpdir) / "merged-hf"
        merged_gguf_f16 = Path(tmpdir) / "merged-f16.gguf"

        # Step 1: Merge with PEFT
        print("Step 1: Loading base model + LoRA adapter...")
        tokenizer = AutoTokenizer.from_pretrained(str(base_hf))
        model = AutoModelForCausalLM.from_pretrained(
            str(base_hf), torch_dtype="auto", low_cpu_mem_usage=True,
            device_map="cpu"
        )
        print("  Merging LoRA weights...")
        model = PeftModel.from_pretrained(model, str(lora_hf))
        model = model.merge_and_unload()
        print(f"  Saving merged model to {merged_hf_dir}...")
        model.save_pretrained(str(merged_hf_dir))
        tokenizer.save_pretrained(str(merged_hf_dir))
        del model, tokenizer  # free memory

        # Step 2: Convert to GGUF
        print("\nStep 2: Converting to GGUF (F16)...")
        run([sys.executable, str(converter),
             str(merged_hf_dir),
             "--outfile", str(merged_gguf_f16),
             "--outtype", "f16"])

        # Step 3: Quantize
        if quantize:
            print(f"\nStep 3: Quantizing to {quantize}...")
            run(["llama-quantize", str(merged_gguf_f16), str(output), quantize])
        else:
            shutil.move(str(merged_gguf_f16), str(output))

    print(f"\nDone: {output} ({os.path.getsize(output) / 1e9:.2f} GB)")


def main():
    parser = argparse.ArgumentParser(
        description="Convert LoRA adapter to merged, quantized GGUF model"
    )
    parser.add_argument("--base", required=True,
                        help="Base model: GGUF file, Ollama name, or HuggingFace model ID/path")
    parser.add_argument("--lora", required=True,
                        help="LoRA adapter: GGUF file or HuggingFace adapter path/ID")
    parser.add_argument("--output", "-o", required=True,
                        help="Output GGUF file path")
    parser.add_argument("--quantize", "-q", default=None,
                        help="Quantization type (e.g., q4_k_m, q5_k_m, q8_0). Omit for F16.")
    parser.add_argument("--llama-cpp-dir", default=None,
                        help=f"Path to llama.cpp source (default: {LLAMA_CPP_DEFAULT})")
    args = parser.parse_args()

    llama_cpp_dir = Path(args.llama_cpp_dir) if args.llama_cpp_dir else Path(
        os.environ.get("LLAMA_CPP_DIR", str(LLAMA_CPP_DEFAULT))
    )

    if args.quantize and args.quantize.lower() not in VALID_QUANT_TYPES:
        print(f"Error: Unknown quantization type '{args.quantize}'", file=sys.stderr)
        print(f"Valid types: {', '.join(sorted(VALID_QUANT_TYPES))}", file=sys.stderr)
        sys.exit(1)

    base = args.base
    lora = args.lora
    output = Path(args.output)

    # Resolve base model
    base_path = Path(base)
    if base_path.exists() and is_gguf(base_path):
        base_is_gguf = True
    else:
        # Try Ollama resolution
        resolved = resolve_ollama_model(base)
        if resolved and is_gguf(resolved):
            base_path = Path(resolved)
            base_is_gguf = True
            print(f"Resolved Ollama model '{base}' → {base_path}")
        else:
            base_is_gguf = False

    # Resolve LoRA format
    lora_path = Path(lora)
    lora_is_gguf = lora_path.exists() and is_gguf(lora_path)

    # Route to appropriate pipeline
    if base_is_gguf and lora_is_gguf:
        pipeline_gguf(base_path, lora_path, output, args.quantize)
    elif not base_is_gguf and not lora_is_gguf:
        pipeline_hf(base, lora, output, args.quantize, llama_cpp_dir)
    elif base_is_gguf and not lora_is_gguf:
        print("Error: GGUF base + HuggingFace LoRA is not directly supported.", file=sys.stderr)
        print("Either:", file=sys.stderr)
        print("  1. Convert LoRA to GGUF first (use llama.cpp's convert_lora_to_gguf.py)", file=sys.stderr)
        print("  2. Use the HuggingFace base model instead of the GGUF", file=sys.stderr)
        sys.exit(1)
    else:
        print("Error: HuggingFace base + GGUF LoRA is not supported.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
