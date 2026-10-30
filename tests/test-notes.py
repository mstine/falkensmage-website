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
FAKE_PASSWORD = "pw-SECRET-abcd-efgh-ijkl"
FAKE_JWT = "jwt-SECRET-session-token-0123456789"
TID_RE = re.compile(r"[234567abcdefghij][234567abcdefghijklmnopqrstuvwxyz]{12}")

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


def run_probe(public, content=None, data=None, now=None):
    """Run validate-notes.sh over a build. content defaults to the notes directory the build was
    made from (Builds and ProbeMutations keep it next to public/), data to the repo's data/ (an
    empty record), now to the wall clock."""
    public = Path(public)
    env = dict(os.environ, VALIDATE_NOTES_PUBLIC=str(public),
               VALIDATE_NOTES_CONTENT=str(content if content is not None else public.parent / "notes"))
    if data is not None:
        env["VALIDATE_NOTES_DATA"] = str(data)
    if now is not None:
        env["VALIDATE_NOTES_NOW"] = now
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


class Card(HTMLParser):
    """Every element inside the page's first h-entry, with its attributes, its ancestors
    (inside the entry) and the text it holds. Only the tags that wrap content are tracked as
    open elements; img, data and the svg parts never get an end tag to wait for."""

    TRACK = {"article", "header", "footer", "div", "a", "span", "ul", "li", "time", "svg", "p"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.els = []             # every element seen inside the first h-entry
        self._entry = None        # depth marker: the first h-entry element
        self._done = False

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        toks = set(a.get("class", "").split())
        if self._entry is None:
            if "h-entry" in toks and not self._done:
                self._entry = True
                el = dict(tag=tag, a=a, cls=toks, anc=[], text="")
                self.els.append(el)
                self.stack.append(el)
            return
        el = dict(tag=tag, a=a, cls=toks, anc=list(self.stack), text="")
        self.els.append(el)
        if tag in self.TRACK:
            self.stack.append(el)

    def handle_endtag(self, tag):
        if self._entry is None or not self.stack:
            return
        if tag == self.stack[-1]["tag"]:
            self.stack.pop()
            if not self.stack:
                self._entry = None
                self._done = True

    def handle_data(self, data):
        for el in self.stack:
            el["text"] += data

    def find(self, cls=None, tag=None, inside=None, outside=None):
        out = []
        for el in self.els:
            if cls is not None and cls not in el["cls"]:
                continue
            if tag is not None and el["tag"] != tag:
                continue
            anc = [c for e in el["anc"] for c in e["cls"]]
            if inside is not None and inside not in anc:
                continue
            if outside is not None and outside in anc:
                continue
            out.append(el)
        return out


def card(path):
    c = Card()
    c.feed(Path(path).read_text(encoding="utf-8"))
    c.close()
    return c


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

    def test_the_card_header_has_a_first_party_avatar_name_and_handle(self):
        page = Builds.get("published") / "notes" / "first" / "index.html"
        c = card(page)
        imgs = c.find(tag="img", inside="h-card")
        self.assertEqual(len(imgs), 1)
        img = imgs[0]
        self.assertIn("u-photo", img["cls"])
        self.assertTrue(img["a"].get("alt", "").strip(), "the avatar needs alt text")
        src = img["a"].get("src", "")
        self.assertTrue(src.startswith("/") and not src.startswith("//"), src)  # first-party, site-relative
        self.assertTrue(img["a"].get("width") and img["a"].get("height"))
        names = c.find("p-name", inside="h-card")
        self.assertEqual([n["text"].strip() for n in names], ["Falken's Mage"])
        nicks = c.find("p-nickname", inside="h-card")
        self.assertEqual([n["text"].strip() for n in nicks], ["@falkensmage.com"])
        self.assertTrue(c.find("u-url", tag="data", inside="h-card"))
        # nothing in the card is an entry-level property
        self.assertEqual(c.find("p-name", outside="h-card"), [])
        self.assertEqual(c.find("p-nickname", outside="h-card"), [])
        self.assertEqual(c.find("u-photo", outside="h-card"), [])
        raw = page.read_text(encoding="utf-8")
        self.assertNotIn("<script", raw[raw.index("<article"):raw.index("</article>")])

    def test_the_timestamp_is_an_entry_level_link_to_the_permalink(self):
        c = card(Builds.get("published") / "notes" / "first" / "index.html")
        links = [e for e in c.find(tag="a", outside="h-card") if "u-url" in e["cls"]]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0]["a"]["href"], "https://falkensmage.com/notes/first/")
        inner = [e for e in c.find("dt-published", tag="time") if any(x is links[0] for x in e["anc"])]
        self.assertEqual(len(inner), 1)

    def test_the_body_is_the_e_content_at_entry_level_and_the_index_uses_the_same_card(self):
        public = Builds.get("published")
        for page in (public / "notes" / "first" / "index.html", public / "notes" / "index.html"):
            c = card(page)
            body = c.find("e-content")
            self.assertGreaterEqual(len(body), 1, page)
            self.assertIn("note__body", body[0]["cls"])
            self.assertEqual(len(c.find("note__actions", tag="footer")), 1, page)
            self.assertGreaterEqual(len(c.find("u-photo", tag="img")), 1, page)

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


class FeedCss(unittest.TestCase):
    """The Notes block of main.css, read as text: a one-column feed, secondary text that stays
    readable, and no violet used as a text colour."""

    @classmethod
    def setUpClass(cls):
        css = (ROOT / "themes" / "arcaeon" / "assets" / "css" / "main.css").read_text(encoding="utf-8")
        cls.block = css[css.index("/* Notes ("):css.index("/* Responses under an essay")]

    def test_the_column_is_about_600px(self):
        self.assertIn("37.5rem", self.block)

    def test_secondary_text_keeps_opacity_at_or_above_point_six(self):
        values = [float(v) for v in re.findall(r"opacity:\s*([\d.]+)", self.block)]
        self.assertTrue(values)
        self.assertGreaterEqual(min(values), 0.6)

    def test_electric_violet_is_never_a_text_colour(self):
        for decl in re.findall(r"(?<![-\w])color:\s*([^;]+);", self.block):
            self.assertNotRegex(decl, r"--color-accent\)|electric-violet", decl)

    def test_no_script_and_no_remote_url_in_the_block_or_the_card(self):
        self.assertNotIn("url(http", self.block)
        entry = (ROOT / "themes" / "arcaeon" / "layouts" / "partials" / "notes" / "entry.html").read_text()
        self.assertNotIn("<script", entry)
        self.assertNotIn("http://", entry.replace("http://www.w3.org", ""))


class NotesProbe(unittest.TestCase):
    def test_the_probe_passes_on_every_build_and_prints_its_h_entry_line(self):
        # the "due" build was made at a pinned clock, so the probe is told the same instant
        for name, n, files, now in (("published", 2, 3, None), ("due", 3, 3, "2100-01-01T00:00:00Z"),
                                    ("empty", 0, 0, None), ("future-only", 0, 1, None)):
            rc, out = run_probe(Builds.get(name), now=now)
            self.assertEqual(rc, 0, f"{name}\n{out}")
            self.assertIn(f"PASS  {files} note files follow the format", out)
            self.assertIn("PASS  every due note has a page and no scheduled note does", out)
            self.assertIn("PASS  every syndicated note shows its u-syndication links", out)
            self.assertIn(f"PASS  {n} notes carry complete h-entry markup", out)
            self.assertIn(f"PASS  the /notes/ index and feed match {n} published notes", out)
            self.assertIn("PASS  nav Notes link hidden, no note published" if n == 0
                          else f"PASS  nav Notes link shown, {n} notes published", out)


SYN_RECORDS = {
    "/notes/first/": {
        "mastodon": {"id": "101", "posted": "2026-01-05T16:00:00Z",
                     "url": "https://mastodon.social/@falkensmage/101"},
        "bluesky": {"id": "at://did:plc:x/app.bsky.feed.post/3abc", "posted": "2026-01-05T16:00:05Z",
                    "url": "https://bsky.app/profile/falkensmage.bsky.social/post/3abc"}},
    "/notes/second/": {
        "mastodon": {"id": "102", "posted": "2026-02-11T00:45:00Z",
                     "url": "https://mastodon.social/@falkensmage/102"}},
}


