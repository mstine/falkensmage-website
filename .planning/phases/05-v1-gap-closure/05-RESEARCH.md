# Phase 5: v1.0 Gap Closure — Research

**Researched:** 2026-04-17
**Domain:** Hugo css.Build internals, HTML5 landmark semantics, bash regex, CI workflow hygiene, GSD documentation frontmatter
**Confidence:** HIGH (all fixes empirically validated against live build output)

---

<user_constraints>
## User Constraints (from v1.0-MILESTONE-AUDIT.md — LOCKED decisions)

Phase 5 has no `05-CONTEXT.md` because the audit doc IS the decision register. Every fix below is a direct closure of an audit-identified gap. No discretion, no alternatives to explore.

### Locked Decisions (from audit)

**Code fixes (Phase 3 tech debt):**
1. **A11Y-01 (nested footer):** index.html wraps `<footer>` around the footer partial, AND the partial itself uses `<footer>` as root. Built HTML has nested `<footer><footer class="...">...</footer></footer>`. Invalid HTML5. MUST fix to exactly one `<footer>` landmark.
2. **PERF-03 (preload/@font-face URL mismatch):** Preload hints point to `/fonts/...`; `css.Build` rewrites `@font-face` `src:` to `./cinzel-...-HASH.woff2` (resolved as `/css/...`). Fonts double-fetched. MUST make preload href === served font URL === @font-face src.
3. **PERF-01 (sub-1s 3G):** Dependent on PERF-03 fix. Verification via structural check of built HTML (preload href matches @font-face src) — Lighthouse measurement optional, not required.
4. **Tech debt (SEO-03 script regex):** `validate-phase-03.sh` line 154 matches `href="https://falkensmage.com"` (no trailing slash) but Hugo emits `href="https://falkensmage.com/"` (with trailing slash). Script reports 32/33 false failure. MUST fix regex to accept either form.

**Code fixes (Phase 4 tech debt):**
5. **CI workflow npm ci hygiene:** Lines 48–49 of `.github/workflows/hugo.yml` run `npm ci` but no subsequent step copies fontsource files anywhere. Committed WOFF2 files in `themes/arcaeon/static/fonts/` + `themes/arcaeon/assets/fonts/` are the actual source of truth. Audit Success Criterion 4 demands ONE consistent choice. Recommended (per audit context): remove `npm ci` entirely; committed WOFF2 files are the intentional source of truth.

**Documentation backfill (SUMMARY frontmatter):**
6. **Phase 1 `requirements-completed` backfill:** `01-02-SUMMARY.md` missing THEME-02, THEME-03. `01-03-SUMMARY.md` missing THEME-04, THEME-05, THEME-06.
7. **Phase 3 `requirements-completed` backfill:** `03-01-SUMMARY.md` missing CURR-01, CURR-02, CURR-03, PERF-03, A11Y-01, A11Y-04. `03-02-SUMMARY.md` missing SEO-01, SEO-02, SEO-03, PERF-01, PERF-02, PERF-04, A11Y-02, A11Y-03.

### Claude's Discretion
- Choice of approach for PERF-03 fix — research below evaluated three approaches empirically, Approach A recommended.
- Decision on whether PERF-01 verification includes Lighthouse measurement (recommended: structural check only — sufficient per audit evidence that "no external dependencies confirmed").
- Wave sequencing and parallelization (research recommends 3 parallel waves — see Wave Sequencing section).

### Deferred Ideas (OUT OF SCOPE)
- Nyquist VALIDATION.md compliance for Phase 3 and 4 — audit notes this as a separate `/gsd-validate-phase 3` and `/gsd-validate-phase 4` follow-up. Do NOT include in Phase 5.
- Phase 4 deploy concerns — audit says live and working.
- All non-listed REQ-IDs — audit says satisfied.
- Any REQUIREMENTS.md copy edits beyond status flips for A11Y-01, PERF-01, PERF-03.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| A11Y-01 | Semantic HTML5 structure — `<header>`, `<main>`, `<section>`, `<footer>`, `<nav>` | Current state: 2 opening `<footer` tags in built HTML. Fix: remove outer wrapper in `index.html` OR change inner root to `<div class="section ...">`. Research recommends removing outer wrapper (preserves existing CSS selectors, minimal blast radius). |
| PERF-03 | Self-hosted fonts with `font-display: swap` and `crossorigin` on preload links — no FOIT, no double-download | Empirically tested three approaches. Approach A works: delete duplicate `assets/fonts/` files + add `externals` option to `css.Build` call. Validated against live build output. |
| PERF-01 | Single page load under 1s on 3G | Derivative of PERF-03. No external CDNs or analytics confirmed. Verify via structural check: preload href exactly equals @font-face src in built CSS. Lighthouse measurement optional. |

</phase_requirements>

---

## Summary

This is a **cleanup phase**, not a build phase. All seven items are well-scoped and empirically confirmed in the live codebase. The interesting work is the PERF-03 fix — the other six items are mechanical.

**The PERF-03 story.** Hugo's `css.Build` is an esbuild wrapper. When CSS source contains `url('/fonts/cinzel-latin-wght-normal.woff2')` AND the same file exists at `themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2`, esbuild's default `file` loader resolves it, copies it alongside the fingerprinted CSS in `/css/`, and rewrites the URL to `./cinzel-latin-wght-normal-HB3QMI3R.woff2`. The preload hint in `<head>` still points to `/fonts/...` (the stable static path), so the browser fetches the font TWICE under two different URLs. The fix requires telling `css.Build` NOT to rewrite these specific URLs. Hugo's `css.Build` `externals` option (a slice of path patterns excluded from bundling) does exactly this — but **only when passed the exact absolute paths, not glob patterns**. Validated empirically: `"/fonts/*"` and `"*.woff2"` both failed to preserve URLs; only `"/fonts/cinzel-latin-wght-normal.woff2"` and `"/fonts/space-grotesk-latin-wght-normal.woff2"` worked.

