#!/usr/bin/env python3
"""Tests for the Notes section (/notes/): the h-entry page, the index, the feed, the nav, the
syndication script (scripts/syndicate-notes.py) and the probes that guard them.

    python3 -I -S -B tests/test-notes.py

-I -S proves the tests are stdlib-only by execution. There is no outbound network, enforced
three ways so a test that forgets a stub fails closed instead of reaching a real system (D-14):

  1. A socket guard, installed for the whole module, raises OutboundBlocked on any connection
     that is not loopback (it catches every Python path to a real host, including a forgotten
     patch of MASTODON). Hugo and the version control tool run as subprocesses the guard cannot
     see: every Hugo build carries `[security.http] urls = ["^$"]`, and every call the script
     makes to the version control tool runs against a file:// origin.
  2. The base class setUp clears both secrets, so a forgotten stub cannot hold a real credential.
  3. The script's ROOT and STATE are a sentinel under /nonexistent/ until a test patches them,
     and the base setUp asserts the patched ROOT's origin is a file:// path.

`hugo` must be on PATH: its absence is a failure, never a skip, so the render checks cannot
silently vanish.

No test depends on what real notes exist or what the real data/syndication.json holds beyond
its shape. Each build mounts a temp directory of fixture notes over content/notes, and the
repo's own content/notes is excluded.
"""
import contextlib
import datetime
import hashlib
import http.server
import importlib.util
import io
import json
import os
import re
import shutil
import socket
import socketserver
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.parse
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
REAL_INDEX = ROOT / "content" / "notes" / "_index.md"
REAL_STATE = ROOT / "data" / "syndication.json"

# The script under test, loaded by path (its name has a hyphen). Its ROOT, STATE and NOTES are
# replaced at once with a sentinel, so a test that forgets to patch them has a failing call to
# the version control tool and cannot touch the real repo.
_spec = importlib.util.spec_from_file_location("syndicate_notes", ROOT / "scripts" / "syndicate-notes.py")
m = importlib.util.module_from_spec(_spec)
sys.modules["syndicate_notes"] = m
_spec.loader.exec_module(m)
SENTINEL = Path("/nonexistent/falkensmage-notes-tests-unpatched")
m.ROOT = SENTINEL
m.STATE = SENTINEL / "data" / "syndication.json"
m.NOTES = SENTINEL / "content" / "notes"


class OutboundBlocked(BaseException):
    """Raised by the guard on any non-loopback connection. A BaseException on purpose: the
    script's `except (URLError, OSError, ...)` clauses must not be able to swallow it, while
    unittest's testPartExecutor still reports it as an error."""


_LOOPBACK = {"127.0.0.1", "::1", "localhost"}
_REAL = {}


def _check_host(host):
    if isinstance(host, bytes):
        host = host.decode("ascii", "replace")
    if host not in _LOOPBACK:
        raise OutboundBlocked(f"blocked outbound connection to {host!r}")


def _guarded_connect(self, address):
    if self.family != socket.AF_UNIX:
        _check_host(address[0])
    return _REAL["connect"](self, address)


def _guarded_connect_ex(self, address):
    if self.family != socket.AF_UNIX:
        _check_host(address[0])
    return _REAL["connect_ex"](self, address)


def _guarded_getaddrinfo(host, *args, **kwargs):
    _check_host(host)
    return _REAL["getaddrinfo"](host, *args, **kwargs)


def setUpModule():
    _REAL.update(connect=socket.socket.connect, connect_ex=socket.socket.connect_ex,
                 getaddrinfo=socket.getaddrinfo)
    socket.socket.connect = _guarded_connect
    socket.socket.connect_ex = _guarded_connect_ex
    socket.getaddrinfo = _guarded_getaddrinfo


def tearDownModule():
    socket.socket.connect = _REAL["connect"]
    socket.socket.connect_ex = _REAL["connect_ex"]
    socket.getaddrinfo = _REAL["getaddrinfo"]

PAST_ONE = ("2026-01-05T09:30:00-06:00", "First note, with a 5 < 6 comparison and \"quotes\".\n\n"
            "A second paragraph links https://example.com/first for the curious.\n")
PAST_TWO = ("2026-02-10T18:45:00-06:00", "Second note, newer than the first, with [a relative link](/fa/archive/).\n")
FUTURE = ("2099-06-01T12:00:00-05:00", "A note from the far future.\n")

# Syndication fixtures, dated around a fixed instant so the script's idea of now, Hugo's --clock
# and the 7-day window all line up.
SYN_NOW = "2026-03-01T12:00:00Z"
NOW = datetime.datetime(2026, 3, 1, 12, 0, tzinfo=datetime.timezone.utc)
ALPHA = ("2026-02-27T09:00:00-06:00",
         "Alpha note with [a link](https://example.com/a), \"quotes\" and https://example.com/bare.\n\n"
         "Second paragraph.\n")
BETA = ("2026-02-28T18:00:00-06:00", "Beta note, plain.\n")
GAMMA = ("2026-03-05T12:00:00-06:00", "Gamma note, still in the future.\n")
SYN_NOTES = {"alpha": ALPHA, "beta": BETA, "gamma": GAMMA}
ALPHA_TEXT = ("Alpha note with a link (https://example.com/a), “quotes” and "
              "https://example.com/bare.\n\nSecond paragraph.")
FAKE_TOKEN = "tok-SECRET-0123456789"

# Notes straddling the instant, in several offsets, for the parity test against hugo --clock.
PARITY_NOW = "2026-03-01T12:00:00Z"
PARITY_NOTES = {
    "before": ("2026-03-01T05:59:59-06:00", "One second before.\n"),
    "equal": ("2026-03-01T06:00:00-06:00", "Exactly now, with an offset.\n"),
    "equalz": ("2026-03-01T12:00:00Z", "Exactly now, in Z.\n"),
    "after": ("2026-03-01T06:00:01-06:00", "One second after.\n"),
    "farplus": ("2026-03-01T22:00:00+14:00", "Eight o'clock UTC, written at +14.\n"),
    "farminus": ("2026-03-01T07:00:00-12:00", "Nineteen o'clock UTC, written at -12.\n"),
    "draftpast": ("2026-02-01T00:00:00Z", "A past draft.\n", "draft: true"),
}


