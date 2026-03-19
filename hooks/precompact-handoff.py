#!/usr/bin/env python3
"""PreCompact hook: summarize transcript via OpenRouter, save YAML handoff.

Upgraded for 1M token context (Opus 4.6):
- Filters noise types (progress, file-history-snapshot, queue-operation, etc.)
- Truncates oversized tool results to preserve semantic signal
- Adaptive routing: single-pass for <800K tokens, map-reduce for larger
- Model: Qwen Plus 0728 (1M context, $0.26/M input)
- Correct token estimation at 3.2 chars/token (not 4.0)
"""
import json, sys, os, datetime, pathlib, urllib.request, re
from concurrent.futures import ThreadPoolExecutor

# --- Constants ---
NOISE_TYPES = {
    "progress", "file-history-snapshot", "queue-operation",
    "custom-title", "agent-name", "last-prompt",
}
CHARS_PER_TOKEN = 3.2
MAX_SINGLE_PASS_TOKENS = 800_000
CHUNK_MAX_CHARS = 640_000  # ~200K tokens per chunk
MODEL = "qwen/qwen-plus-2025-07-28"
MAX_OUTPUT_TOKENS = 2000
TOOL_RESULT_MAX_CHARS = 500
TOOL_RESULT_HALF = 250


# --- Filtering ---

def truncate_tool_content(content):
    """Truncate a tool_result content string if over limit."""
    if not isinstance(content, str) or len(content) <= TOOL_RESULT_MAX_CHARS:
        return content
    return content[:TOOL_RESULT_HALF] + "\n...[truncated]...\n" + content[-TOOL_RESULT_HALF:]


def filter_transcript(lines):
    """Filter noise types and truncate oversized tool results.

    Returns list of filtered JSONL strings (each ending with newline).
    """
    filtered = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        entry_type = entry.get("type", "")
        if entry_type in NOISE_TYPES:
            continue

        # Truncate tool_result content within user entries
        if entry_type == "user":
            data = entry.get("data", entry.get("message", {}))
            content = data.get("content") if isinstance(data, dict) else None
            if isinstance(content, list):
                modified = False
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "tool_result":
                        block_content = block.get("content", "")
                        if isinstance(block_content, str) and len(block_content) > TOOL_RESULT_MAX_CHARS:
                            block["content"] = truncate_tool_content(block_content)
                            modified = True
                        # Handle nested content arrays (content blocks within tool_result)
                        elif isinstance(block_content, list):
                            for sub in block_content:
                                if isinstance(sub, dict):
                                    text_val = sub.get("text")
                                    if isinstance(text_val, str) and len(text_val) > TOOL_RESULT_MAX_CHARS:
                                        sub["text"] = truncate_tool_content(text_val)
                                        modified = True
                if modified:
                    filtered.append(json.dumps(entry) + "\n")
                    continue

        filtered.append(line + "\n")
    return filtered


# --- Token estimation ---

def estimate_tokens(text):
    """Estimate token count from character count using JSONL-appropriate ratio."""
    return int(len(text) / CHARS_PER_TOKEN)


# --- Chunking ---

def chunk_transcript(filtered_lines, max_chars=CHUNK_MAX_CHARS):
    """Split filtered lines into chunks at user-turn boundaries.

    Splits at entries where type=="user" and content is a string
    (indicating a new user message, not a tool_result array).
    """
    chunks = []
    current_chunk = []
    current_chars = 0

    for line in filtered_lines:
        line_len = len(line)

        # Check if we're over budget
        if current_chars + line_len > max_chars and current_chunk:
            split = False
            # Prefer splitting at user-turn boundaries
            try:
                entry = json.loads(line)
                entry_type = entry.get("type", "")
                if entry_type == "user":
                    data = entry.get("data", entry.get("message", {}))
                    content = data.get("content") if isinstance(data, dict) else None
                    if isinstance(content, str):
                        split = True
            except (json.JSONDecodeError, ValueError):
                pass

            # Hard-split fallback: if chunk is 2x over budget, force flush
            if not split and current_chars > max_chars:
                split = True

            if split:
                chunks.append("".join(current_chunk))
                current_chunk = []
                current_chars = 0

        current_chunk.append(line)
        current_chars += line_len

    # Final chunk
    if current_chunk:
        chunks.append("".join(current_chunk))

    return chunks


