#!/usr/bin/env python3
"""Stop hook subprocess: infer session tags + summary from transcript via local llama-server.

Reads last 100 JSONL lines, calls Qwen 2.5 7B (llama-server on port 8787) to extract
topic tags and a 2-4 sentence summary. Writes to ~/.claude/session-tags/{session_id}.json,
updates session-registry.json (our self-maintained session index), and updates
the soul-session registry with topic + summary.

Requires: com.minoan.llama-tags-server launchd daemon running on 127.0.0.1:8787.
"""
import datetime
import fcntl
import json
import os
import pathlib
import subprocess
import sys
import urllib.request


TAGS_DIR = pathlib.Path.home() / ".claude" / "session-tags"
REGISTRY_PATH = pathlib.Path.home() / ".claude" / "session-registry.json"
TAGS_COOLDOWN = 180  # 3 minutes — matches old stop-handoff.py gate
LLAMA_SERVER_URL = "http://127.0.0.1:8787/v1/chat/completions"

# --- Prompt Configurations (switchable) ---

# Qwen 2.5 7B local: system/user split, explicit JSON schema, negative constraints
# Known bug: QwenLM/Qwen2.5 #1095 (mid-generation JSON corruption)
# Mitigated by: response_format json_object + temperature 0.0 + top_k 1
QWEN_LOCAL_SYSTEM_PROMPT = """\
You are a session title generator. Output ONLY valid JSON, nothing else.

RULES:
- The title MUST describe what the USER was trying to accomplish
- The title MUST be 5-8 words, plain English
- DO NOT mention internal operations: hooks, tags, stop events, session management, subagents, registry, JSONL, transcript
- DO NOT mention tools or infrastructure: Next.js, Tailwind, exa, firecrawl, MCP, llama-server, webpack, workspace
- Focus on the USER'S GOAL, not Claude's implementation steps

Required JSON schema:
{
  "tags": ["string", "..."],        // up to 10 topic tags, 4-5 words each
  "display_tags": ["string", "..."], // exactly 3 most relevant tags, 3-5 words
  "title": "string",                // 5-8 word user-focused session title
  "summary": "string"               // 2-4 sentence summary of what the user accomplished
}"""

QWEN_LOCAL_USER_TEMPLATE = """\
Generate a title, tags, and summary for this Claude Code conversation.
The transcript below contains the user's messages. Focus on what the user wanted to do.

BAD titles (too internal): "Session Tags and Stop Hook", "Next.js Workspace Configuration", "Hook Architecture Refactor"
GOOD titles (user-focused): "Optimum Router Bridge Mode Setup", "Fix Dead Session Index File", "Sync Hooks to Both Repos"

Example output:
{{"tags": ["router setup", "bridge mode config", "session tags fix"], "display_tags": ["router bridge mode setup", "session registry migration", "repo hooks sync"], "title": "Router Setup and Session Registry Fix", "summary": "Configured Optimum gateway in bridge mode with GL.iNet Flint 2 router. Diagnosed and replaced dead sessions-index.json with self-maintained session-registry.json."}}

TRANSCRIPT:
{transcript}"""

# Cloud model (Google/OpenRouter): single-prompt, higher temperature tolerance
CLOUD_PROMPT_TEMPLATE = """\
Analyze this Claude Code session transcript and extract topic tags and a summary.

Output ONLY valid JSON with these fields:
- "tags": array of up to 10 topic tags (4-5 words each) describing what this session covers
- "display_tags": array of exactly 3 most relevant tags (3-5 words each, descriptive and specific)
- "title": a short descriptive title for this session (5-8 words, no quotes)
- "summary": a 2-4 sentence summary of what happened in this session (what was built, fixed, or discussed)

Example output:
{{"tags": ["statusline tags feature", "ccstatusline hook design", "plan rename fix"], "display_tags": ["statusline session tags display", "plan rename on creation", "stop hook architecture"], "title": "Session Tags and Plan Rename", "summary": "Extended the statusline with session tag display. Fixed plan rename hook to trigger on file creation. Refactored stop hook to use fire-and-forget pattern for tag inference."}}

TRANSCRIPT:
{transcript}"""

