---
phase: 04-production-deploy
plan: 02
subsystem: infra
tags: [github-pages, github-actions, dns, cname, custom-domain, deployment]

# Dependency graph
requires:
  - phase: 04-production-deploy/04-01
    provides: GitHub Actions workflow, CNAME file, favicon ICO — all deployed artifacts
provides:
  - Public GitHub repo at github.com/mstine/falkensmage-website
  - GitHub Pages live deployment with Actions workflow source
  - Custom domain falkensmage.com set in repo Settings (authoritative)
  - Two successful workflow runs confirming CI/CD pipeline and custom domain persistence
  - Hero image asset committed and included in deployed artifact
affects: [future pushes to main auto-deploy]

# Tech tracking
tech-stack:
  added: [gh CLI repo create, GitHub Pages API]
  patterns: [gh api for Pages config pre-deploy, CNAME in Settings as authoritative custom domain]

key-files:
  created: []
  modified:
    - themes/arcaeon/assets/images/magus-hero.jpg

key-decisions:
  - "Hero image committed as tracked git asset (was untracked) — build succeeds with image in deployed artifact"
  - "Custom domain set in repo Settings before first successful deploy — baseURL resolves to https://falkensmage.com/ in CI"
  - "Two successful workflow runs verified before checkpoint — custom domain persistence confirmed"

patterns-established:
  - "gh repo create --public --source=. --remote=origin --push creates repo and pushes in one command"
  - "gh api repos/{owner}/{repo}/pages POST build_type=workflow enables Actions source immediately"
  - "gh api repos/{owner}/{repo}/pages PUT cname=... sets custom domain before first deploy"

requirements-completed: [INFRA-03, INFRA-04]

# Metrics
duration: 8min
completed: 2026-04-17
---

# Phase 4 Plan 2: Production Deploy Summary

**falkensmage.com live at HTTPS with GitHub Pages CDN, custom domain persisting across deploys, four GitHub Pages IPs in DNS — the site is shipped**

## Performance

- **Duration:** ~8 min automated + ~30 min DNS propagation/cert provisioning wait
- **Started:** 2026-04-17T13:15:00Z
- **Completed:** 2026-04-17T13:33:00Z
- **Tasks:** 2 of 2 complete
- **Files modified:** 1 (hero image added to git tracking)

## Accomplishments
- GitHub repo `mstine/falkensmage-website` created as public repo
- GitHub Pages enabled with `build_type=workflow` (Actions source, not branch deploy)
- Custom domain `falkensmage.com` set in repo Settings before first deploy — `configure-pages@v6` resolves `base_url` to `https://falkensmage.com/` in CI
- First workflow run: build 35s + deploy 9s = successful
- Hero image committed and second workflow run triggered — build 27s + deploy 10s = successful
- Custom domain persists after second push (confirmed by Pages API returning `cname: falkensmage.com`)
- DNS A records configured at Namecheap: all four GitHub Pages IPs (185.199.108-111.153) resolve for falkensmage.com
- www CNAME pointing to mstine.github.io configured
- HTTPS certificate provisioned; `https_enforced: true` confirmed via GitHub Pages API
- Three consecutive successful workflow runs on main confirmed
- **falkensmage.com is live**

## Task Commits

1. **Task 1: Create GitHub repo and push** — Infrastructure via `gh` CLI (no tracked file changes from repo creation itself)
2. **[Rule 1 - Bug] Hero image asset committed** — `e1ae249` (feat)

**Note:** Task 2 is a `checkpoint:human-verify` — DNS configuration at Namecheap and final live site verification.

## Files Created/Modified
- `themes/arcaeon/assets/images/magus-hero.jpg` — Hero image added to git tracking; was untracked, causing image to be missing from deployed artifact

## Decisions Made
- Hero image committed as a tracked git asset (Rule 1 auto-fix — it was untracked, the build succeeds without it only because Hugo gracefully handles missing images, but the actual deployed page would have no hero)
- Custom domain set in Settings before first deploy — this is the load-bearing step ensuring `steps.pages.outputs.base_url` returns `https://falkensmage.com/` and all asset paths resolve correctly

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Hero image was untracked, missing from deployed artifact**
- **Found during:** Task 1 (after repo creation, `git status` revealed untracked file)
- **Issue:** `themes/arcaeon/assets/images/magus-hero.jpg` existed locally but was never committed. Would deploy without the Magus hero image.
- **Fix:** Added to git tracking, committed, pushed — triggered second workflow run which deployed with the image included
- **Files modified:** `themes/arcaeon/assets/images/magus-hero.jpg`
- **Verification:** Second workflow run succeeded; `git status` clean after commit
- **Committed in:** `e1ae249`

---

**Total deviations:** 1 auto-fixed (Rule 1 - Bug)
**Impact on plan:** Essential fix — hero image is the primary visual element of the site. No scope creep.

## Issues Encountered
- None beyond the hero image tracking issue (auto-fixed per Rule 1)

## User Setup Required

Matt completed DNS configuration at Namecheap:

1. Deleted existing `@` CNAME pointing to `target.substack-custom-domains.com` (confirmed unused Substack placeholder — Feral Architecture newsletter runs on feralarchitecture.com, unaffected)
2. Added four A records (Host: `@`): 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153
3. Added CNAME: Host: `www`, Value: `mstine.github.io`
4. Enabled "Enforce HTTPS" in GitHub Settings > Pages after cert provisioned

**Verified live:**
```
dig falkensmage.com A +short
185.199.111.153
185.199.108.153
185.199.109.153
185.199.110.153

gh api repos/mstine/falkensmage-website/pages --jq '{cname,https_enforced,build_type}'
{"build_type":"workflow","cname":"falkensmage.com","https_enforced":true}
```

## Next Phase Readiness

**The project is complete. All four phases and ten plans delivered.**

falkensmage.com is live. Full delivery:
- ARCÆON theme with Electric Violet / Neon Magenta palette
- Two-tier CSS custom property system (palette truths + semantic aliases)
- Cinzel + Space Grotesk variable fonts, self-hosted
- Lemniscate sigil system
- Hero section with Magus image
- Social card grid (Substack, Instagram, TikTok, Bluesky, LinkedIn)
- Build-time Feral Architecture RSS integration
- OG / Twitter card meta tags
- Lemniscate favicon (SVG + ICO)
- Sub-1s load on 3G, WCAG AA accessibility
- Automatic deploys from main via GitHub Actions

---
*Phase: 04-production-deploy*
*Completed: 2026-04-17*

## Self-Check: PASSED
- File exists: `.planning/phases/04-production-deploy/04-02-SUMMARY.md` ✓
- Commit `e1ae249` exists in git log ✓
- GitHub repo `mstine/falkensmage-website` exists and is PUBLIC ✓
- Pages build_type: `workflow` ✓
- Pages cname: `falkensmage.com` ✓
- Pages https_enforced: `true` ✓
- DNS A records: all four GitHub Pages IPs confirmed ✓
- Three consecutive successful workflow runs confirmed ✓
- User confirmed site live with HTTPS in browser ✓
