---
phase: quick-261030-kwk
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - themes/arcaeon/layouts/_default/baseof.html
  - themes/arcaeon/layouts/fa/single.html
  - themes/arcaeon/layouts/partials/fa/mentions.html
  - themes/arcaeon/assets/css/main.css
  - scripts/pull-webmentions.py
  - tests/test-pull-webmentions.py
  - tests/fixtures/webmention/example-mentions.jf2.json
  - tests/fixtures/webmention/hostile-mentions.jf2.json
  - data/webmention-blocklist.json
  - tests/validate-fa.sh
  - .github/workflows/hugo.yml
  - .gitignore
autonomous: true
requirements:
  - IW2-ENDPOINT
  - IW2-PULL
  - IW2-RENDER
  - IW2-BLOCKLIST
  - IW2-PROBE
  - IW2-DEGRADE
  - IW2-TESTS

estimate:
  tokens: 60000
  raw_tokens: 60000
  tasks: 3
  confidence: low

must_haves:
  truths:
    - "Every page advertises https://webmention.io/falkensmage.com/webmention through a link element with rel=webmention"
    - "Every build, on push and on the nightly cron, pulls the whole domain's mentions into a data file Hugo reads, with no client-side JS and no commit back to the repo"
    - "Likes, reposts and replies appear under an FA essay as names and escaped plain text, every link carries rel=nofollow ugc, and no third-party image loads"
    - "An essay with no mentions is byte-identical to the same essay built with no mention data at all"
    - "A private webmention never reaches the data file or a page"
    - "A blocklisted domain or author disappears on the next build, including a build where the pull failed or the secret is absent"
    - "A webmention.io outage still publishes the essay, keeps the last-good mentions on the page, and turns the run red in a job after deploy"
    - "With WEBMENTION_IO_TOKEN absent the deploy stays green and the log says so plainly"
    - "A 200 carrying zero mentions cannot blank existing mentions unless the public per-target endpoint agrees they are gone"
    - "The mention section sits outside the h-entry, so scripts/send-webmentions.py never treats a stranger's URL as a citation"
  artifacts:
    - path: "themes/arcaeon/layouts/_default/baseof.html"
      provides: "Webmention endpoint discovery on every page"
      contains: "webmention.io/falkensmage.com/webmention"
    - path: "themes/arcaeon/layouts/partials/fa/mentions.html"
      provides: "Escaped, names-only mention section, absent when an essay has none"
      contains: "hugo.Data.webmentions"
    - path: "scripts/pull-webmentions.py"
      provides: "Domain-wide pull, stdlib only, with last-good fallback and fail-loud exit"
      exports: ["get_json", "pull_all", "normalize", "apply_blocklist", "load_blocklist", "load_last_good", "witness_total", "write_data", "main"]
    - path: "tests/test-pull-webmentions.py"
      provides: "Pagination, blocklist, hostile content, outage and mutation-proof tests, no outbound network"
      min_lines: 250
    - path: "tests/fixtures/webmention/example-mentions.jf2.json"
      provides: "webmention.io's own example feed, one of every real shape"
    - path: "tests/fixtures/webmention/hostile-mentions.jf2.json"
      provides: "API-shaped feed of hostile mentions"
    - path: "data/webmention-blocklist.json"
      provides: "Committed domains and author URLs applied on every build"
      contains: "domains"
    - path: "tests/validate-fa.sh"
      provides: "Standing probe: endpoint present, render matches data, section stays safe and outside the h-entry"
      contains: "webmention endpoint advertised"
    - path: ".github/workflows/hugo.yml"
      provides: "Pull before Hugo, last-good cache, and the job that turns a failed pull red after deploy"
      contains: "mentions-probe"
  key_links:
    - from: "scripts/pull-webmentions.py"
      to: "themes/arcaeon/layouts/partials/fa/mentions.html"
      via: "data/webmentions.json, keyed by the path Hugo returns as .RelPermalink"
      pattern: "hugo.Data.webmentions"
    - from: ".github/workflows/hugo.yml"
      to: "scripts/pull-webmentions.py"
      via: "Pull step runs after cache restore and before Build with Hugo, with the token in that step's env only"
      pattern: "pull-webmentions.py"
    - from: ".github/workflows/hugo.yml"
      to: ".github/workflows/hugo.yml"
      via: "build job output carries the pull step's outcome to the mentions-probe job after deploy"
      pattern: "needs.build.outputs.mentions"
    - from: "themes/arcaeon/layouts/fa/single.html"
      to: "scripts/send-webmentions.py"
      via: "Section renders after the closing article tag, so entry_links never sees mention URLs"
      pattern: "fa/mentions.html"
    - from: "tests/validate-fa.sh"
      to: "data/webmentions.json"
      via: "Probe compares element counts on each essay with the pulled data"
      pattern: "webmentions.json"
---

<objective>
IndieWeb run 2, receive: when someone replies to, likes or reposts a Feral Architecture essay, it shows up under the essay, with no client-side JS, no third-party image, no hosted widget, and no way for a stranger's text to become markup on Matt's page.

Purpose: run 1 taught the site to talk. This teaches it to hear. The hard part is not rendering, it is failing well: the output is invisible when it breaks, because "no mentions" is also what a healthy page with no mentions looks like. So a broken pull must go red without ever blocking an essay or blanking what was already there.

Output: the rel=webmention link, a stdlib pull that runs before `hugo`, a data file generated at build, an escaped names-only section, a committed blocklist, a last-good cache, a job that turns the run red after deploy, and a probe proven able to fail.

Out of scope here: deployment, PR, merge and the live check are the orchestrator's. Signing in at webmention.io, setting the secret and Bridgy signup are Matt's. Do not push and do not call the live API from tests. All work lands on the already-checked-out `indieweb-run-2` branch.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@.planning/quick/261030-k5d-indieweb-run-1-publish-and-send-microfor/261030-k5d-SUMMARY.md
@scripts/send-webmentions.py
@scripts/send-fa-email.py
@tests/test-send-webmentions.py
@tests/validate-fa.sh
@.github/workflows/hugo.yml
@themes/arcaeon/layouts/fa/single.html
@themes/arcaeon/layouts/_default/baseof.html
@themes/arcaeon/layouts/partials/helpers/band-tone.html

## Measured on 2026-10-30 at 02ccc34 (planning-time facts, do not re-derive)

**webmention.io, against the live service and the raw /api page:**

