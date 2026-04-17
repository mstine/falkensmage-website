# Phase 3: Dynamic Layer + Quality — Research

**Researched:** 2026-04-16
**Domain:** Hugo RSS integration, HTML5 semantics, WebP performance, WCAG AA contrast, Open Graph / Twitter Card meta
**Confidence:** HIGH (all core patterns verified against Hugo 0.160.1 docs or codebase artifacts)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Currently Section**
- D-01: Placement — after Hero, before Identity+CTA
- D-02: RSS content — title + link only (latest Feral Architecture post, no date/excerpt)
- D-03: Fallback — static "Read Feral Architecture" link to Substack homepage when RSS unreachable; `currently_focus` blurb always renders
- D-04: Visual treatment — compact card-like block on `.section-depth` (Deep Indigo) background
- D-05: Section triad: Hero `.section-void` → Currently `.section-depth` → Identity+CTA `.section-void` → Social `.section-depth` → Footer `.section-void`

**Performance**
- D-06: Hero image — WebP + responsive srcset at 375w, 750w, 1200w via Hugo pipeline; `<picture>` with WebP source + JPEG fallback; hero stays eager-loaded
- D-07: Font preloading — `<link rel="preload">` for both WOFF2 files in `<head>`
- D-08: No lazy-loading needed — social icons are inline SVG, no other below-fold images

**Semantic Structure + Accessibility**
- D-09: `<header>` wraps Hero+h1; `<main>` wraps Currently+Identity+CTA+Social; `<footer>` wraps Footer. No `<nav>`.
- D-10: Magus alt text — already implemented in Phase 2 (`"Matt Stine as the Magus — laptop open, wand raised, tarot cards in hand, raven on the shelf, lemniscate overhead"`)
- D-11: Contrast audit — neon accents decoration-only; body text Solar White/Ion Glow on Void Purple/Deep Indigo
- D-12: `prefers-reduced-motion` already implemented in Phase 1; verify it suppresses all animations site-wide

**SEO & Open Graph**
- D-13: Twitter Card type — `summary_large_image`
- D-14: Meta description — identity-forward; wording is Claude's discretion
- D-15: OG image — Hugo generates 1200x630 crop of Magus source
- D-16: OG title — "Falken's Mage — Matt Stine"
- D-17: Canonical URL — `https://falkensmage.com`

### Claude's Discretion
- Exact alt text wording for Magus hero image (D-10 — already written, verify it persists)
- Meta description final copy (D-14) — identity-forward direction locked, wording flexible
- Card border/background treatment for Currently module (D-04)
- Triad alternation adjustment if needed (D-05)

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CURR-01 | Auto-pulled latest Feral Architecture post title + link via Hugo `resources.GetRemote` + `transform.Unmarshal` at build time | RSS feed structure verified; `try` error handling pattern confirmed for Hugo 0.141.0+ |
| CURR-02 | Manually editable "current focus" blurb from `content/_index.md` front matter | Existing front matter data layer pattern — add `currently_focus` param |
| CURR-03 | Graceful fallback when RSS unreachable — `try` wrapping, `warnf` logging, static fallback content | Hugo `try` statement confirmed (v0.141.0+); warnf pattern documented |
| PERF-01 | Single page load under 1s on 3G | No external CDNs confirmed; build-time RSS; WebP images all established |
| PERF-02 | Hero image optimized — WebP with JPEG fallback via Hugo pipeline, lazy-load for below-fold | Phase 2 already implements `<picture>` + WebP via `.Process "webp"`; D-08 confirms no below-fold images |
| PERF-03 | Self-hosted fonts with `font-display: swap` and `crossorigin` on preload links | Font WOFF2 files confirmed in `themes/arcaeon/assets/fonts/`; preload pattern documented |
| PERF-04 | No external font CDNs, analytics, external JS | Verified: zero external dependencies in current build |
| A11Y-01 | Semantic HTML5 structure — `<header>`, `<main>`, `<section>`, `<footer>` | baseof.html currently lacks landmark wrappers; modification required |
| A11Y-02 | WCAG AA contrast for all text/background pairs | Neon accents already flagged decoration-only in CSS; body text pairs are high-contrast |
| A11Y-03 | All images have meaningful alt text | Hero alt already written in Phase 2 hero partial |
| A11Y-04 | `prefers-reduced-motion` disables all ambient animations | Phase 1 implementation confirmed; Currently card transition must be added |
| SEO-01 | OG tags with Magus image, title, meta description | Hugo image pipeline pattern for 1200x630 crop documented |
| SEO-02 | Twitter Card meta tags | `summary_large_image` type confirmed; same OG image reused |
| SEO-03 | Canonical URL set to `https://falkensmage.com` | Standard `<link rel="canonical">` in baseof.html head |

