#!/bin/bash
# Resolve an Ollama model name to its GGUF blob file path.
# Usage: ollama_model_path.sh <model-name>
# Example: ollama_model_path.sh qwen2.5:7b
#          ollama_model_path.sh cas/nous-hermes-2-mistral-7b-dpo:latest
# Output: /path/to/.ollama/models/blobs/sha256-<hash>

set -e

if [ $# -lt 1 ]; then
    echo "Usage: ollama_model_path.sh <model-name>" >&2
    echo "Example: ollama_model_path.sh qwen2.5:7b" >&2
    exit 1
fi

MODEL="$1"
OLLAMA_DIR="${OLLAMA_MODELS:-$HOME/.ollama/models}"

if [ ! -d "$OLLAMA_DIR" ]; then
    echo "Error: Ollama models directory not found: $OLLAMA_DIR" >&2
    echo "Is Ollama installed? Try: brew install ollama && ollama pull $MODEL" >&2
    exit 1
fi

# Parse model name into namespace/model:tag
if [[ "$MODEL" == *"/"* ]]; then
    NAMESPACE=$(echo "$MODEL" | cut -d'/' -f1)
    MODEL_TAG=$(echo "$MODEL" | cut -d'/' -f2)
else
    NAMESPACE="library"
    MODEL_TAG="$MODEL"
fi

if [[ "$MODEL_TAG" == *":"* ]]; then
    MODEL_NAME=$(echo "$MODEL_TAG" | cut -d':' -f1)
    TAG=$(echo "$MODEL_TAG" | cut -d':' -f2)
else
    MODEL_NAME="$MODEL_TAG"
    TAG="latest"
fi

MANIFEST="$OLLAMA_DIR/manifests/registry.ollama.ai/$NAMESPACE/$MODEL_NAME/$TAG"
if [ ! -f "$MANIFEST" ]; then
    echo "Error: Manifest not found: $MANIFEST" >&2
    echo "Available models:" >&2
    ollama list 2>/dev/null | tail -n +2 | awk '{print "  " $1}' >&2
    exit 1
fi

DIGEST=$(python3 -c "
import json, sys
with open(sys.argv[1]) as f:
    manifest = json.load(f)
for layer in manifest.get('layers', []):
    if layer.get('mediaType') == 'application/vnd.ollama.image.model':
        print(layer['digest'].replace(':', '-'))
        sys.exit(0)
print('ERROR: No model layer found', file=sys.stderr)
sys.exit(1)
" "$MANIFEST")

BLOB_PATH="$OLLAMA_DIR/blobs/$DIGEST"
if [ ! -f "$BLOB_PATH" ]; then
    echo "Error: Blob file not found: $BLOB_PATH" >&2
    exit 1
fi

echo "$BLOB_PATH"
