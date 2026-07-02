#!/usr/bin/env bash
# validate-phase-06.sh
# Automated validation for Phase 6 — Offer Pages
# Run from project root: bash tests/validate-phase-06.sh
# Exit 0 = all checks pass. Exit 1 = one or more checks failed.
#
# OFFERQ-02 coverage rationale (read before editing this file):
# OFFERQ-02 is a four-part budget — sub-1s/3G, zero external deps/CDN,
# mobile-first 375px, WCAG AA. Phase 6 adds NO new CSS system: the /work/
# templates compose exclusively from existing arcaeon classes and palette
# vars (section-void/section-depth, glow-radiant-core). Therefore:
#   - sub-1s/3G           -> INHERITED-BY-REUSE (no new assets/CSS/JS added;
#                            already verified in phases 1-3).
#   - mobile-first 375px  -> INHERITED-BY-REUSE from baseof.html's fluid
#                            layout + viewport meta; guarded below by a
#                            direct viewport-meta-tag check on every new page.
#   - WCAG AA contrast    -> INHERITED-BY-REUSE from the ARCÆON palette CSS
#                            custom properties; guarded below by a "no new
#                            hex color literal" negative grep — if a new
#                            hardcoded hex color were introduced, contrast
#                            would no longer be guaranteed by the existing,
#                            already-audited palette.
#   - zero external deps  -> verified directly below (no booking script/
#                            widget under public/work/, no new CDN).
# Full 3G-timing and contrast re-measurement is out of scope here precisely
# because no new design surface was introduced — the guards below (viewport
# meta, no-new-hex, no-fixed-px) are what keep that inheritance intact; if a
# future change touches the design system, they will fail and re-measurement
# becomes necessary again.

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

# href_has PATH FILE — matches href=PATH with or without surrounding quotes.
# Hugo's minifier drops quotes from attribute values that need no escaping
# (e.g. href=/work/ instead of href="/work/"), so a plain quoted-string grep
# is not reliable against a minified build.
href_has() { grep -qE "href=\"?${1}\"?" "$2"; }

# count_matches PATTERN FILE... — total occurrence count (not line count) of
# an extended-regex PATTERN across one or more files. Uses `grep -hoE` (no -c)
# so multi-file invocations never hit the "grep -c prints one count PER FILE"
# portability quirk noted in 06-02's execution — every match becomes its own
# output line via -o, then wc -l gives one aggregate total.
count_matches() {
  local pattern="$1"; shift
  grep -hoE "$pattern" "$@" 2>/dev/null | wc -l | tr -d ' '
}

# count_matches_ci — case-insensitive variant of count_matches.
count_matches_ci() {
  local pattern="$1"; shift
  grep -hoEi "$pattern" "$@" 2>/dev/null | wc -l | tr -d ' '
}

# count_matches_recursive PATTERN DIR — same as count_matches, but recurses
# into a directory (for scanning public/work/ build output).
count_matches_recursive() {
  local pattern="$1" dir="$2"
  grep -rhoEi "$pattern" "$dir" 2>/dev/null | wc -l | tr -d ' '
}

echo ""
echo "Phase 6 — Offer Pages Validation"
echo "====================================="
echo "Project root: $PROJECT_ROOT"
echo ""

# ── Build ──────────────────────────────────────────────────────────────────
echo "[ Build ] Clean hugo --minify exits 0"
cd "$PROJECT_ROOT"
rm -rf public/ resources/_gen/
if hugo --minify --quiet > /dev/null 2>&1; then
  pass "hugo --minify exits with code 0"
else
  fail "hugo --minify failed (non-zero exit)"
  echo ""
  echo "FATAL: Hugo build failed — aborting remaining checks"
  exit 1
fi
if [ -f "$PROJECT_ROOT/public/index.html" ]; then
  pass "public/index.html exists after clean build"
else
  fail "public/index.html MISSING after clean build"
  echo ""
  echo "FATAL: build did not produce homepage — aborting remaining checks"
  exit 1
fi
echo ""

