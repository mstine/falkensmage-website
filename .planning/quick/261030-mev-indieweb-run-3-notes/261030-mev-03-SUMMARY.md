---
phase: quick-261030-mev
plan: 03
subsystem: site
tags: [indieweb, syndication, bluesky, atproto, github-actions, webmentions, testing]
requires:
  - quick-261030-mev-02 (state protocol, Mastodon posting, record-before-next-post)
provides:
  - Bluesky posting on the AT Protocol with a note-derived TID record key (post_bluesky, tid)
  - find_urls, facets (link and tag, UTF-8 byte offsets), fit and mastodon_length
  - .github/workflows/notes.yml, the 15-minute check, syndicate, rebuild clock
  - Deploy gate: validate-notes.sh and tests/test-notes.py run in hugo.yml before anything deploys
  - Outbound Webmentions for recent notes, with u-syndication anchors skipped
affects:
  - scripts/syndicate-notes.py
  - scripts/send-webmentions.py
  - tests/test-notes.py
  - tests/test-send-webmentions.py
  - .github/workflows/notes.yml
  - .github/workflows/hugo.yml
tech-stack:
  added: []
  patterns:
    - rkey derived from the note (sha256 of path into a real TID), so a second createRecord on it cannot make a second post
    - getRecord before every createRecord; createRecord only after a clean RecordNotFound
    - a failed login cached for the run, so a broken password is tried once
    - workflow properties pinned by an indentation-based reader, because the suite runs under -I -S with no YAML parser
key-files:
  created:
    - .github/workflows/notes.yml
  modified:
    - scripts/syndicate-notes.py
    - scripts/send-webmentions.py
    - tests/test-notes.py
    - tests/test-send-webmentions.py
    - .github/workflows/hugo.yml
decisions:
  - Bluesky length is counted in code points (conservative; len() can only overcount a grapheme count), Mastodon counts each link as 23
  - A hard cut never ends inside a link (the link is dropped whole) and a tag split by it gets no facet
  - notes.yml has its own concurrency group, not pages, because it waits on a run that needs pages
  - The old essay no longer ends send-webmentions early; notes are processed either way
metrics:
  tasks: 3
  completed: 2026-10-30
status: complete
actuals:
  tokens: 18400
  tasks: 3
  commits: 3
plan_head_before: 24cd8fa7f46ffcc6828f8d08fd0d7b0506a3f5ce
plan_head_after: 21f1c627e8a143971187b34bdfc3bc163df7725d
---

# Phase quick-261030-mev Plan 03: Both networks, on a clock Summary

A due note now goes to Mastodon and Bluesky directly (no Buffer anywhere), whole if it fits and cut at a word boundary with a link back if not, with exact link and hashtag facets on Bluesky, driven by `notes.yml` every 15 minutes, and recent notes send Webmentions. Nothing was pushed, no real API was called, and no real note exists.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Tracer: a note reaches a stub Bluesky beside Mastodon, with exact facets and a key that cannot post twice | ac51607 |
| 2 | Any note length goes out correctly on both networks | d5877bd |
| 3 | On a clock: notes.yml, the deploy gate, and Webmentions from notes | 21f1c62 |

Tracer gate: `<verify>` is automated-only, so it was re-run end to end (`test-notes.py` OK, `check` reports nothing due) before Tasks 2 and 3 expanded on it.

## What was built

