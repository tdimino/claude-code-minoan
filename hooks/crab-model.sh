#!/bin/bash
# Output 🦀 + model name from Claude Code StatusLine JSON
INPUT=$(cat)
MODEL=$(echo "$INPUT" | python3 -c "
import sys,json
d=json.load(sys.stdin)
m=d.get('model','')
if isinstance(m,dict):
    print(m.get('display_name',m.get('id','')))
else:
    print(m)
" 2>/dev/null)
echo "🦀: ${MODEL:-unknown}"
