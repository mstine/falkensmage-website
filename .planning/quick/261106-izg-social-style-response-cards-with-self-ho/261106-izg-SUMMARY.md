---
phase: quick-261106-izg
plan: 01
subsystem: webmentions
tags: [webmentions, avatars, hugo, privacy, bridgy]
status: complete
requires: []
provides:
  - self-hosted webmention avatars (static/webmention-avatars/, gitignored, own Actions cache entry)
  - Bridgy-Mastodon conversation links (derive in pull-webmentions.py)
  - social-style response cards and face rows (fa/mentions.html + main.css)
key-files:
  created: []
  modified:
    - scripts/pull-webmentions.py
    - tests/test-pull-webmentions.py
    - tests/test-notes.py
    - tests/validate-fa.sh
    - themes/arcaeon/layouts/partials/fa/mentions.html
    - themes/arcaeon/assets/css/main.css
    - .github/workflows/hugo.yml
    - .gitignore
decisions:
  - "Avatars live in static/ (copied without decoding), named sha256(photo url)[:32].<sniffed ext>; remote photo URL never enters a record"
  - "write_data is the privacy boundary: records cut to FIELDS, avatar must fullmatch AVATAR_RE"
  - "derive() runs on fresh and last-good records (idempotent), so old caches are upgraded with no token"
  - "Avatars get their own Actions cache pair; the data cache steps are untouched (path-list version hash)"
commits: 3
plan_head_before: 4a8fc3f1f07231b9947f2e3551f10b01bb33edfc
plan_head_after: 0adea2f5cde67e1fd1ae3a2976af481a8750cc40
actuals:
  tokens: 60000
  tasks: 3
  commits: 3
---

# Phase quick-261106-izg Plan 01: Social-style response cards with self-hosted avatars Summary

Webmention responses now render as note-style cards with round avatars that falkensmage.com serves itself (downloaded at build, sniffed by magic bytes, capped at 200 KB, never hotlinked), and Bridgy-Mastodon replies link to the conversation on the instance instead of an ActivityPub JSON document.

## Commits

| Task | Commit | Message |
|------|--------|---------|
| 1 (tracer) | 539d236 | feat(webmentions): self-host reply avatars, end to end |
| 2 | 398bf4d | feat(webmentions): avatar cache and limits, Bridgy conversation links, card fields |
| 3 | 0adea2f | feat(responses): social-style response cards with self-hosted avatars |

Nothing is pushed.

## What changed

- **Pull script.** `normalize(children, photos=None)` records photo URLs in a side dict. `attach_avatars` fetches each distinct photo once (https only, dotted host, no IP literal/localhost, no redirects, one 5 s attempt, 200 KB cap, 45 s budget, no Authorization header), sniffs PNG/JPEG/WebP/GIF, and writes atomically. Valid cached files are reused with no request. `write_data` sanitizes to `FIELDS` and drops any avatar not matching `/webmention-avatars/<32 hex>.<ext>`. `derive` computes the Bridgy conversation URL, platform, handle and initial. `restore`/`assemble`/`keep_present_avatars`/`prune_avatars` give every run (pull, no token, outage) a pruned avatar dir and revalidated references. Blocklist runs before any photo fetch. Docstring "Why names only" replaced with "Why avatars are self-hosted, never hotlinked" plus a Bridgy section.
- **Template + CSS.** Likes and reposts are overlapping 2rem faces with a count and `Liked by` / `Reposted by` accessible names. Replies are cards (avatar or initial on violet, name, handle, linked date, text, "View on Mastodon/Bluesky"). Mentions row unchanged. `id="responses"` on the heading. No JS, no remote load, nothing animates.
- **Probe.** `tests/validate-fa.sh` now allows `img`/`svg`/`path` and fails on any img whose src is not a `/webmention-avatars/` path present in the build (or lacks `alt`).
- **Workflow.** New restore/save pair for `static/webmention-avatars` (`webmention-avatars-` prefix); data cache steps unchanged. `static/webmention-avatars/` gitignored.

