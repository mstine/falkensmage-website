---
phase: 02-static-content
plan: 02
subsystem: ui
tags: [hugo, svg, social-links, css-grid, ghost-card, glow-interactive, footer, inline-svg]

requires:
  - phase: 02-static-content-01
    provides: hero.html, identity-cta.html, main.css base with glow-interactive + sigil CSS classes, content/_index.md with social_links array and footer_closing

provides:
  - 8 inline SVG icon partials (currentColor, 20x20) for Substack, LinkedIn, X, Bluesky, Instagram, Threads, Spotify, TarotPulse
  - social.html: 2-column mobile grid of ghost cards with glow-interactive hover, aria-labels, noopener noreferrer
  - footer.html: "Stay feral, folks.", lemniscate mark (aria-hidden), dynamic copyright year, section-depth background
  - index.html: all four sections wired in correct order (hero, identity-cta, social, footer)
  - main.css: social grid CSS (2→3→4 col breakpoints), ghost card styles, z-index fix for glow layer, footer styles, sigil boundary positioning

affects: [03-dynamic-content, 04-production-deploy]

tech-stack:
  added: []
  patterns:
    - "Icon partials: standalone inline SVG files in themes/arcaeon/layouts/partials/icons/ — dynamic lookup via partial (printf 'icons/%s.html' .icon)"
    - "Ghost card pattern: border-only card with glow-interactive hover, z-index:1 on icon/label content above ::before glow layer"
    - "Section partial orchestration: index.html is the single wiring point for all sections, no logic in individual partials"
    - "Footer closing line sourced from front matter via | default fallback — zero hardcoded strings in partials"

key-files:
  created:
    - themes/arcaeon/layouts/partials/icons/substack.html
    - themes/arcaeon/layouts/partials/icons/linkedin.html
    - themes/arcaeon/layouts/partials/icons/x.html
    - themes/arcaeon/layouts/partials/icons/bluesky.html
    - themes/arcaeon/layouts/partials/icons/instagram.html
    - themes/arcaeon/layouts/partials/icons/threads.html
    - themes/arcaeon/layouts/partials/icons/spotify.html
    - themes/arcaeon/layouts/partials/icons/tarotpulse.html
    - themes/arcaeon/layouts/partials/sections/social.html
    - themes/arcaeon/layouts/partials/sections/footer.html
  modified:
    - themes/arcaeon/assets/css/main.css
    - themes/arcaeon/layouts/index.html

key-decisions:
  - "Icon partials use currentColor throughout — no hardcoded fill colors, CSS hover color changes propagate automatically"
  - "Social card content (icon + label) gets z-index: 1 to stay above the glow-interactive ::before layer at z-index: 0"
  - "Footer lemniscate rendered as Unicode &#x221E; with aria-hidden=true — decorative, not semantic"
  - "Dynamic copyright year via {{ now.Year }} — zero maintenance"

patterns-established:
  - "Icon partial naming: icon slug in _index.md front matter matches partial filename exactly (e.g. icon: 'substack' → icons/substack.html)"
  - "Ghost card z-index discipline: any content that must appear above a glow ::before layer needs position: relative + z-index: 1"
  - "Section partial wiring lives exclusively in index.html — partials themselves have no knowledge of order"

requirements-completed: [SOCIAL-01, SOCIAL-02, SOCIAL-03, SOCIAL-04, SOCIAL-05, FOOT-01, FOOT-02, FOOT-03]

duration: 8min
completed: 2026-04-16
---

# Phase 02 Plan 02: Social Links + Footer Summary

**8-platform ghost card grid with inline SVG icons and glow-interactive hover, footer with "Stay feral, folks." + lemniscate, all four sections wired in index.html**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-16T17:50:00Z
- **Completed:** 2026-04-16T17:58:00Z
- **Tasks:** 2
- **Files modified:** 12

## Accomplishments

- 8 inline SVG icon partials (currentColor, 20x20) dynamically resolved via `partial (printf "icons/%s.html" .icon)`
- Social grid renders 8 platform links in 2-col (mobile) → 3-col (tablet) → 4-col (desktop), ghost card style with 44px touch targets, aria-labels, and `rel="noopener noreferrer"` on all external links
- Footer renders "Stay feral, folks." from front matter, Unicode lemniscate (aria-hidden), dynamic year via `{{ now.Year }}`
- `index.html` wires all four sections in order: hero → identity-cta → social → footer

## Task Commits

1. **Task 1: SVG icon partials + social section + grid CSS** - `fda858b` (feat)
2. **Task 2: Footer partial + index.html wiring** - `2067211` (feat)

## Files Created/Modified

- `themes/arcaeon/layouts/partials/icons/substack.html` — Substack S letterform SVG
- `themes/arcaeon/layouts/partials/icons/linkedin.html` — LinkedIn "in" mark SVG
- `themes/arcaeon/layouts/partials/icons/x.html` — X mark SVG
- `themes/arcaeon/layouts/partials/icons/bluesky.html` — Bluesky butterfly SVG
- `themes/arcaeon/layouts/partials/icons/instagram.html` — Instagram camera SVG
- `themes/arcaeon/layouts/partials/icons/threads.html` — Threads mark SVG
- `themes/arcaeon/layouts/partials/icons/spotify.html` — Spotify circle SVG
- `themes/arcaeon/layouts/partials/icons/tarotpulse.html` — Lemniscate/infinity SVG
- `themes/arcaeon/layouts/partials/sections/social.html` — Social grid section partial
- `themes/arcaeon/layouts/partials/sections/footer.html` — Footer section partial
- `themes/arcaeon/assets/css/main.css` — Social grid, ghost card, footer, sigil boundary CSS appended
- `themes/arcaeon/layouts/index.html` — All four sections wired

## Decisions Made

- Icon partials use `currentColor` throughout — no hardcoded fills, so hover color shifts propagate via CSS without JS
- `social-card__icon` and `social-card__label` get `position: relative; z-index: 1` to stay above the `glow-interactive::before` pseudo-element at `z-index: 0` — the must_have truth "All social card content visible above glow layer" depends on this
- Footer lemniscate is Unicode `&#x221E;` with `aria-hidden="true"` — decorative mark, not screen-reader content
- `{{ now.Year }}` in footer — builds with correct year on every deploy, zero maintenance

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None. Hugo build clean on both task verifications. All 8 platform URLs present in built output, all 8 aria-labels and noopener noreferrer attributes verified.

## Known Stubs

None — all social links point to real URLs sourced from content/_index.md. Footer closing line renders from front matter via `| default` fallback.

## Threat Flags

None — T-02-01 (window.opener on target=_blank links) mitigated as planned via `rel="noopener noreferrer"` on all 8 social links.

## Next Phase Readiness

- Full single-page layout is now complete: Hero → Identity+CTA → Social → Footer
- Phase 02-03 can add the Currently/RSS section and any remaining dynamic content
- All four required sections render correctly and build clean
- No blockers

---
*Phase: 02-static-content*
*Completed: 2026-04-16*
