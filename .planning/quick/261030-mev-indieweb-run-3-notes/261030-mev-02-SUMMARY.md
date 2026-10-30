---
phase: quick-261030-mev
plan: 02
subsystem: site
tags: [indieweb, syndication, mastodon, posse, microformats, testing]
requires:
  - quick-261030-mev-01 (notes as h-entry pages, validate-notes.sh, test-notes.py)
provides:
  - scripts/syndicate-notes.py with check and post (stdlib only, Python 3.10-compatible)
  - data/syndication.json, the durable per-note per-platform record
  - u-syndication links rendered inside the note h-entry from that record
  - validate-notes.sh checks for note format, built-vs-due and u-syndication
  - test guards that make it structurally hard for a test to touch anything real
affects:
  - themes/arcaeon/layouts/partials/notes/entry.html
  - themes/arcaeon/assets/css/main.css
  - tests/validate-notes.sh
  - tests/test-notes.py
tech-stack:
  added: []
  patterns:
    - text posted is read from the live page's e-content, so Hugo stays the only Markdown parser
    - Idempotency-Key derived only from the note path
    - record committed and pushed before the next post, state reloaded after a rebase
    - three-layer test guard: BaseException socket guard, cleared secrets, sentinel ROOT plus file:// origin
key-files:
  created:
    - scripts/syndicate-notes.py
    - data/syndication.json
  modified:
    - themes/arcaeon/layouts/partials/notes/entry.html
    - themes/arcaeon/assets/css/main.css
    - tests/validate-notes.sh
    - tests/test-notes.py
decisions:
  - Per-platform host allow-list in the probe (mastodon.social for mastodon, bsky.app for bluesky), stricter than "either host for either platform"
  - pending() considers only registered POSTERS, so a note recorded on Mastodon is not "pending" while Bluesky is unregistered
  - After a successful rebase the in-memory state is replaced with the merged file, so a later record cannot erase another run's record
  - Dotfiles in content/notes are skipped by load_notes; any other non-.md file is refused
metrics:
  tasks: 3
  completed: 2026-10-30
status: complete
actuals:
  tokens: 28000
  tasks: 3
  commits: 4
plan_head_before: 29f13d035456ca95084bc1a35593dd0440d15b9d
plan_head_after: f267b174d1bbfacb68c63c596908613189bfad5b
---

# Phase quick-261030-mev Plan 02: The state protocol Summary

A due note's live page is read, posted to Mastodon with an explicit public visibility and a note-derived Idempotency-Key, and the returned URL is committed and pushed before anything else happens; the note's page then shows it as a u-syndication link. The at-most-once rule is proven against a loopback stub and a local bare origin, and a test cannot reach a real host, hold a real secret or push to the real origin.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Tracer: live page to stub Mastodon to pushed record to u-syndication link | 3866a67 |
| 2 | A retry cannot double-post: the at-most-once protocol under every failure | d5a8317 |
| 3 | The probe holds the record to the page, and proves it can fail | a7304d6 |
| 3 (fix) | Probe loads the script without writing a bytecode cache | f267b17 |

## What was built

- **Script.** `check` writes `pending` and `deploy` to GITHUB_OUTPUT and touches no network when nothing is due. `post` pulls main, loads notes and state (a missing or malformed state file exits 1 with nothing posted), computes pending itself, waits for each page, reads its e-content, posts, and records each success before the next post. Strict note format (RFC 3339 date with offset or Z, `draft` only, lowercase slug, no leaf bundles, no empty body). The docstring carries the format, run order, protocol, residual risk, failure table and the DP-11 Mastodon coverage list.
- **Record and render.** `data/syndication.json` is committed with an empty `notes` object. The entry partial renders `p.note__syndication` with `u-syndication` / `rel=syndication` anchors from `hugo.Data`, keyed by `.RelPermalink`, with plain `{{ .url }}` so html/template's URL filter applies.
- **Probe.** `validate-notes.sh` gained three checks with the exact pass lines from the plan, env overrides, and loads the script through importlib so the note format has one definition.
- **Test guards (D-14).** A socket guard raising a `BaseException` subclass on any non-loopback `connect`, `connect_ex` or `getaddrinfo`; a base `setUp` that clears both secrets, `GITHUB_OUTPUT` and `DRY_RUN` and isolates git config; a sentinel `ROOT`/`STATE`/`NOTES` under `/nonexistent/` and a `file://` origin assertion before any test body. The guards are themselves tested.

## Verification

