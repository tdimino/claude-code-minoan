#!/usr/bin/env python3
"""
RLAMA Resilient Indexing Script - Fast batch processing with graceful error handling.

Uses a Pre-Filter + Batch approach for speed:
1. Estimates which files are "safe" (unlikely to exceed context limits)
2. Processes safe files in ONE batch call (fast!)
3. Only processes large/risky files individually

Optional parallel processing with --parallel N flag.

Usage:
    python3 rlama_resilient.py create my-rag ~/Documents
    python3 rlama_resilient.py create my-rag ~/Research --docs-only
    python3 rlama_resilient.py create my-rag ~/Code --parallel 4
    python3 rlama_resilient.py add my-rag ./more-docs --parallel 8
"""

import argparse
import shutil
import subprocess
import sys
import os
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import List, Tuple, Optional, Dict

# Import logger (optional - graceful fallback if not available)
try:
    from rlama_logger import get_logger
    LOGGER_AVAILABLE = True
except ImportError:
    LOGGER_AVAILABLE = False

# Default model (qwen2.5:7b as of Jan 2026)
DEFAULT_MODEL = 'qwen2.5:7b'
LEGACY_MODEL = 'llama3.2'

# Token estimation: ~4 characters per token on average
# Default context is 4096 tokens, so ~16KB is the danger zone
# We use a conservative threshold of 12KB (~3000 tokens) for "safe" files
DEFAULT_SAFE_THRESHOLD_KB = 12

# Supported file extensions by RLAMA
SUPPORTED_EXTENSIONS = {
    '.txt', '.md', '.markdown',
    '.pdf', '.docx', '.doc',
    '.py', '.js', '.ts', '.go', '.rs', '.java', '.rb', '.cpp', '.c', '.h',
    '.json', '.yaml', '.yml', '.csv',
    '.html', '.htm',
    '.org'
}

# Document-only extensions (for --docs-only)
DOC_EXTENSIONS = {'.pdf', '.md', '.txt', '.docx', '.doc', '.org'}

# Errors that indicate we should skip the file and continue
SKIP_ERRORS = [
    'input length exceeds the context length',
    'context length exceeded',
    'embedding generation failed',
    'failed to generate embedding',
]

# Errors that indicate we should abort entirely
FATAL_ERRORS = [
    'model not found',
    'rlama: command not found',
    'connection refused',
    'ollama not running',
]


def estimate_tokens(file_path: Path) -> int:
    """Estimate token count from file size (~4 chars per token)."""
    try:
        size_bytes = file_path.stat().st_size
        return size_bytes // 4
    except OSError:
        return 0


def is_safe_file(file_path: Path, threshold_kb: int = DEFAULT_SAFE_THRESHOLD_KB) -> bool:
    """Check if file is likely safe (won't exceed context limits)."""
    threshold_bytes = threshold_kb * 1024
    try:
        return file_path.stat().st_size < threshold_bytes
    except OSError:
        return True  # Assume safe if can't read


def safe_relative_path(file_path: Path, base_folder: Path) -> str:
    """Get relative path safely, handling Python <3.9 and edge cases."""
    try:
        return str(file_path.relative_to(base_folder))
    except ValueError:
        return file_path.name


def is_skippable_error(stderr: str) -> bool:
    """Check if error is one we should skip and continue."""
    stderr_lower = stderr.lower()
    return any(err in stderr_lower for err in SKIP_ERRORS)


def is_fatal_error(stderr: str) -> bool:
    """Check if error is fatal and we should abort."""
    stderr_lower = stderr.lower()
    return any(err in stderr_lower for err in FATAL_ERRORS)


def get_supported_files(
    folder_path: Path,
    docs_only: bool = False,
    process_exts: Optional[List[str]] = None,
    exclude_exts: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
) -> List[Path]:
    """Get list of supported files from folder."""

    # Determine which extensions to use
    if process_exts:
        allowed_exts = set(ext if ext.startswith('.') else f'.{ext}' for ext in process_exts)
    elif docs_only:
        allowed_exts = DOC_EXTENSIONS
    else:
        allowed_exts = SUPPORTED_EXTENSIONS

    # Extensions to exclude
    excluded_exts = set()
    if exclude_exts:
        excluded_exts = set(ext if ext.startswith('.') else f'.{ext}' for ext in exclude_exts)

    # Directories to exclude
    excluded_dirs = {'.git', '.osgrep', '.claude', 'node_modules', '__pycache__', 'venv', '.venv'}
    if exclude_dirs:
        excluded_dirs.update(exclude_dirs)

    files = []
    for root, dirs, filenames in os.walk(folder_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in excluded_dirs]

        for filename in filenames:
            ext = Path(filename).suffix.lower()
            if ext in allowed_exts and ext not in excluded_exts:
                files.append(Path(root) / filename)

    return sorted(files)


