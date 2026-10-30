#!/usr/bin/env python3
"""syndicate-notes.py — send each due note to Mastodon, and record where it went.

    python3 scripts/syndicate-notes.py check    # is anything due? (no network when nothing is)
    python3 scripts/syndicate-notes.py post     # post what is due, record each success

Stdlib only, Python 3.10-compatible. `check` is the cheap half a schedule runs often: it does
nothing unless a note is due and not yet syndicated. `post` is the half that publishes. Neither
runs against anything real in tests (tests/test-notes.py arms a guard that raises on any
non-loopback connection).

The one rule: at most one post per note per platform
----------------------------------------------------
A public post cannot be taken back quietly, so whatever fails and whenever it fails, a note
goes to a platform once. Everything below serves that rule.

How to write a note
-------------------
A file content/notes/SLUG.md holding YAML front matter between --- lines and a body:

    ---
    date: 2026-10-30T09:30:00-05:00
    ---
    The text of the note.

The format is strict because this script reads the file itself, and a second opinion on the
date or the URL would drift from Hugo's. Keys are `date` (required, RFC 3339 with an explicit
offset or Z) and `draft` (optional, true or false), and nothing else. The filename stem is
lowercase letters, digits and hyphens, and is not `index`. Leaf bundles are refused. A bare
date, a date with no offset, TOML front matter and an empty body are refused too: Hugo reads
the first two as UTC without saying so. Anything else is a loud failure naming the file.
`hugo new content notes/SLUG.md` writes a file that passes.

Run order
---------
`post`:
  1. git pull --rebase origin main, so the state is the tip of main at post time, never the
     commit this run was created at. actions/checkout fixes its ref when a run is created; a
     run that queued behind another would otherwise read old state and post again.
  2. Load the notes and data/syndication.json. A missing or malformed state file posts nothing
     and exits 1: empty state would mean "post everything".
  3. Work out what is due itself, oldest first. It never trusts `check`.
  4. Per due note: wait for its page to be live, read the text from that page, then per
     platform not yet recorded: post, and commit and push the record before the next post.

The text that goes out is read from the live page's e-content. Hugo stays the only Markdown
parser (a second converter in Python would be a second, drifting opinion), and the same fetch
proves the page is live, so "live before posting" cannot be skipped. A [text](url) link
becomes `text (url)`; a bare URL stays bare.

The at-most-once protocol
-------------------------
 * Each success is committed and pushed before the next post, because a runner's disk is not
   durable. If the push fails after retries, the run stops at once: posting further with no
   way to record is the double post. The ::error line prints the note, platform and URL so
   the record can be committed by hand.
 * Mastodon gets an Idempotency-Key derived only from the note (sha256 of
   "falkensmage.com:mastodon:" plus the note's path), so a retry after a lost response, in the
   same run or the next, returns the first status instead of a second. Mastodon keeps keys
   "for up to 1 hour". The key holds nothing time-based.
 * A note dated more than 7 days ago (MAX_AGE) and not recorded is never posted: it is logged,
   gets a ::warning and exits 0. That bounds the damage of a bad revert, and it makes a
   backdated note a deliberate publish-here-only.

Residual risk, accepted: a Mastodon post succeeds, every push retry fails, and the next run is
more than an hour later, so the key has expired. Then that one note double-posts on Mastodon.
It needs GitHub's git service to fail at that exact moment and the schedule to then stall for
an hour, and the run has already gone red with the URL printed for hand-commit. Hardening it
would need a write-ahead commit per post or scraping one's own timeline back into text;
neither earns its place.

What each failure does
----------------------
    Nothing due                             state unchanged, exit 0, no network
    Due, page not live (check)              exit 0 with deploy=true
    Page never goes live / no e-content     nothing posted, exit 1
    Mastodon 5xx, 429, timeout (3 tries)    state unchanged, exit 1, retried with the same key
    401, 403, 422, any 3xx                  state unchanged, exit 1, no retry, no redirect followed
    Post succeeded, response lost           exit 1; the next run gets the same status by key
    Post succeeded, push fails              stop at once, exit 1, ::error prints the URL
    Rebase conflict on the state file       git rebase --abort, exit 1
    State file missing or malformed         nothing posted, exit 1
    Note malformed                          nothing posted, exit 1
    Secret absent                           that platform fails, exit 1 (a due note silently
                                            not going out is the failure)
    Note older than 7 days, not recorded    never posted, exit 0, ::warning

Env: MASTODON_ACCESS_TOKEN (sent as a Bearer header only), GITHUB_OUTPUT (pending, deploy and
recorded are written there when set), DRY_RUN=1 (fetch, compute and log sizes; no POST, no git).

Mastodon coverage (opt out explicitly, never by omission)
---------------------------------------------------------
In: POST /api/v1/statuses with `status`, `visibility=public`, `language=en`, a Bearer header
and an Idempotency-Key. Visibility is set explicitly, never left to the account default.
Out, on purpose: media_ids and poll fields (images are out of scope, polls were not requested);
in_reply_to_id, quoted_status_id and quote_approval_policy (a note is a standalone post);
sensitive and spoiler_text (a note has no field for them); scheduled_at (scheduling here must
follow the page going live, which native scheduling cannot); PUT, DELETE, history, source and
the favourite, reblog, bookmark, pin, mute, translate and context methods (post once, never
edit or engage; a correction is a human act); GET /api/v2/instance for limits (length rules
are constants); reading one's own timeline to detect a prior post (see the residual risk).

Logs carry slugs, platforms and counts, never a token and never note text.
"""
import collections
import datetime
import hashlib
import html.parser
import http.client
import json
import os
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NOTES = ROOT / "content" / "notes"
STATE = ROOT / "data" / "syndication.json"
SITE = "https://falkensmage.com"
MASTODON = "https://mastodon.social/api/v1/statuses"
MASTODON_POST_PREFIX = "https://mastodon.social/@falkensmage/"
UA = "falkensmage-note-syndicator (+https://falkensmage.com/)"
TIMEOUT = 20
TRIES = 3
WAIT = 5
LIVE_TRIES = 60       # a deploy takes 1 to 7.5 minutes: 60 tries at 15 seconds is 15 minutes
LIVE_WAIT = 15
PUSH_TRIES = 5
PUSH_WAIT = 10
GIT_TIMEOUT = 120
MAX_BYTES = 2 * 1024 * 1024
MAX_AGE = datetime.timedelta(days=7)
REMOTE = "origin"
BRANCH = "main"
PLATFORMS = ("mastodon", "bluesky")
GIT_ID = ["-c", "user.name=github-actions[bot]",
          "-c", "user.email=41898282+github-actions[bot]@users.noreply.github.com",
          "-c", "commit.gpgsign=false"]
