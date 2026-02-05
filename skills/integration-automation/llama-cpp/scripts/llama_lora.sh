#!/bin/bash
# Run inference with a LoRA adapter loaded on top of a base GGUF model.
# Usage: llama_lora.sh <base.gguf|ollama-name> <lora.gguf> "prompt"
#
# The LoRA adapter is loaded dynamically — no merge step needed.
# This enables hot-swapping adapters for testing different fine-tunes.
#
# Examples:
#   llama_lora.sh base-model.gguf kothar-lora.gguf "Hello, I am Kothar."
#   llama_lora.sh cas/nous-hermes-2-mistral-7b-dpo lora.gguf "prompt"

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 3 ]; then
    echo "Usage: llama_lora.sh <base.gguf|ollama-name> <lora.gguf> \"prompt\"" >&2
    echo "" >&2
    echo "Environment:" >&2
    echo "  N_PREDICT   Max tokens to generate (default: 256)" >&2
    echo "  CTX         Context size (default: 4096)" >&2
    exit 1
fi

BASE="$1"
LORA="$2"
PROMPT="$3"
N_PREDICT="${N_PREDICT:-256}"
CTX="${CTX:-4096}"

# Resolve Ollama model name if not a file path
if [ ! -f "$BASE" ] && command -v ollama &>/dev/null; then
    RESOLVED=$("$SCRIPT_DIR/ollama_model_path.sh" "$BASE" 2>/dev/null) && BASE="$RESOLVED"
fi

if [ ! -f "$BASE" ]; then
    echo "Error: Base model not found: $BASE" >&2
    exit 1
fi

if [ ! -f "$LORA" ]; then
    echo "Error: LoRA adapter not found: $LORA" >&2
    exit 1
fi

echo "Base model: $BASE"
echo "LoRA adapter: $LORA"
echo "Tokens: $N_PREDICT"
echo ""

llama-cli \
    -m "$BASE" \
    --lora "$LORA" \
    -p "$PROMPT" \
    -n "$N_PREDICT" \
    --n-gpu-layers all \
    --ctx-size "$CTX" \
    --flash-attn on \
    --simple-io \
    --single-turn \
    --no-display-prompt
