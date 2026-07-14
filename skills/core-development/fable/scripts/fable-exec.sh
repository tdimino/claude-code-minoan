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

# Availability probe (cached per-day)—no calendar gates; the access
# window has shifted twice and must be tested, not assumed. A failed
# probe doesn't exit: the attempt below has its own Opus fallback.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if ! bash "$SCRIPT_DIR/fable-probe.sh"; then
  echo "Probe says Fable 5 is unavailable—attempting anyway, will fall back to Opus 4.6 on failure."
fi

# Self-report instruction: the first line of output must record the model
# that actually ran, so silent fallbacks are always visible in the transcript.
TASK="First line of your output: 'MODEL: ' followed by the exact model id powering you. Then proceed with the task.

$TASK"

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
  # Verify the self-report—a clamp or silent fallback shows up here
  reported=$(grep -m1 '^MODEL:' "$OUTPUT_FILE" 2>/dev/null || true)
  if [[ "$reported" == *fable* ]]; then
    echo "Verified: $reported"
  else
    echo "WARNING: expected claude-fable-5, got '${reported:-no MODEL line}'—the task did NOT run on Fable"
  fi
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
  # Verify the fallback too—the self-report philosophy applies to every spawn
  reported=$(grep -m1 '^MODEL:' "$OUTPUT_FILE" 2>/dev/null || true)
  if [[ "$reported" == *opus* ]]; then
    echo "Verified fallback: $reported"
  else
    echo "WARNING: expected an Opus model in fallback, got '${reported:-no MODEL line}'"
  fi
  echo "Opus 4.6 fallback output written to: $OUTPUT_FILE"
fi
