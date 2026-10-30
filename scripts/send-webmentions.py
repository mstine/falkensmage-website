#!/usr/bin/env python3
"""send-webmentions.py — tell the pages the newest Feral Architecture essay cites that it cited them.

Runs after deploy, so a target never gets a Webmention for a page that isn't live. Reads the
deployed feed, takes the newest essay, collects the external links inside its h-entry, finds
each target's Webmention endpoint (W3C Webmention §3.1.2) and POSTs source and target
(§3.1.3). Stdlib only; DRY_RUN=1 skips every POST.

Exit 1 if our own side is broken: the feed is unreachable or empty, or the essay page has no
h-entry. A dead or hostile target never changes the exit code.
"""
import email.utils
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

FEED = "https://falkensmage.com/fa/index.xml"
SITE_HOST = "falkensmage.com"
UA = "falkensmage-webmention-sender (+https://falkensmage.com/)"
TIMEOUT = 20
MAX_BYTES = 2 * 1024 * 1024
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
        if host == SITE_HOST or host.endswith("." + SITE_HOST):
            continue
        if urllib.parse.urldefrag(url)[0] == own or url in out:
            continue
        out.append(url)
    return out


# --- HTTP -------------------------------------------------------------------------------

def _opener(*extra):
    """An opener holding only http(s) handlers. Never build_opener/urlopen: those carry file:
    and ftp: handlers, and a redirected POST becomes a GET that reports a false 200.
    UnknownHandler is required, or an unknown scheme returns None silently."""
    op = urllib.request.OpenerDirector()
    for h in (urllib.request.UnknownHandler(), urllib.request.HTTPDefaultErrorHandler(),
              urllib.request.HTTPErrorProcessor(), urllib.request.HTTPHandler(),
              urllib.request.HTTPSHandler(), *extra):
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


# --- run --------------------------------------------------------------------------------

def main():
    dry = os.environ.get("DRY_RUN", "") == "1"
    req = urllib.request.Request(FEED, headers={"User-Agent": UA})
    with GET_OPENER.open(req, timeout=TIMEOUT) as r:
        newest = newest_essay(r.read(MAX_BYTES).decode("utf-8"))
    if newest is None:
        sys.exit("send-webmentions: feed has no items")
    source, _published = newest

    _, _, page = fetch(source)
    links = entry_links(page or "")
    if links is None:
        sys.exit(f"send-webmentions: {source} has no h-entry")
    targets = external_targets(links, source)
    log(f"{source}: {len(targets)} external targets{' (dry run)' if dry else ''}")
    for target in targets:
        endpoint = discover(target)
        if endpoint is None:
            log(f"no endpoint: {target}")
            continue
        if dry:
            log(f"would send: {target} -> {endpoint}")
            continue
        log(f"sent {notify(endpoint, source, target)}: {target} -> {endpoint}")


if __name__ == "__main__":
    main()
