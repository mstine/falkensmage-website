# Pitfalls Research

**Domain:** Hugo single-page personal brand site — custom theme, GitHub Pages, dark palette, self-hosted fonts, RSS at build time
**Researched:** 2026-04-16
**Confidence:** HIGH (Hugo-specific pitfalls verified via official docs and Hugo discourse; CSS/accessibility pitfalls verified via MDN and W3C)

---

## Critical Pitfalls

### Pitfall 1: baseURL Mismatch Breaks All Asset Paths

**What goes wrong:**
Hugo hardcodes the `baseURL` into every generated link, stylesheet reference, and image path. If `baseURL` in `hugo.toml` doesn't exactly match the live domain — including trailing slash behavior — every asset on the deployed site returns 404. This is the single most common cause of a "build succeeded, site broken" situation with GitHub Pages.

**Why it happens:**
Developers set `baseURL = "http://localhost:1313/"` for local dev and forget to update it for production. Or they set it to the GitHub Pages default URL (`https://username.github.io/repo/`) when the site actually lives on a custom apex domain (`https://falkensmage.com`). These are not the same URL and Hugo will generate wrong paths for whichever context doesn't match.

**How to avoid:**
Set `baseURL = "https://falkensmage.com/"` in `hugo.toml` from day one — this is the production domain and GitHub Pages will serve it there. For local development, pass `--baseURL` on the CLI or use `hugo server` which overrides automatically. Never commit a localhost baseURL. Confirm the value is correct before the first deployment.

**Warning signs:**
- CSS loads locally but 404s on deployed site
- Images load in `hugo server` but break on GitHub Pages
- All links have doubled path segments (e.g., `/falkensmage.com/styles.css`)

**Phase to address:** Phase 1 (Foundation / Theme scaffolding) — set correctly before writing a single template.

---

### Pitfall 2: CNAME File Gets Overwritten on Deploy

**What goes wrong:**
GitHub Pages requires a `CNAME` file in the repository root (or `gh-pages` branch root) containing the custom domain (`falkensmage.com`). Hugo's build process outputs to `/public` and then GitHub Actions pushes that directory to `gh-pages`. If the CNAME file lives only in the repo root and not in `/static/`, every deploy overwrites it and GitHub Pages silently stops serving the custom domain — reverting to the `.github.io` URL or breaking HTTPS provisioning.

**Why it happens:**
Developers add the CNAME in GitHub Pages settings UI, which writes it to the `gh-pages` branch. The next deploy force-pushes `/public` over that branch, wiping the CNAME. The GitHub UI shows the domain is configured but the file is gone.

**How to avoid:**
Place `static/CNAME` in the Hugo project root containing `falkensmage.com`. Hugo copies everything in `/static/` to `/public/` verbatim during build. This way the CNAME is always present in every deploy artifact and can never be overwritten.

**Warning signs:**
- Custom domain was working, then stopped after a deploy
- GitHub Pages settings show "Your site is published at https://falkensmage.github.io/..." instead of the custom domain
- HTTPS certificate error after deployment

**Phase to address:** Phase 2 (GitHub Actions / CI-CD pipeline setup) — add `static/CNAME` before first production deploy.

---

### Pitfall 3: Hugo GITHUB_TOKEN Permissions Fail First Deploy

**What goes wrong:**
The default `GITHUB_TOKEN` in GitHub Actions has read-only permissions. Deploying to `gh-pages` requires `contents: write`. Without this, the workflow appears to run but the push to `gh-pages` silently fails or errors with a permissions message. First-time deployers frequently miss this and spend significant time debugging.

**Why it happens:**
GitHub tightened default token permissions. Older tutorials that predate this change don't include the `permissions` block. Copy-pasted workflow files from these tutorials fail silently.

**How to avoid:**
Add the following to the workflow file explicitly:

```yaml
permissions:
  contents: write
  pages: write
  id-token: write
```

