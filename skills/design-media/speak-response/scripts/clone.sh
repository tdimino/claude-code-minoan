#!/bin/bash
# Clone a voice from an audio sample using Qwen3-TTS
# Usage: clone.sh "<text>" "<audio_file>" "<ref_text>" [output_file]

set -e

TEXT="$1"
AUDIO="$2"
REF_TEXT="$3"
OUTPUT="${4:-/tmp/claude-clone-$$.wav}"

if [ -z "$TEXT" ]; then
    echo "Error: No text provided" >&2
    exit 1
fi

if [ -z "$AUDIO" ]; then
    echo "Error: No audio file provided" >&2
    exit 1
fi

if [ ! -f "$AUDIO" ]; then
    echo "Error: Audio file not found: $AUDIO" >&2
    exit 1
fi

if [ -z "$REF_TEXT" ]; then
    echo "Error: Reference text (transcript of audio) required" >&2
    exit 1
fi

# Clone voice using Qwen3-TTS Base model
qwen-tts clone "$TEXT" "$AUDIO" -r "$REF_TEXT" -o "$OUTPUT" 2>/dev/null

# Play audio (macOS)
afplay "$OUTPUT" 2>/dev/null &

echo "Playing: $OUTPUT"
