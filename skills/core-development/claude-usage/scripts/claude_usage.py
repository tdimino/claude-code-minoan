#!/usr/bin/env python3
"""
Claude Usage Report — ground-truth token counts from JSONL session files.

ccusage undercounts output tokens by 77-94% because it ignores subagent files
and has timezone confusion. This script reads every JSONL file—parent sessions
and sidechains—to produce accurate numbers.

Data lives at ~/.claude/projects/{encoded-path}/{session-uuid}.jsonl (parent)
and {session-uuid}/subagents/{agent-id}.jsonl (sidechains).

Usage:
    claude_usage.py                              # today's usage
    claude_usage.py --since 7d                   # last 7 days
    claude_usage.py --since 2026-02-01           # since date
    claude_usage.py --by week --since 30d        # weekly breakdown
    claude_usage.py --by model --since 7d        # per-model breakdown
    claude_usage.py --by session --since 1d      # per-session with summaries
    claude_usage.py --by project --since 7d      # per-project breakdown
    claude_usage.py --project Thera --since 30d  # filter to one project
    claude_usage.py --json                       # machine-readable JSON
    claude_usage.py --csv                        # CSV output
    claude_usage.py --compare                    # show delta vs ccusage

Requires: Python 3.9+ (uses zoneinfo)
"""

import argparse
import csv
import io
import json
import os
import pathlib
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

# ─────────────────────────────────────────────
# PRICING TABLE
# Substring-matched against model name, most specific first.
# (input_per_mtok, output_per_mtok, cache_write_per_mtok, cache_read_per_mtok)
# Source: https://www.anthropic.com/pricing (Feb 2026)
# ─────────────────────────────────────────────
PRICING = {
    "opus-4":   (15.00, 75.00, 18.75, 1.50),
    "sonnet-4": ( 3.00, 15.00,  3.75, 0.30),
    "haiku-4":  ( 0.80,  4.00,  1.00, 0.08),
    "opus-3":   (15.00, 75.00, 18.75, 1.50),
    "sonnet-3": ( 3.00, 15.00,  3.75, 0.30),
    "haiku-3":  ( 0.25,  1.25,  0.30, 0.03),
}
DEFAULT_PRICING = (3.00, 15.00, 3.75, 0.30)

PROJECTS_DIR = pathlib.Path.home() / ".claude" / "projects"
_warned_models = set()


# ─────────────────────────────────────────────
# PRICING
# ─────────────────────────────────────────────

def get_pricing(model: str) -> tuple:
    """Match model name to pricing tier via substring."""
    m = model.lower()
    for key, prices in PRICING.items():
        if key in m:
            return prices
    if model not in _warned_models:
        print(f"  WARNING: no pricing for model '{model}', using default Sonnet rates", file=sys.stderr)
        _warned_models.add(model)
    return DEFAULT_PRICING


def calc_cost(usage: dict, model: str) -> float:
    """Calculate USD cost from a usage dict and model string."""
    inp, out, cw, cr = get_pricing(model)
    M = 1_000_000
    return (
        (usage.get("input_tokens", 0) or 0) * inp / M
        + (usage.get("output_tokens", 0) or 0) * out / M
        + (usage.get("cache_creation_input_tokens", 0) or 0) * cw / M
        + (usage.get("cache_read_input_tokens", 0) or 0) * cr / M
    )


# ─────────────────────────────────────────────
# JSONL DISCOVERY
# ─────────────────────────────────────────────

def iter_all_jsonl(project_filter=None):
    """
    Enumerate all JSONL files: parent sessions + subagent sidechains.

    Layout:
      {projects_dir}/{encoded-path}/{session-uuid}.jsonl         <- parent
      {projects_dir}/{encoded-path}/{session-uuid}/subagents/    <- subagents
        {agent-id}.jsonl

    Uses iterdir() (not rglob) to avoid descending into unrelated dirs.
    """
    if not PROJECTS_DIR.is_dir():
        return []

    files = []
    for project_dir in sorted(PROJECTS_DIR.iterdir()):
        if not project_dir.is_dir():
            continue
        if project_filter and project_filter.lower() not in project_dir.name.lower():
            continue
        for entry in project_dir.iterdir():
            if entry.suffix == ".jsonl" and entry.is_file():
                files.append(entry)
            elif entry.is_dir():
                subagents_dir = entry / "subagents"
                if subagents_dir.is_dir():
                    for sf in subagents_dir.iterdir():
                        if sf.suffix == ".jsonl" and sf.is_file():
                            files.append(sf)
    return files