TOKEN_RE = re.compile(r"[\x21-\x7e]+")
SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*")
DATE_RE = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:Z|[+-]\d\d:\d\d)")
PATH_RE = re.compile(r"/notes/[a-z0-9][a-z0-9-]*/")

Note = collections.namedtuple("Note", "slug path date draft")


class NoteError(Exception):
    """A note file does not follow the format. The message names the file."""


class StateError(Exception):
    """data/syndication.json is missing or malformed."""


class GitError(Exception):
    """The checkout could not be brought to the tip of main. Nothing was posted."""


class PostError(Exception):
    """A platform did not take the post. Safe to log: it never holds the token or note text."""


class RecordError(Exception):
    """A post succeeded and could not be made durable. Carries what a human needs to commit it."""

    def __init__(self, note, platform, url, why):
        super().__init__(why)
        self.note, self.platform, self.url, self.why = note, platform, url, why


# No redirect handler: an Authorization header must never follow a redirect, so any 3xx raises.
# No ProxyHandler: the token only ever goes to the host named in MASTODON. UnknownHandler is
# required, or an unknown scheme returns None silently.
OPENER = urllib.request.OpenerDirector()
for _h in (urllib.request.UnknownHandler(), urllib.request.HTTPDefaultErrorHandler(),
           urllib.request.HTTPErrorProcessor(), urllib.request.HTTPHandler(),
           urllib.request.HTTPSHandler()):
    OPENER.add_handler(_h)


def log(msg):
    print(f"syndicate-notes: {msg}", flush=True)


def utcnow():
    return datetime.datetime.now(datetime.timezone.utc)


