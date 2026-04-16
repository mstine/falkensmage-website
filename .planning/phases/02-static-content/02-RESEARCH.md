# Phase 2: Static Content — Research

**Researched:** 2026-04-16
**Domain:** Hugo templating, image processing pipeline, CSS layout, SVG icons, content data patterns
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Hero Composition**
- D-01: Image above, text below on mobile (375px). Magus image full-width at top, "Falken's Mage" logotype + tagline stacked below. Clean separation.
- D-02: Mobile image crop via `object-fit: cover` with a taller container (~280-300px) to center-crop the 1424x752 source into approximately 4:3. Loses edges but gives visual weight. Hugo `<picture>` with art direction handles responsive variants.
- D-03: Ambient glow pulse (`.glow-ambient`) wraps the hero image container — Electric Violet bleeds out from behind the Magus. Image is the focal point.
- D-04 (Discretion): Desktop hero layout is Claude's discretion — stacked or side-by-side.

**Social Links Layout**
- D-05: 2-column grid on mobile (4 rows × 2 links). Scales to 3-4 columns on tablet/desktop. Each cell: icon + label.
- D-06: Inline SVG icons embedded directly in the Hugo social links partial. Zero HTTP requests, fully CSS-styleable. 8 hand-curated SVG paths.
- D-07 (Discretion): Feral Architecture (Substack) in the top-left position. Claude arranges remaining 7 platforms for visual/logical flow.
- D-08 (Discretion): Social link card style is Claude's discretion — filled card with glow hover or ghost card (border only). Must use `.glow-interactive` for hover treatment.

**Section Flow & Triad Assignments**
- D-09: Four sections top-to-bottom: Hero → Identity+CTA (combined) → Social Links → Footer. Identity statement flows directly into the "Work With Me" CTA.
- D-10: Triad alternation: Hero = `.section-void`, Identity+CTA = `.section-depth`, Social = `.section-void`, Footer = `.section-depth`.
- D-11 (Discretion): Sigil decorative elements at section boundaries only. Sizes and rotation angles are Claude's discretion.

**Identity & Copy Tone**
- D-12: Identity statement lives inside the Identity+CTA section (Deep Indigo background).
- D-13: Full-voice placeholder copy in Matt's voice (first person, direct, alive, irreverent). Replaceable via `content/_index.md` front matter.
- D-14: Full-voice placeholder for hero tagline slot. Replaceable via front matter.
- D-15: CTA copy: "Coaching. Speaking. Collaboration." + single mailto button (`falkensmage@falkenslabyrinth.com`). Radiant Core glow treatment.

### Claude's Discretion
- Desktop hero layout (stacked vs side-by-side) — D-04
- Social link card style (filled vs ghost) — D-08
- Social link platform ordering after Feral Architecture — D-07
- Sigil arc sizes and rotation angles at section boundaries — D-11
- Exact image container height for mobile crop (280-300px range) — D-02

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| HERO-01 | Magus image full-width/near-full-width with responsive art direction (portrait crop mobile 375px, original aspect desktop) | Hugo image processing verified: `.Fill "750x580 Center"` for mobile, `.Resize "1200x q85"` for desktop, `.Process "webp"` for format conversion. `<picture>` art direction pattern confirmed working. |
| HERO-02 | "Falken's Mage" display treatment — large typographic presence using Cinzel display weight | `.display-text` class already exists in Phase 1: Cinzel Variable, `clamp(2.5rem, 8vw, 4rem)`, weight 800. Ready to apply. |
| HERO-03 | Tagline placeholder slot — styled typography treatment, easily swappable | Front matter param in `content/_index.md` → `{{ .Params.tagline }}` in template. Documented copy direction. |
| HERO-04 | Ambient glow pulse animation on hero image — CSS-only, GPU-composited, honors `prefers-reduced-motion` | `.glow-ambient` class fully built in Phase 1. Apply to image wrapper `<div>`. Known interaction with section `overflow: hidden` documented. |
| IDENT-01 | 2-3 sentence identity statement in Matt's voice — first-person, "technomagickal motherfucker" energy | Voice-matched placeholder copy drafted. Front matter param pattern verified. |
| IDENT-02 | Placeholder text scaffolded in Matt's voice style, easily replaceable | `content/_index.md` front matter → `{{ .Params.identity_statement }}`. Verified Hugo template access works. |
| SOCIAL-01 | Social links section with icon + label for each platform, styled as grid | 2-column CSS grid confirmed for mobile. SVG icon paths documented for all 8 platforms. Hugo partial structure planned. |
| SOCIAL-02 | Hover animation on each social link — ARCÆON glow aesthetic | `.glow-interactive` class built in Phase 1. Confirmed z-index layering requirement: card content needs `position: relative; z-index: 1`. |
| SOCIAL-03 | Minimum 44px touch targets on all social links | CSS minimum height/min-width: 44px on `.social-card`. Verified pattern. |
| SOCIAL-04 | 8 platforms: Feral Architecture, LinkedIn, X, Instagram, Threads, Bluesky, Spotify, TarotPulse | All 8 URLs confirmed from SPEC.md. SVG paths sourced for all platforms. |
| SOCIAL-05 | Aria-labels on all social links for accessibility | `aria-label="{{ .name }} on {{ .platform }}"` pattern in Hugo template. |
| CTA-01 | Brief description — coaching, speaking, collaboration | Copy locked: "Coaching. Speaking. Collaboration." via `{{ .Params.cta_description }}`. |
| CTA-02 | Single mailto CTA button with Radiant Core glow treatment | `.glow-radiant-core` class fully built in Phase 1. `<a href="mailto:...">` with class applied. |
| FOOT-01 | "Stay feral, folks." signature closing | Exact copy locked. `{{ .Params.footer_closing }}` or hardcoded in footer partial. |
| FOOT-02 | Copyright: Digital Intuition LLC with current year | `{{ now.Year }}` Hugo template function for dynamic year. |
| FOOT-03 | Subtle lemniscate/sigil mark as decorative element | Unicode ∞ (U+221E) styled with Electric Violet, low opacity — or inline SVG lemniscate. CSS approach consistent with Phase 1 sigil grammar. |

