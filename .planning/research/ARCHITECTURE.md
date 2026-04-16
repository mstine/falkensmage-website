# Architecture Research

**Domain:** Hugo custom theme — single-page personal brand site
**Researched:** 2026-04-16
**Confidence:** HIGH (Hugo official docs + official GitHub Actions workflow + verified community patterns)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CI/CD Layer                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  GitHub Actions (.github/workflows/hugo.yaml)           │   │
│  │  trigger: push to main → build → deploy to Pages        │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │ hugo build
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                        Hugo Build Layer                         │
├──────────────┬──────────────┬───────────────┬───────────────────┤
│  Content     │  Data        │  Assets       │  Layouts          │
│  _index.md   │  (none yet)  │  CSS + fonts  │  themes/arcaeon/  │
│  (front mat- │              │  Hero image   │  layouts/         │
│   ter only)  │              │  Favicon SVG  │  partials/        │
└──────┬───────┴──────┬───────┴───────┬───────┴───────┬───────────┘
       │              │               │               │
       ↓ resources.GetRemote at build │               │
┌─────────────┐       │               │               │
│ External    │       │               │               │
│ RSS: Feral  │       │               │               │
│ Architecture│       │               │               │
│ Substack    │       │               │               │
└─────────────┘       │               │               │
                      ↓               ↓               ↓
┌─────────────────────────────────────────────────────────────────┐
│                     public/ (compiled output)                   │
│  index.html  │  assets/  │  fonts/  │  favicon.ico              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ↓
              GitHub Pages → falkensmage.com
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| `themes/arcaeon/` | Brand theme — owns ALL visual identity | Hugo theme directory |
| `themes/arcaeon/assets/css/` | ARCÆON color system, typography, animations | CSS with custom properties |
| `themes/arcaeon/assets/fonts/` | Self-hosted typeface files | `.woff2` + `.woff` |
| `themes/arcaeon/layouts/_default/baseof.html` | Root HTML shell — `<head>`, open graph, preload hints | Hugo base template |
| `themes/arcaeon/layouts/index.html` | Homepage entrypoint — invokes section partials in order | Hugo home template |
| `themes/arcaeon/layouts/partials/` | Individual page sections — each partial = one section | Hugo partials |
| `themes/arcaeon/static/` | Favicon, `robots.txt` — direct-copy, no processing | Static assets |
| `content/_index.md` | Front matter only — title, description, tagline slot, current-focus blurb | Hugo content |
| `.github/workflows/hugo.yaml` | Build + deploy pipeline | GitHub Actions |

## Recommended Project Structure

```
falkensmage-website/
├── .github/
│   └── workflows/
│       └── hugo.yaml               # Build + GitHub Pages deploy
├── content/
│   └── _index.md                   # Front matter: title, description, current-focus
├── hugo.toml                        # Site config: baseURL, theme: arcaeon, cache config
└── themes/
    └── arcaeon/
        ├── assets/
        │   ├── css/
        │   │   ├── main.css         # @import order: tokens → base → sections → utilities
        │   │   ├── _tokens.css      # CSS custom properties (ARCÆON palette + type scale)
        │   │   ├── _base.css        # Reset, body, selection, scrollbar
        │   │   ├── _typography.css  # Font face declarations, heading/body styles
        │   │   ├── _hero.css        # Hero section styles
        │   │   ├── _identity.css    # Identity statement section
        │   │   ├── _social.css      # Social links grid
        │   │   ├── _work.css        # Work With Me CTA section
        │   │   ├── _currently.css   # Currently section (RSS + focus blurb)
        │   │   ├── _footer.css      # Footer styles
        │   │   └── _animations.css  # Ambient glow, hover, prefers-reduced-motion
        │   └── fonts/
        │       ├── [face]-regular.woff2
        │       └── [face]-bold.woff2
        ├── layouts/
        │   ├── _default/
        │   │   └── baseof.html      # HTML shell: <head>, OG meta, font preload, body wrapper
        │   ├── index.html           # Homepage: extends baseof, calls section partials
        │   └── partials/
        │       ├── head/
        │       │   ├── meta.html    # Open Graph, Twitter card, canonical
        │       │   └── preload.html # Font preload links, critical CSS hints
        │       ├── sections/
        │       │   ├── hero.html        # Magus image, display treatment, tagline slot
        │       │   ├── identity.html    # 2-3 sentence identity statement
        │       │   ├── social.html      # Social links grid with icons
        │       │   ├── work.html        # Work With Me CTA + mailto button
        │       │   ├── currently.html   # RSS fetch + current-focus blurb
        │       │   └── footer.html      # Closing line, copyright, sigil mark
        │       └── components/
        │           ├── icon.html        # SVG icon renderer (accepts name param)
        │           └── glow-button.html # Radiant Core button component
        └── static/
            ├── favicon.svg          # Lemniscate sigil
            └── robots.txt
```

