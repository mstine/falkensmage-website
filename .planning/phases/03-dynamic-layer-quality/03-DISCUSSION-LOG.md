# Phase 3: Dynamic Layer + Quality - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 03-dynamic-layer-quality
**Areas discussed:** Currently section design, Performance strategy, Semantic structure + A11Y, SEO & Open Graph

---

## Currently Section Design

### Placement

| Option | Description | Selected |
|--------|-------------|----------|
| After Hero, before Identity+CTA | Fresh content up top — stranger sees what you're thinking about NOW before the bio | ✓ |
| After Identity+CTA, before Social Links | Identity lands first, then "here's what I'm doing now" as supporting evidence | |
| After Social Links, before Footer | Closing alive-signal right before footer sign-off | |

**User's choice:** After Hero, before Identity+CTA
**Notes:** Signals aliveness immediately — most prominent position for dynamic content.

### RSS Content Display

| Option | Description | Selected |
|--------|-------------|----------|
| Title + link only | Clean, minimal — just latest post title as clickable link | ✓ |
| Title + date + link | Adds publication date for freshness signal | |
| Title + excerpt + link | Adds 1-2 sentence excerpt — more content but heavier | |

**User's choice:** Title + link only
**Notes:** None — straightforward selection.

### RSS Fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Static "Read Feral Architecture" link | Simple link to Substack homepage when RSS fails | ✓ |
| Hide entire RSS portion | Only current focus blurb shows | |
| Show last-known post from front matter | Manually-maintained fallback title/link | |

**User's choice:** Static "Read Feral Architecture" link
**Notes:** Current focus blurb from front matter always shows regardless of RSS status.

### Visual Treatment

| Option | Description | Selected |
|--------|-------------|----------|
| Compact card-like block | Contained card/panel on Deep Indigo background | ✓ |
| Full-width section | Same treatment as Hero, Identity, Social sections | |
| Inline within Hero section | Lives at bottom of Hero section | |

**User's choice:** Compact card-like block
**Notes:** Reads as a distinct information module — lighter weight than full sections.

---

## Performance Strategy

### Hero Image Optimization

| Option | Description | Selected |
|--------|-------------|----------|
| WebP conversion + responsive srcset | Hugo generates WebP at 375w, 750w, 1200w with JPEG fallback | ✓ |
| WebP only, single size | Convert to WebP but don't generate multiple sizes | |
| You decide | Claude picks approach that hits PERF-01 | |

**User's choice:** WebP conversion + responsive srcset
**Notes:** Biggest single performance win. Hero stays eager-loaded (above fold).

### Font Preloading

| Option | Description | Selected |
|--------|-------------|----------|
| Preload both fonts | Two <link rel="preload"> tags for WOFF2 files in <head> | ✓ |
| No preload | Rely on CSS font-display: swap alone | |
| You decide | Claude picks based on Lighthouse results | |

**User's choice:** Preload both fonts
**Notes:** Eliminates FOUT flash by starting font download before CSS is parsed.

---

## Semantic Structure + A11Y

### Landmark Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Add <header> with site title | Hero in <header>, sections in <main>, footer in <footer> | ✓ |
| Skip <header>, keep flat | Everything stays inside <main> | |
| You decide | Claude picks based on WCAG AA requirements | |

**User's choice:** Add <header> with site title
**Notes:** No <nav> needed — single page with no navigation links.

### Magus Image Alt Text

| Option | Description | Selected |
|--------|-------------|----------|
| You decide | Claude writes descriptive alt text from viewing the image | ✓ |
| Let me write it | User provides exact alt text string | |

**User's choice:** You decide (Claude's discretion)
**Notes:** None.

---

## SEO & Open Graph

### Twitter Card Type

| Option | Description | Selected |
|--------|-------------|----------|
| summary_large_image | Large image preview above title/description | ✓ |
| summary | Small square thumbnail next to title/description | |

**User's choice:** summary_large_image
**Notes:** Magus image at 1424x752 is perfect for large format.

### Meta Description Direction

| Option | Description | Selected |
|--------|-------------|----------|
| Identity-forward | Leads with who Falken's Mage is — intersection of architecture and symbolic intelligence | ✓ |
| Action-forward | Leads with what you can do — coaching, speaking, newsletter | |
| Let me write it | User provides exact meta description | |

**User's choice:** Identity-forward
**Notes:** Encodes the identity, not the site's function. Claude writes final copy.

### OG Image Dimensions

| Option | Description | Selected |
|--------|-------------|----------|
| Resize to 1200x630 | Hugo generates exact OG standard crop at build time | ✓ |
| Use source dimensions as-is | Let platforms handle the crop from 1424x752 | |
| You decide | Claude picks based on platform rendering | |

**User's choice:** Resize to 1200x630
**Notes:** Matches OG standard exactly — no platform-side cropping surprises.

---

## Claude's Discretion

- Magus hero image alt text wording
- Meta description final copy (identity-forward direction locked)
- Currently card border/background visual treatment details
- Triad alternation adjustment for new section insertion

## Deferred Ideas

None — discussion stayed within phase scope.
