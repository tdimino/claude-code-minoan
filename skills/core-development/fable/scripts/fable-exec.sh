#!/usr/bin/env bash
# CLI fallback for summoning Fable 5 (or Opus 5) when CLAUDE_CODE_SUBAGENT_MODEL
# blocks the Agent(model: ...) override.
#
# Spawns a fresh claude process with an explicit --model, bypassing the env
# var entirely: it governs subagent resolution only and cannot reach a
# spawned process's main model.
#
# Usage:
#   fable-exec.sh "<task prompt>" [--opus] [--cwd <dir>] [--turns <N>]
#
#   --opus   run on claude-opus-5 instead of claude-fable-5 (half the cost,
#            no availability window, so the Fable probe is skipped)

set -euo pipefail

TASK=""
CWD="/Users/tomdimino/Desktop/Programming/Fable-Test"
TURNS=100
OPUS=0

usage() {
  echo "Usage: fable-exec.sh \"<task>\" [--opus] [--cwd <dir>] [--turns <N>]" >&2
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --opus)
      OPUS=1
      shift
      ;;
    --cwd)
      # Guard the value: a trailing --cwd would otherwise abort with a bare
      # "unbound variable" under set -u rather than something readable.
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
      # Never fold an unrecognized flag into the prompt. A typo like --opuss
      # would silently run on Fable at 2x the cost—precisely the outcome the
      # flag exists to prevent—so fail loudly instead.
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
# the run to count as genuine—EXPECT_MODEL is version-specific on purpose, so
# a clamp from Opus 5 down to Opus 4.8 is caught rather than waved through.
if [[ $OPUS -eq 1 ]]; then
  MODEL="claude-opus-5"
  LABEL="Opus 5"
  PREFIX="opus"
  EXPECT_MODEL="opus-5"
  EXPECT_ALT="opus 5"
else
  MODEL="claude-fable-5"
  LABEL="Naos (Fable 5)"
  PREFIX="fable"
  EXPECT_MODEL="fable"
  EXPECT_ALT="fable"
fi

# Returns 0 when the output file's MODEL: line names the model we asked for,
# and stamps the verdict into the file itself. Without that trailer a clamped
# run and a clean run are indistinguishable on disk, and whoever reads the
# file later has to re-derive a judgement this function already made.
#
# NOTE ON WHAT THIS CAN AND CANNOT CATCH: this verifies what the model *says*
# it is. A model that misreports its own id passes. The check defends against
# harness-level clamping, not against an unreliable self-report.
verify_report() {
  local file="$1" want="$2" alt="$3" reported lowered
  # Tolerate leading whitespace and markdown bolding—a spawn that writes
  # "**MODEL:** claude-opus-5" is reporting honestly and must not read as a
  # mismatch just because it formatted the line.
  reported=$(grep -m1 -E '^[[:space:]]*\*{0,2}MODEL:' "$file" 2>/dev/null || true)
  lowered=$(printf '%s' "$reported" | tr '[:upper:]' '[:lower:]')
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

# Availability probe (cached per-day)—no calendar gates; the access
# window has shifted twice and must be tested, not assumed. A failed
# probe doesn't exit: the attempt below has its own Opus fallback.
# Opus 5 is generally available and has no window, so probing it would
# burn tokens on a foregone answer—skip it entirely.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ $OPUS -eq 0 ]]; then
  PROBE_RC=0
  bash "$SCRIPT_DIR/fable-probe.sh" || PROBE_RC=$?
  if [[ $PROBE_RC -eq 1 ]]; then
    echo "Probe says Fable 5 is unavailable—attempting anyway, will fall back to Opus 5 on failure."
  elif [[ $PROBE_RC -ge 2 ]]; then
    echo "Probe errored (indeterminate)—attempting anyway; the MODEL: self-report below is the real verification."
  fi
fi

# Self-report instruction: the first line of output must record the model
# that actually ran, so silent fallbacks are always visible in the transcript.
TASK="First line of your output: 'MODEL: ' followed by the exact model id powering you. Then proceed with the task.

$TASK"

# Ensure output directory exists
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

# Unset ANTHROPIC_API_KEY so claude -p bills to the subscription, not API credits.
# Spawn with direct model selection, bypassing CLAUDE_CODE_SUBAGENT_MODEL.
# A failed verification must reach the caller's exit status. Detecting a clamp
# and then exiting 0 anyway would make the whole self-report scheme decorative.
STATUS=0

if env -u ANTHROPIC_API_KEY claude --model "$MODEL" \
  -p "$TASK" \
  --max-turns "$TURNS" \
  --output-format text \
  | tee "$OUTPUT_FILE"; then
  echo "---"
  # Verify the self-report—a clamp or silent fallback shows up here
  verify_report "$OUTPUT_FILE" "$EXPECT_MODEL" "$EXPECT_ALT" || STATUS=1
  echo "$LABEL output written to: $OUTPUT_FILE"
elif [[ $OPUS -eq 1 ]]; then
  # Opus 5 is already the fallback tier—there is nowhere below it to route to,
  # so report the failure rather than silently degrading further.
  echo "---"
  echo "Opus 5 failed. No fallback tier below it—$OUTPUT_FILE holds whatever it produced first."
  printf '\n<!-- fable-exec verdict: RUN FAILED model=%s -->\n' "$MODEL" >> "$OUTPUT_FILE"
  exit 1
else
  echo "---"
  echo "Fable 5 unavailable or failed. Its partial output is preserved at: $OUTPUT_FILE"
  printf '\n<!-- fable-exec verdict: RUN FAILED model=%s (fell back to claude-opus-5) -->\n' \
    "$MODEL" >> "$OUTPUT_FILE"

  # The fallback gets its own opus-prefixed file. Reusing the Fable file would
  # both destroy the evidence of why Fable failed and file Opus output under
  # the fable-* prefix, breaking the prefix-names-the-model contract that the
  # skill's retrieval globs depend on.
  FALLBACK_FILE="$CWD/.subdaimon-output/opus-${TIMESTAMP}.md"
  echo "Falling back to Opus 5 → $FALLBACK_FILE"
  if env -u ANTHROPIC_API_KEY claude --model claude-opus-5 \
    -p "$TASK" \
    --max-turns "$TURNS" \
    --output-format text \
    | tee "$FALLBACK_FILE"; then
    echo "---"
    # Verify the fallback too—the self-report philosophy applies to every spawn
    MODEL="claude-opus-5" LABEL="Opus 5" \
      verify_report "$FALLBACK_FILE" "opus-5" "opus 5" || STATUS=1
    echo "Opus 5 fallback output written to: $FALLBACK_FILE"
  else
    echo "---"
    echo "Opus 5 fallback also failed. See $OUTPUT_FILE and $FALLBACK_FILE."
    exit 1
  fi
fi

exit $STATUS
