# AGENTS.md Templates

Practical templates for common project types. Each is cross-agent compatible (Codex, Cursor, Copilot, Devin, Jules, Amp, Gemini CLI) and follows the WHAT/WHY/HOW framework with Boundaries sections.

---

## Minimal Template

Use for any project where a lightweight config is sufficient.

```markdown
# Project Name

Brief description of the project.

## Commands

- Build: `make build`
- Test: `make test`
- Lint: `make lint`

## Structure

- `/src` -- Application source code
- `/tests` -- Test suites

## Conventions

- Follow existing code style and patterns
- Write tests for new functionality

## Boundaries

- Always: Run tests before committing
- Ask: Before adding new dependencies
- Never: Commit secrets, credentials, or API keys
```

---

## Node.js / TypeScript Template

```markdown
# Project Name

TypeScript application using pnpm for package management.

## Commands

- Install: `pnpm install`
- Dev: `pnpm dev`
- Build: `pnpm build`
- Test: `pnpm test`
- Lint: `pnpm lint`
- Format: `pnpm format`
- Type check: `pnpm tsc --noEmit`

## Structure

- `/src` -- Application source (TypeScript)
- `/src/types` -- Shared type definitions
- `/tests` -- Test suites (vitest or jest)
- `/scripts` -- Build and utility scripts
- `/dist` -- Compiled output (gitignored)

## Conventions

- Use TypeScript strict mode. No `any` unless justified with a comment.
- Prefer named exports over default exports.
- Use `interface` for object shapes, `type` for unions and intersections.
- Import order: node builtins, external packages, internal modules, relative imports.
- Error handling: throw typed errors, never swallow exceptions silently.
- Use `async/await` over raw promises. Avoid `.then()` chains.

## Testing

- Framework: vitest (or jest)
- Run single file: `pnpm test -- path/to/file.test.ts`
- Coverage: `pnpm test -- --coverage`
- Name test files `*.test.ts` adjacent to source or in `/tests`.
- Mock external dependencies; never hit real APIs in tests.

## Boundaries

- Always: Run `pnpm lint` and `pnpm tsc --noEmit` before committing
- Always: Run tests after modifying logic
- Ask: Before adding production dependencies to `package.json`
- Ask: Before changing tsconfig compiler options
- Never: Modify `pnpm-lock.yaml` manually
- Never: Use `npm` or `yarn` (this project uses pnpm exclusively)

## Troubleshooting

- **Type errors after pulling**: Run `pnpm install` then `pnpm tsc --noEmit`
- **Test timeouts**: Check for missing async/await or unresolved promises
- **Module not found**: Verify path aliases in `tsconfig.json` match import paths
```

---

## Python Template

```markdown
# Project Name

Python application using uv for dependency management.

## Commands

- Install: `uv sync`
- Run: `uv run python -m mypackage`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Type check: `uv run mypy .`

## Structure

- `/src/mypackage` -- Application source
- `/tests` -- Test suites (pytest)
- `/scripts` -- Utility scripts
- `pyproject.toml` -- Project config, dependencies, tool settings

## Conventions

- Python 3.11+ features are allowed.
- Use type hints on all public functions and methods.
- Use `pathlib.Path` over `os.path`.
- Prefer dataclasses or Pydantic models over plain dicts for structured data.
- Use `logging` module, not `print()`, for operational output.
- Docstrings: Google style for public APIs.

## Testing

- Framework: pytest with pytest-asyncio for async tests
- Run single file: `uv run pytest tests/test_specific.py -v`
- Run single test: `uv run pytest tests/test_specific.py::test_name -v`
- Coverage: `uv run pytest --cov=src`
- Fixtures go in `conftest.py` at the appropriate directory level.
- Use `tmp_path` fixture for temp files, never write to project directories.

## Boundaries

- Always: Run `uv run ruff check .` before committing
- Always: Run tests after changing logic
- Ask: Before adding dependencies to `pyproject.toml`
- Ask: Before changing minimum Python version
- Never: Use `pip install` directly (use `uv pip install` or `uv add`)
- Never: Commit `.venv/` or `__pycache__/`

## Troubleshooting

- **Import errors**: Run `uv sync` to ensure dependencies are installed
- **Type errors**: Run `uv run mypy .` and check for missing stubs
- **Test fixtures not found**: Ensure `conftest.py` is in the correct directory
```