- **Loud failures.** A bad token returns 401 with `{"error":"forbidden","error_description":"Access token was not valid"}`, by header and by query string alike. `domain` with no token returns 400. Both are JSON.
- **The silent failure.** `controllers/api.rb` in aaronpk/webmention.io: a valid token whose account does not hold that `domain` sets `links = []`, which is a 200 with an empty feed. This is the only shape of "quietly no mentions", and it is why the empty-pull witness below exists.
- **Paging.** `paging` carries `per-page`, `page`, `total`, `total-pages`. `per-page=5000` clamps to 1000 and echoes 1000. `page` is zero-based. Past the end returns empty `children` with correct totals.
- **Why not the `since_id` cursor the docs suggest.** With `sort-dir=up` the example feed comes back in received order, not id order (1007, 1017, 1008, 1001, ...), so "the last id seen" is not the maximum, and `total` shrinks under `since_id`. Stepping `page` with `sort-dir=up` has no ordering assumption, new mentions append at the end, and a short walk is caught by the count guard.
- **`target[]`** works unauthenticated, and `urllib.parse.urlencode` percent-encoding the brackets is fine (checked with two targets).
- **Token listings include private mentions**, flagged `wm-private: true`. The example feed has one, id 1018.
- **Real shapes:** `author` name and url can each be `""` or null, `published` can be null, `content` is absent on likes and reposts, legacy content carries `content-type` and `value` beside `text`, `url` differs from `wm-source` on bridged posts (ids 1002, 1013). `wm-target` is the canonical URL, which the site's rel=canonical makes `https://falkensmage.com/fa/SLUG/`.
- **Example fixture URL:** `https://webmention.io/api/example/mentions.jf2?seed=123&per-page=30&sort-dir=up&target=https://falkensmage.com/fa/youve-been-heard/`. Byte-stable across fetches, sha256 `b3b4da4e…9e443f`. 21 mentions: 1 like, 1 repost, 4 public replies, 1 private reply, 9 `mention-of`, 4 `rsvp`, 1 `bookmark-of`.
- Python `urllib` with a custom User-Agent reaches the API (200).

**Hugo 0.160.1, prototyped in a scratch copy:**

- `index (hugo.Data.webmentions.pages | default dict) .RelPermalink` is nil-safe with no file, `{}`, and a normal file. `site.Data` logs a deprecation since 0.156, so new code uses `hugo.Data`.
- **Test data injection works:** `hugo --minify --config hugo.toml,TMP/mounts.toml --destination TMP/public --cacheDir TMP/cache`, cwd at the repo root. The TOML holds `[[module.mounts]]` for the temp data dir (absolute `source` is fine) and for `data` with `files = ["! webmentions.json"]`, so a local generated file cannot leak in. A `layouts` mount overrides the theme's partial.
- **Hugo reaches the network.** launch-banner.html calls `resources.GetRemote` for rewired.show. Adding `[security.http]` with `urls = ["^$"]` to that TOML denies it, the existing `try` falls back, and the build exits 0. Every test build must carry this or the suite makes an outbound call.
- Cold build about 8 s in a fresh worktree, warm under 1 s.
- `--minify` writes the tag as `<link rel=webmention href=https://webmention.io/falkensmage.com/webmention>`.
- Escaping: html/template plus the minifier leaves `<` as `&lt;` but a bare `>` in text, and turns a `javascript:` href into `#ZgotmplZ`. Tests must parse with `html.parser`, not grep for entities.
- An essay with no mentions is byte-identical with and without the data file.
- **A truncated data file makes `hugo` fail** ("failed to load data"), so a corrupt cache entry would block a deploy unless the pull repairs it first.
- **A template error on a data value aborts the build.** The prototype did this with `$.date_text` inside a `with`. Nothing in the partial may call a function that can fail on mention data, so dates arrive pre-formatted.
- `band-tone` advances per call. Calling it inside the `with` re-stripes the footer correctly on essays with a section. Calling it outside would shift every essay.
- `entry_links` on a page with the section after the closing article tag returned the essay's 13 links and no mention URLs. Inside the article it would hand strangers' URLs to the sender.
- A theme partial overridden through the `layouts` mount with `safeHTML` on a name renders a live img element with onerror, so that mutation is real.

**Baselines at 02ccc34:** `tests/validate-fa.sh` 10 passed, 0 failed. `validate-phase-06` 32/0, `validate-phase-02` 16/2, `validate-phase-03` 31/8 (the 02 and 03 failures pre-exist). `grep -c webmention` on baseof is 0, `grep -c VALIDATE_FA` on validate-fa.sh is 0, `grep -c fa-mentions` on main.css is 0, `grep -c webmentions.json` on .gitignore is 0. Do not gate on the word `mentions` in hugo.yml: it already appears 10 times. Local `python3` is 3.10, so stay 3.10-compatible.

## Decision: the data file is generated at build, last-good lives in an Actions cache

| Mechanism | Verdict |
|---|---|
| Commit data/webmentions.json back to main | Rejected. Needs `contents: write`, leaves a bot commit per mention, and has a deploy-loop cost. |
| Client-side fetch | Rejected by the brief: no client-side JS. |
| Generated at build, no fallback | Rejected. One outage blanks every mention on the site. |
| **Generated at build, gitignored, last-good in the Actions cache** | **Chosen.** Same pattern as run 1's sent state: no new permissions, no commits, no deploy trigger. |

Mechanics: restore by prefix before the pull, key unique per run, and save only when the pull step succeeded, so a failed run can never overwrite good data. The nightly restore keeps the entry younger than GitHub's 7-day eviction. The script rewrites the file before any network call, so a corrupt restore and a new blocklist entry are both handled before `hugo` runs.

## Decision: what each failure does

| Situation | Data file | Exit | Deploy | Run |
|---|---|---|---|---|
| Pull succeeds | Fresh | 0 | Yes | Green |
| Secret absent (the one non-failure) | Last-good, or empty, with blocklist reapplied | 0 | Yes | Green, with a log line and a `::notice` |
| Outage, 5xx, timeout, after 3 tries | Last-good with blocklist reapplied | 1 | Yes | Red in `mentions-probe` |
| 401, 400 or any 3xx | Same | 1, no retry | Yes | Red |
| Wrong shape, bad JSON, short walk | Same | 1 | Yes | Red |
| 200 with zero mentions, last-good has some, witness finds mentions | Same | 1 | Yes | Red |
| 200 with zero mentions, witness agrees they are gone | Emptied, correctly | 0 | Yes | Green |
| Corrupt cache entry | Repaired to valid before anything else | Per the row above it falls into | Yes | Per that row |
| Script crash | Whatever the last rewrite left, always valid | Non-zero | Yes | Red |
| Blocklist file malformed | Untouched | 1, plus `tests/validate-fa.sh` blocks | **No** | Red. This is a repo bug, not an outage |
| Template no longer renders the data | Valid | 0 | **No** | Red. `tests/validate-fa.sh` runs before upload |

