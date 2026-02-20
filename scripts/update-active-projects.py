#!/usr/bin/env python3
"""Auto-update ~/.claude/agent_docs/active-projects.md with session and plan data.

Run manually or via Stop hook:
  python3 ~/.claude/scripts/update-active-projects.py [hook-input.json]

When invoked by the Stop hook, reads JSON from a temp file (argv[1]) containing
session_id and transcript_path, and only summarizes that specific session.

Features:
- Grouped projects view with up to 3 sessions each (top 10 projects)
- Reads session titles from Claude Code's sessions-index.json (customTitle/summary)
- Falls back to local llama-cli summarization when no title is available
- Plan staleness detection (30-day threshold)
- Robust logging to ~/.claude/logs/update-agent-docs.log
"""

import json
import logging
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECTS_DIR = Path.home() / ".claude" / "projects"
AGENT_DOC = Path.home() / ".claude" / "agent_docs" / "active-projects.md"
SUMMARY_CACHE = Path.home() / ".claude" / "session-summaries.json"
LOG_FILE = Path.home() / ".claude" / "logs" / "update-agent-docs.log"
MAX_PROJECTS = 10
MAX_SESSIONS_PER_PROJECT = 3
MAX_LINES_HEAD = 60  # First N lines for metadata + opening messages
MAX_LINES_TAIL = 80  # Last N lines for context (messages to summarize)
MAX_NEW_SUMMARIES = 20  # Cap API calls per run
STALE_DAYS = 30

# --- Logging setup ---

try:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _handlers = [logging.FileHandler(LOG_FILE), logging.StreamHandler()]
except OSError:
    _handlers = [logging.StreamHandler()]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=_handlers,
)
log = logging.getLogger("update-agent-docs")


# --- Hook input ---

def read_hook_input() -> dict:
    """Read hook JSON from temp file (argv[1]) or stdin fallback."""
    # Preferred: temp file passed by shell hook (race-free)
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        try:
            with open(sys.argv[1]) as f:
                data = json.load(f)
            os.unlink(sys.argv[1])
            return data
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Failed to parse hook input file %s: %s", sys.argv[1], e)
    # Fallback: stdin (manual piped invocation)
    if not sys.stdin.isatty():
        try:
            raw = sys.stdin.read()
            if raw.strip():
                return json.loads(raw)
        except (json.JSONDecodeError, OSError) as e:
            log.warning("Failed to parse hook stdin: %s", e)
    return {}


# --- Session index (Claude Code titles) ---

def load_session_index(project_dir: Path) -> dict:
    """Load sessions-index.json for a project dir. Returns {session_id: {title, summary, firstPrompt}}."""
    index_path = project_dir / "sessions-index.json"
    if not index_path.exists():
        return {}
    try:
        data = json.loads(index_path.read_text())
        result = {}
        for entry in data.get("entries", []):
            sid = entry.get("sessionId", "")
            if not sid:
                continue
            custom_title = entry.get("customTitle") or ""
            cc_summary = entry.get("summary") or ""
            first_prompt = entry.get("firstPrompt") or ""
            # Skip API error summaries
            if cc_summary.startswith("API Error:"):
                cc_summary = ""
            result[sid] = {
                "customTitle": custom_title,
                "summary": cc_summary,
                "firstPrompt": first_prompt,
            }
        return result
    except (json.JSONDecodeError, OSError):
        return {}


# --- Session parsing ---

