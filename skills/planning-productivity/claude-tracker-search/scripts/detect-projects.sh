#!/usr/bin/env bash
# Detect all projects across Claude Code sessions
# Outputs JSON for further processing
exec node "$(dirname "$0")/detect-projects.js" "$@"