</phase_requirements>

---

## Summary

Phase 2 builds all visible content sections on top of the complete Phase 1 design system. Every glow class, section alternation pattern, typography treatment, and font is already in place. This phase is purely assembly: Hugo partials for four sections, a `<picture>` art direction pipeline for the hero image, inline SVG icons for social links, and content data wired through `content/_index.md` front matter.

The image processing pipeline is the most technically novel piece. The Magus source image is 1424x752 (landscape, 1.89:1 ratio). On a 375px mobile viewport with a ~290px container height, `object-fit: cover` with a center anchor crops the image correctly — losing ~87px on each horizontal edge but preserving the Magus figure. Hugo's `.Fill "750x580 Center"` (2x retina) handles this exactly. The `<picture>` element with `media="(min-width: 768px)"` source delivers the full-width desktop variant. WebP conversion via `.Process "webp"` is confirmed working in Hugo 0.160.1.

The three critical implementation decisions with non-obvious technical requirements: (1) the sigil `::after` elements need explicit `top`/`right` positioning CSS added in Phase 2 — Phase 1 defined the shape but not the placement; (2) social card content needs `position: relative; z-index: 1` to appear above the `.glow-interactive::before` glow layer; (3) the image must live in `themes/arcaeon/assets/images/` (not `static/`) for Hugo's processing pipeline to access it — the source image has been copied there already.

**Primary recommendation:** Build in wave order — image pipeline first (most risk), then section partials and CSS in the established Phase 1 patterns, then content data wiring, then validation script extension.

---

## Standard Stack

### Core (all already installed/configured in Phase 1)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Hugo Extended | 0.160.1 | Builds all partials, image processing, template rendering | Phase 1 established, verified working. [VERIFIED: `hugo version` output] |
| Hugo css.Build | built-in 0.160+ | CSS pipeline — no new CSS tooling needed | Phase 1 CSS already processed through this pipeline. [VERIFIED: Phase 1 build] |
| Cinzel Variable | 5.2.8 | `.display-text` for "Falken's Mage" logotype | Phase 1 installed and declared in `@font-face`. [VERIFIED: filesystem] |
| Space Grotesk Variable | 5.2.10 | Body text throughout all sections | Phase 1 installed. [VERIFIED: filesystem] |

### No New Dependencies
Phase 2 requires zero new npm packages or Hugo modules. Everything needed is already in the Phase 1 baseline.

**Build command (unchanged):**
```bash
hugo --minify
```

**Dev server (unchanged):**
```bash
hugo server --buildDrafts
```

---

## Architecture Patterns

### Recommended Project Structure (new files only)

```
themes/arcaeon/
├── assets/
│   ├── css/
│   │   └── main.css              # EXTEND with section-specific CSS
│   └── images/
│       └── magus-hero.jpg        # ALREADY COPIED (1424x752 source)
├── layouts/
│   ├── index.html                # REPLACE: wire section partials
│   └── partials/
│       └── sections/
│           ├── hero.html         # NEW: hero section partial
│           ├── identity-cta.html # NEW: identity + CTA section partial
│           ├── social.html       # NEW: social links section partial
│           └── footer.html       # NEW: footer section partial
content/
└── _index.md                     # EXTEND: add all content params
tests/
└── validate-phase-02.sh          # NEW: validation script
```

