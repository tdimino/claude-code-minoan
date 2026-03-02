#!/bin/bash
# Serve Qwen3.5-9B via llama-server. Dense 9B model, optimized for 24-36GB systems.
# Tuned for Apple Silicon unified memory (M4 Max 36GB target).
#
# Usage: llama_serve_qwen35_9b.sh [model] [extra-args...]
#
# Environment:
#   PORT     Server port (default: 8081)
#   CTX      Context size (default: 32768)
#   THINK    Enable thinking mode: 1=on (default), 0=off
#   KV_K     KV cache key type (default: q8_0)
#   KV_V     KV cache value type (default: q4_0)
#   MAX_GEN  Max generation tokens (default: 32768)
#
# Examples:
#   llama_serve_qwen35_9b.sh                                    # default: qwen3.5:9b
#   llama_serve_qwen35_9b.sh ~/models/Qwen3.5-9B-BF16.gguf     # full precision F16
#   THINK=0 CTX=8192 llama_serve_qwen35_9b.sh                   # non-thinking, shorter ctx
#   PORT=8082 llama_serve_qwen35_9b.sh model.gguf               # custom port, direct path

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Default model is Qwen3.5-9B (dense, 6.6GB Q4_K_M via Ollama)
MODEL="${1:-qwen3.5:9b}"
shift 2>/dev/null || true

# Resolve Ollama model name if not a file path
if [ ! -f "$MODEL" ] && command -v ollama &>/dev/null; then
    RESOLVED=$("$SCRIPT_DIR/ollama_model_path.sh" "$MODEL" 2>/dev/null) && MODEL="$RESOLVED"
fi

if [ ! -f "$MODEL" ]; then
    echo "Error: Model not found: $MODEL" >&2
    echo "Try: ollama pull qwen3.5:9b" >&2
    exit 1
fi

PORT="${PORT:-8081}"
CTX="${CTX:-32768}"
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

echo "=== Qwen3.5-9B llama-server ==="
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
