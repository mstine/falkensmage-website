#!/usr/bin/env python3
"""send-webmentions.py — tell the pages the newest Feral Architecture essay and the recent notes
cite that they were cited.

Runs after deploy, so a target never gets a Webmention for a page that isn't live. Reads the
deployed essay feed, takes the newest essay, collects the external links inside its h-entry,
finds each target's Webmention endpoint (W3C Webmention §3.1.2) and POSTs source and target
(§3.1.3). Notes send too: the deployed notes feed lists them, every note inside the same
7-day window is a source, and the same state file records what was accepted. A note page's
u-syndication links (its own copies on Mastodon and Bluesky) are skipped: a syndicated copy is
not a citation. An old essay no longer ends the run, since notes may still be in the window.
Stdlib only; DRY_RUN=1 skips every POST.

Env: DRY_RUN ("1" to skip every POST), WEBMENTION_STATE (path of the sent-state file).
Exit 1 if our own side is broken: the essay feed is unreachable or empty, the notes feed is
unreachable or unreadable (an empty notes feed is fine: there may be no notes), or a page
never gains an h-entry. A dead or hostile target never changes the exit code.

Sent state: where it lives and why
----------------------------------
Webmention has no API to ask "did I already send this?", so the sender keeps its own record:
one tab-separated `source<TAB>target` line per pair a receiver accepted (any 2xx), appended
immediately so a killed job keeps earlier work. The workflow stores that file in the Actions
cache (restore by key prefix, save under `if: always()`); the workflow's `concurrency: pages`
serializes runs, so restore, send and save cannot interleave.

Not a commit back to main: that needs `contents: write` on the job that parses untrusted HTML
and leaves a bot commit per essay. Not a time window alone: that resends on every run inside
it. Not a diff against the live feed: one transient failure would be lost for good.

Failure direction: a lost or denied cache save costs a duplicate POST inside the window, which
the spec (section 3.2.4) says receivers should tolerate. It can never cost a missed send. The
window is MAX_AGE (7 days) from the essay's publish date; an essay past it never sends, so a
lost cache cannot resend history. The cache entry stays younger than GitHub's 7-day eviction
because the nightly rebuild restores and re-saves it. Only accepted pairs are recorded, so dead
links and 5xx endpoints are retried nightly until the window closes, and each run logs how many
pairs it loaded: zero after a successful send is the only visible sign of a denied cache save.

Safety: targets are third-party pages, so every connection (GET, POST, each redirect hop)
checks the connected peer address and refuses anything non-global before a request byte is
written. Only http and https open; a redirect on a POST is a failure, never followed.
"""
import email.utils
import http.client
import ipaddress
import os
import ssl
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser

FEED = "https://falkensmage.com/fa/index.xml"
NOTES_FEED = "https://falkensmage.com/notes/index.xml"
SITE_HOST = "falkensmage.com"
UA = "falkensmage-webmention-sender (+https://falkensmage.com/)"
TIMEOUT = 20
MAX_BYTES = 2 * 1024 * 1024
MAX_AGE = timedelta(days=7)
STATE = os.environ.get("WEBMENTION_STATE", ".webmentions-sent")
HTML_TYPES = ("text/html", "application/xhtml+xml")


def log(msg):
    print(f"send-webmentions: {msg}", flush=True)


# --- the feed ---------------------------------------------------------------------------

def newest_essay(xml_text):
    """(url, published) of the newest feed item, or None for an empty feed."""
    items = []
    for it in ET.fromstring(xml_text).iter("item"):
        items.append(((it.findtext("link") or "").strip(),
                      email.utils.parsedate_to_datetime(it.findtext("pubDate"))))
    return max(items, key=lambda i: i[1]) if items else None


def recent_notes(xml_text, now):
    """[(url, published)] for each feed item `decide` says to send, oldest first. An empty feed
    is an empty list."""
    items = []
    for it in ET.fromstring(xml_text).iter("item"):
        published = email.utils.parsedate_to_datetime(it.findtext("pubDate"))
        if published.tzinfo is None:
            published = published.replace(tzinfo=timezone.utc)
        url = (it.findtext("link") or "").strip()
        if url and decide(published, now) == "send":
            items.append((url, published))
    return sorted(items, key=lambda i: i[1])


# --- the source page --------------------------------------------------------------------

