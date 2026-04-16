# Phase 1: Theme Foundation - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

The `arcaeon` Hugo theme exists as a portable design system — color tokens, typography, glow treatments, dark graphic novel aesthetic, sigil grammar decorative elements, and responsive mobile-first scaffold — ready for sections to be dropped into in Phase 2. Includes Hugo project initialization (`hugo.toml`, theme directory structure) and a kitchen sink demo page for visual validation.

</domain>

<decisions>
## Implementation Decisions

### CSS Architecture
- **D-01:** Tiered token naming — palette truth vars (`--arcaeon-primary-violet`, `--arcaeon-depth-indigo`, etc.) with semantic aliases (`--color-bg`, `--color-text`, `--color-accent`) layered on top. Two levels: palette truth + usage intent.
- **D-02:** Triad Rule enforced via section-level CSS overrides — each section partial gets scoped `--section-purple`, `--section-blue`, `--section-warm` vars that override root defaults. Convention lives in the partial structure.
- **D-03:** Single `main.css` file with clearly commented sections (Tokens, Reset, Typography, Glow System, Layout, Components). No modular imports — one file, bundled and minified by Hugo `css.Build`.

### Typography Scale
- **D-04:** Minor Third (1.2 ratio) type scale — body 1rem (16px), h3 ~1.44rem, h2 ~1.728rem, h1 ~2.074rem. Display treatment (Falken's Mage logotype) at `clamp(2.5rem, 8vw, 4rem)` — outside the scale.
- **D-05:** Cinzel Variable for display treatment and all headings (h1-h3). Space Grotesk Variable for everything else: body text, UI labels, social link labels, CTA button text, footer text. Clear boundary: heading = Cinzel, not-heading = Space Grotesk.
- **D-06:** Bold Cinzel weight progression — display 800, h1 700, h2 600, h3 500. Heavy weights to ensure legibility against dark backgrounds.

### Glow Treatment System
- **D-07:** Three distinct glow variants defined as reusable CSS classes:
  1. **Ambient pulse** — slow breathing radial gradient glow for hero image and decorative elements
  2. **Interactive glow** — hover/focus state for links and social cards (opacity transition)
  3. **Radiant Core** — CTA button gradient glow (Fusion Gold → Ignition Orange)
- **D-08:** All glow effects use `::before` pseudo-element + `opacity` pattern (GPU-composited). No `box-shadow`.
- **D-09:** Ambient pulse color: Electric Violet (#7a2cff). Mystical, on-brand, fits the magus energy.
- **D-10:** Ambient pulse timing: slow breath, 4-6 second cycle. Barely-there — subconsciously noticed, not distracting.

### Dark Aesthetic Direction
- **D-11:** Alternating depth backgrounds per section — Void Purple and Deep Indigo alternate. Midnight Blue used for gradient transitions between sections. Creates visual separation without borders.
- **D-12:** Sigil grammar as CSS-only decorative shapes — broken geometric circles and arc fragments via `border-radius` on pseudo-elements with partial borders, rotated. Placed at section boundaries at low opacity (~0.3). No SVG files, no external assets.
- **D-13:** Kitchen sink demo page included in Phase 1 — renders all color tokens, type scale samples, all three glow treatments, and sigil elements for visual validation before Phase 2 builds real sections. Can be a content page or partial, gets removed/hidden later.

### Claude's Discretion
- Exact opacity values for sigil elements (started at 0.3, tunable)
- Precise gradient transition heights between sections
- Demo page format (content page vs. partial — whichever is simpler)
- Space Grotesk weight choices for body/UI (variable font, Claude picks what reads best)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### ARCAEON Color System
- `~/.psyche/swipe-files/podcasting-creative/2026-04-16-12-33-18-arc-on-color-palette-full.md` — Full ARCAEON palette system with all color tiers, usage rules, and the Triad Rule
- `SPEC.md` §Color Palette — ARCAEON System — Hex values, tier definitions, usage guidelines

### Visual Aesthetic
- `~/Documents/Business-Brand/Feral-Architecture/covers/TEMPLATE.md` — Feral Architecture aesthetic contract defining the dark graphic novel visual language, sigil grammar vocabulary

### Project Requirements
- `.planning/REQUIREMENTS.md` §Theme & Design System — THEME-01 through THEME-07 acceptance criteria
- `.planning/REQUIREMENTS.md` §Infrastructure — INFRA-01, INFRA-02 acceptance criteria

### Tech Stack
- `CLAUDE.md` §Technology Stack — Hugo Extended 0.160.1, css.Build, @fontsource-variable packages, npm setup, CSS architecture patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no code exists yet

### Established Patterns
- None — this phase establishes the patterns all future phases inherit

### Integration Points
- `hugo.toml` — ARCAEON palette values defined here, referenced by CSS tokens
- `themes/arcaeon/` — portable theme directory, all CSS/layouts/partials live here
- `content/_index.md` — Hugo content file that will use the theme in Phase 2
- `static/` — self-hosted font files (WOFF2) copied from @fontsource-variable packages

</code_context>

<specifics>
## Specific Ideas

- The glow system preview showed `radial-gradient(var(--arcaeon-primary-violet), transparent 70%)` for ambient pulse — this approach confirmed
- Section-level triad override pattern: `.hero { --section-purple: var(--arcaeon-depth-void); }` — confirmed as the enforcement mechanism
- Cinzel weight progression (800→700→600→500) descending from display to h3 — specific values locked

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-theme-foundation*
*Context gathered: 2026-04-16*
