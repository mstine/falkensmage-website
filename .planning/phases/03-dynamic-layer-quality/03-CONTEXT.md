# Phase 3: Dynamic Layer + Quality - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

The site is complete, fast, accessible, and search-legible. The "Currently" section pulls live Substack content via RSS at build time and shows a static fallback when unreachable. Performance hits sub-1s on 3G. Semantic HTML5 landmarks and WCAG AA contrast are in place. Open Graph and Twitter Card meta tags surface the Magus image and identity on social shares.

</domain>

<decisions>
## Implementation Decisions

### "Currently" Section
- **D-01:** Placement — after Hero, before Identity+CTA. Fresh content up top so a stranger sees what you're thinking about right now before the bio.
- **D-02:** RSS content — title + link only. Just the latest Feral Architecture post title as a clickable link. No date, no excerpt. Clean and minimal.
- **D-03:** Fallback — static "Read Feral Architecture" link to Substack homepage when RSS is unreachable at build time. The "current focus" blurb from front matter always shows regardless of RSS status.
- **D-04:** Visual treatment — compact card-like block on Deep Indigo background (`.section-depth`). Not a full-width section — reads as a contained information module. Lighter weight than Identity or Social sections.
- **D-05:** Section triad assignment — Currently gets `.section-depth` (Deep Indigo). Page flow becomes: Hero (`.section-void`) → Currently (`.section-depth`) → Identity+CTA (`.section-void`) → Social (`.section-depth`) → Footer (`.section-void`). Alternation continues cleanly.

### Performance
- **D-06:** Hero image — WebP conversion + responsive srcset at 375w, 750w, 1200w via Hugo image pipeline. `<picture>` element with WebP source + JPEG fallback. Hero stays eager-loaded (above fold).
- **D-07:** Font preloading — add `<link rel="preload">` hints in `<head>` for both WOFF2 files (Cinzel Variable + Space Grotesk Variable) with `as="font"`, `type="font/woff2"`, and `crossorigin` attributes. Eliminates FOUT flash.
- **D-08:** No lazy-loading needed for below-fold images — social icons are inline SVG, no other images exist below the hero. The `loading="lazy"` attribute is not applicable here.

### Semantic Structure + Accessibility
- **D-09:** Landmark structure — `<header>` wraps the Hero section with the `<h1>`, `<main>` wraps Currently + Identity+CTA + Social sections, `<footer>` wraps the footer section. No `<nav>` — single page with no navigation links.
- **D-10:** Magus image alt text — Claude's discretion. Write descriptive alt text based on viewing the actual image, describing the scene for screen readers.
- **D-11:** Contrast audit — verify all text/background pairs meet WCAG AA. Neon accents (Electric Violet, Neon Magenta) are decoration-only per existing convention. Body text uses Solar White/Ion Glow on Void Purple/Deep Indigo backgrounds.
- **D-12:** `prefers-reduced-motion` — already implemented for ambient glow pulse in Phase 1. Verify it suppresses all animations site-wide.

### SEO & Open Graph
- **D-13:** Twitter Card type — `summary_large_image`. The Magus image at 1424x752 is perfect for the large format.
- **D-14:** Meta description — identity-forward. Leads with who Falken's Mage is (enterprise architect, archetypal tarotist, systems builder). Encodes the identity, not the site's function. Claude writes the final copy in Matt's voice.
- **D-15:** OG image — Hugo generates a 1200x630 resize/crop from the Magus source specifically for OG/social cards. Matches the standard exactly.
- **D-16:** OG title — "Falken's Mage — Matt Stine" (per SEO-01).
- **D-17:** Canonical URL — `https://falkensmage.com` (per SEO-03).