**Secondary cleanup.** With `externals` set, `css.Build` no longer scans `themes/arcaeon/assets/fonts/` for these files. Those copies become orphan bytes in git. Delete them. Single source of truth: `themes/arcaeon/static/fonts/`.

**Primary recommendation:** Four parallel work streams, three waves.
- **Wave 1 (parallel):** A11Y-01 footer fix + PERF-03 font fix (they touch adjacent lines in the same files but are logically independent). Both re-verify via `hugo` build.
- **Wave 2 (parallel, depends on Wave 1):** Script regex fix + CI workflow npm ci removal + all four SUMMARY frontmatter backfills (these are completely isolated file edits).
- **Wave 3 (serial):** Run `validate-phase-03.sh` end-to-end → expect 33/33. Build with `--baseURL "https://falkensmage.com/"` + verify preload href === @font-face src. Update REQUIREMENTS.md traceability table status flips.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| HTML5 landmark structure | Frontend Server (Hugo template) | — | `index.html` template owns page-level landmark wrappers; partial template owns its own root element. Both belong to Hugo's template tier, not runtime. |
| Font URL resolution | Frontend Server (Hugo css.Build) | Static asset serving | `css.Build` (esbuild) rewrites CSS `url()` at build time. Static files under `themes/arcaeon/static/fonts/` serve via Hugo's static pipeline at runtime (browser fetches `/fonts/...`). The mismatch is a build-time / serve-time coordination bug. |
| Build-time asset validation | Build (bash + grep) | — | `validate-phase-*.sh` scripts run post-build. SEO-03 regex lives in the validation tier, not production HTML. |
| CI workflow | Build Infrastructure (GitHub Actions YAML) | — | `.github/workflows/hugo.yml` defines build steps. `npm ci` is a build-tier concern only. |
| Documentation traceability | Planning (GSD frontmatter) | — | `requirements-completed` YAML keys in SUMMARY.md files. No runtime impact. Consumed by `gsd-audit-milestone`. |

---

## Standard Stack

### Core (already installed — no new packages)

| Tool | Version | Purpose | Notes |
|------|---------|---------|-------|
| Hugo Extended | 0.160.1 | Static site generator + `css.Build` (esbuild wrapper) | `externals` option confirmed supported in `css.Build` dict [CITED: gohugo.io/functions/css/build/] |
| esbuild (embedded in Hugo) | — | CSS bundler, default `file` loader for `.woff2` | `file` loader copies file + rewrites URL unless marked external [CITED: esbuild.github.io/content-types/] |
| bash | system | Validation script runtime | macOS 3.2 and Ubuntu bash 5.x both support `grep -E` extended regex |

No new dependencies. No installs. [VERIFIED: `hugo version` and `bash --version`]

---

## Architecture Patterns

### System Architecture Diagram (build + runtime flow for fonts)

```
SOURCE TIER (git-tracked):
  themes/arcaeon/static/fonts/cinzel-latin-wght-normal.woff2      ─┐
  themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2      ─┤  DUPLICATE
  themes/arcaeon/assets/css/main.css  (contains url('/fonts/…'))  ─┤
  themes/arcaeon/layouts/_default/baseof.html  (preload + css.Build) ─┘
         │
         ▼
BUILD TIER (Hugo 0.160.1):
  [static/fonts/*]  ────────────────────►  public/fonts/cinzel-*.woff2 (stable path)
  [assets/css/main.css] ────►  css.Build(externals: [...])  ────►  public/css/main.min.HASH.css
                                       │         (with externals, url() preserved AS-IS)
                                       ▼
                                  preserves: url(/fonts/cinzel-*.woff2)
                                  DOES NOT copy fonts to public/css/
         │
         ▼
SERVE TIER (browser at runtime):
  <link rel="preload" href="/fonts/cinzel-*.woff2" crossorigin>  ──►  GET /fonts/cinzel-*.woff2  (cached)
  <style>@font-face { src: url(/fonts/cinzel-*.woff2); }</style>  ──►  preload cache HIT  (no second fetch)
```

Before the fix, the diagram looks like:

```
BUILD TIER (broken):
  [assets/css/main.css url('/fonts/cinzel-…')] ──► css.Build  ──► file loader resolves via assets/
                                                      │
                                                      ▼
                                             copies → public/css/cinzel-HASH.woff2
                                             rewrites url → url(./cinzel-HASH.woff2)

SERVE TIER (browser):
  preload href="/fonts/cinzel-*.woff2"         ──►  GET /fonts/cinzel-*.woff2   (miss cache → downloads)
  @font-face src="/css/cinzel-HASH.woff2"      ──►  GET /css/cinzel-HASH.woff2  (different URL → downloads again)
                                                    TOTAL: 2 fetches per font, 4 wasted requests
```

### Pattern 1: Hugo css.Build externals option

**What:** Tell esbuild to leave matching `url()` references in CSS unchanged — no resolution, no copying, no URL rewriting.

**When to use:** When font/image files are served from Hugo's static pipeline (not processed via asset pipeline), and CSS needs to reference their stable URLs.

**Critical finding (empirically validated 2026-04-17):** `externals` accepts exact path matches ONLY. Glob patterns do not work with esbuild's CSS url() resolver for this use case.

| Pattern tried | Result |
|---------------|--------|
| `"/fonts/*"` | FAIL — `url()` still rewritten to `./cinzel-HASH.woff2` |
| `"*.woff2"` | FAIL — `url()` still rewritten |
| `"/fonts/cinzel-latin-wght-normal.woff2"` (exact) | PASS — `url(/fonts/cinzel-latin-wght-normal.woff2)` preserved |
| `"/fonts/space-grotesk-latin-wght-normal.woff2"` (exact) | PASS — `url(/fonts/space-grotesk-latin-wght-normal.woff2)` preserved |

[VERIFIED: empirical test, live Hugo 0.160.1 build output]

**Example (the fix):**

