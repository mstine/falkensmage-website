# Phase 1: Theme Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 01-theme-foundation
**Areas discussed:** CSS architecture, Typography scale, Glow treatment system, Dark aesthetic direction

---

## CSS Architecture

### Color Token Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Tiered naming | Palette truth vars with semantic aliases layered on top — two levels | ✓ |
| Flat naming | Simple names without tier prefixes, no semantic alias layer | |
| Hugo vars injection | Define palette in hugo.toml, inject via css.Build @import "hugo:vars" | |

**User's choice:** Tiered naming
**Notes:** None — selected recommended option

### Triad Rule Enforcement

| Option | Description | Selected |
|--------|-------------|----------|
| Section-level overrides | Each section partial gets scoped --section-purple/blue/warm vars | ✓ |
| Convention only | No CSS enforcement, Triad Rule lives in documentation only | |
| You decide | Claude picks the approach | |

**User's choice:** Section-level overrides
**Notes:** None

### CSS File Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Single file + sections | One main.css with commented sections | ✓ |
| Modular imports | Separate files per concern with @import | |
| You decide | Claude picks | |

**User's choice:** Single file + sections
**Notes:** None

---

## Typography Scale

### Type Scale Approach

| Option | Description | Selected |
|--------|-------------|----------|
| Minor Third (1.2) | Gentle progression, works well mobile-first | ✓ |
| Major Third (1.25) | More dramatic, more visual contrast | |
| Custom manual steps | Hand-picked sizes, design intuition | |

**User's choice:** Minor Third (1.2)
**Notes:** None

### Font Boundary (Cinzel vs Space Grotesk)

| Option | Description | Selected |
|--------|-------------|----------|
| Cinzel for display + headings | Cinzel handles display and h1-h3, Space Grotesk handles everything else | ✓ |
| Cinzel for display only | Cinzel reserved for logotype only | |
| You decide | Claude picks | |

**User's choice:** Cinzel for display + headings
**Notes:** None

### Cinzel Weight Range

| Option | Description | Selected |
|--------|-------------|----------|
| Bold headings (700+) | Display 800, h1 700, h2 600, h3 500 | ✓ |
| Regular weight (400-500) | Elegant, inscriptional feel, relies on size for hierarchy | |
| You decide | Claude picks weights that read well against dark | |

**User's choice:** Bold headings (700+)
**Notes:** None

---

## Glow Treatment System

### Number of Glow Variants

| Option | Description | Selected |
|--------|-------------|----------|
| Three variants | Ambient pulse, Interactive glow, Radiant Core CTA | ✓ |
| Two variants | Just ambient pulse + interactive hover | |
| You decide | Claude determines based on Phase 2 needs | |

**User's choice:** Three variants
**Notes:** None

### Ambient Pulse Color

| Option | Description | Selected |
|--------|-------------|----------|
| Electric Violet (#7a2cff) | Mystical, on-brand, primary identity color | ✓ |
| Neon Magenta (#ff3cac) | Warmer, more intense, leans into 'feral' energy | |
| Multi-color cycle | Cycles through violet → blue → magenta | |
| You decide | Claude picks based on visual testing | |

**User's choice:** Electric Violet
**Notes:** None

### Ambient Pulse Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Slow breath (4-6s) | Meditative, barely-there, subconsciously noticed | ✓ |
| Heartbeat (2-3s) | Faster, more noticeable, more energy | |
| You decide | Claude picks and tunes via custom property | |

**User's choice:** Slow breath (4-6s)
**Notes:** None

---

## Dark Aesthetic Direction

### Background Variation

| Option | Description | Selected |
|--------|-------------|----------|
| Alternating depths | Void Purple and Deep Indigo alternate per section, Midnight Blue for transitions | ✓ |
| Single background + gradients | One base with gradient overlays for section differentiation | |
| You decide | Claude picks best visual depth approach | |

**User's choice:** Alternating depths
**Notes:** None

### Sigil Grammar Decorative Elements

| Option | Description | Selected |
|--------|-------------|----------|
| CSS-only decorative shapes | Broken circles via border-radius on pseudo-elements, partial borders, low opacity | ✓ |
| Inline SVG sigils | Hand-crafted SVG fragments in Hugo partials | |
| Minimal — gradients only | Skip geometric shapes, only void-to-glow gradient fades | |
| You decide | Claude picks complement for dark aesthetic | |

**User's choice:** CSS-only decorative shapes
**Notes:** None

### Demo Page for Visual Validation

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — kitchen sink partial | Demo page showing all tokens, type scale, glow treatments, sigils | ✓ |
| No — validate in Phase 2 | Skip demo, validate when real sections are built | |
| You decide | Claude determines if demo adds enough value | |

**User's choice:** Yes — kitchen sink partial
**Notes:** None

---

## Claude's Discretion

- Exact opacity values for sigil elements
- Precise gradient transition heights between sections
- Demo page format (content page vs. partial)
- Space Grotesk weight choices for body/UI

## Deferred Ideas

None — discussion stayed within phase scope
