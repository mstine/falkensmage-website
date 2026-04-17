# Phase 4: Production Deploy - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

falkensmage.com is live, HTTPS, deploying automatically from `main`, with the custom domain persisting across every deploy. This phase creates the GitHub repo, GitHub Actions workflow, CNAME configuration, and lemniscate favicon. No content or styling changes — pure infrastructure to ship what already exists.

</domain>

<decisions>
## Implementation Decisions

### Favicon
- **D-01:** Style — ARCAEON glow mark. Electric Violet (#7a2cff) lemniscate stroke on transparent background with subtle Neon Magenta (#ff3cac) outer glow. Clean geometric curves, readable at 16x16 and 32x32.
- **D-02:** Source — Hugo-generated SVG at build time via a template partial. Favicon inherits palette token values from hugo.toml, stays in sync automatically if colors ever shift.
- **D-03:** Formats — `.svg` for modern browsers + `.ico` generated from the SVG for legacy. Both linked in `<head>`.

### GitHub Actions Workflow
- **D-04:** Trigger — push to `main` only. No PR builds, no manual dispatch. Solo project, simplest path.
- **D-05:** Build steps — Hugo Extended 0.160.1 pinned (not `latest`), `npm ci` for font packages, `hugo --minify --environment production`, deploy to GitHub Pages via `actions/deploy-pages@v4`.
- **D-06:** Workflow pattern — follow official Hugo starter workflow structure: `actions/configure-pages@v4`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`. Direct Hugo binary install, no third-party Hugo action.

### Repository + Domain
- **D-07:** Repo creation — use `gh repo create` to create public repo under personal GitHub account. Add remote, push existing `main` branch.
- **D-08:** CNAME — `static/CNAME` file containing `falkensmage.com`. Persists custom domain across deploys because Hugo copies `static/` to build output root.
- **D-09:** DNS — phase plan includes a step-by-step DNS checklist for pointing falkensmage.com to GitHub Pages (A records for apex + CNAME for www). Manual steps for Matt to follow.
- **D-10:** HTTPS — automatic via GitHub Pages once DNS propagates. No manual cert configuration needed.

### Claude's Discretion
- SVG lemniscate curve geometry and glow filter parameters (D-01, D-02) — as long as it reads clearly at favicon sizes
- Exact workflow YAML structure within the pattern constraints (D-06)
- `.ico` generation approach — build-time script or committed artifact from SVG source
- DNS checklist formatting and level of detail

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### GitHub Actions + Pages
- `CLAUDE.md` §GitHub Actions Workflow Pattern — official workflow structure with `actions/configure-pages@v4`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`
- `CLAUDE.md` §Technology Stack — Hugo Extended 0.160.1, `npm ci` font dependency, `hugo --minify`

### Hugo Configuration
- `hugo.toml` — `baseURL = "https://falkensmage.com/"`, ARCAEON palette values under `[params.colors]`, cache settings for RSS
- `package.json` — `@fontsource-variable/cinzel` and `@fontsource-variable/space-grotesk` dependencies required in CI

### ARCAEON Palette (for favicon)
- `hugo.toml` §[params.colors] — Electric Violet, Neon Magenta token values the favicon SVG template will reference
- `~/.psyche/swipe-files/podcasting-creative/2026-04-16-12-33-18-arc-on-color-palette-full.md` — Full ARCAEON palette system

### Prior Phase Decisions
- `.planning/phases/01-theme-foundation/01-CONTEXT.md` — Hugo project setup, css.Build pipeline, theme architecture
- `.planning/phases/03-dynamic-layer-quality/03-CONTEXT.md` — Font preload pattern in `<head>`, OG meta tags already in baseof.html

### Project Requirements
- `.planning/REQUIREMENTS.md` §Infrastructure — INFRA-03 (Actions workflow), INFRA-04 (CNAME), INFRA-05 (favicon)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `hugo.toml` `[params.colors]` — palette token values accessible in Hugo templates via `.Site.Params.colors.electricViolet` etc. Favicon SVG template can reference these directly.
- `themes/arcaeon/layouts/_default/baseof.html` — existing `<head>` section where favicon `<link>` tags will be added (alongside existing font preloads and OG meta)
- Hugo `css.Build` pipeline pattern — already established for CSS, same asset pipeline approach can inform favicon generation

### Established Patterns
- Two-tier token naming: palette truth (`--arcaeon-*`) + semantic aliases (`--color-*`) — favicon should use palette truth values directly since it's a brand mark
- Content from hugo.toml params — established pattern of centralizing config values, favicon colors follow this
- `static/` directory for files that copy to build root — CNAME goes here

### Integration Points
- `themes/arcaeon/layouts/_default/baseof.html` `<head>` — needs favicon `<link>` tags (SVG + ICO)
- `themes/arcaeon/layouts/partials/` — needs a favicon SVG generation partial (or `static/` output)
- `.github/workflows/` — new directory, new `hugo.yml` workflow file
- `static/CNAME` — new file, build root output
- Git remote — currently no remote configured, needs `origin` added

</code_context>

<specifics>
## Specific Ideas

- Favicon lemniscate uses the same infinity symbol (∞) visual as the footer decorative mark, but rendered as a proper SVG with ARCAEON palette glow treatment
- Hugo template generates the SVG so palette changes in hugo.toml automatically propagate to favicon — no manual re-export needed
- Workflow follows the official Hugo starter workflow exactly, with Hugo version pinned (not floating)
- `gh repo create` handles repo creation + remote setup in one command

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 04-production-deploy*
*Context gathered: 2026-04-17*
