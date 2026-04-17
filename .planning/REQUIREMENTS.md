# Requirements: falkensmage.com

**Defined:** 2026-04-16
**Core Value:** A stranger landing from social media instantly understands who this person is and can reach everything that matters — in under ten seconds, on a phone.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Theme & Design System

- [x] **THEME-01**: ARCÆON palette implemented as CSS custom properties (design tokens) with all color tiers — Primary Identity, Focal Energy, Cosmic Depth, Energy Accents
- [x] **THEME-02**: Typographic hierarchy with self-hosted variable fonts (Cinzel for display/headings, Space Grotesk for body/UI) — validated against ARCÆON palette before locking
- [x] **THEME-03**: Glow treatment system — reusable CSS for CTA buttons, hover states, hero image pulse using GPU-composited `::before` pseudo-element + `opacity` pattern (not `box-shadow`)
- [x] **THEME-04**: Dark graphic novel aesthetic — deep backgrounds (Deep Indigo/Void Purple), directional light via gradients, painted shadow shapes
- [x] **THEME-05**: Mobile-first responsive foundation — 375px viewport first, scales up via breakpoints baked into every partial
- [x] **THEME-06**: Sigil grammar decorative elements — broken geometric circles, void-to-glow gradients as subtle visual DNA from Feral Architecture vocabulary
- [x] **THEME-07**: Portable Hugo theme architecture (`themes/arcaeon/`) — built as reusable theme for future Digital Intuition properties, not root-level layouts

### Hero Section

- [x] **HERO-01**: Magus image displayed full-width or near-full-width with responsive art direction (portrait crop for mobile 375px, original aspect on desktop)
- [x] **HERO-02**: "Falken's Mage" display treatment — large typographic presence using Cinzel display weight
- [x] **HERO-03**: Tagline placeholder slot — styled typography treatment with dummy text, easily swappable when Matt writes the real line
- [x] **HERO-04**: Ambient glow pulse animation on hero image — CSS-only, GPU-composited (`transform`/`opacity`), honors `prefers-reduced-motion`

### Identity Statement

- [x] **IDENT-01**: 2-3 sentence identity statement in Matt's voice — first-person, "technomagickal motherfucker" energy, not a third-person bio
- [x] **IDENT-02**: Placeholder text scaffolded in Matt's voice style, easily replaceable with final copy

### Social Links

- [x] **SOCIAL-01**: Social links section with icon + label for each platform, styled as Linktree-style grid or vertical stack
- [x] **SOCIAL-02**: Hover animation on each social link — subtle, consistent with ARCÆON glow aesthetic
- [x] **SOCIAL-03**: Minimum 44px touch targets on all social links
- [x] **SOCIAL-04**: 8 platforms included: Feral Architecture (Substack), LinkedIn, X, Instagram, Threads, Bluesky, Spotify (album link), TarotPulse
- [x] **SOCIAL-05**: Aria-labels on all social links for accessibility

### Work With Me

- [x] **CTA-01**: Brief description (1-2 sentences) — coaching, speaking, collaboration
- [x] **CTA-02**: Single mailto CTA button (`falkensmage@falkenslabyrinth.com`) with Radiant Core glow treatment (Fusion Gold → Ignition Orange gradient)

### Currently Section

- [x] **CURR-01**: Auto-pulled latest Feral Architecture post title + link via Hugo `resources.GetRemote` + `transform.Unmarshal` at build time
- [x] **CURR-02**: Manually editable "current focus" blurb from `content/_index.md` front matter
- [x] **CURR-03**: Graceful fallback when Substack RSS is unreachable — `try` wrapping, `warnf` logging, static fallback content

### Footer

- [x] **FOOT-01**: "Stay feral, folks." signature closing
- [x] **FOOT-02**: Copyright: Digital Intuition LLC with current year
- [x] **FOOT-03**: Subtle lemniscate/sigil mark as decorative element

### Infrastructure

- [x] **INFRA-01**: Hugo project initialized with custom `arcaeon` theme under `themes/arcaeon/`
- [x] **INFRA-02**: `hugo.toml` configured with `baseURL = "https://falkensmage.com/"`, ARCÆON palette values, and Hugo cache settings for RSS
- [x] **INFRA-03**: GitHub Actions workflow — Hugo Extended 0.160.1 pinned, `npm ci` for fonts, `hugo --minify`, deploy to GitHub Pages
- [x] **INFRA-04**: `static/CNAME` file with `falkensmage.com` to persist custom domain across deploys
- [x] **INFRA-05**: Lemniscate sigil favicon (`.ico` + `.svg`)

### Performance

