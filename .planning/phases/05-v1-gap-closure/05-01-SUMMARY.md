---
phase: 05-v1-gap-closure
plan: 01
subsystem: infra
tags: [hugo, css.Build, esbuild, fonts, html5-landmarks, accessibility, performance]

# Dependency graph
requires:
  - phase: 01-theme-foundation
    provides: Cinzel + Space Grotesk WOFF2 files committed under themes/arcaeon/static/fonts/
  - phase: 03-dynamic-layer-quality
    provides: @font-face src switched to absolute /fonts/... paths; preload href on the same path
provides:
  - Built HTML with exactly one <footer> landmark (A11Y-01 restored)
  - css.Build externals slice preserving /fonts/ URLs byte-identical to preload href (PERF-03 part 1)
  - Single source of truth for font WOFF2 files (themes/arcaeon/static/fonts/) — duplicate assets/fonts/ removed (PERF-03 part 2)
affects: [05-02-PLAN.md (hygiene fixes), 05-03-PLAN.md (verification), /gsd-validate-phase-3 future run]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Hugo css.Build externals dict with exact absolute path slice — prevents esbuild file loader from rewriting url() for matched paths"
    - "Single source of truth for self-hosted fonts: themes/arcaeon/static/fonts/ served via Hugo static pipeline; zero duplication in assets/"
    - "HTML5 landmark hygiene via partial-owns-root-element — caller template does NOT re-wrap in same semantic element"

key-files:
  created: []
  modified:
    - "themes/arcaeon/layouts/index.html — removed <footer>/</footer> wrapper (13 lines → 11 lines)"
    - "themes/arcaeon/layouts/_default/baseof.html — added $cssOpts dict with externals slice, passed to css.Build"
  deleted:
    - "themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2"
    - "themes/arcaeon/assets/fonts/space-grotesk-latin-wght-normal.woff2"

key-decisions:
  - "Option A (remove outer wrapper) over Option B (change inner root to div) for A11Y-01 — zero CSS blast radius, semantically honest partial name"
  - "Exact absolute path strings in externals slice — glob patterns (/fonts/*, *.woff2) empirically do NOT work with esbuild CSS url() resolver"
  - "Task 2 externals MUST be committed before Task 3 deletion — reversing order triggers 'Could not resolve /fonts/...' build error (Pitfall 4)"

patterns-established:
  - "css.Build externals: dict \"externals\" (slice ...) passed as pipeline argument with exact absolute url() strings"
  - "Clean rebuild discipline: rm -rf public/ resources/_gen/ before verification grep, to invalidate Hugo's cache"

requirements-completed: [A11Y-01, PERF-03]

# Metrics
duration: 2m
completed: 2026-04-17
---

# Phase 5 Plan 1: Code Defect Fixes Summary

**Restored HTML5 `<footer>` landmark validity and eliminated font double-fetch via Hugo `css.Build` externals slice preserving `/fonts/` URLs byte-identical to preload hints**

## Performance

- **Duration:** 1m 42s
- **Started:** 2026-04-17T19:24:36Z
- **Completed:** 2026-04-17T19:26:18Z
- **Tasks:** 3
- **Files modified:** 2
- **Files deleted:** 2

## Accomplishments

- A11Y-01: `public/index.html` now has exactly one `<footer>` opening tag and one `</footer>` closing tag — previously nested because `index.html` wrapped a partial whose root was already `<footer>`.
- PERF-03 part 1: `css.Build` receives an `externals` slice of exact font paths. Built CSS (`public/css/main.min.*.css`) contains `url(/fonts/cinzel-latin-wght-normal.woff2)` and `url(/fonts/space-grotesk-latin-wght-normal.woff2)` — byte-identical to preload `href` — enabling preload cache hit on first font fetch.
- PERF-03 part 2: `themes/arcaeon/assets/fonts/` directory removed entirely. `themes/arcaeon/static/fonts/` is now the single source of truth for self-hosted WOFF2 files. `public/css/` contains zero `.woff2` files post-build; `public/fonts/` contains both.

## Task Commits

Each task was committed atomically:

1. **Task 1: A11Y-01 — Remove nested footer wrapper in index.html** — `0b294a7` (fix)
2. **Task 2: PERF-03(a) — Add externals slice to css.Build call in baseof.html** — `339ce26` (fix)
3. **Task 3: PERF-03(b) — Delete duplicate assets/fonts/ woff2 files** — `953bbf7` (fix)

## Files Created/Modified

