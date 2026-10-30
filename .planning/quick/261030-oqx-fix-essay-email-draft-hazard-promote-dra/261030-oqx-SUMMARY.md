---
phase: quick-261030-oqx
plan: 01
subsystem: fa-email
tags: [buttondown, ci, python, tests]
status: complete
key-files:
  modified:
    - scripts/send-fa-email.py
    - tests/test-send-fa-email.py
commits: 1
plan_head_before: 3a4c1230ac29c8db1a492457fc9d306850b30779
plan_head_after: 9f1d0318e0fa98132ef39fb4d7c0a7bbd2994893
actuals:
  tasks: 1
  commits: 1
completed: 2026-10-30
---

# Quick 261030-oqx: Essay email draft hazard

A send_email=true dispatch now promotes the single existing draft to about_to_send via PATCH, and a requested send that cannot happen exits non-zero instead of printing skip-duplicate.

## What changed

- `scripts/send-fa-email.py`: new `promote` action in `decide()`, `pick_draft()` (lowest id by string sort), `DELIVERED` and `send_blocked()`, `api(method=)`, `statuses_for_subject()` returns `(id, status)` pairs, and `act()` extracted from `main()`. The PATCH body is `{"status": "about_to_send"}` only, so edits made to the draft in Buttondown are mailed as left. The failure check runs before the dry-run return, so a dry run reports a would-fail send.
- `tests/test-send-fa-email.py`: 39 tests, up from 6. Covers the decision table, non-send pin against an inline copy of the old rule (all combinations up to 3 of the 14 statuses), PATCH request shape, an in-memory fake Buttondown with a decoy subject, and a two-dispatch scenario from three start states. An invariant checker passes for the real `decide()` and fails for all three mutants. The wiring-level check trips with mutants (a) and (b) patched in. `urlopen` is a tripwire for the whole suite; a dummy key is used and no environment is read.

## Verification

- `python3 -I -S -B tests/test-send-fa-email.py`: 39 tests, OK, about 0.02s.
- `grep -c 'method="PATCH"' scripts/send-fa-email.py` = 1 (baseline 0). `grep -c urlopen tests/test-send-fa-email.py` = 5 (baseline 0).
- `git status --short -- scripts tests .github` listed exactly the two files before commit.
- The script was not run and no real API call was made.

## Deviations from Plan

None. The `.github/workflows/hugo.yml` file was not touched.

One note on mutant (a) at wiring level: with the real `pick_draft`, a second dispatch under mutant (a) finds no draft and exits, which the helper converts to AssertionError. With three starting drafts it produces a genuine second mail call. Both routes are caught.

## Known Stubs

None.

## Self-Check: PASSED

Both files exist and commit 9f1d031 is HEAD.
