---
phase: 06-offer-pages
plan: 03
subsystem: testing
tags: [hugo, arcaeon, nav, validation, regression-gate]

# Dependency graph
requires:
  - phase: 06-offer-pages
    provides: "[params.booking] config table in hugo.toml, themes/arcaeon/layouts/work/single.html, themes/arcaeon/layouts/work/list.html (Plan 06-01); content/work/_index.md, the-query.md, the-cast.md, the-daemon.md (Plan 06-02)"
provides:
  - "content/_index.md homepage secondary CTA repointed from mailto: to the /work/ hub (NAV-01)"
  - "tests/validate-phase-06.sh — 32-check automated acceptance regression gate for all eight Phase 6 requirement IDs"
  - "tests/validate-phase-02.sh CTA-02 check updated to reflect the intentional NAV-01 mailto->/work/ repoint"
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "count_matches/count_matches_ci helpers (grep -hoE ... | wc -l) for multi-file occurrence counting — avoids the grep -c per-file-count and grep -c-plus-|| double-zero portability bugs"
    - "href_has helper tolerant of Hugo minifier's unquoted-attribute output (href=/work/ vs href=\"/work/\")"

key-files:
  created:
    - tests/validate-phase-06.sh
  modified:
    - content/_index.md
    - tests/validate-phase-02.sh

key-decisions:
  - "cta_secondary anchor text changed from the raw email address to a voiced work-together invite (\"See how we can work together\") linking to /work/ — mechanism (safeHTML front-matter string) and internal-nav convention (no target=_blank) both preserved unchanged"
  - "tests/validate-phase-02.sh CTA-02 assertion narrowed to glow-radiant-core only (dropping the now-permanently-false mailto:falkensmage@falkenslabyrinth.com assertion), with a comment pointing to validate-phase-06.sh's NAV-01 check for the superseding coverage"
  - "OFFERQ-02's four-part budget (sub-1s/3G, zero-dep, mobile-first, WCAG-AA) is verified as: direct assertion for zero-dep/link-out, and inherited-by-reuse guards (viewport-meta, no-new-hex, no-fixed-px) for mobile-first + WCAG-AA, since Phase 6 introduces no new CSS system — documented in the script's header comment"
  - "OFFER-04 consult-gate verified with a concrete negative check (extract the built glow-radiant-core CTA anchor's inner text, assert it is not $4,500/Buy Now/Book & Pay) rather than a vague absence check"

patterns-established:
  - "count_matches/count_matches_ci: the canonical way to sum regex-match occurrences across N files in a bash validation script without hitting grep -c's multi-file per-file-count output or its always-prints-0-and-exits-1 no-match behavior"

requirements-completed: [NAV-01, OFFERQ-01, OFFERQ-02]

coverage:
  - id: D1
    description: "content/_index.md cta_secondary repointed from mailto:falkensmage@falkenslabyrinth.com to the /work/ hub, preserving the safeHTML front-matter mechanism and internal-nav convention"
    requirement: "NAV-01"
    verification:
      - kind: other
        ref: "bash tests/validate-phase-06.sh (NAV-01 section: href=/work/ present, legacy mailto absent) — pass"
        status: pass
    human_judgment: false
  - id: D2
    description: "tests/validate-phase-06.sh — 32-check automated regression gate covering OFFER-01..05, NAV-01, OFFERQ-01, OFFERQ-02, and the practitioner-language rule, on a clean hugo --minify build"
    requirement: "OFFERQ-01"
    verification:
      - kind: other
        ref: "bash tests/validate-phase-06.sh — 32 passed, 0 failed, exit 0"
        status: pass
    human_judgment: false
  - id: D3
    description: "OFFERQ-02 four-leg budget verified: link-out/zero-dep by direct assertion (no booking script/widget under public/work/, rel=noopener on every target=_blank CTA); mobile-first + WCAG-AA by inherited-by-reuse guards (viewport meta present, zero new hex colors, zero new fixed-px widths)"
    requirement: "OFFERQ-02"
    verification:
      - kind: other
        ref: "bash tests/validate-phase-06.sh (OFFERQ-02a/b/c sections) — pass"
        status: pass
    human_judgment: false
  - id: D4
    description: "Clean hugo --minify build exits 0; prior-phase validate-phase-01.sh remains fully green (no regression)"
    verification:
      - kind: other
        ref: "rm -rf public/ resources/_gen/ && hugo --minify --quiet (exit 0); bash tests/validate-phase-01.sh (46 passed, 0 failed, 1 manual-only, exit 0)"
        status: pass
    human_judgment: false

# Metrics
duration: 11min
completed: 2026-07-02
status: complete
---

# Phase 6 Plan 3: Homepage Repoint + Regression Gate Summary