---

## Rust Template

```markdown
# Project Name

Rust application managed with Cargo.

## Commands

- Build: `cargo build`
- Test: `cargo test`
- Lint: `cargo clippy -- -D warnings`
- Format check: `cargo fmt -- --check`
- Format: `cargo fmt`
- Run: `cargo run`
- Doc: `cargo doc --open`

## Structure

- `/src` -- Application source
- `/src/lib.rs` -- Library root (if applicable)
- `/src/main.rs` -- Binary entry point
- `/tests` -- Integration tests
- `/benches` -- Benchmarks

## Conventions

- Run `cargo clippy` with `-D warnings` (treat warnings as errors).
- Use `thiserror` for library errors, `anyhow` for application errors.
- Prefer `&str` over `String` in function parameters when ownership is not needed.
- Use `#[must_use]` on functions that return values that should not be ignored.
- Minimize `unsafe`. When required, document the safety invariants.
- Prefer iterators and combinators over manual loops.

## Cross-Compilation

- Targets: list with `rustup target list --installed`
- Add target: `rustup target add aarch64-apple-darwin`
- Build for target: `cargo build --target aarch64-apple-darwin`

## Boundaries

- Always: Run `cargo clippy -- -D warnings` before committing
- Always: Run `cargo test` after modifying logic
- Always: Run `cargo fmt` before committing
- Ask: Before adding dependencies to `Cargo.toml`
- Ask: Before using `unsafe`
- Never: Ignore clippy warnings without documented justification
- Never: Commit `target/` directory

## Troubleshooting

- **Linking errors**: Check that C dependencies are installed (`pkg-config --list-all`)
- **Borrow checker issues**: Consider using `Arc<Mutex<T>>` for shared mutable state
- **Slow builds**: Use `cargo build --release` only for final artifacts; dev builds skip optimizations
```

---

## Go Template

```markdown
# Project Name

Go application using Go modules.

## Commands

- Build: `go build ./...`
- Test: `go test ./...`
- Test verbose: `go test -v ./...`
- Lint: `golangci-lint run`
- Format: `gofmt -w .`
- Vet: `go vet ./...`
- Run: `go run .`

## Structure

- `/cmd` -- Entry points (one subdirectory per binary)
- `/internal` -- Private application code
- `/pkg` -- Public library code (if any)
- `/api` -- API definitions (protobuf, OpenAPI)
- `go.mod` -- Module definition and dependencies

## Conventions

- Follow Effective Go and the Go Code Review Comments guide.
- Error handling: return errors, do not panic. Wrap with `fmt.Errorf("context: %w", err)`.
- Use `context.Context` as the first parameter for functions that do I/O.
- Naming: short, lowercase package names. No underscores or mixedCaps in package names.
- Use table-driven tests with `t.Run()` subtests.
- Interfaces should be small (1-3 methods). Define them where consumed, not where implemented.

## Boundaries

- Always: Run `go vet ./...` and `golangci-lint run` before committing
- Always: Run `go test ./...` after changes
- Ask: Before adding external dependencies
- Ask: Before changing Go version in `go.mod`
- Never: Commit `vendor/` unless the project explicitly vendors dependencies
- Never: Use `init()` functions without documented justification

## Troubleshooting

- **Module errors**: Run `go mod tidy`
- **Import cycle**: Move shared types to a separate package in `/internal`
- **Test cache**: Force re-run with `go test -count=1 ./...`
```

---

## React / Next.js Template

```markdown
# Project Name

Next.js application with React and TypeScript.

## Commands

- Dev: `pnpm dev`
- Build: `pnpm build`
- Start: `pnpm start`
- Test: `pnpm test`
- Lint: `pnpm lint`
- Type check: `pnpm tsc --noEmit`

## Structure

- `/app` -- Next.js App Router pages and layouts
- `/components` -- Reusable React components
- `/components/ui` -- Primitive UI components (buttons, inputs, cards)
- `/lib` -- Utilities, API clients, helpers
- `/hooks` -- Custom React hooks
- `/types` -- Shared TypeScript types
- `/public` -- Static assets
- `/styles` -- Global styles and CSS modules

## Conventions

