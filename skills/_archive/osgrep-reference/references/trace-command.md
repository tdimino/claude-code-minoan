# Trace Command Reference

The `trace` command reveals the call graph for any symbol, showing both who calls it (callers) and what it calls (callees). This bidirectional analysis is essential for understanding dependencies, impact analysis, and code relationships.

## Overview

Trace provides a focused view of how a function, method, or class integrates into the broader codebase by mapping its connections in both directions:

- **Callers (Upstream)** - What code depends on this symbol?
- **Callees (Downstream)** - What does this symbol depend on?

**Key use cases:**
- **Impact analysis** - Understand the blast radius of changes
- **Refactoring safety** - Identify all affected code before modifying
- **Entry point discovery** - Find top-level callers of low-level functions
- **Dependency mapping** - Trace chains of function calls
- **Dead code detection** - Find functions with no callers
- **Testing strategy** - Identify what needs test coverage when changing code

## Command Syntax

```bash
osgrep trace <symbol>
```

**Arguments:**
- `<symbol>` - Function name, method name, or class name to trace

**No options** - Trace is intentionally simple and focused.

## Output Format

```
Callers (Who calls this?):
  ↑ main (src/module/main.py:84)
  ↑ api_handler (src/api/routes.py:23)

▶ functionName
  Defined in src/path/to/file.py:42
  Role: ORCHESTRATION

Callees (What does this call?):
  ↓ validate_input
  ↓ process_data
  ↓ save_result
  ↓ send_notification
```

**Output components:**
- **Callers (Who calls this?)** - Functions that invoke this symbol (upstream dependencies)
  - **↑ name (path:line)** - Caller with location where call occurs
- **▶ symbolName** - The function/method being traced
  - **Defined in** - Where it's defined (file:line)
  - **Role** - ORCHESTRATION if it coordinates multiple operations
- **Callees (What does this call?)** - Functions invoked by this symbol (downstream dependencies)
  - **↓ name** - Functions called by the traced symbol

## Understanding the Call Graph

### Interpreting Callers

**Many callers (5+)** indicates:
- Core utility function used throughout codebase
- High impact if changed or removed
- Needs comprehensive test coverage
- Consider backward compatibility

**Few callers (1-3)** indicates:
- Specialized function with limited scope
- Lower refactoring risk
- May be candidate for inlining
- Easier to deprecate if needed

**Zero callers** indicates:
- Dead code (if not an entry point)
- Recently added but unused
- Public API not yet consumed
- Exported for external use

### Interpreting Callees

**Many callees (5+)** indicates:
- Orchestrator function (high-level coordinator)
- Entry point or main workflow
- Higher complexity
- Important architectural function

**Few callees (1-3)** indicates:
- Worker function (specific task)
- Leaf node in call graph
- Lower complexity
- Easier to understand and test

**Zero callees** indicates:
- Pure logic or calculation
- No external dependencies
- Easiest to test (unit test candidate)
- Lowest refactoring risk

## Common Workflows

### Workflow 1: Safe Refactoring

```bash
# Goal: Safely refactor validateUser()

# Step 1: Understand what it does
osgrep skeleton validateUser

# Step 2: Find all callers (impact analysis)
osgrep trace validateUser

# Example output:
# Callers (Who calls this?):
#   ↑ login_handler (src/auth/login.py:23)
#   ↑ register_handler (src/auth/register.py:45)
#   ↑ api_middleware (src/middleware/auth.py:12)
#   ↑ admin_panel (src/admin/users.py:67)

# Step 3: Check each caller's context
Read src/auth/login.py
Read src/middleware/auth.py

# Step 4: Make changes knowing full impact
# All 4 call sites need to be tested after refactoring
```

### Workflow 2: Understanding Feature Flow

```bash
# Goal: Understand payment processing flow

# Step 1: Find entry point
osgrep skeleton "payment processing" -l 3
# Identify: process_payment() as entry point

# Step 2: Trace what it calls (downstream flow)
osgrep trace process_payment

# Example output:
# Callees (What does this call?):
#   ↓ validate_payment_data
#   ↓ charge_card
#   ↓ create_transaction
#   ↓ send_receipt
#   ↓ log_payment

# Step 3: Trace critical callees deeper
osgrep trace charge_card
osgrep trace create_transaction

# Result: Complete flow map from entry to execution
```