**Homepage secondary CTA repointed from a bare `mailto:` to the `/work/` hub (NAV-01), plus a 32-check `tests/validate-phase-06.sh` acceptance gate proving all eight Phase 6 requirement IDs on a clean `hugo --minify` build.**

## Performance

- **Duration:** 11 min
- **Started:** 2026-07-02T00:32:35Z
- **Completed:** 2026-07-02T00:43:35Z
- **Tasks:** 2
- **Files modified:** 3 (`content/_index.md`, `tests/validate-phase-06.sh` created, `tests/validate-phase-02.sh` deviation fix)

## Accomplishments
- Repointed `content/_index.md`'s `cta_secondary` front matter from `mailto:falkensmage@falkenslabyrinth.com` to an internal `/work/` link with voiced anchor text ("See how we can work together") — the front door now reaches the offers hub. Mechanism (safeHTML raw-`<a>` string rendered by `identity-cta.html`) and internal-nav convention (no `target="_blank"`) both preserved; every other line of `content/_index.md` left byte-identical.
- Wrote `tests/validate-phase-06.sh`: a 32-check automated regression gate covering OFFER-01 through OFFER-05, NAV-01, OFFERQ-01, OFFERQ-02 (both the direct-assertion zero-dep leg and the inherited-by-reuse mobile-first/WCAG-AA legs), and the practitioner-language rule. All 32 checks pass on a clean `hugo --minify` build.
- OFFER-04's consult-gate is enforced with a concrete negative check: the script extracts the built the-daemon page's `glow-radiant-core` CTA anchor's inner text and asserts it equals `"Book a Clarity Consult ($150, credited)"` — not `$4,500`, `Buy Now`, or `Book & Pay`.
- Fixed a stale assertion in `tests/validate-phase-02.sh` (CTA-02) that would have permanently failed after the NAV-01 repoint — see Deviations below.
- Ran the full regression suite: `tests/validate-phase-06.sh` (32/32 pass) and `tests/validate-phase-01.sh` (46/46 automated pass, 1 manual-only) both exit 0 on a clean build.

## Task Commits

Each task was committed atomically:

1. **Task 1: Repoint homepage secondary CTA to /work/ (NAV-01)** - `32370d5` (feat)
2. **Task 2: Write tests/validate-phase-06.sh and confirm clean-build green (OFFERQ-01, OFFERQ-02)** - `218ed87` (test)

**Deviation fix (Rule 1):** `348f441` (fix) — updated `tests/validate-phase-02.sh` CTA-02 assertion, superseded by NAV-01.

## Files Created/Modified
- `content/_index.md` - `cta_secondary` front-matter value repointed from `mailto:` to `/work/`; all other lines unchanged
- `tests/validate-phase-06.sh` - New 32-check Phase 6 acceptance regression script (executable)
- `tests/validate-phase-02.sh` - CTA-02 check narrowed to `glow-radiant-core` only, dropping the now-obsolete mailto assertion (see Deviations)
- `.planning/phases/06-offer-pages/deferred-items.md` - Logs two unrelated, pre-existing `validate-phase-02.sh` failures discovered during regression-guard runs (out of scope for this plan)

## Decisions Made
- Anchor text for the repointed CTA reads "See how we can work together" rather than restating the offer names or an email address — matches the front door's "start there, then follow whatever pulls you" voice and correctly signals internal navigation rather than a direct contact channel.
- `tests/validate-phase-02.sh`'s CTA-02 check now asserts only `glow-radiant-core` (still meaningful — it's the primary CTA button class) and defers the mailto->`/work/` transition proof to `validate-phase-06.sh`'s NAV-01 section, which is the correct owner of that assertion going forward.
- `href_has`/`count_matches` helper functions were added to `validate-phase-06.sh` specifically to survive two environment quirks hit during authoring: Hugo's minifier drops quotes from unambiguous attribute values (`href=/work/`, not `href="/work/"`), and this machine's `grep` (ugrep, aliased as `grep`) prints a literal `0` on no-match with `-c` while still exiting 1 — chaining `|| echo 0` after it double-prints `0\n0`, which breaks bash arithmetic. Both fixes are general-purpose and documented inline in the script.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Stale `tests/validate-phase-02.sh` CTA-02 assertion made permanently false by NAV-01**
- **Found during:** Task 2, while running the plan's own required regression guard (`bash tests/validate-phase-01.sh && bash tests/validate-phase-02.sh`)
- **Issue:** `validate-phase-02.sh`'s CTA-02 check asserted BOTH `mailto:falkensmage@falkenslabyrinth.com` AND `glow-radiant-core` are present in the built homepage HTML. The mailto address appeared on the page only via `cta_secondary` (confirmed by grepping `themes/arcaeon/layouts/` — the `cta_email` fallback branch in `identity-cta.html` is never used since `cta_url` is set). Task 1 of this plan intentionally and correctly removes that mailto address per NAV-01, which means CTA-02's mailto assertion would fail on every future build, permanently, by design — a stale test encoding a requirement this very plan is explicitly superseding.
- **Fix:** Narrowed CTA-02 to assert only `glow-radiant-core` (the primary CTA button's class, unrelated to the secondary CTA's target and still a legitimate Phase-2 assertion), with an inline comment explaining the mailto->`/work/` transition and pointing to `validate-phase-06.sh`'s NAV-01 check as the new home for that specific assertion.
- **Files modified:** `tests/validate-phase-02.sh`
- **Verification:** `bash tests/validate-phase-02.sh` — CTA-02 now passes; ran before and after the fix to confirm the change was isolated to CTA-02 (see Issues Encountered for the two unrelated pre-existing failures this did NOT touch).
- **Committed in:** `348f441` (fix commit, separate from Task 1/2 commits)