def write_notes(dest, notes):
    """Write fixture notes (slug -> (date, body)) and the section's own _index.md into dest."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(REAL_INDEX, dest / "_index.md")
    for slug, (date, body, *extra) in notes.items():
        front = "".join(line + "\n" for line in extra)
        (dest / f"{slug}.md").write_text(f"---\ndate: {date}\n{front}---\n{body}")
    return dest


def build_site(dest, notes_dir, data_dir=None, work=None, clock=None):
    """Build the real site into dest with `hugo --minify`, offline. notes_dir is mounted over
    content/notes (the repo's own notes are always excluded); the repo's webmentions.json and
    syndication.json are always excluded from data, so a local generated file cannot leak in;
    data_dir, when given, is mounted over data/. clock pins Hugo's notion of now."""
    work = Path(work or tempfile.mkdtemp())
    mounts = ['[security.http]', 'urls = ["^$"]',
              '[[module.mounts]]', f'source = {json.dumps(str(ROOT / "content"))}',
              'target = "content"', 'files = ["! notes/**"]',
              '[[module.mounts]]', f'source = {json.dumps(str(notes_dir))}',
              'target = "content/notes"',
              '[[module.mounts]]', f'source = {json.dumps(str(ROOT / "data"))}',
              'target = "data"', 'files = ["! webmentions.json", "! syndication.json"]']
    if data_dir is not None:
        mounts += ['[[module.mounts]]', f'source = {json.dumps(str(data_dir))}', 'target = "data"']
    conf = work / "mounts.toml"
    conf.write_text("\n".join(mounts) + "\n")
    hugo = shutil.which("hugo")
    if hugo is None:
        raise AssertionError("hugo is not on PATH: the render checks must not silently vanish")
    cmd = [hugo, "--minify", "--config", f"hugo.toml,{conf}",
           "--destination", str(dest), "--cacheDir", str(work / "cache")]
    if clock:
        cmd += ["--clock", clock]
    r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"hugo failed ({r.returncode}):\n{r.stderr[-2000:]}")
    return work


