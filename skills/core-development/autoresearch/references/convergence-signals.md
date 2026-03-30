# Convergence Signals

Nine soft signals the runner checks after every experiment. These are advisory—they inform strategy adjustments, not hard state transitions. The runner logs which signals are active and includes them in the eval-report.

Adapted from [ResearcherSkill](https://github.com/krzysztofdudek/ResearcherSkill) v1.1.0 (March 2026).

## The 9 Signals

### 1. Consecutive Discards (5+)

**Signal:** 5 or more DISCARD results in a row.

**What it means:** The current approach is exhausted. The agent is making changes that don't improve the composite, suggesting the remaining improvement surface requires a fundamentally different strategy.

**Response:** Try a radically different hypothesis. If the last 5 experiments were all in the same code area, explore a different area entirely. Consider reading the dead-ends list for patterns.

### 2. Metric Plateau (<0.5% over 5 KEEPs)

**Signal:** The last 5 KEEP results improved the composite by less than 0.5% total.

**What it means:** Diminishing returns. The easy wins are captured, and further improvement requires disproportionate effort for marginal gain.

**Response:** Either declare the run successful and stop, or make a dramatic change in strategy (new tier of gates, new metric dimension, restructure the program.md priorities).

### 3. Same Code Area Modified 3+ Times

**Signal:** 3 or more consecutive experiments touched files in the same directory or module.

**What it means:** Over-optimization of one area at the expense of the whole. Like watering one plant in a garden while the rest dry out.

**Response:** Explicitly target a different part of the codebase. Check which gate tiers have the lowest scores and focus there.

### 4. Alternating Keep/Discard on Similar Changes

**Signal:** The last 4+ results alternate K-D-K-D, and the experiments describe similar approaches.

**What it means:** The agent is oscillating between two approaches without converging. One change improves the metric, the next undoes it.

**Response:** Isolate the variable. Run a smaller, more targeted experiment that changes only one thing instead of making broad modifications.

### 5. Two or More Consecutive Timeouts

**Signal:** 2+ experiments in a row hit the timeout limit.

**What it means:** The approach is computationally expensive or the implementation is hitting an infinite loop / deadlock.

**Response:** Reassess the experiment design. The hypothesis might be generating code that takes too long to build or test. Simplify the approach or increase the timeout if justified.

### 6. Three or More Consecutive Crashes

**Signal:** 3+ experiments crash (eval infrastructure failure, not just low scores).

**What it means:** Something is structurally wrong. The eval.py itself might be broken, or the build system is in a bad state.

**Response:** Stop the loop. Fix the eval infrastructure before continuing. Running more experiments will just produce more crashes.

### 7. Thought Experiments Repeating

**Signal:** The hypothesis generator suggests the same idea it already tried (detected via description similarity).

**What it means:** The agent has run out of novel ideas within its current understanding of the problem.

**Response:** Inject new information. Update program.md with new hypothesis directions, read the codebase more carefully, or add new eval gates that expose previously unmeasured dimensions.

### 8. Results Contradict Theory

**Signal:** An experiment that the hypothesis predicted would improve the score actually made it worse, and vice versa.

**What it means:** The agent's model of how the code works is wrong. The assumptions driving hypothesis generation are inaccurate.

**Response:** Go back to reading the code. The agent needs to understand the actual behavior before proposing changes. An "INTERESTING" status is appropriate here.

### 9. Branch Stagnating While Other Thrives

**Signal:** The current branch has 3+ discards while a different branch (visible in results.tsv parent column) has recent keeps.

**What it means:** This branch hit a local optimum, but the alternative branch found a better trajectory.

**Response:** Fork from the thriving branch or switch to it entirely. Mark the current branch as `closed` in branches.md.

## How the Runner Uses These

After each experiment, the runner scans the last N results in `.lab/results.tsv` and checks each signal. Active signals are:
1. Logged to `.lab/log.md`
2. Included in `.lab/eval-report.md`
3. Passed to the hypothesis generator as context (so it can adjust strategy)

No signal causes automatic termination. The runner logs them and continues. The hypothesis generator is expected to adjust its strategy based on active signals.