### Structure Rationale

- **`themes/arcaeon/`**: Theme IS the brand. Keeping it as a proper Hugo theme (rather than root-level layouts) means it can be reused across future Digital Intuition properties without modification.
- **`assets/css/` with partials via `@import`**: Each CSS file maps to one section partial. When you open `hero.html` and need to adjust styles, `_hero.css` is the obvious destination — no search required.
- **`assets/fonts/`** inside assets (not static): Allows Hugo Pipes to fingerprint font filenames for cache-busting. Fonts served from `static/` get no cache-busting.
- **`partials/head/`**: Head concerns separated from body concerns. `meta.html` owns social sharing; `preload.html` owns performance hints. Both invoked by `baseof.html`.
- **`partials/sections/`**: One file per section. `index.html` just invokes them in order — the page structure is readable in ~10 lines.
- **`partials/components/`**: Reusable primitives (icon renderer, glow button) that sections can call. Prevents inline SVG duplication across multiple sections.
- **`content/_index.md`**: Holds the text content Matt will actually edit — identity statement, tagline, current-focus blurb. Keeps editorial content out of templates.

## Architectural Patterns

### Pattern 1: Section-Per-Partial

**What:** Each visible page section (hero, identity, social links, etc.) is its own partial in `partials/sections/`. The homepage template (`index.html`) is just an ordered list of `{{ partial "sections/hero.html" . }}` calls.

**When to use:** Always, for any page with multiple named sections. The single-page architecture benefits most from this pattern.

**Trade-offs:** Adds one file per section. Worth it — each section can be moved, hidden, or swapped without touching any other section. The alternative (monolithic `index.html`) becomes unnavigable past 200 lines.

**Example:**
```html
{{ define "main" }}
  {{ partial "sections/hero.html" . }}
  {{ partial "sections/identity.html" . }}
  {{ partial "sections/social.html" . }}
  {{ partial "sections/work.html" . }}
  {{ partial "sections/currently.html" . }}
  {{ partial "sections/footer.html" . }}
{{ end }}
```

### Pattern 2: CSS Custom Properties as Design Token System

**What:** All ARCÆON palette values and type scale defined as CSS custom properties on `:root` in `_tokens.css`. No hard-coded hex values anywhere else — every color reference uses a token.

**When to use:** Always for a branded theme. Particularly important here because the ARCÆON palette has a strict triad rule (every section needs one purple + one blue + one warm core) that is easier to enforce when colors are named semantically.

**Trade-offs:** One extra file. Pays back immediately when Matt wants to adjust a shade — one change in `_tokens.css`, propagates everywhere.

**Example:**
```css
/* _tokens.css */
:root {
  /* Cosmic Depth */
  --color-void-purple: #1a0f2e;
  --color-deep-indigo: #0a0f3c;
  --color-midnight-blue: #111a6b;

  /* Primary Identity */
  --color-electric-violet: #7a2cff;
  --color-neon-magenta: #ff3cac;
  --color-electric-blue: #2fd3ff;

  /* Focal Energy */
  --color-solar-white: #fff4e6;
  --color-fusion-gold: #ffb347;
  --color-ignition-orange: #ff7a18;

  /* Energy Accents */
  --color-ion-glow: #5be7ff;
  --color-plasma-pink: #ff5fd2;

  /* Semantic aliases */
  --bg-primary: var(--color-void-purple);
  --text-primary: var(--color-solar-white);
  --accent-primary: var(--color-electric-violet);

  /* Type scale */
  --font-display: 'TypefaceName', system-ui, sans-serif;
  --font-body: 'TypefaceName', Georgia, serif;
  --text-hero: clamp(2.5rem, 8vw, 5rem);
  --text-xl: clamp(1.5rem, 4vw, 2.5rem);
  --text-base: 1.125rem;
}
```

