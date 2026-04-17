---
phase: 5
slug: v1-gap-closure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution. Source: 05-RESEARCH.md §Validation Architecture.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Bash + `grep` (project-established pattern, matches Phase 3) |
| **Config file** | none — standalone shell scripts in `tests/` |
| **Quick run command** | `hugo --quiet && bash tests/validate-phase-03.sh` |
| **Full suite command** | `rm -rf public/ && hugo --quiet && bash tests/validate-phase-01.sh && bash tests/validate-phase-02.sh && bash tests/validate-phase-03.sh` |
| **Estimated runtime** | ~10–15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `hugo --quiet && bash tests/validate-phase-03.sh` (must remain green)
- **After every plan wave:** Run full regression: `rm -rf public/ && hugo --quiet && bash tests/validate-phase-01.sh && bash tests/validate-phase-02.sh && bash tests/validate-phase-03.sh`
- **Before `/gsd-verify-work`:** Full suite must be green AND PERF-03 structural diff returns empty for both fonts AND `public/css/` contains no `.woff2` files
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 5-01-01 | 01 | 1 | A11Y-01 | — | N/A | structural | `[ "$(grep -cE '<footer[ >]' public/index.html)" -eq 1 ]` | ❌ W0 (add to validate-phase-03.sh) | ⬜ pending |
| 5-01-02 | 01 | 1 | PERF-03 | — | N/A | structural | `diff <(grep -oE '/fonts/cinzel-[^"]*' public/index.html \| head -1) <(grep -oE '/fonts/cinzel-[^)]*' public/css/main.min.*.css \| head -1)` returns empty | ❌ W0 (add to validate-phase-03.sh) | ⬜ pending |
| 5-01-03 | 01 | 1 | PERF-03 | — | N/A | structural | `diff <(grep -oE '/fonts/space-grotesk-[^"]*' public/index.html \| head -1) <(grep -oE '/fonts/space-grotesk-[^)]*' public/css/main.min.*.css \| head -1)` returns empty | ❌ W0 | ⬜ pending |
| 5-01-04 | 01 | 1 | PERF-03 | — | N/A | structural | `[ -z "$(ls public/css/*.woff2 2>/dev/null)" ] && [ -n "$(ls public/fonts/*.woff2 2>/dev/null)" ]` | ❌ W0 | ⬜ pending |
| 5-01-05 | 01 | 1 | PERF-01 | — | N/A | smoke | Existing line 68 of `validate-phase-03.sh` (no external CDN) — derivative of PERF-03 covered by tasks 02/03/04 | ✅ existing | ⬜ pending |
| 5-02-01 | 02 | 2 | SEO-03 (tech debt) | — | N/A | smoke | `bash tests/validate-phase-03.sh` reports 33/33 (or higher with new checks) — SEO-03 line passes | ✅ existing (script line 154 patched in this task) | ⬜ pending |
| 5-02-02 | 02 | 2 | tech-debt (CI) | — | N/A | structural | `! grep -q 'npm ci' .github/workflows/hugo.yml` | ❌ W0 (add to validate-phase-03.sh) | ⬜ pending |
| 5-02-03 | 02 | 2 | tech-debt (frontmatter) | — | N/A | structural | `grep -l 'requirements-completed' .planning/phases/01-theme-foundation/01-02-SUMMARY.md` returns 1 path | ✅ existing file (edit) | ⬜ pending |
| 5-02-04 | 02 | 2 | tech-debt (frontmatter) | — | N/A | structural | `grep -l 'requirements-completed' .planning/phases/01-theme-foundation/01-03-SUMMARY.md` returns 1 path | ✅ existing | ⬜ pending |
| 5-02-05 | 02 | 2 | tech-debt (frontmatter) | — | N/A | structural | `grep -l 'requirements-completed' .planning/phases/03-dynamic-layer-quality/03-01-SUMMARY.md` returns 1 path | ✅ existing | ⬜ pending |
| 5-02-06 | 02 | 2 | tech-debt (frontmatter) | — | N/A | structural | `grep -l 'requirements-completed' .planning/phases/03-dynamic-layer-quality/03-02-SUMMARY.md` returns 1 path | ✅ existing | ⬜ pending |
| 5-03-01 | 03 | 3 | A11Y-01, PERF-01, PERF-03 | — | N/A | regression | Full suite command (above) — all green | ✅ | ⬜ pending |
| 5-03-02 | 03 | 3 | traceability | — | N/A | structural | `grep -E '^\| (A11Y-01\|PERF-01\|PERF-03) \| Phase 5 \| Complete' .planning/REQUIREMENTS.md` returns 3 lines | ✅ existing | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/validate-phase-03.sh` — patch line 154 (SEO-03 regex: `href="https://falkensmage\.com/?"` to accept optional trailing slash)
- [ ] `tests/validate-phase-03.sh` — add A11Y-01 check: `<footer[ >]` opening-tag count equals 1
- [ ] `tests/validate-phase-03.sh` — add PERF-03 structural diff check (preload href === @font-face src) for both Cinzel and Space Grotesk
- [ ] `tests/validate-phase-03.sh` — add tech-debt check: `npm ci` absent from `.github/workflows/hugo.yml`
- [ ] `tests/validate-phase-03.sh` — add tech-debt check: all four target SUMMARY.md files contain `requirements-completed:` key

*All Wave 0 work is patches/additions to the existing `tests/validate-phase-03.sh` script. No new framework, no new files. Per research §Open Questions, a separate `tests/validate-phase-04.sh` is deferred — the single Phase 4 tech-debt check is added inline to Phase 3's validation script.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Visual confirmation that fonts render correctly post-fix (no swap flash, no broken glyphs) | PERF-03 | Visual rendering cannot be grep-verified | Open `hugo server` locally, view `localhost:1313`, confirm Cinzel + Space Grotesk render in their correct weights with no FOIT |
| Lighthouse 3G timing measurement (PERF-01 sub-1s claim) | PERF-01 | Audit accepts structural correctness as the v1.0 gate; full Lighthouse measurement is optional | Run `npx lighthouse https://falkensmage.com --throttling.cpuSlowdownMultiplier=4 --throttling.requestLatencyMs=300 --throttling.downloadThroughputKbps=1638` if user wants empirical confirmation |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references (5 patches/additions to validate-phase-03.sh)
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