def syn_doc(notes=None):
    return json.dumps({"_comment": "fixture", "notes": SYN_RECORDS if notes is None else notes},
                      ensure_ascii=False, indent=1, sort_keys=True) + "\n"


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
        (cls.data / "syndication.json").write_text(syn_doc())
        cls.empty_data = cls.tmp / "empty-data"
        cls.empty_data.mkdir()
        (cls.empty_data / "syndication.json").write_text(syn_doc({}))
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
        cls.second = cls.public / "notes" / "second" / "index.html"
        cls.index = cls.public / "notes" / "index.html"
        cls.content = cls.tmp / "notes"
        cls.empty_content = cls.tmp / "empty-notes"

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

    def probe(self, public=None, content=None, data=None, now=None):
        """The notes probe over the fixture build (or, given `public`, the empty-section build)."""
        if public is None:
            return run_probe(self.public, content or self.content, data or self.data, now)
        return run_probe(public, content or self.empty_content, data or self.empty_data, now)

    def temp_dir(self, name):
        path = self.tmp / name
        shutil.rmtree(path, ignore_errors=True)
        path.mkdir()
        return path

    def data_with(self, text):
        path = self.temp_dir("data-" + str(abs(hash(text))))
        (path / "syndication.json").write_text(text)
        return path

    def content_with(self, **files):
        """A copy of the fixture notes directory plus the given files (name -> text)."""
        path = self.tmp / ("content-" + str(abs(hash(tuple(sorted(files.items()))))))
        shutil.rmtree(path, ignore_errors=True)
        shutil.copytree(self.content, path)
        for name, text in files.items():
            (path / name).write_text(text)
        return path

    def assert_notes_red(self, needle, public=None, **kw):
        rc, out = self.probe(public, **kw)
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
        rc, out = self.probe()
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS  3 note files follow the format", out)
        self.assertIn("PASS  every due note has a page and no scheduled note does", out)
        self.assertIn("PASS  every syndicated note shows its u-syndication links", out)
        # not vacuous: the pages really carry the links the probe compares
        self.assertEqual(len(syndication_anchors(self.page)), 2)
        self.assertEqual(len(syndication_anchors(self.second)), 1)
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
        rc, out = self.probe(self.empty_public)
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS  0 notes carry complete h-entry markup", out)
        self.assertIn("PASS  0 note files follow the format", out)
        rc, out = run_fa_probe(self.empty_public, self.bare_data)
        self.assertEqual(rc, 0, out)

    # --- the card's footer: counts from the pulled data, copies from the record

    def counts(self, page):
        c = card(page)
        out = {}
        for kind in ("replies", "likes", "reposts"):
            els = c.find(f"note__count--{kind}")
            self.assertEqual(len(els), 1, kind)
            self.assertEqual(len(c.find("visually-hidden", inside=f"note__count--{kind}")), 1, kind)
            icons = c.find(tag="svg", inside=f"note__count--{kind}")
            self.assertEqual(len(icons), 1, kind)
            self.assertEqual(icons[0]["a"].get("aria-hidden"), "true", kind)
            n = c.find("note__n", inside=f"note__count--{kind}")
            self.assertEqual(len(n), 1, kind)
            out[kind] = n[0]["text"].strip()
            self.assertTrue(out[kind].isdigit(), out[kind])  # an integer from len, never stranger text
        return out

    def test_counts_come_from_the_pulled_data_and_show_zeros(self):
        self.assertEqual(self.counts(self.page), {"replies": "1", "likes": "1", "reposts": "0"})
        self.assertEqual(self.counts(self.second), {"replies": "0", "likes": "0", "reposts": "0"})

    def test_the_footer_holds_exactly_the_recorded_copies_with_icons(self):
        c = card(self.page)
        links = c.find("u-syndication", tag="a", inside="note__actions")
        self.assertEqual(sorted(l["a"]["href"] for l in links),
                         sorted(r["url"] for r in SYN_RECORDS[FIRST].values()))
        for l in links:
            self.assertIn("syndication", l["a"].get("rel", "").split())
            self.assertTrue(l["text"].strip())  # a visible label
            self.assertEqual(len([e for e in c.find(tag="svg") if any(x is l for x in e["anc"])]), 1)
        self.assertEqual(c.find("u-syndication", outside="note__actions"), [])
        c = card(self.second)
        links = c.find("u-syndication", tag="a", inside="note__actions")
        self.assertEqual([l["a"]["href"] for l in links], ["https://mastodon.social/@falkensmage/102"])

    def test_the_entry_has_no_footer_copy_links_when_nothing_is_recorded(self):
        public = Builds.get("published")
        c = card(public / "notes" / "first" / "index.html")
        self.assertEqual(c.find("u-syndication"), [])
        self.assertEqual(len(c.find("note__actions", tag="footer")), 1)

    # --- validate-notes.sh

    def test_e_content_dropped(self):
        self.mutate(self.page, lambda h: h.replace("e-content", "e-contnt", 1))
        self.assert_notes_red(f"{FIRST} missing: e-content")

    def test_dt_published_dropped(self):
        self.mutate(self.page, lambda h: h.replace("dt-published", "dt-publishd", 1))
        self.assert_notes_red(f"{FIRST} missing: dt-published")

    def test_entry_level_u_url_dropped(self):
        self.mutate(self.page, lambda h: re.sub(r'<a class="u-url note__time"', '<a class="u-urx note__time"', h, count=1))
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

    def with_text(self, text):
        """Put `text` into the first note's e-content, as plain text after 'A second paragraph'."""
        # the head repeats the text (description meta), so edit inside the article, not the first hit
        def edit(h):
            i = h.index("A second paragraph", h.index('<article class="h-entry note">'))
            return h[:i] + "A second paragraph " + text + h[i + len("A second paragraph"):]
        self.mutate(self.page, edit)

    def test_bare_domain_with_a_path(self):
        self.with_text("example.com/path")
        out = self.assert_notes_red(f'bare domain: {FIRST} has "example.com/path" outside a link')
        self.assertIn("https://", out)

    def test_bare_domain_host_only(self):
        self.with_text("falkensmage.com")
        self.assert_notes_red(f'bare domain: {FIRST} has "falkensmage.com" outside a link')

    def test_bare_domain_inside_an_anchor_is_fine(self):
        self.with_text("<a href=https://example.com/path>example.com/path</a>")
        rc, out = self.probe()
        self.assertEqual(rc, 0, out)
        self.assertIn("PASS  no note has a bare domain outside a link", out)

    def test_bare_domain_with_a_scheme_is_fine(self):
        self.with_text("https://example.com/path and http://falkensmage.com")
        rc, out = self.probe()
        self.assertEqual(rc, 0, out)

    def test_bare_domain_check_ignores_handles_and_file_names(self):
        self.with_text("@falkensmage.com, file.txt, Node.js, e.g. this, v1.5/2 and a.b")
        rc, out = self.probe()
        self.assertEqual(rc, 0, out)

    def test_bare_domain_in_the_card_header_is_not_read(self):
        # the handle sits in the header, outside e-content; a bare host there is not the body's
        self.mutate(self.page, lambda h: h.replace(
            '<article class="h-entry note">',
            '<article class="h-entry note"><span>falkensmage.com/x</span>', 1))
        rc, out = self.probe()
        self.assertEqual(rc, 0, out)

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

    # --- validate-notes.sh, the record held to the pages

    def test_a_u_syndication_anchor_removed(self):
        self.mutate(self.page, lambda h: re.sub(r"<a [^>]*u-syndication[^>]*bsky\.app[^>]*>.*?</a>", "", h, count=1, flags=re.S))
        self.assert_notes_red("syndication: /notes/first/ shows 1 u-syndication links")

    def test_a_u_syndication_href_changed(self):
        self.mutate(self.page, lambda h: h.replace("/@falkensmage/101", "/@falkensmage/999", 1))
        self.assert_notes_red("syndication: /notes/first/ shows 2 u-syndication links")

    def test_a_u_syndication_anchor_with_no_record(self):
        self.mutate(self.second, lambda h: h.replace(
            "</article>", "<a class=u-syndication rel=syndication href=https://bsky.app/profile/x/post/1>Bluesky</a></article>", 1))
        self.assert_notes_red("syndication: /notes/second/ shows 2 u-syndication links")

    def test_rel_syndication_removed(self):
        self.mutate(self.page, lambda h: re.sub(r" ?rel=syndication", "", h, count=1))
        out = self.assert_notes_red("syndication: /notes/first/ u-syndication link to")
        self.assertIn("lacks rel=syndication", out)

    def test_a_due_notes_page_deleted(self):
        original = self.second.read_bytes()
        self.addCleanup(self.second.write_bytes, original)
        self.second.unlink()
        self.assert_notes_red("due: /notes/second/ came due more than 10 minutes ago but has no page")

    def test_a_page_added_for_a_future_note(self):
        later = self.public / "notes" / "later"
        later.mkdir()
        self.addCleanup(shutil.rmtree, later, ignore_errors=True)
        (later / "index.html").write_bytes(self.page.read_bytes())
        self.assert_notes_red("due: /notes/later/ is a draft or dated in the future but has a page")

    def test_a_page_for_a_draft(self):
        drafted = self.content_with(**{"first.md": f"---\ndate: {PAST_ONE[0]}\ndraft: true\n---\n{PAST_ONE[1]}"})
        self.assert_notes_red("due: /notes/first/ is a draft or dated in the future but has a page",
                              content=drafted)

    def test_a_corrupt_state_file(self):
        self.assert_notes_red("state: syndication.json: is not valid JSON", data=self.data_with("{nope"))

    def test_a_record_with_a_host_outside_the_two_allowed(self):
        records = json.loads(json.dumps(SYN_RECORDS))
        records["/notes/first/"]["mastodon"]["url"] = "https://evil.example/@falkensmage/101"
        self.assert_notes_red("syndication: /notes/first/ mastodon url is not https on mastodon.social",
                              data=self.data_with(syn_doc(records)))

    def test_a_record_on_the_wrong_scheme_or_a_lookalike_host(self):
        for url in ("http://mastodon.social/@falkensmage/101",
                    "https://mastodon.social.evil.example/@falkensmage/101",
                    "https://evil.example@mastodon.social/@falkensmage/101"):
            with self.subTest(url):
                records = json.loads(json.dumps(SYN_RECORDS))
                records["/notes/first/"]["mastodon"]["url"] = url
                self.assert_notes_red("/notes/first/ mastodon url is not https on mastodon.social",
                                      data=self.data_with(syn_doc(records)))

    def test_a_note_file_with_an_empty_body(self):
        content = self.content_with(**{"empty.md": "---\ndate: 2026-02-01T00:00:00Z\n---\n"})
        self.assert_notes_red("format: empty.md: the body is empty", content=content)

    def test_a_note_file_with_a_bad_name_or_date_is_named(self):
        content = self.content_with(**{"Bad_Name.md": "---\ndate: 2026-02-01T00:00:00Z\n---\nHi\n"})
        self.assert_notes_red("format: Bad_Name.md", content=content)

    def test_a_due_note_seconds_old_with_no_page_is_a_race_not_a_bug(self):
        now = "2026-06-01T12:00:00Z"
        fresh = self.content_with(**{"fresh.md": "---\ndate: 2026-06-01T11:59:30Z\n---\nJust now.\n"})
        rc, out = self.probe(content=fresh, now=now)
        self.assertEqual(rc, 0, out)
        stale = self.content_with(**{"stale.md": "---\ndate: 2026-06-01T11:49:00Z\n---\nEleven minutes ago.\n"})
        self.assert_notes_red("due: /notes/stale/ came due more than 10 minutes ago", content=stale, now=now)

    def test_a_record_whose_content_file_is_gone_is_counted_and_skipped(self):
        records = json.loads(json.dumps(SYN_RECORDS))
        records["/notes/gone/"] = {"mastodon": {"id": "7", "posted": "2026-01-01T00:00:00Z",
                                                "url": "https://mastodon.social/@falkensmage/7"}}
        rc, out = self.probe(data=self.data_with(syn_doc(records)))
        self.assertEqual(rc, 0, out)
        self.assertIn("1 recorded notes have no content file and were skipped as retired", out)

    def test_a_recorded_note_with_no_page_is_red(self):
        records = json.loads(json.dumps(SYN_RECORDS))
        records["/notes/later/"] = {"mastodon": {"id": "8", "posted": "2026-01-01T00:00:00Z",
                                                 "url": "https://mastodon.social/@falkensmage/8"}}
        self.assert_notes_red("syndication: /notes/later/ is recorded as syndicated but has no page",
                              data=self.data_with(syn_doc(records)))

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
    """A loopback server standing in for the live site (it serves a built public/ directory), for
    Mastodon (POST /api/v1/statuses, with Mastodon's Idempotency-Key behavior) and for Bluesky's
    PDS (createSession, getRecord, createRecord, with records held by key and a repeat
    createRecord refused, as the PDS does). Every request is logged. `mastodon` is a script of
    actions consumed one per POST, default "ok": "ok", "lose" (create the status, then drop the
    connection), ("status", code), ("redirect", location). `on_post` runs after a status is
    accepted, before it is answered. `bsky_session`, `bsky_get` and `bsky_create` are the same
    kind of script for the three Bluesky calls: "ok", ("status", code), ("status", code, error),
    and for createSession ("did", other), for createRecord "lose" (create the record, then drop
    the connection). `on_create` runs after a record is stored."""

    def __init__(self, site=None):
        self.site = Path(site) if site else None
        self.requests = []
        self.mastodon = []
        self.statuses = []
        self.by_key = {}
        self.on_post = None
        self.bsky_session = []
        self.bsky_get = []
        self.bsky_create = []
        self.records = {}
        self.on_create = None
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

            def _authorized(self):
                if self.headers.get("Authorization") == f"Bearer {FAKE_JWT}":
                    return True
                self._send(401, b'{"error": "AuthenticationRequired"}')
                return False

            def _bsky_get(self):
                query = urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)
                action = outer.bsky_get.pop(0) if outer.bsky_get else "ok"
                if isinstance(action, tuple) and action[0] == "status":
                    err = action[2] if len(action) > 2 else "StubError"
                    return self._send(action[1], json.dumps({"error": err}).encode())
                if not self._authorized():
                    return
                rkey = (query.get("rkey") or [""])[0]
                if rkey in outer.records:
                    return self._send(200, json.dumps({
                        "uri": outer.records[rkey]["uri"], "cid": "bafystub",
                        "value": outer.records[rkey]["record"]}).encode())
                self._send(400, b'{"error": "RecordNotFound", "message": "Could not locate record"}')

            def do_GET(self):
                self._log()
                path = urllib.parse.urlsplit(self.path).path
                if path == "/xrpc/com.atproto.repo.getRecord":
                    return self._bsky_get()
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

            def _bsky_session(self, body):
                action = outer.bsky_session.pop(0) if outer.bsky_session else "ok"
                if isinstance(action, tuple) and action[0] == "status":
                    err = action[2] if len(action) > 2 else "StubError"
                    return self._send(action[1], json.dumps({"error": err}).encode())
                did = action[1] if isinstance(action, tuple) and action[0] == "did" else m.BLUESKY_DID
                self._send(200, json.dumps({"accessJwt": FAKE_JWT, "refreshJwt": "refresh-stub",
                                            "did": did, "handle": "falkensmage.com"}).encode())

            def _bsky_create(self, body):
                action = outer.bsky_create.pop(0) if outer.bsky_create else "ok"
                if isinstance(action, tuple) and action[0] == "status":
                    err = action[2] if len(action) > 2 else "StubError"
                    return self._send(action[1], json.dumps({"error": err}).encode())
                if not self._authorized():
                    return
                doc = json.loads(body)
                rkey = doc["rkey"]
                if not TID_RE.fullmatch(rkey):
                    return self._send(400, b'{"error": "InvalidRequest", "message": "bad rkey"}')
                if rkey in outer.records:
                    return self._send(400, b'{"error": "InvalidRequest", "message": "Record already exists"}')
                uri = f"at://{doc['repo']}/{doc['collection']}/{rkey}"
                outer.records[rkey] = {"uri": uri, "record": doc["record"], "doc": doc}
                if outer.on_create:
                    outer.on_create()
                if action == "lose":
                    self.close_connection = True
                    return
                self._send(200, json.dumps({"uri": uri, "cid": "bafystub"}).encode())

            def do_POST(self):
                body = self._log()
                path = urllib.parse.urlsplit(self.path).path
                if path == "/xrpc/com.atproto.server.createSession":
                    return self._bsky_session(body)
                if path == "/xrpc/com.atproto.repo.createRecord":
                    return self._bsky_create(body)
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
        """The Mastodon status POSTs."""
        return [r for r in self.requests if r["method"] == "POST" and r["path"] == "/api/v1/statuses"]

    def xrpc(self, name):
        """Every request to one Bluesky method, in order."""
        return [r for r in self.requests if r["path"].split("?")[0] == f"/xrpc/{name}"]

    def sessions(self):
        return self.xrpc("com.atproto.server.createSession")

    def creates(self):
        return self.xrpc("com.atproto.repo.createRecord")

    def getrecords(self):
        return self.xrpc("com.atproto.repo.getRecord")

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
    NETWORKS = ("mastodon", "bluesky")   # the posters registered for the test

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
                       MASTODON=self.stub.base + "/api/v1/statuses", BLUESKY=self.stub.base,
                       WAIT=0, LIVE_WAIT=0, PUSH_WAIT=0, LIVE_TRIES=2, utcnow=lambda: NOW,
                       POSTERS={k: v for k, v in m.POSTERS.items() if k in self.NETWORKS})
        for name, value in patches.items():
            p = mock.patch.object(m, name, value)
            p.start()
            self.addCleanup(p.stop)
        m.reset_session()
        self.addCleanup(m.reset_session)
        r = subprocess.run(["git", "-C", str(m.ROOT), "remote", "get-url", "origin"],
                           capture_output=True, text=True)
        self.assertTrue(r.stdout.startswith("file://"), f"origin is not a file:// path: {r.stdout!r}")

    def token(self):
        """Both fake secrets, set for one block through patch.dict, never from the real env."""
        return mock.patch.dict(os.environ, {"MASTODON_ACCESS_TOKEN": FAKE_TOKEN,
                                            "BLUESKY_APP_PASSWORD": FAKE_PASSWORD})

    def assertNoSecrets(self, out):
        for secret in (FAKE_TOKEN, FAKE_PASSWORD, FAKE_JWT):
            self.assertNotIn(secret, out)

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
        with self.token(), mock.patch.object(m, "BLUESKY", "https://bsky.social"):
            with self.assertRaises(OutboundBlocked):
                m.post_bluesky(m.read_note(m.NOTES / "alpha.md"), "text")


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
        done = {"url": "https://example.test/1"}
        state = {"notes": {"/notes/before/": {"mastodon": done, "bluesky": done}}}
        got = {n.slug: p for n, p in m.pending(notes, state, NOW)}
        self.assertNotIn("before", got)
        self.assertNotIn("draftpast", got)
        self.assertNotIn("after", got)
        self.assertEqual(got["equal"], ["mastodon", "bluesky"])

    def test_edited_body_is_not_pending(self):
        # Note carries no body and state is keyed by note.path, so an edited body cannot make a
        # recorded note due again. By construction; this pins it.
        tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        path = tmp / "edited.md"
        date = "2026-02-27T09:00:00-06:00"
        path.write_text(f"---\ndate: {date}\n---\nFirst wording of the body.\n")
        before = m.read_note(path)
        path.write_text(f"---\ndate: {date}\n---\nA different wording, with https://falkensmage.com/notes/.\n")
        after = m.read_note(path)
        self.assertEqual(before, after)
        self.assertEqual(m.tid(before), m.tid(after))
        done = {"url": "https://example.test/1"}
        state = {"notes": {before.path: {"mastodon": done, "bluesky": done}}}
        self.assertEqual(m.pending([before], state, NOW), [])
        self.assertEqual(m.pending([after], state, NOW), [])

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
    """One note travels from its live page, through a stub Mastodon and a stub Bluesky, to two
    pushed records and two u-syndication links on the rebuilt page."""

    NOTES = {"alpha": ALPHA}

    def test_a_due_note_reaches_both_stubs_is_recorded_and_pushed_then_shows_as_u_syndication(self):
        output = self.output_file()
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 0, out)
        self.assertNoSecrets(out)
        # Bluesky: a session, one getRecord, then one createRecord with the deterministic key
        note = m.read_note(m.NOTES / "alpha.md")
        rkey = m.tid(note)
        self.assertEqual(len(self.stub.sessions()), 1)
        login = json.loads(self.stub.sessions()[0]["body"])
        self.assertEqual(login, {"identifier": "falkensmage.com", "password": FAKE_PASSWORD})
        self.assertEqual(len(self.stub.getrecords()), 1)
        self.assertEqual(len(self.stub.creates()), 1)
        create = self.stub.creates()[0]
        self.assertEqual(create["headers"]["authorization"], f"Bearer {FAKE_JWT}")
        doc = json.loads(create["body"])
        self.assertEqual(set(doc), {"repo", "collection", "rkey", "record"})
        self.assertEqual((doc["repo"], doc["collection"], doc["rkey"]),
                         (m.BLUESKY_DID, "app.bsky.feed.post", rkey))
        record = doc["record"]
        self.assertEqual(record["$type"], "app.bsky.feed.post")
        self.assertEqual(record["text"], ALPHA_TEXT)
        self.assertEqual(record["langs"], ["en"])
        self.assertEqual(record["createdAt"], "2026-03-01T12:00:00.000Z")
        self.assertEqual([f["features"][0]["uri"] for f in record["facets"]],
                         ["https://example.com/a", "https://example.com/bare"])
        bsky_rec = self.local_state()["notes"][ALPHA_PATH]["bluesky"]
        self.assertEqual(bsky_rec, {"url": m.BLUESKY_WEB + rkey, "uri": self.stub.records[rkey]["uri"],
                                    "posted": "2026-03-01T12:00:00Z"})
        self.assertEqual(self.origin_state()["notes"][ALPHA_PATH]["bluesky"], bsky_rec)
        self.assertEqual(vcs(self.origin, "rev-list", "--count", "main").stdout.strip(), "3",
                         "the seed and one pushed commit per platform")
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
        # a rebuild with the records shows both links, inside the h-entry, with the exact URLs
        data = self.tmp / "data"
        data.mkdir()
        shutil.copy(m.STATE, data / "syndication.json")
        work = self.tmp / "work"
        work.mkdir()
        public = self.tmp / "public"
        build_site(public, m.NOTES, data_dir=data, work=work, clock=SYN_NOW)
        both = [(status["url"], "syndication"), (m.BLUESKY_WEB + rkey, "syndication")]
        self.assertEqual(syndication_anchors(public / "notes" / "alpha" / "index.html"), both)
        self.assertEqual(syndication_anchors(public / "notes" / "index.html"), both)
        # and a second run sends nothing, to either network
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 0, out)
        self.assertEqual(len(self.stub.posts()), 1)
        self.assertEqual(len(self.stub.creates()), 1)
        self.assertEqual(len(self.stub.sessions()), 1, "no session when nothing is pending")

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