### Pattern 1: Hugo Section Partial Architecture

**What:** The `index.html` template becomes a thin orchestrator that includes section partials in order. Each partial is self-contained — its own HTML structure, section class, and content data access.

**When to use:** All four sections (Hero, Identity+CTA, Social, Footer).

**Example (`layouts/index.html`):**
```html
{{ define "main" }}
<main>
  {{ partial "sections/hero.html" . }}
  {{ partial "sections/identity-cta.html" . }}
  {{ partial "sections/social.html" . }}
  {{ partial "sections/footer.html" . }}
</main>
{{ end }}
```

### Pattern 2: Hugo Image Processing Pipeline

**What:** Image placed in `themes/arcaeon/assets/images/`. `resources.Get` loads it. `.Fill` crops to exact dimensions. `.Resize` maintains aspect for desktop. `.Process "webp"` converts format. `<picture>` provides art direction with WebP + JPEG fallback.

**Verified syntax (Hugo 0.160.1):** [VERIFIED: live build test]
```html
{{ $img := resources.Get "images/magus-hero.jpg" }}
{{ $mobileFill := $img.Fill "750x580 Center" }}
{{ $mobileWebP := $mobileFill.Process "webp" }}
{{ $desktopResize := $img.Resize "1200x q85" }}
{{ $desktopWebP := $desktopResize.Process "webp" }}

<picture>
  <source media="(min-width: 768px)" type="image/webp" srcset="{{ $desktopWebP.RelPermalink }}">
  <source media="(min-width: 768px)" type="image/jpeg" srcset="{{ $desktopResize.RelPermalink }}">
  <source type="image/webp" srcset="{{ $mobileWebP.RelPermalink }}">
  <img src="{{ $mobileFill.RelPermalink }}"
       alt="Matt Stine as the Magus — laptop open, wand raised, tarot cards in hand, raven on the shelf, lemniscate overhead"
       width="{{ $mobileFill.Width }}"
       height="{{ $mobileFill.Height }}"
       loading="eager">
</picture>
```

**Important:** `.Format "webp"` does NOT work — `.Process "webp"` is the correct method for format conversion in Hugo 0.160.1. [VERIFIED: error message confirmed `.Format` fails on `images.ImageResource`]

### Pattern 3: Content Data via Front Matter

**What:** All user-editable copy and social link data lives in `content/_index.md` front matter. Templates read via `.Params.*`. This separates data from presentation without adding a data file dependency.

**Verified syntax:** [VERIFIED: live build test]

`content/_index.md`:
```yaml
---
title: "Falken's Mage"
tagline: "[Matt's line — placeholder until written]"
identity_statement: "[Placeholder in Matt's voice]"
cta_description: "Coaching. Speaking. Collaboration."
cta_email: "falkensmage@falkenslabyrinth.com"
footer_closing: "Stay feral, folks."
social_links:
  - name: "Feral Architecture"
    url: "https://feralarchitecture.substack.com"
    label: "Substack"
    icon: "substack"
  - name: "LinkedIn"
    url: "https://linkedin.com/in/mattstine"
    label: "LinkedIn"
    icon: "linkedin"
  # ... (8 total)
---
```

Template access:
```html
{{ .Params.identity_statement }}
{{ range .Params.social_links }}{{ .name }} — {{ .url }}{{ end }}
```

### Pattern 4: Social Card with Inline SVG + Glow

**What:** Each social link is an `<a>` with `.social-card.glow-interactive`. Content children need `position: relative; z-index: 1` to appear above the `::before` glow layer. Inline SVG icon + label span.

**Z-index layering requirement:** [VERIFIED: CSS inspection of Phase 1 `.glow-interactive::before { z-index: 0 }`]
```html
<a href="{{ .url }}" 
   class="social-card glow-interactive"
   target="_blank"
   rel="noopener noreferrer"
   aria-label="{{ .name }}">
  <span class="social-card__icon" aria-hidden="true">
    {{/* inline SVG here */}}
  </span>
  <span class="social-card__label">{{ .label }}</span>
</a>
```

Required CSS addition to `main.css`:
```css
.social-card__icon,
.social-card__label {
  position: relative;
  z-index: 1;
}
```

### Pattern 5: Sigil Placement at Section Boundaries

**What:** Sigil `::after` pseudo-elements need explicit `top`/`right`/`left` coordinates. Phase 1 defined the shape but not placement coordinates. Phase 2 adds positioning CSS for boundary-specific variants.

