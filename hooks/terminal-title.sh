#!/bin/bash
# Two-tier terminal title with repo icons for Claude Code
# Sets: STATUS_ICON REPO_ICON MAIN_TITLE: SUBTITLE
#
# Called as on-thinking.sh (PreToolUse) or on-ready.sh (Stop)
# Symlinked: on-thinking.sh -> terminal-title.sh, on-ready.sh -> terminal-title.sh

# Read hook input JSON from stdin
INPUT=$(cat)

SCRIPT_NAME=$(basename "$0")

# --- Extract session metadata from hook JSON ---

# Single jq pass for all fields
read -r CWD SESSION_ID TRANSCRIPT_PATH < <(echo "$INPUT" | jq -r '[
  .cwd // "",
  .session_id // "",
  .transcript_path // ""
] | @tsv' 2>/dev/null)
if [[ -z "$CWD" || "$CWD" == "null" ]]; then
  CWD="$(pwd)"
fi

# --- Repo Icon Detection ---

detect_repo_icon() {
  local cwd="$1"

  # Check CLAUDE.md for semantic keywords first
  if [[ -f "$cwd/CLAUDE.md" ]]; then
    local claude_head
    claude_head=$(head -30 "$cwd/CLAUDE.md" 2>/dev/null)
    case "$claude_head" in
      *[Ss]oul*|*daimonic*|*[Dd]aimon*) echo "👁"; return ;;
      *[Rr]esearch*|*[Mm]inoan*|*[Ss]emitic*|*[Ll]inear\ A*) echo "📜"; return ;;
      *[Gg]ame*|*BG3*|*[Mm]odding*|*Script\ Extender*) echo "🎮"; return ;;
      *[Ee]vent*|*[Cc]ommunit*) echo "🏛"; return ;;
    esac
  fi

  # File-based heuristics (most specific first)
  if [[ -f "$cwd/package.json" ]]; then
    local pkg
    pkg=$(cat "$cwd/package.json" 2>/dev/null)
    if echo "$pkg" | grep -q '"react"' 2>/dev/null; then
      echo "⚛️"; return
    elif echo "$pkg" | grep -q '"astro"' 2>/dev/null; then
      echo "🚀"; return
    elif echo "$pkg" | grep -q '"next"' 2>/dev/null; then
      echo "▲"; return
    elif echo "$pkg" | grep -q '"svelte"' 2>/dev/null; then
      echo "🔥"; return
    elif echo "$pkg" | grep -q '"vue"' 2>/dev/null; then
      echo "💚"; return
    fi
    echo "🟨"; return  # Generic JS/Node
  fi
  [[ -f "$cwd/Cargo.toml" ]] && { echo "🦀"; return; }
  [[ -f "$cwd/pyproject.toml" || -f "$cwd/setup.py" || -f "$cwd/requirements.txt" ]] && { echo "🐍"; return; }
  [[ -f "$cwd/Gemfile" ]] && { echo "💎"; return; }
  [[ -f "$cwd/go.mod" ]] && { echo "🔵"; return; }
  [[ -f "$cwd/Dockerfile" && ! -f "$cwd/package.json" && ! -f "$cwd/pyproject.toml" ]] && { echo "🐳"; return; }
  [[ -f "$cwd/Package.swift" || -f "$cwd/.swift-version" ]] && { echo "🐦"; return; }
  [[ -f "$cwd/CMakeLists.txt" || -f "$cwd/Makefile" ]] && { echo "🔧"; return; }

  echo "📁"
}

# Hash CWD once, reuse for all temp files
CWD_HASH=$(echo "$CWD" | md5 -q 2>/dev/null || echo "$CWD" | md5sum 2>/dev/null | cut -d' ' -f1)

# Cache icon per CWD (computed once per session)
ICON_CACHE="/tmp/claude-icon-$CWD_HASH"
if [[ -f "$ICON_CACHE" ]]; then
  REPO_ICON=$(cat "$ICON_CACHE")
else
  REPO_ICON=$(detect_repo_icon "$CWD")
  echo "$REPO_ICON" > "$ICON_CACHE"
fi

# --- Main Title (persistent, only /rename changes it) ---

MAIN_TITLE=""

# Priority 1: customTitle from sessions-index.json (set via /rename)
if [[ -n "$TRANSCRIPT_PATH" && -n "$SESSION_ID" ]]; then
  PROJECT_DIR=$(dirname "$TRANSCRIPT_PATH")
  INDEX_FILE="$PROJECT_DIR/sessions-index.json"
  if [[ -f "$INDEX_FILE" ]]; then
    CUSTOM_TITLE=$(jq -r --arg sid "$SESSION_ID" \
      '.entries[] | select(.sessionId == $sid) | .customTitle // empty' \
      "$INDEX_FILE" 2>/dev/null)
    if [[ -n "$CUSTOM_TITLE" && "$CUSTOM_TITLE" != "null" ]]; then
      MAIN_TITLE="$CUSTOM_TITLE"
    fi
  fi