def one_line(value, limit=300):
    """Single-line, control-free, capped text. Always used after a fixed prefix, so a server's
    text cannot start a line with `::`, which the runner would read as a workflow command."""
    s = "".join(" " if (c.isspace() or ord(c) < 32 or ord(c) == 127) else c for c in str(value))
    s = " ".join(s.split())
    return s if len(s) <= limit else s[:limit].rstrip() + "…"


def annotate(level, msg):
    print(f"::{level} title=Notes::{one_line(msg)}", flush=True)


def gh_output(**values):
    path = os.environ.get("GITHUB_OUTPUT")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as f:
        for key, value in values.items():
            f.write(f"{key}={value}\n")


def git(*args, ident=False):
    """`git -C ROOT ...` with an argument list, never a shell. Failure to run is a returncode 1."""
    cmd = ["git", "-C", str(ROOT)] + (GIT_ID if ident else []) + list(args)
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=GIT_TIMEOUT, env=env)
    except (OSError, subprocess.TimeoutExpired) as e:
        return subprocess.CompletedProcess(cmd, 1, "", type(e).__name__)


def rebase_in_progress():
    for name in ("rebase-merge", "rebase-apply"):
        r = git("rev-parse", "--git-path", name)
        if r.returncode == 0 and (ROOT / r.stdout.strip()).exists():
            return True
    return False


def pull_main():
    """Bring the checkout to the tip of main. `post` does this before it reads state: a run that
    queued behind another was created at an older commit and would otherwise read stale state."""
    r = git("pull", "--rebase", REMOTE, BRANCH, ident=True)
    if r.returncode != 0:
        if rebase_in_progress():
            git("rebase", "--abort")
        raise GitError(f"could not pull {REMOTE} {BRANCH}: {one_line(r.stderr, 160)}")


# --- the note format --------------------------------------------------------------------

def read_note(path):
    """One note file as a Note(slug, path, date, draft), or NoteError naming the file."""
    path = Path(path)

    def bad(why):
        raise NoteError(f"{path.name}: {why}")

    if path.suffix != ".md":
        bad("not a .md file")
    slug = path.stem
    if not SLUG_RE.fullmatch(slug):
        bad("the filename must be lowercase letters, digits and hyphens, starting with a letter "
            "or digit (Hugo lowercases the URL, so anything else would drift)")
    if slug == "index":
        bad("the filename cannot be index")
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        bad(f"unreadable ({type(e).__name__})")
    lines = text.replace("\r\n", "\n").split("\n")
    if lines[0] != "---":
        bad("front matter must open with a --- line (YAML only; TOML is refused)")
    try:
        end = lines.index("---", 1)
    except ValueError:
        bad("front matter has no closing --- line")
    fields = {}
    for line in lines[1:end]:
        found = re.fullmatch(r"([a-z]+): *(.*?) *", line)
        if not found:
            bad("a front matter line is not 'key: value'")
        key, value = found.groups()
        if key not in ("date", "draft"):
            bad(f"unknown front matter key {key!r} (only date and draft are allowed)")
        if key in fields:
            bad(f"front matter key {key!r} appears twice")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        fields[key] = value
    if "date" not in fields:
        bad("date is required")
    if not DATE_RE.fullmatch(fields["date"]):
        bad("date must be RFC 3339 with an explicit offset or Z, like 2026-01-05T09:30:00-06:00")
    raw = fields["date"]
    try:
        date = datetime.datetime.fromisoformat(raw[:-1] + "+00:00" if raw.endswith("Z") else raw)
    except ValueError:
        bad("date is not a real date")
    draft = fields.get("draft", "false")
    if draft not in ("true", "false"):
        bad("draft must be true or false")
    if not "\n".join(lines[end + 1:]).strip():
        bad("the body is empty")
    return Note(slug, f"/notes/{slug}/", date, draft == "true")


def load_notes(directory):
    """Every note in the directory, oldest first. `_index.md` and dotfiles are skipped; a
    subdirectory (a leaf bundle) is refused."""
    directory = Path(directory)
    try:
        entries = sorted(directory.iterdir())
    except OSError:
        raise NoteError(f"{directory.name}: the notes directory is unreadable") from None
    notes = []
    for entry in entries:
        if entry.name == "_index.md" or entry.name.startswith("."):
            continue
        if entry.is_dir():
            raise NoteError(f"{entry.name}: subdirectories (leaf bundles) are not supported")
        notes.append(read_note(entry))
    return sorted(notes, key=lambda n: (n.date, n.slug))


