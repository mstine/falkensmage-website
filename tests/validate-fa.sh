#!/usr/bin/env bash
# validate-fa.sh — gate for the Feral Architecture section (/fa/).
# Run from project root after a build: hugo --minify && bash tests/validate-fa.sh
# Exit 0 = all checks pass. Exit 1 = one or more checks failed.
#
# The cutover redirect rewrites feralarchitecture.com/p/<slug> → /fa/<slug>/ blindly.
# A slug with no page here becomes a silent 404 for every old link to it, so the
# first check is the one that matters: every legacy essay slug must have a page.
#
# The last two checks are the standing microformats probe. Class-level markup rot (an
# h-entry class dropped from a template, a rel=me lost from a profile link) is invisible
# in a browser and silently stops scripts/send-webmentions.py and every microformats
# parser, so it gets a probe instead of trust. Essays are found by their rendered
# og:type=article tag as well as data/fa-legacy.json, because the newest essays are not
# in that list.

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

missing_pages=$(python3 -I - "$PROJECT_ROOT/data/fa-legacy.json" "$PUBLIC" <<'PY'
import json, os, sys
legacy = json.load(open(sys.argv[1]))
for slug in legacy["pages"] + ["about", "archive"]:
    if not os.path.isfile(os.path.join(sys.argv[2], "fa", slug, "index.html")):
        print(slug)
PY
)
[ -z "$missing_pages" ] && pass "all legacy pages + about + archive exist under /fa/" || fail "pages with no /fa/ page: $(echo "$missing_pages" | tr '\n' ' ')"

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
for slug in $(python3 -I -c 'import json,sys; print(" ".join(json.load(open(sys.argv[1]))["essays"]))' "$PROJECT_ROOT/data/fa-legacy.json"); do
  page="$PUBLIC/fa/$slug/index.html"
  grep -Eq 'property="?og:type"? content="?article' "$page" && grep -Eq 'property="?og:image"?' "$page" || { no_og=$((no_og + 1)); echo "        no article OG: ${page#$PUBLIC}"; }
done
[ "$no_og" -eq 0 ] && pass "every essay has article Open Graph tags with an image" || fail "$no_og essays missing article OG tags"

stale=$(grep -l "feralarchitecture.com/p/" "$PUBLIC"/fa/*/index.html 2>/dev/null | wc -l | tr -d ' ')
[ "$stale" -eq 0 ] && pass "no essay links back to feralarchitecture.com/p/" || fail "$stale essays still link to feralarchitecture.com/p/"

leftover=$(grep -l -E '\[(insert|INSERT|TODO|TK)[^]]*\]' "$PUBLIC"/fa/*/index.html 2>/dev/null | wc -l | tr -d ' ')
[ "$leftover" -eq 0 ] && pass "no drafting placeholders ([insert …], [TODO], [TK]) in published pages" || fail "$leftover pages still contain drafting placeholders"

if grep -Eq 'href="?/fa/"?' "$PUBLIC/index.html"; then
  pass "home page links to /fa/"
else
  fail "home page has no /fa/ link"
fi

