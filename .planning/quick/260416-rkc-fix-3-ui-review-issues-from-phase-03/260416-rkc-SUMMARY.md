---
phase: quick
plan: 260416-rkc
subsystem: theme/arcaeon
tags: [ui-fix, section-triad, og-meta, css-layout]
dependency_graph:
  requires: [03-dynamic-layer-quality]
  provides: [corrected-triad-alternation, resilient-og-dimensions, compact-currently-card]
  affects: [themes/arcaeon/layouts, themes/arcaeon/assets/css]
tech_stack:
  added: []
  patterns: [void-depth alternation, Hugo image dimension introspection, margin-inline centering]
key_files:
  modified:
    - themes/arcaeon/layouts/partials/sections/identity-cta.html
    - themes/arcaeon/layouts/partials/sections/social.html
    - themes/arcaeon/layouts/partials/sections/footer.html
    - themes/arcaeon/layouts/_default/baseof.html
    - themes/arcaeon/assets/css/main.css
decisions:
  - OG dimensions now derived from $ogImg.Width/$ogImg.Height — resilient to future source image changes without requiring template edits
  - margin-inline: auto used instead of margin: 0 auto — more explicit intent, no vertical margin side effect
metrics:
  duration: 8min
  completed: 2026-04-16
  tasks: 2
  files: 5
---

# Quick Task 260416-rkc: Fix 3 UI Review Issues from Phase 03 — Summary

**One-liner:** Three targeted fixes restoring void-depth-void-depth-void section triad, making OG image dimensions template-derived, and constraining the Currently card to 32rem on desktop.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Fix section triad alternation and OG image dimensions | 52718ad | identity-cta.html, social.html, footer.html, baseof.html |
| 2 | Constrain Currently card max-width on desktop | 97fd7d5 | main.css |

## What Was Done

**Task 1** corrected the void-depth alternation across the final three sections. The triad had two consecutive `section-depth` sections (identity-cta and social running back-to-back as depth), which broke the D-05 visual rhythm. Swapped identity-cta to `section-void`, social to `section-depth`, footer to `section-void`. Also replaced hardcoded `content="1200"` and `content="630"` OG dimension strings with `{{ $ogImg.Width }}` and `{{ $ogImg.Height }}` so the values derive from Hugo's image processing result rather than manual maintenance.

**Task 2** added `max-width: 32rem` and `margin-inline: auto` to `.currently-card`. The section-content container is 56rem wide on desktop — without a max-width the card spans the full container. At 32rem it reads as a compact content unit, centered via margin-inline. On mobile (375px), 32rem exceeds the viewport so the card fills available width naturally with no media query required.

## Verification

Hugo build: clean, zero errors.

Rendered triad order (from `grep -oE 'section-(void|depth)' public/index.html | head -5`):
```
section-void    ← hero
section-depth   ← currently
section-void    ← identity-cta
section-depth   ← social
section-void    ← footer
```

OG meta in rendered HTML:
```html
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
```
Values are template-derived (1200×630 matches `.Fill "1200x630 Center"` — correct).

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Self-Check: PASSED

- identity-cta.html modified: confirmed (section-void present in rendered output)
- social.html modified: confirmed (section-depth present in rendered output)
- footer.html modified: confirmed (section-void present in rendered output)
- baseof.html modified: confirmed ($ogImg.Width/$ogImg.Height in source)
- main.css modified: confirmed (max-width: 32rem + margin-inline: auto in .currently-card)
- Commit 52718ad: confirmed
- Commit 97fd7d5: confirmed