# =========================================================================================
# The at-most-once protocol under every failure (one test per row of the script's failure table)
# =========================================================================================

def state_with(**notes):
    """A state document text with the given records: state_with(old={"mastodon": {...}})."""
    doc = {"_comment": "fixture", "notes": {f"/notes/{slug}/": plats for slug, plats in notes.items()}}
    return json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"


def rec(n):
    return {"mastodon": {"id": str(n), "posted": "2026-01-01T00:00:00Z",
                         "url": f"https://mastodon.social/@falkensmage/{n}"}}


class PostCase(SyndicationCase):
    """Helpers for tests that run `post`. Not a test itself. Mastodon only by default, which is
    the protocol the at-most-once tests were written against; Bluesky cases opt in."""

    NETWORKS = ("mastodon",)

    def run_post(self, *, expect_rc=None):
        with self.token():
            rc, out = self.run_main("post")
        self.assertNoSecrets(out)
        if expect_rc is not None:
            self.assertEqual(rc, expect_rc, out)
        return rc, out

    def keys(self):
        return {p["headers"]["idempotency-key"] for p in self.stub.posts()}

    def add_beta(self):
        """A second due note, left untracked in the checkout so a pull rebases around it."""
        (m.NOTES / "beta.md").write_text("---\ndate: %s\n---\n%s" % BETA)