Alternatively use the GitHub-native Pages deploy action (`actions/deploy-pages`) which handles this via the `pages: write` permission. Verify the workflow's permissions block before first run.

**Warning signs:**
- Workflow shows green checkmark but site hasn't updated
- Action log shows "remote: Permission to ... denied" or "refusing to allow"
- `gh-pages` branch not created after first successful build

**Phase to address:** Phase 2 (GitHub Actions pipeline) — verify permissions block before first deployment attempt.

---

### Pitfall 4: Neon Accent Colors Fail WCAG AA on Dark Backgrounds

**What goes wrong:**
The ARCÆON palette is built around electric violet (`#7a2cff`), neon magenta (`#ff3cac`), and electric blue (`#2fd3ff`) against deep indigo (`#0a0f3c`) and void purple (`#1a0f2e`) backgrounds. Several of these combinations will fail WCAG AA 4.5:1 contrast ratio for body text — particularly electric violet on deep indigo backgrounds, which can fall as low as 2.5:1. This makes the site legally and ethically inaccessible and tanks Lighthouse accessibility scores.

**Why it happens:**
Neon colors appear perceptually bright to the human eye but WCAG's luminance formula measures photometric brightness, not perceptual vividness. A color that "pops" visually can still fail the mathematical test. Dark mode palettes are especially prone to this — WCAG 2.x is notoriously lenient on light-on-dark combinations but still flags the most saturated neons. Designers assume a color that looks bright must contrast well.

**How to avoid:**
Run every text-on-background color pair through the WebAIM Contrast Checker before implementing. The primary body text color must achieve 4.5:1 against the background. Reserve the neon accents (electric violet, neon magenta) for decorative elements, glows, borders, and icons — not body copy. Use Solar White (`#fff4e6`) or Ion Glow (`#5be7ff`) for readable body text on dark backgrounds. Check interactive states (hover, focus) separately — they often fail when the base state passes.

**Warning signs:**
- Lighthouse accessibility score below 90 after first build
- WebAIM checker showing ratio below 4.5:1 for any text/background pair
- Any use of Electric Violet `#7a2cff` as body text color on a dark background

**Phase to address:** Phase 1 (ARCÆON theme tokens / CSS custom properties) — build a validated color-pair reference table before writing any typography rules.

---

### Pitfall 5: RSS Fetch at Build Time Fails Silently and Breaks the Build

**What goes wrong:**
The "Currently" section fetches the latest Feral Architecture post via Substack RSS at build time using `resources.GetRemote`. If Substack is slow, rate-limiting the IP, returning a non-200, or if the feed URL changes, the build fails entirely — taking down CI/CD. Alternatively, if error handling is missing, Hugo exits with a fatal error and the deploy never runs.

**Why it happens:**
`resources.GetRemote` will halt the build on HTTP failure unless the error is explicitly caught with `errorf` and handled. The deprecated `data.GetJSON` had the same behavior and was removed in Hugo 0.123 — projects still using it break on Hugo upgrades. Build-time network calls are a fragile dependency in a CI/CD pipeline.

**How to avoid:**
Use `resources.GetRemote` with explicit try/catch error handling:

```go-html-template
{{ $feed := "" }}
{{ with try (resources.GetRemote "https://feralarchitecture.substack.com/feed") }}
  {{ with .Err }}
    {{ warnf "RSS fetch failed: %s" . }}
  {{ else }}
    {{ $feed = .Value }}
  {{ end }}
{{ end }}
```

Configure `cacheDir` and `maxAge` in `hugo.toml` under `[caches]` so the feed is cached between builds. Set a reasonable timeout. The template should render a graceful fallback (a static "latest post" link) when the fetch fails, rather than empty content.

**Warning signs:**
- CI/CD pipeline fails intermittently for no apparent code reason
- Error log shows "failed to GET resource" or "context deadline exceeded"
- Build succeeds locally but fails in GitHub Actions (network policy differences)

