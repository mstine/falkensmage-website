#!/usr/bin/env python3
"""sync-cr.py — one-way sync of the Contemplating Resonance archive into content/cr/.

The Substack publication (falkenslabyrinth.com) is the source. This script reads the
saved archive listing (~/.psyche/tools/substack/cr-archive.json), fetches each public
post's body once through the publication's own JSON API, and regenerates
content/cr/<slug>/ page bundles from scratch. Every run rewrites the bundles it owns,
so a hand edit under content/cr/<slug>/ is overwritten, loudly, next run (design
principle 10: maintenance never returns to the failing substrate). content/cr/_index.md
is hand-authored and never touched.

Why bundles hold index.html, not index.md: Substack hands back HTML. Converting it to
markdown loses figures, captions and footnote anchors, and rendering it through goldmark
would need the global `unsafe` switch. Hugo's HTML content format passes the body through
`.Content` untouched, so the sanitizer in this file is the only thing standing between
remote markup and the page, and tests/validate-cr.sh re-checks its output.

Why every image is self-hosted: the site constraint is no external dependencies, and the
whole point of the migration is that the archive keeps working when the Substack does not.
Substack's fetch CDN, its post-media bucket and its legacy buckets are all resolved to the
original, downloaded, and written into the bundle (cover.jpg, img-NN.ext).

Slugs are kept byte-for-byte, so the later redirect is a pure /p/<slug> to /cr/<slug>
swap. Two August-2024 posts are gated (founding / paid) and are excluded by name; any
other non-public post in the listing aborts the run rather than being published.

Network etiquette: every live request to a Substack host sleeps 3 seconds first. Post
JSON and image bytes are cached under ~/.cache/sync-cr (outside the repo), so --offline
reruns make no network calls at all and reproduce the output byte for byte. The cookie
file is read only when --cookie-file is passed and is never printed, cached or committed.

Usage: python3 scripts/sync-cr.py [--listing FILE] [--cache DIR] [--only SLUG ...]
                                  [--fetch-only] [--offline] [--refresh] [--cookie-file FILE]
Exit 1 if any kept post fails to produce a bundle.
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

try:
    from bs4 import BeautifulSoup, NavigableString, Tag
except ImportError:
    sys.exit("sync-cr: beautifulsoup4 is required (python3 -c 'import bs4' fails). Not installing anything.")

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "cr"
FA_OUT = ROOT / "content" / "fa"
LEGACY = ROOT / "data" / "cr-legacy.json"

# The two gated August-2024 posts. Excluded by name; anything else gated aborts the run.
DROPPED = ["your-august-2024-contemplative-alchemist", "your-august-2024-paid-member-discount"]
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
API = "https://falkenslabyrinth.com/api/v1/posts/{slug}"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
THROTTLE = 3  # seconds before every live request
MAX_EDGE = 1600

# Substack-hosted image: the fetch CDN, the post-media bucket, legacy bucketeer buckets,
# or a *.substack.com image path.
SUBSTACK_IMG_RE = re.compile(
    r"^https?://(?:substackcdn\.com/|substack-post-media\.s3[.\-a-z0-9]*\.amazonaws\.com/|"
    r"bucketeer-[a-z0-9\-]+\.s3[.\-a-z0-9]*\.amazonaws\.com/|[a-z0-9\-]+\.substack\.com/)", re.I)


class Net:
    """One place that touches the network. Sleeps THROTTLE seconds before every live call."""

    def __init__(self, cache, offline, cookie_file):
        self.cache, self.offline = cache, offline
        self.cookie = None
        if cookie_file:
            self.cookie = Path(cookie_file).expanduser().read_text().strip().replace("\n", "")
        self.live = 0
        for sub in ("posts", "img", "processed"):
            (cache / sub).mkdir(parents=True, exist_ok=True)

    def _get(self, url, accept, what):
        if self.offline:
            raise RuntimeError(f"offline cache miss: {what}")
        time.sleep(THROTTLE)
        headers = {"user-agent": UA, "accept": accept}
        if self.cookie:
            headers["cookie"] = self.cookie
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=60) as r:
                data = r.read()
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"{what}: HTTP {e.code}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise RuntimeError(f"{what}: {type(e).__name__}") from None
        self.live += 1
        return data

    def post(self, slug, refresh):
        path = self.cache / "posts" / f"{slug}.json"
        if path.is_file() and not refresh:
            data = json.loads(path.read_text(encoding="utf-8"))
        else:
            raw = self._get(API.format(slug=slug), "application/json", f"post JSON for {slug}")
            try:
                data = json.loads(raw)
            except ValueError:
                raise RuntimeError(f"post JSON for {slug}: not JSON") from None
        if not isinstance(data, dict) or not data.get("body_html"):
            raise RuntimeError(f"post JSON for {slug}: no body_html")
        if data.get("audience") != "everyone":
            raise RuntimeError(f"post JSON for {slug}: audience is {data.get('audience')!r}, refusing")
        if not path.is_file() or refresh:
            path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data

    def image(self, url):
        """Bytes of an image URL, cached by sha1 of the URL. Only JPEG/PNG/GIF/WebP accepted."""
        path = self.cache / "img" / hashlib.sha1(url.encode()).hexdigest()
        if path.is_file():
            data = path.read_bytes()
        else:
            data = self._get(url, "image/*", "image fetch")
            if sniff(data) is None:
                raise RuntimeError("image fetch: not a JPEG/PNG/GIF/WebP")
            path.write_bytes(data)
        if sniff(data) is None:
            raise RuntimeError("image fetch: cached bytes are not a JPEG/PNG/GIF/WebP")
        return path


def sniff(data):
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def load_listing(path):
    posts = json.loads(Path(path).expanduser().read_text(encoding="utf-8"))
    bad = [p.get("slug") for p in posts if not SLUG_RE.match(p.get("slug") or "")]
    if bad:
        sys.exit(f"sync-cr: slugs failing ^[a-z0-9-]+$: {bad}")
    gated = {p["slug"] for p in posts if p.get("audience") != "everyone"}
    if gated != set(DROPPED):
        sys.exit(f"sync-cr: gated posts in listing {sorted(gated)} != expected dropped {sorted(DROPPED)}; "
                 "refusing to publish or drop anything unexpected")
    dropped = [p["slug"] for p in posts if p["slug"] in DROPPED]
    kept = [p for p in posts if p["slug"] not in DROPPED]
    kept.sort(key=lambda p: p["post_date"], reverse=True)
    return kept, dropped


def write_legacy(kept, dropped):
    data = {
        "_comment": "Every /p/<slug> live on falkenslabyrinth.com (Substack archive listing). 'posts' must resolve "
                    "to /cr/<slug>/; 'dropped' are the gated August-2024 posts, never published. Written by "
                    "scripts/sync-cr.py; tests/validate-cr.sh reads it because CI cannot read ~/.psyche.",
        "posts": [p["slug"] for p in kept],
        "dropped": dropped,
    }
    LEGACY.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


# ---------------------------------------------------------------------------
# Image handling
# ---------------------------------------------------------------------------

def is_substack_img(url):
    return bool(url and (SUBSTACK_IMG_RE.match(url) or re.match(r"^https?://substack-video\.s3[.\-a-z0-9]*\.amazonaws\.com/", url, re.I)))


def original_url(url):
    """The original behind a substackcdn fetch URL (percent-encoded or bare tail); else url itself."""
    if url and "substackcdn.com/image/fetch/" in url:
        rest = url.split("/image/fetch/", 1)[1]
        m = re.search(r"(https?%3A%2F%2F.*|https?://.*)$", rest, re.I)
        if m:
            return urllib.parse.unquote(m.group(1))
    return url


def data_attrs(tag):
    raw = tag.get("data-attrs")
    if not raw:
        return {}
    try:
        d = json.loads(raw)
    except ValueError:
        return {}
    return d if isinstance(d, dict) else {}


def sips_dims(path):
    r = subprocess.run(["sips", "-g", "pixelWidth", "-g", "pixelHeight", str(path)], capture_output=True, text=True)
    w = re.search(r"pixelWidth:\s*(\d+)", r.stdout)
    h = re.search(r"pixelHeight:\s*(\d+)", r.stdout)
    if r.returncode != 0 or not (w and h):
        raise RuntimeError("sips could not read image dimensions")
    return int(w.group(1)), int(h.group(1))


def process(net, urls, variant):
    """Fetch the first working URL of `urls`, process it, return (cached processed path, ext).

    variant "cover" always yields a JPEG; "inline" keeps GIF verbatim, PNG as PNG (alpha), else JPEG.
    Processed output is cached by the sha1 of the URL so reruns are byte-identical.
    """
    last = None
    for url in urls:
        if not url:
            continue
        try:
            raw = net.image(url)
        except RuntimeError as e:
            last = e
            continue
        kind = sniff(raw.read_bytes())
        if variant == "cover":
            kind_out = "jpg"
        else:
            kind_out = kind if kind in ("gif", "png") else "jpg"
        out = net.cache / "processed" / f"{hashlib.sha1(url.encode()).hexdigest()}-{variant}.{kind_out}"
        if not out.is_file():
            if kind_out == "gif":
                shutil.copyfile(raw, out)
            else:
                w, h = sips_dims(raw)
                cmd = ["sips"]
                if kind_out == "jpg":
                    cmd += ["-s", "format", "jpeg", "-s", "formatOptions", "82"]
                if max(w, h) > MAX_EDGE:
                    cmd += ["-Z", str(MAX_EDGE)]
                if kind_out == "png" and max(w, h) <= MAX_EDGE:
                    shutil.copyfile(raw, out)
                else:
                    r = subprocess.run(cmd + [str(raw), "--out", str(out)], capture_output=True, text=True)
                    if r.returncode != 0 or not out.is_file():
                        raise RuntimeError(f"sips failed: {r.stderr.strip()[:120]}")
        return out, kind_out
    raise last or RuntimeError("no image URL")


# ---------------------------------------------------------------------------
# Body sanitizer
# ---------------------------------------------------------------------------

REMOVE_CLASS_PREFIX = ("subscription-widget", "captioned-button-wrap", "button-wrapper", "paywall-jump",
                       "install-substack-app", "image-link-expand", "hide-text")
REMOVE_TAGS = {"svg", "script", "style", "form", "input", "button", "noscript", "object", "embed",
               "video", "audio", "source", "link", "meta", "canvas", "textarea", "select"}
ALLOWED_TAGS = {"p", "h2", "h3", "h4", "h5", "h6", "a", "strong", "b", "em", "i", "u", "s", "sup", "sub", "br",
                "hr", "ul", "ol", "li", "blockquote", "figure", "figcaption", "img", "pre", "code", "table",
                "thead", "tbody", "tr", "th", "td", "div"}
BARE_CTA = {"subscribe", "subscribe now", "share", "leave a comment", "share this post", "give a gift subscription"}
CR_HOSTS = {"falkenslabyrinth.com", "www.falkenslabyrinth.com", "falkenslabyrinth.substack.com",
            "contemplatingresonance.com", "www.contemplatingresonance.com"}
FA_HOSTS = {"feralarchitecture.com", "www.feralarchitecture.com", "feralarchitecture.substack.com"}
# Classes that mean "decorative wrapper, nothing lost by unwrapping"; everything else prints a WARN.
BENIGN_CLASSES = {"image2-inset", "image-link", "image2", "is-viewable-img", "sizing-normal", "footnote-content",
                  "table-wrap", "paragraph", "preformatted", "header-anchor-parent", "header-anchor-post",
                  "pencraft", "pc-display-flex", "pc-reset", "footnote-number", "digest-post-embed", "text", "preformatted-block",
                  "button", "primary", "email-input"}


class Ctx:
    def __init__(self, slug, net, bundle, kept, fa_slugs):
        self.slug, self.net, self.bundle, self.kept, self.fa_slugs = slug, net, bundle, kept, fa_slugs
        self.warns = []
        self.classes = Counter()
        self.images = 0
        self.names = {}  # original URL -> bundle file name

    def warn(self, msg):
        self.warns.append(f"{self.slug}: {msg}")

    def note_class(self, tag, why):
        for c in tag.get("class") or []:
            if c not in BENIGN_CLASSES:
                self.classes[(c, why)] += 1


def classes_of(tag):
    return tag.get("class") or [] if isinstance(tag, Tag) else []


def new_tag(soup, name, **attrs):
    t = soup.new_tag(name)
    for k, v in attrs.items():
        t[k.replace("_", "-")] = v
    return t


def link_p(soup, href, text):
    p = soup.new_tag("p")
    a = soup.new_tag("a", href=href)
    a.string = text
    p.append(a)
    return p


def prep_images(soup, ctx):
    """Record each image's original URL(s) while data-attrs still exists; drop srcset/picture."""
    for pic in soup.find_all("picture"):
        img = pic.find("img")
        if img:
            pic.replace_with(img.extract())
        else:
            pic.decompose()
    for img in soup.find_all("img"):
        da = data_attrs(img)
        src = (img.get("src") or "").strip()
        if src.startswith("data:") or not src:
            ctx.warn("dropped inline data: / empty image")
            img.decompose()
            continue
        primary = da.get("src") or original_url(src)
        if is_substack_img(primary) or is_substack_img(src):
            img["data-orig"] = original_url(primary)
            img["data-fb"] = src
        elif src.startswith(("http://", "https://")):
            # Not Substack-hosted (Unsplash stock photos, mostly). Self-hosted all the same: the
            # page must not depend on anyone else's server. If the fetch fails the hotlink stays.
            img["data-orig"] = src
            img["data-fb"] = src
            img["data-ext"] = urllib.parse.urlsplit(src).netloc
        else:
            ctx.warn(f"dropped image with unusable src {src[:60]!r}")
            img.decompose()
            continue
        if not img.get("alt") and da.get("alt"):
            img["alt"] = da["alt"]


