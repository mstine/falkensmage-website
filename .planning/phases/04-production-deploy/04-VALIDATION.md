---
phase: 4
slug: production-deploy
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | Hugo build + shell assertions (no test framework — infra/deploy phase) |
| **Config file** | `.github/workflows/hugo.yml` |
| **Quick run command** | `hugo --minify --environment production 2>&1` |
| **Full suite command** | `hugo --minify --environment production && test -f public/CNAME && test -f public/favicon.ico && test -f public/favicon.svg` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `hugo --minify --environment production 2>&1`
- **After every plan wave:** Run full suite command (build + static asset checks)
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | INFRA-03 | — | N/A | build | `hugo --minify --environment production` | ✅ | ⬜ pending |
| 4-01-02 | 01 | 1 | INFRA-03 | — | N/A | file-check | `test -f .github/workflows/hugo.yml` | ❌ W0 | ⬜ pending |
| 4-01-03 | 01 | 1 | INFRA-04 | — | N/A | file-check | `test -f static/CNAME && cat static/CNAME` | ❌ W0 | ⬜ pending |
| 4-01-04 | 01 | 1 | INFRA-05 | — | N/A | file-check | `test -f static/favicon.ico && test -f static/favicon.svg` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `.github/workflows/hugo.yml` — GitHub Actions workflow for Hugo build + deploy
- [ ] `static/CNAME` — Custom domain persistence file
- [ ] `static/favicon.ico` — ICO favicon (multi-size)
- [ ] `static/favicon.svg` — SVG favicon

*These are the phase deliverables themselves — no separate test framework needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| HTTPS loads without warnings | INFRA-04 | Requires live DNS propagation + GitHub cert issuance | Push to main, wait for deploy, visit https://falkensmage.com in browser |
| Custom domain survives deploy | INFRA-04 | Requires actual deploy cycle on GitHub Pages | Push second commit after initial deploy, verify domain still resolves |
| Favicon visible in browser tab | INFRA-05 | Visual verification at 16x16 | Open site in browser, check tab icon at multiple sizes |
| DNS A records resolve correctly | INFRA-04 | Requires DNS propagation | `dig falkensmage.com +short` should return GitHub Pages IPs |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