def run_probe(public):
    env = dict(os.environ, VALIDATE_NOTES_PUBLIC=str(public))
    r = subprocess.run(["bash", str(ROOT / "tests" / "validate-notes.sh")], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


class Doc(HTMLParser):
    """Reads what the tests assert on: the title, meta and link tags, the h-entries and the
    h-feed, and the primary nav."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self._in_title = False
        self.meta = {}
        self.links = []          # dicts of attrs for every <link>
        self.classes = []        # (tag, class-token-set) for every element
        self.nav = []            # (href, aria-current) for every link in the primary nav
        self._nav_depth = 0
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        self.classes.append((tag, set(a.get("class", "").split())))
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = a.get("property") or a.get("name")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.links.append(a)
        if tag == "nav" and a.get("aria-label") == "Primary":
            self._nav_depth = 1
        elif self._nav_depth:
            if tag == "nav":
                self._nav_depth += 1
            if tag == "a":
                self.nav.append((a.get("href"), a.get("aria-current")))

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag == "nav" and self._nav_depth:
            self._nav_depth -= 1

    def handle_data(self, data):
        if self._in_title:
            self.title += data
        self.text.append(data)

    def count(self, cls):
        return sum(1 for _, toks in self.classes if cls in toks)


def read(path):
    d = Doc()
    d.feed(Path(path).read_text(encoding="utf-8"))
    d.close()
    return d


class Builds:
    """The builds the tests share, made once on first use and removed at exit."""

    _cache = {}
    tmp = None

    @classmethod
    def get(cls, name):
        if name not in cls._cache:
            if cls.tmp is None:
                cls.tmp = Path(tempfile.mkdtemp())
                import atexit
                atexit.register(shutil.rmtree, cls.tmp, ignore_errors=True)
            base = cls.tmp / name
            (base / "work").mkdir(parents=True, exist_ok=True)
            notes, clock = {
                "published": ({"first": PAST_ONE, "second": PAST_TWO, "later": FUTURE}, None),
                "due": ({"first": PAST_ONE, "second": PAST_TWO, "later": FUTURE},
                        "2100-01-01T00:00:00Z"),
                "empty": ({}, None),
                "future-only": ({"later": FUTURE}, None),
                "syn": (SYN_NOTES, SYN_NOW),
                "parity": (PARITY_NOTES, PARITY_NOW),
            }[name]
            notes_dir = write_notes(base / "notes", notes)
            public = base / "public"
            build_site(public, notes_dir, work=base / "work", clock=clock)
            cls._cache[name] = public
        return cls._cache[name]


class NotePage(unittest.TestCase):
    """One note file becomes a complete h-entry page and an index entry."""

    def test_a_past_note_builds_to_its_own_page_with_a_complete_h_entry(self):
        public = Builds.get("published")
        page = public / "notes" / "first" / "index.html"
        self.assertTrue(page.is_file())
        d = read(page)
        self.assertEqual(d.count("h-entry"), 1)
        for cls in ("e-content", "dt-published", "u-url", "p-author", "h-card", "u-photo"):
            self.assertGreaterEqual(d.count(cls), 1, cls)
        # the only p-name on the page is the author's, inside the h-card
        self.assertEqual(d.count("p-name"), 1)
        html = page.read_text(encoding="utf-8")
        self.assertIn("2026-01-05T09:30:00-06:00", html)
        self.assertIn("January 5, 2026, 9:30 AM", html)

    def test_the_index_lists_published_notes_newest_first_in_one_h_feed(self):
        public = Builds.get("published")
        d = read(public / "notes" / "index.html")
        self.assertEqual(d.count("h-feed"), 1)
        self.assertEqual(d.count("h-entry"), 2)
        self.assertEqual(d.count("notes-empty"), 0)
        html = (public / "notes" / "index.html").read_text(encoding="utf-8")
        self.assertLess(html.index("Second note"), html.index("First note"))

    def test_a_future_note_has_no_page_and_no_index_entry_until_due(self):
        public = Builds.get("published")
        self.assertFalse((public / "notes" / "later").exists())
        self.assertNotIn("far future", (public / "notes" / "index.html").read_text(encoding="utf-8"))
        due = Builds.get("due")
        self.assertTrue((due / "notes" / "later" / "index.html").is_file())
        self.assertEqual(read(due / "notes" / "index.html").count("h-entry"), 3)

    def test_an_empty_section_renders_the_empty_state_and_builds_cleanly(self):
        public = Builds.get("empty")
        d = read(public / "notes" / "index.html")
        self.assertEqual(d.count("notes-empty"), 1)
        self.assertEqual(d.count("h-entry"), 0)
        self.assertIn("Nothing here yet.", (public / "notes" / "index.html").read_text())
        self.assertEqual(list((public / "notes").glob("*/index.html")), [])

    def test_a_section_holding_only_a_future_note_is_empty(self):
        public = Builds.get("future-only")
        d = read(public / "notes" / "index.html")
        self.assertEqual(d.count("notes-empty"), 1)
        self.assertEqual(d.count("h-entry"), 0)

    def test_the_title_element_is_non_empty_and_escapes_a_less_than(self):
        public = Builds.get("published")
        page = public / "notes" / "first" / "index.html"
        d = read(page)
        self.assertTrue(d.title.strip())
        self.assertTrue(d.title.startswith("First note, with a 5 < 6"), d.title)
        self.assertTrue(d.title.endswith("| Falken's Mage"), d.title)
        raw = page.read_text(encoding="utf-8")
        start = raw.index("<title>") + len("<title>")
        inner = raw[start:raw.index("</title>")]
        self.assertNotIn("<", inner)
        self.assertEqual(d.meta["og:type"], "article")
        self.assertEqual(d.meta["og:title"], "A note from Falken's Mage")
        self.assertIn("5 < 6", d.meta["description"])
        self.assertIn("article:published_time", d.meta)
        self.assertEqual(d.meta["article:author"], "Matt Stine")

    def test_the_index_and_section_titles_stay_ordinary(self):
        d = read(Builds.get("published") / "notes" / "index.html")
        self.assertEqual(d.title, "Notes | Falken's Mage")


class FeedAndNav(unittest.TestCase):
    def feed_items(self, name):
        root = ET.parse(Builds.get(name) / "notes" / "index.xml").getroot()
        return root.findall("./channel/item")

    def test_the_feed_has_one_titleless_item_per_published_note(self):
        items = self.feed_items("published")
        self.assertEqual(len(items), 2)
        for item in items:
            self.assertIsNone(item.find("title"))
            for tag in ("link", "guid", "pubDate", "description"):
                self.assertTrue((item.findtext(tag) or "").strip(), tag)
        links = [i.findtext("link") for i in items]
        self.assertEqual(links, ["https://falkensmage.com/notes/second/",
                                 "https://falkensmage.com/notes/first/"])
        self.assertEqual(items[0].find("guid").get("isPermaLink"), "true")

    def test_a_relative_link_in_a_note_arrives_absolute(self):
        desc = self.feed_items("published")[0].findtext("description")
        self.assertIn('href="https://falkensmage.com/fa/archive/"', desc)
        self.assertNotIn('href="/fa/', desc)

    def test_a_future_note_has_no_feed_item_until_due(self):
        self.assertEqual(len(self.feed_items("published")), 2)
        self.assertEqual(len(self.feed_items("due")), 3)
        self.assertEqual(self.feed_items("empty"), [])
        self.assertEqual(self.feed_items("future-only"), [])

    def test_with_a_published_note_every_page_links_to_notes_and_the_head_advertises_it(self):
        public = Builds.get("published")
        for page in (public / "index.html", public / "about" / "index.html",
                     public / "notes" / "index.html", public / "notes" / "first" / "index.html"):
            d = read(page)
            self.assertIn("/notes/", [h for h, _ in d.nav], page)
            rss = [l for l in d.links if l.get("type") == "application/rss+xml"
                   and l.get("href", "").endswith("/notes/index.xml")]
            self.assertEqual(len(rss), 1, page)
            feeds = [l for l in d.links if l.get("rel") == "feed"]
            self.assertEqual([f["href"] for f in feeds], ["https://falkensmage.com/notes/"], page)
            self.assertEqual(feeds[0]["type"], "text/html")

    def test_aria_current_is_on_the_notes_link_on_the_index_and_a_note_only(self):
        public = Builds.get("published")
        current = {}
        for key, page in (("home", public / "index.html"),
                          ("index", public / "notes" / "index.html"),
                          ("note", public / "notes" / "first" / "index.html")):
            current[key] = dict(read(page).nav)["/notes/"]
        self.assertEqual(current, {"home": None, "index": "page", "note": "page"})

    def test_with_no_note_published_nothing_links_to_notes_or_advertises_its_feed(self):
        for name in ("empty", "future-only"):
            public = Builds.get(name)
            for page in (public / "index.html", public / "notes" / "index.html"):
                d = read(page)
                self.assertNotIn("/notes/", [h for h, _ in d.nav], (name, page))
                for l in d.links:
                    if l.get("rel") == "canonical":
                        continue  # the notes index's own canonical URL
                    self.assertNotIn("/notes/", l.get("href", ""), (name, page, l))
                self.assertNotIn("/notes/index.xml", page.read_text(encoding="utf-8"))


class Archetype(unittest.TestCase):
    def test_hugo_new_writes_only_a_date_with_an_explicit_offset(self):
        hugo = shutil.which("hugo")
        self.assertIsNotNone(hugo, "hugo is not on PATH")
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        r = subprocess.run([hugo, "new", "content", "notes/x.md", "--contentDir", str(tmp)],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        body = (tmp / "notes" / "x.md").read_text()
        self.assertRegex(body, r"\A---\ndate: \d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:[+-]\d\d:\d\d|Z)\n---\n*\Z")


class NotesProbe(unittest.TestCase):
    def test_the_probe_passes_on_every_build_and_prints_its_h_entry_line(self):
        for name, n in (("published", 2), ("due", 3), ("empty", 0), ("future-only", 0)):
            rc, out = run_probe(Builds.get(name))
            self.assertEqual(rc, 0, f"{name}\n{out}")
            self.assertIn(f"PASS  {n} notes carry complete h-entry markup", out)
            self.assertIn(f"PASS  the /notes/ index and feed match {n} published notes", out)
            self.assertIn("PASS  nav Notes link hidden, no note published" if n == 0
                          else f"PASS  nav Notes link shown, {n} notes published", out)


MENTIONS = {
    "generated": None,
    "pages": {"/notes/first/": {
        "likes": [{"name": "Ann", "url": "https://ann.example/l1"}],
        "reposts": [],
        "mentions": [{"name": "Bo", "url": "https://bo.example/m1"}],
        "replies": [{"name": "Di", "url": "https://di.example/r1",
                     "date": "2026-03-02T10:00:00+00:00", "date_text": "March 2, 2026",
                     "text": "hello"}],
    }},
}
FIRST = "/notes/first/"


def run_fa_probe(public, data_dir):
    env = dict(os.environ, VALIDATE_FA_PUBLIC=str(public), VALIDATE_FA_DATA=str(data_dir))
    r = subprocess.run(["bash", str(ROOT / "tests" / "validate-fa.sh")], cwd=ROOT, env=env,
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def section_span(html):
    """(start, end) of the mention band: the <section> wrapping the fa-mentions div."""
    mid = html.index("fa-prose fa-mentions")
    start = html.rindex("<section", 0, mid)
    end = html.index("</section>", mid) + len("</section>")
    return start, end


class ProbeMutations(unittest.TestCase):
    """The probes are only worth having if they can fail. Build over fixtures (two published
    notes, one future, and a received mention of the first), then break the output in each way
    a regression would, and watch the probe go red and name the page."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        cls.data = cls.tmp / "data"
        cls.data.mkdir()
        (cls.data / "webmentions.json").write_text(json.dumps(MENTIONS))
        cls.fa_data = cls.tmp / "fa-data"
        cls.fa_data.mkdir()
        (cls.fa_data / "webmentions.json").write_text(json.dumps(MENTIONS))
        shutil.copy(ROOT / "data" / "webmention-blocklist.json", cls.fa_data)
        cls.bare_data = cls.tmp / "bare-data"
        cls.bare_data.mkdir()
        shutil.copy(ROOT / "data" / "webmention-blocklist.json", cls.bare_data)
        notes = write_notes(cls.tmp / "notes", {"first": PAST_ONE, "second": PAST_TWO,
                                                "later": FUTURE})
        (cls.tmp / "work").mkdir()
        cls.public = cls.tmp / "public"
        build_site(cls.public, notes, data_dir=cls.data, work=cls.tmp / "work")
        (cls.tmp / "work-empty").mkdir()
        empty = write_notes(cls.tmp / "empty-notes", {})
        cls.empty_public = cls.tmp / "empty-public"
        build_site(cls.empty_public, empty, work=cls.tmp / "work-empty")
        cls.page = cls.public / "notes" / "first" / "index.html"
        cls.index = cls.public / "notes" / "index.html"

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def mutate(self, path, fn):
        """Rewrite a file in the temp output; the original bytes come back after the test."""
        original = Path(path).read_bytes()
        self.addCleanup(Path(path).write_bytes, original)
        new = fn(original.decode("utf-8"))
        self.assertNotEqual(new, original.decode("utf-8"), "the mutation changed nothing")
        Path(path).write_text(new, encoding="utf-8")

    def assert_notes_red(self, needle, public=None):
        rc, out = run_probe(public or self.public)
        self.assertNotEqual(rc, 0, out)
        self.assertIn(needle, out)
        return out

    def assert_fa_red(self, needle, public=None, data=None):
        rc, out = run_fa_probe(public or self.public, data or self.fa_data)
        self.assertNotEqual(rc, 0, out)
        self.assertIn(needle, out)
        return out

    # --- baselines: green first, and not vacuous

    def test_baselines_are_green(self):
        rc, out = run_probe(self.public)
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS  2 notes carry complete h-entry markup", out)
        self.assertIn("PASS  the /notes/ index and feed match 2 published notes", out)
        self.assertIn("PASS  nav Notes link shown, 2 notes published", out)
        rc, out = run_fa_probe(self.public, self.fa_data)
        self.assertEqual(rc, 0, out)
        self.assertRegex(out, r"PASS  mention sections match the pulled data on \d+ essays")
        # not vacuous: the mention is really on the note page the probe compares
        html = self.page.read_text(encoding="utf-8")
        self.assertEqual(html.count("fa-mentions__row"), 3)  # likes, mentions, replies label
        self.assertEqual(html.count("fa-mention--reply"), 1)

    def test_mentions_sit_after_the_entry_and_outside_it(self):
        html = self.page.read_text(encoding="utf-8")
        self.assertLess(html.index("</article>"), html.index("fa-mentions"))
        a, b = section_span(html)
        self.assertEqual(html[a:b].count('rel="nofollow ugc"'), 3)

    def test_with_no_notes_both_probes_pass(self):
        rc, out = run_probe(self.empty_public)
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS  0 notes carry complete h-entry markup", out)
        rc, out = run_fa_probe(self.empty_public, self.bare_data)
        self.assertEqual(rc, 0, out)

    # --- validate-notes.sh

    def test_e_content_dropped(self):
        self.mutate(self.page, lambda h: h.replace("e-content", "e-contnt", 1))
        self.assert_notes_red(f"{FIRST} missing: e-content")

    def test_dt_published_dropped(self):
        self.mutate(self.page, lambda h: h.replace("dt-published", "dt-publishd", 1))
        self.assert_notes_red(f"{FIRST} missing: dt-published")

    def test_entry_level_u_url_dropped(self):
        self.mutate(self.page, lambda h: re.sub(r"<a class=u-url", "<a class=u-urx", h, count=1))
        self.assert_notes_red(f"{FIRST} missing: u-url")

    def test_p_author_h_card_dropped(self):
        self.mutate(self.page, lambda h: h.replace("p-author", "p-authr", 1))
        self.assert_notes_red(f"{FIRST} missing: p-author+h-card")

    def test_entry_level_p_name_added(self):
        self.mutate(self.page, lambda h: h.replace(
            '<article class="h-entry note">', '<article class="h-entry note"><b class=p-name>T</b>', 1))
        self.assert_notes_red(f"{FIRST} has an entry-level p-name")

    def test_h_card_part_dropped(self):
        self.mutate(self.page, lambda h: h.replace("u-photo", "u-phot", 1))
        self.assert_notes_red(f"{FIRST} missing: h-card>u-photo")

    def test_h_entry_removed_from_the_index(self):
        self.mutate(self.index, lambda h: re.sub(
            r'<article class="h-entry note">.*?</article>', "", h, count=1, flags=re.S))
        self.assert_notes_red("/notes/ lists 1 h-entry elements, expected 2")

    def test_feed_item_dropped(self):
        self.mutate(self.public / "notes" / "index.xml",
                    lambda x: re.sub(r"<item>.*?</item>", "", x, count=1, flags=re.S))
        self.assert_notes_red("/notes/index.xml has 1 items, expected 2")

    def test_feed_item_pointing_at_an_unpublished_note(self):
        self.mutate(self.public / "notes" / "index.xml", lambda x: x.replace(
            "<link>https://falkensmage.com/notes/first/</link>",
            "<link>https://falkensmage.com/notes/later/</link>", 1))
        self.assert_notes_red("/notes/later/, which is not a published note")

    def test_empty_state_added_to_a_non_empty_index(self):
        self.mutate(self.index, lambda h: h.replace(
            "</section>", "<p class=notes-empty>Nothing here yet.</p></section>", 1))
        self.assert_notes_red("/notes/ shows the empty state although 2 notes are published")

    def test_nav_link_removed(self):
        home = self.public / "index.html"
        self.mutate(home, lambda h: re.sub(r"<a href=/notes/>Notes</a>\s*", "", h, count=1))
        self.assert_notes_red("the nav has no /notes/ link although 2 notes are published")

    def test_nav_link_added_to_an_empty_section_build(self):
        home = self.empty_public / "index.html"
        self.mutate(home, lambda h: h.replace(
            "<a href=/about/>", "<a href=/notes/>Notes</a><a href=/about/>", 1))
        self.assert_notes_red("the nav links to /notes/ although no note is published",
                              public=self.empty_public)

    def test_head_feed_link_removed(self):
        home = self.public / "index.html"
        self.mutate(home, lambda h: re.sub(r"<link rel=feed[^>]*>", "", h, count=1))
        self.assert_notes_red("the head has no rel=feed link to /notes/")

    # --- validate-fa.sh, over note pages

    def test_mentions_moved_inside_the_h_entry(self):
        def move(h):
            a, b = section_span(h)
            block, rest = h[a:b], h[:a] + h[b:]
            i = rest.index("</article>")
            return rest[:i] + block + rest[i:]
        self.mutate(self.page, move)
        self.assert_fa_red(f"{FIRST} mention section: it sits inside the h-entry")

    def test_ugc_dropped_from_a_mention_link(self):
        def drop(h):
            a, b = section_span(h)
            return h[:a] + h[a:b].replace('rel="nofollow ugc"', "rel=nofollow", 1) + h[b:]
        self.mutate(self.page, drop)
        self.assert_fa_red(f"{FIRST} mention section: a link lacks rel nofollow ugc")

    def test_webmention_link_removed_from_a_note_page(self):
        other = self.public / "notes" / "second" / "index.html"
        self.mutate(other, lambda h: h.replace(
            "<link rel=webmention href=https://webmention.io/falkensmage.com/webmention>", ""))
        self.assert_fa_red("no rel=webmention link on /notes/second/")

    def test_a_mention_count_that_disagrees_with_the_data(self):
        doc = json.loads(json.dumps(MENTIONS))
        doc["pages"][FIRST]["likes"].append({"name": "Ed", "url": "https://ed.example/l2"})
        bad = self.tmp / "bad-data"
        bad.mkdir(exist_ok=True)
        (bad / "webmentions.json").write_text(json.dumps(doc))
        shutil.copy(self.bare_data / "webmention-blocklist.json", bad)
        self.assert_fa_red(f"{FIRST} likes: data has 2, page has 1", data=bad)

    def test_a_note_that_lost_its_og_tag_is_still_checked(self):
        # data that says nothing while the page shows a section: red, even with og removed
        gone = self.tmp / "gone-data"
        gone.mkdir(exist_ok=True)
        (gone / "webmentions.json").write_text('{"generated": null, "pages": {}}')
        shutil.copy(self.bare_data / "webmention-blocklist.json", gone)
        self.mutate(self.page, lambda h: h.replace(
            '<meta property="og:type" content="article">',
            '<meta property="og:type" content="website">', 1))
        self.assert_fa_red(f"{FIRST} has 1 mention sections, expected 0", data=gone)


# =========================================================================================
# The syndication script (scripts/syndicate-notes.py): harness
# =========================================================================================

GIT_IDENT = ["-c", "user.name=Test", "-c", "user.email=test@example.invalid",
             "-c", "commit.gpgsign=false"]
EMPTY_STATE = json.dumps({"_comment": "fixture", "notes": {}}, ensure_ascii=False, indent=1,
                         sort_keys=True) + "\n"
ALPHA_PATH, BETA_PATH = "/notes/alpha/", "/notes/beta/"


def vcs(cwd, *args, check=True):
    """Run the version control tool against a temp repo. Only ever called with a cwd (or a
    file:// remote) under a temp directory."""
    r = subprocess.run(["git", *GIT_IDENT, *args], cwd=cwd, capture_output=True, text=True)
    if check and r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)} failed in {cwd}:\n{r.stdout}{r.stderr}")
    return r


