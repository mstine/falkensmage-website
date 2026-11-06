---
phase: quick-261106-hbn
plan: 01
subsystem: notes-syndication
tags: [bluesky, atproto, link-card, syndication]
status: complete
requires: []
provides:
  - "Bluesky app.bsky.embed.external link card with uploadBlob thumb for syndicated notes"
affects: [scripts/syndicate-notes.py, tests/test-notes.py]
key-files:
  modified:
    - scripts/syndicate-notes.py
    - tests/test-notes.py
decisions:
  - "A 400 from createRecord for a record carrying a card is posted again without it through the same getRecord-first loop on the same rkey (orchestrator-approved R8)"
metrics:
  completed: 2026-11-06
actuals:
  tasks: 3
  commits: 3
plan_head_before: 1feb9974139d55eb4774a9a46ebd3e5011c7e90d
plan_head_after: b379b64
---

# Quick 261106-hbn: Bluesky link cards for syndicated notes Summary

Syndicated notes that link a page other than their own permalink now reach Bluesky with an `app.bsky.embed.external` card (og title and description, JPEG/PNG/WebP thumb up to 1,000,000 bytes via uploadBlob), built best effort so no card failure can fail, block or double a post.

## Commits

- 0bce6e3 `feat(notes): attach a Bluesky link card to syndicated notes` (tracer: card code, CARD_OPENER, stub pages and uploadBlob, CARDS switch, end-to-end test)
- 9a9400c `feat(notes): a Bluesky link card never blocks or doubles a post` (`put(record)` extraction, `_CardRejected` fallback, 19 behavior tests)
- b379b64 `docs(notes): describe Bluesky link cards in the syndication docstring`

## Verification

- `tests/test-notes.py`: 215 tests pass (196 before this work plus 19 new `LinkCards` tests).
- Backstop, pull-webmentions and send-fa-email suites pass.
- Docstring gate prints `doc ok`.
- `tests/test-send-webmentions.py`: 2 failures in `BuiltPages` ("public/ is missing: run `hugo --minify`"). Environmental (fresh worktree has no built `public/`), in a file this plan does not touch; not fixed.

## Design notes

- Card target is chosen from the text `post_bluesky` received, before `_fit` cuts it.
- Card fetches use a separate `CARD_OPENER` (follows up to 5 redirects, no credentials, no proxy); `OPENER` and `fetch` are unchanged.
- At-most-once invariant: the rkey and the getRecord-first loop are unchanged. The loop body moved verbatim into `put(record)`; the only edit is raising `_CardRejected` on a 400 when the record carries an embed. On `_CardRejected`, the embed is removed and `put` runs once more on the same key, getRecord first. Tests: lost createRecord response with a card is one record, one upload; PDS-refused card is two createRecord calls on one rkey and one stored record without `embed`; a 400 for a record with no card is still not retried.

## Deviations from Plan

None beyond the orchestrator-approved PDS-refusal fallback (R8), which the plan already described. The card section sits directly above `post_bluesky` rather than directly after `tid`, so the helpers it calls are defined before it in the file; behavior is unaffected.

## Known Stubs

None.

## Threat Flags

None. The new outbound fetches are covered by the plan's threat model (T-261106-hbn-01 to -07).

## Self-Check: PASSED

- scripts/syndicate-notes.py and tests/test-notes.py modified; commits 0bce6e3, 9a9400c, b379b64 are ancestors of HEAD.
