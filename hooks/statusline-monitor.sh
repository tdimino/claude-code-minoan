#!/bin/bash
# StatusLine wrapper - monitors context and triggers handoff at 5%
# Chains with existing ccstatusline for display

# Read JSON from stdin
INPUT=$(cat)

# Extract values from StatusLine JSON
REMAINING=$(echo "$INPUT" | grep -o '"remaining_percentage":[^,}]*' | cut -d':' -f2 | tr -d ' ')
SESSION_ID=$(echo "$INPUT" | grep -o '"session_id":"[^"]*"' | cut -d'"' -f4)

# State file to track if we've already triggered at this threshold
STATE_FILE="/tmp/claude-handoff-state-$$"

# Account for 16.5% autocompact buffer
# When remaining is 21.5%, actual free-until-compact is 5%
BUFFER=16.5
THRESHOLD=21.5  # 5% + 16.5% buffer

if [ -n "$REMAINING" ]; then
    # Check if below threshold and haven't triggered yet
    TRIGGERED=$(cat "$STATE_FILE" 2>/dev/null || echo "no")

    if [ "$(echo "$REMAINING < $THRESHOLD" | bc -l)" -eq 1 ] && [ "$TRIGGERED" != "yes" ]; then
        # Trigger handoff with session info
        export CLAUDE_SESSION_ID="$SESSION_ID"
        ~/.claude/hooks/session-handoff.sh 2>/dev/null &
        echo "yes" > "$STATE_FILE"
    fi
fi

# Pass through to existing ccstatusline
echo "$INPUT" | ccstatusline
