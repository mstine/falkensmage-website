# Phase 1: Theme Foundation - Research

**Researched:** 2026-04-16
**Domain:** Hugo Extended custom theme — ARCÆON CSS design system, self-hosted variable fonts, GPU-composited glow animations, dark graphic novel aesthetic
**Confidence:** HIGH (Hugo core, css.Build, font packages verified via npm registry and official docs; CSS animation patterns verified via MDN; WCAG contrast ratios computed directly)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**CSS Architecture:**
- D-01: Tiered token naming — palette truth vars (`--arcaeon-primary-violet`, etc.) with semantic aliases (`--color-bg`, `--color-text`, `--color-accent`). Two levels: palette truth + usage intent.
- D-02: Triad Rule enforced via section-level CSS overrides — each section partial gets scoped `--section-purple`, `--section-blue`, `--section-warm` vars that override root defaults. Convention lives in partial structure.
- D-03: Single `main.css` file with clearly commented sections (Tokens, Reset, Typography, Glow System, Layout, Components). No modular imports — one file, bundled and minified by Hugo `css.Build`.

**Typography Scale:**
- D-04: Minor Third (1.2 ratio) type scale — body 1rem (16px), h3 ~1.44rem, h2 ~1.728rem, h1 ~2.074rem. Display treatment at `clamp(2.5rem, 8vw, 4rem)` — outside the scale.
- D-05: Cinzel Variable for display treatment and all headings (h1-h3). Space Grotesk Variable for everything else. Clear boundary: heading = Cinzel, not-heading = Space Grotesk.
- D-06: Bold Cinzel weight progression — display 800, h1 700, h2 600, h3 500.

