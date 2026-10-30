#!/usr/bin/env python3
"""pull-webmentions.py — pull the domain's received Webmentions into data/webmentions.json.

Runs in the build job, after the last-good cache is restored and before `hugo`, on push and on
the nightly cron. Hugo reads the file and renders replies, likes, reposts and mentions under each Feral
Architecture essay (themes/arcaeon/layouts/partials/fa/mentions.html). Stdlib only, no JS on
the page, no commit back to the repo.

Env: WEBMENTION_IO_TOKEN (the webmention.io account token; sent as a Bearer header only).
Exit 0: pulled, or the token is absent (the one non-failure; the log says so and a ::notice is
printed). Exit 1 (PULL_FAILED): anything else. Either way data/webmentions.json is a valid file
when this script exits, so `hugo` always has something it can read.

Where the data lives, and why it is not committed
-------------------------------------------------
data/webmentions.json is generated at build and gitignored. Committing it back to main needs
`contents: write`, leaves a bot commit per mention, and risks a deploy loop; fetching in the
browser is ruled out (no client JS). Instead the previous good file lives in the Actions cache
(restore by prefix before this script, save only when it succeeded), the same pattern as the
sender's sent-state. The nightly build restores and re-saves it, which keeps the entry younger
than GitHub's 7-day eviction.

What each failure does
----------------------
The script rewrites the data file BEFORE any network call: last-good (shape-validated, so a
corrupt cache entry cannot stop `hugo`) with the committed blocklist reapplied (so a new block
takes effect even during an outage). Then:

    pull succeeds                         fresh file, exit 0
    token absent                          last-good kept, exit 0, log line and ::notice
    outage, 5xx, timeout (3 tries)        last-good kept, exit 1
    401, 400, any 3xx                     last-good kept, exit 1, no retry
    wrong shape, bad JSON, short walk     last-good kept, exit 1
    200 with zero mentions                see "The witness"
    blocklist file malformed              data file untouched, exit 1 (a repo bug)

The workflow runs this step with continue-on-error, so a failure never blocks the deploy: the
essay publishes with last-good mentions, and a separate job after deploy turns the run red.

The witness
-----------
webmention.io answers a valid token whose account does not hold the domain with a 200 and an
empty feed. That is indistinguishable from "no mentions", and it would blank every mention on
the site. So when a pull returns zero and last-good holds mentions, the public per-target
endpoint (no token) is asked about those pages. Mentions there mean the domain-wide answer is
wrong: exit 1 and last-good stays. None there means they really are gone: the file is emptied,
exit 0. A witness that cannot be reached counts as failure.

Why `page`, not `since_id`
--------------------------
The service returns `sort-dir=up` feeds in received order, not id order, so "the last id seen"
is not the maximum. Stepping `page` has no ordering assumption, and a short walk is caught by
comparing the unique count with the first response's `total`. Every build is a full pull: volume
is low, one request carries up to 1000, and upstream deletions vanish with no extra endpoint.

Why names only
--------------
No avatar or photo URL is ever copied into the data file, so a template cannot hotlink one even
by accident and no reader's IP reaches a stranger's host. Names link to the mention itself.
Only `content.text` is read, never `content.html`. Logs carry counts and fixed text, never a
mention field: a line of stranger text starting `::` is a workflow command to the runner.

webmention.io coverage (opt out explicitly, never by omission)
--------------------------------------------------------------
In: GET /api/mentions.jf2 with domain, per-page, page and sort-dir (Bearer header), and the
same endpoint with target[] and no token (the witness); wm-property in-reply-to, like-of and
repost-of and mention-of are rendered. Sources on the site's own domains (OWN_DOMAINS) are
dropped and counted as own-site, whatever their kind, so the site's cross-links never render as
responses from other people. Out, on purpose: bookmark-of and rsvp (counted in the log, not
rendered; adding one is a KINDS entry and a template loop); wm-private mentions (dropped,
never public); photo, video, audio and author photos (no third-party images); content.html;
the `token` query parameter; since, since_id, the wm-property filter and sort-by; deleted.jf2
and count (a full pull is authoritative); the legacy, atom, html and jsonp formats; export.jf2;
web hooks; webmention-render.js and its CSS; pingback; and the dashboard (sign-in, settings,
moderation), which is manual and complements data/webmention-blocklist.json.
"""
import datetime
import http.client
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
import urllib.error
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
BLOCKLIST = ROOT / "data" / "webmention-blocklist.json"
NAME_CHARS = 80
REPLY_CHARS = 600
KINDS = {"like-of": "likes", "repost-of": "reposts", "mention-of": "mentions",
         "in-reply-to": "replies"}