def git_remote(tmp, notes, state=EMPTY_STATE):
    """A bare origin on main, seeded with the fixture notes and the state file, and a working
    clone of it made with --depth 1 over file://, which is what actions/checkout gives."""
    tmp = Path(tmp)
    origin = tmp / "origin.git"
    vcs(tmp, "init", "--bare", str(origin))
    vcs(origin, "symbolic-ref", "HEAD", "refs/heads/main")
    seed = tmp / "seed"
    vcs(tmp, "init", str(seed))
    vcs(seed, "symbolic-ref", "HEAD", "refs/heads/main")
    write_notes(seed / "content" / "notes", notes)
    if state is not None:
        (seed / "data").mkdir()
        (seed / "data" / "syndication.json").write_text(state)
    (seed / "README").write_text("seed\n")
    vcs(seed, "add", "-A")
    vcs(seed, "commit", "-m", "seed")
    vcs(seed, "push", f"file://{origin}", "main")
    clone = tmp / "clone"
    vcs(tmp, "clone", "--depth", "1", f"file://{origin}", str(clone))
    return origin, clone


def commit_to_origin(tmp, origin, files, msg="other work"):
    """Land a commit on origin from a second, full clone: another run, or a person."""
    parent = Path(tempfile.mkdtemp(dir=tmp))
    vcs(parent, "clone", f"file://{origin}", "w")
    work = parent / "w"
    for rel, text in files.items():
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        (work / rel).write_text(text)
    vcs(work, "add", "-A")
    vcs(work, "commit", "-m", msg)
    vcs(work, "push", "origin", "HEAD:main")


