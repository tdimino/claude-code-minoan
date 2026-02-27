# Visual QA Checklist

After building slides, run a screenshot verification loop using agent-browser.

## Verification Workflow

```
1. Start dev server: npm run dev
2. For each slide, take a screenshot:
   agent-browser open http://localhost:3200
   agent-browser scroll down [slide_number * 720]
   agent-browser screenshot /tmp/slide-N.png
3. Read each screenshot and check against the table below
4. Fix issues, re-screenshot, verify
```

## Common Visual Bugs

| Issue | Symptom | Fix |
|-------|---------|-----|
| Icon ring overlap | Decorative icons cover heading text | Use elliptical dimensions (1000x600 for 16:9), push to 48% radius, add `opacity-50` |
| GlowBadge inline disproportion | Badge text 16px inside 12px body text | Use `size="sm"` for inline badges (`text-xs px-2 py-0.5`) |
| StatsBar extends beyond cards | Footer bar wider than content area above | Use `mt-auto` (in-flow), not `absolute bottom-0 left-0 right-0` |
| Unreadable yellow on white | `#fbbf24` invisible against `#FAFBFC` background | Darken to `#B45309` (amber-700) or `#D97706` (amber-600) |
| Red alarm on light background | `#DC2626` or `#E11D48` reads as error/danger state | Replace with `#92400E` (amber-800) or brand-aligned color |
| Monochrome card grids | All 3+ cards same color looks flat and monotonous | Assign distinct accent per card, match StatsBar colors |
| TOC titles not vertically centered | Title sits at top of variable-height cards | Wrap title in `flex-1 flex flex-col items-center justify-center` |
| Decorative elements clipping | Elements positioned near slide edges get cut off | Check element dimensions against 1280x720 bounds, add safe margins |
| Logo wrong variant for theme | White logo invisible on light backgrounds | Use `aldea-logo-black.png` for light mode, `aldea-logo.png` for dark |
| Chapter badge color mismatch | Badge uses hardcoded cyan instead of chapter color | Pass `chapterColor` prop to SlideLayout, style badge dynamically |

## Color Readability Quick Reference

Minimum color darkness for light backgrounds (`#FAFBFC`, `#FFFFFF`, etc.):

| Color Family | Minimum Safe Value | Notes |
|-------------|-------------------|-------|
| Yellows | `#B45309` (amber-700) | Anything lighter than amber-700 disappears on white |
| Reds | `#92400E` (amber-800) | Avoid pure reds on light -- they read as error/danger state |
| Greens | `#059669` (emerald-600) | Works well; `#34d399` (emerald-400) too light |
| Blues | `#1E3A8A` (blue-800) | Use blue-800 or darker for reliable contrast |
| Violets | `#7C3AED` (violet-600) | Works well on light backgrounds |
| Browns | `#78350F` (amber-900) | Works well on light backgrounds |
