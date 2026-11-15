#!/usr/bin/env bash
# validate-cr.sh — gate for the Contemplating Resonance section (/cr/).
# Run from the project root: bash tests/validate-cr.sh
# It builds the site itself (into a temp directory, never public/), then checks the build.
# Exit 0 = all checks pass. Exit 1 = one or more checks failed.
#
# NOT in .github/workflows until cutover day. /cr/ is scaffolded on branch cr/own-the-stack
# and stays unlinked and unmerged until then.
#
# The cutover redirect rewrites falkenslabyrinth.com/p/<slug> → /cr/<slug>/ blindly, so a slug
# with no page here becomes a silent 404 for every old link to it. The first check is the one
# that matters: every kept slug in data/cr-legacy.json (written by scripts/sync-cr.py, because
# CI cannot read ~/.psyche) must have a page. The rest guard the sanitizer: the bodies are
# remote HTML published unescaped, so every body is re-parsed here, not trusted.
#
# VALIDATE_CR_PARTIAL=1 checks only the slugs that have a content/cr/<slug>/ bundle and skips
# the "all 51" and feed checks. VALIDATE_CR_PUBLIC=<dir> checks an existing build instead.

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARTIAL="${VALIDATE_CR_PARTIAL:-}"
LEGACY="$PROJECT_ROOT/data/cr-legacy.json"
CONTENT="$PROJECT_ROOT/content/cr"

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL + 1)); }
info() { echo "  INFO  $1"; }

if [ -n "${VALIDATE_CR_PUBLIC:-}" ]; then
  PUBLIC="$VALIDATE_CR_PUBLIC"
else
  PUBLIC="$(mktemp -d "${TMPDIR:-/tmp}/validate-cr.XXXXXX")"
  trap 'rm -rf "$PUBLIC"' EXIT
  if ! (cd "$PROJECT_ROOT" && hugo --minify --quiet --destination "$PUBLIC"); then
    echo "  FAIL  hugo build failed"
    exit 1
  fi
fi

echo "Contemplating Resonance (/cr/)"

# Slugs under test: all kept slugs, or (partial) the ones that have a bundle.
slugs=$(python3 -I - "$LEGACY" "$CONTENT" "$PARTIAL" <<'PY'
import json, os, sys
legacy = json.load(open(sys.argv[1]))
slugs = legacy["posts"]
if sys.argv[3]:
    slugs = [s for s in slugs if os.path.isdir(os.path.join(sys.argv[2], s))]
print("\n".join(slugs))
PY
)
count=$(printf '%s' "$slugs" | grep -c . || true)

# a. every kept slug has a built page
missing=""
for slug in $slugs; do
  [ -f "$PUBLIC/cr/$slug/index.html" ] || missing="$missing $slug"
done
if [ -z "$missing" ] && [ "$count" -gt 0 ]; then
  pass "all $count slugs have a page under /cr/"
else
  fail "slugs with no page under /cr/ (or none under test):$missing"
fi

# b. the gated posts were never published
leaked=$(python3 -I - "$LEGACY" "$CONTENT" "$PUBLIC" <<'PY'
import json, os, sys
for slug in json.load(open(sys.argv[1]))["dropped"]:
    for base in (sys.argv[2], os.path.join(sys.argv[3], "cr")):
        if os.path.exists(os.path.join(base, slug)):
            print(os.path.join(base, slug))
PY
)
[ -z "$leaked" ] && pass "dropped (gated) posts are absent from content/cr and the build" || fail "gated post published: $leaked"

# c. nothing references a Substack-hosted asset
hosted=$(grep -rIEl 'substackcdn|substack-post-media|bucketeer-|substack-video\.s3' "$PUBLIC/cr" "$CONTENT" 2>/dev/null || true)
[ -z "$hosted" ] && pass "no Substack-hosted asset referenced under content/cr or the built /cr/" || fail "Substack-hosted asset referenced in: $(echo "$hosted" | tr '\n' ' ')"

