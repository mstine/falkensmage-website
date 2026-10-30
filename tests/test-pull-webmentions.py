#!/usr/bin/env python3
"""Tests for scripts/pull-webmentions.py, the mention section, and the probe that guards them.

    python3 -I -S -B tests/test-pull-webmentions.py

-I -S proves the puller is stdlib-only by execution. There is no outbound network: the API is
a stub on 127.0.0.1, and every Hugo build carries `[security.http] urls = ["^$"]` so the
theme's remote fetch is denied. `hugo` must be on PATH: its absence is a failure, never a
skip, so the render checks cannot silently vanish.
"""
import contextlib
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import threading
import unicodedata
import unittest
import urllib.parse
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "webmention"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


m = load("pull_webmentions", "pull-webmentions.py")
sender = load("send_webmentions", "send-webmentions.py")

ESSAY = "https://falkensmage.com/fa/youve-been-heard/"
ESSAY_PATH = "/fa/youve-been-heard/"


class Stub:
    """A tiny HTTP server on 127.0.0.1.

    routes maps a path to (status, [(header, value)], body-bytes), or to a callable
    (method, full_path, headers) -> that tuple. Every request is appended to .log as
    (method, full_path, headers-dict).
    """

    def __init__(self):
        self.routes = {}
        self.log = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.0"

            def do_GET(self):
                headers = {k.lower(): v for k, v in self.headers.items()}
                stub.log.append(("GET", self.path, headers))
                route = stub.routes.get(urllib.parse.urlsplit(self.path).path)
                if route is None:
                    route = (404, [], b"not found")
                elif callable(route):
                    route = route("GET", self.path, headers)
                status, hdrs, payload = route
                self.send_response(status)
                for k, v in hdrs:
                    self.send_header(k, v)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *a):
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=lambda: self.server.serve_forever(0.01), daemon=True).start()

    @property
    def api(self):
        return self.base + "/api/mentions.jf2"

    def json(self, path, doc, status=200):
        self.routes[path] = (status, [("Content-Type", "application/json")],
                             json.dumps(doc).encode())

    def close(self):
        self.server.shutdown()
        self.server.server_close()


def child(wm_id, prop, name, target=ESSAY, **extra):
    c = {"type": "entry", "wm-id": wm_id, "wm-property": prop, "wm-target": target,
         "wm-source": f"https://{name.lower()}.example/{wm_id}", "wm-private": False,
         "url": f"https://{name.lower()}.example/{wm_id}",
         "author": {"type": "card", "name": name, "url": f"https://{name.lower()}.example/"},
         "published": "2026-03-02T10:00:00+00:00"}
    c.update(extra)
    return c


