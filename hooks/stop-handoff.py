#!/usr/bin/env python3
"""Stop hook: throttled handoff — every 5 min, skip if idle >10 min."""
import json, sys, os, time, pathlib, subprocess


def main():
    hook_input = json.loads(sys.stdin.read())

    # Guard 1: Don't fire during forced continuation (prevent infinite loops)
    if hook_input.get("stop_hook_active", False):
        return

    session_id = hook_input.get("session_id", "unknown")
    transcript_path = hook_input.get("transcript_path", "")

    if not transcript_path or not os.path.exists(transcript_path):
        return

    # Guard 2: 5-minute cooldown per session
    state_dir = pathlib.Path.home() / ".claude" / "handoffs"
    state_dir.mkdir(parents=True, exist_ok=True)
    cooldown_file = state_dir / ".last-stop-handoff"

    now = time.time()
    if cooldown_file.exists():
        try:
            last_data = json.loads(cooldown_file.read_text())
            last_time = last_data.get("timestamp", 0)
            last_session = last_data.get("session_id", "")
            # Reset cooldown if session changed
            if last_session == session_id and (now - last_time) < 300:  # 5 min
                return
        except (json.JSONDecodeError, OSError):
            pass

    # Guard 3: 10-minute idle gate — skip if transcript hasn't been modified
    try:
        transcript_mtime = os.path.getmtime(transcript_path)
        if (now - transcript_mtime) > 600:  # 10 min
            return
    except OSError:
        return

    # All gates passed — run the handoff
    hook_input["trigger"] = "stop"
    input_json = json.dumps(hook_input)

    script = pathlib.Path.home() / ".claude" / "hooks" / "precompact-handoff.py"
    try:
        subprocess.run(
            ["python3", str(script)],
            input=input_json,
            text=True,
            timeout=45,
            capture_output=True,
        )
    except Exception:
        return  # Silent failure

    # Update cooldown timestamp
    cooldown_file.write_text(json.dumps({
        "timestamp": now,
        "session_id": session_id,
    }))


if __name__ == "__main__":
    main()