class _EntryLinks(HTMLParser):
    """Collect anchor hrefs inside the first element carrying the h-entry class."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tag = None      # tag name of the h-entry element once found
        self.depth = 0       # same-tag nesting depth inside it
        self.done = False
        self.links = None    # None until an h-entry is seen

    def handle_starttag(self, tag, attrs):
        a = _attrs(attrs)
        if self.tag is None and not self.done:
            if "h-entry" in (a.get("class") or "").split():
                self.tag, self.depth, self.links = tag, 1, []
            return
        if self.tag is None:
            return
        if tag == self.tag:
            self.depth += 1
        if tag == "a" and a.get("href") is not None:
            if "u-syndication" in (a.get("class") or "").split():
                return  # a syndicated copy of this very entry, not something it cites
            self.links.append(a["href"])

    def handle_endtag(self, tag):
        if self.tag is not None and tag == self.tag:
            self.depth -= 1
            if self.depth == 0:
                self.tag, self.done = None, True


def _attrs(pairs):
    """Attribute dict, first occurrence wins (as in HTML); a valueless attribute is ''."""
    out = {}
    for k, v in pairs:
        out.setdefault(k.lower(), "" if v is None else v)
    return out


def entry_links(page_html):
    """hrefs of every anchor inside the page's h-entry; None if there is no h-entry, [] if
    there is one with no links. The distinction is load-bearing: None means our markup rotted."""
    p = _EntryLinks()
    p.feed(page_html)
    p.close()
    return p.links


def external_targets(links, source):
    """Absolute http(s) targets outside this site, deduped in document order."""
    own = urllib.parse.urldefrag(source)[0]
    out = []
    for link in links:
        try:
            url = urllib.parse.urljoin(source, link.strip())
            parts = urllib.parse.urlsplit(url)
            host = (parts.hostname or "").rstrip(".")
        except ValueError:
            continue
        if parts.scheme not in ("http", "https") or not host:
            continue
        if any(c.isspace() or ord(c) < 32 or ord(c) == 127 for c in url):
            continue  # not a valid URL, and tabs/newlines would corrupt the state file
        if host == SITE_HOST or host.endswith("." + SITE_HOST):
            continue
        if urllib.parse.urldefrag(url)[0] == own or url in out:
            continue
        out.append(url)
    return out


# --- HTTP -------------------------------------------------------------------------------

class BlockedAddress(OSError):
    """The connected peer is not a global unicast address."""


_NAT64 = ipaddress.ip_network("64:ff9b::/96")


def peer_allowed(ip):
    """True only for a global, non-multicast address. IPv4-mapped and NAT64 forms are unwrapped
    by hand: `is_global` does not see through them on every supported Python."""
    try:
        addr = ipaddress.ip_address(str(ip).split("%", 1)[0])
    except ValueError:
        return False
    if addr.version == 6:
        if addr.ipv4_mapped is not None:
            addr = addr.ipv4_mapped
        elif addr in _NAT64:
            addr = ipaddress.IPv4Address(int(addr) & 0xFFFFFFFF)
    return addr.is_global and not addr.is_multicast


def _check_peer(sock):
    peer = sock.getpeername()[0]
    if not peer_allowed(peer):
        sock.close()
        raise BlockedAddress(f"refusing to talk to non-global address {peer}")


class GuardedHTTPConnection(http.client.HTTPConnection):
    """Checks the connected peer before any request byte is written (connections are lazy)."""

    def connect(self):
        super().connect()
        _check_peer(self.sock)


class GuardedHTTPSConnection(http.client.HTTPSConnection):
    def connect(self):
        super().connect()
        _check_peer(self.sock)


_SSL = ssl.create_default_context()


class GuardedHTTPHandler(urllib.request.HTTPHandler):
    def http_open(self, req):
        return self.do_open(GuardedHTTPConnection, req)


class GuardedHTTPSHandler(urllib.request.HTTPSHandler):
    def https_open(self, req):
        return self.do_open(GuardedHTTPSConnection, req, context=_SSL)


def _opener(*extra):
    """The single chokepoint for every request this script makes. Holds only guarded http(s)
    handlers. Never build_opener/urlopen: those carry file: and ftp: handlers, and a redirected
    POST becomes a GET that reports a false 200. UnknownHandler is required, or an unknown
    scheme returns None silently. No ProxyHandler: a proxy would become the checked peer."""
    op = urllib.request.OpenerDirector()
    for h in (urllib.request.UnknownHandler(), urllib.request.HTTPDefaultErrorHandler(),
              urllib.request.HTTPErrorProcessor(), GuardedHTTPHandler(),
              GuardedHTTPSHandler(), *extra):
        op.add_handler(h)
    return op


GET_OPENER = _opener(urllib.request.HTTPRedirectHandler())
POST_OPENER = _opener()  # no redirect handler: any 3xx from an endpoint raises


def fetch(url):
    """GET url. Returns (final_url, link_header_values, body); body is None unless HTML."""
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"})
    with GET_OPENER.open(req, timeout=TIMEOUT) as r:
        links = r.headers.get_all("Link") or []
        body = None
        if r.headers.get_content_type() in HTML_TYPES:
            raw = r.read(MAX_BYTES)
            try:
                body = raw.decode(r.headers.get_content_charset() or "utf-8", errors="replace")
            except LookupError:
                body = raw.decode("utf-8", errors="replace")
        return r.geturl(), links, body


def _link_values(header):
    """Parse one Link header into [(url, {param: value})], per the RFC 8288 grammar: URLs may
    contain commas, quoted values may contain `rel=` and `,`, param names are case-insensitive,
    and the first occurrence of a param wins."""
    out, i, n = [], 0, len(header)
    while i < n:
        while i < n and header[i] in " \t,":
            i += 1
        if i >= n or header[i] != "<":
            i += 1
            continue
        end = header.find(">", i)
        if end < 0:
            break
        url, params, i = header[i + 1:end], {}, end + 1
        while i < n:
            while i < n and header[i] in " \t":
                i += 1
            if i >= n or header[i] == ",":
                break
            if header[i] != ";":
                i += 1
                continue
            i += 1
            while i < n and header[i] in " \t":
                i += 1
            start = i
            while i < n and header[i] not in "=;,":
                i += 1
            name, value = header[start:i].strip().lower(), ""
            if i < n and header[i] == "=":
                i += 1
                while i < n and header[i] in " \t":
                    i += 1
                if i < n and header[i] == '"':
                    i += 1
                    buf = []
                    while i < n and header[i] != '"':
                        if header[i] == "\\" and i + 1 < n:
                            i += 1
                        buf.append(header[i])
                        i += 1
                    i += 1
                    value = "".join(buf)
                else:
                    start = i
                    while i < n and header[i] not in ";,":
                        i += 1
                    value = header[start:i].strip()
            if name:
                params.setdefault(name, value)
        out.append((url, params))
    return out


def endpoint_from_links(link_values):
    """First Link header entry whose rel carries the webmention token, unresolved; else None."""
    for header in link_values:
        for url, params in _link_values(header):
            if "webmention" in params.get("rel", "").lower().split():
                return url
    return None


class _EndpointParser(HTMLParser):
    """First <link> or <a> in document order with a webmention rel token and an href."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.found = None

    def handle_starttag(self, tag, attrs):
        if self.found is not None or tag not in ("link", "a"):
            return
        a = _attrs(attrs)
        if "webmention" in a.get("rel", "").lower().split() and "href" in a:
            self.found = a["href"]


