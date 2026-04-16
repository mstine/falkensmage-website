# Stack Research

**Domain:** Hugo personal brand site — single-page, dark aesthetic, GitHub Pages
**Researched:** 2026-04-16
**Confidence:** HIGH (Hugo core + deployment); MEDIUM (font pairing recommendation)

---

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

**Font delivery:** Install via npm, copy WOFF2 files to `static/fonts/` at build time, reference via `@font-face` in the theme CSS. No CDN dependency, no external calls, performance constraint satisfied.

**Why not system stack:** The ARCÆON dark graphic novel aesthetic requires Cinzel's inscriptional authority in the display position. System fonts (SF Pro, Segoe UI) read as OS chrome, not identity. The self-hosting constraint is already set — so the only question is which OFL fonts to use.

**Why not Bebas Neue for display:** Bebas is all-caps condensed — strong for titles, weak for mixed-case logotype treatment. Cinzel carries weight across both ALL CAPS hero treatment and title-case headings. More versatile for a single-page layout with multiple hierarchy levels.

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

---

## Installation

```bash
# In project root — fonts only, not a Node project
npm init -y
npm install @fontsource-variable/cinzel @fontsource-variable/space-grotesk

# Copy WOFF2 files to static assets (run once during theme setup)
cp node_modules/@fontsource-variable/cinzel/files/cinzel-latin-*.woff2 themes/arcaeon/static/fonts/
cp node_modules/@fontsource-variable/space-grotesk/files/space-grotesk-latin-*.woff2 themes/arcaeon/static/fonts/

# Hugo itself — install via Homebrew (dev) or use prebuilt binary in CI
brew install hugo
# Verify extended edition
hugo version  # must show "extended"
```

---

## GitHub Actions Workflow Pattern

```yaml
# .github/workflows/hugo.yml
env:
  HUGO_VERSION: 0.160.1  # pin to current, update intentionally

steps:
  - name: Install Hugo CLI
    run: |
      wget -O ${{ runner.temp }}/hugo.deb \
        https://github.com/gohugoio/hugo/releases/download/v${{ env.HUGO_VERSION }}/hugo_extended_${{ env.HUGO_VERSION }}_linux-amd64.deb
      sudo dpkg -i ${{ runner.temp }}/hugo.deb

  - name: Install Node.js dependencies
    run: "[[ -f package-lock.json ]] && npm ci || true"

  - name: Build with Hugo
    run: hugo --minify
    env:
      HUGO_ENVIRONMENT: production
```

---

## RSS Fetch Pattern (Build-Time)

```go-html-template
{{/* In layouts/partials/currently.html */}}
{{ $rss := "https://feralarchitecture.substack.com/feed" }}
{{ with resources.GetRemote $rss | transform.Unmarshal }}
  {{ with (index .channel.item 0) }}
    <a href="{{ .link }}">{{ .title }}</a>
    <time>{{ .pubDate }}</time>
  {{ end }}
{{ end }}
```

Hugo caches remote resources during build. The "Currently" section shows the latest post as of last deploy — no JavaScript, no CORS, no API key.

---

## CSS Architecture Pattern

Hugo 0.160's `css.Build` with `@import "hugo:vars"` means the ARCÆON palette lives in `hugo.toml` as params and gets injected as CSS custom properties at build time:

```toml
# hugo.toml
[params.colors]
  electricViolet = "#7a2cff"
  neonMagenta = "#ff3cac"
  electricBlue = "#2fd3ff"
  voidPurple = "#1a0f2e"
```

```css
/* themes/arcaeon/assets/css/main.css */
@import "hugo:vars";

:root {
  --color-primary: v-electricViolet;
  --color-accent: v-neonMagenta;
  --color-void: v-voidPurple;
}
```

This is the authoritative pattern for the ARCÆON color system — single source of truth in config, no duplication in CSS.

---

## Ambient Animation Pattern

Pure CSS `@keyframes` — no JavaScript animation library. The dark aesthetic needs subtle: glow pulse on the hero image, slow color-shift on social link hovers, floating particle effect (optional, CSS only).

```css
@keyframes glow-pulse {
  0%, 100% { box-shadow: 0 0 20px rgba(122, 44, 255, 0.4); }
  50%       { box-shadow: 0 0 40px rgba(255, 60, 172, 0.6); }
}

/* Accessibility — kill all motion for users who ask */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

No GSAP, no Framer Motion, no JS animation library. CSS `transform` and `opacity` are GPU-composited — performance is non-negotiable on the sub-1s 3G constraint.

---

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

---

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

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Hugo Extended 0.160.1 | `actions/deploy-pages@v4`, Ubuntu 22.04+ | Official Actions workflow tested on `ubuntu-latest`. Pin Hugo version — don't use `latest` in CI |
| `@fontsource-variable/cinzel` 5.2.8 | Any modern browser | WOFF2 supported in all browsers that matter. Include `font-display: swap` to prevent FOIT |
| `@fontsource-variable/space-grotesk` 5.2.10 | Any modern browser | Same as above |
| Hugo `resources.GetRemote` | Hugo 0.92+ | Available since 0.92. 0.160 adds caching improvements. Substack RSS is `application/xml` — Hugo handles content-type negotiation automatically |
| CSS `@keyframes` + `prefers-reduced-motion` | All modern browsers | 97%+ global support per MDN. No polyfill needed |

---

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

---

*Stack research for: Hugo personal brand site — falkensmage.com*
*Researched: 2026-04-16*