```go-template
{{/* baseof.html — pass externals to css.Build */}}
{{ $cssOpts := dict "externals" (slice
  "/fonts/cinzel-latin-wght-normal.woff2"
  "/fonts/space-grotesk-latin-wght-normal.woff2"
) }}
{{ $css := resources.Get "css/main.css" | css.Build $cssOpts | minify | fingerprint }}
<link rel="stylesheet" href="{{ $css.RelPermalink }}">
```

[CITED: gohugo.io/functions/css/build/ — "externals: A slice of path patterns to exclude from bundling"]

### Pattern 2: HTML5 landmark wrapper pattern (removing the wrapper)

**What:** A `<footer>` landmark must appear exactly once in page HTML. When a partial's root element is `<footer>`, the caller must NOT wrap it in another `<footer>`.

**Two fix options considered:**

| Option | Change | Side effects |
|--------|--------|--------------|
| A — remove outer wrapper in index.html | `index.html`: change `<footer>{{ partial "sections/footer.html" . }}</footer>` to `{{ partial "sections/footer.html" . }}` | None — partial's own `<footer>` is the landmark. Existing CSS selectors (`.footer-section`, `.footer-content`, `.footer-closing`, etc.) unchanged. |
| B — change inner to `<div>` | `sections/footer.html`: change `<footer class="section section-void footer-section ...">` to `<div class="section section-void footer-section ...">` (and closing tag) | Partial becomes non-semantic at the root, but outer wrapper provides the landmark. Requires updating any CSS that targets `footer.footer-section` (grep says there is none — all selectors use class). |

**Recommendation: Option A** — remove the outer wrapper in `index.html`. Rationale:
- `footer.html` partial name implies its content IS the footer; keeping `<footer>` as its root is semantically honest
- Consistent with existing `<header>` and `<main>` wrappers in `index.html` — those wrap partials whose root elements are `<section>`, not `<header>`/`<main>`. The footer partial is the one exception.
- Option B would make the footer partial's root element inconsistent with Plan 03-01's intent (which explicitly introduced the partial with `<footer>` as its root)

**File paths:**
- `themes/arcaeon/layouts/index.html` — lines 10, 12 (`<footer>`/`</footer>` wrapper to remove)

[VERIFIED: read both files, confirmed the nesting in built HTML at `public/index.html` lines 255 + 257]

### Pattern 3: Bash regex for canonical URL (trailing slash tolerance)

**What:** The validation script must accept canonical URL with OR without trailing slash.

**Current broken line (scripts/validate-phase-03.sh:154, actual path `tests/validate-phase-03.sh:154`):**
```bash
check 'canonical points to falkensmage.com' "$(grep -c 'href="https://falkensmage.com"' "$INDEX")"
```

**Fixed line (use `grep -E` with alternation, or explicit `/?` trailing-slash optional group):**
```bash
check 'canonical points to falkensmage.com' "$(grep -cE 'href="https://falkensmage\.com/?"' "$INDEX")"
```

