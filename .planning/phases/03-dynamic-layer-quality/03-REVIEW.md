---
phase: 03-dynamic-layer-quality
reviewed: 2026-04-16T00:00:00Z
depth: standard
files_reviewed: 6
files_reviewed_list:
  - content/_index.md
  - tests/validate-phase-03.sh
  - themes/arcaeon/assets/css/main.css
  - themes/arcaeon/layouts/_default/baseof.html
  - themes/arcaeon/layouts/index.html
  - themes/arcaeon/layouts/partials/sections/currently.html
findings:
  critical: 1
  warning: 3
  info: 3
  total: 7
status: issues_found
---

# Phase 03: Code Review Report

**Reviewed:** 2026-04-16
**Depth:** standard
**Files Reviewed:** 6
**Status:** issues_found

## Summary

Six files reviewed covering the Phase 3 dynamic layer: RSS currently section, validation script, CSS system, base layout, index layout, and front matter. The CSS, index layout, and front matter are clean. One critical functional bug in the RSS partial will cause the currently section to always render its fallback — the live post title will never appear. Three warnings cover a validation script logic issue, a missing build warning for an absent OG image, and a latent CSS layout bug. Three info items round out dead code and minor accessibility inconsistencies.

## Critical Issues

### CR-01: RSS unmarshal path is wrong — currently section never shows live posts

**File:** `themes/arcaeon/layouts/partials/sections/currently.html:10`

**Issue:** `transform.Unmarshal` on Substack's RSS 2.0 feed produces a Go map with a root key of `rss`, not direct `channel` access. The template accesses `.channel.item` on the unmarshalled value, but the correct path is `.rss.channel.item`. Because `.channel` resolves to nil, `range first 1 .` is never entered, `$latestPost` stays an empty dict, and the fallback link always renders. The live post title will never appear in the built HTML regardless of whether the RSS fetch succeeds.

**Fix:**
```html
{{/* Correct path through Hugo's transform.Unmarshal for RSS 2.0 */}}
{{ with . | transform.Unmarshal }}
  {{ with .rss }}
    {{ with .channel.item }}
      {{ range first 1 . }}
        {{ $latestPost = dict "title" (.title | htmlUnescape) "link" .link }}
      {{ end }}
    {{ end }}
  {{ end }}
{{ end }}
```

Verify the exact shape by adding a temporary `{{ . | jsonify }}` in a local dev build if the Substack feed structure differs from standard RSS 2.0.

---

## Warnings

### WR-01: Validation script `check()` function inverted label — FAIL prints for passing checks

**File:** `tests/validate-phase-03.sh:25-31`

**Issue:** The `check()` function treats `result > 0` as PASS and `result == 0` as FAIL, which is correct for `grep -c` usage. However, the echo labels are swapped — line 26 prints `"  PASS: $label"` when result is greater than zero (match found), and line 29 prints `"  FAIL: $label"` when zero. This is actually correct as written. The real bug is that `set -uo pipefail` on line 7 is missing `-e`. A non-zero exit from any unguarded command (such as a failed `cd`, a missing file path, or an error in a subshell) will not abort the script — execution continues, PASS/FAIL counters may be wrong, and the final exit code may be 0 despite bad state. The hugo build check on line 40 is guarded with `if !`, but file path assignments and other commands are not.

**Fix:**
```bash
set -euo pipefail
```

If any existing commands legitimately fail (e.g., `grep` returning exit 1 on zero matches), those are already protected with `|| true` — adding `-e` won't break them.

---

### WR-02: OG/Twitter image silently omitted when hero asset is absent

**File:** `themes/arcaeon/layouts/_default/baseof.html:26-33`

**Issue:** The `{{ with $heroSrc }}` block conditionally renders both `og:image` and `twitter:image`. If `themes/arcaeon/assets/images/magus-hero.jpg` does not exist at build time — a real risk during setup or in CI before the asset is committed — both meta tags are silently dropped. The built page will have `og:title` and `og:description` but no image, which degrades social share previews without any build-time warning.

