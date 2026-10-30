---
phase: quick-261030-pg5
plan: 01
subsystem: notes
tags: [hugo, indieweb, microformats, css, tests]
status: complete
requires:
  - quick-261030-mev (Notes section, syndication, probes)
provides:
  - bare-domain gate in tests/validate-notes.sh
  - notes rendered as a social feed card (index and note page share one partial)
affects:
  - content/notes/new-home.md
  - themes/arcaeon notes layouts, icon partials, notes CSS block
tech-stack:
  added: []
  patterns:
    - one h-entry partial as the single card source
    - counts read from data/webmentions.json keyed by RelPermalink, defaulting empty at each step
key-files:
  created:
    - themes/arcaeon/layouts/partials/icons/reply.html
    - themes/arcaeon/layouts/partials/icons/like.html
    - themes/arcaeon/layouts/partials/icons/repost.html
  modified:
    - content/notes/new-home.md
    - tests/validate-notes.sh
    - tests/test-notes.py
    - themes/arcaeon/layouts/partials/notes/entry.html
    - themes/arcaeon/layouts/notes/single.html
    - themes/arcaeon/layouts/notes/list.html
    - themes/arcaeon/assets/css/main.css
decisions:
  - "Bare-domain rule uses a short host-only TLD list (com, org, net, io, dev, social, me) so file.txt and Node.js in prose never trip it"
  - "Copy-link icons are wrapped in span.note__icon aria-hidden rather than editing the shared mastodon/bluesky partials"
commits: 2
plan_head_before: 8a90de06a500ac257bee5500445544438b3b4739
plan_head_after: dfd2be1e4dcd9c0c099d55e49bd9625172c576d7
actuals:
  tasks: 2
  commits: 2
---

# Phase quick-261030-pg5 Plan 01: Notes links and social feed design Summary

The new-home note now links its URL, a standing probe fails the build when any note carries a bare domain outside a link, and /notes/ plus each note page render as a social post card in the existing ARCAEON palette. Nothing was posted and data/syndication.json is unchanged.

## What was built

