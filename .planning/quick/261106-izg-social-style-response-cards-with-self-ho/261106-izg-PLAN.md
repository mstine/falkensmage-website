---
phase: quick-261106-izg
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/pull-webmentions.py
  - tests/test-pull-webmentions.py
  - tests/validate-fa.sh
  - themes/arcaeon/layouts/partials/fa/mentions.html
  - themes/arcaeon/assets/css/main.css
  - tests/test-notes.py
  - .github/workflows/hugo.yml
  - .gitignore
autonomous: true
requirements:
  - QUICK-261106-izg

estimate:
  tokens: 150000
  raw_tokens: 150000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "A response whose author has a photo shows it as a round avatar served from falkensmage.com at /webmention-avatars/<32 hex>.<png|jpg|webp|gif>; the remote photo URL never appears in data/webmentions.json or in any built page"
    - "An avatar is accepted only if its first bytes identify PNG, JPEG, WebP or GIF and it is at most 204800 bytes. It is fetched over https only, with no redirects, one 5-second attempt, a 45-second total budget per run, and no Authorization header. Any failure means that author shows their initial on a violet circle; the build continues and the exit code is what it would have been without avatars"
    - "A blocked author's photo is never fetched. Every run deletes any avatar file the written data file does not reference, including runs with no token and runs during a webmention.io outage"
    - "Avatars persist between builds in their own Actions cache entry (webmention-avatars-*), restored before the pull and saved only when the pull succeeded; the existing webmentions-data cache steps are byte-identical; static/webmention-avatars/ is gitignored and no avatar is committed"
    - "A response whose wm-source is https://brid.gy/<kind>/mastodon/@<user>@<instance>/<status-id>/... links its timestamp and platform indicator to https://<instance>/@<user>/<status-id>; the author name links to author.url; Bluesky bsky.app URLs and ordinary webmentions keep their URL"
    - "Each reply renders as a card matching the note card: a round avatar or initial, the name, a handle or domain, the date, the text, and a Mastodon or Bluesky indicator linking to the conversation. Likes and reposts render as a row of overlapping round avatars plus a count, and each face's link has the accessible name 'Liked by <name>' or 'Reposted by <name>'"
    - "tests/validate-fa.sh goes red when the Responses section holds an image whose src is not a /webmention-avatars/ file present in the build, and stays green for real self-hosted avatars"
    - "No JS, no external font or CDN, nothing that animates, and WCAG AA contrast. Nothing scrolls horizontally at 375px. A 375px-wide screenshot of the Lovers note's Responses section exists in the quick directory. Nothing is pushed"
  artifacts:
    - path: "scripts/pull-webmentions.py"
      provides: "AVATAR_* constants, FIELDS, avatar_name, sniff_image, avatar_source_ok, fetch_avatar, attach_avatars, keep_present_avatars, prune_avatars, derive, derive_all, assemble, restore; normalize(children, photos=None); write_data as the privacy boundary; the rewritten docstring"
      contains: "Why avatars are self-hosted, never hotlinked"
    - path: "themes/arcaeon/layouts/partials/fa/mentions.html"
      provides: "face rows for likes and reposts, reply cards, the unchanged Mentioned-by row, h2 id=responses"
      contains: "fa-reply__header"
    - path: "themes/arcaeon/assets/css/main.css"
      provides: "fa-avatar, fa-face, fa-reactions, fa-reply styles in the Responses block"
      contains: ".fa-face"
    - path: "tests/validate-fa.sh"
      provides: "the self-hosted-image rule and the avatar-file-exists check in the Webmention probe"
      contains: "webmention-avatars"
    - path: "tests/test-pull-webmentions.py"
      provides: "setUpModule network and filesystem guard, build_site(avatars_dir=...), AvatarTracer, Avatars, Derive, RestorePath, WritePrivacy, AvatarWorkflow"
      contains: "class AvatarTracer"
    - path: ".github/workflows/hugo.yml"
      provides: "restore and save steps for the avatar cache entry"
      contains: "static/webmention-avatars"
    - path: ".gitignore"
      provides: "static/webmention-avatars/ excluded"
      contains: "static/webmention-avatars/"
    - path: ".planning/quick/261106-izg-social-style-response-cards-with-self-ho/responses-375.png"
      provides: "the review-gate screenshot the orchestrator shows Matt"
  key_links:
    - from: "scripts/pull-webmentions.py main"
      to: "assemble / restore -> write_data -> prune_avatars"
      via: "restore runs before any network call; assemble runs after a successful pull; prune_avatars takes the pages write_data returned"
      pattern: "prune_avatars"
    - from: "scripts/pull-webmentions.py write_data"
      to: "AVATAR_RE"
      via: "every record is filtered to FIELDS and an avatar that does not fullmatch AVATAR_RE is dropped before the file is written"
      pattern: "AVATAR_RE"
    - from: "themes/arcaeon/layouts/partials/fa/mentions.html"
      to: "data/webmentions.json avatar field"
      via: "img src is the record's site-relative avatar path, output with plain double braces, no safe-marking pipe"
      pattern: "\\.avatar"
    - from: "tests/validate-fa.sh Webmention probe"
      to: "public/webmention-avatars/"
      via: "every img src inside the section must fullmatch the avatar pattern and name a file that exists in the built output"
      pattern: "webmention-avatars"
    - from: ".github/workflows/hugo.yml build job"
      to: "Pull Webmentions step"
      via: "restore webmention-avatars-* before it; save after it only if steps.mentions.outcome == 'success'"
      pattern: "webmention-avatars-"
---

<objective>
Turn the Responses section under FA essays and notes into social-style cards, using avatars the site hosts itself. Also fix reply links that point at ActivityPub JSON.

Locked by Matt (2026-11-06): "Self-hosted avatars plus card layout." The site must never make a reader's browser contact a third-party host. Today that is guaranteed by copying no image URL at all. After this change it is guaranteed differently: the build downloads each author photo once, serves it from falkensmage.com, and the data file and HTML only ever hold that local path.

Purpose: the Lovers note got its first real responses through Bridgy (a like and a reply from Mastodon). They render as "LIKED BY <name>" and a bare name link. That link opens a JSON document, because webmention.io reports the reply's ActivityPub id as its URL. The note card above has a social-post look, and the responses beneath it should match.

Output:
- Avatar download, cache, limits and pruning, the Bridgy conversation links, and the derived card fields (handle, initial, platform) in scripts/pull-webmentions.py, with its docstring rewritten.
- The card template and its CSS.
- The probe rule for self-hosted images in tests/validate-fa.sh.
- The avatar cache pair in .github/workflows/hugo.yml, and the .gitignore entry.
- Tests for all of the above.
- A 375px review screenshot in the quick directory.
- Three local commits. Nothing is pushed.

