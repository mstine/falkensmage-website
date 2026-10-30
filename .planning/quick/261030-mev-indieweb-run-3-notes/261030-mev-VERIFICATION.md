---
phase: quick-261030-mev
verified: 2026-10-30T23:10:00Z
status: human_needed
score: 22/22 offline-provable must-haves verified
covered_files:
  - .github/workflows/hugo.yml
  - .github/workflows/notes.yml
  - .planning/quick/261030-mev-indieweb-run-3-notes/261030-mev-01-PLAN.md
  - .planning/quick/261030-mev-indieweb-run-3-notes/261030-mev-01-SUMMARY.md
  - .planning/quick/261030-mev-indieweb-run-3-notes/261030-mev-02-PLAN.md
  - .planning/quick/261030-mev-indieweb-run-3-notes/261030-mev-02-SUMMARY.md
  - .planning/quick/261030-mev-indieweb-run-3-notes/261030-mev-03-PLAN.md
  - .planning/quick/261030-mev-indieweb-run-3-notes/261030-mev-03-SUMMARY.md
  - data/syndication.json
  - scripts/pull-webmentions.py
  - scripts/send-webmentions.py
  - scripts/syndicate-notes.py
  - tests/test-notes.py
  - tests/validate-fa.sh
  - tests/validate-notes.sh
  - themes/arcaeon/layouts/notes/list.html
  - themes/arcaeon/layouts/notes/list.rss.xml
  - themes/arcaeon/layouts/notes/single.html
  - themes/arcaeon/layouts/partials/notes/entry.html
covered_digest: "v3:sha256:97f58ea9b684371a9306353b6a6e5e2df6bd214fb6f0f7f05f942e8e1d626f00"
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Bluesky createSession through bsky.social with handle falkensmage.com and the app password"
    expected: "Succeeds and returns did:plc:hrfsenvxai7pczill6ryqnky (the script compares the returned did and aborts on mismatch)"
    why_human: "Needs the real Bluesky API and a real secret. The stub encodes this assumption; D-14 forbids calling it."
  - test: "getRecord for an unused rkey through the bsky.social entryway"
    expected: "HTTP 400 with error RecordNotFound. The script fails closed on anything else (posts nothing, run goes red), so a 404 would be safe but red."
    why_human: "Real PDS response code. Stub and code both assume 400."
  - test: "createRecord with a client-supplied TID rkey for app.bsky.feed.post"
    expected: "Accepted; returned uri ends in the rkey; post renders on https://bsky.app/profile/falkensmage.com/post/<rkey> with working link and hashtag facets"
    why_human: "Real PDS rkey validation and facet rendering."
  - test: "Mastodon POST /api/v1/statuses with MASTODON_ACCESS_TOKEN"
    expected: "write:statuses scope accepted, visibility=public honored, Idempotency-Key honored, returned url under https://mastodon.social/@falkensmage/"
    why_human: "Real token scope and real instance behavior."
  - test: "gh workflow run hugo.yml from notes.yml's GITHUB_TOKEN (actions: write)"
    expected: "Starts a hugo.yml run (documented workflow_dispatch exception)"
    why_human: "Only provable on GitHub Actions."
  - test: "syndicate job's GITHUB_TOKEN push of the state commit to main"
    expected: "Accepted. If main has branch protection that blocks the bot, the post happens, the push fails, the run goes red and prints the URL to hand-commit."
    why_human: "Depends on live branch protection and repo settings."
  - test: "tests/test-notes.py and validate-notes.sh inside the hugo.yml build job"
    expected: "Pass on the runner (needs hugo and git, about a minute)"
    why_human: "Only provable on the runner; they pass locally."
  - test: "Repo secrets MASTODON_ACCESS_TOKEN and BLUESKY_APP_PASSWORD exist"
    expected: "Both present under the repo's Actions secrets"
    why_human: "Cannot be read from the checkout."
  - test: "One real end-to-end note, with Matt's approval"
    expected: "A dated note on main deploys, posts to both networks within about 7 to 25 minutes, records both URLs, and the page shows both u-syndication links after the rebuild"
    why_human: "D-13/D-14: deliberately not done in this task."
---

# Quick 261030-mev: IndieWeb run 3, Notes Verification Report

**Task goal:** A /notes/ section as the primary home for short-form writing, syndicated directly to Mastodon and Bluesky, shipped with no real note and no real post.
**Verified:** 2026-10-30
**Status:** human_needed
**Re-verification:** No, initial verification

