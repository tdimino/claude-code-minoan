#!/bin/bash
# Dynamic terminal title indicator for Claude Code
# Shows thinking/ready state in terminal tab title
# Also sends desktop notifications with click-to-focus

# Debug logging
echo "[$(date)] on-ready.sh called" >> /tmp/claude-hook-debug.log

# Read the hook input (contains session info as JSON)
INPUT=$(cat)
echo "[$(date)] INPUT: $INPUT" >> /tmp/claude-hook-debug.log

# Extract the event type from the hook context
SCRIPT_NAME=$(basename "$0")

# Get the working directory from JSON or fall back to pwd
CWD=$(echo "$INPUT" | jq -r '.cwd // empty' 2>/dev/null)
if [[ -z "$CWD" || "$CWD" == "null" ]]; then
  CWD="$(pwd)"
fi

# Try to get session name from multiple possible JSON fields
# Priority: session_name > cwd basename > "claude"
SESSION_NAME=$(echo "$INPUT" | jq -r '
  .session_name //
  .sessionName //
  .conversation_name //
  .conversationName //
  empty
' 2>/dev/null)

# If no session name in hook JSON, check sessions-index.json for customTitle
if [[ -z "$SESSION_NAME" || "$SESSION_NAME" == "null" ]]; then
  SESSION_ID=$(echo "$INPUT" | jq -r '.session_id // empty' 2>/dev/null)
  TRANSCRIPT_PATH=$(echo "$INPUT" | jq -r '.transcript_path // empty' 2>/dev/null)
  if [[ -n "$TRANSCRIPT_PATH" && -n "$SESSION_ID" ]]; then
    PROJECT_DIR=$(dirname "$TRANSCRIPT_PATH")
    INDEX_FILE="$PROJECT_DIR/sessions-index.json"
    if [[ -f "$INDEX_FILE" ]]; then
      CUSTOM_TITLE=$(jq -r --arg sid "$SESSION_ID" \
        '.entries[] | select(.sessionId == $sid) | .customTitle // empty' \
        "$INDEX_FILE" 2>/dev/null)
      if [[ -n "$CUSTOM_TITLE" && "$CUSTOM_TITLE" != "null" ]]; then
        SESSION_NAME="$CUSTOM_TITLE"
      fi
    fi
  fi
fi

# Fall back to cwd basename if still no name
if [[ -z "$SESSION_NAME" || "$SESSION_NAME" == "null" ]]; then
  SESSION_NAME=$(basename "$CWD")
fi

# Detect project name from package.json, Cargo.toml, or pyproject.toml
# Only use manifest name - VS Code already shows directory
PROJECT_NAME=""
if [[ -f "$CWD/package.json" ]]; then
  PROJECT_NAME=$(grep -o '"name": *"[^"]*"' "$CWD/package.json" 2>/dev/null | head -1 | cut -d'"' -f4)
elif [[ -f "$CWD/Cargo.toml" ]]; then
  PROJECT_NAME=$(grep -o '^name = "[^"]*"' "$CWD/Cargo.toml" 2>/dev/null | head -1 | cut -d'"' -f2)
elif [[ -f "$CWD/pyproject.toml" ]]; then
  PROJECT_NAME=$(grep -o '^name = "[^"]*"' "$CWD/pyproject.toml" 2>/dev/null | head -1 | cut -d'"' -f2)
fi

# Format project name with brackets if found
PROJECT_DISPLAY=""
if [[ -n "$PROJECT_NAME" ]]; then
  # Sanitize
  PROJECT_NAME=$(echo "$PROJECT_NAME" | tr -d '\000-\037\177' | sed 's/\\e//g; s/\\033//g; s/\\x1b//gi')
  if [[ ${#PROJECT_NAME} -gt 20 ]]; then
    PROJECT_NAME="${PROJECT_NAME:0:17}..."
  fi
  PROJECT_DISPLAY=" [$PROJECT_NAME]"
fi

# SECURITY: Sanitize session name to prevent escape sequence injection
# Remove any control characters (0x00-0x1F, 0x7F) and escape sequences
SESSION_NAME=$(echo "$SESSION_NAME" | tr -d '\000-\037\177' | sed 's/\\e//g; s/\\033//g; s/\\x1b//gi')

# Truncate long names to keep title readable (max 20 chars)
if [[ ${#SESSION_NAME} -gt 20 ]]; then
  SESSION_NAME="${SESSION_NAME:0:17}..."
fi

# Final safety: if somehow empty after sanitization, use a safe default
if [[ -z "$SESSION_NAME" ]]; then
  SESSION_NAME="claude"
fi

# Duration tracking - use a temp file keyed by session/cwd
DURATION_FILE="/tmp/claude-start-$(echo "$CWD" | md5 -q)"

# Function to format duration
format_duration() {
  local seconds=$1
  if [[ $seconds -lt 60 ]]; then
    echo "${seconds}s"
  elif [[ $seconds -lt 3600 ]]; then
    local mins=$((seconds / 60))
    local secs=$((seconds % 60))
    echo "${mins}m ${secs}s"
  else
    local hours=$((seconds / 3600))
    local mins=$(((seconds % 3600) / 60))
    echo "${hours}h ${mins}m"
  fi
}

# Function to send desktop notification (runs in background)
send_notification() {
  local title="$1"
  local message="$2"

  # Use terminal-notifier with click-to-focus VS Code
  terminal-notifier \
    -title "$title" \
    -message "$message" \
    -activate "com.microsoft.VSCode" \
    -sound "" \
    -group "claude-$SESSION_NAME" \
    2>/dev/null &
}

# Set terminal title based on which hook called us
case "$SCRIPT_NAME" in
  "on-thinking.sh"|"thinking")
    # Red circle - Claude is working (thinking/generating response)
    TITLE="🔴 $SESSION_NAME$PROJECT_DISPLAY"
    # Record start time for duration tracking
    date +%s > "$DURATION_FILE"
    ;;
  "on-ready.sh"|"ready")
    # Green circle - Claude is ready for input
    TITLE="🟢 $SESSION_NAME$PROJECT_DISPLAY"

    # Calculate duration if we have a start time
    DURATION_MSG=""
    if [[ -f "$DURATION_FILE" ]]; then
      START_TIME=$(cat "$DURATION_FILE")
      NOW=$(date +%s)
      ELAPSED=$((NOW - START_TIME))
      DURATION_MSG=" ($(format_duration $ELAPSED))"
      rm -f "$DURATION_FILE"
    fi

    # Play completion sound - runs in background to not block
    afplay ~/.claude/sounds/soft-ui.mp3 &

    # Send desktop notification with click-to-focus
    send_notification "🟢 $SESSION_NAME" "Ready for input$DURATION_MSG"
    ;;
  *)
    # Determine from argument or default to ready
    if [[ "$1" == "thinking" ]]; then
      TITLE="🔴 $SESSION_NAME$PROJECT_DISPLAY"
      date +%s > "$DURATION_FILE"
    else
      TITLE="🟢 $SESSION_NAME$PROJECT_DISPLAY"

      DURATION_MSG=""
      if [[ -f "$DURATION_FILE" ]]; then
        START_TIME=$(cat "$DURATION_FILE")
        NOW=$(date +%s)
        ELAPSED=$((NOW - START_TIME))
        DURATION_MSG=" ($(format_duration $ELAPSED))"
        rm -f "$DURATION_FILE"
      fi

      afplay ~/.claude/sounds/soft-ui.mp3 &
      send_notification "🟢 $SESSION_NAME" "Ready for input$DURATION_MSG"
    fi
    ;;
esac

# Set terminal title using OSC escape sequence
# Works in VS Code, iTerm2, Terminal.app, and most modern terminals
printf '\033]0;%s\007' "$TITLE"

# Exit successfully (don't block Claude)
exit 0
