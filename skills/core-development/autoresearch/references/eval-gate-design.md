# Adversarial Eval Gate Design

How to write eval gates that actually measure implementation quality. The core principle: **stubs must fail**. If an empty file, a keyword-stuffed comment, or a no-op function can pass your gate, the gate is worthless.

## Anti-Cheat Patterns

### 1. Run real commands, not grep

Bad: `grep -c "fn main" src/main.rs` (passes if the string exists anywhere)
Good: `cargo build 2>&1` (actually compiles the code)

### 2. Validate output content, not file existence

Bad: `os.path.exists("output.json")` (empty file passes)
Good: `json.loads(Path("output.json").read_text()); assert len(data["results"]) > 0`

### 3. Count assertions, not test files

Bad: `len(glob.glob("tests/*.py"))` (empty test files pass)
Good: `sum(1 for f in glob("**/*.py") for line in open(f) if "assert" in line or "def test_" in line)`

### 4. Sum passed counts across ALL result lines

Lesson from shadow-engine eval_v5: `re.search(r"(\d+) passed", output)` matched only the last occurrence (doc-tests: 1 passed), not the total. Fix: `sum(int(m.group(1)) for m in re.finditer(r"(\d+) passed", output))`.

### 5. Check exit codes AND parse output

Bad: `subprocess.run(cmd).returncode == 0` (some tools exit 0 on warnings)
Good: `r = run_command(cmd); r.returncode == 0 and "warning" not in r.stderr.lower()`

### 6. Use percentage thresholds, not absolute numbers

Bad: `test_count >= 400` (only works for one specific repo)
Good: `test_count >= baseline_count * 0.95` (works for any repo, catches regressions)

## Gate Tiers

### Tier 1: Build + Test (weight 0.20)

These are table stakes. If the code doesn't compile and tests don't pass, nothing else matters.

- **build**: Run the build command, check exit code 0
- **tests**: Run the test command, sum passed counts, compare to baseline
- **lint**: Run the lint command, check exit code 0, count warnings

### Tier 2: Behavioral (weight 0.40)

The highest-weighted tier. These test that the code actually *does* something.

- **CLI invocation**: Run the program with known inputs, validate output
- **Integration tests**: Run specific test suites that exercise real behavior
- **Import smoke test**: For libraries, verify the package imports without errors
- **Output validation**: Check that output files contain expected content

### Tier 3: Pipeline (weight 0.25)

Tests that the code produces real artifacts and can be distributed.

- **Build artifacts**: Check that `npm pack` / `pip install .` / `cargo install` succeeds
- **Artifact size**: Verify output files are >1KB (not empty stubs)
- **Header validation**: Check magic bytes, file signatures, schema conformance

### Tier 4: Documentation (weight 0.15)

Tests that the code is documented and the documentation is accurate.

- **Test count floor**: Number of test functions >= 90% of baseline
- **Doc coverage**: Percentage of public functions with docstrings
- **Doc-code cross-reference**: Claims in docs match actual code (count functions, not trust comments)

## The Three-Tier Output Protocol

Every gate emits structured diagnostics to stderr:

```
GATE build=PASS              # Binary pass/fail for the runner
METRIC test_count=475        # Continuous value tracked over time
TRACE build_duration_ms=3200 # Execution data for debugging
```

The runner reads GATE lines to determine crashed gates. METRIC lines feed into results.tsv for trend analysis. TRACE lines are for human debugging only.

## Common Mistakes

1. **LLM judges**: "Ask GPT to rate the code quality 1-10." No. LLM judges are stochastic, expensive, and gameable. Use programmatic gates only.

2. **Network-dependent gates**: "Check if the API returns 200." What if the network is down? Gate fails through no fault of the code. All gates must be local and deterministic.

3. **Time-dependent gates**: "Check if the build takes less than 30 seconds." Build time varies by machine load. Use pass/fail, not timing.

4. **Trusting file existence**: `Path("README.md").exists()` proves nothing. Read the file, check it has content, verify it describes the actual project.

5. **Hardcoded thresholds**: `test_count >= 400` works for exactly one repo at one point in time. Use ratios and baselines.
