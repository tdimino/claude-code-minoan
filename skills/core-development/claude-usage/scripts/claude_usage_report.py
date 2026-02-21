#!/usr/bin/env python3
"""
Claude Usage Report — PDF generator.

Produces a dark editorial PDF report from claude_usage.py JSON output.
Designed for executive sharing: CTO-ready, data-rich, visually distinctive.

Usage:
    # Generate today's report
    python3 claude_usage_report.py

    # Last 30 days
    python3 claude_usage_report.py --since 30d

    # Custom range with project filter
    python3 claude_usage_report.py --since 2026-02-01 --until 2026-02-28 --project Thera

    # Custom output path
    python3 claude_usage_report.py --since 30d -o ~/Desktop/february-usage.pdf

Requires: weasyprint (pip install weasyprint)
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
USAGE_SCRIPT = SCRIPT_DIR / "claude_usage.py"


def get_usage_data(args):
    """Run claude_usage.py --json and return parsed data."""
    cmd = [sys.executable, str(USAGE_SCRIPT), "--json"]
    if args.since:
        cmd += ["--since", args.since]
    if args.until:
        cmd += ["--until", args.until]
    if args.project:
        cmd += ["--project", args.project]
    if args.tz:
        cmd += ["--tz", args.tz]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running claude_usage.py: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    return json.loads(result.stdout)


def fmt_tokens(n):
    """Format token count for display."""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n / 1_000:.0f}K"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)


def fmt_cost(c):
    """Format USD cost."""
    if c >= 1000:
        return f"${c:,.0f}"
    return f"${c:,.2f}"


def fmt_date_short(d):
    """Format date string for compact display."""
    try:
        dt = datetime.strptime(d, "%Y-%m-%d")
        return dt.strftime("%b %d")
    except ValueError:
        return d


def build_html(data, name=None):
    """Build the full HTML report."""
    gt = data["grand_total"]
    groups = data["groups"]
    meta = data["metadata"]
    by = data["by"]

    # Compute date range label
    since_raw = meta.get("since", "")
    until_raw = meta.get("until", "")
    try:
        since_dt = datetime.fromisoformat(since_raw)
        until_dt = datetime.fromisoformat(until_raw)
        date_range = f"{since_dt.strftime('%B %d')} – {until_dt.strftime('%B %d, %Y')}"
    except (ValueError, TypeError):
        date_range = f"{since_raw} – {until_raw}"

    generated = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    # Find max cost for bar chart scaling
    max_cost = max((g["cost"] for g in groups.values()), default=1)

    # Compute model-level summary if we have "by day" data
    # We'll show the top-level metrics regardless
    total_tokens = gt["total_tokens"]
    total_cost = gt["cost"]
    total_entries = gt["entries"]
    total_input = gt["input_tokens"]
    total_output = gt["output_tokens"]
    total_cache_w = gt["cache_creation_input_tokens"]
    total_cache_r = gt["cache_read_input_tokens"]

    num_days = len(groups)
    avg_daily = total_cost / num_days if num_days > 0 else 0

    # Build bar chart rows
    bar_rows = ""
    for key, g in groups.items():
        label = fmt_date_short(key) if by == "day" else key
        cost = g["cost"]
        pct = (cost / max_cost * 100) if max_cost > 0 else 0
        bar_rows += f"""
        <div class="bar-row">
            <span class="bar-label">{label}</span>
            <div class="bar-track">
                <div class="bar-fill" style="width: {pct:.1f}%"></div>
            </div>
            <span class="bar-value">{fmt_cost(cost)}</span>
        </div>"""

    # Build detail table rows
    table_rows = ""
    for key, g in groups.items():
        label = fmt_date_short(key) if by == "day" else key
        table_rows += f"""
        <tr>
            <td class="cell-label">{label}</td>
            <td class="cell-num">{fmt_tokens(g['input_tokens'])}</td>
            <td class="cell-num">{fmt_tokens(g['output_tokens'])}</td>
            <td class="cell-num">{fmt_tokens(g['cache_creation_input_tokens'])}</td>
            <td class="cell-num">{fmt_tokens(g['cache_read_input_tokens'])}</td>
            <td class="cell-num cell-total">{fmt_tokens(g['total_tokens'])}</td>
            <td class="cell-num cell-cost">{fmt_cost(g['cost'])}</td>
        </tr>"""

    # Name line
    name_line = f'<div class="header-name">{name}</div>' if name else ""

    # Project filter note
    project_note = ""
    if meta.get("project_filter"):
        project_note = f'<div class="filter-badge">Filtered: {meta["project_filter"]}</div>'

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Claude Usage Report</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:wght@300;400;600;700&family=JetBrains+Mono:wght@300;400;500;600&family=Inter:wght@300;400;500;600;700&display=swap');

@page {{
    size: letter;
    margin: 24px 48px;
}}

@page :first {{
    margin-top: 0;
}}

* {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}}

:root {{
    --bg-deep: #08080d;
    --bg-surface: #0f1017;
    --bg-elevated: #161822;
    --bg-card: #1a1c2a;
    --border: #252840;
    --border-subtle: #1c1e30;
    --gold: #c9a855;
    --gold-light: #dfc07a;
    --gold-dim: #8a7338;
    --gold-glow: rgba(201, 168, 85, 0.22);
    --accent-steel: #4a7b9d;
    --text-primary: #e8e6e1;
    --text-secondary: #9895a0;
    --text-tertiary: #5d5a66;
    --accent-green: #4ade80;
    --accent-red: #f87171;
    --accent-blue: #60a5fa;
}}

body {{
    font-family: 'Crimson Pro', serif;
    background: var(--bg-deep);
    color: var(--text-primary);
    line-height: 1.5;
    border-left: 2px solid var(--gold-dim);
}}

/* ─── HEADER ─── */

.header {{
    padding: 48px 56px 40px;
    background: linear-gradient(175deg, #0e101a 0%, var(--bg-deep) 60%);
    border-bottom: 1px solid var(--border);
    position: relative;
    overflow: hidden;
}}

.header::before {{
    content: '';
    position: absolute;
    top: -20px;
    right: 40px;
    width: 200px;
    height: 200px;
    background: radial-gradient(circle, var(--gold-glow) 0%, rgba(201, 168, 85, 0.08) 40%, transparent 70%);
    pointer-events: none;
}}

.header-eyebrow {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--gold);
    margin-bottom: 12px;
}}

.header-title {{
    font-family: 'Crimson Pro', serif;
    font-size: 52px;
    font-weight: 300;
    letter-spacing: -1px;
    line-height: 1.05;
    color: var(--text-primary);
    margin-bottom: 12px;
}}

.header-name {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 1px;
    color: var(--gold-light);
    margin-bottom: 4px;
}}

.header-range {{
    font-family: 'Inter', sans-serif;
    font-size: 15px;
    font-weight: 400;
    color: var(--text-secondary);
}}

.filter-badge {{
    display: inline-block;
    margin-top: 10px;
    padding: 4px 12px;
    background: var(--gold-glow);
    border: 1px solid var(--gold-dim);
    border-radius: 4px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
    color: var(--gold);
}}

/* ─── METRICS STRIP ─── */

.metrics {{
    display: flex;
    padding: 32px 40px;
    gap: 0;
    border-bottom: 1px solid var(--border);
    background: var(--bg-surface);
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.3);
}}

.metric {{
    flex: 1;
    position: relative;
    padding: 0 16px;
}}

.metric:first-child {{
    padding-left: 0;
}}

.metric:not(:last-child)::after {{
    content: '';
    position: absolute;
    right: 0;
    top: 4px;
    bottom: 4px;
    width: 1px;
    background: var(--border);
}}

.metric-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 30px;
    font-weight: 600;
    color: var(--text-primary);
    letter-spacing: -1.5px;
    line-height: 1.2;
}}

.metric-value.gold {{
    color: var(--gold);
}}

.metric-label {{
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-tertiary);
    margin-top: 4px;
}}

/* ─── BAR CHART ─── */

.chart-section {{
    padding: 36px 56px;
    border-bottom: 1px solid var(--border);
    page-break-inside: auto;
}}

.section-title {{
    font-family: 'Crimson Pro', serif;
    font-size: 22px;
    font-weight: 400;
    color: var(--text-primary);
    margin-bottom: 24px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border-subtle);
    page-break-after: avoid;
}}

.bar-row {{
    display: flex;
    align-items: center;
    height: 26px;
    margin-bottom: 4px;
}}

.bar-label {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 400;
    color: var(--text-secondary);
    width: 60px;
    flex-shrink: 0;
    text-align: right;
    padding-right: 12px;
}}

.bar-track {{
    flex: 1;
    height: 16px;
    background: var(--bg-elevated);
    border-radius: 2px;
    overflow: hidden;
    position: relative;
}}

.bar-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--gold-dim) 0%, var(--gold) 100%);
    border-radius: 2px;
    min-width: 2px;
}}

.bar-value {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    font-weight: 500;
    color: var(--text-secondary);
    width: 64px;
    flex-shrink: 0;
    text-align: right;
    padding-left: 10px;
}}

/* ─── DATA TABLE ─── */

.table-section {{
    padding: 36px 56px;
    page-break-inside: auto;
}}

table {{
    width: 100%;
    border-collapse: collapse;
    font-family: 'JetBrains Mono', monospace;
    font-size: 11px;
}}

thead th {{
    font-family: 'Inter', sans-serif;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--text-tertiary);
    text-align: right;
    padding: 0 8px 10px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}}

thead th:first-child {{
    text-align: left;
    padding-left: 0;
}}

tbody tr {{
    border-bottom: 1px solid var(--border-subtle);
    page-break-inside: avoid;
}}

tbody tr:nth-child(odd) {{
    background: rgba(255, 255, 255, 0.015);
}}

thead {{
    display: table-header-group;
}}

tfoot {{
    display: table-footer-group;
}}

td {{
    padding: 7px 8px;
    color: var(--text-secondary);
    font-weight: 400;
}}

.cell-label {{
    text-align: left;
    padding-left: 0;
    color: var(--text-primary);
    font-weight: 500;
}}

.cell-num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
}}

.cell-total {{
    color: var(--text-primary);
    font-weight: 500;
}}

.cell-cost {{
    color: var(--gold);
    font-weight: 600;
}}

/* Total row */
tfoot td {{
    padding: 12px 8px 8px;
    border-top: 2px solid var(--border);
    font-weight: 600;
    color: var(--text-primary);
}}

tfoot .cell-cost {{
    color: var(--gold);
    font-size: 12px;
}}

/* ─── FOOTER ─── */

.footer {{
    padding: 24px 56px 72px;
    border-top: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
}}

.footer-left {{
    font-size: 10px;
    color: var(--text-tertiary);
    line-height: 1.6;
}}

.footer-right {{
    text-align: right;
}}

.footer-brand {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 9px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: var(--gold-dim);
}}

.footer-meta {{
    font-size: 9px;
    color: var(--text-tertiary);
    margin-top: 2px;
}}

/* ─── TOKEN COMPOSITION STRIP ─── */

.composition {{
    padding: 28px 56px;
    border-bottom: 1px solid var(--border);
    background: var(--bg-surface);
}}

.comp-bar {{
    display: flex;
    height: 28px;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 16px;
}}

.comp-segment {{
    height: 100%;
    position: relative;
    min-width: 2px;
}}

.comp-segment.input {{ background: var(--accent-blue); }}
.comp-segment.output {{ background: var(--accent-green); }}
.comp-segment.cache-w {{ background: var(--gold); }}
.comp-segment.cache-r {{ background: var(--accent-steel); }}

.comp-legend {{
    display: flex;
    gap: 24px;
}}

.comp-item {{
    display: flex;
    align-items: center;
    gap: 8px;
}}

.comp-dot {{
    width: 8px;
    height: 8px;
    border-radius: 2px;
    flex-shrink: 0;
}}

.comp-dot.input {{ background: var(--accent-blue); }}
.comp-dot.output {{ background: var(--accent-green); }}
.comp-dot.cache-w {{ background: var(--gold); }}
.comp-dot.cache-r {{ background: var(--accent-steel); }}

.comp-text {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 10px;
    color: var(--text-secondary);
}}

.comp-pct {{
    font-weight: 600;
    color: var(--text-primary);
}}
</style>
</head>
<body>

<!-- HEADER -->
<div class="header">
    <div class="header-eyebrow">Claude Code · Token Usage Report</div>
    <div class="header-title">Usage & Cost Analysis</div>
    {name_line}
    <div class="header-range">{date_range}</div>
    {project_note}
</div>

<!-- METRICS -->
<div class="metrics">
    <div class="metric">
        <div class="metric-value gold">{fmt_cost(total_cost)}</div>
        <div class="metric-label">Total Cost</div>
    </div>
    <div class="metric">
        <div class="metric-value">{fmt_tokens(total_tokens)}</div>
        <div class="metric-label">Total Tokens</div>
    </div>
    <div class="metric">
        <div class="metric-value">{fmt_cost(avg_daily)}</div>
        <div class="metric-label">Daily Average</div>
    </div>
    <div class="metric">
        <div class="metric-value">{total_entries:,}</div>
        <div class="metric-label">API Calls</div>
    </div>
    <div class="metric">
        <div class="metric-value">{meta['files_scanned']:,}</div>
        <div class="metric-label">Files Scanned</div>
    </div>
</div>

<!-- TOKEN COMPOSITION -->
<div class="composition">
    <div class="section-title">Token Composition</div>
    <div class="comp-bar">
        <div class="comp-segment input" style="width: {total_input / total_tokens * 100:.2f}%"></div>
        <div class="comp-segment output" style="width: {total_output / total_tokens * 100:.2f}%"></div>
        <div class="comp-segment cache-w" style="width: {total_cache_w / total_tokens * 100:.2f}%"></div>
        <div class="comp-segment cache-r" style="width: {total_cache_r / total_tokens * 100:.2f}%"></div>
    </div>
    <div class="comp-legend">
        <div class="comp-item">
            <div class="comp-dot input"></div>
            <span class="comp-text">Input <span class="comp-pct">{fmt_tokens(total_input)}</span> ({total_input / total_tokens * 100:.1f}%)</span>
        </div>
        <div class="comp-item">
            <div class="comp-dot output"></div>
            <span class="comp-text">Output <span class="comp-pct">{fmt_tokens(total_output)}</span> ({total_output / total_tokens * 100:.1f}%)</span>
        </div>
        <div class="comp-item">
            <div class="comp-dot cache-w"></div>
            <span class="comp-text">Cache Write <span class="comp-pct">{fmt_tokens(total_cache_w)}</span> ({total_cache_w / total_tokens * 100:.1f}%)</span>
        </div>
        <div class="comp-item">
            <div class="comp-dot cache-r"></div>
            <span class="comp-text">Cache Read <span class="comp-pct">{fmt_tokens(total_cache_r)}</span> ({total_cache_r / total_tokens * 100:.1f}%)</span>
        </div>
    </div>
</div>

<!-- BAR CHART -->
<div class="chart-section">
    <div class="section-title">Daily Cost Distribution</div>
    {bar_rows}
</div>

<!-- DATA TABLE -->
<div class="table-section">
    <div class="section-title">Detailed Breakdown</div>
    <table>
        <thead>
            <tr>
                <th>{by.capitalize()}</th>
                <th>Input</th>
                <th>Output</th>
                <th>Cache Write</th>
                <th>Cache Read</th>
                <th>Total</th>
                <th>Cost</th>
            </tr>
        </thead>
        <tbody>
            {table_rows}
        </tbody>
        <tfoot>
            <tr>
                <td class="cell-label">TOTAL</td>
                <td class="cell-num">{fmt_tokens(total_input)}</td>
                <td class="cell-num">{fmt_tokens(total_output)}</td>
                <td class="cell-num">{fmt_tokens(total_cache_w)}</td>
                <td class="cell-num">{fmt_tokens(total_cache_r)}</td>
                <td class="cell-num cell-total">{fmt_tokens(total_tokens)}</td>
                <td class="cell-num cell-cost">{fmt_cost(total_cost)}</td>
            </tr>
        </tfoot>
    </table>
</div>

<!-- FOOTER -->
<div class="footer">
    <div class="footer-left">
        {meta['parent_files']} parent sessions · {meta['subagent_files']} subagent sidechains<br>
        Timezone: {meta.get('timezone', 'EST')} · Source: ~/.claude/projects/ JSONL files
    </div>
    <div class="footer-right">
        <div class="footer-brand">claude-usage</div>
        <div class="footer-meta">Generated {generated}</div>
    </div>
</div>

</body>
</html>"""

    return html


