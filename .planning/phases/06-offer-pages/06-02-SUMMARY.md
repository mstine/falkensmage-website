---
phase: 06-offer-pages
plan: 02
subsystem: content
tags: [hugo, arcaeon, content, offer-pages, voice]

# Dependency graph
requires:
  - phase: 06-offer-pages
    provides: "[params.booking] config table in hugo.toml, themes/arcaeon/layouts/work/single.html, themes/arcaeon/layouts/work/list.html (Plan 06-01)"
provides:
  - "content/work/_index.md — the /work/ hub front-door framing"
  - "content/work/the-query.md — voiced tarot offer pitch ($250/90-min)"
  - "content/work/the-cast.md — voiced astrology offer pitch ($325/90-min)"
  - "content/work/the-daemon.md — voiced 6-month coaching pitch ($4,500, consult-gated)"
affects: [06-03]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Offer content is pure front matter + markdown body — no card markup, no hardcoded booking URLs; all structured fields (price/duration/cta_text/booking_key) consumed by Plan 06-01's templates"

key-files:
  created:
    - content/work/_index.md
    - content/work/the-query.md
    - content/work/the-cast.md
    - content/work/the-daemon.md

key-decisions:
  - "Hub body kept to 2 sentences (well under the ~4-sentence budget) — front door, not an essay; no CTA link in hub body since cards are the navigation"
  - "The Daemon's duration field omitted entirely (not set to null/empty string) so the single.html template's {{ with .Params.duration }} guard correctly suppresses the '/ 90 minutes' fragment for a 6-month container"
  - "Practitioner framing varied naturally per offer — 'archetypal tarotist' for The Query, 'chaos witch and astrologer' for The Cast — matching the homepage identity block's three-part framing (archetypal tarotist, astrologer, chaos witch) rather than mechanically repeating one label everywhere"

patterns-established:
  - "Voiced offer pitch structure: open with the transformation/tension, name the practitioner framing plainly, describe the mechanics in prose without restating front-matter fields as spec-sheet text, close with a direct invitation"

requirements-completed: [OFFER-01, OFFER-02, OFFER-03, OFFER-04]

coverage:
  - id: D1
    description: "content/work/_index.md hub renders a short voiced framing and (via work/list.html) lists all three offers as cards"
    requirement: "OFFER-01"
    verification:
      - kind: other
        ref: "rm -rf public/ resources/_gen/ && hugo --minify --quiet; test -f public/work/index.html; grep -Eic 'tarot reader|chaos magician' content/work/_index.md == 0; manual inspection of public/work/index.html social-grid confirms 3 cards (The Query/$250, The Cast/$325, The Daemon/$4,500)"
        status: pass
    human_judgment: false
  - id: D2
    description: "content/work/the-query.md renders as a voiced 90-min archetypal tarot pitch, $250, 'Book & Pay' CTA resolving to booking_key the-query"
    requirement: "OFFER-02"
    verification:
      - kind: other
        ref: "hugo --minify --quiet; grep '\\$250' public/work/the-query/index.html; grep 'Book & Pay' public/work/the-query/index.html; grep -o 'href=https://cal.com/[^ >]*' public/work/the-query/index.html == https://cal.com/PLACEHOLDER/the-query"
        status: pass
    human_judgment: false
  - id: D3
    description: "content/work/the-cast.md renders as a voiced 90-min archetypal astrology pitch, $325, 'Book & Pay' CTA resolving to booking_key the-cast"
    requirement: "OFFER-03"
    verification:
      - kind: other
        ref: "hugo --minify --quiet; grep '\\$325' public/work/the-cast/index.html; grep -o 'href=https://cal.com/[^ >]*' public/work/the-cast/index.html == https://cal.com/PLACEHOLDER/the-cast"
        status: pass
    human_judgment: false
  - id: D4
    description: "content/work/the-daemon.md renders as a voiced 6-month coaching pitch, $4,500, duration omitted, consult-gated CTA 'Book a Clarity Consult ($150, credited)' resolving to booking_key the-daemon"
    requirement: "OFFER-04"
    verification:
      - kind: other
        ref: "hugo --minify --quiet; grep '\\$4,500' public/work/the-daemon/index.html; grep -qE '150.*credit|credit.*150|Clarity Consult' public/work/the-daemon/index.html; grep -o 'href=https://cal.com/[^ >]*' public/work/the-daemon/index.html == https://cal.com/PLACEHOLDER/the-daemon-consult; manual read of body confirms $150-credited gate is legible, not a direct $4,500 buy"
        status: pass
    human_judgment: false
  - id: D5
    description: "Language rule held: no 'tarot reader' / 'chaos magician' anywhere in content/work/*.md; no hardcoded cal.com URLs in content"
    verification:
      - kind: other
        ref: "grep -Eic 'tarot reader|chaos magician' content/work/*.md == 0 (each file); grep -Ec 'cal\\.com' content/work/*.md == 0 (each file)"
        status: pass
    human_judgment: false

# Metrics
duration: 3min
completed: 2026-07-01
status: complete
---

# Phase 6 Plan 2: Offer Pages Content Summary

