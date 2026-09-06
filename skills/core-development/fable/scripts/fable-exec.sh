#!/usr/bin/env bash
# CLI fallback for summoning Fable 5.1 (default) or Fable 5.0 (--naos) when
# CLAUDE_CODE_SUBAGENT_MODEL blocks the Agent(model: ...) override.
#
# Spawns a fresh claude process with an explicit --model, bypassing the env
# var entirely: it governs subagent resolution only and cannot reach a
# spawned process's main model.
#
# Usage:
#   fable-exec.sh "<task prompt>" [--naos|--5.0] [--cwd <dir>] [--turns <N>]
#
#   --naos / --5.0   run on claude-fable-5 (Naos) instead of claude-fable-5-1 (Theoros)
#
# Fallback: Fable 5.1 → Fable 5.0 on failure. If both fail, exit non-zero.

set -euo pipefail

TASK=""
CWD="/Users/tomdimino/Desktop/Programming/Fable-Test"
TURNS=100
NAOS=0

usage() {
  echo "Usage: fable-exec.sh \"<task>\" [--naos|--5.0] [--cwd <dir>] [--turns <N>]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --naos|--5.0)
      NAOS=1
      shift
      ;;
    --cwd)
      [[ $# -ge 2 ]] || { echo "Error: --cwd requires a value" >&2; usage; exit 1; }
      CWD="$2"
      shift 2
      ;;
    --turns)
      [[ $# -ge 2 ]] || { echo "Error: --turns requires a value" >&2; usage; exit 1; }
      TURNS="$2"
      shift 2
      ;;
    --*)
      echo "Error: unknown flag '$1'" >&2
      usage
      exit 1
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
  echo "Error: no task description provided" >&2
  usage
  exit 1
fi

# Model selection. EXPECT_* are substrings the self-report must contain for
# the run to count as genuine. EXPECT_EXCLUDE prevents cross-version false
# positives (e.g. fable-5-1 satisfying a fable-5 check).
if [[ $NAOS -eq 1 ]]; then
  MODEL="claude-fable-5"
  LABEL="Naos (Fable 5.0)"
  PREFIX="fable"
  EXPECT_MODEL="fable-5"
  EXPECT_ALT="fable 5"
  EXPECT_EXCLUDE="fable-5-1"
else
  MODEL="claude-fable-5-1"
  LABEL="Theoros (Fable 5.1)"
  PREFIX="fable51"
  EXPECT_MODEL="fable-5-1"
  EXPECT_ALT="fable-5.1"
  EXPECT_EXCLUDE=""
fi

# Returns 0 when the output file's MODEL: line names the model we asked for,
# and stamps the verdict into the file itself.
verify_report() {
  local file="$1" want="$2" alt="$3" exclude="${4:-}" reported lowered
  reported=$(grep -m1 -E '^[[:space:]]*\*{0,2}MODEL:' "$file" 2>/dev/null || true)
  lowered=$(printf '%s' "$reported" | tr '[:upper:]' '[:lower:]')

  if [[ -n "$exclude" && "$lowered" == *"$exclude"* ]]; then
    echo "WARNING: expected $MODEL, got '${reported}'—wrong Fable version"
    printf '\n<!-- fable-exec verdict: VERSION MISMATCH requested=%s reported=%s -->\n' \
      "$MODEL" "${reported:-none}" >> "$file"
    return 1
  fi

  if [[ "$lowered" == *"$want"* || "$lowered" == *"$alt"* ]]; then
    echo "Verified: $reported"
    printf '\n<!-- fable-exec verdict: VERIFIED requested=%s reported=%s -->\n' \
      "$MODEL" "${reported:-none}" >> "$file"
    return 0
  fi
  echo "WARNING: expected $MODEL, got '${reported:-no MODEL line}'—the task did NOT run on $LABEL"
  printf '\n<!-- fable-exec verdict: MODEL MISMATCH requested=%s reported=%s -->\n' \
    "$MODEL" "${reported:-none}" >> "$file"
  return 1
}

# Availability probe (cached per-day, keyed per model).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROBE_RC=0
bash "$SCRIPT_DIR/fable-probe.sh" --model "$MODEL" || PROBE_RC=$?
if [[ $PROBE_RC -eq 1 ]]; then
  echo "Probe says $LABEL is unavailable—attempting anyway, will fall back on failure."
elif [[ $PROBE_RC -ge 2 ]]; then
  echo "Probe errored (indeterminate)—attempting anyway; the MODEL: self-report below is the real verification."
fi

# Self-report instruction
TASK="In your FINAL message (the last thing you output), the first line must be 'MODEL: ' followed by the exact model id powering you. Then proceed with the task.

$TASK"

mkdir -p "$CWD/.subdaimon-output"

TIMESTAMP=$(date +%s)
OUTPUT_FILE="$CWD/.subdaimon-output/${PREFIX}-${TIMESTAMP}.md"

echo "Summoning $LABEL in $CWD..."
echo "Task: $TASK"
echo "Model: $MODEL"
echo "Max turns: $TURNS"
echo "Output: $OUTPUT_FILE"
echo "---"

cd "$CWD"

STATUS=0

AGENT_FLAG=""
if [[ $NAOS -eq 1 ]]; then
  AGENT_FLAG="--agent fable"
else
  AGENT_FLAG="--agent fable-5-1"
fi

if env -u ANTHROPIC_API_KEY claude --model "$MODEL" \
  $AGENT_FLAG \
  -p "$TASK" \
  --max-turns "$TURNS" \
  --output-format text \
  | tee "$OUTPUT_FILE"; then
  echo "---"
  verify_report "$OUTPUT_FILE" "$EXPECT_MODEL" "$EXPECT_ALT" "$EXPECT_EXCLUDE" || STATUS=1
  echo "$LABEL output written to: $OUTPUT_FILE"
elif [[ $NAOS -eq 1 ]]; then
  # Naos (Fable 5.0) is already the floor—no further fallback.
  echo "---"
  echo "Fable 5.0 (Naos) failed. No fallback—$OUTPUT_FILE holds whatever it produced first."
  printf '\n<!-- fable-exec verdict: RUN FAILED model=%s -->\n' "$MODEL" >> "$OUTPUT_FILE"
  exit 1
else
  # Fable 5.1 (Theoros) failed—fall back to Fable 5.0 (Naos).
  echo "---"
  echo "Fable 5.1 unavailable or failed. Its partial output is preserved at: $OUTPUT_FILE"
  printf '\n<!-- fable-exec verdict: RUN FAILED model=%s (fell back to claude-fable-5) -->\n' \
    "$MODEL" >> "$OUTPUT_FILE"

  FALLBACK_FILE="$CWD/.subdaimon-output/fable-${TIMESTAMP}.md"
  echo "Falling back to Naos (Fable 5.0) → $FALLBACK_FILE"
  if env -u ANTHROPIC_API_KEY claude --model claude-fable-5 \
    --agent fable \
    -p "$TASK" \
    --max-turns "$TURNS" \
    --output-format text \
    | tee "$FALLBACK_FILE"; then
    echo "---"
    verify_report "$FALLBACK_FILE" "fable-5" "fable 5" "fable-5-1" || STATUS=1
    echo "Naos (Fable 5.0) fallback output written to: $FALLBACK_FILE"
  else
    echo "---"
    echo "Fable 5.0 fallback also failed. Both Fable versions unavailable."
    printf '\n<!-- fable-exec verdict: RUN FAILED model=claude-fable-5 -->\n' >> "$FALLBACK_FILE"
    exit 1
  fi
fi

exit $STATUS