### Claude's Discretion
- Exact alt text wording for Magus hero image (D-10)
- Meta description final copy (D-14) — identity-forward direction is locked, wording is flexible
- Card border/background treatment for "Currently" module (D-04) — subtle distinction from section background
- Triad alternation adjustment if needed after inserting the new Currently section (D-05)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Hugo RSS Pattern
- `CLAUDE.md` §RSS Fetch Pattern (Build-Time) — `resources.GetRemote` + `transform.Unmarshal` pattern for Substack RSS
- `CLAUDE.md` §Technology Stack — Hugo Extended 0.160.1, `css.Build` pipeline, image processing

### ARCAEON Design System
- `~/.psyche/swipe-files/podcasting-creative/2026-04-16-12-33-18-arc-on-color-palette-full.md` — Full ARCAEON palette with Triad Rule
- `.planning/phases/01-theme-foundation/01-CONTEXT.md` — All Phase 1 design system decisions (token naming, glow classes, pseudo-element conventions)

### Phase 2 Implementation
- `.planning/phases/02-static-content/02-CONTEXT.md` — Section flow, triad assignments, image handling patterns
- `content/_index.md` — Front matter data layer pattern (all copy sourced from params)
- `themes/arcaeon/layouts/_default/baseof.html` — Current `<head>` structure that needs OG/meta additions

### Project Requirements
- `.planning/REQUIREMENTS.md` §Currently Section — CURR-01, CURR-02, CURR-03 acceptance criteria
- `.planning/REQUIREMENTS.md` §Performance — PERF-01 through PERF-04 acceptance criteria
- `.planning/REQUIREMENTS.md` §Accessibility — A11Y-01 through A11Y-04 acceptance criteria
- `.planning/REQUIREMENTS.md` §SEO & Meta — SEO-01, SEO-02, SEO-03 acceptance criteria

### Hero Image Source
- `~/Documents/Business-Brand/Feral-Architecture/covers/2026-04-14-aesthetic-decisions/final/aesthetic-decisions-cover.jpg` — 1424x752 source for OG crop and responsive srcset generation

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.glow-ambient` — ambient pulse class (Electric Violet, 5s cycle) — for Currently card if glow treatment desired
- `.glow-interactive` — hover/focus glow class — for RSS post link hover
- `.section-void` / `.section-depth` — alternating section backgrounds with Triad Rule vars
- `.section` + `.section-content` — section spacing and max-width container
- `.section + .section::before` — gradient transition between adjacent sections
- Hugo `css.Build` pipeline — `resources.Get | css.Build | minify | fingerprint` in baseof.html
- Inline SVG icon partial pattern from social links — no external image dependencies

### Established Patterns
- `::before` reserved for glow effects, `::after` reserved for sigils (Phase 1 convention)
- Two-tier token naming: palette truth (`--arcaeon-*`) + semantic aliases (`--color-*`)
- Content as front matter data: all copy sourced from `_index.md` params, zero hardcoded strings
- Hugo `.Process "webp"` for format conversion (not `.Format` — Phase 2 decision)
- `currentColor` on SVG icons for CSS-driven color changes

### Integration Points
- `themes/arcaeon/layouts/index.html` — needs Currently partial inserted after Hero
- `themes/arcaeon/layouts/_default/baseof.html` — needs `<header>`/`<footer>` landmarks, font preload links, OG/meta tags in `<head>`
- `content/_index.md` — needs `currently_focus` front matter field for manual blurb
- `themes/arcaeon/layouts/partials/sections/` — needs new `currently.html` partial
- `themes/arcaeon/assets/css/main.css` — needs Currently card styles appended

</code_context>

<specifics>
## Specific Ideas

- Currently section preview mockup confirmed: "CURRENTLY" header, "Latest from Feral Architecture:" label, post title in guillemets (« »), then current focus blurb below
- RSS fallback shows "Read Feral Architecture →" with link to feralarchitecture.substack.com
- Meta description direction: "Enterprise architect. Archetypal tarotist. Builder of systems that think." — identity-forward, not action-forward
- OG title locked: "Falken's Mage — Matt Stine"

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 03-dynamic-layer-quality*
*Context gathered: 2026-04-16*