# --- OpenRouter API ---

def get_api_key():
    """Resolve OpenRouter API key from env or .env files."""
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
    return api_key


def call_openrouter(prompt, api_key, max_tokens=MAX_OUTPUT_TOKENS):
    """Send a prompt to OpenRouter and return the response content."""
    body = json.dumps({
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
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
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read())
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"OpenRouter call failed: {e}", file=sys.stderr)
        return ""


# --- Prompts ---

SINGLE_PASS_PROMPT = """Summarize this Claude Code session transcript into a YAML handoff document.

Output ONLY valid YAML with these fields:
- objective: What the user was trying to accomplish (1-3 sentences)
- completed: List of things that were done
- decisions: Key choices made and rationale
- blockers: Any unresolved issues (empty list if none)
- next_steps: What should happen next

Be concise. Each list item should be one line.

TRANSCRIPT:
{transcript}"""

MAP_PROMPT = """Summarize this section (part {idx}/{total}) of a Claude Code session transcript into a YAML handoff document.

Output ONLY valid YAML with these fields:
- objective: What the user was trying to accomplish in this section (1-3 sentences)
- completed: List of things that were done in this section
- decisions: Key choices made and rationale
- blockers: Any unresolved issues (empty list if none)
- next_steps: What should happen next based on this section

Be concise. Each list item should be one line.

TRANSCRIPT SECTION {idx}/{total}:
{transcript}"""

REDUCE_PROMPT = """You are given {count} partial summaries from different sections of a single Claude Code session.
Merge them into ONE coherent YAML handoff document that captures the full session arc.

Output ONLY valid YAML with these fields:
- objective: What the user was trying to accomplish overall (1-3 sentences, synthesized from all sections)
- completed: Deduplicated list of everything that was done (merge across sections)
- decisions: Key choices made and rationale (deduplicate)
- blockers: Any unresolved issues at the end of the session (empty list if none)
- next_steps: What should happen next (based on the final state)

Be concise. Each list item should be one line.

PARTIAL SUMMARIES:
{summaries}"""


# --- Map-reduce ---

def summarize_chunk(chunk_text, api_key, idx, total):
    """Map phase: summarize a single chunk."""
    prompt = MAP_PROMPT.format(idx=idx, total=total, transcript=chunk_text)
    return call_openrouter(prompt, api_key)


def reduce_summaries(summaries, api_key):
    """Reduce phase: merge chunk summaries into final YAML."""
    combined = "\n\n---\n\n".join(
        f"## Section {i+1}\n{s}" for i, s in enumerate(summaries)
    )
    prompt = REDUCE_PROMPT.format(count=len(summaries), summaries=combined)
    return call_openrouter(prompt, api_key)


# --- YAML cleanup ---

def strip_fences(text):
    """Remove markdown code fences if present."""
    text = text.strip()
    # Try to extract content from a fenced block
    m = re.search(r'```(?:yaml)?\s*\n([\s\S]*?)(?:\n```|$)', text)
    if m:
        return m.group(1).strip()
    # Fallback: simple strip
    if text.startswith("```"):
        text = "\n".join(text.split("\n")[1:])
    if text.endswith("```"):
        text = "\n".join(text.split("\n")[:-1])
    return text.strip()


# --- Index update ---

