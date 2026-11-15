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
# It also gates the Apple/Spotify podcast feed (/cr/podcast.xml, block k): every episode keeps
# the guid it had on Substack, read from data/cr-podcast.json (CI cannot read ~/.psyche), so
# repointing the listings never duplicates an episode.
#
# VALIDATE_CR_NO_NET=1 skips the INFO-only R2 probe (k13) that HEADs each enclosure URL.
# VALIDATE_CR_PARTIAL=1 checks only the slugs that have a content/cr/<slug>/ bundle and skips
# the "all 51" and feed checks. VALIDATE_CR_PUBLIC=<dir> checks an existing build instead.

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARTIAL="${VALIDATE_CR_PARTIAL:-}"
LEGACY="$PROJECT_ROOT/data/cr-legacy.json"
CONTENT="$PROJECT_ROOT/content/cr"
PODCAST_PIN="$PROJECT_ROOT/data/cr-podcast.json"
PODCAST_ITEMS="${VALIDATE_CR_PODCAST_ITEMS:-$HOME/.psyche/tools/substack/cr-feed-assets/items.json}"

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
# Cut over 2026-11-15: the site nav links /cr/ on every page. Gate on that link being present
# on the home page; any other inbound links are fine now.
if grep -q 'href="/cr/"' "$PUBLIC/index.html" 2>/dev/null || grep -q 'href=/cr/' "$PUBLIC/index.html" 2>/dev/null; then
  pass "cutover: the site nav links to /cr/"
else
  fail "cutover: the home page has no nav link to /cr/"
fi

# j. INFO only: the sitemap and the home feed list /cr/ URLs once built. Both only go live on
# merge, which is cutover day per the FA precedent (OWN-THE-STACK-MIGRATION.md), so nothing extra
# is gated now. A sitemap opt-out, if ever wanted, is front matter `sitemap: {disable: true}`
# cascaded from content/cr/_index.md — deliberately not added.
for f in sitemap.xml index.xml; do
  if [ -f "$PUBLIC/$f" ]; then
    info "$f lists $(grep -o '/cr/' "$PUBLIC/$f" | wc -l | tr -d ' ') /cr/ occurrences (live only on merge)"
  fi
done

# k. the podcast feed (/cr/podcast.xml). Full mode only. One Python pass prints a line per problem,
# "k<n>: ..." (or "INFO: ..."); each check below passes when it has no problem lines.
if [ -z "$PARTIAL" ]; then
  kout=$(python3 -I - "$PUBLIC" "$CONTENT" "$PODCAST_PIN" "$PODCAST_ITEMS" <<'PY'
import glob, json, os, re, sys
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime

public, content, pin_path, items_path = sys.argv[1:5]
out = []


def bad(check, msg):
    out.append(f"{check}: {msg}")


NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd", "podcast": "https://podcastindex.org/namespace/1.0",
      "content": "http://purl.org/rss/1.0/modules/content/", "atom": "http://www.w3.org/2005/Atom"}
pin = json.load(open(pin_path, encoding="utf-8"))["episodes"]

# k1: exists, parses, RSS 2.0 with one channel, the only podcast.xml in the build
feeds = []
for d, _, files in os.walk(public):
    feeds += [os.path.join(d, f) for f in files if f == "podcast.xml"]
want = os.path.join(public, "cr", "podcast.xml")
root = channel = None
if feeds != [want]:
    bad("k1", f"podcast.xml files in the build: {[os.path.relpath(f, public) for f in feeds]}, want only cr/podcast.xml")
if os.path.isfile(want):
    try:
        root = ET.parse(want).getroot()
        if root.tag != "rss" or root.get("version") != "2.0":
            bad("k1", "root is not <rss version=\"2.0\">")
        chans = root.findall("channel")
        if len(chans) != 1:
            bad("k1", f"{len(chans)} channels, want 1")
        else:
            channel = chans[0]
    except ET.ParseError as e:
        bad("k1", f"does not parse: {e}")
if channel is None:
    print("\n".join(out)); sys.exit()

items = channel.findall("item")


def slug_of(it):
    m = re.match(r"^https://falkensmage\.com/cr/([a-z0-9-]+)/$", (it.findtext("link") or ""))
    return m.group(1) if m else None


# k2: item count = podcast bundles = pin = 18
bundles = []
for path in glob.glob(os.path.join(content, "*", "index.html")):
    fm = re.match(r"\A---\n(.*?)\n---\n", open(path, encoding="utf-8").read(), re.S)
    if fm and re.search(r'^cr_kind: "podcast"$', fm.group(1), re.M):
        bundles.append(os.path.basename(os.path.dirname(path)))
