# AGENTS.md Format Guide

AGENTS.md files customize Codex agent behavior by providing persona, focus areas, and output formatting instructions.

## File Location

Codex reads AGENTS.md from the current working directory. The codex-orchestrator skill manages this by:

1. Storing profile templates in `agents/*.md`
2. Copying the selected profile to a temp directory as `AGENTS.md`
3. Running Codex from that directory

## Basic Structure

```markdown
# Agent Role Title

Brief description of the agent's expertise and purpose.

## Primary Focus Areas

1. **Area Name** - Description of focus
2. **Area Name** - Description of focus
3. **Area Name** - Description of focus

## Methodology

Step-by-step approach the agent should follow.

## Output Format

How the agent should structure its responses.

## Checklist (optional)

- [ ] Item to verify
- [ ] Item to verify
```

## Section Guidelines

### Title Section

The title establishes the agent's identity:

```markdown
# Code Reviewer Agent
# Security Auditor Agent
# Debugging Specialist Agent
```

### Focus Areas

List 3-7 primary concerns, ordered by importance:

```markdown
## Primary Focus Areas

1. **Code Quality** - Readability, naming, organization
2. **Bug Detection** - Logic errors, edge cases
3. **Performance** - Complexity, allocations
```

### Methodology

Describe the systematic approach:

```markdown
## Review Methodology

1. **Understand context** - Read surrounding code
2. **Identify issues** - Categorize by severity
3. **Propose fixes** - Provide concrete suggestions
```

### Output Format

Specify exact output structure:

```markdown
## Output Format

Structure findings as:

\`\`\`
## Critical Issues
- [file:line] Description
  Suggestion: How to fix

## Improvements
- [file:line] Description
\`\`\`
```

## Best Practices

### DO
- Be specific about expertise and scope
- Include concrete examples of output
- Define severity levels if applicable
- Provide checklists for systematic coverage

### DON'T
- Make the persona too broad
- Include conflicting instructions
- Leave output format ambiguous
- Overload with too many focus areas

## Example: Minimal Profile

```markdown
# Quick Reviewer

Fast code review for obvious issues.

## Focus
- Critical bugs only
- Security red flags
- Breaking changes

## Output
List issues by severity, max 5 items.
```

## Example: Detailed Profile

```markdown
# Enterprise Security Auditor

You are a senior security engineer performing compliance audits.

## Standards
- OWASP Top 10
- SOC 2 requirements
- PCI DSS (if payment processing)

## Audit Process

1. Identify trust boundaries
2. Trace data flow
3. Check authentication/authorization
4. Review cryptographic usage
5. Scan for hardcoded secrets

## Output Format

\`\`\`
## Compliance Status: PASS/FAIL

### Critical Findings
[SEC-001] Description
- Affected: file:line
- Risk: What could happen
- Remediation: How to fix
- Reference: OWASP A03:2021

### Observations
Non-critical items for improvement
\`\`\`

## Evidence Requirements
Include code snippets and line numbers for all findings.
```

## Profile Inheritance

For complex scenarios, profiles can reference shared content:

```markdown
# API Security Specialist

Extends security auditor with API-specific focus.

## Additional Focus
- REST/GraphQL security
- Rate limiting
- API versioning security
- JWT/OAuth implementation

[Include base security checklist from security.md]
```

## Testing Profiles

Verify a profile works correctly:

```bash
# Test with simple prompt
codex exec "List the files in this directory"

# Verify persona is applied
codex exec "Describe your role and focus areas"
```