HOME_HTML="$PROJECT_ROOT/public/index.html"
HUB_HTML="$PROJECT_ROOT/public/work/index.html"
QUERY_HTML="$PROJECT_ROOT/public/work/the-query/index.html"
CAST_HTML="$PROJECT_ROOT/public/work/the-cast/index.html"
DAEMON_HTML="$PROJECT_ROOT/public/work/the-daemon/index.html"
SINGLE_TPL="$PROJECT_ROOT/themes/arcaeon/layouts/work/single.html"
LIST_TPL="$PROJECT_ROOT/themes/arcaeon/layouts/work/list.html"
HUGO_TOML="$PROJECT_ROOT/hugo.toml"
CONTENT_WORK_DIR="$PROJECT_ROOT/content/work"

# ── OFFER-01 ──────────────────────────────────────────────────────────────
# /work/ hub exists and links to all three offer pages

echo "[ OFFER-01 ] /work/ hub renders and links to all three offer pages"
if [ -f "$HUB_HTML" ]; then
  pass "OFFER-01: public/work/index.html exists"
else
  fail "OFFER-01: public/work/index.html MISSING"
fi
if href_has "/work/the-query/" "$HUB_HTML" 2>/dev/null; then
  pass "OFFER-01: hub links to /work/the-query/"
else
  fail "OFFER-01: hub MISSING link to /work/the-query/"
fi
if href_has "/work/the-cast/" "$HUB_HTML" 2>/dev/null; then
  pass "OFFER-01: hub links to /work/the-cast/"
else
  fail "OFFER-01: hub MISSING link to /work/the-cast/"
fi
if href_has "/work/the-daemon/" "$HUB_HTML" 2>/dev/null; then
  pass "OFFER-01: hub links to /work/the-daemon/"
else
  fail "OFFER-01: hub MISSING link to /work/the-daemon/"
fi
echo ""

# ── OFFER-02 ──────────────────────────────────────────────────────────────
# The Query: $250, 90 minutes, "Book & Pay"

echo "[ OFFER-02 ] The Query — \$250 / 90 minutes / 'Book & Pay' CTA"
if html_has_fixed '$250' "$QUERY_HTML"; then
  pass "OFFER-02: \$250 present on the-query page"
else
  fail "OFFER-02: \$250 MISSING from the-query page"
fi
if html_has_fixed "90 minutes" "$QUERY_HTML"; then
  pass "OFFER-02: '90 minutes' present on the-query page"
else
  fail "OFFER-02: '90 minutes' MISSING from the-query page"
fi
if html_has_fixed "Book & Pay" "$QUERY_HTML" || html_has_fixed "Book &amp; Pay" "$QUERY_HTML"; then
  pass "OFFER-02: 'Book & Pay' CTA present on the-query page"
else
  fail "OFFER-02: 'Book & Pay' CTA MISSING from the-query page"
fi
echo ""

# ── OFFER-03 ──────────────────────────────────────────────────────────────
# The Cast: $325, 90 minutes, "Book & Pay"

echo "[ OFFER-03 ] The Cast — \$325 / 90 minutes / 'Book & Pay' CTA"
if html_has_fixed '$325' "$CAST_HTML"; then
  pass "OFFER-03: \$325 present on the-cast page"
else
  fail "OFFER-03: \$325 MISSING from the-cast page"
fi
if html_has_fixed "90 minutes" "$CAST_HTML"; then
  pass "OFFER-03: '90 minutes' present on the-cast page"
else
  fail "OFFER-03: '90 minutes' MISSING from the-cast page"
fi
if html_has_fixed "Book & Pay" "$CAST_HTML" || html_has_fixed "Book &amp; Pay" "$CAST_HTML"; then
  pass "OFFER-03: 'Book & Pay' CTA present on the-cast page"
else
  fail "OFFER-03: 'Book & Pay' CTA MISSING from the-cast page"
fi
echo ""

# ── OFFER-04 ──────────────────────────────────────────────────────────────
# The Daemon: $4,500 engagement shape + consult CTA mentioning $150/credited,
# with a CONCRETE negative check that the CTA is NOT a direct-buy label.

