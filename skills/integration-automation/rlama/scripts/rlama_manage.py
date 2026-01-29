#!/usr/bin/env python3
"""
RLAMA Management Script - Create, add, remove, and delete RAG operations.

Usage:
    python3 rlama_manage.py create my-rag ~/Documents
    python3 rlama_manage.py add my-rag ./more-docs
    python3 rlama_manage.py remove my-rag document.pdf
    python3 rlama_manage.py delete my-rag
    python3 rlama_manage.py watch my-rag ~/Notes
"""

import argparse
import subprocess
import sys
import json
from pathlib import Path


def filter_warnings(text: str) -> str:
    """Filter out non-critical RLAMA warnings from output."""
    lines = text.split('\n')
    filtered = []
    skip_patterns = [
        'Warning: FlagEmbedding',
        'To install dependencies',
        'run: rlama install-dependencies',
    ]
    for line in lines:
        if not any(pattern in line for pattern in skip_patterns):
            filtered.append(line)
    return '\n'.join(filtered).strip()


def run_rlama_command(args: list, timeout: int = 600, stream: bool = False) -> tuple:
    """
    Run an rlama command and return (stdout, stderr, returncode).

    Args:
        args: Command arguments (without 'rlama' prefix)
        timeout: Command timeout in seconds
        stream: If True, stream output in real-time
    """
    try:
        if stream:
            # Stream output for long-running commands
            process = subprocess.Popen(
                ['rlama'] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            stdout_lines = []
            for line in process.stdout:
                filtered_line = filter_warnings(line.rstrip())
                if filtered_line:
                    print(filtered_line)
                    stdout_lines.append(filtered_line)

            stderr = process.stderr.read()
            process.wait()

            return (
                '\n'.join(stdout_lines),
                filter_warnings(stderr),
                process.returncode
            )
        else:
            result = subprocess.run(
                ['rlama'] + args,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return (
                filter_warnings(result.stdout),
                filter_warnings(result.stderr),
                result.returncode
            )
    except subprocess.TimeoutExpired:
        return ('', f'Command timed out after {timeout} seconds', 1)
    except FileNotFoundError:
        return ('', 'rlama command not found. Is RLAMA installed?', 1)
    except Exception as e:
        return ('', str(e), 1)


def create_rag(
    rag_name: str,
    folder_path: str,
    model: str = 'llama3.2',
    chunking: str = 'hybrid',
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    exclude_dirs: list = None,
    exclude_exts: list = None,
    process_exts: list = None,
    json_output: bool = False,
) -> dict:
    """Create a new RAG system from a folder."""

    # Expand path
    folder_path = str(Path(folder_path).expanduser().resolve())

    # Build command
    cmd = ['rag', model, rag_name, folder_path]

    cmd.extend(['--chunking', chunking])
    cmd.extend(['--chunk-size', str(chunk_size)])
    cmd.extend(['--chunk-overlap', str(chunk_overlap)])

    if exclude_dirs:
        cmd.extend(['--exclude-dir', ','.join(exclude_dirs)])

    if exclude_exts:
        cmd.extend(['--exclude-ext', ','.join(exclude_exts)])

    if process_exts:
        cmd.extend(['--process-ext', ','.join(process_exts)])

    print(f'Creating RAG "{rag_name}" from {folder_path}...')
    print(f'Model: {model}, Chunking: {chunking}')
    print()

    stdout, stderr, code = run_rlama_command(cmd, timeout=1800, stream=True)

    result = {
        'success': code == 0,
        'rag_name': rag_name,
        'folder_path': folder_path,
        'model': model,
        'message': stdout if code == 0 else stderr,
        'error': None if code == 0 else stderr
    }

    if json_output:
        print(json.dumps(result, indent=2))
    elif code != 0:
        print(f'\nError: {stderr}', file=sys.stderr)

    return result


def add_documents(
    rag_name: str,
    folder_path: str,
    exclude_dirs: list = None,
    exclude_exts: list = None,
    json_output: bool = False,
) -> dict:
    """Add documents to an existing RAG."""

    folder_path = str(Path(folder_path).expanduser().resolve())

    cmd = ['add-docs', rag_name, folder_path]

    if exclude_dirs:
        cmd.extend(['--exclude-dir', ','.join(exclude_dirs)])

    if exclude_exts:
        cmd.extend(['--exclude-ext', ','.join(exclude_exts)])

    print(f'Adding documents from {folder_path} to "{rag_name}"...')
    print()

    stdout, stderr, code = run_rlama_command(cmd, timeout=1800, stream=True)

    result = {
        'success': code == 0,
        'rag_name': rag_name,
        'folder_path': folder_path,
        'message': stdout if code == 0 else stderr,
        'error': None if code == 0 else stderr
    }

    if json_output:
        print(json.dumps(result, indent=2))
    elif code != 0:
        print(f'\nError: {stderr}', file=sys.stderr)

    return result


def remove_document(
    rag_name: str,
    doc_id: str,
    force: bool = False,
    json_output: bool = False,
) -> dict:
    """Remove a document from a RAG."""

    cmd = ['remove-doc', rag_name, doc_id]

    if force:
        cmd.append('--force')

    print(f'Removing "{doc_id}" from "{rag_name}"...')

    stdout, stderr, code = run_rlama_command(cmd, timeout=60)

    result = {
        'success': code == 0,
        'rag_name': rag_name,
        'document': doc_id,
        'message': stdout if code == 0 else stderr,
        'error': None if code == 0 else stderr
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        if code == 0:
            print(f'Successfully removed "{doc_id}"')
        else:
            print(f'Error: {stderr}', file=sys.stderr)

    return result


def delete_rag(
    rag_name: str,
    force: bool = False,
    json_output: bool = False,
) -> dict:
    """Delete a RAG system."""

    if not force:
        confirm = input(f'Delete RAG "{rag_name}"? This cannot be undone. [y/N]: ')
        if confirm.lower() != 'y':
            print('Aborted.')
            return {'success': False, 'rag_name': rag_name, 'message': 'Aborted by user'}

    cmd = ['delete', rag_name]

    print(f'Deleting RAG "{rag_name}"...')

    stdout, stderr, code = run_rlama_command(cmd, timeout=60)

    result = {
        'success': code == 0,
        'rag_name': rag_name,
        'message': stdout if code == 0 else stderr,
        'error': None if code == 0 else stderr
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        if code == 0:
            print(f'Successfully deleted "{rag_name}"')
        else:
            print(f'Error: {stderr}', file=sys.stderr)

    return result


def watch_directory(
    rag_name: str,
    folder_path: str,
    json_output: bool = False,
) -> dict:
    """Set up directory watching for a RAG."""

    folder_path = str(Path(folder_path).expanduser().resolve())

    cmd = ['watch', rag_name, folder_path]

    print(f'Setting up watch on {folder_path} for "{rag_name}"...')

    stdout, stderr, code = run_rlama_command(cmd, timeout=60)

    result = {
        'success': code == 0,
        'rag_name': rag_name,
        'watch_path': folder_path,
        'message': stdout if code == 0 else stderr,
        'error': None if code == 0 else stderr
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        if code == 0:
            print(f'Watch enabled. New files in {folder_path} will be indexed.')
            print(f'Check for updates: rlama check-watched {rag_name}')
            print(f'Disable: rlama watch-off {rag_name}')
        else:
            print(f'Error: {stderr}', file=sys.stderr)

    return result


def update_model(
    rag_name: str,
    new_model: str,
    json_output: bool = False,
) -> dict:
    """Update the model used by a RAG."""

    cmd = ['update-model', rag_name, new_model]

    print(f'Updating "{rag_name}" to use model {new_model}...')

    stdout, stderr, code = run_rlama_command(cmd, timeout=60)

    result = {
        'success': code == 0,
        'rag_name': rag_name,
        'new_model': new_model,
        'message': stdout if code == 0 else stderr,
        'error': None if code == 0 else stderr
    }

    if json_output:
        print(json.dumps(result, indent=2))
    else:
        if code == 0:
            print(f'Successfully updated to {new_model}')
        else:
            print(f'Error: {stderr}', file=sys.stderr)

    return result


def main():
    parser = argparse.ArgumentParser(
        description='Manage RLAMA RAG systems',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Commands:
  create   Create a new RAG from a folder
  add      Add documents to an existing RAG
  remove   Remove a document from a RAG
  delete   Delete a RAG system
  watch    Set up directory watching
  model    Update the model used by a RAG

Examples:
  %(prog)s create my-rag ~/Documents
  %(prog)s create my-rag ~/Code --exclude-dirs node_modules,dist
  %(prog)s add my-rag ./more-docs
  %(prog)s remove my-rag old-file.pdf
  %(prog)s delete my-rag --force
  %(prog)s watch my-rag ~/Notes
  %(prog)s model my-rag deepseek-r1:8b
'''
    )

    subparsers = parser.add_subparsers(dest='command', help='Command to run')

    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new RAG')
    create_parser.add_argument('rag_name', help='Name for the new RAG')
    create_parser.add_argument('folder_path', help='Path to folder with documents')
    create_parser.add_argument('--model', '-m', default='llama3.2', help='LLM model (default: llama3.2)')
    create_parser.add_argument('--chunking', choices=['fixed', 'semantic', 'hybrid', 'hierarchical'], default='hybrid')
    create_parser.add_argument('--chunk-size', type=int, default=1000)
    create_parser.add_argument('--chunk-overlap', type=int, default=200)
    create_parser.add_argument('--exclude-dirs', nargs='+', help='Directories to exclude')
    create_parser.add_argument('--exclude-exts', nargs='+', help='File extensions to exclude')
    create_parser.add_argument('--process-exts', nargs='+', help='Only process these extensions')
    create_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Add command
    add_parser = subparsers.add_parser('add', help='Add documents to a RAG')
    add_parser.add_argument('rag_name', help='Name of the RAG')
    add_parser.add_argument('folder_path', help='Path to folder or file to add')
    add_parser.add_argument('--exclude-dirs', nargs='+', help='Directories to exclude')
    add_parser.add_argument('--exclude-exts', nargs='+', help='File extensions to exclude')
    add_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a document from a RAG')
    remove_parser.add_argument('rag_name', help='Name of the RAG')
    remove_parser.add_argument('doc_id', help='Document ID (usually filename)')
    remove_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    remove_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a RAG system')
    delete_parser.add_argument('rag_name', help='Name of the RAG to delete')
    delete_parser.add_argument('--force', '-f', action='store_true', help='Skip confirmation')
    delete_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Watch command
    watch_parser = subparsers.add_parser('watch', help='Set up directory watching')
    watch_parser.add_argument('rag_name', help='Name of the RAG')
    watch_parser.add_argument('folder_path', help='Path to watch')
    watch_parser.add_argument('--json', action='store_true', help='Output as JSON')

    # Model command
    model_parser = subparsers.add_parser('model', help='Update RAG model')
    model_parser.add_argument('rag_name', help='Name of the RAG')
    model_parser.add_argument('new_model', help='New model to use')
    model_parser.add_argument('--json', action='store_true', help='Output as JSON')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    if args.command == 'create':
        result = create_rag(
            rag_name=args.rag_name,
            folder_path=args.folder_path,
            model=args.model,
            chunking=args.chunking,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap,
            exclude_dirs=args.exclude_dirs,
            exclude_exts=args.exclude_exts,
            process_exts=args.process_exts,
            json_output=args.json,
        )
        sys.exit(0 if result['success'] else 1)

    elif args.command == 'add':
        result = add_documents(
            rag_name=args.rag_name,
            folder_path=args.folder_path,
            exclude_dirs=args.exclude_dirs,
            exclude_exts=args.exclude_exts,
            json_output=args.json,
        )
        sys.exit(0 if result['success'] else 1)

    elif args.command == 'remove':
        result = remove_document(
            rag_name=args.rag_name,
            doc_id=args.doc_id,
            force=args.force,
            json_output=args.json,
        )
        sys.exit(0 if result['success'] else 1)

    elif args.command == 'delete':
        result = delete_rag(
            rag_name=args.rag_name,
            force=args.force,
            json_output=args.json,
        )
        sys.exit(0 if result['success'] else 1)

    elif args.command == 'watch':
        result = watch_directory(
            rag_name=args.rag_name,
            folder_path=args.folder_path,
            json_output=args.json,
        )
        sys.exit(0 if result['success'] else 1)

    elif args.command == 'model':
        result = update_model(
            rag_name=args.rag_name,
            new_model=args.new_model,
            json_output=args.json,
        )
        sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
