#!/bin/bash
# Debug script to see what data Claude Code passes to hooks
# Run this once to inspect the JSON structure

INPUT=$(cat)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
LOG_FILE="/tmp/claude-hook-debug-${TIMESTAMP}.json"

echo "$INPUT" | jq '.' > "$LOG_FILE" 2>/dev/null || echo "$INPUT" > "$LOG_FILE"

# Also log to a combined file for easy viewing
echo "=== $(date) ===" >> /tmp/claude-hook-debug.log
echo "$INPUT" | jq '.' >> /tmp/claude-hook-debug.log 2>/dev/null || echo "$INPUT" >> /tmp/claude-hook-debug.log
echo "" >> /tmp/claude-hook-debug.log

exit 0
