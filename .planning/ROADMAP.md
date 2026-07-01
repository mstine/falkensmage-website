# Roadmap: falkensmage.com

## Milestones

- ✅ **v1.0 MVP** — Phases 1–5 (shipped 2026-04-17) — [archive](./milestones/v1.0-ROADMAP.md)
- 🔨 **v1.1 Offer Pages** — Phase 6 (scoped 2026-07-01)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1–5) — SHIPPED 2026-04-17</summary>

- [x] Phase 1: Theme Foundation (3/3 plans) — completed 2026-04-16
- [x] Phase 2: Static Content (3/3 plans) — completed 2026-04-16
- [x] Phase 3: Dynamic Layer + Quality (2/2 plans) — completed 2026-04-17
- [x] Phase 4: Production Deploy (2/2 plans) — completed 2026-04-17
- [x] Phase 5: v1.0 Gap Closure (3/3 plans) — completed 2026-04-17

Full details: [milestones/v1.0-ROADMAP.md](./milestones/v1.0-ROADMAP.md)

</details>

### 🔨 v1.1 Offer Pages — scoped 2026-07-01

- [ ] **Phase 6: Offer Pages** (0/3 plans) — `/work/` hub + The Query / The Cast / The Daemon offer pages with Cal.com link-out CTAs; homepage secondary CTA repointed to `/work/`.

### Phase 6: Offer Pages

**Goal:** Turn falkensmage.com into a linkable commerce surface — offer pages sellable from anywhere (social, podcast, DMs), not just email. Ships a `/work/` hub plus The Query / The Cast / The Daemon offer pages with Cal.com link-out CTAs, and repoints the homepage secondary CTA to `/work/`. Composes only from the existing `arcaeon` design system; holds v1.0 perf/a11y budgets.
**Depends on:** Phase 5 (v1.0 shipped)
**Requirements:** OFFER-01, OFFER-02, OFFER-03, OFFER-04, OFFER-05, NAV-01, OFFERQ-01, OFFERQ-02
**Plans:** 3 plans

Plans:
- [ ] 06-01-PLAN.md — Cal.com booking config (single-source) + `/work/` section templates (hub list + offer single)
- [ ] 06-02-PLAN.md — `/work/` hub content + The Query / The Cast / The Daemon voiced offer pages
- [ ] 06-03-PLAN.md — Homepage secondary CTA repoint to `/work/` + Phase 6 validation script + clean-build check

**Success Criteria**:
1. `/work/` hub renders and links to all three offers.
2. Each offer page renders with correct pitch/price/CTA and a working Cal.com link-out.
3. Homepage secondary CTA points to `/work/`.
4. Cal.com URLs centralized as swappable config.
5. `hugo --minify` builds clean and budgets hold (no external deps, WCAG AA, mobile-first).

Next: `/gsd-plan-phase 6` to plan execution.

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Theme Foundation | v1.0 | 3/3 | Complete | 2026-04-16 |
| 2. Static Content | v1.0 | 3/3 | Complete | 2026-04-16 |
| 3. Dynamic Layer + Quality | v1.0 | 2/2 | Complete | 2026-04-17 |
| 4. Production Deploy | v1.0 | 2/2 | Complete | 2026-04-17 |
| 5. v1.0 Gap Closure | v1.0 | 3/3 | Complete | 2026-04-17 |
| 6. Offer Pages | v1.1 | 0/? | Planning | — |
