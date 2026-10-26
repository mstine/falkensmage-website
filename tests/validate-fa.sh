#!/usr/bin/env bash
# validate-fa.sh — gate for the Feral Architecture section (/fa/).
# Run from project root after a build: hugo --minify && bash tests/validate-fa.sh
# Exit 0 = all checks pass. Exit 1 = one or more checks failed.
#
# The cutover redirect rewrites feralarchitecture.com/p/<slug> → /fa/<slug>/ blindly.
# A slug with no page here becomes a silent 404 for every old link to it, so the
# first check is the one that matters: every legacy essay slug must have a page.

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC="$PROJECT_ROOT/public"

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL + 1)); }

echo "Feral Architecture (/fa/)"

missing=$(python3 -I - "$PROJECT_ROOT/data/fa-legacy.json" "$PUBLIC" <<'PY'
import json, os, sys
legacy = json.load(open(sys.argv[1]))
for slug in legacy["essays"]:
    if not os.path.isfile(os.path.join(sys.argv[2], "fa", slug, "index.html")):
        print(slug)
PY
)
total=$(python3 -I -c 'import json,sys; print(len(json.load(open(sys.argv[1]))["essays"]))' "$PROJECT_ROOT/data/fa-legacy.json")
if [ -z "$missing" ]; then
  pass "all $total legacy essay slugs have a page under /fa/"
else
  fail "legacy slugs with no page: $(echo "$missing" | tr '\n' ' ')"
fi

leaked=$(python3 -I - "$PROJECT_ROOT/data/fa-legacy.json" "$PUBLIC" <<'PY'
import json, os, sys
for slug in json.load(open(sys.argv[1]))["withdrawn"]:
    if os.path.exists(os.path.join(sys.argv[2], "fa", slug)):
        print(slug)
PY
)
[ -z "$leaked" ] && pass "withdrawn essays are not published" || fail "withdrawn essay published: $leaked"

feed="$PUBLIC/fa/index.xml"
if [ -f "$feed" ] && grep -q "<content:encoded>" "$feed"; then
  pass "full-content RSS at /fa/index.xml"
else
  fail "/fa/index.xml missing or has no full-content items"
fi

no_og=0
for page in "$PUBLIC"/fa/*/index.html; do
  grep -Eq 'property="?og:type"? content="?article' "$page" && grep -Eq 'property="?og:image"?' "$page" || { no_og=$((no_og + 1)); echo "        no article OG: ${page#$PUBLIC}"; }
done
[ "$no_og" -eq 0 ] && pass "every essay has article Open Graph tags with an image" || fail "$no_og essays missing article OG tags"

stale=$(grep -l "feralarchitecture.com/p/" "$PUBLIC"/fa/*/index.html 2>/dev/null | wc -l | tr -d ' ')
[ "$stale" -eq 0 ] && pass "no essay links back to feralarchitecture.com/p/" || fail "$stale essays still link to feralarchitecture.com/p/"

if grep -Eq 'href="?/fa/"?' "$PUBLIC/index.html"; then
  pass "home page links to /fa/"
else
  fail "home page has no /fa/ link"
fi

echo
echo "  $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