class _Server(http.server.ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self):
        # HTTPServer.server_bind resolves the host's name; a test server has no use for that.
        socketserver.TCPServer.server_bind(self)
        self.server_name, self.server_port = "127.0.0.1", self.server_address[1]


class Stub:
    """A loopback server standing in for the live site (it serves a built public/ directory) and
    for Mastodon (POST /api/v1/statuses, with Mastodon's Idempotency-Key behavior). Every request
    is logged. `mastodon` is a script of actions consumed one per POST, default "ok":
    "ok", "lose" (create the status, then drop the connection), ("status", code),
    ("redirect", location). `on_post` runs after a status is accepted, before it is answered."""

    def __init__(self, site=None):
        self.site = Path(site) if site else None
        self.requests = []
        self.mastodon = []
        self.statuses = []
        self.by_key = {}
        self.on_post = None
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _log(self):
                n = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(n) if n else b""
                outer.requests.append({"method": self.command, "path": self.path, "body": body,
                                       "headers": {k.lower(): v for k, v in self.headers.items()}})
                return body

            def _send(self, code, body=b"", ctype="application/json", extra=()):
                self.send_response(code)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(body)))
                for k, v in extra:
                    self.send_header(k, v)
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                self._log()
                path = urllib.parse.urlsplit(self.path).path
                target = None
                if outer.site is not None:
                    target = (outer.site / path.lstrip("/")).resolve()
                    if path.endswith("/"):
                        target = target / "index.html"
                    base = outer.site.resolve()
                    if base not in target.parents or not target.is_file():
                        target = None
                if target is None:
                    return self._send(404, b"not found", "text/plain")
                self._send(200, target.read_bytes(), "text/html; charset=utf-8")

            def do_POST(self):
                body = self._log()
                if self.path != "/api/v1/statuses":
                    return self._send(404, b"{}")
                action = outer.mastodon.pop(0) if outer.mastodon else "ok"
                if isinstance(action, tuple) and action[0] == "status":
                    return self._send(action[1], b'{"error": "stub error"}')
                if isinstance(action, tuple) and action[0] == "redirect":
                    return self._send(302, b"", extra=[("Location", action[1])])
                form = urllib.parse.parse_qs(body.decode("utf-8"))
                key = self.headers.get("Idempotency-Key")
                status = outer.by_key.get(key) if key else None
                if status is None:
                    n = len(outer.statuses) + 100
                    status = {"id": str(n), "url": f"https://mastodon.social/@falkensmage/{n}",
                              "form": form}
                    outer.statuses.append(status)
                    if key:
                        outer.by_key[key] = status
                if outer.on_post:
                    outer.on_post()
                if action == "lose":
                    self.close_connection = True
                    return
                self._send(200, json.dumps({"id": status["id"], "url": status["url"]}).encode())

        self.server = _Server(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(5)

    def posts(self):
        return [r for r in self.requests if r["method"] == "POST"]

    def gets(self, path):
        return [r for r in self.requests if r["method"] == "GET" and r["path"] == path]


class SyndicationCase(unittest.TestCase):
    """The base for every test that runs the script. In order: the environment loses both
    secrets (and the output file and DRY_RUN) and the version control tool loses the user's
    config; a bare origin and a shallow clone are made; the script's constants are pointed at
    them and at a loopback stub; then the patched ROOT's origin is asserted to be a file:// path,
    which fails the test before its body runs if anything is aimed at a real remote."""

    NOTES = {"alpha": ALPHA, "beta": BETA}
    STATE = EMPTY_STATE

    def setUp(self):
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for key in ("MASTODON_ACCESS_TOKEN", "BLUESKY_APP_PASSWORD", "GITHUB_OUTPUT", "DRY_RUN"):
            os.environ.pop(key, None)
        os.environ["GIT_CONFIG_GLOBAL"] = os.devnull
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.stub = Stub(Builds.get("syn")).start()
        self.addCleanup(self.stub.stop)
        self.origin, self.clone = git_remote(self.tmp, self.NOTES, self.STATE)
        patches = dict(ROOT=self.clone, STATE=self.clone / "data" / "syndication.json",
                       NOTES=self.clone / "content" / "notes", SITE=self.stub.base,
                       MASTODON=self.stub.base + "/api/v1/statuses", WAIT=0, LIVE_WAIT=0,
                       PUSH_WAIT=0, LIVE_TRIES=2, utcnow=lambda: NOW)
        for name, value in patches.items():
            p = mock.patch.object(m, name, value)
            p.start()
            self.addCleanup(p.stop)
        r = subprocess.run(["git", "-C", str(m.ROOT), "remote", "get-url", "origin"],
                           capture_output=True, text=True)
        self.assertTrue(r.stdout.startswith("file://"), f"origin is not a file:// path: {r.stdout!r}")

    def token(self):
        return mock.patch.dict(os.environ, {"MASTODON_ACCESS_TOKEN": FAKE_TOKEN})

    def output_file(self):
        path = self.tmp / "github-output"
        path.write_text("")
        os.environ["GITHUB_OUTPUT"] = str(path)
        return path

    def run_main(self, *argv):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(out):
            rc = m.main(list(argv))
        return rc, out.getvalue()

    def local_state(self):
        return json.loads(m.STATE.read_text(encoding="utf-8"))

    def origin_state(self):
        return json.loads(vcs(self.origin, "show", "main:data/syndication.json").stdout)

    def origin_commit_files(self):
        return vcs(self.origin, "show", "--name-only", "--format=", "main").stdout.split()

    def origin_head(self):
        return vcs(self.origin, "rev-parse", "main").stdout.strip()


class SyndicationAnchors(HTMLParser):
    """The u-syndication anchors inside the first h-entry: [(href, rel)]."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self._depth = 0

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): v or "" for k, v in attrs}
        if self._depth == 0:
            if "h-entry" in a.get("class", "").split():
                self._depth = 1
            return
        if tag == "article":
            self._depth += 1
        if tag == "a" and "u-syndication" in a.get("class", "").split():
            self.anchors.append((a.get("href"), a.get("rel")))

    def handle_endtag(self, tag):
        if self._depth and tag == "article":
            self._depth -= 1


def syndication_anchors(page):
    p = SyndicationAnchors()
    p.feed(Path(page).read_text(encoding="utf-8"))
    p.close()
    return p.anchors


# =========================================================================================
# Guards (D-14): the tests cannot reach a real host, hold a real secret or push to the real origin
# =========================================================================================

class GuardTests(unittest.TestCase):
    def test_the_guard_blocks_a_request_to_a_real_host_through_the_opener(self):
        with self.assertRaises(OutboundBlocked):
            m.OPENER.open("https://mastodon.social/", timeout=2)

    def test_the_guard_blocks_a_plain_socket_connection(self):
        with self.assertRaises(OutboundBlocked):
            socket.create_connection(("example.org", 80), timeout=2)

    def test_the_guard_is_not_an_exception_a_script_clause_can_swallow(self):
        self.assertFalse(issubclass(OutboundBlocked, Exception))

    def test_a_loopback_request_passes_the_guard_and_reaches_the_stub(self):
        stub = Stub().start()
        self.addCleanup(stub.stop)
        with self.assertRaises(urllib.error.HTTPError) as cm:
            m.OPENER.open(stub.base + "/", timeout=5)
        self.assertEqual(cm.exception.code, 404)
        cm.exception.close()
        self.assertEqual(len(stub.requests), 1)

    def test_a_test_that_never_patched_the_script_gets_a_sentinel_and_a_failing_git_call(self):
        for value in (m.ROOT, m.STATE, m.NOTES):
            self.assertTrue(str(value).startswith("/nonexistent/"), value)
        self.assertNotEqual(m.git("status").returncode, 0)


class BaseSetUp(SyndicationCase):
    def test_both_secrets_are_absent_and_the_origin_is_a_file_path(self):
        for key in ("MASTODON_ACCESS_TOKEN", "BLUESKY_APP_PASSWORD", "GITHUB_OUTPUT", "DRY_RUN"):
            self.assertNotIn(key, os.environ)
        self.assertTrue(str(m.ROOT).startswith(str(self.tmp)))
        r = subprocess.run(["git", "-C", str(m.ROOT), "remote", "get-url", "origin"],
                           capture_output=True, text=True)
        self.assertTrue(r.stdout.startswith("file://"))
        self.assertTrue((m.ROOT / ".git" / "shallow").exists(), "the clone must be shallow")

    def test_an_unstubbed_real_host_cannot_be_reached_even_with_a_secret_set(self):
        with self.token(), mock.patch.object(m, "MASTODON", "https://mastodon.social/api/v1/statuses"):
            with self.assertRaises(OutboundBlocked):
                m.post_mastodon(m.read_note(m.NOTES / "alpha.md"), "text")


# =========================================================================================
# The note format
# =========================================================================================

class NoteFormat(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def write(self, name, text):
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def refused(self, name, text, needle=None):
        path = self.write(name, text)
        with self.assertRaises(m.NoteError) as cm:
            m.read_note(path)
        self.assertIn(name, str(cm.exception))
        if needle:
            self.assertIn(needle, str(cm.exception))

    def test_a_valid_note_is_read_with_its_slug_path_and_aware_date(self):
        note = m.read_note(self.write("a-note-2.md", "---\ndate: 2026-01-05T09:30:00-06:00\n---\nHi\n"))
        self.assertEqual((note.slug, note.path, note.draft), ("a-note-2", "/notes/a-note-2/", False))
        self.assertEqual(note.date.utcoffset(), datetime.timedelta(hours=-6))
        self.assertEqual(note.date.astimezone(datetime.timezone.utc).hour, 15)

    def test_z_a_quoted_date_and_a_true_draft_are_accepted(self):
        z = m.read_note(self.write("z.md", "---\ndate: 2026-01-05T09:30:00Z\n---\nHi\n"))
        self.assertEqual(z.date.utcoffset(), datetime.timedelta(0))
        q = m.read_note(self.write("q.md", "---\ndate: \"2026-01-05T09:30:00+01:00\"\n---\nHi\n"))
        self.assertEqual(q.date.utcoffset(), datetime.timedelta(hours=1))
        d = m.read_note(self.write("d.md", "---\ndate: 2026-01-05T09:30:00Z\ndraft: true\n---\nHi\n"))
        self.assertTrue(d.draft)

    def test_every_malformed_shape_is_refused_naming_the_file(self):
        body = "---\n{}\n---\nHi\n"
        cases = {
            "nooffset.md": (body.format("date: 2026-01-05T09:30:00"), "offset"),
            "naive.md": (body.format("date: 2026-01-05 09:30:00"), "offset"),
            "bare.md": (body.format("date: 2026-01-05"), "offset"),
            "unrealdate.md": (body.format("date: 2026-13-45T09:30:00Z"), "real date"),
            "unknownkey.md": (body.format("date: 2026-01-05T09:30:00Z\ntitle: x"), "unknown front matter key"),
            "twice.md": (body.format("date: 2026-01-05T09:30:00Z\ndate: 2026-01-05T09:30:00Z"), "twice"),
            "nodate.md": (body.format("draft: false"), "date is required"),
            "baddraft.md": (body.format("date: 2026-01-05T09:30:00Z\ndraft: yes"), "draft must be"),
            "toml.md": ("+++\ndate = 2026-01-05T09:30:00Z\n+++\nHi\n", "TOML"),
            "nofront.md": ("Just text\n", "front matter"),
            "unclosed.md": ("---\ndate: 2026-01-05T09:30:00Z\nHi\n", "closing"),
            "emptybody.md": ("---\ndate: 2026-01-05T09:30:00Z\n---\n  \n", "body is empty"),
            "Upper.md": (body.format("date: 2026-01-05T09:30:00Z"), "lowercase"),
            "has_underscore.md": (body.format("date: 2026-01-05T09:30:00Z"), "lowercase"),
            "index.md": (body.format("date: 2026-01-05T09:30:00Z"), "index"),
            "-lead.md": (body.format("date: 2026-01-05T09:30:00Z"), "lowercase"),
            "notmd.txt": (body.format("date: 2026-01-05T09:30:00Z"), ".md"),
        }
        for name, (text, needle) in cases.items():
            with self.subTest(name):
                self.refused(name, text, needle)

    def test_load_notes_skips_the_section_index_and_dotfiles_oldest_first(self):
        self.write("_index.md", "---\ntitle: Notes\n---\n")
        self.write(".DS_Store", "x")
        self.write("later.md", "---\ndate: 2026-02-05T09:30:00Z\n---\nB\n")
        self.write("earlier.md", "---\ndate: 2026-01-05T09:30:00Z\n---\nA\n")
        self.assertEqual([n.slug for n in m.load_notes(self.tmp)], ["earlier", "later"])

    def test_load_notes_refuses_a_leaf_bundle_and_names_it(self):
        (self.tmp / "bundle").mkdir()
        (self.tmp / "bundle" / "index.md").write_text("---\ndate: 2026-01-05T09:30:00Z\n---\nA\n")
        with self.assertRaises(m.NoteError) as cm:
            m.load_notes(self.tmp)
        self.assertIn("bundle", str(cm.exception))

    def test_load_notes_names_the_bad_file_among_good_ones(self):
        self.write("good.md", "---\ndate: 2026-01-05T09:30:00Z\n---\nA\n")
        self.write("bad.md", "---\ndate: 2026-01-05\n---\nA\n")
        with self.assertRaises(m.NoteError) as cm:
            m.load_notes(self.tmp)
        self.assertIn("bad.md", str(cm.exception))

    def test_the_path_matches_the_one_hugo_built_for_the_same_fixture(self):
        public = Builds.get("syn")
        notes = m.load_notes(Builds.tmp / "syn" / "notes")
        self.assertEqual([n.slug for n in notes], ["alpha", "beta", "gamma"])
        built = {"/" + str(p.parent.relative_to(public)) + "/"
                 for p in (public / "notes").glob("*/index.html")}
        self.assertEqual(built, {"/notes/alpha/", "/notes/beta/"})
        for n in notes:
            self.assertEqual(n.path in built, n.date <= NOW, n.slug)

    def test_the_archetype_output_passes_read_note(self):
        hugo = shutil.which("hugo")
        self.assertIsNotNone(hugo, "hugo is not on PATH")
        r = subprocess.run([hugo, "new", "content", "notes/from-archetype.md", "--contentDir", str(self.tmp)],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        # the archetype writes front matter only; a note needs a body, so add one the way a person would
        path = self.tmp / "notes" / "from-archetype.md"
        path.write_text(path.read_text() + "A body.\n")
        note = m.read_note(path)
        self.assertEqual(note.path, "/notes/from-archetype/")
        self.assertIsNotNone(note.date.tzinfo)


class DueParity(unittest.TestCase):
    """D-02: the script's idea of due agrees with Hugo's for the same instant."""

    def test_pending_and_a_hugo_clock_build_agree_on_which_notes_are_due(self):
        public = Builds.get("parity")
        built = {p.parent.name for p in (public / "notes").glob("*/index.html")}
        notes = m.load_notes(Builds.tmp / "parity" / "notes")
        due = {n.slug for n, _ in m.pending(notes, {"notes": {}}, NOW)}
        self.assertEqual(due, built)
        # not vacuous: the fixtures straddle the instant on both sides, and drafts are out
        self.assertIn("before", built)
        self.assertNotIn("after", built)
        self.assertNotIn("farminus", built)
        self.assertNotIn("draftpast", built)
        self.assertEqual(len(notes), 7)

    def test_a_recorded_note_a_draft_and_a_future_note_are_not_pending(self):
        Builds.get("parity")
        notes = m.load_notes(Builds.tmp / "parity" / "notes")
        state = {"notes": {"/notes/before/": {"mastodon": {"url": "https://mastodon.social/@falkensmage/1"}}}}
        got = {n.slug: p for n, p in m.pending(notes, state, NOW)}
        self.assertNotIn("before", got)
        self.assertNotIn("draftpast", got)
        self.assertNotIn("after", got)
        self.assertEqual(got["equal"], ["mastodon"])

    def test_pending_is_oldest_first(self):
        Builds.get("syn")
        notes = m.load_notes(Builds.tmp / "syn" / "notes")
        self.assertEqual([n.slug for n, _ in m.pending(notes, {"notes": {}}, NOW)], ["alpha", "beta"])


class StateFile(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_a_valid_document_loads_and_the_real_file_has_the_right_shape(self):
        path = self.tmp / "s.json"
        path.write_text(json.dumps({"notes": {"/notes/a/": {"mastodon": {"url": "https://mastodon.social/@falkensmage/1"}}}}))
        self.assertIn("/notes/a/", m.load_state(path)["notes"])
        self.assertIsInstance(m.load_state(REAL_STATE)["notes"], dict)  # shape only (D-12)

    def test_a_missing_file_raises_and_never_returns_empty_state(self):
        with self.assertRaises(m.StateError):
            m.load_state(self.tmp / "absent.json")

    def test_every_malformed_shape_raises(self):
        good = {"url": "https://mastodon.social/@falkensmage/1"}
        shapes = {
            "not json": "{nope",
            "a list": "[]",
            "no notes": "{}",
            "notes a list": '{"notes": []}',
            "bad key": json.dumps({"notes": {"bad": {}}}),
            "key without slash": json.dumps({"notes": {"/notes/a": {}}}),
            "note a list": json.dumps({"notes": {"/notes/a/": []}}),
            "unknown platform": json.dumps({"notes": {"/notes/a/": {"twitter": good}}}),
            "record empty": json.dumps({"notes": {"/notes/a/": {"mastodon": {}}}}),
            "url not a string": json.dumps({"notes": {"/notes/a/": {"mastodon": {"url": 3}}}}),
            "url empty": json.dumps({"notes": {"/notes/a/": {"mastodon": {"url": ""}}}}),
            "record a string": json.dumps({"notes": {"/notes/a/": {"mastodon": "x"}}}),
        }
        for label, text in shapes.items():
            with self.subTest(label):
                path = self.tmp / "s.json"
                path.write_text(text)
                with self.assertRaises(m.StateError):
                    m.load_state(path)


class PageText(unittest.TestCase):
    def text(self, body, base="https://falkensmage.com/notes/x/"):
        return m.page_text(f'<html><body><article class="h-entry note"><div class="a e-content">'
                           f"{body}</div><p class=note__meta>meta</p></article></body></html>", base)

    def test_hugos_real_output_gives_curly_quotes_a_label_url_pair_and_a_blank_line(self):
        page = Builds.get("syn") / "notes" / "alpha" / "index.html"
        text = m.page_text(page.read_text(encoding="utf-8"), "https://falkensmage.com/notes/alpha/")
        self.assertEqual(text, ALPHA_TEXT)
        self.assertIn("“quotes”", text)
        self.assertIn("a link (https://example.com/a)", text)
        self.assertEqual(text.count("https://example.com/bare"), 1)
        self.assertIn(".\n\nSecond paragraph.", text)

    def test_the_meta_line_outside_e_content_is_not_part_of_the_text(self):
        self.assertEqual(self.text("<p>Body</p>"), "Body")

    def test_a_missing_h_entry_or_e_content_or_empty_text_is_none(self):
        self.assertIsNone(m.page_text("<html><body><p>x</p></body></html>", "https://x/"))
        self.assertIsNone(m.page_text('<article class="h-entry"><p>x</p></article>', "https://x/"))
        self.assertIsNone(self.text("  <p> </p> "))
        self.assertIsNone(self.text('<img src="a.png" alt="alt text">'))

    def test_the_minifiers_omitted_end_tags_still_split_paragraphs_and_list_items(self):
        self.assertEqual(self.text("<p>One<p>Two<ul><li>a<li>b</ul><p>Three<br>four"),
                         "One\n\nTwo\n\n- a\n- b\n\nThree\nfour")

    def test_entities_and_whitespace_collapse(self):
        self.assertEqual(self.text("<p>5 &lt; 6 &amp;   7 &mldr;\n\n  end</p>"), "5 < 6 & 7 … end")

    def test_anchors(self):
        cases = {
            '<a href="https://e.com/p">label</a>': "label (https://e.com/p)",
            '<a href="https://e.com/p">https://e.com/p</a>': "https://e.com/p",
            '<a href="https://e.com/p/">e.com/p</a>': "https://e.com/p/",
            '<a href="http://www.e.com">www.e.com</a>': "http://www.e.com",
            '<a href="/fa/x/">relative</a>': "relative (https://falkensmage.com/fa/x/)",
            '<a href="mailto:a@b.c">mail me</a>': "mail me",
            '<a href="#top">up</a>': "up (https://falkensmage.com/notes/x/#top)",
            '<a name="x">no href</a>': "no href",
        }
        for body, want in cases.items():
            with self.subTest(body):
                self.assertEqual(self.text(f"<p>{body}</p>"), want)

    def test_only_the_first_h_entry_is_read(self):
        html = ('<article class="h-entry"><div class="e-content"><p>First</p></div></article>'
                '<article class="h-entry"><div class="e-content"><p>Second</p></div></article>')
        self.assertEqual(m.page_text(html, "https://x/"), "First")


class Tracer(SyndicationCase):
    """One note travels from its live page, through a stub Mastodon, to a pushed record and a
    u-syndication link on the rebuilt page."""

    NOTES = {"alpha": ALPHA}

    def test_a_due_note_reaches_the_stub_is_recorded_and_pushed_then_shows_as_u_syndication(self):
        output = self.output_file()
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 0, out)
        # one POST, holding the page's text, explicit visibility, the bearer header and a key
        posts = self.stub.posts()
        self.assertEqual(len(posts), 1)
        form = urllib.parse.parse_qs(posts[0]["body"].decode("utf-8"))
        self.assertEqual(form, {"status": [ALPHA_TEXT], "visibility": ["public"], "language": ["en"]})
        self.assertEqual(posts[0]["headers"]["authorization"], f"Bearer {FAKE_TOKEN}")
        self.assertEqual(posts[0]["headers"]["idempotency-key"],
                         hashlib.sha256(b"falkensmage.com:mastodon:/notes/alpha/").hexdigest())
        # the record is in the checkout and on origin, in a commit that touches only that file
        status = self.stub.statuses[0]
        rec = self.local_state()["notes"][ALPHA_PATH]["mastodon"]
        self.assertEqual(rec, {"url": status["url"], "id": status["id"], "posted": "2026-03-01T12:00:00Z"})
        self.assertEqual(self.origin_state()["notes"][ALPHA_PATH]["mastodon"], rec)
        self.assertEqual(self.origin_commit_files(), ["data/syndication.json"])
        self.assertEqual(self.origin_head(), vcs(m.ROOT, "rev-parse", "HEAD").stdout.strip())
        self.assertIn("recorded=true", output.read_text())
        self.assertNotIn(FAKE_TOKEN, out)
        # a rebuild with the record shows the link, inside the h-entry, with the exact URL
        data = self.tmp / "data"
        data.mkdir()
        shutil.copy(m.STATE, data / "syndication.json")
        work = self.tmp / "work"
        work.mkdir()
        public = self.tmp / "public"
        build_site(public, m.NOTES, data_dir=data, work=work, clock=SYN_NOW)
        self.assertEqual(syndication_anchors(public / "notes" / "alpha" / "index.html"),
                         [(status["url"], "syndication")])
        self.assertEqual(syndication_anchors(public / "notes" / "index.html"),
                         [(status["url"], "syndication")])
        # and a second run sends nothing
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(self.stub.posts()), 1)

    def test_a_page_without_a_record_has_no_u_syndication_link(self):
        self.assertEqual(syndication_anchors(Builds.get("syn") / "notes" / "alpha" / "index.html"), [])


class Check(SyndicationCase):
    NOTES = {"gamma": GAMMA}

    def test_check_with_nothing_due_makes_no_request_and_writes_false_false(self):
        output = self.output_file()
        rc, out = self.run_main("check")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.stub.requests, [])
        self.assertEqual(output.read_text().split(), ["pending=false", "deploy=false"])


if __name__ == "__main__":
    unittest.main()