def parse_session(jsonl_path: Path) -> dict | None:
    """Parse a JSONL session file for metadata, opening messages, and tail context."""
    session_id = jsonl_path.stem
    mtime = jsonl_path.stat().st_mtime
    cwd = None
    slug = None
    git_branch = None
    head_messages = []  # First few user/assistant messages (the topic)

    try:
        with open(jsonl_path) as f:
            for i, line in enumerate(f):
                if i >= MAX_LINES_HEAD:
                    break
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if not cwd and obj.get("cwd"):
                    cwd = obj["cwd"]
                if not slug and obj.get("slug"):
                    slug = obj["slug"]
                if not git_branch and obj.get("gitBranch"):
                    git_branch = obj["gitBranch"]

                # Extract early messages for topic detection
                msg_type = obj.get("type")
                if msg_type in ("user", "assistant") and len(head_messages) < 4:
                    msg = obj.get("message")
                    if isinstance(msg, dict):
                        text = _extract_text(msg.get("content", ""))
                        if text:
                            role = "user" if msg_type == "user" else "assistant"
                            head_messages.append({"role": role, "text": text[:500]})
    except OSError:
        return None

    if not cwd:
        return None

    # Read tail for additional context
    tail_messages = _read_tail_messages(jsonl_path)

    # First user message (for display in active-projects.md)
    # Skip system-like messages: "[Request interrupted", "No prompt", plan implementations
    first_user_msg = ""
    for m in head_messages:
        if m["role"] == "user":
            text = m["text"].strip()
            first_line = text.split("\n")[0].strip()
            if first_line.startswith("[Request") or first_line == "No prompt" or first_line.startswith("Base directory for this skill:"):
                continue
            # For plan implementations, note the plan name
            if first_line.startswith("Implement the following plan:"):
                # Try to extract plan title from next line
                plan_lines = text.split("\n")
                for pl in plan_lines[1:]:
                    pl = pl.strip().lstrip("#").strip()
                    if pl and len(pl) > 5:
                        first_user_msg = f"Implement plan: {pl}"
                        break
                if not first_user_msg:
                    first_user_msg = first_line
            else:
                first_user_msg = first_line[:150]
            break

    return {
        "mtime": mtime,
        "session_id": session_id,
        "cwd": cwd,
        "slug": slug,
        "git_branch": git_branch,
        "head_messages": head_messages,
        "messages": tail_messages,
        "first_user_msg": first_user_msg,
    }


