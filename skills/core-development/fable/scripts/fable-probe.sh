#!/usr/bin/env bash
# Probe whether a Claude Fable model is currently available on this account.
#
# Fable has been permanently included in subscription plans since July 20,
# 2026 (after the June export-control pause and the shifting restoration
# window), but availability is still tested empirically, never assumed—the
# history is exactly why.
#
# Verdicts are three-way, and only definitive ones are cached:
#   exit 0 — available (Fable answered as itself); cached
#   exit 1 — unavailable (affirmative denial, or another model answered); cached
#   exit 2 — probe error (empty reply, transient CLI failure); NEVER cached,
#            so one flaky run cannot poison the day's verdict
#
# Cache: ~/.claude/cache/fable-availability.json, same-day TTL, keyed per model.
#
# Usage:
#   fable-probe.sh                                # probe default (claude-fable-5-1)
#   fable-probe.sh --model claude-fable-5         # probe specific model
#   fable-probe.sh --force                        # bypass cache
#   fable-probe.sh --model claude-fable-5 --force # both

set -euo pipefail

CACHE_DIR="$HOME/.claude/cache"
CACHE_FILE="$CACHE_DIR/fable-availability.json"
TODAY=$(date +%Y-%m-%d)
FORCE=0
MODEL="claude-fable-5-1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --model)
      [[ $# -ge 2 ]] || { echo "Error: --model requires a value" >&2; exit 1; }
      MODEL="$2"
      shift 2
      ;;
    --force)
      FORCE=1
      shift
      ;;
    *)
      echo "Error: unknown argument '$1'" >&2
      echo "Usage: fable-probe.sh [--model <id>] [--force]" >&2
      exit 1
      ;;
  esac
done

# Derive a human-friendly label from the model ID
if [[ "$MODEL" == "claude-fable-5-1" ]]; then
  LABEL="Fable 5.1"
  MATCH_PATTERN="fable-5-1"
  MATCH_ALT="fable-5.1"
  MATCH_EXCLUDE=""
elif [[ "$MODEL" == "claude-fable-5" ]]; then
  LABEL="Fable 5.0"
  MATCH_PATTERN="fable-5"
  MATCH_ALT="fable 5"
  MATCH_EXCLUDE="fable-5-1"
else
  LABEL="$MODEL"
  MATCH_PATTERN="fable"
  MATCH_ALT=""
  MATCH_EXCLUDE=""
fi

# Migrate old flat-schema cache to per-model keyed schema.
# The old format had top-level { date, available, reply, stderr }.
# The new format keys by model ID: { "claude-fable-5": { date, available, ... } }.
migrate_cache() {
  if [[ -f "$CACHE_FILE" ]]; then
    python3 -c "
import json, sys
try:
    with open('$CACHE_FILE') as f:
        d = json.load(f)
    if 'date' in d and 'available' in d:
        migrated = {'claude-fable-5': d}
        with open('$CACHE_FILE', 'w') as f:
            json.dump(migrated, f, indent=2)
            f.write('\n')
except Exception:
    pass
" 2>/dev/null || true
  fi
}

migrate_cache

