---
phase: 01
slug: theme-foundation
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-16
---

# Phase 01 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Build-time only | No user input, no runtime code, no network requests. Static CSS design system. | None — all files are static assets generated at build time |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Spoofing | baseURL | mitigate | `baseURL = "https://falkensmage.com/"` set in hugo.toml from day one — prevents mixed-content and ensures HTTPS | closed |
| T-01-02 | Information Disclosure | node_modules in git | mitigate | `.gitignore` includes `node_modules/` — no npm packages committed to repo | closed |
| T-01-03 | Tampering | npm supply chain | accept | Fonts are static WOFF2 binary files copied at build time; no runtime npm dependency; risk is minimal for font packages | closed |
| T-01-04 | Information Disclosure | kitchen-sink page | mitigate | `draft: true` in front matter — excluded from `hugo --minify` production builds. Only visible with `--buildDrafts` flag | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| AR-01-01 | T-01-03 | Static WOFF2 binary files from @fontsource-variable packages. No runtime npm dependency. Font files are copied once at setup, not fetched at build/deploy time. Supply chain risk is negligible for inert binary assets. | Claude (automated) | 2026-04-16 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-16 | 4 | 4 | 0 | Claude (inline verification) |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-16