def find_endpoint(base, link_values, body):
    """The target's endpoint resolved against `base` (its final URL after redirects), or None.
    Link header first (§3.1.2), then the first matching element. An empty href counts, and
    resolves to the page itself; a missing href does not."""
    found = endpoint_from_links(link_values)
    if found is None and body:
        p = _EndpointParser()
        p.feed(body)
        p.close()
        found = p.found
    return None if found is None else urllib.parse.urljoin(base, found)


def discover(target):
    base, links, body = fetch(target)
    return find_endpoint(base, links, body)


def notify(endpoint, source, target):
    """POST form-encoded source and target to the endpoint URL verbatim (its query string
    survives). Any 2xx returns the status; anything else raises."""
    data = urllib.parse.urlencode({"source": source, "target": target}).encode()
    req = urllib.request.Request(endpoint, data=data, method="POST", headers={
        "User-Agent": UA, "Content-Type": "application/x-www-form-urlencoded"})
    with POST_OPENER.open(req, timeout=TIMEOUT) as r:
        r.read(MAX_BYTES)
        return r.status


# --- state and batch -------------------------------------------------------------------

def decide(published, now):
    """'skip-old' once the essay is past MAX_AGE, else 'send'."""
    return "skip-old" if now - published > MAX_AGE else "send"