- `python3 -I -S -B tests/test-notes.py`: 111 OK (was 36 after plan 01).
- Real tree after `rm -rf public && hugo --minify`: `validate-notes.sh` 6 passed, 0 failed; `validate-fa.sh` 13 passed, 0 failed.
- `test-pull-webmentions.py` 75 OK, `test-send-webmentions.py` 36 OK, `test-send-fa-email.py` 6 OK.
- `python3 scripts/syndicate-notes.py check` on the real tree: "nothing due", exit 0, no network.
- `content/notes/` holds only `_index.md`; `data/syndication.json` holds an empty `notes` object. No `__pycache__` left in `scripts/`. Nothing pushed, no real API called, no real note published.
- Hugo parity: a `--clock` build and `pending()` agree on seven notes straddling the instant in several offsets, including an exactly-equal note in both offset and Z form, a +14 and a -12 offset, and a past draft.

## Mutation proofs (Task 2, applied to scripts/syndicate-notes.py, suite run, file restored)

| Mutation | Result | Tests that went red |
|---|---|---|
| Drop the Idempotency-Key header | red, 3 errors | lost-response retry, key-across-runs, tracer |
| Key includes the current time | red, 2 failures | key-across-runs, tracer |
| `post` skips the pull before reading state | red, 2 failures | stale-checkout, failed-pull |
| `load_state` returns empty on a missing file | red, 3 failures | MissingState post and check, StateFile missing |
| `post` continues after a RecordError | red, 1 failure | push-fails-stops-the-run |
| `post` trusts a list computed before the pull (a list from `check`) | red, 1 failure | stale-checkout |
| Extra: drop the state reload after a rebase | red, 1 failure | record-another-run-pushed-meanwhile |

Task 3's mutations (anchor removed, href changed, anchor with no record, rel removed, due page deleted, page for a future note, corrupt syndication.json, host outside the allowed pair, empty-body note file) are tests in `ProbeMutations`; each asserts the probe goes red and names the page or file.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] A rebase must refresh the in-memory state**
- **Found during:** Task 2 design (the plan has the rebase but not what happens to the document in memory)
- **Issue:** `record` writes from the in-memory document. If a rebase pulled in another run's record, the next record would write a document without it and delete it, which makes a later double post possible.
- **Fix:** After a successful rebase the merged file is re-read with `load_state`, its new record is asserted present, and the in-memory document is replaced in place. A merge that leaves unreadable JSON, or drops our record, is a RecordError. `post` also skips a platform that the refreshed state shows as recorded. Proven by a test and the extra mutation above.
- **Files modified:** scripts/syndicate-notes.py, tests/test-notes.py
- **Commit:** d5a8317

**2. [Rule 3 - Blocking] The probe needs a pinned "now" for builds made with `hugo --clock`**
- **Found during:** Task 3
- **Issue:** The existing "due" fixture build is made at a clock of 2100 and holds a page for a note dated 2099. Judged at the wall clock, that note is in the future and has a page, so the new built-vs-due check would be red on a correct build.
- **Fix:** Added `VALIDATE_NOTES_NOW` beside the three overrides the plan names. Production never sets it. It also lets the race tests pin an exact instant.
- **Files modified:** tests/validate-notes.sh, tests/test-notes.py
- **Commit:** a7304d6

**3. [Rule 1 - Bug] The probe wrote a bytecode cache into scripts/**
- **Found during:** final check
- **Issue:** Loading the script through importlib created `scripts/__pycache__`.
- **Fix:** `python3 -I -B` in the probe; the directory removed (it was gitignored, never tracked).
- **Commit:** f267b17

### Other notes

- The per-plan commit ledger file could not be written from a worktree Bash call (the worktree guard refused the compound command, as in plan 01), so `plan_head_before` is the known base `29f13d0` and `commits` is measured with `git rev-list --count` from it.
- Task 1 was committed with the single-attempt core of the protocol, and Task 2 added retries, pull-before-read, the push retry loop, MAX_AGE, the single try after a timeout and DRY_RUN, as the plan splits them. The script docstring was written complete in Task 1.
- STATE.md and ROADMAP.md were not touched, per the run instructions.

## Known Stubs

None. `POSTERS` holds only mastodon by design; plan 03 registers bluesky.

## Threat Flags

None beyond the plan's register. T-mev-04 through T-mev-10 are mitigated as written: header-only bearer token with a shape check, no redirect handler and no ProxyHandler (a 302 is a failure and its Location gets no request, tested), state shape and host allow-list, hard failure on missing or malformed state plus MAX_AGE, Idempotency-Key plus record-before-next-post plus pull-before-read, response URL checked against the account prefix, size cap and bounded retries, and the three-layer test guard.

## Self-Check: PASSED

- Created files exist: scripts/syndicate-notes.py, data/syndication.json.
- Commits 3866a67, d5a8317, a7304d6, f267b17 are ancestors of HEAD (f267b174d1bbfacb68c63c596908613189bfad5b).
