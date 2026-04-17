---
phase: 03-dynamic-layer-quality
audited: 2026-04-16
auditor: gsd-ui-auditor
baseline: 03-UI-SPEC.md
overall_score: 22
max_score: 24
---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 4/4 | All spec-required strings present and correct; "Archetypal tarotist" used correctly; 139-char meta description within target |
| 2. Visuals | 3/4 | Currently card renders cleanly; section triad mismatch creates two consecutive `.section-depth` sections (Currently + Identity+CTA) with no visual separation |
| 3. Color | 3/4 | Electric Violet correctly gated to decoration; Ion Glow used properly for links; triad swap means wrong background colors on Identity+CTA, Social, and Footer vs D-05 spec |
| 4. Typography | 4/4 | All spec sizes and weights matched; `currently-label` correctly uses `var(--text-h3)` size at weight 600 on a semantically appropriate `<h2>` element |
| 5. Spacing | 4/4 | Card padding `1rem` matches `md` token; sub-label gap `0.25rem`, label gap `0.5rem`, post-link margin `1rem` all within declared scale; no arbitrary values |
| 6. Experience Design | 4/4 | RSS fallback wired and tested; `try` wrapping prevents build failure; `aria-labelledby` on section; `glow-interactive:focus-visible` inherited by post link; 6 `prefers-reduced-motion` blocks exceed minimum of 5 |

**Overall: 22/24**

## Top 3 Priority Fixes

### 1. Section triad mismatch — Currently and Identity+CTA are both `.section-depth`

Phase 3 D-05 specified the triad should alternate: `void → depth → void → depth → void`. Phase 2 D-10 had established `Identity+CTA = depth, Social = void, Footer = depth`. When Currently (depth) was inserted, the executor preserved Phase 2's existing assignments rather than applying D-05's re-specified triad. Result: Currently (depth) and Identity+CTA (depth) are adjacent with no visual break between them — they appear as one long Deep Indigo section on screen.

**Fix:** Update `identity-cta.html` to `section-void`, `social.html` to `section-depth`, and `footer.html` to `section-void` — matching D-05's specified triad.

### 2. OG image dimension tags are static strings, not derived from generated image

`baseof.html` lines 31–32 hardcode `content="1200"` and `content="630"` as strings. Hugo's `.Fill "1200x630 Center"` does produce those dimensions for this source image, but if the source image changes, the dimension tags will silently lie to social crawlers.

**Fix:** Replace hardcoded values with `{{ $ogImg.Width }}` and `{{ $ogImg.Height }}` inside the `{{ with $heroSrc }}` block.

### 3. Currently card has no explicit max-width on desktop

The card spans 100% of `section-content` max-width on desktop (56rem / 896px), conflicting with D-04 intent of "compact card" and "lighter weight than Identity or Social sections."

**Fix:** Add `max-width: 32rem` (or similar compact value) to `.currently-card`. Center with `margin: 0 auto` or leave left-aligned per aesthetic preference.

## Detailed Findings

### Pillar 1: Copywriting (4/4)

Every string in the Copywriting Contract section of the spec is correctly implemented:

- `currently.html:22` — "CURRENTLY" verbatim
- `currently.html:24` — "Latest from Feral Architecture:" verbatim
- `currently.html:37` — "Read Feral Architecture →" verbatim
- `baseof.html:7` — Meta description: "Enterprise architect. Archetypal tarotist. Builder of systems that think. Matt Stine at the intersection of code, consciousness, and craft." — 139 chars, within 150–160 target
- OG/Twitter title: "Falken's Mage — Matt Stine" verbatim
- `content/_index.md:14` — `currently_focus` present
- No generic labels found in any layout file
- Fallback URL correctly points to `feralarchitecture.substack.com`
- RSS URL correctly uses `feralarchitecture.com/feed` (not the 301-redirecting Substack URL)
- Post title guillemets render via `&laquo;&thinsp;{title}&thinsp;&raquo;` — matches spec format

