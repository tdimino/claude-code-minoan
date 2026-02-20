#!/bin/bash
# StatusLine wrapper — hand-built line 1 (ANSI passthrough) + ccstatusline lines 2-3
# Line 1 is assembled here because ccstatusline strips inline ANSI codes,
# and the gradient context bar needs true color.

INPUT=$(cat)

# ── ANSI color codes ──
TYRIAN="\033[38;2;204;92;58m"      # hex:CC5C3A (original session name color)
CRAB_COLOR="\033[38;2;200;128;188m" # Pastel Byzantium (#C880BC)
BLUE="\033[94m"                   # brightBlue
DIM="\033[2m"
RESET="\033[0m"

# ── Separator ──
SEP="${DIM} | ${RESET}"

# ── Widget 1: Session name (Tyrian purple) ──
SESSION_NAME=$(echo "$INPUT" | ~/.claude/hooks/session-name.sh 2>/dev/null)

# ── Widget 2: Crab model (brightMagenta) ──
CRAB_MODEL=$(echo "$INPUT" | ~/.claude/hooks/crab-model.sh 2>/dev/null)

# ── Widget 3: Context bar (gradient — renders its own ANSI) ──
CONTEXT_BAR=$(echo "$INPUT" | python3 ~/.claude/hooks/context-bar.sh 2>/dev/null)

# ── Widget 4: Git branch (brightBlue) ──
GIT_BRANCH=$(git branch --show-current 2>/dev/null)
[ -z "$GIT_BRANCH" ] && GIT_BRANCH="detached"

# ── Widget 5: Git changes (yellow) — disabled for now ──
# YELLOW="\033[33m"
# GIT_CHANGES=""
# if git rev-parse --git-dir &>/dev/null; then
#   ADDED=$(git ls-files --others --exclude-standard 2>/dev/null | wc -l | tr -d ' ')
#   MODIFIED=$(git diff --name-only --diff-filter=M 2>/dev/null | wc -l | tr -d ' ')
#   MODIFIED_STAGED=$(git diff --cached --name-only --diff-filter=M 2>/dev/null | wc -l | tr -d ' ')
#   MODIFIED=$((MODIFIED + MODIFIED_STAGED))
#   DELETED=$(git diff --name-only --diff-filter=D 2>/dev/null | wc -l | tr -d ' ')
#   DELETED_STAGED=$(git diff --cached --name-only --diff-filter=D 2>/dev/null | wc -l | tr -d ' ')
#   DELETED=$((DELETED + DELETED_STAGED))
#   PARTS=""
#   [ "$ADDED" -gt 0 ] && PARTS="+${ADDED}"
#   [ "$MODIFIED" -gt 0 ] && PARTS="${PARTS:+$PARTS }~${MODIFIED}"
#   [ "$DELETED" -gt 0 ] && PARTS="${PARTS:+$PARTS }-${DELETED}"
#   GIT_CHANGES="$PARTS"
# fi

# ── Assemble line 1 ──
LINE1="${TYRIAN}${SESSION_NAME}${RESET}"
LINE1="${LINE1}${SEP}"
LINE1="${LINE1}${CRAB_COLOR}${CRAB_MODEL}${RESET}"
LINE1="${LINE1}${SEP}"
LINE1="${LINE1}${CONTEXT_BAR}"
LINE1="${LINE1}${SEP}"
LINE1="${LINE1}${BLUE}⎇ ${GIT_BRANCH}${RESET}"
# [ -n "$GIT_CHANGES" ] && LINE1="${LINE1}${SEP}${YELLOW}${GIT_CHANGES}${RESET}"

# ── Render ccstatusline (lines 2-3 only now) ──
CC_OUTPUT=$(echo "$INPUT" | ccstatusline 2>/dev/null)

# ── Output ──
printf '%b\n' "$LINE1"
echo "$CC_OUTPUT"
