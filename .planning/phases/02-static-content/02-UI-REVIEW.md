# Phase 2 — UI Review

**Audited:** 2026-04-16
**Baseline:** 02-UI-SPEC.md (approved design contract)
**Screenshots:** Not captured — Playwright browsers not installed (`npx playwright install` required). Dev server confirmed running at localhost:1313. Audit conducted against built `public/index.html` and source CSS/templates.

---

## Pillar Scores

| Pillar | Score | Key Finding |
|--------|-------|-------------|
| 1. Copywriting | 3/4 | CTA button diverges from spec ("Get Feral With Me" vs "Work With Me") — legitimate upgrade but undocumented deviation |
| 2. Visuals | 3/4 | Tablet hero switches to `object-fit: contain` which breaks the intended immersive image treatment |
| 3. Color | 4/4 | Electric Violet correctly confined to glow, border, and decorative elements; no body text violations |
| 4. Typography | 4/4 | Four-tier scale intact, correct font-family assignments, weights match spec |
| 5. Spacing | 3/4 | Social grid gap (0.75rem = 12px) falls between declared scale values; hero section horizontal padding removes declared `xl` (1.25rem) on mobile |
| 6. Experience Design | 4/4 | Full a11y contract met, all reduced-motion paths covered, focus-visible on all interactive elements |

**Overall: 21/24**

---

## Top 3 Priority Fixes

1. **Tablet hero uses `object-fit: contain` instead of `cover`** — At 768px the hero image will letterbox against the Void Purple background rather than filling edge-to-edge, breaking the immersive visual impact the glow-ambient treatment was designed to support. Fix: change the `@media (min-width: 48rem)` block to keep `object-fit: cover` and set `height: 450px` (matching the original Plan 01 intent before it was overridden).

2. **CTA button label changed without spec update** — "Get Feral With Me" shipped instead of specced "Work With Me". The new copy is stronger and fully voice-matched, but the UI-SPEC.md Copywriting Contract still says "Work With Me". This is a documentation gap, not a regression — update the spec so the contract matches reality before Phase 3 inherits stale guidance.

3. **Social grid gap (0.75rem) is off the declared spacing scale** — The spec declares xs/sm/md/xl/2xl/3xl/4xl. 0.75rem = 12px sits between sm (8px) and md (16px) with no declared token. Either add a 12px slot to the scale or shift the gap to `0.5rem` (sm, tighter) or `1rem` (md, more breathing room). Minor but worth locking before Phase 3 adds more components that inherit from the scale.

---

## Detailed Findings

### Pillar 1: Copywriting (3/4)

**What the spec required:**

| Element | Spec | Actual |
|---------|------|--------|
| CTA button text | "Work With Me" | "Get Feral With Me" |
| Hero tagline | "Where enterprise architecture meets the technomagickal." (placeholder) | "He's one technomagickal motherfucker." |
| Identity statement | Single `identity_statement` param | Array via `identity_blocks` — 6 paragraphs |
| CTA description | "Coaching. Speaking. Collaboration." | "Coaching for leaders done performing. Speaking for rooms done pretending. If you're ready to stop splitting yourself in half to fit — let's fucking go." |
| Footer closing | "Stay feral, folks." | "Stay feral, folks." — exact match |
| Footer copyright | "© [year] Digital Intuition LLC" | "© 2026 Digital Intuition LLC" — correct |

**Assessment:** The copy upgrades are genuine improvements. "Get Feral With Me" is more alive than "Work With Me". The six-paragraph identity treatment is richer than the single-sentence placeholder. The CTA description is stronger. All of this is consistent with voice.md and the principle that placeholder copy is "replaceable via front matter." However, the UI-SPEC.md copywriting contract was not updated to reflect these final values — which means any future agent reading the spec will see a mismatch. Score held at 3/4 rather than 2/4 because this is a documentation gap, not a design failure.

**One structural note:** The Plan 01 template used `.Params.identity_statement` (singular string); the actual partial uses `range .Params.identity_blocks` (array). Both render correctly — the front matter was updated to match the partial. This is a clean evolution, but the UI-SPEC.md Component Inventory still references `.identity-statement` as a single `<p>`, while the built output renders six `<p class="identity-statement">` elements. No functional defect — the CSS handles both — but the spec doesn't reflect the actual structure.

**Files:** `content/_index.md`, `themes/arcaeon/layouts/partials/sections/identity-cta.html`

