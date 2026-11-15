---
phase: quick-261115-fjc
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/sync-cr.py
  - data/cr-legacy.json
  - content/cr/_index.md
  - content/cr/<slug>/ (51 generated page bundles: index.html, cover.jpg, img-NN.*)
  - themes/arcaeon/layouts/cr/single.html
  - themes/arcaeon/layouts/cr/list.html
  - themes/arcaeon/layouts/cr/list.rss.xml
  - themes/arcaeon/layouts/partials/cr/posts.html
  - themes/arcaeon/layouts/partials/cr/masthead.html
  - themes/arcaeon/layouts/_default/baseof.html
  - themes/arcaeon/assets/css/main.css
  - tests/validate-cr.sh
autonomous: true
requirements:
  - QUICK-261115-fjc

estimate:
  tokens: 120000
  raw_tokens: 120000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "`python3 scripts/sync-cr.py` turns the 53-entry listing at ~/.psyche/tools/substack/cr-archive.json into exactly 51 page bundles at content/cr/<substack-slug>/ (slug kept byte-for-byte, so the later redirect is a pure /p/<slug> to /cr/<slug> swap). The two gated August-2024 posts produce no bundle, and any OTHER non-public post in the listing aborts the run instead of being silently dropped or published"
    - "Every live request to a Substack host is preceded by a sleep of at least 3 seconds. Post JSON and image bytes are cached under ~/.cache/sync-cr (outside the repo), so a rerun with --offline makes zero network calls and reproduces content/cr/ and data/cr-legacy.json byte-for-byte. The cookie file is read only when --cookie-file is passed; its contents are never printed, cached, or committed"
    - "All 51 slugs render at /cr/<slug>/ in the arcaeon look (Cinzel display headings, fa-room bands, fa-prose rhythm): title, subtitle, byline, date, cover, cleaned body. The 18 podcast pages also show the episode duration and a pending-player notice, and their front matter carries media_url set to an empty string plus the NAS media_file name"
    - "Nothing under content/cr/ or the built /cr/ tree references a Substack-hosted asset (the substackcdn fetch CDN, the substack-post-media bucket, or the legacy bucketeer bucket); every cover and inline image is a file in its page bundle, served from falkensmage.com"
    - "Post bodies hold no Substack clutter and no active content: no subscribe/share widgets or buttons, no 'Thanks for reading' CTAs, no iframes, scripts, forms, svg, event-handler attributes or javascript: URLs, and no class attribute other than cr-footnote. Captioned images survive as figure + img + figcaption; Spotify and embedded-post cards survive as plain links; footnotes still jump to their notes; links between CR posts point at /cr/<slug>/"
    - "/cr/ lists all 51 posts newest-first, grouped by year; /cr/index.xml is a full-content RSS feed whose item bodies use absolute falkensmage.com URLs"
    - "/cr/ stays invisible until cutover: no built page outside /cr/ links to it; the nav header partial, home template, content/_index.md and .github/workflows/ are byte-identical to the merge-base with origin/main; validate-cr.sh is not wired into any workflow; nothing is merged to main and no PR is opened"
    - "tests/validate-cr.sh builds the site itself and exits 0; tests/validate-fa.sh still reports 13 passed, 0 failed (its baseline at HEAD on 2026-11-15)"
  artifacts:
    - path: "scripts/sync-cr.py"
      provides: "listing reader, throttled cached fetcher (--only, --fetch-only, --offline, --refresh, --cookie-file, --listing, --cache), body sanitizer, image localizer, bundle + data/cr-legacy.json writer, WARN report"
      contains: "def sanitize_body"
    - path: "data/cr-legacy.json"
      provides: "the 51 kept slugs (newest first) and the 2 dropped slugs; validate-cr.sh's source of truth"
      contains: "\"dropped\""
    - path: "content/cr/_index.md"
      provides: "section title Contemplating Resonance and lede copied verbatim from the Substack publication description"
      contains: "Contemplating Resonance"
    - path: "themes/arcaeon/layouts/cr/single.html"
      provides: "post page: compact masthead, h-entry header with byline/date/duration, cover, pending-player notice for podcasts, body, older/newer neighbors"
      contains: "data-cr-player"
    - path: "themes/arcaeon/layouts/cr/list.html"
      provides: "section index: masthead + lede, newest post featured, all posts grouped by year, RSS link"
      contains: "GroupByDate"
    - path: "themes/arcaeon/layouts/cr/list.rss.xml"
      provides: "full-content RSS at /cr/index.xml with absolutized URLs"
      contains: "content:encoded"
    - path: "themes/arcaeon/layouts/partials/cr/posts.html"
      provides: "the section's posts newest-first"
      contains: "site.GetPage \"/cr\""
    - path: "themes/arcaeon/layouts/partials/cr/masthead.html"
      provides: "text masthead in the display face, compact variant for post pages"
      contains: "cr-masthead"
    - path: "tests/validate-cr.sh"
      provides: "self-building gate: 51 slugs, dropped slugs absent, no Substack-hosted assets, sanitized bodies, local images resolve, podcast notice, feed, CR head metadata, pre-cutover invisibility"
      contains: "VALIDATE_CR_PARTIAL"
  key_links:
    - from: "scripts/sync-cr.py"
      to: "data/cr-legacy.json -> tests/validate-cr.sh"
      via: "the committed slug list (CI cannot read ~/.psyche)"
    - from: "content/cr/<slug>/index.html (Hugo HTML content format, YAML front matter)"
      to: "themes/arcaeon/layouts/cr/single.html"
      via: "{{ .Content }} passes the sanitized HTML through untouched; no global goldmark unsafe switch"
    - from: "themes/arcaeon/layouts/partials/cr/posts.html"
      to: "cr/list.html, cr/list.rss.xml, cr/single.html neighbors"
      via: "partial return value"
    - from: "themes/arcaeon/layouts/_default/baseof.html ($inCR branch)"
      to: "every /cr/ page head"
      via: "title, og:* and feed discovery scoped to Section cr only"
