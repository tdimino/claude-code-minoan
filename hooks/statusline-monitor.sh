#!/bin/bash
# StatusLine wrapper — pass through to ccstatusline for display
# Handoffs are handled by PreCompact, Stop, and SessionEnd hooks

# Read JSON from stdin and pass to ccstatusline
cat | ccstatusline