# --- the state file ---------------------------------------------------------------------

def load_state(path):
    """The whole state document. A missing or malformed file raises StateError and is never
    read as "nothing recorded yet": empty state would mean post everything."""
    path = Path(path)

    def bad(why):
        raise StateError(f"{path.name}: {why}")

    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except FileNotFoundError:
        bad("is missing (it is committed to the repo; restore it, do not recreate it empty)")
    except (OSError, ValueError, RecursionError):
        bad("is not valid JSON")
    if not isinstance(doc, dict) or not isinstance(doc.get("notes"), dict):
        bad("has no notes object")
    for key, platforms in doc["notes"].items():
        if not PATH_RE.fullmatch(key):
            bad("a notes key is not a /notes/SLUG/ path")
        if not isinstance(platforms, dict):
            bad("a note's record is not an object")
        for platform, rec in platforms.items():
            if platform not in PLATFORMS:
                bad("a record names an unknown platform")
            if not isinstance(rec, dict) or not isinstance(rec.get("url"), str) or not rec["url"]:
                bad("a record has no string url")
    return doc


def write_state(path, doc):
    """Atomic: a temp file in the same directory, then os.replace. No directory is created: a
    state file whose directory is gone is a broken checkout, not a fresh start."""
    path = Path(path)
    body = json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True) + "\n"
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=".syndication-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(body)
        os.chmod(tmp, 0o644)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def pending(notes, state, now, platforms=None):
    """[(note, [platform, ...])], oldest first: non-draft notes whose date has passed and that
    still lack a record on a platform in `platforms` (default: every registered poster). Hugo
    publishes a note when its date is not after now, and so does this. A note older than MAX_AGE
    that lacks a record is logged, warned about and left out: that bounds what a bad revert of
    the state file can re-post, and makes a backdated note a deliberate publish-here-only."""
    wanted = list(platforms or POSTERS)
    out = []
    for note in sorted(notes, key=lambda n: (n.date, n.slug)):
        if note.draft or note.date > now:
            continue
        done = state["notes"].get(note.path, {})
        todo = [p for p in wanted if p not in done]
        if not todo:
            continue
        if now - note.date > MAX_AGE:
            log(f"{note.slug}: older than {MAX_AGE.days} days and not syndicated; never posted")
            annotate("warning", f"{note.path} is older than {MAX_AGE.days} days and was never "
                                f"syndicated to {', '.join(todo)}; it will not be posted")
            continue
        out.append((note, todo))
    return out


# --- reading the live page --------------------------------------------------------------

_VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source",
         "track", "wbr"}
_BLOCKS = {"p", "div", "section", "article", "header", "footer", "aside", "nav", "main",
           "figure", "figcaption", "blockquote", "pre", "h1", "h2", "h3", "h4", "h5", "h6", "hr",
           "table", "thead", "tbody", "tr", "td", "th", "dl", "dt", "dd", "details", "summary"}
_LISTS = {"ul", "ol"}
_SKIP = {"script", "style", "template", "noscript"}