echo "[ OFFER-04 ] The Daemon — \$4,500 shape / consult-gated CTA (\$150, credited)"
if html_has_fixed '$4,500' "$DAEMON_HTML"; then
  pass "OFFER-04: \$4,500 engagement shape present on the-daemon page"
else
  fail "OFFER-04: \$4,500 MISSING from the-daemon page"
fi
if html_has "150.*credit|credit.*150|Clarity Consult" "$DAEMON_HTML"; then
  pass "OFFER-04: consult CTA mentioning \$150/credited present on the-daemon page"
else
  fail "OFFER-04: consult CTA (\$150/credited) MISSING from the-daemon page"
fi

# Concrete negative check: extract the glow-radiant-core CTA anchor's inner
# text and confirm it is NOT one of the forbidden direct-buy labels.
DAEMON_CTA_TEXT=$(grep -oE 'glow-radiant-core[^>]*>[^<]*' "$DAEMON_HTML" | sed -E 's/^.*>//' || true)
if [ -z "$DAEMON_CTA_TEXT" ]; then
  fail "OFFER-04: could not extract glow-radiant-core CTA anchor text from the-daemon page"
else
  FORBIDDEN=false
  case "$DAEMON_CTA_TEXT" in
    '$4,500'|'Buy Now'|'Book & Pay'|'Book &amp; Pay') FORBIDDEN=true ;;
  esac
  if $FORBIDDEN; then
    fail "OFFER-04: the-daemon glow-radiant-core CTA text is a forbidden direct-buy label ('$DAEMON_CTA_TEXT')"
  else
    pass "OFFER-04: the-daemon glow-radiant-core CTA text ('$DAEMON_CTA_TEXT') is NOT \$4,500 / Buy Now / Book & Pay — consult-gate held"
  fi
fi
echo ""

# ── OFFER-05 ──────────────────────────────────────────────────────────────
# [params.booking] single-source config; built CTA hrefs match config values

echo "[ OFFER-05 ] [params.booking] single-source config; CTA hrefs match config"
if grep -qE '^\[params\.booking\]' "$HUGO_TOML"; then
  pass "OFFER-05: [params.booking] table present in hugo.toml"
else
  fail "OFFER-05: [params.booking] table MISSING from hugo.toml"
fi

get_booking_value() {
  # Extract the value for a given booking key from hugo.toml, e.g.
  #   "the-query" = "https://cal.com/PLACEHOLDER/the-query"
  # NOTE: uses [[:space:]] rather than \s — BSD/macOS sed (unlike GNU sed)
  # does not support the \s shorthand even in extended-regex (-E) mode.
  local key="$1"
  grep -E "^[[:space:]]*\"?${key}\"?[[:space:]]*=" "$HUGO_TOML" | head -1 \
    | sed -E 's/^[^=]*=[[:space:]]*"([^"]*)".*/\1/'
}

QUERY_CFG=$(get_booking_value "the-query")
CAST_CFG=$(get_booking_value "the-cast")
DAEMON_CFG=$(get_booking_value "the-daemon")

# Fixed-string containment check (grep -F) — no ERE metachar escaping needed
# since the config values themselves (URLs with '.' and '/') are compared
# verbatim against the built page.
if [ -n "$QUERY_CFG" ] && grep -qF -- "$QUERY_CFG" "$QUERY_HTML"; then
  pass "OFFER-05: the-query built CTA href matches [params.booking] the-query value ($QUERY_CFG)"
else
  fail "OFFER-05: the-query built CTA href does NOT match [params.booking] the-query value"
fi
if [ -n "$CAST_CFG" ] && grep -qF -- "$CAST_CFG" "$CAST_HTML"; then
  pass "OFFER-05: the-cast built CTA href matches [params.booking] the-cast value ($CAST_CFG)"
else
  fail "OFFER-05: the-cast built CTA href does NOT match [params.booking] the-cast value"