---

**Total deviations:** 1 auto-fixed (Rule 1 - stale test assertion superseded by this plan's own locked requirement)
**Impact on plan:** Necessary for the plan's own "all three [validation scripts] must be green" verification step to be achievable post-NAV-01. No scope creep — the fix is scoped to the exact assertion this plan's Task 1 change invalidates.

## Issues Encountered

- **Two pre-existing, out-of-scope `validate-phase-02.sh` failures** discovered while running the regression guard: **SOCIAL-04** (expects platform-domain string `my.tarotpulse.com`, but the actual URL in `content/_index.md` is `mytarotpulse.com` — no dot) and **CTA-01** (expects literal text `Coaching` in built HTML, but the homepage copy was rewritten in an earlier phase to the current "archetypal tarotist, astrologer, chaos witch" voice and no longer contains that word). Confirmed via `git show HEAD~1:content/_index.md` that both mismatches predate this plan's commits — neither is caused by, or in scope of, Task 1 or Task 2. Per the executor's scope-boundary rule, these were logged to `.planning/phases/06-offer-pages/deferred-items.md` and NOT fixed. As a result, `bash tests/validate-phase-02.sh` exits 1 (16 passed / 2 failed) even after the CTA-02 deviation fix — both remaining failures are unrelated pre-existing drift, not a regression introduced by this plan.
- **Hugo minifier drops attribute quotes.** `hugo --minify` renders `href=/work/` (no quotes) rather than `href="/work/"` for attribute values needing no escaping — this affects every href on the homepage (including the pre-existing `cta_url`), not just the new `/work/` link. The plan's own inline verify commands (e.g. `grep -q 'href="/work/"' public/index.html`) would fail against the minified build for this reason alone; `validate-phase-06.sh`'s `href_has()` helper and the manual verification steps in this Summary account for both quoted and unquoted forms. This is a pre-existing minifier behavior, not something introduced by this plan.
- **`grep -c` portability quirks** (two, both worked around in `validate-phase-06.sh`, documented in the script header and its commit message): (1) `grep -c pattern file1 file2` prints one count per file rather than a sum — the same quirk 06-02 flagged; (2) on this machine's `grep` (ugrep), `grep -c` prints a literal `0` on no-match while still exiting 1, so `grep -c ... || echo 0` double-prints `0\n0` and breaks `$(( ))` arithmetic. Both avoided via a `count_matches`/`count_matches_ci` helper built on `grep -hoE ... | wc -l`.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 6 (offer-pages) is complete end-to-end: all eight requirement IDs (OFFER-01 through OFFER-05, NAV-01, OFFERQ-01, OFFERQ-02) are verified green by `tests/validate-phase-06.sh` on a clean `hugo --minify` build.
- The `/work/` hub is reachable from the homepage front door (NAV-01), closing the loop opened by Plans 06-01 (plumbing) and 06-02 (content).
- `tests/validate-phase-02.sh` has two unrelated, pre-existing, out-of-scope failures (SOCIAL-04, CTA-01) logged in `deferred-items.md` — recommend a future tech-debt plan reconcile that script's stale assertions against current homepage copy. Not a blocker for Phase 6 or v1.1.
- OFFER-F1 (swap placeholder Cal.com URLs for live event-type links) and OFFER-F2 (offer pages as Sigil & Thread source material) remain deferred per `06-CONTEXT.md`, unchanged by this plan.

---
*Phase: 06-offer-pages*
*Completed: 2026-07-02*

## Self-Check: PASSED

All created/modified files confirmed present on disk: `content/_index.md`, `tests/validate-phase-06.sh` (executable), `tests/validate-phase-02.sh`, `.planning/phases/06-offer-pages/deferred-items.md`, `.planning/phases/06-offer-pages/06-03-SUMMARY.md`. All three commit hashes (`32370d5`, `348f441`, `218ed87`) confirmed in `git log --all`.