def _collapse(parts):
    """Join text parts and collapse HTML whitespace per line; \\0 marks a <br>."""
    lines = [re.sub(r"[ \t\r\n\f]+", " ", line).strip(" ") for line in "".join(parts).split("\0")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


class _Extract(html.parser.HTMLParser):
    """The text of the first h-entry's first e-content. The minifier drops optional end tags
    (</p>, </li>), so a block start closes the previous block instead of relying on its end."""

    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base = base
        self.entry = None       # [tag, depth] inside the h-entry
        self.content = None     # [tag, depth] inside e-content
        self.found = False
        self.done = False
        self.blocks = []
        self.items = []
        self.cur = []
        self.list_depth = 0
        self.in_li = False
        self.href = None
        self.a_start = 0
        self.skip = 0

    # structure
    def handle_starttag(self, tag, attrs):
        if self.done:
            return
        a = {}
        for k, v in attrs:
            a.setdefault(k.lower(), v or "")
        toks = a.get("class", "").split()
        if self.entry is None:
            if "h-entry" in toks and tag not in _VOID:
                self.entry = [tag, 1]
            return
        if tag == self.entry[0] and tag not in _VOID:
            self.entry[1] += 1
        if self.content is None:
            if "e-content" in toks and tag not in _VOID:
                self.content = [tag, 1]
                self.found = True
            return
        if tag == self.content[0] and tag not in _VOID:
            self.content[1] += 1
        self._start_inside(tag, a)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)

    def handle_endtag(self, tag):
        if self.done or self.entry is None:
            return
        if self.content is not None:
            if tag == self.content[0]:
                self.content[1] -= 1
                if self.content[1] == 0:
                    self._finish()
                    return
            self._end_inside(tag)
        if tag == self.entry[0]:
            self.entry[1] -= 1
            if self.entry[1] == 0:
                self.done = True

    def handle_data(self, data):
        if self.content is not None and not self.done and not self.skip:
            self.cur.append(data)

    # inside e-content
    def _start_inside(self, tag, a):
        if tag in _SKIP:
            self.skip += 1
        elif self.skip:
            return
        elif tag == "br":
            self.cur.append("\0")
        elif tag == "li":
            if self.in_li:
                self._close_li()
            self._flush()
            self.in_li = True
        elif tag in _LISTS:
            self._flush()
            self.list_depth += 1
        elif tag == "a":
            href = a.get("href", "").strip()
            self.href = self._resolve(href) if href else None
            self.a_start = len(self.cur)
        elif tag in _BLOCKS:
            self._flush()

    def _end_inside(self, tag):
        if tag in _SKIP:
            self.skip = max(0, self.skip - 1)
        elif self.skip:
            return
        elif tag == "li":
            if self.in_li:
                self._close_li()
        elif tag in _LISTS:
            if self.in_li:
                self._close_li()
            self._flush()
            self.list_depth = max(0, self.list_depth - 1)
            if self.list_depth == 0 and self.items:
                self.blocks.append("\n".join("- " + item for item in self.items))
                self.items = []
        elif tag == "a":
            self._close_a()
        elif tag in _BLOCKS:
            self._flush()

    def _resolve(self, href):
        try:
            full = urllib.parse.urljoin(self.base, href)
            parts = urllib.parse.urlsplit(full)
            ok = parts.scheme in ("http", "https") and bool(parts.hostname)
        except ValueError:
            return None
        return full if ok else None

    def _close_a(self):
        href, self.href = self.href, None
        if href is None:
            return
        label = " ".join(_collapse(self.cur[self.a_start:]).split())
        bare = lambda s: re.sub(r"^https?://", "", s).rstrip("/")
        out = href if (not label or bare(label) == bare(href)) else f"{label} ({href})"
        self.cur[self.a_start:] = [out]

    def _flush(self):
        text = _collapse(self.cur)
        self.cur = []
        if text:
            (self.items if self.list_depth > 0 else self.blocks).append(text)

    def _close_li(self):
        self._flush()
        self.in_li = False

    def _finish(self):
        if self.in_li:
            self._close_li()
        self._flush()
        if self.items:
            self.blocks.append("\n".join("- " + item for item in self.items))
            self.items = []
        self.done = True


def page_text(html_text, base):
    """The plain text of the first h-entry's e-content, or None when either is absent or the
    text is empty. Whitespace collapses per block; paragraphs and other blocks join with a blank
    line; list items join with a single newline and a '- ' prefix; <br> is a newline; an anchor
    with an http(s) href becomes `label (href)`, or just the href when the label is the href
    (with or without scheme and trailing slash); relative hrefs resolve against `base`; images
    are ignored."""
    parser = _Extract(base)
    parser.feed(html_text)
    parser.close()
    if not parser.found:
        return None
    parser._finish()
    text = "\n\n".join(parser.blocks)
    return text or None


def fetch(url):
    """The page's HTML if it answers 200, else None (not deployed yet, or unreachable)."""
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "text/html"})
    try:
        with OPENER.open(req, timeout=TIMEOUT) as r:
            if r.status != 200:
                return None
            body = r.read(MAX_BYTES + 1)
    except urllib.error.HTTPError as e:
        e.close()
        return None
    except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException):
        return None
    if len(body) > MAX_BYTES:
        return None
    return body.decode("utf-8", errors="replace")


def live_text(note):
    """The note's text from its live page, None if the page is not live. A live page with no
    e-content is a PostError: waiting longer will not fix it."""
    page = fetch(SITE + note.path)
    if page is None:
        return None
    text = page_text(page, SITE + note.path)
    if text is None:
        raise PostError(f"{note.path}: the live page has no h-entry e-content to post")
    return text


