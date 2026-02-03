#!/usr/bin/env python3
"""
Batch RAG Ingestion for rlama

Ingests documents in batches with checkpoint/resume support to handle
transient network failures (e.g., HuggingFace DNS resolution errors).

Usage:
    python3 rlama_batch_ingest.py academic-research ./staging --batch-size 50
    python3 rlama_batch_ingest.py academic-research ./staging --resume
    python3 rlama_batch_ingest.py academic-research ./staging --dry-run
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Import logger (optional - graceful fallback if not available)
try:
    from rlama_logger import get_logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False


CHECKPOINT_DIR = Path.home() / ".rlama" / ".batch_checkpoints"
SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".html", ".json"}


def get_checkpoint_path(rag_name: str) -> Path:
    """Get the checkpoint file path for a RAG."""
    return CHECKPOINT_DIR / f"{rag_name}_checkpoint.json"


def load_checkpoint(rag_name: str) -> Optional[dict]:
    """Load checkpoint if it exists."""
    path = get_checkpoint_path(rag_name)
    if path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def save_checkpoint(checkpoint: dict) -> None:
    """Save checkpoint to disk."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    path = get_checkpoint_path(checkpoint["rag_name"])
    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)
    print(f"  💾 Checkpoint saved: {len(checkpoint['completed_files'])} files completed")


def delete_checkpoint(rag_name: str) -> None:
    """Delete checkpoint file after successful completion."""
    path = get_checkpoint_path(rag_name)
    if path.exists():
        path.unlink()
        print(f"  🗑️  Checkpoint deleted")


def get_source_files(source_dir: Path) -> list[str]:
    """Get all supported files from source directory, sorted for determinism."""
    files = []
    for ext in SUPPORTED_EXTENSIONS:
        files.extend(source_dir.glob(f"**/*{ext}"))
    # Return relative paths sorted for consistent ordering
    return sorted([str(f.relative_to(source_dir)) for f in files])


def rag_exists(rag_name: str) -> bool:
    """Check if the RAG already exists."""
    result = subprocess.run(
        ["rlama", "list"],
        capture_output=True,
        text=True
    )
    return rag_name in result.stdout


def create_seed_rag(rag_name: str, source_dir: Path, seed_file: str, verbose: bool = False) -> bool:
    """Create initial RAG with a single seed document."""
    print(f"\n🌱 Creating seed RAG with: {seed_file}")

    # Create a temp directory with just the seed file
    with tempfile.TemporaryDirectory() as tmpdir:
        src = source_dir / seed_file
        dst = Path(tmpdir) / seed_file
        dst.parent.mkdir(parents=True, exist_ok=True)

        # Copy the seed file
        import shutil
        shutil.copy2(src, dst)

        cmd = ["rlama", "rag", "llama3.2", rag_name, tmpdir]
        if verbose:
            print(f"  Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=not verbose,
            text=True
        )

        if result.returncode != 0:
            print(f"  ❌ Failed to create seed RAG")
            if not verbose:
                print(f"  stderr: {result.stderr}")
            return False

        print(f"  ✅ Seed RAG created successfully")
        return True


def add_batch(rag_name: str, source_dir: Path, files: list[str],
              verbose: bool = False, max_retries: int = 3) -> bool:
    """Add a batch of files to the RAG with retry logic."""

    with tempfile.TemporaryDirectory() as tmpdir:
        # Copy batch files to temp directory
        for rel_path in files:
            src = source_dir / rel_path
            dst = Path(tmpdir) / rel_path
            dst.parent.mkdir(parents=True, exist_ok=True)
            import shutil
            shutil.copy2(src, dst)

        cmd = ["rlama", "add-docs", rag_name, tmpdir]

        for attempt in range(max_retries):
            if attempt > 0:
                wait_time = 2 ** attempt  # Exponential backoff
                print(f"    ⏳ Retry {attempt + 1}/{max_retries} after {wait_time}s...")
                time.sleep(wait_time)

            if verbose:
                print(f"    Running: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=not verbose,
                text=True
            )

            if result.returncode == 0:
                return True

            # Check for network errors
            stderr = result.stderr if not verbose else ""
            if "nodename nor servname" in stderr or "Max retries exceeded" in stderr:
                print(f"    ⚠️  Network error detected")
                continue
            else:
                # Non-network error, don't retry
                print(f"    ❌ Non-recoverable error")
                if not verbose:
                    print(f"    stderr: {stderr[:500]}")
                return False

        print(f"    ❌ Max retries exceeded")
        return False


