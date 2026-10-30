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
#
# The Webmention checks follow the same rule. An empty mention section looks exactly like a
# healthy page with no mentions, so the render is checked against the data: the rel=webmention
# link is on every page, each essay's section matches data/webmentions.json (when the build
# has one), the section holds only inert markup and sits outside the h-entry, and the
# blocklist file is well formed.

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC="${VALIDATE_FA_PUBLIC:-$PROJECT_ROOT/public}"
DATA_DIR="${VALIDATE_FA_DATA:-$PROJECT_ROOT/data}"

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

# Webmention probe. html.parser, not grep: the minifier unquotes attributes. The block prints
# PASS/FAIL lines and ends with DONE; a crash leaves DONE out, which is a red, not a blank.
# It compares structure, never stranger text, so a mention cannot trip the gate (and block a
# deploy) unless something actually escaped.
mention_out=$(python3 -I - "$PUBLIC" "$DATA_DIR" <<'PY'
import glob, json, os, re, sys
from html.parser import HTMLParser

public, data_dir = sys.argv[1], sys.argv[2]
ENDPOINT = "https://webmention.io/falkensmage.com/webmention"
ALLOWED = {"h2", "p", "ul", "li", "a", "span", "time"}
KINDS = (("fa-mention--like", "likes"), ("fa-mention--repost", "reposts"),
         ("fa-mention--mention", "mentions"), ("fa-mention--reply", "replies"))
out = []


def ok(text):
    out.append("PASS " + text)


def bad(text):
    out.append("FAIL " + text)


def safe(text):
    return re.sub(r"[^A-Za-z0-9_.-]", "?", text)[:40]


class Page(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.og = None
        self.endpoints = []
        self.entry = None     # [tag, depth] while inside the h-entry
        self.sec = None       # [tag, depth] while inside the mention section
        self.sections = 0
        self.problems = set()
        self.kinds = {cls: 0 for cls, _ in KINDS}

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        toks = set(a.get("class", "").split())
        if tag == "meta" and a.get("property") == "og:type":
            self.og = a.get("content")
        if tag == "link" and "webmention" in a.get("rel", "").lower().split():
            self.endpoints.append(a.get("href"))
        for cls in self.kinds:
            if cls in toks:
                self.kinds[cls] += 1
        if self.entry is None:
            if "h-entry" in toks:
                self.entry = [tag, 1]
        elif tag == self.entry[0]:
            self.entry[1] += 1
        if self.sec is None:
            if "fa-mentions" in toks:
                self.sections += 1
                self.sec = [tag, 1]
                if self.entry is not None:
                    self.problems.add("it sits inside the h-entry")
            return
        if tag == self.sec[0]:
            self.sec[1] += 1
        if tag not in ALLOWED:
            self.problems.add(f"it holds a <{safe(tag)}> element")
        for name in a:
            if name.startswith("on") or name in ("style", "src", "srcset"):
                self.problems.add(f"it holds a {safe(name)} attribute")
        if tag == "a":
            if not {"nofollow", "ugc"} <= set(a.get("rel", "").lower().split()):
                self.problems.add("a link lacks rel nofollow ugc")
            if not re.match(r"https?://[^/\s]", a.get("href", ""), re.I):
                self.problems.add("a link is not http or https")

    def handle_endtag(self, tag):
        if self.sec is not None and tag == self.sec[0]:
            self.sec[1] -= 1
            if self.sec[1] == 0:
                self.sec = None
        if self.entry is not None and tag == self.entry[0]:
            self.entry[1] -= 1
            if self.entry[1] == 0:
                self.entry = None


pages = {}
files = [os.path.join(public, "index.html")] + sorted(glob.glob(os.path.join(public, "fa", "*", "index.html")))
for f in files:
    if not os.path.isfile(f):
        bad(f"missing built page {os.path.relpath(f, public)}")
        continue
    p = Page()
    p.feed(open(f, encoding="utf-8", errors="replace").read())
    p.close()
    rel = os.path.relpath(os.path.dirname(f), public)
    pages["/" if rel == "." else "/" + rel + "/"] = p

# 1. the endpoint link, on every page
lacking = [path for path, p in pages.items() if ENDPOINT not in p.endpoints]
for path in lacking:
    bad(f"no rel=webmention link on {path}")
if pages and not lacking:
    ok(f"webmention endpoint advertised on {len(pages)} pages")

# 2 and 3. the render against the data, and the section's safety
data, readable = None, True
data_file = os.path.join(data_dir, "webmentions.json")
if os.path.isfile(data_file):
    try:
        data = json.load(open(data_file, encoding="utf-8"))["pages"]
        assert isinstance(data, dict)
    except Exception:
        readable = False
        bad("webmentions.json is unreadable or has the wrong shape")
problems = []
essays = 0
for path, p in sorted(pages.items()):
    essay = p.og == "article"
    essays += essay
    entry = data.get(path) if (data and essay) else None
    entry = entry if isinstance(entry, dict) else {}
    want = 1 if entry else 0
    if p.sections != want:
        problems.append(f"{path} has {p.sections} mention sections, expected {want}")
    for what in sorted(p.problems):
        problems.append(f"{path} mention section: {what}")
    for cls, key in KINDS:
        n = len(entry.get(key) or [])
        if p.kinds[cls] != n:
            problems.append(f"{path} {key}: data has {n}, page has {p.kinds[cls]}")
for line in problems:
    bad(line)
if readable and not problems:
    if data is None:
        ok("no mention data in this build, and no mention section on any page")
    else:
        ok(f"mention sections match the pulled data on {essays} essays")

# 4. the committed blocklist
try:
    block = json.load(open(os.path.join(data_dir, "webmention-blocklist.json"), encoding="utf-8"))
    assert isinstance(block, dict)
    for key in ("domains", "authors"):
        assert isinstance(block[key], list) and all(isinstance(v, str) for v in block[key])
    ok("webmention blocklist is well formed")
except Exception:
    bad("webmention blocklist is missing or malformed")

print("\n".join(out))
print("DONE")
PY
)
mention_done=0
while IFS= read -r line; do
  case "$line" in
    "PASS "*) pass "${line#PASS }" ;;
    "FAIL "*) fail "${line#FAIL }" ;;
    DONE) mention_done=1 ;;
  esac
done <<< "$mention_out"
[ "$mention_done" -eq 1 ] || fail "webmention probe did not finish"

echo
echo "  $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
