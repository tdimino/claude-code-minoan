#!/usr/bin/env python3
"""
RLAMA Query Script - Non-interactive RAG querying with clean output.

Usage:
    python3 rlama_query.py <rag-name> "your query"
    python3 rlama_query.py my-docs "what is the main idea?" --show-sources
    python3 rlama_query.py my-docs "explain auth" --context-size 30 --model deepseek-r1:8b
"""

import argparse
import subprocess
import sys
import json
import re


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


def query_rag(
    rag_name: str,
    query: str,
    context_size: int = 20,
    model: str = None,
    show_sources: bool = False,
    temperature: float = 0.7,
    max_tokens: int = None,
    verbose: bool = False,
    json_output: bool = False,
) -> dict:
    """
    Query a RLAMA RAG system non-interactively.

    Returns:
        dict with 'answer', 'sources' (if show_sources), and 'error' (if any)
    """
    cmd = ['rlama', 'run', rag_name, '--query', query, '--stream=false']

    if context_size:
        cmd.extend(['--context-size', str(context_size)])

    if model:
        cmd.extend(['-m', model])

    if show_sources:
        cmd.append('--show-context')

    if temperature != 0.7:
        cmd.extend(['--temperature', str(temperature)])

    if max_tokens:
        cmd.extend(['--max-tokens', str(max_tokens)])

    if verbose:
        cmd.append('--verbose')

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        stdout = filter_warnings(result.stdout)
        stderr = filter_warnings(result.stderr)

        if result.returncode != 0:
            return {
                'error': stderr or stdout or f'Command failed with code {result.returncode}',
                'answer': None,
                'sources': []
            }

        # Parse output
        output = {
            'answer': stdout,
            'sources': [],
            'error': None
        }

        # If show_sources, try to parse source info from output
        if show_sources and stdout:
            # RLAMA shows context info when --show-context is used
            # Format varies, but typically includes file paths
            source_pattern = r'(?:Source|Document|File):\s*(.+?)(?:\n|$)'
            sources = re.findall(source_pattern, stdout, re.IGNORECASE)
            if sources:
                output['sources'] = list(set(sources))

        return output

    except subprocess.TimeoutExpired:
        return {
            'error': 'Query timed out after 5 minutes',
            'answer': None,
            'sources': []
        }
    except FileNotFoundError:
        return {
            'error': 'rlama command not found. Is RLAMA installed?',
            'answer': None,
            'sources': []
        }
    except Exception as e:
        return {
            'error': str(e),
            'answer': None,
            'sources': []
        }


def list_rags() -> list:
    """List all available RAG systems."""
    try:
        result = subprocess.run(
            ['rlama', 'list'],
            capture_output=True,
            text=True,
            timeout=30
        )
        stdout = filter_warnings(result.stdout)
        return stdout
    except Exception as e:
        return f'Error listing RAGs: {e}'


def main():
    parser = argparse.ArgumentParser(
        description='Query a RLAMA RAG system non-interactively',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s my-docs "what is the main idea?"
  %(prog)s project-docs "explain the architecture" --show-sources
  %(prog)s research "summarize the findings" --context-size 30
  %(prog)s my-rag "complex question" --model deepseek-r1:8b
  %(prog)s --list  # List all RAGs
'''
    )

    parser.add_argument('rag_name', nargs='?', help='Name of the RAG system to query')
    parser.add_argument('query', nargs='?', help='The question to ask')

    parser.add_argument(
        '--context-size', '-c',
        type=int,
        default=20,
        help='Number of context chunks to retrieve (default: 20)'
    )

    parser.add_argument(
        '--model', '-m',
        help='Override the LLM model (e.g., deepseek-r1:8b, qwen2.5:7b)'
    )

    parser.add_argument(
        '--show-sources', '-s',
        action='store_true',
        help='Show which documents contributed to the answer'
    )

    parser.add_argument(
        '--temperature', '-t',
        type=float,
        default=0.7,
        help='Sampling temperature (default: 0.7)'
    )

    parser.add_argument(
        '--max-tokens',
        type=int,
        help='Maximum tokens to generate'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )

    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    parser.add_argument(
        '--list', '-l',
        action='store_true',
        help='List all available RAG systems'
    )

    args = parser.parse_args()

    # Handle --list
    if args.list:
        print(list_rags())
        return

    # Validate required arguments
    if not args.rag_name:
        parser.error('rag_name is required (or use --list to see available RAGs)')

    if not args.query:
        parser.error('query is required')

    # Execute query
    result = query_rag(
        rag_name=args.rag_name,
        query=args.query,
        context_size=args.context_size,
        model=args.model,
        show_sources=args.show_sources,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        verbose=args.verbose,
        json_output=args.json,
    )

    # Output
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result['error']:
            print(f"Error: {result['error']}", file=sys.stderr)
            sys.exit(1)

        print(result['answer'])

        if args.show_sources and result['sources']:
            print('\n--- Sources ---')
            for source in result['sources']:
                print(f'  - {source}')


if __name__ == '__main__':
    main()
