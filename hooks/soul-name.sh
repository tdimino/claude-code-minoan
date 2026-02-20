#!/bin/bash
# Display soul name from Claudicle config
# Reads CLAUDICLE_SOUL_NAME env var, defaults to "Claudius"
cat > /dev/null  # consume stdin
SOUL_NAME="${CLAUDICLE_SOUL_NAME:-${CLAUDIUS_SOUL_NAME:-Claudius}}"
echo "$SOUL_NAME"