def spotify_text(da, src):
    title = (da.get("title") or "").strip()
    sub = (da.get("subtitle") or "").strip()
    if title and sub:
        return f"{title} — {sub} (Spotify)"
    return f"{title or 'Listen'} (Spotify)"


def convert_embeds(soup, ctx):
    for tag in soup.find_all("div", class_="youtube-wrap"):
        da = data_attrs(tag)
        vid = da.get("videoId")
        if not vid:
            ifr = tag.find("iframe")
            m = re.search(r"youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]+)", (ifr.get("src") if ifr else "") or "")
            vid = m.group(1) if m else ""
        if vid:
            tag.replace_with(link_p(soup, f"https://www.youtube.com/watch?v={vid}", "Watch on YouTube"))
        else:
            ctx.warn("youtube-wrap with no video id removed")
            tag.decompose()
    # A @-mention is its author's name as plain text.
    for tag in soup.find_all(class_="mention-wrap"):
        name = (data_attrs(tag).get("name") or "").strip()
        tag.replace_with(NavigableString(name)) if name else tag.decompose()
    # Publication recommendation cards become one link.
    for tag in soup.find_all("div", class_="embedded-publication-wrap"):
        da = data_attrs(tag)
        base = (da.get("base_url") or "").strip()
        name = (da.get("name") or "").strip()
        by = (da.get("author_name") or "").strip()
        if base.startswith(("http://", "https://")) and name:
            tag.replace_with(link_p(soup, base, f"{name} — {by}" if by else name))
        else:
            ctx.warn("embedded-publication card with no URL removed")
            tag.decompose()
    # Image galleries become one figure per image, the gallery caption on the last.
    for tag in soup.find_all("div", class_="image-gallery-embed"):
        g = data_attrs(tag).get("gallery") or {}
        figs = []
        for im in g.get("images") or []:
            if im.get("src"):
                fig = soup.new_tag("figure")
                fig.append(soup.new_tag("img", src=im["src"], alt=g.get("alt") or ""))
                figs.append(fig)
        if not figs:
            ctx.warn("image-gallery-embed with no images removed")
            tag.decompose()
            continue
        if g.get("caption"):
            fc = soup.new_tag("figcaption")
            fc.string = g["caption"]
            figs[-1].append(fc)
        for fig in figs:
            tag.insert_before(fig)
        tag.decompose()
    for tag in soup.find_all("iframe"):
        if getattr(tag, "decomposed", False):
            continue
        cls = classes_of(tag)
        da = data_attrs(tag)
        src = tag.get("src") or ""
        if "spotify-wrap" in cls and da.get("url"):
            tag.replace_with(link_p(soup, da["url"], spotify_text(da, src)))
            continue
        parent_cls = classes_of(tag.parent) if tag.parent else []
        yt = re.search(r"youtube(?:-nocookie)?\.com/embed/([A-Za-z0-9_-]+)", src)
        if yt or "youtube-wrap" in parent_cls:
            vid = yt.group(1) if yt else (data_attrs(tag.parent).get("videoId") or "")
            target = tag.parent if "youtube-wrap" in parent_cls else tag
            if vid:
                target.replace_with(link_p(soup, f"https://www.youtube.com/watch?v={vid}", "Watch on YouTube"))
                continue
        if src.startswith(("http://", "https://")):
            ctx.warn(f"iframe embed became a link: {src[:80]}")
            tag.replace_with(link_p(soup, src, src))
        else:
            ctx.warn("iframe with no usable src removed")
            tag.decompose()
    for tag in soup.find_all("div"):
        if getattr(tag, "decomposed", False):
            continue
        cls = classes_of(tag)
        if "digest-post-embed" in cls or "embedded-post-wrap" in cls or "embedded-post" in cls:
            da = data_attrs(tag)
            url = da.get("canonical_url") or da.get("url") or ""
            if not url:
                a = tag.find("a", href=True)
                url = a["href"] if a else ""
            title = da.get("title") or (tag.get_text(" ", strip=True)[:120])
            if url:
                tag.replace_with(link_p(soup, url, title or url))
            else:
                ctx.warn(f"embedded-post card with no URL removed ({title[:50]!r})")
                tag.decompose()


