---
phase: 02-static-content
plan: 03
subsystem: testing
tags: [validation, shell-script, requirements-traceability, hugo-build, accessibility, grep]

requires:
  - phase: 02-static-content-01
    provides: hero.html, identity-cta.html, all glow CSS, main.css
  - phase: 02-static-content-02
    provides: social.html, footer.html, 8 SVG icon partials, social grid CSS, footer CSS

provides:
  - tests/validate-phase-02.sh: 18-check automated validation script for all 16 Phase 2 requirements plus 1 regression check
  - Automated gate for /gsd-verify-work Phase 2 sign-off
  - Confirmed: Hugo build clean, all 16 Phase 2 requirements satisfied in built HTML

affects: [03-dynamic-content, 04-production-deploy]

tech-stack:
  added: []
  patterns:
    - Shell validation script pattern following Phase 1 establish convention (validate-phase-0N.sh)
    - html_has (extended regex) and html_has_fixed (literal) helpers for HTML grep reliability
    - Multi-platform loop check for SOCIAL-04 (8 domains in one requirement)
    - Dual-condition CTA-02 check (mailto AND glow-radiant-core must both be present)

key-files:
  created:
    - tests/validate-phase-02.sh
  modified: []

decisions:
  - SOCIAL-04 check implemented as a loop over all 8 platform domains with per-platform MISSING output — reports which platform is absent rather than generic failure
  - HERO-04-REG added as 17th check (counted as check 18 total with build check) — validates prefers-reduced-motion regression from Phase 1 has not been broken
  - Script aborts on Hugo build failure rather than greping a stale build — prevents false positives from previous build artifacts
  - html_has_fixed used for class/text checks, html_has (extended regex) as fallback for picture element — handles Hugo minifier variation in attribute quoting

metrics:
  duration: 5min
  completed: 2026-04-16
  tasks_completed: 2
  files_created: 1
  files_modified: 0

key-decisions:
  - Validation script aborts on Hugo build failure — prevents greping stale build artifacts
  - SOCIAL-04 implemented as loop with per-platform failure reporting — easier diagnosis when a link URL changes
  - Separate html_has / html_has_fixed helpers — grep -E vs -F prevents false matches on CSS class patterns that look like regex
---

# Phase 02 Plan 03: Phase 2 Validation Script — Summary

Phase 2 automated gate: shell validation script that runs Hugo, then checks all 16 Phase 2 requirements against built HTML and CSS, with a regression check ensuring Phase 1's prefers-reduced-motion is intact.

## What Was Built

`tests/validate-phase-02.sh` — 18-check validation script following the Phase 1 pattern (`validate-phase-01.sh`). Script runs `hugo --minify`, aborts on build failure, then greps `public/index.html` and `themes/arcaeon/assets/css/main.css` for each requirement. Prints `PASS/FAIL` per check, exits 0 if all pass, exits 1 if any fail.

**Checks implemented:**

| # | Requirement | What's Checked | Target |
|---|-------------|----------------|--------|
| Build | — | Hugo exits 0 | hugo binary |
| 1 | HERO-01 | `<picture>` element present | public/index.html |
| 2 | HERO-02 | `display-text` class present | public/index.html |
| 3 | HERO-03 | `hero-tagline` class present | public/index.html |
| 4 | HERO-04 | `glow-ambient` class present | public/index.html |
| 5 | IDENT-01 | `identity-statement` class present | public/index.html |
| 6 | IDENT-02 | `identity_statement:` key in front matter | content/_index.md |
| 7 | SOCIAL-01 | `social-grid` class present | public/index.html |
| 8 | SOCIAL-02 | `glow-interactive` class present | public/index.html |
| 9 | SOCIAL-03 | `min-height: 44px` in CSS | themes/arcaeon/assets/css/main.css |
| 10 | SOCIAL-04 | All 8 platform domains present (loop) | public/index.html |
| 11 | SOCIAL-05 | `aria-label=` count >= 8 | public/index.html |
| 12 | CTA-01 | `Coaching` text present | public/index.html |
| 13 | CTA-02 | `mailto:falkensmage@...` AND `glow-radiant-core` | public/index.html |
| 14 | FOOT-01 | `Stay feral, folks.` text present | public/index.html |
| 15 | FOOT-02 | `Digital Intuition LLC` text present | public/index.html |
| 16 | FOOT-03 | `footer-lemniscate` class present | public/index.html |
| 17 | HERO-04-REG | `prefers-reduced-motion` >= 1 occurrence | themes/arcaeon/assets/css/main.css |

**Results when run:** 18 passed, 0 failed. Phase 1 regression: 46 passed, 0 failed.

## Task 2: Visual Checkpoint

**Status: Auto-approved** (running in `--auto` mode per execution context)

The validation script confirms all 16 Phase 2 requirements are present in the built HTML at the structural level. Visual rendering at 375px and desktop requires the dev server (`hugo server --buildDrafts`) and browser DevTools — this is the manual gate for Phase 2 sign-off via `/gsd-verify-work`.

## Deviations from Plan

### Auto-added Checks

**1. [Rule 2 - Missing Critical] Abort-on-build-failure guard**
- **Found during:** Task 1 implementation
- **Issue:** Without explicit abort on Hugo build failure, subsequent grep checks would run against stale `public/index.html` from a previous build, producing false positives
- **Fix:** Added `exit 1` immediately after Hugo build failure, before any HTML checks
- **Files modified:** tests/validate-phase-02.sh

**2. [Rule 2 - Missing Critical] html_has vs html_has_fixed helper split**
- **Found during:** Task 1 implementation
- **Issue:** CSS class patterns like `.glow-ambient` and social card URLs contain characters that are regex metacharacters — using `-E` for all greps risks false matches or missed matches
- **Fix:** Two helpers: `html_has_fixed` (literal `-F`) for string/class checks, `html_has` (extended `-E`) for structural patterns like `<picture`
- **Files modified:** tests/validate-phase-02.sh

## Known Stubs

None — validation script is the full artifact, not a stub. Content stubs (tagline placeholder, identity statement placeholder) are documented in Plans 01 and 02 SUMMARYs and are intentional scaffolding for Matt to replace.

## Threat Flags

None — validation script reads local files only. No new network surface, auth paths, or trust boundaries introduced.

## Self-Check: PASSED

- `tests/validate-phase-02.sh` exists: FOUND
- Script is executable: CONFIRMED
- All 18 checks pass on current codebase: CONFIRMED
- Phase 1 regression (46 checks): CONFIRMED passing
- Commit e7d9ad9: CONFIRMED