fi
if [ -n "$DAEMON_CFG" ] && grep -qF -- "$DAEMON_CFG" "$DAEMON_HTML"; then
  pass "OFFER-05: the-daemon built CTA href matches [params.booking] the-daemon value ($DAEMON_CFG)"
else
  fail "OFFER-05: the-daemon built CTA href does NOT match [params.booking] the-daemon value"
fi

# No hardcoded booking-provider URL literal in templates/content (hugo.toml is
# the legitimate single source and is excluded from this negative check).
CAL_LITERAL_COUNT=$(count_matches 'cal\.com' "$SINGLE_TPL" "$LIST_TPL" "$CONTENT_WORK_DIR"/*.md)
if [ "$CAL_LITERAL_COUNT" -eq 0 ]; then
  pass "OFFER-05: zero hardcoded cal.com URL literals in templates/content (config is single source)"
else
  fail "OFFER-05: found $CAL_LITERAL_COUNT hardcoded cal.com URL literal(s) in templates/content"
fi
echo ""

# ── NAV-01 ────────────────────────────────────────────────────────────────
# Homepage secondary CTA points to /work/; old mailto gone

echo "[ NAV-01 ] Homepage secondary CTA -> /work/; legacy mailto removed"
if href_has "/work/" "$HOME_HTML"; then
  pass "NAV-01: public/index.html secondary CTA links to /work/"
else
  fail "NAV-01: public/index.html MISSING href to /work/"
fi
MAILTO_COUNT=$(grep -c 'mailto:falkensmage@falkenslabyrinth.com' "$HOME_HTML" || true)
if [ "$MAILTO_COUNT" -eq 0 ]; then
  pass "NAV-01: legacy mailto:falkensmage@falkenslabyrinth.com absent from public/index.html"
else
  fail "NAV-01: legacy mailto:falkensmage@falkenslabyrinth.com still present ($MAILTO_COUNT occurrence(s))"
fi
echo ""

# ── OFFERQ-01 ─────────────────────────────────────────────────────────────
# Design-system reuse only — arcaeon classes, no new <style> blocks

echo "[ OFFERQ-01 ] Design-system reuse — arcaeon classes only, no new CSS"
if html_has_fixed "section-void" "$QUERY_HTML" && html_has_fixed "section-depth" "$QUERY_HTML"; then
  pass "OFFERQ-01: section-void AND section-depth present on the-query page"
else
  fail "OFFERQ-01: section-void and/or section-depth MISSING from the-query page"
fi
if html_has_fixed "glow-radiant-core" "$QUERY_HTML"; then
  pass "OFFERQ-01: glow-radiant-core present on the-query page"
else
  fail "OFFERQ-01: glow-radiant-core MISSING from the-query page"
fi
STYLE_BLOCK_COUNT=$(count_matches '<style' "$SINGLE_TPL" "$LIST_TPL")
if [ "$STYLE_BLOCK_COUNT" -eq 0 ]; then
  pass "OFFERQ-01: zero <style blocks in work/single.html and work/list.html"
else
  fail "OFFERQ-01: found $STYLE_BLOCK_COUNT <style block(s) in work templates"
fi
echo ""

# ── OFFERQ-02 (link-out / zero-dep leg) ──────────────────────────────────

echo "[ OFFERQ-02a ] Link-out only — no booking script/widget; rel=noopener"
BOOKING_SCRIPT_COUNT=$(count_matches_recursive '<script[^>]*(cal\.com|calendly|booking)' "$PROJECT_ROOT/public/work/")
if [ "$BOOKING_SCRIPT_COUNT" -eq 0 ]; then
  pass "OFFERQ-02a: no booking-provider <script> tags under public/work/"
else
  fail "OFFERQ-02a: found $BOOKING_SCRIPT_COUNT booking-provider <script> reference(s) under public/work/"
fi

WIDGET_COUNT=$(count_matches_recursive 'cal-embed|cal\.com/embed|data-cal-link|calendly-inline' "$PROJECT_ROOT/public/work/")
if [ "$WIDGET_COUNT" -eq 0 ]; then
  pass "OFFERQ-02a: no booking-widget/embed markup under public/work/"
else
  fail "OFFERQ-02a: found $WIDGET_COUNT booking-widget/embed reference(s) under public/work/"
fi

# Every target=_blank anchor in built offer pages must carry rel=noopener.
NOOPENER_OK=true
for f in "$HUB_HTML" "$QUERY_HTML" "$CAST_HTML" "$DAEMON_HTML"; do
  # extract each anchor tag containing target=_blank/"_blank" and check it also has noopener
  while IFS= read -r anchor; do
    [ -z "$anchor" ] && continue
    if ! printf '%s' "$anchor" | grep -qi 'noopener'; then
      NOOPENER_OK=false
      echo "    MISSING rel=noopener: $anchor (in $f)"
    fi
  done < <(grep -oE '<a[^>]*target=_?"?_blank"?[^>]*>' "$f" 2>/dev/null)
done
if $NOOPENER_OK; then
  pass "OFFERQ-02a: every target=_blank anchor in built offer pages carries rel=noopener"
else
  fail "OFFERQ-02a: one or more target=_blank anchors MISSING rel=noopener"
fi
echo ""

# ── OFFERQ-02 (mobile-first 375px leg) ───────────────────────────────────

echo "[ OFFERQ-02b ] Mobile-first — viewport meta on every /work/ page"
VIEWPORT_OK=true
for f in "$HUB_HTML" "$QUERY_HTML" "$CAST_HTML" "$DAEMON_HTML"; do
  if ! grep -qE 'name=\"?viewport\"?[^>]*width=device-width' "$f" 2>/dev/null; then
    VIEWPORT_OK=false
    echo "    MISSING viewport meta: $f"
  fi
done
if $VIEWPORT_OK; then
  pass "OFFERQ-02b: viewport meta (width=device-width) present on hub + all three offer pages"
else
  fail "OFFERQ-02b: viewport meta MISSING from one or more /work/ pages"
fi
echo ""

# ── OFFERQ-02 (WCAG-AA + fluidity, inherited-by-reuse guard) ─────────────

echo "[ OFFERQ-02c ] No new design language — zero new hex colors / fixed-px widths"
HEX_COUNT=$(count_matches '#[0-9a-fA-F]{6}' "$SINGLE_TPL" "$LIST_TPL" "$CONTENT_WORK_DIR"/*.md)
if [ "$HEX_COUNT" -eq 0 ]; then
  pass "OFFERQ-02c: zero hardcoded 6-digit hex color literals in work templates/content"
else
  fail "OFFERQ-02c: found $HEX_COUNT hardcoded hex color literal(s) in work templates/content"
fi

PX_COUNT=$(count_matches '(min-)?width:[[:space:]]*[0-9]+px' "$SINGLE_TPL" "$LIST_TPL" "$CONTENT_WORK_DIR"/*.md)
if [ "$PX_COUNT" -eq 0 ]; then
  pass "OFFERQ-02c: zero fixed-px container widths introduced in work templates/content"
else
  fail "OFFERQ-02c: found $PX_COUNT fixed-px width declaration(s) in work templates/content"
fi
echo ""

# ── Language rule ─────────────────────────────────────────────────────────
# Belt-and-suspenders: banned practitioner terms must not appear anywhere in
# content/work/*.md (checked per-file to avoid the multi-file grep -c
# per-file-count portability quirk noted in 06-02's execution).

echo "[ Language rule ] No 'tarot reader' / 'chaos magician' in content/work/*.md"
LANG_VIOLATIONS=$(count_matches_ci 'tarot reader|chaos magician' "$CONTENT_WORK_DIR"/*.md)
if [ "$LANG_VIOLATIONS" -eq 0 ]; then
  pass "Language rule: zero occurrences of banned practitioner terms in content/work/*.md"
else
  fail "Language rule: found $LANG_VIOLATIONS banned practitioner term occurrence(s) in content/work/*.md"
fi
echo ""

# ── SUMMARY ──────────────────────────────────────────────────────────────

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