def convert_structure(soup, ctx):
    for tag in list(soup.find_all(True)):
        if getattr(tag, "decomposed", False):
            continue
        cls = classes_of(tag)
        if tag.name in REMOVE_TAGS or any(c.startswith(REMOVE_CLASS_PREFIX) for c in cls):
            tag.decompose()
    for p in soup.find_all("p"):
        if getattr(p, "decomposed", False):
            continue
        txt = " ".join(p.get_text(" ", strip=True).split()).lower().rstrip(".!")
        if txt.startswith("thanks for reading") or txt in BARE_CTA:
            p.decompose()
    # captioned images → figure + img + figcaption
    for box in soup.find_all("div", class_="captioned-image-container"):
        if getattr(box, "decomposed", False):
            continue
        img = box.find("img")
        cap = box.find("figcaption")
        if not img:
            box.decompose()
            continue
        fig = soup.new_tag("figure")
        fig.append(img.extract())
        if cap and cap.get_text(strip=True):
            fc = soup.new_tag("figcaption")
            for child in list(cap.children):
                fc.append(child.extract())
            fig.append(fc)
        box.replace_with(fig)
    # remaining image-link anchors: unwrap when they just point at an image
    for a in soup.find_all("a", class_="image-link"):
        href = (a.get("href") or "")
        if not href or is_substack_img(href) or re.search(r"\.(?:jpe?g|png|gif|webp)(?:\?|$)", href, re.I):
            a.unwrap()
    for q in soup.find_all(class_="pullquote"):
        q.name = "blockquote"
        q.attrs = {}
    for a in soup.find_all("a", class_="footnote-anchor"):
        sup = soup.new_tag("sup")
        a.replace_with(sup)
        sup.append(a)
    for note in soup.find_all("div", class_="footnote"):
        box = soup.new_tag("div")
        box["class"] = ["cr-footnote"]
        num = note.find("a", class_="footnote-number")
        content = note.find("div", class_="footnote-content")
        if num:
            num.attrs = {k: v for k, v in num.attrs.items() if k in ("href", "id")}
            box.append(num.extract())
        for child in list((content or note).children):
            box.append(child.extract())
        note.replace_with(box)
    for h in soup.find_all("h1"):
        h.name = "h2"
    # Anything left carrying data-attrs that is a div/p widget we have no rule for.
    for tag in soup.find_all(["div", "p", "span"]):
        if getattr(tag, "decomposed", False):
            continue
        if tag.get("data-attrs") and not tag.find("img"):
            ctx.warn(f"unrecognized embed removed: class={' '.join(classes_of(tag)) or tag.get('data-component-name')}")
            tag.decompose()
    for tag in list(soup.find_all(True)):
        if getattr(tag, "decomposed", False) or tag.name not in ("div", "span", "section", "article", "font", "center", "main", "header", "footer", "aside", "nav"):
            continue
        if tag.name == "div" and classes_of(tag) == ["cr-footnote"]:
            continue
        ctx.note_class(tag, f"{tag.name} unwrapped")
        tag.unwrap()


