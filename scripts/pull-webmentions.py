#!/usr/bin/env python3
"""pull-webmentions.py — pull the domain's received Webmentions into data/webmentions.json.

Runs in the build job before `hugo`, on push and on the nightly cron. Hugo reads the file and
renders replies, likes and reposts under each Feral Architecture essay. Stdlib only.

Env: WEBMENTION_IO_TOKEN (the webmention.io account token).
Exit 0 on success and when the token is absent. Exit 1 (PULL_FAILED) on anything else.
"""
import datetime
import json
import os
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://webmention.io/api/mentions.jf2"
DOMAIN = "falkensmage.com"
SITE = "https://falkensmage.com"
UA = "falkensmage-webmention-puller (+https://falkensmage.com/)"
TIMEOUT = 20
PER_PAGE = 1000
DATA = ROOT / "data" / "webmentions.json"
NAME_CHARS = 80
REPLY_CHARS = 600
KINDS = {"like-of": "likes", "repost-of": "reposts", "in-reply-to": "replies"}
PULL_FAILED = 1

# No redirect handler: an Authorization header must never follow a redirect. No ProxyHandler.
OPENER = urllib.request.OpenerDirector()
for _h in (urllib.request.UnknownHandler(), urllib.request.HTTPDefaultErrorHandler(),
           urllib.request.HTTPErrorProcessor(), urllib.request.HTTPHandler(),
           urllib.request.HTTPSHandler()):
    OPENER.add_handler(_h)


def log(msg):
    print(f"pull-webmentions: {msg}", flush=True)


def get_json(params, token=None):
    """GET API with `params` (a list of pairs). The token goes in a header, never the URL."""
    url = API + "?" + urllib.parse.urlencode(params)
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with OPENER.open(urllib.request.Request(url, headers=headers), timeout=TIMEOUT) as r:
        return json.loads(r.read())


# --- cleaning stranger text -------------------------------------------------------------

_BIDI = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A)) | {0x200E, 0x200F, 0x061C}


def clean_url(value):
    """The value if it is a plain http(s) URL with a host, else ''."""
    if not isinstance(value, str) or len(value) > 2000:
        return ""
    if any(c.isspace() or unicodedata.category(c) == "Cc" for c in value):
        return ""
    try:
        parts = urllib.parse.urlsplit(value)
        host = parts.hostname
    except ValueError:
        return ""
    if parts.scheme not in ("http", "https") or not host:
        return ""
    return value


def clean_text(value, limit):
    """Plain one-line text: controls and bidi overrides gone, whitespace collapsed, capped."""
    if not isinstance(value, str):
        return ""
    out = []
    for ch in value:
        if ch.isspace():
            out.append(" ")
        elif unicodedata.category(ch) == "Cc" or ord(ch) in _BIDI:
            continue
        else:
            out.append(ch)
    s = " ".join("".join(out).split())
    if len(s) > limit:
        cut = s[:limit]
        if " " in cut:
            cut = cut[:cut.rfind(" ")]
        s = cut.rstrip() + "…"
    return s


def page_key(target):
    """'/fa/slug/' for a target on this site's essay paths, else None."""
    if not isinstance(target, str):
        return None
    try:
        parts = urllib.parse.urlsplit(target)
        host = (parts.hostname or "").lower()
    except ValueError:
        return None
    if host not in (DOMAIN, "www." + DOMAIN):
        return None
    path = parts.path if parts.path.endswith("/") else parts.path + "/"
    parts_ok = path.startswith("/fa/") and path.count("/") == 3 and len(path) > 5
    return path if parts_ok else None


def _host(url):
    try:
        return urllib.parse.urlsplit(url).hostname or ""
    except ValueError:
        return ""


def _date(child):
    for field in ("published", "wm-received"):
        v = child.get(field)
        if isinstance(v, str):
            try:
                d = datetime.date.fromisoformat(v[:10])
            except ValueError:
                continue
            return d.isoformat(), f"{d:%B} {d.day}, {d.year}"
    return "", ""


def normalize(children):
    """(pages, counts). pages maps '/fa/slug/' to {likes, reposts, replies} lists of records."""
    pages, seen = {}, set()
    counts = {"private": 0, "other": 0, "off_essay": 0, "unusable": 0}
    for child in children:
        if child.get("wm-private"):
            counts["private"] += 1
            continue
        kind = KINDS.get(child.get("wm-property"))
        if kind is None:
            counts["other"] += 1
            continue
        path = page_key(child.get("wm-target"))
        if path is None:
            counts["off_essay"] += 1
            continue
        source = clean_url(child.get("wm-source"))
        url = clean_url(child.get("url")) or source
        if not url:
            counts["unusable"] += 1
            continue
        if (path, kind, source) in seen:
            continue
        seen.add((path, kind, source))
        author = child.get("author") if isinstance(child.get("author"), dict) else {}
        author_url = clean_url(author.get("url"))
        name = (clean_text(author.get("name"), NAME_CHARS) or _host(author_url)
                or _host(url) or "Someone")
        rec = {"name": name, "url": url, "source": source, "author_url": author_url}
        if kind == "replies":
            content = child.get("content")
            text = clean_text(content.get("text"), REPLY_CHARS) if isinstance(content, dict) else ""
            rec["text"] = text or clean_text(child.get("name"), REPLY_CHARS)
            rec["date"], rec["date_text"] = _date(child)
        pages.setdefault(path, {}).setdefault(kind, []).append(rec)
    return pages, counts


def write_data(path, pages, generated):
    """Atomic write: a temp file in the same directory, then os.replace."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps({"generated": generated, "pages": pages}, ensure_ascii=False,
                      indent=1, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".webmentions-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(body)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main():
    token = os.environ.get("WEBMENTION_IO_TOKEN", "").strip()
    if not token:
        log("WEBMENTION_IO_TOKEN is not set, which is not a failure")
        return 0
    feed = get_json([("domain", DOMAIN), ("per-page", PER_PAGE), ("sort-dir", "up")], token)
    pages, counts = normalize(feed["children"])
    generated = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_data(DATA, pages, generated)
    n = {k: sum(len(p.get(k, [])) for p in pages.values()) for k in KINDS.values()}
    log(f"pulled {len(feed['children'])}: {n['likes']} likes, {n['reposts']} reposts, "
        f"{n['replies']} replies on {len(pages)} essays; not rendered: {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