def enrich_session(jsonl_path: Path) -> dict:
    """Extract model, token usage, turns, duration, cost, and worktree status from JSONL.

    Reads head (100 lines) for model/cwd and tail (300 lines) for usage stats.
    """
    model = ""
    cwd = ""
    total_input = 0
    total_output = 0
    num_turns = 0
    total_duration_ms = 0
    total_cost_usd = 0.0

    try:
        with open(jsonl_path) as f:
            # Head: find model and cwd
            for i, line in enumerate(f):
                if i >= 100:
                    break
                try:
                    obj = json.loads(line)
                    if not cwd and obj.get("cwd"):
                        cwd = obj["cwd"]
                    if obj.get("type") == "assistant" and not model:
                        msg = obj.get("message", {})
                        model = msg.get("model", "")
                except json.JSONDecodeError:
                    continue

        # Tail: usage stats + cost
        tail_lines = _tail(jsonl_path, 300)
        for line in tail_lines:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") == "assistant":
                msg = obj.get("message", {})
                if not model:
                    model = msg.get("model", "")
                usage = msg.get("usage", {})
                if usage.get("output_tokens"):
                    total_input += usage.get("input_tokens", 0)
                    total_output += usage.get("output_tokens", 0)

            if obj.get("type") == "system" and obj.get("subtype") == "turn_duration":
                num_turns += 1
                total_duration_ms += obj.get("durationMs", 0)

            # Cost from result messages (last one is cumulative)
            if obj.get("type") == "result" and obj.get("total_cost_usd"):
                total_cost_usd = obj["total_cost_usd"]
            if obj.get("costUsd"):
                total_cost_usd = max(total_cost_usd, obj["costUsd"])
    except OSError:
        pass

    # Detect git worktree
    is_worktree = False
    if cwd:
        try:
            result = subprocess.run(
                ["git", "-C", cwd, "rev-parse", "--git-dir"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0 and "/worktrees/" in result.stdout:
                is_worktree = True
        except (subprocess.TimeoutExpired, OSError):
            pass

    # Shorten model for display
    model_short = (
        model.replace("claude-opus-4-6", "opus-4.6")
        .replace("claude-opus-4-5-20251101", "opus-4.5")
        .replace("claude-sonnet-4-5-20250929", "sonnet-4.5")
        .replace("claude-haiku-4-5-20251001", "haiku-4.5")
    )
    if model_short.startswith("claude-"):
        model_short = model_short[7:]

    return {
        "model": model,
        "model_short": model_short,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "num_turns": num_turns,
        "total_duration_ms": total_duration_ms,
        "total_cost_usd": total_cost_usd,
        "is_worktree": is_worktree,
    }


def _read_tail_messages(jsonl_path: Path) -> list[dict]:
    """Read last N lines and extract user/assistant text messages."""
    messages = []
    try:
        tail_lines = _tail(jsonl_path, MAX_LINES_TAIL)
        for line in tail_lines:
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            msg_type = obj.get("type")
            if msg_type not in ("user", "assistant"):
                continue

            msg = obj.get("message")
            if not isinstance(msg, dict):
                continue

            text = _extract_text(msg.get("content", ""))
            if not text:
                continue

            role = "user" if msg_type == "user" else "assistant"
            messages.append({"role": role, "text": text[:500]})
    except OSError:
        pass

    return messages


def _extract_text(content) -> str:
    """Extract plain text from message content (string or content-block list)."""
    if isinstance(content, str):
        if content.startswith("<"):
            return ""
        return content.strip()
    elif isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict) and block.get("type") == "text":
                t = block.get("text", "").strip()
                if t:
                    parts.append(t)
        return " ".join(parts)
    return ""


def _tail(path: Path, n: int) -> list[str]:
    """Read the last n lines of a file efficiently."""
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            size = f.tell()
            chunk_size = min(size, 200_000)
            f.seek(size - chunk_size)
            data = f.read().decode("utf-8", errors="replace")
            lines = data.splitlines()
            return lines[-n:]
    except OSError:
        return []


# --- Summary cache ---

def load_summary_cache() -> dict:
    """Load cached session summaries."""
    if SUMMARY_CACHE.exists():
        try:
            return json.loads(SUMMARY_CACHE.read_text())
        except (json.JSONDecodeError, OSError):
            pass
    return {}


def save_summary_cache(cache: dict):
    """Write summary cache atomically."""
    tmp = SUMMARY_CACHE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cache, indent=2))
    tmp.rename(SUMMARY_CACHE)


# --- Summary helpers ---

