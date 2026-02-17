#!/usr/bin/env python3
"""
li_ingest.py — Prepare RLAMA-optimized documents and create/update collection.

Usage:
    uv run li_ingest.py                    # Full pipeline: export + ingest
    uv run li_ingest.py --prepare-only     # Just prepare docs (no RLAMA create)
    uv run li_ingest.py --rebuild          # Delete and recreate collection

Requires:
    - Run li_parse.py first to generate parsed.json
    - RLAMA + Ollama running for ingestion (optional for --prepare-only)
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
PARSED_FILE = DATA_DIR / "parsed.json"
RLAMA_DIR = DATA_DIR / "rlama"
COLLECTION_NAME = "linkedin-tdimino"

# Import the export function from li_export
sys.path.insert(0, str(Path(__file__).parent))
from li_export import export_rlama, load_data


def check_rlama() -> bool:
    """Check if RLAMA is available."""
    try:
        result = subprocess.run(["rlama", "--version"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def check_ollama() -> bool:
    """Check if Ollama is running."""
    try:
        result = subprocess.run(["ollama", "list"], capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def collection_exists() -> bool:
    """Check if the RLAMA collection already exists."""
    try:
        result = subprocess.run(
            ["rlama", "list"],
            capture_output=True, text=True, timeout=10
        )
        return COLLECTION_NAME in result.stdout
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def delete_collection() -> bool:
    """Delete existing RLAMA collection."""
    try:
        result = subprocess.run(
            ["rlama", "delete", COLLECTION_NAME],
            capture_output=True, text=True, timeout=30
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def create_collection() -> bool:
    """Create RLAMA collection from prepared documents."""
    print(f"\nCreating RLAMA collection: {COLLECTION_NAME}")
    print(f"  Source: {RLAMA_DIR}")
    print(f"  Chunking: fixed/600/100")
    print()

    try:
        result = subprocess.run(
            [
                "rlama", "rag",
                "qwen2.5:7b",
                COLLECTION_NAME,
                str(RLAMA_DIR),
                "--chunking=fixed",
                "--chunk-size=600",
                "--chunk-overlap=100",
            ],
            capture_output=True,
            text=True,
            timeout=300,
        )

        if result.returncode != 0:
            print(f"Error: rlama rag failed (exit {result.returncode})", file=sys.stderr)
            if result.stderr:
                print(f"  stderr: {result.stderr.strip()}", file=sys.stderr)
            return False

        print(f"\nCollection '{COLLECTION_NAME}' created.")

        # Add reranker
        print("Adding reranker...")
        rerank_result = subprocess.run(
            ["rlama", "add-reranker", COLLECTION_NAME],
            capture_output=True,
            text=True,
            timeout=120,
        )

        if rerank_result.returncode == 0:
            print("Reranker added.")
        else:
            print("Warning: Failed to add reranker (non-critical).", file=sys.stderr)

        return True

    except FileNotFoundError:
        print("Error: rlama not found. Install RLAMA first.", file=sys.stderr)
        return False
    except subprocess.TimeoutExpired:
        print("Error: RLAMA ingestion timed out.", file=sys.stderr)
        return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Prepare and ingest LinkedIn data into RLAMA")
    parser.add_argument("--prepare-only", action="store_true", help="Only prepare documents, skip RLAMA ingestion")
    parser.add_argument("--rebuild", action="store_true", help="Delete and recreate collection")
    parser.add_argument("--data", help=f"Path to parsed.json (default: {PARSED_FILE})")
    parser.add_argument("--output", "-o", help=f"RLAMA output directory (default: {RLAMA_DIR})")
    args = parser.parse_args()

    data_path = Path(args.data) if args.data else None
    rlama_dir = Path(args.output) if args.output else RLAMA_DIR

    # Load data
    data = load_data(data_path)

    # Prepare RLAMA documents
    print("Preparing RLAMA-optimized documents...")

    if rlama_dir.exists():
        shutil.rmtree(rlama_dir)

    file_count = export_rlama(data, rlama_dir)
    print(f"Prepared {file_count} RLAMA documents in {rlama_dir}")

    # Show file summary
    total_size = sum(f.stat().st_size for f in rlama_dir.glob("*.md"))
    print(f"Total size: {total_size / 1024:.1f} KB")
    print()

    for f in sorted(rlama_dir.glob("*.md")):
        size = f.stat().st_size
        print(f"  {f.name:<45} {size / 1024:.1f} KB")

    if args.prepare_only:
        print(f"\n--prepare-only: Skipping RLAMA ingestion.")
        print(f"\nTo create collection manually:")
        print(f"  rlama rag qwen2.5:7b {COLLECTION_NAME} {rlama_dir} \\")
        print(f"    --chunking=fixed --chunk-size=600 --chunk-overlap=100")
        print(f"  rlama add-reranker {COLLECTION_NAME}")
        return

    # Check prerequisites
    if not check_rlama():
        print("\nError: RLAMA not found or not working.", file=sys.stderr)
        print("Install: go install github.com/dontizi/rlama@latest", file=sys.stderr)
        sys.exit(1)

    if not check_ollama():
        print("\nError: Ollama not running.", file=sys.stderr)
        print("Start: ollama serve", file=sys.stderr)
        sys.exit(1)

    # Handle existing collection
    if collection_exists():
        if args.rebuild:
            print(f"\nDeleting existing collection '{COLLECTION_NAME}'...")
            if delete_collection():
                print("Deleted.")
            else:
                print("Warning: Failed to delete. Attempting to create anyway.", file=sys.stderr)
        else:
            print(f"\nCollection '{COLLECTION_NAME}' already exists.")
            print("Use --rebuild to recreate, or query with:")
            print(f"  rlama run {COLLECTION_NAME} --query \"What did I discuss with [person]?\"")
            return

    # Create collection
    success = create_collection()

    if success:
        print(f"\nReady to query:")
        print(f"  rlama run {COLLECTION_NAME} --query \"What did I discuss with [person]?\"")
        print(f"  rlama run {COLLECTION_NAME} --query \"Who works at [company]?\"")
        print(f"  rlama run {COLLECTION_NAME} --query \"What are my top skills?\"")


if __name__ == "__main__":
    main()