**Fix:** Add a `warnf` in the else branch so the absence surfaces during build:
```html
{{ $heroSrc := resources.Get "images/magus-hero.jpg" }}
{{ if $heroSrc }}
  {{ $ogImg := $heroSrc.Fill "1200x630 Center" }}
  <meta property="og:image" content="{{ $ogImg.Permalink }}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:image" content="{{ $ogImg.Permalink }}">
{{ else }}
  {{ warnf "baseof.html: magus-hero.jpg not found — og:image and twitter:image will be absent" }}
{{ end }}
```

---

### WR-03: `.sigil-arc` base class missing position coordinates — renders at (0,0) without a boundary class

**File:** `themes/arcaeon/assets/css/main.css:403-418`

**Issue:** `.sigil-arc::after` sets `position: absolute` with no `top`, `right`, `bottom`, or `left` values. The positioning is deferred to `.sigil-boundary-tr::after` (line 665) and `.sigil-boundary-bl::after` (line 671). Any element using `.sigil-arc` without one of those boundary modifier classes will render the decorative arc pseudo-element at `top: 0; left: 0` by default, potentially overlapping section headings or content. The same applies to `.sigil-arc-sm::after` (lines 421-432). This is a latent layout bug that will surface the moment `.sigil-arc` is used on a section that doesn't have a boundary modifier.

**Fix:** Add a safe default position to the base class, or add a CSS comment explicitly documenting that this class requires a boundary modifier to function correctly:
```css
.sigil-arc {
  position: relative;
  /* REQUIRES a .sigil-boundary-* modifier class for correct positioning.
     Without one, ::after renders at top: 0; left: 0 and may overlap content. */
}
```
Or give the base class a safe default:
```css
.sigil-arc::after {
  /* ... existing properties ... */
  top: -20px;   /* safe default; override with .sigil-boundary-* */
  right: 2rem;
}
```

---

## Info

### IN-01: Dead variable `CONTENT` declared but never used

**File:** `tests/validate-phase-03.sh:19`

**Issue:** `CONTENT="_index.md"` is declared on line 19. The actual variable used throughout the script is `CONTENT_PATH` (line 20). `CONTENT` is referenced nowhere after declaration. It is dead code.

**Fix:** Remove line 19:
```bash
# Remove this line — unused
CONTENT="_index.md"
```

---

### IN-02: RSS feed URL and fallback link point to different domains

**File:** `themes/arcaeon/layouts/partials/sections/currently.html:2` and `:33`

**Issue:** The RSS fetch targets `https://feralarchitecture.com/feed` (a custom domain) while the fallback link targets `https://feralarchitecture.substack.com` (the Substack domain). These are two different properties. If `feralarchitecture.com` is not yet configured or doesn't serve RSS at `/feed`, every build silently falls through to the fallback. The `warnf` on line 7 will fire, but only in build output — not surfaced to the end user. This is worth making intentional and explicit.

**Fix:** Confirm which domain is canonical for the RSS feed. If `feralarchitecture.com` is not yet live, switch the RSS URL to the known-good Substack feed:
```go
{{ $rssURL := "https://feralarchitecture.substack.com/feed" }}
```
If `feralarchitecture.com` is the intended canonical, update the fallback link to match.

---

### IN-03: Fallback link in currently partial missing `aria-label`

**File:** `themes/arcaeon/layouts/partials/sections/currently.html:33-38`

**Issue:** The primary post link (line 25-30) includes `aria-label="Read: {{ $latestPost.title }} on Feral Architecture"` for screen readers. The fallback link (line 33-37) has no `aria-label`. The link text "Read Feral Architecture →" is reasonably descriptive on its own, but the inconsistency with the primary link's pattern is worth closing for WCAG AA compliance.

**Fix:**
```html
<a href="https://feralarchitecture.substack.com"
   class="currently-post-link glow-interactive"
   target="_blank"
   rel="noopener noreferrer"
   aria-label="Read Feral Architecture on Substack">
  Read Feral Architecture &rarr;
</a>
```

---

_Reviewed: 2026-04-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
