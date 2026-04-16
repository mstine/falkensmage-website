# Phase 2: Static Content - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

All visible sections rendered, styled, and mobile-first — hero through footer. A stranger lands on falkensmage.com and understands who this person is and can reach every platform. Four sections: Hero, Identity+CTA, Social Links, Footer.

</domain>

<decisions>
## Implementation Decisions

### Hero Composition
- **D-01:** Image above, text below on mobile (375px). Magus image full-width at top, "Falken's Mage" logotype + tagline stacked below. Clean separation.
- **D-02:** Mobile image crop via `object-fit: cover` with a taller container (~280-300px) to center-crop the 1424x752 source into approximately 4:3. Loses edges but gives visual weight. Hugo `<picture>` with art direction handles responsive variants.
- **D-03:** Ambient glow pulse (`.glow-ambient`) wraps the hero image container — Electric Violet bleeds out from behind the Magus. Image is the focal point.
- **D-04:** Desktop hero layout is Claude's discretion — stacked or side-by-side, whichever works best with the 1424x752 source dimensions.

### Social Links Layout
- **D-05:** 2-column grid on mobile (4 rows × 2 links). Scales to 3-4 columns on tablet/desktop. Each cell: icon + label.
- **D-06:** Inline SVG icons embedded directly in the Hugo social links partial. Zero HTTP requests, fully CSS-styleable for hover color changes. 8 hand-curated SVG paths.
- **D-07:** Feral Architecture (Substack) in the top-left position (most prominent). Claude arranges remaining 7 platforms for visual/logical flow.
- **D-08:** Social link card style is Claude's discretion — filled card with glow hover or ghost card (border only), whichever reads best against the section background. Must use `.glow-interactive` for hover treatment.

### Section Flow & Triad Assignments
- **D-09:** Four sections top-to-bottom: Hero → Identity+CTA (combined) → Social Links → Footer. Identity statement flows directly into the "Work With Me" CTA within a single section.
- **D-10:** Triad alternation: Hero = `.section-void` (Void Purple), Identity+CTA = `.section-depth` (Deep Indigo), Social = `.section-void`, Footer = `.section-depth`. Gradient transitions between each per Phase 1 D-11.
- **D-11:** Sigil decorative elements placed at section boundaries only (where gradient transitions happen). Not within section content areas.

### Identity & Copy Tone
- **D-12:** Identity statement lives inside the Identity+CTA section (Deep Indigo background), not in the hero. Hero is visual impact; Identity+CTA is verbal identity flowing into action.
- **D-13:** Full-voice placeholder copy for the identity statement — written in Matt's voice (first person, direct, alive, irreverent). Close enough to ship temporarily. Replaceable via `content/_index.md` front matter.
- **D-14:** Full-voice placeholder for the hero tagline slot as well — a line that carries the right energy so the typography treatment can be evaluated with real-ish text. Replaceable via front matter.
- **D-15:** CTA copy is brief and general: "Coaching. Speaking. Collaboration." + single mailto button (`falkensmage@falkenslabyrinth.com`). Keeps it open since ICP is still being refined.

### Claude's Discretion
- Desktop hero layout (stacked vs side-by-side) — D-04
- Social link card style (filled vs ghost) — D-08
- Social link platform ordering after Feral Architecture — D-07
- Sigil arc sizes and rotation angles at section boundaries — D-11
- Exact image container height for mobile crop (280-300px range) — D-02

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ARCAEON Color System
- `~/.psyche/swipe-files/podcasting-creative/2026-04-16-12-33-18-arc-on-color-palette-full.md` — Full ARCAEON palette with Triad Rule enforcement
- Phase 1 established: `--section-purple`, `--section-blue`, `--section-warm` override pattern per section

### Visual Aesthetic
- `~/Documents/Business-Brand/Feral-Architecture/covers/TEMPLATE.md` — Feral Architecture aesthetic contract (dark graphic novel language)

### Hero Image Source
- `~/Documents/Business-Brand/Feral-Architecture/covers/2026-04-14-aesthetic-decisions/final/aesthetic-decisions-cover.jpg` — 1424x752 source image, needs center-crop for mobile

