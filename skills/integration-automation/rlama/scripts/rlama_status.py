#!/usr/bin/env python3
"""
RLAMA Status - Check status of RLAMA operations.

Shows active and recent operations with progress, ETA, and summaries.

Usage:
    python3 rlama_status.py              # Show active operations
    python3 rlama_status.py --recent     # Show recent completed
    python3 rlama_status.py --follow     # Follow mode (like tail -f but formatted)
    python3 rlama_status.py --all        # Show both active and recent
"""

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path


# Log directory
LOG_DIR = Path.home() / '.rlama' / 'logs'
LOG_FILE = LOG_DIR / 'rlama.log'
OPERATIONS_FILE = LOG_DIR / 'operations.json'


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s"
    else:
        hours = int(seconds // 3600)
        mins = int((seconds % 3600) // 60)
        return f"{hours}h {mins}m"


def format_eta(eta_sec: int) -> str:
    """Format ETA in human-readable form."""
    if eta_sec is None:
        return "calculating..."
    return format_duration(eta_sec)


def format_time_ago(iso_time: str) -> str:
    """Format time as relative time ago."""
    try:
        dt = datetime.fromisoformat(iso_time)
        delta = datetime.now() - dt
        seconds = delta.total_seconds()

        if seconds < 60:
            return "just now"
        elif seconds < 3600:
            mins = int(seconds // 60)
            return f"{mins} minute{'s' if mins != 1 else ''} ago"
        elif seconds < 86400:
            hours = int(seconds // 3600)
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        else:
            days = int(seconds // 86400)
            return f"{days} day{'s' if days != 1 else ''} ago"
    except (ValueError, TypeError):
        return "unknown"


def load_operations_state() -> dict:
    """Load operations state from disk."""
    if not OPERATIONS_FILE.exists():
        return {'active': {}, 'recent': []}

    try:
        with open(OPERATIONS_FILE) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {'active': {}, 'recent': []}


def print_active_operations(operations: dict):
    """Print active operations."""
    if not operations:
        print("  No active operations")
        return

    for op_id, op in operations.items():
        op_type = op.get('type', 'unknown').upper()
        rag_name = op.get('rag_name', 'unknown')
        processed = op.get('processed', 0)
        total = op.get('total', 0)
        current = op.get('current_item')
        eta_sec = op.get('eta_sec')
        started = op.get('started')

        # Progress percentage
        pct = (processed / total * 100) if total > 0 else 0

        # Progress bar
        bar_width = 20
        filled = int(bar_width * pct / 100)
        bar = '=' * filled + '-' * (bar_width - filled)

        print(f"  [{op_type}] {rag_name}: {processed}/{total} files ({pct:.0f}%)")
        print(f"    [{bar}]")

        if current:
            # Truncate long filenames
            if len(current) > 50:
                current = '...' + current[-47:]
            print(f"    Current: {current}")

        if eta_sec:
            print(f"    ETA: {format_eta(eta_sec)}")

        if started:
            print(f"    Started: {format_time_ago(started)}")

        print()


def print_recent_operations(operations: list, limit: int = 10):
    """Print recent completed operations."""
    if not operations:
        print("  No recent operations")
        return

    # Show most recent first
    for op in reversed(operations[-limit:]):
        op_type = op.get('type', 'unknown').upper()
        rag_name = op.get('rag_name', 'unknown')
        success = op.get('success', False)
        completed = op.get('completed')
        duration = op.get('duration_sec', 0)
        summary = op.get('summary', {})

        status_icon = '\u2713' if success else '\u2717'  # checkmark or X
        status_text = 'Completed' if success else 'Failed'

        print(f"  [{op_type}] {rag_name}: {status_icon} {status_text} {format_time_ago(completed)}")

        # Summary details based on operation type
        if summary:
            details = []
            if 'added' in summary:
                details.append(f"Added: {summary['added']}")
            if 'skipped' in summary:
                details.append(f"Skipped: {summary['skipped']}")
            if 'removed' in summary:
                details.append(f"Removed: {summary['removed']}")
            if 'files_ingested' in summary:
                details.append(f"Files: {summary['files_ingested']}")
            if details:
                print(f"    {', '.join(details)}")

        print(f"    Duration: {format_duration(duration)}")
        print()


def follow_log():
    """Follow the log file and print formatted output."""
    if not LOG_FILE.exists():
        print(f"Log file not found: {LOG_FILE}")
        print("Run an RLAMA operation to create it.")
        return

    print(f"Following {LOG_FILE} (Ctrl+C to stop)\n")
    print("=" * 60)

    # Start from end of file
    with open(LOG_FILE) as f:
        f.seek(0, 2)  # Seek to end

        try:
            while True:
                line = f.readline()
                if line:
                    try:
                        entry = json.loads(line.strip())
                        print_log_entry(entry)
                    except json.JSONDecodeError:
                        print(line.strip())
                else:
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nStopped.")


def print_log_entry(entry: dict):
    """Print a formatted log entry."""
    ts = entry.get('ts', '')
    level = entry.get('level', 'info')
    cat = entry.get('cat', '')
    msg = entry.get('msg', '')
    data = entry.get('data', {})

    # Color codes (if terminal supports)
    colors = {
        'error': '\033[91m',  # Red
        'warn': '\033[93m',   # Yellow
        'info': '\033[92m',   # Green
        'debug': '\033[94m',  # Blue
        'reset': '\033[0m'
    }

    # Use colors if available
    try:
        import os
        use_color = os.isatty(1)
    except:
        use_color = False

    if use_color:
        level_color = colors.get(level, colors['info'])
        reset = colors['reset']
    else:
        level_color = ''
        reset = ''

    # Format timestamp (just time, not date)
    if ts:
        ts = ts.split('T')[1].split('.')[0] if 'T' in ts else ts

    # Format data
    data_str = ''
    if data:
        # Prioritize certain fields
        if 'i' in data and 'total' in data:
            pct = data['i'] / data['total'] * 100
            data_str = f" [{data['i']}/{data['total']} {pct:.0f}%]"
            if 'file' in data:
                fname = data['file']
                if len(fname) > 30:
                    fname = '...' + fname[-27:]
                data_str += f" {fname}"
            if 'eta_sec' in data:
                data_str += f" ETA: {format_eta(data['eta_sec'])}"
        elif 'added' in data or 'removed' in data:
            parts = []
            if 'added' in data:
                parts.append(f"added={data['added']}")
            if 'skipped' in data:
                parts.append(f"skipped={data['skipped']}")
            if 'removed' in data:
                parts.append(f"removed={data['removed']}")
            if 'duration_sec' in data:
                parts.append(f"in {format_duration(data['duration_sec'])}")
            data_str = f" ({', '.join(parts)})"

    print(f"{ts} {level_color}[{cat}]{reset} {msg}{data_str}")


def main():
    parser = argparse.ArgumentParser(
        description='Check status of RLAMA operations',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('--recent', '-r', action='store_true',
        help='Show recent completed operations')
    parser.add_argument('--follow', '-f', action='store_true',
        help='Follow log file (like tail -f)')
    parser.add_argument('--all', '-a', action='store_true',
        help='Show both active and recent operations')
    parser.add_argument('--limit', '-n', type=int, default=10,
        help='Limit number of recent operations (default: 10)')
    parser.add_argument('--json', action='store_true',
        help='Output raw JSON')

    args = parser.parse_args()

    if args.follow:
        follow_log()
        return

    state = load_operations_state()

    if args.json:
        print(json.dumps(state, indent=2))
        return

    print()
    print("RLAMA Status")
    print("=" * 60)

    show_active = not args.recent or args.all
    show_recent = args.recent or args.all

    if show_active:
        print("\nActive Operations:")
        print("-" * 40)
        print_active_operations(state.get('active', {}))

    if show_recent:
        print("\nRecent Operations:")
        print("-" * 40)
        print_recent_operations(state.get('recent', []), args.limit)

    if not show_active and not show_recent:
        # Default: show active only
        print("\nActive Operations:")
        print("-" * 40)
        print_active_operations(state.get('active', {}))

    print(f"Log file: {LOG_FILE}")
    print(f"\nTip: tail -f {LOG_FILE} | jq -r '\"\\(.ts) [\\(.cat)] \\(.msg)\"'")


if __name__ == '__main__':
    main()