### Pattern 3: Build-Time RSS Fetch via resources.GetRemote

**What:** The "Currently" section fetches the Feral Architecture Substack RSS feed at Hugo build time using `resources.GetRemote` + `transform.Unmarshal`. No JavaScript, no client-side fetch, no external dependency at runtime.

**When to use:** Any "latest post" feature on a static site. Requires a rebuild to update content — acceptable for a personal site deploying on push to main.

**Trade-offs:** Content freshness tied to build frequency. A GitHub Actions schedule trigger (cron) can force daily rebuilds to keep it current. The RSS fetch is cached between builds for performance.

**Example:**
```html
<!-- partials/sections/currently.html -->
{{ $rssURL := "https://feralarchitecture.substack.com/feed" }}
{{ with resources.GetRemote $rssURL | transform.Unmarshal }}
  {{ with (index .channel.item 0) }}
    <a href="{{ .link }}" class="currently__post-link">
      {{ .title }}
    </a>
    <time>{{ .pubDate }}</time>
  {{ end }}
{{ end }}
```

### Pattern 4: Hugo Image Processing Pipeline

**What:** The Magus hero image passes through Hugo Pipes at build time — resized for mobile/desktop breakpoints, converted to WebP with JPEG fallback, fingerprinted for cache-busting. Uses `<picture>` element with `srcset`.

**When to use:** Any image that needs responsive delivery and format optimization. The hero image is the highest-impact target on this site.

**Trade-offs:** Increases build time slightly (images cached after first build so subsequent builds are fast). Requires the source image in `assets/` not `static/`.

**Example:**
```html
{{ $src := resources.Get "images/magus-hero.jpg" }}
{{ $webp := $src.Resize "800x webp" }}
{{ $jpeg := $src.Resize "800x jpg" }}
{{ $webp2x := $src.Resize "1600x webp" }}
<picture>
  <source srcset="{{ $webp.RelPermalink }} 1x, {{ $webp2x.RelPermalink }} 2x" type="image/webp">
  <img src="{{ $jpeg.RelPermalink }}" alt="Falken's Mage — Matt Stine" loading="eager" fetchpriority="high">
</picture>
```

### Pattern 5: Self-Hosted Fonts via Hugo Pipes

**What:** Font files live in `themes/arcaeon/assets/fonts/`. Hugo Pipes fingerprints them (cache-busting), and `baseof.html` emits preload hints for the critical weight. `@font-face` declarations live in `_typography.css` with `font-display: swap`.

**When to use:** Always for this project — no external font CDNs is a hard constraint (sub-1s on 3G requires zero third-party latency).

**Trade-offs:** Font files add to repo size. Self-hosting eliminates the ~300-600ms CDN connection overhead on cold loads.

**Example:**
```html
<!-- baseof.html preload -->
{{ $font := resources.Get "fonts/display-regular.woff2" | fingerprint }}
<link rel="preload" href="{{ $font.RelPermalink }}" as="font" type="font/woff2" crossorigin>
```

```css
/* _typography.css */
@font-face {
  font-family: 'DisplayFace';
  src: url('/fonts/display-regular-[hash].woff2') format('woff2');
  font-weight: 400;
  font-style: normal;
  font-display: swap;
}
```

## Data Flow

### Build-Time Data Flow

```
push to main
    ↓
GitHub Actions: checkout → install Hugo Extended → hugo build
    ↓
Hugo reads content/_index.md (front matter → page variables)
    ↓
Hugo evaluates partials:
    sections/currently.html
        → resources.GetRemote("substack RSS URL")
        → transform.Unmarshal (XML → Go struct)
        → first item extracted → rendered into HTML
    sections/hero.html
        → resources.Get("images/magus-hero.jpg")
        → .Resize (WebP + JPEG variants)
        → <picture> element with fingerprinted URLs
    All other sections
        → read front matter vars from content/_index.md
        → render HTML
    ↓
Hugo Pipes processes assets/css/main.css
    → resolves @imports → outputs bundled CSS with fingerprinted filename
    ↓
public/ assembled
    ↓
upload-pages-artifact → actions/deploy-pages
    ↓
falkensmage.com live
```

