# Factory.ai Agent Lint Categories

Seven categories of agent-specific lint rules based on Factory.ai's "Linters as Agent Steering" paradigm. Each category includes detection patterns and `lint-rules.json` templates.

The core insight: agents self-correct faster against lint output than prose instructions. Codify what you can enforce mechanically; instruct only what requires judgment.

## 1. Grep-ability

Ensure code remains searchable by agents and humans.

**Why**: Agents rely on grep/ripgrep to find code. Dynamic string construction, computed property names, and metaprogramming break search.

**Rules**:

```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "\\[`[^`]*\\$\\{",
  "message": "[grep-ability] Computed property name with template literal reduces searchability",
  "exclude_patterns": ["// grep-ok", "test\\."]
}
```

```json
{
  "extensions": ["py"],
  "pattern": "getattr\\(.*,\\s*f['\"]",
  "message": "[grep-ability] Dynamic getattr with f-string breaks grep discovery",
  "exclude_patterns": ["# grep-ok"]
}
```

## 2. Glob-ability

Ensure file organization supports glob-based discovery.

**Why**: Agents use glob patterns to find relevant files. Non-standard locations, deeply nested files, and ambiguous naming break this.

**Rules**:

```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "from ['\"]\\.\\./(\\.\\./)+(\\.\\./).*['\"]",
  "message": "[glob-ability] Deep relative import (3+ levels) — consider re-exporting from a barrel file",
  "exclude_patterns": ["node_modules"]
}
```

## 3. Architectural Boundaries

Enforce module boundaries and dependency direction.

**Why**: Agents lack architectural context. Without boundary enforcement, they import from internal modules, create circular dependencies, or bypass API surfaces.

**Rules** (customize per project):

```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "from ['\"].*\\/internal\\/",
  "message": "[architecture] Importing from internal/ module — use the public API instead",
  "exclude_patterns": ["internal/"]
}
```

```json
{
  "extensions": ["rs"],
  "pattern": "pub\\(crate\\).*use super::super::",
  "message": "[architecture] Deep super:: import across module boundaries",
  "exclude_patterns": ["mod\\.rs"]
}
```

## 4. Security

Prevent common security anti-patterns.

**Why**: Agents generate code that works but may be insecure — hardcoded secrets, SQL injection vectors, insecure deserialization.

**Rules**:

```json
{
  "extensions": ["ts", "tsx", "js", "jsx", "py", "rb"],
  "pattern": "(password|secret|api_key|token)\\s*=\\s*['\"][^'\"]+['\"]",
  "message": "[security] Hardcoded secret — use environment variables",
  "exclude_patterns": ["test", "spec", "mock", "fixture", "example", "\\.env\\.example"]
}
```

```json
{
  "extensions": ["py"],
  "pattern": "eval\\(|exec\\(",
  "message": "[security] eval/exec usage — potential code injection",
  "exclude_patterns": ["# nosec", "test_"]
}
```

```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "dangerouslySetInnerHTML",
  "message": "[security] dangerouslySetInnerHTML — XSS risk, sanitize input",
  "exclude_patterns": ["// sanitized"]
}
```

## 5. Testability

Enforce patterns that make code testable.

**Why**: Agents generate tightly coupled code that resists testing — global state, hidden dependencies, side effects in constructors.

**Rules**:

```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "new Date\\(\\)|Date\\.now\\(\\)",
  "message": "[testability] Direct Date construction — inject a clock for testability",
  "exclude_patterns": ["test", "spec", "mock"]
}
```

```json
{
  "extensions": ["py"],
  "pattern": "^import os$|^from os import",
  "message": "[testability] Direct os import at module level — consider dependency injection for filesystem ops",
  "exclude_patterns": ["test_", "conftest"]
}
```

## 6. Observability

Ensure code is observable in production.

**Why**: Agents generate code that works in dev but is opaque in production — no structured logging, no metrics, no error context.

**Rules**:

```json
{
  "extensions": ["ts", "tsx", "js", "jsx"],
  "pattern": "catch\\s*\\([^)]*\\)\\s*\\{\\s*\\}",
  "message": "[observability] Empty catch block swallows errors — log or rethrow",
  "exclude_patterns": ["// intentionally empty"]
}
```

```json
{
  "extensions": ["py"],
  "pattern": "except:\\s*$|except Exception:\\s*$",
  "message": "[observability] Bare except or broad Exception catch — be specific and log",
  "exclude_patterns": ["# nosec", "pass  #"]
}
```

## 7. Documentation

Enforce documentation standards for public APIs.

**Why**: Agents generate functions without documenting parameters, return types, or side effects.

**Rules**:

```json
{
  "extensions": ["ts", "tsx"],
  "pattern": "^export (async )?function [a-zA-Z]+\\(",
  "message": "[documentation] Exported function without JSDoc — add documentation for public API",
  "require_absent": "/**",
  "exclude_patterns": ["test", "spec", "\\.d\\.ts"]
}
```

## 8. Debugging Residue (Bonus)

Detect files and patterns left behind by iterative AI coding.

**Why**: Agents create backup files, versioned copies, and debugging artifacts that accumulate as technical debt.

**Rules**:

```json
{
  "extensions": ["ts", "tsx", "js", "jsx", "py", "rs", "rb", "go"],
  "pattern": "console\\.log\\(|debugger;|binding\\.pry|import pdb|println!\\(\"DEBUG",
  "message": "[debugging-residue] Debug statement left in code",
  "exclude_patterns": ["test", "spec", "debug\\."]
}
```

```json
{
  "extensions": ["ts", "tsx", "js", "jsx", "py", "rs", "rb", "go"],
  "pattern": "TODO.*HACK|FIXME.*temp|XXX|DELETEME",
  "message": "[debugging-residue] Temporary marker left in code",
  "exclude_patterns": []
}
```

**File-level detection** (checked by audit.py, not grep rules):
- Files matching: `*_v2.*`, `*_backup.*`, `*_fixed.*`, `*_old.*`, `*_new.*`, `*_copy.*`, `*.bak`, `*.orig`
- These indicate iterative AI attempts that were never cleaned up.

## Template: Minimal lint-rules.json

A starting config for any JS/TS project:

```json
{
  "linter": "eslint",
  "rules": [
    {
      "extensions": ["ts", "tsx", "js", "jsx"],
      "pattern": "console\\.log\\(",
      "message": "[debugging-residue] console.log left in code",
      "exclude_patterns": ["test", "spec"],
      "exclude_paths": ["*/scripts/*"]
    },
    {
      "extensions": ["ts", "tsx", "js", "jsx"],
      "pattern": "(password|secret|api_key|token)\\s*=\\s*['\"][^'\"]+['\"]",
      "message": "[security] Hardcoded secret — use environment variables",
      "exclude_patterns": ["test", "spec", "mock", "fixture"]
    },
    {
      "extensions": ["ts", "tsx", "js", "jsx"],
      "pattern": "catch\\s*\\([^)]*\\)\\s*\\{\\s*\\}",
      "message": "[observability] Empty catch block swallows errors",
      "exclude_patterns": ["// intentionally empty"]
    }
  ]
}
```
