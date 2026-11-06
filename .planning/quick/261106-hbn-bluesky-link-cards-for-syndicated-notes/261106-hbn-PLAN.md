---
phase: quick-261106-hbn
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/syndicate-notes.py
  - tests/test-notes.py
autonomous: true
requirements:
  - QUICK-261106-hbn

estimate:
  tokens: 85000
  raw_tokens: 85000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "A note whose text links a page other than its own permalink goes to Bluesky with an app.bsky.embed.external card for the FIRST such link, titled and described from the page's og:title / og:description (falling back to <title> / meta description)"
    - "When the page's og:image is a JPEG, PNG or WebP of at most 1,000,000 bytes, it is uploaded with com.atproto.repo.uploadBlob and attached as the card's thumb; too big, wrong type or failed means a card with no thumb"
    - "A note with no link, or only its own permalink, goes to Bluesky exactly as before: no embed, no card fetch, no uploadBlob, no card log line"
    - "No card failure (page not 200, no title, bad or failed thumb, uploadBlob failure, the PDS refusing the embed, any exception) fails or blocks a post; each logs one line and the post goes out without the card or without the thumb, with the same exit code it would have had"
    - "The card never creates a second record: the deterministic rkey and the getRecord-first RecordNotFound -> createRecord loop are unchanged; a lost createRecord response with a card is one record; a PDS-refused card is posted again WITHOUT the embed through the same getRecord-first loop on the same key"
    - "The Bluesky session token never reaches a card target: card page and image fetches carry no Authorization header and use their own opener, and OPENER stays redirect-free"
    - "Mastodon posting, notes.yml and the data/syndication.json format are unchanged (a bluesky record is still exactly {url, uri, posted})"
    - "The module docstring describes the card behavior, its limits and its explicit opt-outs; the old line listing embed and uploadBlob as out of scope is gone"
  artifacts:
    - path: "scripts/syndicate-notes.py"
      provides: "card_target, _card_get, _CardMeta, _image_type, _upload_thumb, _card_thumb, link_card, CARD_OPENER, _CardRejected; post_bluesky attaching record['embed']; the rewritten docstring"
      contains: "app.bsky.embed.external"
    - path: "tests/test-notes.py"
      provides: "Stub.pages and Stub uploadBlob; the SyndicationCase.CARDS switch; the LinkCards test class"
      contains: "class LinkCards"
  key_links:
    - from: "scripts/syndicate-notes.py post_bluesky"
      to: "link_card"
      via: "record['embed'] set once, before the getRecord/createRecord loop, from the text post_bluesky received (pre-fit)"
      pattern: "record\\[\"embed\"\\]"
    - from: "scripts/syndicate-notes.py _upload_thumb"
      to: "com.atproto.repo.uploadBlob"
      via: "_bsky(..., raw=bytes, ctype=mime) with the run's session token"
      pattern: "com.atproto.repo.uploadBlob"
    - from: "tests/test-notes.py SyndicationCase.setUp"
      to: "m.link_card"
      via: "patched to return None unless the class sets CARDS = True"
      pattern: "CARDS"
---

<objective>
Give syndicated notes a Bluesky link card. scripts/syndicate-notes.py posts each note to Bluesky with text and facets but no embed, so a note that links an essay or an external post shows no preview card. Add an `app.bsky.embed.external` card, built best-effort, that can never block, fail or double a post.

Purpose: on 2026-11-06 Matt took Mastodon and Bluesky off the third-party scheduler. An FA essay's launch post is now a falkensmage.com note. The scheduler's Bluesky posts had link cards, and on Bluesky the card is what drives the click, so without this change every essay launch regresses there. Mastodon needs nothing, because the instance builds its own card from the URL's OG tags.

Output: the card code and its docstring in scripts/syndicate-notes.py; the stub extensions, a CARDS switch and a LinkCards test class in tests/test-notes.py. Three commits, not pushed.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@scripts/syndicate-notes.py
@tests/test-notes.py

## Facts the planner verified (do not re-derive)

