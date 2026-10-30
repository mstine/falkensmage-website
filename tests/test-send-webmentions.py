#!/usr/bin/env python3
"""Tests for scripts/send-webmentions.py. Needs a built site first:

    hugo --minify && python3 -I -S -B tests/test-send-webmentions.py

-I -S proves the sender is stdlib-only by execution. A missing public/ is a failure, never a
skip, so the built-page check cannot silently vanish. Everything else runs against a stub
HTTP server on 127.0.0.1; there is no outbound network.
"""
import contextlib
import importlib.util
import io
import os
import socket
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"
FIXTURES = ROOT / "tests" / "fixtures" / "webmention"

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
        threading.Thread(target=lambda: self.server.serve_forever(0.01), daemon=True).start()

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



# --- everything below needs loopback, so the address guard is patched open ---------------

class LoopbackCase(unittest.TestCase):
    """A stub site, with the real address guard patched to allow loopback."""

    def setUp(self):
        self.stub = Stub()
        self.addCleanup(self.stub.close)
        p = mock.patch.object(m, "peer_allowed", return_value=True)
        p.start()
        self.addCleanup(p.stop)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.state = os.path.join(tmp.name, "sent")
        sp = mock.patch.object(m, "STATE", self.state)
        sp.start()
        self.addCleanup(sp.stop)
        fp = mock.patch.object(m, "FEED", f"{self.stub.base}/feed.xml")
        fp.start()
        self.addCleanup(fp.stop)

    def run_main(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            m.main(entry_wait=0)
        return out.getvalue()

    def posts(self, path):
        return [r for r in self.stub.requests("POST") if r[1] == path]

    def state_lines(self):
        if not os.path.exists(self.state):
            return []
        with open(self.state) as f:
            return f.read().splitlines()


class Tracer(LoopbackCase):
    def test_main_posts_one_webmention_for_the_entry_link(self):
        s = self.stub
        stub_feed(s)
        target = f"{s.base}/target/"
        s.html("/fa/essay/", minified_essay(s, [target]))
        s.html("/target/", "<link rel=webmention href=/wm>")
        s.routes["/wm"] = (202, [], b"")
        s.html("/outside/", "<link rel=webmention href=/wm>")
        self.run_main()
        posts = s.requests("POST")
        self.assertEqual(len(posts), 1)
        self.assertEqual(posts[0][1], "/wm")
        self.assertEqual(urllib.parse.parse_qs(posts[0][2], strict_parsing=True),
                         {"source": [f"{s.base}/fa/essay/"], "target": [target]})
        self.assertFalse([r for r in s.log if r[1].startswith("/outside")],
                         "a link outside the h-entry was fetched")


# --- discovery conformance --------------------------------------------------------------
# Ported from popov's FunctionsTest.kt (the 17 webmention.rocks discovery fixtures), but over
# real HTTP sockets instead of mocks.
#
# Where this deliberately disagrees with popov: its composeWebmentionRequest uses `ifBlank` to
# append "/webmention", and its test for #15 asserts /test/15/webmention. That is wrong. An
# empty href is a relative reference, and it resolves to the base URL (RFC 3986 section 5.2);
# the fixture's own text says "the page is its own Webmention endpoint". We follow the spec,
# so #15 resolves to /test/15. popov's suite also stops at #17; #18 through #23 below are new.

class Conformance(LoopbackCase):
    def serve_fixture(self, n, *headers):
        text = (FIXTURES / f"discovery-test-{n}.html").read_text(encoding="utf-8")
        # popov's WireMock templates {{request.baseUrl}}; we substitute at serve time.
        self.stub.html(f"/test/{n}", text.replace("{{request.baseUrl}}", self.stub.base), headers)
        return f"{self.stub.base}/test/{n}"

    def check(self, n, *headers, endpoint=None):
        target = self.serve_fixture(n, *headers)
        want = endpoint if endpoint is not None else f"{self.stub.base}/test/{n}/webmention"
        self.assertEqual(m.discover(target), want, f"fixture {n}")

    def test_html_only_fixtures(self):
        for n in (3, 4, 5, 6, 9, 12, 13, 14, 16, 17):
            with self.subTest(n=n):
                self.check(n)

    def test_header_fixtures(self):
        b = self.stub.base
        cases = {
            1: ("Link", "</test/1/webmention>; rel=webmention"),
            2: ("Link", f"<{b}/test/2/webmention>; rel=webmention"),
            7: ("LinK", f"<{b}/test/7/webmention>; rel=webmention"),
            8: ("Link", f'<{b}/test/8/webmention>; rel="webmention"'),
            10: ("Link", f'<{b}/test/10/webmention>; rel="webmention somethingelse"'),
            11: ("Link", '</test/11/webmention>; rel="webmention"'),
        }
        for n, header in cases.items():
            with self.subTest(n=n):
                self.check(n, header)

    def test_11_header_beats_both_error_links_in_the_html(self):
        text = (FIXTURES / "discovery-test-11.html").read_text(encoding="utf-8")
        self.assertEqual(text.count("/test/11/webmention/error"), 2)
        self.check(11, ("Link", '</test/11/webmention>; rel="webmention"'))

    def test_15_empty_href_is_the_page_itself(self):
        self.check(15, endpoint=f"{self.stub.base}/test/15")

    def test_18_two_link_headers(self):
        self.stub.html("/test/18", "", [("Link", "</nope>; rel=other"),
                                        ("Link", "</test/18/webmention>; rel=webmention")])
        self.assertEqual(m.discover(f"{self.stub.base}/test/18"), f"{self.stub.base}/test/18/webmention")

    def test_19_comma_joined_header(self):
        self.stub.html("/test/19", "", [("Link", "</nope>; rel=other, </test/19/webmention>; rel=webmention")])
        self.assertEqual(m.discover(f"{self.stub.base}/test/19"), f"{self.stub.base}/test/19/webmention")

    def test_20_element_without_href_is_skipped(self):
        self.stub.html("/test/20", '<a rel=webmention>no href</a>'
                                   '<link rel=webmention href="/test/20/webmention">')
        self.assertEqual(m.discover(f"{self.stub.base}/test/20"), f"{self.stub.base}/test/20/webmention")

    def test_21_query_string_survives_and_stays_out_of_the_body(self):
        s = self.stub
        s.html("/test/21", '<link rel=webmention href="/test/21/webmention?token=abc">')
        s.routes["/test/21/webmention"] = (201, [], b"")
        endpoint = m.discover(f"{s.base}/test/21")
        self.assertEqual(endpoint, f"{s.base}/test/21/webmention?token=abc")
        self.assertEqual(m.notify(endpoint, "https://src.example/p/", f"{s.base}/test/21"), 201)
        method, path, body = s.requests("POST")[0]
        self.assertEqual(path, "/test/21/webmention?token=abc")
        self.assertEqual(urllib.parse.parse_qs(body, strict_parsing=True),
                         {"source": ["https://src.example/p/"], "target": [f"{s.base}/test/21"]})

    def test_22_relative_endpoint_resolves_against_the_page_path(self):
        self.stub.html("/test/22/page", '<link rel=webmention href="endpoint">')
        self.assertEqual(m.discover(f"{self.stub.base}/test/22/page"), f"{self.stub.base}/test/22/endpoint")

    def test_23_relative_endpoint_resolves_against_the_final_url(self):
        s = self.stub
        s.routes["/test/23"] = (302, [("Location", "/test/23/redirected/page")], b"")
        s.html("/test/23/redirected/page", '<link rel=webmention href="endpoint">')
        self.assertEqual(m.discover(f"{s.base}/test/23"), f"{s.base}/test/23/redirected/endpoint")


class LinkHeader(unittest.TestCase):
    def test_grammar(self):
        f = m.endpoint_from_links
        self.assertEqual(f(["<https://a.example/x,y>; rel=webmention"]), "https://a.example/x,y")
        self.assertIsNone(f(['<https://a.example/p>; title="rel=webmention"; rel=other']))
        self.assertEqual(f(['<https://a.example/p>; REL="Other WebMention"']), "https://a.example/p")
        self.assertIsNone(f(["<https://a.example/p>; rel=not-webmention"]))
        self.assertEqual(f(['<https://a.example/a>; title="x, <y>"; rel=webmention']), "https://a.example/a")
        self.assertEqual(f(["<>; rel=webmention"]), "")
        self.assertIsNone(f(["garbage", "", "<unterminated"]))


# --- the address guard ------------------------------------------------------------------

class PeerAllowed(unittest.TestCase):
    def test_refuses_everything_non_global(self):
        for ip in ("127.0.0.1", "::1", "10.0.0.1", "172.16.0.1", "192.168.1.1", "169.254.169.254",
                   "100.64.0.1", "0.0.0.0", "::", "::ffff:127.0.0.1", "::ffff:10.0.0.1", "fc00::1",
                   "fe80::1", "fe80::1%en0", "224.0.0.1", "64:ff9b::7f00:1", "garbage", ""):
            with self.subTest(ip=ip):
                self.assertFalse(m.peer_allowed(ip))

    def test_allows_global(self):
        for ip in ("8.8.8.8", "2606:4700:4700::1111", "::ffff:8.8.8.8"):
            with self.subTest(ip=ip):
                self.assertTrue(m.peer_allowed(ip))


class RealGuard(unittest.TestCase):
    """No patching: the real guard against live sockets."""

    def setUp(self):
        self.stub = Stub()
        self.addCleanup(self.stub.close)
        self.stub.html("/", "<p>secret</p>")

    def test_loopback_by_address_and_by_name_never_reaches_the_server(self):
        port = self.stub.server.server_address[1]
        for url in (f"http://127.0.0.1:{port}/", f"http://localhost:{port}/"):
            with self.subTest(url=url):
                with self.assertRaises(urllib.error.URLError):
                    m.fetch(url)
        self.assertEqual(self.stub.log, [])

    def test_notify_to_loopback_never_posts(self):
        with self.assertRaises(urllib.error.URLError):
            m.notify(f"{self.stub.base}/wm", "https://a.example/", "https://b.example/")
        self.assertEqual(self.stub.log, [])

    def test_redirect_to_a_blocked_hop_is_refused(self):
        first, second = Stub(), Stub()
        self.addCleanup(first.close)
        self.addCleanup(second.close)
        first.routes["/start"] = (302, [("Location", f"{second.base}/secret")], b"")
        second.html("/secret", "secret")
        with mock.patch.object(m, "peer_allowed", side_effect=[True, False]):
            with self.assertRaises(urllib.error.URLError):
                m.fetch(f"{first.base}/start")
        self.assertEqual(len(first.log), 1)
        self.assertEqual(second.log, [])


class Schemes(LoopbackCase):
    def test_file_and_ftp_endpoints_raise(self):
        for endpoint in ("file:///etc/hosts", "ftp://127.0.0.1/x", "gopher://127.0.0.1/x", "data:,x"):
            with self.subTest(endpoint=endpoint):
                with self.assertRaises(urllib.error.URLError):
                    m.notify(endpoint, "https://a.example/", "https://b.example/")
                with self.assertRaises(urllib.error.URLError):
                    m.fetch(endpoint)

    def test_get_redirect_to_file_or_ftp_raises(self):
        for loc in ("file:///etc/hosts", "ftp://127.0.0.1/x"):
            with self.subTest(loc=loc):
                self.stub.routes["/r"] = (302, [("Location", loc)], b"")
                with self.assertRaises(urllib.error.URLError):
                    m.fetch(f"{self.stub.base}/r")

    def test_post_answered_with_302_is_a_failure_and_never_followed(self):
        s = self.stub
        s.routes["/wm"] = (302, [("Location", f"{s.base}/secret")], b"")
        s.html("/secret", "secret")
        with self.assertRaises(urllib.error.HTTPError):
            m.notify(f"{s.base}/wm", "https://a.example/", "https://b.example/")
        self.assertEqual([r[1] for r in s.log], ["/wm"])


# --- the unattended batch ---------------------------------------------------------------

def closed_port_url():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return f"http://127.0.0.1:{sock.getsockname()[1]}/gone/"


class Batch(LoopbackCase):
    def build(self):
        s = self.stub
        stub_feed(s)
        dead, bad, live = closed_port_url(), f"{s.base}/bad/", f"{s.base}/live/"
        s.html("/fa/essay/", minified_essay(s, [dead, bad, live]))
        s.html("/bad/", "<link rel=webmention href=/wm500>")
        s.routes["/wm500"] = (500, [], b"boom")
        s.html("/live/", "<link rel=webmention href=/wm>")
        s.routes["/wm"] = (200, [], b"")
        return dead, bad, live

    def test_dead_and_failing_targets_do_not_stop_the_batch(self):
        dead, bad, live = self.build()
        out = self.run_main()  # returns normally
        self.assertEqual(len(self.posts("/wm")), 1)
        self.assertEqual(len(self.posts("/wm500")), 1)
        self.assertEqual(self.state_lines(), [f"{self.stub.base}/fa/essay/\t{live}"])
        self.assertIn(f"failed: {dead}", out)
        self.assertIn(f"failed: {bad}", out)

    def test_second_run_sends_nothing_and_retries_failures(self):
        self.build()
        self.run_main()
        out = self.run_main()
        self.assertEqual(len(self.posts("/wm")), 1)
        self.assertEqual(len(self.posts("/wm500")), 2, "a failed target is retried on the next run")
        self.assertIn("1 pairs loaded from state", out)
        self.assertIn("1 already sent", out)

    def test_state_survives_a_crash_mid_batch(self):
        s = self.stub
        stub_feed(s)
        s.html("/fa/essay/", minified_essay(s, [f"{s.base}/live/", f"{s.base}/live2/"]))
        s.html("/live/", "<link rel=webmention href=/wm>")
        s.html("/live2/", "<link rel=webmention href=/wm>")
        s.routes["/wm"] = (200, [], b"")
        with mock.patch.object(m, "notify", side_effect=[200, KeyboardInterrupt]):
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
                m.main(entry_wait=0)
        self.assertEqual(len(self.state_lines()), 1)

    def test_dry_run_posts_nothing_and_writes_no_state(self):
        self.build()
        with mock.patch.dict(os.environ, {"DRY_RUN": "1"}):
            self.run_main()
        self.assertEqual(self.stub.requests("POST"), [])
        self.assertFalse(os.path.exists(self.state))

    def test_state_file_exists_after_a_run_even_with_nothing_sent(self):
        stub_feed(self.stub)
        self.stub.html("/fa/essay/", minified_essay(self.stub, []))
        self.run_main()
        self.assertTrue(os.path.exists(self.state))


class Window(LoopbackCase):
    NOW = datetime(2026, 11, 2, 18, 0, tzinfo=timezone.utc)

    def test_decide(self):
        self.assertEqual(m.decide(self.NOW - timedelta(days=6, hours=23), self.NOW), "send")
        self.assertEqual(m.decide(self.NOW - timedelta(days=7, seconds=1), self.NOW), "skip-old")

    def test_old_essay_sends_nothing_and_fetches_nothing_but_the_feed(self):
        s = self.stub
        stub_feed(s, published=datetime.now(timezone.utc) - timedelta(days=8))
        s.html("/fa/essay/", minified_essay(s, [f"{s.base}/live/"]))
        s.html("/live/", "<link rel=webmention href=/wm>")
        out = self.run_main()
        self.assertIn("skip-old", out)
        self.assertEqual([r[1] for r in s.log], ["/feed.xml"])
        self.assertTrue(os.path.exists(self.state))


class SourcePage(LoopbackCase):
    def test_page_that_never_gains_an_h_entry_exits_nonzero(self):
        stub_feed(self.stub)
        self.stub.html("/fa/essay/", "<html><body><article><a href=https://x.example/>x</a></article></body></html>")
        with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as cm:
            m.main(entry_wait=0)
        self.assertNotIn(cm.exception.code, (0, None))
        self.assertEqual(self.stub.requests("POST"), [])

    def test_page_that_gains_its_h_entry_after_a_stale_response_is_used(self):
        s = self.stub
        stub_feed(s)
        target = f"{s.base}/live/"
        s.html("/live/", "<link rel=webmention href=/wm>")
        s.routes["/wm"] = (200, [], b"")
        hits = []

        def essay(method, path, body):
            hits.append(1)
            page = "<html><body>old build</body></html>" if len(hits) < 3 else minified_essay(s, [target])
            return 200, [("Content-Type", "text/html")], page.encode()

        s.routes["/fa/essay/"] = essay
        self.run_main()
        self.assertEqual(len(hits), 3)
        self.assertEqual(len(self.posts("/wm")), 1)

    def test_feed_unreachable_or_empty_exits_nonzero(self):
        with self.assertRaises(SystemExit):
            self.run_main()  # /feed.xml is a 404
        self.stub.routes["/feed.xml"] = (200, [], b"<rss><channel></channel></rss>")
        with self.assertRaises(SystemExit):
            self.run_main()


if __name__ == "__main__":
    unittest.main()
