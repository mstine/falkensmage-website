---
phase: quick-261115-j4q
plan: 01
subsystem: cr-podcast-feed
tags: [hugo, rss, podcast, apple-podcasts, spotify, cloudflare-r2, own-the-stack]
status: complete
requires:
  - quick-261115-fjc (the /cr/ scaffold and scripts/sync-cr.py)
provides:
  - "https://falkensmage.com/cr/podcast.xml: Apple/Spotify podcast feed, 18 episodes, original Substack guids"
  - "data/cr-podcast.json: pinned guids, enclosure lengths, explicit and transcript flags"
  - "static/cr/podcast-cover.jpg: the show's original 1500x1500 Contemplating Resonance art"
affects:
  - scripts/sync-cr.py
  - tests/validate-cr.sh
  - hugo.toml
  - themes/arcaeon/layouts/cr/list.podcast.xml
key-files:
  created:
    - data/cr-podcast.json
    - static/cr/podcast-cover.jpg
    - themes/arcaeon/layouts/cr/list.podcast.xml
    - content/cr/<15 podcast slugs>/transcript.vtt
  modified:
    - scripts/sync-cr.py
    - tests/validate-cr.sh
    - hugo.toml
    - content/cr/_index.md
    - content/cr/<18 podcast slugs>/index.html
    - content/cr/{and-heres-your-weekend-update,whats-resonating-and-whats-to-come,episode-1-wtf-is-contemplating-resonance}/index.html
decisions:
  - "Every item keeps its Substack guid (substack:post:<id>, isPermaLink false), so repointing Apple Podcasts and Spotify duplicates nothing."
  - "No per-episode itunes:image: every item inherits the channel image (orchestrator amendment 1)."
  - "Channel art is the original 1500x1500 Canva export, installed by hand and final; sync-cr.py does not generate or overwrite it."
  - "Categories: Society & Culture > Philosophy first, plus Religion & Spirituality > Spirituality carried over from the Substack feed (one template line to delete for Philosophy only)."
  - "The no-substack.com rule is narrowed to Substack infrastructure and own-publication hosts; guests' own newsletters stay as outbound links."
metrics:
  tasks: 3
  commits: 4
  plan_head_before: 791f9e1a5f728c435083dc38ee0a69c0a9f87d20
  plan_head_after: fec134fcc05e0749da87108df8cc86b6bd054a0c
actuals:
  tokens: 60000
  tasks: 3
  commits: 4
completed: 2026-11-15
---

# Phase quick-261115-j4q Plan 01: Self-hosted Contemplating Resonance podcast feed Summary

A Hugo `podcast` output format emits https://falkensmage.com/cr/podcast.xml with 18 episodes carrying their original Substack guids and Cloudflare R2 enclosures, so Matt can repoint the Apple Podcasts and Spotify listings and delete the Substack without duplicating an episode.

## What was built

- **Generator (scripts/sync-cr.py):** reads the saved Substack feed facts (`~/.psyche/tools/substack/cr-feed-assets/items.json`, local files only, so `--offline` still makes 0 live requests), validates every entry, and writes `podcast_guid`, `audio_url`, `audio_bytes`, `explicit` and (for 15 episodes) `transcript` into the 18 podcast bundles. It pins guids, lengths and flags in `data/cr-podcast.json` and fails on an unpinned or orphaned episode. Enclosure lengths are cross-checked against the NAS copies when mounted.
- **Hugo wiring:** `[outputFormats.podcast]` in hugo.toml; only `content/cr/_index.md` opts in (`outputs: ["html", "rss", "podcast"]`). The build emits exactly one podcast.xml. `/cr/index.xml` is unchanged.
- **Feed template (themes/arcaeon/layouts/cr/list.podcast.xml):** full channel metadata (owner Matt Stine / falkensmage@falkenslabyrinth.com, copyright, explicit, episodic, categories, self-hosted itunes:image), and per item: guid, pubDate, enclosure (audio/mpeg, pinned length), duration, explicit, show notes in CDATA for description and content:encoded (CDATA terminator defused), and podcast:transcript (text/vtt). The template calls `errorf` for any podcast page lacking a guid or audio URL, so a guid-less item can never ship.
- **Own-publication links:** `contemplatingresonance.substack.com` added to the own hosts, so 7 links in 3 bundles now point at `/cr/<slug>/`, including the episode-1 show notes that land in the feed. A link whose visible text was the old URL now shows the new falkensmage.com address.
- **Gate (tests/validate-cr.sh, block k):** k1-k12 as planned, with the amendments applied (k9 requires a square JPEG of 1400-3000 px; k10 asserts that no item carries its own itunes:image). k13 is an INFO-only R2 HEAD probe (`VALIDATE_CR_NO_NET=1` skips it). A sentinel makes the gate fail if the Python pass crashes before finishing.

## Results

