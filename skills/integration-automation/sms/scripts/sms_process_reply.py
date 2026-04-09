#!/usr/bin/env python3
"""
Batch SMS reply processor — sends reply + performs all memory operations in one call.

Replaces 9 separate python3 -c invocations in the /sms-respond pipeline.

Usage:
    python3 sms_process_reply.py \
        --phone "+17327595647" \
        --our-number "+18557066006" \
        --message-id "SM0334c637c6017dbf84eae2a7fd824abd" \
        --message-text "Hmm, how's that poller" \
        --reply-text "The poller is alive and well." \
        --monologue-text "They're testing the watcher loop." \
        --monologue-verb "noticed" \
        --dialogue-verb "quipped" \
        --user-model-check false

    # With user model and soul state updates:
    python3 sms_process_reply.py \
        --phone "+17327595647" \
        --our-number "+18557066006" \
        --message-id "SM..." \
        --message-text "original text" \
        --reply-text "reply text" \
        --monologue-text "monologue" \
        --monologue-verb "thought" \
        --dialogue-verb "said" \
        --user-model-check true \
        --user-model-md "# Updated model markdown" \
        --soul-updates '{"currentTopic": "testing", "emotionalState": "engaged"}'
"""

import argparse
import json
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sms_memory as m
from _sms_utils import mark_inbox_handled


def load_args_from_stdin():
    """Read all arguments as a JSON object from stdin. Avoids shell quoting issues."""
    data = json.load(sys.stdin)
    # Convert to namespace matching argparse fields
    class Args:
        pass
    args = Args()
    args.phone = data["phone"]
    args.our_number = data["our_number"]
    args.message_id = data["message_id"]
    args.message_text = data["message_text"]
    args.reply_text = data["reply_text"]
    args.monologue_text = data["monologue_text"]
    args.monologue_verb = data.get("monologue_verb", "thought")
    args.dialogue_verb = data.get("dialogue_verb", "said")
    args.user_model_check = str(data.get("user_model_check", "false"))
    args.user_model_md = data.get("user_model_md")
    args.soul_updates = json.dumps(data["soul_updates"]) if data.get("soul_updates") else None
    args.dry_run = data.get("dry_run", False)
    return args


def main():
    # --stdin-json mode: read all args from stdin as JSON (avoids shell quoting)
    # --dry-run CLI flag overrides JSON dry_run field for safety
    if "--stdin-json" in sys.argv:
        args = load_args_from_stdin()
        if "--dry-run" in sys.argv:
            args.dry_run = True
    else:
        parser = argparse.ArgumentParser(description="Batch SMS reply: send + memory update")
        parser.add_argument("--phone", required=True, help="Sender's E.164 number")
        parser.add_argument("--our-number", required=True, help="Our number they texted")
        parser.add_argument("--message-id", required=True, help="Inbox message ID")
        parser.add_argument("--message-text", required=True, help="Original inbound message text")
        parser.add_argument("--reply-text", required=True, help="External dialogue text to send")
        parser.add_argument("--monologue-text", required=True, help="Internal monologue text")
        parser.add_argument("--monologue-verb", default="thought", help="Monologue verb")
        parser.add_argument("--dialogue-verb", default="said", help="Dialogue verb")
        parser.add_argument("--user-model-check", default="false",
                            help="Whether user model was updated (true/false)")
        parser.add_argument("--user-model-md", help="Updated user model markdown (if check was true)")
        parser.add_argument("--soul-updates", help="JSON dict of soul state updates")
        parser.add_argument("--dry-run", action="store_true", help="Skip sending SMS, do memory only")
        parser.add_argument("--stdin-json", action="store_true", help="Read args from stdin as JSON")
        args = parser.parse_args()

    user_model_check = str(args.user_model_check).lower() == "true"
    scripts_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. Send the reply
    if not args.dry_run:
        result = subprocess.run(
            [sys.executable, os.path.join(scripts_dir, "sms_send.py"),
             args.phone, args.reply_text, "--from", args.our_number],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            print(f"Send failed: {result.stderr}", file=sys.stderr)
            sys.exit(1)
        print(result.stdout.strip())
    else:
        print(f"[dry-run] Would send to {args.phone}: {args.reply_text[:80]}")

    # 2. Log inbound message to working memory
    m.add_working_memory(args.phone, args.our_number, "userMessage", args.message_text)

    # 2a. Extract and log any URLs as link entries
    urls = re.findall(r'https?://[^\s<>"\']+', args.message_text)
    for url in urls:
        from urllib.parse import urlparse
        domain = urlparse(url).netloc
        m.add_working_memory(args.phone, args.our_number, "link", url,
                             metadata={"domain": domain, "source_message_id": args.message_id})
    if urls:
        print(f"  Extracted {len(urls)} link(s)")

    # 3. Log internal monologue
    m.add_working_memory(args.phone, args.our_number, "internalMonologue",
                         args.monologue_text, verb=args.monologue_verb)

    # 4. Log external dialogue
    m.add_working_memory(args.phone, args.our_number, "externalDialog",
                         args.reply_text, verb=args.dialogue_verb)

    # 5. Update user model if check was true
    if user_model_check and args.user_model_md:
        m.save_user_model(args.phone, args.user_model_md)
        print(f"  User model updated")

    # 6. Update soul state
    if args.soul_updates:
        try:
            updates = json.loads(args.soul_updates)
            for key, value in updates.items():
                m.set_soul(key, str(value))
            print(f"  Soul state updated: {', '.join(updates.keys())}")
        except json.JSONDecodeError as e:
            print(f"Warning: invalid --soul-updates JSON: {e}", file=sys.stderr)

    # 7. Log user_model_check decision
    m.add_working_memory(args.phone, args.our_number, "mentalQuery",
                         "user model check", metadata={"result": user_model_check})

    # 8. Increment interaction counter
    m.increment_interaction(args.phone)

    # 9. Mark as handled + dedup
    handled = mark_inbox_handled(args.message_id)
    m.mark_replied(args.message_id)

    status = "handled" if handled else "not found in inbox"
    print(f"  Memory updated, message {status}")


if __name__ == "__main__":
    main()