Source coverage (every item from the brief has a home):

| Brief item | Where |
|---|---|
| 1. Download avatars at build, store under a hash name, record only the local path | Task 1 (tracer), Task 2 (dedupe, reuse) |
| 1. About 200 KB cap, PNG/JPEG/WebP/GIF by magic bytes, short timeout, stdlib, failure means no avatar and the build continues | Task 1 (sniff, cap, timeout), Task 2 (budget, rejection tests) |
| 1. Privacy invariant holds and stays tested | Task 1 (write_data boundary, probe, AvatarTracer), Task 2 (WritePrivacy) |
| 1. Persistence across builds; no committed binaries | Task 2 (cache pair, .gitignore, restore path) |
| 1. Blocked authors get no avatar download | Task 2 (Avatars, RestorePath) |
| 1. Docstring "Why names only" rewritten | Task 2 |
| 2. Bridgy-Mastodon conversation links; name links to author.url; Bluesky and plain webmentions unchanged; mapping in the script | Task 2 (derive), Task 3 (template links) |
| 3. Cards: avatar, name, handle or domain, date, text, platform indicator; face rows with counts and accessible names; initial fallback; 375px, AA, no JS or CDN, reduced motion; microformat semantics kept | Task 3 |
| Review gate: fixture build, 375px screenshot of the Lovers note's Responses, local commits only | Task 3 |
| Out of scope: notes.yml, syndicate-notes.py, any new data source | Not touched (verification checks the diff) |
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@scripts/pull-webmentions.py
@tests/test-pull-webmentions.py
@themes/arcaeon/layouts/partials/fa/mentions.html
@themes/arcaeon/layouts/partials/notes/entry.html
@tests/validate-fa.sh
@.github/workflows/hugo.yml
@data/webmention-blocklist.json

In themes/arcaeon/assets/css/main.css, read only the note card block (search for `.note {` through `.note__icon`), `.fa-prose img`, and the block that starts with the comment `/* Responses under an essay` and ends before `/* Compact masthead`. The file is 2504 lines, so do not read all of it.

## Facts the planner verified (do not re-derive)

- **Baseline.** Run `hugo --minify`, then `for f in tests/test-*.py; do python3 -I -S -B "$f" || exit 1; done`. At HEAD (1ab0ecb) all five suites pass in about 87 s. Local Python is 3.10.0, so the script must stay 3.10-compatible and stdlib-only. Hugo is v0.160.1+extended at /opt/homebrew/bin/hugo. `python3 -I -S -B <file> -k <Name>` filters by substring, and `-k` can be repeated.
- **Real Lovers data**, from the public per-target endpoint (no token):
  - The like: wm-source `https://brid.gy/like/mastodon/@falkensmage@mastodon.social/117570501730802441/115539496341770518`, url `https://mastodon.social/@falkensmage/117570501730802441#favorited-by-115539496341770518`.
  - The reply: wm-source `https://brid.gy/comment/mastodon/@falkensmage@mastodon.social/117570501730802441/117570690950774654`, url `https://mysticmikester.com/.ghost/activitypub/note/314ca2f2-8d73-434e-b04c-0e33f23e2bbe` (this URL serves JSON), author.url `https://mysticmikester.com/`.
  - The photo for both: `https://avatars.webmention.io/files.mastodon.social/<hex>.png`. It answers 200 with image/png, 6770 bytes, no redirect.
  - So: the `@` in the Bridgy path is literal (not percent-encoded), status ids are numeric, and webmention.io serves author photos from its own avatars host with no redirect. A no-redirect fetch policy costs nothing on real data.
