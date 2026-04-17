---
phase: 04-production-deploy
reviewed: 2026-04-17T00:00:00Z
depth: standard
files_reviewed: 23
files_reviewed_list:
  - .github/workflows/hugo.yml
  - content/_index.md
  - content/kitchen-sink.md
  - scripts/png-to-ico.py
  - static/CNAME
  - static/favicon.ico
  - static/favicon.svg
  - themes/arcaeon/assets/css/main.css
  - themes/arcaeon/layouts/_default/baseof.html
  - themes/arcaeon/layouts/index.html
  - themes/arcaeon/layouts/kitchen-sink/single.html
  - themes/arcaeon/layouts/partials/icons/bluesky.html
  - themes/arcaeon/layouts/partials/icons/instagram.html
  - themes/arcaeon/layouts/partials/icons/linkedin.html
  - themes/arcaeon/layouts/partials/icons/spotify.html
  - themes/arcaeon/layouts/partials/icons/substack.html
  - themes/arcaeon/layouts/partials/icons/tarotpulse.html
  - themes/arcaeon/layouts/partials/icons/threads.html
  - themes/arcaeon/layouts/partials/icons/x.html
  - themes/arcaeon/layouts/partials/sections/currently.html
  - themes/arcaeon/layouts/partials/sections/footer.html
  - themes/arcaeon/layouts/partials/sections/hero.html
  - themes/arcaeon/layouts/partials/sections/identity-cta.html
  - themes/arcaeon/layouts/partials/sections/social.html
findings:
  critical: 0
  warning: 4
  info: 4
  total: 8
status: issues_found
---

# Phase 04: Code Review Report

**Reviewed:** 2026-04-17
**Depth:** standard
**Files Reviewed:** 23
**Status:** issues_found

## Summary

Reviewed all Phase 04 production-deploy source files: GitHub Actions workflow, Hugo templates, CSS, content, icons, and the favicon generation script. The codebase is generally solid — the Hugo pipeline is well-structured, the CSS design system is internally consistent, and the accessibility patterns (aria labels, prefers-reduced-motion, rel="noopener noreferrer") are correctly applied throughout.

Four warnings and four info items. No critical issues. The warnings are all real bugs that will produce incorrect behavior at runtime: a wrong RSS feed URL, a hardcoded canonical URL that will be wrong for any non-production build, a missing image fallback that silently renders no hero section, and a Python script that will crash on no-argument invocation with an unhelpful error. The info items are minor quality concerns that won't cause bugs.

---

## Warnings

### WR-01: Wrong RSS feed URL — 404 at build time

**File:** `themes/arcaeon/layouts/partials/sections/currently.html:2`
**Issue:** The RSS URL is set to `https://feralarchitecture.com/feed` but the site is hosted at Substack (`https://feralarchitecture.substack.com`). The correct Substack RSS endpoint is `https://feralarchitecture.substack.com/feed`. The current URL will 404 on every build, triggering the `warnf` fallback path and silently rendering the fallback link instead of the latest post. The `try` wrapper suppresses the build failure, so this will never surface as a hard error — it just silently doesn't work.
**Fix:**
```html
{{ $rssURL := "https://feralarchitecture.substack.com/feed" }}
```

### WR-02: Hardcoded canonical URL breaks staging and preview builds

**File:** `themes/arcaeon/layouts/_default/baseof.html:41`
**Issue:** `<link rel="canonical" href="https://falkensmage.com">` is hardcoded as a static string. This emits the production URL on every build regardless of environment, including local dev and any branch preview deployments. Search engines indexing a preview URL will see a canonical pointing to production, which is correct intent but the implementation bypasses Hugo's built-in URL resolution. More importantly, the OG `og:url` on line 23 has the same issue. Both should use Hugo's `.Permalink` or `site.BaseURL` so they resolve correctly in all environments.
**Fix:**
```html
{{/* Line 23 */}}
<meta property="og:url" content="{{ .Permalink }}">

{{/* Line 41 */}}
<link rel="canonical" href="{{ .Permalink }}">
```

### WR-03: Hero section silently renders nothing if image asset is missing

