#!/usr/bin/env python3
"""Stop hook subprocess: infer session tags from transcript via OpenRouter.

Reads last 100 JSONL lines, calls Gemini Flash Lite to extract topic tags,
writes to ~/.claude/session-tags/{session_id}.json. Also auto-sets customTitle
in sessions-index.json if none exists.
"""
import datetime
import fcntl
import json
import os
import pathlib
import sys
import urllib.request


TAGS_DIR = pathlib.Path.home() / ".claude" / "session-tags"


def get_api_key():
    """Resolve OpenRouter API key from env or .env files."""
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if key:
        return key
    for env_file in [
        pathlib.Path.home() / "Desktop/Aldea/Prompt development/Aldea-Soul-Engine/.env",
        pathlib.Path.home() / "Desktop/minoanmystery-astro/.env",
    ]:
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if line.startswith("OPENROUTER_API_KEY="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


def read_transcript_tail(transcript_path, max_lines=100):
    """Read last N lines from JSONL transcript."""
    try:
        with open(transcript_path) as f:
            lines = f.readlines()
        return "\n".join(lines[-max_lines:])
    except (OSError, UnicodeDecodeError):
        return ""


def extract_json(text):
    """Robustly extract JSON object from LLM output (handles code fences, whitespace)."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        raise ValueError(f"No JSON object found in: {text[:100]}")
    return json.loads(text[start:end])


def infer_tags(api_key, transcript_text):
    """Call OpenRouter to extract tags from transcript."""
    prompt = f"""Analyze this Claude Code session transcript and extract topic tags.

Output ONLY valid JSON with these fields:
- "tags": array of up to 10 topic tags (4-5 words each) describing what this session covers
- "display_tags": array of exactly 3 most relevant tags (3-5 words each, descriptive and specific)
- "title": a short descriptive title for this session (5-8 words, no quotes)

Example output:
{{"tags": ["statusline tags feature", "ccstatusline hook design", "plan rename fix"], "display_tags": ["statusline session tags display", "plan rename on creation", "stop hook architecture"], "title": "Session Tags and Plan Rename"}}

TRANSCRIPT:
{transcript_text}"""

    body = json.dumps({
        "model": "google/gemini-2.0-flash-lite-001",
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 500,
        "temperature": 0.2,
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/tdimino/claudius",
        },
    )

    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())

    content = result["choices"][0]["message"]["content"]
    return extract_json(content)


def auto_rename_session(session_id, transcript_path, title):
    """Set customTitle in sessions-index.json if none exists. Uses file locking."""
    if not title:
        return

    project_dir = pathlib.Path(transcript_path).parent
    index_path = project_dir / "sessions-index.json"

    if not index_path.exists():
        return

    # File lock to prevent race with propagate-rename.py and other hooks
    lock_path = pathlib.Path("/tmp") / f"claude-{os.getuid()}" / "sessions-index.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        lock_fd = open(lock_path, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        return  # Another process holds the lock — skip

    try:
        index_data = json.loads(index_path.read_text())

        for entry in index_data.get("entries", []):
            if entry.get("sessionId") == session_id:
                if entry.get("customTitle"):
                    return  # Already has a title—don't overwrite
                entry["customTitle"] = title
                break
        else:
            return  # Session not found

        # Atomic write
        tmp = index_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(index_data, indent=2))
        tmp.rename(index_path)
    except (json.JSONDecodeError, OSError):
        pass
    finally:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)
            lock_fd.close()
        except OSError:
            pass


def main():
    # Read hook input from stdin
    try:
        hook_input = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, OSError):
        return

    session_id = hook_input.get("session_id", "")
    transcript_path = hook_input.get("transcript_path", "")

    if not session_id or not transcript_path or not os.path.exists(transcript_path):
        return

    api_key = get_api_key()
    if not api_key:
        return

    transcript_text = read_transcript_tail(transcript_path)
    if not transcript_text:
        return

    # Truncate if over 200K chars (~50K tokens), align to line boundary
    if len(transcript_text) > 200_000:
        transcript_text = transcript_text[-200_000:]
        nl = transcript_text.find("\n")
        if nl > 0:
            transcript_text = transcript_text[nl + 1:]

    try:
        result = infer_tags(api_key, transcript_text)
    except Exception:
        return

    tags = result.get("tags", [])[:10]
    display_tags = result.get("display_tags", tags[:3])[:3]
    title = result.get("title", "")

    # Count turns (approximate: count user messages)
    try:
        with open(transcript_path) as f:
            turn_count = sum(1 for line in f if '"userType": "external"' in line)
    except OSError:
        turn_count = 0

    # Write sidecar JSON (atomic)
    TAGS_DIR.mkdir(parents=True, exist_ok=True)
    sidecar = {
        "session_id": session_id,
        "tags": tags,
        "display_tags": display_tags,
        "updated": datetime.datetime.now().isoformat(timespec="seconds"),
        "turn_count": turn_count,
    }

    sidecar_path = TAGS_DIR / f"{session_id}.json"
    tmp = sidecar_path.with_suffix(".tmp")
    try:
        tmp.write_text(json.dumps(sidecar, indent=2))
        tmp.rename(sidecar_path)
    except OSError:
        return

    print(f"session-tags: {len(tags)} tags, display: {display_tags}", file=sys.stderr)

    # Auto-rename session if no customTitle
    auto_rename_session(session_id, transcript_path, title)


if __name__ == "__main__":
    main()