---

<objective>
Scaffold the Contemplating Resonance section at /cr/ on branch `cr/own-the-stack`: a one-way Substack-to-Hugo sync script, 51 self-hosted page bundles, list/single/RSS templates in the arcaeon look, and a self-building validation gate. Mirror the Feral Architecture own-the-stack pattern already in this repo (scripts/sync-fa.py, themes/arcaeon/layouts/fa/, tests/validate-fa.sh, content/fa/ page bundles). The section stays invisible until cutover: no nav link, no home card, no workflow wiring, no merge.

Purpose: own the CR archive on falkensmage.com so the falkenslabyrinth.com Substack can later redirect /p/<slug> to /cr/<slug>/ with nothing lost and nothing hotlinked back to Substack.

Output: scripts/sync-cr.py, data/cr-legacy.json, content/cr/ (index + 51 bundles), five templates/partials, a scoped baseof.html edit, a CSS block, tests/validate-cr.sh.

Key difference from FA: there are no local drafts. The source is Substack itself: the saved listing (~/.psyche/tools/substack/cr-archive.json) plus one GET per post body.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@hugo.toml
@scripts/sync-fa.py
@tests/validate-fa.sh
@themes/arcaeon/layouts/fa/single.html
@themes/arcaeon/layouts/fa/list.rss.xml
@themes/arcaeon/layouts/fa/archive.html
@themes/arcaeon/layouts/partials/fa/card.html
@themes/arcaeon/layouts/partials/fa/essays.html
@themes/arcaeon/layouts/_default/baseof.html
@/Users/falkensmage/.psyche/drafts/feral-architecture/OWN-THE-STACK-MIGRATION.md

Inputs outside the repo (read, never copied wholesale, never committed):
- /Users/falkensmage/.psyche/tools/substack/cr-archive.json: list of 53 post objects (publication_id 2076995). Fields used: slug, title, subtitle, post_date, cover_image, type (newsletter|podcast), audience, podcast_duration, podcast_episode_image_url. 51 have audience "everyone"; the two gated ones are your-august-2024-contemplative-alchemist (founding) and your-august-2024-paid-member-discount (only_paid).
- /Users/falkensmage/Inbox/substack-cookies.txt: only if a public post ever refuses an anonymous request. Never print it, never commit it.
- /Users/falkensmage/mnemosyne-nas/creative-media/Podcast-Video/contemplating-resonance/<YYYY-MM-DD>-<slug>.mp4: podcast video on the NAS. Never commit it. Only its filename goes into front matter. The date is post_date[:10], the same naming pull_cr_videos.sh uses.

Verified during planning (2026-11-15), so the executor need not rediscover these:
- GET https://falkenslabyrinth.com/api/v1/posts/<slug> works without auth: 200, application/json, a top-level object (not wrapped) with body_html, cover_image, audience, type, podcast_duration, publishedBylines, podcast_episode_image_url. Probed with s3e4-stripping-down-the-sacred-with and the-labyrinth-is-gone-the-architect.
- s3e4 body_html contains: a subscription-widget-wrap-editor block (SubscribeWidgetToDOM), a captioned-button-wrap "Thanks for reading … share" block with a button-wrapper Share button, two Spotify iframes (class spotify-wrap, data-attrs JSON carrying url/title/subtitle), and a digest-post-embed (data-attrs JSON carrying title, caption, publishedBylines with photo_url). The podcast player is NOT inside body_html.
- the-labyrinth-is-gone-the-architect body_html opens with a captioned-image-container whose image is the cover image itself: the img data-attrs "src" is the same substack-post-media original, it has no figcaption, and data-attrs has topImage true. Inside it: an image-link anchor to the fetch CDN, picture/source srcset, and an image-link-expand div holding pencraft/lucide svg buttons. The body also links to feralarchitecture.com/p/<slug> (FA is already live at /fa/<slug>/).
- Fetch-CDN URLs look like https://substackcdn.com/image/fetch/<transforms>/https%3A%2F%2Fsubstack-post-media.s3.amazonaws.com%2Fpublic%2Fimages%2F<file>. The original is the percent-decoded tail. On inline images the img data-attrs "src" carries the original directly.
- Hugo v0.160.1+extended renders a leaf bundle whose index file is index.html with YAML front matter: the HTML passes through .Content untouched, sibling bundle files (img-01.jpg) are published next to the page, and a front-matter key named kind lands in .Params.kind while .Kind stays "page". hugo.toml has no markup.goldmark unsafe setting, and this plan does not add one.
- By default Hugo lists /cr/ pages in public/sitemap.xml and in the home feed public/index.xml (confirmed in a scratch site).
- `hugo --minify` writes unquoted attributes (href=/fa/ as well as class="a b"), so any HTML check must accept both. Parse with html.parser, as validate-fa.sh does; do not grep attributes.
- beautifulsoup4 4.12.3 and PyYAML are already importable by `python3 -I` (pyenv 3.10). No package installs are needed.
- tests/validate-fa.sh at HEAD after `hugo --minify`: 13 passed, 0 failed. A full build takes about 1.6s.
- Matt's FA precedent (OWN-THE-STACK-MIGRATION.md): the branch merges to main on cutover day. Until then nothing on this branch is deployed.
</context>