def decode_project_path(encoded: str) -> str:
    """Convert encoded project path back to human-readable form.

    Claude Code encodes paths by replacing / with -.
    Reverse is ambiguous when dirs contain hyphens (e.g. bg3se-macos),
    so we greedily match against the actual filesystem.
    """
    parts = encoded.lstrip("-").split("-")
    resolved = "/"
    i = 0
    while i < len(parts):
        # Try longest possible segment first (greedy match)
        matched = False
        for j in range(len(parts), i, -1):
            candidate = "-".join(parts[i:j])
            full = os.path.join(resolved, candidate)
            if os.path.isdir(full) or os.path.isfile(full):
                resolved = full
                i = j
                matched = True
                break
        if not matched:
            resolved = os.path.join(resolved, parts[i])
            i += 1

    home = str(pathlib.Path.home())
    if resolved.startswith(home):
        resolved = "~" + resolved[len(home):]
    return resolved


# ─────────────────────────────────────────────
# JSONL PARSING
# ─────────────────────────────────────────────

def parse_jsonl(path, since_dt, until_dt, local_tz):
    """
    Stream-parse a JSONL file line by line (O(1) memory for 300MB+ files).
    Returns list of token records from assistant entries only.

    Skips: non-assistant entries, synthetic models, all-zero usage, entries
    outside the date window.
    """
    records = []
    is_sidechain = "subagents" in str(path)

    # Determine project from path structure
    if is_sidechain:
        # .../projects/{encoded-path}/{session-uuid}/subagents/{agent}.jsonl
        project_encoded = path.parts[-4] if len(path.parts) >= 5 else "unknown"
    else:
        # .../projects/{encoded-path}/{session-uuid}.jsonl
        project_encoded = path.parts[-2] if len(path.parts) >= 3 else "unknown"

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for raw_line in f:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    obj = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue

                if obj.get("type") != "assistant":
                    continue

                msg = obj.get("message", {})
                model = msg.get("model", "")
                if not model or model == "<synthetic>":
                    continue

                usage = msg.get("usage", {})
                total = (
                    (usage.get("input_tokens") or 0)
                    + (usage.get("output_tokens") or 0)
                    + (usage.get("cache_creation_input_tokens") or 0)
                    + (usage.get("cache_read_input_tokens") or 0)
                )
                if total == 0:
                    continue

                ts_str = obj.get("timestamp", "")
                if not ts_str:
                    continue
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                except ValueError:
                    continue

                ts_local = ts.astimezone(local_tz)

                if since_dt and ts_local < since_dt:
                    continue
                if until_dt and ts_local > until_dt:
                    continue

                records.append({
                    "ts": ts_local,
                    "model": model,
                    "session_id": obj.get("sessionId", path.stem),
                    "agent_id": obj.get("agentId"),
                    "is_sidechain": obj.get("isSidechain", is_sidechain),
                    "project": project_encoded,
                    "input_tokens": usage.get("input_tokens") or 0,
                    "output_tokens": usage.get("output_tokens") or 0,
                    "cache_creation_input_tokens": usage.get("cache_creation_input_tokens") or 0,
                    "cache_read_input_tokens": usage.get("cache_read_input_tokens") or 0,
                    "cost": calc_cost(usage, model),
                })
    except OSError as e:
        print(f"  WARNING: skipped {path.name}: {e}", file=sys.stderr)

    return records


# ─────────────────────────────────────────────
# SESSION NAME RESOLUTION
# ─────────────────────────────────────────────

def load_session_names():
    """Load session summaries from all sessions-index.json files."""
    names = {}
    if not PROJECTS_DIR.is_dir():
        return names
    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue
        idx = project_dir / "sessions-index.json"
        if not idx.is_file():
            continue
        try:
            data = json.loads(idx.read_text())
            for entry in data.get("entries", []):
                sid = entry.get("sessionId")
                summary = entry.get("summary") or entry.get("firstPrompt", "")[:60]
                if sid and summary:
                    names[sid] = summary
        except (json.JSONDecodeError, OSError):
            continue
    return names


