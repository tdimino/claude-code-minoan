#!/usr/bin/env python3
"""
Rebuild a RLAMA RAG with deduplicated source files.

Instead of removing duplicates one-by-one (slow due to reranker reload),
this script:
1. Collects all source files from specified directories
2. Deduplicates by basename (prefers .md over .pdf)
3. Deletes the existing RAG
4. Creates a fresh RAG with only unique files

Usage:
    python3 rlama_rebuild_deduped.py <rag-name> <source-dir1> [source-dir2 ...]
    python3 rlama_rebuild_deduped.py academic-research ~/sources ~/dossiers --dry-run
"""

import subprocess
import sys
from collections import defaultdict
from pathlib import Path


SUPPORTED_EXTENSIONS = {'.md', '.pdf', '.txt', '.json', '.yaml', '.yml'}
PRIORITY_ORDER = ['.md', '.txt', '.json', '.yaml', '.yml', '.pdf']  # .md preferred over .pdf


def collect_files(source_dirs):
    """Recursively collect all supported files from source directories."""
    files = []
    for source_dir in source_dirs:
        path = Path(source_dir).expanduser()
        if not path.exists():
            print(f"  ⚠️  Directory not found: {source_dir}")
            continue
        for ext in SUPPORTED_EXTENSIONS:
            files.extend(path.rglob(f"*{ext}"))
    return files


def normalize_stem(stem):
    """
    Normalize stem to handle variants like:
    - 'Astour-X-1966-mistral' -> 'Astour-X-1966'
    - 'Astour-X-1966-raw' -> 'Astour-X-1966'
    """
    suffixes_to_strip = ['-mistral', '-raw', '-ocr', '-converted', '-clean']
    normalized = stem
    for suffix in suffixes_to_strip:
        if normalized.endswith(suffix):
            normalized = normalized[:-len(suffix)]
    return normalized


def deduplicate_files(files):
    """
    Deduplicate files by normalized basename, preferring .md over .pdf.
    Returns list of unique file paths.
    """
    # Group by normalized stem (handles X.pdf vs X-mistral.md as same doc)
    by_normalized = defaultdict(list)
    for f in files:
        normalized = normalize_stem(f.stem)
        by_normalized[normalized].append(f)

    unique_files = []
    duplicates_removed = 0

    for normalized_stem, candidates in by_normalized.items():
        if len(candidates) == 1:
            unique_files.append(candidates[0])
        else:
            # Sort by priority (prefer .md over .pdf)
            def priority(f):
                ext = f.suffix.lower()
                try:
                    return PRIORITY_ORDER.index(ext)
                except ValueError:
                    return len(PRIORITY_ORDER)

            candidates.sort(key=priority)
            unique_files.append(candidates[0])
            duplicates_removed += len(candidates) - 1

    return unique_files, duplicates_removed


def get_extension_counts(files):
    """Count files by extension."""
    counts = defaultdict(int)
    for f in files:
        counts[f.suffix.lower()] += 1
    return dict(counts)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    rag_name = sys.argv[1]
    dry_run = '--dry-run' in sys.argv
    source_dirs = [arg for arg in sys.argv[2:] if not arg.startswith('--')]

    print("=" * 60)
    print("RLAMA Rebuild (Deduplicated)")
    print("=" * 60)
    print(f"RAG: {rag_name}")
    print(f"Source directories: {len(source_dirs)}")
    for d in source_dirs:
        print(f"  - {d}")
    print(f"Mode: {'DRY RUN' if dry_run else 'LIVE'}")

    # Step 1: Collect all files
    print(f"\n📁 Collecting source files...")
    all_files = collect_files(source_dirs)
    print(f"  Found: {len(all_files)} files")
    print(f"  By type: {get_extension_counts(all_files)}")

    # Step 2: Deduplicate
    print(f"\n🔄 Deduplicating...")
    unique_files, removed_count = deduplicate_files(all_files)
    print(f"  Unique files: {len(unique_files)}")
    print(f"  Duplicates removed: {removed_count}")
    print(f"  By type: {get_extension_counts(unique_files)}")

    if dry_run:
        print(f"\n[DRY RUN] Would rebuild RAG with {len(unique_files)} unique files")
        print(f"\nSample of files to include:")
        for f in sorted(unique_files, key=lambda x: x.name)[:20]:
            print(f"  {f.name}")
        if len(unique_files) > 20:
            print(f"  ... and {len(unique_files) - 20} more")
        sys.exit(0)

    # Step 3: Verify backup exists
    print(f"\n🔍 Checking for backup...")
    rlama_dir = Path.home() / '.rlama'
    backups = list(rlama_dir.glob(f'{rag_name}.backup-*'))
    if backups:
        print(f"  ✓ Backup found: {backups[-1].name}")
    else:
        print(f"  ⚠️  No backup found!")
        confirm = input("  Continue without backup? [y/N]: ")
        if confirm.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    # Step 4: Delete existing RAG
    print(f"\n🗑️  Deleting existing RAG '{rag_name}'...")
    rag_path = rlama_dir / rag_name
    if rag_path.exists():
        import shutil
        shutil.rmtree(rag_path)
        print(f"  ✓ Deleted")
    else:
        print(f"  (RAG didn't exist)")

    # Step 5: Create staging directory with unique files (symlinks)
    # Use persistent directory to avoid cleanup during RLAMA operation
    staging_dir = rlama_dir / f'.rebuild_staging_{rag_name}'

    print(f"\n📂 Preparing unique files...")

    # Clean up any previous staging directory
    if staging_dir.exists():
        import shutil
        shutil.rmtree(staging_dir)

    staging_dir.mkdir(parents=True)

    # Create symlinks to unique files
    for f in unique_files:
        link = staging_dir / f.name
        # Handle name collisions by adding parent dir
        if link.exists():
            link = staging_dir / f"{f.parent.name}_{f.name}"
        link.symlink_to(f)

    print(f"  ✓ Prepared {len(unique_files)} files in {staging_dir}")

    # Step 6: Create new RAG
    print(f"\n🔨 Creating RAG '{rag_name}' with unique files...")
    print(f"  (This will load the reranker ONCE)")

    result = subprocess.run(
        ['rlama', 'rag', 'qwen2.5:7b', rag_name, str(staging_dir)],
        capture_output=False  # Show output in real-time
    )

    if result.returncode != 0:
        print(f"\n❌ RAG creation failed!")
        print(f"  Staging directory preserved at: {staging_dir}")
        sys.exit(1)

    # Step 6b: Clean up staging directory on success
    print(f"\n🧹 Cleaning up staging directory...")
    import shutil
    shutil.rmtree(staging_dir)
    print(f"  ✓ Removed {staging_dir}")

    # Step 7: Verify
    print(f"\n✅ Rebuild complete!")
    print(f"\nVerifying...")
    result = subprocess.run(
        ['rlama', 'list-docs', rag_name],
        capture_output=True, text=True
    )
    doc_count = len([l for l in result.stdout.strip().split('\n')[2:] if l.strip()])
    print(f"  New RAG has {doc_count} documents")
    print(f"  (Expected: {len(unique_files)})")


if __name__ == '__main__':
    main()