The `/?` makes the trailing slash optional. The `\.` escapes the literal dot (so `com` can't match `comX`). Use `-E` for extended regex. [VERIFIED: tested with grep -E locally against both `href="https://falkensmage.com"` and `href="https://falkensmage.com/"` — both match]

**File path:** `tests/validate-phase-03.sh` line 154

### Pattern 4: CI workflow minimal steps (remove dead code)

**What:** Delete the `npm ci` step since no build step consumes `node_modules/`.

**Current state (`.github/workflows/hugo.yml` lines 48–49):**
```yaml
      - name: Install Node.js dependencies
        run: "[[ -f package-lock.json || -f npm-shrinkwrap.json ]] && npm ci || true"
```

**Why it's dead:**
- `@fontsource-variable/cinzel` and `@fontsource-variable/space-grotesk` install to `node_modules/@fontsource-variable/*/files/*.woff2`
- No workflow step copies from `node_modules/` to `themes/arcaeon/assets/fonts/` or `themes/arcaeon/static/fonts/`
- Font WOFF2 files are already committed under `themes/arcaeon/static/fonts/` and `themes/arcaeon/assets/fonts/` (verified with `git ls-files`)
- `hugo` build operates exclusively on committed files
- Removing `npm ci` shaves seconds off every CI run and eliminates a silent install failure mode

**Fix:** Delete lines 48–49 (the step name line and the run line). Keep the `Setup Pages` step before and the `Build with Hugo` step after.

**Trade-offs considered (rejected):**
- Keep `npm ci` AND add a copy step → adds complexity; committed fonts are already the source of truth; duplication risk
- Remove committed fonts AND rely on `npm ci` + copy step → introduces a new CI dependency (npm registry availability) and breaks local development (devs must run `npm ci` before first `hugo server`)

**Recommendation: remove `npm ci` step entirely.** Audit-adjacent: consider whether to also delete `package.json` and `package-lock.json`. Research recommendation: leave them. They document the font versions (5.2.8, 5.2.10) as historical record, and removing them would be a separate tech-debt item outside this phase's scope. Audit success criterion 4 requires "one consistent choice" — keeping package.json as version documentation is consistent with removing the `npm ci` step.

**File path:** `.github/workflows/hugo.yml` lines 48–49

### Pattern 5: YAML frontmatter backfill

**What:** Copy requirement IDs from PLAN `requirements:` field to SUMMARY `requirements-completed:` field verbatim.

**Canonical key name:** `requirements-completed` (hyphen, not underscore). [VERIFIED: `/Users/falkensmage/.claude/get-shit-done/bin/lib/commands.cjs:463` — audit SDK reads `fm['requirements-completed']`]

**Canonical format:** inline YAML array (single line). Matches existing pattern in `01-01-SUMMARY.md`, `02-01-SUMMARY.md`, `02-02-SUMMARY.md`, `04-01-SUMMARY.md`, `04-02-SUMMARY.md`.

**Four files, eleven requirement IDs to backfill:**

| File | Add key | Value |
|------|---------|-------|
| `.planning/phases/01-theme-foundation/01-02-SUMMARY.md` | `requirements-completed` | `[THEME-02, THEME-03]` |
| `.planning/phases/01-theme-foundation/01-03-SUMMARY.md` | `requirements-completed` | `[THEME-04, THEME-05, THEME-06]` |
| `.planning/phases/03-dynamic-layer-quality/03-01-SUMMARY.md` | `requirements-completed` | `[CURR-01, CURR-02, CURR-03, PERF-03, A11Y-01, A11Y-04]` |
| `.planning/phases/03-dynamic-layer-quality/03-02-SUMMARY.md` | `requirements-completed` | `[SEO-01, SEO-02, SEO-03, PERF-01, PERF-02, PERF-04, A11Y-02, A11Y-03]` |

**Derivation:** Copied verbatim from each PLAN.md's `requirements:` field.

**Audit note:** Phase 1 Plan 03 requirements include THEME-04 — but THEME-04 is also listed in Plan 01-01's `requirements-completed`. This is intentional overlap (dark aesthetic was tokenized in Plan 01 and demonstrated/finalized in Plan 03). The audit considers THEME-04 satisfied by listing in either plan, so listing it in both is not a duplication bug.

[VERIFIED: read each PLAN.md frontmatter; confirmed requirement IDs]

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Prevent esbuild from rewriting font url() | Custom esbuild plugin or post-build sed script | `css.Build` `externals` option with exact paths | Hugo exposes the native esbuild knob; no plugin infrastructure needed |
| YAML frontmatter edits | Parsing with yq or python-yaml | Direct text edit | Single-line inline array, surgical edit, no ambiguity |
| Canonical URL regex | Complex URL parsing | `grep -cE` with `/?` optional group | One-line change, handles both trailing-slash forms |
| Removing nested footer | Restructure all partials | Remove one wrapper tag | Minimal blast radius; preserves existing CSS |

**Key insight:** Every fix here is a deletion or a surgical addition, not a redesign. The planner should resist the temptation to "improve" adjacent code — this is a gap-closure phase, not a refactor phase.

---

## Runtime State Inventory

This IS a refactor-adjacent phase (CI workflow change + font file consolidation), so the inventory applies:

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — static site, no databases | None |
| Live service config | GitHub Actions workflow config on github.com — but authoritative source IS `.github/workflows/hugo.yml` in git. No UI-only config. | None (repo change is sufficient) |
| OS-registered state | None — no Task Scheduler, pm2, launchd | None |
| Secrets/env vars | None — workflow uses `${{ runner.temp }}` and `${{ steps.pages.outputs.base_url }}`, both GitHub-managed, no custom secrets | None |
| Build artifacts / installed packages | `node_modules/@fontsource-variable/*` — installed locally by Matt, NOT committed (gitignored). After `npm ci` removal, CI will no longer install. Local dev still works (Hugo reads only from `assets/` and `static/`). If `package-lock.json` and `package.json` are kept for documentation, local `npm install` still works. | None required; `node_modules/` can optionally be removed locally, no functional impact. |
| Duplicate source files | `themes/arcaeon/assets/fonts/*.woff2` (2 files) AND `themes/arcaeon/static/fonts/*.woff2` (2 files) — same bytes at two paths; both tracked in git | **After externals fix: delete `themes/arcaeon/assets/fonts/` entirely.** (single source of truth: `static/fonts/`). Confirmed safe because no other asset or partial references `assets/fonts/`. |

**Grep audit for `assets/fonts/` references:**

```bash
grep -rE '\bassets/fonts|\.\./fonts' themes/ content/ layouts/ 2>/dev/null
# Expected output: empty after Plan 03-01 changed @font-face src from ../fonts/ to /fonts/
```

[VERIFIED: `@font-face src:` already uses `/fonts/...` (line 117, 125 of `main.css`); no other references to `assets/fonts/` or `../fonts/` in the theme]

---

## Common Pitfalls

### Pitfall 1: Glob patterns in `externals` don't work for CSS url()
**What goes wrong:** Using `"/fonts/*"` or `"*.woff2"` in `css.Build` externals. Build succeeds, but CSS url() still gets rewritten.
**Why it happens:** esbuild's external pattern matching for CSS url() resolution requires exact paths, not globs (empirically verified; documentation ambiguity confirmed). Glob support may exist for `@import` externals but not for url() references in the current Hugo/esbuild combination.
**How to avoid:** Use exact absolute paths only. Two files = two strings in the `externals` slice.
**Warning signs:** Built CSS (`public/css/main.min.*.css`) still contains `url(./cinzel-...HASH.woff2)` instead of `url(/fonts/cinzel-latin-wght-normal.woff2)` after applying the fix.

### Pitfall 2: Removing outer `<footer>` wrapper breaks sibling selectors
**What goes wrong:** Future CSS or JS that uses `index.html > footer` or `main + footer` selectors will still work — but if any code relies on the wrapper for spacing or positioning, removing it changes layout.
**Why it happens:** The outer `<footer>` had no classes or styles, only semantic role. But a pixel-perfect regression could appear if margin/padding collapsing differs between `<main><footer>` direct sibling and `<main><footer><footer class="...">` nested.
**How to avoid:** Verify visual render at 375px and 1024px after the change. Compare `public/index.html` HTML diff before/after to confirm ONLY the wrapper tags are removed (no CSS class changes).
**Warning signs:** Footer section padding or spacing looks visibly different in browser.

### Pitfall 3: `grep -E` syntax differences across bash versions
**What goes wrong:** `grep -cE 'href="https://falkensmage\.com/?"'` works in GNU grep (Linux CI) but has subtle behavior on macOS BSD grep. The `/?` is ERE-standard and works in both — but escape sequences like `\.` behave differently.
**Why it happens:** Bash scripts must run both locally (macOS, Matt's dev machine) and in CI (Ubuntu).
**How to avoid:** Use ERE features that are portable: `\.` (escaped dot), `/?` (zero-or-one). Avoid lookaheads/lookbehinds. Test locally with `bash tests/validate-phase-03.sh` before pushing.
**Warning signs:** Script passes locally but fails in CI, or vice versa.

### Pitfall 4: Deleting `assets/fonts/` before applying `externals` fix causes build failure
**What goes wrong:** If you delete `themes/arcaeon/assets/fonts/*.woff2` BEFORE adding the `externals` option to `css.Build`, Hugo errors out: `ERROR js.Build failed: ... Could not resolve "/fonts/cinzel-latin-wght-normal.woff2"`.
**Why it happens:** Without `externals`, `css.Build` resolves the `/fonts/...` URL via asset lookup. If fonts aren't in `assets/`, the resolver fails (static files are NOT in the asset resolution path).
**How to avoid:** ORDER MATTERS — add `externals` first, verify build succeeds and CSS has preserved URLs, THEN delete the duplicate `assets/fonts/` files. Verified empirically.
**Warning signs:** Hugo build error mentioning "Could not resolve /fonts/*.woff2".

### Pitfall 5: YAML inline array syntax vs block syntax mixing
**What goes wrong:** Copy-pasting a block-style requirements list into an inline array:
```yaml
requirements-completed: [
  THEME-02,
  THEME-03,
]
```
vs. the clean inline form:
```yaml
requirements-completed: [THEME-02, THEME-03]
```
The multi-line form with trailing comma works in modern YAML parsers but differs from the established convention in existing summaries.
**Why it happens:** Agents drafting the edit may reach for a more "readable" multi-line form.
**How to avoid:** Use inline array on a single line — matches existing pattern in `01-01-SUMMARY.md`, `02-01-SUMMARY.md`, `02-02-SUMMARY.md`, `04-01-SUMMARY.md`, `04-02-SUMMARY.md`. Consistency with prior art matters more than stylistic preference.
**Warning signs:** YAML frontmatter diff shows multiple lines added per summary instead of one.

### Pitfall 6: `hugo --baseURL` override vs `hugo.toml` baseURL — canonical URL varies
**What goes wrong:** Running `hugo` locally without `--baseURL` produces canonical `href="http://localhost:1313/"`. The SEO-03 regex check must match the PRODUCTION baseURL.
**Why it happens:** Hugo's dev server and local build use the configured baseURL (from `hugo.toml`) unless `--baseURL` overrides it. CI always passes `--baseURL "https://falkensmage.com/"`.
**How to avoid:** The validation script should run `hugo --baseURL "https://falkensmage.com/" --quiet` (NOT bare `hugo`) before grepping. Check current script — line 40 runs `hugo --quiet`, which means local runs match whatever is in `hugo.toml`. Since `hugo.toml` has `baseURL = "https://falkensmage.com/"`, this happens to work locally (canonical will have `https://falkensmage.com/`). But a dev who runs `hugo server` and then inspects `public/` would see `localhost` URLs.
**How to avoid (continued):** No change needed to the script — `hugo --quiet` reads `hugo.toml`'s baseURL. But the regex fix must still account for trailing slash, because `hugo.toml`'s baseURL already has it.
**Warning signs:** Script passes/fails inconsistently between environments.

### Pitfall 7: `grep -c '<footer>'` counts only the bare tag, not the attribute-bearing tag
**What goes wrong:** The existing validation script on line 108 uses `grep -c '</footer>'` for counting. That's correct (closing tag has no attrs). But if any new check uses `grep -c '<footer>'`, it will match only the naked wrapper, not the class-bearing inner footer. Easy to produce a false "count = 1" result that masks the nested bug.
**Why it happens:** `<footer>` (with nothing after) is a literal string; `<footer class="...">` is not matched by that pattern.
**How to avoid:** For counting opening footer tags, use `grep -cE '<footer[ >]'` — matches both `<footer>` and `<footer class="...">`. Or test that there's exactly one of each by grepping `</footer>` and asserting count == 1.
**Warning signs:** Validation passes but visual inspection still shows nested footers in source view.

---

## Code Examples

### Example 1: The PERF-03 fix (baseof.html edit)

**Before (lines 15 of current `themes/arcaeon/layouts/_default/baseof.html`):**
```go-template
  {{ $css := resources.Get "css/main.css" | css.Build | minify | fingerprint }}
```

**After:**
```go-template
  {{/* externals: exact font paths preserved as-is so preload href matches @font-face src (PERF-03) */}}
  {{ $cssOpts := dict "externals" (slice
    "/fonts/cinzel-latin-wght-normal.woff2"
    "/fonts/space-grotesk-latin-wght-normal.woff2"
  ) }}
  {{ $css := resources.Get "css/main.css" | css.Build $cssOpts | minify | fingerprint }}
```

[VERIFIED: empirically tested against Hugo 0.160.1 — built CSS output confirmed to contain `url(/fonts/cinzel-latin-wght-normal.woff2)` after this change]

### Example 2: The A11Y-01 fix (index.html edit)

**Before (current `themes/arcaeon/layouts/index.html`):**
```go-template
{{ define "main" }}
<header>
  {{ partial "sections/hero.html" . }}
</header>
<main>
  {{ partial "sections/currently.html" . }}
  {{ partial "sections/identity-cta.html" . }}
  {{ partial "sections/social.html" . }}
</main>
<footer>
  {{ partial "sections/footer.html" . }}
</footer>
{{ end }}
```

**After (remove `<footer>` / `</footer>` wrapper; the partial IS a `<footer>`):**
```go-template
{{ define "main" }}
<header>
  {{ partial "sections/hero.html" . }}
</header>
<main>
  {{ partial "sections/currently.html" . }}
  {{ partial "sections/identity-cta.html" . }}
  {{ partial "sections/social.html" . }}
</main>
{{ partial "sections/footer.html" . }}
{{ end }}
```

Result in built HTML: one `<footer class="section section-void footer-section sigil-arc-sm sigil-boundary-bl">` landmark, no nesting.

### Example 3: The SEO-03 regex fix (validate-phase-03.sh)

**Before (`tests/validate-phase-03.sh:154`):**
```bash
check 'canonical points to falkensmage.com' "$(grep -c 'href="https://falkensmage.com"' "$INDEX")"
```

**After:**
```bash
check 'canonical points to falkensmage.com' "$(grep -cE 'href="https://falkensmage\.com/?"' "$INDEX")"
```

### Example 4: CI workflow npm ci removal (.github/workflows/hugo.yml)

**Before (lines 48–49):**
```yaml
      - name: Install Node.js dependencies
        run: "[[ -f package-lock.json || -f npm-shrinkwrap.json ]] && npm ci || true"
```

**After:** Delete these two lines entirely. No replacement needed.

### Example 5: SUMMARY frontmatter backfill (01-02-SUMMARY.md)

**Before (YAML frontmatter block, no `requirements-completed` line):**
```yaml
tech_stack:
  added: []
  patterns:
    - "@font-face with font-display: swap for FOIT prevention"
    ...
metrics:
  duration: "82 seconds"
```

**After (add one line in the frontmatter, before `metrics:`):**
```yaml
tech_stack:
  added: []
  patterns:
    - "@font-face with font-display: swap for FOIT prevention"
    ...
requirements-completed: [THEME-02, THEME-03]
metrics:
  duration: "82 seconds"
```

Repeat the same pattern for `01-03-SUMMARY.md`, `03-01-SUMMARY.md`, `03-02-SUMMARY.md` with the requirement ID lists from the Pattern 5 table above.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `css.Build` without externals, duplicate fonts in `assets/fonts/` AND `static/fonts/` | `css.Build` with explicit `externals` slice, fonts only in `static/fonts/` | This phase | Single source of truth; no double-fetch; ~48 KB saved across both fonts in the CI cache |
| `validate-phase-03.sh` SEO-03 literal string match | `grep -E` with `/?` trailing slash tolerance | This phase | Script reports true 33/33; no false failures |
| CI workflow `npm ci` step | Direct use of committed WOFF2 files | This phase | Faster CI runs (~5–10s saved per deploy); removes silent install failure mode |

**Deprecated/outdated:**
- Font pipeline via `npm ci` + copy: audit success criterion 4 supersedes. Fonts are committed.
- SEO-03 regex match without trailing slash: superseded by `/?` optional pattern.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Removing the outer `<footer>` wrapper in `index.html` has no visual layout regression at 375px or 1024px | Pattern 2 / Pitfall 2 | LOW — the wrapper has no CSS; only semantic role. Visual checkpoint recommended post-fix. |
| A2 | `package.json` and `package-lock.json` should be kept (not deleted) as version documentation after `npm ci` is removed from CI | Pattern 4 | LOW — keeping them preserves the version record (5.2.8, 5.2.10); removing would require a separate tech-debt decision outside this phase's scope. If user prefers to delete them, that's a one-line task addition. |
| A3 | Audit "success criterion 4 demands one consistent choice" means removing `npm ci` is the preferred direction (as stated in the phase description), not adding a copy step | User Constraints | LOW — user's phase description explicitly states "Recommend the simpler (b) since fonts are already committed." |
| A4 | Hugo `css.Build` `externals` option does not rewrite URLs AND does not attempt to resolve the referenced file — validated empirically with live build, but not formally documented | Pattern 1 | LOW — empirical test passed with built CSS containing preserved URLs. If documented behavior changes in future Hugo versions, rebuild verification will catch it. |
| A5 | THEME-04 listing in BOTH 01-01-SUMMARY (already present) and 01-03-SUMMARY (to be added) is acceptable overlap, not a duplication bug | Pattern 5 | LOW — audit treats requirement satisfied if listed in ANY plan; cross-referencing is informative, not incorrect. |

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Hugo Extended | All fix verification | ✓ | 0.160.1 | — |
| bash | `validate-phase-03.sh` | ✓ | macOS 3.2, Ubuntu 5.x | — |
| grep | Regex check in script | ✓ | BSD (macOS) and GNU (Linux) both support `-cE` | — |
| git | Commit fixes | ✓ | 2.x | — |
| GitHub Actions runner | CI verification after workflow change | ✓ | ubuntu-latest | — |
| feralarchitecture.com/feed | RSS fetch at build time | ✓ | Unchanged from Phase 3; not part of this phase | — |

**No missing dependencies.** No new tools required.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Bash + `grep` (project-established pattern, matches Phase 3) |
| Config file | None — standalone shell scripts |
| Quick run command | `bash tests/validate-phase-03.sh` |
| Full suite command | `bash tests/validate-phase-03.sh && bash tests/validate-phase-02.sh && bash tests/validate-phase-01.sh` (regression) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| A11Y-01 | Exactly one `<footer>` landmark in built HTML | structural | `[ "$(grep -cE '<footer[ >]' public/index.html)" -eq 1 ]` | ✅ Will update `tests/validate-phase-03.sh` |
| A11Y-01 | Exactly one `</footer>` closing tag | structural | `[ "$(grep -c '</footer>' public/index.html)" -eq 1 ]` | ✅ Existing check at line 108 becomes accurate after fix |
| PERF-03 | Preload href exactly matches @font-face src — Cinzel | structural | `diff <(grep -oE 'preload[^>]*cinzel[^"]*' public/index.html \| grep -oE '/fonts/[^"]*') <(grep -oE 'url\([^)]*cinzel[^)]*\)' public/css/main.min.*.css \| grep -oE '/fonts/[^)]*')` returns empty | ✅ Will add to `tests/validate-phase-03.sh` |
| PERF-03 | Preload href exactly matches @font-face src — Space Grotesk | structural | Same diff pattern for `space-grotesk` | ✅ Will add |
| PERF-03 | Fonts present at `/fonts/` and NOT duplicated at `/css/` | structural | `[ ! -f public/css/cinzel*.woff2 ] && [ -f public/fonts/cinzel*.woff2 ]` | ✅ Will add |
| PERF-01 | No external CDN calls | smoke | Existing check line 68 in `validate-phase-03.sh` — passes already | ✅ Existing |
| PERF-01 | Preload href matches served font URL (derivative of PERF-03) | structural | Covered by PERF-03 checks | ✅ |
| SEO-03 | Canonical URL accepts trailing slash | smoke | `grep -cE 'href="https://falkensmage\.com/?"' public/index.html` > 0 | ✅ Will patch script line 154 |
| Tech debt | CI workflow has no `npm ci` step | structural | `! grep -q 'npm ci' .github/workflows/hugo.yml` | ✅ Will add to `tests/validate-phase-03.sh` or a new `tests/validate-phase-04.sh` (preferred: extend existing per-phase pattern, keep Phase 4 validation in a `validate-phase-04.sh`) |
| Tech debt | Frontmatter `requirements-completed` present in all Phase 1 + 3 summaries | structural | `grep -l 'requirements-completed' .planning/phases/01-theme-foundation/01-{02,03}-SUMMARY.md .planning/phases/03-dynamic-layer-quality/03-{01,02}-SUMMARY.md \| wc -l` equals 4 | ✅ Will add (new check, or manual verification) |

### Sampling Rate

- **Per task commit:** `hugo --quiet` (clean build confirms no breakage) + `bash tests/validate-phase-03.sh` (33/33 after fixes)
- **Per wave merge:** Above + `bash tests/validate-phase-02.sh` + `bash tests/validate-phase-01.sh` (full regression)
- **Phase gate:** All three validate-phase-*.sh scripts green before `/gsd-verify-work`. Plus: the new PERF-03 diff check returns empty for BOTH fonts.

### Wave 0 Gaps

- [ ] `tests/validate-phase-03.sh` — patch line 154 for SEO-03 regex fix
- [ ] `tests/validate-phase-03.sh` — add PERF-03 structural diff check (preload href === @font-face src) for both fonts
- [ ] `tests/validate-phase-03.sh` — add A11Y-01 nested-footer check (count of `<footer[ >]` opening tags equals 1)
- [ ] Optional: `tests/validate-phase-04.sh` — one check: `npm ci` absent from workflow YAML. Audit notes Phase 4 has no existing validation script. Research recommends deferring creation of the full Phase 4 validation script to a separate `/gsd-validate-phase 4` run (out of scope per user constraints) and adding only the single tech-debt check inline to `validate-phase-03.sh`.

---

## Security Domain

No authentication, no user input, no secrets, no session state. Fix-only phase — no new attack surface introduced.

**Applicable ASVS Categories:**

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | n/a |
| V3 Session Management | no | n/a |
| V4 Access Control | no | n/a |
| V5 Input Validation | no | No input in this phase — all changes are static content edits |
| V6 Cryptography | no | n/a |

**Known Threat Patterns for this stack:**

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Font subresource integrity (SRI) absent on preload | Tampering | accept — fonts self-hosted same-origin, no SRI required for static-domain preloads |
| npm supply chain (node_modules from fontsource) | Tampering | accept — but also mitigated by this phase's removal of `npm ci` from CI; committed WOFF2 files are the trust root going forward |

No new threats introduced.

---

## Wave Sequencing

**Wave 1 — structural fixes (parallel):**
1. A11Y-01 footer fix in `themes/arcaeon/layouts/index.html`
2. PERF-03 `externals` addition in `themes/arcaeon/layouts/_default/baseof.html`
3. (NEW) Deletion of `themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2` and `themes/arcaeon/assets/fonts/space-grotesk-latin-wght-normal.woff2`

Order within Wave 1: externals FIRST (step 2), then delete assets/fonts/ (step 3). If reversed, build will error (Pitfall 4). Footer fix (step 1) is fully parallel.

**Wave 2 — hygiene fixes + documentation (parallel):**
4. SEO-03 regex fix in `tests/validate-phase-03.sh`
5. `npm ci` removal in `.github/workflows/hugo.yml`
6. Frontmatter backfill — `01-02-SUMMARY.md`
7. Frontmatter backfill — `01-03-SUMMARY.md`
8. Frontmatter backfill — `03-01-SUMMARY.md`
9. Frontmatter backfill — `03-02-SUMMARY.md`

All six fully parallel — no shared files, no dependencies on each other.

**Wave 3 — verification + traceability update (serial):**
10. Run `bash tests/validate-phase-03.sh` → expect 33/33 (plus any new checks added to the script)
11. Rebuild with `hugo --baseURL "https://falkensmage.com/" --quiet` and run PERF-03 structural check (diff preload href === @font-face src for both fonts)
12. Rebuild and verify `public/css/` contains NO `.woff2` files
13. Update `.planning/REQUIREMENTS.md` traceability table — A11Y-01, PERF-01, PERF-03 Phase 5 → Complete; flip `- [ ]` to `- [x]` in section checklists

**Parallel potential:** Wave 1 + Wave 2 could technically run in parallel (no shared files between Wave 1's code fixes and Wave 2's script/workflow/docs fixes), but research recommends Wave 1 completes FIRST because Wave 3's PERF-03 structural diff check depends on Wave 1's externals fix being live. If Wave 1 and Wave 2 run fully parallel, a Wave 2 verification run of `validate-phase-03.sh` would see stale state.

---

## Landmines

Risks that could surprise an executor mid-phase:

1. **`hugo.toml` cache configuration.** There is a `[caches.getresource]` with `maxAge = "1h"` in `hugo.toml`. If an executor edits `baseof.html` and the cached CSS output doesn't invalidate, the test might see stale bundled CSS. Mitigation: `rm -rf public resources/_gen/` before verification runs (or `hugo --gc`).
2. **Multi-file main.min.HASH.css in public/css/.** After multiple builds, `public/css/` can accumulate 9+ fingerprinted CSS files (confirmed by `ls public/css/` showing 9 `main.min.*.css` files). This is normal — the current `RelPermalink` references the latest. BUT: if tests grep across all `main.min.*.css` files, they'll see mixed results from stale builds. Mitigation: `rm -rf public/` before each verification.
3. **`themes/arcaeon/assets/fonts/` git-tracked deletion.** Those two files ARE tracked in git (`git ls-files themes/arcaeon/assets/fonts/` confirms). A plain `rm` removes them from disk but not from git history until `git add -u && git commit`. Mitigation: use `git rm` for the deletion so git-tracking and filesystem stay in sync.
4. **`hugo.toml` baseURL affects everything.** The `baseURL = "https://falkensmage.com/"` setting is what makes canonical URL use production domain even in local builds. If an executor changes baseURL for testing, canonical regex check will fail. Mitigation: Do not modify `hugo.toml` during this phase.
5. **esbuild `externals` + absolute path precedence.** The empirical test used path exactly matching the CSS `url()` text (`/fonts/cinzel-latin-wght-normal.woff2`). If the CSS changes to a different format (e.g., `url(fonts/cinzel-...)` without leading slash), the externals entry would need to update. Current CSS uses `/fonts/...` absolute per Plan 03-01 — stable. Mitigation: do not modify `@font-face src:` paths as part of this phase.
6. **Hugo cache directory permissions.** `resources/_gen/` may be owned by user different from current invocation on some CI setups. Unlikely here (single-developer project), but noted. Mitigation: `hugo --gc` clears Hugo's cache atomically.
7. **Validation script exit-code trap with set -uo pipefail.** The current `validate-phase-03.sh` uses `set -uo pipefail` (line 7). An untrapped grep returning 0 hits exits 1 in pipefail mode. Any new check added must use `|| true` on grep invocations that legitimately can match zero items. (Reference: lines 68, 95, 277 of the current script already follow this pattern.)

---

## Open Questions

1. **Should `package.json` and `package-lock.json` be deleted alongside `npm ci` removal?**
   - What we know: No CI step consumes them after `npm ci` removal; committed WOFF2 files are the source of truth; files document font versions.
   - What's unclear: Whether user prefers strict minimalism (delete) or historical record (keep).
   - Recommendation: KEEP. Files document that Cinzel 5.2.8 and Space Grotesk 5.2.10 were the chosen versions. Removing them doesn't simplify anything (they're not in CI's critical path either way). If user later disagrees, it's a one-line PR to delete.

2. **Should `tests/validate-phase-04.sh` be created in this phase to cover the `npm ci` removal check?**
   - What we know: No Phase 4 validation script exists. Audit notes Phase 4 has `wave_0_complete: false` but defers full validation to `/gsd-validate-phase 4`.
   - What's unclear: Whether a thin Phase 4 validation script should be created now, or deferred.
   - Recommendation: DEFER. Create only the inline check in `validate-phase-03.sh` for `npm ci` absence. Full Phase 4 validation is explicitly out of scope per user constraints.

3. **Should the PERF-03 fix also remove the orphan `themes/arcaeon/assets/fonts/` directory (not just the two files)?**
   - What we know: The directory will be empty after deletion of both .woff2 files. Git does not track empty directories.
   - What's unclear: Whether to `rmdir themes/arcaeon/assets/fonts/` explicitly as part of the task.
   - Recommendation: YES, explicitly `rmdir` the directory after `git rm` of the two files. Leaves the filesystem clean. No CI or build impact either way — but tidier.

---

## Sources

### Primary (HIGH confidence)
- [VERIFIED: empirical test, Hugo 0.160.1 build output on 2026-04-17] — PERF-03 `externals` option fix empirically validated; exact path strings confirmed as the working form; glob patterns confirmed as the failing form
- [VERIFIED: `public/index.html` line 255 + 257] — nested `<footer>` confirmed in current built HTML
- [VERIFIED: `public/css/main.min.0ad2a692...`] — `url(./cinzel-HASH.woff2)` confirmed in built CSS before fix
- [VERIFIED: `git ls-files themes/arcaeon/static/fonts/ themes/arcaeon/assets/fonts/`] — both directories tracked in git, duplicate WOFF2 files confirmed
- [VERIFIED: `/Users/falkensmage/.claude/get-shit-done/bin/lib/commands.cjs:463`] — audit SDK uses `fm['requirements-completed']` (hyphenated) as canonical frontmatter key
- [CITED: https://gohugo.io/functions/css/build/] — `externals` option documented as "slice of path patterns to exclude from bundling"
- [CITED: https://esbuild.github.io/content-types/] — `.woff2` default loader is `file` (copies + rewrites URL)

### Secondary (MEDIUM confidence)
- [CITED: https://rednafi.com/misc/self-hosted-google-fonts-in-hugo/] — Hugo convention of `src: url('/fonts/...')` with fonts in `static/fonts/`
- [CITED: https://github.com/evanw/esbuild/issues/800] — esbuild's CSS url() externals behavior (context)
- [CITED: https://esbuild.github.io/api/#external] — esbuild externals API (general)

### Tertiary (LOW confidence / ASSUMED)
- See Assumptions Log — all assumptions rated LOW risk, verifiable via post-fix visual check or rebuild.

---

## Metadata

**Confidence breakdown:**
- PERF-03 fix: HIGH — empirically validated against live Hugo 0.160.1 build
- A11Y-01 fix: HIGH — nesting confirmed in live `public/index.html`; fix is removal of one wrapper
- SEO-03 regex: HIGH — tested against both trailing-slash and no-trailing-slash forms
- `npm ci` removal: HIGH — no workflow step depends on it; committed WOFF2 files are git-tracked
- Frontmatter backfill: HIGH — canonical key name verified against audit SDK source
- Wave sequencing: HIGH — fix ordering dependency (externals before file deletion) empirically required
- PERF-01 verification: MEDIUM — structural check is sufficient per audit evidence, but actual Lighthouse 3G timing not measured in this research

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (Hugo 0.160.1 stable; audit findings locked; no external dependencies changing)

## RESEARCH COMPLETE