class AtMostOnce(PostCase):
    NOTES = {"alpha": ALPHA}

    # --- the retry rows

    def test_a_response_lost_after_mastodon_took_the_post_is_retried_with_the_same_key(self):
        self.stub.mastodon = ["lose"]
        self.run_post(expect_rc=0)
        self.assertEqual(len(self.stub.posts()), 2)
        self.assertEqual(len(self.keys()), 1)
        self.assertEqual(len(self.stub.statuses), 1)
        self.assertEqual(self.local_state()["notes"][ALPHA_PATH]["mastodon"]["url"],
                         self.stub.statuses[0]["url"])

    def test_the_key_is_unchanged_across_runs_so_a_next_run_cannot_make_a_second_status(self):
        self.stub.mastodon = ["lose"] * m.TRIES
        rc, out = self.run_post(expect_rc=1)
        self.assertIn("::error title=Notes::", out)
        self.assertEqual(len(self.stub.posts()), m.TRIES)
        self.assertEqual(self.local_state()["notes"], {})
        later = NOW + datetime.timedelta(minutes=45)
        with mock.patch.object(m, "utcnow", lambda: later):
            self.run_post(expect_rc=0)
        self.assertEqual(len(self.keys()), 1)
        self.assertEqual(self.keys(), {hashlib.sha256(b"falkensmage.com:mastodon:/notes/alpha/").hexdigest()})
        self.assertEqual(len(self.stub.statuses), 1)
        self.assertEqual(self.origin_state()["notes"][ALPHA_PATH]["mastodon"]["url"],
                         self.stub.statuses[0]["url"])

    def test_two_500s_then_a_200_is_one_record_and_exit_0(self):
        self.stub.mastodon = [("status", 500), ("status", 500)]
        self.run_post(expect_rc=0)
        self.assertEqual(len(self.stub.posts()), 3)
        self.assertEqual(len(self.local_state()["notes"][ALPHA_PATH]), 1)
        self.assertEqual(len(self.stub.statuses), 1)

    def test_5xx_and_429_after_three_tries_leave_state_unchanged_and_exit_1(self):
        for code in (500, 503, 429):
            with self.subTest(code):
                before = len(self.stub.posts())
                self.stub.mastodon = [("status", code)] * m.TRIES
                self.run_post(expect_rc=1)
                self.assertEqual(len(self.stub.posts()) - before, m.TRIES)
        self.assertEqual(self.local_state()["notes"], {})
        self.assertEqual(self.stub.statuses, [])

    def test_4xx_is_not_retried_and_the_token_never_appears(self):
        for code in (401, 403, 422):
            with self.subTest(code):
                before = len(self.stub.posts())
                self.stub.mastodon = [("status", code)] * 5
                rc, out = self.run_post(expect_rc=1)
                self.assertEqual(len(self.stub.posts()) - before, 1)
                self.assertIn(f"HTTP {code}", out)
        self.assertEqual(self.local_state()["notes"], {})

    def test_a_redirect_from_the_api_is_a_failure_and_its_location_gets_no_request(self):
        self.stub.mastodon = [("redirect", "/elsewhere")]
        rc, out = self.run_post(expect_rc=1)
        self.assertIn("HTTP 302", out)
        self.assertEqual(len(self.stub.posts()), 1)
        self.assertEqual([r for r in self.stub.requests if r["path"].startswith("/elsewhere")], [])
        self.assertEqual(self.local_state()["notes"], {})

    def test_a_response_about_someone_elses_status_is_not_recorded(self):
        with mock.patch.object(m, "MASTODON_POST_PREFIX", "https://mastodon.social/@someone-else/"):
            rc, out = self.run_post(expect_rc=1)
        self.assertEqual(self.local_state()["notes"], {})
        self.assertIn("not a status on this account", out)

    def test_a_servers_text_cannot_start_a_workflow_command_line(self):
        self.assertEqual(m.one_line("::error title=x::boom\n::warning y\r\n"), "::error title=x::boom ::warning y")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            m.annotate("error", "line one\n::warning title=Injected::two")
        self.assertEqual(out.getvalue().count("\n"), 1)
        self.assertTrue(out.getvalue().startswith("::error title=Notes::"))

    # --- the durable-record rows

    def test_a_push_that_fails_after_retries_stops_the_run_at_once(self):
        hook = self.origin / "hooks" / "pre-receive"
        hook.write_text("#!/bin/sh\necho rejected >&2\nexit 1\n")
        hook.chmod(0o755)
        self.add_beta()  # a second due note, so there is something that must not be posted
        output = self.output_file()
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(len(self.stub.posts()), 1, "no further POST once a record cannot be made")
        line = next(l for l in out.splitlines() if l.startswith("::error"))
        self.assertIn("/notes/alpha/", line)
        self.assertIn("mastodon", line)
        self.assertIn(self.stub.statuses[0]["url"], line)
        self.assertEqual(output.read_text(), "", "recorded=true is only written once a record is durable")
        self.assertNotIn(ALPHA_PATH, vcs(self.origin, "show", "main:data/syndication.json").stdout)

    def test_a_commit_landing_on_origin_between_checkout_and_push_is_rebased_over(self):
        landed = []
        self.stub.on_post = lambda: landed or (landed.append(1), commit_to_origin(
            self.tmp, self.origin, {"OTHER.txt": "someone else\n"}))
        self.run_post(expect_rc=0)
        self.assertEqual(self.origin_state()["notes"][ALPHA_PATH]["mastodon"]["url"], self.stub.statuses[0]["url"])
        self.assertEqual(vcs(self.origin, "show", "main:OTHER.txt").stdout, "someone else\n")
        self.assertEqual(self.origin_head(), vcs(m.ROOT, "rev-parse", "HEAD").stdout.strip())
        self.assertFalse(m.rebase_in_progress())

    def test_a_rebase_conflict_on_the_state_file_aborts_the_rebase_and_exits_1(self):
        theirs = state_with(zeta=rec(9))
        landed = []
        self.stub.on_post = lambda: landed or (landed.append(1), commit_to_origin(
            self.tmp, self.origin, {"data/syndication.json": theirs}))
        rc, out = self.run_post(expect_rc=1)
        self.assertFalse(m.rebase_in_progress(), "git rebase --abort must have run")
        self.assertEqual(vcs(m.ROOT, "status", "--porcelain").stdout, "")
        self.assertIn("rebase", out)
        self.assertIn(self.stub.statuses[0]["url"], out)
        self.assertEqual(len(self.stub.posts()), 1)
        self.assertEqual(self.origin_state()["notes"].keys(), {"/notes/zeta/"})

    def test_a_record_another_run_pushed_meanwhile_is_kept_by_the_next_record(self):
        # old is recorded; alpha and beta are due. During alpha's POST another run records zzz
        # (far from alpha's insertion point, so the rebase merges cleanly). Beta's record is then
        # written from memory, which must already include zzz.
        commit_to_origin(self.tmp, self.origin, {"data/syndication.json": state_with(old=rec(1))})
        vcs(m.ROOT, "pull", "--rebase", "origin", "main")
        self.add_beta()
        theirs = state_with(old=rec(1), zzz=rec(2))
        landed = []
        self.stub.on_post = lambda: landed or (landed.append(1), commit_to_origin(
            self.tmp, self.origin, {"data/syndication.json": theirs}))
        self.run_post(expect_rc=0)
        final = self.origin_state()["notes"]
        self.assertEqual(sorted(final), ["/notes/alpha/", "/notes/beta/", "/notes/old/", "/notes/zzz/"])
        self.assertEqual(sorted(self.local_state()["notes"]), sorted(final))
        self.assertEqual(len(self.stub.posts()), 2)

    def test_a_record_in_origin_newer_than_the_checkout_is_seen_before_posting(self):
        self.add_beta()
        commit_to_origin(self.tmp, self.origin, {"data/syndication.json": state_with(alpha=rec(7))})
        self.assertNotIn("alpha", m.STATE.read_text(), "the checkout is stale")
        self.run_post(expect_rc=0)
        bodies = [urllib.parse.parse_qs(p["body"].decode())["status"][0] for p in self.stub.posts()]
        self.assertEqual(bodies, ["Beta note, plain."], "alpha was already recorded in origin")

    def test_a_failed_pull_before_posting_posts_nothing_and_exits_1(self):
        vcs(m.ROOT, "remote", "set-url", "origin", f"file://{self.tmp}/gone.git")
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(self.stub.requests, [])
        self.assertIn("::error", out)

    def test_recorded_true_reaches_the_output_at_the_first_record_even_when_a_later_step_fails(self):
        self.add_beta()
        output = self.output_file()
        self.stub.mastodon = ["ok", ("status", 401)]
        self.run_post(expect_rc=1)
        self.assertEqual(len(self.stub.posts()), 2)
        self.assertIn("recorded=true", output.read_text())
        self.assertEqual(list(self.origin_state()["notes"]), [ALPHA_PATH])

    # --- the guard rows

    def test_the_secret_absent_is_exit_1_with_no_post(self):
        rc, out = self.run_main("post")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.stub.posts(), [])
        self.assertIn("MASTODON_ACCESS_TOKEN is not set", out)
        self.assertEqual(self.local_state()["notes"], {})

    def test_a_secret_with_header_unsafe_characters_is_refused_before_it_reaches_a_header(self):
        with mock.patch.dict(os.environ, {"MASTODON_ACCESS_TOKEN": "bad token\nX-Evil: 1"}):
            rc, out = self.run_main("post")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.stub.posts(), [])
        self.assertNotIn("X-Evil", out)

    def test_dry_run_posts_nothing_and_writes_nothing(self):
        before = self.origin_head()
        local = vcs(m.ROOT, "rev-parse", "HEAD").stdout
        text = m.STATE.read_text()
        with mock.patch.dict(os.environ, {"DRY_RUN": "1"}):
            rc, out = self.run_post(expect_rc=0)
        self.assertEqual(self.stub.posts(), [])
        self.assertEqual(len(self.stub.gets(ALPHA_PATH)), 1, "the page is still fetched")
        self.assertIn("would post", out)
        self.assertEqual(m.STATE.read_text(), text)
        self.assertEqual(vcs(m.ROOT, "rev-parse", "HEAD").stdout, local)
        self.assertEqual(self.origin_head(), before)


