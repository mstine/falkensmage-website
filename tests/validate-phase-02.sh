#!/usr/bin/env bash
# validate-phase-02.sh
# Automated validation for Phase 2 — Static Content
# Run from project root: bash tests/validate-phase-02.sh
# Exit 0 = all checks pass. Exit 1 = one or more checks failed.

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL + 1)); }

# html_has PATTERN FILE — extended regex search against HTML
html_has() { grep -qE "$1" "$2"; }

# html_has_fixed STRING FILE — fixed-string search against HTML
html_has_fixed() { grep -qF -e "$1" "$2"; }

# css_has VAR FILE — fixed-string search safe against leading-dash patterns
css_has() { grep -qF -e "$1" "$2"; }

echo ""
echo "Phase 2 — Static Content Validation"
echo "====================================="
echo "Project root: $PROJECT_ROOT"
echo ""

# ── Hugo Build ────────────────────────────────────────────────────────────────
# Hugo build exits 0

echo "[ Build ] Hugo build exits 0"
cd "$PROJECT_ROOT"
if hugo --minify --quiet > /dev/null 2>&1; then
  pass "hugo --minify exits with code 0"
else
  fail "hugo --minify failed (non-zero exit)"
  echo ""
  echo "FATAL: Hugo build failed — aborting remaining checks"
  exit 1
fi
echo ""

HTML="$PROJECT_ROOT/public/index.html"
CSS="$PROJECT_ROOT/themes/arcaeon/assets/css/main.css"
CONTENT="$PROJECT_ROOT/content/_index.md"

# ── HERO-01 ───────────────────────────────────────────────────────────────────
# Hero image with <picture> element present

echo "[ HERO-01 ] Hero image — <picture> element present"
if html_has_fixed "<picture>" "$HTML" || html_has_fixed "<picture " "$HTML" || html_has "<picture" "$HTML"; then
  pass "HERO-01: <picture> element present in built HTML"
else
  fail "HERO-01: <picture> element MISSING from built HTML"
fi
echo ""

# ── HERO-02 ───────────────────────────────────────────────────────────────────
# display-text class present (Falken's Mage logotype treatment)

echo "[ HERO-02 ] Hero logotype — display-text class present"
if html_has_fixed "display-text" "$HTML"; then
  pass "HERO-02: display-text class present in built HTML"
else
  fail "HERO-02: display-text class MISSING from built HTML"
fi
echo ""

# ── HERO-03 ───────────────────────────────────────────────────────────────────
# hero-tagline class present

echo "[ HERO-03 ] Hero tagline — hero-tagline class present"
if html_has_fixed "hero-tagline" "$HTML"; then
  pass "HERO-03: hero-tagline class present in built HTML"
else
  fail "HERO-03: hero-tagline class MISSING from built HTML"
fi
echo ""

# ── HERO-04 ───────────────────────────────────────────────────────────────────
# glow-ambient class present (ambient animation on hero image wrapper)

echo "[ HERO-04 ] Hero ambient glow — glow-ambient class present"
if html_has_fixed "glow-ambient" "$HTML"; then
  pass "HERO-04: glow-ambient class present in built HTML"
else
  fail "HERO-04: glow-ambient class MISSING from built HTML"
fi
echo ""

# ── IDENT-01 ──────────────────────────────────────────────────────────────────
# identity-statement class present

echo "[ IDENT-01 ] Identity statement — identity-statement class present"
if html_has_fixed "identity-statement" "$HTML"; then
  pass "IDENT-01: identity-statement class present in built HTML"
else
  fail "IDENT-01: identity-statement class MISSING from built HTML"
fi
echo ""

# ── IDENT-02 ──────────────────────────────────────────────────────────────────
# identity_blocks: key present in content/_index.md front matter
# (Implementation evolved from single identity_statement string to identity_blocks array)

echo "[ IDENT-02 ] Identity statement — identity_blocks: key in front matter"
if html_has_fixed "identity_blocks:" "$CONTENT"; then
  pass "IDENT-02: identity_blocks: key present in content/_index.md"
else
  fail "IDENT-02: identity_blocks: key MISSING from content/_index.md"
fi
echo ""

# ── SOCIAL-01 ─────────────────────────────────────────────────────────────────
# social-grid class present

echo "[ SOCIAL-01 ] Social links grid — social-grid class present"
if html_has_fixed "social-grid" "$HTML"; then
  pass "SOCIAL-01: social-grid class present in built HTML"
else
  fail "SOCIAL-01: social-grid class MISSING from built HTML"
fi
echo ""

# ── SOCIAL-02 ─────────────────────────────────────────────────────────────────
# glow-interactive class present (hover glow on social cards)

echo "[ SOCIAL-02 ] Social card hover glow — glow-interactive class present"
if html_has_fixed "glow-interactive" "$HTML"; then
  pass "SOCIAL-02: glow-interactive class present in built HTML"
else
  fail "SOCIAL-02: glow-interactive class MISSING from built HTML"
fi
echo ""

# ── SOCIAL-03 ─────────────────────────────────────────────────────────────────
# min-height: 44px present in .social-card rule (touch target sizing)

echo "[ SOCIAL-03 ] Touch targets — min-height: 44px in social-card CSS rule"
if css_has "min-height: 44px" "$CSS" || css_has "min-height:44px" "$CSS"; then
  pass "SOCIAL-03: min-height: 44px (or minified variant) present in CSS"
else
  fail "SOCIAL-03: min-height: 44px MISSING from CSS — touch target requirement unmet"
fi
echo ""

# ── SOCIAL-04 ─────────────────────────────────────────────────────────────────
# All 8 platform domains present in built HTML

