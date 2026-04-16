---
phase: 01-theme-foundation
reviewed: 2026-04-16T00:00:00Z
depth: standard
files_reviewed: 7
files_reviewed_list:
  - content/_index.md
  - content/kitchen-sink.md
  - hugo.toml
  - themes/arcaeon/assets/css/main.css
  - themes/arcaeon/layouts/_default/baseof.html
  - themes/arcaeon/layouts/index.html
  - themes/arcaeon/layouts/kitchen-sink/single.html
findings:
  critical: 0
  warning: 4
  info: 3
  total: 7
status: issues_found
---

# Phase 01: Code Review Report

**Reviewed:** 2026-04-16
**Depth:** standard
**Files Reviewed:** 7
**Status:** issues_found

## Summary

Phase 1 establishes the ARCÆON design system foundation: color tokens, typography, glow treatments, sigil grammar, layout scaffolding, and a kitchen sink validation page. The architecture is clean — single CSS file, Hugo's native pipeline, self-hosted fonts, no external dependencies. No security vulnerabilities or logic errors. All critical constraints from CLAUDE.md (no external CDNs, no analytics, sub-1s budget discipline, WCAG AA) are respected in structure.

Four warnings worth addressing before production: a font-path mismatch that will silently 404 in production, missing `<meta name="description">` wiring, an accessibility gap on the kitchen sink's inline color labels, and a stacking context issue that could clip glow effects in certain layouts. Three info-level items round out the quality picture.

---

## Warnings

### WR-01: Font `src` URL will 404 in production (path mismatch)

**File:** `themes/arcaeon/assets/css/main.css:117` and `:125`

**Issue:** The `@font-face` declarations reference fonts via a relative path:
```css
src: url('../fonts/cinzel-latin-wght-normal.woff2') format('woff2');
```
When Hugo processes `assets/css/main.css` through `css.Build`, the output CSS is written to a content-hashed path like `/css/main.abc123.css`. The relative `../fonts/` path resolves correctly from `assets/css/` at build time, but Hugo's `css.Build` does **not** rewrite relative URLs in `@font-face` src declarations the way a PostCSS pipeline would. The font files live in `assets/fonts/`, not `static/fonts/`, meaning Hugo does not copy them to the output without an explicit resource reference.

Confirm whether the fonts are being emitted to the public directory. The `resources.Get` + `fingerprint` calls in `baseof.html` (lines 9 and 11) only generate preload links — they do not themselves cause Hugo to publish the font files. The CSS relative URL also won't be rewritten to the fingerprinted path.

**Fix:** Either move font files to `static/fonts/` and update the CSS path to `/fonts/cinzel-latin-wght-normal.woff2` (absolute, not relative — survives CSS relocation), or use Hugo's resource pipeline to publish them explicitly and inject the fingerprinted URL via a CSS custom property set in the template. The simplest path for a single-page static site:

```css
/* Use absolute paths from static/ root */
src: url('/fonts/cinzel-latin-wght-normal.woff2') format('woff2');
```

And move WOFF2 files from `themes/arcaeon/assets/fonts/` to `themes/arcaeon/static/fonts/`.

---

### WR-02: `<meta name="description">` present in `hugo.toml` but never emitted to `<head>`

**File:** `themes/arcaeon/layouts/_default/baseof.html:1-21`

**Issue:** `hugo.toml` defines `params.description = "Falken's Mage - Matt Stine"` (line 8), and content pages will have front matter descriptions in future. The `<head>` block has no `<meta name="description">` tag at all. Social sharing and search crawlers will fall back to page content scraping, which for the sparse `_index.md` (3 lines of front matter, no body content) means an empty or garbage description.

**Fix:** Add to `baseof.html` inside `<head>`:
```html
{{ with .Description }}
  <meta name="description" content="{{ . }}">
{{ else }}{{ with site.Params.description }}
  <meta name="description" content="{{ . }}">
{{ end }}{{ end }}
```

---

### WR-03: Glow `::before` pseudo-elements use `z-index: -1` without establishing a stacking context on the parent

**File:** `themes/arcaeon/assets/css/main.css:213-231` (`.glow-ambient`), `:251-276` (`.glow-interactive`), `:307-333` (`.glow-radiant-core`)

**Issue:** All three glow components use `position: relative` on the parent and `z-index: -1` on the `::before` pseudo-element to push the glow behind the content. This works when the parent has no `background` — the glow bleeds behind the element into whatever is behind it in the document. However, the moment the parent element itself has a `background-color` (as the kitchen sink demos do: `background: var(--arcaeon-deep-indigo)`), the `z-index: -1` pseudo-element renders *behind the parent's background*, making it invisible.

The kitchen sink demo for `.glow-ambient` and `.glow-interactive` both set a background color inline (lines 61 and 67 of `kitchen-sink/single.html`). In those cases, the glow is fully hidden by the parent's own background. The current demos appear to work only if the parent is transparent.

