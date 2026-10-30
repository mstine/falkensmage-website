#!/usr/bin/env bash
# validate-notes.sh — gate for the Notes section (/notes/).
# Run from project root after a build: hugo --minify && bash tests/validate-notes.sh
# Exit 0 = all checks pass. Exit 1 = one or more checks failed.
#
# A note missing its markup looks fine in a browser and silently stops every microformats
# consumer: Bridgy, webmention senders, readers. Class-level rot (an h-entry class dropped
# from a template, an entry-level p-name that turns the note into an article) is invisible
# by eye, so it gets a standing probe instead of trust. The probe is only worth having if it
# can fail: tests/test-notes.py breaks the output in each way a regression would and
# watches this script go red.
#
# The record of where each note was syndicated (data/syndication.json) is held to the built
# pages the same way: a dropped u-syndication link breaks backfeed with no visible sign, and a
# note that is due but has no page, or scheduled but already built, is invisible until a reader
# or a post finds it. The note format has one definition, scripts/syndicate-notes.py, which this
# probe loads through importlib rather than restating.
#
# html.parser, never grep: `hugo --minify` writes unquoted attributes and shortens
# entities. The python block prints PASS/FAIL lines and ends with DONE; a crash leaves DONE
# out, which is a red, not a blank.
#
# Overrides (the tests point them at temp builds): VALIDATE_NOTES_PUBLIC the build directory,
# VALIDATE_NOTES_DATA the directory holding syndication.json, VALIDATE_NOTES_CONTENT the notes
# directory, VALIDATE_NOTES_NOW an RFC 3339 instant that pins "now" (a build made with
# `hugo --clock` is judged at its own clock, not the wall clock).

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC="${VALIDATE_NOTES_PUBLIC:-$PROJECT_ROOT/public}"
DATA="${VALIDATE_NOTES_DATA:-$PROJECT_ROOT/data}"
CONTENT="${VALIDATE_NOTES_CONTENT:-$PROJECT_ROOT/content/notes}"
NOW="${VALIDATE_NOTES_NOW:-}"

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL + 1)); }

echo "Notes (/notes/)"

