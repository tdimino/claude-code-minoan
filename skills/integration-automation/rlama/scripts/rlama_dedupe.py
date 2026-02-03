#!/usr/bin/env python3
"""
Remove duplicate entries from RLAMA RAG, prioritizing markdown over PDF.

Features:
- Backup verification before execution
- Progress checkpointing (resume interrupted runs)
- Configurable delay between deletions
- Confirmation prompt for safety

Usage:
    python3 rlama_dedupe.py <rag-name> --dry-run        # Preview removals
    python3 rlama_dedupe.py <rag-name>                  # Execute with confirmation
    python3 rlama_dedupe.py <rag-name> --resume         # Resume interrupted run
    python3 rlama_dedupe.py <rag-name> --delay 0.2      # Custom delay (seconds)
    python3 rlama_dedupe.py <rag-name> --no-confirm     # Skip confirmation prompt
"""

import json
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path

# Import logger (optional - graceful fallback if not available)
try:
    from rlama_logger import get_logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False


CHECKPOINT_DIR = Path.home() / '.rlama' / '.dedupe_checkpoints'


def get_all_docs(rag_name):
    """Get list of all document IDs in the RAG."""
    result = subprocess.run(
        ['rlama', 'list-docs', rag_name],
        capture_output=True, text=True
    )
    docs = []
    for line in result.stdout.strip().split('\n')[2:]:  # Skip header
        if line.strip():
            doc_id = line.split()[0]
            docs.append(doc_id)
    return docs


def get_basename(doc_id):
    """Get basename without extension."""
    return Path(doc_id).stem


def get_extension(doc_id):
    """Get file extension."""
    return Path(doc_id).suffix.lower()


def find_duplicates(docs):
    """Find duplicates prioritizing .md over .pdf."""
    # Group by basename (format duplicates)
    basename_groups = defaultdict(list)
    for doc in docs:
        basename_groups[get_basename(doc)].append(doc)

    to_remove = []

    # Handle pure duplicates: keep first occurrence
    seen = set()
    for doc in docs:
        if doc in seen:
            to_remove.append(doc)
        else:
            seen.add(doc)

    # Handle format duplicates: prefer .md over .pdf
    for basename, group in basename_groups.items():
        unique_group = list(set(group))
        has_md = any(get_extension(d) == '.md' for d in unique_group)
        has_pdf = any(get_extension(d) == '.pdf' for d in unique_group)

        if has_md and has_pdf:
            # Mark all PDFs for removal
            for doc in unique_group:
                if get_extension(doc) == '.pdf' and doc not in to_remove:
                    to_remove.append(doc)

    return to_remove


def check_backup_exists(rag_name):
    """Check if a recent backup exists."""
    rlama_dir = Path.home() / '.rlama'
    today = datetime.now().strftime('%Y%m%d')

    backups = list(rlama_dir.glob(f'{rag_name}.backup-{today}*'))
    if backups:
        return backups[0]

    # Check for any backup
    all_backups = list(rlama_dir.glob(f'{rag_name}.backup-*'))
    if all_backups:
        latest = sorted(all_backups)[-1]
        return latest

    return None


def load_checkpoint(rag_name):
    """Load checkpoint file if exists."""
    checkpoint_file = CHECKPOINT_DIR / f'{rag_name}.json'
    if checkpoint_file.exists():
        with open(checkpoint_file) as f:
            return json.load(f)
    return None


def save_checkpoint(rag_name, completed, remaining, stats):
    """Save progress to checkpoint file."""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)
    checkpoint_file = CHECKPOINT_DIR / f'{rag_name}.json'

    data = {
        'rag_name': rag_name,
        'timestamp': datetime.now().isoformat(),
        'completed': completed,
        'remaining': remaining,
        'stats': stats
    }

    with open(checkpoint_file, 'w') as f:
        json.dump(data, f, indent=2)


def clear_checkpoint(rag_name):
    """Remove checkpoint file after successful completion."""
    checkpoint_file = CHECKPOINT_DIR / f'{rag_name}.json'
    if checkpoint_file.exists():
        checkpoint_file.unlink()