class FacetTests(unittest.TestCase):
    def slices(self, text):
        raw = text.encode("utf-8")
        return [(raw[f["index"]["byteStart"]:f["index"]["byteEnd"]].decode("utf-8"), f["features"][0])
                for f in m.facets(text)]

    def test_offsets_are_utf8_bytes_so_an_emoji_before_a_link_does_not_shift_the_slice(self):
        text = "🎉🎉 héllo — see https://example.com/a?x=1 #wow"
        got = self.slices(text)
        self.assertEqual([s for s, _ in got], ["https://example.com/a?x=1", "#wow"])
        link = m.facets(text)[0]["index"]
        self.assertNotEqual(link["byteStart"], text.index("https"), "code points and bytes differ here")
        self.assertEqual(link["byteStart"], len(text[:text.index("https")].encode("utf-8")))

    def test_feature_shapes_a_link_holds_the_uri_and_a_tag_holds_no_hash(self):
        got = dict((s, f) for s, f in self.slices("a https://x.io/p and #Tag"))
        self.assertEqual(got["https://x.io/p"], {"$type": "app.bsky.richtext.facet#link", "uri": "https://x.io/p"})
        self.assertEqual(got["#Tag"], {"$type": "app.bsky.richtext.facet#tag", "tag": "Tag"})

    def test_trailing_punctuation_is_stripped_from_links_and_tags(self):
        text = "Read https://x.io/a. Then (https://y.io/b) and https://z.io/c! #tag! #fin;"
        self.assertEqual([s for s, _ in self.slices(text)],
                         ["https://x.io/a", "https://y.io/b", "https://z.io/c", "#tag", "#fin"])

    def test_a_link_that_holds_a_paren_keeps_its_closing_paren(self):
        self.assertEqual([s for s, _ in self.slices("see https://en.wikipedia.org/wiki/A_(b)")],
                         ["https://en.wikipedia.org/wiki/A_(b)"])

    def test_no_tag_for_digits_for_a_fragment_inside_a_link_or_a_hash_mid_word(self):
        text = "item #123 and #1_2 at https://x.io/p#frag, but x#nope and # alone"
        self.assertEqual([s for s, _ in self.slices(text)], ["https://x.io/p#frag"])

    def test_a_tag_over_64_code_points_has_no_facet_and_64_does(self):
        self.assertEqual(self.slices("#" + "a" * 65), [])
        self.assertEqual([f["tag"] for _, f in self.slices("#" + "a" * 64)], ["a" * 64])

    def test_a_tag_may_start_the_text_and_a_link_may_start_the_text(self):
        self.assertEqual([s for s, _ in self.slices("#start https://x.io")], ["#start", "https://x.io"])
        self.assertEqual([s for s, _ in self.slices("https://x.io #end")], ["https://x.io", "#end"])

    def test_unicode_tags_and_sorting_by_byte_start(self):
        facets = m.facets("#日本語 then https://x.io then #z")
        starts = [f["index"]["byteStart"] for f in facets]
        self.assertEqual(starts, sorted(starts))
        self.assertEqual([f["features"][0].get("tag") or f["features"][0]["uri"] for f in facets],
                         ["日本語", "https://x.io", "z"])

    def test_plain_text_has_no_facets_and_find_urls_gives_code_point_spans(self):
        self.assertEqual(m.facets("nothing to link, not even example.com"), [])
        text = "é https://x.io/a"
        (start, end), = m.find_urls(text)
        self.assertEqual(text[start:end], "https://x.io/a")


