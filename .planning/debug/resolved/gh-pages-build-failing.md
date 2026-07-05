---
slug: gh-pages-build-failing
status: resolved
trigger: GitHub Pages build/deploy workflow keeps failing on main
created: 2026-07-05
updated: 2026-07-05
---

# Debug: GH Pages build keeps failing

## Current Focus
hypothesis: The `Install Dart Sass` step (`sudo snap install dart-sass`) fails intermittently with Snap Store rate-limiting, and the step is unnecessary because the theme uses no Sass.
next_action: (resolved)

## Evidence
- timestamp: 2026-07-05 — Runs 28758197112 / 28758169843 (manual dispatch) failed in ~10s at the "Install Dart Sass" step: `error: cannot install "dart-sass": too many requests`.
- timestamp: 2026-07-05 — Scheduled run 28738639407 (48s) also failed (same flaky snap step).
- timestamp: 2026-07-04 — Run 28716614913 was a DIFFERENT, transient failure: build succeeded, artifact uploaded, but `actions/deploy-pages@v5` returned `Deployment failed, try again later.` — a GitHub Pages platform hiccup, self-resolving (same commit built green before and after). Not code-actionable.
- grep: zero `.scss`/`.sass` files in repo; theme's only CSS pipeline is `css.Build` (esbuild, native to Hugo Extended) in `themes/arcaeon/layouts/_default/baseof.html`.
- local: `hugo --minify` builds all 10 pages in ~614ms with NO sass binary on PATH — proving Dart Sass is never invoked.
- Pages config verified: `build_type: workflow`, source branch main, CNAME + HTTPS approved. Config was never the problem.

## Eliminated
- hypothesis: GitHub Pages source misconfigured → REJECTED (`gh api .../pages` shows correct `build_type: workflow`).
- hypothesis: Hugo build itself broken → REJECTED (local build succeeds; CI reached build fine on runs that got past the snap step).

## Resolution
root_cause: The workflow's `Install Dart Sass` step (`sudo snap install dart-sass`) is both (a) unnecessary — no Sass in the project — and (b) flaky, failing under Snap Store rate-limiting with "too many requests". This is the step breaking the recent runs.
fix: Removed the `Install Dart Sass` step from `.github/workflows/hugo.yml` (commit 9ea0d7a). Left a comment documenting why, so it isn't re-added unless `.scss` is introduced.
verification: Pushed to main → run 28758288494 completed with **success**.
files_changed: .github/workflows/hugo.yml

## Note
The 2026-07-04 deploy-side `Deployment failed, try again later` was a separate transient GitHub Pages platform error, not addressed by this fix and not reproducible. If deploy-side failures recur, re-run the job; if persistent, check GitHub status / Pages quotas.
