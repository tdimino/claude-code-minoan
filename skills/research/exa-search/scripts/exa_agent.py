#!/usr/bin/env python3
"""
Exa Agent - async research, list building, and enrichment via the Agent API.

Replaces the retired Research API (/research/v0, /research/v1 return 410).
A run searches, reads, and verifies across many steps, then returns prose
(output.text), schema-shaped JSON (output.structured), and field-level
citations (output.grounding). This script creates a run and polls it.

Effort (price per run):
  minimal $0.012 · low $0.025 · medium $0.10 (default here) · high $0.50 · xhigh $1.00
  auto  metered, $5 cap  (the API's own default; --max-cost $1-100)
  ultra metered, $20 cap (--max-cost $1-100, --max-duration 300-10800s; `stop` keeps partial results)

Usage:
    exa_agent.py run "Who founded Anthropic and when?" --effort low
    exa_agent.py run "Find 10 AI infra startups that raised Series A in 2026" \\
        --schema-preset company --max-items 10 --effort auto --max-cost 3
    exa_agent.py run "Add CEO and HQ for each company" --input-file companies.json
    exa_agent.py status agent_run_abc123
    exa_agent.py list --limit 5
    exa_agent.py cancel agent_run_abc123

Requires: EXA_API_KEY environment variable
Install: pip install requests
"""

import sys
import json
import time
import copy
import argparse
from typing import Optional, List, Dict, Any

from _exa_common import (
    ExaAPIError, add_schema_args, die, format_cost, format_grounding, get, load_schema, post,
)

EFFORTS = ["minimal", "low", "medium", "high", "xhigh", "auto", "ultra"]
DEFAULT_CAPS = {"auto": 5, "ultra": 20}
DATA_SOURCES = ["fiber", "financial_datasets", "similarweb", "baselayer", "affiliate",
                "particle", "jinko", "polymarket", "macrobond"]
TERMINAL = ("completed", "failed", "cancelled")
POLL_INTERVAL = 4  # seconds, per Exa's agent quickstart
POLL_RETRIES = 3   # consecutive transient failures (network or 5xx) tolerated while polling


class PollLost(Exception):
    """Polling stopped before a terminal status; the run itself continues server-side."""

    def __init__(self, run: Dict[str, Any], reason: str):
        self.run, self.reason = run, reason
        super().__init__(reason)


def _load_records(path: str, flag: str) -> List[Dict[str, Any]]:
    """Read a JSON array of objects, or JSONL, for input.data / input.exclusion."""
    try:
        with open(path) as f:
            raw = f.read()
    except OSError as e:
        raise ValueError(f"{flag}: {e}")
    try:
        records = json.loads(raw)
    except json.JSONDecodeError:
        try:
            records = [json.loads(line) for line in raw.splitlines() if line.strip()]
        except json.JSONDecodeError as e:
            raise ValueError(f"{flag}: not a JSON array or JSONL file ({e})")
    if isinstance(records, dict):  # a one-line JSONL file parses as a single object
        records = [records]
    if not isinstance(records, list) or not all(isinstance(r, dict) for r in records):
        raise ValueError(f"{flag}: expected a list of JSON objects")
    return records


def bound_arrays(schema: Dict[str, Any], max_items: int) -> Dict[str, Any]:
    """Set maxItems on top-level array properties so list-building cost stays predictable."""
    schema = copy.deepcopy(schema)
    for prop in (schema.get("properties") or {}).values():
        if isinstance(prop, dict) and prop.get("type") == "array":
            prop["maxItems"] = max_items
    return schema


