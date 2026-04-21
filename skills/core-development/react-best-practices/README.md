# React Best Practices

40+ performance optimization rules for React and Next.js applications, prioritized by impact across 8 categories. Sourced from Vercel Engineering guidelines.

**Last updated:** 2026-04-21

---

## Why This Skill Exists

React performance pitfalls (waterfalls, barrel imports, unnecessary re-renders) are easy to introduce and hard to spot in review. This skill provides a priority-ordered ruleset that Claude can reference when writing, reviewing, or refactoring React/Next.js code---applying the highest-impact patterns first.

---

## Structure

```
react-best-practices/
  SKILL.md                                     # Quick reference and priority table
  README.md                                    # This file
  references/
    react-performance-guidelines.md            # Complete guide with code examples
```

---

## Priority Categories

| Priority | Category | Impact |
|----------|----------|--------|
| 1 | Eliminating Waterfalls | CRITICAL |
| 2 | Bundle Size Optimization | CRITICAL |
| 3 | Server-Side Performance | HIGH |
| 4 | Client-Side Data Fetching | MEDIUM-HIGH |
| 5 | Re-render Optimization | MEDIUM |
| 6 | Rendering Performance | MEDIUM |
| 7 | JavaScript Performance | LOW-MEDIUM |
| 8 | Advanced Patterns | LOW |

---

## When to Apply

- Writing new React components or Next.js pages
- Reviewing code for performance issues
- Refactoring existing React/Next.js code
- Optimizing bundle size or load times
- Implementing data fetching (client or server-side)

---

## Key Patterns

**Critical:** `Promise.all()` for independent async ops, avoid barrel file imports, use `next/dynamic` for heavy components, Suspense boundaries for streaming.

**High:** `React.cache()` for per-request dedup, LRU cache for cross-request, parallelize data fetching with component composition.

**Medium:** SWR for request dedup, lazy state initialization, `startTransition` for non-urgent updates, `content-visibility: auto` for long lists.

See `references/react-performance-guidelines.md` for the complete guide with code examples.

---

## Requirements

- No dependencies---this is a reference skill (guidelines only, no scripts)

---

## Part of Claude-Code-Minoan

This skill is part of [claude-code-minoan](https://github.com/tdimino/claude-code-minoan)---curated Claude Code configuration including skills, MCP servers, slash commands, and CLI tools.

Install:

```bash
cp -r skills/core-development/react-best-practices ~/.claude/skills/
```
