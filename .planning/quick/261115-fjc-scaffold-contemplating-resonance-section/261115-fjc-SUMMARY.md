---
phase: quick-261115-fjc
plan: 01
subsystem: cr-section
tags: [hugo, substack-migration, own-the-stack, sanitizer, rss]
status: complete
requires:
  - FA own-the-stack pattern (scripts/sync-fa.py, themes/arcaeon/layouts/fa/, tests/validate-fa.sh)
provides:
  - "/cr/ section: 51 self-hosted page bundles, index, full-content RSS, validate-cr.sh gate"
affects:
  - themes/arcaeon/layouts/_default/baseof.html (CR-scoped branches only)
  - themes/arcaeon/assets/css/main.css (appended CR block)
tech-stack:
  added: []
  patterns: ["throttled cached fetcher", "bs4 allowlist sanitizer", "HTML-content-format leaf bundles"]
key-files:
  created:
    - scripts/sync-cr.py
    - data/cr-legacy.json
    - content/cr/_index.md
    - content/cr/<51 slugs>/ (index.html, cover.jpg, img-NN.*)
    - themes/arcaeon/layouts/cr/single.html
    - themes/arcaeon/layouts/cr/list.html
    - themes/arcaeon/layouts/cr/list.rss.xml
    - themes/arcaeon/layouts/partials/cr/posts.html
    - themes/arcaeon/layouts/partials/cr/masthead.html
    - tests/validate-cr.sh
  modified:
    - themes/arcaeon/layouts/_default/baseof.html
    - themes/arcaeon/assets/css/main.css
decisions:
  - "Front matter key is cr_kind, not kind: Hugo 0.160.1 hard-errors on a front matter key named kind"
  - "Non-Substack remote images (Unsplash) are localized too, so every image is a bundle file; a failed fetch leaves the hotlink with a WARN"
metrics:
  duration: "~1h (dominated by 3s-throttled network: 49 post fetches, ~115 image fetches)"
  completed: 2026-11-15
plan_head_before: 8d4f1164384fd2820fb163148ffe27c3e4c3a2df
plan_head_after: 033291cc2c50bfc301b6b4b0a680aa0a6cbd4871
commits: 3
actuals:
  tokens: 116800
  tasks: 3
  commits: 3
---

# Phase quick-261115-fjc Plan 01: Scaffold the Contemplating Resonance section Summary

One-way Substack-to-Hugo sync (throttled, cached, sanitized, image-localizing) that turns the 53-entry CR listing into 51 self-hosted page bundles at /cr/<exact-slug>/, with list, single and full-content RSS templates in the arcaeon look and a self-building gate, all on branch cr/own-the-stack, unlinked and unmerged.

## What shipped

- `scripts/sync-cr.py`: reads the saved listing, asserts the non-public set equals the two named gated slugs, fetches post JSON from `/api/v1/posts/<slug>` (3 s sleep before every live request, one helper for everything), caches JSON and image bytes under `~/.cache/sync-cr` (outside the repo), sanitizes bodies with a bs4 allowlist, localizes images with sips, writes `content/cr/<slug>/index.html` (HTML content format) and `data/cr-legacy.json`. The cookie file was never passed or read; every public post answered anonymously. `--offline` rerun: 0 live requests, `git diff` empty (byte-identical).
- Counts: 51 posts, 18 podcasts, 49 covers (2 posts have no cover in Substack: `pardon-the-interruption-folks`, `were-taking-an-indefinite-break-yall`), 88 inline images localized, 8 posts with footnotes.
- Templates: `cr/single.html` (compact masthead, h-entry header with byline/date/duration, cover, pending-player notice for podcasts with `data-cr-player`, body, older/newer neighbors), `cr/list.html` (masthead + lede, newest featured via the existing FA card partial read-only, all posts grouped by year, RSS link), `cr/list.rss.xml` (30 newest, `content:encoded` with absolutized `src`/`href`), `partials/cr/posts.html`, `partials/cr/masthead.html`.
- `baseof.html`: `$inCR` branches only (site name, title, article OG with the bundle cover, section OG with the lede, feed discovery rendered only when in `/cr/`). FA and notes branches untouched.
- `tests/validate-cr.sh`: builds into a mktemp dir, 12 checks (51 slugs, dropped slugs absent, no Substack-hosted asset, sanitized bodies, local imgs resolve, podcast player notice + `media_url`, 51/2 counts, feed full-content and absolute URLs, article OG, `| Contemplating Resonance` titles, pre-cutover unlinked block) plus 2 INFO lines. `VALIDATE_CR_PARTIAL=1` mode used for the tracer. Not wired into any workflow.

## Tracer

Three posts: `s3e4-stripping-down-the-sacred-with` (podcast: subscribe widget, share CTA, two Spotify iframes, digest-post card), `the-labyrinth-is-gone-the-architect` (newest; leading cover duplicate dropped), and the third slug **`whats-resonating-this-week-14`** (newest newsletter with a surviving Substack-hosted inline image). `closing-one-door-opening-another` is newer with one captioned image, but that image is an Unsplash photo, so it would not have exercised Substack-image localization at the time. Gate: `VALIDATE_CR_PARTIAL=1 bash tests/validate-cr.sh` passed; all 51 post JSONs cached.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Front matter key `kind` rejected by Hugo 0.160.1**
- **Found during:** Task 1 (first validator build failed)
- **Issue:** The plan states a `kind` key lands in `.Params.kind`. In Hugo 0.160.1 it logs `ERROR deprecated: kind in front matter was ... removed`, failing the build.
- **Fix:** Renamed to `cr_kind` in the script's front matter, `cr/single.html`, `cr/list.html` and `validate-cr.sh`.
- **Files modified:** scripts/sync-cr.py, themes/arcaeon/layouts/cr/single.html, themes/arcaeon/layouts/cr/list.html, tests/validate-cr.sh
- **Commit:** 8f007af

