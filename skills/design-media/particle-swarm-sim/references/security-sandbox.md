# Security Sandbox

The sandbox validates all injected code before execution. This is defense-in-depth — it prevents common mistakes and accidental DOM access. It is not a hardened isolation boundary.

## Threat Model

The primary users are AI models (Claude, Gemini) generating code from creative prompts. The sandbox prevents:
- Accidental DOM manipulation that breaks the host UI
- Network requests from injected code
- Prototype pollution that corrupts Three.js internals
- Infinite loops that freeze the browser tab
- Global scope escape via constructor chains

It does NOT protect against a determined attacker with full knowledge of the sandbox internals. For hostile-input scenarios, use a Web Worker or sandboxed iframe.

## Validation Pipeline

### Stage 1: Forbidden Pattern Scan (Instant)

Regex patterns applied against the raw code string. Any match = immediate rejection.

| Pattern | Blocks | Reason |
|---------|--------|--------|
| `\bdocument\b` | `document.*` | DOM access |
| `\bwindow\b` | `window.*` | Global scope |
| `\bfetch\b` | `fetch()` | Network |
| `\bXMLHttpRequest\b` | XHR | Network |
| `\bWebSocket\b` | WebSocket | Network |
| `\beval\b` | `eval()` | Code injection |
| `\bFunction\s*\(` | `Function(...)` | Constructor escape |
| `\bimport\s*\(` | Dynamic import | Module loading |
| `\brequire\s*\(` | CommonJS | Module loading |
| `\bprocess\b` | Node.js process | System access |
| `\b__proto__\b` | `__proto__` | Prototype pollution |
| `\.prototype\b` | `.prototype` | Prototype chain |
| `\bglobalThis\b` | `globalThis` | Global scope |
| `\bself\b` | `self` | Worker global |
| `\blocation\b` | `location` | URL access |
| `\bnavigator\b` | `navigator` | Browser API |
| `\blocalStorage\b` | localStorage | Storage |
| `\bsessionStorage\b` | sessionStorage | Storage |
| `\bindexedDB\b` | IndexedDB | Storage |
| `\bcrypto\b` | Crypto API | System access |
| `\bsetTimeout\b` | setTimeout | Async escape |
| `\bsetInterval\b` | setInterval | Async escape |
| `\balert\s*\(` | alert() | UI hijack |
| `\bconfirm\s*\(` | confirm() | UI hijack |
| `\bprompt\s*\(` | prompt() | UI hijack |
| `\.constructor\b` | `.constructor` | Constructor chain escape |
| `\bReflect\b` | Reflect API | Metaprogramming |
| `\bProxy\b` | Proxy | Metaprogramming |
| `\bthis\s*\[` | `this[...]` | Dynamic property access |
| `\bwhile\s*\(\s*true\s*\)` | `while(true)` | Infinite loop |
| `\bfor\s*\(\s*;\s*;\s*\)` | `for(;;)` | Infinite loop |

### Stage 2: Syntax Check

The code is compiled via `new Function(...)` with all API parameters as named arguments. Syntax errors are caught and reported with the parser's error message.

### Stage 3: Dry-Run Stability Gate

The compiled function is executed with mock values:
- 3 frames (`time` = 0, 0.016, 0.032)
- 10 particles per frame (`i` = 0..9, `count` = 100)
- `THREE` = `SAFE_THREE` (frozen subset: Vector3, Color, MathUtils)
- `addControl` returns `1` (constant)
- `setInfo` and `annotate` are no-ops
- **Time budget**: 500ms total. Exceeding this = rejection (catches infinite loops that bypass regex).

After each particle: check `target.x/y/z` and `color.r/g/b` for `isFinite()`. Non-finite values = rejection.

### Stage 4: Runtime Protection

During live execution:
- The `try/catch` wraps the **entire frame loop** (not per-particle). A single throw disables the sim and displays the error.
- Position writes are guarded: non-finite values are silently skipped (particle retains previous position).
- Color writes are guarded: non-finite values are silently skipped.

## `SAFE_THREE` Subset

The full `THREE` namespace includes classes like `FileLoader` and `ImageLoader` that internally call `fetch()` — bypassing the regex blacklist since `"fetch"` never appears in the injected code. To prevent this:

The host provides `SAFE_THREE`, a frozen object containing only:
- `THREE.Vector3`
- `THREE.Color`
- `THREE.MathUtils` (frozen copy)

This is the only `THREE` object the sim code can access. The API contract documents `THREE` as a "safe subset."

## Known Limitations

1. **Not a true sandbox.** The `new Function` approach shares the JS realm. A sufficiently clever bypass could theoretically reach the host scope. For production use with untrusted users, execute in a Web Worker with `postMessage` for position/color data transfer.
2. **Infinite loop detection is heuristic.** The regex catches `while(true)` and `for(;;)` but not all infinite loop patterns (e.g., `while(1)`, mutual recursion). The 500ms time budget is the real backstop, but it only protects during dry-run — a loop that takes 501ms to trigger will freeze the live execution.
3. **String concatenation bypasses are possible.** `'doc' + 'ument'` constructs the word "document" without matching `\bdocument\b`. The `.constructor` ban mitigates most exploitation paths, but edge cases exist.