# Sources served from these hosts (or a subdomain) are the site's own pages, never a response.
OWN_DOMAINS = ("falkensmage.com", "rewired.show", "feralarchitecture.com", "arcaeon.rocks",
               "mytarotpulse.com", "psyche.sh")
PULL_FAILED = 1
MAX_PAGES = 100
TRIES = 3
WAIT = 5
MAX_BYTES = 32 * 1024 * 1024
WITNESS_PATHS = 50
TOKEN_RE = re.compile(r"[\x21-\x7e]+")


class PullError(Exception):
    """The pull or its inputs are broken. The message is safe to log: it never holds the token
    or any mention field."""


# No redirect handler: an Authorization header must never follow a redirect, so any 3xx raises.
# No ProxyHandler: the token only ever goes to API's host. UnknownHandler is required, or an
# unknown scheme returns None silently.
OPENER = urllib.request.OpenerDirector()
for _h in (urllib.request.UnknownHandler(), urllib.request.HTTPDefaultErrorHandler(),
           urllib.request.HTTPErrorProcessor(), urllib.request.HTTPHandler(),
           urllib.request.HTTPSHandler()):
    OPENER.add_handler(_h)


def log(msg):
    print(f"pull-webmentions: {msg}", flush=True)


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
    """Plain one-line text: controls and bidi overrides gone, whitespace collapsed, capped at
    `limit` characters (cut at the last space, with a trailing ellipsis)."""
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
    return path if re.fullmatch(r"/fa/[^/]+/", path) else None


def _host(url):
    try:
        return (urllib.parse.urlsplit(url).hostname or "").lower().rstrip(".")
    except ValueError:
        return ""


def is_own(url):
    """True when the URL's parsed host is an own domain or a subdomain of one. The dot boundary
    keeps falkensmage.com.evil.example and notpsyche.sh out; a host named only in the path or
    userinfo is never read."""
    host = _host(url)
    return bool(host) and any(host == d or host.endswith("." + d) for d in OWN_DOMAINS)


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


# --- HTTP -------------------------------------------------------------------------------