### Voice & Copy
- `~/.psyche/identity/voice.md` — Matt's voice characteristics for placeholder copy
- `~/.psyche/identity/voice-samples.md` — Calibration material for voice-matching placeholder text

### Project Requirements
- `.planning/REQUIREMENTS.md` §Hero Section — HERO-01 through HERO-04 acceptance criteria
- `.planning/REQUIREMENTS.md` §Identity Statement — IDENT-01, IDENT-02 acceptance criteria
- `.planning/REQUIREMENTS.md` §Social Links — SOCIAL-01 through SOCIAL-05 acceptance criteria
- `.planning/REQUIREMENTS.md` §Work With Me — CTA-01, CTA-02 acceptance criteria
- `.planning/REQUIREMENTS.md` §Footer — FOOT-01 through FOOT-03 acceptance criteria

### Tech Stack & Theme
- `CLAUDE.md` §Technology Stack — Hugo image processing pipeline, css.Build patterns
- `.planning/phases/01-theme-foundation/01-CONTEXT.md` — All Phase 1 design system decisions (token naming, glow classes, pseudo-element conventions, sigil shapes)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `.glow-ambient` — ambient pulse class ready for hero image (Electric Violet, 5s cycle)
- `.glow-interactive` — hover/focus glow class ready for social link cards
- `.glow-radiant-core` — CTA button gradient glow (Fusion Gold → Ignition Orange) ready to apply
- `.section-void` / `.section-depth` — alternating section backgrounds with Triad Rule vars
- `.section` + `.section-content` — section spacing and max-width container
- `.section + .section::before` — gradient transition between adjacent sections
- `.display-text` — Cinzel display treatment at `clamp(2.5rem, 8vw, 4rem)` weight 800
- `.sigil-arc`, `.sigil-arc-sm`, `.sigil-gradient` — decorative sigil shapes ready for placement
- Cinzel Variable + Space Grotesk Variable — self-hosted, font-display: swap confirmed

### Established Patterns
- `::before` reserved for glow effects, `::after` reserved for sigils (Phase 1 convention)
- Two-tier token naming: palette truth (`--arcaeon-*`) + semantic aliases (`--color-*`)
- Section-level triad override: `.section-void { --section-purple: ...; --section-blue: ...; --section-warm: ...; }`
- Hugo `css.Build` pipeline: `resources.Get "css/main.css" | css.Build | minify | fingerprint`

### Integration Points
- `themes/arcaeon/layouts/index.html` — currently renders `{{ .Content }}` in `<main>`, needs section partials
- `themes/arcaeon/layouts/partials/sections/` — empty directory, ready for section partials (hero.html, identity-cta.html, social.html, footer.html)
- `themes/arcaeon/layouts/_default/baseof.html` — `<head>` with CSS pipeline, needs `<header>`, `<footer>` semantic structure
- `content/_index.md` — minimal front matter, needs identity statement, tagline, social links data, CTA text fields
- `themes/arcaeon/assets/css/main.css` — single CSS file, new section-specific styles append here per D-03

</code_context>

<specifics>
## Specific Ideas

- Identity statement placeholder energy: "Enterprise architect. Tarot reader. Builder of systems that think. I hold paradox for a living — yours included." (This is a direction marker, not final copy — Claude writes the actual placeholder in this voice.)
- CTA format: "Coaching. Speaking. Collaboration." as descriptor, single "Work With Me" button below with Radiant Core glow treatment
- Footer closing: "Stay feral, folks." is exact — not paraphrased, not softened
- Social link order: Feral Architecture (Substack) anchors top-left, then Claude arranges LinkedIn, X, Instagram, Threads, Bluesky, Spotify, TarotPulse for flow
- The 8 platforms from SOCIAL-04: Feral Architecture (Substack), LinkedIn, X, Instagram, Threads, Bluesky, Spotify (album link), TarotPulse

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 02-static-content*
*Context gathered: 2026-04-16*
