---
phase: 05-v1-gap-closure
plan: 02
subsystem: tooling, ci, documentation
tags: [validation-script, bash, regex, ci-hygiene, frontmatter-backfill, traceability]

# Dependency graph
requires:
  - phase: 05-v1-gap-closure
    provides: "Plan 05-01 code fixes — nested footer removed, css.Build externals slice preserving /fonts/ URLs — live in codebase so new structural checks have a valid target"
provides:
  - "validate-phase-03.sh with SEO-03 regex fixed (-cE with /? trailing-slash tolerance) and 6 new Phase-5 structural assertions — 39 total passing"
  - "Clean CI workflow with zero vestigial npm ci steps — committed WOFF2 files confirmed as single source of truth"
  - "Traceability-restored SUMMARY frontmatter across 4 files — every v1.0 REQ-ID now discoverable via gsd-audit-milestone frontmatter scan"
affects: [05-03-PLAN.md (verification + REQUIREMENTS.md status flips)]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Structural regression checks via bash + grep — Phase-5 additions to validate-phase-03.sh assert the INVARIANTS of Plan 05-01's fixes (footer count, preload/@font-face URL parity, no fonts in /css/) so future edits cannot silently regress"
    - "Inline YAML array frontmatter backfill — requirements-completed: [ID-1, ID-2] on single line matching 01-01, 02-01, 02-02, 04-01, 04-02 convention"
    - "CI hygiene: committed WOFF2 as source of truth — npm ci removed; package.json retained as version documentation for Cinzel 5.2.8 / Space Grotesk 5.2.10"
    - "set -uo pipefail + || true convention on grep calls that can legitimately match zero items — prevents false script abort"

key-files:
  created: []
  modified:
    - "tests/validate-phase-03.sh — line 154 SEO-03 regex swapped to -cE 'href=\"https://falkensmage\\.com/?\"' plus 5 new Phase-5 check blocks (6 assertion points) appended before results summary"
    - ".github/workflows/hugo.yml — deleted 2 lines (Install Node.js dependencies step + its run body); Setup Pages → Build with Hugo now adjacent"
    - ".planning/phases/01-theme-foundation/01-02-SUMMARY.md — inserted requirements-completed: [THEME-02, THEME-03] before metrics"
    - ".planning/phases/01-theme-foundation/01-03-SUMMARY.md — inserted requirements-completed: [THEME-04, THEME-05, THEME-06] before metrics"
    - ".planning/phases/03-dynamic-layer-quality/03-01-SUMMARY.md — inserted requirements-completed: [CURR-01, CURR-02, CURR-03, PERF-03, A11Y-01, A11Y-04] before metrics"
    - ".planning/phases/03-dynamic-layer-quality/03-02-SUMMARY.md — inserted requirements-completed: [SEO-01, SEO-02, SEO-03, PERF-01, PERF-02, PERF-04, A11Y-02, A11Y-03] before metrics"
  deleted: []

key-decisions:
  - "Structural-check additions live inside validate-phase-03.sh (not a new validate-phase-04.sh) — audit Open Questions Q2 deferred Phase 4 validation to a separate /gsd-validate-phase run; Phase-5 invariants fit semantically with Phase 3 fixes they guard"
  - "ERE with /? trailing-slash optional — not alternation — chosen for SEO-03 regex; shorter, more idiomatic, portable across BSD (macOS) and GNU (Ubuntu CI) grep"
  - "Inline YAML arrays on single line — matches established convention in 5 other SUMMARY files; consistency with prior art over 'more readable' multi-line form (Pitfall 5)"
  - "package.json / package-lock.json retained as version documentation — not deleted alongside npm ci removal (research Open Questions Q1, Assumption A2)"
  - "All grep calls that can legitimately match zero items wrapped with || true — set -uo pipefail on line 7 would abort the script otherwise (Landmine 7)"