**Four voiced content files — the `/work/` hub plus The Query ($250 tarot), The Cast ($325 astrology), and The Daemon ($4,500 consult-gated coaching) — rendering through Plan 06-01's templates with zero hardcoded booking URLs.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-07-01T19:25:00-05:00
- **Completed:** 2026-07-01T19:28:26-05:00
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- Wrote `content/work/_index.md` — a two-sentence front-door framing naming the three ways to work together, with no card markup (cards are template-generated by `work/list.html`) and no CTA link in the body.
- Wrote `content/work/the-query.md` — a voiced pitch for the 90-minute archetypal tarot reading ($250), framing the practitioner as an archetypal tarotist reading cards the way a legacy codebase gets read: for the load-bearing pattern underneath the surface.
- Wrote `content/work/the-cast.md` — a voiced pitch for the 90-minute archetypal astrology reading ($325), framing the chart as a psyche-architecture map rather than a horoscope, practitioner voiced as chaos witch/astrologer.
- Wrote `content/work/the-daemon.md` — a voiced pitch for the 6-month Hermetic coaching container ($4,500), with `duration` deliberately omitted and the $150-credited Clarity Consult gate made explicit in the closing paragraph so the CTA reads as intended (not a direct $4,500 buy).
- Verified end-to-end via `hugo --minify`: hub renders all three cards by weight with correct price/summary; each offer page renders correct price, correct CTA text, and a CTA href resolving to its `booking_key`'s placeholder Cal.com URL (`the-query`, `the-cast`, `the-daemon-consult`) — confirming the content-to-template contract from Plan 06-01 holds with zero hardcoded URLs in content.

## Task Commits

Each task was committed atomically:

1. **Task 1: Write the /work/ hub content content/work/_index.md (OFFER-01)** - `bf9533f` (feat)
2. **Task 2: Write The Query + The Cast reading pages (OFFER-02, OFFER-03)** - `97d8951` (feat)
3. **Task 3: Write The Daemon consult-gated coaching page (OFFER-04)** - `dd4e855` (feat)

## Files Created/Modified
- `content/work/_index.md` - Work-With-Me hub: title + 2-sentence framing body
- `content/work/the-query.md` - The Query offer: front matter (offer_name/price/duration/cta_text/booking_key/summary/weight) + voiced tarot pitch body
- `content/work/the-cast.md` - The Cast offer: front matter + voiced astrology pitch body
- `content/work/the-daemon.md` - The Daemon offer: front matter (duration omitted) + voiced coaching pitch body with legible $150-credited consult gate

## Decisions Made
- Hub body kept to 2 sentences (plan allowed up to ~4) — the front-door instinct from 06-CONTEXT.md ("short framing, not a services essay") favored tighter over looser.
- The Daemon's `duration` field was omitted entirely from front matter (not set to an empty value) so `single.html`'s `{{ with .Params.duration }}` guard cleanly suppresses the "/ 90 minutes" fragment, confirmed in the rendered hero: `<p>$4,500</p>` with no duration suffix.
- Practitioner framing varied per offer to match the homepage's own three-part identity language ("archetypal tarotist, astrologer, and chaos witch") rather than mechanically repeating a single label across all three pages — The Query leads with "archetypal tarotist," The Cast leads with "chaos witch and astrologer."

## Deviations from Plan

None - plan executed exactly as written. All four front-matter/body contracts match the canonical offers table in 06-CONTEXT.md and 06-02-PLAN.md exactly (price, duration presence/absence, cta_text, booking_key, weight).

## Issues Encountered

None. One local verification-script quirk worth noting for future plans: the plan's inline verify command `[ "$(grep -Eic 'pattern' file1 file2)" -eq 0 ]` breaks when grep is given multiple files, because `grep -c` with 2+ files prints one `file:count` line per file (e.g. `content/work/the-cast.md:0\ncontent/work/the-query.md:0`) rather than a single integer — the `-eq` comparison then fails on the multi-line string, not on the actual content. Verified manually by running `grep -Eic ... file` per-file instead; all returned `0` as intended. No content or template change was needed — this is a verification-script portability note, not a deviation from plan content.

## User Setup Required

None - no external service configuration required. Cal.com URLs remain PLACEHOLDER values by design (OFFER-F1 defers the live swap to a later phase, unchanged from Plan 06-01).

## Next Phase Readiness

- All four OFFER-0{1,2,3,4} requirements are satisfied: hub + three offer pages render clean through `hugo --minify` with correct prices, correct CTA text, and CTA targets resolving via `booking_key` (no hardcoded Cal.com URLs anywhere in `content/work/*.md`).
- Language rule held throughout: zero occurrences of "tarot reader" or "chaos magician" across all four new content files.
- Plan 06-03 (homepage CTA repoint to `/work/` hub, per NAV-01) can now proceed — the `/work/` hub exists and is a valid link target.
- No blockers.

---
*Phase: 06-offer-pages*
*Completed: 2026-07-01*

## Self-Check: PASSED

All four created files confirmed present on disk (`content/work/_index.md`, `content/work/the-query.md`, `content/work/the-cast.md`, `content/work/the-daemon.md`). All three task commit hashes (`bf9533f`, `97d8951`, `dd4e855`) confirmed in `git log`.