- Use Server Components by default. Add `"use client"` only when needed (state, effects, browser APIs).
- Components: one component per file, named export matching filename.
- Hooks: prefix with `use`, place in `/hooks`. One hook per file.
- Styling: Tailwind CSS utility classes. Extract repeated patterns to components, not utility classes.
- Data fetching: use Server Components with `fetch()` or server actions. No client-side fetching for initial page data.
- Images: use `next/image` for optimization. Never use raw `<img>` tags.
- Links: use `next/link` for internal navigation.

## Component Guidelines

- Props: define with `interface`, suffix with `Props` (e.g., `ButtonProps`).
- Avoid prop drilling deeper than 2 levels; use Context or composition instead.
- Memoize expensive computations with `useMemo`. Memoize callbacks with `useCallback` only when passed to child components.
- Keep components under 150 lines. Extract logic into hooks or utilities.

## Boundaries

- Always: Run `pnpm lint` and `pnpm tsc --noEmit` before committing
- Always: Test in both dev and production builds (`pnpm dev` and `pnpm build`)
- Ask: Before adding new dependencies
- Ask: Before modifying `next.config.js`
- Ask: Before changing the routing structure in `/app`
- Never: Import server-only code in client components
- Never: Store sensitive data in client-side state or localStorage

## Troubleshooting

- **Hydration mismatch**: Ensure server and client render identical HTML. Check for `typeof window` usage.
- **Build errors with Server Components**: Verify no client hooks (`useState`, `useEffect`) in server components.
- **CSS not applying**: Check Tailwind content paths in `tailwind.config.ts`.
- **Module not found**: Clear `.next` cache with `rm -rf .next && pnpm dev`.
```

---

## Monorepo Template

Root-level AGENTS.md plus subdirectory overrides.

### Root: `/AGENTS.md`

```markdown
# Monorepo Name

Monorepo managed with [pnpm workspaces | turborepo | nx | lerna].

## Commands (Root)

- Install all: `pnpm install`
- Build all: `pnpm build`
- Test all: `pnpm test`
- Lint all: `pnpm lint`
- Build specific: `pnpm --filter <package> build`

## Structure

- `/packages` -- Shared libraries
- `/apps` -- Deployable applications
- `/tools` -- Internal build and dev tools
- `/configs` -- Shared configuration (tsconfig, eslint, prettier)

## Conventions

- Shared dependencies live in the root `package.json`.
- Package-specific dependencies go in each package's `package.json`.
- Cross-package imports use workspace protocol (`"workspace:*"`).
- All packages must pass lint and type check before merging to main.
- Changes to shared packages require running dependent package tests.

## Boundaries

- Always: Run `pnpm build` from root to verify cross-package compatibility
- Always: Run affected tests when modifying shared packages
- Ask: Before creating new packages or apps
- Ask: Before modifying root-level configuration
- Never: Import from another package's internal paths (use the package's public API)
- Never: Add circular dependencies between packages

## Troubleshooting

- **Phantom dependencies**: Run `pnpm install` from root; check for hoisted packages
- **Build order failures**: Verify `dependsOn` in turbo.json or equivalent
- **Type errors across packages**: Rebuild shared packages first (`pnpm --filter shared build`)
```

### Subdirectory: `/apps/web/AGENTS.md`

```markdown
# Web App

Next.js frontend application. Part of the monorepo.

## Commands

- Dev: `pnpm dev` (from this directory)
- Build: `pnpm build`
- Test: `pnpm test`

## Structure

- `/app` -- Next.js App Router
- `/components` -- App-specific components
- `/lib` -- App-specific utilities

## Conventions

- Import shared UI from `@repo/ui` package.
- Import shared types from `@repo/types` package.
- App-specific components stay in this directory, not in shared packages.

## Boundaries

- Always: Test with `pnpm build` (not just dev mode) before deploying
- Never: Duplicate components that exist in `@repo/ui`
```

### Override Example: `/apps/web/AGENTS.override.md`

When you need temporary overrides without editing the base file:

```markdown
# Temporary Override

## Active Migration

We are migrating from Pages Router to App Router. During this migration:

- New pages go in `/app` (App Router), not `/pages`
- Do not modify existing files in `/pages` unless explicitly asked
- Server Components are the default for all new pages
```

Remove `AGENTS.override.md` once the migration is complete to restore the base `AGENTS.md` guidance.
