---
phase: 05-v1-gap-closure
plan: 03
subsystem: verification, documentation
tags: [regression, validation, traceability, clean-build, requirements-flip, audit-closure]

# Dependency graph
requires:
  - phase: 05-v1-gap-closure
    provides: "Plan 05-01 structural fixes (nested footer removed, css.Build externals, duplicate assets/fonts/ deleted) and Plan 05-02 hygiene + validation checks (SEO-03 regex, Phase-5 structural asserts, npm ci removed, SUMMARY frontmatter backfills) live in repo"
provides:
  - "Final end-to-end regression transcript under clean-build discipline (rm -rf public/ resources/_gen/) — all three validate-phase-*.sh scripts green"
  - "REQUIREMENTS.md traceability table with zero Pending v1 requirements — 42/42 Complete"
  - "Footer note documenting the Phase 5 gap closure completion date"
affects: ["Future /gsd-audit-milestone run — v1.0 will report green", "ROADMAP Phase 5 status flip to Complete"]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Clean-rebuild discipline: rm -rf public/ resources/_gen/ before verification to invalidate Hugo's asset cache and prevent stale-artifact masking (Landmines 1, 2 from 05-RESEARCH.md)"
    - "Structural diff via process substitution — diff <(...) <(...) — to confirm preload href and @font-face url() are byte-identical without intermediate files"
    - "REQ status invariant: every v1 REQ-ID mapped to a phase has status Complete or is reassigned to a later Pending phase; zero Pending rows in the traceability table = milestone fully closed"

key-files:
  created:
    - ".planning/phases/05-v1-gap-closure/05-03-SUMMARY.md (this file)"
  modified:
    - "tests/validate-phase-01.sh — font path references updated from themes/arcaeon/assets/fonts/ to themes/arcaeon/static/fonts/ (Rule 3 deviation, see below)"
    - ".planning/REQUIREMENTS.md — PERF-01 flipped [ ] → [x] in Performance checklist; PERF-01 traceability row Pending → Complete; footer note appended"

key-decisions:
  - "Task 1 clean rebuild discipline enforced — rm -rf public/ resources/_gen/ before validation to catch stale-state bugs (Plan 05-01 and 05-02 had both written to public/ under stale cache conditions)"
  - "tests/validate-phase-01.sh font path update handled as Rule 3 (blocking) auto-fix inline in Task 1 rather than deferred — the failing Phase 1 regression was not a true regression (intentional architecture change in Plan 05-01 made the old paths invalid) and blocked Task 2's gating precondition"
  - "REQUIREMENTS.md edit count reduced from plan's prescribed 6 to 2 REQ-ID edits + 1 footer addition — Plan 05-01's executor had already pre-flipped A11Y-01 and PERF-03 mid-phase (noted harmless in 05-02-SUMMARY). Only PERF-01 remained Pending at start of Plan 05-03"
  - "All three regression scripts run sequentially under single clean build, not parallel — avoids the rare race where one script's final assertion reads state another script mutates; negligible time cost (~4s total), meaningful reliability gain"

patterns-established:
  - "Clean-rebuild verification gate before documentation finalization — Phase 5 final assertion path: (rm -rf public/ resources/_gen/) -> (hugo --quiet) -> (validate-phase-01.sh && validate-phase-02.sh && validate-phase-03.sh) -> (structural diff for both fonts) -> (REQ flip)"
  - "Test-path synchronization after source-of-truth moves — when an architectural change moves files (Plan 05-01 move from assets/fonts/ to static/fonts/), hardcoded test paths must follow or they silently drift; surface via clean-rebuild regression"

requirements-completed: [A11Y-01, PERF-01, PERF-03]

# Metrics
metrics:
  duration: "3 minutes"
  completed: 2026-04-17
---

# Phase 5 Plan 3: Final Verification + Traceability Flip Summary

**Confirmed all Phase 5 code and documentation fixes hold under clean-rebuild regression (46 + 18 + 39 = 103 checks green across three validation scripts), flipped PERF-01 to Complete in REQUIREMENTS.md, and closed the v1.0 milestone audit — 42/42 v1 requirements now Complete.**

## Performance

- **Duration:** ~3 minutes
- **Started:** 2026-04-17T19:36:50Z
- **Completed:** 2026-04-17T19:39:52Z
- **Tasks:** 2
- **Files modified:** 2 (+1 deviation fix)