<!-- planner-discipline-allow: substackcdn -->
<!-- planner-discipline-allow: substack-post-media -->
<!-- planner-discipline-allow: bucketeer- -->
<!-- planner-discipline-allow: <iframe -->
<!-- planner-discipline-allow: <script -->
<!-- planner-discipline-allow: your-august-2024-contemplative-alchemist -->
<!-- planner-discipline-allow: your-august-2024-paid-member-discount -->
<!-- planner-discipline-allow: validate-cr -->

<tasks>

<task type="tracer">
  <name>Task 1: Tracer: three real posts from the Substack API to a built /cr/<slug>/ page, gated by validate-cr.sh</name>
  <files>scripts/sync-cr.py, content/cr/_index.md, themes/arcaeon/layouts/cr/single.html, tests/validate-cr.sh (plus generated content/cr/<3 tracer slugs>/ and data/cr-legacy.json)</files>
  <action>
Stay on branch cr/own-the-stack; never switch branches. Write the whole sync script now. The tracer runs it on three posts only.

A. scripts/sync-cr.py. Model its shape, docstring tone and WARN reporting on scripts/sync-fa.py.
1. Docstring: a one-way sync from the Substack publication into content/cr/. Every run regenerates the bundles it owns, so hand edits under content/cr/<slug>/ are overwritten next run (design principle 10). Explain why HTML content files are used instead of markdown: faithful, and no global goldmark unsafe switch. Explain why every image is self-hosted.
2. Arguments:
   - --listing, default ~/.psyche/tools/substack/cr-archive.json.
   - --cache, default ~/.cache/sync-cr, with subdirectories posts/, img/ and processed/.
   - --only SLUG, repeatable: regenerate just those bundles and leave every other bundle alone.
   - --fetch-only: cache post JSON for every kept slug and write nothing into the repo.
   - --offline: any cache miss is an error, exit 1.
   - --refresh: ignore cached post JSON.
   - --cookie-file PATH: optional, no default.
3. Fail with a clear exit message if bs4 cannot be imported. Never install anything.
4. Slugs:
   - Every listing slug must match ^[a-z0-9-]+$ or the run exits 1.
   - DROPPED holds exactly the two gated August-2024 slugs and is excluded by name.
   - Assert that the set of listing posts whose audience is not "everyone" equals DROPPED. Any extra gated post aborts the run, naming its slug. Per the task, 51 posts are kept.
   - Write data/cr-legacy.json on every run, built from the listing only: a _comment key, "posts" (the 51 kept slugs in listing order, newest first) and "dropped" (the 2). Mirror data/fa-legacy.json.
5. Network:
   - One helper performs every request, and it sleeps 3 seconds before each live request (per the task, this is mandatory). It sends the same browser user-agent string as ~/.psyche/tools/substack/cr_archive.py.
   - Post JSON comes from https://falkenslabyrinth.com/api/v1/posts/<slug> and is cached to cache/posts/<slug>.json. Assert that it is a dict with a non-empty body_html and audience "everyone". Otherwise record a hard failure for that slug.
   - Attach the cookie header only when --cookie-file was given. Error text names the slug or URL kind and the HTTP status, never the headers or the cookie.
   - Image bytes are cached at cache/img/<sha1 of the source URL>.
   - Sniff magic bytes and accept only JPEG, PNG, GIF and WebP. Anything else is a hard failure for that post.
   - Downloaded files are untrusted. They stay in the cache directory and nothing from there is executed or imported.
