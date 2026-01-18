#!/usr/bin/env python3
"""
Exa Async Research - Advanced async research with pro models and structured output.

This script provides access to Exa's /research/v1 endpoint for long-running,
comprehensive research tasks with structured JSON output.

Features:
- Async job-based research (submit and poll for results)
- Model selection: exa-research-fast (quick), exa-research (standard), or exa-research-pro (enhanced)
- Structured JSON output with custom schemas
- Long-form research for complex topics
- Status polling with progress tracking

Use Cases:
- Complex multi-source research requiring synthesis
- Structured data extraction across topics
- Long-running research jobs
- Research with custom output formats
- Pro-quality research with enhanced model

Usage:
    exa_research_async.py "What species of ant are similar to honeypot ants?"
    exa_research_async.py "Compare top 5 AI startups" --pro
    exa_research_async.py "Quick market overview" --fast
    exa_research_async.py "Analyze climate policy trends" --schema '{"policies": [{"name": "string", "country": "string"}]}'
    exa_research_async.py status <research_id>
    exa_research_async.py list

Requires: EXA_API_KEY environment variable
Install: pip install requests
"""

import os
import sys
import json
import argparse
import time
import requests
from typing import Optional, Dict, Any

EXA_API_KEY = os.environ.get("EXA_API_KEY")
BASE_URL = "https://api.exa.ai"


def _headers() -> Dict[str, str]:
    """Get authentication headers."""
    if not EXA_API_KEY:
        raise ValueError("EXA_API_KEY environment variable not set. Get your key at https://dashboard.exa.ai")
    return {
        "Content-Type": "application/json",
        "x-api-key": EXA_API_KEY
    }


