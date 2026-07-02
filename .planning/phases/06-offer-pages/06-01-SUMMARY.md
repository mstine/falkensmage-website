---
phase: 06-offer-pages
plan: 01
subsystem: templates
tags: [hugo, arcaeon, cal.com, config, templates]

# Dependency graph
requires: []
provides:
  - "Single-source-of-truth [params.booking] Cal.com config table in hugo.toml (placeholder URLs)"
  - "themes/arcaeon/layouts/work/single.html — offer-page template (hero/pitch/CTA, config-driven link-out)"
  - "themes/arcaeon/layouts/work/list.html — /work/ hub template (framing + offer cards)"
affects: [06-02, 06-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Config-driven external CTA: templates dereference index site.Params.booking .Params.booking_key — never a literal URL"
    - "Section alternation (D-11) + Triad Rule applied via existing section-void/section-depth CSS custom property overrides, no new tokens"

key-files:
  created:
    - themes/arcaeon/layouts/work/single.html
    - themes/arcaeon/layouts/work/list.html
  modified:
    - hugo.toml

key-decisions:
  - "Cal.com config lives in hugo.toml [params.booking] (not a separate data/booking.toml) — simplest single-source location, matches existing [params.colors] sibling-table convention"
  - "Hub cards reuse social-grid/social-card (2/3/4-col grid, ghost-card hover) rather than currently-card — three offers read better as a grid than a stacked single-card list"
  - "CTA anchor guarded with {{ with index site.Params.booking .Params.booking_key }} so a missing/mistyped booking_key silently omits the CTA rather than emitting a broken empty href"

patterns-established:
  - "Single-source external-link config: any future link-out target should live in one [params.*] table, dereferenced by key from templates — never hardcoded"

requirements-completed: [OFFER-05]

coverage:
  - id: D1
    description: "[params.booking] table in hugo.toml with placeholder URLs for the-query/the-cast/the-daemon"
    requirement: "OFFER-05"
    verification:
      - kind: other
        ref: "hugo config | grep -iA4 booking (three keys present, values are https://cal.com/PLACEHOLDER/* placeholders)"
        status: pass
    human_judgment: false
  - id: D2
    description: "work/single.html renders a three-section offer page with a config-driven, budget-safe Radiant-Core CTA"
    requirement: "OFFERQ-01"
    verification:
      - kind: other
        ref: "grep assertions (glow-radiant-core, index .*[Bb]ooking, rel=\"noopener) + manual hugo build render with test front matter, confirmed CTA href resolves to the correct placeholder URL"
        status: pass
    human_judgment: false
  - id: D3
    description: "work/list.html renders the hub framing and ranges offer pages into cards linking to each offer"
    requirement: "OFFERQ-01"
    verification:
      - kind: other
        ref: "grep assertions (range .Pages, RelPermalink, .Content) + manual hugo build render with two test offer pages, confirmed hub lists both by weight and excludes itself"
        status: pass
    human_judgment: false
  - id: D4
    description: "hugo --minify builds clean with the new plumbing present"
    verification:
      - kind: other
        ref: "rm -rf public/ resources/_gen/ && hugo --minify --quiet (exit 0)"
        status: pass
    human_judgment: false

# Metrics
duration: 6min
completed: 2026-07-01
status: complete
---

# Phase 6 Plan 1: Offer Plumbing Summary

**Single-source `[params.booking]` Cal.com config in hugo.toml plus two arcaeon-native `/work/` templates (hub list + offer single) whose CTAs are structurally forced to dereference the config key instead of a hardcoded URL.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-07-01T19:22:00-05:00
- **Completed:** 2026-07-01T19:23:24-05:00
- **Tasks:** 3
- **Files modified:** 3

## Accomplishments
- Centralized the three Cal.com booking URLs (the-query, the-cast, the-daemon) as placeholders in one `[params.booking]` table — a future live-URL swap (OFFER-F1) is a three-line edit in one place.
- Built `themes/arcaeon/layouts/work/single.html`: a three-section (hero / pitch / CTA) offer-page template, alternating `section-void`/`section-depth` (D-11), composed only from existing arcaeon classes. The CTA anchor's href is guarded and resolved via `{{ with index site.Params.booking .Params.booking_key }}`, carries `glow-radiant-core`, `target="_blank"`, `rel="noopener noreferrer"` — no booking-provider URL literal anywhere in the template.
- Built `themes/arcaeon/layouts/work/list.html`: the `/work/` hub template — a framing section rendering `_index.md`'s `.Content`, and an offers section ranging `.Pages.ByWeight` into `social-card` cards linking via `.RelPermalink` (internal nav, no `target="_blank"`), surfacing `offer_name`/title/price/summary per offer.
- Verified end-to-end with temporary test content pages (not committed): confirmed the single template resolves the correct placeholder Cal.com URL from config, and the hub correctly lists offer pages by weight while excluding itself. Both templates render clean through `hugo --minify --quiet`.

## Task Commits

Each task was committed atomically:

1. **Task 1: Add [params.booking] single-source config to hugo.toml (OFFER-05)** - `1065349` (feat)
2. **Task 2: Build the offer-page template themes/arcaeon/layouts/work/single.html** - `47a1f88` (feat)
3. **Task 3: Build the hub template themes/arcaeon/layouts/work/list.html (OFFER-01)** - `0595da8` (feat)

## Files Created/Modified
- `hugo.toml` - Added `[params.booking]` table (three placeholder Cal.com URLs) between the top-level `[params]` keys and `[params.colors]`
- `themes/arcaeon/layouts/work/single.html` - Offer-page template: hero (offer_name/title/price+duration), pitch (`.Content`), CTA (config-driven `glow-radiant-core` link-out)
- `themes/arcaeon/layouts/work/list.html` - `/work/` hub template: framing (`.Title`/`.Content`) + offer cards (`social-grid`/`social-card`, `.RelPermalink`)

## Decisions Made
- Config location: `hugo.toml [params.booking]` chosen over a separate `data/booking.toml` — matches the existing `[params.colors]` sibling-table convention already in the file, no new file type introduced.
- Hub card visual: `social-grid` + `social-card` chosen over `currently-card` — three offer cards read better as a compact grid (matches the existing social-links section's visual grammar) than a single stacked ghost card.
- CTA guard: wrapped the anchor in `{{ with index site.Params.booking .Params.booking_key }}` so a missing or mistyped `booking_key` in a future content page silently omits the CTA rather than rendering a broken `href=""` — a defensive addition beyond the letter of the plan but directly serving the plan's own stated intent ("Guard the CTA so a missing `booking_key`... does not emit a broken empty href").

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None. Content pages don't exist yet (authored in Plan 06-02), so `/work/` does not render into `public/` from committed content — this matches the plan's own note ("`/work/` pages will not render into `public/` until Plan 06-02 supplies content; this plan verifies the config + template artifacts and a clean build"). Verified template correctness by creating temporary, uncommitted test content pages during Task 2/3 verification, then removing them before each commit — `git status --short` confirmed no stray files were left in the working tree.

## User Setup Required

None - no external service configuration required. Cal.com URLs remain PLACEHOLDER values by design (OFFER-F1 defers the live swap to a later phase).

## Next Phase Readiness

- Config and templates are in place and structurally enforce OFFERQ-01 (design-system reuse only) and OFFERQ-02 (link-out, zero external deps) — Plan 06-02 (content authoring) cannot violate these budgets through the render path.
- Plan 06-02 can now author `content/work/_index.md`, `content/work/the-query.md`, `content/work/the-cast.md`, `content/work/the-daemon.md` against the documented front-matter contract (`title`, `offer_name`, `price`, `duration`, `cta_text`, `booking_key`, `summary`, `weight`) and the voiced-pitch markdown body.
- No blockers.

---
*Phase: 06-offer-pages*
*Completed: 2026-07-01*

## Self-Check: PASSED

All created/modified files confirmed present on disk; all three task commit hashes confirmed in `git log --all`.