# Active configuration: "local" (Qwen 2.5 7B via llama-server) or "cloud" (OpenRouter)
ACTIVE_PROVIDER = "local"


def read_transcript_tail(transcript_path, max_lines=100):
    """Read last N lines from JSONL transcript."""
    try:
        with open(transcript_path) as f:
            lines = f.readlines()
        return "\n".join(lines[-max_lines:])
    except (OSError, UnicodeDecodeError):
        return ""


def read_clean_conversation(transcript_path):
    """Extract real user messages from JSONL transcript using structural filtering.

    Identifies genuine user input by checking for `type == "user"` AND
    `permissionMode` present — this combination uniquely marks actual user
    prompts vs tool results, skill injections, and system messages.

    Returns a clean text of USER: lines suitable for LLM title inference.
    """
    try:
        with open(transcript_path) as f:
            lines = f.readlines()
    except (OSError, UnicodeDecodeError):
        return ""

    user_msgs = []
    for line in lines:
        try:
            obj = json.loads(line)
        except (json.JSONDecodeError, ValueError):
            continue

        # Structural filter: only real user prompts have both fields
        if obj.get("type") != "user" or "permissionMode" not in obj:
            continue

        message = obj.get("message", {})
        content = message.get("content", "")

        # Real user input has string content
        if not isinstance(content, str):
            continue

        text = content.strip()
        if len(text) < 10:
            continue

        # Skip system noise that occasionally appears in user messages
        if text.startswith(("<task-notification", "<local-command")):
            continue

        user_msgs.append(text[:200])

    clean_lines = [f"USER: {msg}" for msg in user_msgs]
    clean_text = "\n".join(clean_lines)

    # Truncate to ~5K chars to leave room for prompt template + output
    if len(clean_text) > 5000:
        clean_text = clean_text[:5000]
        nl = clean_text.rfind("\n")
        if nl > 0:
            clean_text = clean_text[:nl]

    return clean_text


def extract_json(text):
    """Robustly extract JSON object from LLM output (handles code fences, whitespace)."""
    text = text.strip()
    start = text.find("{")
    end = text.rfind("}") + 1
    if start < 0 or end <= start:
        raise ValueError(f"No JSON object found in: {text[:100]}")
    return json.loads(text[start:end])


def infer_tags(transcript_text):
    """Call local llama-server (Qwen 2.5 7B) to extract tags from transcript.

    Uses ACTIVE_PROVIDER to select prompt format and sampling params.
    Switchable between 'local' (Qwen 2.5 7B) and 'cloud' (OpenRouter).
    """
    if ACTIVE_PROVIDER == "local":
        messages = [
            {"role": "system", "content": QWEN_LOCAL_SYSTEM_PROMPT},
            {"role": "user", "content": QWEN_LOCAL_USER_TEMPLATE.format(transcript=transcript_text)},
        ]
        body = json.dumps({
            "messages": messages,
            "temperature": 0.0,
            "top_k": 1,
            "max_tokens": 500,
            "stream": False,
            "response_format": {"type": "json_object"},
        }).encode()
    else:
        # Cloud provider (OpenRouter) — single-prompt, higher temperature tolerance
        messages = [
            {"role": "user", "content": CLOUD_PROMPT_TEMPLATE.format(transcript=transcript_text)},
        ]
        body = json.dumps({
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": 500,
            "stream": False,
        }).encode()

    req = urllib.request.Request(
        LLAMA_SERVER_URL,
        data=body,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())

    content = result["choices"][0]["message"]["content"]
    return extract_json(content)


