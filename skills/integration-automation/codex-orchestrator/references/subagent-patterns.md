# Subagent Delegation Patterns

Patterns for effectively delegating tasks to Codex subagents.

## When to Use Each Profile

### Reviewer

**Best for:**
- Pre-commit code review
- PR review assistance
- Code quality assessment
- Identifying technical debt

**Example prompts:**
```
"Review the changes in src/auth/ for security and quality"
"Check this PR for potential issues before merge"
"Assess the code quality of the new payment module"
```

### Debugger

**Best for:**
- Investigating reported bugs
- Tracing unexpected behavior
- Finding root causes
- Proposing minimal fixes

**Example prompts:**
```
"Debug why login fails with special characters in password"
"Trace the null pointer exception in UserService"
"Find why the API returns 500 on large payloads"
```

### Architect

**Best for:**
- System design decisions
- Evaluating architectural changes
- Planning major refactors
- Assessing technical feasibility

**Example prompts:**
```
"Design a caching layer for our API endpoints"
"Evaluate whether we should split into microservices"
"Plan the migration from REST to GraphQL"
```

### Security

**Best for:**
- Security audits
- Vulnerability assessment
- Compliance checking
- Penetration test preparation

**Example prompts:**
```
"Audit the authentication module for vulnerabilities"
"Check for OWASP Top 10 issues in the API"
"Review secrets handling in the deployment scripts"
```

### Refactor

**Best for:**
- Code cleanup before features
- Reducing technical debt
- Modernizing legacy code
- Improving testability

**Example prompts:**
```
"Refactor the UserController to reduce complexity"
"Extract common logic from these three services"
"Modernize the error handling to use Result types"
```

### Docs

**Best for:**
- API documentation
- README updates
- Code comments
- Architecture documentation

**Example prompts:**
```
"Document the public API for the payment module"
"Write a getting started guide for new developers"
"Add JSDoc comments to the utility functions"
```

## Chaining Subagents

### Pattern: Review → Debug → Fix

1. **Review first** to identify issues
2. **Debug** specific problems found
3. **Fix** with targeted changes

```bash
# Step 1: Find issues
./scripts/codex-exec.sh reviewer "Review src/api/ for bugs"

# Step 2: Investigate specific bug
./scripts/codex-exec.sh debugger "Debug the race condition in src/api/cache.ts"

# Step 3: Apply fix (manual or with another agent)
```

### Pattern: Architect → Review → Refactor

1. **Architect** designs the change
2. **Review** validates the approach
3. **Refactor** implements incrementally

```bash
# Step 1: Design
./scripts/codex-exec.sh architect "Design a new repository layer"

# Step 2: Validate
./scripts/codex-exec.sh reviewer "Review the proposed repository pattern"

# Step 3: Implement
./scripts/codex-exec.sh refactor "Extract repository pattern from services"
```

### Pattern: Security → Review → Docs

1. **Security** finds vulnerabilities
2. **Review** validates fixes
3. **Docs** documents security practices

```bash
# Step 1: Audit
./scripts/codex-exec.sh security "Audit authentication flow"

# Step 2: Review fixes
./scripts/codex-exec.sh reviewer "Review the security patches"

# Step 3: Document
./scripts/codex-exec.sh docs "Document the authentication security model"
```

## Parallel Delegation

For independent tasks, run multiple subagents in parallel:

```bash
# Run in separate terminals or with background jobs
./scripts/codex-exec.sh reviewer "Review src/auth/" &
./scripts/codex-exec.sh security "Security audit src/auth/" &
./scripts/codex-exec.sh docs "Document src/auth/ API" &
wait
```

## Scoping Tasks Effectively

### Too Broad (Avoid)
```
"Review the entire codebase"
"Fix all the bugs"
"Document everything"
```

### Well-Scoped (Prefer)
```
"Review the authentication module for SQL injection"
"Debug the login timeout issue on slow networks"
"Document the public methods in UserService"
```

### Guidelines
- Target specific files or directories
- Focus on one concern at a time
- Include relevant context in the prompt
- Mention specific issues when known

## Error Handling

### If Codex Gets Stuck
- Narrow the scope
- Provide more context
- Try a different profile

### If Results Are Poor
- Check if the right profile was used
- Add constraints to the prompt
- Break into smaller tasks

### If API Errors Occur
- Check OPENAI_API_KEY is set
- Verify network connectivity
- Try with --model o3-mini (faster/cheaper)

## Cost Optimization

| Profile Use Case | Recommended Model |
|-----------------|-------------------|
| Quick checks | o3-mini |
| Detailed review | o3 |
| Complex architecture | o3 |
| Simple docs | o3-mini |
| Security audit | o3 |

```bash
# Override model for cost savings
./scripts/codex-exec.sh reviewer "Quick style check" --model o3-mini

# Use full power for complex tasks
./scripts/codex-exec.sh architect "Design distributed cache" --model o3
```