def get_json(params, token=None):
    """GET API with `params` (a list of pairs) and return the parsed JSON.

    The token goes in a header, never the URL, and must be plain printable ASCII: http.client
    would otherwise put the raw value in its own error. Connection errors, timeouts, 5xx and 429
    are retried (TRIES, WAIT apart); any other HTTP status raises at once. The body is capped.
    """
    if token is not None and not TOKEN_RE.fullmatch(token):
        raise PullError("WEBMENTION_IO_TOKEN holds characters that cannot be sent in a header")
    headers = {"User-Agent": UA, "Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=headers)
    why = "no attempt"
    for attempt in range(TRIES):
        try:
            with OPENER.open(req, timeout=TIMEOUT) as r:
                body = r.read(MAX_BYTES + 1)
            break
        except urllib.error.HTTPError as e:
            try:
                if e.code < 500 and e.code != 429:
                    raise PullError(f"HTTP {e.code}{_api_reason(e)}") from None
                why = f"HTTP {e.code}"
            finally:
                e.close()
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as e:
            why = type(e).__name__
        if attempt < TRIES - 1:
            time.sleep(WAIT)
    else:
        raise PullError(f"webmention.io unreachable ({why}) after {TRIES} tries")
    if len(body) > MAX_BYTES:
        raise PullError("response larger than the size cap")
    try:
        return json.loads(body)
    except (ValueError, RecursionError):
        raise PullError("response was not valid JSON") from None


def _api_reason(err):
    """': <error_description>' from a JSON error body, cleaned and capped; '' if there is none."""
    try:
        doc = json.loads(err.read(4096))
        reason = clean_text(doc.get("error_description"), 200)
    except (ValueError, RecursionError, AttributeError, OSError, http.client.HTTPException):
        return ""
    return f": {reason}" if reason else ""


def _feed(doc):
    """(children, paging) after checking the envelope. Never echoes a value."""
    if not isinstance(doc, dict) or not isinstance(doc.get("children"), list):
        raise PullError("response has no children list")
    paging = doc.get("paging")
    if not isinstance(paging, dict):
        raise PullError("response has no paging object")
    for key in ("total", "total-pages"):
        if type(paging.get(key)) is not int:
            raise PullError(f"paging.{key} is not an integer")
    return doc["children"], paging


def pull_all(token):
    """Every mention for the domain, in received order, deduped by wm-id."""
    seen, out, expected = set(), [], None
    for page in range(MAX_PAGES):
        doc = get_json([("domain", DOMAIN), ("per-page", PER_PAGE), ("sort-dir", "up"),
                        ("page", page)], token)
        children, paging = _feed(doc)
        if expected is None:
            expected = paging["total"]
        for c in children:
            if not isinstance(c, dict):
                raise PullError("a child is not an object")
            if type(c.get("wm-id")) is not int:
                raise PullError("a child has no integer wm-id")
            for key in ("wm-target", "wm-source"):
                if not isinstance(c.get(key), str):
                    raise PullError(f"a child has no string {key}")
            if c["wm-id"] not in seen:
                seen.add(c["wm-id"])
                out.append(c)
        if page + 1 >= paging["total-pages"]:
            break
    else:
        raise PullError(f"more than {MAX_PAGES} pages")
    if len(out) < expected:
        raise PullError(f"short walk: {len(out)} of {expected} mentions")
    # A renamed field would turn everything into 'other' and blank the site. One child without
    # it is legal (old mentions are stored untyped); all of them without it is not.
    if out and not any("wm-property" in c for c in out):
        raise PullError("no child carries wm-property")
    return out


def witness_total(paths):
    """The public per-target count (no token) for these essay paths."""
    params = [("target[]", SITE + p) for p in paths[:WITNESS_PATHS]] + [("per-page", 1)]
    _, paging = _feed(get_json(params))
    return paging["total"]


# --- normalize --------------------------------------------------------------------------

def normalize(children):
    """(pages, counts). pages maps '/fa/slug/' to {likes, reposts, mentions, replies} lists of records
    holding only name, url, source, author_url (and text, date, date_text on replies)."""
    pages, seen = {}, set()
    counts = {"private": 0, "other": 0, "off_essay": 0, "unusable": 0,
              "own": 0}
    for child in children:
        if child.get("wm-private"):
            counts["private"] += 1
            continue
        # A statement about the source, not the kind: the site linking to itself (both-hands to
        # labeled-as-potatoes arrives as mention-of) is never a response from someone else.
        if is_own(child.get("wm-source")):
            counts["own"] += 1
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


# --- blocklist --------------------------------------------------------------------------

def _author_key(url):
    """host + path with any trailing slash removed; scheme, query and fragment ignored."""
    try:
        parts = urllib.parse.urlsplit(url)
        host = (parts.hostname or "").lower().rstrip(".")
    except ValueError:
        return ""
    return (host + parts.path.rstrip("/")) if host else ""


def load_blocklist(path):
    """(domains, authors), lowercased / canonical. Anything malformed raises PullError: a
    blocklist that silently loads as empty would let blocked content ship."""
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError, RecursionError):
        raise PullError("blocklist file is missing or not valid JSON") from None
    if not isinstance(doc, dict):
        raise PullError("blocklist is not an object")
    domains, authors = [], []
    for key, bucket in (("domains", domains), ("authors", authors)):
        values = doc.get(key)
        if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
            raise PullError(f"blocklist {key} is not a list of strings")
        bucket.extend(values)
    domains = [d.strip().lower().strip(".") for d in domains]
    if not all(re.fullmatch(r"[a-z0-9]([a-z0-9.-]*[a-z0-9])?", d) for d in domains):
        raise PullError("blocklist domains must be bare host names")
    authors = [_author_key(a.strip()) for a in authors]
    if not all(authors):
        raise PullError("blocklist authors must be URLs")
    return domains, authors


