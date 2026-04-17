#!/usr/bin/env bash
# validate-phase-03.sh
# Automated validation for Phase 3 — Dynamic Layer + Quality
# Run from project root: bash tests/validate-phase-03.sh
# Exit 0 = all checks pass. Exit 1 = one or more checks failed.

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

BUILD_DIR="$PROJECT_ROOT/public"
INDEX="$BUILD_DIR/index.html"
CSS="$PROJECT_ROOT/themes/arcaeon/assets/css/main.css"
CURRENTLY_PARTIAL="$PROJECT_ROOT/themes/arcaeon/layouts/partials/sections/currently.html"
BASEOF="$PROJECT_ROOT/themes/arcaeon/layouts/_default/baseof.html"
INDEX_LAYOUT="$PROJECT_ROOT/themes/arcaeon/layouts/index.html"
CONTENT="_index.md"
CONTENT_PATH="$PROJECT_ROOT/content/_index.md"

check() {
  local label="$1"
  local result="$2"
  if [ "$result" -gt 0 ]; then
    echo "  PASS: $label"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: $label"
    FAIL=$((FAIL + 1))
  fi
}

echo "=== Phase 3 Validation: Dynamic Layer + Quality ==="
echo ""

# Build first — abort if fails
echo "Building site..."
cd "$PROJECT_ROOT"
if ! hugo --quiet 2>&1; then
  echo "FATAL: Hugo build failed. Aborting validation."
  exit 1
fi
echo ""

# --- CURR-01: Currently section with RSS content ---
echo "--- CURR-01: Currently section present ---"
check "currently-card class in HTML" "$(grep -c 'currently-card' "$INDEX")"
check "resources.GetRemote in partial" "$(grep -c 'resources.GetRemote' "$CURRENTLY_PARTIAL")"
check "feralarchitecture.com/feed URL" "$(grep -c 'feralarchitecture.com/feed' "$CURRENTLY_PARTIAL")"
echo ""

# --- CURR-02: current focus from front matter ---
echo "--- CURR-02: Current focus blurb ---"
check "currently_focus in _index.md" "$(grep -c 'currently_focus' "$CONTENT_PATH")"
check "Params.currently_focus in partial" "$(grep -c 'currently_focus' "$CURRENTLY_PARTIAL")"
echo ""

# --- CURR-03: Graceful fallback ---
echo "--- CURR-03: RSS fallback ---"
check "try wrapping in partial" "$(grep -c 'try' "$CURRENTLY_PARTIAL")"
check "warnf error logging" "$(grep -c 'warnf' "$CURRENTLY_PARTIAL")"
check "fallback link to feral architecture" "$(grep -c 'feralarchitecture.com' "$CURRENTLY_PARTIAL")"
echo ""

# --- PERF-01: No external CDN calls ---
echo "--- PERF-01: No external dependencies ---"
EXTERNAL_CDNS=$(grep -ciE '(googleapis\.com|cdn\.|cloudflare|unpkg|jsdelivr|analytics|gtag)' "$INDEX" || true)
if [ "$EXTERNAL_CDNS" -eq 0 ]; then
  echo "  PASS: No external CDN calls in HTML"
  PASS=$((PASS + 1))
else
  echo "  FAIL: Found $EXTERNAL_CDNS external CDN references"
  FAIL=$((FAIL + 1))
fi
echo ""

# --- PERF-02: Hero image WebP + picture element + eager loading ---
echo "--- PERF-02: Hero image optimization ---"
check "<picture> element present" "$(grep -c '<picture>' "$INDEX")"
check "WebP source present" "$(grep -c 'image/webp' "$INDEX")"
check "loading=eager on hero" "$(grep -c 'loading="eager"' "$INDEX")"
echo ""

# --- PERF-03: Font preload with crossorigin ---
echo "--- PERF-03: Font preloading ---"
check "preload for cinzel" "$(grep -c 'preload.*cinzel' "$INDEX")"
check "preload for space-grotesk" "$(grep -c 'preload.*space-grotesk' "$INDEX")"
check "crossorigin on preloads" "$(grep -c 'crossorigin' "$BASEOF")"
echo ""