def update_index(handoff_dir, session_id, session_short, timestamp, trigger, cwd, project, summary_yaml):
    """Prepend an entry to INDEX.md. Keep last 50 entries."""
    objective = ""
    for line in summary_yaml.splitlines():
        m = re.match(r'^objective:\s*(.+)', line)
        if m:
            objective = m.group(1).strip().strip('"').strip("'")
            break

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

    # Deduplicate: remove prior entry for same session
    existing_rows = [r for r in existing_rows if f"`{session_short}`" not in r]

    all_rows = [new_row] + existing_rows
    all_rows = all_rows[:50]

    index_file.write_text(header + "\n" + "\n".join(all_rows) + "\n")
    print(f"Index updated: {index_file}", file=sys.stderr)


# --- Main ---

def main():
    # 1. Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, EOFError):
        return
    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")
    cwd = hook_input.get("cwd", os.getcwd())
    trigger = hook_input.get("trigger") or hook_input.get("reason", "unknown")

    # 2. Read full transcript
    if not transcript_path or not os.path.exists(transcript_path):
        return

    with open(transcript_path, errors="replace") as f:
        lines = f.readlines()

    # 3. Filter
    filtered = filter_transcript(lines)
    if not filtered:
        # Fallback: unfiltered last 200 lines (original behavior)
        filtered = lines[-200:]

    transcript_text = "".join(filtered)

    # 4. Dry-run mode
    if "--dry-run" in sys.argv:
        est = estimate_tokens(transcript_text)
        route = "single-pass" if est < MAX_SINGLE_PASS_TOKENS else "map-reduce"
        if route == "map-reduce":
            chunks = chunk_transcript(filtered)
            chunk_info = f"{len(chunks)} chunks @ ~{CHUNK_MAX_CHARS:,} chars"
        else:
            chunk_info = "1 chunk"
        print(f"Lines read: {len(lines)}", file=sys.stderr)
        print(f"Lines after filter: {len(filtered)}", file=sys.stderr)
        print(f"Chars: {len(transcript_text):,}", file=sys.stderr)
        print(f"Estimated tokens: {est:,}", file=sys.stderr)
        print(f"Route: {route} ({chunk_info})", file=sys.stderr)
        print(f"Model: {MODEL}", file=sys.stderr)
        return

    # 5. Get API key
    api_key = get_api_key()
    if not api_key:
        return

    # 6. Route: single-pass or map-reduce
    est_tokens = estimate_tokens(transcript_text)

    if est_tokens < MAX_SINGLE_PASS_TOKENS:
        # Single-pass
        prompt = SINGLE_PASS_PROMPT.format(transcript=transcript_text)
        summary_yaml = call_openrouter(prompt, api_key)
    else:
        # Map-reduce
        chunks = chunk_transcript(filtered)
        print(f"Map-reduce: {len(chunks)} chunks, ~{est_tokens:,} tokens", file=sys.stderr)

        with ThreadPoolExecutor(max_workers=3) as pool:
            futures = [
                pool.submit(summarize_chunk, c, api_key, i + 1, len(chunks))
                for i, c in enumerate(chunks)
            ]
            summaries = [f.result() for f in futures]

        # Drop empty results (failed API calls)
        summaries = [s for s in summaries if s.strip()]

        if not summaries:
            return  # Total failure — silent exit

        if len(summaries) == 1:
            # Only one chunk succeeded, use it directly
            summary_yaml = summaries[0]
        else:
            summary_yaml = reduce_summaries(summaries, api_key)

    if not summary_yaml:
        return

    # 7. Strip markdown code fences
    summary_yaml = strip_fences(summary_yaml)

    # 8. Write handoff file
    handoff_dir = pathlib.Path.home() / ".claude" / "handoffs"
    handoff_dir.mkdir(parents=True, exist_ok=True)

    session_short = session_id[:8]
    timestamp = datetime.datetime.now().isoformat(timespec="seconds")
    project = os.path.basename(cwd)

    # Track handoff count (vitality marker)
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

    # 9. Update INDEX.md
    update_index(handoff_dir, session_id, session_short, timestamp, trigger, cwd, project, summary_yaml)


if __name__ == "__main__":
    main()