def run_rlama_command(args: List[str], timeout: int = 300) -> Tuple[str, str, int]:
    """Run an rlama command and return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            ['rlama'] + args,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.TimeoutExpired:
        return '', f'Command timed out after {timeout} seconds', 1
    except FileNotFoundError:
        return '', 'rlama command not found. Is RLAMA installed?', 1
    except (KeyboardInterrupt, SystemExit):
        raise  # Re-raise to allow proper termination
    except Exception as e:
        return '', f'Unexpected error: {str(e)}', 1


def verify_rag_exists(rag_name: str) -> bool:
    """Verify that a RAG exists by checking rlama list output."""
    stdout, stderr, code = run_rlama_command(['list'], timeout=30)
    if code != 0:
        return False
    return rag_name in stdout


def create_batch_folder(files: List[Path], temp_dir: str) -> str:
    """Create a temp folder with symlinks to the given files."""
    for f in files:
        link_path = os.path.join(temp_dir, f.name)
        # Handle duplicate filenames by adding parent folder
        if os.path.exists(link_path):
            parent = f.parent.name
            link_path = os.path.join(temp_dir, f'{parent}_{f.name}')
        try:
            os.symlink(str(f.resolve()), link_path)
        except OSError:
            # Fallback: copy file if symlink fails
            shutil.copy2(str(f), link_path)
    return temp_dir


def process_batch(
    rag_name: str,
    files: List[Path],
    is_create: bool = False,
    model: str = DEFAULT_MODEL,
    chunking: str = 'hybrid',
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> Tuple[bool, str, List[Path]]:
    """
    Process a batch of files in one rlama call.
    Returns (success, error_message, failed_files).
    """
    if not files:
        return True, '', []

    temp_dir = tempfile.mkdtemp(prefix='rlama_batch_')

    try:
        create_batch_folder(files, temp_dir)

        if is_create:
            cmd = [
                'rag', model, rag_name, temp_dir,
                '--chunking', chunking,
                '--chunk-size', str(chunk_size),
                '--chunk-overlap', str(chunk_overlap),
            ]
        else:
            cmd = ['add-docs', rag_name, temp_dir]

        stdout, stderr, code = run_rlama_command(cmd, timeout=600)

        if code == 0:
            return True, '', []

        # Try to identify which file failed from error message
        failed_files = []
        for f in files:
            if f.name in stderr:
                failed_files.append(f)

        # If we can't identify specific files, return all as potentially failed
        if not failed_files:
            failed_files = files

        return False, stderr, failed_files

    finally:
        # Clean up temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def add_single_file(rag_name: str, file_path: Path) -> Tuple[bool, str]:
    """Add a single file to the RAG. Returns (success, error_message).

    Note: rlama add-docs requires a folder path, so we create a temp directory
    with a symlink to the single file.
    """
    temp_dir = tempfile.mkdtemp(prefix='rlama_add_')
    temp_link = os.path.join(temp_dir, file_path.name)

    try:
        os.symlink(str(file_path.resolve()), temp_link)

        cmd = ['add-docs', rag_name, temp_dir]
        stdout, stderr, code = run_rlama_command(cmd, timeout=120)

        if code == 0:
            return True, ''

        return False, stderr
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def process_files_sequential(
    rag_name: str,
    files: List[Path],
    base_folder: Path
) -> Tuple[int, int, List[str]]:
    """Process files one by one sequentially."""
    added = 0
    skipped = 0
    skipped_files = []

    for i, file_path in enumerate(files, 1):
        rel_path = safe_relative_path(file_path, base_folder)
        print(f'  [{i}/{len(files)}] {rel_path}...', end=' ', flush=True)

        success, error = add_single_file(rag_name, file_path)

        if success:
            print('✓')
            added += 1
        else:
            if is_fatal_error(error):
                print(f'\nFatal error: {error}', file=sys.stderr)
                return added, skipped, skipped_files
            elif is_skippable_error(error):
                print('⚠ skipped (context overflow)')
            else:
                print('⚠ skipped')
                print(f'    Error: {error}', file=sys.stderr)
            skipped += 1
            skipped_files.append(rel_path)

    return added, skipped, skipped_files


def process_files_parallel(
    rag_name: str,
    files: List[Path],
    base_folder: Path,
    workers: int = 4
) -> Tuple[int, int, List[str]]:
    """Process files in parallel using ThreadPoolExecutor."""
    added = 0
    skipped = 0
    skipped_files = []

    print(f'  Processing {len(files)} files with {workers} parallel workers...')

    def process_one(file_path: Path) -> Tuple[Path, bool, str]:
        success, error = add_single_file(rag_name, file_path)
        return file_path, success, error

    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(process_one, f): f for f in files}

        for i, future in enumerate(as_completed(futures), 1):
            file_path, success, error = future.result()
            rel_path = safe_relative_path(file_path, base_folder)

            if success:
                print(f'  [{i}/{len(files)}] {rel_path}... ✓')
                added += 1
            else:
                if is_fatal_error(error):
                    print(f'\nFatal error on {rel_path}: {error}', file=sys.stderr)
                    # Cancel remaining futures
                    for f in futures:
                        f.cancel()
                    break
                elif is_skippable_error(error):
                    print(f'  [{i}/{len(files)}] {rel_path}... ⚠ skipped (context overflow)')
                else:
                    print(f'  [{i}/{len(files)}] {rel_path}... ⚠ skipped')
                skipped += 1
                skipped_files.append(rel_path)

    return added, skipped, skipped_files


def _print_summary(added: int, skipped: int, skipped_files: List[str], batch_added: int = 0) -> None:
    """Print processing summary."""
    print()
    total_added = batch_added + added
    print(f'Done! Added {total_added} files, skipped {skipped} files')
    if batch_added > 0:
        print(f'  (batch: {batch_added}, individual: {added})')

    if skipped_files:
        print(f'\nSkipped files:')
        for f in skipped_files[:20]:  # Limit to first 20
            print(f'  - {f}')
        if len(skipped_files) > 20:
            print(f'  ... and {len(skipped_files) - 20} more')


def resilient_create(
    rag_name: str,
    folder_path: str,
    model: str = DEFAULT_MODEL,
    chunking: str = 'hybrid',
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    docs_only: bool = False,
    process_exts: Optional[List[str]] = None,
    exclude_exts: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    safe_threshold_kb: int = DEFAULT_SAFE_THRESHOLD_KB,
    parallel: int = 0,
) -> dict:
    """Create a RAG using Pre-Filter + Batch approach for speed."""

    # Initialize logger if available
    logger = get_logger() if LOGGER_AVAILABLE else None
    op_id = None
    start_time = time.time()

    folder = Path(folder_path).expanduser().resolve()

    if not folder.exists():
        return {
            'success': False,
            'error': f'Folder not found: {folder}',
            'added': 0,
            'skipped': 0,
            'skipped_files': [],
        }

    # Get list of files to process
    files = get_supported_files(
        folder,
        docs_only=docs_only,
        process_exts=process_exts,
        exclude_exts=exclude_exts,
        exclude_dirs=exclude_dirs,
    )

    if not files:
        return {
            'success': False,
            'error': 'No supported files found in folder',
            'added': 0,
            'skipped': 0,
            'skipped_files': [],
        }

    # Split files into safe (batch) and large (individual)
    safe_files = [f for f in files if is_safe_file(f, safe_threshold_kb)]
    large_files = [f for f in files if not is_safe_file(f, safe_threshold_kb)]

    print(f'Found {len(files)} files to index')
    print(f'  - {len(safe_files)} safe files (batch processing)')
    print(f'  - {len(large_files)} large files (individual processing)')
    print(f'Creating RAG "{rag_name}" with model {model}...')
    print()

    # Start logging operation
    if logger:
        op_id = logger.ingest_start(rag_name, str(folder), len(files))

    batch_added = 0
    added = 0
    skipped = 0
    skipped_files = []

    # Step 1: Process safe files in batch
    if safe_files:
        print(f'Step 1: Batch processing {len(safe_files)} safe files...')
        success, error, failed = process_batch(
            rag_name, safe_files, is_create=True,
            model=model, chunking=chunking,
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

        if success:
            batch_added = len(safe_files)
            print(f'  ✓ Batch processed {batch_added} files')
            # Log batch progress
            if logger and op_id:
                logger.update_progress(op_id, batch_added, len(files), 'batch complete', 'ok')
        else:
            if is_fatal_error(error):
                print(f'Fatal error during batch: {error}', file=sys.stderr)
                if logger and op_id:
                    logger.complete_operation(op_id, success=False, summary={'error': error[:100]})
                return {
                    'success': False,
                    'error': error,
                    'added': 0,
                    'skipped': 0,
                    'skipped_files': [],
                }

            # Batch failed - fall back to individual processing
            print(f'  ⚠ Batch failed, falling back to individual processing...')
            print(f'    Error: {error[:200]}...' if len(error) > 200 else f'    Error: {error}')

            # Create RAG with first safe file, then add rest individually
            if safe_files:
                first_file = safe_files[0]
                temp_dir = tempfile.mkdtemp(prefix='rlama_init_')
                try:
                    os.symlink(str(first_file.resolve()), os.path.join(temp_dir, first_file.name))
                    cmd = [
                        'rag', model, rag_name, temp_dir,
                        '--chunking', chunking,
                        '--chunk-size', str(chunk_size),
                        '--chunk-overlap', str(chunk_overlap),
                    ]
                    stdout, stderr, code = run_rlama_command(cmd, timeout=120)
                    if code == 0:
                        batch_added = 1
                        safe_files = safe_files[1:]  # Remove first file
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)

            # Add remaining safe files to large_files for individual processing
            large_files = safe_files + large_files
    else:
        # No safe files - create RAG with first large file
        if large_files:
            first_file = large_files[0]
            temp_dir = tempfile.mkdtemp(prefix='rlama_init_')
            try:
                os.symlink(str(first_file.resolve()), os.path.join(temp_dir, first_file.name))
                cmd = [
                    'rag', model, rag_name, temp_dir,
                    '--chunking', chunking,
                    '--chunk-size', str(chunk_size),
                    '--chunk-overlap', str(chunk_overlap),
                ]
                stdout, stderr, code = run_rlama_command(cmd, timeout=120)
                if code == 0:
                    batch_added = 1
                    large_files = large_files[1:]
                else:
                    skipped += 1
                    skipped_files.append(safe_relative_path(first_file, folder))
                    large_files = large_files[1:]
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)

    # Verify RAG was created
    if not verify_rag_exists(rag_name):
        return {
            'success': False,
            'error': f'Failed to create RAG "{rag_name}"',
            'added': batch_added,
            'skipped': skipped,
            'skipped_files': skipped_files,
        }

    # Step 2: Process large files individually
    if large_files:
        print(f'\nStep 2: Processing {len(large_files)} large files individually...')

        if parallel > 0:
            a, s, sf = process_files_parallel(rag_name, large_files, folder, parallel)
        else:
            a, s, sf = process_files_sequential(rag_name, large_files, folder)

        added += a
        skipped += s
        skipped_files.extend(sf)

    _print_summary(added, skipped, skipped_files, batch_added)

    # Log completion
    if logger and op_id:
        elapsed = time.time() - start_time
        logger.ingest_complete(op_id, batch_added + added, skipped, elapsed)

    return {
        'success': True,
        'added': batch_added + added,
        'skipped': skipped,
        'skipped_files': skipped_files,
    }


def resilient_add(
    rag_name: str,
    folder_path: str,
    docs_only: bool = False,
    process_exts: Optional[List[str]] = None,
    exclude_exts: Optional[List[str]] = None,
    exclude_dirs: Optional[List[str]] = None,
    safe_threshold_kb: int = DEFAULT_SAFE_THRESHOLD_KB,
    parallel: int = 0,
) -> dict:
    """Add files to an existing RAG using Pre-Filter + Batch approach."""

    # Initialize logger if available
    logger = get_logger() if LOGGER_AVAILABLE else None
    op_id = None
    start_time = time.time()

    # Verify RAG exists before attempting to add files
    if not verify_rag_exists(rag_name):
        return {
            'success': False,
            'error': f'RAG "{rag_name}" does not exist. Create it first with "create" command.',
            'added': 0,
            'skipped': 0,
            'skipped_files': [],
        }

    folder = Path(folder_path).expanduser().resolve()

    # Handle single file
    if folder.is_file():
        print(f'Adding single file: {folder.name}')
        success, error = add_single_file(rag_name, folder)

        if success:
            print('✓ Added successfully')
            return {'success': True, 'added': 1, 'skipped': 0, 'skipped_files': []}
        else:
            print(f'⚠ Failed: {error}')
            return {
                'success': False,
                'added': 0,
                'skipped': 1,
                'skipped_files': [str(folder.name)],
                'error': error,
            }

    if not folder.exists():
        return {
            'success': False,
            'error': f'Folder not found: {folder}',
            'added': 0,
            'skipped': 0,
            'skipped_files': [],
        }

    # Get list of files to process
    files = get_supported_files(
        folder,
        docs_only=docs_only,
        process_exts=process_exts,
        exclude_exts=exclude_exts,
        exclude_dirs=exclude_dirs,
    )

    if not files:
        return {
            'success': False,
            'error': 'No supported files found in folder',
            'added': 0,
            'skipped': 0,
            'skipped_files': [],
        }

    # Split files into safe (batch) and large (individual)
    safe_files = [f for f in files if is_safe_file(f, safe_threshold_kb)]
    large_files = [f for f in files if not is_safe_file(f, safe_threshold_kb)]

    print(f'Found {len(files)} files to add to "{rag_name}"')
    print(f'  - {len(safe_files)} safe files (batch processing)')
    print(f'  - {len(large_files)} large files (individual processing)')
    print()

    # Start logging operation
    if logger:
        op_id = logger.ingest_start(rag_name, str(folder), len(files))

    batch_added = 0
    added = 0
    skipped = 0
    skipped_files = []

    # Step 1: Process safe files in batch
    if safe_files:
        print(f'Step 1: Batch processing {len(safe_files)} safe files...')
        success, error, failed = process_batch(rag_name, safe_files, is_create=False)

        if success:
            batch_added = len(safe_files)
            print(f'  ✓ Batch processed {batch_added} files')
            # Log batch progress
            if logger and op_id:
                logger.update_progress(op_id, batch_added, len(files), 'batch complete', 'ok')
        else:
            if is_fatal_error(error):
                print(f'Fatal error during batch: {error}', file=sys.stderr)
                if logger and op_id:
                    logger.complete_operation(op_id, success=False, summary={'error': error[:100]})
                return {
                    'success': False,
                    'error': error,
                    'added': 0,
                    'skipped': 0,
                    'skipped_files': [],
                }

            # Batch failed - add safe files to individual processing
            print(f'  ⚠ Batch failed, falling back to individual processing...')
            large_files = safe_files + large_files

    # Step 2: Process large files individually
    if large_files:
        print(f'\nStep 2: Processing {len(large_files)} files individually...')

        if parallel > 0:
            a, s, sf = process_files_parallel(rag_name, large_files, folder, parallel)
        else:
            a, s, sf = process_files_sequential(rag_name, large_files, folder)

        added += a
        skipped += s
        skipped_files.extend(sf)

    _print_summary(added, skipped, skipped_files, batch_added)

    # Log completion
    if logger and op_id:
        elapsed = time.time() - start_time
        logger.ingest_complete(op_id, batch_added + added, skipped, elapsed)

    return {
        'success': True,
        'added': batch_added + added,
        'skipped': skipped,
        'skipped_files': skipped_files,
    }


def main():
    parser = argparse.ArgumentParser(
        description='Fast resilient RLAMA indexing with Pre-Filter + Batch approach',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Commands:
  create   Create a new RAG with resilient batch processing
  add      Add documents to an existing RAG

Examples:
  %(prog)s create my-rag ~/Documents
  %(prog)s create my-rag ~/Research --docs-only
  %(prog)s create my-rag ~/Code --parallel 4
  %(prog)s add my-rag ./more-docs --parallel 8

Speed optimization:
- Files under 12KB are batched together (one fast call)
- Files over 12KB are processed individually (avoids context overflow)
- Use --parallel N for concurrent individual file processing
- Use --safe-threshold to adjust the batch/individual cutoff
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new RAG (resilient mode)')
    create_parser.add_argument('rag_name', help='Name for the new RAG')
    create_parser.add_argument('folder_path', help='Path to folder with documents')
    create_parser.add_argument('--model', '-m', default=DEFAULT_MODEL,
        help=f'LLM model (default: {DEFAULT_MODEL})')
    create_parser.add_argument('--legacy', action='store_true',
        help=f'Use {LEGACY_MODEL} instead of {DEFAULT_MODEL}')
    create_parser.add_argument('--chunking', choices=['fixed', 'semantic', 'hybrid', 'hierarchical'],
        default='hybrid', help='Chunking strategy (default: hybrid)')
    create_parser.add_argument('--chunk-size', type=int, default=1000,
        help='Chunk size in characters (default: 1000)')
    create_parser.add_argument('--chunk-overlap', type=int, default=200,
        help='Chunk overlap in characters (default: 200)')
    create_parser.add_argument('--docs-only', action='store_true',
        help='Only index documents (PDF, MD, TXT, DOCX, DOC, ORG)')
    create_parser.add_argument('--process-exts', nargs='+',
        help='Only process these file extensions')
    create_parser.add_argument('--exclude-exts', nargs='+',
        help='Exclude these file extensions')
    create_parser.add_argument('--exclude-dirs', nargs='+',
        help='Exclude these directories')
    create_parser.add_argument('--safe-threshold', type=int, default=DEFAULT_SAFE_THRESHOLD_KB,
        help=f'Files under this size (KB) are batched (default: {DEFAULT_SAFE_THRESHOLD_KB})')
    create_parser.add_argument('--parallel', '-p', type=int, default=0,
        help='Number of parallel workers for individual files (default: 0 = sequential)')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add documents to a RAG (resilient mode)')
    add_parser.add_argument('rag_name', help='Name of the existing RAG')
    add_parser.add_argument('folder_path', help='Path to folder or file to add')
    add_parser.add_argument('--docs-only', action='store_true',
        help='Only index documents (PDF, MD, TXT, DOCX, DOC, ORG)')
    add_parser.add_argument('--process-exts', nargs='+',
        help='Only process these file extensions')
    add_parser.add_argument('--exclude-exts', nargs='+',
        help='Exclude these file extensions')
    add_parser.add_argument('--exclude-dirs', nargs='+',
        help='Exclude these directories')
    add_parser.add_argument('--safe-threshold', type=int, default=DEFAULT_SAFE_THRESHOLD_KB,
        help=f'Files under this size (KB) are batched (default: {DEFAULT_SAFE_THRESHOLD_KB})')
    add_parser.add_argument('--parallel', '-p', type=int, default=0,
        help='Number of parallel workers for individual files (default: 0 = sequential)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'create':
        # Handle --legacy flag: only apply if model wasn't explicitly changed
        if args.legacy and args.model == DEFAULT_MODEL:
            model = LEGACY_MODEL
        else:
            model = args.model

        if args.docs_only:
            print(f'Using --docs-only mode: indexing PDF, MD, TXT, DOCX, DOC, ORG only')

        result = resilient_create(
            rag_name=args.rag_name,
            folder_path=args.folder_path,
            model=model,
            chunking=args.chunking,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            docs_only=args.docs_only,
            process_exts=args.process_exts,
            exclude_exts=args.exclude_exts,
            exclude_dirs=args.exclude_dirs,
            safe_threshold_kb=args.safe_threshold,
            parallel=args.parallel,
        )

        sys.exit(0 if result['success'] else 1)

    elif args.command == 'add':
        if args.docs_only:
            print(f'Using --docs-only mode: indexing PDF, MD, TXT, DOCX, DOC, ORG only')

        result = resilient_add(
            rag_name=args.rag_name,
            folder_path=args.folder_path,
            docs_only=args.docs_only,
            process_exts=args.process_exts,
            exclude_exts=args.exclude_exts,
            exclude_dirs=args.exclude_dirs,
            safe_threshold_kb=args.safe_threshold,
            parallel=args.parallel,
        )

        sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
