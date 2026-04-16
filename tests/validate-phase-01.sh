#!/usr/bin/env bash
# validate-phase-01.sh
# Automated validation for Phase 1 — Theme Foundation
# Run from project root: bash tests/validate-phase-01.sh
# Exit 0 = all checks pass. Exit 1 = one or more checks failed.

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL + 1)); }

# css_has VAR FILE — fixed-string search safe against leading-dash patterns
css_has() { grep -qF -e "$1" "$2"; }

echo ""
echo "Phase 1 — Theme Foundation Validation"
echo "======================================"
echo "Project root: $PROJECT_ROOT"
echo ""

# ── 01-01-01 INFRA-01 ────────────────────────────────────────────────────────
# Hugo build exits 0

echo "[ 01-01-01 ] INFRA-01: Hugo build exits 0"
cd "$PROJECT_ROOT"
if hugo --minify --quiet > /dev/null 2>&1; then
  pass "hugo --minify exits with code 0"
else
  fail "hugo --minify failed (non-zero exit)"
fi
echo ""

# ── 01-01-02 INFRA-02 ────────────────────────────────────────────────────────
# HTTPS baseURL in hugo.toml

echo "[ 01-01-02 ] INFRA-02: HTTPS baseURL in hugo.toml"
TOML="$PROJECT_ROOT/hugo.toml"
if grep -qF -e 'baseURL = "https://falkensmage.com/"' "$TOML"; then
  pass 'baseURL = "https://falkensmage.com/" found in hugo.toml'
else
  fail "HTTPS baseURL not found in hugo.toml"
fi
echo ""

# ── 01-02-01 THEME-01 ────────────────────────────────────────────────────────
# All 11 --arcaeon-* palette truth vars + 10 --color-* semantic aliases in main.css

echo "[ 01-02-01 ] THEME-01: CSS token system — 11 palette vars + 10 semantic aliases"
CSS="$PROJECT_ROOT/themes/arcaeon/assets/css/main.css"

PALETTE_VARS=(
  "--arcaeon-electric-violet"
  "--arcaeon-neon-magenta"
  "--arcaeon-plasma-pink"
  "--arcaeon-electric-blue"
  "--arcaeon-solar-white"
  "--arcaeon-fusion-gold"
  "--arcaeon-ignition-orange"
  "--arcaeon-deep-indigo"
  "--arcaeon-midnight-blue"
  "--arcaeon-void-purple"
  "--arcaeon-ion-glow"
)

SEMANTIC_VARS=(
  "--color-bg"
  "--color-bg-alt"
  "--color-bg-transition"
  "--color-text"
  "--color-text-accent"
  "--color-accent"
  "--color-accent-warm"
  "--color-hover"
  "--color-cta-start"
  "--color-cta-end"
)

for v in "${PALETTE_VARS[@]}"; do
  if css_has "$v" "$CSS"; then
    pass "palette var $v present"
  else
    fail "palette var $v MISSING"
  fi
done

for v in "${SEMANTIC_VARS[@]}"; do
  if css_has "$v" "$CSS"; then
    pass "semantic alias $v present"
  else
    fail "semantic alias $v MISSING"
  fi
done
echo ""

# ── 01-02-02 THEME-02 ────────────────────────────────────────────────────────
# WOFF2 files exist + font-display: swap + exactly 2 @font-face declarations

echo "[ 01-02-02 ] THEME-02: Self-hosted fonts — WOFF2 files + font-display: swap + 2 @font-face"

CINZEL_WOFF2="$PROJECT_ROOT/themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2"
SPACE_WOFF2="$PROJECT_ROOT/themes/arcaeon/assets/fonts/space-grotesk-latin-wght-normal.woff2"

if [ -f "$CINZEL_WOFF2" ]; then
  pass "cinzel-latin-wght-normal.woff2 exists"
else
  fail "cinzel-latin-wght-normal.woff2 MISSING from themes/arcaeon/assets/fonts/"
fi

if [ -f "$SPACE_WOFF2" ]; then
  pass "space-grotesk-latin-wght-normal.woff2 exists"
else
  fail "space-grotesk-latin-wght-normal.woff2 MISSING from themes/arcaeon/assets/fonts/"
fi

FONT_DISPLAY_COUNT=$(grep -cF -e "font-display: swap" "$CSS" || true)
if [ "$FONT_DISPLAY_COUNT" -ge 2 ]; then
  pass "font-display: swap present ($FONT_DISPLAY_COUNT occurrences, expected >= 2)"
else
  fail "font-display: swap count is $FONT_DISPLAY_COUNT, expected >= 2"
fi

FONT_FACE_COUNT=$(grep -cF -e "@font-face" "$CSS" || true)
if [ "$FONT_FACE_COUNT" -eq 2 ]; then
  pass "@font-face declarations = 2 (Cinzel + Space Grotesk)"
else
  fail "@font-face count is $FONT_FACE_COUNT, expected exactly 2"
fi
echo ""

