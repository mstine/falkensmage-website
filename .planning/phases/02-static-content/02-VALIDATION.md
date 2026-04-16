---
phase: 2
slug: static-content
status: complete
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-16
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Shell script + Hugo build (established pattern from Phase 1) |
| **Config file** | `hugo.toml` |
| **Quick run command** | `bash tests/validate-phase-02.sh` |
| **Full suite command** | `bash tests/validate-phase-02.sh && bash tests/validate-phase-01.sh` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `bash tests/validate-phase-02.sh`
- **After every plan wave:** Run `bash tests/validate-phase-02.sh && bash tests/validate-phase-01.sh`
- **Before `/gsd-verify-work`:** Full suite must be green + manual 375px visual pass
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 02-01-01 | 01 | 1 | HERO-01 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-01-02 | 01 | 1 | HERO-02 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-01-03 | 01 | 1 | HERO-03 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-01-04 | 01 | 1 | HERO-04 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-02-01 | 02 | 1 | IDENT-01 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-02-02 | 02 | 1 | IDENT-02 | — | N/A | config | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-03-01 | 03 | 1 | SOCIAL-01 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-03-02 | 03 | 1 | SOCIAL-02 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-03-03 | 03 | 1 | SOCIAL-03 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-03-04 | 03 | 1 | SOCIAL-04 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-03-05 | 03 | 1 | SOCIAL-05 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-04-01 | 04 | 1 | CTA-01 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-04-02 | 04 | 1 | CTA-02 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-05-01 | 05 | 1 | FOOT-01 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-05-02 | 05 | 1 | FOOT-02 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |
| 02-05-03 | 05 | 1 | FOOT-03 | — | N/A | smoke | `bash tests/validate-phase-02.sh` | ✅ | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [x] `tests/validate-phase-02.sh` — covers all 16 automated checks above (+ build check + regression = 18 total)
- [x] `themes/arcaeon/layouts/partials/sections/` — 4 section partial files (hero.html, identity-cta.html, social.html, footer.html)
- [x] `themes/arcaeon/layouts/partials/icons/` — 8 SVG icon partials
- [x] `content/_index.md` — social_links, tagline, identity_blocks, cta params in front matter
- [x] `themes/arcaeon/assets/css/main.css` — social grid, hero, footer CSS appended

*`themes/arcaeon/assets/images/magus-hero.jpg` — already present (copied during research)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Magus image displays without distortion at 375px; glow pulse visible | HERO-01, HERO-04 | Visual rendering requires browser | `hugo server` → 375px DevTools → visual confirm |
| Touch targets are visually 44px minimum at 375px | SOCIAL-03 | Computed styles in browser | DevTools computed styles on social cards |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 10s
- [x] `nyquist_compliant: true` set in frontmatter

**Approval:** complete

---

## Validation Audit 2026-04-16

| Metric | Count |
|--------|-------|
| Gaps found | 1 |
| Resolved | 1 |
| Escalated | 0 |

**Details:**
- IDENT-02: Test checked for `identity_statement:` but implementation uses `identity_blocks:` (array). Updated test to match actual key name. Feature was working — test was stale.
