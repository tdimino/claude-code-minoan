#!/usr/bin/env python3
"""PreCompact hook: summarize transcript via OpenRouter, save YAML handoff."""
import json, sys, os, datetime, pathlib, urllib.request, re


def main():
    # 1. Read hook input from stdin
    hook_input = json.loads(sys.stdin.read())
    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", os.getcwd())
    trigger = hook_input.get("trigger") or hook_input.get("reason", "unknown")

    # 2. Read transcript JSONL
    if not transcript_path or not os.path.exists(transcript_path):
        return

    with open(transcript_path) as f:
        lines = f.readlines()

    # Take last 200 JSONL entries (most recent context)
    recent = lines[-200:]
    transcript_text = "\n".join(recent)

    # Truncate if over ~500K chars (~125K tokens) to stay within model context
    if len(transcript_text) > 500_000:
        transcript_text = transcript_text[-500_000:]

    # 3. Call OpenRouter — check env, then fall back to Aldea .env
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        for env_file in [
            pathlib.Path.home() / "Desktop/Aldea/Prompt development/Aldea-Soul-Engine/.env",
            pathlib.Path.home() / "Desktop/minoanmystery-astro/.env",
        ]:
            if env_file.exists():
                for line in env_file.read_text().splitlines():
                    if line.startswith("OPENROUTER_API_KEY="):
                        api_key = line.split("=", 1)[1].strip().strip('"').strip("'")
                        break
            if api_key:
                break
    if not api_key:
        return

    prompt = f"""Summarize this Claude Code session transcript into a YAML handoff document.

Output ONLY valid YAML with these fields:
- objective: What the user was trying to accomplish (1-3 sentences)
- completed: List of things that were done
- decisions: Key choices made and rationale
- blockers: Any unresolved issues (empty list if none)
- next_steps: What should happen next

Be concise. Each list item should be one line.

TRANSCRIPT:
{transcript_text}"""

    body = json.dumps({
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 1000,
        "temperature": 0.2,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/tdimino/claude-code-minoan",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        summary_yaml = result["choices"][0]["message"]["content"]
    except Exception:
        return

    # 4. Strip markdown code fences if present
    summary_yaml = summary_yaml.strip()
    if summary_yaml.startswith("```"):
        summary_yaml = "\n".join(summary_yaml.split("\n")[1:])
    if summary_yaml.endswith("```"):
        summary_yaml = "\n".join(summary_yaml.split("\n")[:-1])

    # 5. Write handoff file (one per session, overwrite on re-compact)
    handoff_dir = pathlib.Path.home() / ".claude" / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)

    session_short = session_id[:8]
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    project = os.path.basename(cwd)

    # Track handoff count (vitality marker — how many times this soul checkpointed)
    handoff_file = handoff_dir / f"{session_id}.yaml"
    handoff_count = 1
    if handoff_file.exists():
        for line in handoff_file.read_text().splitlines():
            m = re.match(r'^handoff_count:\s*(\d+)', line)
            if m:
                handoff_count = int(m.group(1)) + 1
                break

    header = (
        f'session_id: "{session_id}"\n'
        f'session_short: "{session_short}"\n'
        f'timestamp: "{timestamp}"\n'
        f'trigger: "{trigger}"\n'
        f'cwd: "{cwd}"\n'
        f'project: "{project}"\n'
        f'handoff_count: {handoff_count}\n\n'
    )

    with open(handoff_file, "w") as f:
        f.write(header + summary_yaml.strip() + "\n")

    print(f"Handoff saved: {handoff_file}", file=sys.stderr)

    # 6. Update INDEX.md — running log of all handoffs, most recent first
    update_index(handoff_dir, session_id, session_short, timestamp, trigger, cwd, project, summary_yaml)


def update_index(handoff_dir, session_id, session_short, timestamp, trigger, cwd, project, summary_yaml):
    """Prepend an entry to INDEX.md. Keep last 50 entries."""
    # Extract objective from the summary YAML (first line matching "objective:")
    objective = ""
    for line in summary_yaml.splitlines():
        m = re.match(r'^objective:\s*(.+)', line)
        if m:
            objective = m.group(1).strip().strip('"').strip("'")
            break

    # Truncate objective to ~120 chars for the table
    if len(objective) > 120:
        objective = objective[:117] + "..."

    index_file = handoff_dir / "INDEX.md"
    header = "# Session Handoffs\n\n| Date | Project | Session | Trigger | Directory | Summary |\n|------|---------|---------|---------|-----------|---------|"
    new_row = f"| {timestamp} | {project} | `{session_short}` | {trigger} | `{cwd}` | {objective} |"

    existing_rows = []
    if index_file.exists():
        for line in index_file.read_text().splitlines():
            if line.startswith("| ") and not line.startswith("| Date") and not line.startswith("|---"):
                existing_rows.append(line)

    # Deduplicate: remove prior entry for same session (Stop overwrites on re-fire)
    existing_rows = [r for r in existing_rows if f"`{session_short}`" not in r]

    # Prepend new entry, keep last 50
    all_rows = [new_row] + existing_rows
    all_rows = all_rows[:50]

    index_file.write_text(header + "\n" + "\n".join(all_rows) + "\n")
    print(f"Index updated: {index_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