# ── 01-03-01 THEME-03 ────────────────────────────────────────────────────────
# Glow classes exist + zero box-shadow

echo "[ 01-03-01 ] THEME-03: Glow system — 3 classes present + zero box-shadow"

GLOW_CLASSES=(".glow-ambient" ".glow-interactive" ".glow-radiant-core")
for cls in "${GLOW_CLASSES[@]}"; do
  if css_has "$cls" "$CSS"; then
    pass "glow class $cls present"
  else
    fail "glow class $cls MISSING"
  fi
done

BOX_SHADOW_COUNT=$(grep -cF -e "box-shadow" "$CSS" || true)
if [ "$BOX_SHADOW_COUNT" -eq 0 ]; then
  pass "zero box-shadow declarations (GPU-composited glow only)"
else
  fail "box-shadow found $BOX_SHADOW_COUNT time(s) — must be 0"
fi
echo ""

# ── 01-03-02 THEME-04 ────────────────────────────────────────────────────────
# Section alternation: .section-void and .section-depth classes

echo "[ 01-03-02 ] THEME-04: Section alternation — .section-void and .section-depth"

if css_has ".section-void" "$CSS"; then
  pass ".section-void class present"
else
  fail ".section-void class MISSING"
fi

if css_has ".section-depth" "$CSS"; then
  pass ".section-depth class present"
else
  fail ".section-depth class MISSING"
fi
echo ""

# ── 01-03-03 THEME-05 ────────────────────────────────────────────────────────
# No horizontal scroll at 375px — MANUAL ONLY

echo "[ 01-03-03 ] THEME-05: No horizontal scroll at 375px viewport"
echo "  MANUAL  Cannot be automated — requires browser DevTools at 375px"
echo "          Instructions: hugo server --buildDrafts -> open /kitchen-sink/ -> DevTools device toolbar 375px -> confirm no horizontal overflow"
echo ""

# ── 01-03-04 THEME-06 ────────────────────────────────────────────────────────
# Sigil classes exist

echo "[ 01-03-04 ] THEME-06: Sigil grammar — .sigil-arc, .sigil-arc-sm, .sigil-gradient"

SIGIL_CLASSES=(".sigil-arc" ".sigil-arc-sm" ".sigil-gradient")
for cls in "${SIGIL_CLASSES[@]}"; do
  if css_has "$cls" "$CSS"; then
    pass "sigil class $cls present"
  else
    fail "sigil class $cls MISSING"
  fi
done
echo ""

# ── 01-04-01 THEME-07 ────────────────────────────────────────────────────────
# Theme directory structure

echo "[ 01-04-01 ] THEME-07: Theme structure — required dirs and files under themes/arcaeon/"

REQUIRED_PATHS=(
  "themes/arcaeon/assets/css/main.css"
  "themes/arcaeon/assets/fonts/cinzel-latin-wght-normal.woff2"
  "themes/arcaeon/assets/fonts/space-grotesk-latin-wght-normal.woff2"
  "themes/arcaeon/layouts/_default/baseof.html"
  "themes/arcaeon/layouts/index.html"
)

REQUIRED_DIRS=(
  "themes/arcaeon/assets/css"
  "themes/arcaeon/assets/fonts"
  "themes/arcaeon/layouts/_default"
  "themes/arcaeon/static"
)

for p in "${REQUIRED_PATHS[@]}"; do
  if [ -f "$PROJECT_ROOT/$p" ]; then
    pass "file exists: $p"
  else
    fail "file MISSING: $p"
  fi
done

for d in "${REQUIRED_DIRS[@]}"; do
  if [ -d "$PROJECT_ROOT/$d" ]; then
    pass "dir exists: $d"
  else
    fail "dir MISSING: $d"
  fi
done

# No root-level layouts directory with files (all layouts must be under themes/arcaeon/)
if [ ! -d "$PROJECT_ROOT/layouts" ]; then
  pass "root layouts/ directory absent (all layouts under themes/arcaeon/)"
else
  ROOT_LAYOUT_COUNT=$(find "$PROJECT_ROOT/layouts" -type f 2>/dev/null | wc -l | tr -d ' ')
  if [ "$ROOT_LAYOUT_COUNT" -eq 0 ]; then
    pass "root layouts/ directory exists but is empty (acceptable)"
  else
    fail "root layouts/ contains $ROOT_LAYOUT_COUNT file(s) — all layouts must be under themes/arcaeon/"
  fi
fi
echo ""

# ── SUMMARY ──────────────────────────────────────────────────────────────────

TOTAL=$((PASS + FAIL))
echo "======================================"
echo "Results: $PASS passed, $FAIL failed, 1 manual-only (THEME-05)"
echo "Total automated checks: $TOTAL"
echo ""

if [ "$FAIL" -eq 0 ]; then
  echo "ALL AUTOMATED CHECKS PASSED"
  echo ""
  exit 0
else
  echo "SOME CHECKS FAILED — see FAIL lines above"
  echo ""
  exit 1
fi
