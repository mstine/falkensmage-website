---
phase: 2
slug: static-content
status: secured
threats_open: 0
asvs_level: 1
created: 2026-04-16
---

# Phase 2 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Browser → External platforms | Social link `<a>` elements open third-party URLs | URL only, no user data |
| Browser → Email client | `mailto:` link triggers OS email handler | Email address (public) |
| Build-time → Runtime | Hugo processes images and templates at build; output is static HTML/CSS | No runtime data processing |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-02-01 | Information Disclosure | Social link `<a target="_blank">` | mitigate | `rel="noopener noreferrer"` on all 8 social links | closed |
| T-02-02 | Spoofing | `mailto:` link | accept | Native OS handler — no spoofing vector. No `target="_blank"` on mailto. | closed |
| T-02-03 | Tampering | SVG icon injection | accept | Icons are static inline SVGs authored at build time, not user-supplied. No dynamic SVG content. No injection vector. | closed |

*Status: open · closed*

---

## Accepted Risks

| Threat ID | Risk | Justification |
|-----------|------|---------------|
| T-02-02 | mailto link could be harvested by scrapers | Email address is intentionally public (contact CTA). Acceptable risk for a personal brand site. |
| T-02-03 | SVG content is inline HTML | All SVGs are hand-authored static content with no external input. Re-evaluate if user-supplied SVGs are ever introduced. |

---

## Audit Trail

### Security Audit 2026-04-16

| Metric | Count |
|--------|-------|
| Threats found | 3 |
| Closed | 3 |
| Open | 0 |

**Verification method:** Automated — `grep -c 'rel="noopener noreferrer"' public/index.html` returned 8 (all social links). `grep -c 'mailto:.*target="_blank"'` returned 0 (no target on mailto). SVG partials inspected — all static `currentColor` paths, no dynamic content.

**ASVS L1 assessment:** Phase 2 introduces no authentication, session management, access control, user input, or cryptographic operations. ASVS categories V2–V6 are not applicable for a static public page. The only applicable control (`rel="noopener noreferrer"` on external links) is implemented.
