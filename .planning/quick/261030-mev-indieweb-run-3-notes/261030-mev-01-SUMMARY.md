---
phase: quick-261030-mev
plan: 01
subsystem: site
tags: [hugo, indieweb, microformats, notes, webmention, rss]
requires:
  - quick-261030-kwk (run 2: webmention receive, fa/mentions.html, page_key)
provides:
  - /notes/ section: title-less notes as h-entry pages, an h-feed index, an RSS feed, a conditional nav link
  - mentions on note pages, outside the h-entry
  - tests/validate-notes.sh and tests/test-notes.py, with mutation proofs for both probes
affects:
  - scripts/pull-webmentions.py (page_key)
  - tests/validate-fa.sh (webmention probe covers notes)
tech-stack:
  added: []
  patterns:
    - one h-entry partial shared by the note page and the index
    - empty section builds clean, and nothing links to it until a note is published
    - temp-dir content mounts to isolate tests from real notes
key-files:
  created:
    - content/notes/_index.md
    - archetypes/notes.md
    - themes/arcaeon/layouts/notes/single.html
    - themes/arcaeon/layouts/notes/list.html
    - themes/arcaeon/layouts/notes/list.rss.xml
    - themes/arcaeon/layouts/partials/notes/entry.html
    - tests/validate-notes.sh
    - tests/test-notes.py
  modified:
    - themes/arcaeon/layouts/_default/baseof.html
    - themes/arcaeon/layouts/partials/nav/header.html
    - themes/arcaeon/assets/css/main.css
    - scripts/pull-webmentions.py
    - tests/test-pull-webmentions.py
    - tests/validate-fa.sh
decisions:
  - Notes have no entry-level p-name by design (Bridgy treats a named entry as an article)
  - fa/mentions.html reused unchanged; it is keyed on .RelPermalink
  - rel=feed in the head points at the h-feed so backfeed can find a note's original
metrics:
  tasks: 3
  completed: 2026-10-30
status: complete
actuals:
  tokens: 13000
  tasks: 3
  commits: 3
plan_head_before: 4355cede72ac0491106e9c561de13d450cbb1d9a
plan_head_after: d39700afc1c20563a844c4685455ae34b7e82f02
---

# Phase quick-261030-mev Plan 01: Notes site half Summary

A Markdown file with a date and no title now renders as a complete h-entry on its own page, in a /notes/ h-feed and in /notes/index.xml, with received mentions underneath (outside the h-entry), and both probes are proven able to fail.

## Tasks

| Task | Name | Commit |
|------|------|--------|
| 1 | Note file becomes an h-entry page and index entry (tracer) | eb66608 |
| 2 | Feed, nav, head links, look, archetype | f04a557 |
| 3 | Mentions under notes, page_key, mutation proofs | d39700a |

## What was built

- **Page and index.** `partials/notes/entry.html` is the single h-entry (e-content, nested p-author h-card with p-name, u-url, u-photo, a u-url link wrapping dt-published, no entry-level p-name). `notes/single.html` and `notes/list.html` call it. The index is one `h-feed` with a "Nothing here yet." empty state.
- **baseof.** Title-less notes get a title from their own text (`.Plain | htmlUnescape | plainify | truncate 60`, cast with `printf "%s"` so a less-than is escaped), og:type article, a fixed og:title, a description from the note, and `article:published_time` / `article:author` for essays and notes alike.
- **Feed, nav, head.** `notes/list.rss.xml` emits title-less items with absolutized links. The Notes nav link, the RSS alternate link and `rel=feed` appear only once the section has a published note.
- **Look and archetype.** A short CSS block built from existing tokens; `archetypes/notes.md` holds only `date: {{ .Date }}`.
- **Mentions.** `page_key` accepts `/notes/SLUG/` (with or without trailing slash) and returns None for `/notes/`, `/notes/SLUG/extra/`, `/work/SLUG/` and other hosts. `notes/single.html` calls `fa/mentions.html` after the closing article tag. `validate-fa.sh` walks `public/notes/*/index.html` and treats a note as mention-bearing even without its og tag.
- **Probes.** `validate-notes.sh` checks h-entry markup, the index and feed against the published count, and nav and head agreement. `test-notes.py` builds the real site offline (`[security.http] urls = ["^$"]`, fixture notes mounted over `content/notes`) and runs mutation proofs: 13 against `validate-notes.sh`, 5 against `validate-fa.sh`, plus empty-section baselines for both.

## Verification

- `tests/test-notes.py`: 36 OK. `tests/test-pull-webmentions.py`: 75 OK (67 baseline plus 8 `PageKey`). `test-send-webmentions.py` 36 OK, `test-send-fa-email.py` 6 OK.
- Real tree, `rm -rf public && hugo --minify`: `validate-fa.sh` 13/0, `validate-notes.sh` 3/0 with `0 notes`, `/notes/` shows the empty state.
- Baselines unchanged: validate-phase-06 32/0, validate-phase-02 16/2, validate-phase-03 31/8.
- `content/notes/` holds only `_index.md`. No `__pycache__`, no stray files, nothing pushed, no script run against Mastodon or Bluesky.

## Deviations from Plan

None to the behavior. Two notes:

- The plan listed `themes/arcaeon/layouts/notes/single.html` as touched in Task 1 only through the entry partial. The mentions partial call was added in Task 3, as planned.
- The plan's per-plan commit ledger file under the git dir could not be written from a worktree Bash call (the worktree guard refused the compound command), so `plan_head_before` is the known base `4355cede...` and `commits` is measured with `git rev-list --count` from it.

## Known Stubs

None.

## Threat Flags

None. The only new surface is note pages, covered by T-mev-01 (mentions reuse the escaped, names-only partial after the closing article tag, now probed on notes).

## Self-Check: PASSED

- Created files exist: content/notes/_index.md, archetypes/notes.md, notes/single.html, notes/list.html, notes/list.rss.xml, partials/notes/entry.html, tests/validate-notes.sh, tests/test-notes.py.
- Commits eb66608, f04a557, d39700a are ancestors of HEAD.
