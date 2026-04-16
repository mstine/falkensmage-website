---
phase: 1
slug: theme-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Hugo build validation + browser DevTools manual inspection |
| **Config file** | `hugo.toml` |
| **Quick run command** | `hugo server --buildDrafts` |
| **Full suite command** | `hugo --minify` (no build errors) + browser DevTools inspection of kitchen sink page |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `hugo server --buildDrafts`
- **After every plan wave:** Run `hugo --minify` + visual inspection of kitchen sink at 375px
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INFRA-01 | — | N/A | build | `hugo server --buildDrafts 2>&1 \| grep -i error` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | INFRA-02 | — | HTTPS baseURL | config | `grep baseURL hugo.toml` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | THEME-01 | — | N/A | manual — DevTools | `hugo server` → DevTools → `:root` custom properties | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | THEME-02 | — | N/A | manual — Network tab | `hugo server` → Network tab → fonts load once, `font-display: swap` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | THEME-03 | — | N/A | manual — DevTools + Performance | `hugo server` → kitchen sink → hover glow → no paint rects | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 2 | THEME-04 | — | N/A | visual — kitchen sink | `hugo server` → kitchen sink page | ❌ W0 | ⬜ pending |
| 01-03-03 | 03 | 2 | THEME-05 | — | N/A | manual — DevTools device toolbar | `hugo server` → DevTools → 375px → no overflow | ❌ W0 | ⬜ pending |
| 01-03-04 | 03 | 2 | THEME-06 | — | N/A | visual — kitchen sink | `hugo server` → kitchen sink page → sigil arcs visible | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 1 | THEME-07 | — | N/A | build | `hugo` — no errors; `ls themes/arcaeon/` matches structure | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `brew install hugo` — Hugo Extended not installed
- [ ] `npm init -y` + `npm install @fontsource-variable/cinzel @fontsource-variable/space-grotesk` — font packages
- [ ] `themes/arcaeon/` directory structure — theme scaffold
- [ ] `themes/arcaeon/assets/css/main.css` — main stylesheet
- [ ] `themes/arcaeon/layouts/_default/baseof.html` — base template
- [ ] `themes/arcaeon/layouts/index.html` — homepage template
- [ ] `content/kitchen-sink.md` — demo content page (draft: true)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| ARCÆON CSS custom properties resolve in DevTools | THEME-01 | Browser rendering — no CLI equivalent | Open kitchen sink → DevTools → Computed → verify `:root` custom properties |
| Cinzel + Space Grotesk render with no FOIT | THEME-02 | Font rendering behavior | Network tab → fonts load once; page text visible immediately on reload |
| Glow effects GPU-composited, no box-shadow | THEME-03 | GPU compositing requires Performance panel | DevTools → Performance → record hover → check for paint rects |
| Dark backgrounds alternate with Triad Rule | THEME-04 | Visual design validation | Kitchen sink → sections alternate Void Purple / Deep Indigo |
| No horizontal scroll at 375px | THEME-05 | Responsive layout check | DevTools → device toolbar → 375px → no horizontal overflow |
| Sigil arcs render at correct opacity | THEME-06 | Visual rendering | Kitchen sink → sigil elements visible at ~0.3 opacity |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
