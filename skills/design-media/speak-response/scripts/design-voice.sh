#!/bin/bash
# Design a voice from natural language description using Qwen3-TTS VoiceDesign
# Usage: design-voice.sh "<sample_text>" "<voice_description>" [output_file]
#
# The voice description can include:
#   - Gender/Age: "young female", "elderly male", "androgynous"
#   - Tone: "warm", "cold", "mysterious", "friendly"
#   - Pace: "slow and deliberate", "rapid", "measured"
#   - Quality: "deep", "resonant", "breathy", "raspy"
#   - Style: "prophetic", "nurturing", "commanding", "playful"
#
# Example:
#   design-voice.sh "He was warrior and mystic." "deep, resonant, mysterious, prophetic"

set -e

TEXT="$1"
DESCRIPTION="$2"
OUTPUT="${3:-/tmp/designed-voice-$$.wav}"

if [ -z "$TEXT" ]; then
    echo "Error: No sample text provided" >&2
    echo "Usage: design-voice.sh \"<sample_text>\" \"<voice_description>\" [output_file]" >&2
    exit 1
fi

if [ -z "$DESCRIPTION" ]; then
    echo "Error: No voice description provided" >&2
    echo "Usage: design-voice.sh \"<sample_text>\" \"<voice_description>\" [output_file]" >&2
    exit 1
fi

# Generate designed voice using Qwen3-TTS VoiceDesign model
# design.py takes positional args: text instruct
echo "Designing voice: $DESCRIPTION" >&2
qwen-tts design "$TEXT" "$DESCRIPTION" -o "$OUTPUT" 2>/dev/null

echo "Designed voice saved to: $OUTPUT"
echo ""
echo "To clone this voice for new text:"
echo "  clone.sh \"new text here\" \"$OUTPUT\" \"$TEXT\""