# d. every body is inert: no active content, no stray classes
bad=$(python3 -I - "$CONTENT" <<'PY'
import glob, os, re, sys
from html.parser import HTMLParser

FORBIDDEN = {"script", "style", "iframe", "form", "input", "button", "svg", "object", "embed", "video", "audio", "source"}


class Body(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.problems = []

    def handle_starttag(self, tag, attrs):
        if tag in FORBIDDEN:
            self.problems.append(f"<{tag}>")
        for k, v in attrs:
            if k.lower().startswith("on"):
                self.problems.append(f"{k}= on <{tag}>")
            if k.lower() in ("href", "src") and (v or "").strip().lower().startswith(("javascript:", "data:")):
                self.problems.append(f"{k}={v[:20]}")
            if k.lower() == "class" and (v or "").strip() != "cr-footnote":
                self.problems.append(f"class={v}")

    handle_startendtag = handle_starttag


for path in sorted(glob.glob(os.path.join(sys.argv[1], "*", "index.html"))):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"\A---\n.*?\n---\n", text, re.S)
    p = Body()
    p.feed(text[m.end():] if m else text)
    if p.problems:
        print(f"{os.path.relpath(path, sys.argv[1])}: {sorted(set(p.problems))[:5]}")
PY
)
[ -z "$bad" ] && pass "every body is sanitized (no active content, no class but cr-footnote)" || { fail "unsafe body markup:"; echo "$bad" | sed 's/^/        /'; }