6. Image localization, using the sips conventions of sync-fa.py's put_image:
   - Resolve every Substack-hosted image URL to its original: the img data-attrs "src" when present, otherwise the percent-decoded https%3A tail of a fetch-CDN URL. Try the original first and fall back to the CDN URL itself.
   - Substack-hosted means the fetch CDN host, the substack-post-media S3 bucket, any bucketeer-*.s3.amazonaws.com bucket, or a *.substack.com image path.
   - Processed output is cached at cache/processed/<sha1>-<variant>. Bundle files are copies of it, so reruns are byte-identical.
   - Cover: from the post's cover_image, falling back to podcast_episode_image_url, always written as cover.jpg (sips JPEG q82, long edge ≤1600 px). FA templates and Hugo processing GetMatch "cover.jpg".
   - Inline images are named img-01, img-02… in document order. GIF is copied verbatim to keep animation. PNG is resized with sips -Z 1600 and stays PNG to keep alpha. Everything else becomes JPEG q82, long edge ≤1600.
   - Rewrite each img src to the root-relative /cr/<slug>/img-NN.ext and set width and height from the processed file (sips -g pixelWidth -g pixelHeight), plus loading="lazy" decoding="async".
   - Non-Substack image hosts stay as they are, with a WARN line. data: URIs are dropped, with a WARN line.
7. sanitize_body(html, slug, ctx) uses bs4 with the html.parser backend. Rules, in order:
   - Remove entirely: subscription-widget-wrap*, captioned-button-wrap, button-wrapper, paywall-jump, install-substack-app*, image-link-expand, any svg, script, style, form, input, button, noscript, object, embed.
   - Remove any p whose text starts with "Thanks for reading" (case-insensitive), and any p whose whole text is a bare CTA such as Subscribe, Subscribe now, Share, or Leave a comment.
   - captioned-image-container becomes a figure holding the img, plus a figcaption with its sanitized inner HTML only when the caption is non-empty. Anchors wrapping images (image-link) are unwrapped. picture and source collapse to the single img.
   - Leading duplicate cover: if the body's first block is an image whose resolved original equals the cover's resolved original and it has no caption, drop it. This mirrors sync-fa.py's cover-duplicate rule and was verified on the-labyrinth-is-gone-the-architect.
   - iframe embeds become plain links, never iframes, because the site constraint is no external dependencies. For spotify-wrap the link reads "<title> — <subtitle> (Spotify)" and points at data-attrs url. For youtube-wrap it is "Watch on YouTube" linking the video URL. For any other iframe it is a link to its src, with a WARN.
   - digest-post-embed and embedded-post-wrap become a p holding a link to the embedded post's URL (find the URL key in data-attrs; inspect the cached s3e4 JSON), with the data-attrs title as the link text.
   - Native video/audio embeds and any other unrecognized div class carrying data-attrs are removed with a WARN.
   - pullquote becomes blockquote. footnote-anchor becomes sup holding the anchor, keeping its href and id. A footnote div becomes div class="cr-footnote" holding the number anchor (id kept) and the content.
   - h1 is demoted to h2. span, and every div other than cr-footnote, is unwrapped. Empty p (no text, no img) is removed. Back-to-back hr collapse to one, and a leading or trailing hr is removed.
   - Links:
     - falkenslabyrinth.com, falkenslabyrinth.substack.com or open.substack.com/pub/falkenslabyrinth with /p/<slug>: a kept slug becomes /cr/<slug>/, query dropped, fragment kept. A /comments path, an action=share query, or a DROPPED slug is unwrapped to plain text. An unknown slug becomes /cr/<slug>/ with a WARN.
     - The publication root, /archive or /podcast becomes /cr/. Any other falkenslabyrinth path (subscribe, about, chat…) is unwrapped with a WARN.
     - Claude's discretion: feralarchitecture.com/p/<slug> becomes /fa/<slug>/ when content/fa/<slug>/ exists, and the feralarchitecture.com root becomes /fa/. FA is already live, so this saves a redirect hop.
     - javascript: or data: hrefs are unwrapped.
   - Attribute allowlist, enforced last:
     - a: href, id.
     - img: src, alt, width, height, loading, decoding.
     - ol: start.
     - th, td: colspan, rowspan.
     - div: class only when it is exactly cr-footnote.
     - Strip every other attribute (class, style, target, rel, data-*, srcset, sizes, on*).
     - A tag outside the allowlist (p, h2–h6, a, strong, b, em, i, u, s, sup, sub, br, hr, ul, ol, li, blockquote, figure, figcaption, img, pre, code, table, thead, tbody, tr, th, td, div.cr-footnote) is unwrapped.
   - Count every class name that hit no specific rule (removed or unwrapped generically) and print each as a WARN at the end, so new embed types are visible.
   - Replace any literal double opening brace in text with HTML entities, so Hugo never parses body text as a shortcode.
   - Serialize with each top-level block on its own line for readable diffs.