**Phase to address:** Phase 3 (Currently section / dynamic content) — implement error handling before first attempt to fetch live RSS.

---

### Pitfall 6: Animating box-shadow for Glow Effects Destroys Mobile Performance

**What goes wrong:**
The ARCÆON aesthetic calls for glow treatments on buttons, links, and potentially the hero. The intuitive CSS implementation is animating `box-shadow` on hover/focus (e.g., `box-shadow: 0 0 20px #7a2cff`). On mobile — especially mid-range Android devices — animated `box-shadow` triggers paint and composite cycles on every frame because it is not GPU-composited. The result is janky animations, dropped frames, and battery drain on a site that should feel effortlessly alive.

**Why it happens:**
`box-shadow` changes cause the browser's paint phase to re-execute on every animation frame. Only `transform`, `opacity`, `filter`, and `clip-path` can run on the compositor thread (GPU). Everything else hits the main thread.

**How to avoid:**
Implement glow effects via animated `opacity` on a `::before` or `::after` pseudo-element that has the static `box-shadow` set. The pseudo-element sits at opacity 0 at rest and transitions to opacity 1 on hover. This way only `opacity` is animated — GPU-composited, no paint cost. For ambient pulse animations on the hero, use `filter: drop-shadow()` with `opacity` variation rather than `box-shadow`. Always include `will-change: opacity` on animated pseudo-elements.

**Warning signs:**
- Chrome DevTools Performance panel shows paint rectangles on hover interactions
- Animations feel smooth on desktop but stutter on actual phone hardware
- Any `transition: box-shadow` in the CSS codebase

**Phase to address:** Phase 1 (ARCÆON theme component styles) — establish the glow animation pattern correctly from the first button/link implementation.

---

### Pitfall 7: Font Loading Causes FOIT and Layout Shift

**What goes wrong:**
Self-hosted fonts without `font-display: swap` cause FOIT (Flash of Invisible Text) — the browser hides all text until the font file downloads. On a 3G connection this is 1-3 seconds of blank content. Even with `font-display: swap`, improper implementation causes Cumulative Layout Shift (CLS) as fallback fonts reflow to the custom font metrics. Both kill Lighthouse scores and the perceived performance of the site.

**Why it happens:**
Developers add `@font-face` declarations without `font-display: swap`. Or they preload the font file but omit the `crossorigin` attribute, which causes the browser to download the font twice — once for the preload and once for the CSS-triggered load, because without `crossorigin`, the preload cache is not consulted for the CSS-triggered fetch.

**How to avoid:**
Every `@font-face` declaration must include `font-display: swap`. Preload the primary display font in `<head>` with both `rel="preload"` and `crossorigin` (even though it is same-origin — the attribute is required for font preloads to hit the preload cache). Use WOFF2 exclusively — it is 25-40% smaller than WOFF and universally supported in all relevant browsers. Subset fonts to the character ranges actually used (Latin at minimum, omit Cyrillic/CJK unless needed). For a dark-aesthetic site where the font is a primary brand element, size matters: a 500KB unsubsetted typeface will blow the 1s on 3G budget.

**Warning signs:**
- Lighthouse LCP score high despite no large images
- Blank page visible for 1-2 seconds on throttled connection testing
- DevTools Network tab shows the font file downloading twice
- `font-display` property absent from `@font-face` declarations

**Phase to address:** Phase 1 (Typography / font selection and implementation) — validate font loading approach before selecting the final typeface, since subsetting support varies by foundry.

---

### Pitfall 8: Open Graph Image Uses Relative URL and Breaks Social Previews

**What goes wrong:**
Social platforms (Twitter/X, LinkedIn, Slack, Bluesky) require the `og:image` URL to be absolute (`https://falkensmage.com/images/og-cover.jpg`), not relative (`/images/og-cover.jpg`). If the Hugo template outputs a relative URL for `og:image`, every social share generates a broken preview — no image appears. This is invisible in local testing because the browser fills in the domain, but crawlers do not.

