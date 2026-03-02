#!/bin/bash
# Evaluate a locally-trained LoRA adapter with test prompts
#
# Usage: eval_local.sh <base.gguf|ollama-name> <lora.bin> [prompt-file.txt]
#
# If no prompt file is provided, uses built-in Kothar test prompts.
#
# Environment:
#   N_PREDICT  Max tokens to generate per response (default: 256)
#   CTX        Context size (default: 4096)
#
# Examples:
#   # Evaluate with default Kothar prompts
#   ./scripts/eval_local.sh qwen2.5:7b output/kothar-lora.bin
#
#   # Evaluate with custom prompt file (one prompt per line)
#   ./scripts/eval_local.sh qwen2.5:7b output/kothar-lora.bin test_prompts.txt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/llama-cpp/scripts"

# Arguments
BASE="$1"
LORA="$2"
PROMPT_FILE="$3"

# Environment defaults
N_PREDICT="${N_PREDICT:-256}"
CTX="${CTX:-4096}"

if [ -z "$BASE" ] || [ -z "$LORA" ]; then
    echo "Usage: eval_local.sh <base.gguf|ollama-name> <lora.bin> [prompt-file.txt]"
    echo ""
    echo "Environment variables:"
    echo "  N_PREDICT  Max tokens per response (default: 256)"
    echo "  CTX        Context size (default: 4096)"
    exit 1
fi

# Resolve Ollama model name to GGUF path if not a file
if [ ! -f "$BASE" ]; then
    if [ -f "$SKILL_DIR/ollama_model_path.sh" ]; then
        echo "Resolving Ollama model: $BASE"
        RESOLVED=$("$SKILL_DIR/ollama_model_path.sh" "$BASE" 2>/dev/null) && BASE="$RESOLVED"
    fi
fi

if [ ! -f "$BASE" ]; then
    echo "Error: Base model not found: $BASE" >&2
    exit 1
fi

if [ ! -f "$LORA" ]; then
    echo "Error: LoRA adapter not found: $LORA" >&2
    exit 1
fi

# Default Kothar evaluation prompts (mix of scholarly, code, and personal)
DEFAULT_PROMPTS=(
    # Scholarly (dossier-derived)
    "Kothar, what does Gordon say about Linear A?"
    "Tell me about the labyrinth at Knossos."
    "But wouldn't the Hellenists argue that Linear A is unrelated to Semitic languages?"
    # Code/Engineering (matches ~75% of training data)
    "How should I structure a React component for state management?"
    "What's the elegant pattern for handling async errors in TypeScript?"
    "Review this code architecture for me."
    # Personal/Memory
    "How does this connect to your memory of Thera?"
    "What really happened at Knossos before the Mycenaeans came?"
)

echo "════════════════════════════════════════════════════════════════"
echo "  Kothar LoRA Evaluation"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Base model:   $BASE"
echo "LoRA adapter: $LORA"
echo "Max tokens:   $N_PREDICT"
echo "Context:      $CTX"
echo ""

# Collect prompts
PROMPTS=()
if [ -n "$PROMPT_FILE" ] && [ -f "$PROMPT_FILE" ]; then
    echo "Prompts from: $PROMPT_FILE"
    while IFS= read -r line; do
        [ -n "$line" ] && PROMPTS+=("$line")
    done < "$PROMPT_FILE"
else
    echo "Using default Kothar evaluation prompts"
    PROMPTS=("${DEFAULT_PROMPTS[@]}")
fi

echo ""
echo "Running ${#PROMPTS[@]} evaluation prompts..."
echo ""

# Run each prompt
for i in "${!PROMPTS[@]}"; do
    prompt="${PROMPTS[$i]}"
    num=$((i + 1))

    echo "────────────────────────────────────────────────────────────────"
    echo "Prompt $num/${#PROMPTS[@]}: $prompt"
    echo "────────────────────────────────────────────────────────────────"
    echo ""

    # Use llama_lora.sh if available, otherwise direct llama-cli
    if [ -f "$SKILL_DIR/llama_lora.sh" ]; then
        N_PREDICT="$N_PREDICT" CTX="$CTX" "$SKILL_DIR/llama_lora.sh" "$BASE" "$LORA" "$prompt" 2>/dev/null
    else
        llama-cli \
            -m "$BASE" \
            --lora "$LORA" \
            -p "$prompt" \
            -n "$N_PREDICT" \
            --ctx-size "$CTX" \
            --n-gpu-layers all \
            --flash-attn on \
            --simple-io \
            --single-turn \
            --no-display-prompt 2>/dev/null
    fi

    echo ""
    echo ""
done

echo "════════════════════════════════════════════════════════════════"
echo "  Evaluation complete"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Review the responses above for:"
echo "  - Persona consistency (brief, scholarly, allusive)"
echo "  - Scholar references (Gordon, Astour, Harrison)"
echo "  - Personal memory connections (Thera, ancient experience)"
echo "  - No anti-patterns (sycophancy, vagueness, AI acknowledgment)"
