#!/bin/bash
set -e

PORT=9224
GLOBAL_ARGS=()
SERVE_ARGS=(serve --port "$PORT")

for arg in "$@"; do
  case "$arg" in
    --with-proxelar)
      if lsof -i :8080 -sTCP:LISTEN 2>/dev/null | grep -q proxelar; then
        GLOBAL_ARGS+=(--proxy "http://127.0.0.1:8080")
        echo "Chaining through Proxelar on :8080"
      else
        echo "Warning: Proxelar not running on :8080, starting without proxy"
      fi
      ;;
    --stealth)
      SERVE_ARGS+=(--stealth)
      ;;
  esac
done

if lsof -i :"$PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "Port $PORT already in use"
  exit 1
fi

cleanup() {
  if [[ -n "${PID:-}" ]] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    rm -f /tmp/obscura-cdp.pid
  fi
}
trap cleanup EXIT INT TERM

obscura "${GLOBAL_ARGS[@]}" "${SERVE_ARGS[@]}" &
PID=$!
echo "$PID" > /tmp/obscura-cdp.pid
sleep 1

if kill -0 "$PID" 2>/dev/null; then
  echo "Obscura CDP server running (PID $PID)"
  echo "WebSocket: ws://127.0.0.1:$PORT/devtools/browser"
else
  echo "Failed to start Obscura"
  exit 1
fi

wait "$PID"