**Why it happens:**
Hugo's template functions like `absURL` vs. `relURL` are easy to conflate. Developers output relative paths for consistency and don't test social previews until after launch when the damage is already done. The Magus image is a core brand asset — a broken OG preview on every social share is a significant brand hit.

**How to avoid:**
Use Hugo's `absURL` function for the `og:image` meta tag:
```go-html-template
<meta property="og:image" content="{{ "images/magus-og.jpg" | absURL }}">
```
Ensure `baseURL` in `hugo.toml` is set to `https://falkensmage.com/` (with HTTPS and trailing slash) — `absURL` prepends this value. Validate OG tags using the Twitter Card Validator and Facebook Sharing Debugger before launch. The OG image should be 1200x630px (the Substack cover image at 1200x628 is close enough).

**Warning signs:**
- Social share preview shows a broken image placeholder
- Twitter Card Validator or OG debugger shows `og:image` as a relative path
- `relURL` used instead of `absURL` for the image meta tag

**Phase to address:** Phase 4 (SEO / meta tags) — verify absolute URL output using a validator tool before considering the phase complete.

---

### Pitfall 9: prefers-reduced-motion Left Unimplemented

**What goes wrong:**
The ambient animation on the hero section and hover glow effects create a vestibular disorder risk for users who have system-level reduced motion preferences set. Without `prefers-reduced-motion: reduce` handling, the site fails WCAG 2.1 Success Criterion 2.3.3 (Animation from Interactions) and causes real physical harm to affected users. This is not hypothetical — the hero ambient animation is the exact type of motion that triggers vestibular symptoms.

**Why it happens:**
Developers implement animations in the main CSS and treat accessibility as a final pass. By the time reduced-motion is considered, the animation architecture is rigid enough that full removal feels disruptive, so it gets deferred. It never ships.

**How to avoid:**
Build `prefers-reduced-motion` handling into the animation architecture from the start. The pattern is simple — add a single media query block alongside every animation declaration:

```css
@media (prefers-reduced-motion: reduce) {
  .hero-ambient,
  .glow-pulse,
  .link-hover-glow {
    animation: none;
    transition: none;
  }
}
```

Do not use the "nuclear option" of `* { animation: none }` — this can break JavaScript that listens for `animationend` events. Target the specific animation classes. Ambient background effects should collapse to a static state; glow on hover/focus can remain as an instant opacity change rather than a transition.

**Warning signs:**
- Lighthouse accessibility audit flags "2.3.3 Animation from Interactions"
- Any CSS file with `animation:` or `transition:` declarations that lacks a corresponding `@media (prefers-reduced-motion)` block

**Phase to address:** Phase 1 (ARCÆON theme animation system) — implement alongside every animation, not as a final pass.

---

### Pitfall 10: Hugo version pinning omitted from GitHub Actions

**What goes wrong:**
GitHub Actions workflows that install Hugo without pinning a specific version (`uses: peaceiris/actions-hugo@v3` without `hugo-version: '0.x.x'`) will silently upgrade when a new Hugo release publishes. Breaking changes in Hugo's template pipeline, image processing API, or deprecated functions (like `data.GetJSON` removed in 0.140) will cause the build to fail — often weeks or months after initial setup, with no code changes on the developer's end.

**Why it happens:**
Developers use example workflows from tutorials that use `latest` or omit version pinning as a convenience. Hugo has a real history of deprecating functions with removal timelines (e.g., `data.GetJSON` deprecated 0.123, removed 0.140 — 17 minor versions of grace period that still catches people off guard).

**How to avoid:**
Pin a specific Hugo version in the GitHub Actions workflow:
```yaml
- uses: peaceiris/actions-hugo@v3
  with:
    hugo-version: '0.147.0'
    extended: true
```

Also pin the Hugo version in a `.hugo-version` file in the repo root — this is picked up by Netlify automatically and serves as documentation of the intended version. When deliberately upgrading Hugo, update both files together and test locally first.