- `python3 scripts/sync-cr.py --offline`: 51/51 posts, 18 podcasts, 0 live requests; a rerun leaves `content/cr`, `data` and `static/cr` byte-identical.
- R2 probe (k13): `18/18 enclosures answered 200, 18/18 with the pinned Content-Length`. All 18 mp3s are live.
- NAS cross-check: 18/18 enclosure lengths match the NAS copies.
- `xmllint --noout` accepts podcast.xml. `bash tests/validate-cr.sh`: 24 passed, 0 failed (12 original plus k1-k12; k13 is INFO). `bash tests/validate-fa.sh`: 13 passed, 0 failed.
- `/cr/index.xml` token-diffed against the pre-plan build: 0 differences. `.github`, `themes/arcaeon/layouts/_default` and `themes/arcaeon/layouts/partials` are untouched. No nav, head alternate link or workflow wiring.

## Deviations from Plan

### Orchestrator amendments applied

1. **Artwork:** no show.jpg copy, no per-episode itunes:image, no podcast-art files. Reasons: 14 of 18 are the retired Falken's Labyrinth logo, s3e4's is a playlist collage, and the rest are under Apple's 1400 px minimum or non-square. The `podcast_art` front matter key and the art copy step were dropped, and gate check k10's undersized-art INFO line was replaced with a no-per-episode-art assertion.
2. **Channel image:** the plan asked for the 720 px art upscaled to 1400 px as a placeholder (commit 3ed3f13). A later amendment supplied the original `cr-podcast-cover-1500.jpg` (1500x1500 RGB JPEG, Canva export), now installed as `static/cr/podcast-cover.jpg` in commit 205171a. **It is final art, not a placeholder.** The generator does not touch it, so no later step needs to replace it. k9 checks it is a square JPEG between 1400 and 3000 px.
3. **R2:** the upload was already complete, so the k13 probe runs in full (18/18).
4. **Categories:** kept as planned: Philosophy primary, plus Religion & Spirituality > Spirituality carried over from the Substack feed. To publish Philosophy only, delete the one `itunes:category` line for Religion & Spirituality in list.podcast.xml.

### Auto-fixed issues

**1. [Rule 1 - Bug] k7 matched the word "podcast" in index.xml body text**
- **Found during:** Task 1
- **Fix:** match only `xmlns:itunes|xmlns:podcast` and `<itunes:` / `<podcast:` markup.
- **Commit:** cf0fb1c

**2. [Rule 1 - Bug] A link with the old own-publication URL as its visible text kept that text after the href was rewritten**
- **Found during:** Task 2 (the plan's `! grep contemplatingresonance.substack.com content/cr` verify failed on one link text)
- **Fix:** in sync-cr.py, when the anchor text equals the old href and the link is rewritten to `/cr/...`, the text becomes the new falkensmage.com URL. No other bundle changed.
- **Commit:** 3ed3f13

**3. [Rule 1 - Bug] Gate crash passed silently**
- **Found during:** Task 2 (a loop variable shadowed the feed path; the Python pass crashed and bash saw no problem lines)
- **Fix:** renamed the variable, and added a DONE sentinel so a crashed Python pass fails the gate.
- **Commit:** 3ed3f13

**4. [Rule 3 - Blocking] macOS bash 3.2 mis-parses odd quote characters inside `$( ... <<'PY' )` heredocs**
- **Fix:** the root-relative regex uses `\x22` and `\x27` escapes instead of literal quote characters.
- **Commit:** 3ed3f13

## Notes for Matt

- The "no substack.com URLs" rule is narrowed to Substack infrastructure and own-publication hosts. The feed links 6 distinct guest `<name>.substack.com` newsletters from show notes (outbound links; k12 reports the count as INFO).
- Not added, as fenced: itunes:new-feed-url (belongs in the old Substack feed), podcast:locked, any link or nav to the feed, any workflow wiring. validate-cr.sh remains out of CI until cutover.
- Repointing Apple Podcasts Connect and Spotify for Creators to the new feed is Matt's manual step, after the branch ships. The R2 audio is already live.

## Known Stubs

None.

## Threat Flags

None. The only new public surface is the feed itself and its published owner email (falkensmage@falkenslabyrinth.com), both planned in the threat model (T-j4q-03).

## Commits

- cf0fb1c feat(cr): podcast feed at /cr/podcast.xml with pinned Substack guids and R2 enclosures
- 3ed3f13 feat(cr): complete podcast feed metadata, transcripts, show notes and channel art
- 205171a feat(cr): install the original 1500x1500 Contemplating Resonance cover as the podcast channel art
- fec134f test(cr): INFO-only R2 probe for podcast enclosures (k13)

Nothing pushed, merged or opened as a PR. Branch: cr/own-the-stack.

## Self-Check: PASSED

- FOUND: data/cr-podcast.json, static/cr/podcast-cover.jpg (1500x1500 JPEG), themes/arcaeon/layouts/cr/list.podcast.xml, 15 transcript.vtt files
- FOUND commits: cf0fb1c, 3ed3f13, 205171a, fec134f (all ancestors of HEAD)