def update_registry(session_id, transcript_path, title, tags, display_tags, summary):
    """Upsert session entry in session-registry.json. Uses file locking."""
    lock_path = pathlib.Path("/tmp") / f"claude-{os.getuid()}" / "session-registry.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        lock_fd = open(lock_path, "w")
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except (OSError, BlockingIOError):
        return  # Another process holds the lock — skip

    try:
        registry = {"sessions": {}}
        if REGISTRY_PATH.exists():
            try:
                registry = json.loads(REGISTRY_PATH.read_text())
            except (json.JSONDecodeError, OSError):
                registry = {"sessions": {}}

        project_slug = pathlib.Path(transcript_path).parent.name

        # Upsert: preserve existing fields, update with new data
        existing = registry.get("sessions", {}).get(session_id, {})
        registry.setdefault("sessions", {})[session_id] = {
            "title": title or existing.get("title", ""),
            "display_tags": display_tags or existing.get("display_tags", []),
            "tags": tags or existing.get("tags", []),
            "summary": summary or existing.get("summary", ""),
            "project": project_slug,
            "updated": datetime.datetime.now().isoformat(timespec="seconds"),
        }

        # Atomic write
        tmp = REGISTRY_PATH.with_suffix(".tmp")
        tmp.write_text(json.dumps(registry, indent=2))
        tmp.rename(REGISTRY_PATH)
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

    # Check for pending title from plan-session-rename.py BEFORE inference.
    # These breadcrumbs are local-only and don't need an LLM call.
    pending_path = TAGS_DIR / f"{session_id}.pending-title"
    if pending_path.exists():
        try:
            pending_title = pending_path.read_text().strip()
            if pending_title:
                update_registry(session_id, transcript_path, pending_title, [], [], "")
                pending_path.unlink(missing_ok=True)
                print(f"session-tags: applied pending plan title '{pending_title}'", file=sys.stderr)
        except OSError:
            pass

    # Cooldown check — don't call llama-server more than once per TAGS_COOLDOWN seconds.
    cooldown_dir = pathlib.Path(f"/tmp/claude-{os.getuid()}")
    cooldown_dir.mkdir(parents=True, exist_ok=True)
    cooldown_file = cooldown_dir / f"session-tags-{session_id}.last"
    now = datetime.datetime.now().timestamp()
    if cooldown_file.exists():
        try:
            last_run = float(cooldown_file.read_text().strip())
            if now - last_run < TAGS_COOLDOWN:
                return  # Too soon — skip this run
        except (ValueError, OSError):
            pass  # Corrupted file — proceed

    # Use clean conversation extraction (user messages only) for local inference.
    # Falls back to raw tail if clean extraction returns empty.
    transcript_text = read_clean_conversation(transcript_path)
    if not transcript_text:
        transcript_text = read_transcript_tail(transcript_path)
    if not transcript_text:
        return

    # Truncate if over 6K chars (~3K tokens), align to line boundary.
    # llama-server runs with -c 8192; improved prompts use more tokens,
    # so we budget ~3K for transcript, ~2K for prompt template, ~1K for output.
    if len(transcript_text) > 6_000:
        transcript_text = transcript_text[-6_000:]
        nl = transcript_text.find("\n")
        if nl > 0:
            transcript_text = transcript_text[nl + 1:]

    try:
        result = infer_tags(transcript_text)
    except Exception as e:
        print(f"session-tags: inference error: {e}", file=sys.stderr)
        return

    # Write cooldown timestamp AFTER successful inference (not before)
    # so failed calls don't block retries for 3 minutes.
    try:
        cooldown_file.write_text(str(now))
    except OSError:
        pass

    tags = result.get("tags", [])[:10]
    display_tags = result.get("display_tags", tags[:3])[:3]
    title = result.get("title", "")
    summary = result.get("summary", "")

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
        "summary": summary,
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

    # Update session-registry.json with title, tags, summary
    update_registry(session_id, transcript_path, title, tags, display_tags, summary)

    # Update soul registry topic + summary if this session is registered
    if title or summary:
        cmd = ["python3", str(pathlib.Path.home() / ".claude/hooks/soul-registry.py"),
               "heartbeat", session_id]
        if title:
            cmd += ["--topic", title]
        if summary:
            cmd += ["--summary", summary]
        try:
            subprocess.run(cmd, timeout=5, capture_output=True)
        except Exception:
            pass  # Non-critical


if __name__ == "__main__":
    main()
