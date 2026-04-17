---
phase: quick
plan: 260416-rkc
type: execute
wave: 1
depends_on: []
files_modified:
  - themes/arcaeon/layouts/partials/sections/identity-cta.html
  - themes/arcaeon/layouts/partials/sections/social.html
  - themes/arcaeon/layouts/partials/sections/footer.html
  - themes/arcaeon/layouts/_default/baseof.html
  - themes/arcaeon/assets/css/main.css
autonomous: true
requirements: []
must_haves:
  truths:
    - "Section triad alternates void-depth-void-depth-void from hero through footer"
    - "OG image dimensions derive from the actual generated image, not hardcoded strings"
    - "Currently card is visually compact on desktop, not spanning full content width"
  artifacts:
    - path: "themes/arcaeon/layouts/partials/sections/identity-cta.html"
      provides: "section-void class (swapped from section-depth)"
      contains: "section-void"
    - path: "themes/arcaeon/layouts/partials/sections/social.html"
      provides: "section-depth class (swapped from section-void)"
      contains: "section-depth"
    - path: "themes/arcaeon/layouts/partials/sections/footer.html"
      provides: "section-void class (swapped from section-depth)"
      contains: "section-void"
    - path: "themes/arcaeon/layouts/_default/baseof.html"
      provides: "Dynamic OG image dimensions"
      contains: "$ogImg.Width"
    - path: "themes/arcaeon/assets/css/main.css"
      provides: "Currently card max-width constraint"
      contains: "max-width"
  key_links:
    - from: "identity-cta.html"
      to: "main.css"
      via: "section-void class styling"
      pattern: "section-void"
    - from: "social.html"
      to: "main.css"
      via: "section-depth class styling"
      pattern: "section-depth"
---

<objective>
Fix three UI review issues identified in 03-UI-REVIEW.md that dropped the Visuals and Color pillar scores from 4/4 to 3/4.

Purpose: Restore the void-depth alternation pattern, make OG image dimensions resilient to source changes, and constrain the Currently card to compact proportions on desktop.
Output: All three fixes applied, hugo build clean, triad alternation correct in rendered output.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@.planning/phases/03-dynamic-layer-quality/03-UI-REVIEW.md

<interfaces>
<!-- Current section class assignments (WRONG - two consecutive depth sections): -->
<!-- hero.html:         section-void   (correct, stays) -->
<!-- currently.html:    section-depth  (correct, stays) -->
<!-- identity-cta.html: section-depth  (WRONG -> section-void) -->
<!-- social.html:       section-void   (WRONG -> section-depth) -->
<!-- footer.html:       section-depth  (WRONG -> section-void) -->

From themes/arcaeon/layouts/partials/sections/identity-cta.html line 2:
```html
<section class="section section-depth identity-cta-section">
```

From themes/arcaeon/layouts/partials/sections/social.html line 2:
```html
<section class="section section-void social-section sigil-arc sigil-boundary-tr">
```

From themes/arcaeon/layouts/partials/sections/footer.html line 2:
```html
<footer class="section section-depth footer-section sigil-arc-sm sigil-boundary-bl">
```

From themes/arcaeon/layouts/_default/baseof.html lines 30-31:
```html
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
```

From themes/arcaeon/assets/css/main.css lines 687-692:
```css
.currently-card {
  border: 1px solid rgba(122, 44, 255, 0.35);
  border-radius: 8px;
  padding: 1rem;
  transition: border-color 0.25s ease;
}
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix section triad alternation and OG image dimensions</name>
  <files>
    themes/arcaeon/layouts/partials/sections/identity-cta.html,
    themes/arcaeon/layouts/partials/sections/social.html,
    themes/arcaeon/layouts/partials/sections/footer.html,
    themes/arcaeon/layouts/_default/baseof.html
  </files>
  <action>
    Three edits to restore D-05 triad (void-depth-void-depth-void):

    1. identity-cta.html line 2: Change `section-depth` to `section-void`.
       Result: `<section class="section section-void identity-cta-section">`

    2. social.html line 2: Change `section-void` to `section-depth`.
       Result: `<section class="section section-depth social-section sigil-arc sigil-boundary-tr">`

    3. footer.html line 2: Change `section-depth` to `section-void`.
       Result: `<footer class="section section-void footer-section sigil-arc-sm sigil-boundary-bl">`

    One edit for OG image dimensions:

    4. baseof.html lines 30-31: Replace hardcoded dimension strings with Hugo template vars.
       Change: `content="1200"` to `content="{{ $ogImg.Width }}"`
       Change: `content="630"` to `content="{{ $ogImg.Height }}"`
  </action>
  <verify>
    <automated>cd /Users/falkensmage/RitualSync/falkensmage-website && hugo --quiet 2>&1 && grep -c 'section-void.*identity-cta' public/index.html && grep -c 'section-depth.*social-section' public/index.html && grep -c 'section-void.*footer-section' public/index.html && grep -o 'og:image:width" content="[0-9]*"' public/index.html</automated>
  </verify>
  <done>
    - identity-cta renders with section-void class
    - social renders with section-depth class
    - footer renders with section-void class
    - Triad in rendered HTML: void (hero), depth (currently), void (identity-cta), depth (social), void (footer)
    - OG image width/height tags contain numeric values derived from Hugo image processing, not hardcoded strings
  </done>
</task>

<task type="auto">
  <name>Task 2: Constrain Currently card max-width on desktop</name>
  <files>themes/arcaeon/assets/css/main.css</files>
  <action>
    Add `max-width: 32rem` and `margin-inline: auto` to the `.currently-card` rule block (lines 687-692 of main.css).

    The rule should become:
    ```css
    .currently-card {
      max-width: 32rem;
      margin-inline: auto;
      border: 1px solid rgba(122, 44, 255, 0.35);
      border-radius: 8px;
      padding: 1rem;
      transition: border-color 0.25s ease;
    }
    ```

    `margin-inline: auto` centers the card within the 56rem section-content container. On mobile (375px), 32rem (512px) exceeds viewport so the card naturally fills available width — no media query needed.
  </action>
  <verify>
    <automated>cd /Users/falkensmage/RitualSync/falkensmage-website && hugo --quiet 2>&1 && grep -A2 'max-width' themes/arcaeon/assets/css/main.css | head -5</automated>
  </verify>
  <done>
    - .currently-card has max-width: 32rem
    - .currently-card is centered via margin-inline: auto
    - Hugo build succeeds with no warnings
    - Card appears compact and centered on desktop viewports
  </done>
</task>

</tasks>

<verification>
Run full build and validate all three fixes in rendered output:

```bash
cd /Users/falkensmage/RitualSync/falkensmage-website
hugo --quiet
# Triad check: extract section classes in order from rendered HTML
grep -oE 'section-(void|depth)' public/index.html | head -5
# Expected: void, depth, void, depth, void
# OG dimensions check
grep 'og:image:' public/index.html
# Expected: width and height with numeric content values (1200, 630)
```
</verification>

<success_criteria>
- Hugo builds cleanly with zero errors
- Section triad in rendered HTML follows void-depth-void-depth-void pattern
- No two consecutive sections share the same depth class
- OG image dimensions are template-derived, not string literals in source
- Currently card constrained to 32rem max-width, centered in its section
</success_criteria>

<output>
After completion, create `.planning/quick/260416-rkc-fix-3-ui-review-issues-from-phase-03/260416-rkc-SUMMARY.md`
</output>