### Runtime Data Flow (static — nothing dynamic)

```
Browser requests falkensmage.com
    ↓
GitHub Pages serves pre-built index.html
    ↓
Browser parses HTML → requests fingerprinted CSS → requests preloaded fonts
    ↓
Hero image: <picture> element → browser picks WebP or JPEG per capability
    ↓
Below-fold images: loading="lazy" → deferred until scroll
    ↓
No JavaScript required for any section
    ↓
Page interactive (all CSS loaded, fonts swapped in)
```

### Key Data Flows

1. **Editorial content**: `content/_index.md` front matter → page `.Params` → available to all partials via context (`.`). Matt edits the markdown file; all sections that reference those fields update on next build.

2. **RSS content**: Substack RSS XML → `resources.GetRemote` → `transform.Unmarshal` → Go map → `currently.html` partial renders latest post title + link. Cached by Hugo between builds; force-refresh by clearing Hugo cache or bumping cache key.

3. **Styles**: `_tokens.css` defines custom properties → imported by `main.css` → all section CSS files inherit tokens. Section partials reference CSS classes; Hugo Pipes bundles and fingerprints the output file.

4. **Images**: Source JPEG in `assets/images/` → Hugo Pipes resize + format conversion at build → fingerprinted output URLs in `public/assets/` → `<picture>` srcset in rendered HTML.

## Scaling Considerations

This is a static single-page site. Traditional scaling concerns (concurrent users, database load) do not apply. The relevant scaling concerns are:

| Concern | Current Approach | If Site Grows |
|---------|-----------------|---------------|
| Build time | Fast — single page, few assets | Add more sections: still fast. Add 100+ images: cache handles it. |
| Content freshness | RSS updates on every push to main | Add scheduled GitHub Actions cron job (daily rebuild) |
| Additional pages | Not in scope | Hugo's section/single template system handles it without restructuring the theme |
| Additional brand properties | `arcaeon` theme is self-contained | New Hugo site imports the theme as a git submodule |

## Anti-Patterns

### Anti-Pattern 1: All Content Hard-Coded in Templates

**What people do:** Write the identity statement, tagline, social links, and current-focus blurb directly into partial HTML files.

**Why it's wrong:** Every text edit requires touching a template file. Hugo's whole model is separating content from presentation. The `content/_index.md` front matter is the right home for anything Matt will ever edit.

**Do this instead:** Store all editorial text in `content/_index.md` front matter. Templates reference `{{ .Params.identity_statement }}`, `{{ .Params.tagline }}`, etc. Matt edits markdown; templates never change.

### Anti-Pattern 2: data.GetJSON for RSS Fetching

**What people do:** Use the old `data.GetJSON` or `getJSON` template function (common in tutorials pre-2024).

**Why it's wrong:** `data.GetJSON` was deprecated in Hugo v0.123.0 and removed in v0.140.0. A build that uses it will fail on any recent Hugo version.

**Do this instead:** Use `resources.GetRemote $url | transform.Unmarshal`. Works for XML (RSS), JSON, CSV, TOML, YAML.

### Anti-Pattern 3: Fonts in static/ Instead of assets/

**What people do:** Drop font files into `themes/arcaeon/static/fonts/` — the path that "makes sense" since they're static files.

**Why it's wrong:** Files in `static/` are copied as-is with no processing. No fingerprinting means no cache-busting — users get stale font files after updates. Files in `assets/` pass through Hugo Pipes, enabling fingerprinting.

**Do this instead:** Put font files in `themes/arcaeon/assets/fonts/`. Use `resources.Get` + `fingerprint` to produce a cache-busted URL. Reference that URL in `@font-face` declarations and `<link rel="preload">` in the head.

### Anti-Pattern 4: Monolithic index.html

**What people do:** Build the entire single-page layout as one large `index.html` template with all sections inline.

**Why it's wrong:** A 400-line template file is hard to navigate, impossible to test sections in isolation, and makes reordering sections a copy-paste operation prone to error.

**Do this instead:** `index.html` is 10-15 lines — one `{{ partial }}` call per section. Each section lives in its own file under `partials/sections/`. Reordering is a one-line change.

### Anti-Pattern 5: Inline Styles for ARCÆON Colors

**What people do:** Write `style="color: #7a2cff"` or hard-coded hex values in templates when building quickly.

