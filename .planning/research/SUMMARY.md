# Research Summary: falkensmage.com

**Synthesized:** 2026-04-16
**Sources:** STACK.md, FEATURES.md, ARCHITECTURE.md, PITFALLS.md

## Executive Summary

Single-page personal brand identity site — social discovery front door, not a portfolio or offer stack. The ARCÆON dark graphic novel aesthetic IS the brand signal. Research consensus: Hugo Extended 0.160.1 (prior experience, native CSS processing, build-time RSS), self-hosted fonts (3G constraint + no-CDN), GitHub Pages (zero vendor dependency).

The `arcaeon` theme is treated as reusable brand infrastructure from day one. Architecture: section-per-partial, CSS custom property token system, build-time RSS for "Currently," Hugo Pipes for image optimization and font fingerprinting. All content lives in `content/_index.md` front matter. Scope is tight: zero email capture, zero analytics, zero multi-page navigation. Under a second on 3G.

Key risks cluster in Phase 1: neon palette pairs fail WCAG AA on body text, glow animation destroys mobile perf if done with `box-shadow`, font loading without `font-display: swap` causes FOIT. Build-it-wrong-once problems — cheaper to prevent than retrofit.

## Recommended Stack

| Component | Choice | Version | Confidence |
|-----------|--------|---------|------------|
| Static site generator | Hugo Extended | 0.160.1 | HIGH |
| CSS processing | Hugo `css.Build` (native) | — | HIGH |
| Display font | Cinzel Variable (self-hosted) | @fontsource 5.2.8 | MEDIUM (aesthetic) |
| Body font | Space Grotesk Variable (self-hosted) | @fontsource 5.2.10 | MEDIUM (aesthetic) |
| RSS fetch | `resources.GetRemote` + `transform.Unmarshal` | — | HIGH |
| Hosting | GitHub Pages | — | HIGH |
| CI/CD | GitHub Actions (official Hugo workflow) | — | HIGH |

**Do NOT use:** Tailwind, PostCSS, GSAP, Google Fonts CDN, `peaceiris/actions-hugo`, `data.GetJSON` (removed in Hugo 0.140), analytics.

## Table Stakes Features

- Hero with Magus image + display name + tagline slot
- Identity statement in voice (first-person, no third-person bio)
- Social links grid (8 platforms, icon + label + hover, 44px touch targets)
- "Work With Me" mailto CTA with Radiant Core glow
- Open Graph / Twitter Card meta with absolute URL OG image
- Mobile-first responsive at 375px, sub-1s on 3G
- WCAG AA baseline, semantic HTML5
- HTTPS + custom domain, lemniscate favicon

## Differentiators

- ARCÆON CSS custom property system as full brand infrastructure
- Ambient hero animation (CSS-only, GPU-composited, reduced-motion honored)
- "Currently" section (RSS-pulled latest post + manual current-focus blurb)
- Voice-first copy + "Stay feral, folks." footer signature

## Top Pitfalls

1. **baseURL mismatch** — set `https://falkensmage.com/` from day one
2. **Neon colors fail WCAG AA as body text** — reserve for decoration only; validate every text/bg pair
3. **`box-shadow` animation kills mobile** — use `::before` pseudo-element + `opacity` for glow
4. **CNAME overwritten on deploy** — `static/CNAME` file required
5. **RSS fetch breaks CI silently** — wrap in `try`, log with `warnf`, render fallback
6. **Font FOIT + double-download** — `font-display: swap` + `crossorigin` on preload
7. **Hugo version unpinned** — explicit `hugo-version: '0.160.1'` in Actions workflow

## Suggested Phase Structure

| Phase | Focus | Key Dependencies |
|-------|-------|-----------------|
| 1 | Foundation — ARCÆON theme scaffold + token system | None (root) |
| 2 | Static Sections — hero through footer | Phase 1 tokens |
| 3 | Dynamic Content — "Currently" section + RSS | Phase 2 layout |
| 4 | CI/CD Pipeline + Production Deploy | Phase 3 complete |

## Research Gaps

- **Font pairing** (MEDIUM confidence) — Cinzel + Space Grotesk needs visual validation against ARCÆON palette before type scale is locked
- **Magus image art direction** — 1200x628 horizontal source needs assessment for 375px portrait crop
- **Copy dependencies** — identity statement + tagline are human dependencies; scaffolded as placeholder slots

---
*Synthesized: 2026-04-16*
