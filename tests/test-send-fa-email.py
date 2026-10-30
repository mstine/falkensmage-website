#!/usr/bin/env python3
"""Decision logic and request flow for scripts/send-fa-email.py.

Run: python3 -I -S -B tests/test-send-fa-email.py

Offline by construction: urlopen is replaced with a tripwire for every test, and all
Buttondown traffic goes through an in-memory fake. A dummy key is used throughout.
"""
import contextlib
import importlib.util
import io
import itertools
import json
import unittest
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "send_fa_email", Path(__file__).resolve().parent.parent / "scripts" / "send-fa-email.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

NOW = datetime(2026, 11, 2, 18, 0, tzinfo=timezone.utc)
FRESH = {"published": NOW - timedelta(hours=1), "title": "T", "url": "https://x/y/",
         "subtitle": "A & B", "content": "<p>Body</p>"}
OLD = {**FRESH, "published": NOW - timedelta(hours=25)}
KEY = "dummy-key-not-real"
FEED = """<rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<item><title>Old</title><link>https://x/old/</link><pubDate>Mon, 07 Sep 2026 23:04:18 +0000</pubDate>
<description>o</description><content:encoded><![CDATA[<p>o</p>]]></content:encoded></item>
<item><title>New</title><link>https://x/new/</link><pubDate>Fri, 30 Oct 2026 15:56:14 +0000</pubDate>
<description>n</description><content:encoded><![CDATA[<p>n</p>]]></content:encoded></item>
</channel></rss>"""

# All 14 EmailStatus values from the Buttondown OpenAPI spec.
STATUSES = ("draft", "managed_by_rss", "about_to_send", "scheduled", "in_flight", "paused",
            "deleted", "errored", "sent", "partially_sent", "imported", "throttled",
            "resending", "transactional")
MAILING = ("send", "promote")


class NoNetwork(unittest.TestCase):
    """Any real request in any test is a failure."""

    def setUp(self):
        p = mock.patch.object(m.urllib.request, "urlopen",
                              side_effect=AssertionError("real network request attempted"))
        p.start()
        self.addCleanup(p.stop)


def legacy_decide(item, now, existing_statuses, send_requested):
    """Verbatim copy of the pre-change rule, pinned for non-send triggers."""
    if now - item["published"] > m.MAX_AGE:
        return "skip-old"
    if any(s != "deleted" for s in existing_statuses):
        return "skip-duplicate"
    return "send" if send_requested else "draft"


# ---- invariant checker and mutants ---------------------------------------------------

def check_invariants(decide_fn):
    """Raise AssertionError if decide_fn can double-send or mail a non-draft."""
    for n in range(4):
        for combo in itertools.combinations_with_replacement(STATUSES, n):
            statuses = list(combo)
            live = [s for s in statuses if s != "deleted"]
            for send in (True, False):
                action = decide_fn(FRESH, NOW, statuses, send)
                if action not in MAILING:
                    continue
                if not send:
                    raise AssertionError(f"{statuses}: non-send request produced {action}")
                if any(s != "draft" for s in live):
                    raise AssertionError(f"{statuses}: {action} with a non-draft email present")
                if action == "send" and live:
                    raise AssertionError(f"{statuses}: send while an email already exists")
                if action == "promote" and not live:
                    raise AssertionError(f"{statuses}: promote with nothing to promote")
                after = list(statuses)
                if action == "send":
                    after.append("about_to_send")
                else:
                    after[after.index("draft")] = "about_to_send"
                again = decide_fn(FRESH, NOW, after, True)
                if again in MAILING:
                    raise AssertionError(f"{statuses}: second dispatch mails again ({again})")


def mutant_promote_any(item, now, statuses, send):
    if now - item["published"] > m.MAX_AGE:
        return "skip-old"
    if not [s for s in statuses if s != "deleted"]:
        return "send" if send else "draft"
    return "promote" if send else "skip-duplicate"


def mutant_always_send(item, now, statuses, send):
    if now - item["published"] > m.MAX_AGE:
        return "skip-old"
    return "send" if send else "draft"


