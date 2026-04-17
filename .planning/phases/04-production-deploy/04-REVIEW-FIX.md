---
phase: 04-production-deploy
fixed_at: 2026-04-17T00:00:00Z
review_path: .planning/phases/04-production-deploy/04-REVIEW.md
iteration: 1
findings_in_scope: 4
fixed: 4
skipped: 0
status: all_fixed
---

# Phase 04: Code Review Fix Report

**Fixed at:** 2026-04-17
**Source review:** .planning/phases/04-production-deploy/04-REVIEW.md
**Iteration:** 1

**Summary:**
- Findings in scope: 4
- Fixed: 4
- Skipped: 0

## Fixed Issues

### WR-01: Wrong RSS feed URL — 404 at build time

**Files modified:** `themes/arcaeon/layouts/partials/sections/currently.html`
**Commit:** 09d3022
**Applied fix:** Changed `$rssURL` from `https://feralarchitecture.com/feed` to `https://feralarchitecture.substack.com/feed` — the correct Substack RSS endpoint.

### WR-02: Hardcoded canonical URL breaks staging and preview builds

**Files modified:** `themes/arcaeon/layouts/_default/baseof.html`
**Commit:** 259ef38
**Applied fix:** Replaced hardcoded `https://falkensmage.com` with `{{ .Permalink }}` on both the `og:url` meta tag (line 23) and the `<link rel="canonical">` element (line 41). Both now resolve correctly in all build environments.

### WR-03: Hero section silently renders nothing if image asset is missing

**Files modified:** `themes/arcaeon/layouts/partials/sections/hero.html`
**Commit:** aaeb2bf
**Applied fix:** Added `{{ if not $img }}{{ errorf "Hero image missing: ..." }}{{ end }}` guard before the `{{ with $img }}` block. A missing hero image now fails the build hard rather than silently emitting an empty `<header>`.

### WR-04: png-to-ico.py crashes with unhelpful error on bad invocation

**Files modified:** `scripts/png-to-ico.py`
**Commit:** 8bae6c4
**Applied fix:** Added `len(sys.argv) < 3` guard that prints a usage message to stderr and exits with code 1 before the unpacking assignment. Also added a PNG signature check (`\x89PNG\r\n\x1a\n`) for each input file before passing to `create_ico`, preventing silent corrupt ICO output from non-PNG inputs.

---

_Fixed: 2026-04-17_
_Fixer: Claude (gsd-code-fixer)_
_Iteration: 1_