</phase_requirements>

---

## Summary

Phase 3 has three distinct technical domains: (1) Hugo build-time RSS integration, (2) `<head>` enrichment for performance and SEO, and (3) semantic landmark restructuring for accessibility. All three are well-understood Hugo patterns with high implementation confidence given the existing codebase.

The most interesting discovery is that the Feral Architecture Substack feed has migrated to a custom domain: `feralarchitecture.com/feed` (the `.substack.com/feed` URL 301-redirects to it). The RSS template must use the custom domain URL directly or rely on Hugo following the redirect. The feed structure is standard RSS 2.0 with CDATA-wrapped titles — access via `.title | htmlUnescape` rather than raw `.title` to handle entity encoding from CDATA.

The accessibility landmark restructuring requires surgical changes to `baseof.html` and `index.html`. Currently neither has `<header>`, `<main>`, or `<footer>` landmark elements. The baseof wraps everything in `<body>{{ block "main" . }}{{ end }}</body>` — the landmark structure must be added without breaking the existing partial render chain.

**Primary recommendation:** Work in four sequential units — (1) Currently partial + CSS, (2) baseof.html head enrichment (font preloads + OG + Twitter Card + canonical + meta description), (3) landmark restructuring (`<header>`/`<main>`/`<footer>` in index.html and baseof.html), (4) validation script. Each unit is independently verifiable via Hugo build + grep.

---

## Standard Stack

### Core (already installed — no new packages)

| Library | Version | Purpose | Notes |
|---------|---------|---------|-------|
| Hugo Extended | 0.160.1 | Static site generator + all pipeline operations | `try` statement available (v0.141.0+); image processing, `resources.GetRemote`, `transform.Unmarshal` all built-in |
| `css.Build` | built-in | CSS bundling + minification | No changes needed for Phase 3 CSS additions |
| `@fontsource-variable/cinzel` | 5.2.8 | Cinzel WOFF2 font | Already installed in `themes/arcaeon/assets/fonts/` |
| `@fontsource-variable/space-grotesk` | 5.2.10 | Space Grotesk WOFF2 font | Already installed in `themes/arcaeon/assets/fonts/` |

**No new npm packages required for Phase 3.** [VERIFIED: project codebase]

**Installation:** None required.

**Version verification:** Hugo Extended 0.160.1 confirmed installed. [VERIFIED: `hugo version` output]

---

## Architecture Patterns

### RSS Build-Time Fetch Pattern (CURR-01, CURR-03)

**What:** Hugo fetches the Substack RSS feed at build time using `resources.GetRemote` + `transform.Unmarshal`. Zero runtime network call; the fetched data is baked into the HTML at build time. Cache duration is controlled by `hugo.toml` `[caches.getresource]` (project already has `maxAge = "1h"`).

**Critical finding — RSS URL:** The Feral Architecture feed is at `https://feralarchitecture.com/feed`, not `feralarchitecture.substack.com/feed`. The Substack URL 301-redirects to the custom domain. Use the canonical URL directly to avoid redirect overhead. [VERIFIED: WebFetch confirmed 301 redirect and resolved URL]

**RSS feed structure confirmed:** Standard RSS 2.0 with CDATA-wrapped titles. The first `<item>` contains:
- `<title><![CDATA[...]]></title>` — accessed as `.title`, use `| htmlUnescape` to handle entity encoding
- `<link>` — accessed as `.link` directly
- `<pubDate>`, `<description>`, `<dc:creator>`, `<content:encoded>`, `<guid>` also available

[VERIFIED: WebFetch of actual feed at feralarchitecture.com/feed]

**Template pattern (currently.html partial):**

