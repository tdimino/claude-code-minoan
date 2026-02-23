# CLAUDE.md Templates by Project Type

Ready-to-customize templates for common project types. Copy, adapt, and trim to fit the project.

## Table of Contents
- [Minimal Template](#minimal-template)
- [Node.js/TypeScript](#nodejstypescript)
- [Python](#python)
- [Ruby/Rails](#rubyrails)
- [Go](#go)
- [Rust](#rust)
- [React/Next.js](#reactnextjs)
- [Monorepo](#monorepo)
- [Monorepo with Rules](#monorepo-with-rules)

## Minimal Template

For simple projects. Under 30 lines.

```markdown
# Project Name

Brief description.

## Stack
- Language/Framework
- Key dependencies

## Commands
- Dev: `command`
- Test: `command`
- Build: `command`

## Conventions
- Key convention 1
- Key convention 2
```

---

## Node.js/TypeScript

```markdown
# Project Name

[One-line description]

## Stack
- Node.js 20 LTS with TypeScript 5.x
- [Framework: Express/Fastify/Hono]
- [Database: Prisma/Drizzle + Postgres/SQLite]
- [Package manager: pnpm/npm/bun]

## Structure
- `src/` - Application code
- `src/routes/` - API endpoints
- `src/services/` - Business logic
- `src/lib/` - Shared utilities
- `tests/` - Test suites

## Commands
- Dev: `pnpm dev`
- Test: `pnpm test`
- Build: `pnpm build`
- Types: `pnpm typecheck`

## Conventions
- Strict TypeScript (no `any`)
- Functional style, avoid classes
- Errors via Result types, not exceptions
- Tests required for new features

## Git
- Branch: `feat/description` or `fix/description`
- Commits: Conventional format
- Squash merge to main
```

---

## Python

```markdown
# Project Name

[One-line description]

## Stack
- Python 3.11+
- [Framework: FastAPI/Django/Flask]
- [ORM: SQLAlchemy/Django ORM]
- uv for dependency management

## Structure
- `src/` - Application code
- `src/api/` - API endpoints
- `src/models/` - Data models
- `src/services/` - Business logic
- `tests/` - Pytest suites

## Commands
- Dev: `uv run uvicorn src.main:app --reload`
- Test: `uv run pytest`
- Lint: `uv run ruff check .`
- Format: `uv run ruff format .`
- Types: `uv run mypy src/`

## Conventions
- Type hints required (strict mypy)
- Pydantic for validation
- Async by default
- Docstrings for public APIs

## Git
- Branch: `feature/description`
- Use Conventional Commits
- Rebase before merge
```

---

## Ruby/Rails

```markdown
# Project Name

[One-line description]

## Stack
- Ruby 3.3+ / Rails 7.x
- PostgreSQL
- Hotwire (Turbo + Stimulus)
- [Background: Sidekiq/GoodJob]

## Structure
- Standard Rails conventions
- `app/services/` - Service objects
- `app/components/` - ViewComponents
- `lib/` - Non-Rails code

## Commands
- Dev: `bin/dev`
- Console: `bin/rails c`
- Test: `bin/rails test` or `bundle exec rspec`
- Migrate: `bin/rails db:migrate`

## Conventions
- Prefer Rails conventions over configuration
- Service objects for complex business logic
- No concerns (extract to modules/classes)
- System tests for critical paths

## Git
- Branch from main
- Squash merge
- Conventional Commits
```

---

## Go

```markdown
# Project Name

[One-line description]

## Stack
- Go 1.22+
- [Framework: stdlib/Chi/Gin/Echo]
- [Database: sqlc/GORM/ent]

## Structure
- `cmd/` - Entry points
- `internal/` - Private packages
- `pkg/` - Public packages
- `api/` - API definitions

## Commands
- Dev: `go run ./cmd/server`
- Test: `go test ./...`
- Build: `go build -o bin/app ./cmd/server`
- Lint: `golangci-lint run`

## Conventions
- Accept interfaces, return structs
- Errors are values, handle explicitly
- Table-driven tests
- No globals (dependency injection)

## Git
- Branch: `feat/description`
- Squash to main
```

---

## Rust

```markdown
# Project Name

[One-line description]

## Stack
- Rust stable (1.75+)
- [Framework: Axum/Actix/Rocket]
- [Async: Tokio]
- Cargo workspace (if applicable)

## Structure
- `src/` - Library/application code
- `src/bin/` - Binary entry points
- `tests/` - Integration tests
- `benches/` - Benchmarks

## Commands
- Dev: `cargo run`
- Test: `cargo test`
- Check: `cargo clippy`
- Format: `cargo fmt`
- Doc: `cargo doc --open`

## Conventions
- Prefer `thiserror` for errors
- Use `#[must_use]` on important returns
- Document public APIs

## Git
- Feature branches
- Squash merge
- Clippy must pass
```

---

## React/Next.js

```markdown
# Project Name

[One-line description]

## Stack
- Next.js 14+ (App Router)
- TypeScript strict mode
- [Styling: Tailwind/CSS Modules]
- [State: React Query/Zustand]

## Structure
- `app/` - Routes and layouts (App Router)
- `components/` - React components
- `lib/` - Utilities and helpers
- `hooks/` - Custom hooks
- `types/` - TypeScript types

## Commands
- Dev: `pnpm dev`
- Build: `pnpm build`
- Test: `pnpm test`
- Lint: `pnpm lint`

## Conventions
- Server Components by default
- Client components: `'use client'` only when needed
- Colocation: page-specific components near routes
- Prefer server actions over API routes

## Git
- Feature branches
- Conventional Commits
- Preview deploys on PR
```

---

## Monorepo

```markdown
# Project Name

[One-line description]

## Stack
- Turborepo/Nx/pnpm workspaces
- [See individual apps for stack details]

## Structure
- `apps/web/` - Next.js frontend
- `apps/api/` - Backend service
- `packages/ui/` - Shared components
- `packages/utils/` - Shared utilities
- `packages/config/` - Shared config (ESLint, TS)

## Commands
- Dev all: `pnpm dev`
- Dev specific: `pnpm --filter web dev`
- Build: `pnpm build`
- Test: `pnpm test`
- Add dep: `pnpm --filter <package> add <dep>`

## Conventions
- Shared code in `packages/`
- Apps import from packages, not each other
- Root commands run across all packages
- Filter to specific package for isolated work

## App-Specific Docs
- Frontend conventions and component patterns: @apps/web/CLAUDE.md
- Backend API design and database conventions: @apps/api/CLAUDE.md

## Git
- Feature branches
- Required checks before merge
- Conventional Commits with scope (e.g., `feat(web):`)
```

---

## Monorepo with Rules

Alternative monorepo pattern using `.claude/rules/` for path-specific instructions instead of nested CLAUDE.md files.

```
project/
  CLAUDE.md                    # Universal conventions only
  .claude/rules/
    frontend.md                # paths: ["apps/web/**", "packages/ui/**"]
    backend.md                 # paths: ["apps/api/**", "packages/db/**"]
    testing.md                 # paths: ["**/*.test.*", "**/*.spec.*"]
```

Example rule file (`.claude/rules/frontend.md`):

```yaml
---
paths:
  - "apps/web/**"
  - "packages/ui/**"
---
## Frontend Conventions
- Server Components by default, `'use client'` only when needed
- Colocation: page-specific components near routes
- Tailwind for styling, no CSS modules
- Component tests required in `__tests__/` alongside source
```

The root CLAUDE.md stays minimal — stack, commands, git conventions. Path-specific instructions live in rules files and load only when editing matching files.

```markdown
# Project Name

[One-line description]

## Stack
- Turborepo with pnpm workspaces
- See .claude/rules/ for app-specific conventions

## Commands
- Dev all: `pnpm dev`
- Dev specific: `pnpm --filter web dev`
- Build: `pnpm build`
- Test: `pnpm test`

## Conventions
- Shared code in `packages/`
- Apps import from packages, not each other

## Git
- Feature branches
- Conventional Commits with scope (e.g., `feat(web):`)
```

---

## Usage Tips

1. **Start minimal** - Copy the smallest applicable template
2. **Remove unused sections** - Delete anything not relevant
3. **Add project specifics** - Custom conventions, unusual patterns
4. **Test commands** - Verify all commands actually work
5. **Iterate** - Refine based on Claude's behavior

## Customization Checklist

After copying a template:
- [ ] Update project name and description
- [ ] Verify tech stack matches the project
- [ ] Confirm directory structure is accurate
- [ ] Test all listed commands
- [ ] Add project-specific conventions
- [ ] Remove sections that don't apply
- [ ] Keep under 100 lines (ideally under 60)