def mutant_draftlike(item, now, statuses, send):
    if now - item["published"] > m.MAX_AGE:
        return "skip-old"
    live = [s for s in statuses if s != "deleted"]
    if not live:
        return "send" if send else "draft"
    if send and all(s in ("draft", "about_to_send", "scheduled") for s in live):
        return "promote"
    return "skip-duplicate"


# ---- in-memory Buttondown ------------------------------------------------------------

class FakeButtondown:
    def __init__(self, emails):
        self.emails = [dict(e) for e in emails]
        self.calls = []          # (method, path, payload)
        self.mail_calls = 0
        self._next = 900

    def api(self, path, key, payload=None, method=None):
        assert key == KEY
        method = method or ("POST" if payload is not None else "GET")
        self.calls.append((method, path, payload))
        if method == "GET" and path.startswith("/emails?"):
            subject = urllib.parse.parse_qs(urllib.parse.urlsplit(path).query)["subject"][0]
            # Buttondown's subject filter is "contains", not exact.
            return {"results": [dict(e) for e in self.emails if subject in e["subject"]]}
        if method == "POST" and path == "/emails":
            self._next += 1
            made = {"id": str(self._next), "subject": payload["subject"], "status": payload["status"]}
            self.emails.append(made)
            if made["status"] == "about_to_send":
                self.mail_calls += 1
            return dict(made)
        if method == "PATCH" and path.startswith("/emails/"):
            eid = urllib.parse.unquote(path[len("/emails/"):])
            target = next(e for e in self.emails if e["id"] == eid)
            assert set(payload) == {"status"}
            target["status"] = payload["status"]
            if target["status"] == "about_to_send":
                self.mail_calls += 1
            return dict(target)
        raise AssertionError(f"unexpected request {method} {path}")

    def writes(self, method=None):
        return [c for c in self.calls if c[0] != "GET" and (method is None or c[0] == method)]

    def status_of(self, eid):
        return next(e["status"] for e in self.emails if e["id"] == eid)


def email(eid, status, subject="T"):
    return {"id": eid, "subject": subject, "status": status}


# A different subject that merely contains the title: must never be treated as ours.
DECOY = email("d1", "sent", subject="T: the sequel")


class ActCase(NoNetwork):
    def run_act(self, emails, send=True, dry=False, item=FRESH, page_up=True, decide_fn=None):
        fake = FakeButtondown(emails)
        out = io.StringIO()
        patches = [mock.patch.object(m, "api", fake.api),
                   mock.patch.object(m, "page_is_up", lambda url: page_up)]
        if decide_fn is not None:
            patches.append(mock.patch.object(m, "decide", decide_fn))
        with contextlib.ExitStack() as stack:
            for p in patches:
                stack.enter_context(p)
            stack.enter_context(contextlib.redirect_stdout(out))
            try:
                m.act(item, KEY, send, dry, NOW)
                code = None
            except SystemExit as e:
                code = e.code
        self.assertNotIn(KEY, out.getvalue())
        return fake, code


# ---- tests ---------------------------------------------------------------------------

class Decide(NoNetwork):
    def test_send_only_when_requested(self):
        self.assertEqual(m.decide(FRESH, NOW, [], True), "send")
        self.assertEqual(m.decide(FRESH, NOW, [], False), "draft")

    def test_old_essay_never_goes_out(self):
        self.assertEqual(m.decide(OLD, NOW, [], True), "skip-old")
        self.assertEqual(m.decide(OLD, NOW, ["draft"], True), "skip-old")

    def test_drafts_are_promoted_on_send(self):
        for n in (1, 2, 3):
            self.assertEqual(m.decide(FRESH, NOW, ["draft"] * n, True), "promote")

    def test_beyond_draft_is_duplicate_even_beside_a_draft(self):
        for s in STATUSES:
            if s in ("draft", "deleted"):
                continue
            self.assertEqual(m.decide(FRESH, NOW, [s], True), "skip-duplicate", s)
            self.assertEqual(m.decide(FRESH, NOW, ["draft", s], True), "skip-duplicate", s)

    def test_deleted_email_does_not_block(self):
        self.assertEqual(m.decide(FRESH, NOW, ["deleted"], True), "send")
        self.assertEqual(m.decide(FRESH, NOW, ["deleted", "draft"], True), "promote")

    def test_non_send_decisions_unchanged_for_every_status_combination(self):
        for item in (FRESH, OLD):
            for n in range(4):
                for combo in itertools.product(STATUSES, repeat=n):
                    self.assertEqual(m.decide(item, NOW, list(combo), False),
                                     legacy_decide(item, NOW, list(combo), False), combo)

    def test_send_unchanged_except_draft_promotion(self):
        for n in range(4):
            for combo in itertools.product(STATUSES, repeat=n):
                new = m.decide(FRESH, NOW, list(combo), True)
                old = legacy_decide(FRESH, NOW, list(combo), True)
                if new != old:
                    live = [s for s in combo if s != "deleted"]
                    self.assertEqual((old, new), ("skip-duplicate", "promote"))
                    self.assertTrue(live and all(s == "draft" for s in live), combo)