def rewrite_link(a, ctx):
    """Returns the new href, or None to unwrap."""
    href = (a.get("href") or "").strip()
    if not href:
        return None if not a.get("id") else ""
    if href.startswith("#"):
        return href
    sp = urllib.parse.urlsplit(href)
    if sp.scheme.lower() in ("javascript", "data", "vbscript"):
        return None
    if sp.scheme.lower() not in ("http", "https", "mailto", "tel", ""):
        return None
    host = sp.netloc.lower()
    path = sp.path or "/"
    frag = f"#{sp.fragment}" if sp.fragment else ""
    query = urllib.parse.parse_qs(sp.query)
    is_cr = host in CR_HOSTS
    if host == "open.substack.com" and path.startswith("/pub/falkenslabyrinth"):
        is_cr = True
        path = path[len("/pub/falkenslabyrinth"):] or "/"
    if is_cr:
        m = re.match(r"^/p/([^/]+)(/.*)?$", path)
        if m:
            slug, extra = m.group(1), m.group(2) or ""
            if extra.startswith("/comments") or "share" in query.get("action", []) or slug in DROPPED:
                return None
            if slug not in ctx.kept:
                ctx.warn(f"link to unknown CR slug /p/{slug} (left pointing at /cr/{slug}/)")
            return f"/cr/{slug}/{frag}"
        if path.rstrip("/") in ("", "/archive", "/podcast"):
            return f"/cr/{frag}"
        ctx.warn(f"unlinked falkenslabyrinth path {path}")
        return None
    if host in FA_HOSTS:
        m = re.match(r"^/p/([^/]+)/?$", path)
        if m and m.group(1) in ctx.fa_slugs:
            return f"/fa/{m.group(1)}/{frag}"
        if path.rstrip("/") == "":
            return f"/fa/{frag}"
    return href