# ─────────────────────────────────────────────
# AGGREGATION
# ─────────────────────────────────────────────

def new_bucket():
    return {
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "total_tokens": 0,
        "cost": 0.0,
        "entries": 0,
    }


def aggregate(records, by):
    """Aggregate records by: day | week | month | session | model | project."""
    groups = defaultdict(new_bucket)

    for r in records:
        ts = r["ts"]
        if by == "day":
            key = ts.strftime("%Y-%m-%d")
        elif by == "week":
            iso = ts.isocalendar()
            key = f"{iso.year}-W{iso.week:02d}"
        elif by == "month":
            key = ts.strftime("%Y-%m")
        elif by == "session":
            key = r["session_id"]
        elif by == "model":
            key = r["model"]
        elif by == "project":
            key = r["project"]
        else:
            key = ts.strftime("%Y-%m-%d")

        g = groups[key]
        g["input_tokens"] += r["input_tokens"]
        g["output_tokens"] += r["output_tokens"]
        g["cache_creation_input_tokens"] += r["cache_creation_input_tokens"]
        g["cache_read_input_tokens"] += r["cache_read_input_tokens"]
        total = r["input_tokens"] + r["output_tokens"] + r["cache_creation_input_tokens"] + r["cache_read_input_tokens"]
        g["total_tokens"] += total
        g["cost"] += r["cost"]
        g["entries"] += 1

    return dict(sorted(groups.items()))


def grand_total(groups):
    """Sum all groups into a grand total."""
    total = new_bucket()
    for g in groups.values():
        for k in total:
            total[k] += g[k]
    return total


# ─────────────────────────────────────────────
# FORMATTING — HUMAN TABLE
# ─────────────────────────────────────────────

