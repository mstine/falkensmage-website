---
phase: 02-static-content
plan: "01"
subsystem: ui
tags: [hugo, css, html, image-pipeline, webp, arcaeon]

# Dependency graph
requires:
  - phase: 01-theme-foundation
    provides: CSS design system (glow classes, section classes, display-text, ARCAEON tokens, sigil grammar)

provides:
  - content/_index.md with full front matter data layer (all Phase 2 section content)
  - hero.html partial with Hugo picture element (WebP + JPEG, mobile fill 750x580, desktop resize 1200px)
  - identity-cta.html partial with front-matter-driven identity statement and mailto CTA
  - Hero and identity+CTA section CSS appended to main.css
  - index.html wired to render hero and identity-cta partials

affects: [02-02-social-links, 02-03-footer-currently, 03-dynamic-rss, 04-production-deploy]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hugo picture element with art direction: mobile .Fill crop + desktop .Resize, both with .Process webp"
    - "Section partial pattern: partial sections/{name}.html wired through index.html define main block"
    - "Front matter as content data layer: all copy sourced from _index.md params, zero hardcoded strings in partials"

key-files:
  created:
    - themes/arcaeon/layouts/partials/sections/hero.html
    - themes/arcaeon/layouts/partials/sections/identity-cta.html
  modified:
    - content/_index.md
    - themes/arcaeon/assets/css/main.css
    - themes/arcaeon/layouts/index.html

key-decisions:
  - "Hugo .Process 'webp' used (not .Format 'webp') — .Format errors in Hugo 0.160.1, .Process is the correct API"
  - "loading=eager on hero img — above fold, must not lazy-load (minification strips quotes, attribute still present)"
  - "No target=_blank on mailto link — native OS protocol handler per threat model T-02-02"
  - "Identity statement and tagline are voice-matched ship-ready placeholders, not broken stubs — replaceable via front matter"

patterns-established:
  - "Partial wiring: index.html uses partial 'sections/{name}.html' . for each page section"
  - "Content data: all copy lives in content/_index.md front matter, partials use .Params.{key}"
  - "Image pipeline: resources.Get + .Fill/.Resize + .Process webp for responsive picture elements"

requirements-completed: [HERO-01, HERO-02, HERO-03, HERO-04, IDENT-01, IDENT-02, CTA-01, CTA-02]

# Metrics
duration: 8min
completed: 2026-04-16
---

# Phase 2 Plan 01: Hero + Identity+CTA Summary

**Hugo picture pipeline with WebP/JPEG art direction, front-matter data layer for all Phase 2 content, and identity+CTA section with Radiant Core mailto CTA**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-16T17:41:14Z
- **Completed:** 2026-04-16T17:49:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Full content data layer in `_index.md` — all eight social platforms, identity statement, tagline, CTA copy, footer closing wired as front matter params
- Hero section with Hugo `<picture>` element: mobile `.Fill "750x580 Center"` + WebP variant, desktop `.Resize "1200x q85"` + WebP variant; `.glow-ambient` wraps image container; `display-text` h1; loading=eager
- Identity+CTA section: front-matter-driven identity statement and CTA description flowing into a `mailto:` button with `.glow-radiant-core` treatment; no `target="_blank"` per threat model

## Task Commits

1. **Task 1: Content data layer + Hero section partial with image pipeline** — `c39ce1b` (feat)
2. **Task 2: Identity+CTA section partial with CSS** — `c332b85` (feat)

## Files Created/Modified

- `content/_index.md` — Full front matter data layer: tagline, identity_statement, cta_*, footer_closing, social_links (8 platforms)
- `themes/arcaeon/layouts/partials/sections/hero.html` — Hero partial with Hugo picture pipeline, glow-ambient wrapper, display-text h1, tagline
- `themes/arcaeon/layouts/partials/sections/identity-cta.html` — Identity statement + CTA section with section-depth background and glow-radiant-core button
- `themes/arcaeon/assets/css/main.css` — Hero section CSS (hero-image-wrapper, hero-image, hero-tagline, responsive breakpoints) + identity+CTA CSS (identity-statement, cta-description, cta-button)
- `themes/arcaeon/layouts/index.html` — Wired to include hero and identity-cta partials

## Decisions Made

- `.Process "webp"` used instead of `.Format "webp"` — `.Format` errors in Hugo 0.160.1; `.Process` is the correct API for format conversion
- `loading=eager` on hero `<img>` — above fold, must not lazy-load; Hugo minification strips attribute quotes but the attribute is present and correct
- No `target="_blank"` on mailto link — native OS protocol handler, no window.opener vector; matches threat model T-02-02 accept disposition
- Identity/tagline placeholder copy is voice-matched and ship-ready as-is per D-13/D-14; Matt replaces via `content/_index.md` front matter

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Hero and Identity+CTA sections render correctly; Hugo build is clean
- `content/_index.md` front matter data layer is complete — social_links array ready for Plan 02-02 social links partial
- Plan 02-02 can immediately iterate over `.Params.social_links` for the social grid section
- Threat T-02-01 (`rel="noopener noreferrer"` on social links) is deferred to Plan 02-02 where social `<a>` elements are created

---
*Phase: 02-static-content*
*Completed: 2026-04-16*
