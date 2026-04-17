# Roadmap: falkensmage.com

## Overview

Four phases, each delivering a coherent slice of the site. Phase 1 builds the brand infrastructure — the ARCÆON token system and Hugo theme scaffold that everything else inherits. Phase 2 renders the visible page: hero through footer, all static content. Phase 3 adds the dynamic layer (RSS "Currently") and bakes in the cross-cutting requirements: performance, accessibility, SEO. Phase 4 cuts the site to production — GitHub Actions pipeline, CNAME, favicon, live at falkensmage.com.

## Phases

- [x] **Phase 1: Theme Foundation** - ARCÆON design system + Hugo `arcaeon` theme scaffold (completed 2026-04-16)
- [x] **Phase 2: Static Content** - All visible sections: hero, identity, social links, CTA, footer (completed 2026-04-16)
- [x] **Phase 3: Dynamic Layer + Quality** - "Currently" RSS section + performance, accessibility, SEO (completed 2026-04-17)
- [x] **Phase 4: Production Deploy** - GitHub Actions pipeline, CNAME, favicon, live site (completed 2026-04-17)
- [x] **Phase 5: v1.0 Gap Closure** - Phase 3 & 4 code fixes + Phase 1 & 3 documentation backfill (completed 2026-04-17)

## Phase Details

### Phase 1: Theme Foundation
**Goal**: The `arcaeon` Hugo theme exists as a portable design system — color tokens, typography, glow treatments, dark graphic novel aesthetic, and responsive scaffold — ready for sections to be dropped into.
**Depends on**: Nothing (first phase)
**Requirements**: THEME-01, THEME-02, THEME-03, THEME-04, THEME-05, THEME-06, THEME-07, INFRA-01, INFRA-02
**Success Criteria** (what must be TRUE):
  1. Hugo project runs locally with `hugo server` and renders a blank page using the `arcaeon` theme without errors
  2. ARCÆON CSS custom properties (all color tiers) are available globally and resolve correctly in browser DevTools
  3. Cinzel (display) and Space Grotesk (body) render from self-hosted files with no FOIT — `font-display: swap` confirmed in network tab
  4. A glow CTA button and ambient pulse can be rendered in isolation using the CSS component system — GPU-composited, no `box-shadow`
  5. The `themes/arcaeon/` directory is structured as a portable Hugo theme (not root-level layouts)
**Plans**: 3 plans
Plans:
- [x] 01-01-PLAN.md — Hugo project init + ARCAEON CSS token system
- [x] 01-02-PLAN.md — Typography + Glow treatment system
- [x] 01-03-PLAN.md — Dark aesthetic, sigils, kitchen sink demo + visual checkpoint
**UI hint**: yes

### Phase 2: Static Content
**Goal**: A stranger can land on falkensmage.com and understand who this person is and reach every platform — all visible sections rendered, styled, and mobile-first.
**Depends on**: Phase 1
**Requirements**: HERO-01, HERO-02, HERO-03, HERO-04, IDENT-01, IDENT-02, SOCIAL-01, SOCIAL-02, SOCIAL-03, SOCIAL-04, SOCIAL-05, CTA-01, CTA-02, FOOT-01, FOOT-02, FOOT-03
**Success Criteria** (what must be TRUE):
  1. Magus image renders full-width at 375px with portrait crop; correct aspect on desktop — no stretching, no overflow
  2. "Falken's Mage" appears in Cinzel display weight with the ambient glow pulse active (and suppressed when `prefers-reduced-motion` is set)
  3. All 8 social platform links are present, tappable at 44px minimum, and show ARCÆON glow on hover
  4. The "Work With Me" mailto button fires an email client when tapped; Radiant Core glow (Fusion Gold → Ignition Orange) is visible
  5. Footer reads "Stay feral, folks." with Digital Intuition LLC copyright and lemniscate decorative mark
**Plans**: 3 plans
Plans:
- [x] 02-01-PLAN.md — Content data + Hero section + Identity+CTA section
- [x] 02-02-PLAN.md — Social links (SVG icons + grid) + Footer + index.html wiring
- [x] 02-03-PLAN.md — Validation script + visual checkpoint
**UI hint**: yes

