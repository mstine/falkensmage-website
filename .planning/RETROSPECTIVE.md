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

## Milestone: v1.1 — Offer Pages

**Shipped:** 2026-07-02
**Phases:** 1 (Phase 6) | **Plans:** 3 | **Timeline:** 1 day

### What Was Built

- New `/work/` Hugo section — a "Work With Me" hub plus three offer pages (The Query $250 tarot, The Cast $325 astrology, The Daemon $4,500 consult-gated coaching), each a voiced sales page with a Cal.com link-out CTA
- Single-source `[params.booking]` config in `hugo.toml` — templates structurally dereference the booking key, never a hardcoded URL (one-place swap for OFFER-F1)
- Homepage secondary CTA repointed from a bare `mailto:` to the `/work/` hub (NAV-01)
- `tests/validate-phase-06.sh` — 32-check acceptance gate proving all 8 requirement IDs, all four OFFERQ-02 budget legs, and a concrete consult-gate check on The Daemon
- Offer-page sales redesign (UAT gap closure) — price-as-hero, lede, scannable facet cards, pull-quotes, CTA reassurance; one palette-vars-only `arcaeon` CSS extension

### What Worked

- **Templates-before-content sequencing (Wave 1 plumbing first).** The offer template was built to dereference `[params.booking]` and compose only from `arcaeon` classes *before* any content landed — so OFFER-05 (no hardcoded URLs) and OFFERQ-01 (reuse-only) became properties of the render path, not per-page discipline.
- **Plan-checker caught two real validation gaps before execution.** OFFERQ-02's mobile-first/WCAG legs were unasserted and OFFER-04's consult-gate check was prose, not a grep. Folding both into 06-03 before executing meant the phase's own gate actually tested what it claimed.
- **The human UAT gate caught what every automated check missed.** All 32 script checks and 11 verifier truths passed on offer pages a human immediately called flat and weak. This is the Generator self-evaluation blind spot exactly — structure verified, desire didn't.
- **Live-proof iteration for the design fix.** Instead of firing the formal diagnose→plan→execute gap-closure pipeline at a taste problem, redesigned one page live against a running `hugo server`, got approval on the real thing, then rolled out. Faster and truer for a design decision.

### What Was Inefficient

- **The spec produced the flatness, not the execution.** The CONTEXT constraints "voiced pitch, not a spec sheet" + "no new design language, pure `arcaeon` reuse" jointly optimized for voice + reuse + budgets and silently under-specified sales-page craft and visual hierarchy. The pages were built exactly to spec — and the spec was the gap.
- **"Pure reuse" got read as "minimal."** The first-pass offer template deployed almost none of the graphical vocabulary `arcaeon` already had (sigils, glow, cards, section alternation). Reuse-only isn't the same as good; here it meant flat.
- **Phase 6 was hand-registered into ROADMAP.md and didn't resolve.** The `roadmap.get-phase` parser needs a `### Phase N:` heading; the milestone-scoping session wrote a decorative heading instead, so planning couldn't start until it was re-registered. Machine-readable format matters when a human authors roadmap entries.

### Patterns Established

- **Front-matter-driven page structure** (`lede`, `what_you_get`, `who_for`, `pull_quote`, `reassurance`) with graceful `with`/`range` guards — one template serves both rich and minimal pages, and content authors add structure without touching templates.
- **Conscious design-system amendment** — when a "no new CSS" fence is what produces the bad outcome, extend the system with a named, palette-vars-only block and record *why* (extends vs. forks). Not silent scope creep.
- **Live-proof iteration for taste/design gaps** — for a static site, iterate a proof against the running server before invoking the formal gap-closure machinery; the machinery root-causes bugs, and taste isn't a bug.

### Key Lessons

1. **Automated checks verify structure, not desire.** 32 script checks + 11 verifier truths all passed on pages a human called weak in one sentence. Keep the human gate, and aim its questions squarely at the Core Value (comprehension/UX), because that's the one thing greps can't see.
2. **A "pure reuse / no new design" constraint can be the defect.** When a fence causes the bad outcome, amend it consciously rather than executing harder inside it. Reuse-only ≠ good.
3. **Human-authored roadmap entries must match the parser's format.** A `### Phase N:` heading, not decorative prose. Re-registration cost a step before planning could begin.
4. **Coherence over ceremony (again).** A design/taste fix on a static site didn't need the diagnose→plan→execute subagent pipeline — a live proof + approval was the coherent move. Same instinct as v1.0's acknowledge-and-ship.

### Cost Observations

- Model mix: opus planner, sonnet executors + verifier + plan-checker; single focused session.
- Notable: the two efficiency wins were the plan-checker catching validation gaps pre-execution, and the live-proof loop replacing a heavier gap-closure round for the design fix.

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Phases | Key Change |
|-----------|--------|------------|
| v1.0 | 5 | Established GSD workflow baseline — discuss → plan → execute → verify → audit → gap-close → archive |
| v1.1 | 1 | Human UAT gate + live-proof iteration — caught a Core-Value gap all automated checks passed, fixed it live instead of via the formal gap-closure pipeline |

### Cumulative Quality

| Milestone | Tests | Coverage | Zero-Dep Additions |
|-----------|-------|----------|-------------------|
| v1.0 | 3 validation scripts (46 + 18 + 39 = 103 checks) | 42/42 requirements | 0 runtime JS, 0 external CDNs, 0 Node in CI |
| v1.1 | +1 validation script (validate-phase-06.sh, 32 checks) | 8/8 v1.1 requirements | 0 runtime JS, 0 external CDNs, CTAs link OUT (no widget) |

### Top Lessons (Verified Across Milestones)

1. **Coherence over bookkeeping/ceremony.** v1.0 acknowledged-and-shipped past frontmatter drift; v1.1 fixed a design gap with a live proof instead of the full subagent pipeline. Both times, the coherent move beat the ceremonial one.
2. **Automated verification proves structure; humans prove desire.** v1.1's flat offer pages passed every script and verifier truth. The human gate is where Core-Value (comprehension/UX) claims actually get tested.
3. **Hugo/toolchain reality over docs.** v1.0's API-version lessons (`.Process` not `.Format`, `@v6` not `@v4`) and v1.1's parser-format requirement both reward verifying in the running system over trusting the spec.