- **Bluesky.** `post_bluesky` makes one lazy session per run (handle plus app password, the returned `did` compared with the D-08 constant, the failure cached so a broken login is tried once). Each attempt asks `getRecord` first: a 200 adopts that post's URI, a 400 `RecordNotFound` lets `createRecord` run, anything else posts nothing. 5xx, 429 and connection errors retry, and the retry asks `getRecord` again before creating. The response URI must end with the rkey. The record holds `$type`, `text`, `createdAt` (milliseconds, Z), `langs: ["en"]` and `facets` when there are any.
- **`tid(note)`.** First 8 bytes of sha256 of the note path give the sub-second microseconds and the 10-bit clock id; the note's own second fills the rest. `/notes/2026-11-01-0900/` at 09:00 -05:00 gives `3mzaxt2cwok3b`, as planned; every key fullmatches the TID regex, decodes to the note's second, and has a zero top bit.
- **Facets.** `find_urls` ports the reference detection (start, whitespace or `(` before `https?://\S+`, one trailing `[.,;:!?]`, then `)` when the link has no `(`). `facets` adds `#tag` from whitespace-or-start, strips trailing Unicode punctuation by category, skips empty, digit-or-punctuation-only and over-64 tags, and converts to UTF-8 byte offsets. A `#frag` inside a link and `x#nope` get no tag facet.
- **Length.** `fit` returns the text at the limit unchanged; one over, it cuts at the longest word end that leaves room for `… <note url>`. Bluesky counts code points (decision recorded in the docstring), Mastodon counts every link as 23. `DRY_RUN` logs each network's count and whole-or-cut.
- **`notes.yml`.** `schedule` at minutes 7, 22, 37, 52 and `workflow_dispatch`, nothing else. Top-level `permissions: {}`. Concurrency group `notes-syndication`, not `pages`. `check` (contents read, actions write) runs `check` and dispatches `hugo.yml` only when a page is not live. `syndicate` (contents write, 30 minutes) holds both secrets in one step's env. `rebuild` (actions write) dispatches once after any recording run, including a partial one. Every checkout is `ref: main`; no expression is interpolated into a `run:`; the only action is `actions/checkout`.
- **Deploy gate.** `hugo.yml` runs `bash tests/validate-notes.sh` directly after the FA validation and `tests/test-notes.py` in "Run Python test suites"; the header says `notes.yml` dispatches it; the webmentions step is renamed. Nothing else changed: no flag on `hugo`, top-level `contents: read` stays.
- **Webmentions from notes.** `NOTES_FEED`, `recent_notes(xml, now)` (in-window items, oldest first), u-syndication anchors skipped in `_EntryLinks`, and `main` no longer returns on a `skip-old` essay: it reads the notes feed (exit non-zero if our own feed fails, an empty feed is fine) and sends per recent note against the same state file.

## Verification

- `python3 -I -S -B tests/test-notes.py`: 178 OK (111 after plan 02; 67 new, and the guard still armed).
- `rm -rf public && hugo --minify`, then `validate-fa.sh` 13/0 and `validate-notes.sh` 6/0.
- `test-send-webmentions.py` 46 OK (was 36), `test-pull-webmentions.py` 75 OK, `test-send-fa-email.py` 6 OK.
- Baselines unchanged: validate-phase-06 32/0, validate-phase-02 16/2, validate-phase-03 31/8.
- Both workflow files parse with PyYAML; the parsed `notes.yml` shows the expected triggers, permissions, `needs` and `if` conditions.
- `python3 scripts/syndicate-notes.py check` on the real tree: "nothing due", exit 0, no network.
- Shipping state: `content/notes/` holds only `_index.md`; `data/syndication.json` holds an empty `notes` object.
- `scripts/send-fa-email.py` untouched (empty diff against 24cd8fa). `git status` clean after the mutation runs; no `__pycache__`.
- Nothing pushed, no real Mastodon or Bluesky call. The test stub speaks createSession, getRecord and createRecord like a PDS (client-supplied key validated as a TID, repeat createRecord refused, bearer token checked), and the socket guard plus patched `BLUESKY` mean a forgotten stub fails closed.

## Mutation proofs (applied one at a time, full suite run, file restored)