### Phase 3: Dynamic Layer + Quality
**Goal**: The site is complete, fast, accessible, and search-legible — the "Currently" section pulls live Substack content, and every cross-cutting quality requirement is satisfied.
**Depends on**: Phase 2
**Requirements**: CURR-01, CURR-02, CURR-03, PERF-01, PERF-02, PERF-03, PERF-04, A11Y-01, A11Y-02, A11Y-03, A11Y-04, SEO-01, SEO-02, SEO-03
**Success Criteria** (what must be TRUE):
  1. "Currently" section displays the latest Feral Architecture post title + link, fetched from Substack RSS at build time — and shows static fallback content when RSS is unreachable
  2. Page loads in under 1 second on a simulated 3G connection (Lighthouse or WebPageTest)
  3. Hero image serves WebP with JPEG fallback; below-fold images lazy-load; no external font CDNs or analytics scripts in network tab
  4. WCAG AA contrast passes for all text/background pairs (neon accents decoration-only, body text in Solar White/Ion Glow)
  5. Sharing the URL on social surfaces the Magus image, "Falken's Mage — Matt Stine" title, and identity meta description via Open Graph and Twitter Card
**Plans**: 2 plans
Plans:
- [x] 03-01-PLAN.md — Currently section partial + landmarks + font preload infrastructure
- [x] 03-02-PLAN.md — SEO/OG meta tags + validation script + visual checkpoint
**UI hint**: yes

### Phase 4: Production Deploy
**Goal**: falkensmage.com is live, HTTPS, deploying automatically from `main`, with the custom domain persisting across every deploy.
**Depends on**: Phase 3
**Requirements**: INFRA-03, INFRA-04, INFRA-05
**Success Criteria** (what must be TRUE):
  1. Pushing to `main` triggers the GitHub Actions workflow; Hugo Extended 0.160.1 builds and deploys to GitHub Pages without manual intervention
  2. `https://falkensmage.com` loads the site with valid HTTPS — no certificate warnings, no redirect loops
  3. The lemniscate sigil favicon appears in browser tabs and bookmark lists (`.ico` + `.svg` both present)
  4. Custom domain survives a deploy cycle — `static/CNAME` file present and GitHub Pages custom domain setting intact after push
**Plans**: 2 plans
Plans:
- [x] 04-01-PLAN.md — Favicon (SVG + ICO) + CNAME + GitHub Actions workflow
- [x] 04-02-PLAN.md — Repo creation, push, DNS configuration + live verification
**UI hint**: no

### Phase 5: v1.0 Gap Closure
**Goal**: All v1.0 audit gaps closed — Phase 3 quality defects fixed, tech debt eliminated, and SUMMARY frontmatter traceability restored so the milestone can be archived cleanly.
**Depends on**: Phase 3, Phase 4
**Requirements**: A11Y-01, PERF-01, PERF-03
**Gap Closure**: Closes gaps from `.planning/v1.0-MILESTONE-AUDIT.md`
**Success Criteria** (what must be TRUE):
  1. Built HTML contains exactly one `<footer>` landmark — no nested footer elements
  2. Fonts are fetched exactly once per face — preload href matches the resolved `@font-face` src from `css.Build`
  3. `validate-phase-03.sh` reports 33/33 with no false failures on SEO-03 canonical check
  4. CI workflow is internally consistent — either `npm ci` wires fontsource → assets/fonts during build, or `npm ci` is removed and committed WOFF2 files are the intentional source of truth
  5. Every v1.0 REQ-ID appears in `requirements_completed` frontmatter of at least one SUMMARY.md across Phases 1–4
**Plans**: 3 plans
Plans:
- [x] 05-01-PLAN.md — Wave 1 code fixes: remove nested footer, add css.Build externals, delete duplicate assets/fonts/
- [x] 05-02-PLAN.md — Wave 2 hygiene + backfill: patch validate-phase-03.sh, remove npm ci, add requirements-completed to 4 SUMMARYs
- [x] 05-03-PLAN.md — Wave 3 verification + traceability flip in REQUIREMENTS.md
**UI hint**: no

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Theme Foundation | 3/3 | Complete   | 2026-04-16 |
| 2. Static Content | 3/3 | Complete   | 2026-04-16 |
| 3. Dynamic Layer + Quality | 2/2 | Complete   | 2026-04-17 |
| 4. Production Deploy | 2/2 | Complete   | 2026-04-17 |
| 5. v1.0 Gap Closure | 3/3 | Complete    | 2026-04-17 |
