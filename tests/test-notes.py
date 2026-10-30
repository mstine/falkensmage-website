#!/usr/bin/env python3
"""Tests for the Notes section (/notes/): the h-entry page, the index, the feed, the nav, and
the probes that guard them.

    python3 -I -S -B tests/test-notes.py

-I -S proves the tests are stdlib-only by execution. There is no outbound network: every
Hugo build carries `[security.http] urls = ["^$"]`, so the theme's remote fetch is denied.
`hugo` must be on PATH: its absence is a failure, never a skip, so the render checks cannot
silently vanish.

No test depends on what real notes exist. Each build mounts a temp directory of fixture
notes over content/notes, and the repo's own content/notes is excluded.
"""
import json
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REAL_INDEX = ROOT / "content" / "notes" / "_index.md"

PAST_ONE = ("2026-01-05T09:30:00-06:00", "First note, with a 5 < 6 comparison and \"quotes\".\n\n"
            "A second paragraph links https://example.com/first for the curious.\n")
PAST_TWO = ("2026-02-10T18:45:00-06:00", "Second note, newer than the first, with [a relative link](/fa/archive/).\n")
FUTURE = ("2099-06-01T12:00:00-05:00", "A note from the far future.\n")


def write_notes(dest, notes):
    """Write fixture notes (slug -> (date, body)) and the section's own _index.md into dest."""
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    shutil.copy(REAL_INDEX, dest / "_index.md")
    for slug, (date, body) in notes.items():
        (dest / f"{slug}.md").write_text(f"---\ndate: {date}\n---\n{body}")
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


if __name__ == "__main__":
    unittest.main()
