---
phase: quick-261030-oqx
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - scripts/send-fa-email.py
  - tests/test-send-fa-email.py
autonomous: true
requirements: [FA-EMAIL-DRAFT-HAZARD]

must_haves:
  truths:
    - "Send requested and the subject has only draft emails (deleted ones ignored): exactly one draft is PATCHed to about_to_send, no new email is created, the other drafts are untouched."
    - "Send requested and any non-deleted email is beyond draft: no mail-producing call is made, ever. Exit 0 if the email has gone out or is going out on its own (sent, about_to_send, in_flight, scheduled, throttled, resending, partially_sent); non-zero for any other beyond-draft status (paused, errored, managed_by_rss, ...)."
    - "Send requested and the essay is older than 24h: job exits non-zero instead of logging a skip."
    - "Non-send triggers (push, nightly, note-driven): decide() output is identical to today for every status combination, and no code path other than send ever calls PATCH."
    - "statuses_for_subject returns (id, status) pairs for exact-subject matches only."
    - "The test suite makes zero outbound network calls and a mutated decide() that can double-send fails it."
  artifacts:
    - path: "scripts/send-fa-email.py"
      provides: "promote action, pick_draft, send_blocked, act(), api(method=), id-bearing statuses_for_subject"
    - path: "tests/test-send-fa-email.py"
      provides: "decision table, request-shape test, in-memory fake Buttondown scenarios, mutation proof"
  key_links:
    - "act() -> decide() -> pick_draft() -> api(PATCH /emails/{id}, status about_to_send): the only path that mails an existing draft"
    - "act() -> send_blocked() -> sys.exit(message): the only path that turns a requested-but-impossible send into a red job"
---

<objective>
Close the draft hazard in scripts/send-fa-email.py: a draft created by a push, nightly or note-driven deploy within 24h of a new essay currently makes a later send_email=true dispatch print skip-duplicate and mail nobody.

Purpose: a dispatched send must either mail the essay exactly once or fail the job visibly, never silently do nothing.
Output: updated scripts/send-fa-email.py and tests/test-send-fa-email.py. The workflow file is not touched; sys.exit(message) already turns the email job red.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@CLAUDE.md
@scripts/send-fa-email.py
@tests/test-send-fa-email.py

Buttondown API shape, confirmed from https://docs.buttondown.com/openapi.json (operation update_email):
- PATCH /v1/emails/{id}, JSON body, additionalProperties false. The `status` field is optional and accepts an EmailStatus enum value; about_to_send is valid, and the docs' status diagram shows Draft -> About to send as an owner-triggered transition. 200 returns the Email (id, status, subject). 409, 422 and 429 are possible and surface as urllib.error.HTTPError, which fails the job.
- GET /emails `subject` filter is "contains", not exact, so the existing exact-equality filter in statuses_for_subject stays.
- EmailStatus values: draft, managed_by_rss, about_to_send, scheduled, in_flight, paused, deleted, errored, sent, partially_sent, imported, throttled, resending, transactional (14).
- Baseline before this change: python3 -I -S -B tests/test-send-fa-email.py runs 6 tests, all OK.
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Promote an existing draft on send, fail loudly when a requested send cannot happen</name>
  <files>scripts/send-fa-email.py, tests/test-send-fa-email.py</files>
  <behavior>
    - decide(..., send_requested=True): no live emails -> send; live emails all draft (any count, deleted ignored) -> promote; any live non-draft (even beside a draft) -> skip-duplicate; stale essay -> skip-old.
    - decide(..., send_requested=False): identical to the old behavior for every combination of up to 3 statuses drawn from all 14 EmailStatus values (pin it against an inline copy of the old rule).
    - pick_draft(existing): returns one id whose status is draft, deterministic regardless of input order (lowest id by string sort); None when there is no draft.
    - send_blocked: None for non-send requests; message for skip-old; message for skip-duplicate unless some status is in DELIVERED; None otherwise.
    - api(path, key, payload, method="PATCH") builds a Request with get_method() PATCH, URL API + path, JSON body, Authorization header (assert on the captured Request with urlopen stubbed).
    - statuses_for_subject returns (id, status) pairs and drops emails whose subject only contains the title.
    - act() against an in-memory fake Buttondown: one draft -> one PATCH, zero POST; three drafts -> exactly one PATCH; none -> one POST with about_to_send; draft+sent -> zero mail calls, returns normally; only paused -> SystemExit non-zero; stale+send -> SystemExit non-zero; non-send with a draft -> zero calls; dry run -> zero mail calls.
    - Two consecutive send dispatches against the fake (start states: no email, one draft, three drafts) produce exactly one mail-producing call in total.
    - Mutation proof: an invariant checker (live emails must be empty or all draft before any mail-producing action, and a second dispatch after a mail call must produce none) passes for the real decide() and raises AssertionError for each mutant: (a) promotes whenever any email exists, (b) ignores existing statuses and always sends, (c) treats about_to_send and scheduled as draft-like.
  </behavior>
  <action>
In scripts/send-fa-email.py:

1. api(): add keyword `method=None` and pass it to urllib.request.Request. Existing GET and POST callers stay as they are.
2. statuses_for_subject(): keep the name and the exact-subject filter; return a list of (id, status) tuples instead of bare statuses.
3. decide(): keep the signature and keep taking plain status strings. Order: age check first (skip-old); live = statuses other than "deleted"; empty live -> "send" if send_requested else "draft"; send_requested and every live status == "draft" -> new action "promote"; everything else -> "skip-duplicate". Non-send behavior must not change.
4. Add pick_draft(existing): among (id, status) pairs with status "draft", return exactly one id (lowest by string sort so reruns choose the same one), or None. Do not delete or touch the other drafts.
5. Add module constant DELIVERED (frozenset: sent, about_to_send, in_flight, scheduled, throttled, resending, partially_sent) and send_blocked(action, send_requested, statuses) returning a failure message or None: None when not send_requested (non-send triggers never fail on skips); a message naming the 24h window for skip-old; for skip-duplicate a message listing the statuses unless any status is in DELIVERED. An email that has gone out, or is committed to go out, is success; an unsendable one (paused, errored, managed_by_rss and the rest) is a red job and still sends nothing.
6. Extract the post-feed logic from main() into act(item, key, send, dry, now): fetch existing = statuses_for_subject(...), action = decide(...) over the statuses, print the existing "send-fa-email: {action}: {title}" log line, then problem = send_blocked(...); if problem, sys.exit("send-fa-email: " + problem). This runs before the dry-run return, so a dry run reports a would-fail send too. Then: skip or dry -> return; page_is_up false -> sys.exit as today; action "promote" -> eid = pick_draft(existing), exit with a message if None, then api(f"/emails/{urllib.parse.quote(eid, safe='')}", key, {"status": "about_to_send"}, method="PATCH") and print the id and resulting status; send/draft -> create exactly as today. The PATCH body is status only (confirmed accepted field) so any edits Matt made to the draft in Buttondown are mailed as he left them, not overwritten from the feed.
7. main() keeps env handling, the feed fetch and the empty-feed exit, then calls act(items[0], key, send, dry, datetime.now(timezone.utc)). Update the module docstring: send now promotes an existing draft, a requested send that cannot happen exits 1, and an email that already went out is success.

Do not change .github/workflows/hugo.yml, MAX_AGE, build_email, parse_feed or page_is_up. Do not add dependencies; the suite runs under python3 -I -S -B, so stdlib only (itertools, io, json, unittest, unittest.mock).

In tests/test-send-fa-email.py, keep the Feed and Build classes. Replace Decide's duplicate test with the table above, keeping the send-only-when-requested, old-essay and deleted-does-not-block cases. Add an inline legacy-rule copy for the non-send pin. Add a FakeButtondown helper: holds a list of {id, subject, status} dicts, installed by patching m.api and m.page_is_up with unittest.mock.patch.object. It must serve GET /emails?..., POST /emails (appends, counts a mail call when status is about_to_send), and PATCH /emails/{id} (sets status, counts a mail call when status is about_to_send), and raise AssertionError for anything else. Include a decoy email whose subject merely contains the title, to prove exact matching. Patch m.urllib.request.urlopen to raise AssertionError in setUp for the whole suite so any real request fails the test; the api() request-shape test installs its own urlopen stub returning io.BytesIO. Never read BUTTONDOWN_API_KEY from the environment; pass a dummy key string. Build the mutation proof as an exhaustive invariant check over multisets of up to 3 statuses, run against m.decide and against mutants (a), (b), (c) via assertRaises(AssertionError), plus the two-dispatch fake scenario run with mutant (a) patched in as decide to prove the wiring-level check also trips.

Do not send any real email. Do not run the script itself.
  </action>
  <verify>
    <automated>python3 -I -S -B tests/test-send-fa-email.py</automated>
  </verify>
  <done>
Suite passes offline in under a second with more than the 6 baseline tests. A send dispatch promotes exactly one draft via PATCH, skips cleanly when the email already went out, and exits non-zero when a requested send cannot happen. Non-send decisions are provably unchanged. Every mutant fails the invariant checker.
  </done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| CI runner -> Buttondown API | Authenticated PATCH/POST that mails subscribers; irreversible once sent |
| Buttondown API -> script | Response ids and statuses decide which email is promoted |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-oqx-01 | Tampering | decide()/pick_draft(): promoting the wrong email, or mailing twice | high | mitigate | promote only when every live status is draft; pick exactly one id; PATCH targets a single email id so a rerun or race cannot create a second email; exhaustive invariant test plus three mutants and a two-dispatch fake |
| T-oqx-02 | Repudiation | send_blocked(): a requested send fails silently as a log line | medium | mitigate | sys.exit(message) gives exit 1 and a red email job; tests assert non-zero for stale, paused and errored cases |
| T-oqx-03 | Information Disclosure | logs and tests | medium | mitigate | print only ids and statuses, never headers or the API key; tests pass a dummy key and never read the environment |
| T-oqx-04 | Denial of Service | two simultaneous dispatches both creating an email | low | accept | pre-existing create-path race, unchanged; the promote path cannot double-mail because it targets one email id |
| T-oqx-SC | Tampering | package installs | high | accept | no installs; stdlib only |
</threat_model>

<verification>
- python3 -I -S -B tests/test-send-fa-email.py exits 0 (this is the exact invocation hugo.yml uses to gate deploys).
- Baselines recorded at HEAD: grep -c 'method="PATCH"' scripts/send-fa-email.py is 0; grep -c urlopen tests/test-send-fa-email.py is 0; test count is 6. After: the first is at least 1, the second at least 1, the third is greater than 6.
- git status --short -- scripts tests .github lists exactly scripts/send-fa-email.py and tests/test-send-fa-email.py (baseline: empty).
</verification>

<success_criteria>
- Dispatch with send_email=true after an automatic draft mails the essay once, via the existing draft.
- Dispatch after the email already went out is green and sends nothing; a requested send that cannot happen is red.
- Push, nightly and note-driven runs behave exactly as before.
- Tests are offline and the mutation proof demonstrates double-send is caught.
</success_criteria>

<output>
Create `.planning/quick/261030-oqx-fix-essay-email-draft-hazard-promote-dra/261030-oqx-SUMMARY.md` when done
</output>