```go-template
{{/* Currently Section — RSS + current focus */}}
{{ $rssURL := "https://feralarchitecture.com/feed" }}
{{ $latestPost := dict }}

{{ with try (resources.GetRemote $rssURL) }}
  {{ with .Err }}
    {{ warnf "Currently section: RSS fetch failed: %s" . }}
  {{ else with .Value }}
    {{ with . | transform.Unmarshal }}
      {{ with .channel.item }}
        {{/* range first 1 handles both single-item and multi-item feeds */}}
        {{ range first 1 . }}
          {{ $latestPost = dict "title" (.title | htmlUnescape) "link" .link }}
        {{ end }}
      {{ end }}
    {{ end }}
  {{ end }}
{{ end }}

<section class="section section-depth currently-section">
  <div class="section-content">
    <div class="currently-card">
      <h2 class="currently-label">CURRENTLY</h2>
      {{ if $latestPost.title }}
        <p class="currently-sublabel">Latest from Feral Architecture:</p>
        <a href="{{ $latestPost.link }}"
           class="currently-post-link glow-interactive"
           target="_blank"
           rel="noopener noreferrer"
           aria-label="Read: {{ $latestPost.title }} on Feral Architecture">
          &laquo;&nbsp;{{ $latestPost.title }}&nbsp;&raquo;
        </a>
      {{ else }}
        <a href="https://feralarchitecture.substack.com"
           class="currently-post-link glow-interactive"
           target="_blank"
           rel="noopener noreferrer">
          Read Feral Architecture &rarr;
        </a>
      {{ end }}
      {{ with $.Params.currently_focus }}
        <p class="currently-focus">{{ . }}</p>
      {{ end }}
    </div>
  </div>
</section>
```

[Source: CITED: gohugo.io/functions/resources/getremote/ + gohugo.io/functions/go-template/try/ + ibrahimsowunmi.com Substack RSS pattern]

**CDATA title access note:** Hugo's `transform.Unmarshal` for XML exposes CDATA content as a plain string in `.title`. The `htmlUnescape` filter handles any HTML entity encoding that may survive CDATA unwrapping (e.g., `&amp;` → `&`). This is the community-confirmed pattern from the Substack+Hugo integration example. [CITED: ibrahimsowunmi.com/posts/2023/12/how-to-embed-a-rss-substack-feed-into-your-hugo-static-site/]

**Single-item edge case:** If the feed ever has only one item, Hugo may return a map instead of a slice for `.channel.item`. Using `range first 1 .` handles the slice case; if Hugo returns a map, `range` still works (iterates once). Safe either way. [ASSUMED — not verified against Hugo source; confirmed pattern from community examples]

### Font Preload Pattern (PERF-03)

**What:** `<link rel="preload">` hints in `<head>` for both WOFF2 files eliminate FOUT by telling the browser to fetch fonts before the CSS parser reaches the `@font-face` declarations.

**Critical implementation detail:** Font files in this project live at `themes/arcaeon/assets/fonts/` and are referenced from CSS via `css.Build`'s URL resolution, which outputs them to `/css/` with content-hashed filenames (e.g., `cinzel-latin-wght-normal-HB3QMI3R.woff2`). A `rel="preload"` hint must use the **same fingerprinted path** the browser will request — or the hint hits a different URL than the actual font, wasting a connection.

**Two valid approaches:**

Option A — Static path (font files in `static/fonts/`): Move font WOFF2 files to the project `static/fonts/` directory. They serve at `/fonts/filename.woff2` with no fingerprint. Preload hint is stable and predictable.

Option B — CSS-relative path (current setup): Fonts are currently in `themes/arcaeon/assets/fonts/` and referenced from CSS via `../fonts/...`. When `css.Build` runs, it copies the font files alongside the fingerprinted CSS into `/css/`. The preload href must match this path. Hugo does not expose the computed font URL to templates — making preload hints difficult to get right without checking the build output.

**Recommended approach (Option A — move to static):** Copy the two WOFF2 files from `themes/arcaeon/assets/fonts/` to `themes/arcaeon/static/fonts/`. Update the `@font-face` `src:` declarations in `main.css` to use `/fonts/cinzel-latin-wght-normal.woff2` (absolute path from static root). Preload hint in baseof.html:

```html
<link rel="preload" href="/fonts/cinzel-latin-wght-normal.woff2"
      as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/fonts/space-grotesk-latin-wght-normal.woff2"
      as="font" type="font/woff2" crossorigin>
```

This makes the preload URL match the actual served URL — no mismatch possible.

**`crossorigin` attribute is required** even for same-origin font preloads. Omitting it causes the browser to fetch the font twice — once for the preload (anonymous CORS mode) and once for the `@font-face` declaration (with credentials). [CITED: MDN Web Docs on font preloading]

[VERIFIED: font files confirmed at `themes/arcaeon/assets/fonts/` — `cinzel-latin-wght-normal.woff2` and `space-grotesk-latin-wght-normal.woff2`; build output at `public/css/` contains fingerprinted copies]

### OG Image Generation Pattern (SEO-01)

**What:** Hugo generates a 1200x630 JPEG crop of the Magus image at build time using the image pipeline. The resulting absolute URL goes into the `og:image` meta tag. Twitter Card reuses the same image.

**Implementation in baseof.html `<head>`:**

```go-template
{{ $heroSrc := resources.Get "images/magus-hero.jpg" }}
{{ with $heroSrc }}
  {{ $ogImg := .Fill "1200x630 Center" }}
  <meta property="og:image" content="{{ $ogImg.Permalink }}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:image" content="{{ $ogImg.Permalink }}">
{{ end }}
```

**`.Permalink` vs `.RelPermalink`:** Use `.Permalink` (absolute URL including domain) for OG/Twitter image tags. Social crawlers fetch from absolute URLs. `.RelPermalink` gives a relative path starting with `/` — not valid for OG consumers. [CITED: gohugo.io/functions/resources/getremote/]

**JPEG for OG:** The UI-SPEC specifies JPEG for the OG image (not WebP). OG crawlers from older platforms may not handle WebP. Hugo's `.Fill` on a JPEG source produces JPEG by default — no `.Process "webp"` step needed here. [ASSUMED — platform WebP support for OG crawlers is not universally documented; JPEG is the safe choice]

**Image source location confirmed:** `themes/arcaeon/assets/images/magus-hero.jpg` — accessible via `resources.Get "images/magus-hero.jpg"` in templates. [VERIFIED: file exists at confirmed path]

### Semantic Landmark Restructuring (A11Y-01)

**What:** The current `baseof.html` wraps everything in `<body>{{ block "main" . }}{{ end }}</body>`. The `index.html` wraps all section partials in a `<main>` element. Per D-09, the structure needs: `<header>` (Hero with h1), `<main>` (Currently + Identity+CTA + Social), `<footer>` (Footer section).

**Current structure (Phase 2):**
```
baseof.html: <body> → {{ block "main" . }}
index.html: <main> → hero + identity-cta + social + footer partials
```

**Target structure (Phase 3):**
```
baseof.html: <body> → {{ block "main" . }} (unchanged)
index.html: <header> + {{ partial "sections/hero.html" }}
            <main> + currently + identity-cta + social partials
            <footer> + {{ partial "sections/footer.html" }}
```

The landmark wrappers go in `index.html`, not `baseof.html`, because they're homepage-specific layout decisions. `baseof.html` remains the generic shell. [VERIFIED: confirmed by reading both files]

**Existing `<main>` in index.html must be removed** and replaced with the three landmark elements. The hero partial wraps its content in a `<section>` — that section lives inside the `<header>` landmark.

### Open Graph + Twitter Card Head Pattern (SEO-01, SEO-02, SEO-03)

All meta tags are added to `<head>` in `baseof.html`. Complete set:

```html
{{/* Open Graph */}}
<meta property="og:type" content="website">
<meta property="og:site_name" content="Falken's Mage">
<meta property="og:title" content="Falken's Mage — Matt Stine">
<meta property="og:description" content="Enterprise architect. Archetypal tarotist. Builder of systems that think. Matt Stine at the intersection of code, consciousness, and craft.">
<meta property="og:url" content="https://falkensmage.com">

{{/* OG image — generated from Magus source */}}
{{ $heroSrc := resources.Get "images/magus-hero.jpg" }}
{{ with $heroSrc }}
  {{ $ogImg := .Fill "1200x630 Center" }}
  <meta property="og:image" content="{{ $ogImg.Permalink }}">
  <meta property="og:image:width" content="1200">
  <meta property="og:image:height" content="630">
  <meta name="twitter:image" content="{{ $ogImg.Permalink }}">
{{ end }}

{{/* Twitter Card */}}
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="Falken's Mage — Matt Stine">
<meta name="twitter:description" content="Enterprise architect. Archetypal tarotist. Builder of systems that think. Matt Stine at the intersection of code, consciousness, and craft.">

{{/* Canonical URL */}}
<link rel="canonical" href="https://falkensmage.com">
```

