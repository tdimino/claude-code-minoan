# AI-Specific Anti-Patterns

Ten anti-patterns observed in AI-generated code (CodeRabbit data: AI PRs contain 1.7x more issues than human PRs). Each includes a detection heuristic and lint-rules.json template where applicable.

## 1. Dead-Weight Tests

**What**: Tests that always pass regardless of implementation correctness. Common forms: testing that a function exists, asserting truthy values, testing mock behavior instead of real behavior.

**Severity**: High — creates false confidence in test suite.

**Detection heuristic**:
- Tests with no meaningful assertions (only `expect(x).toBeTruthy()` or `assert True`)
- Tests where the mock's return value is the same as the expected value
- Test files with 0 failing tests across all runs

**Grep pattern**:
```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "expect\\(.*\\)\\.toBeTruthy\\(\\)|expect\\(.*\\)\\.toBeDefined\\(\\)",
  "message": "[dead-weight-test] Weak assertion — test specific values, not existence",
  "exclude_patterns": ["// existence check intentional"]
}
```

## 2. Happy-Path Bias

**What**: Tests cover only the success path. No error cases, edge cases, or boundary conditions.

**Severity**: High — production failures come from untested paths.

**Detection heuristic**:
- Test file with no `throw`, `reject`, `error`, `fail`, `invalid`, or `expect(...).toThrow` keywords
- No tests for empty input, null, undefined, or boundary values
- All test descriptions use positive language ("should work", "returns correct")

**Grep pattern**:
```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "describe\\(|it\\(",
  "message": "[happy-path-bias] Test file has no error path coverage",
  "require_absent": "throw|reject|error|fail|invalid|toThrow|raises|Error",
  "exclude_patterns": []
}
```

## 3. Hallucinated Imports

**What**: Importing modules, functions, or types that don't exist in the project or its dependencies.

**Severity**: Critical — code won't compile/run.

**Detection heuristic**: Best caught by the type checker or build step, not grep. The audit checks whether type checking is configured.

**Recommendation**: Ensure `tsc --noEmit` or equivalent runs as part of the feedback loop. This catches hallucinated imports at compile time.

## 4. Framework Confusion

**What**: Mixing patterns from different frameworks or different eras of the same framework. Examples: React class components mixed with hooks, Express middleware mixed with Fastify plugins.

**Severity**: Medium — code works but is inconsistent and confusing.

**Grep patterns**:
```json
{
  "extensions": ["tsx", "jsx"],
  "pattern": "extends React\\.Component|extends Component",
  "message": "[framework-confusion] Class component in a hooks-based codebase — use function components",
  "exclude_patterns": ["ErrorBoundary", "// class component required"]
}
```

```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "require\\(['\"]",
  "message": "[framework-confusion] CommonJS require() in ESM codebase — use import",
  "require_absent": "\"type\": \"commonjs\"",
  "exclude_patterns": ["jest\\.config", "\\.cjs$", "// commonjs required"]
}
```

## 5. Debugging Residue Files

**What**: Files created during iterative debugging that were never cleaned up: `*_v2.*`, `*_backup.*`, `*_fixed.*`, `*_old.*`, `*.bak`.

**Severity**: Medium — technical debt, confusing for future agents.

**Detection heuristic**: File-level glob, not content grep. The audit script checks for:
```
*_v2.*, *_v3.*, *_backup.*, *_fixed.*, *_old.*, *_new.*, *_copy.*, *_temp.*,
*.bak, *.orig, *.swp, *~
```

## 6. Implementation-First Test Writing

**What**: Tests written after implementation that merely confirm what the code does rather than what it should do. Symptoms: tests mirror implementation structure, use same variable names, test internal state.

**Severity**: Medium — tests don't catch regressions because they're coupled to implementation.

**Detection heuristic**:
- Test imports internal/private symbols
- Test variable names match implementation variable names exactly
- Test structure mirrors implementation function order

**Recommendation**: CLAUDE.md instruction — "Write tests before implementation or from the specification, not from reading the implementation."

## 7. Banned API Usage

**What**: Using APIs that are deprecated, insecure, or banned by project convention.

**Severity**: Varies — project-specific.

**Grep patterns** (customize per project):
```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "\\bfetch\\(",
  "message": "[banned-api] Direct fetch() — use the project's HTTP client wrapper",
  "exclude_patterns": ["// direct fetch ok", "polyfill", "test"]
}
```

```json
{
  "extensions": ["py"],
  "pattern": "import requests",
  "message": "[banned-api] Direct requests import — use the project's HTTP client",
  "exclude_patterns": ["# direct ok", "test_"]
}
```

## 8. Duplicate Utility Creation

**What**: Creating a new utility function that already exists in the codebase. Agents lack awareness of existing helpers.

**Severity**: Medium — code bloat, inconsistency.

**Detection heuristic**: Not detectable by grep. The CLAUDE.md instruction "grep before writing any utility" addresses this. The audit checks whether this instruction exists.

**Recommendation**: CLAUDE.md should contain: "Before writing any helper function, search the codebase for its verb. If the function exists, use it."

## 9. Over-Abstraction

**What**: Creating unnecessary abstractions, interfaces, or indirection layers. Common: wrapping a single function in a class, creating a factory for one implementation, adding a service layer with one method.

**Severity**: Low-Medium — increases complexity without value.

**Detection heuristic**:
- Classes with a single method
- Interfaces with a single implementation
- Files with "Factory", "Manager", "Handler", "Service" in name that contain <50 lines

**Grep pattern**:
```json
{
  "extensions": ["ts"],
  "pattern": "class \\w+(Factory|Manager|Handler|Service|Provider|Wrapper)",
  "message": "[over-abstraction] Named abstraction pattern — verify this isn't a single-use wrapper",
  "exclude_patterns": ["// abstraction justified"]
}
```

## 10. Missing Error Boundaries

**What**: No error handling at system boundaries — API calls, file I/O, user input parsing, external service calls.

**Severity**: High — uncaught errors crash the application.

**Detection heuristic**:
- `fetch()` or HTTP client calls without try/catch or `.catch()`
- File operations without error handling
- JSON.parse without try/catch

**Grep patterns**:
```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "JSON\\.parse\\(",
  "message": "[error-boundary] JSON.parse without try/catch — wrap in error handling",
  "exclude_patterns": ["try", "catch", "// validated input"]
}
```

```json
{
  "extensions": ["py"],
  "pattern": "json\\.loads\\(",
  "message": "[error-boundary] json.loads without try/except — wrap in error handling",
  "exclude_patterns": ["try:", "except", "# validated"]
}
```

## Summary Table

| # | Anti-Pattern | Severity | Detectable by Grep? | Primary Mitigation |
|---|-------------|----------|---------------------|-------------------|
| 1 | Dead-weight tests | High | Partially | lint-rules.json |
| 2 | Happy-path bias | High | Partially | lint-rules.json + CLAUDE.md |
| 3 | Hallucinated imports | Critical | No | Type checker / build step |
| 4 | Framework confusion | Medium | Yes | lint-rules.json |
| 5 | Debugging residue files | Medium | File glob | audit.py file scan |
| 6 | Implementation-first tests | Medium | No | CLAUDE.md instruction |
| 7 | Banned API usage | Varies | Yes | lint-rules.json (project-specific) |
| 8 | Duplicate utility creation | Medium | No | CLAUDE.md instruction |
| 9 | Over-abstraction | Low-Med | Partially | lint-rules.json (advisory) |
| 10 | Missing error boundaries | High | Partially | lint-rules.json |