def apply_blocklist(pages, blocklist):
    """(pages, blocked_count) without any record whose url, source or author_url is on a
    blocked domain (or a subdomain of one), or whose author URL is blocked. Emptied lists and
    pages are removed. Used on fresh and on last-good data alike."""
    domains, authors = blocklist
    kept, blocked = {}, 0
    for path, kinds in pages.items():
        for kind, records in kinds.items():
            for rec in records:
                hosts = {_host(rec.get(f, "")) for f in ("url", "source", "author_url")}
                hit = any(h == d or h.endswith("." + d) for h in hosts for d in domains if h)
                akey = _author_key(rec.get("author_url", ""))
                if hit or (akey and akey in authors):
                    blocked += 1
                else:
                    kept.setdefault(path, {}).setdefault(kind, []).append(rec)
    return kept, blocked


# --- the data file ----------------------------------------------------------------------

_OPTIONAL = ("source", "author_url", "text", "date", "date_text")


def load_last_good(path):
    """(pages, generated) from the data file. Missing is ({}, None). A file that does not parse
    or has the wrong shape is logged loudly and treated as empty: a bad file stops `hugo`, and
    a wrong-typed value fails a `range`."""
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except FileNotFoundError:
        return {}, None
    except (OSError, ValueError, RecursionError):
        log("last-good data is not valid JSON; ignoring it")
        return {}, None
    try:
        pages = doc["pages"]
        assert isinstance(pages, dict)
        for key, kinds in pages.items():
            assert isinstance(key, str) and isinstance(kinds, dict)
            for kind, records in kinds.items():
                assert kind in KINDS.values() and isinstance(records, list)
                for rec in records:
                    assert isinstance(rec, dict)
                    assert isinstance(rec.get("name"), str) and isinstance(rec.get("url"), str)
                    assert all(isinstance(rec.get(f, ""), str) for f in _OPTIONAL)
        generated = doc.get("generated")
        return pages, generated if isinstance(generated, str) else None
    except (AssertionError, KeyError, TypeError):
        log("last-good data has the wrong shape; ignoring it")
        return {}, None


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


def _count(pages, kinds=tuple(KINDS.values())):
    return sum(len(p.get(k, [])) for p in pages.values() for k in kinds)


# --- main -------------------------------------------------------------------------------

def main():
    """The order is the design: blocklist, then last-good rewritten with the blocklist applied
    (before any network call), then the pull."""
    try:
        blocklist = load_blocklist(BLOCKLIST)
    except PullError as e:
        log(f"FAILED: {e}; data file left untouched")
        print(f"::error title=Webmentions::{e}", flush=True)
        return PULL_FAILED

    last, generated = load_last_good(DATA)
    last, _ = apply_blocklist(last, blocklist)
    write_data(DATA, last, generated)
    kept = _count(last)

    token = os.environ.get("WEBMENTION_IO_TOKEN", "").strip()
    if not token:
        log(f"WEBMENTION_IO_TOKEN is not set, which is not a failure; kept {kept} last-good mentions")
        print("::notice title=Webmentions::WEBMENTION_IO_TOKEN is not set; "
              f"kept {kept} last-good mentions", flush=True)
        return 0

    try:
        children = pull_all(token)
        if not children and last:
            total = witness_total(sorted(last))
            if total > 0:
                raise PullError(f"the domain-wide pull is empty but the public endpoint "
                                f"reports {total} mentions")
    except PullError as e:
        log(f"FAILED: {e}; kept {kept} last-good mentions from {generated or 'an unknown time'}")
        print(f"::error title=Webmentions::{e}; kept {kept} last-good mentions", flush=True)
        return PULL_FAILED

    pages, counts = normalize(children)
    pages, blocked = apply_blocklist(pages, blocklist)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    write_data(DATA, pages, now)
    log(f"pulled {len(children)}: {_count(pages, ('likes',))} likes, "
        f"{_count(pages, ('reposts',))} reposts, {_count(pages, ('mentions',))} mentions, "
        f"{_count(pages, ('replies',))} replies "
        f"on {len(pages)} essays; not rendered: {counts['private']} private, "
        f"{counts['other']} other kinds, {counts['off_essay']} off-essay, "
        f"{counts['own']} own-site, {blocked} blocked, {counts['unusable']} unusable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