### Workflow 3: Dead Code Detection

```bash
# Goal: Find unused helper functions

# Step 1: Trace a suspected unused function
osgrep trace old_helper_function

# Example output:
# Callers (Who calls this?):
#   (no callers found)
#
# Callees (What does this call?):
#   ↓ utility_a
#   ↓ utility_b

# Result: Safe to remove (no callers)
# Note: Check if it's an exported API before removing!
```

### Workflow 4: Dependency Chain Analysis

```bash
# Goal: Understand full dependency chain

# Start with high-level function
osgrep trace handleUserRequest

# CALLS:
#   parseRequest() @ src/parsers/request.ts:10
#   authenticateUser() @ src/auth/auth.ts:25
#   processRequest() @ src/handlers/process.ts:40

# Trace each callee deeper
osgrep trace authenticateUser

# CALLS:
#   validateToken() @ src/auth/tokens.ts:15
#   fetchUserFromDB() @ src/db/users.ts:30
#   checkPermissions() @ src/auth/permissions.ts:45

# Trace even deeper if needed
osgrep trace validateToken

# Result: Complete dependency tree
# handleUserRequest → authenticateUser → validateToken → [leaf functions]
```

### Workflow 5: Finding Entry Points

```bash
# Goal: Find top-level entry points to a subsystem

# Step 1: Pick a low-level utility
osgrep trace connectDatabase

# Example output:
# CALLED BY (3 callers):
#   initializeApp() @ src/app.ts:12
#   reconnectOnFailure() @ src/db/reconnect.ts:23
#   testSetup() @ tests/setup.ts:8

# Step 2: Trace the callers
osgrep trace initializeApp

# CALLED BY (1 caller):
#   main() @ src/index.ts:5

# Result: main() is the entry point
```

### Workflow 6: Test Coverage Planning

```bash
# Goal: Determine testing strategy for changes

# Step 1: Trace function being modified
osgrep trace calculateDiscount

# CALLED BY (6 callers):
#   checkoutFlow() @ src/checkout/cart.ts:45
#   applyPromoCode() @ src/promo/apply.ts:23
#   bulkPricing() @ src/pricing/bulk.ts:67
#   adminPreview() @ src/admin/preview.ts:12
#   apiEndpoint() @ src/api/discounts.ts:89
#   reportGenerator() @ src/reports/sales.ts:34

# Result: 6 integration points need testing
# Create tests covering each caller's usage pattern
```

## Advanced Patterns

### Pattern: Bidirectional Impact Analysis

```bash
# Understand both upstream and downstream impact

# What depends on this? (upstream)
osgrep trace myFunction
# -> Shows CALLED BY (who will break if myFunction changes)

# What does this depend on? (downstream)
osgrep trace myFunction
# -> Shows CALLS (what might break myFunction if they change)

# Complete picture: bidirectional risk assessment
```

### Pattern: Cross-Module Dependencies

```bash
# Find coupling between modules

osgrep trace authModule.validateSession

# CALLED BY:
#   api/handlers.ts
#   admin/panel.ts
#   websocket/connection.ts

# Result: auth module has 3 cross-module dependencies
# Consider: Is this tight coupling intentional?
```

### Pattern: Recursive Tracing

```bash
# Manually trace a deep call chain

# Level 1
osgrep trace topLevelHandler
# Identifies: processRequest()

# Level 2
osgrep trace processRequest
# Identifies: validateInput(), executeLogic()

# Level 3
osgrep trace executeLogic
# Identifies: fetchData(), transformData(), saveData()

# Level 4
osgrep trace fetchData
# Identifies: queryDB(), cacheGet()

# Result: 4-level deep call chain mapped
```

### Pattern: Hotspot Identification

```bash
# Find most-used functions (potential bottlenecks)

osgrep trace logger
# CALLED BY (47 callers)  <- High traffic!

osgrep trace formatDate
# CALLED BY (23 callers)  <- Widely used utility

osgrep trace cryptoHash
# CALLED BY (8 callers)   <- Performance critical?

# Result: High caller count = optimization candidate
```