8. Bundle write:
   - A full run (no --only) removes every subdirectory of content/cr/ first, keeping _index.md, as sync-fa.py does.
   - Write content/cr/<slug>/index.html as front matter lines in sync-fa.py's key: json.dumps(value) style between --- fences, a blank line, then the sanitized body.
   - Front matter:
     - title, subtitle, date (post_date), slug.
     - kind: "newsletter" or "podcast", from type.
     - byline: publishedBylines names joined with " & ", default "Matt Stine".
     - legacy_url: https://falkenslabyrinth.com/p/<slug>.
     - cover: "cover.jpg", only when a cover was written.
     - Podcasts only: duration (int seconds, rounded from podcast_duration); duration_label ("1h 4m" from one hour up, otherwise "<n>m" rounded with a minimum of 1m); media_url: "" (the hosting decision between Riverside and YouTube is pending); media_file: "<post_date[:10]>-<slug>.mp4".
   - Final report, in sync-fa.py's print style: counts (posts, covers, inline images localized), the dropped slugs, every WARN, every hard failure. Exit 1 if any kept post hard-failed.

B. content/cr/_index.md (hand-authored; the script never touches it):
   - title: "Contemplating Resonance".
   - lede: the publication description copied verbatim from the content of the meta name="description" tag on https://falkenslabyrinth.com/. Fetch it once, at least 3 seconds after any other Substack call. If there is none, omit lede. Do not write copy in Matt's voice.

C. themes/arcaeon/layouts/cr/single.html, mirroring fa/single.html. This tracer version leaves out the masthead and neighbors; Task 3 adds them.
   - define "main", main.fa-room, article.h-entry.
   - Header band (helpers/band-tone.html): h1.fa-essay-title.p-name; the subtitle as p.offer-lede.p-summary; p.fa-essay-byline holding the byline (Params.byline, defaulting to site.Params.author) · time.dt-published (formatted as in FA) · and, when kind is podcast, "Episode · <duration_label>".
   - Cover: GetMatch "cover.jpg", Resize "1200x webp q80", with the same alt fallback pattern as FA, worded "Cover image for <title>".
   - When kind is podcast:
     - If Params.media_url is set, render a launch-banner__cta link reading "Watch the episode →".
     - Otherwise render div.cr-player.cr-player--pending with data-cr-player="pending" and role="note", holding p.cr-player__label "Episode" and the p "Video for this episode is moving to its new home and will play here. The show notes are below." This is the pending-player notice the task requires.
   - Body band: div.section-content.offer-body.page-body.fa-prose.cr-prose.e-content wrapping .Content.
   - Then a closing band with a link to /cr/ reading "All posts →".

D. tests/validate-cr.sh, modeled on validate-fa.sh (pass/fail helpers, totals, exit 1 on any failure).
   - Build: unless VALIDATE_CR_PUBLIC is set, build into a mktemp directory with hugo --minify --quiet --destination and remove it on exit. Otherwise check the given directory. The script never writes into public/.
   - With VALIDATE_CR_PARTIAL=1, check only the slugs that have a content/cr/<slug>/ bundle and skip the "all 51" and feed checks. That mode exists for this tracer.
   - Checks, each reading slugs from data/cr-legacy.json with python3 -I heredocs as validate-fa.sh does:
     a. Every kept slug (in partial mode, every bundled slug) has <public>/cr/<slug>/index.html. Print the count.
     b. No dropped slug exists under content/cr/ or <public>/cr/.
     c. No Substack-hosted asset string appears in any file under <public>/cr/ (HTML and XML) or under content/cr/. Use one extended regex covering the fetch-CDN host, the post-media bucket and the bucketeer bucket prefix.
     d. Every body in content/cr/*/index.html (front matter stripped), parsed with html.parser: no forbidden tag (script, style, iframe, form, input, button, svg, object, embed, video, audio, source), no attribute starting with "on", no href or src starting with javascript: or data:, and the only class value anywhere is cr-footnote.
     e. Every img src under <public>/cr/*/index.html that starts with / resolves to a file in the build. Parse; do not grep.
     f. Every slug whose front matter kind is podcast renders an element with data-cr-player and has a media_url key in its front matter. No newsletter page renders data-cr-player.
     g. Full mode only: data/cr-legacy.json lists 51 posts and 2 dropped; <public>/cr/index.xml exists, has content:encoded, and holds no root-relative src=" or href=" values.
   - Note in the header comment: run from the project root; it is NOT in .github/workflows until cutover.