def fmt_tok(n):
    """Format token count with K/M suffix for readability."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1_000:.0f}K"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def format_table(groups, by, total_records, session_names):
    """Render human-readable fixed-width table."""
    lines = []

    # Header
    lines.append("")
    lines.append("=" * 94)
    lines.append(f"  CLAUDE TOKEN USAGE — by {by}")
    lines.append("=" * 94)

    # Column headers
    if by == "project":
        col1 = "Project"
        col1_w = 36
    elif by == "session":
        col1 = "Session"
        col1_w = 36
    else:
        col1 = by.capitalize()
        col1_w = 16

    lines.append(
        f"  {col1:<{col1_w}} {'Input':>8} {'Output':>8} {'CacheW':>8} "
        f"{'CacheR':>8} {'Total':>10} {'Cost':>10}"
    )
    lines.append("  " + "─" * 92)

    for key, g in groups.items():
        label = key
        if by == "session" and key in session_names:
            label = f"{key[:8]}  {session_names[key][:24]}"
        elif by == "project":
            label = decode_project_path(key)
            if len(label) > col1_w:
                label = "..." + label[-(col1_w - 3):]

        lines.append(
            f"  {label:<{col1_w}} {fmt_tok(g['input_tokens']):>8} "
            f"{fmt_tok(g['output_tokens']):>8} "
            f"{fmt_tok(g['cache_creation_input_tokens']):>8} "
            f"{fmt_tok(g['cache_read_input_tokens']):>8} "
            f"{fmt_tok(g['total_tokens']):>10} "
            f"${g['cost']:>9.2f}"
        )

    # Grand total
    gt = grand_total(groups)
    lines.append("  " + "─" * 92)
    lines.append(
        f"  {'TOTAL':<{col1_w}} {fmt_tok(gt['input_tokens']):>8} "
        f"{fmt_tok(gt['output_tokens']):>8} "
        f"{fmt_tok(gt['cache_creation_input_tokens']):>8} "
        f"{fmt_tok(gt['cache_read_input_tokens']):>8} "
        f"{fmt_tok(gt['total_tokens']):>10} "
        f"${gt['cost']:>9.2f}"
    )
    lines.append("")
    lines.append(f"  {total_records:,} assistant entries parsed.")
    lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# FORMATTING — JSON
# ─────────────────────────────────────────────

def format_json(groups, by, total_records, metadata):
    """Machine-readable JSON output."""
    gt = grand_total(groups)
    output = {
        "by": by,
        "groups": groups,
        "grand_total": gt,
        "metadata": metadata,
    }
    return json.dumps(output, indent=2, default=str)


# ─────────────────────────────────────────────
# FORMATTING — CSV
# ─────────────────────────────────────────────

def format_csv(groups, by):
    """CSV output with header row."""
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([by, "input_tokens", "output_tokens", "cache_creation_input_tokens",
                     "cache_read_input_tokens", "total_tokens", "cost_usd"])
    for key, g in groups.items():
        writer.writerow([
            key,
            g["input_tokens"],
            g["output_tokens"],
            g["cache_creation_input_tokens"],
            g["cache_read_input_tokens"],
            g["total_tokens"],
            f"{g['cost']:.6f}",
        ])
    return buf.getvalue()


# ─────────────────────────────────────────────
# CCUSAGE COMPARISON
# ─────────────────────────────────────────────

def compare_with_ccusage(our_total):
    """Shell out to ccusage, parse its JSON, show delta."""
    try:
        result = subprocess.run(
            ["npx", "ccusage", "daily", "--json", "--since",
             datetime.now().strftime("%Y%m%d")],
            capture_output=True, text=True, timeout=60,
        )
        if result.returncode != 0:
            stderr_msg = result.stderr.strip()[:200] if result.stderr else ""
            return f"  ccusage returned non-zero exit code.{' ' + stderr_msg if stderr_msg else ''}"

        data = json.loads(result.stdout)
        cc_out = data.get("totals", {}).get("outputTokens", 0)
        cc_total = data.get("totals", {}).get("totalTokens", 0)
        cc_cost = data.get("totals", {}).get("totalCost", 0)

        our_out = our_total["output_tokens"]
        our_all = our_total["total_tokens"]
        our_cost = our_total["cost"]

        lines = [
            "",
            "  ── ccusage comparison ──",
            f"  {'Metric':<20} {'ccusage':>14} {'claude-usage':>14} {'Delta':>10}",
            f"  {'─' * 60}",
        ]

        def delta_str(ours, theirs):
            if theirs == 0:
                return "N/A"
            pct = (ours - theirs) / theirs * 100
            return f"{pct:+.0f}%"

        lines.append(
            f"  {'Output tokens':<20} {fmt_tok(cc_out):>14} {fmt_tok(our_out):>14} "
            f"{delta_str(our_out, cc_out):>10}"
        )
        lines.append(
            f"  {'Total tokens':<20} {fmt_tok(cc_total):>14} {fmt_tok(our_all):>14} "
            f"{delta_str(our_all, cc_total):>10}"
        )
        lines.append(
            f"  {'Cost (USD)':<20} ${cc_cost:>13.2f} ${our_cost:>13.2f} "
            f"{delta_str(our_cost, cc_cost):>10}"
        )
        lines.append("")

        return "\n".join(lines)

    except FileNotFoundError:
        return "  ccusage/npx not found in PATH."
    except subprocess.TimeoutExpired:
        return "  ccusage timed out after 60s."
    except json.JSONDecodeError as e:
        return f"  ccusage output parse error: {e}"


# ─────────────────────────────────────────────
# DATE RESOLUTION
# ─────────────────────────────────────────────

def resolve_since(since_str, local_tz):
    """Parse --since value: YYYY-MM-DD, Nd (last N days), or None (today)."""
    if since_str is None:
        return datetime.now(tz=local_tz).replace(hour=0, minute=0, second=0, microsecond=0)
    if re.match(r"^\d+d$", since_str):
        days = int(since_str[:-1])
        base = datetime.now(tz=local_tz) - timedelta(days=days)
        return base.replace(hour=0, minute=0, second=0, microsecond=0)
    try:
        dt = datetime.strptime(since_str, "%Y-%m-%d")
        return dt.replace(tzinfo=local_tz)
    except ValueError:
        print(f"Error: cannot parse --since '{since_str}'. Use YYYY-MM-DD or Nd.", file=sys.stderr)
        sys.exit(1)


def resolve_until(until_str, local_tz):
    """Parse --until value: YYYY-MM-DD or None (now)."""
    if until_str is None:
        return datetime.now(tz=local_tz)
    try:
        dt = datetime.strptime(until_str, "%Y-%m-%d")
        # End of day
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=local_tz)
    except ValueError:
        print(f"Error: cannot parse --until '{until_str}'. Use YYYY-MM-DD.", file=sys.stderr)
        sys.exit(1)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(
        description="Ground-truth Claude token usage from JSONL files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  claude_usage.py                        Today's usage
  claude_usage.py --since 7d             Last 7 days
  claude_usage.py --by week --since 30d  Weekly breakdown
  claude_usage.py --by model --since 7d  Per-model breakdown
  claude_usage.py --by session --since 1d Per-session with summaries
  claude_usage.py --by project --since 7d Per-project breakdown
  claude_usage.py --project Thera        Filter to one project
  claude_usage.py --json                 Machine-readable JSON
  claude_usage.py --compare              Show delta vs ccusage""",
    )
    p.add_argument("--since", help="Start date: YYYY-MM-DD or Nd (default: today)")
    p.add_argument("--until", help="End date: YYYY-MM-DD (default: now)")
    p.add_argument("--by", choices=["day", "week", "month", "session", "model", "project"],
                   default="day", help="Aggregation dimension (default: day)")
    p.add_argument("--project", help="Filter to projects whose path contains this string")
    p.add_argument("--json", action="store_true", dest="json_out", help="JSON output")
    p.add_argument("--csv", action="store_true", dest="csv_out", help="CSV output")
    p.add_argument("--compare", action="store_true", help="Show delta vs ccusage")
    p.add_argument("--tz", help="Timezone (e.g. America/New_York). Default: system tz")
    args = p.parse_args()

    # Resolve timezone
    if args.tz:
        try:
            local_tz = ZoneInfo(args.tz)
        except KeyError:
            print(f"Error: unknown timezone '{args.tz}'", file=sys.stderr)
            sys.exit(1)
    else:
        local_tz = datetime.now().astimezone().tzinfo

    since_dt = resolve_since(args.since, local_tz)
    until_dt = resolve_until(args.until, local_tz)

    # Discover files
    jsonl_files = iter_all_jsonl(project_filter=args.project)
    if not jsonl_files:
        print("No JSONL files found in ~/.claude/projects/", file=sys.stderr)
        sys.exit(1)

    # Parse all files
    all_records = []
    files_scanned = 0
    parent_files = 0
    subagent_files = 0

    for path in jsonl_files:
        records = parse_jsonl(path, since_dt, until_dt, local_tz)
        all_records.extend(records)
        files_scanned += 1
        if "subagents" in str(path):
            subagent_files += 1
        else:
            parent_files += 1

    if not all_records:
        since_str = since_dt.strftime("%Y-%m-%d")
        until_str = until_dt.strftime("%Y-%m-%d")
        print(f"No entries found between {since_str} and {until_str}.", file=sys.stderr)
        print(f"  Scanned {files_scanned} files ({parent_files} parent, {subagent_files} subagent).", file=sys.stderr)
        sys.exit(0)

    # Aggregate
    groups = aggregate(all_records, args.by)
    gt = grand_total(groups)
    session_names = load_session_names() if args.by == "session" else {}

    metadata = {
        "since": str(since_dt),
        "until": str(until_dt),
        "timezone": str(local_tz),
        "files_scanned": files_scanned,
        "parent_files": parent_files,
        "subagent_files": subagent_files,
        "total_entries": len(all_records),
        "project_filter": args.project,
    }

    # Output
    if args.json_out:
        print(format_json(groups, args.by, len(all_records), metadata))
    elif args.csv_out:
        print(format_csv(groups, args.by), end="")
    else:
        print(format_table(groups, args.by, len(all_records), session_names))
        print(f"  {files_scanned} files scanned ({parent_files} parent, {subagent_files} subagent)")
        since_label = args.since or "today"
        print(f"  Range: {since_label} → {until_dt.strftime('%Y-%m-%d %H:%M')}")
        print(f"  Timezone: {local_tz}")

    # Optional ccusage comparison
    if args.compare:
        print(compare_with_ccusage(gt))


if __name__ == "__main__":
    main()