- Baseline: `for f in tests/test-*.py; do python3 -I -S -B "$f" || exit 1; done` passes at HEAD in about 80 s. Local Python is 3.10.0, and the script must stay 3.10-compatible and stdlib-only.
- `python3 -I -S -B tests/test-notes.py -k <ClassName>` filters with unittest's `-k`. `-k` can be repeated.
- **Test-harness trap.** The fixture note ALPHA links `https://example.com/a`. The socket guard raises `OutboundBlocked`, which is a **BaseException** on purpose, so the card's `except Exception` cannot swallow it. With a real card builder, every existing Bluesky test that posts ALPHA would error. That is why `SyndicationCase` gets a `CARDS = False` switch that patches `m.link_card` off by default (Task 1). The card tests opt in and serve their pages from the loopback stub.
- **Source-text trap.** `BlueskyPosting.test_a_note_reaches_bluesky_directly_and_nothing_else_is_called` asserts that the lowercased script source does not contain the name of the old social scheduling service. Do not write that word anywhere in scripts/syndicate-notes.py, in any case: not in the docstring rationale, not in a variable name for raw bytes. Write "the old scheduler" if you need to.
- **Real-world cap check.** Essay pages emit `og:image` as a 1200x630 JPEG crop from `themes/arcaeon/layouts/_default/baseof.html` (lines 63-69). Across 116 built covers the largest is 161 KB, so the 1,000,000-byte blob cap does not cost the main use case its thumbnail and no resizing is needed. That is fortunate, because stdlib has no image codec.
- Python 3.10's `urllib.request.HTTPRedirectHandler` follows 301, 302, 303 and 307 (308 from 3.11). Its class attribute `max_redirections` defaults to 10. Tests use 301.
- `html.parser.HTMLParser` with `convert_charrefs=True` already unescapes entities in data and in attribute values.

## Design refinements (planner, each with its reason; the brief allowed refinements)

- R1 **Card target from the pre-fit text.** Pick the target from the text `post_bluesky` received, before `_fit` reassigns `text`. When a long note is cut, the card is the one place its lead link survives the cut.
- R2 **Separate `CARD_OPENER` that follows up to 5 redirects; `OPENER` stays redirect-free.** A Hugo URL without its trailing slash, an http-to-https hop or a custom-domain hop answers 3xx, and without following it that link silently gets no card. No credential ever travels on `CARD_OPENER`. Like `OPENER`, it has no ProxyHandler.
- R3 **`fetch` is left unchanged.** It is the live-page check, where None means "not deployed yet". Card fetches need different caps, a shorter timeout and redirects.
- R4 **Page cap is a prefix, not a refusal.** Read at most `CARD_PAGE_BYTES` (1,000,000) and parse that prefix. OG tags live in `<head>`, so a big page still yields its card.
- R5 **Thumb type by magic bytes,** never by the Content-Type header, which a server can set to anything.
- R6 **No title means no card.** Neither og:title nor `<title>` means no embed, because a card with an empty title renders as a blank box.
- R7 **One card per `post_bluesky` call,** built after the session exists and before the attempt loop, and reused by every retry in that loop. On the rare adopt path (getRecord finds the post), the uploaded blob is never referenced and the PDS discards unreferenced blobs. Accepted, because it keeps the idempotency loop untouched.
- R8 **PDS refuses the card, so post again without it.** If createRecord answers a non-transient 400 for a record that carries an embed, the same getRecord-first loop runs once more on the same rkey with the embed removed. Without this, a card the PDS rejects would fail the post on every run, breaking "never fail a post because of the card". It is safe because the key is unchanged and getRecord is asked first, so the second pass adopts rather than duplicates.
- R9 **One uploadBlob attempt, no retry,** because the thumb is best effort.
- R10 **Logs:** the slug, plus a fixed reason or an exception's type name. Never the target URL, the title, the description or page text, because the URL is part of the note text and the logs never carry note text.
- R11 **Metadata read:** og:title, og:description and og:image, taken from `property=` or, failing that, `name=`, plus `<title>` and `meta name=description`. twitter:*, oEmbed and JSON-LD are explicit opt-outs, recorded in the docstring per design principle 11 (opt out explicitly, never by omission).
- R12 **DRY_RUN builds no card.** uploadBlob is a write, and `test_a_dry_run_makes_no_bluesky_call` already asserts that a dry run makes no XRPC call.
</context>

<tasks>

