---
phase: quick-261030-k5d
plan: 01
subsystem: indieweb
tags: [microformats2, h-entry, h-card, rel-me, webmention, ssrf, github-actions]
requires: []
provides:
  - h-entry markup on every Feral Architecture essay
  - homepage h-card and rel=me on all four profiles
  - standing microformats probe in tests/validate-fa.sh
  - stdlib Webmention sender with address guard, idempotent state and a post-deploy job
affects: [fa/single.html, hero.html, validate-fa.sh, hugo.yml]
tech-stack:
  added: []
  patterns: [Actions cache as sent-state, peer-address guard at one opener chokepoint]
key-files:
  created:
    - scripts/send-webmentions.py
    - tests/test-send-webmentions.py
    - tests/fixtures/webmention/discovery-test-1.html (through -17)
  modified:
    - themes/arcaeon/layouts/fa/single.html
    - themes/arcaeon/layouts/partials/sections/hero.html
    - content/_index.md
    - tests/validate-fa.sh
    - .github/workflows/hugo.yml
    - .gitignore
decisions:
  - Sent state lives in an Actions cache bounded by a 7-day window (not a commit, not a window alone, not a feed diff)
  - Address guard checks the connected peer inside connect(), not a DNS pre-flight
  - An empty href resolves to the page itself (spec), correcting popov on webmention.rocks #15
status: complete
commits: 3
plan_head_before: f373aaa7f651a677f657e273dd9b2cc3473b20b5
plan_head_after: 419ef700b5b8b0df84302afdb830ef3cdcdbd41d
actuals:
  tokens: 14000   # chars/4 over the 54.6 KB code diff (fixtures excluded)
  tasks: 3
  commits: 3
completed: 2026-10-30
---

# Phase quick-261030-k5d Plan 01: IndieWeb run 1, publish and send Summary

Every essay now publishes a complete microformats2 h-entry with a nested author h-card, the homepage carries a representative h-card with rel=me on all four profiles, a build-time probe fails when any of it rots, and a stdlib-only Python sender notifies the pages the newest essay cites, behind a connected-peer address guard and a cache-backed sent record.

## Commits

| Task | Commit | What |
|------|--------|------|
| 1 (tracer) | 8afa7da | h-entry in fa/single.html (guarded off for `fa_page`), sender core, stub end-to-end test |
| 2 | 57ce08b | Address guard, idempotent batch and state, 17 fixtures plus conformance suite, `webmentions` job |
| 3 | 419ef70 | Homepage h-card, `rel_me` on LinkedIn/Bluesky/Instagram, standing probe |

## Verification (all run in this worktree)

- `rm -rf public && hugo --minify && bash tests/validate-fa.sh`: 10 passed, 0 failed. The probe reports 86 essays (including `youve-been-heard`, which is not in `data/fa-legacy.json`) and the homepage check.
- Mutation: stripping `e-content` and the cover's `u-photo` from `youve-been-heard`, and `me` from every profile anchor, turns the probe red naming the page with `e-content, u-photo` on one line and each profile URL. `public/` rebuilt clean afterwards.
- `python3 -I -S -B tests/test-send-webmentions.py`: 36 tests, OK, about 0.5 s, no outbound network. Mutating `peer_allowed` to `return True` made 20 tests fail (restored).
- Baselines unchanged: `validate-phase-06` 32/0, `validate-phase-02` 16/2, `validate-phase-03` 31/8 (the 02 and 03 failures pre-exist). `tests/test-send-fa-email.py` green.
- `git diff f373aaa -- themes/arcaeon/assets/` is empty: no CSS or JS change.
- Newest essay's h-entry: 13 anchors, 9 external targets after dropping the one internal link and duplicates, matching the plan's measurements.
- Workflow job shape checked with Ruby YAML: `needs: deploy`, `permissions: {contents: read}`, `timeout-minutes`, `cache/restore` before the send, `cache/save` last under `if: always()`.

