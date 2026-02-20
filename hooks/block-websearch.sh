#!/bin/bash
cat >&2 << 'EOF'
BLOCKED: WebSearch is disabled.

Use the exa-search skill instead:
- Activate: /exa-search

Exa provides neural search, category filtering, and domain filtering.
EOF
exit 2