**Why it's wrong:** The ARCÆON palette has specific triad rules and semantic relationships between colors. Hard-coded hex values break the system — a palette update requires a grep-and-replace across templates rather than a single token change.

**Do this instead:** All colors through CSS custom properties. Never write a hex value in a template file.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Feral Architecture (Substack) | `resources.GetRemote` at build time | RSS endpoint: `https://feralarchitecture.substack.com/feed`. Fetched once per build, cached. No API key required — RSS is public. |
| GitHub Pages | `actions/deploy-pages@v5` in GitHub Actions | Requires repo Settings → Pages → Source: GitHub Actions. HTTPS automatic. |
| GitHub Actions | `.github/workflows/hugo.yaml` | Official Hugo workflow pattern from gohugo.io. Use Hugo Extended for CSS processing. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `content/_index.md` ↔ templates | Hugo page context (`.Params`) | Front matter keys must match template references exactly — no validation at edit time. |
| `_tokens.css` ↔ section CSS files | CSS custom property inheritance | Token file must be imported first in `main.css` before any section CSS that references the variables. |
| `baseof.html` ↔ `index.html` | Hugo block/define system | `baseof.html` defines `{{ block "main" . }}`. `index.html` provides `{{ define "main" }}`. Hugo wires them at build. |
| `partials/sections/currently.html` ↔ Substack RSS | `resources.GetRemote` | If RSS fetch fails (network error in CI), Hugo logs error but continues build. Partial should include `{{ with }}` guard to degrade gracefully if feed unavailable. |
| `assets/` ↔ `public/` | Hugo Pipes processing | Asset pipeline runs at `hugo build`. Output files in `public/` have fingerprinted names — do not reference them directly in templates; always use the resource's `.RelPermalink`. |

## Build Order Implications

Dependencies between components determine implementation sequence:

1. **`_tokens.css` + `baseof.html` first** — everything depends on these. The token file defines the design system; `baseof.html` is the HTML shell every partial renders inside. Neither can be deferred.

2. **Static sections next** (hero, identity, social, work, footer) — pure HTML + CSS, no external dependencies. Can be built and styled independently.

3. **`currently.html` last among sections** — depends on RSS fetch working in the build environment. Validate that `resources.GetRemote` reaches Substack from GitHub Actions before building this section.

4. **Image pipeline integrated with hero** — hero section and image pipeline ship together. The `<picture>` element in `hero.html` directly references the processed image resources.

5. **GitHub Actions workflow last** — validate locally with `hugo serve` first. Wire CI only once the local build is clean.

## Sources

- [Hugo Directory Structure — gohugo.io](https://gohugo.io/getting-started/directory-structure/) — HIGH confidence, official docs
- [Hugo Data Sources — gohugo.io](https://gohugo.io/content-management/data-sources/) — HIGH confidence, official docs
- [Hugo Host on GitHub Pages — gohugo.io](https://gohugo.io/host-and-deploy/host-on-github-pages/) — HIGH confidence, includes full workflow YAML
- [Hugo Image Processing — gohugo.io](https://gohugo.io/content-management/image-processing/) — HIGH confidence, official docs
- [resources.GetRemote — gohugo.io](https://gohugo.io/functions/resources/getremote/) — HIGH confidence, official docs
- [data.GetJSON deprecation notice — andreas.scherbaum.la](https://andreas.scherbaum.la/post/2025-03-20_error-deprecated-data-getjson-was-deprecated-in-hugo-v0-123-0-and-will-be-removed-in-hugo-0-140-0-use-resources-get-or-resources-getremote-with-transform-unmarshal/) — HIGH confidence, confirmed against Hugo changelog
- [Embed Substack RSS into Hugo — ibrahimsowunmi.com](https://www.ibrahimsowunmi.com/posts/2023/12/how-to-embed-a-rss-substack-feed-into-your-hugo-static-site/) — MEDIUM confidence, community source, pattern verified against official docs
- [Hugo Image Processing Optimization — dasroot.net](https://dasroot.net/posts/2025/12/hugo-image-processing-optimizing-images-web-performance/) — MEDIUM confidence, community, 2025

---
*Architecture research for: Hugo single-page personal brand site (falkensmage.com)*
*Researched: 2026-04-16*
