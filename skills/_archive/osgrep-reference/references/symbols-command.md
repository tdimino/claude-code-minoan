# Symbols Command Reference

The `symbols` command lists all indexed symbols (functions, methods, classes) with their definitions, providing a browsable catalog of the codebase's API surface. This is invaluable for discovery, navigation, and understanding what's available.

## Overview

Symbols provides a comprehensive directory of all named entities in your codebase:

- **Functions** - Top-level and nested functions
- **Methods** - Class and object methods
- **Classes** - Class definitions
- **Interfaces/Types** - Type definitions (language-dependent)

**Key use cases:**
- **API discovery** - "What functions are available?"
- **Naming exploration** - "Is there already a function called X?"
- **Module browsing** - "What's exported from this directory?"
- **Codebase inventory** - "How many functions does this project have?"
- **Convention checking** - "Do we follow naming patterns?"
- **Quick navigation** - Find and jump to definitions

## Command Syntax

```bash
osgrep symbols [pattern] [options]
```

**Arguments:**
- `[pattern]` - Optional filter pattern to match symbol names (case-insensitive substring match)

**Options:**
- `-l, --limit <number>` - Max symbols to display (default: 20)
- `-p, --path <prefix>` - Filter to symbols under specific path
- `-h, --help` - Show help

## Output Format

```
Project: /path/to/project
Symbol                  Count  Path:Line
----------------------  -----  ------------------------------------------------------
handleUserLogin             1  src/auth/login.ts:15
UserController              1  src/api/users.ts:23
validateEmail               2  src/utils/validators.ts:42
processPayment              1  src/payments/process.ts:8
connectDatabase             3  src/db/connection.ts:67
```

**Output columns:**
- **Symbol** - Name of the function/class/method
- **Count** - Number of definitions/references found for this symbol
- **Path:Line** - File path and line number where defined

## Basic Usage

### List All Symbols (Default)

```bash
osgrep symbols
```

**Result:** First 20 symbols in the codebase (alphabetical order).

**Use when:**
- Exploring a new codebase
- Getting a sense of the API surface
- Checking naming conventions

### Filter by Pattern

```bash
osgrep symbols "validate"
osgrep symbols "Controller"
osgrep symbols "handle"
```

**Behavior:**
- Case-insensitive substring match
- Matches anywhere in the symbol name
- Returns up to 20 matches (default)

**Examples:**
```bash
# Find all validation-related functions
osgrep symbols "valid"
# → validateEmail, isValidUser, validatePayment, etc.

# Find all controller classes
osgrep symbols "Controller"
# → UserController, PaymentController, AdminController, etc.

# Find all handler functions
osgrep symbols "handler"
# → errorHandler, requestHandler, webhookHandler, etc.
```

### Increase Result Limit

```bash
osgrep symbols -l 50
osgrep symbols "test" -l 100
```

**Use when:**
- Need to see more results
- Browsing large modules
- Generating documentation
- Analyzing naming patterns across many symbols

### Filter by Path

```bash
osgrep symbols -p src/api/
osgrep symbols -p src/utils/ "helper"
osgrep symbols -p tests/
```

**Behavior:**
- Only shows symbols defined in files under the specified path
- Combines with pattern filtering
- Path prefix must match from project root

**Examples:**
```bash
# All symbols in the API module
osgrep symbols -p src/api/

# All validation functions in utils
osgrep symbols -p src/utils/ "validate"

# All test functions
osgrep symbols -p tests/
```

## Common Workflows

### Workflow 1: API Discovery

```bash
# Goal: Understand what utilities are available

# Step 1: Browse utilities module
osgrep symbols -p src/utils/ -l 30

# Example output:
# formatDate            function    src/utils/date.ts:10
# parseJSON             function    src/utils/json.ts:5
# validateEmail         function    src/utils/validators.ts:15
# sanitizeInput         function    src/utils/sanitize.ts:8
# ... 26 more

# Step 2: Find specific utility type
osgrep symbols -p src/utils/ "format"

# Result: Discovered all formatting utilities
```

### Workflow 2: Checking for Existing Functions

```bash
# Goal: Avoid duplicate implementations

# Before writing validateUserInput(), check if it exists
osgrep symbols "validateUser"

# Example output:
# validateUser          function    src/auth/validate.ts:12
# validateUserEmail     function    src/utils/validators.ts:45
# validateUserData      function    src/api/users.ts:78

# Decision: Reuse existing validateUser() instead of creating duplicate
```

### Workflow 3: Exploring a Feature Area