fi

# Priority 2: basename of CWD (repo/directory name)
if [[ -z "$MAIN_TITLE" ]]; then
  MAIN_TITLE=$(basename "$CWD")
fi

# Sanitize & truncate main title
MAIN_TITLE=$(echo "$MAIN_TITLE" | tr -d '\000-\037\177' | sed 's/\\e//g; s/\\033//g; s/\\x1b//gi')
if [[ ${#MAIN_TITLE} -gt 20 ]]; then
  MAIN_TITLE="${MAIN_TITLE:0:17}..."
fi
if [[ -z "$MAIN_TITLE" ]]; then
  MAIN_TITLE="claude"
fi

# --- Subtitle (dynamic, transcript-derived on Stop events) ---

SUBTITLE_FILE="/tmp/claude-subtitle-${SESSION_ID:-default}"

# On Stop/ready events, extract subtitle from transcript
if [[ "$SCRIPT_NAME" == "on-ready.sh" || "$SCRIPT_NAME" == "ready" || \
      ( "$1" != "thinking" && "$SCRIPT_NAME" != "on-thinking.sh" ) ]]; then
  if [[ -n "$TRANSCRIPT_PATH" && -f "$TRANSCRIPT_PATH" ]]; then
    # Parse last assistant text from JSONL transcript
    LAST_TEXT=$(tail -30 "$TRANSCRIPT_PATH" 2>/dev/null | \
      jq -r 'select(.type == "assistant") | .message.content[]? |
        select(.type == "text") | .text' 2>/dev/null | tail -1)
    if [[ -n "$LAST_TEXT" ]]; then
      # Extract first meaningful fragment: first sentence or first 40 chars
      EXTRACTED=$(echo "$LAST_TEXT" | head -1 | sed 's/[.!?].*//' | head -c 40 | \
        tr -d '\000-\037\177' | sed 's/\\e//g; s/\\033//g; s/\\x1b//gi; s/[[:space:]]*$//')
      if [[ -n "$EXTRACTED" && ${#EXTRACTED} -gt 3 ]]; then
        echo "$EXTRACTED" > "$SUBTITLE_FILE"
      fi
    fi
  fi
fi

# Read cached subtitle (works for both thinking and ready)
SUBTITLE=""
if [[ -f "$SUBTITLE_FILE" ]]; then
  SUBTITLE=$(cat "$SUBTITLE_FILE" 2>/dev/null | head -c 40)
fi

# --- Compose Display Name ---

if [[ -n "$SUBTITLE" ]]; then
  DISPLAY_NAME="$MAIN_TITLE: $SUBTITLE"
else
  DISPLAY_NAME="$MAIN_TITLE"
fi

# --- Duration Tracking ---

DURATION_FILE="/tmp/claude-start-$CWD_HASH"

format_duration() {
  local seconds=$1
  if [[ $seconds -lt 60 ]]; then
    echo "${seconds}s"
  elif [[ $seconds -lt 3600 ]]; then
    echo "$((seconds / 60))m $((seconds % 60))s"
  else
    echo "$((seconds / 3600))h $(((seconds % 3600) / 60))m"
  fi
}

# --- Desktop Notification ---

send_notification() {
  local title="$1"
  local message="$2"
  terminal-notifier \
    -title "$title" \
    -message "$message" \
    -activate "com.microsoft.VSCode" \
    -sound "" \
    -group "claude-${MAIN_TITLE}" \
    2>/dev/null &
}

# --- State Handlers ---

set_thinking() {
  TITLE="🔴 $REPO_ICON $DISPLAY_NAME"
  date +%s > "$DURATION_FILE"
}

set_ready() {
  TITLE="🟢 $REPO_ICON $DISPLAY_NAME"

  DURATION_MSG=""
  if [[ -f "$DURATION_FILE" ]]; then
    START_TIME=$(cat "$DURATION_FILE")
    NOW=$(date +%s)
    ELAPSED=$((NOW - START_TIME))
    DURATION_MSG=" ($(format_duration $ELAPSED))"
    rm -f "$DURATION_FILE"
  fi

  afplay ~/.claude/sounds/soft-ui.mp3 &

  if [[ -n "$SUBTITLE" ]]; then
    send_notification "$REPO_ICON $MAIN_TITLE" "$SUBTITLE$DURATION_MSG"
  else
    send_notification "$REPO_ICON $MAIN_TITLE" "Ready$DURATION_MSG"
  fi
}

case "$SCRIPT_NAME" in
  "on-thinking.sh"|"thinking") set_thinking ;;
  "on-ready.sh"|"ready") set_ready ;;
  *) [[ "$1" == "thinking" ]] && set_thinking || set_ready ;;
esac

# Set terminal title via OSC escape sequence
printf '\033]0;%s\007' "$TITLE"

exit 0
