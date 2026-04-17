---
phase: 3
slug: dynamic-layer-quality
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | bash + grep + hugo CLI (no test framework — static site) |
| **Config file** | none — validation scripts created in Wave 0 |
| **Quick run command** | `hugo build --environment production 2>&1 && echo "BUILD OK"` |
| **Full suite command** | `bash scripts/validate-phase3.sh` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `hugo build --environment production 2>&1 && echo "BUILD OK"`
- **After every plan wave:** Run `bash scripts/validate-phase3.sh`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | CURR-01 | — | N/A | integration | `hugo build && grep -q "feralarchitecture" public/index.html` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | CURR-02 | — | N/A | integration | `grep -q 'resources.GetRemote' themes/arcaeon/layouts/partials/sections/currently.html` | ❌ W0 | ⬜ pending |
| 03-01-03 | 01 | 1 | CURR-03 | — | N/A | source | `grep -q 'Read Feral Architecture' themes/arcaeon/layouts/partials/sections/currently.html` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 1 | PERF-01 | — | N/A | integration | `hugo build && stat -f%z public/index.html` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 1 | PERF-02 | — | N/A | source | `grep -q 'picture' themes/arcaeon/layouts/partials/sections/hero.html` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 1 | PERF-03 | — | N/A | source | `grep -q 'rel="preload"' themes/arcaeon/layouts/_default/baseof.html` | ❌ W0 | ⬜ pending |
| 03-02-04 | 02 | 1 | PERF-04 | — | N/A | source | `grep -v 'analytics\|google\|plausible' themes/arcaeon/layouts/_default/baseof.html` | ❌ W0 | ⬜ pending |
| 03-03-01 | 03 | 1 | A11Y-01 | — | N/A | integration | `hugo build && grep -q '<header' public/index.html && grep -q '<main' public/index.html && grep -q '<footer' public/index.html` | ❌ W0 | ⬜ pending |
| 03-03-02 | 03 | 1 | A11Y-02 | — | N/A | manual | WCAG AA contrast tool | ❌ W0 | ⬜ pending |
| 03-03-03 | 03 | 1 | A11Y-03 | — | N/A | source | `grep -q 'alt=' themes/arcaeon/layouts/partials/sections/hero.html` | ❌ W0 | ⬜ pending |
| 03-03-04 | 03 | 1 | A11Y-04 | — | N/A | source | `grep -q 'prefers-reduced-motion' themes/arcaeon/assets/css/main.css` | ❌ W0 | ⬜ pending |
| 03-04-01 | 04 | 1 | SEO-01 | — | N/A | integration | `hugo build && grep -q 'og:title' public/index.html` | ❌ W0 | ⬜ pending |
| 03-04-02 | 04 | 1 | SEO-02 | — | N/A | integration | `hugo build && grep -q 'twitter:card' public/index.html` | ❌ W0 | ⬜ pending |
| 03-04-03 | 04 | 1 | SEO-03 | — | N/A | integration | `hugo build && grep -q 'canonical' public/index.html` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `scripts/validate-phase3.sh` — comprehensive validation script covering all 14 requirements
- [ ] Hugo build environment verified working after Phase 2

*Existing infrastructure covers framework needs — Hugo CLI is the test runner.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| WCAG AA contrast for all text/background pairs | A11Y-02 | Requires visual inspection or external contrast tool | Run page through WebAIM contrast checker or browser DevTools accessibility audit |
| Sub-1s page load on simulated 3G | PERF-01 | Requires Lighthouse or WebPageTest with network throttling | Run `npx lighthouse http://localhost:1313 --throttling-method=simulate --preset=perf` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