# Microformats probe, essays. html.parser reads quoted and unquoted attributes alike, which
# matters because `hugo --minify` writes class=h-entry but class="a b". Do not grep classes.
essay_probe=$(python3 -I - "$PROJECT_ROOT/data/fa-legacy.json" "$PUBLIC" <<'PY'
import glob, json, os, sys
from html.parser import HTMLParser

legacy = set(json.load(open(sys.argv[1]))["essays"])
public = sys.argv[2]


class Page(HTMLParser):
    """Reads og:type, and the h-entry (with its nested h-card tracked separately)."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.og = None
        self.entry = None        # [tag, depth] while inside the h-entry
        self.card = None         # [tag, depth] while inside the nested h-card
        self.has_entry = False
        self.entry_cls = set()   # classes at entry level, outside the h-card
        self.card_cls = set()    # classes inside the h-card
        self.author_card = False  # p-author and h-card on one element

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        if tag == "meta" and a.get("property") == "og:type":
            self.og = a.get("content")
        toks = set(a.get("class", "").split())
        if self.entry is None:
            if "h-entry" in toks and not self.has_entry:
                self.has_entry, self.entry = True, [tag, 1]
            return
        if tag == self.entry[0]:
            self.entry[1] += 1
        if self.card is not None:
            if tag == self.card[0]:
                self.card[1] += 1
            self.card_cls |= toks
        elif "h-card" in toks:
            self.card = [tag, 1]
            self.author_card = self.author_card or "p-author" in toks
        else:
            self.entry_cls |= toks

    def handle_endtag(self, tag):
        if self.entry is None:
            return
        if self.card is not None and tag == self.card[0]:
            self.card[1] -= 1
            if self.card[1] == 0:
                self.card = None
        if tag == self.entry[0]:
            self.entry[1] -= 1
            if self.entry[1] == 0:
                self.entry = self.card = None


def read(path):
    p = Page()
    p.feed(open(path, encoding="utf-8", errors="replace").read())
    p.close()
    return p


pages = {}
for path in sorted(glob.glob(os.path.join(public, "fa", "*", "index.html"))):
    pages[os.path.basename(os.path.dirname(path))] = read(path)

essays = {slug for slug, pg in pages.items() if pg.og == "article"}
essays |= {slug for slug in legacy if slug in pages}

for slug, pg in sorted(pages.items()):
    where = f"/fa/{slug}/"
    if slug not in essays:
        if pg.has_entry:
            print(f"{where} is not an essay but carries h-entry")
        continue
    if not pg.has_entry:
        print(f"{where} missing: h-entry")
        continue
    need = ["p-name", "dt-published", "e-content", "u-url"]
    if "offer-lede" in pg.entry_cls:
        need.append("p-summary")
    if "fa-essay-cover" in pg.entry_cls:
        need.append("u-photo")
    missing = [c for c in need if c not in pg.entry_cls]
    if not pg.author_card:
        missing.append("p-author+h-card")
    missing += [f"h-card>{c}" for c in ("p-name", "u-url", "u-photo") if c not in pg.card_cls]
    if missing:
        print(f"{where} missing: {', '.join(missing)}")

print(f"TOTAL {len(essays)}")
PY
)
essay_total=$(echo "$essay_probe" | sed -n 's/^TOTAL //p')
essay_problems=$(echo "$essay_probe" | grep -v '^TOTAL ')
if [ -z "$essay_total" ] || [ "$essay_total" -eq 0 ]; then
  fail "microformats probe found no essays under public/fa/"
elif [ -z "$essay_problems" ]; then
  pass "$essay_total essays carry complete h-entry markup"
else
  while IFS= read -r line; do fail "h-entry: $line"; done <<< "$essay_problems"
fi

# Microformats probe, homepage: an h-card, and every Find Me Elsewhere profile (read from
# the page's own sameAs, so nothing is hardcoded here) linked with rel=me.
home_problems=$(python3 -I - "$PUBLIC/index.html" <<'PY'
import json, sys
from html.parser import HTMLParser


class Home(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.card = None
        self.card_cls = set()
        self.has_card = False
        self.me = set()
        self.ld = None
        self.sameas = []

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        toks = set(a.get("class", "").split())
        if tag == "script" and a.get("type") == "application/ld+json":
            self.ld = []
        if tag == "a" and "me" in a.get("rel", "").lower().split() and a.get("href"):
            self.me.add(a["href"])
        if self.card is not None:
            if tag == self.card[0]:
                self.card[1] += 1
            self.card_cls |= toks
        elif "h-card" in toks and not self.has_card:
            self.has_card, self.card = True, [tag, 1]

    def handle_endtag(self, tag):
        if tag == "script" and self.ld is not None:
            collect(json.loads("".join(self.ld)), self.sameas)
            self.ld = None
        if self.card is not None and tag == self.card[0]:
            self.card[1] -= 1
            if self.card[1] == 0:
                self.card = None

    def handle_data(self, data):
        if self.ld is not None:
            self.ld.append(data)


def collect(node, out):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "sameAs":
                out.extend(v if isinstance(v, list) else [v])
            else:
                collect(v, out)
    elif isinstance(node, list):
        for v in node:
            collect(v, out)


h = Home()
h.feed(open(sys.argv[1], encoding="utf-8", errors="replace").read())
h.close()
if not h.has_card:
    print("no h-card on the home page")
else:
    gone = [c for c in ("p-name", "p-nickname", "u-url", "u-photo") if c not in h.card_cls]
    if gone:
        print(f"home page h-card missing: {', '.join(gone)}")
if not h.sameas:
    print("home page JSON-LD has no sameAs profiles to check")
for url in h.sameas:
    if url not in h.me:
        print(f"no rel=me link for {url}")
PY
)
if [ -z "$home_problems" ]; then
  pass "homepage h-card and rel=me cover every Find Me Elsewhere profile"
else
  while IFS= read -r line; do fail "$line"; done <<< "$home_problems"
fi

echo
echo "  $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