**Recommended approach:** Add modifier classes for boundary placement positions:
```css
/* Section boundary sigil — top-right corner */
.sigil-boundary-tr::after {
  top: -20px;
  right: 2rem;
}

/* Section boundary sigil — bottom-left corner */
.sigil-boundary-bl::after {
  bottom: -20px;
  left: 2rem;
}
```

Apply as multi-class on the section element:
```html
<section class="section section-depth sigil-arc sigil-boundary-tr">
```

### Recommended Desktop Hero Layout (Claude's Discretion — D-04)

Given the 1424x752 landscape source, the desktop layout recommendation is **stacked** (same as mobile, just larger). Side-by-side would require the image to be cropped to a narrower column, losing the full horizontal impact of the scene. The image is meant to dominate. On desktop at `min-width: 1024px`, the hero section can use a larger container (up to 56rem per Phase 1 `.section-content` max-width), with the image scaling to full container width and the text treatment below.

**Rationale:** The Magus at the desk scene has wide compositional importance — the lemniscate overhead, raven on shelf, laptop and wand. Side-by-side forces a 50% crop. Full-width stacked lets the image breathe.

### Recommended Social Card Style (Claude's Discretion — D-08)

**Ghost card** (border only, no fill) against `.section-void` (Void Purple background). The Electric Violet border at low opacity completes the ARCÆON Triad (purple + blue + warm). `.glow-interactive` adds the Electric Violet radial fill on hover. Ghost reads lighter on dark — more "feral" than corporate card style.

```css
.social-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border: 1px solid rgba(122, 44, 255, 0.35); /* Electric Violet at low opacity */
  border-radius: 8px;
  min-height: 44px;  /* SOCIAL-03: 44px touch target */
  color: var(--color-text);
  text-decoration: none;
  transition: border-color 0.25s ease, color 0.25s ease;
}

.social-card:hover,
.social-card:focus-visible {
  border-color: var(--arcaeon-electric-violet);
  color: var(--arcaeon-ion-glow);
}
```

### Recommended Social Link Platform Order (Claude's Discretion — D-07)

Top-left anchor = Feral Architecture (Substack). Remaining 7 in a logical cluster grouping:
1. Feral Architecture (Substack) — primary content platform, top-left
2. LinkedIn — professional identity, high-value discovery
3. X — real-time presence
4. Bluesky — alternative/feral social
5. Instagram — visual identity
6. Threads — Meta cross-post
7. Spotify — "Falken's Labyrinth" album, unexpected delight
8. TarotPulse — owned platform, tech credibility signal

Reading order: professional clusters (1-4) then personal/creative clusters (5-8).

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Image format conversion | Custom build script | `$img.Process "webp"` in Hugo | Hugo handles caching, fingerprinting, and output path management |
| Image crop/resize | ImageMagick preprocessing | `$img.Fill "750x580 Center"` | Hugo rebuilds on source change, caches derived images |
| Responsive `<picture>` | JS lazy-loader | Native `<picture>` + `media` attribute | Zero JS, correct browser-native behavior |
| Social icon sprites | Custom SVG spritesheet | Inline SVG per card | Phase 1 decision (D-06): inline SVG is simpler for 8 icons, eliminates HTTP request |
| Content editable fields | CMS, Forestry, NetlifyCMS | `content/_index.md` front matter | Hugo's built-in. Zero tooling, plaintext, git-native |
| Touch target sizing | JS tap detection | CSS `min-height: 44px` | Native, zero cost, correct |
| Dynamic copyright year | Hardcoded "2025" | `{{ now.Year }}` Hugo template | Automatic, never stale |

**Key insight:** Hugo's image pipeline replaces every external image optimization tool. Don't introduce build steps that Hugo already handles.

---

## Common Pitfalls

### Pitfall 1: Wrong Hugo Image Format Conversion Method

**What goes wrong:** Calling `.Format "webp"` on an `images.ImageResource` errors: `can't evaluate field Format in type images.ImageResource`.

**Why it happens:** Hugo's image processing methods are on the resource type returned by `resources.Get`. The `.Format` method does not exist. Format conversion uses `.Process "webp"`.

**How to avoid:** Always chain: `$resized := $img.Fill "WxH Center"` then `$webp := $resized.Process "webp"`. [VERIFIED: confirmed error and correct syntax via live build test]

**Warning signs:** Template fails to render with "can't evaluate field Format" error.

### Pitfall 2: Image in `static/` Instead of `assets/`

**What goes wrong:** Hugo can serve images from `static/` but CANNOT process them (resize, convert, fingerprint). If the Magus image is in `static/images/`, `resources.Get "images/magus-hero.jpg"` returns nil. The template silently produces no image.