class TidTests(unittest.TestCase):
    def note(self, path, stamp="2026-11-01T09:00:00-05:00"):
        return m.Note(path.strip("/").split("/")[-1], path, datetime.datetime.fromisoformat(stamp.replace("Z", "+00:00")), False)

    def decode(self, key):
        value = 0
        for ch in key:
            value = value * 32 + m.B32.index(ch)
        return value

    def test_the_known_value_for_the_planned_note(self):
        self.assertEqual(m.tid(self.note("/notes/2026-11-01-0900/")), "3mzaxt2cwok3b")

    def test_deterministic_valid_tid_syntax_and_different_paths_differ(self):
        a = self.note("/notes/alpha/")
        self.assertEqual(m.tid(a), m.tid(self.note("/notes/alpha/")))
        self.assertRegex(m.tid(a), TID_RE)
        keys = {m.tid(self.note(f"/notes/n{i}/")) for i in range(200)}
        self.assertEqual(len(keys), 200)
        self.assertTrue(all(TID_RE.fullmatch(k) for k in keys))

    def test_it_decodes_to_the_notes_own_second_and_the_top_bit_is_zero(self):
        for stamp in ("2026-11-01T09:00:00-05:00", "2026-03-01T12:00:00Z", "2099-12-31T23:59:59+14:00"):
            note = self.note("/notes/x/", stamp)
            value = self.decode(m.tid(note))
            self.assertEqual(value >> 63, 0)
            self.assertEqual((value >> 10) // 1_000_000, int(note.date.timestamp()))

    def test_it_does_not_depend_on_the_site_or_the_clock(self):
        before = m.tid(self.note("/notes/alpha/"))
        with mock.patch.object(m, "SITE", "http://elsewhere.invalid"), mock.patch.object(m, "utcnow", lambda: NOW):
            self.assertEqual(m.tid(self.note("/notes/alpha/")), before)


class BlueskyCase(PostCase):
    """Both networks registered, ALPHA due. Not a test itself."""

    NETWORKS = ("mastodon", "bluesky")
    NOTES = {"alpha": ALPHA}

    def rkey(self, slug="alpha"):
        return m.tid(m.read_note(m.NOTES / f"{slug}.md"))

    def recorded(self, path=ALPHA_PATH):
        return sorted(self.origin_state()["notes"].get(path, {}))


class BlueskyPosting(BlueskyCase):
    def test_a_note_reaches_bluesky_directly_and_nothing_else_is_called(self):
        self.run_post(expect_rc=0)
        paths = {r["path"].split("?")[0] for r in self.stub.requests}
        self.assertEqual(paths, {ALPHA_PATH, "/api/v1/statuses", "/xrpc/com.atproto.server.createSession",
                                 "/xrpc/com.atproto.repo.getRecord", "/xrpc/com.atproto.repo.createRecord"})
        source = (ROOT / "scripts" / "syndicate-notes.py").read_text().lower()
        self.assertNotIn("buffer", source)

    def test_the_password_goes_only_in_the_session_body_and_the_token_only_in_headers(self):
        self.run_post(expect_rc=0)
        for req in self.stub.requests:
            is_login = req["path"].endswith("createSession")
            self.assertEqual(FAKE_PASSWORD.encode() in req["body"], is_login, req["path"])
            self.assertNotIn(FAKE_PASSWORD, req["path"])
            self.assertNotIn(FAKE_JWT, req["path"])
            self.assertNotIn(FAKE_JWT.encode(), req["body"])
            self.assertNotIn(FAKE_PASSWORD, str(req["headers"]))

    def test_mastodon_ok_then_bluesky_500_three_times_records_mastodon_and_the_next_run_posts_only_bluesky(self):
        self.stub.bsky_create = [("status", 500)] * m.TRIES
        output = self.output_file()
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(len(self.stub.creates()), m.TRIES)
        self.assertEqual(len(self.stub.getrecords()), m.TRIES, "getRecord is asked again before each create")
        self.assertEqual(self.recorded(), ["mastodon"])
        self.assertEqual(self.stub.records, {})
        self.assertIn("recorded=true", output.read_text())
        # the next run: the page is live, so there is nothing to deploy
        output.write_text("")
        self.assertEqual(self.run_main("check")[0], 0)
        self.assertEqual(sorted(output.read_text().split()), ["deploy=false", "pending=true"])
        self.run_post(expect_rc=0)
        self.assertEqual(len(self.stub.posts()), 1, "no second Mastodon POST")
        self.assertEqual(self.recorded(), ["bluesky", "mastodon"])
        self.assertEqual(len(self.stub.records), 1)

    def test_a_failed_bluesky_login_still_lets_mastodon_post(self):
        self.stub.bsky_session = [("status", 500)]
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(len(self.stub.posts()), 1)
        self.assertEqual(self.recorded(), ["mastodon"])
        self.assertEqual(self.stub.getrecords() + self.stub.creates(), [])
        self.assertIn("createSession failed", out)

    def test_mastodon_failing_does_not_stop_bluesky_and_the_next_run_retries_only_mastodon(self):
        self.stub.mastodon = [("status", 500)] * m.TRIES
        self.run_post(expect_rc=1)
        self.assertEqual(self.recorded(), ["bluesky"])
        self.run_post(expect_rc=0)
        self.assertEqual(self.recorded(), ["bluesky", "mastodon"])
        self.assertEqual(len(self.stub.creates()), 1, "Bluesky was not posted again")
        self.assertEqual(len(self.stub.statuses), 1)

    def test_a_response_lost_after_the_record_was_made_is_adopted_by_getrecord_not_recreated(self):
        self.stub.bsky_create = ["lose"]
        self.run_post(expect_rc=0)
        self.assertEqual(len(self.stub.records), 1)
        self.assertEqual(len(self.stub.creates()), 1, "the retry found the record and created nothing")
        self.assertEqual(len(self.stub.getrecords()), 2)
        rec = self.local_state()["notes"][ALPHA_PATH]["bluesky"]
        self.assertEqual(rec["uri"], self.stub.records[self.rkey()]["uri"])
        self.assertEqual(rec["url"], m.BLUESKY_WEB + self.rkey())

    def test_a_record_the_state_lost_is_adopted_at_any_later_time_without_a_second_post(self):
        # A post exists on Bluesky but the state never heard of it (the residual window).
        self.stub.records[self.rkey()] = {"uri": f"at://{m.BLUESKY_DID}/app.bsky.feed.post/{self.rkey()}",
                                          "record": {}}
        later = NOW + datetime.timedelta(hours=5)
        with mock.patch.object(m, "utcnow", lambda: later):
            self.run_post(expect_rc=0)
        self.assertEqual(self.stub.creates(), [])
        self.assertEqual(len(self.stub.records), 1)
        self.assertEqual(self.local_state()["notes"][ALPHA_PATH]["bluesky"]["uri"],
                         self.stub.records[self.rkey()]["uri"])

    def test_the_key_is_never_random_two_runs_ask_for_the_same_record(self):
        self.stub.bsky_create = [("status", 500)] * m.TRIES
        self.run_post(expect_rc=1)
        first = {json.loads(r["body"])["rkey"] for r in self.stub.creates()}
        self.run_post(expect_rc=0)
        second = {json.loads(r["body"])["rkey"] for r in self.stub.creates()}
        self.assertEqual(first, {self.rkey()})
        self.assertEqual(second, {self.rkey()})

    def test_getrecord_500_three_times_sends_no_createrecord(self):
        self.stub.bsky_get = [("status", 500)] * m.TRIES
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(self.stub.creates(), [])
        self.assertEqual(len(self.stub.getrecords()), m.TRIES)
        self.assertEqual(self.recorded(), ["mastodon"])

    def test_getrecord_400_other_than_recordnotfound_sends_no_createrecord_and_is_not_retried(self):
        self.stub.bsky_get = [("status", 400, "InvalidRequest")]
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(self.stub.creates(), [])
        self.assertEqual(len(self.stub.getrecords()), 1)
        self.assertIn("getRecord HTTP 400: InvalidRequest", out)

    def test_createrecord_4xx_is_not_retried(self):
        self.stub.bsky_create = [("status", 400, "InvalidRequest")]
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(len(self.stub.creates()), 1)
        self.assertEqual(self.recorded(), ["mastodon"])

    def test_a_429_on_createrecord_is_retried(self):
        self.stub.bsky_create = [("status", 429), "ok"]
        self.run_post(expect_rc=0)
        self.assertEqual(len(self.stub.creates()), 2)
        self.assertEqual(len(self.stub.records), 1)

    def test_a_uri_that_does_not_end_with_the_key_is_refused(self):
        original = m._bsky

        def wrong(method, name, **kw):
            status, doc = original(method, name, **kw)
            if name.endswith("createRecord") and doc:
                doc["uri"] = doc["uri"] + "x"
            return status, doc

        with mock.patch.object(m, "_bsky", wrong):
            rc, out = self.run_post(expect_rc=1)
        self.assertEqual(self.recorded(), ["mastodon"])
        self.assertIn("no matching uri", out)

    def test_a_session_for_another_account_posts_nothing_to_bluesky_and_is_tried_once_per_run(self):
        self.add_beta()
        self.stub.bsky_session = [("did", "did:plc:someoneelse")]
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(len(self.stub.sessions()), 1, "a broken login is not retried for the next note")
        self.assertEqual(self.stub.getrecords() + self.stub.creates(), [])
        self.assertEqual(len(self.stub.posts()), 2, "Mastodon still posted both")
        self.assertIn("different account", out)

    def test_a_rejected_login_is_tried_once_per_run(self):
        self.add_beta()
        self.stub.bsky_session = [("status", 401, "AuthenticationRequired")] * 5
        rc, out = self.run_post(expect_rc=1)
        self.assertEqual(len(self.stub.sessions()), 1)
        self.assertEqual(self.stub.creates(), [])

    def test_the_password_absent_fails_bluesky_posts_mastodon_and_exits_1(self):
        with mock.patch.dict(os.environ, {"MASTODON_ACCESS_TOKEN": FAKE_TOKEN}):
            rc, out = self.run_main("post")
        self.assertEqual(rc, 1, out)
        self.assertEqual(len(self.stub.posts()), 1)
        self.assertEqual(self.stub.sessions(), [], "no login without a password")
        self.assertIn("BLUESKY_APP_PASSWORD is not set", out)
        self.assertEqual(self.recorded(), ["mastodon"])

    def test_a_set_password_appears_in_no_output_even_when_every_call_fails(self):
        self.stub.bsky_session = [("status", 500)]
        rc, out = self.run_post(expect_rc=1)
        self.assertNotIn(FAKE_PASSWORD, out)

    def test_no_session_is_made_when_nothing_is_pending(self):
        self.run_post(expect_rc=0)
        before = len(self.stub.requests)
        self.run_post(expect_rc=0)
        self.assertEqual(len(self.stub.sessions()), 1)
        self.assertEqual([r for r in self.stub.requests[before:] if r["path"].startswith("/xrpc")], [])

    def test_a_dry_run_makes_no_bluesky_call(self):
        with mock.patch.dict(os.environ, {"DRY_RUN": "1"}):
            self.run_post(expect_rc=0)
        self.assertEqual([r for r in self.stub.requests if r["path"].startswith("/xrpc")], [])


class FitTests(unittest.TestCase):
    URL = "https://falkensmage.com/notes/x/"
    SUFFIX = "… " + URL

    def test_text_at_exactly_the_limit_is_unchanged_and_one_over_is_cut(self):
        at = "abc " * 74 + "abcd"
        self.assertEqual(len(at), 300)
        self.assertEqual(m.fit(at, 300, self.URL), at)
        out = m.fit(at + "e", 300, self.URL)
        self.assertNotEqual(out, at + "e")
        self.assertLessEqual(len(out), 300)

    def test_a_cut_lands_on_a_word_boundary_ends_in_ellipsis_space_url_and_keeps_as_much_as_fits(self):
        words = ["w%08d" % i for i in range(60)]
        text = " ".join(words)
        out = m.fit(text, 300, self.URL)
        self.assertTrue(out.endswith(self.SUFFIX))
        body = out[:-len(self.SUFFIX)]
        self.assertTrue(text.startswith(body))
        self.assertEqual(text[len(body)], " ", "the cut is at the end of a word")
        self.assertLessEqual(len(out), 300)
        longer = text[:len(body) + 10]   # one more word
        self.assertGreater(len(longer + self.SUFFIX), 300, "a longer cut would not have fit")

    def test_a_single_word_longer_than_the_room_is_cut_hard_and_stays_within_the_limit(self):
        out = m.fit("x" * 400, 300, self.URL)
        self.assertTrue(out.endswith(self.SUFFIX))
        self.assertLessEqual(len(out), 300)
        self.assertEqual(set(out[:-len(self.SUFFIX)]), {"x"})
        self.assertEqual(len(out), 300, "the hard cut uses all the room")

    def test_a_hard_cut_never_ends_inside_a_link_the_link_is_dropped_whole(self):
        text = "https://example.com/" + "a" * 400
        self.assertEqual(m.fit(text, 300, self.URL), self.URL)
        text = "hi " + "https://example.com/" + "a" * 400
        out = m.fit(text, 300, self.URL)
        self.assertEqual(out, "hi" + self.SUFFIX)

    def test_a_link_in_the_kept_part_is_never_split(self):
        text = "see https://example.com/page and " + "word " * 80
        out = m.fit(text, 300, self.URL)
        self.assertIn("https://example.com/page", out)

    def test_300_single_code_point_characters_are_whole_for_bluesky_and_301_are_not(self):
        self.assertEqual(m.fit("x" * 300, m.BLUESKY_LIMIT, self.URL), "x" * 300)
        self.assertNotEqual(m.fit("x" * 301, m.BLUESKY_LIMIT, self.URL), "x" * 301)

    def test_a_zwj_heavy_note_of_310_code_points_is_truncated_the_recorded_conservative_count(self):
        family = "\U0001F468‍\U0001F469‍\U0001F467"   # one grapheme, five code points
        text = " ".join([family] * 52)
        self.assertEqual(len(text), 311)
        out = m.fit(text, m.BLUESKY_LIMIT, self.URL)
        self.assertNotEqual(out, text)
        self.assertLessEqual(len(out), 300)
        self.assertTrue(out.endswith(self.SUFFIX))

    def test_a_510_character_note_holding_a_60_character_link_fits_mastodon_whole(self):
        link = "https://example.com/" + "p" * 40
        text = "abcd " * 90 + link
        self.assertEqual((len(link), len(text)), (60, 510))
        self.assertEqual(m.mastodon_length(text), 473)
        self.assertEqual(m.fit(text, m.MASTODON_LIMIT, self.URL, m.mastodon_length), text)
        self.assertNotEqual(m.fit(text, m.BLUESKY_LIMIT, self.URL), text)

    def test_mastodon_cuts_by_its_own_count_and_stays_within_500(self):
        text = "word " * 150 + "https://example.com/" + "p" * 40
        out = m.fit(text, m.MASTODON_LIMIT, self.URL, m.mastodon_length)
        self.assertLessEqual(m.mastodon_length(out), 500)
        self.assertTrue(out.endswith(self.SUFFIX))

    def test_a_link_back_that_cannot_fit_is_a_post_error_not_a_bad_post(self):
        with self.assertRaises(m.PostError):
            m.fit("word " * 100, 20, self.URL)


class LengthPosting(BlueskyCase):
    def note(self):
        return m.read_note(m.NOTES / "alpha.md")

    def bsky_record(self):
        return self.stub.records[self.rkey()]["record"]

    def test_a_note_of_300_characters_goes_to_bluesky_whole_with_no_link_back(self):
        with self.token():
            m.post_bluesky(self.note(), "x" * 300)
        self.assertEqual(self.bsky_record()["text"], "x" * 300)
        self.assertNotIn("facets", self.bsky_record())

    def test_a_truncated_bluesky_post_links_back_to_the_note_with_an_exact_facet(self):
        text = " ".join(["word"] * 100) + " #cuttag"
        with self.token():
            m.post_bluesky(self.note(), text)
        record = self.bsky_record()
        link = m.SITE + ALPHA_PATH
        self.assertTrue(record["text"].endswith("… " + link))
        self.assertLessEqual(len(record["text"]), 300)
        facet = record["facets"][-1]
        raw = record["text"].encode("utf-8")
        self.assertEqual(raw[facet["index"]["byteStart"]:facet["index"]["byteEnd"]].decode(), link)
        self.assertEqual(facet["features"][0]["uri"], link)
        self.assertEqual([f for f in record["facets"] if f["features"][0]["$type"].endswith("#tag")], [],
                         "the tag was cut off, so it has no facet")

    def test_a_tag_split_by_a_hard_cut_has_no_facet_but_the_link_back_does(self):
        with self.token():
            m.post_bluesky(self.note(), "#" + "t" * 400)
        record = self.bsky_record()
        self.assertTrue(record["text"].startswith("#ttt"))
        kinds = [f["features"][0]["$type"] for f in record["facets"]]
        self.assertEqual(kinds, ["app.bsky.richtext.facet#link"])

    def test_a_tag_that_survives_the_cut_keeps_its_facet(self):
        text = "#early " + " ".join(["word"] * 100)
        with self.token():
            m.post_bluesky(self.note(), text)
        tags = [f["features"][0].get("tag") for f in self.bsky_record()["facets"]]
        self.assertEqual(tags[:1], ["early"])

    def test_a_510_character_note_goes_to_mastodon_whole(self):
        link = "https://example.com/" + "p" * 40
        text = "abcd " * 90 + link
        with self.token():
            m.post_mastodon(self.note(), text)
        form = urllib.parse.parse_qs(self.stub.posts()[0]["body"].decode("utf-8"))
        self.assertEqual(form["status"], [text])

    def test_a_long_note_goes_to_mastodon_cut_with_its_own_link_back(self):
        with self.token():
            m.post_mastodon(self.note(), "word " * 200)
        status = urllib.parse.parse_qs(self.stub.posts()[0]["body"].decode("utf-8"))["status"][0]
        self.assertTrue(status.endswith("… " + m.SITE + ALPHA_PATH))
        self.assertLessEqual(m.mastodon_length(status), 500)

    def test_a_dry_run_logs_how_each_network_counts_the_text(self):
        with mock.patch.dict(os.environ, {"DRY_RUN": "1"}):
            rc, out = self.run_post(expect_rc=0)
        self.assertIn("mastodon: would post", out)
        self.assertIn("of 500 counted, whole", out)
        self.assertIn("of 300 counted, whole", out)
        self.assertEqual(self.stub.posts() + self.stub.creates(), [])


class MissingState(SyndicationCase):
    NOTES = {"alpha": ALPHA}
    STATE = None

    def test_a_missing_state_file_posts_nothing_and_exits_1(self):
        self.assertFalse(m.STATE.exists())
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.stub.requests, [])
        self.assertIn("syndication.json", out)
        self.assertFalse(m.STATE.exists(), "it must not be recreated empty")

    def test_check_also_fails_on_a_missing_state_file(self):
        rc, out = self.run_main("check")
        self.assertEqual(rc, 1, out)


