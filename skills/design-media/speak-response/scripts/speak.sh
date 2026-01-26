#!/bin/bash
# Vocalize text using Qwen3-TTS
# Default: Oracle voice (cloned from Dune narrator)
# Usage: speak.sh "<text>" [output_file]
#        speak.sh --preset "<text>" [speaker] [instruction] [output_file]

set -e

SKILL_DIR="$(dirname "$0")/.."
ORACLE_REF="$SKILL_DIR/voices/oracle/reference.mp3"
ORACLE_TRANSCRIPT="$SKILL_DIR/voices/oracle/transcript.txt"

# Check for --preset flag (use CustomVoice preset speakers instead of oracle)
if [ "$1" = "--preset" ]; then
    shift
    TEXT="$1"
    SPEAKER="${2:-Ryan}"
    INSTRUCT="${3:-}"
    OUTPUT="${4:-/tmp/claude-speak-$$.wav}"

    if [ -z "$TEXT" ]; then
        echo "Error: No text provided" >&2
        exit 1
    fi

    # Generate with preset speaker
    if [ -n "$INSTRUCT" ]; then
        qwen-tts generate "$TEXT" -s "$SPEAKER" -i "$INSTRUCT" -o "$OUTPUT" 2>/dev/null
    else
        qwen-tts generate "$TEXT" -s "$SPEAKER" -o "$OUTPUT" 2>/dev/null
    fi
else
    # Default: Oracle voice (cloned)
    TEXT="$1"
    OUTPUT="${2:-/tmp/claude-speak-$$.wav}"

    if [ -z "$TEXT" ]; then
        echo "Error: No text provided" >&2
        exit 1
    fi

    if [ ! -f "$ORACLE_REF" ]; then
        echo "Error: Oracle reference audio not found: $ORACLE_REF" >&2
        echo "Falling back to preset speaker..." >&2
        qwen-tts generate "$TEXT" -s Ryan -o "$OUTPUT" 2>/dev/null
    else
        REF_TEXT=$(cat "$ORACLE_TRANSCRIPT")
        qwen-tts clone "$TEXT" "$ORACLE_REF" -r "$REF_TEXT" -o "$OUTPUT" 2>/dev/null
    fi
fi

# Play audio (macOS)
afplay "$OUTPUT" 2>/dev/null &

echo "Playing: $OUTPUT"