if not (len(items) == len(bundles) == len(pin) == 18):
    bad("k2", f"items={len(items)} podcast bundles={len(bundles)} pinned={len(pin)}, want all 18")

# k3: continuity of guids
seen, slugs = set(), []
for it in items:
    slug = slug_of(it)
    slugs.append(slug)
    g = it.find("guid")
    if slug not in pin:
        bad("k3", f"item link {it.findtext('link')!r} is not a pinned episode")
        continue
    if g is None or g.text != pin[slug]["guid"]:
        bad("k3", f"{slug}: guid {None if g is None else g.text!r} != pinned {pin[slug]['guid']!r}")
    if g is None or g.get("isPermaLink") != "false":
        bad("k3", f"{slug}: guid isPermaLink is not \"false\"")
    if g is not None and g.text in seen:
        bad("k3", f"{slug}: duplicate guid {g.text}")
    seen.add(g.text if g is not None else None)
if set(slugs) != set(pin):
    bad("k3", f"slug set differs from pin: {sorted(set(slugs) ^ set(pin))}")

# k4: pin vs the saved Substack facts, when readable
if os.path.isfile(items_path):
    src = json.load(open(items_path, encoding="utf-8"))
    if set(src) != set(pin):
        bad("k4", f"slug sets differ: {sorted(set(src) ^ set(pin))}")
    for slug, e in pin.items():
        s = src.get(slug)
        if s is None:
            continue
        got = (s.get("guid"), s.get("length"), s.get("explicit") == "Yes", bool(s.get("transcript")))
        have = (e["guid"], e["length"], e["explicit"], e["transcript"])
        if got != have:
            bad("k4", f"{slug}: items.json {got} != pin {have}")
else:
    out.append(f"INFO: k4 cross-check against {items_path} skipped (not readable here, e.g. CI)")

# k5 enclosures, k6 dates/duration/explicit
for it in items:
    slug = slug_of(it)
    enc = it.find("enclosure")
    pe = pin.get(slug)
    m = None
    if enc is None:
        bad("k5", f"{slug}: no enclosure")
    else:
        m = re.match(r"^https://media\.falkensmage\.com/cr/(\d{4}-\d{2}-\d{2})-" + re.escape(slug or "?") + r"\.mp3$", enc.get("url") or "")
        if not m:
            bad("k5", f"{slug}: enclosure url {enc.get('url')!r}")
        if enc.get("type") != "audio/mpeg":
            bad("k5", f"{slug}: enclosure type {enc.get('type')!r}")
        if pe and str(enc.get("length")) != str(pe["length"]):
            bad("k5", f"{slug}: enclosure length {enc.get('length')} != pinned {pe['length']}")
    try:
        d = parsedate_to_datetime(it.findtext("pubDate") or "").astimezone(timezone.utc).date().isoformat()
        if m and d != m.group(1):
            bad("k6", f"{slug}: pubDate date {d} != enclosure date {m.group(1)}")
    except (TypeError, ValueError):
        bad("k6", f"{slug}: pubDate {it.findtext('pubDate')!r} does not parse")
    dur = it.findtext("itunes:duration", namespaces=NS) or ""
    if not (dur.isdigit() and int(dur) > 0):
        bad("k6", f"{slug}: itunes:duration {dur!r}")
    if (it.findtext("itunes:explicit", namespaces=NS) or "") not in ("true", "false"):
        bad("k6", f"{slug}: itunes:explicit is not true/false")

# k7: the existing /cr/index.xml has no podcast markup
idx = os.path.join(public, "cr", "index.xml")
if not os.path.isfile(idx) or re.search(r"xmlns:(itunes|podcast)|<(itunes|podcast):", open(idx, encoding="utf-8").read(), re.I):
    bad("k7", "/cr/index.xml is missing or carries itunes/podcast markup")

# k8: channel metadata
def ct(tag):
    return channel.findtext(tag, namespaces=NS)


lede = re.search(r'^lede: (".*")$', open(os.path.join(content, "_index.md"), encoding="utf-8").read(), re.M)
lede = json.loads(lede.group(1)) if lede else None
for tag, exp in [("title", "Contemplating Resonance"), ("link", "https://falkensmage.com/cr/"), ("language", "en"),
                  ("copyright", "Digital Intuition LLC"), ("itunes:author", "Matt Stine"),
                  ("itunes:explicit", "true"), ("itunes:type", "episodic"), ("description", lede)]:
    if ct(tag) != exp:
        bad("k8", f"channel {tag} is {str(ct(tag))[:60]!r}, want {str(exp)[:60]!r}")