class MalformedState(SyndicationCase):
    NOTES = {"alpha": ALPHA}
    STATE = '{"notes": []}\n'

    def test_a_malformed_state_file_posts_nothing_and_exits_1(self):
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.stub.requests, [])


class MalformedNote(SyndicationCase):
    NOTES = {"alpha": ALPHA}

    def test_a_malformed_note_posts_nothing_and_exits_1_naming_the_file(self):
        (m.NOTES / "broken.md").write_text("---\ndate: 2026-02-01\n---\nHi\n")
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 1, out)
        self.assertIn("broken.md", out)
        self.assertEqual(self.stub.posts(), [])


class Window(SyndicationCase):
    NETWORKS = ("mastodon",)
    NOTES = {"alpha": ALPHA, "beta": BETA, "gamma": GAMMA,
             "drafty": ("2026-02-20T09:00:00-06:00", "A draft.\n", "draft: true")}

    def test_a_note_older_than_7_days_is_never_posted_and_warns(self):
        later = NOW + datetime.timedelta(days=20)
        with mock.patch.object(m, "utcnow", lambda: later), self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.stub.requests, [])
        self.assertIn("::warning title=Notes::/notes/alpha/", out)
        self.assertIn("::warning title=Notes::/notes/beta/", out)
        self.assertEqual(self.local_state()["notes"], {})

    def test_the_window_is_exactly_a_week_and_a_recorded_note_never_warns(self):
        notes = [n for n in m.load_notes(m.NOTES) if n.slug in ("alpha", "beta")]
        edge = notes[0].date + m.MAX_AGE
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual([n.slug for n, _ in m.pending(notes, {"notes": {}}, edge)], ["alpha", "beta"])
            self.assertEqual(out.getvalue(), "", "exactly 7 days old is still in the window")
            past = edge + datetime.timedelta(seconds=1)
            self.assertEqual([n.slug for n, _ in m.pending(notes, {"notes": {}}, past)], ["beta"])
        self.assertIn("::warning title=Notes::/notes/alpha/", out.getvalue())
        out = io.StringIO()
        recorded = {"notes": {ALPHA_PATH: rec(1), BETA_PATH: rec(2)}}
        with contextlib.redirect_stdout(out):
            self.assertEqual(m.pending(notes, recorded, edge + datetime.timedelta(days=30)), [])
        self.assertEqual(out.getvalue(), "")

    def test_a_draft_and_a_future_note_are_not_posted_and_nothing_is_fetched_for_them(self):
        with mock.patch.object(m, "utcnow", lambda: NOW - datetime.timedelta(days=60)), self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 0, out)
        self.assertEqual(self.stub.requests, [])
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 0, out)
        paths = {r["path"] for r in self.stub.requests if r["method"] == "GET"}
        self.assertEqual(paths, {ALPHA_PATH, BETA_PATH})


class LivePage(SyndicationCase):
    NETWORKS = ("mastodon",)
    NOTES = {"alpha": ALPHA, "beta": BETA}

    def test_a_page_that_never_goes_live_sends_no_post_and_a_later_note_gets_one_try(self):
        self.stub.site = self.tmp / "empty-site"
        self.stub.site.mkdir()
        with mock.patch.object(m, "LIVE_TRIES", 3):
            with self.token():
                rc, out = self.run_main("post")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.stub.posts(), [])
        self.assertEqual(len(self.stub.gets(ALPHA_PATH)), 3)
        self.assertEqual(len(self.stub.gets(BETA_PATH)), 1)
        self.assertIn("never went live", out)

    def test_a_live_page_with_no_e_content_sends_no_post_and_exits_1(self):
        site = self.tmp / "bare-site"
        for slug in ("alpha", "beta"):
            (site / "notes" / slug).mkdir(parents=True)
            (site / "notes" / slug / "index.html").write_text("<html><body><p>no entry here</p></body></html>")
        self.stub.site = site
        with self.token():
            rc, out = self.run_main("post")
        self.assertEqual(rc, 1, out)
        self.assertEqual(self.stub.posts(), [])
        self.assertIn("e-content", out)
        self.assertEqual(len(self.stub.gets(ALPHA_PATH)), 1, "waiting does not fix a page with no e-content")

    def test_check_with_a_due_note_says_deploy_false_when_live_and_true_when_not(self):
        output = self.output_file()
        self.assertEqual(self.run_main("check")[0], 0)
        self.assertEqual(sorted(output.read_text().split()), ["deploy=false", "pending=true"])
        self.stub.site = self.tmp / "empty-site"
        self.stub.site.mkdir()
        output.write_text("")
        self.assertEqual(self.run_main("check")[0], 0)
        self.assertEqual(sorted(output.read_text().split()), ["deploy=true", "pending=true"])
        self.assertEqual(self.stub.posts(), [])

    def test_check_deploys_when_any_one_pending_page_is_missing(self):
        site = self.tmp / "half-site"
        shutil.copytree(Builds.get("syn"), site)
        shutil.rmtree(site / "notes" / "beta")
        self.stub.site = site
        output = self.output_file()
        self.assertEqual(self.run_main("check")[0], 0)
        self.assertEqual(sorted(output.read_text().split()), ["deploy=true", "pending=true"])


# =========================================================================================
# The workflows' properties (stdlib has no YAML parser and the suite runs under -I -S, so these
# read the files by indentation: top-level keys, the `on:` block and one block per job)
# =========================================================================================

WORKFLOWS = ROOT / ".github" / "workflows"


def _strip_comments(text):
    out = []
    for line in text.splitlines():
        if line.lstrip().startswith("#"):
            continue
        out.append(re.sub(r"\s+#(?=[^\"']*$).*$", "", line).rstrip())
    return out