**File:** `themes/arcaeon/layouts/partials/sections/hero.html:2-28`
**Issue:** The entire `<section>` is wrapped inside `{{ with $img }}...{{ end }}`. If `themes/arcaeon/assets/images/magus-hero.jpg` is absent (not committed, wrong filename, path mismatch), Hugo silently emits an empty `<header>` element in the page. The visitor sees no hero — no image, no site name, no tagline — with no error logged at build time unless `--verbose` is set. For a single-page site whose value proposition is immediate identity legibility, silent hero erasure is a significant regression risk.
**Fix:** Add a fallback or a build-time assertion:
```html
{{ $img := resources.Get "images/magus-hero.jpg" }}
{{ if not $img }}
  {{ errorf "Hero image missing: themes/arcaeon/assets/images/magus-hero.jpg" }}
{{ end }}
{{ with $img }}
  ...
{{ end }}
```
Using `errorf` instead of `warnf` makes a missing hero a hard build failure rather than a silent omission.

### WR-04: png-to-ico.py crashes with unhelpful error on bad invocation

**File:** `scripts/png-to-ico.py:35`
**Issue:** `*inputs, output = sys.argv[1:]` raises `ValueError: not enough values to unpack` with no message when the script is called with zero or one argument. A first-time runner gets a Python traceback with no guidance. Additionally, the script reads the entire PNG into memory at `data = f.read()` (line 12) before validating it's actually a PNG — a non-PNG file passed as input will silently produce a corrupt ICO with wrong dimensions parsed from non-PNG bytes at offset 16-24 (the PNG IHDR width/height fields).
**Fix:**
```python
if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/png-to-ico.py input16.png input32.png output.ico", file=sys.stderr)
        sys.exit(1)
    *inputs, output = sys.argv[1:]
    # Validate PNG signature before processing
    for path in inputs:
        with open(path, 'rb') as f:
            sig = f.read(8)
        if sig != b'\x89PNG\r\n\x1a\n':
            print(f"Error: {path} is not a valid PNG file", file=sys.stderr)
            sys.exit(1)
    create_ico(inputs, output)
    print(f'Created {output}')
```

---

## Info

### IN-01: OG and Twitter meta description diverges from page `<meta name="description">`

**File:** `themes/arcaeon/layouts/_default/baseof.html:7,22,37`
**Issue:** All three description strings are duplicated as hardcoded literals. If the description is updated in one place, it's easy to miss the others. Not a bug, but a maintenance trap — three strings that must stay in sync manually.
**Fix:** Define once in `hugo.toml` as `params.description` and reference via `site.Params.description`:
```html
<meta name="description" content="{{ site.Params.description }}">
<meta property="og:description" content="{{ site.Params.description }}">
<meta name="twitter:description" content="{{ site.Params.description }}">
```

### IN-02: `actions/configure-pages` pinned to v6, other actions to v3/v4/v5

**File:** `.github/workflows/hugo.yml:46`
**Issue:** `actions/configure-pages@v6` is ahead of the official Hugo starter workflow pattern (which uses v4 as of this review). `actions/upload-pages-artifact@v3` and `actions/deploy-pages@v5` are mixed versions. This is not broken, but the mismatched pinning suggests manual version bumping without cross-checking compatibility. Worth auditing that these versions are actually stable releases, not pre-release or deprecated tags.
**Fix:** Verify each action version against its GitHub releases page. If v6 of `configure-pages` is stable and compatible, document the explicit version choices in a comment. If it's a typo, revert to v4.

### IN-03: `identity-cta.html` passes raw content block strings through `safeHTML` without sanitization

**File:** `themes/arcaeon/layouts/partials/sections/identity-cta.html:5`
**Issue:** `{{ . | safeHTML }}` marks the identity block content as trusted HTML. This is appropriate for the current content (which includes a single intentional `<em>` tag in the last identity block). It is worth noting that `safeHTML` suppresses Hugo's default HTML escaping — if this content ever comes from a less-controlled source or is edited carelessly, it becomes an unescaped output vector. For a site where the content author is also the template author this is low risk, but the pattern is worth naming.
**Fix:** No change required now. If the content source widens in the future, replace `safeHTML` with explicit whitelisted-element rendering.

### IN-04: Kitchen sink page marked `draft: true` — confirm it's excluded from production build

**File:** `content/kitchen-sink.md:4`
**Issue:** `draft: true` correctly excludes the page from production builds unless `--buildDrafts` is passed. The CI workflow does not pass `--buildDrafts`, so this is working as intended. Worth a one-time confirmation that `hugo --minify` in the Actions step does not emit the kitchen sink, since the page contains no sensitive data but does expose internal design system details that may not be intended for public consumption.
**Fix:** No change required. Confirm with `hugo list drafts` locally to verify the kitchen sink is draft-gated.

---

_Reviewed: 2026-04-17_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