self_link = [a for a in channel.findall("atom:link", NS) if a.get("rel") == "self"]
if not (len(self_link) == 1 and self_link[0].get("href") == "https://falkensmage.com/cr/podcast.xml"
        and self_link[0].get("type") == "application/rss+xml"):
    bad("k8", "atom:link rel=self is not https://falkensmage.com/cr/podcast.xml")
if ct("itunes:owner/itunes:name") != "Matt Stine" or ct("itunes:owner/itunes:email") != "falkensmage@falkenslabyrinth.com":
    bad("k8", "itunes:owner is not Matt Stine / falkensmage@falkenslabyrinth.com")
cats = channel.findall("itunes:category", NS)
if not cats or cats[0].get("text") != "Society & Culture" or [c.get("text") for c in cats[0].findall("itunes:category", NS)] != ["Philosophy"]:
    bad("k8", "first itunes:category is not Society & Culture > Philosophy")

# k9: show art, a square JPEG of 1400-3000 px, self-hosted, inherited by every item
def jpeg_dims(b):
    i = 2
    while i + 9 < len(b):
        if b[i] != 0xFF:
            i += 1
            continue
        mk = b[i + 1]
        if mk in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(b[i + 7:i + 9], "big"), int.from_bytes(b[i + 5:i + 7], "big")
        i += 2 + int.from_bytes(b[i + 2:i + 4], "big")
    return None


img = channel.find("itunes:image", NS)
href = img.get("href") if img is not None else None
if href != "https://falkensmage.com/cr/podcast-cover.jpg":
    bad("k9", f"channel itunes:image href is {href!r}")
else:
    art = os.path.join(public, "cr", "podcast-cover.jpg")
    if not os.path.isfile(art):
        bad("k9", "cr/podcast-cover.jpg is not in the build")
    else:
        b = open(art, "rb").read()
        dims = jpeg_dims(b) if b[:3] == b"\xff\xd8\xff" else None
        if dims is None:
            bad("k9", "podcast-cover.jpg is not a JPEG")
        elif dims[0] != dims[1] or not 1400 <= dims[0] <= 3000:
            bad("k9", f"podcast-cover.jpg is {dims[0]}x{dims[1]}, want a square 1400-3000 px")

# k10: transcripts; no per-episode art (every item inherits the channel image)
n_tr = 0
for it in items:
    slug = slug_of(it)
    if it.find("itunes:image", NS) is not None:
        bad("k10", f"{slug}: per-episode itunes:image present (items must inherit the channel image)")
    for tr in it.findall("podcast:transcript", NS):
        n_tr += 1
        u = tr.get("url") or ""
        pre = f"https://falkensmage.com/cr/{slug}/"
        f = os.path.join(public, u[len("https://falkensmage.com/"):]) if u.startswith(pre) else None
        if tr.get("type") != "text/vtt" or not f or not os.path.isfile(f):
            bad("k10", f"{slug}: transcript {u!r} (type {tr.get('type')!r}) does not resolve in the build")
        elif not open(f, "rb").read().lstrip(b"\xef\xbb\xbf").startswith(b"WEBVTT"):
            bad("k10", f"{slug}: transcript does not start with WEBVTT")
want_tr = sum(1 for e in pin.values() if e["transcript"])
if n_tr != want_tr:
    bad("k10", f"{n_tr} podcast:transcript elements, pin says {want_tr}")

# k11: show notes present and absolute
for it in items:
    slug = slug_of(it)
    for tag in ("description", "content:encoded"):
        t = it.findtext(tag, namespaces=NS) or ""
        if not t.strip():
            bad("k11", f"{slug}: empty {tag}")
        elif re.search(r"(src|href)=[\x22\x27]?/[^/\x22\x27 >]", t):
            bad("k11", f"{slug}: {tag} holds a root-relative src/href")

# k12: nothing that depends on Substack
raw = open(want, encoding="utf-8").read()
for pat in [r"substackcdn", r"substack-post-media", r"bucketeer-", r"substack-video", r"api\.substack\.com",
            r"open\.substack\.com", r"//(www\.)?substack\.com", r"(falkenslabyrinth|contemplatingresonance)\.substack\.com",
            r"https?://(www\.)?falkenslabyrinth\.com", r"/Users/", r"mnemosyne"]:
    if re.search(pat, raw, re.I):
        bad("k12", f"podcast.xml matches /{pat}/")
guests = len(set(re.findall(r"https?://[a-z0-9-]+\.substack\.com", raw, re.I)))
out.append(f"INFO: podcast.xml links {guests} guest <name>.substack.com newsletters from show notes (outbound, allowed)")