<task type="tracer">
  <name>Task 1: End-to-end link card: a note linking an essay posts to Bluesky with an external card and an uploaded thumb</name>
  <files>scripts/syndicate-notes.py, tests/test-notes.py</files>
  <read_first>
    - scripts/syndicate-notes.py lines 233-241 (OPENER: why it has no redirect handler and no proxy), 251-256 (one_line), 634-649 (fetch: leave it as it is, per R3), 747-806 (find_urls, facets), 874-1011 (_BSKY, _bsky, _login, bluesky_token, post_bluesky)
    - tests/test-notes.py lines 1099-1286 (Stub: do_GET, do_POST, the per-call script lists, the request log), 1288-1358 (SyndicationCase.setUp patches, token(), run_main), 1689-1765 (Tracer: the end-to-end assertion style), 1793-1813 (PostCase.run_post), 2091-2103 (BlueskyCase), 2347-2360 (LengthPosting: calling m.post_bluesky directly inside self.token())
  </read_first>
  <action>
Script, scripts/syndicate-notes.py. Put the new code in the Bluesky section after `tid`, under its own `# --- Bluesky: the link card ---` divider.

1. Constants: `EMBED_EXTERNAL = "app.bsky.embed.external"`, `CARD_TIMEOUT = 10`, `CARD_PAGE_BYTES = 1_000_000`, `CARD_REDIRECTS = 5`, `BLOB_MAX = 1_000_000` (Bluesky's thumb limit), `CARD_TITLE_MAX = 300`, `CARD_DESC_MAX = 1000`.
2. `CARD_OPENER`, per R2. An `urllib.request.OpenerDirector` built like `OPENER`, plus a subclass `_CardRedirect(urllib.request.HTTPRedirectHandler)` with `max_redirections = CARD_REDIRECTS`. Handlers: UnknownHandler, HTTPDefaultErrorHandler, _CardRedirect, HTTPErrorProcessor, HTTPHandler, HTTPSHandler, and no ProxyHandler. Add a one-line comment saying why it is separate: OPENER carries credentials and must never follow a redirect, and nothing secret is ever sent on CARD_OPENER. Do not change OPENER or fetch.
3. `_card_get(url, accept, cap)` returns `(final_url, charset, data)` or None. It sends a GET with only `User-Agent: UA` and `Accept: accept`, never an Authorization header, through CARD_OPENER with `timeout=CARD_TIMEOUT`. It returns None unless the status is 200. It reads at most `cap + 1` bytes, takes `final_url` from `r.geturl()` and `charset` from `r.headers.get_content_charset()`. HTTPError is closed and gives None. URLError, TimeoutError, OSError, http.client.HTTPException and ValueError give None.
4. `_CardMeta(html.parser.HTMLParser)` with `convert_charrefs=True`. For each `meta` tag, the key is the lowercased, stripped `property` attribute, or the `name` attribute when `property` is absent. Record the FIRST `content` seen for the keys og:title, og:description, og:image and description. Also record the text of the first `<title>` element. Read nothing else and reference no other resource (R11).
5. `card_target(note, text)`: walk `find_urls(text)` in order and return the first URL that is not the note itself, else None. "Itself" means: with any `#fragment` removed and a trailing `/` stripped, the URL equals `SITE + note.path` normalized the same way. Read `SITE` at call time, because tests patch it.
6. `_image_type(data)` returns `"image/jpeg"` when data starts with bytes FF D8 FF, `"image/png"` when it starts with the 8-byte PNG signature, `"image/webp"` when bytes 0-3 are `RIFF` and bytes 8-11 are `WEBP`, and None otherwise (R5).
7. Extend `_bsky` with keyword-only `raw=None, ctype=None`. When `raw` is given, send those bytes as the body with `Content-Type: ctype` instead of a JSON body. Everything else stays the same: no redirect, no body printed, the same (status, doc) return. The test wrapper in `test_a_uri_that_does_not_end_with_the_key_is_refused` passes `**kw` through and keeps working.
8. `_upload_thumb(token, data, mime)`: exactly one `_bsky("POST", "com.atproto.repo.uploadBlob", token=token, raw=data, ctype=mime)` (R9). Return a freshly built dict `{"$type": "blob", "ref": {"$link": link}, "mimeType": mt, "size": n}`, never the server's object passed through, and only when all of these hold: the status is 200; the response's `blob` is a dict whose `$type` is "blob"; `ref.$link` is a str; `mimeType` is a str starting with "image/"; `size` is an int from 1 to BLOB_MAX. Otherwise return None.
9. `_card_thumb(note, token, page_url, og_image)` returns the blob or None. Steps: urljoin the stripped og_image against `page_url`, the post-redirect URL; require an http or https scheme and a hostname; `_card_get` it with accept `"image/jpeg,image/png,image/webp"` and cap BLOB_MAX; refuse a body longer than BLOB_MAX; refuse what `_image_type` does not recognise; then `_upload_thumb`. Each refusal logs exactly one line, `{slug} bluesky: link card without a thumbnail ({reason})`, with a fixed reason: "the image did not answer 200", "the image is over 1,000,000 bytes", "the image is not JPEG, PNG or WebP", "uploadBlob failed". The whole body sits in `except Exception`, which logs the same line with `type(e).__name__` as the reason and returns None.
10. `link_card(note, text, token)` returns the embed dict or None. Steps:
    - `target = card_target(note, text)`. If it is None, return None and log nothing: the post goes out exactly as today.
    - `_card_get(target, "text/html,application/xhtml+xml", CARD_PAGE_BYTES)`. If that is None, log `{slug} bluesky: no link card (the page did not answer 200)` and return None.
    - Decode `data[:CARD_PAGE_BYTES]` with the charset, or utf-8 when the charset is absent or raises LookupError, using `errors="replace"`, and feed it to `_CardMeta` (R4).
    - title = og:title, or else `<title>`. description = og:description, or else meta description, or else "". Clean each with `one_line`, capped so the stored string is at most CARD_TITLE_MAX / CARD_DESC_MAX code points including the ellipsis: pass the max minus one, because one_line appends one "…" when it cuts.
    - Empty title: log `{slug} bluesky: no link card (the page has no title)` and return None (R6).
    - Build `external = {"uri": target, "title": ..., "description": ...}`. The uri is the URL as written in the note, not the post-redirect one. When og:image is present, set `external["thumb"]` to the `_card_thumb` result if it is not None. With no og:image, log `link card without a thumbnail (the page has no og:image)`.
    - Log `{slug} bluesky: link card attached, with a thumbnail` or `, without a thumbnail`, and return `{"$type": EMBED_EXTERNAL, "external": external}`.
    - The whole body sits in `except Exception`, which logs `{slug} bluesky: no link card ({type name})` and returns None. Catch Exception, not BaseException, so KeyboardInterrupt and the tests' OutboundBlocked still propagate.
    - Per R10, no log line carries the URL, title, description or page text.
11. `post_bluesky`: keep the text it received under its own name before the `_fit` line reassigns `text`. After the facets block and before the attempt loop, call `link_card(note, <received text>, token)` through the module-global name, so tests can patch `m.link_card`. When the result is a dict, set `record["embed"]` to it (R1, R7). Do not touch the attempt loop in this task.

Tests, tests/test-notes.py:

12. Stub:
    - Add `self.pages = {}`. It maps a request path without its query to `(status, content_type, body_bytes)` or `("redirect", status, location)`. Consult it in `do_GET` right after the getRecord branch and before the site lookup, serving the body or a 3xx with a Location header.
    - Add uploadBlob to `do_POST`. The path `/xrpc/com.atproto.repo.uploadBlob` goes to a new `_bsky_upload(body)` driven by a script list `self.bsky_upload` ("ok" or ("status", code[, error])), the same shape as the other Bluesky scripts. It requires `_authorized()`, appends `{"mime": <request Content-Type>, "data": body}` to `self.blobs`, and answers 200 with `{"blob": {"$type": "blob", "ref": {"$link": "bafkreistub<n>"}, "mimeType": <request Content-Type>, "size": len(body)}}`.
    - Add a helper `uploads()` that returns `self.xrpc("com.atproto.repo.uploadBlob")`, and extend the Stub docstring to describe pages and uploadBlob.
13. SyndicationCase: add the class attribute `CARDS = False`, with a docstring sentence giving the reason: fixture notes link example.com, and the guard's OutboundBlocked is a BaseException the card's guard rightly cannot swallow. In setUp, when `not self.CARDS`, add `link_card=lambda note, text, token: None` to the `patches` dict. Change no existing test.
14. Module-level fixtures near the other syndication fixtures:
    - Byte constants `CARD_PNG` (the PNG signature plus 64 zero bytes), `CARD_JPEG` (FF D8 FF E0 plus padding), `CARD_WEBP` (`RIFF`, four length bytes, `WEBP`, plus padding) and `CARD_GIF` (`GIF89a` plus padding).
    - A builder `card_html(*, og_title=None, og_description=None, og_image=None, title=None, description=None, body="")` that returns UTF-8 bytes of a small HTML page holding only the tags it was given.
15. A new class `LinkCards(BlueskyCase)` placed after `LengthPosting`:
    - `CARDS = True`.
    - Helpers: `url(path)`, which returns `self.stub.base + path`; `serve(path, body, ctype="text/html; charset=utf-8", status=200)`, which sets `self.stub.pages[path]`; and `post(text)`, which runs `m.post_bluesky(m.read_note(m.NOTES / "alpha.md"), text)` inside `self.token()` with stdout captured and returns `(stored_record, log_text)`, where stored_record is `self.stub.records[self.rkey()]["record"]`.
    - The tracer test `test_a_note_linking_an_essay_posts_to_bluesky_with_an_external_card_and_an_uploaded_thumb`:
      - Serve `/card/essay/` with og:title "Card Title", og:description "Card description." and og:image `self.url("/card/thumb.png")`, and serve `/card/thumb.png` as CARD_PNG with type "image/png".
      - Patch `m.wait_live` to `lambda note, tries: "New essay: " + self.url("/card/essay/")`, then call `self.run_post(expect_rc=0)`.
      - Assert exactly one uploadBlob request, with content-type image/png, body equal to CARD_PNG and authorization `Bearer FAKE_JWT`.
      - Assert that the createRecord body's `record["embed"]` equals `{"$type": "app.bsky.embed.external", "external": {"uri": <essay url>, "title": "Card Title", "description": "Card description.", "thumb": {"$type": "blob", "ref": {"$link": <the stub's link>}, "mimeType": "image/png", "size": len(CARD_PNG)}}}` exactly.
      - Assert that every request outside `/xrpc/` has no authorization header (the token never reaches the card target).
      - Assert that `set(self.local_state()["notes"][ALPHA_PATH]["bluesky"])` is `{"url", "uri", "posted"}`, that `self.recorded()` is `["bluesky", "mastodon"]`, and that the Mastodon form's status equals the note text (that path is unchanged).
      - Assert that the run's output contains neither "/card/" nor "Card Title" (R10).

Commit when the full loop passes. The message is `feat(notes): attach a Bluesky link card to syndicated notes`, ending with the line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Do not push.
  </action>
  <verify>
    <automated>python3 -I -S -B tests/test-notes.py -k LinkCards && for f in tests/test-*.py; do python3 -I -S -B "$f" || exit 1; done</automated>
  </verify>
  <done>The LinkCards tracer test passes: a note linking an essay page reaches the stub PDS with an app.bsky.embed.external embed carrying the page's OG title and description and a thumb whose blob came from uploadBlob. No request outside /xrpc/ carries an Authorization header. Every pre-existing test in all five suites still passes unchanged, with the card switched off by default. One commit is made and nothing is pushed.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Best effort, never blocking, never doubling: every card failure still posts exactly once</name>
  <files>scripts/syndicate-notes.py, tests/test-notes.py</files>
  <read_first>
    - scripts/syndicate-notes.py post_bluesky as Task 1 left it (the attempt loop, from `why = "no attempt"` to the `for ... else` raise), plus link_card, _card_thumb and _image_type
    - tests/test-notes.py LinkCards (Task 1), plus BlueskyPosting tests test_a_response_lost_after_the_record_was_made_is_adopted_by_getrecord_not_recreated and test_createrecord_4xx_is_not_retried (around lines 2158-2215), which must keep passing unchanged
  </read_first>
  <behavior>
    - Card target: for the text "self <SITE>/notes/alpha/ first <stub>/card/one/ then <stub>/card/two/", the embed uri is /card/one/, and /card/two/ gets no GET.
    - No link, or only the note's own permalink (with or without its trailing slash): no "embed" key in the record, no request outside /xrpc/, no uploadBlob, and no "link card" text in the log. The post is made.
    - A page with no og tags gives a title from <title> and a description from meta name=description. A page with og:title but no description gives description "".
    - A page with neither og:title nor <title>: no embed, the post is made, and the log says "no link card (the page has no title)".
    - A card page answering 404 or 500: no embed, the post is made, one "no link card" log line.
    - A redirect: /card/moved/ answers 301 to /card/essay/, whose og:image is the RELATIVE "thumb.png". The embed uri is the note's /card/moved/ URL, the title comes from /card/essay/, and the thumb was fetched from /card/essay/thumb.png (resolved against the final URL).
    - An og:image of 1,000,001 bytes (PNG signature then padding): the card has no "thumb", there are zero uploadBlob calls, and the log says "over 1,000,000 bytes". An image of exactly 1,000,000 bytes gets a thumb.
    - CARD_GIF served with Content-Type image/png: no thumb, no uploadBlob, and the log says "not JPEG, PNG or WebP" (magic bytes win over the header).
    - An og:image answering 404 gives no thumb and the card is still attached.
    - uploadBlob answering 500: the card is attached without a thumb, there is exactly one uploadBlob request (no retry), and the post is made.
    - m._card_get patched to raise RuntimeError("secret-looking detail"): the post is made with no embed, the log carries "RuntimeError" and not the message text.
    - Card text: an og:title of 400 characters is stored with at most 300 code points, ending in "…". An og:description of 1500 is stored with at most 1000. "A &amp; B\n\n  C" is stored as "A & B C".
    - Lost createRecord response with a card (bsky_create=["lose"]): one record in the stub, one createRecord, two getRecord, exactly one uploadBlob, the stored record has the embed, and the state records bluesky once.
    - PDS refuses the card (bsky_create=[("status", 400, "InvalidRequest")] with a card): createRecord is called twice on the same rkey, getRecord is asked before each, the stub holds one record with no "embed" key, post_bluesky returns normally, and the log says "refused the link card".
    - _image_type unit cases: JPEG, PNG and WebP recognised; GIF, b"" and b"RIFF\0\0\0\0WAVE" return None.
    - Across a successful card and a failed card, the log never contains "/card/" or the page title.
  </behavior>
  <action>
RED: add the behavior list as tests in the LinkCards class, using its serve, post and url helpers and the fixtures from Task 1. Each test drives `post_bluesky` directly through the `post` helper. The exception is the lost-response test, which also uses `self.run_post` with `m.wait_live` patched (as the Task 1 tracer does) to show the state records Bluesky once. Run them. The PDS-refusal test must fail, because Task 1 left the loop untouched. Fix any other failure in the card code, not in the test, unless the test contradicts this plan.

GREEN, per R8. In scripts/syndicate-notes.py:
- Add `class _CardRejected(PostError)` with the docstring "createRecord answered 400 for a record carrying a link card: no record was written, and the card is the likely cause."
- In `post_bluesky`, move the existing attempt loop verbatim into a nested function `put(record)` that returns `uri`. That means the `why` initialisation, the getRecord-first branches, `createdAt` set per create attempt, the transient retry, the sleep, and the for/else raise all move unchanged. The ONLY edit inside it: in the non-transient createRecord branch, raise `_CardRejected` with the identical message when `status == 400 and "embed" in record`, and `PostError` otherwise, exactly as today.
- After the record is built, call `uri = put(record)` inside `try`. On `_CardRejected`, log `{slug} bluesky: the PDS refused the link card; posting without it`, delete `record["embed"]`, and call `uri = put(record)` again.
- The rkey is the same and getRecord is asked first, so the second pass adopts any record the first pass might have written and can never make a second one.
- A record with no embed never takes the second pass, so `test_createrecord_4xx_is_not_retried` still sees exactly one createRecord.

REFACTOR only if a helper grew past what one reading holds. Keep stdlib only and Python 3.10 syntax.

Commit when the verify command passes. The message is `feat(notes): a Bluesky link card never blocks or doubles a post`, ending with the line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Do not push.
  </action>
  <verify>
    <automated>python3 -I -S -B tests/test-notes.py -k LinkCards -k BlueskyPosting -k LengthPosting -k AtMostOnce -k Tracer -k GuardTests -k BaseSetUp</automated>
  </verify>
  <done>Every behavior above is a passing test in LinkCards. A PDS-refused card is posted without the embed on the same rkey through the unchanged getRecord-first loop. The existing BlueskyPosting, AtMostOnce, LengthPosting, Tracer and guard tests pass unchanged. One commit is made and nothing is pushed.</done>
</task>

<task type="auto">
  <name>Task 3: Rewrite the module docstring to describe link cards, their limits and their opt-outs</name>
  <files>scripts/syndicate-notes.py</files>
  <read_first>
    - scripts/syndicate-notes.py docstring lines 1-154, especially "What each failure does" (99-119), "Env" (121-123), "Bluesky coverage, AT Protocol" (137-151) and the closing "Logs carry" line (153)
  </read_first>
  <action>
Edit the module docstring in its existing voice: plain declarative sentences, reasons given inline, no marketing.

1. "Bluesky coverage, AT Protocol". Rewrite the In list so it adds: the record's `embed` of type app.bsky.embed.external when the note links a page other than itself; and com.atproto.repo.uploadBlob, one attempt, for the card's thumb. Rewrite the Out list so the sentence that put embed and uploadBlob out of scope is gone entirely. Keep each remaining opt-out with its reason:
    - embed images, video, record and recordWithMedia (a note has no attachments, and images are out of scope);
    - a card for any link but the first;
    - a card for the note's own permalink;
    - twitter:*, oEmbed and JSON-LD metadata (og plus `<title>` and the meta description is enough);
    - resizing or recompressing a thumb (stdlib has no image codec; essay covers are 1200x630 JPEG crops well under the limit);
    - retrying uploadBlob (the thumb is best effort);
    - a card in DRY_RUN (uploadBlob is a write).
   Keep every other existing In/Out item unchanged.
2. Add a short "Link cards (Bluesky only)" section after the Bluesky coverage section. It says:
    - The target is the first http(s) link in the note's text, as read from the live page and before any cut, that is not the note's own permalink.
    - No such link means the post goes out exactly as it would with no card code.
    - The page is fetched once, with a 10 s timeout and no credentials, through its own opener that follows up to 5 redirects. The API opener never follows one.
    - Only the first 1,000,000 bytes are read, and only meta tags and `<title>` are parsed. Fetched HTML is untrusted: nothing in it is executed or followed except the one og:image fetch.
    - The title and description are made single-line and capped at 300 and 1000 code points.
    - No title means no card.
    - The thumb is og:image only if it is JPEG, PNG or WebP by its bytes and at most 1,000,000 bytes, uploaded once. Otherwise the card goes without a thumb.
    - The card is built once per post, before the getRecord/createRecord loop, so the record key and the at-most-once protocol are unchanged. On the rare adopt path, the uploaded blob is never referenced and the PDS discards it.
    - A 400 from createRecord for a record carrying a card makes the same getRecord-first loop run once more, on the same key, without the card.
    - A card is made once, at post time. A target that was not live then gets no card, and a post is never edited to add one.
    - Mastodon needs no card code: the instance builds its own from the link's OG tags.
   Do not name the old scheduler in this rationale (see the source-text trap in context).
3. "What each failure does": add rows in the table's two-column style.
    - "No link but the note's own": no card, post as before.
    - "Card page not 200, no title, or any card error": post made with no card, a log line, exit unchanged.
    - "Thumb too big, not an image, or upload failed": card with no thumb, a log line.
    - "PDS refuses the card (400)": posted again without it, same key, getRecord first.
4. Extend the closing "Logs carry" line so it also says card lines carry the slug and a fixed reason, never the link, title or page text.
5. Keep the docstring's existing line width (about 96 columns), and keep "Stdlib only, Python 3.10-compatible".

Commit when the verify command passes. The message is `docs(notes): describe Bluesky link cards in the syndication docstring`, ending with the line `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Do not push.
  </action>
  <verify>
    <automated>python3 -I -S -B -c 'import importlib.util as u; s=u.spec_from_file_location("s","scripts/syndicate-notes.py"); m=u.module_from_spec(s); s.loader.exec_module(m); d=m.__doc__; assert "app.bsky.embed.external" in d and "com.atproto.repo.uploadBlob" in d and "external cards, records, video) and uploadBlob" not in d, "docstring gate"; print("doc ok")' && for f in tests/test-*.py; do python3 -I -S -B "$f" || exit 1; done</automated>
  </verify>
  <done>The docstring gate prints "doc ok". It fails at HEAD (planner-verified baseline: AssertionError), so it is a real gate. The docstring states the card's target rule, fetch limits, thumb rules, best-effort guarantee, the same-key fallback and the explicit opt-outs. All five test suites pass, including the existing ban on naming the old scheduler in the source. One commit is made and nothing is pushed.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| runner -> card target page | A URL taken from the note's text. Its HTML is untrusted input, read by the runner during a run that holds the Bluesky session token. |