- [x] **PERF-01**: Single page load under 1s on 3G connection
- [x] **PERF-02**: Hero image optimized — WebP with JPEG fallback via Hugo image pipeline, lazy-load for below-fold content
- [x] **PERF-03**: Self-hosted fonts with `font-display: swap` and `crossorigin` on preload links — no FOIT, no double-download
- [x] **PERF-04**: No external font CDNs, no analytics scripts, no external JS dependencies

### Accessibility

- [x] **A11Y-01**: Semantic HTML5 structure — `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`
- [x] **A11Y-02**: Color contrast ratios meet WCAG AA against dark backgrounds — neon accents reserved for decoration only, Solar White/Ion Glow for body text
- [x] **A11Y-03**: All images have meaningful alt text (hero image describes the Magus scene)
- [x] **A11Y-04**: `prefers-reduced-motion` media query disables all ambient animations

### SEO & Meta

- [x] **SEO-01**: Open Graph tags with Magus image, proper title "Falken's Mage — Matt Stine", meta description encoding identity
- [x] **SEO-02**: Twitter Card meta tags
- [x] **SEO-03**: Canonical URL set to `https://falkensmage.com`

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Content Automation

- **AUTO-01**: Scheduled GitHub Actions cron job for daily rebuilds to keep "Currently" RSS content fresh
- **AUTO-02**: Automated social card image generation for OG tags

### Future Expansion

- **EXPAND-01**: "Currently" section expanded with multiple content sources (podcast, projects)
- **EXPAND-02**: Additional pages (about, services) using `arcaeon` theme partials
- **EXPAND-03**: Dark mode / light mode toggle (currently dark-only)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Email capture / CRM | Sovereign stack project — premature without the infrastructure |
| Analytics | No conversion funnel to measure — adds weight for zero signal |
| Podcast link | Rewired feed not live — no dead links |
| Portfolio / case studies | This is identity, not credentials |
| Blog / content hub | Feral Architecture on Substack handles content |
| OAuth / user accounts | Static public page — no user state |
| Scheduling widget / intake form | ICP still being refined — premature |
| Multi-page navigation | Single page by design |
| Third-party theme | `arcaeon` is the brand, not a skin on someone else's work |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| THEME-01 | Phase 1 | Complete |
| THEME-02 | Phase 1 | Complete |
| THEME-03 | Phase 1 | Complete |
| THEME-04 | Phase 1 | Complete |
| THEME-05 | Phase 1 | Complete |
| THEME-06 | Phase 1 | Complete |
| THEME-07 | Phase 1 | Complete |
| INFRA-01 | Phase 1 | Complete |
| INFRA-02 | Phase 1 | Complete |
| HERO-01 | Phase 2 | Complete |
| HERO-02 | Phase 2 | Complete |
| HERO-03 | Phase 2 | Complete |
| HERO-04 | Phase 2 | Complete |
| IDENT-01 | Phase 2 | Complete |
| IDENT-02 | Phase 2 | Complete |
| SOCIAL-01 | Phase 2 | Complete |
| SOCIAL-02 | Phase 2 | Complete |
| SOCIAL-03 | Phase 2 | Complete |
| SOCIAL-04 | Phase 2 | Complete |
| SOCIAL-05 | Phase 2 | Complete |
| CTA-01 | Phase 2 | Complete |
| CTA-02 | Phase 2 | Complete |
| FOOT-01 | Phase 2 | Complete |
| FOOT-02 | Phase 2 | Complete |
| FOOT-03 | Phase 2 | Complete |
| CURR-01 | Phase 3 | Complete |
| CURR-02 | Phase 3 | Complete |
| CURR-03 | Phase 3 | Complete |
| PERF-01 | Phase 5 | Complete |
| PERF-02 | Phase 3 | Complete |
| PERF-03 | Phase 5 | Complete |
| PERF-04 | Phase 3 | Complete |
| A11Y-01 | Phase 5 | Complete |
| A11Y-02 | Phase 3 | Complete |
| A11Y-03 | Phase 3 | Complete |
| A11Y-04 | Phase 3 | Complete |
| SEO-01 | Phase 3 | Complete |
| SEO-02 | Phase 3 | Complete |
| SEO-03 | Phase 3 | Complete |
| INFRA-03 | Phase 4 | Complete |
| INFRA-04 | Phase 4 | Complete |
| INFRA-05 | Phase 4 | Complete |

**Coverage:**
- v1 requirements: 42 total (note: prior count of 33 was incorrect — 42 requirements exist across 11 categories)
- Mapped to phases: 42
- Unmapped: 0

---
*Requirements defined: 2026-04-16*
*Last updated: 2026-04-17 — A11Y-01, PERF-01, PERF-03 reset to Pending and reassigned to Phase 5 (gap closure) per v1.0 milestone audit*
*Phase 5 gap closure complete: A11Y-01, PERF-01, PERF-03 marked Complete on 2026-04-17*