```bash
# Goal: Understand payment processing implementation

# Step 1: Find all payment-related symbols
osgrep symbols "payment" -l 50

# Example output:
# processPayment        function    src/payments/process.ts:15
# validatePayment       function    src/payments/validate.ts:8
# PaymentController     class       src/api/payments.ts:23
# createPaymentIntent   function    src/payments/stripe.ts:42
# refundPayment         function    src/payments/refund.ts:67
# ... 45 more

# Step 2: Read key files
Read src/payments/process.ts
Read src/api/payments.ts

# Result: Complete feature understanding
```

### Workflow 4: Navigation to Definition

```bash
# Goal: Jump to specific function definition

# Find the function
osgrep symbols "connectDatabase"

# Output:
# connectDatabase       function    src/db/connection.ts:89

# Read the definition
Read src/db/connection.ts
```

### Workflow 5: Module Inventory

```bash
# Goal: Catalog what's in a module

# List everything in auth module
osgrep symbols -p src/auth/ -l 100

# Count and categorize:
# - 15 functions
# - 3 classes
# - 8 methods

# Result: Understanding of module scope and complexity
```

### Workflow 6: Convention Checking

```bash
# Goal: Verify naming conventions are followed

# Check for inconsistent handler naming
osgrep symbols "handler" -l 50

# Expected pattern: handleX or XHandler
# Found violations:
# processUser          <- Missing "handle" prefix
# userProcessing       <- Wrong pattern

# Result: Identify refactoring candidates for consistency
```

### Workflow 7: Test Function Discovery

```bash
# Goal: Find all test functions

# List test functions
osgrep symbols -p tests/ -l 100

# Or filter by test naming patterns
osgrep symbols "test" -l 100
osgrep symbols "should" -l 100  # BDD-style tests

# Result: Test inventory and coverage understanding
```

## Advanced Usage Patterns

### Pattern: Hierarchical Exploration

```bash
# Top-level: Explore main categories
osgrep symbols -p src/ -l 10

# Mid-level: Dive into specific module
osgrep symbols -p src/api/ -l 30

# Deep-level: Specific file's exports
osgrep symbols -p src/api/users.ts -l 50
```

### Pattern: Naming Pattern Analysis

```bash
# Find all functions using specific patterns
osgrep symbols "get" -l 50      # Getters
osgrep symbols "set" -l 50      # Setters  
osgrep symbols "create" -l 50   # Creators
osgrep symbols "delete" -l 50   # Deleters
osgrep symbols "validate" -l 50 # Validators
osgrep symbols "handle" -l 50   # Handlers
```

### Pattern: Cross-Module Comparison

```bash
# Compare API surface of two modules
osgrep symbols -p src/api/v1/ -l 50
osgrep symbols -p src/api/v2/ -l 50

# Result: Understand API evolution and migration needs
```

### Pattern: Public API Cataloging

```bash
# List exports from public-facing modules
osgrep symbols -p src/api/ -l 100
osgrep symbols -p src/lib/ -l 100

# Document as public API surface
# Monitor for breaking changes
```

## Combining Symbols with Other Commands

### Symbols → Trace

```bash
# Discovery then impact analysis

# Find function
osgrep symbols "processOrder"
# → processOrder @ src/orders/process.ts:45

# Analyze dependencies
osgrep trace processOrder

# Result: Function discovery + relationship analysis
```

### Symbols → Skeleton

```bash
# Browse then examine structure

# Find relevant file
osgrep symbols -p src/payments/
# → Multiple symbols in src/payments/processor.ts

# View file structure
osgrep skeleton src/payments/processor.ts

# Result: Quick navigation to structural overview
```

### Symbols → Search

```bash
# When symbols aren't enough, use semantic search

# Try symbols first
osgrep symbols "authentication"
# → Shows defined functions

# If need to find usage patterns
osgrep "authentication flow implementation"

# Result: Definition discovery + usage discovery
```

### Symbols → Read

```bash
# Direct navigation workflow

# Find definition
osgrep symbols "validateWebhook"
# → validateWebhook @ src/webhooks/validator.ts:23

# Read implementation
Read src/webhooks/validator.ts

# Result: Instant navigation to full implementation
```

## When to Use Symbols

✅ **Exploring unfamiliar codebase** - Browse available functions
✅ **Checking for duplicates** - "Does this function already exist?"
✅ **Finding naming candidates** - See existing naming patterns
✅ **Module understanding** - What's in this directory?
✅ **Quick navigation** - Jump to definition by name
✅ **API documentation** - Generate symbol inventories
✅ **Convention auditing** - Check naming consistency
✅ **Refactoring planning** - Understand scope of changes

## When NOT to Use Symbols

