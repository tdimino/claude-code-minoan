#!/bin/bash
set -euo pipefail

PASS=0
FAIL=0
TOTAL=0

result() {
  TOTAL=$((TOTAL + 1))
  if [ "$1" = "PASS" ]; then
    PASS=$((PASS + 1))
    printf "  %-40s \033[32mPASS\033[0m\n" "$2"
  else
    FAIL=$((FAIL + 1))
    printf "  %-40s \033[31mFAIL\033[0m  %s\n" "$2" "${3:-}"
  fi
}

CDP_PID=""
cleanup() { [ -n "$CDP_PID" ] && kill "$CDP_PID" 2>/dev/null; wait "$CDP_PID" 2>/dev/null; }
trap cleanup EXIT INT TERM

echo "=== Obscura Smoke Tests ==="
echo ""

# 1. Binary check
if obscura --help >/dev/null 2>&1; then
  result PASS "binary responds to --help"
else
  result FAIL "binary responds to --help" "obscura not found or crashed"
fi

# 2. Checksum verification
BINARY="$HOME/tools/obscura/obscura"
CHECKSUM_FILE="$HOME/tools/obscura/obscura.sha256"
if [ -f "$CHECKSUM_FILE" ] && [ -f "$BINARY" ]; then
  expected=$(cat "$CHECKSUM_FILE" | awk '{print $1}')
  actual=$(shasum -a 256 "$BINARY" | awk '{print $1}')
  if [ "$expected" = "$actual" ]; then
    result PASS "SHA-256 checksum matches"
  else
    result FAIL "SHA-256 checksum matches" "expected=$expected actual=$actual"
  fi
else
  result FAIL "SHA-256 checksum matches" "binary or checksum file missing"
fi

# 3. Fetch basic — example.com title extraction
title=$(obscura fetch --quiet https://example.com --eval "document.title" 2>/dev/null || true)
if echo "$title" | grep -qi "example domain"; then
  result PASS "fetch + eval extracts page title"
else
  result FAIL "fetch + eval extracts page title" "got: $(echo "$title" | head -c 80)"
fi

# 4. Stealth active — navigator.webdriver should be undefined
webdriver=$(obscura fetch --stealth --quiet https://example.com --eval "String(navigator.webdriver)" 2>/dev/null || true)
if echo "$webdriver" | grep -q "undefined"; then
  result PASS "stealth hides navigator.webdriver"
else
  result FAIL "stealth hides navigator.webdriver" "got: $(echo "$webdriver" | head -c 80)"
fi

# 5. CDP server start/stop
PORT=9224
if lsof -i :"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  result FAIL "CDP server lifecycle" "port $PORT already in use"
else
  obscura serve --port "$PORT" --stealth >/dev/null 2>&1 &
  CDP_PID=$!
  sleep 2

  if kill -0 "$CDP_PID" 2>/dev/null; then
    version_json=$(curl -s "http://127.0.0.1:$PORT/json/version" 2>/dev/null || true)
    kill "$CDP_PID" 2>/dev/null || true
    wait "$CDP_PID" 2>/dev/null || true

    if echo "$version_json" | grep -qi "obscura\|browser"; then
      result PASS "CDP server lifecycle"
    else
      result FAIL "CDP server lifecycle" "/json/version returned: $(echo "$version_json" | head -c 80)"
    fi
  else
    result FAIL "CDP server lifecycle" "server process died immediately"
  fi
fi

# 6. Port isolation — 9224 should not be Chrome's 9222
if lsof -i :9222 -sTCP:LISTEN >/dev/null 2>&1; then
  proc_9222=$(lsof -i :9222 -sTCP:LISTEN | tail -1 | awk '{print $1}')
  if echo "$proc_9222" | grep -qi "obscura"; then
    result FAIL "port isolation (9224 vs 9222)" "obscura is on Chrome's port 9222"
  else
    result PASS "port isolation (9224 vs 9222)"
  fi
else
  result PASS "port isolation (9224 vs 9222)"
fi

echo ""
echo "=== Results: $PASS/$TOTAL passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