E. Run it:
   1. python3 scripts/sync-cr.py --fetch-only (51 throttled calls, about 3 minutes; background run is fine).
   2. From the cached JSON, pick the newest newsletter whose body still has at least one captioned image after the leading-cover rule, so the tracer exercises inline localization. Record that slug in the SUMMARY.
   3. Run python3 scripts/sync-cr.py --only s3e4-stripping-down-the-sacred-with --only the-labyrinth-is-gone-the-architect --only <picked slug>.
   4. Run VALIDATE_CR_PARTIAL=1 bash tests/validate-cr.sh.
   5. Commit the script, _index.md, single.html, validate-cr.sh, data/cr-legacy.json and the three bundles.
  </action>
  <verify>
    <automated>VALIDATE_CR_PARTIAL=1 bash tests/validate-cr.sh && test -f content/cr/s3e4-stripping-down-the-sacred-with/index.html && test -f content/cr/the-labyrinth-is-gone-the-architect/cover.jpg && ls content/cr/*/img-* >/dev/null && test "$(ls ~/.cache/sync-cr/posts/*.json | wc -l | tr -d ' ')" = 51</automated>
  </verify>
  <done>Three real posts (a podcast with Spotify, digest and subscribe/share clutter, the newest newsletter with a cover-duplicate lead image, and a newsletter with a surviving inline image) render at /cr/<slug>/ from self-hosted files. All 51 post JSONs are cached outside the repo. VALIDATE_CR_PARTIAL=1 bash tests/validate-cr.sh passes. Committed on cr/own-the-stack.</done>
</task>

<task type="auto">
  <name>Task 2: All 51 posts land, plus the /cr/ index and full-content feed</name>
  <files>scripts/sync-cr.py, themes/arcaeon/layouts/cr/list.html, themes/arcaeon/layouts/cr/list.rss.xml, themes/arcaeon/layouts/partials/cr/posts.html, themes/arcaeon/layouts/partials/cr/masthead.html (plus regenerated content/cr/<51 slugs>/ and data/cr-legacy.json)</files>
  <action>
1. Run python3 scripts/sync-cr.py with no --only. This is the full regeneration. Image downloads are throttled at 3s each, so expect several minutes; run it in the background and wait for it.
2. Read every WARN line. For each unrecognized embed class that dropped real content, add a specific rule in sanitize_body, consistent with Task 1's rules (iframe-style embeds become plain links, widgets are removed), and rerun. Rerun output comes from the cache with no network. Clutter-only WARNs may stand. Record them in the SUMMARY with a one-line reason each, together with any non-Substack image hosts left in place.
3. Write themes/arcaeon/layouts/partials/cr/posts.html:
   - Returns site.GetPage "/cr" .RegularPages.ByDate.Reverse, or an empty slice. Mirror partials/fa/essays.html.
4. Write themes/arcaeon/layouts/partials/cr/masthead.html:
   - Context: dict page and compact.
   - Renders div.cr-masthead (plus cr-masthead--compact when compact) holding an a.cr-masthead__brand to /cr/ with aria-label "Contemplating Resonance — home".
   - Inside it: the words Contemplating Resonance in an h1.cr-masthead__title when not compact, otherwise a span.cr-masthead__title.
   - When not compact, add the page's lede as p.cr-masthead__lede.
   - No image wordmark exists for CR; Task 3 sets the display face in CSS.
5. Write themes/arcaeon/layouts/cr/list.html, mirroring fa/list.html and fa/archive.html markup so the existing FA classes style it:
   - main.fa-room, section.section.section-void.fa-band, div.fa-wide.
   - The masthead partial (non-compact).
   - The newest post through the existing partials/fa/card.html with size "featured". Reuse it read-only; do not edit FA partials.
   - An h2.fa-rail-heading "All <n> posts".
   - Posts grouped with GroupByDate "2006" (year headings as h2.fa-archive__month, rows as ol.fa-archive__list > li > a.fa-popular__item, the same row markup as fa/archive.html including the 160x160 cover thumb). The meta line is the date, plus " · Episode · <duration_label>" for podcasts.
   - A p.fa-sidebar__feed RSS link from .OutputFormats.Get "rss".
6. Write themes/arcaeon/layouts/cr/list.rss.xml, mirroring fa/list.rss.xml:
   - first 30 of the posts partial; channel title Contemplating Resonance; description from Params.lede.
   - Items: title, link, guid, pubDate, description (subtitle).
   - content:encoded holds the cover paragraph first (Resize "1200x jpg q80" Permalink), then .Content with every root-relative src or href made absolute. Use replaceRE with the pattern (src|href)="/([^/]) and the replacement ${1}="<baseURL without trailing slash>/${2}. FA's absURL pipe does not absolutize in-body paths, so it is not the tool here.
7. Rerun python3 scripts/sync-cr.py --offline and confirm the generated tree is unchanged (see verify).
8. Run bash tests/validate-cr.sh in full mode.
9. Commit the script changes, templates, data/cr-legacy.json and all 51 bundles. The commit is large because of the images; that matches how content/fa/ is committed.
  </action>
  <verify>
    <automated>git add content/cr data/cr-legacy.json && python3 scripts/sync-cr.py --offline && git diff --quiet -- content/cr data/cr-legacy.json && test "$(find content/cr -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')" = 51 && bash tests/validate-cr.sh</automated>
  </verify>
  <done>content/cr/ holds exactly 51 bundles. An --offline rerun reproduces them byte-for-byte with zero network calls. /cr/ lists all 51 newest-first by year, and /cr/index.xml is a full-content feed with absolute URLs. Full-mode validate-cr.sh passes. Every remaining WARN is accounted for in the SUMMARY. Committed.</done>
</task>

<task type="auto">
  <name>Task 3: Make the room look like the house, give CR its own head metadata, and lock in pre-cutover invisibility</name>
  <files>themes/arcaeon/layouts/cr/single.html, themes/arcaeon/layouts/_default/baseof.html, themes/arcaeon/assets/css/main.css, tests/validate-cr.sh</files>
  <action>
1. cr/single.html:
   - Add the compact masthead (partials/cr/masthead.html, compact true) in a leading fa-band section, as fa/single.html does.
   - Replace the closing band with an older/newer neighbor nav built from partials/cr/posts.html. Use the same loop and the same fa-after / fa-after__neighbors / fa-after__link markup as fa/single.html, without the email CTA, and finish with "All posts →" to /cr/.
   - Do not include the FA mentions partial.
2. baseof.html, a scoped edit that leaves FA and notes behavior untouched:
   - Add $inCR as eq .Section "cr". $siteName becomes "Contemplating Resonance" when $inCR, keeping the FA case.
   - The title branch for the CR section page reads "Contemplating Resonance — Matt Stine".
   - Add an else-if branch for CR pages (IsPage): ogType article, ogTitle .Title, $desc from subtitle, and the og image from the bundle's cover.jpg, mirroring the $isEssay branch.
   - Add a branch for the CR section page: ogTitle "Contemplating Resonance — Matt Stine", desc from lede.
   - Add CR feed discovery (link rel alternate to /cr/index.xml, title Contemplating Resonance) rendered ONLY when $inCR, so no page outside /cr/ mentions it.
3. main.css: append one block headed with a Contemplating Resonance (/cr/) comment. Use only existing custom properties and tokens, and keep WCAG AA contrast by reusing the text colors of .fa-post__meta and .fa-prose.
   - .cr-masthead and its compact variant: spacing parallel to .fa-masthead.
   - .cr-masthead__title in var(--font-display) (Cinzel) with the existing display weight tokens.
   - .cr-masthead__lede.
   - .cr-prose figure (block margins), .cr-prose figcaption (smaller, centered, muted token).
   - .cr-prose table set to display block and overflow-x auto, so nothing scrolls horizontally at 375px.
   - .cr-footnote, smaller text.
   - .cr-player and .cr-player--pending: a bordered note box using an existing accent token, legible at 375px.
4. validate-cr.sh, appended:
   a. Every CR post page has og:type article and an og:image. Use the same regex style as validate-fa.sh's OG check, which tolerates minified unquoted attributes.
   b. Every CR post title tag ends with "| Contemplating Resonance".
   c. A clearly labeled "Pre-cutover: /cr/ is unlinked — delete this block on cutover day" block. It parses every .html file in the build outside <public>/cr/ and fails if any a href (relative, root-relative, or absolute falkensmage.com) points into /cr/, or if <public>/index.html contains /cr/ at all.
   d. INFO lines (not failures) counting how many /cr/ URLs appear in sitemap.xml and the home feed index.xml. Comment that both only go live on merge, which is cutover day per the FA precedent, so nothing extra is gated now (the task's "keep it simple" choice). A sitemap opt-out would be front-matter sitemap disable cascaded from content/cr/_index.md, but it is deliberately not added.
5. Regression and invariants:
   - Run bash tests/validate-cr.sh, then hugo --minify --quiet followed by bash tests/validate-fa.sh, which must still report 13 passed, 0 failed.
   - Confirm git diff against the merge-base with origin/main is empty for the nav header partial, the home template, content/_index.md and .github/workflows.
6. Commit. Do not merge, do not open a PR, do not touch .github/workflows.
  </action>
  <verify>
    <automated>bash tests/validate-cr.sh && hugo --minify --quiet && bash tests/validate-fa.sh && git diff --quiet "$(git merge-base HEAD origin/main)" -- themes/arcaeon/layouts/partials/nav/header.html themes/arcaeon/layouts/index.html content/_index.md .github/workflows && test "$(git branch --show-current)" = cr/own-the-stack</automated>
  </verify>
  <done>CR pages wear the arcaeon look, with a Cinzel text masthead, figure/caption styling, a legible pending-player box and neighbor nav. They carry their own title, og tags and feed discovery, scoped to /cr/ only. validate-cr.sh passes including the pre-cutover invisibility block and reports sitemap and home-feed exposure as INFO. validate-fa.sh still passes 13/13. The nav, home and workflows are untouched. Still on cr/own-the-stack, unmerged.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Substack API → sync-cr.py | Remote JSON and body_html are untrusted input. They become HTML that Hugo publishes unescaped. |
| Image hosts → cache → repo | Remote bytes land on disk and are then committed and served from falkensmage.com. |
| Local secrets → sync-cr.py | The Substack cookie file sits next to the workflow and must never cross into output, logs or git. |
| Branch → production | Anything merged to main deploys; /cr/ must not go live before cutover. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261115-fjc-01 | Tampering / Elevation (stored XSS) | sanitize_body → content/cr/*/index.html rendered via .Content | high | mitigate | Tag allowlist with removal of script/style/iframe/form/input/button/svg/object/embed. An attribute allowlist strips on*, style, class (except cr-footnote) and data-*. javascript: and data: links are unwrapped. validate-cr.sh check (d) parses every body and fails on any violation. |
| T-261115-fjc-02 | Information disclosure | ~/Inbox/substack-cookies.txt | high | mitigate | Read only with an explicit --cookie-file and never by default. Error text carries slug and HTTP status only. The cookie is never written to the cache or repo; the cache lives at ~/.cache/sync-cr outside the repo. The final verification scans the branch diff for session-cookie names. |
| T-261115-fjc-03 | Denial of service (Substack rate limit / account standing) | network helper in sync-cr.py | medium | mitigate | A single request helper sleeps ≥3s before every live call. All post JSON and image bytes are cached, --offline proves reruns make zero calls, and --refresh is opt-in. |
| T-261115-fjc-04 | Tampering (path traversal) | slug → content/cr/<slug>/ and cache paths | medium | mitigate | Slug must match ^[a-z0-9-]+$ or the run exits 1. Bundle image names are generated (cover.jpg, img-NN.ext) and cache names are sha1 digests; neither is taken from remote URLs. |
| T-261115-fjc-05 | Tampering (malicious file) | downloaded image bytes | low | mitigate | Magic-byte sniff accepts JPEG/PNG/GIF/WebP only. Bytes are processed only by sips and stored in a cache directory separate from scripts. Nothing in the cache is executed or imported. |
| T-261115-fjc-06 | Information disclosure (gated content) | listing posts with non-public audience | medium | mitigate | The two gated slugs are excluded by name, and the run aborts if any other non-"everyone" post appears. validate-cr.sh check (b) asserts the dropped slugs are absent. |
| T-261115-fjc-07 | Information disclosure (premature launch) | /cr/ section visibility | low | mitigate | No nav/home link and no workflow wiring; the branch stays unmerged. The validate-cr.sh pre-cutover block fails on any inbound link from outside /cr/. Sitemap and home-feed inclusion are reported as INFO and documented as live only at merge (cutover). |
| T-261115-fjc-SC | Tampering | Python packages | low | accept | No package-manager installs in this plan. Uses stdlib plus beautifulsoup4 4.12.3 already present in the pyenv interpreter. The script exits with a message if bs4 is missing rather than installing. |
</threat_model>