# --- PERF-04: No external font CDNs or analytics ---
echo "--- PERF-04: No external font/analytics ---"
GOOGLE_FONTS=$(grep -ci 'fonts.googleapis.com' "$INDEX" || true)
if [ "$GOOGLE_FONTS" -eq 0 ]; then
  echo "  PASS: No Google Fonts CDN"
  PASS=$((PASS + 1))
else
  echo "  FAIL: Google Fonts CDN found"
  FAIL=$((FAIL + 1))
fi
echo ""

# --- A11Y-01: Semantic landmarks ---
echo "--- A11Y-01: Semantic HTML5 landmarks ---"
check "<header> element" "$(grep -c '<header>' "$INDEX")"
check "<main> element" "$(grep -c '<main>' "$INDEX")"
check "<footer> element (landmark)" "$(grep -c '</footer>' "$INDEX")"
HERO_IN_HEADER=$(grep -c 'header' "$INDEX_LAYOUT" || true)
check "hero wrapped in header (layout)" "$HERO_IN_HEADER"
echo ""

# --- A11Y-02: Contrast conventions ---
echo "--- A11Y-02: Color contrast conventions ---"
check "Electric Violet decoration-only warning in CSS" "$(grep -c 'NEVER body text' "$CSS")"
check "body text uses --color-text" "$(grep -c 'color: var(--color-text)' "$CSS")"
echo ""

# --- A11Y-03: Alt text on hero image ---
echo "--- A11Y-03: Hero image alt text ---"
check "alt text present and non-empty" "$(grep -c 'alt="Matt Stine as the Magus' "$INDEX")"
echo ""

# --- A11Y-04: prefers-reduced-motion ---
echo "--- A11Y-04: Motion suppression ---"
MOTION_COUNT=$(grep -c 'prefers-reduced-motion' "$CSS")
if [ "$MOTION_COUNT" -ge 5 ]; then
  echo "  PASS: prefers-reduced-motion count >= 5 ($MOTION_COUNT found)"
  PASS=$((PASS + 1))
else
  echo "  FAIL: prefers-reduced-motion count < 5 ($MOTION_COUNT found, need >= 5)"
  FAIL=$((FAIL + 1))
fi
echo ""

# --- SEO-01: Open Graph tags ---
echo "--- SEO-01: Open Graph ---"
check "og:title present" "$(grep -c 'og:title' "$INDEX")"
check "og:image present" "$(grep -c 'og:image' "$INDEX")"
check "og:description present" "$(grep -c 'og:description' "$INDEX")"
check "og:url present" "$(grep -c 'og:url' "$INDEX")"
echo ""

# --- SEO-02: Twitter Card ---
echo "--- SEO-02: Twitter Card ---"
check "twitter:card present" "$(grep -c 'twitter:card' "$INDEX")"
check "summary_large_image type" "$(grep -c 'summary_large_image' "$INDEX")"
check "twitter:image present" "$(grep -c 'twitter:image' "$INDEX")"
echo ""

# --- SEO-03: Canonical URL ---
echo "--- SEO-03: Canonical URL ---"
check 'canonical URL present' "$(grep -c 'rel="canonical"' "$INDEX")"
check 'canonical points to falkensmage.com' "$(grep -cE 'href="https://falkensmage\.com/?"' "$INDEX")"
echo ""

# --- Phase 5 gap closure: A11Y-01 nested-footer guard ---
echo "--- A11Y-01 (Phase 5): Exactly one footer landmark ---"
FOOTER_OPEN=$(grep -cE '<footer[ >]' "$INDEX" || true)
if [ "$FOOTER_OPEN" -eq 1 ]; then
  echo "  PASS: exactly one <footer> opening tag in built HTML"
  PASS=$((PASS + 1))
else
  echo "  FAIL: expected 1 <footer> opening tag, found $FOOTER_OPEN"
  FAIL=$((FAIL + 1))
fi
echo ""

# --- Phase 5 gap closure: PERF-03 preload href === @font-face url for both fonts ---
echo "--- PERF-03 (Phase 5): Preload href matches @font-face url ---"
CSS_BUILD=$(ls "$BUILD_DIR"/css/main.min.*.css 2>/dev/null | head -1)
if [ -z "$CSS_BUILD" ]; then
  echo "  FAIL: no built CSS found in public/css/"
  FAIL=$((FAIL + 1))