def run_batch_ingestion(
    rag_name: str,
    source_dir: Path,
    batch_size: int = 50,
    resume: bool = False,
    dry_run: bool = False,
    verbose: bool = False
) -> bool:
    """Main batch ingestion logic."""

    # Initialize logger
    logger = get_logger() if LOGGER_AVAILABLE else None
    op_id = None

    all_files = get_source_files(source_dir)
    print(f"\n📂 Found {len(all_files)} files in {source_dir}")

    # Check for existing checkpoint
    checkpoint = load_checkpoint(rag_name) if resume else None

    if checkpoint:
        completed = set(checkpoint["completed_files"])
        remaining = [f for f in all_files if f not in completed]
        print(f"📋 Resuming from checkpoint: {len(completed)} completed, {len(remaining)} remaining")
    else:
        completed = set()
        remaining = all_files
        checkpoint = {
            "rag_name": rag_name,
            "source_dir": str(source_dir),
            "batch_size": batch_size,
            "total_files": len(all_files),
            "completed_files": [],
            "current_batch": 0,
            "last_success": None,
            "status": "starting"
        }

    if not remaining:
        print("✅ All files already ingested!")
        return True

    if dry_run:
        print(f"\n🔍 DRY RUN - Would process {len(remaining)} files in {(len(remaining) + batch_size - 1) // batch_size} batches")
        for i, batch_start in enumerate(range(0, len(remaining), batch_size)):
            batch = remaining[batch_start:batch_start + batch_size]
            print(f"  Batch {i + 1}: {len(batch)} files ({batch[0]} ... {batch[-1]})")
        return True

    # Create RAG if it doesn't exist
    if not rag_exists(rag_name):
        if not remaining:
            print("❌ No files to ingest and RAG doesn't exist")
            return False

        seed_file = remaining[0]
        if not create_seed_rag(rag_name, source_dir, seed_file, verbose):
            return False

        # Mark seed file as completed
        completed.add(seed_file)
        remaining = remaining[1:]
        checkpoint["completed_files"].append(seed_file)
        checkpoint["status"] = "in_progress"
        save_checkpoint(checkpoint)

    # Process remaining files in batches
    total_batches = (len(remaining) + batch_size - 1) // batch_size

    # Start logging operation (after dry-run check and RAG creation)
    if logger and not dry_run:
        op_id = logger.batch_start(rag_name, total_batches, len(all_files))

    for batch_num, batch_start in enumerate(range(0, len(remaining), batch_size)):
        batch = remaining[batch_start:batch_start + batch_size]
        batch_end = min(batch_start + batch_size, len(remaining))

        progress_pct = (len(completed) / len(all_files)) * 100
        print(f"\n📦 Batch {batch_num + 1}/{total_batches} ({len(batch)} files) - {progress_pct:.1f}% complete")

        success = add_batch(rag_name, source_dir, batch, verbose)

        if success:
            # Update checkpoint
            for f in batch:
                completed.add(f)
            checkpoint["completed_files"] = list(completed)
            checkpoint["current_batch"] = batch_num + 1
            checkpoint["last_success"] = datetime.now().isoformat()
            save_checkpoint(checkpoint)
            print(f"  ✅ Batch {batch_num + 1} completed")

            # Log progress
            if logger and op_id:
                logger.batch_progress(op_id, batch_num + 1, total_batches, len(completed), len(all_files))
        else:
            print(f"\n❌ Batch {batch_num + 1} failed. Run with --resume to continue.")
            checkpoint["status"] = "failed"
            save_checkpoint(checkpoint)
            if logger and op_id:
                logger.complete_operation(op_id, success=False, summary={'failed_batch': batch_num + 1})
            return False

    # All done!
    checkpoint["status"] = "completed"
    save_checkpoint(checkpoint)
    delete_checkpoint(rag_name)

    # Log completion
    if logger and op_id:
        logger.batch_complete(op_id, len(all_files), total_batches)

    print(f"\n🎉 Successfully ingested {len(all_files)} files into '{rag_name}'")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Batch ingest documents into rlama RAG with checkpoint/resume support"
    )
    parser.add_argument("rag_name", help="Name of the RAG to create/update")
    parser.add_argument("source_dir", help="Directory containing source documents")
    parser.add_argument("--batch-size", type=int, default=50, help="Files per batch (default: 50)")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--dry-run", action="store_true", help="Preview batches without executing")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show command output")

    args = parser.parse_args()

    source_dir = Path(args.source_dir).resolve()
    if not source_dir.exists():
        print(f"❌ Source directory not found: {source_dir}")
        sys.exit(1)

    success = run_batch_ingestion(
        rag_name=args.rag_name,
        source_dir=source_dir,
        batch_size=args.batch_size,
        resume=args.resume,
        dry_run=args.dry_run,
        verbose=args.verbose
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
