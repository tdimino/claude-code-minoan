#!/usr/bin/env bash
# Probe whether Claude Fable 5 is currently available on this account.
#
# Replaces the old hardcoded date gate—Anthropic's availability window
# has shifted twice (paused June 2026, restored July 1, extended to July 19),
# so availability must be tested empirically, never assumed from a calendar.
#
# Verdict is cached in ~/.claude/cache/fable-availability.json with a
# same-day TTL so repeated /fable invocations don't burn probe tokens.
#
# Usage:
#   fable-probe.sh            # cached probe (exit 0 = available, 1 = not)
#   fable-probe.sh --force    # bypass cache, probe live

set -euo pipefail

CACHE_DIR="$HOME/.claude/cache"
CACHE_FILE="$CACHE_DIR/fable-availability.json"
TODAY=$(date +%Y-%m-%d)
FORCE=0

[[ "${1:-}" == "--force" ]] && FORCE=1

# Cache hit: same-day verdict
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

# Live probe: one-turn self-report. Unset ANTHROPIC_API_KEY so the probe
# bills to the subscription, not API credits.
echo "Probing Fable 5 availability..." >&2
reply=$(env -u ANTHROPIC_API_KEY claude --model claude-fable-5 \
  -p "Reply with only the exact model id powering you, nothing else." \
  --max-turns 1 --output-format text 2>/dev/null) || reply=""

if [[ "$reply" == *fable* ]]; then
  available=true
  status=0
  echo "Fable 5 available (model reported: $reply)"
else
  available=false
  status=1
  echo "Fable 5 unavailable (reply: ${reply:-<error>})"
fi

# Cache write is best-effort: a missing python3 or unwritable dir must
# never override the verdict the live probe just established.
mkdir -p "$CACHE_DIR" 2>/dev/null || true
CACHE_FILE="$CACHE_FILE" TODAY="$TODAY" PROBE_REPLY="$reply" PROBE_AVAILABLE="$available" python3 -c "
import json, os
with open(os.environ['CACHE_FILE'], 'w') as f:
    json.dump({
        'date': os.environ['TODAY'],
        'available': os.environ['PROBE_AVAILABLE'] == 'true',
        'reply': os.environ['PROBE_REPLY'][:200],
    }, f, indent=2)
    f.write('\n')
" 2>/dev/null || echo "note: cache write failed—verdict not cached" >&2
exit $status
