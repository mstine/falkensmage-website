#!/usr/bin/env python3
"""Tests for scripts/send-webmentions.py. Needs a built site first:

    hugo --minify && python3 -I -S -B tests/test-send-webmentions.py

-I -S proves the sender is stdlib-only by execution. A missing public/ is a failure, never a
skip, so the built-page check cannot silently vanish. Everything else runs against a stub
HTTP server on 127.0.0.1; there is no outbound network.
"""
import importlib.util
import threading
import unittest
import urllib.parse
from datetime import datetime, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"

spec = importlib.util.spec_from_file_location(
    "send_webmentions", ROOT / "scripts" / "send-webmentions.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class Stub:
    """A tiny HTTP site on 127.0.0.1.

    routes maps a path to (status, [(header, value)], body-bytes), or to a callable
    (method, full_path, body) -> that tuple. Every request is appended to .log as
    (method, full_path, body-text).
    """

    def __init__(self):
        self.routes = {}
        self.log = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def _serve(self, method):
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n).decode() if n else ""
                stub.log.append((method, self.path, body))
                route = stub.routes.get(urllib.parse.urlsplit(self.path).path)
                if route is None:
                    route = (404, [], b"not found")
                elif callable(route):
                    route = route(method, self.path, body)
                status, headers, payload = route
                self.send_response(status)
                for k, v in headers:
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                if method != "HEAD":
                    self.wfile.write(payload)

            def do_GET(self):
                self._serve("GET")

            def do_POST(self):
                self._serve("POST")

            def log_message(self, *a):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def html(self, path, body, headers=()):
        self.routes[path] = (200, [("Content-Type", "text/html; charset=utf-8"), *headers],
                             body.encode())

    def requests(self, method=None):
        return [r for r in self.log if method is None or r[0] == method]

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def stub_feed(stub, essay_path="/fa/essay/", published=None):
    published = published or datetime.now(timezone.utc)
    xml = (f'<rss version="2.0"><channel><item><title>T</title>'
           f'<link>{stub.base}{essay_path}</link>'
           f'<pubDate>{format_datetime(published)}</pubDate></item></channel></rss>')
    stub.routes["/feed.xml"] = (200, [("Content-Type", "application/rss+xml")], xml.encode())


# What `hugo --minify` actually emits: unquoted single-token attributes, trailing-slash hrefs.
def minified_essay(stub, targets, outside="/outside/"):
    links = "".join(f"<a href={t}>x</a>" for t in targets)
    return ("<!doctype html><html><body><main><article class=h-entry>"
            "<h1 class=p-name>T</h1><div class=e-content><p>"
            f"{links}</p></div></article>"
            f"<nav><a href={stub.base}{outside}>elsewhere</a></nav></main></body></html>")


class BuiltPages(unittest.TestCase):
    def setUp(self):
        if not PUBLIC.is_dir():
            self.fail("public/ is missing: run `hugo --minify` before this test")

    def test_newest_essay_yields_external_links_only(self):
        url, _ = m.newest_essay((PUBLIC / "fa" / "index.xml").read_text())
        slug = urllib.parse.urlsplit(url).path.strip("/")
        page = (PUBLIC / slug / "index.html").read_text()
        links = m.entry_links(page)
        self.assertIsNotNone(links, "the newest essay has no h-entry")
        targets = m.external_targets(links, url)
        self.assertTrue(targets)
        self.assertEqual(len(targets), len(set(targets)))
        for t in targets:
            self.assertNotIn("falkensmage.com", urllib.parse.urlsplit(t).hostname)

    def test_fa_page_is_not_an_entry(self):
        page = (PUBLIC / "fa" / "about" / "index.html").read_text()
        self.assertIsNone(m.entry_links(page))


class Targets(unittest.TestCase):
    SRC = "https://falkensmage.com/fa/essay/"

    def test_host_matching_is_on_a_dot_boundary(self):
        got = m.external_targets([
            "https://notfalkensmage.com/a", "https://falkensmage.com.evil.net/b",
            "https://www.falkensmage.com/c", "https://falkensmage.com/d", "https://falkensmage.com./e",
        ], self.SRC)
        self.assertEqual(got, ["https://notfalkensmage.com/a", "https://falkensmage.com.evil.net/b"])

    def test_dropped_kinds(self):
        got = m.external_targets([
            "/relative", "#frag", self.SRC, self.SRC + "#notes", "mailto:a@b.c",
            "javascript:void(0)", "https://[bad", "https://ok.example/x", "https://ok.example/x",
        ], self.SRC)
        self.assertEqual(got, ["https://ok.example/x"])

    def test_empty_h_entry_is_empty_list_not_none(self):
        self.assertEqual(m.entry_links("<article class=h-entry><p>none</p></article>"), [])
        self.assertIsNone(m.entry_links("<article><a href=x>y</a></article>"))

    def test_unclosed_and_void_elements_do_not_end_scope(self):
        page = ("<article class=h-entry><p>one<br><img src=a><p>two <a href=https://a.example/>a</a>"
                "</article><a href=https://b.example/>b</a>")
        self.assertEqual(m.entry_links(page), ["https://a.example/"])


class Tracer(unittest.TestCase):
    def setUp(self):
        self.stub = Stub()
        self.addCleanup(self.stub.close)

    def test_main_posts_one_webmention_for_the_entry_link(self):
        s = self.stub
        stub_feed(s)
        target = f"{s.base}/target/"
        s.html("/fa/essay/", minified_essay(s, [target]))
        s.html("/target/", "<link rel=webmention href=/wm>")
        s.routes["/wm"] = (202, [], b"")
        s.routes["/outside/"] = (200, [("Content-Type", "text/html")], b"<link rel=webmention href=/wm>")
        with mock.patch.object(m, "FEED", f"{s.base}/feed.xml"):
            m.main()
        posts = s.requests("POST")
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0][1], "/wm")
        self.assertEqual(urllib.parse.parse_qs(posts[0][2], strict_parsing=True),
                         {"source": [f"{s.base}/fa/essay/"], "target": [target]})
        self.assertFalse([r for r in s.log if r[1].startswith("/outside")],
                         "a link outside the h-entry was fetched")


if __name__ == "__main__":
    unittest.main()