### Pillar 2: Visuals (3/4)

**Passing:**
- Hero image renders correctly with full-bleed Magus illustration
- Clear visual hierarchy: large display logotype → tagline → section break → Currently card
- Currently card ghost treatment (transparent fill, Electric Violet border at 0.35 opacity) reads correctly against Deep Indigo background
- Section gradient transitions implemented
- Mobile layout collapses correctly at 375px
- CURRENTLY heading in Cinzel + Ion Glow post link creates correct visual weight distinction

**Issues:**
- Section triad D-05 not applied: Currently and Identity+CTA both Deep Indigo, appearing as merged block. No color break after Currently card before identity bio text begins.
- Currently card spans 100% of section-content max-width on desktop — disproportionate for 3–4 lines of content.

### Pillar 3: Color (3/4)

**Passing:**
- Electric Violet correctly gated: appears only in glow pseudo-elements, card border, sigil elements, and footer lemniscate at 0.5 opacity
- Ion Glow correctly applied to `currently-post-link` via `var(--color-text-accent)` — WCAG AA compliant
- Solar White used for all body text — contrast compliant
- No hardcoded hex colors in layout templates

**Issues:**
- Section triad mismatch: actual operative triad is `void, depth, depth, void, depth` vs specified `void, depth, void, depth, void`. Gradient transitions between consecutive depth sections produce no visual effect.

### Pillar 4: Typography (4/4)

| Element | Spec | Actual | Status |
|---------|------|--------|--------|
| CURRENTLY heading | `var(--text-h3)` / 23px / weight 600 / Cinzel | Matches | Pass |
| Sub-label | 14px / weight 400 / Space Grotesk / opacity 0.7 | Matches | Pass |
| Post title link | 16px / weight 600 / Space Grotesk / Ion Glow | Matches | Pass |
| Focus blurb | 16px / weight 400 / Space Grotesk / opacity 0.85 | Matches | Pass |

`<h2>` element choice semantically correct — first landmark heading within `<main>`. No heading levels skipped.

### Pillar 5: Spacing (4/4)

| Property | Spec | Actual | Status |
|----------|------|--------|--------|
| Card padding | `1rem` (md token) | `padding: 1rem` | Pass |
| Label margin-bottom | `0.5rem` (sm token) | `margin-bottom: 0.5rem` | Pass |
| Sub-label margin-bottom | `0.25rem` (xs token) | `margin-bottom: 0.25rem` | Pass |
| Post link separator | `1rem` (md token) | `margin-bottom: 1rem` | Pass |

No arbitrary spacing values found. All values trace to declared 7-step scale. Card border-radius `8px` matches social card convention.

### Pillar 6: Experience Design (4/4)

- RSS fallback: correctly handles unavailable RSS with static "Read Feral Architecture →" link
- Build resilience: `try` wrapper prevents build failure on RSS timeout; `warnf` logs to build output only
- `currently_focus` always renders regardless of RSS status
- Semantic landmarks: `<header>`, `<main>`, `<footer>` correctly placed; `aria-labelledby` on section
- Focus visible: `glow-interactive` class applied to both live RSS and fallback links
- Motion suppression: 6 `prefers-reduced-motion` blocks (minimum 5 required)
- Alt text: Hero image alt descriptive and present

## Files Audited

- `themes/arcaeon/layouts/partials/sections/currently.html`
- `themes/arcaeon/layouts/partials/sections/hero.html`
- `themes/arcaeon/layouts/partials/sections/identity-cta.html`
- `themes/arcaeon/layouts/partials/sections/social.html`
- `themes/arcaeon/layouts/partials/sections/footer.html`
- `themes/arcaeon/layouts/index.html`
- `themes/arcaeon/layouts/_default/baseof.html`
- `themes/arcaeon/assets/css/main.css`
- `content/_index.md`
- `public/index.html` (rendered build output)