Not run: the sender against production, `hugo` in CI, and the post-deploy job itself (orchestrator's live check).

## Carried forward

**Sent-state decision and failure direction.** Actions cache, key unique per run, restore by prefix, save under `always()`, plus `MAX_AGE` of 7 days from the essay's publish date. A lost or denied cache save costs a duplicate POST inside the window (spec section 3.2.4 says receivers tolerate repeats); it can never cost a missed send, and an essay past the window can never resend. Only accepted pairs are recorded, so dead links and 5xx endpoints retry nightly until the window closes. Each run logs `N pairs loaded from state`; zero after a successful send is the only visible sign of a denied cache save. Rejected: commit to main (needs `contents: write` on the job parsing untrusted HTML, bot commit per essay), branch (same scope), window alone (resends every run), feed diff (one transient failure lost forever).

**Popov #15 correction.** popov's `composeWebmentionRequest` uses `ifBlank` to append `/webmention` and its test asserts `/test/15/webmention`. An empty `href` is a relative reference that resolves to the base URL, and the fixture text says the page is its own endpoint. This suite asserts `/test/15`. popov stops at #17; #18 through #23 (two Link headers, comma-joined header, element without href skipped, query string preserved and kept out of the body, relative endpoint against page path, against the final URL after a redirect) are new here. The comment sits beside the cases in `tests/test-send-webmentions.py`.

**Coverage opt-outs (DP-11, explicit).** In: link extraction from the h-entry, Link header then link/a element discovery, relative resolution and redirects, form-encoded POST with any 2xx as success, query string preserved, loopback avoidance widened to every non-global address. Opted out, not needed yet: re-send on post update (section 3.1.4, a SHOULD; a link added inside the window still sends because state is per pair), sending for deleted posts. Opted out by the brief: backfill of older essays (newest only).

**Run 2: the receiving side is untouched.** Receiving, verifying and displaying Webmentions are explicitly out of scope and unstarted. No h-feed on list pages either (fa/list.html, archive.html, card.html untouched).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing critical functionality] State-file corruption guard**
- **Found during:** Task 2
- **Issue:** The state is tab-separated lines, and a hostile or malformed href containing tab, newline or other control characters could split or inject a record.
- **Fix:** `external_targets` drops any URL containing whitespace or control characters. Not in the plan's listed behaviors, consistent with its threat register (T-k5d-04, T-k5d-06).
- **Files modified:** scripts/send-webmentions.py
- **Commit:** 57ce08b

**2. [Rule 2 - Missing critical functionality] NAT64 unwrapping in the address guard**
- **Found during:** Task 2
- **Issue:** `64:ff9b::/96` embeds an IPv4 address and reads as global on some Pythons, so a hostile host on a NAT64 network could reach an internal address.
- **Fix:** `peer_allowed` unwraps NAT64 the same way it unwraps `::ffff:` mapped addresses; covered by `64:ff9b::7f00:1` in the refusal list.
- **Files modified:** scripts/send-webmentions.py, tests/test-send-webmentions.py
- **Commit:** 57ce08b

**3. [Rule 3 - Blocking] Stub server shutdown slowed the suite**
- **Found during:** Task 2
- **Issue:** `ThreadingHTTPServer.shutdown()` waits out a 0.5 s poll interval per stub, so the suite took 14 s.
- **Fix:** `serve_forever(0.01)` in the test stub; suite now runs in about 0.5 s.
- **Commit:** 57ce08b

### Notes on plan interpretation

- `main(entry_wait=15)` takes the retry wait as a parameter so tests can pass 0; the plan specified `load_entry(url, tries=10, wait=15)` and that signature is unchanged.
- The HTTPS guard checks the peer after the TLS handshake (it overrides `connect()` and calls `super().connect()` first, as the plan specified), so a ClientHello can reach a non-global address before the refusal. No HTTP request bytes are ever written to it. Tightening that needs a private `http.client` hook and was not taken.
- The guard test covers `http://127.0.0.1`, `http://localhost`, and the redirect hop; there is no HTTPS-to-loopback case because the stub speaks plain HTTP.
- `tests/validate-fa.sh` now reports 10 checks instead of 8 (the two probes), per the plan's added lines.

## Auth Gates

None.

## Known Stubs

None.

## Threat Flags

None beyond the plan's threat register. The `webmentions` job adds outbound network egress from CI to third-party hosts; this is T-k5d-01 through T-k5d-07, mitigated as planned.

## Self-Check: PASSED

- scripts/send-webmentions.py, tests/test-send-webmentions.py, 17 fixtures under tests/fixtures/webmention/: present
- Commits 8afa7da, 57ce08b, 419ef70: ancestors of HEAD
- No `__pycache__`, `.webmentions-sent` or `*.bak` in `git status`
- No submodules in the repo (`.gitmodules` absent)
