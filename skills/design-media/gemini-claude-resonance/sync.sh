#!/bin/bash
# Sync gemini-claude-resonance between local skill and repo
#
# Usage:
#   ./sync.sh push    # Local skill → Repo (default)
#   ./sync.sh pull    # Repo → Local skill
#
# Excludes: .env, .DS_Store, canvas/, test-results/, __pycache__/

set -e

LOCAL_SKILL="$HOME/.claude/skills/gemini-claude-resonance"
REPO_SKILL="$(dirname "$0")"

EXCLUDES=(
    --exclude='.env'
    --exclude='.DS_Store'
    --exclude='canvas/'
    --exclude='test-results/'
    --exclude='__pycache__/'
)

case "${1:-push}" in
    push)
        echo "Syncing: Local skill → Repo"
        rsync -av "${EXCLUDES[@]}" "$LOCAL_SKILL/" "$REPO_SKILL/"
        echo "Done. Run 'git status' to see changes."
        ;;
    pull)
        echo "Syncing: Repo → Local skill"
        rsync -av "${EXCLUDES[@]}" "$REPO_SKILL/" "$LOCAL_SKILL/"
        echo "Done. Local skill updated."
        ;;
    *)
        echo "Usage: $0 [push|pull]"
        echo "  push - Local skill → Repo (default)"
        echo "  pull - Repo → Local skill"
        exit 1
        ;;
esac
