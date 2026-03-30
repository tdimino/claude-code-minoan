# The Five Autoresearch Invariants

These invariants are non-negotiable. Violating any one of them produces runs that either waste iterations, produce false improvements, or corrupt the experiment record.

## 1. Single Mutable Surface

Each iteration changes exactly one thing. Not "implement feature X and also refactor Y." One hypothesis, one implementation, one eval. If the composite improves, you know exactly what caused it. If you change two things and the score goes up, you don't know which change mattered—or if one improvement is masking a regression from the other.

**Anti-pattern:** "While I'm in this file, let me also clean up the imports." Don't. That's a separate experiment.

## 2. Fixed Eval Budget

The eval runs in bounded, predictable time with no external dependencies. No network calls, no database queries, no LLM judges. If eval takes 10 seconds on iteration 1, it takes ~10 seconds on iteration 50. If eval is stochastic (different scores on the same code), the runner will thrash between KEEP and DISCARD on noise.

**Anti-pattern:** "Let's add an LLM judge to evaluate code quality." No. The eval must be deterministic and programmatic. If you need qualitative judgment, encode it as a countable metric (e.g., count `#[test]` functions instead of asking an LLM if there are enough tests).

## 3. One Scalar Metric

The composite score is a single number in [0, 1]. The runner doesn't reason about multi-dimensional trade-offs—it sees one number and compares it to the previous best. If composite >= baseline + threshold, KEEP. Otherwise, DISCARD.

This is deliberate. Multi-objective optimization requires Pareto frontiers and human judgment calls. A single scalar metric makes the loop mechanical and trustworthy.

**The `KEEP*` status**: When the primary composite improves but a secondary metric regresses, log it as `KEEP*` to flag the trade-off. But the keep/discard decision is still driven by the single composite.

## 4. Binary Keep/Discard

No "partial keeps." No "let me keep some of this change but revert that part." The experiment either improved the composite or it didn't. If it did, the commit stays. If it didn't, `git reset --hard HEAD~1` reverts the entire commit.

The `INTERESTING` status is an exception: the experiment didn't improve the score, but the result reveals structural information about the problem. The code is still reverted, but the insight is logged to `.lab/dead-ends.md` so the agent doesn't retry the same approach.

## 5. Git-as-Memory

Every experiment is a git commit. Every discard is a git revert. The experiment history is the git log plus `.lab/results.tsv`. There is no other state.

This means:
- You can always `git log` to see what was tried
- You can always `git diff HEAD~1` to see what a specific experiment changed
- You can always `git reset --hard` to a known-good state
- The `.lab/` directory (gitignored) holds the experiment knowledge that survives reverts

**Why `.lab/` is gitignored:** Because `git reset --hard HEAD~1` would destroy the experiment log if it were tracked. Code state and experiment knowledge must be decoupled.
