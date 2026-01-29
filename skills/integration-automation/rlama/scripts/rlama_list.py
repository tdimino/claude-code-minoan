#!/usr/bin/env python3
"""
RLAMA List Script - Clean formatted listing of RAG systems and documents.

Usage:
    python3 rlama_list.py                    # List all RAGs
    python3 rlama_list.py --docs my-rag      # List documents in a RAG
    python3 rlama_list.py --stats my-rag     # Show RAG statistics
    python3 rlama_list.py --json             # Output as JSON
"""

import argparse
import subprocess
import sys
import json
import re
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


def run_rlama_command(args: list, timeout: int = 60) -> tuple:
    """Run an rlama command and return (stdout, stderr, returncode)."""
    try:
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
        return ('', 'Command timed out', 1)
    except FileNotFoundError:
        return ('', 'rlama command not found', 1)
    except Exception as e:
        return ('', str(e), 1)


def list_rags(json_output: bool = False) -> dict:
    """List all available RAG systems."""
    stdout, stderr, code = run_rlama_command(['list'])

    if code != 0:
        return {'error': stderr or 'Failed to list RAGs', 'rags': []}

    # Parse the output
    rags = []
    lines = stdout.split('\n')

    # Skip header lines and parse data rows
    in_data = False
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if 'NAME' in line and 'MODEL' in line:
            in_data = True
            continue
        if in_data and line:
            # Parse table row: NAME  MODEL  CREATED ON  DOCUMENTS  SIZE
            parts = line.split()
            if len(parts) >= 5:
                # Handle date which has spaces
                rags.append({
                    'name': parts[0],
                    'model': parts[1],
                    'created': ' '.join(parts[2:4]) if len(parts) > 4 else parts[2],
                    'documents': parts[-2] if len(parts) > 4 else 'N/A',
                    'size': parts[-1] if len(parts) > 4 else 'N/A',
                })

    return {'rags': rags, 'count': len(rags), 'error': None}


def list_documents(rag_name: str, json_output: bool = False) -> dict:
    """List documents in a specific RAG."""
    stdout, stderr, code = run_rlama_command(['list-docs', rag_name])

    if code != 0:
        return {'error': stderr or f'Failed to list documents in {rag_name}', 'documents': []}

    # Parse the output
    documents = []
    lines = stdout.split('\n')

    for line in lines:
        line = line.strip()
        if line and not line.startswith('Documents') and not line.startswith('='):
            # Each line is a document
            documents.append({'name': line})

    return {
        'rag_name': rag_name,
        'documents': documents,
        'count': len(documents),
        'error': None
    }


def get_rag_stats(rag_name: str) -> dict:
    """Get statistics for a specific RAG."""
    # Get documents
    docs_result = list_documents(rag_name)

    # Get RAG info from list
    rags_result = list_rags()
    rag_info = None
    for rag in rags_result.get('rags', []):
        if rag['name'] == rag_name:
            rag_info = rag
            break

    # Check data directory
    data_dir = Path.home() / '.rlama' / rag_name
    exists = data_dir.exists()

    return {
        'name': rag_name,
        'exists': exists,
        'info': rag_info,
        'document_count': docs_result.get('count', 0),
        'documents': docs_result.get('documents', []),
        'data_path': str(data_dir),
        'error': docs_result.get('error') or rags_result.get('error')
    }


def format_rags_table(rags: list) -> str:
    """Format RAGs as a readable table."""
    if not rags:
        return 'No RAG systems found.\n\nCreate one with:\n  rlama rag llama3.2 my-rag ~/Documents'

    # Calculate column widths
    headers = ['Name', 'Model', 'Documents', 'Size', 'Created']
    rows = []
    for r in rags:
        rows.append([
            r.get('name', 'N/A'),
            r.get('model', 'N/A'),
            str(r.get('documents', 'N/A')),
            r.get('size', 'N/A'),
            r.get('created', 'N/A'),
        ])

    # Calculate widths
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    # Format output
    lines = []

    # Header
    header_line = '  '.join(h.ljust(widths[i]) for i, h in enumerate(headers))
    lines.append(header_line)
    lines.append('-' * len(header_line))

    # Rows
    for row in rows:
        lines.append('  '.join(cell.ljust(widths[i]) for i, cell in enumerate(row)))

    lines.append('')
    lines.append(f'Total: {len(rags)} RAG system(s)')

    return '\n'.join(lines)


def format_documents_list(rag_name: str, documents: list) -> str:
    """Format document list as readable output."""
    if not documents:
        return f'No documents in "{rag_name}".\n\nAdd documents with:\n  rlama add-docs {rag_name} <folder-path>'

    lines = [f'Documents in "{rag_name}" ({len(documents)} total):', '']
    for doc in documents:
        lines.append(f'  - {doc["name"]}')

    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(
        description='List RLAMA RAG systems and documents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s                     # List all RAG systems
  %(prog)s --docs my-rag       # List documents in my-rag
  %(prog)s --stats my-rag      # Show stats for my-rag
  %(prog)s --json              # Output as JSON
'''
    )

    parser.add_argument(
        '--docs', '-d',
        metavar='RAG_NAME',
        help='List documents in a specific RAG'
    )

    parser.add_argument(
        '--stats', '-s',
        metavar='RAG_NAME',
        help='Show statistics for a specific RAG'
    )

    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # Handle different modes
    if args.stats:
        result = get_rag_stats(args.stats)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result['error']:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            print(f"RAG: {result['name']}")
            print(f"Path: {result['data_path']}")
            print(f"Exists: {result['exists']}")
            if result['info']:
                print(f"Model: {result['info'].get('model', 'N/A')}")
                print(f"Size: {result['info'].get('size', 'N/A')}")
                print(f"Created: {result['info'].get('created', 'N/A')}")
            print(f"Documents: {result['document_count']}")

    elif args.docs:
        result = list_documents(args.docs)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result['error']:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            print(format_documents_list(args.docs, result['documents']))

    else:
        result = list_rags()
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result['error']:
                print(f"Error: {result['error']}", file=sys.stderr)
                sys.exit(1)
            print(format_rags_table(result['rags']))


if __name__ == '__main__':
    main()
