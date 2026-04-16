---
phase: 1
slug: theme-foundation
status: validated
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-16
validated: 2026-04-16
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Shell script (`bash tests/validate-phase-01.sh`) + Hugo build validation |
| **Config file** | `hugo.toml` |
| **Quick run command** | `bash tests/validate-phase-01.sh` |
| **Full suite command** | `bash tests/validate-phase-01.sh` + manual 375px viewport check |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `bash tests/validate-phase-01.sh`
- **After every plan wave:** Run `bash tests/validate-phase-01.sh` + manual 375px viewport check
- **Before `/gsd-verify-work`:** Full suite must be green (46/46 automated + 1 manual)
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INFRA-01 | — | N/A | build | `bash tests/validate-phase-01.sh` | ✅ | ✅ green |
| 01-01-02 | 01 | 1 | INFRA-02 | — | HTTPS baseURL | config | `bash tests/validate-phase-01.sh` | ✅ | ✅ green |
| 01-02-01 | 02 | 1 | THEME-01 | — | N/A | smoke | `bash tests/validate-phase-01.sh` | ✅ | ✅ green |
| 01-02-02 | 02 | 1 | THEME-02 | — | N/A | smoke | `bash tests/validate-phase-01.sh` | ✅ | ✅ green |
| 01-03-01 | 03 | 2 | THEME-03 | — | N/A | smoke | `bash tests/validate-phase-01.sh` | ✅ | ✅ green |
| 01-03-02 | 03 | 2 | THEME-04 | — | N/A | smoke | `bash tests/validate-phase-01.sh` | ✅ | ✅ green |
| 01-03-03 | 03 | 2 | THEME-05 | — | N/A | manual | DevTools → 375px → no overflow | — | ⬜ manual-only |
| 01-03-04 | 03 | 2 | THEME-06 | — | N/A | smoke | `bash tests/validate-phase-01.sh` | ✅ | ✅ green |
| 01-04-01 | 04 | 1 | THEME-07 | — | N/A | smoke | `bash tests/validate-phase-01.sh` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `brew install hugo` — Hugo Extended installed
- [x] `npm init -y` + `npm install @fontsource-variable/cinzel @fontsource-variable/space-grotesk` — font packages
- [x] `themes/arcaeon/` directory structure — theme scaffold
- [x] `themes/arcaeon/assets/css/main.css` — main stylesheet
- [x] `themes/arcaeon/layouts/_default/baseof.html` — base template
- [x] `themes/arcaeon/layouts/index.html` — homepage template
- [x] `content/kitchen-sink.md` — demo content page (draft: true)
- [x] `tests/validate-phase-01.sh` — automated validation script (46 checks)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| No horizontal scroll at 375px | THEME-05 | Responsive layout requires browser viewport | `hugo server --buildDrafts` → open /kitchen-sink/ → DevTools device toolbar → 375px → confirm no horizontal scrollbar |

*Note: THEME-01 (tokens), THEME-02 (fonts), THEME-03 (glow classes), THEME-04 (sections), THEME-06 (sigils) now have automated smoke checks via `tests/validate-phase-01.sh`. Visual rendering aspects (font FOIT, GPU compositing, color accuracy) remain visual-confirm-only but are covered by the kitchen sink page.*

---

## Validation Audit 2026-04-16

| Metric | Count |
|--------|-------|
| Gaps found | 9 |
| Resolved (automated) | 8 |
| Escalated (manual-only) | 1 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 5s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** approved 2026-04-16