out.append("DONE")
print("\n".join(out))
PY
)
  kcheck() { # kcheck <id> <pass text> <fail text>
    local lines
    lines=$(printf '%s\n' "$kout" | grep "^$1: " || true)
    if [ -z "$lines" ]; then pass "$2"; else fail "$3"; printf '%s\n' "$lines" | sed 's/^/        /'; fi
  }
  printf '%s\n' "$kout" | grep -qx 'DONE' || { fail "podcast feed checks crashed before finishing (a missing or malformed feed also lands here)"; printf '%s\n' "$kout" | sed 's/^/        /'; }
  kcheck k1 "podcast feed: /cr/podcast.xml is well-formed RSS 2.0, one channel, the only podcast.xml in the build" "podcast feed structure"
  kcheck k2 "podcast feed: 18 items = 18 podcast bundles = 18 pinned episodes" "podcast feed item count"
  kcheck k3 "podcast feed: every guid equals its pinned Substack guid, isPermaLink false, none repeated" "podcast guid continuity"
  kcheck k4 "podcast pin matches the saved Substack feed facts (guid, length, explicit, transcript)" "podcast pin differs from items.json"
  kcheck k5 "podcast feed: every enclosure is the R2 mp3 for its slug, audio/mpeg, pinned length" "podcast enclosures"
  kcheck k6 "podcast feed: pubDate = enclosure date, duration positive, explicit true/false" "podcast item dates/duration/explicit"
  kcheck k7 "/cr/index.xml carries no itunes/podcast markup" "/cr/index.xml changed shape"
  kcheck k8 "podcast feed: channel metadata (title, link, self, author, owner, explicit, type, category, lede)" "podcast channel metadata"
  kcheck k9 "podcast feed: show art is a self-hosted square JPEG, 1400-3000 px" "podcast show art"
  kcheck k10 "podcast feed: transcripts resolve as WEBVTT; no per-episode art (items inherit the channel image)" "podcast transcripts / episode art"
  kcheck k11 "podcast feed: every item has show notes in description and content:encoded, absolute URLs" "podcast show notes"
  kcheck k12 "podcast feed: no Substack infrastructure, own-publication URL, or local path" "podcast feed depends on Substack"
  printf '%s\n' "$kout" | grep '^INFO: ' | sed 's/^INFO: //' | while IFS= read -r l; do info "$l"; done
  # k13. INFO only, never FAIL: HEAD each enclosure on R2 (the upload is out of band; the feed is
  # correct either way). One request per URL, no retries.
  if [ -n "${VALIDATE_CR_NO_NET:-}" ]; then
    info "k13 R2 probe skipped (VALIDATE_CR_NO_NET set)"
  elif ! command -v curl >/dev/null 2>&1; then
    info "k13 R2 probe skipped (curl not found)"
  else
    probe_ok=0; probe_len=0; probe_total=0; probe_lines=""; probe_net_down=0
    while IFS="$(printf '\t')" read -r url want_len; do
      [ -n "$url" ] || continue
      probe_total=$((probe_total + 1))
      res=$(curl -sIL -o /dev/null --max-time 10 -w '%{http_code} %{size_download} %header{content-length}' "$url" 2>/dev/null) || res="000 0 "
      code=${res%% *}
      clen=$(printf '%s' "$res" | awk '{print $3}')
      [ "$code" = "000" ] && probe_net_down=$((probe_net_down + 1))
      [ "$code" = "200" ] && probe_ok=$((probe_ok + 1))
      [ "$code" = "200" ] && [ "$clen" = "$want_len" ] && probe_len=$((probe_len + 1))
      if [ "$code" != "200" ] || [ "$clen" != "$want_len" ]; then
        probe_lines="$probe_lines
$url: status $code, content-length ${clen:-none}, want $want_len"
      fi
    done <<EOF_URLS
$(python3 -I - "$PUBLIC/cr/podcast.xml" <<'PY'
import sys
import xml.etree.ElementTree as ET
for it in ET.parse(sys.argv[1]).getroot().find("channel").findall("item"):
    e = it.find("enclosure")
    print(f"{e.get('url')}\t{e.get('length')}")
PY
)
EOF_URLS
    if [ "$probe_total" -gt 0 ] && [ "$probe_net_down" -eq "$probe_total" ]; then
      info "k13 R2 probe skipped (network unreachable)"
    else
      info "k13 R2 probe: $probe_ok/$probe_total enclosures answered 200, $probe_len/$probe_total with the pinned Content-Length"
      printf '%s\n' "$probe_lines" | grep . | while IFS= read -r l; do info "k13 $l"; done
    fi
  fi

fi

echo ""
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