**Warning signs:**
- Build failure after a period of no code changes
- Error mentions a deprecated or removed function
- No `hugo-version` specified in the Actions workflow file

**Phase to address:** Phase 2 (GitHub Actions pipeline) — pin on first pipeline creation.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Inline styles for one-off adjustments | Fast for single elements | Multiplies, blocks theming, kills dark-mode consistency | Never — use CSS custom properties |
| External font CDN (Google Fonts) instead of self-hosting | Zero setup | Violates performance constraint, privacy CDN dependency, blocks sub-1s 3G load | Never for this project — self-host is a hard requirement |
| `data.GetJSON` for RSS fetch | Familiar API | Deprecated since Hugo 0.123, removed in 0.140 — will break on version upgrade | Never — use `resources.GetRemote` from the start |
| Skipping WOFF2 subsetting | Saves time | Unsubsetted display fonts easily reach 400-800KB, blowing the 3G budget | Never for a display typeface used as a brand element |
| Hardcoding the latest Substack post as static HTML | Eliminates RSS fetch complexity | "Currently" section becomes stale and misleading the moment it ships | Acceptable only as a temporary placeholder before RSS implementation |
| Using `box-shadow` transitions for glow effects | Intuitive implementation | Janky on mobile, paint-heavy, no GPU compositing | Never — use pseudo-element + opacity pattern |
| Single `baseof.html` with all content inline | Simpler initial structure | Blocks component reuse across future Digital Intuition properties, defeats the purpose of `arcaeon` theme | Never — partials from the start |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Substack RSS via `resources.GetRemote` | No error handling — build fails when Substack is unreachable | Wrap in `try`, log warning, render fallback static link |
| Substack RSS via `resources.GetRemote` | Fetching on every build with no cache — slow CI and rate-limit risk | Configure `cacheDir` and `maxAge` in `[caches]` section of `hugo.toml` |
| GitHub Pages custom domain | CNAME only set in GitHub UI, not in `static/CNAME` | Add `static/CNAME` with `falkensmage.com` — survives every deploy |
| GitHub Pages HTTPS | Enforcing HTTPS before DNS propagation completes | Wait for GitHub's DNS check to succeed (can take up to 1 hour after DNS records set) before enabling "Enforce HTTPS" |
| GitHub Pages HTTPS | CAA DNS records that don't include `letsencrypt.org` | Audit DNS CAA records; GitHub Pages uses Let's Encrypt |
| Open Graph / Twitter Card | Relative URL for `og:image` | Use `absURL` in template; verify with Twitter Card Validator before launch |
| Social link icons | Inline SVG without `aria-label` | Every icon-only link needs `aria-label="Platform Name"` to pass WCAG |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Unsubsetted display font | LCP > 2.5s on 3G throttle, CLS from font swap | Subset to Latin character range, use WOFF2, preload primary face | From first load on slow connections |
| Animated `box-shadow` for glow effects | Janky hover/focus on mid-range mobile, paint rectangles in DevTools | Use `::before` pseudo-element + `opacity` transition instead | On any device below flagship-tier GPU |
| Hero image not converted to WebP | Image weight > 200KB for above-fold content | Run through Hugo image pipeline: `.Resize` + `.Format "webp"` with JPEG fallback via `<picture>` | On first real user on a metered connection |
| Multiple Google Font requests | Two extra DNS lookups + TCP connections before render | Self-host — zero external font requests | Consistently — defeats the sub-1s 3G target |
| Ambient animation without GPU compositing | Continuous main-thread work, battery drain on mobile | Animate only `transform` and `opacity` on compositor-promoted layers | On mobile from first visit |
| RSS fetch without cache | Build time increases by 2-5s per fetch; rate limiting risk | Set `maxAge` in Hugo file caches config | In GitHub Actions where network is throttled |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Touch targets smaller than 44px on mobile | Social link grid becomes difficult to tap accurately on 375px viewport | Minimum 44px tap target height and width per WCAG 2.5.5; use padding not font-size to achieve this |
| Ambient animation on hero with no reduced-motion handling | Vestibular disorder symptoms, disorientation | Implement `prefers-reduced-motion: reduce` alongside every animation declaration |
| Glow button with insufficient contrast between text and glow background | "Work With Me" CTA illegible for low-vision users | Check button text contrast independently of the glow treatment; glow is decoration, text contrast is mandatory |
| Horizontal scroll on 375px viewport | Core mobile UX failure — makes the site feel broken | Set `overflow-x: hidden` on `body`, test every section at 375px during development |
| No visible focus indicator for keyboard navigation | Keyboard users cannot determine their position on the page | Use `:focus-visible` with a high-contrast outline — the ARCÆON Ion Glow (`#5be7ff`) outline on dark is strong |
| Placeholder tagline slot left empty at launch | Looks unfinished, undermines the ten-second legibility goal | Ship with a real interim tagline even if not final; an empty slot is worse than an imperfect line |

