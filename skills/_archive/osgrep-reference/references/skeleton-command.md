# Skeleton Command Reference

The `skeleton` command compresses code files to show only function and class signatures, providing an architectural overview without implementation details. This achieves ~85% token reduction while preserving structural information.

## Overview

Skeleton mode extracts the "shape" of code—function signatures, class definitions, and their relationships—without the implementation bodies. This is invaluable for:

- **Rapid codebase exploration** - Understand file structure in seconds
- **Token optimization** - View 10+ files in the space of one full file
- **Architectural analysis** - See relationships and complexity at a glance
- **Entry point identification** - Find orchestrator functions vs leaf definitions
- **Impact analysis** - Understand what a function calls before diving into implementation

## Command Syntax

```bash
osgrep skeleton <target> [options]
```

**Arguments:**
- `<target>` - Can be a file path, symbol name, or semantic search query

**Options:**
- `-l, --limit <n>` - Max files for query mode (default: 3)
- `--json` - Output as JSON for programmatic parsing
- `--no-summary` - Omit call/complexity summary in function bodies
- `-s, --sync` - Sync index before searching

## Three Modes of Operation

### 1. File Path Mode

**Use when:** You know the exact file and want to see its structure.

```bash
osgrep skeleton src/server.ts
osgrep skeleton pkg/handlers/auth.go
osgrep skeleton lib/database.py
```

**Output example:**
```python
# src/server.py (skeleton, ~157 tokens)
#!/usr/bin/env python3
"""Server module docstring"""

import sys
from pathlib import Path

def start_server(config_path, port=8080):

    # → load_config, init_db, start_http, print, ... | C:8 | ORCH
    ...

def stop_server():

    # → close_db, cleanup | C:3
    ...

if __name__ == "__main__":
    start_server(sys.argv[1])
```

**Output interpretation:**
- **# path/to/file.py (skeleton, ~N tokens)** - Header with file path and estimated token count
- **# → func1, func2, ... | C:N | ROLE** - Summary line inside function body showing:
  - **→ [calls]** - Functions/methods this code invokes
  - **C:N** - Complexity score (cyclomatic complexity approximation)
  - **ORCH** - Orchestrator role (coordinates multiple operations)
- **...** - Implementation body omitted for token efficiency

### 2. Symbol Name Mode

**Use when:** You want to see a specific function/class and its context.

```bash
osgrep skeleton handleRequest
osgrep skeleton UserController
osgrep skeleton authenticateUser
```

**Behavior:**
- Searches for the symbol across the codebase
- Shows the file containing that symbol in skeleton mode
- Highlights the target symbol in context

**Example workflow:**
```bash
# Find where processPayment is defined
osgrep skeleton processPayment

# Output shows the entire file structure with processPayment highlighted
```

### 3. Search Query Mode

**Use when:** You want architectural overview of files related to a concept.

```bash
osgrep skeleton "authentication logic" -l 5
osgrep skeleton "database connection handling" -l 3
osgrep skeleton "API rate limiting"
```

**Behavior:**
- Performs semantic search for the query
- Returns skeleton view of top N matching files (default: 3)
- Sorted by relevance

**Example workflow:**
```bash
# Understand how webhooks are structured across the codebase
osgrep skeleton "webhook processing" -l 4

# Shows signatures from 4 most relevant files
# Reveals: entry points, helper functions, data flow
```

## Understanding Output Indicators

### Complexity Score (C:N)

**C:1-3** - Simple, straightforward logic
- Single responsibility
- Few branches or loops
- Good candidates for inline expansion

**C:4-7** - Moderate complexity
- Multiple conditional paths
- Some nested logic
- Typical business logic

**C:8+** - High complexity
- Many branches, loops, or conditions
- May need refactoring
- Read full implementation carefully

### Role Indicators

**ORCH** (Orchestrator)
- Coordinates multiple operations
- High-level workflow control
- Entry points to features
- Often calls 3+ other functions

**No role indicator** - Simpler function without orchestration role

### Call Information

**→ func1, func2, ...** - Shows direct function calls within the implementation, revealing:
- **Dependencies** - What this code relies on
- **Control flow** - Sequence of operations
- **Integration points** - External APIs or modules used

## Common Workflows

### Workflow 1: Learning a New Codebase

```bash
# Step 1: Get overview of main entry points
osgrep skeleton "application startup initialization"

# Step 2: Examine key files
osgrep skeleton src/main.py
osgrep skeleton src/app.ts

# Step 3: Understand specific subsystems
osgrep skeleton "user authentication flow" -l 3
osgrep skeleton "database query handling" -l 3

# Result: Architectural map without drowning in implementation details
```

### Workflow 2: Impact Analysis for Refactoring

