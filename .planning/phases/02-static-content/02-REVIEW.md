---
phase: 02-static-content
reviewed: 2026-04-16T00:00:00Z
depth: standard
files_reviewed: 16
files_reviewed_list:
  - content/_index.md
  - tests/validate-phase-02.sh
  - themes/arcaeon/assets/css/main.css
  - themes/arcaeon/layouts/index.html
  - themes/arcaeon/layouts/partials/icons/bluesky.html
  - themes/arcaeon/layouts/partials/icons/instagram.html
  - themes/arcaeon/layouts/partials/icons/linkedin.html
  - themes/arcaeon/layouts/partials/icons/spotify.html
  - themes/arcaeon/layouts/partials/icons/substack.html
  - themes/arcaeon/layouts/partials/icons/tarotpulse.html
  - themes/arcaeon/layouts/partials/icons/threads.html
  - themes/arcaeon/layouts/partials/icons/x.html
  - themes/arcaeon/layouts/partials/sections/footer.html
  - themes/arcaeon/layouts/partials/sections/hero.html
  - themes/arcaeon/layouts/partials/sections/identity-cta.html
  - themes/arcaeon/layouts/partials/sections/social.html
findings:
  critical: 0
  warning: 2
  info: 2
  total: 4
status: issues_found
---

# Phase 02: Code Review Report

**Reviewed:** 2026-04-16
**Depth:** standard
**Files Reviewed:** 16
**Status:** issues_found

## Summary

Reviewed all 16 source files for Phase 2 — static content, templates, CSS, and the validation script. The implementation is solid: CSS design system is well-structured with proper token layering, accessibility patterns (aria-label, aria-hidden, prefers-reduced-motion) are applied consistently, the social grid correctly uses noopener+noreferrer on external links, and the glow system uses GPU-composited pseudo-elements as intended.

Two warnings and two informational items. No critical issues. Both warnings are in the validation script and hero template — neither is a production blocker, but both will surface as confusing failures under specific conditions.

## Warnings

### WR-01: Hero section silently disappears if image resource is missing

**File:** `themes/arcaeon/layouts/partials/sections/hero.html:3-28`
**Issue:** The entire hero section — including the `<h1>` logotype and tagline — is nested inside `{{ with $img }}...{{ end }}`. If `magus-hero.jpg` doesn't exist in `themes/arcaeon/assets/images/`, Hugo silently renders nothing. The page loads with no h1, no hero, no tagline, and no error. HERO-01 through HERO-04 validation checks would all fail with no indication of why.

The fix is to hoist the text content out of the `{{ with }}` block so the logotype and tagline render regardless of image availability, and optionally render a placeholder or omit the picture element gracefully:

```html
{{/* Hero Section — Magus image + logotype + tagline */}}
{{ $img := resources.Get "images/magus-hero.jpg" }}

<section class="section section-void hero-section">
  {{ with $img }}
    {{ $mobileFill := .Fill "750x580 Center" }}
    {{ $mobileWebP := $mobileFill.Process "webp" }}
    {{ $desktopResize := .Resize "1200x q85" }}
    {{ $desktopWebP := $desktopResize.Process "webp" }}
    <div class="hero-image-wrapper glow-ambient">
      <picture>
        <source media="(min-width: 768px)" type="image/webp" srcset="{{ $desktopWebP.RelPermalink }}">
        <source media="(min-width: 768px)" type="image/jpeg" srcset="{{ $desktopResize.RelPermalink }}">
        <source type="image/webp" srcset="{{ $mobileWebP.RelPermalink }}">
        <img src="{{ $mobileFill.RelPermalink }}"
             alt="Matt Stine as the Magus — laptop open, wand raised, tarot cards in hand, raven on the shelf, lemniscate overhead"
             width="{{ $mobileFill.Width }}"
             height="{{ $mobileFill.Height }}"
             loading="eager"
             class="hero-image">
      </picture>
    </div>
  {{ end }}
  <div class="section-content hero-text">
    <h1 class="display-text">{{ $.Title | default "Falken's Mage" }}</h1>
    {{ with $.Params.tagline }}<p class="hero-tagline">{{ . }}</p>{{ end }}
  </div>
</section>
```

### WR-02: ARIA count check will abort script under pipefail if no aria-label exists

**File:** `tests/validate-phase-02.sh:184`
**Issue:** `set -uo pipefail` is active (line 7). Line 184 runs:

```bash
ARIA_COUNT=$(grep -oF -e 'aria-label=' "$HTML" | wc -l | tr -d ' ')
```

When `grep` finds no matches it exits with code 1. With `-o pipefail`, this exit code propagates through the pipeline and causes the entire script to abort — not record a FAIL for SOCIAL-05, but terminate immediately with no output. This is particularly likely during initial development before all aria-labels are in place.

The same file correctly guards the regression check at line 265 with `|| true`:

```bash
REDUCED_MOTION_COUNT=$(grep -cF -e "prefers-reduced-motion" "$CSS" || true)
```

Apply the same pattern to line 184:

```bash
ARIA_COUNT=$(grep -oF -e 'aria-label=' "$HTML" | wc -l | tr -d ' ' || echo "0")
```

Or use `grep -c` which returns 0 (not a non-zero exit on macOS when using `-c`) and handles the count directly:

```bash
ARIA_COUNT=$(grep -cF -e 'aria-label=' "$HTML" || true)
```

## Info

### IN-01: Hugo build errors silently discarded on failure

**File:** `tests/validate-phase-02.sh:36`
**Issue:** The build step redirects all output to `/dev/null`:

```bash
hugo --minify --quiet > /dev/null 2>&1
```

When the build fails and the script prints "FATAL: Hugo build failed — aborting remaining checks", there's no diagnostic information available. A developer staring at that message has no idea what Hugo actually complained about.

**Fix:** Capture output to a temp file and display it only on failure:

```bash
BUILD_LOG=$(mktemp)
if hugo --minify --quiet > "$BUILD_LOG" 2>&1; then
  pass "hugo --minify exits with code 0"
else
  fail "hugo --minify failed (non-zero exit)"
  echo ""
  echo "Hugo output:"
  cat "$BUILD_LOG"
  rm -f "$BUILD_LOG"
  echo ""
  echo "FATAL: Hugo build failed — aborting remaining checks"
  exit 1
fi
rm -f "$BUILD_LOG"
```

### IN-02: Mobile hero image has no high-density srcset

**File:** `themes/arcaeon/layouts/partials/sections/hero.html:4-5`
**Issue:** The mobile image is processed to a fixed 750px wide crop. On 3x retina devices (e.g., iPhone Pro), the image displays at ~375 CSS pixels wide but is only 750 physical pixels — exactly 2x. 3x devices will upscale it. The desktop source is 1200px wide but also has no density descriptor.

This is a quality note, not a correctness issue. The current implementation meets the project's sub-1s 3G performance constraint by keeping image size bounded. Adding a 3x mobile source would improve sharpness on high-end devices at the cost of ~additional weight.

If sharpness on 3x mobile matters, add a 1125px (3x 375px) mobile source:

```html
{{ $mobile3x := .Fill "1125x870 Center" }}
{{ $mobile3xWebP := $mobile3x.Process "webp" }}
...
<source type="image/webp" srcset="{{ $mobileWebP.RelPermalink }} 1x, {{ $mobile3xWebP.RelPermalink }} 2x">
```

---

_Reviewed: 2026-04-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