The pull step uses `continue-on-error: true`, so any exit, crash or step timeout included, leaves the deploy free and shows as `outcome == failure`. A red step inside `build` would block `deploy`, which is why the red lives in a separate job after it.

**The witness.** When a pull returns zero and last-good holds mentions, ask the public per-target endpoint about those pages with no token. Mentions there mean the domain-wide answer is wrong, so the run goes red and last-good stays. None there means they really are gone. No human has to clear a cache for a legitimate deletion, and a token from the wrong account cannot blank the page. A witness that cannot be reached counts as failure.

## Other decisions

- **Blocklist is JSON, not YAML.** The brief's `.yaml` was an example. Python's stdlib has no YAML parser, and the pull is stdlib only under `-I -S`. `data/` already holds three JSON lists with a `_comment` key, so `data/webmention-blocklist.json` matches. Hugo reads it harmlessly.
- **Blocklist applies on every run, not only on fresh pulls.** Otherwise a block committed during an outage would not take effect.
- **Names only, no avatars.** Hotlinking would hand every reader's IP to strangers' hosts. Proxying or fetching images at build adds a pipeline and a hostile-file surface for decoration. The data file never holds an image URL, so a template cannot hotlink one even by accident.
- **Names link to the mention itself** (`url`, falling back to `wm-source`), not the author's profile. That credits the person and lets a reader check it. Author URLs stay in the data for the blocklist.
- **Section outside the h-entry, no h-cite markup.** Inside would feed the sender. Nesting comments as microformats is opted out for that reason.
- **Full pull every build.** Volume is low, one request covers up to 1000 mentions, and deletions upstream vanish with no extra endpoint.
- **Logs carry counts, never mention content.** A line of stranger text starting `::` is a workflow command to the Actions runner.

## webmention.io coverage (DP-11: opt out explicitly, never by omission)

| Surface | Status |
|---|---|
| `GET /api/mentions.jf2` with `domain`, Bearer header, `per-page`, `page`, `sort-dir` | In: the pull |
| Same endpoint with `target[]` and no token | In: the witness |
| `wm-property` `in-reply-to`, `like-of`, `repost-of` | In: rendered |
| `wm-property` `mention-of`, `bookmark-of`, `rsvp` | Opted out, the brief's render list is these three. Counted in the log so the gap stays visible. Adding one is a `KINDS` entry and a template loop |
| `wm-private` true | Dropped on purpose, never public |
| `author.photo`, post `photo`, `video`, `audio` | Opted out: no third-party images |
| `content.html` | Opted out: `content.text` only, per the brief |
| Query parameter `token` | Opted out: the header keeps it out of URLs and logs |
| `since`, `since_id`, `wm-property` filter, `sort-by` | Opted out: a full pull needs none, and filtering in code lets the count guard see everything |
| `/api/deleted.jf2` | Opted out: a full pull is already authoritative |
| `/api/count` | Opted out: counts derive from the pull |
| Legacy `/api/mentions`, `/api/links`, `.atom`, `.html`, `jsonp` | Opted out: jf2 is the recommended format |
| `/api/export.jf2` | Opted out: a backup tool, rate limited, includes private mentions |
| `/api/example/*` | Used once to capture a fixture, never at build or test time |
| Web hooks | Opted out: a static site has no receiver, and nightly freshness is enough |
| `webmention-render.js` and its CSS | Opted out: client JS from a third party, against the site's constraint |
| Pingback link | Opted out: not requested |
| Sign-in, settings, moderation, blocking on the dashboard | Matt's, manual. Dashboard blocks complement the repo blocklist |

## Source audit

| Brief item | Requirement | Task |
|---|---|---|
| 1. rel=webmention link in baseof, API read and recorded | IW2-ENDPOINT | 1, this context |
| 2. pull script, data file, before `hugo`, Actions on push and cron, secret, build-only data | IW2-PULL | 1, 3 |
| 3. Render under essays, no hotlinks, escaped, rel=nofollow ugc, absent when empty, strangers shown | IW2-RENDER | 1, 3 |
| 4. Repo blocklist at build time | IW2-BLOCKLIST | 2 |
| 5. Standing probe, outage behaviour decided and documented, validate-fa.sh check | IW2-PROBE | 2, 3 |
| 6. Tests: pagination, blocklist, escaping, outage, mutation proof | IW2-TESTS | 2, 3 |
| Absent secret degrades cleanly and is visible | IW2-DEGRADE | 2 |
| API coverage opt-outs recorded | all | This context, script docstring |
</context>

<tasks>

<task type="tracer">
  <name>Task 1: End-to-end, one essay's mentions travel from a stub API through the pull and a real Hugo build onto the page</name>
  <files>themes/arcaeon/layouts/_default/baseof.html, themes/arcaeon/layouts/fa/single.html, themes/arcaeon/layouts/partials/fa/mentions.html, scripts/pull-webmentions.py, tests/test-pull-webmentions.py</files>
  <behavior>
    - main() with a token set and a stub API serving one like, one repost and one reply for https://falkensmage.com/fa/youve-been-heard/ returns 0 and writes a data file whose page key is /fa/youve-been-heard/
    - A real `hugo --minify` into a temp destination with that data renders exactly one fa-mentions element on that essay, holding the three names and the reply text
    - A reply reading "<b>x</b>" renders as text: html.parser finds no b element inside the section
    - fa/both-hands/index.html is byte-identical to the same page from a build with no mention data at all
    - /fa/about/ renders no section even when the data holds a /fa/about/ key
    - The built essay's head has a link element with rel token webmention and the exact href
    - send-webmentions' entry_links on the rendered essay returns none of the mention URLs
    - The partial source contains no Hugo function that marks text safe
  </behavior>
  <action>
**Endpoint, per brief item 1.** In themes/arcaeon/layouts/_default/baseof.html, directly under the `fediverse:creator` meta, add a `link` element with `rel="webmention"` and `href="https://webmention.io/falkensmage.com/webmention"`, with a one-line template comment saying where received mentions go. It is discovery metadata, so browsers fetch nothing.

**Partial.** Create themes/arcaeon/layouts/partials/fa/mentions.html, context is the Page. Open with a template comment stating the three rules: outside the h-entry so the sender never sees it, every value is stranger text and renders through plain `{{ }}` with no pipe at all (no safeHTML or any sibling, per brief item 3), names only with no images. Look up with `index (hugo.Data.webmentions.pages | default dict) .RelPermalink` and render everything inside a `with` on that value, so no entry means zero output.

