# RESUME — Phase 6: Offer Pages (v1.1)

**Written:** 2026-07-01 · Handoff from a psyche-ws session to a session rooted in this repo.

## Where things stand

- **v1.1 milestone is SCOPED and COMMITTED** — commit `a5edf76` ("docs: start milestone v1.1 Offer Pages").
  - `PROJECT.md` — Current Milestone: v1.1; two v1.0 Out-of-Scope items consciously reversed (offer *pages* now in scope; single-page → multi-page).
  - `REQUIREMENTS.md` — OFFER-01…05, NAV-01, OFFERQ-01…02 (8 reqs, all mapped to Phase 6).
  - `ROADMAP.md` — Phase 6 entry (human-readable).
  - `STATE.md` — milestone flipped to v1.1 / planning via GSD handler.

## ⚠ Do this FIRST in the new session

`node .../gsd-tools.cjs query init.plan-phase 6` returns **`phase_found: false`** — the Phase 6 entry was hand-written into ROADMAP.md and the `roadmap.get-phase` parser doesn't resolve it (normally the roadmapper subagent writes the machine-readable form). **Fix before planning:** re-register Phase 6 via the roadmapper (re-run the roadmap step) or `/gsd-phase` to add it in the parser-recognized format, then confirm `roadmap.get-phase 6` resolves. THEN `/gsd-plan-phase 6`.

(Why this got handed off: plan-phase requires independent planner/checker subagents; GSD returns repo-relative paths, so subagents spawned from the psyche-ws session resolved `.planning/` against the wrong repo. Running in-repo fixes it. The milestone step was safe to drive remotely because no subagent touched `.planning/`.)

## Phase 6 build spec (zero re-derivation for the planner)

**Goal:** Turn falkensmage.com into a linkable commerce surface — offer pages sellable from anywhere (social, podcast, DMs), not just email.

**Deliverables:**
- New Hugo `/work/` section:
  - `content/work/_index.md` — "Work With Me" **hub**: short framing + 3 offer cards linking to each page.
  - `content/work/the-query.md`, `content/work/the-cast.md`, `content/work/the-daemon.md` — individual offer pages.
  - Section layout under `themes/arcaeon/layouts/work/` — follow the `kitchen-sink/single.html` pattern + `_default/baseof.html` shell.
- Homepage: repoint `content/_index.md` front-matter `cta_secondary` from the bare `mailto:falkensmage@falkenslabyrinth.com` to the `/work/` hub.
- Centralize Cal.com booking URLs as **single-source-of-truth config** (e.g. `hugo.toml [params]` or a `data/` file) — they are PLACEHOLDERS now, swapped in one place when Cal.com event types exist.

**The offers (canonical: `~/.psyche/hermetic/offer-architecture.md`):**
| Page | Offer | Price / shape | CTA |
|---|---|---|---|
| the-query | Archetypal **Tarot** reading | $250 / 90 min | "Book & Pay" → Cal.com |
| the-cast | Archetypal **Astrology** reading | $325 / 90 min | "Book & Pay" → Cal.com |
| the-daemon | 6-mo Hermetic coaching | $4,500 (consult-gated) | "Book a Clarity Consult ($150, credited)" → Cal.com |

**Voice:** match the homepage register (`content/_index.md` — "one technomagickal motherfucker," direct, "if that made you flinch, we're probably not a fit," "Stay feral, folks."). Voiced pitch per offer; not a spec sheet.

**Design — compose ONLY from the existing `arcaeon` system (no new design language):**
- ARCÆON palette CSS vars, Cinzel (display) + Space Grotesk (body).
- `.section-void` / `.section-depth` alternation; Triad Rule (one purple + one blue + one warm per section).
- `.glow-radiant-core` for the CTA buttons (see `themes/arcaeon/layouts/partials/sections/identity-cta.html` for the CTA pattern; `content/kitchen-sink.md` demos every token/component).
- Sigil decorations (`.sigil-arc`, `.sigil-gradient`); `::before` = glow, `::after` = sigil convention.

**Constraints (v1.0 budgets HELD — OFFERQ-01/02):**
- CTAs **LINK OUT** to Cal.com — NO embedded widget/script. No external deps/CDN/JS. This is how sub-1s/3G is preserved.
- Mobile-first 375px, WCAG AA, self-hosted fonts only. Clean `hugo --minify` build.

## Interim commerce architecture (context)

Cal.com (book + pay-at-booking via Matt's own Stripe) is the interim checkout; The Construct membership sells via Substack (not on this site); Systeme.io is list+send only. Sigil & Thread later replaces Cal.com and inherits the same Stripe rail. These pages are also future source material for the S&T-rendered version of the site. Full detail: `~/.psyche/hermetic/offer-architecture.md` (Interim checkout bridge block).

## Success criteria (from ROADMAP Phase 6)

1. `/work/` hub renders and links to all three offers.
2. Each offer page renders with correct pitch/price/CTA and a working Cal.com link-out.
3. Homepage secondary CTA points to `/work/`.
4. Cal.com URLs centralized as swappable config.
5. `hugo --minify` builds clean; budgets hold (no external deps, WCAG AA, mobile-first).
