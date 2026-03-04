#!/usr/bin/env python3
"""
Background SMS listener — polls Twilio + receives Telnyx webhooks → inbox.jsonl.

Runs as a standalone daemon alongside Claude Code sessions.
Two subsystems in one process:
  1. Twilio poller thread — queries Messages API every N seconds
  2. Telnyx webhook server — HTTP server on port 9147 for inbound webhooks

Usage:
    python3 sms_listen.py             # foreground (testing)
    python3 sms_listen.py --bg        # daemonize, PID file
    python3 sms_listen.py --stop      # kill running listener
    python3 sms_listen.py --status    # check if running

Requires: requests (pip install requests)
"""

import argparse
import json
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import HTTPServer, BaseHTTPRequestHandler

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _sms_utils import (
    append_inbox, get_listener_pid, normalize_e164,
    twilio_request, SMSError, TWILIO_NUMBERS,
    LISTENER_PID_PATH, LISTENER_STATE_PATH,
)

DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
LOG_PATH = os.path.join(DATA_DIR, "listener.log")

# ── State Management ──────────────────────────────────────────────────────

def load_state() -> dict:
    """Load listener state (last_check_ts, seen_ids) from disk."""
    try:
        with open(LISTENER_STATE_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {
            "last_check_ts": datetime.now(timezone.utc).isoformat(),
            "seen_ids": [],
        }


def save_state(state: dict) -> None:
    """Persist listener state to disk."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(LISTENER_STATE_PATH, "w") as f:
        json.dump(state, f, indent=2)


# ── Twilio Poller ─────────────────────────────────────────────────────────

def poll_twilio(numbers: list, state: dict) -> int:
    """Poll Twilio for new inbound messages. Returns count of new messages."""
    new_count = 0
    seen = set(state.get("seen_ids", []))

    for number in numbers:
        try:
            params = {
                "To": number,
                "PageSize": 50,
            }
            # Only fetch messages since last check
            last_ts = state.get("last_check_ts")
            if last_ts:
                # Twilio DateSent uses YYYY-MM-DD format
                date_str = last_ts[:10]
                params["DateSent>"] = date_str

            result = twilio_request("GET", "/Messages.json", params=params)
            for msg in result.get("messages", []):
                sid = msg.get("sid", "")
                direction = msg.get("direction", "")

                # Skip outbound and already-seen
                if "inbound" not in direction:
                    continue
                if sid in seen:
                    continue

                entry = {
                    "ts": time.time(),
                    "from": msg.get("from", "?"),
                    "to": msg.get("to", "?"),
                    "body": msg.get("body", ""),
                    "id": sid,
                    "provider": "twilio",
                    "date_sent": msg.get("date_sent") or msg.get("date_created", ""),
                    "handled": False,
                }
                append_inbox(entry)
                seen.add(sid)
                new_count += 1

                ts_str = time.strftime("%H:%M:%S")
                body_preview = (entry["body"] or "")[:60]
                print(f"[{ts_str}] Twilio inbound: {entry['from']} → {entry['to']}: {body_preview}", flush=True)

        except SMSError as e:
            print(f"[{time.strftime('%H:%M:%S')}] Twilio poll error for {number}: {e}", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Twilio poll error: {e}", file=sys.stderr, flush=True)

    # Update state
    state["last_check_ts"] = datetime.now(timezone.utc).isoformat()
    state["seen_ids"] = list(seen)[-500:]  # Rotate to last 500
    save_state(state)

    return new_count


def twilio_poll_loop(numbers: list, interval: int, stop_event: threading.Event):
    """Main polling loop for Twilio. Runs until stop_event is set."""
    state = load_state()
    print(f"Twilio poller started — monitoring {len(numbers)} number(s), interval {interval}s", flush=True)

    while not stop_event.is_set():
        try:
            poll_twilio(numbers, state)
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Poll loop error: {e}", file=sys.stderr, flush=True)
        stop_event.wait(interval)


# ── Telnyx Webhook Server ─────────────────────────────────────────────────

class TelnyxWebhookHandler(BaseHTTPRequestHandler):
    """HTTP handler for Telnyx inbound message webhooks."""

    # Shared state for dedup (set by server setup)
    seen_ids = set()

    def do_POST(self):
        if self.path != "/telnyx":
            self.send_response(404)
            self.end_headers()
            return

        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            payload = json.loads(body)
        except (ValueError, json.JSONDecodeError):
            self.send_response(400)
            self.end_headers()
            return

        # Telnyx webhook structure: { "data": { "event_type": "...", "payload": { ... } } }
        data = payload.get("data", {})
        event_type = data.get("event_type", "")

        if event_type != "messaging.message.received":
            # Acknowledge non-inbound events silently
            self.send_response(200)
            self.end_headers()
            return

        msg_payload = data.get("payload", {})
        msg_id = data.get("id") or msg_payload.get("id", "")

        # Dedup
        if msg_id in self.seen_ids:
            self.send_response(200)
            self.end_headers()
            return

        from_info = msg_payload.get("from", {})
        to_info = msg_payload.get("to", [{}])
        from_number = from_info.get("phone_number", "?") if isinstance(from_info, dict) else str(from_info)
        to_number = to_info[0].get("phone_number", "?") if isinstance(to_info, list) and to_info else "?"

        entry = {
            "ts": time.time(),
            "from": from_number,
            "to": to_number,
            "body": msg_payload.get("text", ""),
            "id": msg_id,
            "provider": "telnyx",
            "date_sent": msg_payload.get("received_at") or datetime.now(timezone.utc).isoformat(),
            "handled": False,
        }
        append_inbox(entry)
        self.seen_ids.add(msg_id)

        ts_str = time.strftime("%H:%M:%S")
        body_preview = (entry["body"] or "")[:60]
        print(f"[{ts_str}] Telnyx inbound: {entry['from']} → {entry['to']}: {body_preview}", flush=True)

        self.send_response(200)
        self.end_headers()

    def log_message(self, format, *args):
        """Suppress default HTTP server access logs."""
        pass


def run_webhook_server(port: int, stop_event: threading.Event):
    """Run the Telnyx webhook HTTP server until stop_event is set."""
    server = HTTPServer(("127.0.0.1", port), TelnyxWebhookHandler)
    server.timeout = 1.0  # Check stop_event every second
    print(f"Telnyx webhook server on :{port}", flush=True)

    while not stop_event.is_set():
        server.handle_request()

    server.server_close()
    print("Telnyx webhook server stopped.", flush=True)


# ── Daemon Lifecycle ──────────────────────────────────────────────────────

def cmd_stop():
    """Kill the running listener via PID file."""
    pid = get_listener_pid()
    if pid is None:
        print("Listener is not running.")
        try:
            LISTENER_PID_PATH.unlink(missing_ok=True)
        except (AttributeError, FileNotFoundError):
            pass
        return
    os.kill(pid, signal.SIGTERM)
    for _ in range(30):
        try:
            os.kill(pid, 0)
        except OSError:
            break
        time.sleep(0.1)
    try:
        LISTENER_PID_PATH.unlink(missing_ok=True)
    except (AttributeError, FileNotFoundError):
        pass
    print(f"Listener (PID {pid}) stopped.")


def cmd_status():
    """Check if listener is running."""
    pid = get_listener_pid()
    if pid is not None:
        print(f"Listener running (PID {pid})")
    else:
        print("Listener is not running.")
        try:
            LISTENER_PID_PATH.unlink(missing_ok=True)
        except (AttributeError, FileNotFoundError):
            pass


def run_listener(
    background: bool = False,
    interval: int = 10,
    numbers: list = None,
    webhook_port: int = 9147,
    enable_twilio: bool = True,
    enable_telnyx: bool = True,
):
    """Start the SMS listener daemon."""
    # Check if already running
    pid = get_listener_pid()
    if pid is not None:
        print(f"Listener already running (PID {pid}). Use --stop first.")
        sys.exit(1)

    if not enable_twilio and not enable_telnyx:
        print("Error: Both --no-twilio and --no-telnyx specified. Nothing to do.", file=sys.stderr)
        sys.exit(1)

    # Default: monitor all Twilio numbers
    if numbers is None:
        numbers = list(TWILIO_NUMBERS.keys())
    else:
        numbers = [normalize_e164(n) for n in numbers]

    os.makedirs(DATA_DIR, exist_ok=True)

    if background:
        pid = os.fork()
        if pid > 0:
            # Parent
            LISTENER_PID_PATH.parent.mkdir(parents=True, exist_ok=True)
            LISTENER_PID_PATH.write_text(str(pid))
            print(f"Listener started in background (PID {pid})")
            return
        # Child — detach
        os.setsid()
        log_fd = open(LOG_PATH, "a")
        os.dup2(log_fd.fileno(), sys.stdout.fileno())
        os.dup2(log_fd.fileno(), sys.stderr.fileno())
    else:
        # Foreground — write PID file for status checks
        LISTENER_PID_PATH.parent.mkdir(parents=True, exist_ok=True)
        LISTENER_PID_PATH.write_text(str(os.getpid()))

    stop_event = threading.Event()

    # Graceful shutdown
    def _cleanup(signum, frame):
        print("\nListener shutting down...", flush=True)
        stop_event.set()
        try:
            LISTENER_PID_PATH.unlink(missing_ok=True)
        except (AttributeError, FileNotFoundError):
            pass

    signal.signal(signal.SIGTERM, _cleanup)
    signal.signal(signal.SIGINT, _cleanup)

    print(f"SMS listener started (PID {os.getpid()})", flush=True)

    threads = []

    # Start Telnyx webhook server in background thread
    if enable_telnyx:
        telnyx_thread = threading.Thread(
            target=run_webhook_server,
            args=(webhook_port, stop_event),
            daemon=True,
        )
        telnyx_thread.start()
        threads.append(telnyx_thread)

    # Run Twilio poller (in main thread, or skip if disabled)
    if enable_twilio:
        twilio_poll_loop(numbers, interval, stop_event)
    else:
        # If Twilio disabled, just wait for stop signal
        print("Twilio polling disabled. Telnyx webhook-only mode.", flush=True)
        try:
            while not stop_event.is_set():
                stop_event.wait(1.0)
        except KeyboardInterrupt:
            stop_event.set()

    # Wait for threads to finish
    for t in threads:
        t.join(timeout=3)

    print("Listener stopped.", flush=True)


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SMS inbound listener daemon")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--bg", action="store_true", help="Run in background")
    group.add_argument("--stop", action="store_true", help="Stop running listener")
    group.add_argument("--status", action="store_true", help="Check if running")

    parser.add_argument("--interval", type=int, default=10, help="Twilio poll interval in seconds (default: 10)")
    parser.add_argument("--numbers", nargs="+", help="Twilio numbers to monitor (default: all)")
    parser.add_argument("--webhook-port", type=int, default=9147, help="Telnyx webhook port (default: 9147)")
    parser.add_argument("--no-telnyx", action="store_true", help="Disable Telnyx webhook server")
    parser.add_argument("--no-twilio", action="store_true", help="Disable Twilio polling")

    args = parser.parse_args()

    if args.stop:
        cmd_stop()
    elif args.status:
        cmd_status()
    else:
        run_listener(
            background=args.bg,
            interval=args.interval,
            numbers=args.numbers,
            webhook_port=args.webhook_port,
            enable_twilio=not args.no_twilio,
            enable_telnyx=not args.no_telnyx,
        )


if __name__ == "__main__":
    main()
