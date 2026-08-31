#!/usr/bin/env bash
# Probe whether Claude Fable 5 is currently available on this account.
#
# Fable 5 has been permanently included in subscription plans since July 20,
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
# Cache: ~/.claude/cache/fable-availability.json, same-day TTL.
#
# Usage:
#   fable-probe.sh            # cached probe
#   fable-probe.sh --force    # bypass cache, probe live

set -euo pipefail

CACHE_DIR="$HOME/.claude/cache"
CACHE_FILE="$CACHE_DIR/fable-availability.json"
TODAY=$(date +%Y-%m-%d)
FORCE=0

[[ "${1:-}" == "--force" ]] && FORCE=1

# Cache hit: same-day definitive verdict
if [[ $FORCE -eq 0 && -f "$CACHE_FILE" ]]; then
  cached=$(CACHE_FILE="$CACHE_FILE" TODAY="$TODAY" python3 -c "
import json, os
try:
    with open(os.environ['CACHE_FILE']) as f:
        d = json.load(f)
    if d.get('date') == os.environ['TODAY']:
        print('available' if d.get('available') else 'unavailable')
except Exception:
    pass
" 2>/dev/null)
  if [[ "$cached" == "available" ]]; then
    echo "Fable 5 available (cached $TODAY)"
    exit 0
  elif [[ "$cached" == "unavailable" ]]; then
    echo "Fable 5 unavailable (cached $TODAY)—rerun with --force to re-probe"
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
  reply=$(env -u ANTHROPIC_API_KEY claude --model claude-fable-5 \
    -p "Reply with only the exact model id powering you, nothing else." \
    --max-turns 1 --output-format text \
    --safe-mode --no-session-persistence 2>"$err_file") || reply=""
  PROBE_REPLY="$reply"
  PROBE_STDERR=$(head -c 500 "$err_file")
  rm -f "$err_file"
}

write_cache() {
  # Best-effort, definitive verdicts only: a missing python3 or unwritable
  # dir must never override the verdict the live probe just established.
  mkdir -p "$CACHE_DIR" 2>/dev/null || true
  CACHE_FILE="$CACHE_FILE" TODAY="$TODAY" PROBE_REPLY="$PROBE_REPLY" \
  PROBE_STDERR="$PROBE_STDERR" PROBE_AVAILABLE="$1" python3 -c "
import json, os
with open(os.environ['CACHE_FILE'], 'w') as f:
    json.dump({
        'date': os.environ['TODAY'],
        'available': os.environ['PROBE_AVAILABLE'] == 'true',
        'reply': os.environ['PROBE_REPLY'][:200],
        'stderr': os.environ['PROBE_STDERR'][:200],
    }, f, indent=2)
    f.write('\n')
" 2>/dev/null || echo "note: cache write failed—verdict not cached" >&2
}

is_denial() {
  local l
  l=$(printf '%s %s' "$PROBE_REPLY" "$PROBE_STDERR" | tr '[:upper:]' '[:lower:]')
  [[ "$l" == *not_found* || "$l" == *"not found"* || \
     "$l" == *"no access"* || "$l" == *permission* || \
     "$l" == *unauthorized* || "$l" == *"not authorized"* || \
     "$l" == *forbidden* || "$l" == *"invalid model"* ]]
}

echo "Probing Fable 5 availability..." >&2
probe_once
# Retry only a genuinely indeterminate failure—an affirmative denial with an
# empty reply is already a verdict and doesn't warrant a second probe token.
if [[ -z "$PROBE_REPLY" ]] && ! is_denial; then
  echo "Probe reply empty—retrying once..." >&2
  sleep 5
  probe_once
fi

if [[ "$PROBE_REPLY" == *fable* ]]; then
  write_cache true
  echo "Fable 5 available (model reported: $PROBE_REPLY)"
  exit 0
elif is_denial; then
  # Affirmative denial from the CLI/API—Fable is genuinely off this account.
  write_cache false
  echo "Fable 5 unavailable (denied: ${PROBE_STDERR:-$PROBE_REPLY})"
  exit 1
elif [[ -n "$PROBE_REPLY" ]]; then
  # Something answered, and it wasn't Fable—a silent clamp is a definitive no.
  write_cache false
  echo "Fable 5 unavailable (another model answered: $PROBE_REPLY)"
  exit 1
else
  # Empty reply twice with no denial text: the probe itself failed. This is
  # indeterminate—do NOT cache, leave any prior verdict untouched.
  echo "Probe error: no reply from claude CLI (stderr: ${PROBE_STDERR:-<none>})"
  echo "Indeterminate—not cached. Fable may still be available; proceed via fable-exec.sh, which self-verifies."
  exit 2
fi