Call `partial "helpers/band-tone.html" $` inside the `with` and nowhere else. Outer element `section class="section TONE"`. Inner `div class="section-content fa-prose fa-mentions"`, which inherits the existing prose link colour. Heading `h2 class="fa-rail-heading"` reading `Responses`, which needs no new CSS for its type.

- Likes: `p class="fa-mentions__row"` holding `span class="fa-post__meta"` reading `Liked by`, then comma-separated anchors with `class="fa-mention--like"`, `href` the record's `url`, `rel="nofollow ugc"`, text the record's `name`.
- Reposts: same, `Reposted by`, class `fa-mention--repost`.
- Replies: `p class="fa-mentions__row"` holding a `span class="fa-post__meta"` reading `Replies`, then `ul class="fa-mentions__replies"` with one `li class="fa-mention--reply"` per reply: a `p` with the name anchor (same href and rel rules) and, when `date` is set, a `time` with `datetime` the `date` value and text the `date_text` value; then, when `text` is set, `p class="fa-mention__text"`.

Use named range variables (`$p`, `$r`) and interpolate `$r.text`, `$r.name`, `$p.name` by that name, also inside any `with`, never a bare dot. Inside a `with`, `.` and `$` rebind, which is what broke the prototype, and Task 3's mutation regex keys on those names. Never call a Hugo time, string or transform function on mention data: a function that can fail on a value lets a stranger block a deploy.

**Placement.** In themes/arcaeon/layouts/fa/single.html, inside the existing `if not $isPage` block that follows the closing article tag, as its first line, add `{{ partial "fa/mentions.html" . }}`. That position is load-bearing: `entry_links` in scripts/send-webmentions.py collects every anchor inside the h-entry, so a section inside the article would make the sender POST to strangers' URLs. Do not touch scripts/send-webmentions.py.

**Pull, the single path.** Create scripts/pull-webmentions.py modeled on scripts/send-webmentions.py: module docstring (what, when it runs, env, exit codes), `log` with the prefix `pull-webmentions:`, stdlib only. Constants: `ROOT` (repo root from `__file__`), `API = "https://webmention.io/api/mentions.jf2"`, `DOMAIN = "falkensmage.com"`, `SITE = "https://falkensmage.com"`, `UA` naming the site, `TIMEOUT = 20`, `PER_PAGE = 1000`, `DATA = ROOT / "data" / "webmentions.json"`, `NAME_CHARS = 80`, `REPLY_CHARS = 600`, `KINDS = {"like-of": "likes", "repost-of": "reposts", "in-reply-to": "replies"}`, `PULL_FAILED = 1`. No environment variable may change `API`: the token only ever goes to that host. Tests patch the attribute.

- `OPENER`: a hand-composed `urllib.request.OpenerDirector` from `UnknownHandler`, `HTTPDefaultErrorHandler`, `HTTPErrorProcessor`, `HTTPHandler`, `HTTPSHandler`, as `_opener` does in send-webmentions.py (do not import it). No redirect handler, because an Authorization header must never follow a redirect, and no `ProxyHandler`.
- `get_json(params, token=None)`: `params` is a list of pairs for `urlencode`. GET through `OPENER` with the UA, `Accept: application/json`, and `Authorization: Bearer` only when `token` is given. The token never goes in the URL.
- `clean_url(value) -> str`: returns the value when it is a string of at most 2000 characters, has no whitespace or control character, parses with `urlsplit`, has scheme http or https and a hostname. Otherwise `""`. A `ValueError` also returns `""`.
- `clean_text(value, limit) -> str`: non-strings become `""`. Drop category `Cc` and the bidi controls U+202A to U+202E and U+2066 to U+2069, collapse whitespace with `" ".join(s.split())`, and cut longer text at the last space inside `limit` with a trailing `…`.
- `page_key(target) -> str | None`: `urlsplit`, host must be `falkensmage.com` or `www.falkensmage.com` case-insensitively, append a trailing slash when missing, drop query and fragment, and return the path only when it matches `^/fa/[^/]+/$`. `ValueError` returns None.
- `normalize(children) -> (pages, counts)`: for each child in order. Truthy `wm-private` counts `private`. `KINDS.get(child.get("wm-property"))` missing counts `other`. `page_key(child["wm-target"])` None counts `off_essay`. `source = clean_url(child["wm-source"])`, `url = clean_url(child.get("url")) or source`, and no `url` counts `unusable`. `author` is `child.get("author")` when it is a dict, else `{}`. `author_url = clean_url(author.get("url"))`. `name` is `clean_text(author.get("name"), NAME_CHARS)`, or the host of `author_url`, or the host of `url`, or `Someone`. Drop a repeat of `(path, kind, source)`. Every record holds exactly `name`, `url`, `source`, `author_url`. A reply adds `text`, `date`, `date_text`.
- Reply text is `clean_text(content.get("text"), REPLY_CHARS)` when `content` is a dict, falling back to `clean_text(child.get("name"), REPLY_CHARS)`. Never read `content.html` or `content.value`.
- Reply date: for `published` then `wm-received`, take a string's first 10 characters through `datetime.date.fromisoformat`, and on the first that parses set `date` to that ISO string and `date_text` to `f"{d:%B} {d.day}, {d.year}"`. If neither parses both are `""`.
- `author.photo`, `photo`, `video` and `audio` are never copied, so the data file cannot hold an image URL.
- `write_data(path, pages, generated)`: JSON with `ensure_ascii=False`, `indent=1`, `sort_keys=True`, a trailing newline, top-level keys `generated` and `pages`, written to a temp file in the same directory then `os.replace`d. `pages` maps a path to any of `likes`, `reposts`, `replies`, each a non-empty list.
- `main()`: read `WEBMENTION_IO_TOKEN`, fetch one page of `domain`, `per-page`, `sort-dir=up`, normalize, write with `generated` as the current UTC time, log the counts, return 0. Task 2 builds the walk and every failure path around this. End the script with `sys.exit(main())` under the main guard.

**Tests.** Create tests/test-pull-webmentions.py in the style of tests/test-send-webmentions.py: load both scripts through `importlib.util.spec_from_file_location`, stdlib `unittest`, run directly under `python3 -I -S -B`. Docstring: no outbound network, and `hugo` on PATH is required, its absence a failure and never a skip, so the render checks cannot silently vanish.

