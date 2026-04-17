---
phase: 03-dynamic-layer-quality
asvs_level: 1
audited: 2026-04-16
auditor: gsd-security-auditor
result: SECURED
threats_total: 9
threats_closed: 9
threats_open: 0
---

# Phase 03 Security Audit — Dynamic Layer + Quality

## Summary

**Phase:** 03 — Dynamic Layer + Quality
**Threats Closed:** 9/9
**ASVS Level:** 1
**Block on:** high

All declared threats verified closed. No open mitigations. No unregistered threat flags.

---

## Threat Verification

| Threat ID | Category | Disposition | Evidence |
|-----------|----------|-------------|----------|
| T-03-01 | Spoofing | accept | RSS URL hardcoded at `currently.html:2` — `$rssURL := "https://feralarchitecture.com/feed"`. No user input controls feed selection. Logged in accepted risks below. |
| T-03-02 | Tampering | mitigate | `currently.html:30` — RSS title rendered as `{{ $latestPost.title }}` with no `safeHTML`; Hugo default HTML context escaping active. `htmlUnescape` at line 12 decodes CDATA entities before Hugo re-escapes on output — does not bypass escaping. |
| T-03-03 | Tampering | mitigate | `currently.html:25` — RSS link rendered as `href="{{ $latestPost.link }}"` with no `safeURL`; Hugo default attribute context escaping active. |
| T-03-04 | Information Disclosure | mitigate | `currently.html:7` — `warnf "Currently section: RSS fetch failed: %s"` routes errors to build stderr only. No error content rendered into HTML output. |
| T-03-05 | Denial of Service | mitigate | `currently.html:5` — `try` wrapping on `resources.GetRemote` prevents build failure on RSS unavailability. `currently.html:33-38` — fallback link to `feralarchitecture.substack.com` renders when RSS fetch yields no title. |
| T-03-06 | Elevation of Privilege | accept | Static HTML site. No server-side execution, no user sessions, no runtime input processing. Logged in accepted risks below. |
| T-03-07 | Information Disclosure | accept | Meta description is intentional public identity copy. `baseof.html:7` — hardcoded identity statement. No sensitive data. Logged in accepted risks below. |
| T-03-08 | Tampering | accept | OG image path hardcoded at `baseof.html:26` — `resources.Get "images/magus-hero.jpg"`. No user input controls path selection. Logged in accepted risks below. |
| T-03-09 | Spoofing | accept | Canonical URL hardcoded at `baseof.html:41` — `href="https://falkensmage.com"`. No dynamic input. Logged in accepted risks below. |

---

## Accepted Risks Log

| Threat ID | Accepted Risk | Rationale |
|-----------|---------------|-----------|
| T-03-01 | RSS feed URL is a trusted first-party domain (feralarchitecture.com) with no user-controlled input. Feed compromise would require compromise of Matt's own Substack. | Risk surface is equivalent to trusting one's own publishing infrastructure — acceptable for a personal site. |
| T-03-06 | No elevation-of-privilege surface exists. Static site compiled to HTML at build time with no server-side code path. | Static hosting on GitHub Pages provides no runtime execution environment to elevate into. |
| T-03-07 | Meta description exposes identity information (name, role, domain) intentionally. This is the designed function of Open Graph and meta description tags. | Public identity disclosure is the purpose of the tags, not a vulnerability. |
| T-03-08 | OG image asset path is hardcoded in template. Modifying the image would require write access to the repository. | Same trust boundary as all other template content. No additional risk. |
| T-03-09 | Canonical URL is hardcoded to `https://falkensmage.com`. Spoofing would require DNS or repository compromise. | Equivalent trust boundary to all other hardcoded site configuration. |

---

## Unregistered Threat Flags

None. The `## Threat Flags` section in `03-02-SUMMARY.md` explicitly states no new attack surface was introduced. No unregistered flags from either plan summary.

---

## Files Audited

| File | Role |
|------|------|
| `themes/arcaeon/layouts/partials/sections/currently.html` | RSS fetch, title/link rendering, error handling, fallback |
| `themes/arcaeon/layouts/_default/baseof.html` | OG tags, Twitter Card, canonical URL, meta description |
| `.planning/phases/03-dynamic-layer-quality/03-01-PLAN.md` | Threat model source (T-03-01 through T-03-06) |
| `.planning/phases/03-dynamic-layer-quality/03-02-PLAN.md` | Threat model source (T-03-07 through T-03-09) |
| `.planning/phases/03-dynamic-layer-quality/03-01-SUMMARY.md` | Execution summary, inline threat verification |
| `.planning/phases/03-dynamic-layer-quality/03-02-SUMMARY.md` | Execution summary, threat flags section |
