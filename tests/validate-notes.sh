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
# html.parser, never grep: `hugo --minify` writes unquoted attributes and shortens
# entities. The python block prints PASS/FAIL lines and ends with DONE; a crash leaves DONE
# out, which is a red, not a blank.
#
# VALIDATE_NOTES_PUBLIC overrides the build directory (the tests point it at temp builds).

set -uo pipefail

PASS=0
FAIL=0
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PUBLIC="${VALIDATE_NOTES_PUBLIC:-$PROJECT_ROOT/public}"

pass() { echo "  PASS  $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL  $1"; FAIL=$((FAIL + 1)); }

echo "Notes (/notes/)"

notes_out=$(python3 -I - "$PUBLIC" <<'PY'
import glob, os, sys
from html.parser import HTMLParser

public = sys.argv[1]
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

print("\n".join(out))
print("DONE")
PY
)
notes_done=0
while IFS= read -r line; do
  case "$line" in
    "PASS "*) pass "${line#PASS }" ;;
    "FAIL "*) fail "${line#FAIL }" ;;
    DONE) notes_done=1 ;;
  esac
done <<< "$notes_out"
[ "$notes_done" -eq 1 ] || fail "notes probe did not finish"

echo
echo "  $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ]
