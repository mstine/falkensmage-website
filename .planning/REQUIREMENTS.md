# Requirements: falkensmage.com

**Defined:** 2026-04-16
**Core Value:** A stranger landing from social media instantly understands who this person is and can reach everything that matters — in under ten seconds, on a phone.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Theme & Design System

- [ ] **THEME-01**: ARCÆON palette implemented as CSS custom properties (design tokens) with all color tiers — Primary Identity, Focal Energy, Cosmic Depth, Energy Accents
- [ ] **THEME-02**: Typographic hierarchy with self-hosted variable fonts (Cinzel for display/headings, Space Grotesk for body/UI) — validated against ARCÆON palette before locking
- [ ] **THEME-03**: Glow treatment system — reusable CSS for CTA buttons, hover states, hero image pulse using GPU-composited `::before` pseudo-element + `opacity` pattern (not `box-shadow`)
- [ ] **THEME-04**: Dark graphic novel aesthetic — deep backgrounds (Deep Indigo/Void Purple), directional light via gradients, painted shadow shapes
- [ ] **THEME-05**: Mobile-first responsive foundation — 375px viewport first, scales up via breakpoints baked into every partial
- [ ] **THEME-06**: Sigil grammar decorative elements — broken geometric circles, void-to-glow gradients as subtle visual DNA from Feral Architecture vocabulary
- [ ] **THEME-07**: Portable Hugo theme architecture (`themes/arcaeon/`) — built as reusable theme for future Digital Intuition properties, not root-level layouts

### Hero Section

- [ ] **HERO-01**: Magus image displayed full-width or near-full-width with responsive art direction (portrait crop for mobile 375px, original aspect on desktop)
- [ ] **HERO-02**: "Falken's Mage" display treatment — large typographic presence using Cinzel display weight
- [ ] **HERO-03**: Tagline placeholder slot — styled typography treatment with dummy text, easily swappable when Matt writes the real line
- [ ] **HERO-04**: Ambient glow pulse animation on hero image — CSS-only, GPU-composited (`transform`/`opacity`), honors `prefers-reduced-motion`

### Identity Statement

- [ ] **IDENT-01**: 2-3 sentence identity statement in Matt's voice — first-person, "technomagickal motherfucker" energy, not a third-person bio
- [ ] **IDENT-02**: Placeholder text scaffolded in Matt's voice style, easily replaceable with final copy

### Social Links

- [ ] **SOCIAL-01**: Social links section with icon + label for each platform, styled as Linktree-style grid or vertical stack
- [ ] **SOCIAL-02**: Hover animation on each social link — subtle, consistent with ARCÆON glow aesthetic
- [ ] **SOCIAL-03**: Minimum 44px touch targets on all social links
- [ ] **SOCIAL-04**: 8 platforms included: Feral Architecture (Substack), LinkedIn, X, Instagram, Threads, Bluesky, Spotify (album link), TarotPulse
- [ ] **SOCIAL-05**: Aria-labels on all social links for accessibility

### Work With Me

- [ ] **CTA-01**: Brief description (1-2 sentences) — coaching, speaking, collaboration
- [ ] **CTA-02**: Single mailto CTA button (`falkensmage@falkenslabyrinth.com`) with Radiant Core glow treatment (Fusion Gold → Ignition Orange gradient)

### Currently Section

- [ ] **CURR-01**: Auto-pulled latest Feral Architecture post title + link via Hugo `resources.GetRemote` + `transform.Unmarshal` at build time
- [ ] **CURR-02**: Manually editable "current focus" blurb from `content/_index.md` front matter
- [ ] **CURR-03**: Graceful fallback when Substack RSS is unreachable — `try` wrapping, `warnf` logging, static fallback content

### Footer

- [ ] **FOOT-01**: "Stay feral, folks." signature closing
- [ ] **FOOT-02**: Copyright: Digital Intuition LLC with current year
- [ ] **FOOT-03**: Subtle lemniscate/sigil mark as decorative element

### Infrastructure

- [ ] **INFRA-01**: Hugo project initialized with custom `arcaeon` theme under `themes/arcaeon/`
- [ ] **INFRA-02**: `hugo.toml` configured with `baseURL = "https://falkensmage.com/"`, ARCÆON palette values, and Hugo cache settings for RSS
- [ ] **INFRA-03**: GitHub Actions workflow — Hugo Extended 0.160.1 pinned, `npm ci` for fonts, `hugo --minify`, deploy to GitHub Pages
- [ ] **INFRA-04**: `static/CNAME` file with `falkensmage.com` to persist custom domain across deploys
- [ ] **INFRA-05**: Lemniscate sigil favicon (`.ico` + `.svg`)

### Performance

- [ ] **PERF-01**: Single page load under 1s on 3G connection
- [ ] **PERF-02**: Hero image optimized — WebP with JPEG fallback via Hugo image pipeline, lazy-load for below-fold content
- [ ] **PERF-03**: Self-hosted fonts with `font-display: swap` and `crossorigin` on preload links — no FOIT, no double-download
- [ ] **PERF-04**: No external font CDNs, no analytics scripts, no external JS dependencies

### Accessibility

- [ ] **A11Y-01**: Semantic HTML5 structure — `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>`
- [ ] **A11Y-02**: Color contrast ratios meet WCAG AA against dark backgrounds — neon accents reserved for decoration only, Solar White/Ion Glow for body text
- [ ] **A11Y-03**: All images have meaningful alt text (hero image describes the Magus scene)
- [ ] **A11Y-04**: `prefers-reduced-motion` media query disables all ambient animations

### SEO & Meta

- [ ] **SEO-01**: Open Graph tags with Magus image, proper title "Falken's Mage — Matt Stine", meta description encoding identity
- [ ] **SEO-02**: Twitter Card meta tags
- [ ] **SEO-03**: Canonical URL set to `https://falkensmage.com`

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
| — | — | — |

**Coverage:**
- v1 requirements: 33 total
- Mapped to phases: 0
- Unmapped: 33 (pending roadmap creation)

---
*Requirements defined: 2026-04-16*
*Last updated: 2026-04-16 after initial definition*