**Why it happens:** Hugo has two image directories with different capabilities. `static/` is passthrough. `assets/` is processable.

**How to avoid:** Image must be in `themes/arcaeon/assets/images/magus-hero.jpg` (or project `assets/images/`). The image has already been copied to `themes/arcaeon/assets/images/magus-hero.jpg` during research. [VERIFIED: image present, `.Fill` and `.Process` confirmed working]

**Warning signs:** `{{ if $img }}` block is never entered; `resources.Get` returns nil.

### Pitfall 3: Social Card Content Hidden Behind Glow Layer

**What goes wrong:** Social card icon and label are invisible (rendered behind the `.glow-interactive::before` glow layer at `z-index: 0`).

**Why it happens:** `.glow-interactive` sets `isolation: isolate` which creates a stacking context. Without explicit `z-index` on child elements, they may fall beneath the `::before` layer depending on browser rendering order.

**How to avoid:** Add to CSS: `.social-card__icon, .social-card__label { position: relative; z-index: 1; }`. [VERIFIED: Phase 1 CSS inspection shows `::before` at `z-index: 0`]

**Warning signs:** Cards render as empty rectangles that glow on hover but show no icon or text.

### Pitfall 4: Sigil Positions Default to Top-Left Corner

**What goes wrong:** All sigil decorative elements stack at the top-left corner of every section (x:0, y:0 absolute position within the section).

**Why it happens:** Phase 1 defined `.sigil-arc::after { position: absolute }` without `top`/`right` values. Without coordinates, `position: absolute` defaults to the element's natural flow position — effectively top-left of the nearest `position: relative` ancestor (the section).

**How to avoid:** Add boundary placement modifier classes in Phase 2 CSS with explicit `top`/`right`/`bottom`/`left` values. [VERIFIED: CSS inspection of Phase 1 `.sigil-arc::after`]

**Warning signs:** All section-boundary sigils overlap in the same corner position.

### Pitfall 5: Ambient Glow Clipped by Section Overflow

**What goes wrong:** The `.glow-ambient::before` glow appears as a hard-edged rectangle rather than a soft radial spread, because `.section { overflow: hidden }` clips everything outside the section boundary.

**Why it happens:** `.glow-ambient::before { inset: -20% }` extends 20% beyond the image container. When the image container is inside `.section { overflow: hidden }`, the outer 20% extension is clipped at the section edge.

**How to avoid:** This is acceptable behavior for the hero section — D-03 specifies the glow bleeds from behind the Magus within the hero, not between sections. The glow is still visible within the section height. If the glow appears too clipped, add `.hero-section { overflow: visible }` to the hero section specifically. [ASSESSED: overflow: hidden is correct for inter-section boundaries; hero-internal glow is sufficient]

**Warning signs:** Glow looks like a box outline rather than a radial spread. If so, override `overflow` on the hero section only.

### Pitfall 6: `mailto:` Link Treated as External Link

**What goes wrong:** The CTA button opens in a new tab instead of the email client, or accessibility tools flag it as an external link.

**Why it happens:** Adding `target="_blank"` to a `mailto:` href is incorrect. `mailto:` links should not have `target="_blank"` — they are native OS protocol handlers.

**How to avoid:** Do not add `target="_blank" rel="noopener"` to the `<a href="mailto:...">` CTA. Those attributes are for web URLs only. [ASSUMED — standard HTML specification behavior, not verified in this session]

---

## Code Examples

Verified patterns from live build tests:

### Hero Section Partial Structure
```html
{{/* themes/arcaeon/layouts/partials/sections/hero.html */}}
{{ $img := resources.Get "images/magus-hero.jpg" }}
{{ $mobileFill := $img.Fill "750x580 Center" }}
{{ $mobileWebP := $mobileFill.Process "webp" }}
{{ $desktopResize := $img.Resize "1200x q85" }}
{{ $desktopWebP := $desktopResize.Process "webp" }}

<section class="section section-void hero-section">
  <div class="hero-image-wrapper glow-ambient">
    <picture>
      <source media="(min-width: 768px)" type="image/webp" srcset="{{ $desktopWebP.RelPermalink }}">
      <source media="(min-width: 768px)" type="image/jpeg" srcset="{{ $desktopResize.RelPermalink }}">
      <source type="image/webp" srcset="{{ $mobileWebP.RelPermalink }}">
      <img src="{{ $mobileFill.RelPermalink }}"
           alt="Matt Stine as the Magus — laptop open, wand raised, tarot cards in hand, raven on the shelf, lemniscate overhead"
           width="{{ $mobileFill.Width }}"
           height="{{ $mobileFill.Height }}"
           loading="eager">
    </picture>
  </div>
  <div class="section-content hero-text">
    <h1 class="display-text">Falken's Mage</h1>
    {{ with .Params.tagline }}<p class="hero-tagline">{{ . }}</p>{{ end }}
  </div>
</section>
```

