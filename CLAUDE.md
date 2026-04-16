<!-- GSD:project-start source:PROJECT.md -->
## Project

**falkensmage.com**

Single-page, mobile-first personal site for Matt Stine's public identity: **Falken's Mage**. The front door. Social discovery lands here — makes the person legible in ten seconds on a phone screen. Everything else orbits it: Feral Architecture (Substack), Digital Intuition (LLC), Falken's Labyrinth (book), RitualSync (software company).

**Core Value:** A stranger landing from social media instantly understands who this person is and can reach everything that matters — in under ten seconds, on a phone.

### Constraints

- **Stack**: Hugo static site generator with custom `arcaeon` theme — Matt has prior Hugo experience, no ramp-up cost
- **Hosting**: GitHub Pages via GitHub Actions build/deploy pipeline
- **Domain**: falkensmage.com — owned, needs DNS pointed to GitHub Pages, HTTPS automatic
- **Performance**: Sub-1s page load on 3G — no external fonts unless self-hosted, no analytics, no external dependencies
- **Mobile-first**: 375px viewport designed first, scales up
- **Accessibility**: WCAG AA minimum
- **No external font CDNs**: Self-host or system stack only
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Hugo Extended | 0.160.1 | Static site generator | Prior experience, no ramp-up. Extended edition required for `css.Build` and Dart Sass support. 0.160.x adds `@import "hugo:vars"` — CSS custom properties injected directly from Hugo config, perfect for the ARCÆON palette system |
| Hugo `css.Build` | (built-in 0.160+) | CSS processing | Replaces PostCSS for bundling/minification without the Node dependency overhead. 0.160 specifically adds the ability to inject Hugo config vars as CSS custom properties — eliminates a separate build step for the color system |
| GitHub Actions | `ubuntu-latest` | Build + deploy pipeline | Official Hugo starter workflow at `actions/starter-workflows` uses `actions/configure-pages@v4`, `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4`. No third-party action needed |
| GitHub Pages | — | Hosting | Zero-cost, HTTPS automatic, custom domain DNS via CNAME record. Constraint is already set — no decision needed |
### Typography
| Package | Version | Purpose | Why |
|---------|---------|---------|-----|
| `@fontsource-variable/cinzel` | 5.2.8 | Display / headings — Falken's Mage logotype treatment, section headers | Variable weight 400–900. Cinzel reads as Roman inscription meets dark fantasy — classical authority without Gothic cliché. Pairs perfectly with the Electric Violet / Neon Magenta palette. Self-hosted via npm, no Google CDN call |
| `@fontsource-variable/space-grotesk` | 5.2.10 | Body / UI text — identity statement, social labels, CTAs | Variable weight 300–700. Geometric grotesque with technical edge — not clinical like Inter, not cold like Helvetica. The "technomagickal" voice needs a body face with personality. Pairs with Cinzel without competing |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `node` + `npm` | LTS (22.x) | Font file management only | Required to install and copy Fontsource WOFF2 files during initial setup. Not a runtime dependency. GitHub Actions workflow runs `npm ci` if `package-lock.json` is present |
| Hugo `resources.GetRemote` | built-in | Build-time Substack RSS fetch | Fetches latest Feral Architecture post at `hugo build` time via `{{ with resources.GetRemote $url \| transform.Unmarshal }}`. No JavaScript, no external API call at runtime. Updates on each deploy |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| `hugo server --buildDrafts` | Local dev with live reload | Hugo's built-in dev server. No extra tooling needed — instant rebuild on CSS/template changes |
| `hugo --minify --environment production` | Production build | Minifies HTML/CSS/JS output. Set `HUGO_ENVIRONMENT=production` in Actions workflow to enable |
| Dart Sass (via snap in CI) | Sass compilation | Only needed if you adopt `.scss` files in the theme. With `css.Build` native CSS, Dart Sass may be skippable — but the official Actions workflow installs it, so leave it |
| `imageoptim` / Hugo image processing | WebP conversion + responsive `<picture>` | Hugo's built-in `resources.Get` + `.Resize` + `.Format "webp"` handles the Magus hero image. Use `<picture>` with WebP source + JPEG fallback for browser compatibility |
## Installation
# In project root — fonts only, not a Node project
# Copy WOFF2 files to static assets (run once during theme setup)
# Hugo itself — install via Homebrew (dev) or use prebuilt binary in CI
# Verify extended edition
## GitHub Actions Workflow Pattern
# .github/workflows/hugo.yml
## RSS Fetch Pattern (Build-Time)
## CSS Architecture Pattern
# hugo.toml
## Ambient Animation Pattern
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Hugo Extended | Eleventy, Astro | Astro if the site grows to multi-page with component-heavy UI. Hugo wins here on prior experience, build speed, and the `resources.GetRemote` RSS pattern being native |
| Hugo Extended | Hugo Standard edition | Never for this project — `css.Build` requires Extended |
| `css.Build` native CSS | PostCSS pipeline | Only if you need PostCSS-specific plugins (autoprefixer, etc.). PostCSS is Node-dependent and significantly slower. Hugo 0.160's native CSS handles everything needed here |
| `@fontsource-variable` | Download + manual WOFF2 | Fontsource packages are the same files, better organized, versioned via npm. Manual download is fine for one-time setup but fontsource is cleaner for tracking |
| `resources.GetRemote` (build-time) | Client-side JS RSS fetch | Client-side fetch requires CORS proxy, adds JS payload, fails gracefully but adds complexity. Build-time is zero JS, zero runtime dependency, perfect for a static site |
| GitHub Actions + Pages | Netlify, Vercel | Netlify/Vercel would simplify deployment but add vendor dependency. GitHub Pages is free, already integrated with the repo, and fits the static-site constraint. No reason to add a platform |
| Cinzel + Space Grotesk | System font stack | System stack kills the ARCÆON aesthetic. Self-hosting constraint is already set — use it |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Tailwind CSS | Adds a build pipeline dependency for a single-page site that doesn't need utility classes at scale. The ARCÆON palette is a custom system — utility classes fight it, not help it | Native CSS custom properties + `css.Build` |
| Google Fonts CDN | Violates the no-external-CDN constraint, sends user data to Google, adds DNS lookup latency | `@fontsource-variable` self-hosted WOFF2 |
| GSAP / anime.js | Runtime JS dependency for animations that CSS handles natively. Every KB on a sub-1s 3G budget is a decision | Pure CSS `@keyframes` + `transform` + `opacity` |
| PostCSS | Node dependency in CI, slower builds, not needed — Hugo 0.160 `css.Build` covers everything required | Hugo `css.Build` native |
| Hugo standard (non-extended) edition | `css.Build` and Dart Sass processing require Extended. Building with standard fails silently or errors on CSS imports | Hugo Extended 0.160.1 |
| `peaceiris/actions-hugo` | Third-party action adds an unnecessary dependency. Official Hugo workflow pattern using direct binary download is simpler and controlled | Direct binary install in workflow (see above) |
| Analytics (Plausible, GA, Fathom) | Explicitly out of scope per PROJECT.md. Every external script is a performance hit and a privacy signal | Nothing — omit entirely |
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Hugo Extended 0.160.1 | `actions/deploy-pages@v4`, Ubuntu 22.04+ | Official Actions workflow tested on `ubuntu-latest`. Pin Hugo version — don't use `latest` in CI |
| `@fontsource-variable/cinzel` 5.2.8 | Any modern browser | WOFF2 supported in all browsers that matter. Include `font-display: swap` to prevent FOIT |
| `@fontsource-variable/space-grotesk` 5.2.10 | Any modern browser | Same as above |
| Hugo `resources.GetRemote` | Hugo 0.92+ | Available since 0.92. 0.160 adds caching improvements. Substack RSS is `application/xml` — Hugo handles content-type negotiation automatically |
| CSS `@keyframes` + `prefers-reduced-motion` | All modern browsers | 97%+ global support per MDN. No polyfill needed |
## Sources
- [Hugo gohugoio/hugo GitHub releases](https://github.com/gohugoio/hugo/releases) — v0.160.1 confirmed latest, April 8 2026 (HIGH confidence)
- [Hugo: Host on GitHub Pages](https://gohugo.io/host-and-deploy/host-on-github-pages/) — Workflow pattern, HUGO_VERSION: 0.160.0 in official docs (HIGH confidence)
- [GitHub actions/starter-workflows hugo.yml](https://github.com/actions/starter-workflows/blob/main/pages/hugo.yml) — Official workflow structure verified (HIGH confidence)
- [Hugo discourse: Substack RSS via resources.GetRemote](https://discourse.gohugo.io/t/custom-shortcode-to-display-the-date-when-a-remote-rss-feed-was-last-updated-e-g-substack-mastodon/52028) — Build-time RSS pattern confirmed (HIGH confidence)
- [How to Embed RSS Substack Feed into Hugo](https://www.ibrahimsowunmi.com/posts/2023/12/how-to-embed-a-rss-substack-feed-into-your-hugo-static-site/) — template syntax verified (MEDIUM confidence — 2023 post, but `resources.GetRemote` API is stable)
- [@fontsource-variable/cinzel npm](https://www.npmjs.com/package/@fontsource-variable/cinzel) — v5.2.8, weights 400–900 (HIGH confidence)
- [@fontsource-variable/space-grotesk npm](https://www.npmjs.com/package/@fontsource-variable/space-grotesk) — v5.2.10 (HIGH confidence)
- [Smashing Magazine: Ambient Animations in Web Design Part 2](https://www.smashingmagazine.com/2025/10/ambient-animations-web-design-practical-applications-part2/) — Performance patterns, prefers-reduced-motion (HIGH confidence)
- [MDN: prefers-reduced-motion](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion) — Accessibility implementation (HIGH confidence)
- [Hugo discourse 0.160.0 release announcement](https://discourse.gohugo.io/t/hugo-0-160-0-released/56961) — `css.Build` + `@import "hugo:vars"` CSS vars injection (HIGH confidence)
- Font pairing recommendation (Cinzel + Space Grotesk) — MEDIUM confidence. Evidence: Cinzel is the standard dark/fantasy serif on Fontsource and Typewolf; Space Grotesk is a confirmed tech-adjacent grotesque. Aesthetic judgment not empirically verifiable — validate in Phase 1 with real comps
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->
## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, or `.github/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