**Task 1 (86bfa6b): link the domain, gate bare domains.**
- `validate-notes.sh` gained a `Bare` parser (first h-entry's e-content text outside anchors) and a `BARE_DOMAIN` regex: dotted hostname plus a slash, or a host ending in com/org/net/io/dev/social/me, not preceded by a word character, @, dot, colon, hyphen or slash. Failure line: `bare domain: /notes/SLUG/ has "MATCH" outside a link, write it with https:// because syndication links only URLs with a scheme`. Pass line: `no note has a bare domain outside a link`.
- Red at HEAD before the content fix, as required: `FAIL bare domain: /notes/new-home/ has "falkensmage.com/notes" outside a link ...` (6 passed, 1 failed). After the body edit: 7 passed, 0 failed, and the built page holds `<a href=https://falkensmage.com/notes/>https://falkensmage.com/notes/</a>`.
- `new-home.md`: body only; front matter (date line) byte-identical, checked by the plan's own assertion.
- Mutation proofs in `ProbeMutations` (all named `*bare_domain*`): with a path, host only, plus negative controls (inside an anchor, with a scheme, handle/file-name/Node.js/e.g. tokens, and a bare host in the card header outside e-content). `DueParity.test_edited_body_is_not_pending` pins that two files with the same path and date and different bodies read as equal notes, share a tid, and are not pending for a recorded path.

**Task 2 (dfd2be1): social feed card.**
- `partials/notes/entry.html` is the single source: `header` with one `a.p-author.h-card` (round first-party Hugo-processed avatar `img.u-photo` with alt, width/height 48, lazy; `p-name` Falken's Mage; `p-nickname` @falkensmage.com; `u-url` data) and, as a sibling, the timestamp anchor `u-url note__time` wrapping `time.dt-published`; body `div.note__body.e-content`; `footer.note__actions` with reply/like/repost counts (integers from `len`, zeros shown, never a template error on a missing record) and `u-syndication rel=syndication` anchors with the existing Mastodon and Bluesky icons. No entry-level p-name.
- New icon partials: reply, like, repost (inline svg, viewBox 0 0 24 24, outline, currentColor, aria-hidden).
- `single.html` and `list.html`: `notes-room` on main, `notes-band` on the band; h1, lede, h-feed, newest-first, empty state and the mentions partial after the closing article are untouched.
- CSS (Notes block in main.css, tokens only): edge-to-edge cards at 375px with 1rem inside; from 37.5rem a centered 37.5rem column with hairline sides (this also narrows the Responses band); violet hairline dividers; wrapping flex header and footer; 2.75rem tall footer links; 2px accent focus ring; no script, no transitions.
- Tests: new card/avatar/handle, timestamp-permalink, same-card-on-index, counts (1/1/0 for the mentioned note, 0/0/0 otherwise), recorded-copies-in-footer, and a `FeedCss` class (37.5rem present, opacity at least 0.6, no violet text colour, no remote URL or script). The new card tests were watched failing against the old template (5 failures) before the new template was restored.

## Verification (all run in this worktree after `rm -rf public && hugo --minify`)

| Check | Result |
|-------|--------|
| validate-notes.sh | 7 passed, 0 failed |
| validate-fa.sh | 13 passed, 0 failed (baseline 13/0) |
| tests/test-notes.py | 195 tests OK (baseline 178 plus 17 new) |
| tests/test-pull-webmentions.py | 75 OK |
| tests/test-send-webmentions.py | 46 OK |
| tests/test-send-fa-email.py | 39 OK |
| validate-phase-02 | 16 passed, 2 failed (identical to pre-edit record) |
| validate-phase-03 | 31 passed, 8 failed (identical to pre-edit record) |
| validate-phase-06 | 32 passed, 0 failed (identical to pre-edit record) |
| `git diff -- data/syndication.json` | empty |
| `syndicate-notes.py check` | `syndicate-notes: nothing due` |

The validate-phase-02 and -03 failures exist at HEAD before any edit (SOCIAL-04, CTA-01, and eight Currently-card/GetRemote checks); they are pre-existing and out of scope, recorded unchanged.

**Browser check (seen, not reasoned):** built to a scratch directory with baseURL 127.0.0.1 and driven with Playwright over Google Chrome. At 375px `/notes/` and `/notes/new-home/` have scrollWidth 375 (no horizontal scroll) and the column is 375 wide at left 0. At 1024px the column is 600 wide at left 212 (centered), with hairline sides. Screenshots read: avatar, name, handle, timestamp wrapping beneath at 375, body with the URL as an underlined link, counts, and Mastodon and Bluesky links.

**Contrast (computed from the palette hexes):** secondary text at opacity 0.75 on var(--color-text): 9.7:1 on void purple, 9.7:1 on deep indigo, 8.3:1 on midnight blue; accent links 12.4:1 on void purple (12.5 on indigo, 10.3 on midnight); hover magenta 5.6:1 on void purple (5.7 indigo, 4.7 on midnight; midnight is only the section seam gradient, not a band background).

## Deviations from Plan

None to the plan's scope. Notes for the record:
- The new mastodon/bluesky icons are not edited; their `aria-hidden` is carried by a wrapping `span.note__icon`.
- The footer counts test reads the number from `span.note__n` rather than splitting the whole `li` text, because the visible text of an `li` joins with the hidden label.
- The Hugo `.Site.Data` deprecation warning printed on build comes from existing code, not from this change (the new partial uses `hugo.Data`).

## Known Stubs

None.

## Threat Flags

None. The card adds no endpoint, auth path or third-party request; the avatar is first-party, counts are `len` integers, copy hrefs use plain output.

## Self-Check: PASSED

- Files exist: entry.html, single.html, list.html, reply.html, like.html, repost.html, main.css, test-notes.py, validate-notes.sh, new-home.md (all present, committed).
- Commits exist on this branch: 86bfa6b, dfd2be1.