- A small `Stub` on `ThreadingHTTPServer` bound to 127.0.0.1 port 0 with `serve_forever(0.01)`, recording each request's path and headers, with a callable route so Task 2 can vary by query string. Patch `m.API` and `m.DATA` with `mock.patch.object`.
- A `build_site(dest, data_dir=None, layouts_dir=None)` helper that writes TMP/mounts.toml with `[security.http]` `urls = ["^$"]`, a mount of `data_dir` when given, the `data` mount with `files = ["! webmentions.json"]`, and a `layouts` mount when given, then runs the command from the context with `cwd=ROOT` and `--cacheDir` in the temp dir. Non-zero exit fails with Hugo's stderr. Keep `[security.http]` and the exclusion in every build.
- A `Section` `html.parser.HTMLParser` that returns the tags, classes and attributes inside the `fa-mentions` element.

Run the end-to-end path through `main()` so the test covers stub to data file to Hugo to page.
  </action>
  <verify>
    <automated>rm -rf public && hugo --minify >/dev/null && bash tests/validate-fa.sh && grep -Eq 'rel="?webmention"? href="?https://webmention\.io/falkensmage\.com/webmention' public/fa/youve-been-heard/index.html && python3 -I -S -B tests/test-pull-webmentions.py</automated>
  </verify>
  <done>The tracer test passes through a real Hugo build. The essay shows the three names and the escaped reply, a mention-free essay is byte-identical to a no-data build, the sender sees no mention URL, and validate-fa.sh stays at 10 passed with no data file present.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Safe to run unattended: full walk, blocklist, last-good, witness, absent secret, hostile content</name>
  <files>scripts/pull-webmentions.py, tests/test-pull-webmentions.py, tests/fixtures/webmention/example-mentions.jf2.json, tests/fixtures/webmention/hostile-mentions.jf2.json, data/webmention-blocklist.json</files>
  <behavior>
    - Pagination: 2500 mentions at 1000 per page take exactly 3 requests, keep every mention in order, and each request carries domain=falkensmage.com, per-page=1000, sort-dir=up and its page number
    - Short walk: a stub claiming total 2500 whose last page comes back empty exits PULL_FAILED and leaves last-good intact; overlapping pages dedupe by wm-id and the shortfall fails the same way; a missing paging object fails
    - Shape: a child without wm-id, wm-target or wm-source fails; a non-empty feed where no child has wm-property fails; one child without wm-property alone counts as other
    - Example fixture through normalize: 1 like, 1 repost, 4 replies, 14 other, 1 private, id 1018 absent, and the bridged reply (id 1002) links to its url, not its wm-source
    - Hostile fixture: javascript:, data: and relative URLs never reach the output, a bad url falls back to wm-source, content.html and photo sentinels appear nowhere in the data file, bidi and control characters are gone, a long reply is capped, null and empty author fields yield a usable name
    - Log safety: the captured stdout of a hostile run contains no mention text and no line a stranger authored, including the ::error:: sentinel in a name
    - Blocklist: a domain matches the host and subdomains case-insensitively on url, wm-source and author URL; notevil.example survives evil.example; an author URL matches regardless of scheme, case, fragment or trailing slash
    - Blocklist on last-good: a new entry removes a cached mention on the absent-secret path and on the outage path
    - A malformed blocklist returns PULL_FAILED, leaves the data file untouched, and the repo's real file loads with empty lists
    - Outage: 503 three times, then a closed port, each return PULL_FAILED with last-good parsed equal and generated unchanged, no temp file left in the directory
    - Retry: 503 then 200 succeeds in 2 requests; 401 makes exactly 1 request and logs "Access token was not valid"; a 302 is not followed and the second server logs zero requests
    - Token: it appears in the Authorization header only, never in a path or in captured output, including on 401 and on a token holding a newline
    - Corrupt last-good, truncated JSON or a valid JSON file of the wrong shape, with an outage: PULL_FAILED and a valid file that loads with empty pages
    - Absent secret: returns 0, makes no HTTP request, keeps last-good, writes valid empty data when there is none, and prints both a log line and a ::notice
    - Empty pull with last-good: witness total above 0 returns PULL_FAILED and keeps last-good; witness total 0 returns 0 and empties the file; witness unreachable returns PULL_FAILED; witness requests carry no Authorization header
  </behavior>
  <action>
**Fixtures.** Fetch once: `curl -sS 'https://webmention.io/api/example/mentions.jf2?seed=123&per-page=30&sort-dir=up&target=https://falkensmage.com/fa/youve-been-heard/' -o tests/fixtures/webmention/example-mentions.jf2.json`. This one-time capture is the plan's only outbound call to the service. Tests read the file and never fetch it.

Write tests/fixtures/webmention/hostile-mentions.jf2.json by hand in the same feed shape, with `paging` correct and targets on `https://falkensmage.com/fa/youve-been-heard/`. Include at least:
- a reply whose `content.text` holds script and img tags, and an event-handler string
- a `content.html` holding a unique sentinel that must never surface
- an author name with a closing anchor tag, script tag and bidi override
- an author name starting `::error::` with an embedded newline
- `url` values of `javascript:alert(1)`, `data:text/html,x` and a relative path, each with a real https `wm-source`
- an `author.photo` and a post `photo` on an evil host
- a like with `author` null
- a reply with `content` null and a `name`
- a target with a fragment and no trailing slash
- one reply 5000 characters long, unbroken
- a private reply
- one mention from a domain the test blocklists

**Blocklist, per brief item 4.** Create data/webmention-blocklist.json with a `_comment` explaining the matching, plus empty `domains` and `authors` lists. Add `BLOCKLIST = ROOT / "data" / "webmention-blocklist.json"` to the script.

- `load_blocklist(path)`: requires a dict whose `domains` and `authors` are lists of strings, else raises `PullError`. Returns lowercased domains and canonical authors.
- Canonical form of an author URL: host lowercased, then path with any trailing slash removed, ignoring scheme, query and fragment.
- `apply_blocklist(pages, blocklist) -> (pages, blocked_count)`: drops a record when the host of `url`, `source` or `author_url` equals a domain or ends with `.` plus that domain, or its canonical `author_url` is listed. Removes emptied lists and emptied pages. One function, used on fresh and on last-good data.

**Walk, per brief item 2.** Add `class PullError(Exception)`, `MAX_PAGES = 100`, `TRIES = 3`, `WAIT = 5`, `MAX_BYTES = 32 * 1024 * 1024`.

`pull_all(token)` steps `page` from 0 with `domain`, `per-page`, `sort-dir=up`, not `since_id` (see context). Every response must be a dict with a list `children` and a `paging` dict with integer `total` and `total-pages`, else `PullError`. The first response's `total` is the expected count. Each child must be a dict with integer `wm-id` and string `wm-target` and `wm-source`, else `PullError` naming the field, never the value. Dedupe by `wm-id` preserving order. Stop when `page + 1 >= total-pages`. Afterwards, fewer unique mentions than expected is `PullError`, and a non-empty result where no child has `wm-property` is `PullError`, because a renamed field would otherwise turn everything into `other` and blank the site. A single child without it is legal: the docs say old mentions are stored without a type.