| runner -> og:image host | The URL comes from untrusted HTML. Its bytes are untrusted and are uploaded to Matt's Bluesky repo. |
| runner -> bsky.social PDS | uploadBlob and createRecord carry the session token. The embed content derives from untrusted HTML. |
| script -> Actions log | Log lines are parsed by the runner, where `::` at the start of a line is a workflow command. |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-261106-hbn-01 | Information disclosure | _card_get / CARD_OPENER | high | mitigate | Card fetches send only User-Agent and Accept, through CARD_OPENER, which has no credential path. OPENER (which carries tokens) stays redirect-free. The tracer test asserts that no request outside /xrpc/ carries an Authorization header. |
| T-261106-hbn-02 | Tampering | _CardMeta / link_card | medium | mitigate | Only meta content and the first `<title>` text are read. Values go through one_line (control characters stripped, whitespace collapsed) and are capped at 300 and 1000 code points. Nothing is executed. The only further fetch is og:image. Tests cover unescaping and capping. |
| T-261106-hbn-03 | Tampering | _card_thumb | medium | mitigate | The image type comes from magic bytes (JPEG, PNG, WebP), never from the header. More than 1,000,000 bytes is refused before upload. The uploaded blob object is rebuilt from validated fields, never passed through from the server. GIF-labelled-as-PNG and oversize tests cover this. |
| T-261106-hbn-04 | Denial of service | link_card fetches | medium | mitigate | 10 s timeout per fetch, at most 5 redirects, a 1,000,000-byte read cap for the page and 1,000,001 for the image, one uploadBlob with no retry, and at most two fetches plus one upload per post. Any card failure posts without the card (tests for 404, 500, exception, upload 500). |
| T-261106-hbn-05 | Tampering (integrity of at-most-once) | post_bluesky put / _CardRejected | high | mitigate | The card is built before the unchanged getRecord-first loop and the rkey is unchanged. The refused-card fallback reruns the same loop on the same key (getRecord first). The lost-response-with-card and PDS-400-with-card tests assert one record. |
| T-261106-hbn-06 | Spoofing / injection | log lines | low | mitigate | Every card log line goes through log() with the `syndicate-notes:` prefix (so it never starts with `::`) and carries the slug plus a fixed reason or an exception's type name, never the URL, title or page text. A test asserts that neither "/card/" nor the title appears in the output. |
| T-261106-hbn-07 | Information disclosure (SSRF) | CARD_OPENER redirects | low | accept | The target is a link Matt wrote in his own note, and the fetch runs on an ephemeral GitHub runner with no credentials on that path. Redirects are bounded at 5 and limited by urllib to http(s). The response is only parsed for meta tags, never echoed. |
| T-261106-hbn-SC | Tampering | npm/pip/cargo installs | high | accept | No package is installed. The change is stdlib-only, enforced by running every suite under `python3 -I -S`. |
</threat_model>

