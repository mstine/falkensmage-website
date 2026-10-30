---
phase: quick-261030-kwk
plan: 01
subsystem: indieweb
tags: [webmention, hugo, github-actions, python-stdlib]
requires:
  - phase: quick-261030-k5d
    provides: h-entry markup and the outbound sender this section must stay out of
provides:
  - rel=webmention endpoint on every page
  - scripts/pull-webmentions.py (domain-wide pull, last-good, blocklist, witness)
  - names-only, escaped Responses section under FA essays
  - mentions-probe job and validate-fa.sh webmention checks
affects: [fa essays, hugo.yml, validate-fa.sh]
tech-stack:
  added: []
  patterns: [generated-at-build data file with Actions-cache last-good, red-after-deploy job]
key-files:
  created:
    - scripts/pull-webmentions.py
    - tests/test-pull-webmentions.py
    - themes/arcaeon/layouts/partials/fa/mentions.html
    - data/webmention-blocklist.json
    - tests/fixtures/webmention/example-mentions.jf2.json
    - tests/fixtures/webmention/hostile-mentions.jf2.json
  modified:
    - themes/arcaeon/layouts/_default/baseof.html
    - themes/arcaeon/layouts/fa/single.html
    - themes/arcaeon/assets/css/main.css
    - tests/validate-fa.sh
    - .github/workflows/hugo.yml
    - .gitignore
key-decisions:
  - "Blocklist is JSON (data/webmention-blocklist.json), not the brief's example YAML: the pull is stdlib only under python3 -I -S and Python has no YAML parser; data/ already holds JSON lists"
  - "Data file generated at build and gitignored; last-good lives in the Actions cache, saved only on a successful pull"
  - "Names only, no avatars; only content.text is read; mention-of, bookmark-of and rsvp are counted but not rendered"
status: complete
actuals:
  tokens: 20000
  tasks: 3
  commits: 3
plan_head_before: d297e72e88cfe5da524eb86aaeedc6fb0a01ba1a
plan_head_after: c2004cf2df3934e9f7bed556ea9aed6863b02e9f
commits: 3
duration: single session
completed: 2026-10-30
---

# Phase quick-261030-kwk Plan 01: IndieWeb run 2, receive Summary

Every page now advertises `https://webmention.io/falkensmage.com/webmention`, every build pulls the domain's Webmentions through a stdlib script into a generated data file, and FA essays show likes, reposts and replies as escaped names and plain text under the essay, outside the h-entry, with no JS and no third-party image.

## What shipped

- **Endpoint.** `<link rel="webmention">` in baseof.html, under the fediverse:creator meta.
- **Section.** `fa/mentions.html`, rendered after the closing article tag in `fa/single.html`, so `scripts/send-webmentions.py` never sees a stranger's URL. Plain `{{ }}` output only, `rel="nofollow ugc"` on every anchor, no image URL ever in the data. Absent when an essay has no mentions; byte-identical to a no-data build (tested).
- **Pull.** `scripts/pull-webmentions.py`, Python 3.10-compatible, runs under `-I -S`. Paged walk (`page`, not `since_id`) with a count guard, shape checks, 3 tries on 5xx/429/timeouts, no redirect handler, token in the Bearer header only and shape-checked before it reaches http.client. Logs carry counts and fixed text, never a mention field.
- **Workflow.** Restore last-good by prefix, `Pull Webmentions` (`continue-on-error`, 3 min timeout, the only place the secret appears), save last-good only when the pull succeeded, then Hugo. `mentions-probe` runs after deploy and fails on any outcome other than `success`, including empty.
- **Probe.** Three new `tests/validate-fa.sh` checks (13 passed, 0 failed): endpoint on every page, section matches the data and stays inert and outside the h-entry, blocklist well formed.
- **Look.** A short `.fa-mentions` block in main.css, rems and the existing border colour only, `overflow-wrap: anywhere` for 375px.

## The failure table

| Situation | Data file | Exit | Deploy | Run |
|---|---|---|---|---|
| Pull succeeds | Fresh | 0 | Yes | Green |
| Secret absent (the one non-failure) | Last-good or empty, blocklist reapplied | 0 | Yes | Green, log line and `::notice` |
| Outage, 5xx, timeout after 3 tries | Last-good, blocklist reapplied | 1 | Yes | Red in `mentions-probe` |
| 401, 400 or any 3xx | Same | 1, no retry | Yes | Red |
| Wrong shape, bad JSON, short walk | Same | 1 | Yes | Red |
| 200 with zero mentions, last-good has some, witness finds mentions | Same | 1 | Yes | Red |
| 200 with zero mentions, witness agrees they are gone | Emptied | 0 | Yes | Green |
| Corrupt cache entry | Repaired to valid first | Falls into a row above | Yes | Per that row |
| Script crash | Whatever the last rewrite left, always valid | Non-zero | Yes | Red |
| Blocklist file malformed | Untouched | 1, and `validate-fa.sh` blocks | No | Red (repo bug) |
| Template no longer renders the data | Valid | 0 | No | Red (`validate-fa.sh` runs before upload) |