def _sanitize_text(text: str) -> str:
    """Clean up text for display — strip HTML tags and markdown artifacts."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"^\*{1,2}|\*{1,2}$", "", text.strip())
    text = re.sub(r"^_{1,2}|_{1,2}$", "", text.strip())
    return text.strip()


def auto_name_session(first_msg: str) -> str | None:
    """Generate a 3-5 word session title using a one-shot Claude call.

    Returns the title string or None on failure. Costs ~$0.001 per call.
    """
    if not first_msg or len(first_msg.strip()) < 10:
        return None

    prompt = f'Generate a 3-5 word title (no quotes, no punctuation) for this session. Reply with ONLY the title, nothing else.\n\nFirst message: {first_msg[:300]}'
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", "haiku"],
            capture_output=True, text=True, timeout=20
        )
        if result.returncode == 0:
            title = result.stdout.strip().strip('"').strip("'").strip()
            # Validate: 2-8 words, no weird output
            words = title.split()
            if 2 <= len(words) <= 8 and len(title) < 80:
                return title
    except (subprocess.TimeoutExpired, OSError, FileNotFoundError) as e:
        log.debug("Auto-name failed: %s", e)
    return None


def extract_unsummarized(projects: list[dict], cache: dict) -> list[dict]:
    """Find sessions that need summaries and extract their excerpts.

    Returns a list of dicts with session_id, excerpt (head+tail messages),
    first_user_msg, and project path — ready for Claude to summarize.
    """
    unsummarized = []
    for p in projects:
        for s in p["sessions"]:
            sid = s["session_id"]
            if not _cache_needs_update(cache, sid):
                continue

            head = s.get("head_messages", [])
            tail = s.get("messages", [])
            if not head and not tail:
                continue

            excerpt_parts = []
            if head:
                for m in head[:4]:
                    role = "User" if m["role"] == "user" else "Claude"
                    excerpt_parts.append(f"{role}: {m['text'][:400]}")
            if tail:
                for m in tail[-6:]:
                    role = "User" if m["role"] == "user" else "Claude"
                    excerpt_parts.append(f"{role}: {m['text'][:200]}")

            unsummarized.append({
                "session_id": sid,
                "project": p["cwd"],
                "first_user_msg": s.get("first_user_msg", ""),
                "cc_title": s.get("cc_title", ""),
                "cc_summary": s.get("cc_summary", ""),
                "excerpt": "\n".join(excerpt_parts),
            })
    return unsummarized


# --- Project grouping ---

def get_grouped_projects() -> list[dict]:
    """Scan all project directories, return top projects with their recent sessions."""
    if not PROJECTS_DIR.is_dir():
        log.warning("Projects directory not found: %s", PROJECTS_DIR)
        return []

    projects = []

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        jsonls = sorted(
            project_dir.glob("*.jsonl"),
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if not jsonls:
            continue

        # Load Claude Code session titles for this project
        session_titles = load_session_index(project_dir)

        sessions = []
        for jsonl_file in jsonls[:MAX_SESSIONS_PER_PROJECT]:
            result = parse_session(jsonl_file)
            if result:
                # Attach Claude Code's session index data
                cc_data = session_titles.get(result["session_id"], {})
                result["cc_title"] = cc_data.get("customTitle", "") if isinstance(cc_data, dict) else (cc_data if isinstance(cc_data, str) else "")
                result["cc_summary"] = cc_data.get("summary", "") if isinstance(cc_data, dict) else ""
                result["cc_first_prompt"] = cc_data.get("firstPrompt", "") if isinstance(cc_data, dict) else ""
                # Enrich with model/usage data
                enriched = enrich_session(jsonl_file)
                result["model_short"] = enriched["model_short"]
                result["num_turns"] = enriched["num_turns"]
                result["total_input_tokens"] = enriched["total_input_tokens"]
                result["total_output_tokens"] = enriched["total_output_tokens"]
                result["total_cost_usd"] = enriched["total_cost_usd"]
                result["is_worktree"] = enriched["is_worktree"]
                sessions.append(result)

        if not sessions:
            continue

        latest = sessions[0]
        has_claude_md = os.path.isfile(os.path.join(latest["cwd"], "CLAUDE.md"))

        projects.append({
            "cwd": latest["cwd"],
            "has_claude_md": has_claude_md,
            "latest_mtime": latest["mtime"],
            "sessions": sessions,
        })

    projects.sort(key=lambda p: p["latest_mtime"], reverse=True)
    return projects[:MAX_PROJECTS]


def _cache_needs_update(cache: dict, sid: str) -> bool:
    """Check if a cache entry is missing or has bad data (literal HTML tags, empty summary)."""
    if sid not in cache:
        return True
    entry = cache[sid]
    summary = entry.get("summary", "")
    # Detect literal HTML/XML tags that render as collapsed elements
    if summary and re.search(r"<[^>]+>", summary):
        return True
    # Entry exists with a title but no summary — needs enrichment
    if entry.get("title") and not summary:
        return True
    return False


def generate_missing_summaries(projects: list[dict], cache: dict, current_session_id: str | None = None) -> int:
    """Populate cache from Claude Code's sessions-index.json data.

    No LLM calls — uses CC metadata only. Sessions without CC data are left
    unsummarized for Claude to fill in via the skill workflow.
    If current_session_id is provided (from Stop hook), only process that session.
    """
    new_count = 0

    if current_session_id:
        for p in projects:
            for s in p["sessions"]:
                if s["session_id"] == current_session_id:
                    if not _cache_needs_update(cache, current_session_id):
                        log.info("Session %s already cached, skipping", current_session_id[:8])
                        return 0
                    cc_title = s.get("cc_title", "")
                    cc_summary = s.get("cc_summary", "")
                    first_msg = s.get("first_user_msg", "").split("\n")[0].strip()[:150]
                    if cc_title or cc_summary:
                        title = cc_title or cc_summary
                        summary = cc_summary if cc_title else ""
                        log.info("  [%s] Using CC data: %s", current_session_id[:8], title[:60])
                        entry = {"title": title, "summary": summary, "first_msg": first_msg}
                        entry["model"] = s.get("model_short", "")
                        entry["num_turns"] = s.get("num_turns", 0)
                        entry["total_cost_usd"] = s.get("total_cost_usd", 0)
                        cache[current_session_id] = entry
                        return 1
                    log.info("  [%s] No CC data — needs Claude summarization", current_session_id[:8])
                    return 0
        log.warning("Current session %s not found in project scan", current_session_id[:8])
        return 0

    # Manual run: populate from CC data, flag the rest
    log.info("Scanning all sessions for missing/bad summaries")
    unsummarized = []
    for p in projects:
        for s in p["sessions"]:
            sid = s["session_id"]
            if not _cache_needs_update(cache, sid):
                continue

            first_msg = s.get("first_user_msg", "").split("\n")[0].strip()[:150]
            cc_title = s.get("cc_title", "")
            cc_summary = s.get("cc_summary", "")

            if cc_title or cc_summary:
                title = cc_title or cc_summary
                summary = cc_summary if cc_title else ""
                log.info("  [%s] CC data: %s", sid[:8], title[:60])
                entry = {"title": title, "summary": summary, "first_msg": first_msg}
                entry["model"] = s.get("model_short", "")
                entry["num_turns"] = s.get("num_turns", 0)
                entry["total_cost_usd"] = s.get("total_cost_usd", 0)
                cache[sid] = entry
                new_count += 1
            elif new_count < MAX_NEW_SUMMARIES:
                # Auto-name via one-shot Claude call
                auto_title = auto_name_session(first_msg)
                if auto_title:
                    log.info("  [%s] Auto-named: %s", sid[:8], auto_title)
                    cache[sid] = {"title": auto_title, "summary": "", "first_msg": first_msg,
                                  "model": s.get("model_short", ""), "num_turns": s.get("num_turns", 0),
                                  "total_cost_usd": s.get("total_cost_usd", 0), "source": "auto-named"}
                    new_count += 1
                else:
                    unsummarized.append(sid[:8])
            else:
                unsummarized.append(sid[:8])

    if unsummarized:
        log.info("  %d session(s) need Claude summarization: %s", len(unsummarized), ", ".join(unsummarized))

    return new_count


# --- Markdown generation ---

def _get_project_description(cwd: str) -> str:
    """Extract a 1-line project description from CLAUDE.md if available."""
    claude_md = os.path.join(cwd, "CLAUDE.md")
    if not os.path.isfile(claude_md):
        return ""
    try:
        with open(claude_md) as f:
            lines = []
            for line in f:
                lines.append(line.rstrip())
                if len(lines) > 15:
                    break
        # Look for first non-heading, non-empty line that describes the project
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith("#"):
                continue
            if stripped.startswith("*") and stripped.endswith("*"):
                # Italic subtitle — good description candidate
                return stripped.strip("*").strip()
            if len(stripped) > 20 and not stripped.startswith("|") and not stripped.startswith("-"):
                return stripped[:120]
        return ""
    except OSError:
        return ""


def _find_plan_for_project(cwd: str) -> str | None:
    """Find the most recent plan file associated with a project directory."""
    plans_dir = Path.home() / ".claude" / "plans"
    if not plans_dir.is_dir():
        return None

    project_name = os.path.basename(cwd).lower().replace("-", "").replace("_", "")
    best_plan = None
    best_mtime = 0

    for plan_file in plans_dir.glob("*.md"):
        try:
            content = plan_file.read_text()[:500].lower()
            name_lower = plan_file.name.lower()
            # Match by project name in filename or content
            if project_name in name_lower.replace("-", "").replace("_", "") or cwd.lower() in content or os.path.basename(cwd).lower() in content:
                mtime = plan_file.stat().st_mtime
                if mtime > best_mtime:
                    best_mtime = mtime
                    best_plan = plan_file
        except OSError:
            continue

    if best_plan:
        return f"~/.claude/plans/{best_plan.name}"
    return None


def build_projects_section(projects: list[dict], cache: dict) -> str:
    """Build grouped markdown with sessions, summaries, and project descriptions."""
    home = str(Path.home())
    lines = [
        "## Recent Projects",
        "",
        f"*Auto-updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
    ]

    for p in projects:
        display_cwd = p["cwd"].replace(home, "~")
        docs = " (CLAUDE.md)" if p["has_claude_md"] else ""
        lines.append("")
        lines.append(f"### `{display_cwd}`{docs}")

        # Project description from CLAUDE.md
        desc = _get_project_description(p["cwd"])
        if desc:
            lines.append(f"_{desc}_")

        # Plan file link
        plan_path = _find_plan_for_project(p["cwd"])
        if plan_path:
            plan_name = os.path.basename(plan_path).replace(".md", "").replace("-", " ").title()
            lines.append(f"Plan: [{plan_name}]({plan_path})")

        lines.append("")
        lines.append("| Last Active | Session | Branch | Model | Turns | Cost |")
        lines.append("|---|---|---|---|---|---|")

        for s in p["sessions"]:
            ts = datetime.fromtimestamp(s["mtime"]).strftime("%Y-%m-%d %H:%M")
            slug_part = f" {s['slug']}" if s["slug"] else ""
            branch = s["git_branch"] or "\u2014"
            wt_badge = " \U0001F333" if s.get("is_worktree") else ""
            model_col = s.get("model_short", "") or "\u2014"
            turns_col = str(s.get("num_turns", 0)) if s.get("num_turns") else "\u2014"
            cost = s.get("total_cost_usd", 0)
            cost_col = f"${cost:.2f}" if cost else "\u2014"
            lines.append(
                f"| {ts} | `{s['session_id'][:8]}`{slug_part} | {branch}{wt_badge} | {model_col} | {turns_col} | {cost_col} |"
            )

        # Add summaries below the table
        lines.append("")
        for s in p["sessions"]:
            sid = s["session_id"]
            if sid in cache:
                c = cache[sid]
                title = _sanitize_text(c.get("title", ""))
                summary = _sanitize_text(c.get("summary", ""))
                first_msg = c.get("first_msg", "")
                if not title:
                    continue
                summary_part = f" \u2014 {summary}" if summary else ""
                lines.append(f"- `{sid[:8]}`: **{title}**{summary_part}")
                if first_msg:
                    # Show just the first line of the first user message, truncated
                    first_line = first_msg.split("\n")[0].strip()
                    if not first_line or first_line.startswith("[Request"):
                        continue
                    display_msg = first_line[:120]
                    if len(first_line) > 120:
                        display_msg += "..."
                    lines.append(f"  > _{display_msg}_")

    lines.append("")
    lines.append("**Resume:** `claude --resume <session-id>`")
    return "\n".join(lines)


# --- Plan staleness ---

def check_plan_staleness(content: str) -> str:
    """Parse Active Plans table and check for stale/missing plan files."""
    link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    plans_start = content.find("## Active Plans")
    if plans_start == -1:
        return ""

    rest = content[plans_start + len("## Active Plans"):]
    next_heading = rest.find("\n## ")
    plans_section = rest[:next_heading] if next_heading != -1 else rest

    issues = []
    for match in link_pattern.finditer(plans_section):
        name = match.group(1)
        path_str = match.group(2)

        if not path_str.endswith(".md"):
            continue

        resolved = Path(os.path.expanduser(path_str))

        if not resolved.exists():
            issues.append(f"- **MISSING**: {name} \u2192 `{path_str}`")
        else:
            days_old = (time.time() - resolved.stat().st_mtime) / 86400
            if days_old > STALE_DAYS:
                issues.append(
                    f"- **stale ({int(days_old)}d)**: {name} \u2192 `{path_str}`"
                )

    if not issues:
        return ""

    return "\n".join(["## Plan Health", ""] + issues)


# --- Section replacement ---

def replace_section(content: str, marker: str, new_text: str) -> str:
    """Replace a ## section in markdown, or append if not found."""
    if marker in content:
        idx = content.index(marker)
        rest = content[idx + len(marker):]
        next_heading = rest.find("\n## ")
        if not new_text:
            if next_heading != -1:
                return content[:idx].rstrip("\n") + "\n\n" + rest[next_heading + 1:]
            else:
                return content[:idx].rstrip("\n") + "\n"
        else:
            if next_heading != -1:
                return content[:idx] + new_text + "\n\n" + rest[next_heading + 1:]
            else:
                return content[:idx] + new_text + "\n"
    elif new_text:
        return content.rstrip() + "\n\n" + new_text + "\n"
    else:
        return content


