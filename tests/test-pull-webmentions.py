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


if __name__ == "__main__":
    unittest.main()