def workflow_blocks(path):
    """(top, jobs): `top` maps each top-level key to its text (key line included); `jobs` maps each
    job name to its block of lines. Comments are dropped, so a sentence in a header comment can
    never satisfy or break an assertion."""
    top, jobs, key, job = {}, {}, None, None
    for line in _strip_comments(Path(path).read_text(encoding="utf-8")):
        if not line.strip():
            continue
        if not line.startswith(" "):
            key, job = line.split(":", 1)[0], None
            top[key] = [line]
            continue
        top[key].append(line)
        if key == "jobs":
            found = re.fullmatch(r"  ([A-Za-z][\w-]*):", line)
            if found:
                job = found.group(1)
                jobs[job] = []
            if job:
                jobs[job].append(line)
    return {k: "\n".join(v) for k, v in top.items()}, {k: "\n".join(v) for k, v in jobs.items()}


def steps_of(block):
    """A job block split into its steps (each starts at a `      - ` line)."""
    steps, cur = [], None
    for line in block.splitlines():
        if re.match(r"      - ", line):
            cur = [line]
            steps.append(cur)
        elif cur is not None and line.startswith("        "):
            cur.append(line)
        else:
            cur = None
    return ["\n".join(s) for s in steps]


def run_strings(block):
    """Every `run:` value in a block: the one line, or the lines of a `|` or `>` scalar."""
    lines, out, i = block.splitlines(), [], 0
    while i < len(lines):
        found = re.match(r"(\s*)(?:- )?run:\s*(.*)", lines[i])
        if found:
            indent, value = len(found.group(1)), found.group(2)
            if value[:1] in ("|", ">"):
                body = []
                while i + 1 < len(lines) and (len(lines[i + 1]) - len(lines[i + 1].lstrip())) > indent:
                    body.append(lines[i + 1])
                    i += 1
                value = "\n".join(body)
            out.append(value)
        i += 1
    return out


class WorkflowConfig(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.top, cls.jobs = workflow_blocks(WORKFLOWS / "notes.yml")
        cls.hugo_top, cls.hugo_jobs = workflow_blocks(WORKFLOWS / "hugo.yml")

    def test_helper_splits_a_workflow_into_top_keys_and_job_blocks(self):
        self.assertEqual(list(self.jobs), ["check", "syndicate", "rebuild"])
        self.assertEqual({"name", "on", "permissions", "concurrency", "defaults", "jobs"}, set(self.top))
        self.assertEqual(list(self.hugo_jobs), ["build", "deploy", "email", "webmentions", "mentions-probe"])

    # --- triggers

    def test_only_a_schedule_and_a_manual_dispatch_can_start_it(self):
        triggers = re.findall(r"^  ([a-z_]+):", self.top["on"], re.M)
        self.assertEqual(sorted(triggers), ["schedule", "workflow_dispatch"])
        for forbidden in ("push", "pull_request", "pull_request_target", "workflow_run", "repository_dispatch"):
            self.assertNotIn(forbidden, self.top["on"])

    def test_the_schedule_is_every_fifteen_minutes_off_the_hour(self):
        crons = re.findall(r'cron:\s*"([^"]+)"', self.top["on"])
        self.assertEqual(crons, ["7,22,37,52 * * * *"])
        minutes = [int(x) for x in crons[0].split()[0].split(",")]
        self.assertEqual([b - a for a, b in zip(minutes, minutes[1:])], [15, 15, 15])
        self.assertNotIn(0, minutes, "the top of the hour is when GitHub's schedule is most delayed")

    # --- concurrency, permissions, secrets

    def test_its_concurrency_group_is_its_own_and_never_the_pages_group(self):
        self.assertIn("group: notes-syndication", self.top["concurrency"])
        self.assertIn("cancel-in-progress: false", self.top["concurrency"])
        self.assertNotIn("pages", self.top["concurrency"])
        self.assertIn('group: "pages"', self.hugo_top["concurrency"])
        for block in self.jobs.values():
            self.assertNotIn("concurrency", block)

    def test_the_workflow_starts_with_no_permissions_and_each_job_asks_for_its_own(self):
        self.assertEqual(self.top["permissions"].strip(), "permissions: {}")
        grants = {name: sorted(re.findall(r"^      ([a-z-]+): (?:read|write)$", block, re.M))
                  for name, block in self.jobs.items()}
        self.assertEqual(grants, {"check": ["actions", "contents"], "syndicate": ["contents"],
                                  "rebuild": ["actions"]})
        self.assertIn("contents: read", self.jobs["check"])
        self.assertIn("actions: write", self.jobs["check"])
        self.assertIn("contents: write", self.jobs["syndicate"])
        self.assertIn("actions: write", self.jobs["rebuild"])

    def test_contents_write_and_both_secrets_exist_in_exactly_one_job(self):
        holders = [name for name, block in self.jobs.items() if "contents: write" in block]
        self.assertEqual(holders, ["syndicate"])
        for secret in ("MASTODON_ACCESS_TOKEN", "BLUESKY_APP_PASSWORD"):
            self.assertEqual([n for n, b in self.jobs.items() if f"secrets.{secret}" in b], ["syndicate"])
        self.assertNotIn("secrets.", self.top["on"] + self.top["permissions"] + self.top["concurrency"])
        # in one step's env only
        step_holders = [s for s in steps_of(self.jobs["syndicate"]) if "secrets." in s]
        self.assertEqual(len(step_holders), 1)
        self.assertIn("syndicate-notes.py post", step_holders[0])
        self.assertNotIn("GITHUB_TOKEN", "".join(self.jobs.values()), "no token is written out by hand")

    def test_the_other_workflows_deploy_permissions_do_not_change(self):
        self.assertIn("contents: read", self.hugo_top["permissions"])
        self.assertNotIn("contents: write", self.hugo_top["permissions"])
        for name, block in self.hugo_jobs.items():
            self.assertNotIn("contents: write", block, name)

    # --- checkouts, expressions, actions

    def test_every_checkout_is_on_ref_main(self):
        seen = 0
        for name, block in self.jobs.items():
            for step in steps_of(block):
                if "actions/checkout" in step:
                    seen += 1
                    self.assertRegex(step, r"\n\s+ref: main\b", f"{name}: a checkout without ref: main")
        self.assertEqual(seen, 2)

    def test_no_expression_is_interpolated_into_a_run_string(self):
        runs = [r for b in self.jobs.values() for r in run_strings(b)]
        self.assertGreaterEqual(len(runs), 4)
        for run in runs:
            self.assertNotIn("${{", run)

    def test_the_only_action_used_is_the_checkout(self):
        used = re.findall(r"uses:\s*(\S+)", "\n".join(self.jobs.values()))
        self.assertTrue(used)
        for action in used:
            self.assertTrue(action.startswith("actions/checkout@"), action)

    def test_every_job_declares_a_timeout_and_the_syndicate_outlasts_the_live_wait(self):
        for name, block in self.jobs.items():
            self.assertRegex(block, r"timeout-minutes: \d+", name)
        minutes = int(re.search(r"timeout-minutes: (\d+)", self.jobs["syndicate"]).group(1))
        self.assertGreater(minutes * 60, m.LIVE_TRIES * m.LIVE_WAIT)

    # --- the shape: check, then syndicate, then rebuild

    def test_jobs_run_check_then_syndicate_then_rebuild(self):
        self.assertNotIn("needs:", self.jobs["check"])
        self.assertRegex(self.jobs["syndicate"], r"needs: check\b")
        self.assertRegex(self.jobs["rebuild"], r"needs: syndicate\b")
        self.assertIn("needs.check.outputs.pending == 'true'", self.jobs["syndicate"])
        self.assertIn("pending: ${{ steps.due.outputs.pending }}", self.jobs["check"])

    def test_a_deploy_is_dispatched_only_when_the_check_says_a_page_is_not_live(self):
        deploys = [s for s in steps_of(self.jobs["check"]) if "gh workflow run hugo.yml" in s]
        self.assertEqual(len(deploys), 1)
        self.assertIn("if: steps.due.outputs.deploy == 'true'", deploys[0])
        self.assertIn("GH_TOKEN: ${{ github.token }}", deploys[0])
        self.assertIn("--ref main", deploys[0])
        self.assertIn("id: due", self.jobs["check"])
        self.assertIn("syndicate-notes.py check", self.jobs["check"])

    def test_the_rebuild_runs_after_a_partial_success_and_only_when_something_was_recorded(self):
        self.assertIn("!cancelled() && needs.syndicate.outputs.recorded == 'true'", self.jobs["rebuild"])
        self.assertIn("recorded: ${{ steps.post.outputs.recorded }}", self.jobs["syndicate"])
        self.assertIn("gh workflow run hugo.yml", self.jobs["rebuild"])

    def test_a_failed_post_is_not_swallowed(self):
        for block in self.jobs.values():
            self.assertNotIn("continue-on-error", block)
            self.assertNotIn("|| true", block)

    # --- the deploy gate

    def test_the_deploy_gate_runs_the_notes_probe_after_the_fa_probe_and_the_notes_suite(self):
        steps = steps_of(self.hugo_jobs["build"])
        names = [re.search(r"name: (.+)", s).group(1) for s in steps]
        self.assertEqual(names[names.index("Validate Feral Architecture section") + 1], "Validate notes")
        self.assertIn("run: bash tests/validate-notes.sh", steps[names.index("Validate notes")])
        suites = steps[names.index("Run Python test suites")]
        self.assertIn("python3 -I -S -B tests/test-notes.py", suites)
        self.assertIn("python3 -I -S -B tests/test-send-webmentions.py", suites)
        self.assertIn("Send Webmentions for the newest essay and recent notes",
                      "\n".join(steps_of(self.hugo_jobs["webmentions"])))

    def test_neither_the_deploy_nor_the_site_config_builds_future_notes(self):
        hugo_yml = (WORKFLOWS / "hugo.yml").read_text() + (WORKFLOWS / "notes.yml").read_text()
        config = (ROOT / "hugo.toml").read_text()
        for text in (hugo_yml, config):
            self.assertNotRegex(text, r"(?i)buildFuture|--buildFuture|\bhugo\b[^\n]* -F\b")

    def test_the_deploy_workflow_can_be_dispatched_without_inputs(self):
        self.assertIn("workflow_dispatch:", self.hugo_top["on"])
        self.assertIn("default: false", self.hugo_top["on"], "send_email defaults off, so a note deploy mails nobody")
        self.assertIn("SEND_EMAIL: ${{ github.event_name == 'workflow_dispatch' && inputs.send_email }}",
                      self.hugo_jobs["email"])


if __name__ == "__main__":
    unittest.main()