### Social Links Grid Partial
```html
{{/* themes/arcaeon/layouts/partials/sections/social.html */}}
<section class="section section-void">
  <div class="section-content">
    <div class="social-grid">
      {{ range .Params.social_links }}
      <a href="{{ .url }}"
         class="social-card glow-interactive"
         target="_blank"
         rel="noopener noreferrer"
         aria-label="{{ .name }}">
        <span class="social-card__icon" aria-hidden="true">
          {{/* inline SVG — use partial "icons/{{ .icon }}.html" pattern */}}
          {{ partial (printf "icons/%s.html" .icon) . }}
        </span>
        <span class="social-card__label">{{ .label }}</span>
      </a>
      {{ end }}
    </div>
  </div>
</section>
```

### CTA Button
```html
<a href="mailto:{{ .Params.cta_email }}" class="glow-radiant-core cta-button">
  Work With Me
</a>
```

### Footer with Dynamic Year and Lemniscate
```html
{{/* themes/arcaeon/layouts/partials/sections/footer.html */}}
<footer class="section section-depth footer-section">
  <div class="section-content footer-content">
    <p class="footer-closing">{{ .Params.footer_closing | default "Stay feral, folks." }}</p>
    <p class="footer-lemniscate" aria-hidden="true">&#x221E;</p>
    <p class="footer-copyright">&copy; {{ now.Year }} Digital Intuition LLC</p>
  </div>
</footer>
```

### Social Grid CSS
```css
/* Mobile: 2-column grid (D-05) */
.social-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

/* Tablet: 3 columns */
@media (min-width: 48rem) {
  .social-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

/* Desktop: 4 columns */
@media (min-width: 64rem) {
  .social-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

---

## Social Link URLs and Icon Sources

All 8 platform URLs confirmed from `SPEC.md`. [VERIFIED: SPEC.md content]

| Order | Platform | URL | SVG Source |
|-------|----------|-----|------------|
| 1 | Feral Architecture (Substack) | `https://feralarchitecture.substack.com` | Substack "S" letterform |
| 2 | LinkedIn | `https://linkedin.com/in/mattstine` | LinkedIn `in` square |
| 3 | X | `https://x.com/falkensmage` | X wordmark |
| 4 | Bluesky | `https://bsky.app/profile/falkensmage.bsky.social` | Bluesky butterfly |
| 5 | Instagram | `https://www.instagram.com/falkensmage` | Instagram camera square |
| 6 | Threads | `https://www.threads.com/@falkensmage` | Threads "@" stylized |
| 7 | Spotify | `https://open.spotify.com/album/6v081tJ7Gqe77Lja7LuiOd?si=OQyLl6EgTVCfrvC9cubIvA` | Spotify circle |
| 8 | TarotPulse | `https://my.tarotpulse.com` | Custom — lemniscate or card icon |

**SVG implementation approach:** All 8 SVG paths are well-known and should be authored inline per CONTEXT.md D-06. Use simple monochromatic paths (no `fill` attribute hardcoded — use `currentColor` so CSS hover can change icon color). Store each as a Hugo partial in `themes/arcaeon/layouts/partials/icons/[platform].html`. Call via `{{ partial "icons/substack.html" . }}`.

**Icon size:** `width="20" height="20"` with `viewBox` preserved. Scale via CSS `width: 1.25rem; height: 1.25rem;`.

---

## Image Processing: Crop Math Reference

Source: 1424x752 (landscape, 1.89:1 ratio). [VERIFIED: Python PIL read of actual source file]

| Context | Container | Hugo Method | Result |
|---------|-----------|-------------|--------|
| Mobile (375px viewport) | 375px wide × 290px tall | `.Fill "750x580 Center"` | 750x580 JPEG, center crop, 2x retina |
| Desktop (768px+) | full-width up to 1200px | `.Resize "1200x q85"` | 1200×634, natural aspect, no crop |
| WebP mobile | same | `.Process "webp"` on mobile fill | .webp variant, same dimensions |
| WebP desktop | same | `.Process "webp"` on desktop resize | .webp variant, same dimensions |

**Crop analysis:** At 375px wide with 290px height (ratio 1.29:1), `object-fit: cover` scales the 1424x752 source to 549×290 — clipping ~87px on each horizontal edge. The Magus figure is centered in the source, so center-crop preserves the subject. [VERIFIED: Python math against actual image dimensions]