**Fix:** On glow-bearing elements that have a background, use `isolation: isolate` to create a containing stacking context, then set the `::before` to `z-index: 0` and the content to `z-index: 1`:

```css
.glow-ambient {
  position: relative;
  isolation: isolate;   /* creates stacking context */
}

.glow-ambient::before {
  /* change z-index: -1 to 0, keep other rules */
  z-index: 0;
}

/* Wrap inner content in a span/div with z-index: 1 */
```

Or, for the existing pseudo-element approach to work transparently, document that glow classes must not be applied to elements with a `background` set directly — the background must be on a child element.

---

### WR-04: `.sigil-arc-sm` uses `::before` — conflicts with `.section + .section::before` on sectioned elements

**File:** `themes/arcaeon/assets/css/main.css:418-430`

**Issue:** `.sigil-arc-sm` renders its decorative arc via the `::before` pseudo-element. The section transition rule (lines 354-369) also uses `::before` on `.section + .section`. If `.sigil-arc-sm` is ever applied to a `.section` element (or combined with `.section` on the same node), both `::before` rules will conflict and one will win silently — the decorative arc or the gradient transition, not both. CSS allows only one `::before` per element.

The kitchen sink usage (line 88 of `kitchen-sink/single.html`) applies `.sigil-arc-sm` to a plain `<div>`, so there is no current conflict. But the class name gives no visual warning against composing it onto a `.section`, and the failure mode is invisible.

**Fix:** Either rename to signal it is not safe to compose with `.section`:
```css
/* .sigil-arc-sm → .sigil--arc-sm  (BEM modifier pattern signals it's a modifier) */
```

Or convert the sigil to an `::after` pseudo-element so the before/after slots are not both contested. `.sigil-arc` already uses `::after`; making `.sigil-arc-sm` consistent would also simplify mental model:

```css
.sigil-arc-sm::after {   /* was ::before */
  content: '';
  /* ... rest of arc rules ... */
}
```

---

## Info

### IN-01: `index.html` renders only `.Content` — home page will be blank until content body is added to `_index.md`

**File:** `themes/arcaeon/layouts/index.html:3`

**Issue:** The layout is `{{ .Content }}`, and `content/_index.md` has only front matter and no body content. This is intentional scaffolding for Phase 1, but the current production URL will render a `<main></main>` with no content — a blank dark screen with no heading or placeholder text. Not a bug for a draft phase, but worth tracking explicitly.

**Fix:** Either add a temporary placeholder to `content/_index.md` body, or swap the home layout to the kitchen sink layout temporarily for visual validation during development. When the actual hero section is built in a later phase, the index layout will gain real partials.

---

### IN-02: Color token duplication between `hugo.toml` and CSS

**File:** `hugo.toml:10-21`, `themes/arcaeon/assets/css/main.css:13-32`

**Issue:** All 11 palette values are defined in both `hugo.toml` under `[params.colors]` and as CSS custom properties in `:root`. Hugo 0.160's `@import "hugo:vars"` would allow the CSS to consume values directly from the Hugo config, eliminating the duplication. Currently, if a color is changed in `hugo.toml`, the CSS is not automatically updated — a manual edit in both files is required, and they can drift.

**Fix:** Either remove the `[params.colors]` block from `hugo.toml` if it is not consumed by any template (none of the current templates reference `site.Params.colors`), or wire up the `@import "hugo:vars"` pattern as specified in the tech stack documentation in `CLAUDE.md` to make `hugo.toml` the single source of truth. The CLAUDE.md specifically calls out this feature as a reason for choosing Hugo 0.160.

---

### IN-03: Kitchen sink typography section nests `<h1>` and `<h2>` out of document order

**File:** `themes/arcaeon/layouts/kitchen-sink/single.html:47-49`

**Issue:** The typography demo section (`.section-depth`) contains `<h2>Typography Scale</h2>` as its heading, then immediately renders `<h1>Heading 1 — Cinzel 700 — 2.074rem</h1>` as a visual specimen. An `<h1>` appearing after an `<h2>` in the same section breaks heading hierarchy. Screen readers and accessibility tooling will flag this as a structural issue. This is a kitchen sink demo file marked `draft: true`, so real users won't encounter it, but it will produce false positives if accessibility audits are run against the dev server.

**Fix:** Wrap the heading specimens in a `<div role="presentation">` or use CSS-class-styled `<div>` elements rather than actual heading elements for the visual scale demo:

```html
<div class="display-text" ...>Display — Cinzel 800 — clamp(2.5rem, 8vw, 4rem)</div>
<div style="font-size: var(--text-h1); font-weight: var(--weight-h1); font-family: var(--font-heading); line-height: 1.2;">Heading 1 specimen</div>
```

Or add `role="presentation"` to a wrapper div containing the specimens to signal they are decorative, not structural.

---

_Reviewed: 2026-04-16_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