`get_json` retries `URLError`, `TimeoutError`, `OSError`, 5xx and 429 up to `TRIES` with `WAIT` between. Any other `HTTPError` raises `PullError` at once with the status and `clean_text` of the JSON `error_description`, reading at most 4096 bytes. Read the body up to `MAX_BYTES + 1` and treat more as `PullError`. Bad JSON, `ValueError` and `RecursionError` are `PullError`. Tests patch `m.WAIT` to 0.

Reject a token that does not match `[\x21-\x7e]+` with a `PullError` that does not contain it, before it can reach a header: `http.client` puts the raw value in its `ValueError`.

**Last-good.** `load_last_good(path) -> (pages, generated)`: a missing file is `({}, None)`. On unparseable JSON or a wrong shape, log loudly and return `({}, None)`. Valid means a dict with dict `pages`, whose values are dicts with only `likes`, `reposts`, `replies` keys, each a list of dicts with string `name` and `url`. This matters twice: a bad file stops `hugo`, and a wrong-typed value fails a `range`.

`witness_total(paths)`: `get_json` with `target[]` pairs for `SITE + path` over the first 50 paths and `per-page=1`, no token, returning `paging.total`.

**main, in this order.** The order is the design.

1. `load_blocklist`. A `PullError` here logs and returns `PULL_FAILED` with the data file untouched.
2. `load_last_good`, `apply_blocklist`, then `write_data` keeping the old `generated`. This runs before any network call, so a corrupt cache and a new block are handled even if the pull dies.
3. Token absent or blank: log `WEBMENTION_IO_TOKEN is not set, which is not a failure; kept N last-good mentions`, print a `::notice title=Webmentions::` line, return 0.
4. In one `try`: token check, `pull_all`, and if the pull is empty while last-good has pages, `witness_total` over them, raising `PullError` when it is above 0.
5. On `PullError`: log `FAILED: reason; kept N last-good mentions from GENERATED`, print a `::error title=Webmentions::` line, return `PULL_FAILED`.
6. On success: normalize, blocklist, `write_data` with the current UTC time, log one summary line: pulled, likes, reposts, replies, essays, then not rendered: private, other kinds, off-essay, blocked, unusable.

Logs carry counts, fixed text, and `clean_text`-ed API error strings only. Never print a mention field.

**Docstring.** Add to the module docstring: where the data lives and why it is not committed, the last-good cache, the failure table's direction, the witness, why `page` rather than `since_id`, why names only, and the coverage opt-outs in one paragraph, including that `mention-of`, `bookmark-of` and `rsvp` are counted but not rendered.

Tests use a temp directory for data, never `data/` in the repo. Patch `m.BLOCKLIST` for temp blocklists, and also load the real file once.
  </action>
  <verify>
    <automated>python3 -I -S -B tests/test-pull-webmentions.py && python3 -I -c 'import json; b=json.load(open("data/webmention-blocklist.json")); assert b["domains"]==[] and b["authors"]==[]; e=json.load(open("tests/fixtures/webmention/example-mentions.jf2.json")); assert len(e["children"])==21 and any(c.get("wm-private") for c in e["children"]); h=json.load(open("tests/fixtures/webmention/hostile-mentions.jf2.json")); assert h["paging"]["total"]==len(h["children"])'</automated>
  </verify>
  <done>Every behavior above passes under `-I -S` with no outbound network. Each row of the failure table has a test. The script's docstring records the decision and the opt-outs. `main` writes a valid data file before any network call.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 3: Wire it into the deploy, prove the probe can fail, and give it a look</name>
  <files>.github/workflows/hugo.yml, .gitignore, tests/validate-fa.sh, themes/arcaeon/assets/css/main.css, tests/test-pull-webmentions.py</files>
  <behavior>
    - A temp build over the hostile and example fixtures, run through main, passes tests/validate-fa.sh with VALIDATE_FA_PUBLIC and VALIDATE_FA_DATA pointed at it, and prints the mention pass lines
    - That page's section holds no element outside h2, p, ul, li, a, span and time; no on-attribute; and every anchor carries nofollow and ugc with an http or https href
    - Each mutation of the temp output turns the probe red, naming the page: section deleted; img with a remote src added to the section; ugc dropped from one anchor; section moved inside the article; rel=webmention link removed from one page; section added to /fa/about/
    - A blocklist reshaped to a bare list turns the probe red
    - The real partial, copied to a temp layouts dir with a safeHTML pipe regex-added to every name and text interpolation (the test asserts at least 3 substitutions), rebuilt over the hostile data, turns the probe red. The real partial alone stays green
    - With no data file at all the probe passes, reporting no mention data and no section on any page
    - Any element carrying the fa-mentions class on a page when the data is empty fails
  </behavior>
  <action>
**Workflow, per brief items 2 and 5.** Edit .github/workflows/hugo.yml.

In `build`, add job `outputs: mentions: ${{ steps.mentions.outcome }}`. Between `Setup Pages` and `Build with Hugo`, in order, with a 3 to 5 line comment matching the `email` and `webmentions` job comment style, stating the decision and failure direction:

1. `actions/cache/restore@v6`, name `Restore last-good Webmentions`, path `data/webmentions.json`, key `webmentions-data-${{ github.run_id }}-${{ github.run_attempt }}`, restore-keys `webmentions-data-`.
2. Step named `Pull Webmentions`, `id: mentions`, `continue-on-error: true`, `timeout-minutes: 3`, `env: WEBMENTION_IO_TOKEN: ${{ secrets.WEBMENTION_IO_TOKEN }}`, `run: python3 scripts/pull-webmentions.py`. The token appears on this step and nowhere else in the file.
3. `actions/cache/save@v6`, name `Save last-good Webmentions`, same path and key, `if: steps.mentions.outcome == 'success'`, so a failed run never replaces good data.

Add a job `mentions-probe` after `webmentions`: `runs-on: ubuntu-latest`, `needs: [build, deploy]`, `timeout-minutes: 2`, `permissions: {}`, one step with `env: OUTCOME: ${{ needs.build.outputs.mentions }}` whose `run` echoes the outcome, then, when `$OUTCOME` is not `success`, prints a `::error title=Webmentions::` line naming the `Pull Webmentions` step and saying the site deployed with last-good mentions, and exits 1. An empty outcome must fail too. Open it with a comment explaining that a red step inside `build` would block `deploy`, so the red lives here. Do not add `if: always()`: when deploy fails the run is already red.

**.gitignore.** Add `data/webmentions.json`.