echo "[ SOCIAL-04 ] Social platforms — all 8 platform domains present"
PLATFORMS=(
  "feralarchitecture.substack.com"
  "linkedin.com"
  "x.com/falkensmage"
  "bsky.app"
  "instagram.com/falkensmage"
  "threads.com"
  "open.spotify.com"
  "my.tarotpulse.com"
)
PLATFORM_PASS=0
PLATFORM_FAIL=0
for platform in "${PLATFORMS[@]}"; do
  if html_has_fixed "$platform" "$HTML"; then
    PLATFORM_PASS=$((PLATFORM_PASS + 1))
  else
    echo "    MISSING platform: $platform"
    PLATFORM_FAIL=$((PLATFORM_FAIL + 1))
  fi
done
if [ "$PLATFORM_FAIL" -eq 0 ]; then
  pass "SOCIAL-04: all 8 platform domains present ($PLATFORM_PASS/8)"
else
  fail "SOCIAL-04: $PLATFORM_FAIL of 8 platform domains MISSING from built HTML"
fi
echo ""

# ── SOCIAL-05 ─────────────────────────────────────────────────────────────────
# aria-label= present at least 8 times (one per social card)

echo "[ SOCIAL-05 ] Social card accessibility — aria-label= present (>= 8)"
ARIA_COUNT=$(grep -oF -e 'aria-label=' "$HTML" | wc -l | tr -d ' ')
if [ "$ARIA_COUNT" -ge 8 ]; then
  pass "SOCIAL-05: aria-label= present $ARIA_COUNT time(s) (expected >= 8)"
else
  fail "SOCIAL-05: aria-label= count is $ARIA_COUNT, expected >= 8"
fi
echo ""

# ── CTA-01 ────────────────────────────────────────────────────────────────────
# "Coaching" text present on page (from "Coaching. Speaking. Collaboration.")

echo "[ CTA-01 ] CTA text — 'Coaching' present in built HTML"
if html_has_fixed "Coaching" "$HTML"; then
  pass "CTA-01: 'Coaching' text present in built HTML"
else
  fail "CTA-01: 'Coaching' text MISSING from built HTML"
fi
echo ""

# ── CTA-02 ────────────────────────────────────────────────────────────────────
# mailto link present AND glow-radiant-core class present

echo "[ CTA-02 ] CTA button — mailto link + glow-radiant-core class"
MAILTO_PRESENT=false
GLOW_RADIANT_PRESENT=false

if html_has_fixed "mailto:falkensmage@falkenslabyrinth.com" "$HTML"; then
  MAILTO_PRESENT=true
fi
if html_has_fixed "glow-radiant-core" "$HTML"; then
  GLOW_RADIANT_PRESENT=true
fi

if $MAILTO_PRESENT && $GLOW_RADIANT_PRESENT; then
  pass "CTA-02: mailto:falkensmage@falkenslabyrinth.com AND glow-radiant-core both present"
elif ! $MAILTO_PRESENT && ! $GLOW_RADIANT_PRESENT; then
  fail "CTA-02: both mailto link AND glow-radiant-core class MISSING"
elif ! $MAILTO_PRESENT; then
  fail "CTA-02: mailto:falkensmage@falkenslabyrinth.com MISSING from built HTML"
else
  fail "CTA-02: glow-radiant-core class MISSING from built HTML"
fi
echo ""

# ── FOOT-01 ───────────────────────────────────────────────────────────────────
# "Stay feral, folks." text present

echo "[ FOOT-01 ] Footer closing — 'Stay feral, folks.' present"
if html_has_fixed "Stay feral, folks." "$HTML"; then
  pass "FOOT-01: 'Stay feral, folks.' present in built HTML"
else
  fail "FOOT-01: 'Stay feral, folks.' MISSING from built HTML"
fi
echo ""

# ── FOOT-02 ───────────────────────────────────────────────────────────────────
# "Digital Intuition LLC" present

echo "[ FOOT-02 ] Footer copyright — 'Digital Intuition LLC' present"
if html_has_fixed "Digital Intuition LLC" "$HTML"; then
  pass "FOOT-02: 'Digital Intuition LLC' present in built HTML"
else
  fail "FOOT-02: 'Digital Intuition LLC' MISSING from built HTML"
fi
echo ""

# ── FOOT-03 ───────────────────────────────────────────────────────────────────
# footer-lemniscate class present

echo "[ FOOT-03 ] Footer sigil — footer-lemniscate class present"
if html_has_fixed "footer-lemniscate" "$HTML"; then
  pass "FOOT-03: footer-lemniscate class present in built HTML"
else
  fail "FOOT-03: footer-lemniscate class MISSING from built HTML"
fi
echo ""

# ── HERO-04 Regression: prefers-reduced-motion ────────────────────────────────
# prefers-reduced-motion must not have been removed from CSS (Phase 1 regression check)

echo "[ HERO-04-REG ] Regression — prefers-reduced-motion present in CSS"
REDUCED_MOTION_COUNT=$(grep -cF -e "prefers-reduced-motion" "$CSS" || true)
if [ "$REDUCED_MOTION_COUNT" -ge 1 ]; then
  pass "HERO-04-REG: prefers-reduced-motion present ($REDUCED_MOTION_COUNT occurrence(s)) — regression check passed"
else
  fail "HERO-04-REG: prefers-reduced-motion MISSING from CSS — Phase 1 regression!"
fi
echo ""

# ── SUMMARY ──────────────────────────────────────────────────────────────────

TOTAL=$((PASS + FAIL))
echo "====================================="
echo "Results: $PASS passed, $FAIL failed"
echo "Total automated checks: $TOTAL"
echo ""

if [ "$FAIL" -eq 0 ]; then
  echo "ALL CHECKS PASSED"
  echo ""
  exit 0
else
  echo "SOME CHECKS FAILED — see FAIL lines above"
  echo ""
  exit 1
fi
