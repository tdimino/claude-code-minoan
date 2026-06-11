#!/usr/bin/env bash
# CLI fallback for summoning Fable 5 when CLAUDE_CODE_SUBAGENT_MODEL
# blocks the Agent(model: "fable") override.
#
# Spawns a fresh claude process with --model claude-fable-5, bypassing
# the env var entirely.
#
# Usage:
#   fable-exec.sh "<task prompt>" [--cwd <dir>] [--turns <N>]

set -euo pipefail

TASK=""
CWD="/Users/tomdimino/Desktop/Programming/Fable-Test"
TURNS=100

while [[ $# -gt 0 ]]; do
  case "$1" in
    --cwd)
      CWD="$2"
      shift 2
      ;;
    --turns)
      TURNS="$2"
      shift 2
      ;;
    *)
      if [[ -z "$TASK" ]]; then
        TASK="$1"
      else
        TASK="$TASK $1"
      fi
      shift
      ;;
  esac
done

if [[ -z "$TASK" ]]; then
  echo "Error: no task description provided"
  echo "Usage: fable-exec.sh \"<task>\" [--cwd <dir>] [--turns <N>]"
  exit 1
fi

# Date gate — fall back to Opus 4.6 after expiration
if [[ "$(date +%Y%m%d)" -gt "20260622" ]]; then
  echo "Fable 5 access ended June 22, 2026. Falling back to Opus 4.6..."
  mkdir -p "$CWD/.subdaimon-output"
  TIMESTAMP=$(date +%s)
  OUTPUT_FILE="$CWD/.subdaimon-output/fable-${TIMESTAMP}.md"
  cd "$CWD"
  env -u ANTHROPIC_API_KEY claude --model claude-opus-4-6 \
    -p "$TASK" \
    --max-turns "$TURNS" \
    --output-format text \
    | tee "$OUTPUT_FILE"
  echo "---"
  echo "Opus 4.6 fallback output written to: $OUTPUT_FILE"
  exit 0
fi

# Ensure output directory exists
mkdir -p "$CWD/.subdaimon-output"

TIMESTAMP=$(date +%s)
OUTPUT_FILE="$CWD/.subdaimon-output/fable-${TIMESTAMP}.md"

echo "Summoning Naos (Fable 5) in $CWD..."
echo "Task: $TASK"
echo "Max turns: $TURNS"
echo "Output: $OUTPUT_FILE"
echo "---"

cd "$CWD"

# Unset ANTHROPIC_API_KEY so claude -p bills to the subscription, not API credits.
# Spawn with direct model selection, bypassing CLAUDE_CODE_SUBAGENT_MODEL.
# Falls back to Opus 4.6 if Fable is unavailable or refuses.
if env -u ANTHROPIC_API_KEY claude --model claude-fable-5 \
  -p "$TASK" \
  --max-turns "$TURNS" \
  --output-format text \
  | tee "$OUTPUT_FILE"; then
  echo "---"
  echo "Fable output written to: $OUTPUT_FILE"
else
  echo "---"
  echo "Fable 5 unavailable or failed. Falling back to Opus 4.6..."
  env -u ANTHROPIC_API_KEY claude --model claude-opus-4-6 \
    -p "$TASK" \
    --max-turns "$TURNS" \
    --output-format text \
    | tee "$OUTPUT_FILE"
  echo "---"
  echo "Opus 4.6 fallback output written to: $OUTPUT_FILE"
fi