## Verification

- `hugo --minify`; all five suites pass (10 + 215 + 106 + 39 + 46 tests); `tests/validate-fa.sh` 13/0 and `tests/validate-notes.sh` 7/0 on the clean production build.
- `git ls-files static/webmention-avatars` prints nothing; diff touches only the eight files in `files_modified`; `notes.yml`, `syndicate-notes.py` and `data/` untouched.
- `responses-375.png` is 375x1600.

## Review gate

Screenshot: `/Users/falkensmage/workspace/digital-intuition/falkensmage-website/.claude/worktrees/agent-a0c43f2fd6b505d78/.planning/quick/261106-izg-social-style-response-cards-with-self-ho/responses-375.png`

It shows the Lovers note with the fixture Responses section: two like faces (one photo, one initial), one repost face, a Mastodon reply card with avatar, a Bluesky reply card with an initial, platform links, and no horizontal overflow.

Re-shoot (run from the repo root; the quick dir holds the helpers):

```
Q=.planning/quick/261106-izg-social-style-response-cards-with-self-ho
python3 -I $Q/make-fixture.py
hugo --minify --baseURL http://127.0.0.1:1414/
python3 -m http.server 1414 --bind 127.0.0.1 --directory public &
# Chrome headless enforces a ~500px minimum window width, so a plain --window-size=375 renders a
# 500px layout and crops it. Instead shoot a 600px window holding a 375px iframe (frame.html), then crop:
bash $Q/shoot.sh 600 1600 file://$PWD/$Q/frame.html /tmp/wide.png
python3 -I $Q/crop.py /tmp/wide.png $Q/responses-375.png 375 1600
pkill -f "http.server 1414"
rm -f data/webmentions.json && rm -rf static/webmention-avatars
hugo --minify --cleanDestinationDir
```

(`frame.html` and `shoot.sh` hold absolute scratchpad paths from this run: adjust the user-data-dir in `shoot.sh` and nothing else.)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Chrome headless minimum window width**
- **Found during:** Task 3 review gate
- **Issue:** `--window-size=375,N` rendered a ~500px layout, cropping the page on the right (clipped note text and dates), so the screenshot did not show the real 375px layout.
- **Fix:** Shot a 600px window containing a 375px-wide iframe and cropped to 375px with a stdlib PNG cropper (`crop.py`). The result is a true 375px layout, 375px wide.
- **Files modified:** none in the repo (helper scripts live in the quick dir, uncommitted)

**2. [Rule 1 - Bug] Link underline/colour overrode card styles**
- **Found during:** Task 3 screenshot
- **Issue:** `.fa-prose a` (specificity 0,1,1) overrode `.fa-face`, `.fa-reply__author` and `.fa-reply__time`, underlining the author name and initials and colouring the date cyan.
- **Fix:** prefixed those selectors with `.fa-mentions`.
- **Commit:** 0adea2f

**3. [Test adjustment] Cache-reuse test follows the prune design**
- The plan's behavior list implies a pre-seeded avatar file is reused, but the pre-network prune (required: "every run deletes any avatar the data file does not reference") removes unreferenced files first. The reuse test therefore seeds last-good referencing the cached file, and invalid-cache revalidation is tested through `attach_avatars` directly. No behavior change.

## Known Stubs

None. (Fixture data and avatars were removed; `data/webmentions.json` and `static/webmention-avatars/` do not exist in the tree.)

## Threat Flags

None beyond the plan's threat model (T-261106-izg-01 through -10 are all covered by tests: AvatarTracer, Avatars, RestorePath, WritePrivacy, AvatarWorkflow, probe mutations).

## Self-Check: PASSED

- 539d236, 398bf4d, 0adea2f are ancestors of HEAD.
- responses-375.png, make-fixture.py, crop.py, shoot.sh, frame.html exist in the quick dir.