| # | Mutation | Result | Tests that went red |
|---|---|---|---|
| 1 | Widen the Bluesky limit to 3000 | red, 5 failures 1 error | 300/301-character fit, ZWJ truncation, 510-char Mastodon-vs-Bluesky, truncated-post facet, hard-cut tag, dry-run counts |
| 2 | Count code points as bytes in `facets` | red, 1 failure 1 error | emoji-before-link byte offsets, truncated-post link facet |
| 3 | Skip the getRecord check | red, 7 failures | lost-response adoption, lost-record adoption, getRecord 400 and 500 send no create, Mastodon-ok-Bluesky-500 retry, request-path set, tracer |
| 4 | Random rkey | red, 6 failures 5 errors | known TID value, determinism, same key across runs, lost-response adoption, tracer |
| 5 | Drop `ref: main` from one checkout | red, 1 failure | WorkflowConfig every-checkout-on-main |
| 6 | Put `notes.yml` in the `pages` group | red, 1 failure | WorkflowConfig own-concurrency-group |
| 7 | Add `contents: write` to the check job | red, 2 failures | WorkflowConfig exactly-one-job and per-job grants |
| 8 | Stop skipping u-syndication anchors in the sender | red, 2 failures (`test-send-webmentions.py`) | notes' own copies not fetched, mixed class tokens skipped |

## How to write a note

A file `content/notes/SLUG.md` (`hugo new content notes/SLUG.md` writes one that passes):

```
---
date: 2026-11-01T09:00:00-05:00
---
The text of the note.
```