class PickDraft(NoNetwork):
    def test_none_without_a_draft(self):
        self.assertIsNone(m.pick_draft([]))
        self.assertIsNone(m.pick_draft([("1", "sent"), ("2", "deleted")]))

    def test_lowest_id_regardless_of_order(self):
        pairs = [("b", "draft"), ("a", "draft"), ("c", "draft"), ("0", "sent")]
        for perm in itertools.permutations(pairs):
            self.assertEqual(m.pick_draft(list(perm)), "a")

    def test_ignores_non_drafts(self):
        self.assertEqual(m.pick_draft([("a", "sent"), ("z", "draft")]), "z")

    def test_string_sort(self):
        self.assertEqual(m.pick_draft([("9", "draft"), ("10", "draft")]), "10")


class SendBlocked(NoNetwork):
    def test_non_send_never_fails(self):
        for action in ("skip-old", "skip-duplicate", "draft"):
            self.assertIsNone(m.send_blocked(action, False, ["paused"]))

    def test_stale_send_fails_naming_the_window(self):
        self.assertIn("24h", m.send_blocked("skip-old", True, []))

    def test_delivered_statuses_are_success(self):
        for s in m.DELIVERED:
            self.assertIsNone(m.send_blocked("skip-duplicate", True, [s]), s)
        self.assertIsNone(m.send_blocked("skip-duplicate", True, ["draft", "sent"]))
        self.assertIsNone(m.send_blocked("skip-duplicate", True, ["deleted", "sent"]))

    def test_unsendable_statuses_fail_and_list_statuses(self):
        for s in ("paused", "errored", "managed_by_rss", "imported", "transactional"):
            msg = m.send_blocked("skip-duplicate", True, [s])
            self.assertIn(s, msg)

    def test_send_and_promote_not_blocked(self):
        for action in ("send", "promote", "draft"):
            self.assertIsNone(m.send_blocked(action, True, ["draft"]))


class Api(NoNetwork):
    def call(self, *args, **kw):
        captured = []

        def fake_urlopen(req, timeout=None):
            captured.append(req)
            return io.BytesIO(b'{"id": "x", "status": "draft"}')

        with mock.patch.object(m.urllib.request, "urlopen", fake_urlopen):
            result = m.api(*args, **kw)
        self.assertEqual(len(captured), 1)
        return captured[0], result

    def test_patch_request_shape(self):
        req, result = self.call("/emails/abc", KEY, {"status": "about_to_send"}, method="PATCH")
        self.assertEqual(req.get_method(), "PATCH")
        self.assertEqual(req.full_url, m.API + "/emails/abc")
        self.assertEqual(json.loads(req.data), {"status": "about_to_send"})
        self.assertEqual(req.get_header("Authorization"), f"Token {KEY}")
        self.assertEqual(req.get_header("Content-type"), "application/json")
        self.assertEqual(result["id"], "x")

    def test_default_methods_unchanged(self):
        req, _ = self.call("/emails?x=1", KEY)
        self.assertEqual((req.get_method(), req.data), ("GET", None))
        req, _ = self.call("/emails", KEY, {"a": 1})
        self.assertEqual(req.get_method(), "POST")


