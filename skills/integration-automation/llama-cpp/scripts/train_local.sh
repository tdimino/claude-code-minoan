#!/bin/bash
# Local LoRA training with llama.cpp finetune
#
# Usage: train_local.sh <base.gguf|ollama-name> <train.txt> [output-lora.bin]
#
# Environment:
#   ADAM_ITER  Optimization iterations (default: 512)
#   THREADS    CPU threads (default: auto-detect)
#   BATCH      Batch size (default: 4)
#   CTX        Context length (default: 2048)
#   LORA_R     LoRA rank (default: 16)
#   LORA_ALPHA LoRA alpha (default: 32)
#
# Examples:
#   # Train with Ollama model (auto-resolves to GGUF path)
#   ./scripts/train_local.sh qwen2.5:7b output/train.txt
#
#   # Train with explicit GGUF path
#   ./scripts/train_local.sh ~/.ollama/models/blobs/sha256-xxx output/train.txt kothar-lora.bin
#
#   # High-rank LoRA for better capacity
#   LORA_R=64 LORA_ALPHA=128 ./scripts/train_local.sh qwen2.5:7b output/train.txt

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$HOME/.claude/skills/llama-cpp/scripts"

# Arguments
BASE="$1"
TRAIN="$2"
OUTPUT="${3:-lora.bin}"

# Environment defaults
ADAM_ITER="${ADAM_ITER:-512}"
THREADS="${THREADS:-$(sysctl -n hw.ncpu 2>/dev/null || nproc 2>/dev/null || echo 4)}"
BATCH="${BATCH:-4}"
CTX="${CTX:-2048}"
LORA_R="${LORA_R:-16}"
LORA_ALPHA="${LORA_ALPHA:-32}"

if [ -z "$BASE" ] || [ -z "$TRAIN" ]; then
    echo "Usage: train_local.sh <base.gguf|ollama-name> <train.txt> [output-lora.bin]"
    echo ""
    echo "Environment variables:"
    echo "  ADAM_ITER  Optimization iterations (default: 512)"
    echo "  THREADS    CPU threads (default: auto-detect)"
    echo "  BATCH      Batch size (default: 4)"
    echo "  CTX        Context length (default: 2048)"
    echo "  LORA_R     LoRA rank (default: 16)"
    echo "  LORA_ALPHA LoRA alpha (default: 32)"
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
    echo "Provide a valid GGUF file path or Ollama model name" >&2
    exit 1
fi

if [ ! -f "$TRAIN" ]; then
    echo "Error: Training data not found: $TRAIN" >&2
    exit 1
fi

# Check for finetune binary
if ! command -v finetune &>/dev/null; then
    echo "Error: llama.cpp 'finetune' binary not found" >&2
    echo "Install with: brew install llama.cpp" >&2
    exit 1
fi

# Calculate samples count
SAMPLE_COUNT=$(grep -o '<SFT>' "$TRAIN" 2>/dev/null | wc -l | tr -d ' ')
SAMPLE_COUNT=$((SAMPLE_COUNT + 1))  # Add 1 for the first sample (no leading delimiter)

echo "════════════════════════════════════════════════════════════════"
echo "  Kothar Local LoRA Training (llama.cpp finetune)"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Base model:    $BASE"
echo "Training data: $TRAIN ($SAMPLE_COUNT samples)"
echo "Output:        $OUTPUT"
echo ""
echo "Hyperparameters:"
echo "  Iterations:  $ADAM_ITER"
echo "  Threads:     $THREADS"
echo "  Batch size:  $BATCH"
echo "  Context:     $CTX"
echo "  LoRA rank:   $LORA_R"
echo "  LoRA alpha:  $LORA_ALPHA"
echo ""
echo "Starting training... (this may take hours for large datasets)"
echo ""

# Run finetune
# Note: llama.cpp finetune uses --adam-iter for optimization steps
# Loss should drop below 0.1 for good convergence
time finetune \
    --model-base "$BASE" \
    --train-data "$TRAIN" \
    --lora-out "$OUTPUT" \
    --sample-start '<SFT>' \
    --threads "$THREADS" \
    --batch "$BATCH" \
    --ctx-size "$CTX" \
    --lora-r "$LORA_R" \
    --lora-alpha "$LORA_ALPHA" \
    --adam-iter "$ADAM_ITER"

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "  Training complete!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Output: $OUTPUT"
echo ""
echo "Next steps:"
echo "  1. Test with hot-loaded LoRA:"
echo "     $SKILL_DIR/llama_lora.sh '$BASE' '$OUTPUT' 'Hello Kothar'"
echo ""
echo "  2. Merge into GGUF for production:"
echo "     python3 $SKILL_DIR/convert_lora_to_gguf.py \\"
echo "       --base '$BASE' --lora '$OUTPUT' --output kothar-merged.gguf --quantize q4_k_m"
