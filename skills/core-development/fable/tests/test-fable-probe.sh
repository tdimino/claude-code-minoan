#!/usr/bin/env bash

set -euo pipefail

TEST_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
PROBE="$TEST_DIR/../scripts/fable-probe.sh"
TEST_ROOT=$(mktemp -d)
trap 'rm -r "$TEST_ROOT"' EXIT

mkdir -p "$TEST_ROOT/home"

assert_available_with_empty_stderr() {
  local model="$1" label="$2" output status

  set +e
  output=$(HOME="$TEST_ROOT/home" PATH="$TEST_DIR/fixtures:$PATH" \
    bash "$PROBE" --model "$model" --force 2>&1)
  status=$?
  set -e

  if [[ $status -ne 0 ]]; then
    echo "FAIL: $model returned $status" >&2
    echo "$output" >&2
    return 1
  fi
  if [[ "$output" != *"$label available (model reported: $model)"* ]]; then
    echo "FAIL: unexpected output for $model" >&2
    echo "$output" >&2
    return 1
  fi
}

assert_available_with_empty_stderr claude-fable-5-1 "Fable 5.1"
assert_available_with_empty_stderr claude-fable-5 "Fable 5.0"

CACHE_FILE="$TEST_ROOT/home/.claude/cache/fable-availability.json" python3 -c '
import json
import os

with open(os.environ["CACHE_FILE"]) as f:
    cache = json.load(f)

for model in ("claude-fable-5-1", "claude-fable-5"):
    assert cache[model]["available"] is True, cache
    assert cache[model]["reply"] == model, cache
'

echo "PASS: successful probes with empty stderr"