<verification>
- `for f in tests/test-*.py; do python3 -I -S -B "$f" || exit 1; done` passes (about 80 s at baseline; expect slightly more).
- `python3 -I -S -B tests/test-notes.py -k LinkCards` passes, covering the tracer plus every behavior in Task 2.
- The docstring gate in Task 3 prints "doc ok".
- `git diff --stat HEAD~3` lists only scripts/syndicate-notes.py and tests/test-notes.py. `.github/workflows/notes.yml` and `data/syndication.json` are untouched.
- `git log -3 --format=%B` shows three conventional-style messages, each ending with the Co-Authored-By line, and `git status` shows the branch ahead of origin and not pushed.
</verification>

<success_criteria>
- A falkensmage.com note that links an essay goes to Bluesky with an app.bsky.embed.external card (OG title, description, and a thumb uploaded through uploadBlob), matching what the old scheduler's posts had.
- A note with no outside link posts exactly as before.
- No card failure of any kind fails, blocks or doubles a post. The rkey and the getRecord-first protocol are unchanged.
- Mastodon, notes.yml and the state file format are unchanged.
- The docstring documents the behavior and every opt-out explicitly.
</success_criteria>

<output>
Create `.planning/quick/261106-hbn-bluesky-link-cards-for-syndicated-notes/261106-hbn-SUMMARY.md` when done
</output>
