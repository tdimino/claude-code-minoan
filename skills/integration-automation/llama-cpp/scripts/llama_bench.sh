#!/bin/bash
# Benchmark a model: llama.cpp vs Ollama tok/s comparison.
# Usage: llama_bench.sh <ollama-model-name>
# Example: llama_bench.sh qwen2.5:7b

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ $# -lt 1 ]; then
    echo "Usage: llama_bench.sh <ollama-model-name>" >&2
    echo "Example: llama_bench.sh qwen2.5:7b" >&2
    exit 1
fi

MODEL_NAME="$1"
PROMPT="Explain the theory of general relativity in three paragraphs."
N_PREDICT=128
TMPFILE=$(mktemp /tmp/llama-bench-XXXXXX)
trap "rm -f '$TMPFILE'" EXIT

echo "============================================"
echo "  llama.cpp vs Ollama Benchmark"
echo "  Model: $MODEL_NAME"
echo "  Tokens: $N_PREDICT"
echo "============================================"
echo ""

# Resolve GGUF path
GGUF=$("$SCRIPT_DIR/ollama_model_path.sh" "$MODEL_NAME")
echo "GGUF: $GGUF"
echo ""

# --- llama.cpp benchmark ---
echo "--- llama.cpp (Metal, full offload) ---"
# --single-turn: generate one response then exit (prevents interactive mode hang)
# --simple-io: suppress ANSI spinner that floods redirected output
# --show-timings: outputs [ Prompt: X t/s | Generation: Y t/s ] to stdout (default: on)
llama-cli \
    -m "$GGUF" \
    -p "$PROMPT" \
    -n "$N_PREDICT" \
    --n-gpu-layers all \
    --no-display-prompt \
    --single-turn \
    --simple-io \
    >"$TMPFILE" 2>/dev/null

# Parse inline timing from stdout: [ Prompt: 371.2 t/s | Generation: 81.2 t/s ]
PP_SPEED=$(grep -o 'Prompt: [0-9.]\+ t/s' "$TMPFILE" | head -1 | sed 's/Prompt: //')
TG_SPEED=$(grep -o 'Generation: [0-9.]\+ t/s' "$TMPFILE" | head -1 | sed 's/Generation: //')

echo "  Prompt processing: ${PP_SPEED:-?}"
echo "  Token generation:  ${TG_SPEED:-?}"
echo ""

# --- Ollama benchmark ---
echo "--- Ollama ---"
# Warm up model via API (avoids interactive mode hang)
curl -s http://localhost:11434/api/generate \
    -d "{\"model\":\"$MODEL_NAME\",\"prompt\":\"\",\"options\":{\"num_predict\":1}}" &>/dev/null || true

OLLAMA_STATS=$(curl -s http://localhost:11434/api/generate \
    -d "{\"model\":\"$MODEL_NAME\",\"prompt\":\"$PROMPT\",\"stream\":false,\"options\":{\"num_predict\":$N_PREDICT}}" 2>/dev/null)

OLLAMA_PP_RATE=$(echo "$OLLAMA_STATS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
dur=d.get('prompt_eval_duration',0)
count=d.get('prompt_eval_count',1)
print(f'{count/(dur/1e9):.1f} t/s ({count} tokens)' if dur>0 else '?')
" 2>/dev/null || echo "?")

OLLAMA_TG_RATE=$(echo "$OLLAMA_STATS" | python3 -c "
import json,sys
d=json.load(sys.stdin)
dur=d.get('eval_duration',0)
count=d.get('eval_count',1)
print(f'{count/(dur/1e9):.1f} t/s ({count} tokens in {dur/1e9:.2f}s)' if dur>0 else '?')
" 2>/dev/null || echo "?")

echo "  Prompt processing: ${OLLAMA_PP_RATE:-?}"
echo "  Token generation:  ${OLLAMA_TG_RATE:-?}"
echo ""

echo "============================================"
echo "  Benchmark complete"
echo "============================================"