❌ **Finding usage** - Use `trace` to find callers instead
❌ **Understanding implementation** - Use `skeleton` or `Read`
❌ **Semantic discovery** - Use `osgrep search` for concepts
❌ **Variable references** - Symbols indexes functions/classes, not variables
❌ **Content searching** - Use `osgrep search` or `grep` for text

## When to Use Each Tool

**Use Symbols for:**
- "What functions exist?" - Browse available symbols
- "Does X function exist?" - Check before creating
- "Where is X defined?" - Navigate to definition
- "Browse module exports" - Inventory a directory
- "Check naming patterns" - Audit conventions

**Use Search for:**
- "Find by concept" - Semantic discovery
- "Where is X defined?" - Alternative to symbols

**Use Trace for:**
- "Who calls X?" - Find callers
- "Where is X defined?" - Via caller/callee info

## Filtering Best Practices

### Effective Pattern Matching

**Too broad:**
```bash
osgrep symbols "a"  # Matches almost everything
```

**Better:**
```bash
osgrep symbols "auth"      # More specific
osgrep symbols "validate"  # Clear intent
```

**Best:**
```bash
osgrep symbols "authenticate" -l 30  # Specific + adequate limit
osgrep symbols -p src/auth/ "token"  # Scoped + filtered
```

### Path Filtering Strategies

**Project root relative:**
```bash
osgrep symbols -p src/
osgrep symbols -p lib/
osgrep symbols -p tests/
```

**Deep paths for precision:**
```bash
osgrep symbols -p src/api/v2/handlers/
```

**Combine with pattern:**
```bash
osgrep symbols -p src/utils/ "format"  # Scoped search
```

## Limitations

**Case sensitivity:**
- Pattern matching is case-insensitive
- `"User"` matches `"user"`, `"USER"`, `"UserController"`

**Substring matching:**
- Pattern matches anywhere in name
- `"date"` matches `"formatDate"`, `"updateDate"`, `"dateUtils"`
- No regex support (use simple strings)

**Symbol types:**
- Depends on language support
- Python: functions, classes, methods
- JavaScript/TypeScript: functions, classes, methods, interfaces (partial)
- Go: functions, methods, types

**Index freshness:**
- Shows symbols from last index
- May be stale if files changed
- Run `osgrep index` if results seem outdated

**Result limits:**
- Default 20 can miss relevant symbols
- Increase with `-l` for comprehensive view
- Large limits may be slow for huge codebases

## Troubleshooting

**"No symbols found"**
- Run `osgrep index` to build/refresh index
- Check if you're in the project root
- Verify files are not ignored (check `.gitignore`, `.osgrepignore`)

**Expected symbol missing**
- Index may be stale: `osgrep index`
- Symbol may be dynamically created (not indexed)
- Check spelling and case (pattern is case-insensitive)

**Too many results**
- Add pattern filter: `osgrep symbols "specific"`
- Use path filter: `osgrep symbols -p src/module/`
- Combine both: `osgrep symbols -p src/api/ "User"`

**Wrong symbols shown**
- Pattern too broad (matches substrings)
- Add path filter to narrow scope
- Make pattern more specific

**Performance slow**
- Large `-l` values take longer
- Index may need refresh
- Consider narrowing path scope

## Performance Notes

- **Speed**: Sub-second for default limits
- **Scalability**: Handles 10,000+ symbols efficiently
- **Index dependency**: Requires current index
- **Limit impact**: Higher limits = slightly slower
- **Path filtering**: Narrows scope, improves speed

## Best Practices

1. **Start broad, narrow down** - Begin with `osgrep symbols`, then filter
2. **Use path filters liberally** - Speed up queries and reduce noise
3. **Set appropriate limits** - 20 for browsing, 50-100 for comprehensive view
4. **Combine with trace/skeleton** - Symbols for discovery, others for analysis
5. **Check before creating** - Avoid duplicate function implementations
6. **Document conventions** - Use symbols output to establish naming guides
7. **Refresh index regularly** - Keep symbol list current with `osgrep index`
8. **Pattern matching tips** - Use distinctive substrings for precise results

## Integration with Development Workflow

### Before Writing Code
```bash
# Check if function already exists
osgrep symbols "functionName"
```

### During Code Review
```bash
# Understand new additions in context
osgrep symbols -p src/newFeature/ -l 50
```

### Refactoring
```bash
# Inventory what needs renaming
osgrep symbols "oldPattern" -l 100
```

### Documentation
```bash
# Generate API reference
osgrep symbols -p src/api/ -l 500 > api-symbols.txt
```

### Onboarding
```bash
# Show new developers what's available
osgrep symbols -p src/utils/ -l 50
osgrep symbols -p src/api/ -l 50
```