**The witness.** webmention.io answers a valid token whose account does not hold the domain with a 200 and an empty feed. When a pull returns zero and last-good holds mentions, the script asks the public per-target endpoint (no token) about those pages. Mentions there mean the domain-wide answer is wrong: exit 1, last-good stays. None there means they are really gone: the file is emptied, exit 0. An unreachable witness counts as failure.

## Coverage opt-outs (DP-11)

In: `GET /api/mentions.jf2` with `domain`, `per-page`, `page`, `sort-dir` and a Bearer header; the same endpoint with `target[]` and no token (the witness); `in-reply-to`, `like-of`, `repost-of` rendered.

Out, on purpose: **`mention-of`**, `bookmark-of` and `rsvp` (counted in the log, not rendered); private mentions (dropped, never public); photo, video, audio and author photos; `content.html`; the `token` query parameter; `since`, `since_id`, the `wm-property` filter and `sort-by`; `deleted.jf2`, `count`, legacy formats, `export.jf2`; web hooks; `webmention-render.js`; pingback; dashboard sign-in, settings and moderation (manual).

**`mention-of` needs a decision from Matt.** A blog post citing an essay arrives as `mention-of`, so it is counted but not shown, because the brief named likes, reposts and replies. To show them it is one `KINDS` entry in the script and one template loop in the partial.

## Matt's manual steps and checks

- Sign-in and the `WEBMENTION_IO_TOKEN` repo secret are done (per the orchestrator: signed in through GitHub, since IndieLogin rejected the Bluesky rel=me links; the rel=me lines were not touched). The API accepted the token and returned total 0.
- Still Matt's: sign up for Bridgy backfeed.
- **Setup check the witness cannot do.** Once the first mention exists, the next build's log total must match the webmention.io dashboard. A token from the wrong account reads as zero until a mention exists to compare against (T-kwk-12).
- **An absent secret stays green by design.** If the secret is ever removed after setup, the only sign is the `pull-webmentions: WEBMENTION_IO_TOKEN is not set` log line and the `::notice`.

## Verification

- `python3 -I -S -B tests/test-pull-webmentions.py`: 57 tests, OK, no outbound network (every Hugo build carries `[security.http] urls = ["^$"]`).
- Mutation proofs, each turns the probe red naming the page: section deleted, remote img added, ugc dropped, section moved inside the article, endpoint link removed from one page, section added to /fa/about/, like-count mismatch, blocklist reshaped to a bare list, empty data against a rendered section, and a real `safeHTML` pipe added to the partial's name and text interpolations (live `script` and `img` rendered, probe red).
- With `PULL_FAILED = 0` the suite fails (26 failures); restored to 1.
- `bash tests/validate-fa.sh`: 13 passed, 0 failed on a clean build with no data file.
- `test-send-webmentions.py` 36 OK, `test-send-fa-email.py` 6 OK.
- Baselines unchanged: validate-phase-06 32/0, validate-phase-02 16/2, validate-phase-03 31/8 (the 02 and 03 failures pre-exist).
- `scripts/send-webmentions.py` and `scripts/send-fa-email.py` are byte-identical to 02ccc34.
- The workflow parses with restore, pull, save, then Hugo in order; the probe job's real shell exits 0 on `success`, 1 on `failure` and on empty.

## Deviations from Plan

**1. [Rule 1 - Bug] `ul` placed outside the Replies `p`.** The plan described a `p.fa-mentions__row` holding the label span "then `ul`". A `ul` inside a `p` is invalid HTML (browsers close the `p`), so the label `p` closes and the `ul` follows it. Same classes, same probe allow-list.

**2. [Rule 1 - Bug] Tests pin the literal exit code 1.** The first draft compared against `m.PULL_FAILED`, so the plan's own mutation (`PULL_FAILED = 0`) passed the suite. Tests now use a literal `FAILED = 1`. Found by running the mutation.

**3. Fixture capture.** `example-mentions.jf2.json` was fetched once from the example endpoint (sha256 b3b4da4e…9e443f, matching the plan) and committed with Task 1 rather than Task 2, since the same commit's file list was the tracer. No other live call was made.

**4. Base branch.** The plan's baselines were measured at 02ccc34; this worktree is at d297e72 (adds the GitHub rel=me from PR #6). Baseline counts were identical.

Otherwise the plan was executed as written.

## Known Stubs

None.

## Threat Flags

None beyond the plan's register. The new surface (webmention.io network call, Actions cache restore) is the plan's T-kwk-04 and T-kwk-10.

## Self-Check: PASSED

- Files: scripts/pull-webmentions.py, tests/test-pull-webmentions.py, themes/arcaeon/layouts/partials/fa/mentions.html, data/webmention-blocklist.json and both fixtures exist.
- Commits 59396f0, 33cf814, c2004cf are ancestors of HEAD (3 commits since d297e72).
- `git status` shows only the untracked `.planning/quick/...` directory; no `__pycache__`, `*.bak` or `data/webmentions.json`.