<verification>
Baselines recorded at HEAD (2026-11-15, branch cr/own-the-stack, clean tree):
- tests/validate-cr.sh does not exist, so the gate fails at HEAD. Target: exit 0.
- content/cr/ does not exist (0 bundles). Target: 51.
- tests/validate-fa.sh: 13 passed, 0 failed. Target: unchanged.
- The merge-base diff of the nav header, home template, content/_index.md and .github/workflows is empty and must stay empty (an invariant, not a new gate).
- No built page links to /cr/ (trivially true at HEAD). The pre-cutover block keeps it true.

Final checks after Task 3, from the checkout root:
1. bash tests/validate-cr.sh → exit 0, with INFO lines for sitemap and home-feed /cr/ counts.
2. hugo --minify --quiet && bash tests/validate-fa.sh → 13 passed, 0 failed.
3. ! grep -rEq 'substackcdn|substack-post-media|bucketeer-' content/cr data/cr-legacy.json
4. test ! -e content/cr/your-august-2024-contemplative-alchemist && test ! -e content/cr/your-august-2024-paid-member-discount
5. ! git diff "$(git merge-base HEAD origin/main)" -- . | grep -Eiq 'substack\.sid|connect\.sid' (no session cookie in the branch)
6. ! grep -rq 'validate-cr' .github/workflows
7. git branch --show-current prints cr/own-the-stack, and git log origin/main..HEAD shows only this task's commits.