else
  CINZEL_PRELOAD=$(grep -oE '/fonts/cinzel-[^"]*\.woff2' "$INDEX" | head -1 || true)
  CINZEL_URL=$(grep -oE '/fonts/cinzel-[^)]*\.woff2' "$CSS_BUILD" | head -1 || true)
  if [ -n "$CINZEL_PRELOAD" ] && [ "$CINZEL_PRELOAD" = "$CINZEL_URL" ]; then
    echo "  PASS: Cinzel preload href ($CINZEL_PRELOAD) matches @font-face url"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: Cinzel preload='$CINZEL_PRELOAD' vs url='$CINZEL_URL'"
    FAIL=$((FAIL + 1))
  fi
  SG_PRELOAD=$(grep -oE '/fonts/space-grotesk-[^"]*\.woff2' "$INDEX" | head -1 || true)
  SG_URL=$(grep -oE '/fonts/space-grotesk-[^)]*\.woff2' "$CSS_BUILD" | head -1 || true)
  if [ -n "$SG_PRELOAD" ] && [ "$SG_PRELOAD" = "$SG_URL" ]; then
    echo "  PASS: Space Grotesk preload href ($SG_PRELOAD) matches @font-face url"
    PASS=$((PASS + 1))
  else
    echo "  FAIL: Space Grotesk preload='$SG_PRELOAD' vs url='$SG_URL'"
    FAIL=$((FAIL + 1))
  fi
fi
echo ""

# --- Phase 5 gap closure: No .woff2 duplicated into public/css/ ---
echo "--- PERF-03 (Phase 5): Fonts not duplicated into public/css/ ---"
CSS_WOFF2_COUNT=$(ls "$BUILD_DIR"/css/*.woff2 2>/dev/null | wc -l | tr -d ' ')
if [ "$CSS_WOFF2_COUNT" -eq 0 ]; then
  echo "  PASS: public/css/ contains zero .woff2 files"
  PASS=$((PASS + 1))
else
  echo "  FAIL: public/css/ contains $CSS_WOFF2_COUNT .woff2 file(s) -- esbuild copied fonts"
  FAIL=$((FAIL + 1))
fi
echo ""

# --- Phase 5 gap closure: npm ci absent from CI workflow ---
echo "--- Tech debt (Phase 5): npm ci removed from workflow ---"
WORKFLOW="$PROJECT_ROOT/.github/workflows/hugo.yml"
NPM_CI_COUNT=$(grep -c 'npm ci' "$WORKFLOW" || true)
if [ "$NPM_CI_COUNT" -eq 0 ]; then
  echo "  PASS: no 'npm ci' in .github/workflows/hugo.yml"
  PASS=$((PASS + 1))
else
  echo "  FAIL: 'npm ci' still present in workflow ($NPM_CI_COUNT occurrence(s))"
  FAIL=$((FAIL + 1))
fi
echo ""

# --- Phase 5 gap closure: SUMMARY frontmatter backfill present ---
echo "--- Tech debt (Phase 5): requirements-completed in all target SUMMARYs ---"
BACKFILL_COUNT=0
for SUMMARY in \
  "$PROJECT_ROOT/.planning/phases/01-theme-foundation/01-02-SUMMARY.md" \
  "$PROJECT_ROOT/.planning/phases/01-theme-foundation/01-03-SUMMARY.md" \
  "$PROJECT_ROOT/.planning/phases/03-dynamic-layer-quality/03-01-SUMMARY.md" \
  "$PROJECT_ROOT/.planning/phases/03-dynamic-layer-quality/03-02-SUMMARY.md"; do
  if grep -q '^requirements-completed:' "$SUMMARY" 2>/dev/null; then
    BACKFILL_COUNT=$((BACKFILL_COUNT + 1))
  fi
done
if [ "$BACKFILL_COUNT" -eq 4 ]; then
  echo "  PASS: requirements-completed present in all 4 target SUMMARY files"
  PASS=$((PASS + 1))
else
  echo "  FAIL: requirements-completed present in only $BACKFILL_COUNT of 4 target SUMMARY files"
  FAIL=$((FAIL + 1))
fi
echo ""

echo "=== Results: $PASS passed, $FAIL failed ==="
if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
echo "All Phase 3 checks passed."