class StatusesForSubject(NoNetwork):
    def test_id_status_pairs_exact_subject_only(self):
        fake = FakeButtondown([email("1", "draft"), email("2", "deleted"), DECOY])
        with mock.patch.object(m, "api", fake.api):
            self.assertEqual(m.statuses_for_subject("T", KEY), [("1", "draft"), ("2", "deleted")])


class Act(ActCase):
    def test_one_draft_is_promoted_not_recreated(self):
        fake, code = self.run_act([email("a", "draft")])
        self.assertIsNone(code)
        self.assertEqual([c[:2] for c in fake.writes()], [("PATCH", "/emails/a")])
        self.assertEqual(fake.writes()[0][2], {"status": "about_to_send"})
        self.assertEqual(fake.status_of("a"), "about_to_send")
        self.assertEqual(fake.mail_calls, 1)

    def test_three_drafts_promote_exactly_one(self):
        fake, code = self.run_act([email("c", "draft"), email("a", "draft"), email("b", "draft")])
        self.assertIsNone(code)
        self.assertEqual(len(fake.writes()), 1)
        self.assertEqual([fake.status_of(i) for i in "abc"], ["about_to_send", "draft", "draft"])
        self.assertEqual(fake.mail_calls, 1)

    def test_decoy_subject_does_not_block_or_get_promoted(self):
        fake, code = self.run_act([DECOY, email("a", "draft"), email("e", "draft", subject="T 2")])
        self.assertIsNone(code)
        self.assertEqual([c[:2] for c in fake.writes()], [("PATCH", "/emails/a")])
        self.assertEqual(fake.status_of("e"), "draft")
        self.assertEqual(fake.status_of("d1"), "sent")

    def test_deleted_is_ignored_when_promoting(self):
        fake, code = self.run_act([email("a", "deleted"), email("b", "draft")])
        self.assertIsNone(code)
        self.assertEqual([c[:2] for c in fake.writes()], [("PATCH", "/emails/b")])
        self.assertEqual(fake.status_of("a"), "deleted")

    def test_no_email_posts_one_about_to_send(self):
        fake, code = self.run_act([DECOY])
        self.assertIsNone(code)
        writes = fake.writes()
        self.assertEqual([(w[0], w[1]) for w in writes], [("POST", "/emails")])
        self.assertEqual(writes[0][2]["status"], "about_to_send")
        self.assertEqual(fake.mail_calls, 1)

    def test_already_sent_is_green_and_mails_nothing(self):
        for emails in ([email("a", "sent")], [email("a", "draft"), email("b", "sent")],
                       [email("a", "scheduled")], [email("a", "about_to_send")]):
            fake, code = self.run_act(emails)
            self.assertIsNone(code, emails)
            self.assertEqual(fake.writes(), [], emails)

    def test_unsendable_status_fails_and_mails_nothing(self):
        for s in ("paused", "errored", "managed_by_rss"):
            for emails in ([email("a", s)], [email("a", "draft"), email("b", s)]):
                fake, code = self.run_act(emails)
                self.assertTrue(code, (s, emails))
                self.assertEqual(fake.writes(), [], (s, emails))
                self.assertEqual(fake.mail_calls, 0)

    def test_stale_essay_with_send_fails_and_mails_nothing(self):
        for emails in ([], [email("a", "draft")], [email("a", "sent")]):
            fake, code = self.run_act(emails, item=OLD)
            self.assertTrue(code, emails)
            self.assertEqual(fake.writes(), [], emails)

    def test_non_send_triggers_never_patch_or_fail(self):
        for emails in ([email("a", "draft")], [email("a", "sent")], [email("a", "paused")],
                       [email("a", "draft"), email("b", "draft")]):
            fake, code = self.run_act(emails, send=False)
            self.assertIsNone(code, emails)
            self.assertEqual(fake.writes(), [], emails)
        fake, code = self.run_act([email("a", "draft")], send=False, item=OLD)
        self.assertIsNone(code)
        self.assertEqual(fake.writes(), [])

    def test_non_send_with_no_email_creates_a_draft(self):
        fake, code = self.run_act([], send=False)
        self.assertIsNone(code)
        self.assertEqual([(w[0], w[1], w[2]["status"]) for w in fake.writes()],
                         [("POST", "/emails", "draft")])
        self.assertEqual(fake.mail_calls, 0)

    def test_dry_run_mails_nothing(self):
        for emails in ([], [email("a", "draft")], [email("a", "sent")]):
            for send in (True, False):
                fake, code = self.run_act(emails, send=send, dry=True)
                self.assertIsNone(code, (emails, send))
                self.assertEqual(fake.writes(), [])
                self.assertEqual(fake.mail_calls, 0)

    def test_dry_run_still_reports_a_send_that_would_fail(self):
        fake, code = self.run_act([email("a", "paused")], dry=True)
        self.assertTrue(code)
        fake, code = self.run_act([], dry=True, item=OLD)
        self.assertTrue(code)
        self.assertEqual(fake.writes(), [])

    def test_page_down_stops_before_any_write(self):
        for emails in ([], [email("a", "draft")]):
            fake, code = self.run_act(emails, page_up=False)
            self.assertTrue(code)
            self.assertEqual(fake.writes(), [])


