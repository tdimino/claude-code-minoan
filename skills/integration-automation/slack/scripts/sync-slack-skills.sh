#!/bin/bash
# Sync slack + slack-respond skills to both distribution repos.
# Source of truth: ~/.claude/skills/
# Aldea copy: direct (no transforms)
# Minoan copy: URL replacement + content scoping
#
# Usage:
#   ./sync-slack-skills.sh          # sync both
#   ./sync-slack-skills.sh --dry    # show what would be synced

set -euo pipefail

SKILL_DIR="$HOME/.claude/skills"
ALDEA_BASE="$HOME/Desktop/Aldea/Prompt development/claude-code-aldea/skills/integration-automation"
MINOAN_BASE="$HOME/Desktop/claude-code-minoan/skills/integration-automation"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

DRY=""
if [[ "${1:-}" == "--dry" ]]; then
    DRY="--dry-run"
    echo "=== DRY RUN ==="
fi

RSYNC_EXCLUDE=(
    --exclude '__pycache__'
    --exclude '*.pyc'
    --exclude 'node_modules'
    --exclude '.venv'
    --exclude 'inbox.jsonl'
    --exclude 'memory.db'
    --exclude 'sessions.db'
    --exclude 'logs/'
    --exclude 'listener.pid'
    --exclude '.DS_Store'
    --exclude '.env'
    --exclude 'uv.lock'
    --exclude 'transform_for_minoan.py'
    --exclude 'sync-slack-skills.sh'
)

echo "--- Syncing to Aldea (direct copy) ---"
rsync -av $DRY --delete "${RSYNC_EXCLUDE[@]}" \
    "$SKILL_DIR/slack/" "$ALDEA_BASE/slack/"
rsync -av $DRY --delete "${RSYNC_EXCLUDE[@]}" \
    "$SKILL_DIR/slack-respond/" "$ALDEA_BASE/slack-respond/"

echo ""
echo "--- Syncing to Minoan (copy + transform) ---"
rsync -av $DRY --delete "${RSYNC_EXCLUDE[@]}" \
    "$SKILL_DIR/slack/" "$MINOAN_BASE/slack/"
rsync -av $DRY --delete "${RSYNC_EXCLUDE[@]}" \
    "$SKILL_DIR/slack-respond/" "$MINOAN_BASE/slack-respond/"

if [[ -z "$DRY" ]]; then
    echo ""
    echo "--- Transforming Minoan URLs ---"
    python3 "$SCRIPT_DIR/transform_for_minoan.py" "$MINOAN_BASE"
fi

echo ""
echo "=== Sync complete ==="