---

### Pillar 2: Visuals (3/4)

**Hero section — desktop/tablet image treatment:**

The `@media (min-width: 48rem)` block in `main.css` (lines 498–509) overrides the mobile `object-fit: cover` behavior:

```css
@media (min-width: 48rem) {
  .hero-image-wrapper {
    max-width: 800px;
    max-height: none;
    overflow: visible;
    margin-left: auto;
    margin-right: auto;
  }

  .hero-image {
    height: auto;
    object-fit: contain;
  }
}
```

`object-fit: contain` will letterbox the 1424×752 source image inside whatever height `height: auto` resolves to. The Void Purple background bleeds through above and below the image. This directly contradicts the spec's intent ("Image full-width up to section max-width") and undermines the ambient glow treatment, which was designed to make the image appear to float within a deep-space field — not to reveal a letterbox gap.

The Plan 01 PLAN.md specified `height: 450px` at tablet and `height: 580px` at desktop with `object-fit: cover` continuing at all breakpoints. Something changed between plan and execution that produced `contain` + `height: auto`.

**Hero section — padding removal at mobile:**

`.hero-section` zeros left and right padding:
```css
.hero-section {
  padding-top: 0;
  padding-left: 0;
  padding-right: 0;
}
```

This is correct and intentional — image bleeds to viewport edges at mobile. The spec confirms "image full-width." No issue here.

**Section order and hierarchy:** Hero → Identity+CTA → Social → Footer renders correctly. Visual hierarchy within the Identity+CTA section is strong — six paragraphs with identical `identity-statement` class create good visual rhythm. The CTA button breaks from body text visually via the Radiant Core gradient and larger padding.

**Sigil placement:** `.sigil-arc .sigil-boundary-tr` on the social section and `.sigil-arc-sm .sigil-boundary-bl` on the footer match the spec's boundary placement rule (D-11). No sigil elements appear within section content areas.

**Files:** `themes/arcaeon/assets/css/main.css` lines 496–515

---

### Pillar 3: Color (4/4)

Electric Violet usage is correctly confined to:
- `.glow-ambient::before` radial gradient (glow, decorative)
- `.glow-interactive::before` radial gradient (glow, decorative)
- `.social-card` border at rest (`rgba(122, 44, 255, 0.35)`) — within spec
- `.social-card:hover` full border (`var(--arcaeon-electric-violet)`) — within spec
- `.sigil-gradient::after` gradient line (decorative, opacity 0.4) — within spec
- `.footer-lemniscate` color at opacity 0.5 — decorative glyph, `aria-hidden="true"`, not body text — within spec

No Electric Violet appears on body text, identity statement, tagline, CTA description, social labels, or footer text.