---

## "Looks Done But Isn't" Checklist

- [ ] **Custom domain:** CNAME file exists at `static/CNAME` (not just in GitHub Pages UI settings) — verify by checking `/public/CNAME` after build
- [ ] **HTTPS:** "Enforce HTTPS" enabled in GitHub Pages settings AND padlock is green in browser (not just DNS check passing)
- [ ] **baseURL:** `hugo.toml` has `baseURL = "https://falkensmage.com/"` — not localhost, not the `.github.io` URL
- [ ] **OG image:** `og:image` content attribute is an absolute URL starting with `https://` — verify with Twitter Card Validator
- [ ] **Font loading:** `font-display: swap` present in every `@font-face` block — grep the CSS output to confirm
- [ ] **Font preload:** `crossorigin` attribute included on font preload link tag — without it, font downloads twice
- [ ] **RSS error handling:** "Currently" section renders a graceful fallback when RSS fetch fails — test by temporarily using an invalid feed URL
- [ ] **Reduced motion:** Every `animation:` and `transition:` declaration has a corresponding `@media (prefers-reduced-motion: reduce)` block
- [ ] **Touch targets:** All social link icons meet 44px minimum tap target — verify in Chrome DevTools device toolbar at 375px
- [ ] **Contrast:** Every text/background color pair verified via WebAIM checker — document the ratios in a comment in the CSS tokens file
- [ ] **Hugo version pinned:** `hugo-version` specified in Actions workflow — not `latest`
- [ ] **WebP fallback:** Hero image served via `<picture>` with WebP source and JPEG fallback `<img>` — verify in Safari (which handles WebP but the fallback path must be valid)
- [ ] **Aria labels:** Every icon-only social link has `aria-label` — run `axe` or Lighthouse accessibility audit to catch omissions

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| baseURL wrong on live site | LOW | Fix `hugo.toml`, redeploy — 15 minute fix |
| CNAME overwritten, domain broken | LOW | Add `static/CNAME`, redeploy; wait up to 1 hour for HTTPS cert re-provisioning |
| GITHUB_TOKEN permissions | LOW | Add `permissions` block to workflow, re-run failed action |
| Hugo version upgrade breaks build | MEDIUM | Pin version in workflow, fix deprecated function calls (e.g., replace `data.GetJSON` with `resources.GetRemote`) — 1-4 hours depending on how many callsites |
| Neon palette fails WCAG across the site | HIGH | Requires a color audit and systematic replacement of text color tokens — retrofitting accessibility into an existing design is significantly harder than designing with validated pairs from the start |
| Animated box-shadow across all interactive elements | MEDIUM | Replace box-shadow transitions with pseudo-element + opacity pattern site-wide — requires touching every interactive component |
| Self-hosted font at wrong size blows load budget | MEDIUM | Re-subset with stricter character range or switch typeface; retest against 3G budget |
| RSS fetch breaks build in production | LOW | Implement error handling + fallback; if already handled, the build continues gracefully |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| baseURL mismatch | Phase 1 (Foundation) | Check generated link hrefs in `/public` before first deploy |
| CNAME overwritten | Phase 2 (CI/CD pipeline) | Confirm `static/CNAME` exists; check `/public/CNAME` after build |
| GITHUB_TOKEN permissions | Phase 2 (CI/CD pipeline) | Workflow runs end-to-end without permission errors |
| Neon colors fail WCAG AA | Phase 1 (ARCÆON token system) | WebAIM contrast checker — document ratios in CSS comments |
| RSS fetch build failure | Phase 3 (Currently section) | Test with invalid URL, confirm graceful fallback renders |
| box-shadow animation performance | Phase 1 (Component animation system) | Chrome DevTools Performance panel — no paint rectangles on hover |
| Font loading / FOIT | Phase 1 (Typography) | Lighthouse LCP score, Network tab shows font downloaded once |
| OG image relative URL | Phase 4 (SEO / meta) | Twitter Card Validator shows absolute URL with preview image |
| prefers-reduced-motion missing | Phase 1 (Animation system) | Lighthouse accessibility audit; toggle OS reduced-motion setting |
| Hugo version unpinned | Phase 2 (CI/CD pipeline) | `hugo-version` present in workflow YAML |
| Horizontal scroll at 375px | Phase 1 (Mobile-first foundation) | Chrome DevTools device toolbar — 375px shows no horizontal scroll |
| Icon-only links missing aria-labels | Phase 1 (Social links component) | axe DevTools or Lighthouse accessibility audit |