class TwoDispatches(ActCase):
    START_STATES = {
        "no email": [],
        "one draft": [email("a", "draft")],
        "three drafts": [email("a", "draft"), email("b", "draft"), email("c", "draft")],
    }

    def two_dispatches(self, emails, decide_fn=None):
        """Run send twice against the same fake; return it. Fail if either run errors."""
        fake = FakeButtondown(emails)
        for n in (1, 2):
            patches = [mock.patch.object(m, "api", fake.api),
                       mock.patch.object(m, "page_is_up", lambda url: True)]
            if decide_fn is not None:
                patches.append(mock.patch.object(m, "decide", decide_fn))
            with contextlib.ExitStack() as stack:
                for p in patches:
                    stack.enter_context(p)
                stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
                try:
                    m.act(FRESH, KEY, True, False, NOW)
                except SystemExit as e:
                    raise AssertionError(f"dispatch {n} failed: {e.code}")
        return fake

    def test_exactly_one_mail_across_two_dispatches(self):
        for name, emails in self.START_STATES.items():
            fake = self.two_dispatches(emails)
            self.assertEqual(fake.mail_calls, 1, name)

    def test_double_send_mutants_trip_the_wiring_check(self):
        for mutant in (mutant_promote_any, mutant_always_send):
            with self.assertRaises(AssertionError, msg=mutant.__name__):
                for name, emails in self.START_STATES.items():
                    fake = self.two_dispatches(emails, decide_fn=mutant)
                    self.assertEqual(fake.mail_calls, 1, name)


class MutationProof(NoNetwork):
    def test_real_decide_satisfies_every_invariant(self):
        check_invariants(m.decide)

    def test_each_mutant_is_caught(self):
        for mutant in (mutant_promote_any, mutant_always_send, mutant_draftlike):
            with self.assertRaises(AssertionError, msg=mutant.__name__):
                check_invariants(mutant)


class Feed(NoNetwork):
    def test_newest_first_with_full_content(self):
        items = m.parse_feed(FEED)
        self.assertEqual(items[0]["title"], "New")
        self.assertEqual(items[0]["content"], "<p>n</p>")


class Build(NoNetwork):
    def test_email_shape(self):
        e = m.build_email(FRESH, "draft")
        self.assertEqual((e["subject"], e["status"], e["canonical_url"]), ("T", "draft", "https://x/y/"))
        self.assertIn("<em>A &amp; B</em>", e["body"])
        self.assertTrue(e["body"].index("Body") < e["body"].index("Read it on the site"))


class Tripwire(unittest.TestCase):
    def test_suite_blocks_real_requests(self):
        class T(NoNetwork):
            def runTest(self):
                m.urllib.request.urlopen("http://localhost:9/")

        result = unittest.TestResult()
        T().run(result)
        self.assertEqual(len(result.failures) + len(result.errors), 1)


if __name__ == "__main__":
    unittest.main()