```bash
# Goal: Refactor getUserData() safely
# Step 1: See what getUserData does
osgrep skeleton getUserData

# Step 2: Find who calls it (use trace command)
osgrep trace getUserData

# Step 3: Check complexity of calling functions
osgrep skeleton src/api/users.ts

# Result: Understand blast radius before making changes
```

### Workflow 3: Finding Entry Points

```bash
# Find orchestrator functions for a feature
osgrep skeleton "payment processing" -l 3

# Look for high C: scores with ORCH indicator
# These are your entry points

# Example output:
# def process_payment(order_id, amount):
#     # → validate, charge_card, notify, log | C:12 | ORCH
#     ...
# └─ This is the entry point!
```

### Workflow 4: Code Review Preparation

```bash
# Before reviewing a PR, get architectural context
osgrep skeleton src/features/notifications/

# Understand:
# - How many functions are involved
# - Complexity distribution
# - Dependencies between functions
# - Which functions are orchestrators vs workers
```

### Workflow 5: Token-Efficient Multi-File Analysis

```bash
# Bad: Reading 5 full files (15,000+ tokens)
Read src/auth/login.ts
Read src/auth/register.ts
Read src/auth/reset.ts
Read src/auth/verify.ts
Read src/auth/session.ts

# Good: Skeleton view of 5 files (~2,500 tokens)
osgrep skeleton "user authentication" -l 5

# Result: 85% token savings, full structural context
```

## Advanced Usage

### JSON Output for Scripting

```bash
osgrep skeleton src/api.py --json > structure.json
```

**JSON structure:**
```json
{
  "success": true,
  "skeleton": "# src/api.py (skeleton, ~157 tokens)\n...full skeleton output...",
  "tokens": 157
}
```

**Use cases:**
- Programmatic parsing of skeleton output
- Build custom analysis tools
- Integration with other tooling

### Combining with Other Commands

```bash
# Pattern: Search → Skeleton → Read
osgrep "webhook validation"          # Find relevant files
osgrep skeleton src/webhooks/        # See structure
Read src/webhooks/validator.ts       # Deep dive on key function

# Pattern: Skeleton → Trace → Read
osgrep skeleton "payment processing"  # Find entry points
osgrep trace processPayment           # See call graph
Read src/payments/processor.ts        # Understand implementation
```

### Filtering with --no-summary

```bash
# Standard output includes call/complexity summary
osgrep skeleton src/server.py
# def start_server():
#     # → load_config, init_db, start_http | C:8 | ORCH
#     ...

# Minimal output without summaries
osgrep skeleton src/server.py --no-summary
# def start_server():
#     ...
```

**Use --no-summary when:**
- You only need signatures, not call information
- Maximizing token savings
- Output is too verbose

## When NOT to Use Skeleton

❌ **Markdown/text files** - No tree-sitter grammar, will fall back to truncated view

❌ **Implementation details needed** - Skeleton omits function bodies; use `Read` instead

❌ **Configuration files** - JSON/YAML/TOML don't benefit from skeleton view

❌ **Small files (<100 lines)** - Reading the full file is often more efficient

❌ **Data files** - CSV, logs, etc. need full content

## When to Use Each Tool

**Use Skeleton for:**
- Understanding file structure
- Seeing function signatures
- Analyzing architecture
- Finding entry points
- Token-efficient multi-file analysis

**Use Search for:**
- Finding relevant files
- Finding entry points
- Conceptual/semantic queries

**Use Read for:**
- Reading full implementation details
- Seeing function signatures (partial)
- Configuration files
- Small files

## Best Practices

1. **Start broad, narrow down** - Use query mode first, then file mode
2. **Look for ORCH functions** - These are architectural entry points
3. **Check complexity scores** - High C: values warrant full `Read`
4. **Combine with trace** - Skeleton shows structure, trace shows relationships
5. **Use limit wisely** - Default of 3 files is usually sufficient
6. **Watch token counts** - Header shows estimated tokens per file
7. **Don't skip full reads** - Skeleton is for triage, not replacement

## Troubleshooting

**"Skeleton unavailable: No TreeSitter grammar for [language]"**
- Language not supported yet (markdown, plain text, etc.)
- Falls back to showing first 30 lines
- Use `Read` instead

**Empty or minimal output**
- File may be very small or simple
- Check if file is actually code (not config/data)
- Try reading the full file instead

**Too many files in query mode**
- Reduce with `-l` flag: `osgrep skeleton "query" -l 2`
- Make query more specific
- Switch to file path mode if you know the file

**Missing complexity/role indicators**
- Function may be too simple to classify
- Language-specific limitations
- Not a problem—signatures are still shown

## Performance Notes

- **Token savings**: ~85% reduction vs full file read
- **Speed**: Instant (uses indexed data)
- **Limit**: No practical limit on file size
- **Languages**: Best support for Python, JavaScript, TypeScript, Go, Java, C++
