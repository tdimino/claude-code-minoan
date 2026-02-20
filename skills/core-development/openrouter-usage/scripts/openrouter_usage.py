#!/usr/bin/env python3
"""
OpenRouter Usage Report — query API costs for the last 30 days.

Endpoints used (read-only GETs):
  - GET /api/v1/activity  — per-model, per-day spend (requires Management key)
  - GET /api/v1/credits   — total credits purchased/used (requires Management key)

Management keys: https://openrouter.ai/settings/management-keys

Usage:
    openrouter-usage.py                  # Full 30-day summary
    openrouter-usage.py --date 2026-02-01  # Single day
    openrouter-usage.py --csv            # Export as CSV
    openrouter-usage.py --json           # Raw JSON output

Requires: OPENROUTER_API_KEY environment variable (Management key)
"""

import os
import sys
import json
import argparse
import pathlib
import requests
from collections import defaultdict
from datetime import datetime

BASE_URL = "https://openrouter.ai/api/v1"


def load_api_key():
    """Load OpenRouter Management key from env or fallback .env files.

    Checks OPENROUTER_MANAGEMENT_KEY first (dedicated management key),
    then falls back to OPENROUTER_API_KEY for backwards compatibility.
    """
    # Prefer dedicated management key
    key = os.environ.get("OPENROUTER_MANAGEMENT_KEY", "")
    if key:
        return key
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    for env_file in [
        pathlib.Path.home() / ".config/env/global.env",
        pathlib.Path.home() / "Desktop/Aldea/Prompt development/Aldea-Soul-Engine/.env",
        pathlib.Path.home() / "Desktop/minoanmystery-astro/.env",
    ]:
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENROUTER_MANAGEMENT_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def get_credits(api_key):
    """GET /api/v1/credits — total purchased vs used."""
    resp = requests.get(
        f"{BASE_URL}/credits",
        headers={"Authorization": f"Bearer {api_key}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json().get("data", {})


def get_activity(api_key, date=None):
    """GET /api/v1/activity — last 30 days grouped by endpoint."""
    params = {}
    if date:
        params["date"] = date
    resp = requests.get(
        f"{BASE_URL}/activity",
        headers={"Authorization": f"Bearer {api_key}"},
        params=params,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json().get("data", [])


def format_report(activity, credits_data=None):
    """Format activity data into a readable report."""
    lines = []
    lines.append("=" * 70)
    lines.append("OPENROUTER USAGE REPORT")
    lines.append("=" * 70)

    if credits_data:
        total = credits_data.get("total_credits", 0)
        used = credits_data.get("total_usage", 0)
        remaining = total - used
        lines.append(f"\nCredits:  ${total:.2f} purchased  |  ${used:.2f} used  |  ${remaining:.2f} remaining")

    if not activity:
        lines.append("\nNo activity data found.")
        return "\n".join(lines)

    # Aggregate by model
    by_model = defaultdict(lambda: {"usage": 0, "requests": 0, "prompt_tokens": 0, "completion_tokens": 0, "reasoning_tokens": 0})
    # Aggregate by date
    by_date = defaultdict(lambda: {"usage": 0, "requests": 0})
    # Aggregate by provider
    by_provider = defaultdict(lambda: {"usage": 0, "requests": 0})

    total_spend = 0
    total_requests = 0

    for item in activity:
        model = item.get("model", "unknown")
        date = item.get("date", "unknown")
        provider = item.get("provider_name", "unknown")
        usage = item.get("usage", 0) or 0
        byok = item.get("byok_usage_inference", 0) or 0
        spend = usage + byok
        reqs = item.get("requests", 0) or 0
        prompt = item.get("prompt_tokens", 0) or 0
        completion = item.get("completion_tokens", 0) or 0
        reasoning = item.get("reasoning_tokens", 0) or 0

        by_model[model]["usage"] += spend
        by_model[model]["requests"] += reqs
        by_model[model]["prompt_tokens"] += prompt
        by_model[model]["completion_tokens"] += completion
        by_model[model]["reasoning_tokens"] += reasoning

        by_date[date]["usage"] += spend
        by_date[date]["requests"] += reqs

        by_provider[provider]["usage"] += spend
        by_provider[provider]["requests"] += reqs

        total_spend += spend
        total_requests += reqs

    # Summary
    lines.append(f"\nTotal Spend:    ${total_spend:.4f}")
    lines.append(f"Total Requests: {total_requests:,}")
    dates = sorted(by_date.keys())
    if dates:
        lines.append(f"Date Range:     {dates[0]} to {dates[-1]}")

    # By Model (sorted by spend descending)
    lines.append(f"\n{'─' * 70}")
    lines.append("SPEND BY MODEL")
    lines.append(f"{'─' * 70}")
    lines.append(f"  {'Model':<45} {'Spend':>10} {'Requests':>10}")
    lines.append(f"  {'─'*45} {'─'*10} {'─'*10}")
    for model, data in sorted(by_model.items(), key=lambda x: x[1]["usage"], reverse=True):
        lines.append(f"  {model:<45} ${data['usage']:>9.4f} {data['requests']:>10,}")
        if data["prompt_tokens"] or data["completion_tokens"]:
            tokens_detail = f"    prompt: {data['prompt_tokens']:,}  completion: {data['completion_tokens']:,}"
            if data["reasoning_tokens"]:
                tokens_detail += f"  reasoning: {data['reasoning_tokens']:,}"
            lines.append(tokens_detail)

    # By Provider
    if len(by_provider) > 1:
        lines.append(f"\n{'─' * 70}")
        lines.append("SPEND BY PROVIDER")
        lines.append(f"{'─' * 70}")
        for provider, data in sorted(by_provider.items(), key=lambda x: x[1]["usage"], reverse=True):
            lines.append(f"  {provider:<30} ${data['usage']:>9.4f}  ({data['requests']:,} requests)")

    # By Date
    lines.append(f"\n{'─' * 70}")
    lines.append("SPEND BY DATE")
    lines.append(f"{'─' * 70}")
    for date in sorted(by_date.keys()):
        data = by_date[date]
        bar = "█" * max(1, int(data["usage"] / max(total_spend, 0.001) * 40))
        lines.append(f"  {date}  ${data['usage']:>8.4f}  {bar}")

    lines.append("")
    return "\n".join(lines)


def format_csv(activity):
    """Format activity as CSV."""
    lines = ["date,model,provider,spend,requests,prompt_tokens,completion_tokens,reasoning_tokens"]
    for item in sorted(activity, key=lambda x: (x.get("date", ""), x.get("model", ""))):
        usage = (item.get("usage", 0) or 0) + (item.get("byok_usage_inference", 0) or 0)
        lines.append(",".join([
            item.get("date", ""),
            f'"{item.get("model", "")}"',
            f'"{item.get("provider_name", "")}"',
            f"{usage:.6f}",
            str(item.get("requests", 0) or 0),
            str(item.get("prompt_tokens", 0) or 0),
            str(item.get("completion_tokens", 0) or 0),
            str(item.get("reasoning_tokens", 0) or 0),
        ]))
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="OpenRouter Usage Report")
    parser.add_argument("--date", help="Filter to a single UTC date (YYYY-MM-DD)")
    parser.add_argument("--csv", action="store_true", help="Output as CSV")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--no-credits", action="store_true", help="Skip credits lookup")
    args = parser.parse_args()

    api_key = load_api_key()
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found.", file=sys.stderr)
        print("Set it in your environment or in a .env file.", file=sys.stderr)
        sys.exit(1)

    try:
        activity = get_activity(api_key, date=args.date)

        if args.json:
            credits_data = None if args.no_credits else get_credits(api_key)
            print(json.dumps({"credits": credits_data, "activity": activity}, indent=2))
        elif args.csv:
            print(format_csv(activity))
        else:
            credits_data = None if args.no_credits else get_credits(api_key)
            print(format_report(activity, credits_data))

    except requests.exceptions.HTTPError as e:
        status = e.response.status_code if e.response is not None else "?"
        if status == 401:
            print("Error: Unauthorized. Your key may not be a Management key.", file=sys.stderr)
            print("Create one at: https://openrouter.ai/settings/management-keys", file=sys.stderr)
        elif status == 403:
            print("Error: Forbidden. This endpoint requires a Management API key.", file=sys.stderr)
            print("Create one at: https://openrouter.ai/settings/management-keys", file=sys.stderr)
        else:
            print(f"API Error ({status}): {e}", file=sys.stderr)
            if e.response is not None:
                print(f"Response: {e.response.text[:500]}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