**2. [Rule 1 - Bug] Sanitizer dropped or mangled real content (found from the WARN report, Task 2)**
- **Issue:** `youtube-wrap` divs, `mention-wrap` spans, `image-gallery-embed` (lost the gallery photos), `embedded-publication-wrap` recommendation cards (unwrapped into loose text and fetched their logos), editor-only `hide-text` labels ("Text within this block will maintain its original spacing...") and subscription widgets without a `-wrap` class leaked through or were silently deleted.
- **Fix:** YouTube becomes a "Watch on YouTube" link, a mention becomes the author's name as text, a gallery becomes one figure per image (caption on the last), a publication card becomes one link, `hide-text` labels and every `subscription-widget*` class are removed; embeds now convert before image prep so card logos are not downloaded. `pre` blocks get `white-space: pre-wrap`.
- **Commit:** 8ce3676 (CSS line in 033291c)

**3. [Rule 2 / plan-internal conflict] Non-Substack images are localized, not left hotlinked**
- **Issue:** Task 1 step A6 says non-Substack image hosts "stay as they are, with a WARN", but must_have truth 4 says every cover and inline image is a file in its page bundle served from falkensmage.com, and the site constraint is no external dependencies. 15 inline images across 14 posts were hotlinked from images.unsplash.com.
- **Fix:** Any remote http(s) image is fetched through the same throttled helper and localized. If its fetch fails the hotlink is kept with a WARN (it did not happen). Reverting is a one-block change in `prep_images`/the localize loop of `sync-cr.py`.
- **Commit:** 8ce3676

**4. [Rule 2 - Missing critical] Gated-slug and host coverage extras**
- Added `substack-video.s3` to the Substack-hosted image set and to the validator's forbidden-asset regex (podcast covers come from that bucket), and `contemplatingresonance.com` to the CR link hosts (the digest card in s3e4 points there).

## Remaining WARNs (all accounted for)

- `whats-resonating-this-week-1`: `native-video-embed` removed. It is a Substack-hosted video placeholder (`mediaUploadId`, no URL) with nothing to self-host or link to. Content genuinely lost from that one post.
- `whats-resonating-this-week-2`, `-4`, `whats-resonating-and-whats-to-come` (x2): links to `falkenslabyrinth.com/shop...` unwrapped to plain text (Substack-only shop pages have no new home).
- 15 informational "images.unsplash.com localized" lines (see deviation 3). No non-Substack image host was left hotlinked.
- No class-level WARNs remain after the Task 2 rules.
- No unknown-slug links (every in-publication `/p/<slug>` link resolved to a kept slug).

## Things to look at

- **Lede copy:** `content/cr/_index.md` `lede` is the verbatim Substack meta description, as instructed. It reads "...Click to read Falken's Labyrinth, a Substack publication with hundreds of subscribers." That is a Substack-flavored sentence on a page that is about leaving Substack; edit it by hand before cutover (the script never touches `_index.md`).
- **Repo weight:** `content/cr/` is about 53 MB (cover.jpg plus 88 inline images; covers are sometimes duplicated by an inline copy).
- **Podcast covers** come from the Substack video-transcode frame (`cover_image`), per the plan; `podcast_episode_image_url` (square art) is only the fallback.
- **Sitemap and home feed exposure:** once built, `/cr/` appears in `sitemap.xml` (52 occurrences) and the home feed `index.xml`. Harmless while unmerged; merge is cutover day per the FA precedent. `validate-cr.sh` reports it as INFO only. The opt-out, if ever wanted, is a cascaded front matter `sitemap: {disable: true}` in `content/cr/_index.md`.
- `tests/validate-cr.sh` is deliberately not in the deploy workflow; its pre-cutover block (unlinked /cr/) is meant to be deleted on cutover day.
- `media_url` is `""` on all 18 podcast pages; `media_file` holds the NAS filename (`<date>-<slug>.mp4`) for the Riverside/YouTube decision.

## Verification

- `bash tests/validate-cr.sh`: 12 passed, 0 failed (+2 INFO).
- `hugo --minify --quiet && bash tests/validate-fa.sh`: 13 passed, 0 failed (baseline unchanged).
- `python3 scripts/sync-cr.py --offline` after staging: tree byte-identical, 51 bundles.
- Nav header partial, home template, `content/_index.md`, `.github/workflows`: identical to the merge-base with origin/main. No session-cookie strings in the branch diff. `validate-cr` not referenced in workflows. Branch `cr/own-the-stack`, three commits ahead of origin/main, nothing merged or pushed, no PR.
- Headless Chrome screenshots of `/cr/`, a podcast page and a newsletter page looked right in the house style (Cinzel masthead, pending-player note box, figure and cover handling).

## Known Stubs

None. (`media_url: ""` is the documented pending-player state, not a stub.)

## Threat Flags

None beyond the plan's register. T-261115-fjc-01..07 mitigations are implemented and covered by `validate-cr.sh`.

## Self-Check: PASSED

- FOUND: scripts/sync-cr.py, data/cr-legacy.json, content/cr/_index.md, tests/validate-cr.sh, themes/arcaeon/layouts/cr/{single,list}.html, themes/arcaeon/layouts/cr/list.rss.xml, themes/arcaeon/layouts/partials/cr/{posts,masthead}.html
- FOUND commits: 8f007af, 8ce3676, 033291c (ancestors of HEAD on cr/own-the-stack)
- 51 bundle directories under content/cr/