## Combining Trace with Other Commands

### Trace + Skeleton

```bash
# Understand structure AND relationships

# See structure
osgrep skeleton src/payments/processor.ts

# See relationships
osgrep trace processPayment
osgrep trace chargeCard
osgrep trace validateCard

# Result: Complete architectural understanding
```

### Trace + Search

```bash
# Find then trace

# Discovery
osgrep "webhook signature validation"
# -> Finds: validateWebhookSignature()

# Analysis
osgrep trace validateWebhookSignature

# Result: Context-aware tracing
```

### Trace + Read

```bash
# Trace then dive deep

# Map dependencies
osgrep trace handlePayment

# Read critical paths
Read src/payments/handler.ts     # The traced function
Read src/payments/validator.ts   # Key callee
Read src/api/checkout.ts         # Key caller

# Result: Strategic reading based on trace insights
```

## When to Use Trace

✅ **Before refactoring** - Understand full impact
✅ **During code review** - Verify all callers updated
✅ **Learning codebase** - Map function relationships
✅ **Deprecating code** - Find all usages
✅ **Impact assessment** - Risk analysis for changes
✅ **Dead code cleanup** - Find unused functions
✅ **Performance optimization** - Identify hotspots
✅ **Testing strategy** - Plan test coverage

## When NOT to Use Trace

❌ **Variable references** - Trace works on functions/methods, not variables
❌ **Type definitions** - Use search for type usage instead
❌ **Text searching** - Use `osgrep` search or `grep` for content
❌ **Understanding implementation** - Use `skeleton` or `Read` instead
❌ **Configuration** - Trace doesn't help with config files

## Limitations

**Symbol resolution:**
- Must be a function, method, or class name
- Name collisions may show multiple symbols
- Dynamic calls may not be detected (e.g., `obj[funcName]()`)

**Cross-language calls:**
- JavaScript/TypeScript interop usually works
- FFI or subprocess calls not traced
- Dynamically loaded code may be missed

**Accuracy:**
- Based on static analysis of indexed code
- May miss runtime-only relationships
- Conditional calls are treated as definite

**Performance:**
- Fast for functions with <100 callers/callees
- Large codebases may have slight delay
- Index must be current (`osgrep index` if stale)

## Troubleshooting

**"Symbol not found"**
- Check spelling (case-sensitive)
- Ensure index is up to date: `osgrep index`
- Symbol may not be indexed (check with `osgrep symbols <name>`)
- Try searching first: `osgrep "symbol name"`

**Multiple symbols with same name**
- Output will show all matching symbols
- Use file paths to disambiguate
- Consider: Are naming collisions intentional?

**Empty callers or callees**
- May be accurate (dead code, leaf function)
- Could indicate incomplete index
- Check: Is this an exported API?
- Verify: Run `osgrep index` to refresh

**Dynamic calls not shown**
- Example: `obj[methodName]()` may not trace
- Limitation of static analysis
- Search for string patterns if critical

## When to Use Each Tool

**Use Trace for:**
- Finding who calls a function (callers)
- Finding what a function calls (callees)
- Impact analysis before changes
- Understanding dependencies
- Refactoring safety assessment

**Use Skeleton for:**
- Seeing function signatures
- Understanding dependencies (structure)
- Quick file structure overview

**Use Search for:**
- Finding relevant files
- Conceptual/semantic discovery

## Best Practices

1. **Trace before refactoring** - Always check callers before major changes
2. **Map critical paths** - Trace entry points and their callees
3. **Document high-impact functions** - Functions with 10+ callers need extra care
4. **Check for dead code** - Zero callers might indicate cleanup opportunity
5. **Combine with skeleton** - Use both for complete understanding
6. **Refresh index regularly** - Keep trace results accurate with `osgrep index`
7. **Recursive tracing** - Trace callees to build complete dependency chains
8. **Cross-reference with tests** - Ensure all traced callers have test coverage

## Performance Notes

- **Speed**: Sub-second for most queries
- **Index dependency**: Requires up-to-date index
- **Scalability**: Handles large codebases efficiently
- **Accuracy**: Based on static analysis of indexed code