def wait_live(note, tries):
    """live_text, retried LIVE_WAIT apart up to `tries` times. None if it never went live."""
    for attempt in range(tries):
        text = live_text(note)
        if text is not None:
            return text
        if attempt < tries - 1:
            time.sleep(LIVE_WAIT)
    return None


# --- posting ----------------------------------------------------------------------------

def idempotency_key(note):
    """Derived only from the note, so a retry (this run or the next) reuses it. Nothing
    time-based, and not SITE, which tests patch."""
    return hashlib.sha256(f"falkensmage.com:mastodon:{note.path}".encode()).hexdigest()


def _reason(err):
    """': <error>' from a JSON error body, single-line and capped; '' if there is none."""
    try:
        doc = json.loads(err.read(4096))
        reason = one_line(doc.get("error"), 200) if isinstance(doc, dict) and doc.get("error") else ""
    except (ValueError, RecursionError, AttributeError, OSError, http.client.HTTPException):
        return ""
    return f": {reason}" if reason else ""


def post_mastodon(note, text):
    """POST the status. Returns {url, id, posted}. 5xx, 429 and connection errors are retried
    (TRIES, WAIT apart) with the same Idempotency-Key, so a response lost after Mastodon took the
    post returns the first status instead of making a second. Any other status raises at once:
    no retry, and no redirect is followed, so the Authorization header never leaves. Raises
    PostError on anything but a 200 with a string id and a url on the account's own prefix (a
    response about someone else's status is never recorded)."""
    token = os.environ.get("MASTODON_ACCESS_TOKEN", "").strip()
    if not token:
        raise PostError("MASTODON_ACCESS_TOKEN is not set")
    if not TOKEN_RE.fullmatch(token):
        raise PostError("MASTODON_ACCESS_TOKEN holds characters that cannot be sent in a header")
    data = urllib.parse.urlencode([("status", text), ("visibility", "public"),
                                   ("language", "en")]).encode()
    req = urllib.request.Request(MASTODON, data=data, method="POST", headers={
        "Authorization": f"Bearer {token}", "Idempotency-Key": idempotency_key(note),
        "User-Agent": UA, "Accept": "application/json",
        "Content-Type": "application/x-www-form-urlencoded"})
    why = "no attempt"
    for attempt in range(TRIES):
        try:
            with OPENER.open(req, timeout=TIMEOUT) as r:
                status, body = r.status, r.read(MAX_BYTES + 1)
            break
        except urllib.error.HTTPError as e:
            try:
                if e.code < 500 and e.code != 429:
                    raise PostError(f"mastodon: HTTP {e.code}{_reason(e)}") from None
                why = f"HTTP {e.code}"
            finally:
                e.close()
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as e:
            why = f"unreachable ({type(e).__name__})"
        if attempt < TRIES - 1:
            time.sleep(WAIT)
    else:
        raise PostError(f"mastodon: failed ({why}) after {TRIES} tries")
    if len(body) > MAX_BYTES:
        raise PostError("mastodon: the response was larger than the size cap")
    if status != 200:
        raise PostError(f"mastodon: HTTP {status}")
    try:
        doc = json.loads(body)
    except (ValueError, RecursionError):
        raise PostError("mastodon: the response was not valid JSON") from None
    if (not isinstance(doc, dict) or not isinstance(doc.get("id"), str)
            or not isinstance(doc.get("url"), str)
            or not doc["url"].startswith(MASTODON_POST_PREFIX)):
        raise PostError("mastodon: the response is not a status on this account")
    return {"url": doc["url"], "id": doc["id"],
            "posted": utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}


# plan 03 registers bluesky
POSTERS = {"mastodon": post_mastodon}