**Look.** In themes/arcaeon/assets/css/main.css, after the `@media (min-width: 40rem)` block closing `.fa-after__neighbors` and before the `Compact masthead` comment, add a short commented block. `.fa-mentions` is `display: grid`, `gap: 1.25rem`, `overflow-wrap: anywhere` (a stranger's long unbroken string must not force horizontal scroll at 375px). `.fa-mentions .fa-rail-heading` resets `margin-bottom` to 0. `.fa-mentions__replies` drops list style, margin and padding and uses `display: grid`, `gap: 1.25rem`. `.fa-mention--reply` gets `padding-top: 1.25rem` and a top border using the same `rgba(122, 44, 255, 0.35)` as `.fa-after__link`. `.fa-mention__text` gets a small top margin. Rems and existing tokens only, no new hex, nothing outside these selectors.

**Probe, per brief item 5 and DP-12.** In tests/validate-fa.sh:

- Replace the `PUBLIC` line with `PUBLIC="${VALIDATE_FA_PUBLIC:-$PROJECT_ROOT/public}"` and add `DATA_DIR="${VALIDATE_FA_DATA:-$PROJECT_ROOT/data}"`. Only the new check reads `DATA_DIR`. Add one sentence to the header comment: an empty mention section looks exactly like a healthy page, so the render is checked against the data.
- After the homepage check and before the summary, add one `python3 -I - "$PUBLIC" "$DATA_DIR" <<'PY'` block using `html.parser`, not grep, since the minifier unquotes attributes. It prints `PASS text` or `FAIL text` lines and ends with `DONE`. The shell loop maps them to `pass` and `fail`, and calls `fail` when `DONE` is missing, so a crash in the block is a red, not a blank.

Scan `public/index.html` plus `public/fa/*/index.html`:

1. Each page needs a `link` whose rel tokens include `webmention` with the exact href. Pass line: `webmention endpoint advertised on N pages`. A failure names the page.
2. Read `webmentions.json` from `DATA_DIR` when present. Essay means `og:type` is `article`. For each essay, one element with class token `fa-mentions` when the data has that page, none otherwise. Counts of class tokens `fa-mention--like`, `fa-mention--repost` and `fa-mention--reply` must equal the data's list lengths. A failure says page, kind, data count and page count. Non-essays must carry no section even if the data has that path. Paths in the data with no built page are ignored: a mention can target a URL that does not exist.
3. Inside any section: tags limited to h2, p, ul, li, a, span, time; no attribute starting `on`, no `style`, `src` or `srcset`; every anchor has rel tokens nofollow and ugc and an http or https href. The section must not open while an element with token `h-entry` is open: track that with a same-tag depth counter as the essay probe does.
4. Pass line when data is present: `mention sections match the pulled data on N essays`. When the file is absent: `no mention data in this build, and no mention section on any page`. That second line is a real check, since it still scans every page, and it is what a local build reports.
5. `webmention-blocklist.json` from `DATA_DIR` must be a dict whose `domains` and `authors` are lists of strings. Pass line: `webmention blocklist is well formed`. This one blocks a deploy deliberately: a malformed blocklist is a repo bug, and a broken one would otherwise let blocked content ship.

Checks here must compare structure, never stranger text, so a mention cannot trip the gate and block a deploy unless it actually escaped.

**Mutation proofs.** Add a class to tests/test-pull-webmentions.py that in `setUpClass` feeds the example and hostile fixtures through a stub and `main()` into a temp data dir (blocklist copied in), builds with `build_site`, and runs `bash tests/validate-fa.sh` with `VALIDATE_FA_PUBLIC` and `VALIDATE_FA_DATA` set. Each mutation test edits a file in the temp output, runs the probe, asserts non-zero and the page named, and restores the bytes with `addCleanup`. For the template mutation, read the real partial, regex-add a `safeHTML` pipe to each interpolation of a `.name` or `.text` value, write it to a temp `layouts/partials/fa/mentions.html`, rebuild with `layouts_dir`, and assert the probe goes red. Generating it from the real file means it cannot go stale. Copy nothing into the repo tree, and run no mutation against `public/`.
  </action>
  <verify>
    <automated>python3 -I -S -B tests/test-pull-webmentions.py && rm -rf public && hugo --minify >/dev/null && bash tests/validate-fa.sh && bash tests/validate-fa.sh | grep -Eq 'PASS  webmention endpoint advertised on [0-9]+ pages' && bash tests/validate-fa.sh | grep -q 'PASS  no mention data in this build, and no mention section on any page' && bash tests/validate-fa.sh | grep -q 'PASS  webmention blocklist is well formed' && grep -q '^\.fa-mentions {' themes/arcaeon/assets/css/main.css && git check-ignore -q data/webmentions.json && ruby -ryaml -e 'w=YAML.load_file(".github/workflows/hugo.yml"); b=w["jobs"]["build"]; s=b["steps"]; r=s.index{|x|x["uses"].to_s.start_with?("actions/cache/restore@")}; p=s.index{|x|x["id"]=="mentions"}; v=s.index{|x|x["uses"].to_s.start_with?("actions/cache/save@")}; h=s.index{|x|x["name"]=="Build with Hugo"}; abort("order") unless [r,p,v,h].all? && [r,p,v,h]==[r,p,v,h].sort; q=s[p]; abort("pull step") unless q["continue-on-error"]==true && q["timeout-minutes"] && q["env"]["WEBMENTION_IO_TOKEN"].include?("secrets.WEBMENTION_IO_TOKEN"); abort("save guard") unless s[v]["if"].to_s.include?("steps.mentions.outcome"); abort("output") unless b["outputs"]["mentions"].include?("steps.mentions.outcome"); j=w["jobs"]["mentions-probe"]; abort("probe job") unless j && j["needs"].sort==["build","deploy"] && j["permissions"]=={} && j["steps"].last["env"]["OUTCOME"].include?("needs.build.outputs.mentions"); abort("token scope") unless File.readlines(".github/workflows/hugo.yml").grep(/WEBMENTION_IO_TOKEN/).size==1' && S='puts YAML.load_file(".github/workflows/hugo.yml")["jobs"]["mentions-probe"]["steps"].last["run"]' && ruby -ryaml -e "$S" | OUTCOME=success bash >/dev/null && ! ruby -ryaml -e "$S" | OUTCOME=failure bash >/dev/null && ! ruby -ryaml -e "$S" | OUTCOME= bash >/dev/null && sed -i.bak 's/^PULL_FAILED = 1$/PULL_FAILED = 0/' scripts/pull-webmentions.py && ! python3 -I -S -B tests/test-pull-webmentions.py >/dev/null 2>&1; s=$?; mv scripts/pull-webmentions.py.bak scripts/pull-webmentions.py; [ "$s" -eq 0 ]</automated>
  </verify>
  <done>The workflow parses with restore, pull, save, then Hugo in order; the token on one step only; the save gated on success; and a `mentions-probe` job after deploy. The job's real shell fails on `failure` and on empty, and passes on `success`. Every mutation turns the probe red, including a real escape bypass through the template. `PULL_FAILED = 0` makes the suite fail and is restored. A build with no data file passes with 13 checks.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| Stranger's page to webmention.io to the data file | Names, text, URLs and dates are attacker-controlled. Only the `wm-` fields are the service's own |
| Data file to essay page | Stranger text enters a static page every reader loads |
| Build job to webmention.io | A bearer token leaves the runner |
| Actions log | Stdout is parsed by the runner for workflow commands |
| Actions cache to `hugo` | A restored file is read back and can stop a build |
| Received mentions to the outbound sender | Anchors inside the h-entry become POST targets |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-kwk-01 | Tampering | `fa/mentions.html`, stored XSS through reply or name | critical | mitigate | Only `content.text` is read, `clean_text` strips controls, the partial uses plain `{{ }}` with no pipe, the probe's tag and attribute allow-list scans every section in CI, and a test proves that allow-list catches a real safeHTML bypass |
| T-kwk-02 | Spoofing | Hostile `url` or `author.url` | high | mitigate | `clean_url` keeps http and https only, html/template filters again, every anchor carries `rel="nofollow ugc"`, enforced by the probe |
| T-kwk-03 | Information Disclosure | Private mentions in token listings | high | mitigate | `normalize` drops truthy `wm-private` first; tested with the service's own example id 1018 |
| T-kwk-04 | Information Disclosure | `WEBMENTION_IO_TOKEN` | high | mitigate | Header only, no redirect handler, no proxy, env on one step, token shape checked before it reaches `http.client`, `API` not overridable by env; tests cover header, 401, 302 and a newline token |
| T-kwk-05 | Elevation of Privilege | Mention URLs reaching `scripts/send-webmentions.py` | high | mitigate | Section renders after the closing article tag; `entry_links` tested on the rendered page; probe fails a section inside the h-entry |
| T-kwk-06 | Information Disclosure | Third-party images leaking reader IPs | medium | mitigate | No image URL is ever copied to the data file; probe forbids img and src |
| T-kwk-07 | Tampering | Workflow-command injection through logs | high | mitigate | Logs carry counts, fixed text and cleaned API errors only; a test asserts hostile strings never reach stdout |
| T-kwk-08 | Denial of Service | A stranger or a corrupt cache blocking a deploy | high | mitigate | Dates arrive pre-formatted so no template function can fail on them, last-good is shape-validated and rewritten before `hugo`, the probe compares structure and not text, `continue-on-error` frees the deploy |
| T-kwk-09 | Denial of Service | Mention flood inflating page weight | low | accept | Each reply is capped at 600 characters, a source must really link the essay for webmention.io to verify it, and a blocklist commit or dashboard block removes it on the next build |
| T-kwk-10 | Tampering | Actions cache contents | low | accept | Only trusted default-branch triggers can write this scope, and a poisoned entry still passes through shape validation, blocklist and escaping. Worst case is stale mentions until the next good pull |
| T-kwk-11 | Spoofing | A stranger's name impersonating someone | low | accept | Decided: no allowlist. Names link to their source so a reader can check, and the blocklist removes abuse |
| T-kwk-12 | Repudiation | Token valid for the wrong account before any mention exists | low | accept | Reads as "0 mentions", since the witness needs last-good to compare. Once a mention exists the witness catches it. Named in the SUMMARY for Matt's setup check |
| T-kwk-SC | Tampering | npm/pip/cargo installs | high | accept | No package is installed: Python stdlib only, enforced by running under `python3 -I -S` |
</threat_model>

<verification>
Run from the repo root, after all tasks:

1. Clean build, probe, both Python suites: `rm -rf public && hugo --minify >/dev/null && bash tests/validate-fa.sh && python3 -I -S -B tests/test-pull-webmentions.py && python3 -I -S -B tests/test-send-webmentions.py && python3 -B tests/test-send-fa-email.py`
2. No regression against the baselines: `bash tests/validate-phase-06.sh | grep -q 'Results: 32 passed, 0 failed' && bash tests/validate-phase-02.sh | grep -q 'Results: 16 passed, 2 failed' && bash tests/validate-phase-03.sh | grep -q 'Results: 31 passed, 8 failed'`
3. Probe count: `rm -rf public && hugo --minify >/dev/null && bash tests/validate-fa.sh | grep -q '13 passed, 0 failed'`
4. Sender untouched: `git diff --quiet 02ccc34 -- scripts/send-webmentions.py scripts/send-fa-email.py`
5. Nothing stray: `git status --short` shows no `__pycache__`, no `data/webmentions.json`, no `*.bak`
</verification>

<success_criteria>
- rel=webmention appears on every page; the probe fails a page that loses it
- Pagination, blocklist, hostile content and every row of the failure table have tests, with no outbound network
- A hostile mention renders as inert text, through a real Hugo build, and a real escape bypass turns the probe red
- An essay with no mentions is byte-identical to a no-data build
- Private mentions and third-party images cannot reach a page, by construction of the data file
- A blocklist entry takes effect on the next build even during an outage
- An outage deploys, keeps last-good and goes red after deploy; an absent secret deploys green and says so
- A 200 with zero mentions cannot blank existing mentions unless the public endpoint agrees
- The failure behaviour is documented in the script docstring and the workflow comments
</success_criteria>

<output>
Create `.planning/quick/261030-kwk-indieweb-run-2-receive-webmention-io-end/261030-kwk-SUMMARY.md` when done. Carry forward:

- The failure table, and the witness.
- The coverage opt-outs, with `mention-of` called out by name: a blog post citing an essay arrives as `mention-of` and is counted but not rendered, because the brief named likes, reposts and replies. If Matt wants those shown, it is one `KINDS` entry and one template loop.
- The blocklist is JSON rather than the brief's example YAML, and why.
- Matt's manual steps: sign in at webmention.io (IndieLogin accepts a Bluesky handle that is the domain, and the site already links one with rel=me, so no new rel=me is needed), set the `WEBMENTION_IO_TOKEN` repo secret, sign up for Bridgy backfeed.
- The setup check that the witness cannot do: once the first mention exists, the next build's log total must match the webmention.io dashboard. A token from the wrong account reads as zero until then (T-kwk-12).
- An absent secret stays green by design, so if the secret is ever removed after setup, the only sign is the log line and the `::notice`.
</output>