Everything provable without the live services is verified from the code and from tests I ran myself. What remains is the set of assumptions the stubs encode about real Mastodon, real Bluesky and real GitHub Actions. Those are listed above and are the only open items. No gaps found.

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Dated, title-less Markdown file renders as an h-entry, no entry-level p-name | VERIFIED | Scratch build (temp content mount, HTTP denied): `<article class="h-entry note">` with `e-content`, `u-url`, `dt-published`, nested `p-author h-card`. The only `p-name` is inside the author h-card. |
| 2 | /notes/ is an h-feed newest first, /notes/index.xml carries the same notes, Notes nav link appears once a note exists | VERIFIED | Scratch build with one published note: `div.h-feed` holding the entry, RSS `<item>` with absolute link/guid/pubDate and no title, nav `<a href=/notes/>Notes</a>`, head `rel=alternate` and `rel=feed`. |
| 3 | With no notes: clean build, short empty state, nothing links to /notes/ or advertises its feed | VERIFIED | Real tree `hugo --minify`: builds clean. `/notes/` shows "Nothing here yet." No other HTML page contains `/notes/`; `notes/index.xml` appears only in itself. Home nav has no Notes link. |
| 4 | Future-dated note has no page, index entry or feed item until due | VERIFIED | Scratch build with a 2099 note beside a past note: only `past-one/` built, "future" absent from index and feed. `hugo.yml` passes no build-future flag. |
| 5 | Mentions render on note pages outside the h-entry, validate-fa.sh compares them to data | VERIFIED | `single.html` calls `fa/mentions.html` after the closing article tag. `validate-fa.sh` 13/0 and the webmention probe walks `public/notes/*/index.html`. Mutation tests in test-notes.py cover it. |
| 6 | page_key returns /notes/SLUG/ for a note, None for /notes/ and /work/SLUG/ | VERIFIED | `test-pull-webmentions.py` 75 OK including the 8 PageKey tests. |
| 7 | validate-notes.sh and validate-fa.sh go red, naming the page, for every mutation in the list | VERIFIED | `ProbeMutations` (13 against validate-notes, 5 against validate-fa) are in the 178-test run, all pass. |
| 8 | Text posted is read from the live page's e-content after the page is confirmed live | VERIFIED | `page_text`/`live_text`/`wait_live` in `scripts/syndicate-notes.py`; PageText and LivePage test classes pass. |
| 9 | Mastodon post is explicit public with a note-only Idempotency-Key | VERIFIED | `post_mastodon` sets `visibility=public` and `Idempotency-Key: idempotency_key(note)`. My mutation (drop the header) turned Tracer and AtMostOnce red (3 errors). |
| 10 | Each platform's URL is committed and pushed before the next post; failed push stops the run | VERIFIED | `record()` does add/commit/push with rebase-retry and `fail()` on error; AtMostOnce tests (push-fails-stops-the-run, another-run-pushed-meanwhile) pass. |
| 11 | Missing or malformed data/syndication.json posts nothing and exits 1 | VERIFIED | MissingState, MalformedState, StateFile tests pass. |
| 12 | Post reads state from the tip of origin main at post time | VERIFIED | `git pull --rebase origin main` before load; stale-checkout and failed-pull tests pass. |
| 13 | Script's idea of due agrees with Hugo's | VERIFIED | DueParity builds with `--clock` and compares across offsets and the exact-instant edge; passes. |
| 14 | Check with nothing due exits 0 with no network call | VERIFIED | I ran `check` on the real tree with `connect`, `connect_ex` and `getaddrinfo` patched to abort: output "nothing due", exit 0, no abort. |
| 15 | Every syndicated note page shows u-syndication links; probe can fail | VERIFIED | Entry partial renders them from `hugo.Data.syndication` inside the h-entry; third probe check plus ProbeMutations (anchor removed, href changed, orphan anchor, etc.). |
| 16 | Bluesky posting is direct (no Buffer), with a note-derived TID rkey and getRecord-before-create | VERIFIED | No "buffer" string in the script, workflow or templates. `tid()` is sha256(path)+note second. My mutation (always take the create path) turned BlueskyPosting red (2 failures). BlueskyPosting/TidTests pass. |
| 17 | Fit whole, else word-boundary cut with link back; facets use UTF-8 byte offsets | VERIFIED | FitTests, FacetTests, LengthPosting pass within the 178. |
| 18 | Mastodon-ok / Bluesky-fail retries only Bluesky, without a deploy | VERIFIED | Covered by the partial-success tests in BlueskyPosting; `pending()` is per-platform. |
| 19 | notes.yml: schedule + dispatch only, `permissions: {}`, `contents: write` and both secrets in the one `syndicate` job, no push trigger, own concurrency group, every checkout `ref: main`, deploy dispatched only when a page is not live | VERIFIED | Read the file. WorkflowConfig tests pin each property and pass. |
| 20 | Notes suite and probe gate the deploy; external links in recent notes send Webmentions, u-syndication anchors skipped | VERIFIED | `hugo.yml` diff: `bash tests/validate-notes.sh` and `python3 -I -S -B tests/test-notes.py` added before the artifact upload. `test-send-webmentions.py` 46 OK. |
| 21 | Ships with no real note and no real post | VERIFIED | `content/notes/` holds only `_index.md`. `data/syndication.json` has `"notes": {}`. `git log` shows no note file ever added. Working tree clean. |
| 22 | No test or script touched a real Mastodon or Bluesky API | VERIFIED | I ran every suite with both secrets unset. The suites arm a BaseException socket guard, clear secrets and use a `file://` origin (GuardTests/BaseSetUp pass). My own scratch builds used `security.http urls = ["^$"]`. |