---

## State of the Art

| Old Approach | Current Approach | Notes |
|--------------|------------------|-------|
| `$img.Format "webp"` | `$img.Process "webp"` | `.Format` does not exist on `images.ImageResource` in Hugo 0.160.1 |
| External build step for WebP | Hugo native `.Process "webp"` | Hugo 0.160+ handles this natively |
| `PostCSS` for CSS processing | `css.Build` native | No Node dependency, Phase 1 established |
| `resources.GetRemote` for RSS | Phase 3 scope | Not this phase |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `mailto:` links should not use `target="_blank"` | Common Pitfalls #6 | Low — standard HTML behavior. If wrong, worst case is email opens in browser tab rather than email client. |
| A2 | TarotPulse (`https://my.tarotpulse.com`) is the correct URL | Social Link URLs | Medium — if URL is wrong, a live link is broken. Matt should verify before ship. |
| A3 | Ghost card social style reads better than filled card against Void Purple | Architecture Patterns (D-08 discretion) | Low — purely aesthetic. Trivially changed in CSS. |
| A4 | Stacked desktop hero serves the 1424x752 image better than side-by-side | Architecture Patterns (D-04 discretion) | Low — purely aesthetic. Trivially changed. |

---

## Open Questions

1. **Hero tagline copy**
   - What we know: D-14 says full-voice placeholder, replaceable via front matter.
   - What's unclear: Matt hasn't written the real tagline yet. Placeholder needed now.
   - Recommendation: Use "Where enterprise architecture meets the technomagickal." as placeholder. Alive enough to evaluate the typography treatment. Replaceable in 30 seconds.

2. **Identity statement copy**
   - What we know: D-13 says full-voice placeholder in Matt's voice.
   - Direction from CONTEXT.md: "Enterprise architect. Tarot reader. Builder of systems that think. I hold paradox for a living — yours included."
   - Recommendation: Use this exactly as the placeholder — it's already voice-matched per the CONTEXT.md specifics section.

3. **TarotPulse URL confirmation**
   - What we know: SPEC.md lists `https://my.tarotpulse.com`
   - What's unclear: Whether this is the final intended URL or a development subdomain
   - Recommendation: Use as-is. Matt should verify in UAT.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Hugo Extended | Image processing, build | Yes | 0.160.1 | — |
| magus-hero.jpg in theme assets | HERO-01 image pipeline | Yes | 1424x752 | — |
| Cinzel Variable WOFF2 | HERO-02 display text | Yes | 5.2.8 | — |
| Space Grotesk Variable WOFF2 | Body text | Yes | 5.2.10 | — |

[VERIFIED: All confirmed via filesystem check and `hugo version`]

**Missing dependencies with no fallback:** None.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Shell script + Hugo build (established pattern from Phase 1) |
| Config file | `hugo.toml` |
| Quick run command | `bash tests/validate-phase-02.sh` |
| Full suite command | `bash tests/validate-phase-02.sh` + `bash tests/validate-phase-01.sh` (regression) + manual 375px browser check |
| Estimated runtime | ~10 seconds (Hugo build 9ms + checks) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| HERO-01 | `<picture>` element in built HTML; magus-hero image file in assets | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| HERO-02 | `.display-text` class applied to "Falken's Mage" h1 in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| HERO-03 | tagline element present in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| HERO-04 | `.glow-ambient` class in built HTML; `ambient-pulse` keyframe in CSS; `prefers-reduced-motion` in CSS | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| IDENT-01 | identity statement content present in built HTML (non-empty) | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| IDENT-02 | identity statement is front-matter driven (present in `_index.md`) | config | `bash tests/validate-phase-02.sh` | Wave 0 |
| SOCIAL-01 | `.social-grid` in built HTML; 8 social link `<a>` elements present | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| SOCIAL-02 | `.glow-interactive` class applied to social links in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| SOCIAL-03 | CSS `min-height: 44px` on `.social-card` | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| SOCIAL-04 | All 8 platform URLs present in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| SOCIAL-05 | `aria-label` attributes on all 8 social link `<a>` elements | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| CTA-01 | CTA description text present in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| CTA-02 | `href="mailto:falkensmage@falkenslabyrinth.com"` + `.glow-radiant-core` in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| FOOT-01 | "Stay feral, folks." text in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| FOOT-02 | "Digital Intuition LLC" + current year in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| FOOT-03 | `&#x221E;` (lemniscate) or `.footer-lemniscate` class in built HTML | smoke | `bash tests/validate-phase-02.sh` | Wave 0 |
| Visual | Magus image displays without distortion at 375px; glow pulse visible | manual | `hugo server` → 375px DevTools → visual confirm | — |
| SOCIAL-03 visual | Touch targets are visually 44px minimum at 375px | manual | DevTools computed styles on social cards | — |