# Cache hit: same-day definitive verdict for this model
if [[ $FORCE -eq 0 && -f "$CACHE_FILE" ]]; then
  cached=$(CACHE_FILE="$CACHE_FILE" TODAY="$TODAY" MODEL="$MODEL" python3 -c "
import json, os
try:
    with open(os.environ['CACHE_FILE']) as f:
        d = json.load(f)
    entry = d.get(os.environ['MODEL'], {})
    if entry.get('date') == os.environ['TODAY']:
        print('available' if entry.get('available') else 'unavailable')
except Exception:
    pass
" 2>/dev/null)
  if [[ "$cached" == "available" ]]; then
    echo "$LABEL available (cached $TODAY)"
    exit 0
  elif [[ "$cached" == "unavailable" ]]; then
    echo "$LABEL unavailable (cached $TODAY)—rerun with --force to re-probe"
    exit 1
  fi
fi

# One-turn self-report probe. Hermetic flags keep the synthetic session out
# of hooks and the tracker corpus; ANTHROPIC_API_KEY is unset so the probe
# bills to the subscription, not API credits. stderr is captured, not
# discarded—an undiagnosable empty reply is what poisoned the cache before.
probe_once() {
  local err_file reply
  err_file=$(mktemp)
  PROBE_STATUS=0
  reply=$(env -u ANTHROPIC_API_KEY claude --model "$MODEL" \
    -p "Reply with only the exact model id powering you, nothing else." \
    --max-turns 1 --output-format text \
    --safe-mode --no-session-persistence 2>"$err_file") || PROBE_STATUS=$?
  PROBE_REPLY="$reply"
  # grep exits 1 when stderr is empty (or every line is filtered). Under
  # `set -euo pipefail`, that normal condition must not abort a good probe.
  PROBE_STDERR=$(grep -v "^Permission allow rule" "$err_file" | head -c 500) || true
  rm -f "$err_file"
}

write_cache() {
  mkdir -p "$CACHE_DIR" 2>/dev/null || true
  CACHE_FILE="$CACHE_FILE" TODAY="$TODAY" MODEL="$MODEL" \
  PROBE_REPLY="$PROBE_REPLY" PROBE_STDERR="$PROBE_STDERR" \
  PROBE_AVAILABLE="$1" python3 -c "
import json, os
cache_file = os.environ['CACHE_FILE']
model = os.environ['MODEL']
try:
    with open(cache_file) as f:
        d = json.load(f)
except Exception:
    d = {}
d[model] = {
    'date': os.environ['TODAY'],
    'available': os.environ['PROBE_AVAILABLE'] == 'true',
    'reply': os.environ['PROBE_REPLY'][:200],
    'stderr': os.environ['PROBE_STDERR'][:200],
}
with open(cache_file, 'w') as f:
    json.dump(d, f, indent=2)
    f.write('\n')
" 2>/dev/null || echo "note: cache write failed—verdict not cached" >&2
}

is_denial() {
  local l
  l=$(printf '%s %s' "$PROBE_REPLY" "$PROBE_STDERR" | grep -v "^Permission allow rule" | tr '[:upper:]' '[:lower:]')
  [[ "$l" == *not_found* || "$l" == *"not found"* || \
     "$l" == *"no access"* || "$l" == *"permission denied"* || \
     "$l" == *"permission_error"* || \
     "$l" == *unauthorized* || "$l" == *"not authorized"* || \
     "$l" == *forbidden* || "$l" == *"invalid model"* ]]
}

# Boundary-safe model matching: ensures claude-fable-5-1 doesn't satisfy a
# claude-fable-5 probe (and vice versa).
is_match() {
  local lowered
  lowered=$(printf '%s' "$PROBE_REPLY" | tr '[:upper:]' '[:lower:]')
  if [[ -n "$MATCH_EXCLUDE" && "$lowered" == *"$MATCH_EXCLUDE"* ]]; then
    return 1
  fi
  if [[ "$lowered" == *"$MATCH_PATTERN"* ]]; then
    return 0
  fi
  if [[ -n "$MATCH_ALT" && "$lowered" == *"$MATCH_ALT"* ]]; then
    return 0
  fi
  return 1
}

echo "Probing $LABEL availability..." >&2
probe_once
# Retry only a genuinely indeterminate failure—an affirmative denial with an
# empty reply is already a verdict and doesn't warrant a second probe token.
if ! is_denial && { [[ $PROBE_STATUS -ne 0 ]] || [[ -z "$PROBE_REPLY" ]]; }; then
  echo "Probe reply empty—retrying once..." >&2
  sleep 5
  probe_once
fi

if [[ $PROBE_STATUS -eq 0 ]] && is_match; then
  write_cache true
  echo "$LABEL available (model reported: $PROBE_REPLY)"
  exit 0
elif [[ $PROBE_STATUS -eq 0 && -n "$PROBE_REPLY" ]]; then
  # Something answered, but it wasn't the model we asked for—check this before
  # is_denial so a cross-version answer isn't misclassified as an auth denial.
  write_cache false
  echo "$LABEL unavailable (another model answered: $PROBE_REPLY)"
  exit 1
elif is_denial; then
  write_cache false
  echo "$LABEL unavailable (denied: ${PROBE_STDERR:-$PROBE_REPLY})"
  exit 1
else
  echo "Probe error: claude CLI exited $PROBE_STATUS (diagnostic: ${PROBE_STDERR:-${PROBE_REPLY:-<none>}})"
  echo "Indeterminate—not cached. $LABEL may still be available; proceed via fable-exec.sh, which self-verifies."
  exit 2
fi