**Score:** 22/22 offline-provable truths verified. Live-service behavior is carried by `human_verification`.

### Commands I ran

| What | Result |
|------|--------|
| `hugo --minify` on the real tree (HTTP denied) | Clean, 110 pages |
| `tests/validate-notes.sh` | 6 passed, 0 failed |
| `tests/validate-fa.sh` | 13 passed, 0 failed |
| `python3 -I -S -B tests/test-notes.py` | 178 OK (78 s) |
| `tests/test-pull-webmentions.py` | 75 OK |
| `tests/test-send-webmentions.py` | 46 OK |
| `tests/test-send-fa-email.py` | 6 OK |
| `validate-phase-06 / 02 / 03` | all passed / 16 and 2 / 31 and 8, which matches the baselines the plan recorded as pre-existing |
| Independent mutations on `scripts/syndicate-notes.py` (restored, md5 confirmed) | Both went red |

### Required Artifacts

All present, substantive and wired: `scripts/syndicate-notes.py` (1158 lines), `data/syndication.json`, `.github/workflows/notes.yml`, `.github/workflows/hugo.yml` (gate), `scripts/send-webmentions.py` (`NOTES_FEED`), `tests/test-notes.py` (2532 lines), `tests/validate-notes.sh`, `themes/arcaeon/layouts/{notes/single,notes/list,notes/list.rss.xml,partials/notes/entry}`.

### Key Links

All WIRED: single.html and list.html to the one entry partial; nav guarded on `RegularPages`; notes.yml to `gh workflow run hugo.yml`; hugo.yml to `validate-notes.sh`; `syndication.json` to the entry partial via `hugo.Data`; sender to the notes feed.

### Anti-Patterns

No TBD, FIXME, XXX, TODO, HACK or PLACEHOLDER markers in the changed implementation files. No stubs.

### Observations (not blockers)

- `public/sitemap.xml` lists `/notes/` even while the section is empty. Nothing links to it and the page is a valid empty state, so this is consistent with "short empty state". Exclude it from the sitemap if you want it truly unadvertised.
- The `<title>` of a note page contains a newline before the site name in the source; browsers collapse it.
- `scripts/__pycache__/send-webmentions.cpython-310.pyc` dates from 15:00, is gitignored and predates the later work. Not from this task.
- `test-send-webmentions.py` prints a ResourceWarning the summary says it did not investigate. Tests pass.
- Per plan 03: GitHub disables scheduled workflows after 60 days of no repo activity. Documented, not mechanized.

### Requirements Coverage

The plans' IW3-* IDs (IW3-NOTE, IW3-INDEX, IW3-EMPTY, IW3-FUTURE, IW3-MENTIONS, IW3-GATE) map to truths 1 to 7 above and are satisfied. Decisions D-01 to D-14 each map to a verified item.

### Gaps Summary

None. The offline half of the goal is achieved and proven able to fail. Status is `human_needed` solely because the live Mastodon, Bluesky and GitHub Actions behavior cannot and must not be checked here.

---

_Verified: 2026-10-30_
_Verifier: Claude (gsd-verifier)_
