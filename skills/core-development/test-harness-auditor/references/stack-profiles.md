# Stack Profiles

Per-stack detection rules and tool recommendations for the 5 first-class stacks.

## JavaScript / TypeScript

| Layer | Tool | Detection | Strict Mode | Command |
|-------|------|-----------|-------------|---------|
| **Manifest** | npm/yarn/pnpm/bun | `package.json`, `yarn.lock`, `pnpm-lock.yaml`, `bun.lockb` | — | — |
| **Test** | Vitest / Jest / Mocha | `vitest` in deps, `jest` in deps, `mocha` in deps | — | `npx vitest run`, `npx jest`, `npx mocha` |
| **Lint** | ESLint | `.eslintrc*`, `eslint.config.*`, `eslint` in deps | — | `npx eslint .` |
| **Type** | TypeScript | `tsconfig.json`, `typescript` in deps | `"strict": true` in tsconfig | `npx tsc --noEmit` |
| **SA** | npm-audit | `package-lock.json` | — | `npm audit` |
| **Build** | tsc / esbuild / vite | `build` script in package.json | — | `npm run build` |
| **Debug** | Node inspector | `node` binary | — | `node --inspect` |
| **Mutation** | Stryker | `@stryker-mutator/core` in deps | — | `npx stryker run` |

### Detection Logic

```
if package.json exists:
  stack = "javascript"
  if tsconfig.json exists OR typescript in deps:
    stack = "typescript"
  frameworks: check deps for react, vue, svelte, next, express, fastify, nest
  test_runner: first of vitest, jest, mocha, ava, tap in deps
  linter: eslint in deps OR .eslintrc* exists OR eslint.config.* exists
  type_strict: tsconfig.json → strict === true
  build_cmd: scripts.build in package.json
```

## Rust

| Layer | Tool | Detection | Strict Mode | Command |
|-------|------|-----------|-------------|---------|
| **Manifest** | Cargo | `Cargo.toml`, `Cargo.lock` | — | — |
| **Test** | cargo test | built-in | — | `cargo test` |
| **Lint** | Clippy | `clippy` in components (`rustup component list`) | `#![deny(clippy::all)]` | `cargo clippy` |
| **Type** | rustc | built-in (strong typing) | — | `cargo check` |
| **SA** | cargo-audit | `cargo-audit` binary | — | `cargo audit` |
| **Build** | cargo build | built-in | — | `cargo build` |
| **Debug** | rust-gdb / lldb | `rust-gdb` or `lldb` binary | — | `rust-gdb target/debug/binary` |
| **Mutation** | cargo-mutants | `cargo-mutants` binary | — | `cargo mutants` |

### Detection Logic

```
if Cargo.toml exists:
  stack = "rust"
  workspace: [workspace] section in Cargo.toml
  crate_name: name field in [package]
  clippy_strict: grep for deny(clippy in src/**/*.rs
  has_tests: grep for #[test] or #[cfg(test)] in src/
  audit_available: which cargo-audit
```

## Python

| Layer | Tool | Detection | Strict Mode | Command |
|-------|------|-----------|-------------|---------|
| **Manifest** | pip/poetry/uv | `pyproject.toml`, `setup.py`, `setup.cfg`, `requirements.txt` | — | — |
| **Test** | pytest / unittest | `pytest` in deps, `tests/` dir | — | `pytest`, `python -m pytest` |
| **Lint** | Ruff / flake8 / pylint | `ruff.toml`, `.flake8`, `ruff` in deps | — | `ruff check .` |
| **Type** | mypy / pyright | `mypy.ini`, `.mypy.ini`, `pyrightconfig.json`, mypy in deps | `strict = true` in mypy config | `mypy .`, `pyright` |
| **SA** | bandit / safety | `bandit` binary, `safety` binary | — | `bandit -r .`, `safety check` |
| **Build** | setuptools / hatch | `build-system` in pyproject.toml | — | `python -m build` |
| **Debug** | pdb / ipdb | built-in / `ipdb` in deps | — | `python -m pdb script.py` |
| **Mutation** | mutmut | `mutmut` in deps or binary | — | `mutmut run` |

