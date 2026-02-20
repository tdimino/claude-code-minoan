#!/bin/bash
cat >&2 << 'EOF'
BLOCKED: WebFetch is disabled.

Use the Firecrawl skill instead:
- Activate: /Firecrawl

Firecrawl produces cleaner markdown and handles JavaScript better.
EOF
exit 2