# --- Main ---

def update_agent_doc():
    """Rewrite active-projects.md with fresh session data, summaries, and plan health."""
    t_start = time.monotonic()

    hook_input = read_hook_input()
    current_session_id = hook_input.get("session_id")
    hook_cwd = hook_input.get("cwd")
    transcript_path = hook_input.get("transcript_path")

    if current_session_id:
        log.info("=== Stop hook fired: session=%s cwd=%s ===", current_session_id[:8], hook_cwd)
        log.info("Transcript: %s", transcript_path)
    else:
        log.info("=== Manual run (no hook context) ===")

    content = AGENT_DOC.read_text()
    projects = get_grouped_projects()
    total_sessions = sum(len(p["sessions"]) for p in projects)
    cache = load_summary_cache()
    cache_size_before = len(cache)

    log.info("Scanned %d projects, %d sessions, %d cached summaries", len(projects), total_sessions, cache_size_before)

    new_summaries = generate_missing_summaries(projects, cache, current_session_id)
    if new_summaries:
        save_summary_cache(cache)
        log.info("Saved %d new summary to cache (total: %d)", new_summaries, len(cache))

    projects_section = build_projects_section(projects, cache)

    for old_marker in [
        "## Recent Repos (Claude Code Sessions)",
        "## Recent Sessions",
        "## Recent Projects",
        "## Overview",
    ]:
        content = replace_section(content, old_marker, "")

    content = content.rstrip() + "\n\n" + projects_section + "\n"

    staleness = check_plan_staleness(content)
    if staleness:
        content = replace_section(content, "## Plan Health", "")
        content = content.rstrip() + "\n\n" + staleness + "\n"
    elif "## Plan Health" in content:
        content = replace_section(content, "## Plan Health", "")

    tmp = AGENT_DOC.with_suffix(".tmp")
    tmp.write_text(content)
    tmp.rename(AGENT_DOC)
    elapsed = time.monotonic() - t_start
    log.info("Wrote %s (%d projects, %d sessions, %d new summaries) in %.1fs", AGENT_DOC.name, len(projects), total_sessions, new_summaries, elapsed)


def print_unsummarized():
    """Print sessions needing summaries as JSON (for Claude to process)."""
    projects = get_grouped_projects()
    cache = load_summary_cache()
    # First populate CC data
    generate_missing_summaries(projects, cache, None)
    save_summary_cache(cache)
    # Then find what's still missing
    unsummarized = extract_unsummarized(projects, cache)
    if not unsummarized:
        print("All sessions have summaries.")
        return
    print(json.dumps(unsummarized, indent=2))


if __name__ == "__main__":
    if "--summarize" in sys.argv:
        print_unsummarized()
    else:
        update_agent_doc()