### Detection Logic

```
if pyproject.toml OR setup.py OR requirements.txt exists:
  stack = "python"
  test_runner: pytest in deps OR tests/ directory exists
  linter: first of ruff.toml, ruff in deps, .flake8, pylint in deps
  type_checker: mypy in deps OR pyrightconfig.json exists
  type_strict: mypy config → strict = true
  has_bandit: which bandit
```

## Go

| Layer | Tool | Detection | Strict Mode | Command |
|-------|------|-----------|-------------|---------|
| **Manifest** | Go modules | `go.mod`, `go.sum` | — | — |
| **Test** | go test | built-in | — | `go test ./...` |
| **Lint** | golangci-lint | `.golangci.yml`, `golangci-lint` binary | — | `golangci-lint run` |
| **Type** | go vet | built-in (strong typing) | — | `go vet ./...` |
| **SA** | govulncheck | `govulncheck` binary | — | `govulncheck ./...` |
| **Build** | go build | built-in | — | `go build ./...` |
| **Debug** | Delve | `dlv` binary | — | `dlv debug` |
| **Mutation** | go-mutesting | `go-mutesting` binary | — | `go-mutesting ./...` |

### Detection Logic

```
if go.mod exists:
  stack = "go"
  test_files: *_test.go files exist
  linter: .golangci.yml exists OR which golangci-lint
  has_govulncheck: which govulncheck
  has_delve: which dlv
```

## Ruby

| Layer | Tool | Detection | Strict Mode | Command |
|-------|------|-----------|-------------|---------|
| **Manifest** | Bundler | `Gemfile`, `Gemfile.lock` | — | — |
| **Test** | RSpec / Minitest | `rspec` in Gemfile, `spec/` dir, `test/` dir | — | `bundle exec rspec`, `bundle exec rails test` |
| **Lint** | RuboCop | `.rubocop.yml`, `rubocop` in Gemfile | — | `bundle exec rubocop` |
| **Type** | Sorbet / Steep | `sorbet/` dir, `steep` in Gemfile | `# typed: strict` | `bundle exec srb tc` |
| **SA** | bundler-audit / brakeman | `bundler-audit` or `brakeman` in Gemfile | — | `bundle exec bundler-audit`, `bundle exec brakeman` |
| **Build** | rake | `Rakefile` | — | `bundle exec rake build` |
| **Debug** | IRB / Pry / debug | built-in / `pry` in Gemfile / `debug` in Gemfile | — | `bundle exec irb` |
| **Mutation** | mutant | `mutant` in Gemfile | — | `bundle exec mutant run` |

### Detection Logic

```
if Gemfile exists:
  stack = "ruby"
  framework: rails in Gemfile (check for railties or rails gem)
  test_runner: rspec in Gemfile OR spec/ exists, minitest via test/ exists
  linter: .rubocop.yml exists OR rubocop in Gemfile
  type_checker: sorbet/ dir OR steep in Gemfile
  has_brakeman: brakeman in Gemfile (Rails security)
```

## Generic Detection (Other Stacks)

For stacks not in the first-class list, detect basics:
- **Manifest**: any of `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`, `Gemfile`, `pom.xml`, `build.gradle`, `CMakeLists.txt`, `Makefile`
- **CI**: `.github/workflows/`, `.gitlab-ci.yml`, `.circleci/`, `Jenkinsfile`
- **Test command**: look for `test` script in manifest or `test/`/`tests/`/`spec/` directories
- **Lint config**: any `.*rc`, `.*lint*`, `*.config.*` files

Score generically: if manifest exists (1), if CI exists (+1), if test dir/command exists (+1).