def main():
    p = argparse.ArgumentParser(
        description="Generate a PDF usage report from Claude Code session data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  claude_usage_report.py                          Today's report
  claude_usage_report.py --since 30d              Last 30 days
  claude_usage_report.py --since 30d -o report.pdf  Custom output path
  claude_usage_report.py --since 7d --html        HTML only (no PDF)""",
    )
    p.add_argument("--since", help="Start date: YYYY-MM-DD or Nd (default: today)")
    p.add_argument("--until", help="End date: YYYY-MM-DD (default: now)")
    p.add_argument("--project", help="Filter to projects matching this string")
    p.add_argument("--tz", help="Timezone override")
    p.add_argument("--name", help="Your name for the report header (e.g. 'Tom di Mino')")
    p.add_argument("-o", "--output", help="Output PDF path (default: ~/Desktop/claude-usage-report.pdf)")
    p.add_argument("--html", action="store_true", help="Output HTML only, skip PDF conversion")
    args = p.parse_args()

    # Get data
    data = get_usage_data(args)

    if not data.get("groups"):
        print("No data found for the specified range.", file=sys.stderr)
        sys.exit(1)

    # Build HTML
    html = build_html(data, name=args.name)

    if args.html:
        if args.output:
            Path(args.output).write_text(html)
            print(f"HTML written to {args.output}")
        else:
            print(html)
        return

    # Generate PDF via weasyprint
    try:
        import weasyprint
    except ImportError:
        print("weasyprint not installed. Install with: pip install weasyprint", file=sys.stderr)
        print("Falling back to HTML output.", file=sys.stderr)
        out = args.output or os.path.expanduser("~/Desktop/claude-usage-report.html")
        Path(out).write_text(html)
        print(f"HTML written to {out}")
        return

    output_path = args.output or os.path.expanduser("~/Desktop/claude-usage-report.pdf")

    # Write HTML to temp file for weasyprint
    with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False) as f:
        f.write(html)
        tmp_html = f.name

    try:
        doc = weasyprint.HTML(filename=tmp_html)
        doc.write_pdf(output_path)
        print(f"PDF written to {output_path}")
    finally:
        os.unlink(tmp_html)


if __name__ == "__main__":
    main()