notes_out=$(python3 -I - "$PUBLIC" "$DATA" "$CONTENT" "$PROJECT_ROOT/scripts/syndicate-notes.py" "$NOW" <<'PY'
import datetime, glob, importlib.util, os, sys
from html.parser import HTMLParser

public, data_dir, content_dir, script, now_override = sys.argv[1:6]
out = []


def ok(text):
    out.append("PASS " + text)


def bad(text):
    out.append("FAIL " + text)


class Note(HTMLParser):
    """Reads every h-entry on a page, with the nested h-card tracked separately so its
    p-name is not read as the entry's."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.entries = 0
        self.entry = None         # [tag, depth] while inside the h-entry
        self.card = None          # [tag, depth] while inside the nested h-card
        self.econtent = None      # [tag, depth] while inside e-content
        self.econtent_text = ""
        self.entry_cls = set()    # classes at entry level, outside the h-card
        self.card_cls = set()     # classes inside the h-card
        self.author_card = False  # p-author and h-card on one element

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        toks = set(a.get("class", "").split())
        if self.entry is None:
            if "h-entry" in toks:
                self.entries += 1
                if self.entries == 1:
                    self.entry = [tag, 1]
            return
        if tag == self.entry[0]:
            self.entry[1] += 1
        if self.econtent is not None and tag == self.econtent[0]:
            self.econtent[1] += 1
        if self.card is not None:
            if tag == self.card[0]:
                self.card[1] += 1
            self.card_cls |= toks
        elif "h-card" in toks:
            self.card = [tag, 1]
            self.author_card = self.author_card or "p-author" in toks
        else:
            self.entry_cls |= toks
            if "e-content" in toks and self.econtent is None:
                self.econtent = [tag, 1]

    def handle_endtag(self, tag):
        if self.entry is None:
            return
        if self.econtent is not None and tag == self.econtent[0]:
            self.econtent[1] -= 1
            if self.econtent[1] == 0:
                self.econtent = None
        if self.card is not None and tag == self.card[0]:
            self.card[1] -= 1
            if self.card[1] == 0:
                self.card = None
        if tag == self.entry[0]:
            self.entry[1] -= 1
            if self.entry[1] == 0:
                self.entry = self.card = self.econtent = None

    def handle_data(self, data):
        if self.econtent is not None:
            self.econtent_text += data


def read(path):
    p = Note()
    p.feed(open(path, encoding="utf-8", errors="replace").read())
    p.close()
    return p


# 1. every note page carries a complete h-entry
notes = sorted(glob.glob(os.path.join(public, "notes", "*", "index.html")))
problems = []
for path in notes:
    where = "/" + os.path.relpath(os.path.dirname(path), public) + "/"
    pg = read(path)
    if pg.entries != 1:
        problems.append(f"{where} has {pg.entries} h-entry elements, expected 1")
        continue
    missing = [c for c in ("e-content", "dt-published", "u-url") if c not in pg.entry_cls]
    if "e-content" in pg.entry_cls and not pg.econtent_text.strip():
        missing.append("e-content text")
    if not pg.author_card:
        missing.append("p-author+h-card")
    missing += [f"h-card>{c}" for c in ("p-name", "u-url", "u-photo") if c not in pg.card_cls]
    if missing:
        problems.append(f"{where} missing: {', '.join(missing)}")
    if "p-name" in pg.entry_cls:
        problems.append(f"{where} has an entry-level p-name, which makes it an article, not a note")
for line in problems:
    bad("h-entry: " + line)
if not problems:
    ok(f"{len(notes)} notes carry complete h-entry markup")

published = {"/" + os.path.relpath(os.path.dirname(p), public) + "/" for p in notes}
n = len(published)


class Flat(HTMLParser):
    """Class counts, the primary nav's links, and the head's alternate and feed links."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.count = {}
        self.nav = []             # hrefs inside nav[aria-label=Primary]
        self._nav = 0
        self.rss_links = []       # <link rel=alternate type=application/rss+xml> hrefs
        self.feed_links = []      # <link rel=feed> hrefs

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        for tok in a.get("class", "").split():
            self.count[tok] = self.count.get(tok, 0) + 1
        if tag == "link":
            rel = a.get("rel", "").lower().split()
            if "alternate" in rel and a.get("type") == "application/rss+xml":
                self.rss_links.append(a.get("href", ""))
            if "feed" in rel:
                self.feed_links.append(a.get("href", ""))
        if tag == "nav" and a.get("aria-label") == "Primary":
            self._nav = 1
        elif self._nav:
            if tag == "nav":
                self._nav += 1
            if tag == "a":
                self.nav.append(a.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "nav" and self._nav:
            self._nav -= 1


def flat(path):
    f = Flat()
    f.feed(open(path, encoding="utf-8", errors="replace").read())
    f.close()
    return f


# 2. the /notes/ index and feed match the published notes
import xml.etree.ElementTree as ET
from urllib.parse import urlsplit

index_problems = []
index = os.path.join(public, "notes", "index.html")
if not os.path.isfile(index):
    index_problems.append("/notes/ has no index page")
else:
    f = flat(index)
    if f.count.get("h-feed", 0) != 1:
        index_problems.append(f"/notes/ has {f.count.get('h-feed', 0)} h-feed elements, expected 1")
    if f.count.get("h-entry", 0) != n:
        index_problems.append(f"/notes/ lists {f.count.get('h-entry', 0)} h-entry elements, expected {n}")
    empty = f.count.get("notes-empty", 0)
    if n == 0 and empty != 1:
        index_problems.append(f"/notes/ has {empty} notes-empty elements, expected 1 with no notes")
    if n > 0 and empty != 0:
        index_problems.append(f"/notes/ shows the empty state although {n} notes are published")
feed = os.path.join(public, "notes", "index.xml")
if not os.path.isfile(feed):
    index_problems.append("/notes/index.xml is missing")
else:
    try:
        items = ET.parse(feed).getroot().findall("./channel/item")
    except ET.ParseError:
        items = None
        index_problems.append("/notes/index.xml does not parse")
    if items is not None:
        want = min(n, 50)
        if len(items) != want:
            index_problems.append(f"/notes/index.xml has {len(items)} items, expected {want}")
        for item in items:
            link = (item.findtext("link") or "").strip()
            path = urlsplit(link).path
            if path not in published:
                index_problems.append(f"/notes/index.xml has an item linking to {path or '(no link)'}, which is not a published note")
for line in index_problems:
    bad("index: " + line)
if not index_problems:
    ok(f"the /notes/ index and feed match {n} published notes")

# 3. nothing links to an empty room: the nav and head agree with the published count
home = os.path.join(public, "index.html")
if not os.path.isfile(home):
    bad("nav: missing built home page")
else:
    f = flat(home)
    in_nav = "/notes/" in f.nav
    in_rss = any(urlsplit(h).path == "/notes/index.xml" for h in f.rss_links)
    in_feed = any(urlsplit(h).path == "/notes/" for h in f.feed_links)
    nav_problems = []
    if n == 0:
        if in_nav:
            nav_problems.append("the nav links to /notes/ although no note is published")
        if in_rss:
            nav_problems.append("the head advertises the notes feed although no note is published")
        if in_feed:
            nav_problems.append("the head carries rel=feed although no note is published")
    else:
        if not in_nav:
            nav_problems.append(f"the nav has no /notes/ link although {n} notes are published")
        if not in_rss:
            nav_problems.append("the head has no alternate link to /notes/index.xml")
        if not in_feed:
            nav_problems.append("the head has no rel=feed link to /notes/")
    for line in nav_problems:
        bad("nav: " + line)
    if not nav_problems:
        if n == 0:
            ok("nav Notes link hidden, no note published")
        else:
            ok(f"nav Notes link shown, {n} notes published")

# --- the record, the content files and the built pages, held against each other

spec = importlib.util.spec_from_file_location("syndicate_notes", script)
sn = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sn)

if now_override:
    now = datetime.datetime.fromisoformat(now_override.replace("Z", "+00:00"))
else:
    now = datetime.datetime.now(datetime.timezone.utc)
GRACE = datetime.timedelta(minutes=10)


class Syn(HTMLParser):
    """The u-syndication anchors inside the first h-entry: [(href, rel)]."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.anchors = []
        self.entry = None

    def handle_starttag(self, tag, attrs):
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        toks = a.get("class", "").split()
        if self.entry is False:
            return
        if self.entry is None:
            if "h-entry" in toks:
                self.entry = [tag, 1]
            return
        if tag == self.entry[0]:
            self.entry[1] += 1
        if tag == "a" and "u-syndication" in toks:
            self.anchors.append((a.get("href", ""), a.get("rel", "")))

    def handle_endtag(self, tag):
        if self.entry and tag == self.entry[0]:
            self.entry[1] -= 1
            if self.entry[1] == 0:
                self.entry = False


def syndication(path):
    p = Syn()
    p.feed(open(path, encoding="utf-8", errors="replace").read())
    p.close()
    return p.anchors


# 4. every note file follows the one format
try:
    note_files = sn.load_notes(content_dir)
    ok(f"{len(note_files)} note files follow the format")
except sn.NoteError as e:
    note_files = None
    bad(f"format: {e}")

# 5. built pages and dates agree: due means a page, scheduled means none. A note that came due
# in the last 10 minutes may simply not be deployed yet, which is a race and not a bug; a
# date after now was also after the build, so the future case has no race.
if note_files is not None:
    due_problems = []
    for note in note_files:
        has_page = note.path in published
        if note.draft or note.date > now:
            if has_page:
                due_problems.append(f"{note.path} is a draft or dated in the future but has a page")
        elif note.date <= now - GRACE and not has_page:
            due_problems.append(f"{note.path} came due more than 10 minutes ago but has no page")
    for line in due_problems:
        bad("due: " + line)
    if not due_problems:
        ok("every due note has a page and no scheduled note does")

# 6. every syndicated note shows exactly its recorded u-syndication links
HOSTS = {"mastodon": "mastodon.social", "bluesky": "bsky.app"}
try:
    state = sn.load_state(os.path.join(data_dir, "syndication.json"))
except sn.StateError as e:
    state = None
    bad(f"state: {e}")
if state is not None:
    syn_problems = []
    retired = 0
    for key, platforms in sorted(state["notes"].items()):
        for platform, rec in platforms.items():
            u = urlsplit(rec["url"])
            if u.scheme != "https" or u.hostname != HOSTS[platform] or u.username is not None:
                syn_problems.append(f"{key} {platform} url is not https on {HOSTS[platform]}")
    for key in sorted(published | set(state["notes"])):
        slug = key.strip("/").split("/")[-1]
        records = state["notes"].get(key, {})
        if not os.path.isfile(os.path.join(content_dir, slug + ".md")):
            if records:
                retired += 1  # a deliberately retired note: its record stays, its page is gone
            continue
        want = sorted(r["url"] for r in records.values())
        page = os.path.join(public, key.strip("/"), "index.html")
        if not os.path.isfile(page):
            if want:
                syn_problems.append(f"{key} is recorded as syndicated but has no page")
            continue
        anchors = syndication(page)
        got = sorted(href for href, _ in anchors)
        if got != want:
            syn_problems.append(f"{key} shows {len(got)} u-syndication links {got}, expected {len(want)} {want}")
        for href, rel in anchors:
            if "syndication" not in rel.split():
                syn_problems.append(f"{key} u-syndication link to {href} lacks rel=syndication")
    for line in syn_problems:
        bad("syndication: " + line)
    if not syn_problems:
        ok("every syndicated note shows its u-syndication links")
    if retired:
        out.append(f"INFO {retired} recorded notes have no content file and were skipped as retired")

print("\n".join(out))
print("DONE")
PY
)
notes_done=0
while IFS= read -r line; do
  case "$line" in
    "PASS "*) pass "${line#PASS }" ;;
    "FAIL "*) fail "${line#FAIL }" ;;
    "INFO "*) echo "  info  ${line#INFO }" ;;
    DONE) notes_done=1 ;;
  esac
done <<< "$notes_out"
[ "$notes_done" -eq 1 ] || fail "notes probe did not finish"

echo
echo "  $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
