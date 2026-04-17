# falkensmage.com

## Current State

✅ **v1.0 shipped 2026-04-17** — live at https://falkensmage.com.

The front door is up. A stranger landing from social media can see who this person is and reach every platform in under ten seconds on a phone screen. Hugo Extended 0.160.1 static site, GitHub Actions + Pages deploy, custom domain with HTTPS enforced, sub-1s 3G budget, WCAG AA.

<details>
<summary>Pre-v1.0 context (archived)</summary>

Original brownfield scope: single-page mobile-first personal site for Matt Stine's public identity (Falken's Mage). The front door. Social discovery lands here — makes the person legible in ten seconds on a phone screen. Everything else orbits it: Feral Architecture (Substack), Digital Intuition (LLC), Falken's Labyrinth (book), RitualSync (software company).

Core value: A stranger landing from social media instantly understands who this person is and can reach everything that matters — in under ten seconds, on a phone.

</details>

## Next Milestone Goals

Not yet defined. Run `/gsd-new-milestone` to scope v1.1.

Likely candidates (deferred from v1.0, non-binding):

- **Copy finalization** — real tagline (currently placeholder), real identity statement (currently voice-style placeholder)
- **Nyquist validation retroactive** — run `/gsd-validate-phase 0{3,4,5}` to fill VALIDATION.md scaffolds
- **AUTO-01** — scheduled GitHub Actions cron for daily rebuilds so "Currently" RSS stays fresh
- **AUTO-02** — automated social card image generation for OG tags
- **EXPAND-01** — "Currently" expanded with multiple content sources (podcast, projects)
- **EXPAND-02** — additional pages (about, services) using `arcaeon` theme partials
- **EXPAND-03** — dark mode / light mode toggle

## What This Is

Single-page, mobile-first personal site for Matt Stine's public identity: **Falken's Mage**. The front door. Everything else orbits it: Feral Architecture (Substack), Digital Intuition (LLC), Falken's Labyrinth (book), RitualSync (software company).

## Core Value

A stranger landing from social media instantly understands who this person is and can reach everything that matters — in under ten seconds, on a phone.

*Validated in v1.0 — shipped and live.*

## Requirements

### Validated (v1.0)

- ✓ Custom Hugo theme `arcaeon` — ARCAEON palette as CSS custom properties, typographic hierarchy, glow treatments, dark graphic novel aesthetic, responsive mobile-first foundation — v1.0
- ✓ Typography — self-hosted Cinzel Variable (display/headings) and Space Grotesk Variable (body/UI) via `@fontsource-variable`, committed WOFF2 as trust root — v1.0
- ✓ Hero section with Magus image (WebP + JPEG fallback via Hugo `picture` art direction), "Falken's Mage" display treatment, placeholder tagline, ambient glow pulse animation — v1.0
- ✓ Identity statement — 2-3 sentences in Matt's voice, first-person, "technomagickal motherfucker" energy — v1.0
- ✓ Social links section — Linktree-style grid with icons, labels, glow-interactive hover (Substack, LinkedIn, X, Instagram, Threads, Bluesky, Spotify, TarotPulse) — v1.0
- ✓ Work With Me section — coaching/speaking/collaboration CTA, mailto, Radiant Core glow button — v1.0
- ✓ Footer — "Stay feral, folks." closing, Digital Intuition LLC copyright with dynamic year, lemniscate mark — v1.0
- ✓ Currently section — build-time RSS pull from Feral Architecture + manually editable focus blurb, graceful fallback — v1.0
- ✓ Performance — sub-1s 3G budget, single-fetch fonts, WebP hero, no external dependencies — v1.0
- ✓ Mobile-first — 375px viewport first, 44px touch targets, responsive breakpoints — v1.0
- ✓ Accessibility — semantic HTML5 landmarks, WCAG AA contrast, alt text, aria-labels, `prefers-reduced-motion` — v1.0
- ✓ SEO/Meta — Open Graph (1200×630 JPEG Magus image), Twitter Card, canonical URL — v1.0
- ✓ Lemniscate sigil favicon — Electric Violet / Neon Magenta, SVG + ICO — v1.0
- ✓ Hugo static site with GitHub Actions build/deploy to GitHub Pages, HTTPS enforced, custom domain persistent — v1.0

### Active

*None at close. Define via `/gsd-new-milestone` for v1.1.*

### Out of Scope

Reasoning held through v1.0; re-audit at next milestone start.

- CRM / email capture — that's the sovereign stack project, not this site
- Content platform — Feral Architecture on Substack handles that
- Full offer stack with scheduling/payment — premature, ICP still being refined
- Portfolio / resume site — this is identity, not credentials
- Analytics — not included unless explicitly revisited
- Podcast link — omitted until Rewired feed is live (no dead links)
- OAuth / login — this is a static public page, no user accounts
- Multi-page navigation — single page by design
- Third-party theme — `arcaeon` is the brand, not a skin on someone else's work

## Context

**Current codebase state:** 1,048 LOC under `themes/arcaeon/` (HTML + CSS), 71 LOC `.github/workflows/hugo.yml`, 54 LOC test scripts (`tests/validate-phase-0{1,2,3}.sh`). Zero runtime JavaScript dependencies. Zero external CDN calls. Hugo Extended 0.160.1 pinned in CI. GitHub repo at `github.com/mstine/falkensmage-website` (public).