- **Trap: network and repo writes in tests.** The test fixtures carry author photo URLs: 19 children in example-mentions.jf2.json (https://webmention.io/img/example/*.svg) and one PHOTOSENTINEL in hostile-mentions.jf2.json. Once main() downloads avatars, every test that runs main() would reach the real network and write into the repo's static/. The guard in Task 1 (setUpModule) is mandatory.
- **Trap: `.fa-prose img`** (main.css, around line 2014) sets `display:block; width:100%; height:auto; border-radius:0.5rem`. The section's container carries `fa-prose`, so avatar rules must out-specify it, for example `.fa-mentions .fa-avatar`.
- **Trap: the probe counts kinds by class token.** validate-fa.sh counts the elements carrying `fa-mention--like`, `fa-mention--repost`, `fa-mention--mention` or `fa-mention--reply`, and compares each count with the data. Put each kind class on exactly one element per record. New classes use other blocks (`fa-face`, `fa-reply__*`, `fa-avatar`, `fa-reactions*`) so they can never match.
- **Trap: the escape-bypass mutation test** (`test_a_real_escape_bypass_in_the_template_turns_the_probe_red`) rewrites `\{\{\s*(\$[pr]\.(?:name|text))\s*\}\}` and needs at least 3 hits. Keep `$p` as the range variable for likes, reposts and mentions and `$r` for replies, and output with plain `{{ $p.name }}`, `{{ $r.name }}` and `{{ $r.text }}`.
- **Trap: template functions on stranger data.** The partial's header comment explains that no template function that can fail on a stranger's value may be called on mention data. `default`, `eq`, `len` and `cond` cannot fail on these values. Do not call urls.Parse, substr, printf or anything similar on mention data. That is why handle, initial and platform are computed in Python.
- **Trap: the cache version hash.** actions/cache computes an entry's version from its path list. Adding a path to the existing `data/webmentions.json` restore and save steps would orphan the current last-good entry. Avatars therefore get their own restore and save pair, and the data steps stay byte-identical.
- **Trap: test-notes.py pins mention markup.** In ProbeMutations.test_baselines_are_green it asserts `html.count("fa-mentions__row") == 3` (likes row, mentions row, Replies label) and `html.count("fa-mention--reply") == 1`. test_mentions_sit_after_the_entry_and_outside_it asserts `html[a:b].count('rel="nofollow ugc"') == 3`. Its MENTIONS fixture is written directly (no derived fields): 1 like, 1 mention, and 1 reply with no platform and no author_url.
- **Trap: `LAST_GOOD` equality.** About ten tests in test-pull-webmentions.py assert `self.disk()["pages"] == LAST_GOOD` after main() runs. Once derive runs on the restore path, those records gain handle, initial and platform. derive is idempotent, so Task 2 rewrites `LAST_GOOD` in its derived form: Ada becomes handle "ada.example", initial "A", platform "". Bo becomes handle "bo.example", initial "B", platform "". A pre-derived cache then round-trips unchanged.
- **Icons.** icons/like.html, repost.html, reply.html, mastodon.html and bluesky.html are `<svg>` plus `<path>` only. like and repost already carry aria-hidden; mastodon and bluesky do not, so wrap them in `<span aria-hidden="true">` the way note__copy does.
- **Microformats.** The section deliberately sits outside the h-entry and carries no microformat classes. Keep it that way: no h-card, u-photo, p-name or h-cite in the section. Top-level mf2 items there would be read by Bridgy and by the notes probe.
- **Browser.** Neither chromium nor google-chrome is on PATH. Google Chrome is at /Applications/Google Chrome.app (binary: /Applications/Google Chrome.app/Contents/MacOS/Google Chrome). The site's CSS link uses .RelPermalink.
- **Grep baselines at HEAD.**
  - "webmention-avatars": 0 hits in scripts/pull-webmentions.py, .github/workflows/hugo.yml, .gitignore, tests/validate-fa.sh, mentions.html and main.css.
  - "Why avatars are self-hosted": 0.
  - "fa-face" and "fa-reply": 0 in main.css and mentions.html.
  - The old docstring sentence that opens "No avatar or photo URL is ever copied": 1 in scripts/pull-webmentions.py.

## Design decisions (planner, each with its reason)

- **R1. Avatars live in static/webmention-avatars/, not assets/.** Hugo copies static bytes without decoding them. Hugo image processing on a stranger's file could fail the build, which would let a stranger block a deploy. Files are named `<sha256(photo_url)[:32]>.<ext>`, with the extension taken from the sniff. They are served at `/webmention-avatars/<name>`.
- **R2. A remote photo URL never enters `pages`.** `normalize(children, photos=None)` records each kept record's photo in a side dict keyed `(path, kind, source)`. `write_data` is the privacy boundary. Every record is filtered to FIELDS (`name, url, source, author_url, text, date, date_text, avatar, handle, initial, platform`). An `avatar` that does not fullmatch AVATAR_RE is dropped, and so is a `platform` outside {"", "mastodon", "bluesky"}. write_data returns the sanitized pages it wrote.
- **R3. Derived fields are computed by `derive(rec)`** and applied to fresh records and to last-good records alike. The function is idempotent. A cache written before this change is therefore upgraded on the next run (JSON links fixed, initials present), even with no token.
- **R4. The Bridgy mapping applies to every kind** whose wm-source matches, likes included. It lives in the pull script, where it is tested.
- **R5. The restore path drops dangling avatars.** It removes any avatar field whose file is missing or fails revalidation, so if the data cache and the avatar cache ever disagree, the page shows an initial rather than a broken image.
- **R6. Fetch policy.**
  - Only https, with a hostname that contains a dot. IP literals and localhost are rejected.
  - No redirects (OPENER has no redirect handler) and no proxy.
  - One attempt, with a 5 s timeout, reading at most AVATAR_MAX_BYTES + 1 bytes.
  - A 45 s total download budget per run. Reusing a cached file costs no budget.
  - The request carries only User-Agent and an image-only Accept header, never Authorization.
  - A DNS name that resolves to a private address is accepted as residual risk (T-05).
- **R7. The "Mentioned by" row is unchanged.** Mentions are posts on other sites, not reactions from people. This is an explicit opt-out.
- **R8. The fallback initial** is `--color-text` (#fff4e6) on `--color-accent` (#7a2cff), a contrast of 5.3:1, which passes AA. The existing rule "violet is never text" holds, because violet is the fill.
- **R9. Faces are 2rem with a -0.5rem overlap.** That leaves 1.5rem (24px) of each target exposed, which meets WCAG 2.2 SC 2.5.8 (AA).
</context>

<tasks>

<task type="tracer">
  <name>Task 1: One reply with an avatar, end to end: stub photo -> pull script -> data file -> Hugo page -> probe</name>
  <files>scripts/pull-webmentions.py, themes/arcaeon/layouts/partials/fa/mentions.html, tests/validate-fa.sh, tests/test-pull-webmentions.py</files>
  <action>
Wire the thinnest real path: a reply whose author has a photo ends up with a self-hosted avatar on the built page, and the probe accepts it. This implements the locked "self-hosted avatars" decision.

**scripts/pull-webmentions.py**

1. Add these constants:
   - `AVATAR_DIR = ROOT / "static" / "webmention-avatars"`
   - `AVATAR_PREFIX = "/webmention-avatars/"`
   - `AVATAR_RE`, compiled from `/webmention-avatars/[0-9a-f]{32}\.(?:png|jpg|webp|gif)` and used with fullmatch
   - `AVATAR_MAX_BYTES = 200 * 1024`, `AVATAR_TIMEOUT = 5`, `AVATAR_BUDGET = 45`
   - a `FIELDS` tuple per R2
   - `AVATAR_ACCEPT = "image/png, image/jpeg, image/webp, image/gif"`
2. Add `avatar_name(url)`, which returns the first 32 hex characters of the sha256 of the UTF-8 URL.
3. Add `sniff_image(data)`, which returns the extension from magic bytes or None:
   - "png" for `\x89PNG\r\n\x1a\n`
   - "jpg" for `\xff\xd8\xff`
   - "gif" for `GIF87a` or `GIF89a`
   - "webp" for bytes 0-3 `RIFF` with bytes 8-11 `WEBP`
   - anything else, including SVG and HTML, returns None
4. Add `avatar_source_ok(url)`, implementing the R6 policy. It returns False for anything that fails clean_url, any non-https scheme, a host without a dot, an IP-literal host (use the ipaddress module on the bracket-stripped host), and localhost.
5. Add `fetch_avatar(url)`, which returns bytes or None:
   - Use the existing OPENER (no redirect handler, no proxy).
   - Build a fresh Request whose headers are only User-Agent (UA) and Accept (AVATAR_ACCEPT).
   - Use `timeout=AVATAR_TIMEOUT` and read at most AVATAR_MAX_BYTES + 1 bytes. A larger body means None.
   - Catch HTTPError (closing it), URLError, TimeoutError, OSError, http.client.HTTPException and ValueError, and return None. One attempt, no retry.
6. Add `attach_avatars(pages, photos, avatar_dir)`:
   - mkdir avatar_dir (parents, exist_ok).
   - For each record in every page and kind, look up `photos.get((path, kind, rec["source"]))`.
   - Resolve each distinct photo URL once, memoized. If `avatar_source_ok(url)` is False, the URL resolves to no avatar. Otherwise fetch, sniff, and write the bytes atomically (tempfile.mkstemp in avatar_dir with prefix `.avatar-` and suffix `.tmp`, then os.replace) to `avatar_name(url) + "." + ext`.
   - Set `rec["avatar"] = AVATAR_PREFIX + filename` on every record that resolved.
   - Look up `avatar_source_ok` and `fetch_avatar` as module globals at call time (no default-argument capture), so tests can patch them.
   - Return a small counts dict: shown, fetched, unavailable.
7. Change the signature to `normalize(children, photos=None)`. When `photos` is a dict, record `photos[(path, kind, source)] = clean_url(author.get("photo"))` for each kept record whose photo is non-empty. The record itself never holds the photo URL. A non-string or list photo yields an empty string and is skipped.
8. Make write_data the privacy boundary per R2, and have it return the sanitized pages. Extend `_OPTIONAL` in load_last_good with avatar, handle, initial and platform, each validated as a string.
9. Wire the fresh path in main:
   - Create the photos dict and pass it to normalize.
   - Run apply_blocklist next. Blocked records are gone before any photo is fetched.
   - Run attach_avatars with AVATAR_DIR, then write_data.
   - Print one extra log line holding counts only, for example `avatars: N shown, N fetched, N unavailable`. Never print a URL, host or file name.
   - Avatar outcomes never change the exit code.

**themes/arcaeon/layouts/partials/fa/mentions.html.** Inside the reply `li`, before the name link, render `<img class="fa-avatar" src="{{ $r.avatar }}" alt="" width="40" height="40" loading="lazy" decoding="async">` under `{{ if $r.avatar }}`. Use plain double braces with no pipe; html/template's URL filter accepts a site-relative path. Rewrite rule 3 of the header comment: images are self-hosted only, every img src is a /webmention-avatars/ path the pull script wrote after sniffing the bytes, and no remote URL is ever in the data file, so no reader's browser contacts a stranger's host.

**tests/validate-fa.sh (Webmention probe).**
- Add img, svg and path to ALLOWED. The svg and path entries are for the first-party icons in Task 3.
- Keep banning `on*`, style and srcset attributes on every element. Allow src only on img.
- For each img in the section:
  - Its src must fullmatch `/webmention-avatars/[0-9a-f]{32}\.(png|jpg|webp|gif)`. Otherwise add the problem "it holds an image that is not self-hosted".
  - The file at public plus that path must exist. Otherwise add "it shows an avatar that is not in the build".
  - It must carry an alt attribute; present but empty is fine.
- Update the header comment line about inert markup to say the section may show only self-hosted avatar images.

**tests/test-pull-webmentions.py**

1. Capture `REAL_SOURCE_OK = m.avatar_source_ok` at import. Add setUpModule/tearDownModule that patch `m.AVATAR_DIR` to a module temp dir and `m.avatar_source_ok` to accept only URLs starting `http://127.0.0.1:`. Then no test can reach the network for a fixture photo or write into the repo's static/.
2. In PullCase.setUp, also patch `m.AVATAR_DIR` to `self.tmp / "avatars"`.
3. Give build_site an `avatars_dir=None` parameter. When it is set, add two mounts: the repo's static/ targeting "static" with `files = ["! webmention-avatars/**"]`, and avatars_dir targeting "static/webmention-avatars".
4. Widen the regex in test_a_real_escape_bypass_in_the_template_turns_the_probe_red so that the new "not self-hosted" message also satisfies it, and confirm the test still goes red for the bypass.
5. Add class AvatarTracer:
   - Serve a feed holding one in-reply-to child (target ESSAY, author.photo = stub.base + "/a.png"). Serve `/a.png` with PNG magic plus filler bytes and Content-Type text/plain, which proves the type comes from the bytes and not the header.
   - Run main with the token and a class temp AVATAR_DIR.
   - Assert: rc is 0. The record's avatar fullmatches AVATAR_RE and ends ".png". The file holds exactly the served bytes. The raw data file contains neither stub.base nor "/a.png". The image request carried no authorization header.
   - Build with avatars_dir. The section holds exactly one img, whose src equals the record's avatar, and the file exists under the built public at that path. run_probe is green.
   - Three mutations of the built page each turn the probe red and name the page path: src replaced with an https tracker URL, src replaced with `/images/x.png`, and the built avatar file deleted.
  </action>
  <verify>
    <automated>python3 -I -S -B tests/test-pull-webmentions.py -k AvatarTracer && python3 -I -S -B tests/test-pull-webmentions.py</automated>
  </verify>
  <done>
    - A reply author's photo is downloaded once into the avatar dir and recorded as a /webmention-avatars/ path.
    - The data file and the built page never hold the remote URL.
    - The probe accepts the self-hosted image and goes red for a remote image, an image outside the avatar dir, and a missing avatar file.
    - Every existing test in the file still passes with no outbound network.
    - Committed locally as `feat(webmentions): self-host reply avatars, end to end`, ending with the Co-Authored-By line.
  </done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Avatar cache, limits and pruning; Bridgy conversation links; derived card fields; docstring, workflow and gitignore</name>
  <files>scripts/pull-webmentions.py, tests/test-pull-webmentions.py, .github/workflows/hugo.yml, .gitignore</files>
  <behavior>
    - Avatars: two records sharing one photo URL make one request and get the same avatar.
    - Avatars: a valid cached file for the URL's hash makes zero requests and is reused. A cached file whose bytes do not sniff as an image, or whose extension disagrees with the sniff, is deleted and fetched again.
    - Avatars: each of these leaves no avatar, no file and rc 0: SVG bytes; HTML bytes; AVATAR_MAX_BYTES + 1 bytes; a 404; a 500; a 301 to a valid image (exactly one request, the redirect is not followed); a route slower than a patched AVATAR_TIMEOUT of 0.2 s.
    - Avatars: PNG bytes served as text/html are saved as .png, and GIF bytes served as image/png are saved as .gif.
    - Avatars: with AVATAR_BUDGET patched to 0, no image is requested, no avatars are set, and rc is 0.
    - Avatars: an author on a blocklisted domain gets zero requests to their photo route.
    - Avatars: no image request carries an authorization header, and the token appears in no request path. Stdout lines all start "pull-webmentions:" and contain no photo URL, host or avatar file name.
    - Avatars: REAL_SOURCE_OK accepts https://avatars.webmention.io/files.mastodon.social/x.png. It rejects http://, https://127.0.0.1/, https://[::1]/, https://localhost/, https://intranet/, a javascript: URL, a list and None.
    - Derive: the real Lovers reply shape gets url https://mastodon.social/@falkensmage/117570501730802441 and platform "mastodon". The like shape maps to the same conversation URL. author_url is untouched.
    - Derive: a Bluesky Bridgy source (https://brid.gy/comment/bluesky/...) with a bsky.app url keeps its url and gets platform "bluesky". An ordinary webmention keeps its url and gets platform "".
    - Derive: none of these lookalikes is mapped: host brid.gy.evil.example; an instance with no dot; a status id that is not numeric; `..` or extra characters in the user part.
    - Derive: handle. https://mastodon.social/@rowan gives "@rowan@mastodon.social". https://bsky.app/profile/wren.example gives "@wren.example". https://www.rowanvale.example/ gives "rowanvale.example". No author_url falls back to the url's host without "www.". A handle equal to the name becomes "".
    - Derive: initial. "rowan" gives "R". "🌙 Luna" gives "L". A name with no alphanumeric character falls back to the handle's first alphanumeric character, uppercased, and then to "•".
    - Derive: derive(derive(r)) == derive(r).
    - RestorePath: a token-absent run over an underived last-good record (brid.gy Mastodon source, Ghost JSON url) writes the mapped url, the platform and the initial.
    - RestorePath: an avatar referenced by last-good whose file exists and is valid survives a token-absent run and a 503 outage, keeping both the file and the field.
    - RestorePath: a referenced avatar whose file is missing loses its field. A referenced file that is not an image is deleted and loses its field.
    - RestorePath: an unreferenced file and a leftover `.avatar-x.tmp` are deleted.
    - RestorePath: a new blocklist entry deletes that author's avatar file on a token-absent run.
    - WritePrivacy: write_data drops unknown keys (`photo`, `_photo`, `extra`). It drops avatars of `https://x.example/a.png`, `//x.example/a.png`, `/webmention-avatars/../a.png` and an uppercase-hex name. It drops platform "myspace".
    - WritePrivacy: the hostile fixture plus one stub-served photo, through main, writes a file whose text contains neither PHOTOSENTINEL nor stub.base, and every avatar in it fullmatches AVATAR_RE.
    - AvatarWorkflow: in the build job of hugo.yml, a step restoring path static/webmention-avatars with restore-keys webmention-avatars- comes before "Pull Webmentions". A save step for that path, with `if: steps.mentions.outcome == 'success'`, comes after it. The data cache steps still use exactly path data/webmentions.json and prefix webmentions-data-. .gitignore has the line static/webmention-avatars/.
  </behavior>
  <action>
Write the tests above first, in new classes Avatars, Derive, RestorePath, WritePrivacy and AvatarWorkflow (Avatars and RestorePath extend PullCase). Run them and watch them fail. Then implement:

**scripts/pull-webmentions.py**

1. **Cache reuse.** In attach_avatars, after avatar_source_ok passes, check whether a valid cached file exists for `avatar_name(url)` with any of the four extensions. Valid means the size is at most AVATAR_MAX_BYTES, the bytes sniff as an image, and the sniff equals the extension. Reuse a valid file without network and without charging the budget. Delete an invalid one.
2. **Budget.** Track the time spent downloading with time.monotonic. Once AVATAR_BUDGET is spent, unresolved URLs get no avatar.
3. **Wrap each URL's resolution in `except Exception`** so that a stranger's bytes can never crash the run. Count the URL as unavailable.
4. **Add `keep_present_avatars(pages, avatar_dir)`.** Drop the avatar field from any record whose avatar fails AVATAR_RE, whose file is missing, or whose file fails the validity check above. Delete an invalid file.
5. **Add `prune_avatars(avatar_dir, pages)`.** Delete every regular file in avatar_dir that the given pages do not reference, including `.avatar-*.tmp` leftovers. Pass it the pages that write_data returned.
6. **Add `derive(rec)`, which mutates the record and returns it:**
   - **url.** If `source` matches `^https://brid\.gy/[a-z]+/mastodon/@([A-Za-z0-9_]+)@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+)/([0-9]+)(?:/|$)`, set url to `https://<instance lowercased>/@<user>/<status-id>`, passed through clean_url. This fixes reply links that point at ActivityPub JSON.
   - **platform.** "mastodon" or "bluesky" when source matches `^https://brid\.gy/[a-z]+/(mastodon|bluesky)/`; otherwise "bluesky" when the url's host is bsky.app; otherwise "".
   - **handle.** From author_url, following the behavior cases above. Fall back to the url's host. Pass it through clean_text with NAME_CHARS. Set it to "" when it equals the name.
   - **initial.** Following the behavior cases. Take the first character of `.upper()`.
   - Add `derive_all(pages)`, which applies derive to every record.
7. **Add `restore(pages, blocklist, avatar_dir)`** for the pre-network path: apply_blocklist, then derive_all, then keep_present_avatars. Return the pages.
8. **Add `assemble(children, blocklist, avatar_dir)`** for the fresh path: normalize with photos, apply_blocklist, derive_all, attach_avatars. Return (pages, counts, blocked, avatar_counts).
9. **Rewire main.**
   - The pre-network rewrite becomes: load_last_good, restore, write_data, prune_avatars over the returned pages. Make sure AVATAR_DIR exists on this path too, so the cache save step never meets a missing path.
   - After a successful pull, the fresh path becomes: assemble, write_data, prune_avatars, then the log lines.
   - The malformed-blocklist path still touches nothing.
10. **Update the docstring.**
    - Replace the section headed "Why names only" with a section headed exactly "Why avatars are self-hosted, never hotlinked". Cover:
      - The rule: each distinct author photo is downloaded once at build into static/webmention-avatars/, the data file holds only that site-relative path, and so no template can hotlink and no reader's IP reaches a stranger's host.
      - The limits from R6 and the sniffed types (never SVG).
      - Why static/ and not assets/ (R1).
      - That blocked authors are never fetched and unreferenced files are pruned on every run.
      - That any failure shows an initial and never changes the exit code.
      - The separate Actions cache entry, and why it is separate (the path-list version hash).
    - Delete the old section's opening sentence entirely.
    - Add a short "Bridgy conversation links" section explaining the mapping and why: webmention.io reports a bridged reply's ActivityPub id, which serves JSON.
    - Update the "What each failure does" table with an avatar row.
    - Update the coverage paragraph: author photos are now In (self-hosted). Still Out: a mention's own photo, video and audio, SVG and other image types, redirects and retries for avatars.
11. Keep logs as counts and fixed text only.

**tests/test-pull-webmentions.py.** Rewrite `LAST_GOOD` in its derived form, as described in the context. Leave the existing assertions unchanged, and confirm they pass because derive is idempotent.

**.github/workflows/hugo.yml.**
- Directly after "Restore last-good Webmentions", add "Restore last-good Webmention avatars": actions/cache/restore@v6, path static/webmention-avatars, key `webmention-avatars-${{ github.run_id }}-${{ github.run_attempt }}`, restore-keys `webmention-avatars-`.
- Directly after "Save last-good Webmentions", add "Save last-good Webmention avatars": actions/cache/save@v6, same path and key, `if: steps.mentions.outcome == 'success'`.
- Extend the comment block above the restore step. Say that avatars are self-hosted files fetched by the pull and kept in their own cache entry, because adding a path to the data entry would change its cache version and orphan last-good.
- Leave the data steps byte-identical.

**.gitignore.** Add the line `static/webmention-avatars/`.
  </action>
  <verify>
    <automated>python3 -I -S -B tests/test-pull-webmentions.py -k Avatars -k Derive -k RestorePath -k WritePrivacy -k AvatarWorkflow && python3 -I -S -B tests/test-pull-webmentions.py && grep -qx 'static/webmention-avatars/' .gitignore && grep -q 'Why avatars are self-hosted, never hotlinked' scripts/pull-webmentions.py && test "$(grep -c 'No avatar or photo URL is ever copied' scripts/pull-webmentions.py)" = 0 && test "$(grep -c 'static/webmention-avatars' .github/workflows/hugo.yml)" -ge 2 && echo task2-ok</automated>
  </verify>
  <done>
    - Every behavior above is tested and green.
    - A Bridgy-Mastodon response links to the conversation on the instance, including when it comes from a cache written before this change.
    - Avatars are deduped, reused from cache, revalidated, size-capped, type-sniffed and budgeted. They are never fetched for blocked authors and are pruned when unreferenced.
    - The data file can never hold a remote image URL, whatever a caller passes in.
    - The workflow restores and saves avatars in their own cache entry, and the data entry is untouched.
    - Committed locally as `feat(webmentions): avatar cache and limits, Bridgy conversation links, card fields`, ending with the Co-Authored-By line.
  </done>
</task>

<task type="auto">
  <name>Task 3: Social-style response cards (template + CSS), test updates, then the 375px review gate</name>
  <files>themes/arcaeon/layouts/partials/fa/mentions.html, themes/arcaeon/assets/css/main.css, tests/test-pull-webmentions.py, tests/test-notes.py, .planning/quick/261106-izg-social-style-response-cards-with-self-ho/make-fixture.py, .planning/quick/261106-izg-social-style-response-cards-with-self-ho/responses-375.png</files>
  <action>
Build the card layout (the locked "card layout" decision). Then produce the review screenshot.

**themes/arcaeon/layouts/partials/fa/mentions.html.** Keep the section root, the band-tone call and the `section-content fa-prose fa-mentions` div. Give the h2 `id="responses"`.

Define one avatar-or-initial fragment and repeat it inline wherever a face appears:
- With an avatar: `<img class="fa-avatar" src="{{ $X.avatar }}" alt="" width="N" height="N" loading="lazy" decoding="async">`.
- Without one: `<span class="fa-avatar fa-avatar--initial" aria-hidden="true">{{ $X.initial | default "•" }}</span>`. The default covers test-notes' underived fixture.

Likes row, under `with .likes`:
- A `p` with classes `fa-mentions__row fa-reactions`.
- In it, `<span class="fa-reactions__icon" aria-hidden="true">` holding the like icon partial, called with `$`.
- Then `<span class="fa-faces">`. For each `$p`, an anchor with classes `fa-mention--like fa-face`, href `{{ $p.url }}`, rel "nofollow ugc" and title `{{ $p.name }}`. It holds the 32px fragment and `<span class="visually-hidden">Liked by {{ $p.name }}</span>`.
- Then `<span class="fa-reactions__count">` holding the count, followed by "like" when the count is 1 and "likes" otherwise (use `len` and `cond`).

Reposts row: the same, with the repost icon, `fa-mention--repost`, "Reposted by", and "repost" or "reposts".

Mentions row: leave it exactly as it is (R7).

Replies:
- Keep the `fa-mentions__row` "Replies" label and the `fa-mentions__replies` list.
- Each `$r` is an `li` with classes `fa-mention--reply fa-reply`. It holds:
  - A header `p.fa-reply__header`:
    - First, an anchor `.fa-reply__author` with href `{{ $r.author_url | default $r.url }}` and rel "nofollow ugc". It holds the 40px fragment and `span.fa-reply__who`, which holds `span.fa-reply__name` (`{{ $r.name }}`) and, if there is a handle, `span.fa-reply__handle`.
    - Then an anchor `.fa-reply__time` with href `{{ $r.url }}` and rel "nofollow ugc". It holds `<time datetime="{{ $r.date }}">{{ $r.date_text }}</time>` when there is a date, and the text "View reply" otherwise.
  - Under `if $r.text`, `<p class="fa-mention__text">{{ $r.text }}</p>`.
  - Under `if $r.platform`, a `p.fa-reply__actions` holding an anchor `.fa-reply__platform` with href `{{ $r.url }}` and rel "nofollow ugc". It holds `<span class="fa-reply__icon" aria-hidden="true">` with the mastodon or bluesky icon partial (chosen with `eq $r.platform "mastodon"`, each called with `$`), then `<span>View on Mastodon</span>` or "View on Bluesky".

Template rules:
- Put each kind class on exactly one element per record.
- Use no microformat classes.
- Use named range variables inside nested blocks, never a bare dot.
- Use no safe-marking pipe.
- Rewrite the header comment so it describes the card layout and the self-hosted image rule.

**themes/arcaeon/assets/css/main.css.** Replace the block that begins with the comment `/* Responses under an essay` and ends just before `/* Compact masthead`. Start the new comment with `/* Responses under an essay or note`. The new block keeps `.fa-mentions`, its heading rule and `.fa-mentions__replies`, and adds the following, mobile-first at 375px with no media query needed. Build everything from the existing tokens.
- `.fa-mentions a:focus-visible`: 2px solid `var(--color-text-accent)` outline, offset 2px.
- `.fa-mentions .fa-avatar`:
  - Selector specificity must beat `.fa-prose img`.
  - Values: display inline-flex, flex none, width and height 2rem, border-radius 50%, object-fit cover, margin 0.
- `.fa-avatar--initial`: centered content, background `var(--color-accent)`, color `var(--color-text)` (R8), heading font, weight 600, line-height 1.
- `.fa-reactions`: flex, wrap, centered, gap 0.5rem 0.75rem.
- `.fa-reactions__icon` and `.fa-reactions__count`: 0.875rem, opacity 0.75. The icon svg is 1.25rem.
- `.fa-faces`: inline-flex, wrap, padding-left 0.5rem.
- `.fa-face`: inline-flex, margin-left -0.5rem, border-radius 50%, ring `box-shadow: 0 0 0 2px var(--color-bg)`, no underline (R9).
- `.fa-face:hover` and `.fa-face:focus-visible`: position relative and z-index 1, so focus is never hidden under a neighbor. Nothing moves.
- `.fa-reply`: keeps the top hairline from the old `.fa-mention--reply` rule.
- `.fa-reply__header`: the same flex rules as `.note__header`.
- `.fa-reply__author`: flex, gap 0.75rem, min-width 0, color inherit, no underline. Its `.fa-avatar` is 2.5rem.
- `.fa-reply__who`: column, min-width 0.
- `.fa-reply__name`: like `.note__name`.
- `.fa-reply__handle` and `.fa-reply__time`: like `.note__handle` and `.note__time`, color `var(--color-text)`, no underline until hover.
- `.fa-mentions .fa-mention__text`: margin-top 0.5rem, 1rem/1.5, like the note body.
- `.fa-reply__actions` and `.fa-reply__platform`: like `.note__actions` and `.note__copy`, with min-height 2.75rem and a 1.25rem svg.
- Nothing in this block may animate or fade. Honor prefers-reduced-motion by having no motion at all.
- Load nothing remote. Inherit `overflow-wrap: anywhere` so nothing scrolls sideways at 375px.

**Tests.** Update for the new markup and keep each assertion's intent.
- tests/test-pull-webmentions.py:
  - The tag sets in test_reply_markup_is_text_not_elements and test_the_section_holds_only_inert_markup gain img, svg and path.
  - The attribute check allows src only on img, and only when it fullmatches AVATAR_RE.
  - test_essay_renders_one_section_with_names_and_text asserts the visible order likes, reposts, mentions, replies. It asserts the accessible texts "Liked by Ada" and "Reposted by Bo", the mention name "Eve", the reply author "Cy", and that the reply author link targets cy's author URL while its time link targets the mention URL.
- tests/test-notes.py:
  - `fa-mentions__row` stays 3, and `fa-mention--reply` stays 1.
  - The `rel="nofollow ugc"` count in test_mentions_sit_after_the_entry_and_outside_it becomes 4: the like face, the mention, the reply author and the reply time. Add a comment saying so.
- Then run the full suites.

**Review gate** (the last step; the orchestrator shows Matt the screenshot before anything is pushed).

1. Write `.planning/quick/261106-izg-social-style-response-cards-with-self-ho/make-fixture.py`. Stdlib only, run with `python3 -I`. It:
   - Loads scripts/pull-webmentions.py with importlib, as the tests do.
   - Generates two distinct 96x96 solid PNGs from palette colors (fusion gold #ffb347 and ion glow #5be7ff) using zlib, struct and binascii.crc32.
   - Seeds them into `m.AVATAR_DIR` as `avatar_name(url) + ".png"` for the photo URLs https://avatars.webmention.io/fixture/rowan.png and https://avatars.webmention.io/fixture/sol.png.
   - Patches `m.fetch_avatar` to return None, so nothing is fetched and only the seeded cache resolves.
   - Builds children targeting https://falkensmage.com/notes/the-lovers-isn-t-a-romance/:
     - **Reply A** (with avatar): wm-source `https://brid.gy/comment/mastodon/@falkensmage@mastodon.social/117570501730802441/1`, url `https://rowanvale.example/.ghost/activitypub/note/fixture`, author Rowan Vale at https://rowanvale.example/ with the rowan photo, a short clearly fixture text, published 2026-11-05.
     - **Reply B** (no avatar): wm-source `https://brid.gy/comment/bluesky/falkensmage.com/fixture/2`, url `https://bsky.app/profile/wren.example/post/3fixture`, author Wren at https://bsky.app/profile/wren.example, no photo.
     - Like 1 by Rowan Vale (rowan photo), Like 2 by Ivy Marsh (no photo), and a repost by Sol Ortega (sol photo). Each uses a brid.gy mastodon like or repost source.
   - Runs `m.assemble(children, m.load_blocklist(m.BLOCKLIST), m.AVATAR_DIR)`, then `m.write_data(m.DATA, pages, <utc now>)`, then `m.prune_avatars` on the returned pages.
2. Run `python3 -I .planning/quick/261106-izg-social-style-response-cards-with-self-ho/make-fixture.py`.
3. Run `hugo --minify --baseURL http://127.0.0.1:1414/`.
4. Serve `public/` with `python3 -m http.server 1414 --bind 127.0.0.1 --directory public` in the background and note its PID.
5. Run Chrome headless with:
   - `--headless=new --disable-gpu --hide-scrollbars --force-device-scale-factor=1`
   - `--user-data-dir` set to a fresh mktemp dir
   - `--window-size=375,1600 --virtual-time-budget=5000`
   - `--screenshot="$PWD/.planning/quick/261106-izg-social-style-response-cards-with-self-ho/responses-375.png"`
   - the URL `http://127.0.0.1:1414/notes/the-lovers-isn-t-a-romance/#responses`
6. Read the PNG to confirm visually that the Responses heading, the like and repost faces with their counts, both reply cards (one avatar, one initial) and the platform links are in frame, with no horizontal overflow. If the fragment did not scroll, shoot again without it at `--window-size=375,3200`.
7. Kill the server.
8. Clean up: delete data/webmentions.json and the static/webmention-avatars directory, then run `hugo --minify --cleanDestinationDir` so public/ holds the production build with no fixture.
9. Do not commit make-fixture.py or the PNG. They stay in the quick directory for the orchestrator's docs commit.
10. Record the re-shoot commands (steps 2 to 8) in the SUMMARY.
  </action>
  <verify>
    <automated>hugo --minify && for f in tests/test-*.py; do python3 -I -S -B "$f" || exit 1; done && bash tests/validate-fa.sh && bash tests/validate-notes.sh && python3 -I -c "s=open('themes/arcaeon/assets/css/main.css').read(); a=s.index('/* Responses under'); b=s.index('/* Compact masthead', a); r=s[a:b]; assert all(k in r for k in ('.fa-face', '.fa-reply__header', '.fa-avatar--initial')), 'card css missing'; assert not any(w in r for w in ('transition', 'animation', '@keyframes', '@import', 'url(')), 'motion or remote load in block'; print('css ok')" && grep -q 'id="responses"' themes/arcaeon/layouts/partials/fa/mentions.html && python3 -I -c "import struct,sys; d=open(sys.argv[1],'rb').read(24); assert d[:8]==b'\x89PNG\r\n\x1a\n', 'not a png'; w,h=struct.unpack('>II', d[16:24]); assert w==375, (w,h); print('shot ok', w, h)" .planning/quick/261106-izg-social-style-response-cards-with-self-ho/responses-375.png && test ! -e data/webmentions.json && echo task3-ok</automated>
  </verify>
  <done>
    - Replies render as note-style cards: an avatar or initial, the name, a handle or domain, a linked date, the text, and a platform link.
    - Likes and reposts render as overlapping face rows with counts and "Liked by" / "Reposted by" accessible names. Mentions are unchanged.
    - All five suites, validate-fa.sh and validate-notes.sh are green.
    - responses-375.png (375px wide) shows the Lovers note's Responses section built from the fixture.
    - The fixture data and avatars have been removed and public/ rebuilt clean.
    - Committed locally as `feat(responses): social-style response cards with self-hosted avatars`, ending with the Co-Authored-By line. Nothing is pushed.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| runner -> author photo host | The photo URL comes from a stranger's h-card, reported by webmention.io. Its bytes are untrusted and get published on falkensmage.com. The run also holds WEBMENTION_IO_TOKEN. |
| webmention.io -> data file -> page | The url, source, author and text fields are stranger-controlled and rendered on every essay or note that has responses. |
| reader's browser -> page | No third-party request may originate from the Responses section. |
| script -> Actions log | `::` at the start of a log line is a workflow command. |
| Actions cache -> build | A restored avatar or data entry is treated as untrusted on read. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261106-izg-01 | Information disclosure | mentions.html img / write_data | high | mitigate | The remote URL never enters `pages` (R2: photos side dict). write_data drops any avatar that fails AVATAR_RE. The template has no other image source. The probe goes red on any img src outside /webmention-avatars/ or naming a missing file. Covered by AvatarTracer and WritePrivacy. |
| T-261106-izg-02 | Elevation of privilege | static/webmention-avatars files | high | mitigate | Only PNG, JPEG, WebP and GIF are accepted, identified by magic bytes. SVG and HTML are never written. The extension comes from the sniff, never from the URL or Content-Type. Files are only ever referenced from img tags. Covered by the rejection tests in Avatars. |
| T-261106-izg-03 | Denial of service | attach_avatars / fetch_avatar | medium | mitigate | 204800-byte read cap, 5 s timeout, one attempt, no redirects, a 45 s total budget, and a per-URL `except Exception`. Avatar failures never change the exit code. The step's timeout-minutes of 3 is unchanged. Covered by the budget, slow-route and oversize tests. |
| T-261106-izg-04 | Information disclosure | fetch_avatar headers | high | mitigate | Avatar requests carry only User-Agent and Accept, through OPENER, which follows no redirect and uses no proxy. The token stays on the API request only. A test asserts no image request has an authorization header and no path holds the token. |
| T-261106-izg-05 | Information disclosure (SSRF) | avatar_source_ok | low | accept | https only, dotted hostnames, IP literals and localhost rejected, no redirects. Residual: a public DNS name that resolves to a private address. Accepted because the runner is an ephemeral GitHub-hosted VM and the response is published only if it sniffs as an image of at most 200 KB. |
| T-261106-izg-06 | Tampering | blocklist vs avatars | medium | mitigate | apply_blocklist runs before attach_avatars, and restore applies it to last-good. prune_avatars deletes every unreferenced file on every run, including token-absent and outage runs. Covered by tests in Avatars and RestorePath. |
| T-261106-izg-07 | Tampering | poisoned Actions cache entry | low | mitigate | Cached avatars are revalidated (size, sniff, extension) on reuse and on the restore path. An invalid file is deleted and its field dropped. load_last_good already shape-checks the data entry. |
| T-261106-izg-08 | Spoofing | derive Bridgy URL mapping | low | mitigate | The mapping fires only on an anchored `https://brid.gy/` source with strict user, dotted-instance and numeric-id groups, and the result passes through clean_url. Lookalike hosts and malformed parts are tested. Links keep rel="nofollow ugc". |
| T-261106-izg-09 | Spoofing / injection | log lines | low | mitigate | The avatar log line holds counts only, through log() with the `pull-webmentions:` prefix. A test asserts no URL, host or file name appears in stdout. |
| T-261106-izg-10 | Tampering (XSS) | mentions.html | high | mitigate | Every stranger value is plain double-brace output with no safe-marking pipe (test_partial_never_marks_text_safe). Derived fields are computed in Python, so no template function runs on stranger data. The escape-bypass mutation test still turns the probe red. |
| T-261106-izg-SC | Tampering | npm/pip/cargo installs | high | accept | No package is installed. Stdlib only, enforced by running every suite under `python3 -I -S`. |
</threat_model>

<verification>
- `hugo --minify && for f in tests/test-*.py; do python3 -I -S -B "$f" || exit 1; done` passes. The baseline is about 87 s; expect somewhat more.
- `bash tests/validate-fa.sh` and `bash tests/validate-notes.sh` pass on the clean production build.
- `git diff --stat HEAD~3 -- . ':!.planning'` lists only the eight files in files_modified. .github/workflows/notes.yml, scripts/syndicate-notes.py and data/ are untouched, and no file under static/ is tracked (`git ls-files static/webmention-avatars` prints nothing).
- `git log -3 --format=%B` shows three conventional-style messages, each ending with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. `git status -sb` shows the branch ahead of origin and not pushed.
- `.planning/quick/261106-izg-social-style-response-cards-with-self-ho/responses-375.png` exists and is 375 px wide.
</verification>

<success_criteria>
- On the next production build, the Lovers note's real Mastodon reply renders as a card: a self-hosted round avatar, the name linking to the author's site, the domain, and a date and "View on Mastodon" link that open the conversation at mastodon.social rather than a JSON document.
- Likes and reposts read as faces with a count, and each face's accessible name is "Liked by <name>" or "Reposted by <name>".
- No byte of the Responses section can make a reader's browser contact a third-party host, and the probe proves it on every deploy.
- A missing, oversized, wrong-type or slow avatar costs only that avatar, never the build.
- Matt has a 375px screenshot to approve before any push.
</success_criteria>

<output>
Create `.planning/quick/261106-izg-social-style-response-cards-with-self-ho/261106-izg-SUMMARY.md` when done. Include the review-gate re-shoot commands and the absolute path of responses-375.png.
</output>