- `themes/arcaeon/layouts/index.html` — Removed the outer `<footer>` wrapper surrounding `{{ partial "sections/footer.html" . }}`. File shrank from 13 lines to 11 lines. No CSS changes required because the partial's own `<footer class="section section-void footer-section sigil-arc-sm sigil-boundary-bl">` root now IS the single landmark.
- `themes/arcaeon/layouts/_default/baseof.html` — Replaced line 15's single-line `css.Build` pipeline with a three-line `{{ $cssOpts := dict "externals" (slice ...) }}` block followed by `css.Build $cssOpts`. Font URL resolution is now opted-out of esbuild's file loader for the two matched absolute paths.
- `themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2` — Deleted via `git rm`. Orphan duplicate of `static/fonts/` source of truth.
- `themes/arcaeon/assets/fonts/space-grotesk-latin-wght-normal.woff2` — Deleted via `git rm`. Same rationale.

## Decisions Made

- **Option A over Option B for A11Y-01.** Removing the outer `<footer>` wrapper in `index.html` preserves the partial's own `<footer>` root element, which is semantically honest (a file named `sections/footer.html` should be a `<footer>`) and has zero CSS blast radius (all footer selectors target classes like `.footer-section`, `.footer-content`, `.footer-closing`, `.footer-lemniscate`, `.footer-copyright` — none target the bare `footer` element).
- **Exact path strings, not globs, in the `externals` slice.** Research empirically validated on Hugo 0.160.1 that `"/fonts/*"` and `"*.woff2"` both fail to preserve `url()` references; only `"/fonts/cinzel-latin-wght-normal.woff2"` and `"/fonts/space-grotesk-latin-wght-normal.woff2"` work. esbuild's CSS `url()` external pattern matching requires exact path matches for this use case.
- **Task 2 before Task 3 (strict ordering).** If `assets/fonts/*.woff2` are deleted before `css.Build` has `externals` configured, Hugo errors with `Could not resolve "/fonts/cinzel-latin-wght-normal.woff2"` — the asset resolver looks for the file in `assets/`, and `static/` is not in the asset resolution path. Committing externals first, verifying build success, then deleting the duplicates is the only safe order (Pitfall 4 in research).

## Deviations from Plan

None — plan executed exactly as written.

Each task's verification and acceptance criteria were met on the first automated check after the edit. No Rule 1 bugs discovered, no Rule 2 missing critical functionality, no Rule 3 blocking issues. Research pre-validated all three fixes empirically, so the executor's job was mechanical application.

## Issues Encountered

None.

Note: the `git rm` for the two font files also removed the empty parent directory (`themes/arcaeon/assets/fonts/`) automatically, making the planned explicit `rmdir` step a no-op. This is expected Git behavior when `git rm` empties a directory — not an error.

## User Setup Required

None — this plan is a surgical code fix with no external service configuration, no environment variables, and no UI-only changes.

## Next Phase Readiness

- **Plan 05-02 (hygiene fixes) unblocked.** SEO-03 regex fix, CI workflow `npm ci` removal, and four SUMMARY frontmatter backfills touch completely different files and can now execute in parallel.
- **Plan 05-03 (verification + traceability) depends on this plan.** Plan 05-03's PERF-03 structural diff check (preload href === @font-face src) requires Plan 05-01's externals fix to be live in the repo, which it now is.
- **No concerns.** All 8 success-criteria assertions passed on clean rebuild (`rm -rf public/ resources/_gen/ && hugo --quiet`).

## Self-Check: PASSED

Verified on disk:

- `themes/arcaeon/layouts/index.html` — FOUND (11 lines, matches plan target)
- `themes/arcaeon/layouts/_default/baseof.html` — FOUND (contains `css.Build $cssOpts`)
- `themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2` — MISSING (correct — deleted)
- `themes/arcaeon/assets/fonts/space-grotesk-latin-wght-normal.woff2` — MISSING (correct — deleted)
- `themes/arcaeon/static/fonts/cinzel-latin-wght-normal.woff2` — FOUND (source of truth preserved)
- `themes/arcaeon/static/fonts/space-grotesk-latin-wght-normal.woff2` — FOUND (source of truth preserved)

Verified in git log:

- `0b294a7` — FOUND (Task 1)
- `339ce26` — FOUND (Task 2)
- `953bbf7` — FOUND (Task 3)

Built-HTML assertions re-verified after Task 3 commit:

- `grep -cE '<footer[ >]' public/index.html` == 1 — PASS
- `grep -c '</footer>' public/index.html` == 1 — PASS
- `url(/fonts/cinzel-latin-wght-normal.woff2)` in built CSS — PASS
- `url(/fonts/space-grotesk-latin-wght-normal.woff2)` in built CSS — PASS
- Zero `.woff2` files in `public/css/` — PASS
- Both woff2 files present in `public/fonts/` — PASS

---
*Phase: 05-v1-gap-closure*
*Completed: 2026-04-17*