# e. every root-relative img src in a built CR page resolves to a file in the build
broken=$(python3 -I - "$PUBLIC" <<'PY'
import glob, os, sys
from html.parser import HTMLParser

public = sys.argv[1]


class Imgs(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.srcs = []

    def handle_starttag(self, tag, attrs):
        if tag == "img":
            for k, v in attrs:
                if k == "src" and v and v.startswith("/"):
                    self.srcs.append(v)

    handle_startendtag = handle_starttag


for page in sorted(glob.glob(os.path.join(public, "cr", "*", "index.html"))):
    p = Imgs()
    p.feed(open(page, encoding="utf-8").read())
    for src in p.srcs:
        if not os.path.isfile(os.path.join(public, src.split("?")[0].lstrip("/"))):
            print(f"{os.path.relpath(page, public)} → {src}")
PY
)
[ -z "$broken" ] && pass "every local img src on a /cr/ page resolves to a file in the build" || { fail "unresolved img src:"; echo "$broken" | sed 's/^/        /'; }

# f. podcast pages carry the (pending) player notice and a media_url key; newsletters never do
player=$(python3 -I - "$CONTENT" "$PUBLIC" <<'PY'
import glob, os, re, sys
from html.parser import HTMLParser

content, public = sys.argv[1], sys.argv[2]


class Player(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = False

    def handle_starttag(self, tag, attrs):
        if any(k == "data-cr-player" for k, _ in attrs):
            self.found = True


for path in sorted(glob.glob(os.path.join(content, "*", "index.html"))):
    slug = os.path.basename(os.path.dirname(path))
    fm = re.match(r"\A---\n(.*?)\n---\n", open(path, encoding="utf-8").read(), re.S)
    fm = fm.group(1) if fm else ""
    podcast = re.search(r'^cr_kind: "podcast"$', fm, re.M) is not None
    built = os.path.join(public, "cr", slug, "index.html")
    if not os.path.isfile(built):
        continue
    p = Player()
    p.feed(open(built, encoding="utf-8").read())
    if podcast and not p.found:
        print(f"{slug}: podcast page has no data-cr-player")
    if podcast and not re.search(r"^media_url:", fm, re.M):
        print(f"{slug}: podcast front matter has no media_url key")
    if not podcast and p.found:
        print(f"{slug}: newsletter page renders data-cr-player")
PY
)
[ -z "$player" ] && pass "podcast pages show the player notice and carry media_url; newsletters do not" || { fail "player check:"; echo "$player" | sed 's/^/        /'; }

# g. full mode only: counts and the feed
if [ -z "$PARTIAL" ]; then
  counts=$(python3 -I -c 'import json,sys; d=json.load(open(sys.argv[1])); print(len(d["posts"]), len(d["dropped"]))' "$LEGACY")
  [ "$counts" = "51 2" ] && pass "data/cr-legacy.json lists 51 posts and 2 dropped" || fail "data/cr-legacy.json counts are '$counts', want '51 2'"
  feed="$PUBLIC/cr/index.xml"
  if [ -f "$feed" ] && grep -q "<content:encoded>" "$feed"; then
    pass "full-content RSS at /cr/index.xml"
  else
    fail "/cr/index.xml missing or has no full-content items"
  fi
  if [ -f "$feed" ] && ! grep -Eq "(src|href)=[\"']?/[^/\"' >]" "$feed"; then
    pass "feed bodies use absolute URLs only"
  else
    fail "feed holds root-relative src/href values (or is missing)"
  fi
fi

# h. head metadata: article OG tags with an image, and the publication's own <title>
no_og=0
bad_title=0
for slug in $slugs; do
  page="$PUBLIC/cr/$slug/index.html"
  [ -f "$page" ] || continue
  grep -Eq 'property="?og:type"? content="?article' "$page" && grep -Eq 'property="?og:image"?' "$page" || { no_og=$((no_og + 1)); echo "        no article OG: /cr/$slug/"; }
  grep -Eq '<title>[^<]*\| Contemplating Resonance</title>' "$page" || { bad_title=$((bad_title + 1)); echo "        bad <title>: /cr/$slug/"; }
done
[ "$no_og" -eq 0 ] && pass "every CR post has article Open Graph tags with an image" || fail "$no_og CR posts missing article OG tags"
[ "$bad_title" -eq 0 ] && pass "every CR post title ends with | Contemplating Resonance" || fail "$bad_title CR posts with the wrong <title>"

# i. Pre-cutover: /cr/ is unlinked — delete this block on cutover day.
# Nothing outside /cr/ may link into it: every built page outside /cr/ is parsed, and any a href
# that resolves into /cr/ (relative, root-relative or absolute falkensmage.com) fails. The home
# page may not mention /cr/ at all.
inbound=$(python3 -I - "$PUBLIC" <<'PY'
import os, sys
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

public = sys.argv[1]


class Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.hrefs = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            for k, v in attrs:
                if k == "href" and v:
                    self.hrefs.append(v)


for dirpath, dirs, files in os.walk(public):
    rel_dir = os.path.relpath(dirpath, public)
    if rel_dir == "cr" or rel_dir.startswith("cr" + os.sep):
        dirs[:] = []
        continue
    for name in files:
        if not name.endswith(".html"):
            continue
        path = os.path.join(dirpath, name)
        rel = os.path.relpath(path, public)
        base = "https://falkensmage.com/" + (rel[: -len(name)] if rel != name else "")
        text = open(path, encoding="utf-8", errors="replace").read()
        p = Links()
        p.feed(text)
        for href in p.hrefs:
            u = urlsplit(urljoin(base, href))
            if u.netloc in ("falkensmage.com", "www.falkensmage.com") and (u.path == "/cr" or u.path.startswith("/cr/")):
                print(f"{rel} → {href}")
home = open(os.path.join(public, "index.html"), encoding="utf-8").read()
if "/cr/" in home:
    print("index.html mentions /cr/")
PY
)
[ -z "$inbound" ] && pass "pre-cutover: nothing outside /cr/ links into it" || { fail "pre-cutover: /cr/ is linked from outside:"; echo "$inbound" | sed 's/^/        /'; }

# j. INFO only: the sitemap and the home feed list /cr/ URLs once built. Both only go live on
# merge, which is cutover day per the FA precedent (OWN-THE-STACK-MIGRATION.md), so nothing extra
# is gated now. A sitemap opt-out, if ever wanted, is front matter `sitemap: {disable: true}`
# cascaded from content/cr/_index.md — deliberately not added.
for f in sitemap.xml index.xml; do
  if [ -f "$PUBLIC/$f" ]; then
    info "$f lists $(grep -o '/cr/' "$PUBLIC/$f" | wc -l | tr -d ' ') /cr/ occurrences (live only on merge)"
  fi
done

echo ""
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