def build_run_payload(
    query: str,
    effort: str = "medium",
    system_prompt: Optional[str] = None,
    output_schema: Optional[Dict[str, Any]] = None,
    input_data: Optional[List[Dict[str, Any]]] = None,
    exclusion: Optional[List[Dict[str, Any]]] = None,
    previous_run_id: Optional[str] = None,
    data_sources: Optional[List[str]] = None,
    max_cost: Optional[float] = None,
    max_duration: Optional[int] = None,
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the POST /agent/runs body. Effort is always sent (the API default is metered auto)."""
    if effort not in EFFORTS:
        raise ValueError(f"Invalid effort '{effort}'. Must be one of: {EFFORTS}")
    if max_cost is not None:
        if effort not in DEFAULT_CAPS:
            raise ValueError("--max-cost applies only to --effort auto or ultra (fixed efforts have a fixed price)")
        if not 1 <= max_cost <= 100:
            raise ValueError("--max-cost must be between 1 and 100 dollars")
    if max_duration is not None:
        if effort != "ultra":
            raise ValueError("--max-duration applies only to --effort ultra")
        if not 300 <= max_duration <= 10800:
            raise ValueError("--max-duration must be between 300 and 10800 seconds")

    payload: Dict[str, Any] = {"query": query, "effort": effort}
    if system_prompt:
        payload["systemPrompt"] = system_prompt
    if output_schema:
        payload["outputSchema"] = output_schema
    if input_data or exclusion:
        payload["input"] = {}
        if input_data:
            payload["input"]["data"] = input_data
        if exclusion:
            payload["input"]["exclusion"] = exclusion
    if previous_run_id:
        payload["previousRunId"] = previous_run_id
    if data_sources:
        providers = list(dict.fromkeys(data_sources))
        if len(providers) > 5:
            raise ValueError("--data-source accepts at most 5 providers per run")
        payload["dataSources"] = [{"provider": p} for p in providers]
    budget: Dict[str, Any] = {}
    if max_cost is not None:
        budget["maxCostDollars"] = max_cost
    if max_duration is not None:
        budget["maxDurationSeconds"] = max_duration
    if budget:
        payload["budget"] = budget
    if user_id:
        payload["userIdentifier"] = user_id
    return payload


def wait_for_run(run: Dict[str, Any], timeout: int) -> Dict[str, Any]:
    """Poll GET /agent/runs/{id} until a terminal status or the timeout.

    Transient failures (network errors, 5xx) are retried; if they persist, or the
    user interrupts, PollLost carries the last known run so its ID is not lost.
    """
    deadline = time.monotonic() + timeout
    failures = 0
    try:
        while run.get("status") not in TERMINAL and time.monotonic() < deadline:
            time.sleep(POLL_INTERVAL)
            try:
                run = get(f"/agent/runs/{run['id']}")
                failures = 0
            except ExaAPIError as e:
                if e.status != 0 and e.status < 500:
                    raise
                failures += 1
                if failures > POLL_RETRIES:
                    raise PollLost(run, str(e))
    except KeyboardInterrupt:
        raise PollLost(run, "interrupted")
    return run


def format_run(run: Dict[str, Any]) -> str:
    """Readable run: status line, answer text, structured output, grounding, usage, cost."""
    request = run.get("request") or {}
    output = [f"Run: {run.get('id')}  status={run.get('status')}  effort={request.get('effort') or '?'}"
              f"  stopReason={run.get('stopReason')}"]
    out = run.get("output") or {}
    if out.get("text"):
        output += [f"\n{'='*60}", "ANSWER:", "-" * 40, out["text"]]
    if out.get("structured") is not None:
        output += [f"\n{'='*60}", "STRUCTURED OUTPUT:", "-" * 40, json.dumps(out["structured"], indent=2)]
    output.extend(format_grounding(out.get("grounding")))
    usage = run.get("usage") or {}
    if usage:
        output.append(f"\nUsage: {usage.get('agentComputeUnits', 0)} ACU, {usage.get('searches', 0)} searches, "
                      f"{usage.get('emails', 0)} emails, {usage.get('phoneNumbers', 0)} phone numbers")
    output.extend(format_cost(run.get("costDollars")))
    return "\n".join(output)


def format_run_list(listing: Dict[str, Any]) -> str:
    rows = listing.get("data") or []
    output = [f"RUNS ({len(rows)}{'+' if listing.get('hasMore') else ''}):"]
    for run in rows:
        request = run.get("request") or {}
        cost = (run.get("costDollars") or {}).get("total") or 0
        output.append(f"  {run.get('id')}  {run.get('status') or '?':<9}  {request.get('effort') or '?':<7}  "
                      f"${cost:.3f}  {(run.get('createdAt') or '')[:19]}  {(request.get('query') or '')[:60]}")
    if listing.get("nextCursor"):
        output.append(f"  next: --cursor {listing['nextCursor']}")
    return "\n".join(output)


def _emit(run: Dict[str, Any], as_json: bool) -> None:
    print(json.dumps(run, indent=2) if as_json else format_run(run))


def _exit_for(run: Dict[str, Any], timeout: int) -> None:
    """Exit 3 if still running after the timeout, 1 if failed or cancelled."""
    status = run.get("status")
    if status not in TERMINAL:
        print(f"Still {status} after {timeout}s; check later: "
              f"exa_agent.py status {run['id']} --wait", file=sys.stderr)
        sys.exit(3)
    if status in ("failed", "cancelled"):
        print(f"Run {run['id']} {status} (stopReason={run.get('stopReason')})", file=sys.stderr)
        sys.exit(1)


def _poll_lost(err: PollLost, as_json: bool) -> None:
    run_id = err.run.get("id")
    if as_json:
        print(json.dumps({"id": run_id, "status": "unknown", "error": err.reason}, indent=2))
    print(f"Lost track of run {run_id} ({err.reason}); it continues on Exa's side. "
          f"Resume: exa_agent.py status {run_id} --wait", file=sys.stderr)
    sys.exit(3)


def main():
    parser = argparse.ArgumentParser(
        description="Exa Agent - async research, list building, and enrichment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Effort: minimal $0.012 | low $0.025 | medium $0.10 (default) | high $0.50 | xhigh $1.00
        auto (metered, $5 cap) | ultra (metered, $20 cap)

Examples:
  %(prog)s run "Who founded Anthropic and when?" --effort low
  %(prog)s run "Find 10 AI infra startups that raised Series A in 2026" \\
      --schema-preset company --max-items 10 --effort auto --max-cost 3
  %(prog)s run "Add CEO and HQ for each" --input-file rows.json --exclude-file seen.json
  %(prog)s status agent_run_abc123
  %(prog)s list --limit 5
        """
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Create a run and wait for it")
    run_p.add_argument("query", help="Task: what to find, scope, evidence required, what complete looks like")
    run_p.add_argument("--effort", choices=EFFORTS, default="medium", help="Effort tier (default: medium, $0.10)")
    add_schema_args(run_p, text_output=False)
    run_p.add_argument("--max-items", type=int, help="Set maxItems on top-level array fields of the schema")
    run_p.add_argument("--system-prompt", help="Source preferences, novelty or duplication constraints")
    run_p.add_argument("--input-file", help="JSON array or JSONL of records to enrich (input.data)")
    run_p.add_argument("--exclude-file", help="JSON array or JSONL of records to avoid (input.exclusion)")
    run_p.add_argument("--previous-run", help="Completed run ID to continue from")
    run_p.add_argument("--data-source", action="append", choices=DATA_SOURCES,
                       help="Exa Connect provider to enable (repeatable; billed per call)")
    run_p.add_argument("--max-cost", type=float, help="Budget cap in dollars, 1-100 (auto/ultra only)")
    run_p.add_argument("--max-duration", type=int, help="Soft time limit in seconds, 300-10800 (ultra only)")
    run_p.add_argument("--user-id", help="Opaque end-user ID for usage attribution (no PII)")
    run_p.add_argument("--no-wait", action="store_true", help="Return the run ID immediately")
    run_p.add_argument("--timeout", type=int, default=600, help="Seconds to poll before returning (default: 600)")
    run_p.add_argument("--json", action="store_true", help="Output the raw run JSON")

    status_p = sub.add_parser("status", help="Get a run")
    status_p.add_argument("run_id")
    status_p.add_argument("--wait", action="store_true", help="Poll until the run finishes")
    status_p.add_argument("--timeout", type=int, default=600)
    status_p.add_argument("--json", action="store_true")

    list_p = sub.add_parser("list", help="List recent runs")
    list_p.add_argument("--limit", type=int, default=20, help="1-100 (default: 20)")
    list_p.add_argument("--cursor", help="nextCursor from a previous listing")
    list_p.add_argument("--json", action="store_true")

    for name, help_text in [("cancel", "Cancel a queued or running run (no results returned)"),
                            ("stop", "Finish an ultra run early, keeping results so far")]:
        p = sub.add_parser(name, help=help_text)
        p.add_argument("run_id")
        p.add_argument("--json", action="store_true")

    args = parser.parse_args()

    try:
        if args.command == "run":
            try:
                schema = load_schema(args.output_schema, args.schema_file, args.schema_preset)
                if args.max_items and not schema:
                    raise ValueError("--max-items needs a schema (--output-schema, --schema-file, or --schema-preset)")
                if schema and args.max_items:
                    schema = bound_arrays(schema, args.max_items)
                payload = build_run_payload(
                    args.query,
                    effort=args.effort,
                    system_prompt=args.system_prompt,
                    output_schema=schema,
                    input_data=_load_records(args.input_file, "--input-file") if args.input_file else None,
                    exclusion=_load_records(args.exclude_file, "--exclude-file") if args.exclude_file else None,
                    previous_run_id=args.previous_run,
                    data_sources=args.data_source,
                    max_cost=args.max_cost,
                    max_duration=args.max_duration,
                    user_id=args.user_id,
                )
            except ValueError as e:
                parser.error(str(e))
            if args.effort in DEFAULT_CAPS:
                cap = args.max_cost if args.max_cost is not None else DEFAULT_CAPS[args.effort]
                print(f"Note: --effort {args.effort} is metered; this run may cost up to ${cap:g}.", file=sys.stderr)
            run = post("/agent/runs", payload)
            print(f"Created {run['id']} ({run.get('status')})", file=sys.stderr)
            if args.no_wait:
                print(json.dumps(run, indent=2) if args.json else run["id"])
                return
            run = wait_for_run(run, args.timeout)
            _emit(run, args.json)
            _exit_for(run, args.timeout)

        elif args.command == "status":
            run = get(f"/agent/runs/{args.run_id}")
            if args.wait:
                run = wait_for_run(run, args.timeout)
            _emit(run, args.json)
            if args.wait:
                _exit_for(run, args.timeout)

        elif args.command == "list":
            listing = get("/agent/runs", params={"limit": args.limit, **({"cursor": args.cursor} if args.cursor else {})})
            print(json.dumps(listing, indent=2) if args.json else format_run_list(listing))

        elif args.command == "cancel":
            _emit(post(f"/agent/runs/{args.run_id}/cancel", {}), args.json)

        elif args.command == "stop":
            run = get(f"/agent/runs/{args.run_id}")
            effort = (run.get("request") or {}).get("effort")
            if effort and effort != "ultra":
                print(f"Error: stop is supported only for ultra runs (this run is {effort}); use cancel instead",
                      file=sys.stderr)
                sys.exit(1)
            _emit(post(f"/agent/runs/{args.run_id}/stop", {}), args.json)

    except PollLost as e:
        _poll_lost(e, getattr(args, "json", False))
    except (ExaAPIError, ValueError) as e:
        die(e)


if __name__ == "__main__":
    main()