**Glow Treatment System:**
- D-07: Three distinct glow variants — ambient pulse (hero), interactive glow (hover/focus), Radiant Core (CTA button, Fusion Gold → Ignition Orange).
- D-08: All glow effects use `::before` pseudo-element + `opacity` pattern (GPU-composited). No `box-shadow`.
- D-09: Ambient pulse color: Electric Violet (#7a2cff).
- D-10: Ambient pulse timing: 4-6 second cycle, slow breath, barely-there.

**Dark Aesthetic Direction:**
- D-11: Alternating depth backgrounds per section — Void Purple and Deep Indigo alternate. Midnight Blue for gradient transitions between sections.
- D-12: Sigil grammar as CSS-only decorative shapes — broken geometric circles via `border-radius` on pseudo-elements with partial borders, rotated. No SVG files. Low opacity (~0.3).
- D-13: Kitchen sink demo page in Phase 1 — renders all tokens, type scale, glow treatments, sigil elements. Removed/hidden after Phase 2.

### Claude's Discretion
- Exact opacity values for sigil elements (started at 0.3, tunable)
- Precise gradient transition heights between sections
- Demo page format (content page vs. partial — whichever is simpler)
- Space Grotesk weight choices for body/UI (variable font, Claude picks what reads best)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| THEME-01 | ARCÆON palette implemented as CSS custom properties with all color tiers | CSS custom property architecture documented; tiered token naming locked (D-01); contrast ratios computed and verified |
| THEME-02 | Typographic hierarchy with self-hosted variable fonts (Cinzel headings, Space Grotesk body) | Font packages verified at npm registry (5.2.8 / 5.2.10); `@font-face` + `font-display: swap` pattern documented; preload pattern for FOIT prevention |
| THEME-03 | Glow treatment system — GPU-composited `::before` pseudo-element + opacity pattern | `::before` + `opacity` pattern documented with code examples; GPU compositing rationale verified via MDN; three variants (ambient/interactive/Radiant Core) all use same base pattern |
| THEME-04 | Dark graphic novel aesthetic — deep backgrounds, directional light via gradients, painted shadow shapes | ARCÆON palette contrast ratios verified; background alternation pattern (Void Purple / Deep Indigo) documented; Triad Rule enforcement via section vars |
| THEME-05 | Mobile-first responsive foundation — 375px viewport first | CSS architecture supports this; `clamp()` for type scale confirmed; breakpoint strategy documented |
| THEME-06 | Sigil grammar decorative elements — broken geometric circles, void-to-glow gradients | CSS-only sigil implementation approach documented; no SVG needed; pseudo-element border-radius technique confirmed |
| THEME-07 | Portable Hugo theme architecture (`themes/arcaeon/`) — not root-level layouts | Hugo theme directory structure documented; `baseof.html` + partials pattern; portable as git submodule for future Digital Intuition properties |
| INFRA-01 | Hugo project initialized with custom `arcaeon` theme under `themes/arcaeon/` | `hugo new site` + theme setup sequence documented; directory structure canonical |
| INFRA-02 | `hugo.toml` configured with `baseURL`, ARCÆON palette values, Hugo cache settings | `hugo.toml` configuration patterns documented; `baseURL = "https://falkensmage.com/"` confirmed as day-one value; cache config for Phase 3 RSS |
</phase_requirements>

---

## Summary

This phase establishes the ARCÆON design system as Hugo infrastructure. Everything in Phase 2 (visible sections) and beyond inherits from what gets built here — so the token architecture, glow pattern, and font loading strategy must be correct from the start. Retrofitting is significantly more expensive than building right the first time.

The primary technical work is: Hugo project initialization with the `arcaeon` theme directory, a single `main.css` with the full ARCÆON token system (palette truth vars + semantic aliases), `@font-face` declarations for Cinzel and Space Grotesk with `font-display: swap`, the three-variant glow system using `::before` + `opacity`, and a kitchen sink demo page that validates all of it visually.

The prior research in `.planning/research/` (STACK.md, ARCHITECTURE.md, PITFALLS.md, FEATURES.md) is comprehensive and already verified against official sources. This RESEARCH.md synthesizes it with the locked decisions from CONTEXT.md and adds phase-specific guidance the planner needs.

**Primary recommendation:** Build `_tokens.css` (or the equivalent commented section in `main.css` per D-03) before any other CSS work. The token layer is load-bearing for everything else — section layout, typography, and glow treatments all reference it. The kitchen sink demo page is the correctness gate before Phase 2.

---

## Project Constraints (from CLAUDE.md)

| Directive | Category | Enforcement |
|-----------|----------|-------------|
| Hugo Extended 0.160.1 — Extended required for `css.Build` | Stack | Never use standard edition; verify `hugo version` shows "extended" |
| `css.Build` native CSS — no PostCSS | CSS pipeline | No Node build plugins; Hugo handles bundling + minification |
| `@fontsource-variable/cinzel` 5.2.8 + `@fontsource-variable/space-grotesk` 5.2.10 | Typography | Self-hosted WOFF2 from npm packages; no Google Fonts CDN |
| `themes/arcaeon/` portable theme — not root-level layouts | Architecture | ALL CSS/layouts/partials live under `themes/arcaeon/`; nothing in root `layouts/` |
| No Tailwind CSS | CSS | Native CSS custom properties + `css.Build` only |
| No GSAP / anime.js | Animation | Pure CSS `@keyframes` + `transform` + `opacity` |
| No analytics | Performance/privacy | Omit entirely; no Plausible/GA/Fathom |
| `baseURL = "https://falkensmage.com/"` | Hugo config | Set day one — never localhost |
| Sub-1s page load on 3G | Performance | Self-hosted fonts, no external CDNs, GPU-composited animations only |
| Mobile-first 375px | Responsive | Design 375px first, scale up via breakpoints |
| WCAG AA minimum | Accessibility | `prefers-reduced-motion`, semantic HTML5, color contrast |
| `peaceiris/actions-hugo` — avoid | CI/CD | Use direct binary install in workflow instead |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Hugo Extended | 0.160.1 | Static site generator + CSS pipeline | Prior experience; `css.Build` requires Extended; 0.160.x adds `@import "hugo:vars"` for palette injection |
| Hugo `css.Build` | built-in 0.160+ | CSS bundling + minification | Replaces PostCSS without Node dependency; handles the single `main.css` approach from D-03 |

### Typography
| Package | Version | Purpose | Notes |
|---------|---------|---------|-------|
| `@fontsource-variable/cinzel` | 5.2.8 | Display + headings (Cinzel Variable, weights 400-900) | [VERIFIED: npm registry] — Cinzel weights 400-900, Latin subset, WOFF2 |
| `@fontsource-variable/space-grotesk` | 5.2.10 | Body + UI text (Space Grotesk Variable, weights 300-700) | [VERIFIED: npm registry] — Space Grotesk weights 300-700, Latin subset, WOFF2 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `node` + `npm` | 24.4.1 (local) | Font file management | Copy WOFF2 files from npm packages to theme assets; not a runtime dependency |
| Hugo `resources.GetRemote` | built-in | Build-time RSS fetch | Phase 3 only — not needed in Phase 1 |

**Installation:**
```bash
# In project root — font management only
npm init -y
npm install @fontsource-variable/cinzel @fontsource-variable/space-grotesk

# Copy WOFF2 files to theme assets (Hugo Pipes fingerprints from assets/, not static/)
cp node_modules/@fontsource-variable/cinzel/files/cinzel-latin-*.woff2 themes/arcaeon/assets/fonts/
cp node_modules/@fontsource-variable/space-grotesk/files/space-grotesk-latin-*.woff2 themes/arcaeon/assets/fonts/

# Hugo — install via Homebrew (not installed locally yet)
brew install hugo
hugo version  # must show "extended" — standard edition will fail on css.Build
```

**Hugo installation note:** Hugo is NOT currently installed on this machine. [VERIFIED: brew info shows 0.160.1 available, not installed]. Installing via `brew install hugo` will get the current stable version. Verify it's Extended edition after install.

---

## Architecture Patterns

### Hugo Theme Directory Structure (THEME-07)

```
falkensmage-website/
├── hugo.toml                        # baseURL, theme: arcaeon, palette params, cache config
├── content/
│   └── _index.md                    # Front matter: title, tagline slot, current-focus
└── themes/
    └── arcaeon/
        ├── assets/
        │   ├── css/
        │   │   └── main.css         # Single file per D-03: Tokens | Reset | Typography | Glow System | Layout | Components
        │   └── fonts/
        │       ├── cinzel-latin-woff2-*.woff2
        │       └── space-grotesk-latin-*.woff2
        ├── layouts/
        │   ├── _default/
        │   │   └── baseof.html      # HTML shell: <head>, font preload, body wrapper
        │   ├── index.html           # Homepage: extends baseof, calls section partials
        │   └── partials/
        │       ├── head/
        │       │   └── meta.html    # OG, Twitter card, canonical (Phase 3 content)
        │       └── sections/
        │           └── kitchen-sink.html  # Phase 1 demo page — all tokens/glows/sigils
        └── static/
            └── robots.txt
```

**Phase 1 vs Phase 2 distinction:** Phase 1 establishes the theme skeleton and kitchen sink only. Section partials (hero, identity, social, etc.) are Phase 2 work. The theme structure is portable — all CSS, layouts, and partials live under `themes/arcaeon/`.

### Pattern 1: ARCÆON CSS Token Architecture (THEME-01, D-01, D-02, D-03)

**What:** Single `main.css` with two-tier custom property system. Palette truth vars define the raw colors; semantic aliases layer usage intent on top. Section partials override scoped section vars to enforce the Triad Rule.

**Tier 1 — Palette Truth:**
```css
/* Source: ARCÆON Color Palette canonical system (.psyche/swipe-files) */
/* Section: TOKENS — Palette Truth */

:root {
  /* Primary Identity */
  --arcaeon-electric-violet: #7a2cff;
  --arcaeon-neon-magenta: #ff3cac;
  --arcaeon-plasma-pink: #ff5fd2;
  --arcaeon-electric-blue: #2fd3ff;

  /* Focal Energy (Radiant Core) */
  --arcaeon-solar-white: #fff4e6;
  --arcaeon-fusion-gold: #ffb347;
  --arcaeon-ignition-orange: #ff7a18;

  /* Cosmic Depth */
  --arcaeon-deep-indigo: #0a0f3c;
  --arcaeon-midnight-blue: #111a6b;
  --arcaeon-void-purple: #1a0f2e;

  /* Energy Accents */
  --arcaeon-electric-blue-alt: #2fd3ff;
  --arcaeon-ion-glow: #5be7ff;
}
```

**Tier 2 — Semantic Aliases:**
```css
/* Section: TOKENS — Semantic Aliases */

:root {
  --color-bg: var(--arcaeon-void-purple);
  --color-bg-alt: var(--arcaeon-deep-indigo);
  --color-bg-transition: var(--arcaeon-midnight-blue);
  --color-text: var(--arcaeon-solar-white);
  --color-text-accent: var(--arcaeon-ion-glow);
  --color-accent: var(--arcaeon-electric-violet);
  --color-accent-warm: var(--arcaeon-fusion-gold);
  --color-hover: var(--arcaeon-neon-magenta);
  --color-cta-start: var(--arcaeon-fusion-gold);
  --color-cta-end: var(--arcaeon-ignition-orange);
}
```

**Triad Rule enforcement per section (D-02):**
```css
/* Each section partial's scoped vars — override root defaults */
/* Purple variant section */
.section-void {
  --section-purple: var(--arcaeon-void-purple);
  --section-blue: var(--arcaeon-electric-blue);
  --section-warm: var(--arcaeon-fusion-gold);
  background: var(--section-purple);
}

/* Indigo variant section */
.section-depth {
  --section-purple: var(--arcaeon-deep-indigo);
  --section-blue: var(--arcaeon-ion-glow);
  --section-warm: var(--arcaeon-ignition-orange);
  background: var(--section-purple);
}
```

### Pattern 2: Typography Scale (THEME-02, D-04, D-05, D-06)

**What:** Minor Third (1.2) scale, Cinzel Variable for headings, Space Grotesk Variable for body/UI, bold weight progression.

**`@font-face` declarations:**
```css
/* Section: TYPOGRAPHY — Font Face Declarations */

/* Cinzel Variable — display + headings */
@font-face {
  font-family: 'Cinzel Variable';
  src: url('fonts/cinzel-latin-variable-woff2.woff2') format('woff2');
  font-weight: 400 900;
  font-style: normal;
  font-display: swap;
}

/* Space Grotesk Variable — body + UI */
@font-face {
  font-family: 'Space Grotesk Variable';
  src: url('fonts/space-grotesk-latin-variable-woff2.woff2') format('woff2');
  font-weight: 300 700;
  font-style: normal;
  font-display: swap;
}
```

**Type scale (Minor Third, 1.2 ratio, D-04):**
```css
/* Section: TYPOGRAPHY — Type Scale */

:root {
  --font-display: 'Cinzel Variable', 'Times New Roman', serif;
  --font-heading: 'Cinzel Variable', 'Times New Roman', serif;
  --font-body: 'Space Grotesk Variable', system-ui, sans-serif;

  /* Minor Third scale — base 1rem (16px) */
  --text-base: 1rem;          /* 16px — body */
  --text-h3: 1.44rem;         /* ~23px — h3 */
  --text-h2: 1.728rem;        /* ~28px — h2 */
  --text-h1: 2.074rem;        /* ~33px — h1 */
  --text-display: clamp(2.5rem, 8vw, 4rem);  /* display — outside scale per D-04 */

  /* Cinzel weight progression (D-06) */
  --weight-display: 800;
  --weight-h1: 700;
  --weight-h2: 600;
  --weight-h3: 500;
}
```

**baseof.html font preload (FOIT prevention):**
```html
<!-- Source: Hugo docs — font preload pattern -->
{{ $font := resources.Get "fonts/cinzel-latin-variable-woff2.woff2" | fingerprint }}
<link rel="preload" href="{{ $font.RelPermalink }}" as="font" type="font/woff2" crossorigin>
```

**Critical:** `crossorigin` attribute is required even for same-origin fonts — without it, the browser downloads the font twice (preload cache miss).

### Pattern 3: Glow System (THEME-03, D-07, D-08, D-09, D-10)

**What:** Three glow variants, all using `::before` pseudo-element + `opacity` transition. No `box-shadow` anywhere.

**Why `::before` + `opacity`:** Animating `box-shadow` triggers paint on every frame — GPU cannot composite it. Animating `opacity` on a promoted layer runs on the compositor thread with zero main thread cost. [VERIFIED: MDN CSS performance, will-change]

**Ambient Pulse — hero image breathing glow (D-07, D-09, D-10):**
```css
/* Section: GLOW SYSTEM — Ambient Pulse */

.glow-ambient {
  position: relative;
}

.glow-ambient::before {
  content: '';
  position: absolute;
  inset: -20%;
  background: radial-gradient(
    circle,
    var(--arcaeon-electric-violet) 0%,
    transparent 70%
  );
  opacity: 0.4;
  animation: ambient-pulse 5s ease-in-out infinite;
  pointer-events: none;
  will-change: opacity;
}

@keyframes ambient-pulse {
  0%, 100% { opacity: 0.2; }
  50%       { opacity: 0.5; }
}

@media (prefers-reduced-motion: reduce) {
  .glow-ambient::before {
    animation: none;
    opacity: 0.3; /* Static glow — present but not moving */
  }
}
```

**Interactive Glow — hover/focus on links and social cards (D-07):**
```css
/* Section: GLOW SYSTEM — Interactive Glow */

.glow-interactive {
  position: relative;
}

.glow-interactive::before {
  content: '';
  position: absolute;
  inset: -4px;
  background: radial-gradient(
    circle,
    var(--arcaeon-electric-violet) 0%,
    transparent 70%
  );
  opacity: 0;
  transition: opacity 0.25s ease;
  pointer-events: none;
  will-change: opacity;
}

.glow-interactive:hover::before,
.glow-interactive:focus-visible::before {
  opacity: 0.6;
}

@media (prefers-reduced-motion: reduce) {
  .glow-interactive::before {
    transition: none;
  }
}
```

**Radiant Core — CTA button (Fusion Gold → Ignition Orange gradient, D-07):**
```css
/* Section: GLOW SYSTEM — Radiant Core CTA */

.glow-radiant-core {
  position: relative;
  background: linear-gradient(
    135deg,
    var(--arcaeon-fusion-gold) 0%,
    var(--arcaeon-ignition-orange) 100%
  );
  color: var(--arcaeon-void-purple); /* Dark text on warm background — high contrast */
}

.glow-radiant-core::before {
  content: '';
  position: absolute;
  inset: -8px;
  background: radial-gradient(
    circle,
    var(--arcaeon-fusion-gold) 0%,
    transparent 70%
  );
  opacity: 0;
  transition: opacity 0.3s ease;
  pointer-events: none;
  border-radius: inherit;
  will-change: opacity;
}

.glow-radiant-core:hover::before,
.glow-radiant-core:focus-visible::before {
  opacity: 0.7;
}
```

### Pattern 4: CSS-Only Sigil Grammar (THEME-06, D-12)

**What:** Broken geometric circles and arc fragments using `border-radius` + partial `border` declarations on pseudo-elements. CSS-only — no SVG files.

```css
/* Section: COMPONENTS — Sigil Grammar */

.sigil-arc {
  position: relative;
}

.sigil-arc::after {
  content: '';
  position: absolute;
  width: 80px;
  height: 80px;
  border-radius: 50%;
  border: 1px solid var(--arcaeon-electric-violet);
  /* Partial border — break the circle using transparent segments */
  border-top-color: transparent;
  border-right-color: transparent;
  opacity: 0.3;    /* Claude's discretion — tunable */
  transform: rotate(-45deg);
  pointer-events: none;
}

/* Variant — smaller, rotated differently for visual variety */
.sigil-arc-sm::before {
  content: '';
  position: absolute;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid var(--arcaeon-neon-magenta);
  border-bottom-color: transparent;
  border-left-color: transparent;
  opacity: 0.2;
  transform: rotate(30deg);
  pointer-events: none;
}
```

### Pattern 5: hugo.toml Configuration (INFRA-02)

```toml
baseURL = "https://falkensmage.com/"
languageCode = "en-us"
title = "Falken's Mage"
theme = "arcaeon"

[params]
  author = "Matt Stine"
  description = "Falken's Mage — Matt Stine"

[params.colors]
  electricViolet = "#7a2cff"
  neonMagenta = "#ff3cac"
  plasmaPink = "#ff5fd2"
  electricBlue = "#2fd3ff"
  solarWhite = "#fff4e6"
  fusionGold = "#ffb347"
  ignitionOrange = "#ff7a18"
  deepIndigo = "#0a0f3c"
  midnightBlue = "#111a6b"
  voidPurple = "#1a0f2e"
  ionGlow = "#5be7ff"

# Cache config — Phase 3 RSS fetch will use this
[caches]
  [caches.getresource]
    dir = ":cacheDir/:project"
    maxAge = "1h"
```

### Pattern 6: Kitchen Sink Demo Page (D-13)

**What:** A content page (simpler than a partial) that renders all tokens, type scale, glow treatments, and sigils for visual validation.

**Implementation:** Create `content/kitchen-sink.md` with `draft: true` and a corresponding layout in `themes/arcaeon/layouts/kitchen-sink/single.html`. Run with `hugo server --buildDrafts` to view. Mark as draft — it won't deploy to production but remains available locally for Phase 2 validation.

**Format choice (Claude's discretion from D-13):** Content page with draft:true is simpler than a partial — requires no layout plumbing to render in isolation, and `--buildDrafts` flag keeps it completely out of production builds.

### Anti-Patterns to Avoid

- **`box-shadow` transitions:** Always the first instinct for glow effects. Always wrong on mobile. Use `::before` + `opacity` from the first implementation.
- **Fonts in `static/` instead of `assets/`:** `static/` gets no Hugo Pipes processing — no fingerprinting = no cache-busting. Fonts belong in `assets/fonts/`.
- **Missing `crossorigin` on font preload:** Causes double download. Include it even though the font is same-origin.
- **Hardcoded hex values in templates or section CSS:** All color references must go through custom properties. Never write a hex value outside of `_tokens` section.
- **`baseURL = "http://localhost:1313/"`:** Set production URL from day one. Never commit a localhost baseURL.
- **Root-level layouts:** Everything lives under `themes/arcaeon/`. The theme is the brand — portable and self-contained.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| CSS bundling and minification | Custom build scripts | Hugo `css.Build` | Native to Hugo 0.160+; no Node pipeline needed |
| Font file fingerprinting / cache-busting | Manual hash in filename | `resources.Get` + `fingerprint` in Hugo Pipes | Automatic, consistent, survives file content changes |
| Color token management | Global find-replace | CSS custom properties | Single source of truth; cascade handles inheritance |
| Glow effects | `box-shadow` animations | `::before` + `opacity` pattern | GPU compositing — the only approach that works on mobile |
| Font subsetting | Custom Python scripts | Fontsource packages (already Latin-subset) | Fontsource WOFF2 files are already subset; no extra tooling |

---

## WCAG Contrast Reference

Computed directly [VERIFIED: Python WCAG luminance formula]. Phase 1 must honor these — typography token defaults must use passing combinations only.

| Color Pair | Ratio | WCAG Status | Use For |
|------------|-------|-------------|---------|
| Solar White (#fff4e6) on Void Purple (#1a0f2e) | 16.79:1 | PASS AA | Body text — primary |
| Solar White (#fff4e6) on Deep Indigo (#0a0f3c) | 16.86:1 | PASS AA | Body text — alternate sections |
| Ion Glow (#5be7ff) on Void Purple (#1a0f2e) | 12.43:1 | PASS AA | Accent text, links |
| Ion Glow (#5be7ff) on Deep Indigo (#0a0f3c) | 12.49:1 | PASS AA | Accent text — alternate sections |
| Electric Blue (#2fd3ff) on Void Purple (#1a0f2e) | 10.32:1 | PASS AA | Accent text |
| Fusion Gold (#ffb347) on Void Purple (#1a0f2e) | 10.24:1 | PASS AA | CTA warm accent |
| Fusion Gold (#ffb347) on Deep Indigo (#0a0f3c) | 10.28:1 | PASS AA | CTA warm accent |
| Neon Magenta (#ff3cac) on Void Purple (#1a0f2e) | 5.64:1 | PASS AA | Hover states, accent (not body text) |
| Electric Violet (#7a2cff) on Void Purple (#1a0f2e) | 3.15:1 | FAIL AA body / PASS large text+UI | Decorative only, glows, borders — NEVER body text |
| Electric Violet (#7a2cff) on Deep Indigo (#0a0f3c) | 3.17:1 | FAIL AA body / PASS large text+UI | Decorative only — NEVER body text |

**Key constraint:** Electric Violet fails WCAG AA for body text on both primary backgrounds. It is decoration-only (glows, borders, sigils). This is expected and by design — the pitfalls research flagged this, and the ARCÆON palette's usage hierarchy already correctly assigns violet to branding/glow, not body copy.

---

## Common Pitfalls

### Pitfall 1: `box-shadow` for Glow Effects (Phase 1 critical)
**What goes wrong:** Animated `box-shadow` triggers paint on every frame — no GPU compositing. Stutters on mid-range mobile, drains battery.
**How to avoid:** `::before` + `opacity` pattern only. Every glow variant in Phase 1 must use this approach from first implementation.
**Warning signs:** Any `transition: box-shadow` in CSS. Chrome DevTools showing paint rectangles on hover.

### Pitfall 2: Font Double-Download (Phase 1 critical)
**What goes wrong:** `<link rel="preload">` without `crossorigin` attribute causes the browser to download the font twice — once for the preload, once for the CSS-triggered fetch (preload cache miss).
**How to avoid:** Always include `crossorigin` on font preload links, even for same-origin fonts. Verify in DevTools Network tab — font should appear once.

### Pitfall 3: Fonts in `static/` (Phase 1 critical)
**What goes wrong:** Files in `static/` are copied as-is — no Hugo Pipes, no fingerprinting. Font updates don't bust cache.
**How to avoid:** Font WOFF2 files go in `themes/arcaeon/assets/fonts/`. Reference via `resources.Get` + `fingerprint`.

### Pitfall 4: `baseURL` Set to Localhost
**What goes wrong:** Every asset path on the deployed site returns 404.
**How to avoid:** Set `baseURL = "https://falkensmage.com/"` in `hugo.toml` from day one. `hugo server` overrides this for local dev automatically.

### Pitfall 5: Electric Violet as Body Text
**What goes wrong:** #7a2cff achieves only 3.15:1 contrast on Void Purple — fails WCAG AA for normal text (requires 4.5:1).
**How to avoid:** Electric Violet is for glows, borders, and decorative elements only. Body and accent text must use Solar White or Ion Glow. Document the restriction in a CSS comment in the tokens section.

### Pitfall 6: Missing `prefers-reduced-motion` on Ambient Pulse
**What goes wrong:** Ambient hero animation violates WCAG 2.1 SC 2.3.3 for vestibular disorder users.
**How to avoid:** Every `animation:` and `transition:` declaration ships with a corresponding `@media (prefers-reduced-motion: reduce)` block. Build it alongside the animation, not as a later pass.

---

## Environment Availability

| Dependency | Required By | Available | Version | Action |
|------------|------------|-----------|---------|--------|
| Hugo Extended | All Phase 1 work | NOT INSTALLED | 0.160.1 available via brew | `brew install hugo` — Wave 0 task |
| Node.js | Font file management | YES | 24.4.1 | Ready to use |
| npm | Font package install | YES | 11.4.2 | Ready to use |
| git | Version control | YES | 2.50.1 | Ready |
| `@fontsource-variable/cinzel` | Typography | YES (npm registry) | 5.2.8 | `npm install` — Wave 0 task |
| `@fontsource-variable/space-grotesk` | Typography | YES (npm registry) | 5.2.10 | `npm install` — Wave 0 task |

**Missing dependencies blocking execution:**
- Hugo Extended 0.160.1 — must be installed before any `hugo` commands. Install: `brew install hugo`. Verify with `hugo version` — must show "extended".

**Missing dependencies with fallback:**
- None.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | Hugo build validation + browser DevTools manual inspection |
| Config file | `hugo.toml` |
| Quick run command | `hugo server --buildDrafts` |
| Full validation | `hugo --minify` (no build errors) + browser DevTools inspection of kitchen sink page |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | Exists? |
|--------|----------|-----------|-------------------|---------|
| THEME-01 | ARCÆON CSS custom properties resolve in browser | Manual — DevTools | `hugo server` → DevTools → `:root` custom properties visible | No — Wave 0 creates kitchen sink |
| THEME-02 | Cinzel + Space Grotesk render from self-hosted files, no FOIT | Manual — Network tab | `hugo server` → Network tab shows fonts loading once, `font-display: swap` in CSS | No — Wave 0 creates kitchen sink |
| THEME-03 | Glow button and ambient pulse render without `box-shadow` | Manual — DevTools + Performance | `hugo server` → kitchen sink → hover glow → no paint rectangles | No — Wave 0 creates kitchen sink |
| THEME-04 | Dark backgrounds alternate, Triad Rule color combos visible | Visual — kitchen sink | `hugo server` → kitchen sink page | No — Wave 0 creates kitchen sink |
| THEME-05 | 375px viewport shows no horizontal scroll | Manual — DevTools device toolbar | `hugo server` → DevTools → 375px → check overflow | No — Wave 0 creates kitchen sink |
| THEME-06 | Sigil arc shapes render at correct opacity without SVG | Visual — kitchen sink | `hugo server` → kitchen sink page | No — Wave 0 creates kitchen sink |
| THEME-07 | `themes/arcaeon/` structure is a portable Hugo theme | Build — `hugo` command | `hugo` — must build without errors; no root-level `layouts/` | No — Wave 0 creates directory |
| INFRA-01 | `hugo server` renders without errors | Build | `hugo server --buildDrafts 2>&1 \| grep -i error` | No — Wave 0 initializes project |
| INFRA-02 | `hugo.toml` has correct baseURL and palette params | Config inspection | `grep baseURL hugo.toml` | No — Wave 0 creates config |

### Sampling Rate
- **Per task commit:** `hugo server --buildDrafts` — confirms clean build, no template errors
- **Per wave merge:** `hugo --minify` — confirms production build succeeds; visual inspection of kitchen sink at 375px
- **Phase gate:** Kitchen sink page visually validates all five success criteria before Phase 2 begins

### Wave 0 Gaps
- [ ] `brew install hugo` — Hugo Extended not installed
- [ ] `hugo new site falkensmage-website` — project not initialized yet (only `.planning/` and `CLAUDE.md` exist)
- [ ] `npm init -y` + `npm install @fontsource-variable/cinzel @fontsource-variable/space-grotesk` — no `package.json` exists
- [ ] `themes/arcaeon/` directory structure — theme does not exist yet
- [ ] `themes/arcaeon/assets/css/main.css` — main stylesheet
- [ ] `themes/arcaeon/layouts/_default/baseof.html` — base template
- [ ] `themes/arcaeon/layouts/index.html` — homepage template
- [ ] `content/kitchen-sink.md` — demo content page (draft: true)

---

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Static site — no auth |
| V3 Session Management | No | No user sessions |
| V4 Access Control | No | Public static site |
| V5 Input Validation | No | No user input in Phase 1 |
| V6 Cryptography | No | No secrets handled |
| V7 Error Handling | Minimal | Hugo build errors logged, not exposed to users |

**Phase 1 security surface:** Essentially zero. This is a static file generation phase — no user input, no authentication, no secrets. The only security-adjacent consideration is ensuring the `baseURL` is HTTPS from day one (`https://falkensmage.com/`), which also prevents mixed-content warnings in Phase 4.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `data.GetJSON` for RSS | `resources.GetRemote \| transform.Unmarshal` | Hugo 0.123 (deprecated) / 0.140 (removed) | Old tutorials still show `data.GetJSON` — do not use it |
| `peaceiris/actions-hugo` action | Direct Hugo binary install in workflow | Ongoing preference shift | Third-party action adds dependency; direct install is simpler |
| PostCSS pipeline for Hugo | Hugo `css.Build` native | Hugo 0.80+ | Hugo 0.160's `@import "hugo:vars"` eliminates last reason to use PostCSS |
| Fonts in `static/` | Fonts in `assets/` + Hugo Pipes fingerprinting | Hugo Pipes stable | Cache-busting requires `assets/` path |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Cinzel Variable font files follow naming pattern `cinzel-latin-*.woff2` after npm install | Standard Stack / Installation | Wrong copy command — would need to inspect actual filenames in `node_modules/@fontsource-variable/cinzel/files/` before copying |
| A2 | `brew install hugo` installs the Extended edition (not standard) | Environment Availability | Standard edition would fail on `css.Build`; would need to install from GitHub releases directly |
| A3 | Space Grotesk Variable weight 350-400 reads well for body text at 16px on dark backgrounds | Typography Scale | Aesthetic judgment — validate visually in kitchen sink before locking weight choices |

---

## Open Questions (RESOLVED)

1. **Cinzel Variable file naming pattern**
   - What we know: Fontsource packages store WOFF2 files under `files/` subdirectory; pattern varies by package
   - What's unclear: Exact filenames for Cinzel and Space Grotesk variable WOFF2 files
   - Recommendation: `ls node_modules/@fontsource-variable/cinzel/files/` after `npm install` before writing copy commands

2. **Space Grotesk body weight selection**
   - What we know: Variable range is 300-700; Claude has discretion per D-05
   - What's unclear: Which specific weights (300? 400? 450?) read best for body text at 16px on dark backgrounds
   - Recommendation: Default to 400 for body, 500 for UI labels, 600 for CTAs — validate in kitchen sink

3. **Kitchen sink page as content page vs. partial (D-13)**
   - Resolution: Content page with `draft: true` is the simpler approach — no extra layout plumbing, stays out of production automatically with `hugo --minify` (drafts excluded by default)

---

## Sources

### Primary (HIGH confidence)
- [VERIFIED: npm registry] — `@fontsource-variable/cinzel` v5.2.8, `@fontsource-variable/space-grotesk` v5.2.10 — confirmed current as of research date
- [VERIFIED: Python WCAG luminance formula] — Contrast ratios computed directly from ARCÆON hex values in this session
- [VERIFIED: Homebrew] — Hugo 0.160.1 available via `brew install hugo`, not currently installed on machine
- [CITED: gohugo.io/content-management/image-processing/] — Hugo Pipes fingerprint + assets/ pattern
- [CITED: gohugo.io/functions/resources/getremote/] — `resources.GetRemote` + `transform.Unmarshal` pattern
- [CITED: developer.mozilla.org/en-US/docs/Web/CSS/will-change] — GPU compositing via `opacity` + `will-change`
- [CITED: developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-reduced-motion] — reduced motion implementation

### Secondary (MEDIUM confidence)
- `.planning/research/STACK.md` — Prior project research, sourced from official Hugo docs + npm registry (HIGH confidence findings)
- `.planning/research/ARCHITECTURE.md` — Prior project research, Hugo official docs patterns
- `.planning/research/PITFALLS.md` — Prior project research, verified against Hugo discourse + MDN + W3C
- `.planning/research/FEATURES.md` — Prior project research, feature landscape analysis

### Canonical project sources
- `~/.psyche/swipe-files/podcasting-creative/2026-04-16-12-33-18-arc-on-color-palette-full.md` — ARCÆON full palette (all hex values)
- `~/Documents/Business-Brand/Feral-Architecture/covers/TEMPLATE.md` — Feral Architecture aesthetic contract (dark graphic novel visual language)
- `/Users/falkensmage/RitualSync/falkensmage-website/SPEC.md` — Site specification (hex values, usage hierarchy)
- `/Users/falkensmage/RitualSync/falkensmage-website/CLAUDE.md` — Technology stack decisions, constraints

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Hugo 0.160.1 + fontsource packages verified at registry; both confirmed current
- Architecture: HIGH — prior research verified against official Hugo docs; decisions locked in CONTEXT.md
- WCAG contrast ratios: HIGH — computed directly from hex values using WCAG luminance formula
- Pitfalls: HIGH — prior research sourced from Hugo discourse + MDN + W3C
- Sigil CSS implementation: MEDIUM — CSS approach is sound but exact visual output needs kitchen sink validation

**Research date:** 2026-04-16
**Valid until:** 2026-07-16 (Hugo 0.160.x is stable; fontsource packages update regularly but WOFF2 format is stable — re-verify package versions before install)
