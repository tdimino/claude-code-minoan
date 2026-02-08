#!/bin/bash
# Session Handoff - appends to ~/.claude/handoffs/YYYY-MM-DD.md
# Triggered via StatusLine at 5% (creates entry) or PreCompact (updates entry)

set -e

DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)
HANDOFF_DIR="$HOME/.claude/handoffs"
HANDOFF_FILE="${HANDOFF_DIR}/${DATE}.md"
STATE_DIR="$HOME/.claude/handoffs/.state"

mkdir -p "$HANDOFF_DIR" "$STATE_DIR"

# Get session ID from environment (StatusLine) or stdin JSON (PreCompact)
SESSION_ID="${CLAUDE_SESSION_ID:-}"
TRIGGER="${HANDOFF_TRIGGER:-5pct}"  # "5pct" or "compact"

if [ -z "$SESSION_ID" ] && [ ! -t 0 ]; then
    INPUT=$(cat)
    SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4 2>/dev/null || echo "")
    TRIGGER="compact"
fi
SESSION_ID="${SESSION_ID:-unknown}"
SESSION_SHORT="${SESSION_ID:0:8}"

# State file for this session
STATE_FILE="${STATE_DIR}/${SESSION_ID}"

# Get current directory and project
CURRENT_DIR=$(pwd)
PROJECT_NAME=""
if [ -f "package.json" ]; then
    PROJECT_NAME=$(grep -o '"name": *"[^"]*"' package.json | head -1 | cut -d'"' -f4)
elif [ -f "Cargo.toml" ]; then
    PROJECT_NAME=$(grep -o '^name = "[^"]*"' Cargo.toml | head -1 | cut -d'"' -f2)
elif [ -f "pyproject.toml" ]; then
    PROJECT_NAME=$(grep -o '^name = "[^"]*"' pyproject.toml | head -1 | cut -d'"' -f2)
fi
PROJECT_NAME="${PROJECT_NAME:-$(basename "$CURRENT_DIR")}"

# Git info
GIT_BRANCH=""
GIT_STATUS=""
RECENT_COMMITS=""
if git rev-parse --git-dir > /dev/null 2>&1; then
    GIT_BRANCH=$(git branch --show-current 2>/dev/null || echo "unknown")
    GIT_STATUS=$(git status --short 2>/dev/null | head -15)
    RECENT_COMMITS=$(git log --oneline -5 2>/dev/null || echo "")
fi

# Recently modified files
RECENT_FILES=$(find . -type f \( -name "*.ts" -o -name "*.tsx" -o -name "*.js" -o -name "*.py" -o -name "*.md" -o -name "*.astro" -o -name "*.sh" \) -mmin -120 2>/dev/null | grep -v node_modules | grep -v '.git' | head -10 || echo "")

# Create header if file doesn't exist
if [ ! -f "$HANDOFF_FILE" ]; then
    cat > "$HANDOFF_FILE" << EOF
# Session Handoffs - ${DATE}

Central log of all session compactions across projects.

---
EOF
fi

# Check if we already have an entry for this session (created at 5%)
if [ -f "$STATE_FILE" ] && [ "$TRIGGER" = "compact" ]; then
    # UPDATE existing entry: add compaction marker
    # Find the line with this session ID and add [COMPACTED] to the header
    sed -i '' "s/## ${PROJECT_NAME} — .* \[5%\] (${SESSION_SHORT})/## ${PROJECT_NAME} — ${TIME} [COMPACTED] (${SESSION_SHORT})/" "$HANDOFF_FILE"

    # Clean up state file
    rm -f "$STATE_FILE"
    echo "Updated entry in: $HANDOFF_FILE" >&2
else
    # CREATE new entry at 5%
    cat >> "$HANDOFF_FILE" << EOF

## ${PROJECT_NAME} — ${TIME} [5%] (${SESSION_SHORT})

| Field | Value |
|-------|-------|
| **Session** | \`${SESSION_ID}\` |
| **Directory** | \`${CURRENT_DIR}\` |
| **Branch** | ${GIT_BRANCH} |

### Current Objective
<!-- What were you trying to accomplish? -->

### What Was Done
<!-- Summary of completed work -->

### Decisions Made
<!-- Key choices and rationale -->

### Blockers / Open Questions
<!-- Unresolved issues -->

### Git Status
\`\`\`
${GIT_STATUS:-No changes}
\`\`\`

### Recent Commits
\`\`\`
${RECENT_COMMITS:-No commits}
\`\`\`

### Recently Modified
${RECENT_FILES:-None detected}

### Next Steps
<!-- What should happen next -->

---
EOF

    # Mark that we created an entry for this session
    echo "$TIME" > "$STATE_FILE"
    echo "Created entry in: $HANDOFF_FILE" >&2
fi
