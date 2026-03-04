#!/usr/bin/env python3
"""
One-time migration: copy SMS working memory into the canonical Claudicle daemon DB.

Migrates entries from ~/.claude/skills/sms/data/sms_memory.db into
~/.claudicle/daemon/memory/memory.db with proper channel prefixes.

Idempotent: skips entries already present (by content + timestamp match).

Usage:
    python3 migrate_to_canonical.py [--dry-run]
"""

import json
import os
import sqlite3
import sys
from pathlib import Path

# Add daemon directory to path
DAEMON_DIR = os.path.expanduser("~/.claudicle/daemon")
if DAEMON_DIR not in sys.path:
    sys.path.insert(0, DAEMON_DIR)

SMS_DB = Path(os.path.expanduser("~/.claude/skills/sms/data/sms_memory.db"))
SOUL_PATH = Path(os.path.expanduser("~/.claudicle/soul/soul.md"))

# Import shared modules
_SHARED_DIR = str(Path(__file__).parent)
if _SHARED_DIR not in sys.path:
    sys.path.insert(0, _SHARED_DIR)

import usermodel_resolver as _ur


def migrate_sms_memory(dry_run: bool = False) -> dict:
    """Copy SMS working memory entries into canonical DB.

    Returns: {"migrated": N, "would_migrate": N, "skipped": N, "errors": N}
    """
    if not SMS_DB.exists():
        print(f"SMS DB not found: {SMS_DB}")
        return {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    if not SOUL_PATH.exists():
        print("Soul not active (soul.md not found). Cannot migrate to canonical DB.")
        return {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    from memory import working_memory
    from memory import db as _db

    sms_conn = sqlite3.connect(str(SMS_DB))
    sms_conn.row_factory = sqlite3.Row

    stats = {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    try:
        rows = sms_conn.execute(
            """SELECT phone_number, our_number, entry_type, verb, content, metadata, created_at
               FROM working_memory
               ORDER BY created_at ASC"""
        ).fetchall()

        for row in rows:
            phone = row["phone_number"]
            channel = f"sms:{phone}"
            content = row["content"]
            created_at = row["created_at"]

            # Check if already exists in canonical DB (by channel + content + timestamp)
            conn = _db.memory_pool.get_conn()
            existing = conn.execute(
                """SELECT 1 FROM working_memory
                   WHERE channel = ? AND content = ? AND ABS(created_at - ?) < 1""",
                (channel, content, created_at),
            ).fetchone()

            if existing:
                stats["skipped"] += 1
                continue

            if dry_run:
                display_name = _ur.get_display_name_for_phone(phone)
                print(f"[DRY RUN] Would migrate: {channel} | {row['entry_type']} | {content[:60]}...")
                stats["would_migrate"] += 1
                continue

            try:
                metadata = None
                if row["metadata"]:
                    try:
                        metadata = json.loads(row["metadata"])
                    except (json.JSONDecodeError, TypeError):
                        metadata = None

                display_name = _ur.get_display_name_for_phone(phone)
                working_memory.add(
                    channel=channel,
                    thread_ts=phone,
                    user_id=phone,
                    entry_type=row["entry_type"],
                    content=content,
                    verb=row["verb"],
                    metadata=metadata,
                    display_name=display_name,
                )
                stats["migrated"] += 1
            except Exception as e:
                print(f"Error migrating entry: {e}")
                stats["errors"] += 1
    finally:
        sms_conn.close()

    return stats


def migrate_sms_user_models(dry_run: bool = False) -> dict:
    """Copy SMS user model entries into canonical DB.

    Returns: {"migrated": N, "would_migrate": N, "skipped": N, "errors": N}
    """
    if not SMS_DB.exists():
        return {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    if not SOUL_PATH.exists():
        print("Soul not active. Cannot migrate.")
        return {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    from memory import user_models

    sms_conn = sqlite3.connect(str(SMS_DB))
    sms_conn.row_factory = sqlite3.Row

    stats = {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    try:
        rows = sms_conn.execute(
            "SELECT phone_number, display_name, model_md, interaction_count FROM user_models"
        ).fetchall()

        for row in rows:
            phone = row["phone_number"]
            model_md = row["model_md"]

            # Skip empty or template-only models
            if not model_md or "Unknown — first SMS interaction" in model_md:
                stats["skipped"] += 1
                continue

            # Skip if rich userModel exists (don't overwrite curated models)
            rich = _ur.resolve_by_phone(phone)
            if rich:
                stats["skipped"] += 1
                continue

            # Check if already in canonical DB
            existing = user_models.get(phone)
            if existing:
                stats["skipped"] += 1
                continue

            if dry_run:
                print(f"[DRY RUN] Would migrate user model: {phone} ({row['display_name']})")
                stats["would_migrate"] += 1
                continue

            try:
                user_models.save(phone, model_md, row["display_name"])
                stats["migrated"] += 1
            except Exception as e:
                print(f"Error migrating user model for {phone}: {e}")
                stats["errors"] += 1
    finally:
        sms_conn.close()

    return stats


def migrate_sms_soul_memory(dry_run: bool = False) -> dict:
    """Copy SMS soul memory into canonical DB.

    Returns: {"migrated": N, "would_migrate": N, "skipped": N, "errors": N}
    """
    if not SMS_DB.exists():
        return {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    if not SOUL_PATH.exists():
        print("Soul not active. Cannot migrate.")
        return {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    from memory import soul_memory

    sms_conn = sqlite3.connect(str(SMS_DB))
    sms_conn.row_factory = sqlite3.Row

    stats = {"migrated": 0, "would_migrate": 0, "skipped": 0, "errors": 0}

    try:
        rows = sms_conn.execute("SELECT key, value FROM soul_memory").fetchall()

        for row in rows:
            key = row["key"]
            value = row["value"]

            # Skip default values
            defaults = {
                "currentProject": "", "currentTask": "", "currentTopic": "",
                "emotionalState": "neutral", "conversationSummary": "",
            }
            if value == defaults.get(key, ""):
                stats["skipped"] += 1
                continue

            # Check if canonical already has a non-default value
            existing = soul_memory.get(key)
            if existing and existing != defaults.get(key, ""):
                stats["skipped"] += 1
                continue

            if dry_run:
                print(f"[DRY RUN] Would migrate soul key: {key} = {value[:60]}")
                stats["would_migrate"] += 1
                continue

            try:
                soul_memory.set(key, value)
                stats["migrated"] += 1
            except Exception as e:
                print(f"Error migrating soul key {key}: {e}")
                stats["errors"] += 1
    finally:
        sms_conn.close()

    return stats


def main():
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("=== DRY RUN MODE ===\n")

    print("--- SMS Working Memory ---")
    wm_stats = migrate_sms_memory(dry_run)
    print(f"Working memory: {wm_stats}")

    print("\n--- SMS User Models ---")
    um_stats = migrate_sms_user_models(dry_run)
    print(f"User models: {um_stats}")

    print("\n--- SMS Soul Memory ---")
    sm_stats = migrate_sms_soul_memory(dry_run)
    print(f"Soul memory: {sm_stats}")

    key = "would_migrate" if dry_run else "migrated"
    total = sum(s[key] for s in [wm_stats, um_stats, sm_stats])
    label = "Would migrate" if dry_run else "Total migrated"
    print(f"\n{label}: {total}")


if __name__ == "__main__":
    main()