### Sampling Rate
- **Per task commit:** `bash tests/validate-phase-02.sh`
- **Per wave merge:** `bash tests/validate-phase-02.sh && bash tests/validate-phase-01.sh` (regression)
- **Phase gate:** Both scripts green + manual visual pass before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/validate-phase-02.sh` — covers all 16 automated checks above
- [ ] `themes/arcaeon/layouts/partials/sections/` directory populated (4 files) — currently empty
- [ ] `themes/arcaeon/layouts/partials/icons/` directory — needs 8 SVG icon partials
- [ ] `content/_index.md` — needs social_links, tagline, identity_statement, cta params
- [ ] `themes/arcaeon/assets/css/main.css` — needs social grid, hero, footer CSS appended

`themes/arcaeon/assets/images/magus-hero.jpg` — **already present** (copied during research)

---

## Security Domain

This phase introduces no authentication, session management, access control, or cryptographic operations. The site is a static public page with no user input, no form submission, no server-side processing.

Applicable ASVS categories:

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | N/A — static site, no login |
| V3 Session Management | No | N/A — no session state |
| V4 Access Control | No | N/A — public content only |
| V5 Input Validation | No | N/A — no user input in Phase 2 |
| V6 Cryptography | No | N/A — no sensitive data |

**`rel="noopener noreferrer"` on external links:** Apply to all social link `<a target="_blank">` elements. This prevents the opened tab from accessing `window.opener` (cross-origin information leak). The `noreferrer` also suppresses the referrer header to external platforms. [ASSUMED — standard web security practice; spec: https://html.spec.whatwg.org/#link-type-noopener]

---

## Project Constraints (from CLAUDE.md)

| Directive | Impact on Phase 2 |
|-----------|-------------------|
| Hugo Extended only | Confirmed. `.Process "webp"` is Extended-only. [VERIFIED] |
| No external font CDNs | Fonts self-hosted. No Google Fonts. Phase 1 established. |
| No analytics, no external JS | No tracking snippets, no JS libraries for social cards. |
| Sub-1s 3G page load | WebP conversion + responsive sizing essential. No lazy-load on hero (above fold). Lazy-load applicable to nothing below-fold in Phase 2. |
| Mobile-first 375px | All CSS written mobile-first with breakpoints up. |
| WCAG AA minimum | `aria-label` on social links (SOCIAL-05). `alt` text on hero image. Electric Violet never used for body text (Phase 1 rule). |
| No `peaceiris/actions-hugo` | Not touched in Phase 2. |
| `themes/arcaeon/` portable theme | All new layouts under `themes/arcaeon/layouts/partials/sections/`. No root-level layout files. |
| GSD workflow enforcement | Phase executing via GSD. |

---

## Sources

### Primary (HIGH confidence)
- Live Hugo build tests — image processing methods (`.Fill`, `.Resize`, `.Process "webp"`), front matter access, data template patterns. Confirmed via build output in this session.
- Phase 1 codebase inspection — `themes/arcaeon/assets/css/main.css` (all glow classes, section classes, z-index values), `tests/validate-phase-01.sh` (test pattern), `layouts/kitchen-sink/single.html` (rendering patterns).
- `SPEC.md` — social link URLs (8 platforms), page structure, copy direction.
- `CONTEXT.md` — all locked decisions D-01 through D-15, code context (reusable assets), specifics.

### Secondary (MEDIUM confidence)
- Python PIL image dimension read — 1424x752 confirmed dimensions, RGB mode.
- CSS inspection for overflow/z-index interaction — reasoning from Phase 1 code, not a browser render test.

### Tertiary (LOW confidence)
- `mailto:` link `target="_blank"` anti-pattern — [ASSUMED], standard HTML specification behavior.
- `rel="noopener noreferrer"` security requirement on external links — [ASSUMED], standard web security practice.

---

## Metadata

**Confidence breakdown:**
- Hugo image processing pipeline: HIGH — verified with live build tests
- Content data patterns (front matter): HIGH — verified with live build test
- CSS patterns and class structure: HIGH — verified via Phase 1 code inspection
- Social platform URLs: HIGH for all except TarotPulse (MEDIUM — assumed subdomain is final)
- Security/rel attributes: LOW — standard practice, not formally verified

**Research date:** 2026-04-16
**Valid until:** 2026-07-16 (Hugo APIs are stable; 90-day horizon reasonable for a pinned 0.160.1 version)