The three hardcoded values in the CSS are not violations:
- `rgba(122, 44, 255, 0.35)` — documented spec exception for ghost card border (can't express with `var()` + opacity simultaneously in CSS without `color-mix()`)
- Two hex values in comments only

The Radiant Core gradient (Fusion Gold → Ignition Orange) on the CTA button is correctly applied via `.glow-radiant-core`. CTA button text uses `var(--arcaeon-void-purple)` for contrast safety.

Section backgrounds alternate `.section-void` (Void Purple) and `.section-depth` (Deep Indigo) in the correct order per D-10.

**Files:** `themes/arcaeon/assets/css/main.css`

---

### Pillar 4: Typography (4/4)

The four-tier system is intact:

| Tier | Expected | Actual |
|------|----------|--------|
| Display | Cinzel, clamp(2.5rem, 8vw, 4rem), weight 800 | Correct — `.display-text` |
| H1 | Cinzel, 2.074rem, weight 700 | Correct — `h1` rule |
| H2/Tagline | Cinzel or Space Grotesk, 1.728rem, weight 600 | Correct — `.hero-tagline` |
| Body/Label | Space Grotesk, 1rem, 400/600 | Correct |

Cinzel is used exclusively for headings and the footer-closing element. Space Grotesk covers all body text, social labels, and UI copy. No cross-assignment.

Font weight 300 appears in the `@font-face` declaration range (`300 700`) but is not applied to any element rule — it's a range declaration, not actual usage. The declared weights in element rules are 400 and 600, matching the spec.

The footer closing ("Stay feral, folks.") uses `.footer-closing` with `font-family: var(--font-display)` at `var(--text-h2)` weight 600 — Cinzel treatment at the sub-heading tier, appropriate for a closing mark of that weight.

`font-display: swap` present on both font-face declarations — no FOIT risk.

**Files:** `themes/arcaeon/assets/css/main.css` lines 115–194

---

### Pillar 5: Spacing (3/4)

**Declared scale (from spec):**

| Token | Value |
|-------|-------|
| xs | 4px / 0.25rem |
| sm | 8px / 0.5rem |
| md | 16px / 1rem |
| xl | 24px / 1.5rem |
| 2xl | 32px / 2rem |
| 3xl | 48px / 3rem |
| 4xl | 64px / 4rem |

**Findings:**

`gap: 0.75rem` (12px) in the social grid — between sm and md with no declared token. Minor but outside the four-corner rule. The spec does document an exception for social card padding (12px vertical × 16px horizontal) as a visual breathing room choice — but the grid gap was not listed as an exception. Low severity.

`margin-bottom: 0.75rem` on `.footer-lemniscate` — same 12px undeclared value.

`margin-top: 0.75rem` on `.hero-tagline` — same.

The 0.75rem value appears three times, consistently, so this appears to be an intentional micro-spacing choice that was applied without declaring a token. Either formalize it (`--space-xs-plus: 0.75rem` or a named exception) or replace with `0.5rem` (sm) or `1rem` (md).

Section padding values are correct: 3rem/1.25rem mobile, 4rem/2rem tablet, 5rem/2rem desktop. These match the Phase 1 established values.

CTA button padding `0.875rem 2rem` — the vertical value (0.875rem = 14px) is undeclared but within spec's documented exception ("12px vertical × 32px horizontal" for CTA button). The actual implementation uses 14px rather than 12px — close enough to be intentional breathing room, not a flag.

**Files:** `themes/arcaeon/assets/css/main.css` lines 558–620

---

### Pillar 6: Experience Design (4/4)

**Accessibility contract — fully met:**

| Requirement | Status |
|-------------|--------|
| Hero image alt text | Present and descriptive — passes WCAG 1.1.1 |
| Social link aria-labels | 8 of 8 present — passes WCAG 4.1.2 |
| Lemniscate aria-hidden | Present — passes WCAG 1.1.1 |
| Touch targets min-height 44px | Present on `.social-card` — passes WCAG 2.5.5 |
| External links rel="noopener noreferrer" | 8 of 8 — security hygiene met |
| mailto no target="_blank" | Correct — native OS protocol handler |
| focus-visible on interactive elements | Present on `.glow-interactive`, `.glow-radiant-core`, `.social-card` |

**Reduced motion — 5 declarations:**
1. `html { scroll-behavior: auto }` — Phase 1 baseline
2. `.glow-ambient::before { animation: none; opacity: 0.3 }` — hero glow locked static
3. `.glow-interactive::before { transition: none }` — social card glow suppressed
4. `.glow-radiant-core::before { transition: none }` — CTA glow suppressed
5. `.social-card { transition: none }` — border/color transition suppressed

All five reduced-motion paths are correct. The Phase 1 regression check (HERO-04-REG) confirmed these remain intact.

**Loading states:** This is a static display surface with no async content in Phase 2. Loading states are not applicable — the `loading="eager"` on the above-fold hero image is the correct choice (not a loading state omission, but correct behavior).

**Error/empty states:** Not applicable to Phase 2 static surface per the UI-SPEC.md contract.

**Registry audit:** Not applicable. No `components.json` present. No shadcn, no third-party registries.

**Files:** `public/index.html` (built output), `themes/arcaeon/assets/css/main.css`

---

## Files Audited

- `content/_index.md`
- `themes/arcaeon/layouts/index.html`
- `themes/arcaeon/layouts/partials/sections/hero.html`
- `themes/arcaeon/layouts/partials/sections/identity-cta.html`
- `themes/arcaeon/layouts/partials/sections/social.html`
- `themes/arcaeon/layouts/partials/sections/footer.html`
- `themes/arcaeon/assets/css/main.css`
- `public/index.html` (built output — `hugo --minify`)
- `.planning/phases/02-static-content/02-UI-SPEC.md`
- `.planning/phases/02-static-content/02-CONTEXT.md`
- `.planning/phases/02-static-content/02-01-SUMMARY.md`
- `.planning/phases/02-static-content/02-02-SUMMARY.md`
- `.planning/phases/02-static-content/02-03-SUMMARY.md`