SUMMARY must record:
- The third tracer slug.
- Counts: posts, podcasts, covers, inline images.
- Every remaining WARN, with its reason.
- Any non-Substack image hosts left in place.
- The sitemap and home-feed exposure note: /cr/ appears in both once built, which is harmless while unmerged; merge happens on cutover day per FA precedent. The opt-out, if ever wanted, is a cascaded front-matter sitemap disable in content/cr/_index.md.
- That validate-cr.sh is deliberately not in the deploy workflow.
</verification>

<success_criteria>
- 51 page bundles at content/cr/<exact-substack-slug>/, each with index.html (HTML content format) and self-hosted images. The 2 gated posts are absent.
- /cr/, /cr/<slug>/ and /cr/index.xml build and render in the arcaeon look. Podcast pages show duration and a pending-player notice, with an empty media_url ready for the hosting decision.
- Zero Substack-hosted asset references and zero active content in CR output.
- tests/validate-cr.sh passes. tests/validate-fa.sh is unchanged at 13/13.
- /cr/ is unlinked from the rest of the site, absent from the nav, the home page and the deploy workflow. The branch is unmerged with no PR opened. Pushing the branch is left to the orchestrator.
</success_criteria>

<output>
Create `.planning/quick/261115-fjc-scaffold-contemplating-resonance-section/261115-fjc-SUMMARY.md` when done
</output>