**Tech stack locked:** Hugo Extended 0.160.1, `css.Build` native CSS pipeline (no PostCSS), `@fontsource-variable/cinzel@5.2.8` + `@fontsource-variable/space-grotesk@5.2.10` (committed WOFF2 as trust root; `package.json` retained as version documentation), GitHub Actions + GitHub Pages, no Node in CI.

**Brand architecture:** Falken's Mage is the public identity. Digital Intuition LLC is the legal entity. Feral Architecture is the Substack newsletter. Falken's Labyrinth is the book. RitualSync is the software company (TarotPulse, etc.).

**Voice:** "Technomagickal motherfucker." Direct, alive, irreverent, holding paradox without apology. No register shift, no softening. The site feels like the person who writes Feral Architecture.

**Hero image source:** `~/Documents/Business-Brand/Feral-Architecture/covers/2026-04-14-aesthetic-decisions/final/aesthetic-decisions-cover.jpg` — 1200×628 Substack/OG horizontal, adapted via Hugo `.Fill`/`.Resize` pipeline.

**ARCÆON color system:**

- Primary Identity: Electric Violet `#7a2cff`, Neon Magenta `#ff3cac`, Electric Blue `#2fd3ff`
- Focal Energy: Solar White `#fff4e6`, Fusion Gold `#ffb347`, Ignition Orange `#ff7a18`
- Cosmic Depth: Deep Indigo `#0a0f3c`, Midnight Blue `#111a6b`, Void Purple `#1a0f2e`
- Energy Accents: Ion Glow `#5be7ff`, Plasma Pink `#ff5fd2`
- Triad Rule: every section needs one purple + one blue + one warm core

**Reference material:**

- ARCAEON palette full system: `~/.psyche/swipe-files/podcasting-creative/2026-04-16-12-33-18-arc-on-color-palette-full.md`
- Feral Architecture aesthetic contract: `~/Documents/Business-Brand/Feral-Architecture/covers/TEMPLATE.md`

**Known issues / deferred at v1.0 close:**

- 5 bookkeeping drift items (see `STATE.md` → Deferred Items). Resolved in substance per milestone audit.
- Nyquist validation scaffolds in draft for Phases 3, 4, 5 — non-blocking, fillable retroactively.

## Constraints

- **Stack:** Hugo Extended 0.160.1 with custom `arcaeon` theme
- **Hosting:** GitHub Pages via GitHub Actions build/deploy pipeline
- **Domain:** falkensmage.com — live, DNS pointed to GitHub Pages, HTTPS enforced
- **Performance:** Sub-1s page load on 3G — no external fonts unless self-hosted, no analytics, no external dependencies
- **Mobile-first:** 375px viewport designed first, scales up
- **Accessibility:** WCAG AA minimum
- **No external font CDNs:** Self-hosted WOFF2 only (committed as trust root)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Hugo over hand-crafted HTML | Prior experience, partials/sections ready for growth, asset pipeline, `resources.GetRemote` for RSS | ✓ Good — paid off inside Phase 1 |
| Custom `arcaeon` theme from scratch | Theme IS the brand — aesthetic contract at infrastructure level, reusable across future Digital Intuition properties | ✓ Good — portable, used as designed |
| Include "Currently" section in v1 | Adds dynamism — RSS auto-pull from Substack + manual current focus blurb | ✓ Good — zero JS, zero runtime cost |
| Self-hosted variable fonts | Dark graphic novel aesthetic needs Cinzel + Space Grotesk; system stack insufficient; constraint forbids CDNs | ✓ Good — committed WOFF2 as trust root |
| Lemniscate sigil as favicon | Consistent with Feral Architecture visual grammar | ✓ Good — SVG + ICO both rendering |
| Omit podcast link until feed live | No dead links — add when Rewired launches | — Pending (still waiting on Rewired) |
| Placeholder tagline slot | Matt writes the real line later — build the typography treatment now | — Pending (copy work deferred) |
| `css.Build` over PostCSS | Node-free build, native fingerprint + minify, 0.160+ config var injection | ✓ Good — no PostCSS regret |
| Two-tier ARCAEON token naming | Palette truth (`--arcaeon-*`) + semantic aliases (`--color-*`) | ✓ Good — load-bearing from Phase 1 on |
| `::before` = glow, `::after` = sigil convention | Consistent pseudo-element semantics across components | ✓ Good — held across all partials |
| `.Process "webp"` not `.Format "webp"` | `.Format` errors in Hugo 0.160.1 | ✓ Good — Hugo API reality |
| RSS URL to `feralarchitecture.com/feed` | Avoids 301 redirect from `substack.com` | ✓ Good — direct host, no cache footgun |
| OG image as JPEG (not WebP) | Max social crawler compatibility | ✓ Good — OG previews work everywhere |
| ICO committed as static artifact | Zero CI apt dependency for `rsvg-convert` | ✓ Good — pure Hugo + Pages in CI |
| `css.Build` externals with absolute path strings | Glob patterns empirically fail with esbuild CSS `url()` resolver | ✓ Good — Phase 5 fix landed |
| Committed WOFF2 as CI trust root | Remove `npm ci` from workflow; `package.json` as version documentation only | ✓ Good — eliminated Node from CI entirely |
| Clean-rebuild verification gate | `rm -rf public/ resources/_gen/` before assertions — exposed stale-state masking in Phase 5 | ✓ Good — established discipline |

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
*Last updated: 2026-04-17 after v1.0 milestone*
