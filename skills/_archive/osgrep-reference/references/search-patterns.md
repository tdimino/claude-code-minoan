# Common Search Patterns

This reference provides semantic search patterns for different architectural patterns and codebases.

**Related references:**
- `skeleton-command.md` - Compress files to signatures after finding them
- `trace-command.md` - Analyze call graphs for symbols you discover
- `symbols-command.md` - Browse available functions by name

## Table of Contents

- [Open Souls / Daimonic Architecture](#open-souls--daimonic-architecture)
- [React / Next.js Applications](#react--nextjs-applications)
- [Backend / API Services](#backend--api-services)
- [Database & Persistence](#database--persistence)
- [Testing & Quality](#testing--quality)
- [DevOps & Infrastructure](#devops--infrastructure)

## Open Souls / Daimonic Architecture

### Mental Processes
```bash
osgrep "mental processes that handle conversation flow"
osgrep "where do we transition between mental processes?"
osgrep "process orchestration logic"
```

### Subprocesses
```bash
osgrep "background processes that learn about the user"
osgrep "subprocesses using dual persistence pattern"
osgrep "where do we monitor user emotional state?"
```

### Cognitive Steps
```bash
osgrep "LLM prompts for decision making"
osgrep "cognitive steps that use structured output"
osgrep "where do we construct system prompts?"
osgrep "ephemeral scaffolding patterns"
```

### Memory Management
```bash
osgrep "soulMemory persistent state"
osgrep "workingMemory immutability"
osgrep "memory region management"
osgrep "dual persistence synchronization"
```

### Hooks & State
```bash
osgrep "useActions hook usage"
osgrep "useProcessMemory ephemeral state"
osgrep "useSoulMemory persistent values"
```

## React / Next.js Applications

### Components
```bash
osgrep "where do we handle form submission?"
osgrep "modal component implementation"
osgrep "data fetching in components"
osgrep "error boundary patterns"
```

### Hooks & State
```bash
osgrep "custom hooks for API calls"
osgrep "global state management"
osgrep "effect cleanup patterns"
```

### Routing & Navigation
```bash
osgrep "protected route logic"
osgrep "URL parameter handling"
osgrep "navigation guards"
```

### API Integration
```bash
osgrep "where do we call external APIs?"
osgrep "webhook processing"
osgrep "API error handling"
```

## Backend / API Services

### Authentication
```bash
osgrep "user authentication logic"
osgrep "JWT token validation"
osgrep "permission checks"
osgrep "session management"
```

### Request Handling
```bash
osgrep "webhook signature validation"
osgrep "rate limiting implementation"
osgrep "request idempotency"
osgrep "CORS configuration"
```

### Business Logic
```bash
osgrep "payment processing flow"
osgrep "notification sending logic"
osgrep "data validation rules"
```

## Database & Persistence

### Schema & Models
```bash
osgrep "user table schema"
osgrep "relationship definitions"
osgrep "database migrations"
```

### Queries
```bash
osgrep "complex join operations"
osgrep "transaction handling"
osgrep "query optimization"
```

### ORM Patterns
```bash
osgrep "model lifecycle hooks"
osgrep "soft delete implementation"
osgrep "eager loading strategies"
```

## Testing & Quality

### Test Patterns
```bash
osgrep "integration test setup"
osgrep "mock implementations"
osgrep "test fixture creation"
```

### Error Handling
```bash
osgrep "error logging"
osgrep "exception handling patterns"
osgrep "retry logic"
```

## DevOps & Infrastructure

### Configuration
```bash
osgrep "environment variable usage"
osgrep "feature flag checks"
osgrep "configuration loading"
```

### Deployment
```bash
osgrep "build process configuration"
osgrep "database migration scripts"
osgrep "health check endpoints"
```

### Monitoring
```bash
osgrep "metrics collection"
osgrep "error tracking integration"
osgrep "logging setup"
```

## Tips for Effective Queries

### Concept vs. Implementation
- ❌ `osgrep "useState"` (too literal)
- ✅ `osgrep "component state management"` (conceptual)

### Specific vs. General
- ❌ `osgrep "code"` (too broad)
- ✅ `osgrep "user registration flow"` (specific intent)

### Problem-Oriented
- ❌ `osgrep "function"` (too vague)
- ✅ `osgrep "where do we prevent duplicate submissions?"` (problem-focused)

### Natural Language
- ✅ `osgrep "how do we handle payment failures?"`
- ✅ `osgrep "what happens when a webhook arrives?"`
- ✅ `osgrep "where is user data validated?"`

### Follow-Up Workflows

After finding relevant files with search:

```bash
# Search → Skeleton: Understand file structure
osgrep "payment processing"              # Find files
osgrep skeleton src/payments/process.py  # See signatures

# Search → Trace: Understand dependencies
osgrep "webhook handler"                 # Find entry point
osgrep trace handle_webhook              # See callers/callees

# Search → Symbols: Explore related functions
osgrep "authentication"                  # Find auth files
osgrep symbols -p src/auth/              # Browse auth symbols
```