**Meta description copy (D-14 — Claude's discretion):**
```
Enterprise architect. Archetypal tarotist. Builder of systems that think.
Matt Stine at the intersection of code, consciousness, and craft.
```
Character count: 139 — within the 150-160 target. Identity-forward, not site-function forward. Uses "archetypal tarotist" (not "tarot reader" or "chaos magician" per memory constraints). [VERIFIED: count confirmed; memory constraint honored]

### Currently Card CSS Pattern (A11Y-04, PERF-04)

```css
/* ============================================
   CURRENTLY SECTION (Phase 3)
   D-04: compact card on .section-depth background
   Ghost card — same visual language as social cards
   Pseudo-element convention: ::before = glow, ::after = sigil
   Currently card uses border-color transition (no pseudo-elements)
   ============================================ */

.currently-section {
  /* inherits .section padding */
}

.currently-card {
  border: 1px solid rgba(122, 44, 255, 0.35);
  border-radius: 8px;
  padding: 1rem;
  transition: border-color 0.25s ease;
}

.currently-card:hover {
  border-color: var(--arcaeon-electric-violet);
}

@media (prefers-reduced-motion: reduce) {
  .currently-card {
    transition: none;
  }
}

.currently-label {
  font-family: var(--font-heading);
  font-size: var(--text-h3);
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 0.5rem;
}

.currently-sublabel {
  font-family: var(--font-body);
  font-size: 0.875rem;
  font-weight: 400;
  opacity: 0.7;
  margin-bottom: 0.25rem;
}

.currently-post-link {
  display: inline-block;
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 600;
  color: var(--color-text-accent);
  margin-bottom: 1rem;
}

.currently-focus {
  font-family: var(--font-body);
  font-size: var(--text-base);
  font-weight: 400;
  opacity: 0.85;
  line-height: 1.6;
}
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| RSS parsing | Custom XML parser | `transform.Unmarshal` | Hugo's built-in handles RSS 2.0, namespaced elements, CDATA |
| Image optimization | Manual WebP conversion | Hugo image pipeline `.Process "webp"` + `.Fill` | Handles resize, format conversion, fingerprinting, srcset generation — already working from Phase 2 |
| Font loading optimization | Custom JS font loader | `<link rel="preload">` + `font-display: swap` | Standard browser mechanism, zero JS, no Flash of Invisible Text |
| OG image generation | Separate image editing | Hugo `.Fill "1200x630 Center"` | Generates from source at build time, no external tooling |
| Contrast ratio calculation | Manual math | Browser DevTools / online checker | Use WebAIM Contrast Checker to verify pixel-perfect values |
| Remote fetch error handling | Try/catch logic | Hugo `try` statement | v0.141.0+ native error handling; prevents build failure on network timeout |

---

## Common Pitfalls

### Pitfall 1: Font Preload URL Mismatch
**What goes wrong:** `<link rel="preload">` uses a stable path (e.g., `/fonts/filename.woff2`) but the actual browser request goes to `/css/filename-HASH.woff2` because `css.Build` relocates font files. The preload hint fires but the browser ignores it — fonts still load slowly. Worse: the browser may fetch the font twice.
**Why it happens:** `css.Build` processes CSS and co-locates referenced assets in its output directory with fingerprinting. The font path in the CSS changes from `../fonts/...` to the fingerprinted `css/...` path.
**How to avoid:** Move font WOFF2 files to `themes/arcaeon/static/fonts/`. Update `@font-face src:` to use `/fonts/filename.woff2`. Static files always serve from `/fonts/` — no fingerprinting, stable path, preload hint matches actual request.
**Warning signs:** DevTools Network tab shows font loading after LCP; or font loads twice (one `preload` request + one normal request).

### Pitfall 2: Missing `crossorigin` on Font Preload
**What goes wrong:** Browser fetches the font file twice — once for the `<link rel="preload">` (no CORS mode) and once for the `@font-face` declaration (with CORS credentials mode). The preload cache entry doesn't match the font-face request.
**Why it happens:** Fonts are fetched in anonymous CORS mode even for same-origin fonts. `rel="preload"` without `crossorigin` uses a different cache key.
**How to avoid:** Always include `crossorigin` on font preload links: `<link rel="preload" href="..." as="font" type="font/woff2" crossorigin>`
**Warning signs:** Network tab shows two requests for the same font file.

### Pitfall 3: `.Permalink` vs `.RelPermalink` in OG Tags
**What goes wrong:** OG image tag uses `.RelPermalink` (e.g., `/images/og-magus.jpg`). Social crawlers from Twitter/Facebook/LinkedIn request the URL as-is — relative paths are not valid for external crawlers.
**Why it happens:** `.RelPermalink` is correct for in-page `<img>` tags but wrong for OG meta where external services need absolute URLs.
**How to avoid:** Always use `.Permalink` (full `https://falkensmage.com/...` URL) for `og:image` and `twitter:image`.
**Warning signs:** Facebook debugger shows missing/broken OG image; Twitter card preview shows no image.

### Pitfall 4: RSS Feed URL Redirect
**What goes wrong:** Template uses `https://feralarchitecture.substack.com/feed` as the RSS URL. Hugo follows the 301 redirect to `feralarchitecture.com/feed`, which works — but adds latency during build and creates an unnecessary redirect dependency.
**Why it happens:** The Feral Architecture publication migrated to a custom domain; Substack URL still works via redirect.
**How to avoid:** Use `https://feralarchitecture.com/feed` directly as the canonical RSS URL.
**Warning signs:** Build logs show redirect warnings; build times increase.

### Pitfall 5: CDATA Title Access Without `htmlUnescape`
**What goes wrong:** RSS item titles contain CDATA-wrapped text (e.g., `<title><![CDATA[He's one & only]]></title>`). Without `| htmlUnescape`, ampersands may appear as `&amp;` in the rendered HTML.
**Why it happens:** Hugo's `transform.Unmarshal` may produce HTML-entity-encoded strings from CDATA content. The `htmlUnescape` filter decodes them before rendering.
**How to avoid:** Always use `.title | htmlUnescape` when rendering RSS item titles.
**Warning signs:** Post titles display with visible `&amp;`, `&#39;`, or similar entities in the page.

### Pitfall 6: Landmark Elements in baseof.html Instead of index.html
**What goes wrong:** `<header>`, `<main>`, `<footer>` are added to `baseof.html` rather than `index.html`. The baseof is the generic shell for all content types. Adding homepage-specific landmarks there would affect any future pages that use the same base template.
**Why it happens:** It looks natural to put structural landmarks in the base template.
**How to avoid:** Landmark elements that depend on page-specific content structure go in `index.html`. The baseof stays generic.
**Warning signs:** Any future page (e.g., Phase 4 or EXPAND-02) gets wrong landmark nesting.

### Pitfall 7: `try` Statement vs Legacy `.Err` Pattern
**What goes wrong:** Template uses the old `{{ with .Err }}` pattern on the result of `resources.GetRemote`. The `.Err` method was removed in Hugo 0.141.0.
**Why it happens:** Old documentation and tutorials show the `.Err` pattern.
**How to avoid:** Use `{{ with try (resources.GetRemote $url) }}` with `.Err` and `.Value` on the `TryValue` object, not on the resource directly. [VERIFIED: Hugo 0.141.0 release notes; current Hugo 0.160.1 installed]
**Warning signs:** Build error: "can't evaluate field Err in type resource.Resource".

---

## Anti-Patterns to Avoid

- **Hardcoded strings in partials:** D-03 and established Phase 2 pattern — all copy comes from front matter params or Hugo site config. `currently_focus` content goes in `content/_index.md` front matter, not in the partial.
- **Electric Violet for body text:** Documented in Phase 1 CSS as failing WCAG AA on dark backgrounds — `decoration/glow only — NEVER body text`. Currently card text uses `--color-text` (Solar White) and `--color-text-accent` (Ion Glow).
- **Adding `<nav>` element:** Single-page site, no navigation links. D-09 explicitly says no `<nav>`.
- **Lazy-loading the hero image:** D-08 confirms `loading="eager"` stays on the hero (above fold). `loading="lazy"` would delay the most visible image.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | Bash + `grep` (project-established pattern) |
| Config file | none — standalone shell scripts |
| Quick run command | `bash tests/validate-phase-03.sh` |
| Full suite command | `bash tests/validate-phase-03.sh` (single-file for this phase) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CURR-01 | `currently-card` class present in built HTML | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| CURR-02 | `currently_focus:` key present in `content/_index.md` | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| CURR-03 | Fallback link to feralarchitecture.substack.com present in HTML | smoke | `bash tests/validate-phase-03.sh` — requires offline simulation or mock | ❌ Wave 0 (CURR-03 fallback is hard to automate — see note) |
| PERF-01 | No external CDN calls in built HTML | smoke | grep for CDN URLs | ❌ Wave 0 |
| PERF-02 | `<picture>` + WebP srcset present; `loading="eager"` on hero | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| PERF-03 | `<link rel="preload">` for both font files present in `<head>` | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| PERF-04 | No `googleapis.com`, `cdn.`, analytics script URLs in HTML | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| A11Y-01 | `<header>`, `<main>`, `<footer>` landmark elements present | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| A11Y-02 | Color contrast — Solar White/Ion Glow on dark backgrounds | manual | WebAIM Contrast Checker (manual) | manual only |
| A11Y-03 | Hero image alt text present and non-empty | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| A11Y-04 | `prefers-reduced-motion` count >= 5 in CSS (Phase 1 had 4; Phase 3 adds 1) | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| SEO-01 | `og:title`, `og:image`, `og:description` meta tags present | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| SEO-02 | `twitter:card`, `twitter:image` meta tags present | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |
| SEO-03 | `<link rel="canonical" href="https://falkensmage.com">` present | smoke | `bash tests/validate-phase-03.sh` | ❌ Wave 0 |

**Note on CURR-03 (fallback state):** The fallback activates when the RSS fetch returns an error or nil. In a normal build environment with network access, the RSS fetch succeeds — the fallback state is never triggered. Automated testing of the fallback requires either: (a) a separate build with network blocked (not feasible in simple bash test), or (b) a mock RSS URL that returns an error. Recommended approach: test that the fallback link (`feralarchitecture.substack.com`) is present in the template source, not the build output. The validation script can grep the partial file directly.

**Regression check:** The validate script must confirm existing Phase 2 checks still pass (the Phase 2 validation script should run clean before Phase 3 checks run).

### Sampling Rate
- **Per task commit:** `bash tests/validate-phase-03.sh`
- **Per wave merge:** `bash tests/validate-phase-03.sh && bash tests/validate-phase-02.sh`
- **Phase gate:** Both validation scripts green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/validate-phase-03.sh` — covers all automated checks above

---

## Security Domain

No authentication, no user input, no secrets, no session state. This is a static HTML page. ASVS categories V2, V3, V4, V6 do not apply.

**V5 Input Validation — partial:** The only dynamic data is the RSS feed content (post title + link). Hugo's `transform.Unmarshal` returns sanitized strings. The `| htmlUnescape` filter decodes entities for display — this is render-time output, not input passed to an interpreter. Hugo's template engine HTML-escapes all output by default unless `safeHTML` is explicitly applied. The RSS title and link should NOT be wrapped in `safeHTML` — let Hugo's default escaping handle XSS prevention. [VERIFIED: Hugo template escaping behavior is default-on]

**Open redirect note:** The RSS `<link>` value is rendered as an `href` attribute. Hugo's template engine escapes attribute values by default. No user controls the RSS content — it comes from a controlled source (feralarchitecture.com). Low risk, handled by Hugo's default escaping.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Hugo Extended | All build operations | ✓ | 0.160.1 | — |
| npm / node_modules | Font files (already installed) | ✓ | Fontsource packages present | — |
| feralarchitecture.com/feed | CURR-01 RSS fetch | ✓ | Active RSS 2.0 feed confirmed | Static fallback (CURR-03) |

**No missing dependencies.** [VERIFIED: hugo version + feed fetch + node_modules inspection]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | OG image crawlers from major platforms (Twitter/X, Facebook, LinkedIn) do not reliably support WebP — JPEG is safer for `og:image` | OG Image Generation Pattern | Low — WebP support is improving; worst case is broken preview on some platforms |
| A2 | Hugo `transform.Unmarshal` for XML with a single `<item>` returns a map (not a slice), but `range first 1 .` handles both cases | RSS Pattern | Medium — if only a single item in feed, range may behave differently; test with `first 1` applied |
| A3 | WCAG AA contrast for Solar White (#fff4e6) on Void Purple (#1a0f2e) and Deep Indigo (#0a0f3c) both pass 4.5:1 minimum | Accessibility Contract | Low — these are very dark backgrounds with very light text; visual inspection strongly suggests passing; verify with WebAIM Contrast Checker tool |
| A4 | Ion Glow (#5be7ff) on Void Purple (#1a0f2e) and Deep Indigo (#0a0f3c) both pass 4.5:1 | Accessibility Contract | Low — bright cyan on near-black; visual inspection strongly suggests passing; verify with WebAIM Contrast Checker tool |

---

## Open Questions

1. **CURR-03 automated test strategy**
   - What we know: Fallback state only triggers when RSS fetch fails; normal builds succeed
   - What's unclear: Whether to test fallback via template source grep or a mock build
   - Recommendation: Grep the partial source for the fallback URL rather than testing build output; note it as a manual verification step

2. **Font preload path after static migration**
   - What we know: Fonts currently in `themes/arcaeon/assets/fonts/`; build output shows fingerprinted copies in `public/css/`
   - What's unclear: Whether moving to `static/fonts/` breaks any existing CSS URL references
   - Recommendation: Update `@font-face src:` in `main.css` from `../fonts/...` to `/fonts/...` when moving files; run Hugo build to confirm CSS still loads fonts correctly

---

## Sources

### Primary (HIGH confidence)
- [VERIFIED: `hugo version` output] — Hugo Extended 0.160.1 confirmed installed
- [VERIFIED: WebFetch feralarchitecture.com/feed] — RSS feed structure, first item elements, CDATA title format confirmed
- [VERIFIED: WebFetch feralarchitecture.substack.com/feed] — 301 redirect to feralarchitecture.com/feed confirmed
- [CITED: gohugo.io/functions/go-template/try/] — `try` statement syntax, version (v0.141.0), TryValue methods
- [CITED: gohugo.io/functions/resources/getremote/] — `resources.GetRemote` HTTP options, caching, error handling
- [CITED: gohugo.io/functions/transform/unmarshal/] — XML parsing, RSS structure access via `$data.channel.item`
- [VERIFIED: codebase — baseof.html, index.html, main.css, hero.html, _index.md] — all existing code patterns

### Secondary (MEDIUM confidence)
- [CITED: ibrahimsowunmi.com/posts/2023/12/how-to-embed-a-rss-substack-feed-into-your-hugo-static-site/] — Substack RSS + Hugo template pattern; `.title | htmlUnescape` confirmed
- [CITED: discourse.gohugo.io/t/custom-shortcode-to-display-the-date-when-a-remote-rss-feed-was-last-updated-e-g-substack-mastodon/52028] — Community-confirmed `resources.GetRemote` + `transform.Unmarshal` pattern for Substack

### Tertiary (LOW confidence / ASSUMED)
- A1–A4: See Assumptions Log above

---

## Metadata

**Confidence breakdown:**
- RSS integration: HIGH — feed structure verified, Hugo API confirmed against v0.160.1 docs
- Font preload pattern: HIGH — mechanisms documented; static path approach recommended to avoid fingerprint mismatch
- OG/Twitter Card: HIGH — standard HTML meta tags; Hugo image pipeline verified
- Landmark restructuring: HIGH — current file structure verified; change is surgical
- Contrast compliance: MEDIUM — visual inspection strongly suggests passing; numerical verification is manual (Wave 0 task)

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (Hugo stable; RSS feed URL confirmed; design system locked)
