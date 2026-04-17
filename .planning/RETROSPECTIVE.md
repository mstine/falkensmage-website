# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-04-17
**Phases:** 5 | **Plans:** 13 | **Timeline:** 2 days

### What Was Built

- Portable `arcaeon` Hugo theme with two-tier CSS token system (palette truth + semantic aliases), three GPU-composited glow variants, self-hosted variable fonts, Triad Rule section classes
- Full single-page site — hero with WebP/JPEG Magus image art direction, identity statement, 8-platform social ghost-card grid, Radiant Core mailto CTA, build-time RSS "Currently" section, footer — all sourced from `content/_index.md` front matter
- Build-time dynamic layer: `resources.GetRemote` + `try` wrapper pulling from `feralarchitecture.com/feed` with graceful static fallback, zero runtime JS
- Production deploy: Hugo Extended 0.160.1 pinned in GitHub Actions (`configure-pages@v6` + `deploy-pages@v5`), custom domain with HTTPS enforced at https://falkensmage.com, lemniscate sigil favicon (SVG + ICO committed as static artifact)
- Gap-closure phase (Phase 5) that turned a `gaps_found` audit into a clean close — nested `<footer>` removed, font double-fetch eliminated via `css.Build` externals slice, traceability backfilled, `npm ci` removed from CI

### What Worked

- **Two-tier ARCAEON token naming decided in Phase 1.** Palette truth (`--arcaeon-*`) + semantic aliases (`--color-*`) held as load-bearing convention for every subsequent plan. Zero refactors required downstream.
- **`::before` = glow, `::after` = sigil pseudo-element convention.** Cheap to establish, avoided every collision as components piled on.
- **Front matter as the single content data layer.** Zero hardcoded strings in partials. Copy changes don't touch templates. Paid back immediately when social links were added.
- **Inserting Phase 5 for gap closure instead of trying to squeeze fixes into Phase 4.** Milestone audit surfaced 3 real gaps (A11Y-01, PERF-01, PERF-03). A dedicated three-wave phase (code fixes → hygiene/backfill → verification) landed them cleanly with atomic commits and a passing re-audit. Trying to inline the fixes would have smeared the trail.
- **Clean-rebuild verification discipline** (`rm -rf public/ resources/_gen/` before assertions). Established in Phase 5 after stale-state masking nearly hid a bug. Worth locking in as default.
- **`css.Build` externals slice with exact absolute path strings.** After PERF-03 investigation, discovered glob patterns empirically fail with esbuild's CSS `url()` resolver. Only the exact path string preserves `url()` byte-identically.

### What Was Inefficient

- **First pass on fonts used relative `../fonts/` paths.** Worked locally, but fingerprinted CSS caused preload `href` and `@font-face src` to diverge under minify — double-fetch. Should have jumped straight to absolute `/fonts/` paths with `crossorigin` attribute.
- **Hero image was untracked at Phase 4 push time.** Missing from the deployed artifact; Rule 1 auto-fix in Plan 04-02. Easy to miss — add a pre-deploy tracked-assets check next time.
- **`npm ci` step left in CI workflow after Phase 3 migrated fonts to committed WOFF2.** Vestigial step removed in Phase 5. When source-of-truth moves, surface all downstream CI references in the same change, not a later cleanup phase.
- **4 SUMMARY.md files shipped without `requirements-completed` frontmatter.** Created an invisible traceability gap the milestone audit caught. A SUMMARY template check (frontmatter schema) would surface this at plan close rather than at milestone close.
- **`tests/validate-phase-01.sh` font paths not synced with Plan 05-01's architecture move.** Surfaced during Phase 5 clean-rebuild gate — test-path drift is silent until a regression run actually runs. Same surface-at-the-source lesson as `npm ci`.
- **`gsd-sdk query` CLI referenced by the workflow doesn't exist on this machine** — only `gsd-sdk run/auto/init` and `gsd-tools.cjs`. Workflow orchestration fell back to manual steps cleanly, but the skill prompt ought to match the installed toolchain.

### Patterns Established

- **Two-tier design token naming** (palette truth + semantic aliases) — reusable across any theme project.
- **Pseudo-element convention** (`::before` = glow, `::after` = sigil) — structural rule, not a style.
- **Front matter as content data layer** with `| default` fallbacks — copy edits without template edits.
- **Draft-only kitchen-sink demo** (`draft: true`, `type: kitchen-sink`) — design system correctness gate excluded from production build.
- **Gap-closure phase as first-class citizen** — when an audit flags issues, an explicit multi-plan phase (fix → hygiene → verify) beats inline patching.
- **Clean-rebuild verification gate** (`rm -rf public/ resources/_gen/` before assertions) — catches stale-state masking.
- **Test-path synchronization discipline** — when source-of-truth moves, update tests + CI in the same change.
- **Structural invariants embedded in validation scripts** — not separate `validate-phase-04.sh` for every new concern; assertions live with the phase they guard.

### Key Lessons

1. **Fingerprinted CSS will break font preload/src parity unless the externals slice names the exact absolute path.** Globs don't work with esbuild's CSS `url()` resolver. Lock this in: `/fonts/...` absolute paths, `css.Build` externals dict, `crossorigin` on preload, preload `href` must be byte-identical to the resolved `@font-face src`.
2. **Milestone audit is the authoritative close record.** The open-artifact audit tool flags frontmatter drift (e.g., VERIFICATION.md `status: human_needed` when HUMAN-UAT.md is `status: complete`). When the substantive audit shows closure, record the drift as deferred and ship. Don't let bookkeeping block aliveness.
3. **When a gap-closure phase fixes an issue, also update the tests + CI that referenced the old state.** Drift is silent until the next regression run.
4. **Hugo 0.160.1 API reality checks matter** — `.Process "webp"` not `.Format`, `feralarchitecture.com/feed` not `substack.com`, `configure-pages@v6` not `@v4`. Research docs lag actual releases by weeks. Verify in the running system.
5. **Coherence over bookkeeping.** 5 "open items" at milestone close were all substantively closed per audit. Acknowledge-and-ship was the coherent move. Resolving the drift would have spent energy without changing the reality.

### Cost Observations

- Model mix: not tracked per-session for this milestone. Consider capturing in future milestones for cost ratio analysis.
- Sessions: ~3 per phase estimate; milestone completed in 2 calendar days of focused work.
- Notable: Phase 5 (gap closure) was small-scoped and high-throughput — 3 plans in ~8 minutes total. Audit → dedicated phase → close pipeline was the efficiency win.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Key Change |
|-----------|--------|------------|
| v1.0 | 5 | Established GSD workflow baseline — discuss → plan → execute → verify → audit → gap-close → archive |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 3 validation scripts (46 + 18 + 39 = 103 checks) | 42/42 requirements | 0 runtime JS, 0 external CDNs, 0 Node in CI |

### Top Lessons (Verified Across Milestones)

*Will accumulate once v1.1+ ship. For now, v1.0 lessons stand on their own.*
