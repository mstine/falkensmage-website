---
phase: 03-dynamic-layer-quality
plan: 01
subsystem: currently-section, landmarks, font-preload
tags: [rss, hugo, accessibility, performance, fonts, css]
dependency_graph:
  requires: [02-03]
  provides: [currently-section, landmark-structure, font-preload]
  affects: [03-02]
tech_stack:
  added: [resources.GetRemote, try-wrapper, font-preload]
  patterns: [build-time-rss, html5-landmarks, static-font-preload]
key_files:
  created:
    - themes/arcaeon/layouts/partials/sections/currently.html
    - themes/arcaeon/static/fonts/cinzel-latin-wght-normal.woff2
    - themes/arcaeon/static/fonts/space-grotesk-latin-wght-normal.woff2
  modified:
    - themes/arcaeon/layouts/index.html
    - content/_index.md
    - themes/arcaeon/assets/css/main.css
    - themes/arcaeon/layouts/_default/baseof.html
decisions:
  - RSS URL hardcoded to feralarchitecture.com/feed (not substack.com — avoids 301 redirect)
  - try wrapping for resources.GetRemote per Hugo 0.141.0+ error handling pattern
  - Font paths changed from relative ../fonts/ to absolute /fonts/ so @font-face and preload href match exactly
  - crossorigin attribute required on font preload links even for same-origin (avoids double-fetch cache key mismatch)
  - currently_focus field added to _index.md front matter for manually editable blurb independent of RSS status
requirements-completed: [CURR-01, CURR-02, CURR-03, PERF-03, A11Y-01, A11Y-04]
metrics:
  duration: ~8min
  completed: 2026-04-17
  tasks: 2
  files: 7
---

# Phase 03 Plan 01: Currently Section + Landmarks + Font Preload Summary

Build-time RSS-fed "Currently" section using `resources.GetRemote` with `try` fallback, HTML5 landmark restructure (header/main/footer), font migration to stable static paths, and preload hints in head.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Currently partial + landmark restructure + front matter | 1e70fff | currently.html, index.html, _index.md |
| 2 | Currently card CSS + font static migration + preload hints | 5b3210e | main.css, baseof.html, static/fonts/ |

## What Was Built

**Currently section partial** (`currently.html`): Hugo build-time RSS fetch from `https://feralarchitecture.com/feed` via `resources.GetRemote` wrapped in `try` for resilient error handling. `htmlUnescape` applied to RSS title for CDATA entity decoding. Fallback to `feralarchitecture.substack.com` when RSS is unreachable. `currently_focus` blurb from front matter renders regardless of RSS status. Section uses `.section-depth` background per triad D-05 assignment. Post link uses `.glow-interactive`. Section has `aria-labelledby` pointing to heading `id` for screen reader landmark navigation.

**Landmark restructure** (`index.html`): Replaced single `<main>` wrapper with proper HTML5 landmarks — `<header>` wraps hero (contains the `<h1>`), `<main>` wraps Currently + Identity+CTA + Social, `<footer>` wraps footer partial. No `<nav>` (single page, no navigation needed).

**Font static migration**: Copied both WOFF2 files from `assets/fonts/` to `static/fonts/` so they serve at a stable, fingerprint-free `/fonts/` path. Updated `@font-face` src paths from `url('../fonts/...')` to `url('/fonts/...')` so CSS reference and preload `href` match exactly — no browser double-fetch.

**Font preload hints** (`baseof.html`): Two `<link rel="preload">` tags with `as="font"`, `type="font/woff2"`, and `crossorigin` attribute added before the CSS pipeline tag. `crossorigin` is required even for same-origin fonts to match the CORS cache key used by `@font-face`.

**Currently card CSS**: Ghost card with `1px solid rgba(122, 44, 255, 0.35)` border, `border-color` transition on hover (no pseudo-elements — those are reserved for glow/sigil), `prefers-reduced-motion` suppression. Typography classes for label (Cinzel h3), sublabel (Space Grotesk 0.875rem), post link (ion-glow accent), and focus blurb.

## Deviations from Plan

None — plan executed exactly as written.

## Threat Model Verification

T-03-02 (RSS title XSS): Hugo's default template escaping handles XSS. `htmlUnescape` only decodes entity references before Hugo re-escapes output — does not bypass escaping. `safeHTML` not used.

T-03-03 (RSS link href): Hugo escapes attribute values in `href` by default. `safeURL` not used.

T-03-04 (build error disclosure): `warnf` logs to build output only, not rendered HTML. No error UI visible to end users.

T-03-05 (RSS timeout/DoS): `try` wrapping prevents build failure on RSS unavailability. Fallback content renders.

## Known Stubs

None — `currently_focus` is wired to front matter and renders. Currently section renders either RSS data or fallback link. No placeholder-only content.

## Self-Check: PASSED

- `themes/arcaeon/layouts/partials/sections/currently.html` — FOUND
- `themes/arcaeon/layouts/index.html` — FOUND (contains `<header>`, `<main>`, `<footer>`)
- `themes/arcaeon/static/fonts/cinzel-latin-wght-normal.woff2` — FOUND
- `themes/arcaeon/static/fonts/space-grotesk-latin-wght-normal.woff2` — FOUND
- `public/fonts/cinzel-latin-wght-normal.woff2` — FOUND (build output)
- `public/fonts/space-grotesk-latin-wght-normal.woff2` — FOUND (build output)
- `public/index.html` contains `currently-card` — FOUND
- `public/index.html` contains `<header>` — FOUND
- `public/index.html` contains `<footer>` — FOUND
- `public/index.html` contains `rel="preload"` (2 hits) — FOUND
- `prefers-reduced-motion` count in main.css: 6 (>= 5 required) — PASSED
- Commit 1e70fff — FOUND
- Commit 5b3210e — FOUND
- Hugo build exits 0 — PASSED
