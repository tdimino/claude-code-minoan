#!/bin/bash
# Start llama-server with Apple Silicon Metal defaults.
# Usage: llama_serve.sh <model.gguf|ollama-model-name> [extra-args...]
# Environment: PORT (default 8081), CTX (default 4096)
#
# Examples:
#   llama_serve.sh model.gguf
#   llama_serve.sh qwen2.5:7b
#   PORT=8082 CTX=8192 llama_serve.sh qwen2.5:7b

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 1 ]; then
    echo "Usage: llama_serve.sh <model.gguf|ollama-model-name> [extra-args...]" >&2
    echo "" >&2
    echo "Environment variables:" >&2
    echo "  PORT  Server port (default: 8081)" >&2
    echo "  CTX   Context size (default: 4096)" >&2
    exit 1
fi

MODEL="$1"
shift

# Resolve Ollama model name if not a file path
if [ ! -f "$MODEL" ] && command -v ollama &>/dev/null; then
    RESOLVED=$("$SCRIPT_DIR/ollama_model_path.sh" "$MODEL" 2>/dev/null) && MODEL="$RESOLVED"
fi

if [ ! -f "$MODEL" ]; then
    echo "Error: Model file not found: $MODEL" >&2
    exit 1
fi

PORT="${PORT:-8081}"
CTX="${CTX:-4096}"

echo "Starting llama-server..."
echo "  Model: $MODEL"
echo "  Port:  $PORT"
echo "  CTX:   $CTX"
echo "  GPU:   Full Metal offload"
echo ""
echo "API: http://localhost:$PORT/v1/chat/completions"
echo "Docs: http://localhost:$PORT"
echo ""

exec llama-server \
    --model "$MODEL" \
    --port "$PORT" \
    --n-gpu-layers all \
    --ctx-size "$CTX" \
    --flash-attn on \
    --host "${HOST:-127.0.0.1}" \
    "$@"