def create_research(
    instructions: str,
    model: str = "exa-research",
    output_schema: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Create a new async research request.

    Args:
        instructions: Instructions for what research should be conducted (max 4096 chars)
        model: Model to use - "exa-research-fast" (quick), "exa-research" (standard), or "exa-research-pro" (enhanced)
        output_schema: Optional JSON schema for structured output

    Returns:
        Dict with researchId and initial status
    """
    if len(instructions) > 4096:
        raise ValueError(f"Instructions too long ({len(instructions)} chars). Max is 4096.")

    valid_models = ["exa-research-fast", "exa-research", "exa-research-pro"]
    if model not in valid_models:
        raise ValueError(f"Invalid model '{model}'. Must be one of: {valid_models}")

    payload: Dict[str, Any] = {
        "instructions": instructions,
        "model": model,
    }

    if output_schema:
        payload["outputSchema"] = output_schema

    response = requests.post(
        f"{BASE_URL}/research/v1",
        headers=_headers(),
        json=payload
    )
    response.raise_for_status()
    return response.json()


def get_research_status(research_id: str) -> Dict[str, Any]:
    """
    Get the status and results of a research request.

    Args:
        research_id: The research ID from create_research

    Returns:
        Dict with status, and output if completed
    """
    response = requests.get(
        f"{BASE_URL}/research/v1/{research_id}",
        headers=_headers(),
    )
    response.raise_for_status()
    return response.json()


def list_research(cursor: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """
    List all research requests.

    Args:
        cursor: Pagination cursor
        limit: Number of results (1-50, default 10)

    Returns:
        Dict with data array and pagination info
    """
    params: Dict[str, Any] = {"limit": min(max(limit, 1), 50)}
    if cursor:
        params["cursor"] = cursor

    response = requests.get(
        f"{BASE_URL}/research/v1",
        headers=_headers(),
        params=params
    )
    response.raise_for_status()
    return response.json()


def wait_for_completion(research_id: str, timeout: int = 300, poll_interval: int = 5) -> Dict[str, Any]:
    """
    Wait for a research job to complete.

    Args:
        research_id: The research ID to wait for
        timeout: Maximum seconds to wait (default 300 = 5 minutes)
        poll_interval: Seconds between status checks (default 5)

    Returns:
        Final research result
    """
    start_time = time.time()

    while True:
        result = get_research_status(research_id)
        status = result.get("status", "unknown")

        if status == "completed":
            return result
        elif status == "failed":
            raise RuntimeError(f"Research failed: {result.get('error', 'Unknown error')}")
        elif status not in ["running", "pending"]:
            raise RuntimeError(f"Unknown status: {status}")

        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise TimeoutError(f"Research timed out after {timeout} seconds")

        print(f"Status: {status} (elapsed: {int(elapsed)}s)...", file=sys.stderr)
        time.sleep(poll_interval)


def format_result(result: Dict[str, Any]) -> str:
    """Format research result for display."""
    output = []

    output.append(f"Research ID: {result.get('researchId', 'Unknown')}")
    output.append(f"Status: {result.get('status', 'Unknown')}")
    output.append(f"Model: {result.get('model', 'Unknown')}")

    if result.get('createdAt'):
        from datetime import datetime
        created = datetime.fromtimestamp(result['createdAt'] / 1000)
        output.append(f"Created: {created.isoformat()}")

    if result.get('instructions'):
        output.append(f"\nInstructions: {result['instructions'][:200]}...")

    if result.get('output'):
        output.append(f"\n{'='*60}")
        output.append("OUTPUT:")
        output.append("-" * 40)
        out = result['output']
        if isinstance(out, dict):
            output.append(json.dumps(out, indent=2))
        else:
            output.append(str(out))

    if result.get('numSearches'):
        output.append(f"\nSearches performed: {result['numSearches']}")
    if result.get('numPages'):
        output.append(f"Pages analyzed: {result['numPages']}")
    if result.get('pageTokens'):
        output.append(f"Page tokens: {result['pageTokens']}")
    if result.get('reasoningTokens'):
        output.append(f"Reasoning tokens: {result['reasoningTokens']}")

    return "\n".join(output)


def format_list(results: Dict[str, Any]) -> str:
    """Format research list for display."""
    output = []
    data = results.get("data", [])

    output.append(f"Research Jobs ({len(data)} shown):")
    output.append("=" * 60)

    for r in data:
        status_emoji = {"completed": "✓", "running": "⟳", "failed": "✗"}.get(r.get('status'), "?")
        output.append(f"\n{status_emoji} {r.get('researchId', 'Unknown')}")
        output.append(f"  Model: {r.get('model', 'Unknown')}")
        output.append(f"  Status: {r.get('status', 'Unknown')}")
        if r.get('instructions'):
            output.append(f"  Instructions: {r['instructions'][:60]}...")

    if results.get('hasMore'):
        output.append(f"\n(More results available, use --cursor {results.get('nextCursor')})")

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Async Research - Advanced async research with pro models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  <instructions>  Create a new research job with the given instructions
  status <id>     Check status of a research job
  list            List all research jobs

Examples:
  %(prog)s "What species of ant are similar to honeypot ants?"
  %(prog)s "Compare top 5 AI agent frameworks" --pro --wait
  %(prog)s "Quick market overview" --fast
  %(prog)s "Analyze startup funding trends" --schema '{"startups": [{"name": "str", "funding": "int"}]}'
  %(prog)s status res_abc123
  %(prog)s list --limit 20

Models:
  exa-research-fast  Faster/cheaper research model for quick tasks
  exa-research       Standard research model (default)
  exa-research-pro   Enhanced research model with better synthesis
        """
    )

    parser.add_argument("command", nargs="?", help="Instructions, 'status', or 'list'")
    parser.add_argument("arg", nargs="?", help="Research ID for status command")

    parser.add_argument("--pro", action="store_true", help="Use exa-research-pro model")
    parser.add_argument("--fast", action="store_true", help="Use exa-research-fast model (quicker/cheaper)")
    parser.add_argument("--schema", help="JSON schema for structured output")
    parser.add_argument("--wait", action="store_true", help="Wait for completion (with 'create')")
    parser.add_argument("--timeout", type=int, default=300, help="Timeout in seconds (with --wait)")
    parser.add_argument("--limit", type=int, default=10, help="Results per page (with 'list')")
    parser.add_argument("--cursor", help="Pagination cursor (with 'list')")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == "list":
            results = list_research(cursor=args.cursor, limit=args.limit)
            if args.json:
                print(json.dumps(results, indent=2))
            else:
                print(format_list(results))

        elif args.command == "status":
            if not args.arg:
                print("Error: status command requires a research ID", file=sys.stderr)
                sys.exit(1)
            result = get_research_status(args.arg)
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(format_result(result))

        else:
            # Create new research
            instructions = args.command
            if args.arg:
                instructions = f"{args.command} {args.arg}"

            # Determine model: --pro > --fast > default
            if args.pro:
                model = "exa-research-pro"
            elif args.fast:
                model = "exa-research-fast"
            else:
                model = "exa-research"

            schema = None
            if args.schema:
                try:
                    schema = json.loads(args.schema)
                except json.JSONDecodeError as e:
                    print(f"Invalid JSON schema: {e}", file=sys.stderr)
                    sys.exit(1)

            result = create_research(
                instructions=instructions,
                model=model,
                output_schema=schema
            )

            research_id = result.get("researchId")
            print(f"Created research job: {research_id}", file=sys.stderr)

            if args.wait:
                print("Waiting for completion...", file=sys.stderr)
                result = wait_for_completion(research_id, timeout=args.timeout)

            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(format_result(result))

    except requests.exceptions.HTTPError as e:
        print(f"API Error: {e}", file=sys.stderr)
        if e.response is not None:
            print(f"Response: {e.response.text}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, RuntimeError, TimeoutError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