patterns-established:
  - "Phase-5 structural checks guard the invariants created by Plan 05-01 — footer count, preload/@font-face parity, no fonts in /css/ — preventing silent regression by future edits"
  - "requirements-completed: [...] inline YAML array as canonical traceability key — hyphenated, consumed by gsd-audit-milestone SDK (commands.cjs:463)"

requirements-completed: [PERF-01]

# Metrics
duration: 3m
completed: 2026-04-17
---

# Phase 5 Plan 2: Hygiene + Traceability Backfill Summary

**Patched SEO-03 false-failure regex, added 6 Phase-5 structural assertions guarding Plan 05-01's invariants, removed vestigial `npm ci` from CI, and restored requirements-completed frontmatter across 4 SUMMARY files — 39/39 checks passing, every v1.0 REQ-ID now discoverable via audit scan.**

## Performance

- **Duration:** ~3 minutes
- **Started:** 2026-04-17 (immediately after 05-01 Wave 1 landed at 3b807bd's parent)
- **Tasks:** 6
- **Files modified:** 6

## Accomplishments

- **SEO-03 regex false-failure eliminated.** `tests/validate-phase-03.sh` line 154 now uses `grep -cE 'href="https://falkensmage\.com/?"'` — accepts both `href="https://falkensmage.com"` and `href="https://falkensmage.com/"` forms. Hugo's actual output (baseURL with trailing slash) matches; script reports `PASS: canonical points to falkensmage.com` instead of the previous 32/33 false failure.
- **5 new Phase-5 structural checks added (6 assertion points).** All run after the existing 33 Phase 3 assertions and guard Plan 05-01's fixes:
  - A11Y-01 opening `<footer[ >]` count equals 1 (nested-footer regression guard)
  - PERF-03 Cinzel preload href exactly equals @font-face url extracted from built CSS
  - PERF-03 Space Grotesk preload href exactly equals @font-face url
  - Zero `.woff2` files in `public/css/` (esbuild did not copy fonts)
  - `npm ci` absent from `.github/workflows/hugo.yml`
  - `requirements-completed:` present in all 4 target SUMMARY files
- **Deploy workflow cleaned.** `.github/workflows/hugo.yml` no longer contains the vestigial `Install Node.js dependencies` step. Setup Pages → Build with Hugo now adjacent. Saves ~5-10s per deploy and removes a silent install-failure mode. Committed WOFF2 files under `themes/arcaeon/static/fonts/` are the confirmed trust root.
- **Frontmatter traceability restored across 4 SUMMARY files.** Every v1.0 REQ-ID now appears in at least one SUMMARY.md's `requirements-completed` inline YAML array — ROADMAP Phase 5 success criterion 5 satisfied end-to-end.
- **Clean build + validation script: 39 passed, 0 failed.** Confirms Plan 05-01's A11Y-01 footer fix and PERF-03 externals fix are live AND structurally guarded against regression.

## Task Commits

Each task committed atomically:

1. **Task 1: Patch validate-phase-03.sh — SEO-03 regex + 5 Phase-5 structural checks** — `3b807bd` (fix)
2. **Task 2: Delete vestigial npm ci step from .github/workflows/hugo.yml** — `3340d5b` (chore)
3. **Task 3: Backfill 01-02-SUMMARY.md frontmatter with requirements-completed** — `dfe9881` (docs)
4. **Task 4: Backfill 01-03-SUMMARY.md frontmatter with requirements-completed** — `98434a9` (docs)
5. **Task 5: Backfill 03-01-SUMMARY.md frontmatter with requirements-completed** — `14ff36d` (docs)
6. **Task 6: Backfill 03-02-SUMMARY.md frontmatter with requirements-completed** — `c6d10d8` (docs)

## Files Created/Modified

- `tests/validate-phase-03.sh` — Line 154 SEO-03 check swapped from literal-match `grep -c 'href="https://falkensmage.com"'` to ERE `grep -cE 'href="https://falkensmage\.com/?"'`. 5 new Phase-5 check blocks appended (87 insertions, 1 deletion): A11Y-01 opening-footer count, PERF-03 Cinzel preload/url parity, PERF-03 Space Grotesk preload/url parity, no-woff2-in-css, npm-ci-absent, backfill-present-in-4-summaries. Every grep-of-things-that-can-match-zero wrapped with `|| true` to respect `set -uo pipefail`.
- `.github/workflows/hugo.yml` — Deleted 3 lines: the `- name: Install Node.js dependencies` line, its `run:` body line, and the blank separator. Setup Pages and Build with Hugo steps are now adjacent. No other step modified; `Install Dart Sass`, `Checkout`, and the `deploy:` job untouched.
- `.planning/phases/01-theme-foundation/01-02-SUMMARY.md` — Inserted `requirements-completed: [THEME-02, THEME-03]` as a single new line between `tech_stack.patterns` and `metrics:` in the YAML frontmatter. No other keys reordered; body content byte-identical.
- `.planning/phases/01-theme-foundation/01-03-SUMMARY.md` — Inserted `requirements-completed: [THEME-04, THEME-05, THEME-06]` similarly. THEME-04 also listed in 01-01-SUMMARY — intentional cross-referencing per research A5.
- `.planning/phases/03-dynamic-layer-quality/03-01-SUMMARY.md` — Inserted `requirements-completed: [CURR-01, CURR-02, CURR-03, PERF-03, A11Y-01, A11Y-04]`. PERF-03 and A11Y-01 were the partial-status items that Plan 05-01 fully closed — listing here is correct per original plan scope.
- `.planning/phases/03-dynamic-layer-quality/03-02-SUMMARY.md` — Inserted `requirements-completed: [SEO-01, SEO-02, SEO-03, PERF-01, PERF-02, PERF-04, A11Y-02, A11Y-03]`. PERF-01 (derivative of PERF-03) closed end-to-end in Plan 05.

## Decisions Made

- **ERE `/?` trailing-slash optional over alternation** for SEO-03 canonical regex. Shorter, more idiomatic, and portable across BSD grep (macOS dev machine) and GNU grep (Ubuntu CI). One-character delta from original literal pattern.
- **Structural checks in validate-phase-03.sh, not a new validate-phase-04.sh.** Audit Open Questions Q2 explicitly defers Phase 4 validation script creation. The Phase-5 invariants guard Plan 03-01 and Plan 03-02 outputs, so they fit semantically with the Phase 3 script.
- **Inline YAML arrays on a single line** for `requirements-completed` frontmatter entries. Matches prior art in 01-01, 02-01, 02-02, 04-01, 04-02 SUMMARY files. Multi-line block form is valid YAML but breaks the established convention (Pitfall 5).
- **All zero-match grep calls in new checks use `|| true`.** `set -uo pipefail` on line 7 of the script aborts on non-zero exit from piped commands; grep returns 1 when zero matches, which without `|| true` would kill the script mid-assertion (Landmine 7).
- **`package.json` / `package-lock.json` retained** (not deleted) alongside `npm ci` removal. They document Cinzel 5.2.8 and Space Grotesk 5.2.10 version lineage. Removing would be a separate tech-debt item (research Open Questions Q1, Assumption A2). Local `npm install` still works for anyone wanting to regenerate fonts from source.

## Deviations from Plan

None — plan executed exactly as written.

All six tasks' verification commands returned expected results on the first run. No Rule 1 bugs discovered, no Rule 2 missing critical functionality, no Rule 3 blocking issues, no Rule 4 architectural changes. Research pre-validated the regex syntax, workflow edit, and frontmatter key name empirically — the executor's job was mechanical application.

## Issues Encountered

None.

Note on the pre-tool-use hook: during each `Edit` operation, a "READ-BEFORE-EDIT REMINDER" advisory was issued, but all edits succeeded because the files had been read earlier in the session per the execution flow. No actual rejections occurred.

## Verification Results

| Check | Result |
|-------|--------|
| `hugo --quiet` exits 0 | yes |
| `validate-phase-03.sh` total passed | **39** |
| `validate-phase-03.sh` total failed | **0** |
| SEO-03 `canonical points to falkensmage.com` | PASS (was FAIL pre-Task-1) |
| A11Y-01 (Phase 5) opening footer count == 1 | PASS |
| PERF-03 (Phase 5) Cinzel preload === @font-face url | PASS (`/fonts/cinzel-latin-wght-normal.woff2`) |
| PERF-03 (Phase 5) Space Grotesk preload === @font-face url | PASS (`/fonts/space-grotesk-latin-wght-normal.woff2`) |
| PERF-03 (Phase 5) zero .woff2 in public/css/ | PASS |
| `npm ci` count in workflow | 0 |
| `requirements-completed:` in 01-02-SUMMARY | PASS |
| `requirements-completed:` in 01-03-SUMMARY | PASS |
| `requirements-completed:` in 03-01-SUMMARY | PASS |
| `requirements-completed:` in 03-02-SUMMARY | PASS |

## Known Stubs

None. All edits are content additions (regex patch, new check blocks, frontmatter lines) or deletions (npm ci step). No placeholder data or hardcoded empty values introduced.

## Threat Flags

None. Per plan `<threat_model>`, T-05-02 is accept-disposition (npm ci removal documented in research; structural check in Task 1 prevents accidental reintroduction). No new trust boundaries, no runtime attack surface, build-tier and documentation edits only.

## User Setup Required

None — surgical script, workflow, and documentation edits with no external service configuration, environment variables, or UI-only changes.

## Next Phase Readiness

- **Plan 05-03 unblocked.** Wave 3 verification + REQUIREMENTS.md status flips for PERF-01 (A11Y-01 and PERF-03 already flipped by 05-01 executor deviation) can proceed. The validate-phase-03.sh + clean build already demonstrate all Phase 3 criteria pass.
- **No concerns.** 39/39 structural checks green on clean rebuild. `npm ci` absence verified. All 4 SUMMARY files pass the backfill check.

## Self-Check: PASSED

Verified on disk:

- `tests/validate-phase-03.sh` — FOUND (contains `grep -cE` SEO-03 pattern + 5 Phase-5 sections)
- `.github/workflows/hugo.yml` — FOUND (contains zero `npm ci`, preserves Setup Pages / Install Dart Sass / Build with Hugo steps)
- `.planning/phases/01-theme-foundation/01-02-SUMMARY.md` — FOUND (contains `requirements-completed: [THEME-02, THEME-03]`)
- `.planning/phases/01-theme-foundation/01-03-SUMMARY.md` — FOUND (contains `requirements-completed: [THEME-04, THEME-05, THEME-06]`)
- `.planning/phases/03-dynamic-layer-quality/03-01-SUMMARY.md` — FOUND (contains `requirements-completed: [CURR-01, CURR-02, CURR-03, PERF-03, A11Y-01, A11Y-04]`)
- `.planning/phases/03-dynamic-layer-quality/03-02-SUMMARY.md` — FOUND (contains `requirements-completed: [SEO-01, SEO-02, SEO-03, PERF-01, PERF-02, PERF-04, A11Y-02, A11Y-03]`)

Verified in git log:

- `3b807bd` — FOUND (Task 1 — SEO-03 regex + 5 Phase-5 checks)
- `3340d5b` — FOUND (Task 2 — npm ci removal)
- `dfe9881` — FOUND (Task 3 — 01-02 backfill)
- `98434a9` — FOUND (Task 4 — 01-03 backfill)
- `14ff36d` — FOUND (Task 5 — 03-01 backfill)
- `c6d10d8` — FOUND (Task 6 — 03-02 backfill)

Runtime re-verification after all 6 commits:

- `rm -rf public/ resources/_gen/ && hugo --quiet && bash tests/validate-phase-03.sh` → `=== Results: 39 passed, 0 failed ===` → PASS
- `grep -c 'npm ci' .github/workflows/hugo.yml` → 0 → PASS

---
*Phase: 05-v1-gap-closure*
*Completed: 2026-04-17*