---

## Sources

- Hugo official docs — `resources.GetRemote`: https://gohugo.io/functions/resources/getremote/
- Hugo discourse — baseURL and GitHub Pages 404s: https://discourse.gohugo.io/t/problem-with-deploying-hugo-site-to-github-pages-404-after-deployment/54301
- Hugo `data.GetJSON` deprecation (removed 0.140): https://andreas.scherbaum.la/post/2025-03-20_error-deprecated-data-getjson-was-deprecated-in-hugo-v0-123-0-and-will-be-removed-in-hugo-0-140-0-use-resources-get-or-resources-getremote-with-transform-unmarshal/
- GitHub Pages troubleshooting — custom domains and HTTPS: https://docs.github.com/en/pages/configuring-a-custom-domain-for-your-github-pages-site/troubleshooting-custom-domains-and-github-pages
- GitHub Pages deploying with Actions — peaceiris/actions-gh-pages: https://github.com/peaceiris/actions-gh-pages
- WCAG 1.4.3 Contrast (Minimum): https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- WebAIM — Contrast and Color Accessibility (dark mode WCAG limitations): https://webaim.org/articles/contrast/
- WCAG 2.3.3 Animation from Interactions: https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html
- CSS prefers-reduced-motion — MDN: https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@media/prefers-reduced-motion
- Web Animation Performance Tier List (GPU compositing): https://motion.dev/magazine/web-animation-performance-tier-list
- CSS GPU Animation — Smashing Magazine: https://www.smashingmagazine.com/2016/12/gpu-animation-doing-it-right/
- Font loading strategies (font-display, preloading, WOFF2): https://font-converters.com/guides/font-loading-strategies
- Hugo self-hosted Google Fonts: https://rednafi.com/misc/self-hosted-google-fonts-in-hugo/
- Hugo — Paul Charlesworth on fonts and Lighthouse: https://paulcharlesworth.net/web-fonts/
- Hugo image optimization render hook: https://runtimeterror.dev/hugo-image-optimization-render-hook/
- Substack RSS into Hugo static site: https://www.ibrahimsowunmi.com/posts/2023/12/how-to-embed-a-rss-substack-feed-into-your-hugo-static-site/

---
*Pitfalls research for: Hugo single-page personal brand site — falkensmage.com*
*Researched: 2026-04-16*