## Accomplishments

- **Clean-rebuild regression passed end-to-end.** `rm -rf public/ resources/_gen/ && hugo --quiet` completes without errors. All three validation scripts green with no failures:
  - `validate-phase-01.sh` — 46/46 passed (after Rule 3 path fix, was 41/46)
  - `validate-phase-02.sh` — 18/18 passed (unchanged)
  - `validate-phase-03.sh` — 39/39 passed (includes 6 Phase-5 structural checks)
- **Byte-for-byte URL parity confirmed for both fonts.** Structural diff of preload href vs `url(...)` in built CSS returns empty for both:
  - Cinzel: `/fonts/cinzel-latin-wght-normal.woff2` (preload) === `/fonts/cinzel-latin-wght-normal.woff2` (@font-face)
  - Space Grotesk: `/fonts/space-grotesk-latin-wght-normal.woff2` (preload) === `/fonts/space-grotesk-latin-wght-normal.woff2` (@font-face)
- **Zero `.woff2` files in `public/css/`** — esbuild's file loader is fully opted out via the `externals` slice from Plan 05-01.
- **Both font files present at `public/fonts/`** — Hugo's static pipeline serves them from the new single-source location.
- **PERF-01 traceability flipped Pending → Complete.** Section checklist `[ ]` → `[x]` and table row status updated.
- **Footer note appended** documenting Phase 5 gap closure completion on 2026-04-17.
- **Zero Pending v1 requirements.** `grep -cE '^\| [A-Z]+-[0-9]+ \| Phase [0-9]+ \| Pending \|$' .planning/REQUIREMENTS.md` returns 0.

## Task Commits

1. **Task 1: Final regression + Rule 3 path fix to validate-phase-01.sh** — `9bde6e0` (fix)
2. **Task 2: Flip PERF-01 status + append footer note in REQUIREMENTS.md** — `90b8bf6` (docs)

Note: Plan 03 was specified as Task 1 being read-only verification. Task 1 became a mixed verification + fix commit because the regression surfaced a test-path mismatch (validate-phase-01.sh hardcoded the pre-Plan-05-01 font location). See Deviations.

## Files Created/Modified

- `tests/validate-phase-01.sh` — Two surgical edits: line 104-105 updated `CINZEL_WOFF2`/`SPACE_WOFF2` path variables from `themes/arcaeon/assets/fonts/` to `themes/arcaeon/static/fonts/`; line 204-205 + 212 updated the `REQUIRED_PATHS` and `REQUIRED_DIRS` arrays in the THEME-07 structural check to match. Also updated the human-readable PASS/FAIL labels to mention the new location. Inline comments added referencing Plan 05-01 PERF-03 fix as the architectural justification.
- `.planning/REQUIREMENTS.md` — Three edits: line 67 `- [ ] **PERF-01**` → `- [x] **PERF-01**` (section checklist); line 148 `| PERF-01 | Phase 5 | Pending |` → `| PERF-01 | Phase 5 | Complete |` (traceability table); line 171 appended a new footer line `*Phase 5 gap closure complete: A11Y-01, PERF-01, PERF-03 marked Complete on 2026-04-17*`.

## Decisions Made