def remove_docs(rag_name, docs, dry_run=False, delay=0.1, resume_from=0):
    """Remove documents from RAG with progress tracking."""
    # Initialize logger
    logger = get_logger() if LOGGER_AVAILABLE else None
    op_id = None

    total = len(docs)
    completed = []
    failed = []

    # Start logging operation (not for dry runs)
    if logger and not dry_run:
        op_id = logger.dedupe_start(rag_name, total)

    print(f"\n{'[DRY RUN] ' if dry_run else ''}Removing {total} documents...")
    if delay > 0 and not dry_run:
        print(f"  (with {delay}s delay between operations to reduce index fragmentation)")

    if resume_from > 0:
        print(f"  Resuming from document {resume_from + 1}")
        docs = docs[resume_from:]

    start_time = time.time()

    try:
        for i, doc in enumerate(docs, resume_from + 1):
            progress = f"[{i}/{total}]"
            print(f"  {progress} {doc}", end='')

            if not dry_run:
                result = subprocess.run(
                    ['rlama', 'remove-doc', rag_name, doc],
                    capture_output=True, text=True
                )

                if result.returncode == 0:
                    completed.append(doc)
                    print(" ✓")
                    # Log progress
                    if logger and op_id:
                        logger.dedupe_progress(op_id, i, total, doc, 'ok')
                else:
                    failed.append({'doc': doc, 'error': result.stderr.strip()})
                    print(" ✗")
                    # Log failure
                    if logger and op_id:
                        logger.dedupe_progress(op_id, i, total, doc, 'failed')

                # Save checkpoint every 50 documents
                if i % 50 == 0:
                    remaining = [d for d in docs[i - resume_from:]]
                    save_checkpoint(rag_name, completed, remaining, {
                        'total': total,
                        'processed': i,
                        'failed': len(failed)
                    })

                # Delay between operations
                if delay > 0 and i < total:
                    time.sleep(delay)
            else:
                print()

        elapsed = time.time() - start_time

        # Clear checkpoint on successful completion
        if not dry_run:
            clear_checkpoint(rag_name)
            # Log completion
            if logger and op_id:
                logger.dedupe_complete(op_id, len(completed), len(failed))

        # Print summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        if dry_run:
            print(f"  Would remove: {total} documents")
        else:
            print(f"  Successfully removed: {len(completed)} documents")
            if failed:
                print(f"  Failed: {len(failed)} documents")
                for f in failed[:5]:  # Show first 5 failures
                    print(f"    - {f['doc']}: {f['error'][:50]}")
                if len(failed) > 5:
                    print(f"    ... and {len(failed) - 5} more")
            print(f"  Time elapsed: {elapsed:.1f}s")

        return len(completed), len(failed)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted! Saving checkpoint...")
        remaining = [d for d in docs[i - resume_from:]]
        save_checkpoint(rag_name, completed, remaining, {
            'total': total,
            'processed': i - 1,
            'failed': len(failed)
        })
        print(f"  Checkpoint saved. Resume with: python3 rlama_dedupe.py {rag_name} --resume")
        sys.exit(1)


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    rag_name = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    resume = '--resume' in sys.argv
    no_confirm = '--no-confirm' in sys.argv

    # Parse delay argument
    delay = 0.1  # Default 100ms
    if '--delay' in sys.argv:
        idx = sys.argv.index('--delay')
        if idx + 1 < len(sys.argv):
            try:
                delay = float(sys.argv[idx + 1])
            except ValueError:
                print("Error: --delay must be a number")
                sys.exit(1)

    print(f"{'=' * 60}")
    print(f"RLAMA Deduplication Tool")
    print(f"{'=' * 60}")
    print(f"RAG: {rag_name}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")

    # Check for existing checkpoint
    checkpoint = None
    if resume:
        checkpoint = load_checkpoint(rag_name)
        if checkpoint:
            print(f"\n📋 Found checkpoint from {checkpoint['timestamp']}")
            print(f"   Processed: {checkpoint['stats']['processed']}/{checkpoint['stats']['total']}")
            remaining = checkpoint['remaining']
            print(f"   Remaining: {len(remaining)} documents")
        else:
            print("\n⚠️  No checkpoint found. Starting fresh.")
            resume = False

    # Check backup exists (for live runs)
    if not dry_run and not resume:
        backup = check_backup_exists(rag_name)
        if backup:
            print(f"\n✓ Backup found: {backup.name}")
        else:
            print(f"\n⚠️  WARNING: No backup found for '{rag_name}'")
            print(f"   Create one with: cp -r ~/.rlama/{rag_name} ~/.rlama/{rag_name}.backup-$(date +%Y%m%d)")
            if not no_confirm:
                confirm = input("\n   Continue without backup? [y/N]: ")
                if confirm.lower() != 'y':
                    print("Aborted.")
                    sys.exit(0)

    # Analyze or use checkpoint
    if resume and checkpoint:
        to_remove = checkpoint['remaining']
        resume_from = checkpoint['stats']['processed']
        print(f"\nResuming with {len(to_remove)} remaining documents...")
    else:
        print(f"\nAnalyzing RAG...")
        docs = get_all_docs(rag_name)
        print(f"  Total documents: {len(docs)}")
        print(f"  Unique documents: {len(set(docs))}")

        to_remove = find_duplicates(docs)
        print(f"  Duplicates found: {len(to_remove)}")
        resume_from = 0

        if not to_remove:
            print("\n✓ No duplicates found!")
            sys.exit(0)

        # Categorize what will be removed
        pdf_removes = [d for d in to_remove if get_extension(d) == '.pdf']
        exact_dupes = len(to_remove) - len(pdf_removes)
        print(f"\n  Breakdown:")
        print(f"    - Exact duplicates: {exact_dupes}")
        print(f"    - PDFs with MD equivalent: {len(pdf_removes)}")

    # Confirmation for live runs
    if not dry_run and not no_confirm:
        print(f"\n⚠️  This will permanently remove {len(to_remove)} documents.")
        confirm = input("   Proceed? [y/N]: ")
        if confirm.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    # Execute
    remove_docs(rag_name, to_remove, dry_run, delay, resume_from)


if __name__ == '__main__':
    main()