def record(state, note, platform, rec):
    """Make one success durable: update the document, write it atomically, commit it alone and
    push (on a rejection, pull --rebase and push again, PUSH_TRIES times), then tell the
    workflow. Raises RecordError, carrying what a human needs to commit it by hand, on any
    failure."""
    state["notes"].setdefault(note.path, {})[platform] = rec

    def fail(why):
        raise RecordError(note.path, platform, rec["url"], why)

    try:
        write_state(STATE, state)
    except OSError as e:
        fail(f"could not write the state file ({type(e).__name__})")
    rel = os.path.relpath(STATE, ROOT)
    if git("add", "--", rel).returncode != 0:
        fail("git add failed")
    msg = f"chore(notes): record {platform} syndication for {note.slug}"
    if git("commit", "-m", msg, "--", rel, ident=True).returncode != 0:
        fail("git commit failed")
    why = "git push failed"
    for attempt in range(PUSH_TRIES):
        if git("push", REMOTE, f"HEAD:{BRANCH}").returncode == 0:
            break
        pulled = git("pull", "--rebase", REMOTE, BRANCH, ident=True)
        if pulled.returncode != 0:
            if rebase_in_progress():
                git("rebase", "--abort")
                fail("the rebase conflicted on the state file and was aborted")
            why = "git push failed and the pull failed"
        else:
            # Someone else's commit may now sit under ours. Our in-memory document predates it,
            # and the next record writes from memory, so take the merged file as the truth.
            try:
                merged = load_state(STATE)
            except StateError:
                fail("the rebase left an unreadable state file")
            if platform not in merged["notes"].get(note.path, {}):
                fail("the rebase dropped the new record")
            state.clear()
            state.update(merged)
        if attempt < PUSH_TRIES - 1:
            time.sleep(PUSH_WAIT)
    else:
        fail(f"{why} after {PUSH_TRIES} tries")
    gh_output(recorded="true")


# --- commands ---------------------------------------------------------------------------

def cmd_check():
    try:
        notes = load_notes(NOTES)
        state = load_state(STATE)
    except (NoteError, StateError) as e:
        log(f"FAILED: {e}")
        annotate("error", e)
        return 1
    due = pending(notes, state, utcnow())
    if not due:
        log("nothing due")
        gh_output(pending="false", deploy="false")
        return 0
    live = all(fetch(SITE + note.path) is not None for note, _ in due)
    log(f"{len(due)} due, {'live' if live else 'not all live: a deploy is needed'}")
    gh_output(pending="true", deploy="false" if live else "true")
    return 0


def cmd_post():
    dry = os.environ.get("DRY_RUN") == "1"
    try:
        if not dry:
            pull_main()
        notes = load_notes(NOTES)
        state = load_state(STATE)
    except (GitError, NoteError, StateError) as e:
        log(f"FAILED: {e}")
        annotate("error", e)
        return 1
    failed = timed_out = False
    # Computed here, never trusted from `check`: the checkout may have moved since.
    for note, platforms in pending(notes, state, utcnow()):
        try:
            # After one page has timed out, later notes get a single try, so the job cannot
            # spend its whole timeout waiting on pages that are not coming.
            text = wait_live(note, 1 if timed_out else LIVE_TRIES)
        except PostError as e:
            log(f"FAILED: {e}")
            annotate("error", e)
            failed = True
            continue
        if text is None:
            timed_out = failed = True
            log(f"FAILED: {note.path} is not live")
            annotate("error", f"{note.path} never went live; nothing was posted")
            continue
        for platform in platforms:
            if platform in state["notes"].get(note.path, {}):
                continue  # a rebase brought in another run's record for it
            if dry:
                log(f"dry run: {note.slug} {platform}: would post {len(text)} characters")
                continue
            try:
                rec = POSTERS[platform](note, text)
            except PostError as e:
                log(f"FAILED: {note.slug} {platform}: {e}")
                annotate("error", f"{note.path} {platform}: {e}")
                failed = True
                continue
            try:
                record(state, note, platform, rec)
            except RecordError as e:
                # Posting further with no way to record is the double post: stop now.
                log(f"FAILED: {note.slug} {platform}: posted but not recorded ({e.why})")
                annotate("error", f"POSTED BUT NOT RECORDED: {e.note} {e.platform} {e.url} "
                                  f"({e.why}). Add it to data/syndication.json by hand.")
                return 1
            log(f"{note.slug} {platform}: posted and recorded")
    return 1 if failed else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else list(argv)
    if len(argv) != 1 or argv[0] not in ("check", "post"):
        print("usage: syndicate-notes.py check|post", file=sys.stderr)
        return 2
    return {"check": cmd_check, "post": cmd_post}[argv[0]]()


if __name__ == "__main__":
    sys.exit(main())
