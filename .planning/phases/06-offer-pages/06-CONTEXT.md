# Phase 6: Offer Pages - Context

**Gathered:** 2026-07-01
**Status:** Ready for planning
**Source:** RESUME handoff build spec (`.planning/RESUME.md`) + canonical offer architecture (`~/.psyche/hermetic/offer-architecture.md`)

<domain>
## Phase Boundary

Turn falkensmage.com from a single-page front door into a **linkable commerce surface** — offer pages sellable from anywhere (social, podcast, DMs), not just an email CTA.

**In scope:**
- A new Hugo `/work/` section: a "Work With Me" hub plus three individual offer pages.
- Repointing the homepage secondary CTA from a bare `mailto:` to the `/work/` hub.
- Centralizing Cal.com booking URLs as single-source-of-truth config (placeholders now, swapped in one place later).

**Out of scope (do NOT build):**
- No embedded booking widget or checkout script — CTAs LINK OUT to Cal.com only.
- No new design language — compose exclusively from the existing `arcaeon` system.
- No Cal.com account/event-type setup — URLs are placeholders this phase (OFFER-F1 defers the live swap).
- The Construct membership (sells via Substack, not this site) and Systeme.io (list+send only).
</domain>

<decisions>
## Implementation Decisions

### Section structure (`/work/`)
- Create `content/work/_index.md` — the **hub**: short framing + three offer cards, each linking to its offer page.
- Create `content/work/the-query.md`, `content/work/the-cast.md`, `content/work/the-daemon.md` — one page per offer.
- Add a section layout under `themes/arcaeon/layouts/work/` — follow the `kitchen-sink/single.html` composition pattern on the `_default/baseof.html` shell. (List template for the hub, single template for offer pages, as the section requires.)

### The offers (canonical — do not alter price/shape/CTA)
| Page | Offer | Price / shape | CTA |
|---|---|---|---|
| the-query | Archetypal **Tarot** reading | $250 / 90 min | "Book & Pay" → Cal.com |
| the-cast | Archetypal **Astrology** reading | $325 / 90 min | "Book & Pay" → Cal.com |
| the-daemon | 6-month Hermetic coaching | $4,500 (consult-gated) | "Book a Clarity Consult ($150, credited)" → Cal.com |

- The Daemon's CTA is **consult-gated** — it books a $150 clarity consult (credited toward the engagement), NOT a direct $4,500 buy.
- Language note (project memory): the tarot offer is an **archetypal tarotist** reading and the practitioner framing is **chaos witch** — never "tarot reader" / "chaos magician."

### Voice
- Match the homepage register in `content/_index.md`: direct, technomagickal, lightly profane — "one technomagickal motherfucker," "if that made you flinch, we're probably not a fit," "Stay feral, folks."
- Each offer page is a **voiced pitch**, not a spec sheet. Sell the transformation; the price/shape is a detail inside the pitch.

### Cal.com config (single source of truth) — OFFER-05
- Centralize the three booking URLs in ONE place — `hugo.toml [params]` (e.g. a `[params.booking]` table) is the default; a `data/booking.toml` file is an acceptable alternative if the planner prefers data-driven lookup.
- Values are **PLACEHOLDER** Cal.com URLs this phase, swapped in one location when Cal.com event types exist. Templates reference the config key, never a hardcoded URL.

### Homepage CTA repoint — NAV-01
- `content/_index.md` front matter `cta_secondary` (currently a raw-HTML `mailto:falkensmage@falkenslabyrinth.com` string at ~line 22) → repoint to the `/work/` hub. Preserve the existing front-matter shape; change the target, not the mechanism.

### Design — compose ONLY from the existing `arcaeon` system
- ARCÆON palette CSS custom properties; Cinzel (display) + Space Grotesk (body), self-hosted.
- `.section-void` / `.section-depth` alternation between sections; **Triad Rule** — one purple + one blue + one warm accent per section.
- `.glow-radiant-core` for the CTA buttons — see `themes/arcaeon/layouts/partials/sections/identity-cta.html` for the established CTA pattern.
- Sigil decorations (`.sigil-arc`, `.sigil-gradient`); pseudo-element convention: `::before` = glow, `::after` = sigil.
- `content/kitchen-sink.md` + its layout demo every token/component — the reuse source of truth.

### Claude's Discretion
- Exact per-page section count and markup, hub card layout, and how offer front matter is modeled (front-matter fields vs. body prose).
- The precise config key names and whether to use `hugo.toml [params]` vs `data/booking.toml`.
- Whether the offer pages share one `single.html` or use per-page front-matter-driven variation.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design system (reuse source — no new design language)
- `content/kitchen-sink.md` — demos every ARCÆON token/component; the reuse catalog.
- `themes/arcaeon/layouts/kitchen-sink/single.html` — layout composition pattern to follow for `/work/` templates.
- `themes/arcaeon/layouts/_default/baseof.html` — the page shell all templates extend.
- `themes/arcaeon/layouts/partials/sections/identity-cta.html` — the established Radiant-Core CTA button pattern.

### Content + config to modify
- `content/_index.md` — homepage front matter; `cta_secondary` (~line 22) is repointed for NAV-01; also the voice reference for the offer pitches.
- `hugo.toml` — `[params]` block (line 6) is where Cal.com booking config is centralized (OFFER-05).

### Offer architecture (external canonical, outside repo)
- `~/.psyche/hermetic/offer-architecture.md` — canonical prices/shapes/CTAs and the interim commerce architecture (Cal.com = interim checkout via Matt's Stripe; Sigil & Thread replaces it later, inherits the same rail). These pages are future source material for the S&T-rendered site.
</canonical_refs>

<specifics>
## Specific Ideas

- Cal.com is the interim checkout: book + pay-at-booking via Matt's own Stripe. The link-out (not a widget) is exactly how the sub-1s / 3G / zero-external-dependency budget is preserved.
- The hub framing is short — this is a front door to the offers, not a services essay.
</specifics>

<deferred>
## Deferred Ideas

- **OFFER-F1** — swap placeholder Cal.com URLs for live event-type booking links once Cal.com is stood up.
- **OFFER-F2** — offer pages become source material for the Sigil & Thread-rendered version of the site.
</deferred>

---

## Constraints (v1.0 budgets HELD — OFFERQ-01 / OFFERQ-02)

- CTAs LINK OUT to Cal.com — **no** embedded widget/script, **no** external deps / CDN / JS.
- Mobile-first 375px, WCAG AA, self-hosted fonts only.
- Clean `hugo --minify` build.

## Success Criteria (from ROADMAP Phase 6)

1. `/work/` hub renders and links to all three offers.
2. Each offer page renders with correct pitch/price/CTA and a working Cal.com link-out.
3. Homepage secondary CTA points to `/work/`.
4. Cal.com URLs centralized as swappable config.
5. `hugo --minify` builds clean; budgets hold (no external deps, WCAG AA, mobile-first).

---

*Phase: 06-offer-pages*
*Context captured 2026-07-01 from RESUME handoff build spec (lean path — UI-SPEC and research skipped; design is pure `arcaeon` reuse, phase is well-understood Hugo section scaffolding).*