- **Task 1 scope expanded to include validate-phase-01.sh path fix.** The plan described Task 1 as "read-only verification" but the regression revealed Phase 1 validation hardcoded the pre-Plan-05-01 font location (`themes/arcaeon/assets/fonts/`). Rather than log this as a deferred item and block Task 2 on its precondition, the executor applied a Rule 3 (blocking issue) auto-fix in line with the deviation rules: update the test to reflect the intentional new architecture. This preserves the regression guard's intent (fonts exist in source tree) without asserting a location that was deliberately removed.
- **Clean-rebuild discipline mandatory before any assertion.** 05-RESEARCH.md Landmines 1 and 2 warn that Hugo's `resources/_gen/` cache and the accumulation of fingerprinted `main.min.*.css` files in `public/css/` can mask bugs. Every verification step was preceded by `rm -rf public/ resources/_gen/` and a fresh `hugo --quiet` to guarantee the state being tested was built from current sources.
- **Task 2 edit list pared from 6 to 2.** Plan 05-03 prescribed 3 section-checklist flips and 3 traceability-table flips, but the REQUIREMENTS.md as of Plan 05-03 start had already been partially flipped by Plan 05-01's executor (A11Y-01 and PERF-03 were pre-emptively marked Complete in a commit from that plan — noted as harmless deviation in 05-02-SUMMARY's Next Phase Readiness). Only PERF-01 remained Pending in both places. The executor flipped the actual Pending state rather than re-flipping already-Complete rows.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Updated validate-phase-01.sh font paths to match Plan 05-01 architecture**
- **Found during:** Task 1 regression run — `bash tests/validate-phase-01.sh` returned 5 failures under clean rebuild
- **Issue:** `tests/validate-phase-01.sh` hardcodes `themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2` and the corresponding Space Grotesk path in two places (the THEME-02 font file existence check at line 104-116, and the THEME-07 theme structure `REQUIRED_PATHS` + `REQUIRED_DIRS` arrays at line 204-212). Plan 05-01 Task 3 intentionally deleted that directory as part of the PERF-03 single-source-of-truth fix. The Phase 1 test was asserting against a location that no longer exists and should not exist — producing 5 false failures that blocked Task 1's "Phase 1 validation exits 0" acceptance criterion.
- **Fix:** Updated both path references in the test script to point at `themes/arcaeon/static/fonts/` (the new canonical location). Added inline comments explaining the Plan 05-01 PERF-03 architectural justification. Updated PASS/FAIL labels to reflect the new location.
- **Files modified:** `tests/validate-phase-01.sh` (two edits)
- **Commit:** `9bde6e0`
- **Verification after fix:** Phase 1 now 46/46 passed (was 41/46); Phase 2 and Phase 3 regression unaffected and still green; structural diff for both fonts returns empty.

**2. [Documentation alignment] Task 2 edit count reduced from 6 to 2 REQ-ID flips + 1 footer append**
- **Found during:** Initial read of REQUIREMENTS.md at start of Task 2
- **Issue:** Plan 05-03 prescribed 6 REQUIREMENTS.md status-flip edits (3 section checklists + 3 traceability rows) for A11Y-01, PERF-01, PERF-03. But Plan 05-01's executor had pre-emptively flipped A11Y-01 and PERF-03 mid-phase (harmless pre-flip; noted in 05-02-SUMMARY). By the time Plan 05-03 started, only PERF-01 remained Pending in both the checklist and the table.
- **Fix:** Performed only the edits needed to reconcile the actual state with the target state: PERF-01 `[ ]` → `[x]`, PERF-01 `Pending` → `Complete`, and the footer append. Skipped the already-correct lines for A11Y-01 and PERF-03. Reconciled plan intent (three REQ-IDs fully Complete in REQUIREMENTS.md) without redundant edits.
- **Files modified:** `.planning/REQUIREMENTS.md` (three edits, all on PERF-01 + footer)
- **Commit:** `90b8bf6`
- **Verification after fix:** `grep -cE '^\| (A11Y-01|PERF-01|PERF-03) \| Phase 5 \| Complete \|$' = 3`; Pending count across all 42 v1 requirements = 0.

## Issues Encountered

None blocking. The two deviations above were handled cleanly within Rule 3 (blocking issue auto-fix) and documentation-reconciliation scope. No Rule 4 architectural checkpoint triggered.

Note on `set -u` / verification scripting: an inline verification step using chained `&&` with `grep -c` silently failed one sub-check because grep returns exit 1 when match count is 0, and the `$(...)` capture inherits that failure under `pipefail`. Worked around with explicit `|| true` suffixes on the capture expressions. This is Landmine 7 from 05-RESEARCH.md ("set -uo pipefail + grep-returns-1-on-zero-matches trap") showing up in an interactive context — well-understood behavior.

## Verification Results

