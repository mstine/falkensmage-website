---
phase: 05-v1-gap-closure
reviewed: 2026-04-17T00:00:00Z
depth: standard
files_reviewed: 5
files_reviewed_list:
  - themes/arcaeon/layouts/index.html
  - themes/arcaeon/layouts/_default/baseof.html
  - tests/validate-phase-03.sh
  - tests/validate-phase-01.sh
  - .github/workflows/hugo.yml
findings:
  critical: 0
  warning: 0
  info: 3
  total: 3
status: issues_found
---

# Phase 5: Code Review Report

**Reviewed:** 2026-04-17
**Depth:** standard
**Files Reviewed:** 5
**Status:** issues_found (info-only — no correctness or security issues)

## Summary

Phase 5 was a tightly-scoped v1.0 gap closure touching five files with surgical edits. The changes are correct, minimal, and well-aligned with their stated intents.

Cross-file verification confirmed:

- `themes/arcaeon/layouts/index.html` — the wrapping `<footer>` was removed; the `<footer class="section section-void footer-section ...">` landmark now lives only in `partials/sections/footer.html`. Spot-checks of the other four partials (`hero.html`, `currently.html`, `identity-cta.html`, `social.html`) show no stray `<header>`/`<main>`/`<footer>` tags, so the built HTML will contain exactly one of each landmark as A11Y-01 intends.
- `themes/arcaeon/layouts/_default/baseof.html` — the `css.Build` `externals` slice uses the exact `/fonts/cinzel-latin-wght-normal.woff2` and `/fonts/space-grotesk-latin-wght-normal.woff2` paths. These match the preload `href` values on lines 10/12 **and** the `url(...)` values in `themes/arcaeon/assets/css/main.css` lines 117/125 byte-for-byte. esbuild will leave those `url()` references alone, so preload and `@font-face` resolve to the same asset and the browser gets one fetch per font, not two.
- `tests/validate-phase-03.sh` — regex on line 154 `'href="https://falkensmage\.com/?"'` correctly accepts both `https://falkensmage.com/` (Hugo's default with trailing slash on the baseURL) and `https://falkensmage.com` (no trailing slash), verified with `printf`/`grep -cE` smoke. The five new Phase-5 structural checks (lines 157–240) are well-guarded — they check file-system state, built-HTML shape, and planning-artifact presence in ways that cannot silently pass when the underlying change has reverted.
- `tests/validate-phase-01.sh` — all font path assertions now point at `themes/arcaeon/static/fonts/...` as the single source of truth. Comments on lines 105–108 and 205 document the invariant with the correct rationale (css.Build `externals` need the url() path to match the static asset, not be rewritten through an assets-dir copy).
- `.github/workflows/hugo.yml` — the vestigial `npm ci` step is gone. The remaining workflow is coherent: Hugo extended binary install, Dart Sass snap, `actions/configure-pages@v6`, build with `--minify --baseURL`, `actions/upload-pages-artifact@v3`, and `actions/deploy-pages@v5`. No other font/asset management assumed Node was installed.

Three low-severity Info items below are observations for follow-up, not defects.

## Info

### IN-01: `set -uo pipefail` without `-e` lets later checks silently mis-count on unset helpers

**File:** `tests/validate-phase-03.sh:7`
**Issue:** The script uses `set -uo pipefail` (same as `tests/validate-phase-01.sh:7`). Without `-e`, a failing command early in the script does not abort; failures are counted via the `check()` helper. This is a deliberate design choice and correct for a validator that wants to run all checks and summarize. The subtle risk: several new Phase-5 blocks use bare command substitutions (e.g. `CSS_BUILD=$(ls "$BUILD_DIR"/css/main.min.*.css 2>/dev/null | head -1)` on line 171) where an empty match is handled, but patterns like `grep -oE ... | head -1 || true` on lines 176–177 and 185–186 rely on `|| true` to avoid a pipefail trip. If anyone later removes the `|| true` guard to "tighten" the script, the failure mode is a silent exit (pipefail aborts the pipeline, `set -u` is irrelevant here, script ends with no summary). Worth a one-line comment near line 7 noting "do not add `-e` or remove `|| true` guards without auditing every pipeline."
**Fix:** Add a comment above `set -uo pipefail`:
```bash
# Intentionally NOT -e: we run every check and summarize at the end.
# The `|| true` guards on pipelines are required with pipefail — do not remove.
set -uo pipefail
```

### IN-02: Phase 3 script hard-codes Phase 5 SUMMARY paths, coupling two phases

**File:** `tests/validate-phase-03.sh:222-240`
**Issue:** The "requirements-completed in all target SUMMARYs" check lives inside `validate-phase-03.sh` but asserts frontmatter on four SUMMARYs across phases 01 and 03. That check conceptually belongs to Phase 5 (it is a backfill verification), not Phase 3. Putting it in `validate-phase-03.sh` means:
1. Running only the Phase 3 suite will fail if the Phase 5 backfill is ever reverted.
2. There is no `validate-phase-05.sh` entry point to run the gap-closure checks as a standalone suite.
This is not broken — it works — but it fuzzes the boundaries between phase validators. Consider extracting lines 157–240 into a `tests/validate-phase-05.sh` that mirrors the existing validator shape. Low priority; acceptable as-is if the team has decided phase validators are cumulative rather than isolated.
**Fix:** Either (a) extract Phase 5 checks into a dedicated script, or (b) add a one-line header comment at line 157 acknowledging the coupling: `# Phase 5 gap-closure checks intentionally live here so validate-phase-03.sh remains the integration gate.`

### IN-03: Preload `href` uses absolute `/fonts/...` paths, will 404 if site is ever served from a subpath

**File:** `themes/arcaeon/layouts/_default/baseof.html:10-18`
**Issue:** The preload `<link rel="preload" href="/fonts/...">` and the `externals` slice both use root-absolute paths. This is correct for `falkensmage.com` where the site is served from `/`. If the GH Pages deployment ever moves to a project-path URL (e.g. `username.github.io/falkensmage-website/`) or the domain changes such that Hugo's `baseURL` includes a subpath, the preloads will 404 and the `externals` entries will no longer match the rewritten `url()` in the built CSS. This is not a bug today — the CI workflow uses `--baseURL "${{ steps.pages.outputs.base_url }}/"` which resolves to the custom-domain root — but it is worth noting that the preloads are not using Hugo's `{{ "fonts/..." | relURL }}` or `absURL`, so they will not adapt if the deploy target changes. CLAUDE.md calls out custom-domain CNAME routing, so this is likely intentional. Flag only for awareness.
**Fix:** If the site's deploy target ever includes a non-root base path, switch to:
```go-html-template
<link rel="preload" href="{{ "fonts/cinzel-latin-wght-normal.woff2" | relURL }}"
      as="font" type="font/woff2" crossorigin>
```
and update the `externals` slice to match (note: `externals` needs a literal string, so this would require a computed `printf`/`dict` dance). Not worth the complexity unless a subpath deploy becomes real.

---

_Reviewed: 2026-04-17_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