def sanitize_body(html, slug, ctx, cover_orig=None):
    """Raw Substack body_html → inert, self-hosted HTML (one top-level block per line)."""
    soup = BeautifulSoup(html, "html.parser")
    convert_embeds(soup, ctx)
    prep_images(soup, ctx)
    convert_structure(soup, ctx)

    for a in list(soup.find_all("a")):
        new = rewrite_link(a, ctx)
        if new is None:
            a.unwrap()
        elif new == "":
            del a["href"]
        else:
            a["href"] = new

    # Normalize top level: bare inline runs become paragraphs.
    top = []
    run = []

    def flush():
        if run and any((isinstance(n, Tag) or n.strip()) for n in run):
            p = soup.new_tag("p")
            for n in run:
                p.append(n)
            top.append(p)
        run.clear()

    BLOCK = {"p", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote", "figure", "pre", "table", "hr", "div"}
    for node in list(soup.contents):
        node = node.extract()
        if isinstance(node, Tag) and node.name in BLOCK:
            flush()
            top.append(node)
        else:
            run.append(node)
    flush()
    soup = BeautifulSoup("", "html.parser")
    for node in top:
        soup.append(node)

    # Empty paragraphs, doubled / leading / trailing rules.
    blocks = []
    for node in list(soup.contents):
        if node.name == "p" and not node.get_text(strip=True) and not node.find("img"):
            continue
        if node.name == "hr" and (not blocks or blocks[-1].name == "hr"):
            continue
        blocks.append(node)
    while blocks and blocks[-1].name == "hr":
        blocks.pop()

    # Leading duplicate of the cover.
    if blocks and cover_orig:
        first = blocks[0]
        img = first.find("img") if first.name in ("figure", "p") else None
        only_img = img is not None and not first.find("figcaption") and not first.get_text(strip=True)
        if only_img and img.get("data-orig") and img["data-orig"] == cover_orig:
            blocks = blocks[1:]
            while blocks and blocks[0].name == "hr":
                blocks = blocks[1:]

    soup = BeautifulSoup("", "html.parser")
    for node in blocks:
        soup.append(node)

    # Localize images in document order.
    for img in soup.find_all("img"):
        orig = img["data-orig"]
        if orig in ctx.names:
            name, w, h = ctx.names[orig]
        else:
            try:
                out, ext = process(ctx.net, [orig, img.get("data-fb")], "inline")
            except RuntimeError as e:
                if not img.get("data-ext"):
                    raise
                ctx.warn(f"non-Substack image host {img['data-ext']} left in place ({e})")
                img.attrs = {"src": img["data-fb"], "alt": img.get("alt", ""), "loading": "lazy"}
                continue
            ctx.images += 1
            if img.get("data-ext"):
                ctx.warn(f"non-Substack image host {img['data-ext']} localized")
            name = f"img-{ctx.images:02d}.{ext}"
            shutil.copyfile(out, ctx.bundle / name)
            w, h = sips_dims(out)
            ctx.names[orig] = (name, w, h)
        img.attrs = {"src": f"/cr/{slug}/{name}", "alt": img.get("alt") or "", "width": str(w), "height": str(h),
                     "loading": "lazy", "decoding": "async"}

    allowlist_pass(soup, ctx)
    out = []
    for node in soup.contents:
        if isinstance(node, NavigableString):
            continue
        out.append(str(node))
    body = "\n".join(out) + "\n"
    return body.replace("{{", "&#123;&#123;")


ATTR_ALLOW = {"a": {"href", "id"}, "img": {"src", "alt", "width", "height", "loading", "decoding"},
              "ol": {"start"}, "th": {"colspan", "rowspan"}, "td": {"colspan", "rowspan"}}


def allowlist_pass(soup, ctx):
    for tag in list(soup.find_all(True)):
        if getattr(tag, "decomposed", False):
            continue
        if tag.name not in ALLOWED_TAGS:
            ctx.note_class(tag, f"{tag.name} unwrapped")
            tag.unwrap()
            continue
        if tag.name == "div":
            if classes_of(tag) == ["cr-footnote"]:
                tag.attrs = {"class": ["cr-footnote"]}
            else:
                ctx.note_class(tag, "div unwrapped")
                tag.unwrap()
            continue
        allowed = ATTR_ALLOW.get(tag.name, set())
        tag.attrs = {k: v for k, v in tag.attrs.items() if k in allowed}
    for a in list(soup.find_all("a")):
        if not a.get("href") and not a.get("id"):
            a.unwrap()


# ---------------------------------------------------------------------------
# Bundles
# ---------------------------------------------------------------------------

def duration_label(seconds):
    total = round(seconds / 60)
    if seconds >= 3600 or total >= 60:
        h, m = divmod(total, 60)
        return f"{h}h {m}m" if m else f"{h}h"
    return f"{max(1, total)}m"


def build_bundle(listing_post, net, refresh, kept, fa_slugs, report):
    slug = listing_post["slug"]
    post = net.post(slug, refresh)
    bundle = OUT / slug
    if bundle.exists():
        shutil.rmtree(bundle)
    bundle.mkdir(parents=True)
    ctx = Ctx(slug, net, bundle, kept, fa_slugs)
    try:
        cover_url = post.get("cover_image") or listing_post.get("cover_image")
        alt_cover = post.get("podcast_episode_image_url") or listing_post.get("podcast_episode_image_url")
        cover_orig = original_url(cover_url) if cover_url else None
        cover_written = False
        cands = [u for u in (cover_orig, cover_url, original_url(alt_cover) if alt_cover else None, alt_cover) if u]
        if cands:
            out, _ = process(net, cands, "cover")
            shutil.copyfile(out, bundle / "cover.jpg")
            cover_written = True
        body = sanitize_body(post["body_html"], slug, ctx, cover_orig)
    except Exception:
        shutil.rmtree(bundle, ignore_errors=True)
        raise
    kind = post.get("type") or listing_post.get("type") or "newsletter"
    names = [b.get("name") for b in (post.get("publishedBylines") or []) if b.get("name")]
    date = listing_post["post_date"]
    front = {
        "title": post.get("title") or listing_post["title"],
        "subtitle": post.get("subtitle") or listing_post.get("subtitle") or "",
        "date": date,
        "slug": slug,
        "cr_kind": kind,
        "byline": " & ".join(names) or "Matt Stine",
        "legacy_url": f"https://falkenslabyrinth.com/p/{slug}",
    }
    if cover_written:
        front["cover"] = "cover.jpg"
    if kind == "podcast":
        dur = post.get("podcast_duration") or listing_post.get("podcast_duration")
        if dur:
            front["duration"] = int(round(dur))
            front["duration_label"] = duration_label(dur)
        front["media_url"] = ""
        front["media_file"] = f"{date[:10]}-{slug}.mp4"
    head = "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items())
    (bundle / "index.html").write_text(f"---\n{head}\n---\n\n{body}", encoding="utf-8")
    report["covers"] += 1 if cover_written else 0
    report["images"] += ctx.images
    report["podcasts"] += 1 if kind == "podcast" else 0
    report["warns"].extend(ctx.warns)
    for key, n in ctx.classes.items():
        report["classes"][key] += n
        report["class_posts"][key].add(slug)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--listing", default=os.path.expanduser("~/.psyche/tools/substack/cr-archive.json"))
    ap.add_argument("--cache", default=os.path.expanduser("~/.cache/sync-cr"))
    ap.add_argument("--only", action="append", default=[], metavar="SLUG")
    ap.add_argument("--fetch-only", action="store_true")
    ap.add_argument("--offline", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    ap.add_argument("--cookie-file")
    args = ap.parse_args()

    kept, dropped = load_listing(args.listing)
    kept_slugs = [p["slug"] for p in kept]
    unknown = [s for s in args.only if s not in kept_slugs]
    if unknown:
        sys.exit(f"sync-cr: --only names no kept post: {unknown}")
    net = Net(Path(args.cache).expanduser(), args.offline, args.cookie_file)
    targets = [p for p in kept if not args.only or p["slug"] in args.only]

    if args.fetch_only:
        failures = []
        for p in targets:
            try:
                net.post(p["slug"], args.refresh)
            except RuntimeError as e:
                failures.append(f"{p['slug']}: {e}")
        print(f"sync-cr: cached post JSON for {len(targets) - len(failures)}/{len(targets)} posts "
              f"({net.live} live requests)")
        for f in failures:
            print(f"sync-cr: FAIL {f}")
        sys.exit(1 if failures else 0)

    write_legacy(kept, dropped)
    fa_slugs = {d.name for d in FA_OUT.iterdir() if d.is_dir()} if FA_OUT.is_dir() else set()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.only:
        for child in OUT.iterdir():
            if child.is_dir():
                shutil.rmtree(child)

    from collections import defaultdict
    report = {"covers": 0, "images": 0, "podcasts": 0, "warns": [], "classes": Counter(),
              "class_posts": defaultdict(set)}
    failures, built = [], 0
    for p in targets:
        try:
            build_bundle(p, net, args.refresh, set(kept_slugs), fa_slugs, report)
            built += 1
        except (RuntimeError, OSError) as e:
            failures.append(f"{p['slug']}: {e}")

    print(f"sync-cr: {built}/{len(targets)} posts → content/cr/ ({report['podcasts']} podcasts, "
          f"{report['covers']} covers, {report['images']} inline images localized; {net.live} live requests)")
    print(f"sync-cr: dropped (gated), excluded: {', '.join(dropped)}")
    for line in report["warns"]:
        print(f"sync-cr: WARN {line}")
    for (cls, why), n in sorted(report["classes"].items()):
        print(f"sync-cr: WARN class '{cls}' hit no specific rule ({why}; {n}x in {len(report['class_posts'][(cls, why)])} posts)")
    for f in failures:
        print(f"sync-cr: FAIL {f}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
