# Phase 2: Static Content - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 02-static-content
**Areas discussed:** Hero composition, Social links layout, Section flow & triad, Identity & copy tone

---

## Hero Composition

| Option | Description | Selected |
|--------|-------------|----------|
| Image above, text below | Magus image fills full width at top, logotype + tagline stacked below. Clean separation. | ✓ |
| Text overlaid on image | Full-bleed background with dark gradient overlay, text centered on top. More cinematic. | |
| Side-by-side on desktop, stacked on mobile | Image left, text right at desktop. Falls back to stacked on mobile. | |

**User's choice:** Image above, text below
**Notes:** Recommended approach — clean separation of visual impact (image) and textual identity (logotype).

| Option | Description | Selected |
|--------|-------------|----------|
| Full image, natural aspect | Show full 1.9:1 image at full width. ~198px tall on 375px screen. | |
| Center-crop to ~4:3 | object-fit: cover with taller container (~280-300px). Crops edges, more visual weight. | ✓ |
| Separate portrait crop | Dedicated portrait-oriented crop for mobile. Most control, requires manual image prep. | |

**User's choice:** Center-crop to ~4:3
**Notes:** Hugo `<picture>` with art direction handles responsive variants.

| Option | Description | Selected |
|--------|-------------|----------|
| Behind the image | .glow-ambient wraps image container. Electric Violet pulse bleeds from behind Magus. | ✓ |
| Behind the logotype | Glow wraps the "Falken's Mage" text. Glowing-text-from-the-void feel. | |
| Both | Image gets ambient pulse, logotype gets subtler variant. | |
| You decide | Claude picks what looks best. | |

**User's choice:** Behind the image
**Notes:** Image as focal point, dramatic framing effect.

| Option | Description | Selected |
|--------|-------------|----------|
| Stay stacked, wider image | Same stacked layout at all breakpoints. Simple, consistent. | |
| Side-by-side at desktop | Image left, logotype + tagline right at 1024px+. More sophisticated. | |
| You decide | Claude picks based on image dimensions. | ✓ |

**User's choice:** You decide (Claude's discretion)
**Notes:** —

---

## Social Links Layout

| Option | Description | Selected |
|--------|-------------|----------|
| 2-column grid | 4 rows of 2 links. Icon + label per cell. Compact, scannable. Scales to 3-4 cols on desktop. | ✓ |
| Vertical stack | Full-width rows, one link per row. Linktree-style. More scrolling. | |
| Icon-only grid + labels on hover/focus | Tight 4x2 icon grid, labels in tooltips and aria-labels. Minimal footprint. | |

**User's choice:** 2-column grid
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Inline SVG in Hugo partials | Hand-curated SVG paths embedded directly. Zero HTTP requests, CSS-styleable. | ✓ |
| SVG sprite sheet | Single SVG file with <symbol> definitions. One HTTP request. | |
| You decide | Claude picks the approach. | |

**User's choice:** Inline SVG in Hugo partials
**Notes:** 8 icons is manageable for inline embedding.

| Option | Description | Selected |
|--------|-------------|----------|
| Filled card with glow hover | Dark bg slightly lighter than section, border. .glow-interactive on hover. Substantial. | |
| Ghost card (border only) | Transparent with subtle border. Border lights up on hover. Lighter visual weight. | |
| You decide | Claude picks based on section background. | ✓ |

**User's choice:** You decide (Claude's discretion)
**Notes:** Must use .glow-interactive for hover treatment regardless of card style.

| Option | Description | Selected |
|--------|-------------|----------|
| Feral Architecture first, rest by Claude | Substack top-left (most prominent). Claude arranges other 7. | ✓ |
| Specific order I'll describe | User has a particular ordering. | |
| You decide entirely | Claude arranges all 8. | |

**User's choice:** Feral Architecture first, rest by Claude
**Notes:** Substack is the primary content platform.

---

## Section Flow & Triad

| Option | Description | Selected |
|--------|-------------|----------|
| Hero → Identity → Social → CTA → Footer | 5 sections, natural discovery flow. | |
| Hero → Social → Identity → CTA → Footer | Links immediately after hero for social-discovery visitors. | |
| Hero → Identity+CTA combined → Social → Footer | 4 sections. Identity flows into CTA within single section. | ✓ |

**User's choice:** Hero → Identity+CTA combined → Social → Footer
**Notes:** Strong move — identity earns its keep by leading directly to "work with me."

| Option | Description | Selected |
|--------|-------------|----------|
| void/depth/void/depth | Hero on Void Purple (darkest), alternating. Classic. | ✓ |
| depth/void/depth/void | Inverted — hero on Deep Indigo (brighter). | |
| You decide | Claude assigns. | |

**User's choice:** Hero: void, Identity+CTA: depth, Social: void, Footer: depth
**Notes:** —

| Option | Description | Selected |
|--------|-------------|----------|
| Section boundaries only | Sigils at gradient transition points. Subtle, structural. | ✓ |
| Within sections as floating accents | Positioned inside sections. More decorative presence, risk of clutter on mobile. | |
| You decide | Claude places sigils optimally. | |

**User's choice:** Section boundaries only
**Notes:** Not competing with content.

---

## Identity & Copy Tone

| Option | Description | Selected |
|--------|-------------|----------|
| Inside Identity+CTA section | Opens the Identity+CTA section on Deep Indigo. Statement flows into CTA. | ✓ |
| Tacked onto hero bottom | Below logotype/tagline, still within hero on Void Purple. | |
| You decide | Claude places it where it reads best. | |

**User's choice:** Inside Identity+CTA section
**Notes:** Hero is visual impact, Identity+CTA is verbal identity flowing into action.

| Option | Description | Selected |
|--------|-------------|----------|
| Full voice placeholder | Written in Matt's voice. Close enough to ship temporarily. Replaceable. | ✓ |
| Lorem ipsum / obvious placeholder | Generic placeholder. Obviously not final. | |
| Just the slot, no text | Empty container with typography treatment. | |

**User's choice:** Full voice placeholder
**Notes:** Direction marker: "Enterprise architect. Tarot reader. Builder of systems that think."

| Option | Description | Selected |
|--------|-------------|----------|
| Brief + general | "Coaching. Speaking. Collaboration." + mailto button. Keeps it open. | ✓ |
| Slightly more specific | "Executive coaching, keynotes, technical leadership advisory." | |
| You decide | Claude writes CTA copy. | |

**User's choice:** Brief + general
**Notes:** ICP still being refined — don't promise specifics.

| Option | Description | Selected |
|--------|-------------|----------|
| Full voice placeholder | A line carrying the right energy so typography treatment can be evaluated. | ✓ |
| Typographic placeholder only | "[Your tagline here]" or short evocative phrase that's obviously placeholder. | |
| Empty slot, no text | Just the styled container. | |

**User's choice:** Full voice placeholder
**Notes:** Same approach as identity statement — replaceable via front matter.

## Claude's Discretion

- Desktop hero layout (stacked vs side-by-side)
- Social link card style (filled vs ghost)
- Social link platform ordering after Feral Architecture
- Sigil arc sizes and rotation angles at section boundaries
- Exact image container height for mobile crop (280-300px range)

## Deferred Ideas

None — discussion stayed within phase scope.