def feed(children, per_page=1000, total=None):
    total = len(children) if total is None else total
    return {"type": "feed", "name": "Webmentions",
            "paging": {"per-page": per_page, "page": 0, "total": total,
                       "total-pages": max(1, -(-total // per_page))},
            "children": children}


def build_site(dest, data_dir=None, layouts_dir=None, work=None):
    """Build the real site into dest with `hugo --minify`, offline. data_dir is mounted over
    data/ (the repo's own webmentions.json is always excluded, so a local generated file
    cannot leak in); layouts_dir overrides the theme's layouts."""
    work = Path(work or tempfile.mkdtemp())
    mounts = ['[security.http]', 'urls = ["^$"]',
              '[[module.mounts]]', f'source = {json.dumps(str(ROOT / "data"))}',
              'target = "data"', 'files = ["! webmentions.json"]']
    if data_dir is not None:
        mounts += ['[[module.mounts]]', f'source = {json.dumps(str(data_dir))}', 'target = "data"']
    if layouts_dir is not None:
        mounts += ['[[module.mounts]]', f'source = {json.dumps(str(layouts_dir))}',
                   'target = "layouts"']
    conf = work / "mounts.toml"
    conf.write_text("\n".join(mounts) + "\n")
    hugo = shutil.which("hugo")
    if hugo is None:
        raise AssertionError("hugo is not on PATH: the render checks must not silently vanish")
    r = subprocess.run([hugo, "--minify", "--config", f"hugo.toml,{conf}",
                        "--destination", str(dest), "--cacheDir", str(work / "cache")],
                       cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"hugo failed ({r.returncode}):\n{r.stderr[-2000:]}")
    return work


class Section(HTMLParser):
    """Reads the fa-mentions element: how many there are, the tags and attributes inside
    each, the anchors, and the text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.sections = 0
        self.tag = None
        self.depth = 0
        self.tags = []
        self.attrs = []      # (tag, {attr: value}) for every element inside
        self.anchors = []    # (href, rel, text)
        self.text = []
        self._a = None

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        if self.tag is None:
            if "fa-mentions" in a.get("class", "").split():
                self.sections += 1
                self.tag, self.depth = tag, 1
            return
        if tag == self.tag:
            self.depth += 1
        self.tags.append(tag)
        self.attrs.append((tag, a))
        if tag == "a":
            self._a = [a.get("href"), a.get("rel"), ""]

    def handle_endtag(self, tag):
        if self.tag is None:
            return
        if tag == "a" and self._a is not None:
            self.anchors.append(tuple(self._a))
            self._a = None
        if tag == self.tag:
            self.depth -= 1
            if self.depth == 0:
                self.tag = None

    def handle_data(self, data):
        if self.tag is not None:
            self.text.append(data)
            if self._a is not None:
                self._a[2] += data


def section_of(path):
    p = Section()
    p.feed(Path(path).read_text(encoding="utf-8"))
    p.close()
    return p


class Tracer(unittest.TestCase):
    """Stub API -> main() -> data file -> real Hugo build -> page."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.stub = Stub()
        cls.stub.json("/api/mentions.jf2", feed([
            child(1, "like-of", "Ada"),
            child(2, "repost-of", "Bo"),
            child(3, "in-reply-to", "Cy", content={"text": "hello <b>x</b> there",
                                                   "html": "<p>hello</p>"}),
            child(4, "like-of", "Dee", target="https://falkensmage.com/fa/about/"),
        ]))
        cls.data = cls.tmp / "data"
        with mock.patch.object(m, "API", cls.stub.api), mock.patch.object(m, "DATA",
                                                                          cls.data / "webmentions.json"), \
                mock.patch.dict(os.environ, {"WEBMENTION_IO_TOKEN": "tok_abc123"}), \
                contextlib.redirect_stdout(io.StringIO()):
            cls.rc = m.main()
        cls.with_data = cls.tmp / "with"
        cls.without = cls.tmp / "without"
        work = build_site(cls.with_data, cls.data)
        build_site(cls.without, None, work=work)

    @classmethod
    def tearDownClass(cls):
        cls.stub.close()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_main_writes_page_keyed_data(self):
        self.assertEqual(self.rc, 0)
        doc = json.loads((self.data / "webmentions.json").read_text())
        self.assertIn(ESSAY_PATH, doc["pages"])
        self.assertEqual([r["name"] for r in doc["pages"][ESSAY_PATH]["likes"]], ["Ada"])
        self.assertIn("/fa/about/", doc["pages"])

    def test_token_is_a_header_not_a_url(self):
        req = [r for r in self.stub.log if r[1].startswith("/api/mentions.jf2")][0]
        self.assertEqual(req[2]["authorization"], "Bearer tok_abc123")
        self.assertNotIn("tok_abc123", req[1])

    def test_essay_renders_one_section_with_names_and_text(self):
        sec = section_of(self.with_data / "fa" / "youve-been-heard" / "index.html")
        self.assertEqual(sec.sections, 1)
        names = [a[2] for a in sec.anchors]
        self.assertEqual(names, ["Ada", "Bo", "Cy"])
        self.assertIn("hello <b>x</b> there", "".join(sec.text))

    def test_reply_markup_is_text_not_elements(self):
        sec = section_of(self.with_data / "fa" / "youve-been-heard" / "index.html")
        self.assertNotIn("b", sec.tags)
        self.assertEqual(set(sec.tags) - {"h2", "p", "ul", "li", "a", "span", "time"}, set())

    def test_every_anchor_is_nofollow_ugc_and_no_image_loads(self):
        sec = section_of(self.with_data / "fa" / "youve-been-heard" / "index.html")
        for href, rel, _ in sec.anchors:
            self.assertEqual(set(rel.split()), {"nofollow", "ugc"})
            self.assertTrue(href.startswith("https://"))
        self.assertNotIn("img", sec.tags)

    def test_essay_without_mentions_is_byte_identical_to_a_no_data_build(self):
        a = (self.with_data / "fa" / "both-hands" / "index.html").read_bytes()
        b = (self.without / "fa" / "both-hands" / "index.html").read_bytes()
        self.assertEqual(a, b)

    def test_a_standalone_page_never_gets_a_section(self):
        self.assertEqual(section_of(self.with_data / "fa" / "about" / "index.html").sections, 0)

    def test_head_advertises_the_endpoint(self):
        class Head(HTMLParser):
            found = []

            def handle_starttag(self, tag, attrs):
                a = {k: (v or "") for k, v in attrs}
                if tag == "link" and "webmention" in a.get("rel", "").split():
                    self.found.append(a.get("href"))
        for page in ("index.html", "fa/youve-been-heard/index.html"):
            h = Head()
            h.found = []
            h.feed((self.with_data / page).read_text())
            self.assertEqual(h.found, ["https://webmention.io/falkensmage.com/webmention"], page)

    def test_the_sender_never_sees_a_mention_url(self):
        page = (self.with_data / "fa" / "youve-been-heard" / "index.html").read_text()
        links = sender.entry_links(page)
        self.assertTrue(links)
        for link in links:
            self.assertNotIn(".example/", link)

    def test_partial_never_marks_text_safe(self):
        src = (ROOT / "themes" / "arcaeon" / "layouts" / "partials" / "fa" / "mentions.html"
               ).read_text()
        code = re.sub(r"\{\{-?\s*/\*.*?\*/\s*-?\}\}", "", src, flags=re.S)
        self.assertIsNone(re.search(r"safe(HTML|HTMLAttr|CSS|JS|JSStr|URL)", code, re.I))


TOKEN = "tok_abc123"
EXAMPLE = json.loads((FIXTURES / "example-mentions.jf2.json").read_text())
HOSTILE = json.loads((FIXTURES / "hostile-mentions.jf2.json").read_text())


def rec(name="N", url="https://n.example/1", **kw):
    r = {"name": name, "url": url, "source": url, "author_url": ""}
    r.update(kw)
    return r


def paged(children, per_page=1000):
    """A route that serves `children` the way webmention.io pages them, by ?page=."""
    def route(method, path, headers):
        q = urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)
        page = int(q.get("page", ["0"])[0])
        total = len(children)
        doc = feed(children[page * per_page:(page + 1) * per_page], per_page, total)
        doc["paging"]["page"] = page
        return 200, [("Content-Type", "application/json")], json.dumps(doc).encode()
    return route


class PullCase(unittest.TestCase):
    """A stub API, a temp data dir and blocklist, no sleeping between retries."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.stub = Stub()
        self.addCleanup(self.stub.close)
        self.data = self.tmp / "webmentions.json"
        self.block = self.tmp / "blocklist.json"
        self.set_blocklist([], [])
        for p in (mock.patch.object(m, "API", self.stub.api), mock.patch.object(m, "DATA", self.data),
                  mock.patch.object(m, "BLOCKLIST", self.block), mock.patch.object(m, "WAIT", 0),
                  mock.patch.dict(os.environ, {"WEBMENTION_IO_TOKEN": TOKEN})):
            p.start()
            self.addCleanup(p.stop)

    def set_blocklist(self, domains, authors):
        self.block.write_text(json.dumps({"domains": domains, "authors": authors}))

    def seed(self, pages, generated="2026-01-01T00:00:00Z"):
        m.write_data(self.data, pages, generated)

    def disk(self):
        return json.loads(self.data.read_text())

    def run_main(self):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            rc = m.main()
        return rc, buf.getvalue()

    def api_requests(self):
        return [r for r in self.stub.log if r[1].startswith("/api/mentions.jf2")]

    def leftovers(self):
        return sorted(p.name for p in self.tmp.iterdir())


LAST_GOOD = {ESSAY_PATH: {"likes": [rec("Ada", "https://ada.example/1")],
                          "replies": [rec("Bo", "https://bo.example/1", text="hi",
                                          date="2026-03-02", date_text="March 2, 2026")]}}


class Pagination(PullCase):
    def test_2500_mentions_take_three_requests_in_order(self):
        kids = [child(i, "like-of", f"P{i}") for i in range(1, 2501)]
        self.stub.routes["/api/mentions.jf2"] = paged(kids)
        got = m.pull_all(TOKEN)
        self.assertEqual([c["wm-id"] for c in got], list(range(1, 2501)))
        reqs = self.api_requests()
        self.assertEqual(len(reqs), 3)
        for n, (_, path, _) in enumerate(reqs):
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)
            self.assertEqual(q["domain"], ["falkensmage.com"])
            self.assertEqual(q["per-page"], ["1000"])
            self.assertEqual(q["sort-dir"], ["up"])
            self.assertEqual(q["page"], [str(n)])

    def test_short_walk_fails_and_keeps_last_good(self):
        self.seed(LAST_GOOD)
        kids = [child(i, "like-of", f"P{i}") for i in range(1, 2001)]

        def route(method, path, headers):
            q = urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)
            page = int(q["page"][0])
            doc = feed(kids[page * 1000:(page + 1) * 1000], 1000, 2500)
            doc["paging"]["total-pages"] = 3
            return 200, [], json.dumps(doc).encode()
        self.stub.routes["/api/mentions.jf2"] = route
        rc, out = self.run_main()
        self.assertEqual(rc, m.PULL_FAILED)
        self.assertIn("short walk", out)
        self.assertEqual(self.disk()["pages"], LAST_GOOD)
        self.assertEqual(self.disk()["generated"], "2026-01-01T00:00:00Z")

    def test_overlapping_pages_dedupe_by_wm_id(self):
        pages = {"0": [child(1, "like-of", "A"), child(2, "like-of", "B")],
                 "1": [child(2, "like-of", "B"), child(3, "like-of", "C")]}

        def route(method, path, headers, total=3):
            page = urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)["page"][0]
            doc = feed(pages[page], 2, total)
            return 200, [], json.dumps(doc).encode()
        self.stub.routes["/api/mentions.jf2"] = route
        self.assertEqual([c["wm-id"] for c in m.pull_all(TOKEN)], [1, 2, 3])
        self.stub.routes["/api/mentions.jf2"] = lambda *a: route(*a, total=4)
        with self.assertRaises(m.PullError):
            m.pull_all(TOKEN)

    def test_missing_paging_fails(self):
        doc = feed([child(1, "like-of", "A")])
        del doc["paging"]
        self.stub.json("/api/mentions.jf2", doc)
        with self.assertRaises(m.PullError):
            m.pull_all(TOKEN)


class Shape(PullCase):
    def test_a_child_missing_a_required_field_fails(self):
        for field in ("wm-id", "wm-target", "wm-source"):
            with self.subTest(field=field):
                c = child(1, "like-of", "A")
                del c[field]
                self.stub.json("/api/mentions.jf2", feed([c]))
                with self.assertRaises(m.PullError) as cm:
                    m.pull_all(TOKEN)
                self.assertIn(field, str(cm.exception))

    def test_no_child_with_wm_property_fails_but_one_without_is_other(self):
        c = child(1, "like-of", "A")
        del c["wm-property"]
        self.stub.json("/api/mentions.jf2", feed([c]))
        with self.assertRaises(m.PullError):
            m.pull_all(TOKEN)
        self.stub.json("/api/mentions.jf2", feed([c, child(2, "like-of", "B")]))
        kids = m.pull_all(TOKEN)
        pages, counts = m.normalize(kids)
        self.assertEqual(counts["other"], 1)
        self.assertEqual(len(pages[ESSAY_PATH]["likes"]), 1)


class Normalize(unittest.TestCase):
    def test_example_fixture(self):
        pages, counts = m.normalize(EXAMPLE["children"])
        p = pages[ESSAY_PATH]
        self.assertEqual((len(p["likes"]), len(p["reposts"]), len(p["replies"])), (1, 1, 4))
        self.assertEqual(counts["other"], 14)
        self.assertEqual(counts["private"], 1)
        blob = json.dumps(pages)
        self.assertNotIn("lunarheron.example/private/reply", blob)  # id 1018, the private one
        bridged = [r for r in p["replies"] if r["source"].startswith("https://bridge.example/")]
        self.assertEqual(len(bridged), 1)
        self.assertTrue(bridged[0]["url"].startswith("https://social.example/"))

    def test_hostile_fixture(self):
        pages, counts = m.normalize(HOSTILE["children"])
        p = pages[ESSAY_PATH]
        self.assertEqual((len(p["likes"]), len(p["reposts"]), len(p["replies"])), (6, 1, 7))
        self.assertEqual(counts["private"], 1)
        blob = json.dumps(pages, ensure_ascii=False)
        for bad in ("HTMLSENTINEL", "PHOTOSENTINEL", "PRIVATESENTINEL", "javascript:", "data:text",
                    "/relative/"):
            self.assertNotIn(bad, blob)
        for r in [x for kind in p.values() for x in kind]:
            self.assertTrue(r["url"].startswith("https://"), r)
            self.assertTrue(r["name"])
            for field in ("name", "text"):
                for ch in r.get(field, ""):
                    self.assertNotEqual(unicodedata.category(ch), "Cc")
                    self.assertNotIn(ord(ch), range(0x202A, 0x202F))
                    self.assertNotIn(ord(ch), range(0x2066, 0x206A))
        by_name = {r["name"]: r for kind in p.values() for r in kind}
        self.assertEqual(by_name["Jay"]["url"], "https://js.example/a")
        self.assertEqual(by_name["Dana"]["url"], "https://data.example/b")
        self.assertEqual(by_name["Rel"]["url"], "https://rel.example/c")
        self.assertIn("anon.example", by_name)
        self.assertIn("empty.example", by_name)
        self.assertIn("Zed", by_name)
        title = by_name["title.example"]
        self.assertEqual((title["text"], title["date"], title["date_text"]),
                         ("A title-only reply", "2026-03-06", "March 6, 2026"))
        long_reply = by_name["Longform"]["text"]
        self.assertLessEqual(len(long_reply), m.REPLY_CHARS + 1)
        self.assertTrue(long_reply.endswith("…"))
        self.assertEqual(by_name["Mallory"]["author_url"], "https://mallory.example/")
        for r in [x for kind in p.values() for x in kind]:
            self.assertLessEqual(set(r), {"name", "url", "source", "author_url", "text", "date",
                                          "date_text"})

    def test_page_key(self):
        cases = {"https://falkensmage.com/fa/x/": "/fa/x/", "https://WWW.Falkensmage.com/fa/x": "/fa/x/",
                 "https://falkensmage.com/fa/x/?a=1#f": "/fa/x/",
                 "https://falkensmage.com/fa/x/y/": None, "https://falkensmage.com/fa/": None,
                 "https://falkensmage.com/about/": None, "https://evil.example/fa/x/": None,
                 "https://falkensmage.com.evil.example/fa/x/": None, "http://[bad": None, None: None}
        for target, want in cases.items():
            self.assertEqual(m.page_key(target), want, target)

    def test_clean_helpers(self):
        self.assertEqual(m.clean_url("https://a.example/x"), "https://a.example/x")
        for bad in ("javascript:alert(1)", "data:text/html,x", "/rel", "https://", "ftp://a.example/",
                    "https://a.example/a b", "https://a.example/\n", None, 5, "http://[bad",
                    "https://a.example/" + "x" * 2000):
            self.assertEqual(m.clean_url(bad), "", bad)
        self.assertEqual(m.clean_text("a\nb\t c\u0007d", 50), "a b cd")
        self.assertEqual(m.clean_text(None, 5), "")
        self.assertEqual(m.clean_text("one two three", 8), "one two…")
        self.assertEqual(m.clean_text("x" * 20, 8), "x" * 8 + "…")


class Blocklist(PullCase):
    def test_domain_matches_host_and_subdomains_case_insensitively(self):
        bl = m.load_blocklist(self.write_block(["Evil.Example"], []))
        pages = {ESSAY_PATH: {"likes": [
            rec("a", "https://evil.example/1"), rec("b", "https://SUB.EVIL.example/2"),
            rec("c", "https://notevil.example/3"), rec("d", "https://ok.example/4",
                                                       source="https://x.evil.example/5"),
            rec("e", "https://ok.example/6", author_url="https://evil.example/u"),
            rec("f", "https://ok.example/7")]}}
        kept, blocked = m.apply_blocklist(pages, bl)
        self.assertEqual([r["name"] for r in kept[ESSAY_PATH]["likes"]], ["c", "f"])
        self.assertEqual(blocked, 4)

    def test_author_url_matches_regardless_of_scheme_case_fragment_or_slash(self):
        bl = m.load_blocklist(self.write_block([], ["https://Author.example/u/me/"]))
        pages = {ESSAY_PATH: {"likes": [
            rec("a", author_url="http://author.example/u/me#x"),
            rec("b", author_url="https://AUTHOR.example/u/me/?a=1"),
            rec("c", author_url="https://author.example/u/other"),
            rec("d", author_url="https://author.example/u/me/more")]}}
        kept, blocked = m.apply_blocklist(pages, bl)
        self.assertEqual([r["name"] for r in kept[ESSAY_PATH]["likes"]], ["c", "d"])
        self.assertEqual(blocked, 2)

    def test_emptied_lists_and_pages_are_removed(self):
        bl = m.load_blocklist(self.write_block(["evil.example"], []))
        kept, _ = m.apply_blocklist({ESSAY_PATH: {"likes": [rec("a", "https://evil.example/1")]}}, bl)
        self.assertEqual(kept, {})

    def write_block(self, domains, authors):
        self.set_blocklist(domains, authors)
        return self.block

    def test_new_entry_removes_a_cached_mention_without_a_token(self):
        self.seed({ESSAY_PATH: {"likes": [rec("Bad", "https://bad.example/1"),
                                          rec("Good", "https://good.example/1")]}})
        self.set_blocklist(["bad.example"], [])
        with mock.patch.dict(os.environ, {"WEBMENTION_IO_TOKEN": ""}):
            rc, _ = self.run_main()
        self.assertEqual(rc, 0)
        names = [r["name"] for r in self.disk()["pages"][ESSAY_PATH]["likes"]]
        self.assertEqual(names, ["Good"])

    def test_new_entry_removes_a_cached_mention_during_an_outage(self):
        self.seed({ESSAY_PATH: {"likes": [rec("Bad", "https://bad.example/1"),
                                          rec("Good", "https://good.example/1")]}})
        self.set_blocklist(["bad.example"], [])
        self.stub.routes["/api/mentions.jf2"] = (503, [], b"down")
        rc, _ = self.run_main()
        self.assertEqual(rc, m.PULL_FAILED)
        self.assertEqual([r["name"] for r in self.disk()["pages"][ESSAY_PATH]["likes"]], ["Good"])

    def test_malformed_blocklist_fails_and_leaves_the_data_file_untouched(self):
        self.seed(LAST_GOOD)
        before = self.data.read_bytes()
        for bad in ("[]", '{"domains": "x", "authors": []}', '{"domains": [], "authors": [1]}',
                    '{"domains": []}', "not json", '{"domains": ["https://evil.example/"], "authors": []}',
                    '{"domains": [], "authors": ["not a url"]}'):
            with self.subTest(bad=bad):
                self.block.write_text(bad)
                rc, _ = self.run_main()
                self.assertEqual(rc, m.PULL_FAILED)
                self.assertEqual(self.data.read_bytes(), before)
        self.block.unlink()
        self.assertEqual(self.run_main()[0], m.PULL_FAILED)
        self.assertEqual(self.data.read_bytes(), before)
        self.assertEqual(self.api_requests(), [])

    def test_the_real_blocklist_loads_empty(self):
        self.assertEqual(m.load_blocklist(ROOT / "data" / "webmention-blocklist.json"), ([], []))


class Outage(PullCase):
    def setUp(self):
        super().setUp()
        self.seed(LAST_GOOD)

    def assert_last_good_kept(self, rc, out=""):
        self.assertEqual(rc, m.PULL_FAILED)
        self.assertEqual(self.disk(), {"generated": "2026-01-01T00:00:00Z", "pages": LAST_GOOD})
        self.assertEqual(self.leftovers(), ["blocklist.json", "webmentions.json"])
        self.assertIn("::error title=Webmentions::", out)
        self.assertIn("kept 2 last-good mentions", out)

    def test_503_three_times(self):
        self.stub.routes["/api/mentions.jf2"] = (503, [], b"down")
        rc, out = self.run_main()
        self.assert_last_good_kept(rc, out)
        self.assertEqual(len(self.api_requests()), m.TRIES)

    def test_closed_port(self):
        import socket
        s = socket.socket()
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        with mock.patch.object(m, "API", f"http://127.0.0.1:{port}/api/mentions.jf2"):
            rc, out = self.run_main()
        self.assert_last_good_kept(rc, out)

    def test_503_then_200_succeeds_in_two_requests(self):
        calls = []

        def route(method, path, headers):
            calls.append(path)
            if len(calls) == 1:
                return 503, [], b"down"
            return 200, [], json.dumps(feed([child(1, "like-of", "Fresh")])).encode()
        self.stub.routes["/api/mentions.jf2"] = route
        rc, _ = self.run_main()
        self.assertEqual(rc, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(self.disk()["pages"][ESSAY_PATH]["likes"][0]["name"], "Fresh")
        self.assertNotEqual(self.disk()["generated"], "2026-01-01T00:00:00Z")

    def test_401_makes_one_request_and_says_why(self):
        self.stub.json("/api/mentions.jf2", {"error": "forbidden",
                                             "error_description": "Access token was not valid"}, 401)
        rc, out = self.run_main()
        self.assert_last_good_kept(rc, out)
        self.assertEqual(len(self.api_requests()), 1)
        self.assertIn("Access token was not valid", out)
        self.assertNotIn(TOKEN, out)

    def test_a_redirect_is_not_followed(self):
        other = Stub()
        self.addCleanup(other.close)
        other.json("/api/mentions.jf2", feed([]))
        self.stub.routes["/api/mentions.jf2"] = (302, [("Location", other.api)], b"")
        rc, out = self.run_main()
        self.assert_last_good_kept(rc, out)
        self.assertEqual(other.log, [])
        self.assertEqual(len(self.api_requests()), 1)

    def test_bad_json_and_wrong_shape_fail(self):
        for body in (b"not json", b"[]", b'{"children": 1}', b'{"children": [], "paging": {}}'):
            with self.subTest(body=body):
                self.stub.routes["/api/mentions.jf2"] = (200, [], body)
                rc, out = self.run_main()
                self.assert_last_good_kept(rc, out)

    def test_script_crash_leaves_a_valid_file(self):
        with mock.patch.object(m, "pull_all", side_effect=RuntimeError("boom")):
            with self.assertRaises(RuntimeError), contextlib.redirect_stdout(io.StringIO()):
                m.main()
        self.assertEqual(self.disk()["pages"], LAST_GOOD)


class Token(PullCase):
    def test_header_only_never_in_path_or_output(self):
        self.stub.json("/api/mentions.jf2", feed([child(1, "like-of", "A")]))
        rc, out = self.run_main()
        self.assertEqual(rc, 0)
        for _, path, headers in self.api_requests():
            self.assertEqual(headers["authorization"], f"Bearer {TOKEN}")
            self.assertNotIn(TOKEN, path)
        self.assertNotIn(TOKEN, out)

    def test_a_token_holding_a_newline_never_leaves_the_machine(self):
        bad = "tok\nX-Evil: 1"
        with mock.patch.dict(os.environ, {"WEBMENTION_IO_TOKEN": bad}):
            rc, out = self.run_main()
        self.assertEqual(rc, m.PULL_FAILED)
        self.assertEqual(self.stub.log, [])
        self.assertNotIn("tok", out.replace("WEBMENTION_IO_TOKEN", ""))
        self.assertNotIn("X-Evil", out)


class CorruptLastGood(PullCase):
    def test_corrupt_cache_with_an_outage_is_repaired(self):
        self.stub.routes["/api/mentions.jf2"] = (503, [], b"down")
        bad_files = ['{"generated": "x", "pages": {"/fa/a/": {"lik', "[]",
                     '{"pages": {"/fa/a/": {"likes": "oops"}}}',
                     '{"pages": {"/fa/a/": {"likes": [{"name": 1, "url": "u"}]}}}',
                     '{"pages": {"/fa/a/": {"surprise": []}}}']
        for body in bad_files:
            with self.subTest(body=body):
                self.data.write_text(body)
                rc, _ = self.run_main()
                self.assertEqual(rc, m.PULL_FAILED)
                self.assertEqual(self.disk()["pages"], {})
                self.assertEqual(m.load_last_good(self.data), ({}, None))


class AbsentSecret(PullCase):
    def test_keeps_last_good_makes_no_request_and_says_so(self):
        self.seed(LAST_GOOD)
        with mock.patch.dict(os.environ, {"WEBMENTION_IO_TOKEN": "  "}):
            rc, out = self.run_main()
        self.assertEqual(rc, 0)
        self.assertEqual(self.stub.log, [])
        self.assertEqual(self.disk()["pages"], LAST_GOOD)
        self.assertIn("pull-webmentions: WEBMENTION_IO_TOKEN is not set, which is not a failure", out)
        self.assertIn("::notice title=Webmentions::", out)

    def test_writes_valid_empty_data_when_there_is_none(self):
        env = {k: v for k, v in os.environ.items() if k != "WEBMENTION_IO_TOKEN"}
        with mock.patch.dict(os.environ, env, clear=True):
            rc, _ = self.run_main()
        self.assertEqual(rc, 0)
        self.assertEqual(self.disk(), {"generated": None, "pages": {}})
        self.assertEqual(self.stub.log, [])


class Witness(PullCase):
    def setUp(self):
        super().setUp()
        self.seed(LAST_GOOD)
        self.witness = (200, [], json.dumps({"paging": {"per-page": 1, "page": 0, "total": 0,
                                                        "total-pages": 0}, "children": []}).encode())

        def route(method, path, headers):
            if "target%5B%5D" in path:
                return self.witness
            return 200, [], json.dumps(feed([])).encode()
        self.stub.routes["/api/mentions.jf2"] = route

    def witness_requests(self):
        return [r for r in self.api_requests() if "target%5B%5D" in r[1]]

    def say_total(self, n):
        self.witness = (200, [], json.dumps({"paging": {"per-page": 1, "page": 0, "total": n,
                                                        "total-pages": n}, "children": []}).encode())

    def test_public_endpoint_still_has_mentions_so_the_empty_pull_is_wrong(self):
        self.say_total(3)
        rc, out = self.run_main()
        self.assertEqual(rc, m.PULL_FAILED)
        self.assertEqual(self.disk()["pages"], LAST_GOOD)
        self.assertIn("::error title=Webmentions::", out)
        w = self.witness_requests()
        self.assertEqual(len(w), 1)
        self.assertNotIn("authorization", w[0][2])
        self.assertIn(urllib.parse.quote("https://falkensmage.com" + ESSAY_PATH, safe=""), w[0][1])

    def test_public_endpoint_agrees_they_are_gone(self):
        rc, _ = self.run_main()
        self.assertEqual(rc, 0)
        self.assertEqual(self.disk()["pages"], {})

    def test_unreachable_witness_is_a_failure(self):
        self.witness = (503, [], b"down")
        rc, _ = self.run_main()
        self.assertEqual(rc, m.PULL_FAILED)
        self.assertEqual(self.disk()["pages"], LAST_GOOD)

    def test_no_witness_when_there_is_no_last_good(self):
        self.seed({})
        rc, _ = self.run_main()
        self.assertEqual(rc, 0)
        self.assertEqual(self.witness_requests(), [])


class HostileThroughMain(PullCase):
    def test_log_carries_counts_only_and_the_file_is_clean(self):
        self.set_blocklist(["blocked.example"], [])
        self.stub.json("/api/mentions.jf2", HOSTILE)
        rc, out = self.run_main()
        self.assertEqual(rc, 0)
        for line in out.splitlines():
            self.assertTrue(line.startswith("pull-webmentions:"), line)
        for stranger in ("Mallory", "pwned", "alert", "script", "workflow", "title-only", "::error"):
            self.assertNotIn(stranger, out)
        self.assertIn("1 blocked", out)
        raw = self.data.read_text(encoding="utf-8")
        for bad in ("HTMLSENTINEL", "PHOTOSENTINEL", "PRIVATESENTINEL", "blocked.example"):
            self.assertNotIn(bad, raw)
        self.assertEqual(len(self.disk()["pages"][ESSAY_PATH]["replies"]), 6)


#@@MORE@@


if __name__ == "__main__":
    unittest.main()
