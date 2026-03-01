#!/bin/bash
# Serve Qwen3.5 models via llama-server with MoE-optimized settings.
# Tuned for Apple Silicon unified memory (M4 Max 36GB target).
#
# Usage: llama_serve_qwen35.sh [model] [extra-args...]
#
# Environment:
#   PORT     Server port (default: 8081)
#   CTX      Context size (default: 16384)
#   THINK    Enable thinking mode: 1=on (default), 0=off
#   KV_K     KV cache key type (default: q8_0)
#   KV_V     KV cache value type (default: q4_0)
#   MAX_GEN  Max generation tokens (default: 32768)
#
# Examples:
#   llama_serve_qwen35.sh                          # default: qwen3.5:35b-a3b
#   llama_serve_qwen35.sh qwen3.5:27b
#   THINK=0 CTX=8192 llama_serve_qwen35.sh         # non-thinking, shorter ctx
#   PORT=8082 llama_serve_qwen35.sh model.gguf      # custom port, direct path

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default model is Qwen3.5-35B-A3B
MODEL="${1:-qwen3.5:35b-a3b}"
shift 2>/dev/null || true

# Resolve Ollama model name if not a file path
if [ ! -f "$MODEL" ] && command -v ollama &>/dev/null; then
    RESOLVED=$("$SCRIPT_DIR/ollama_model_path.sh" "$MODEL" 2>/dev/null) && MODEL="$RESOLVED"
fi

if [ ! -f "$MODEL" ]; then
    echo "Error: Model not found: $MODEL" >&2
    echo "Try: ollama pull qwen3.5:35b-a3b" >&2
    exit 1
fi

PORT="${PORT:-8081}"
CTX="${CTX:-16384}"
THINK="${THINK:-1}"
KV_K="${KV_K:-q8_0}"
KV_V="${KV_V:-q4_0}"
MAX_GEN="${MAX_GEN:-32768}"

# Build reasoning args
REASONING_ARGS=()
if [ "$THINK" = "1" ]; then
    REASONING_ARGS+=(--reasoning-format deepseek)
    MODE_LABEL="thinking"
else
    MODE_LABEL="non-thinking"
fi

echo "=== Qwen3.5 llama-server ==="
echo "  Model:    $MODEL"
echo "  Port:     $PORT"
echo "  Context:  $CTX"
echo "  Mode:     $MODE_LABEL"
echo "  KV cache: keys=$KV_K values=$KV_V"
echo "  Max gen:  $MAX_GEN"
echo ""
echo "  API: http://localhost:$PORT/v1/chat/completions"
echo "  UI:  http://localhost:$PORT"
echo ""

exec llama-server \
    --model "$MODEL" \
    --port "$PORT" \
    --host "${HOST:-127.0.0.1}" \
    --n-gpu-layers all \
    --flash-attn on \
    --ctx-size "$CTX" \
    --predict "$MAX_GEN" \
    --split-mode row \
    --jinja \
    "${REASONING_ARGS[@]}" \
    --cache-type-k "$KV_K" \
    --cache-type-v "$KV_V" \
    --no-context-shift \
    "$@"