The date needs an explicit offset or Z; `draft: true` holds it; the filename is lowercase letters, digits and hyphens. Commit to main. Within roughly 7 to 25 minutes after the date (the 15-minute cron plus GitHub's schedule delay) `notes.yml` deploys the page if it is not live, posts to both networks, records each post, and deploys once more so the u-syndication links show. A note more than 7 days old and never syndicated is not posted (it warns). Tags (`#tag`) and bare `https://` links in the text become Bluesky facets.

## The 60-day schedule limit

GitHub disables a public repository's scheduled workflows after 60 days with no repository activity. That would silently stop both syndication and the nightly rebuild. Feral Architecture commits land far more often, so this is a comment in `notes.yml` and this line, not a mechanism. If the site ever goes quiet for two months, re-enable the schedule in the Actions tab.

## What the live check must confirm (the orchestrator's, with Matt's approval)

Nothing here was run against a real API. The stub encodes assumptions the live check has to confirm:

1. `createSession` through `bsky.social` accepts `falkensmage.com` plus the app password and returns `did:plc:hrfsenvxai7pczill6ryqnky`.
2. `getRecord` for an unused rkey answers HTTP 400 with error `RecordNotFound` through the `bsky.social` entryway (the stub and the code assume 400; if it is a 404 the script fails closed and posts nothing, which is safe but red).
3. `createRecord` accepts the client-supplied TID rkey for `app.bsky.feed.post`, returns a `uri` ending in it, and the post renders with working link and tag facets at `https://bsky.app/profile/falkensmage.com/post/<rkey>`.
4. The Mastodon token's scope allows `POST /api/v1/statuses` (write:statuses) and the Idempotency-Key is honored.
5. A `gh workflow run hugo.yml` from a `GITHUB_TOKEN` with `actions: write` starts a `hugo.yml` run (the file is on main, and the documented exception for workflow_dispatch holds).
6. The `syndicate` job's `GITHUB_TOKEN` push to main succeeds. If main has branch protection that blocks the bot, the state push fails after the post, the run goes red, and the `::error` line prints the URL to hand-commit. Confirm main accepts it.
7. `tests/test-notes.py` passes inside the `hugo.yml` build job (it needs `hugo` and `git` on the runner, both present there; about a minute).
8. Both secrets, `MASTODON_ACCESS_TOKEN` and `BLUESKY_APP_PASSWORD`, exist on the repo.

## For Matt: the Buttondown interaction

A note-driven deploy is a `workflow_dispatch` with no inputs, so `send_email` is false and the `email` job mails no subscriber. `send-fa-email.py` still runs against the newest essay, not the note: older than 24 hours is `skip-old`, any non-deleted email with that subject is `skip-duplicate`, otherwise it creates a draft. So a note-driven deploy makes at most one Buttondown draft, only for an essay under 24 hours old with no email yet, and never repeats. That draft counts as an existing email, so a later `send_email=true` dispatch for the same essay is `skip-duplicate` and sends nothing. This already happens today with a push or the nightly rebuild; note deploys widen it a little: an essay dated before its release dispatch, with a note deploy landing in the gap, gets a draft and then no send.

The essay-email draft hazard is known and already queued as its own fix, so `scripts/send-fa-email.py` is deliberately unchanged here.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Existing plan 01/02 tests assumed Mastodon was the only registered poster**
- **Found during:** Task 1
- **Issue:** Registering `bluesky` in `POSTERS` made every earlier `post` test try Bluesky with no stub, changing exit codes and recorded state; `DueParity` expected `["mastodon"]` as the pending platform list.
- **Fix:** `SyndicationCase` gained a `NETWORKS` class attribute that filters `POSTERS` per test. `PostCase`, `Window` and `LivePage` stay Mastodon-only (the protocol they were written against), `Tracer` and the new Bluesky cases use both. `DueParity` now records both platforms for the recorded note and expects both for a due one. `Stub.posts()` now means Mastodon status POSTs only; `sessions()`, `creates()` and `getrecords()` cover Bluesky. `token()` sets both fake secrets, and `assertNoSecrets` checks the token, the password and the session token never reach output.
- **Files modified:** tests/test-notes.py
- **Commit:** ac51607

**2. [Rule 2 - Missing critical functionality] A hard cut must not leave half a link or a half-tag**
- **Found during:** Task 2
- **Issue:** The plan says a truncated post never ends inside a URL and a tag cut off by truncation has no facet, but a single word longer than the room (a long link, or a long hashtag) is cut mid-word, which would leave a broken link or a facet on a different tag.
- **Fix:** When the hard cut would land inside a link, the link is dropped whole (a note that is one huge link posts as just the link back); when it splits a tag, that tag's facet is removed. Both tested.
- **Files modified:** scripts/syndicate-notes.py, tests/test-notes.py
- **Commit:** d5877bd

### Other notes

- The per-plan commit ledger could not be written (compound Bash calls naming git are refused by the worktree guard, as in plans 01 and 02), so `plan_head_before` is the known base `24cd8fa` and `commits` is measured with `git rev-list --count` from it.
- `main` in the sender still exits at once if the essay page never gains an h-entry (existing behavior), which also skips that run's notes. It is loud and retried by the next deploy, so it was left as is.
- The record key is derived from the note's path and date. If a note's date is edited after a Bluesky post whose record was also lost, the new date is a new key. The state file is what normally prevents that; noted in the script's docstring.
- `test-send-webmentions.py` prints a `ResourceWarning` for an unclosed socket at a `addCleanup` line. I did not investigate whether it predates this plan.
- STATE.md and ROADMAP.md were not touched, per the run instructions.

## Known Stubs

None. `POSTERS` now holds both networks.

## Threat Flags

None beyond the plan's register. T-mev-11 (permissions, secrets in one job, no push or PR trigger) is pinned by `WorkflowConfig`. T-mev-14 (wrong account) is the DID check, tested. T-mev-15 (rate limits) is the lazy session and cached login failure, tested. T-mev-17 (double post) is the deterministic key plus getRecord, tested with a lost response, a lost record and a refused repeat. T-mev-18 (secrets) is covered by tests that the password and session token appear only in the session body and the Authorization header and never in output.

## Self-Check: PASSED

- Created file exists: .github/workflows/notes.yml.
- Commits ac51607, d5877bd, 21f1c62 are ancestors of HEAD (21f1c627e8a143971187b34bdfc3bc163df7725d).
