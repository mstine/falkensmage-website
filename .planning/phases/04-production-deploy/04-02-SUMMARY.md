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

**Public GitHub repo created, GitHub Actions pipeline deployed successfully, custom domain falkensmage.com set — awaiting DNS configuration at Namecheap to go live**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-04-17T13:15:00Z
- **Completed:** 2026-04-17T13:18:30Z (Task 1 only; Task 2 is human checkpoint)
- **Tasks:** 1 of 2 automated tasks complete; Task 2 is DNS checkpoint
- **Files modified:** 1 (hero image added to git tracking)

## Accomplishments
- GitHub repo `mstine/falkensmage-website` created as public repo
- GitHub Pages enabled with `build_type=workflow` (Actions source, not branch deploy)
- Custom domain `falkensmage.com` set in repo Settings before first deploy — `configure-pages@v6` resolves `base_url` to `https://falkensmage.com/` in CI
- First workflow run: build 35s + deploy 9s = successful
- Hero image committed and second workflow run triggered — build 27s + deploy 10s = successful
- Custom domain persists after second push (confirmed by Pages API returning `cname: falkensmage.com`)

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

**DNS configuration required to complete this plan.** See Task 2 checkpoint details:

1. Namecheap > Domain List > falkensmage.com > Manage > Advanced DNS
2. DELETE existing `@` CNAME pointing to `target.substack-custom-domains.com`
3. ADD four A records (Host: `@`, TTL: Automatic):
   - `185.199.108.153`
   - `185.199.109.153`
   - `185.199.110.153`
   - `185.199.111.153`
4. ADD CNAME: Host: `www`, Value: `mstine.github.io`, TTL: Automatic
5. Wait ~30 minutes, then verify DNS and HTTPS
6. Enable "Enforce HTTPS" in GitHub Settings > Pages after cert provisions

Verification commands after DNS propagation:
```bash
dig falkensmage.com A +short
# Expected: 185.199.108.153, 185.199.109.153, 185.199.110.153, 185.199.111.153

dig www.falkensmage.com +short
# Expected: mstine.github.io

curl -I https://falkensmage.com
# Expected: HTTP/2 200
```

## Next Phase Readiness
- All automated deployment infrastructure is complete and verified
- Two successful CI/CD runs confirmed
- Custom domain persistence confirmed across pushes
- Blocked on DNS propagation (Namecheap config) before HTTPS is live
- Once DNS is configured and HTTPS provisions, the site is fully live — no additional code changes needed

---
*Phase: 04-production-deploy*
*Completed: 2026-04-17 (Task 1 of 2; awaiting DNS checkpoint)*

## Self-Check: PASSED
- File exists: `.planning/phases/04-production-deploy/04-02-SUMMARY.md` ✓
- Commit `e1ae249` exists in git log ✓
- GitHub repo `mstine/falkensmage-website` exists and is PUBLIC ✓
- Pages build_type: `workflow` ✓
- Pages cname: `falkensmage.com` ✓
- Two successful workflow runs confirmed ✓