| Check | Result |
|-------|--------|
| `rm -rf public/ resources/_gen/ && hugo --quiet` exits 0 | yes |
| `grep -cE '<footer[ >]' public/index.html` == 1 | **1** (PASS) |
| `grep -c '</footer>' public/index.html` == 1 | **1** (PASS) |
| `url(/fonts/cinzel-latin-wght-normal.woff2)` in `public/css/main.min.*.css` | present (PASS) |
| `url(/fonts/space-grotesk-latin-wght-normal.woff2)` in `public/css/main.min.*.css` | present (PASS) |
| Cinzel preload href === @font-face url (structural diff) | empty (PASS) |
| Space Grotesk preload href === @font-face url (structural diff) | empty (PASS) |
| `ls public/css/*.woff2 \| wc -l` | **0** (PASS) |
| `public/fonts/cinzel-latin-wght-normal.woff2` exists | yes (PASS) |
| `public/fonts/space-grotesk-latin-wght-normal.woff2` exists | yes (PASS) |
| `bash tests/validate-phase-01.sh` | **46 passed, 0 failed** (PASS) |
| `bash tests/validate-phase-02.sh` | **18 passed, 0 failed** (PASS) |
| `bash tests/validate-phase-03.sh` | **39 passed, 0 failed** (PASS) |
| REQUIREMENTS.md `grep -cE '^\| (A11Y-01\|PERF-01\|PERF-03) \| Phase 5 \| Complete \|$'` | **3** (PASS) |
| REQUIREMENTS.md `grep -cE '^- \[x\] \*\*(A11Y-01\|PERF-01\|PERF-03)\*\*'` | **3** (PASS) |
| REQUIREMENTS.md `grep -cE '^\| (A11Y-01\|PERF-01\|PERF-03) \| Phase 5 \| Pending \|$'` | **0** (PASS) |
| REQUIREMENTS.md v1 Pending total `grep -cE '^\| [A-Z]+-[0-9]+ \| Phase [0-9]+ \| Pending \|$'` | **0** (PASS) |
| Footer note contains "Phase 5 gap closure complete" | yes (PASS) |

## Known Stubs

None. Plan 05-03 is verification + traceability documentation only; no placeholder data, no UI wiring.

## Threat Flags

None. Per plan `<threat_model>`, T-05-03 is accept-disposition (REQUIREMENTS.md status integrity guarded by git-tracked diff and the Task 1 regression gate). No new trust boundaries, no runtime attack surface. Documentation and test-path edits only.

## User Setup Required

None — final verification and documentation edits only. No external services, no environment variables, no UI changes.

## Next Phase Readiness

- **v1.0 milestone fully closed.** All 42 v1 requirements are Complete in REQUIREMENTS.md; all three Phase 5 REQ-IDs (A11Y-01, PERF-01, PERF-03) are marked Complete and traceable via SUMMARY frontmatter (originals in 03-01 and 03-02 via Plan 05-02 backfill; final closure here).
- **ROADMAP Phase 5 ready to flip to Complete.** Plan checklist in ROADMAP.md line 97 (`- [ ] 05-03-PLAN.md`) should flip to `- [x]`; Phase 5 header on line 13 should flip to `- [x]`; Progress table row 108 should move from "2/3 In Progress" to "3/3 Complete" with completion date 2026-04-17. These updates are handled by the executor's post-plan state-update step, not manually in this summary.
- **No concerns.** Clean-rebuild regression green on first run after deviations applied. No stub UI, no threat flags, no deferred items.
- **Future gsd-audit-milestone run** will report v1.0 as fully closed — the audit findings that created this phase are now resolved end-to-end and verified by clean-build assertions.

## Self-Check: PASSED

Verified on disk:

- `.planning/phases/05-v1-gap-closure/05-03-SUMMARY.md` — FOUND (this file)
- `tests/validate-phase-01.sh` — FOUND (contains `themes/arcaeon/static/fonts/cinzel-latin-wght-normal.woff2` path)
- `.planning/REQUIREMENTS.md` — FOUND (contains `- [x] **PERF-01**` and `| PERF-01 | Phase 5 | Complete |` and the new footer line)

Verified in git log:

- `9bde6e0` — FOUND (Task 1 — validate-phase-01.sh path fix)
- `90b8bf6` — FOUND (Task 2 — REQUIREMENTS.md PERF-01 flip + footer)

Runtime re-verification:

- Clean rebuild via `rm -rf public/ resources/_gen/ && hugo --quiet` → exit 0
- `validate-phase-01.sh` → 46 passed, 0 failed
- `validate-phase-02.sh` → 18 passed, 0 failed
- `validate-phase-03.sh` → 39 passed, 0 failed
- Cinzel preload === @font-face url structural diff → empty
- Space Grotesk preload === @font-face url structural diff → empty
- REQUIREMENTS.md v1 Pending count → 0

---
*Phase: 05-v1-gap-closure*
*Completed: 2026-04-17*