def load_sent(path):
    """Set of (source, target) pairs a receiver already accepted."""
    try:
        with open(path, encoding="utf-8") as f:
            pairs = (line.rstrip("\n").split("\t") for line in f if line.strip())
            return {tuple(p) for p in pairs if len(p) == 2}
    except FileNotFoundError:
        return set()


def mark_sent(path, source, target):
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"{source}\t{target}\n")
        f.flush()
        os.fsync(f.fileno())


def send_all(source, targets, state, dry=False):
    """Send one Webmention per target. A target failing for any reason is one dead link: it is
    logged and the batch continues. Returns the tally."""
    done = load_sent(state)
    log(f"{len(done)} pairs loaded from state")
    tally = {"sent": 0, "already sent": 0, "no endpoint": 0, "failed": 0}
    for target in targets:
        if (source, target) in done:
            tally["already sent"] += 1
            log(f"already sent: {target}")
            continue
        try:
            endpoint = discover(target)
            if endpoint is None:
                tally["no endpoint"] += 1
                log(f"no endpoint: {target}")
            elif dry:
                log(f"would send: {target} -> {endpoint}")
            else:
                status = notify(endpoint, source, target)
                mark_sent(state, source, target)
                tally["sent"] += 1
                log(f"sent {status}: {target} -> {endpoint}")
        except Exception as e:  # deliberate: any hostile or dead target is just a dead link
            tally["failed"] += 1
            log(f"failed: {target}: {type(e).__name__}: {e}")
    log(f"{len(done)} loaded, " + ", ".join(f"{v} {k}" for k, v in tally.items()))
    return tally


def load_entry(url, tries=10, wait=15):
    """The essay's h-entry links, retrying while the deploy propagates. A 200 with no h-entry is
    treated as not-up-yet (the CDN may still serve the old page); a page that never gains one
    exits non-zero, because zero links and broken markup must not look the same."""
    for n in range(tries):
        try:
            _, _, body = fetch(url)
            links = entry_links(body or "")
            if links is not None:
                return links
            log(f"{url} has no h-entry yet")
        except Exception as e:
            log(f"{url} not up yet ({type(e).__name__}: {e})")
        if n < tries - 1:
            time.sleep(wait)
    sys.exit(f"send-webmentions: {url} never showed an h-entry; nothing sent")


def main(entry_wait=15):
    dry = os.environ.get("DRY_RUN", "") == "1"
    try:
        req = urllib.request.Request(FEED, headers={"User-Agent": UA})
        with GET_OPENER.open(req, timeout=TIMEOUT) as r:
            newest = newest_essay(r.read(MAX_BYTES).decode("utf-8"))
    except Exception as e:
        sys.exit(f"send-webmentions: feed unreachable or unreadable ({type(e).__name__}: {e})")
    if newest is None:
        sys.exit("send-webmentions: feed has no items")
    source, published = newest
    if published.tzinfo is None:
        published = published.replace(tzinfo=timezone.utc)

    if not dry:
        open(STATE, "a").close()  # the cache save always has a path
    action = decide(published, datetime.now(timezone.utc))
    log(f"{action}: {source}{' (dry run)' if dry else ''}")
    if action != "skip-old":
        links = load_entry(source, wait=entry_wait)
        targets = external_targets(links, source)
        log(f"{len(targets)} external targets")
        send_all(source, targets, STATE, dry)

    # Notes: our own feed, so it being unreadable is our side broken. An empty one is fine.
    try:
        req = urllib.request.Request(NOTES_FEED, headers={"User-Agent": UA})
        with GET_OPENER.open(req, timeout=TIMEOUT) as r:
            notes = recent_notes(r.read(MAX_BYTES).decode("utf-8"), datetime.now(timezone.utc))
    except Exception as e:
        sys.exit(f"send-webmentions: notes feed unreachable or unreadable ({type(e).__name__}: {e})")
    log(f"{len(notes)} recent notes")
    for note, _ in notes:
        links = load_entry(note, wait=entry_wait)
        targets = external_targets(links, note)
        log(f"{note}: {len(targets)} external targets")
        send_all(note, targets, STATE, dry)


if __name__ == "__main__":
    main()
