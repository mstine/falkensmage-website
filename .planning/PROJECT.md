# falkensmage.com

## What This Is

Single-page, mobile-first personal site for Matt Stine's public identity: **Falken's Mage**. The front door. Social discovery lands here — makes the person legible in ten seconds on a phone screen. Everything else orbits it: Feral Architecture (Substack), Digital Intuition (LLC), Falken's Labyrinth (book), RitualSync (software company).

## Core Value

A stranger landing from social media instantly understands who this person is and can reach everything that matters — in under ten seconds, on a phone.

## Requirements

### Validated

- [x] Custom Hugo theme `arcaeon` — ARCAEON palette as CSS custom properties, typographic hierarchy, glow treatments, dark graphic novel aesthetic, responsive mobile-first foundation — *Validated in Phase 1: Theme Foundation*
- [x] Typography — self-hosted Cinzel Variable (display/headings) and Space Grotesk Variable (body/UI) via @fontsource-variable — *Validated in Phase 1: Theme Foundation*
- [x] Hero section with Magus image, "Falken's Mage" display treatment, placeholder tagline, subtle ambient animation — *Validated in Phase 2: Static Content*
- [x] Identity statement — 2-3 sentences in Matt's voice, first-person, "technomagickal motherfucker" energy — *Validated in Phase 2: Static Content*
- [x] Social links section — Linktree-style grid/stack with icons, labels, hover animations (Substack, LinkedIn, X, Instagram, Threads, Bluesky, Spotify, TarotPulse) — *Validated in Phase 2: Static Content*
- [x] "Work With Me" section — coaching/speaking/collaboration CTA, mailto link, Radiant Core glow button — *Validated in Phase 2: Static Content*
- [x] Footer — "Stay feral, folks." closing, Digital Intuition LLC copyright, subtle sigil/lemniscate mark — *Validated in Phase 2: Static Content*

### Active

*No active requirements — all v1.0 milestone requirements validated.*

### Recently Validated (Phase 3 + 4)

- [x] "Currently" section — auto-pulled latest Feral Architecture post via RSS + manually editable "current focus" blurb — *Validated in Phase 3: Dynamic Layer + Quality*
- [x] Performance — single page load under 1s on 3G, WebP with JPEG fallback, lazy-load below fold — *Validated in Phase 3: Dynamic Layer + Quality*
- [x] Mobile-first — designed for 375px viewport, 44px touch targets, portrait hero, no horizontal scroll — *Validated in Phase 3: Dynamic Layer + Quality*
- [x] Accessibility — semantic HTML5, WCAG AA contrast, meaningful alt text, aria-labels, prefers-reduced-motion — *Validated in Phase 3: Dynamic Layer + Quality*
- [x] SEO/Meta — Open Graph tags with Magus image, Twitter card, proper title/description, canonical URL — *Validated in Phase 3: Dynamic Layer + Quality*
- [x] Lemniscate sigil favicon — Electric Violet lemniscate with ARCAEON glow, SVG + ICO formats — *Validated in Phase 4: Production Deploy*
- [x] Hugo static site with GitHub Actions build/deploy pipeline to GitHub Pages — *Validated in Phase 4: Production Deploy*

### Out of Scope

- CRM / email capture — that's the sovereign stack project, not this site
- Content platform — Feral Architecture on Substack handles that
- Full offer stack with scheduling/payment — premature, ICP still being refined
- Portfolio / resume site — this is identity, not credentials
- Analytics — not included unless Matt explicitly adds later
- Podcast link — omitted until feed is live
- OAuth / login — this is a static public page, no user accounts

## Context

**Brand architecture:** Falken's Mage is the public identity. Digital Intuition LLC is the legal entity. Feral Architecture is the Substack newsletter. Falken's Labyrinth is the book. RitualSync is the software company (TarotPulse, etc.).

**Voice:** "Technomagickal motherfucker." Direct, alive, irreverent, holding paradox without apology. No register shift, no softening. The site should feel like the person who writes Feral Architecture.

**Hero image source:** `~/Documents/Business-Brand/Feral-Architecture/covers/2026-04-14-aesthetic-decisions/final/aesthetic-decisions-cover.jpg` — 1200x628 (Substack/OG horizontal). Needs adaptation for mobile portrait and desktop layouts.

**ARCÆON color system:**
- Primary Identity: Electric Violet `#7a2cff`, Neon Magenta `#ff3cac`, Electric Blue `#2fd3ff`
- Focal Energy: Solar White `#fff4e6`, Fusion Gold `#ffb347`, Ignition Orange `#ff7a18`
- Cosmic Depth: Deep Indigo `#0a0f3c`, Midnight Blue `#111a6b`, Void Purple `#1a0f2e`
- Energy Accents: Ion Glow `#5be7ff`, Plasma Pink `#ff5fd2`
- Triad Rule: every section needs one purple + one blue + one warm core

**Reference material:**
- ARCAEON palette full system: `~/.psyche/swipe-files/podcasting-creative/2026-04-16-12-33-18-arc-on-color-palette-full.md`
- Feral Architecture aesthetic contract: `~/Documents/Business-Brand/Feral-Architecture/covers/TEMPLATE.md`

## Constraints

- **Stack**: Hugo static site generator with custom `arcaeon` theme — Matt has prior Hugo experience, no ramp-up cost
- **Hosting**: GitHub Pages via GitHub Actions build/deploy pipeline
- **Domain**: falkensmage.com — owned, needs DNS pointed to GitHub Pages, HTTPS automatic
- **Performance**: Sub-1s page load on 3G — no external fonts unless self-hosted, no analytics, no external dependencies
- **Mobile-first**: 375px viewport designed first, scales up
- **Accessibility**: WCAG AA minimum
- **No external font CDNs**: Self-host or system stack only

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hugo over hand-crafted HTML | Prior experience, partials/sections ready for growth, asset pipeline for image optimization, content as markdown for future expansion | — Pending |
| Custom `arcaeon` theme from scratch | Theme IS the brand — aesthetic contract at infrastructure level, reusable across future Digital Intuition properties | — Pending |
| Include "Currently" section in v1 | Adds dynamism — RSS auto-pull from Substack + manual current focus blurb | — Pending |
| Self-hosted font via research | Dark graphic novel aesthetic needs the right typeface — system stack may not carry it | — Pending |
| Lemniscate sigil as favicon | Consistent with Feral Architecture visual grammar | — Pending |
| Omit podcast link until feed live | No dead links — add when Rewired launches | — Pending |
| Placeholder tagline slot | Matt writes the real line later — build the typography treatment now | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-04-17 after Phase 4: Production Deploy complete — falkensmage.com is live*
