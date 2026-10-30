#!/usr/bin/env python3
"""Decision logic for scripts/send-fa-email.py. Run: python3 tests/test-send-fa-email.py"""
import importlib.util
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "send_fa_email", Path(__file__).resolve().parent.parent / "scripts" / "send-fa-email.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

NOW = datetime(2026, 11, 2, 18, 0, tzinfo=timezone.utc)
FRESH = {"published": NOW - timedelta(hours=1), "title": "T", "url": "https://x/y/",
         "subtitle": "A & B", "content": "<p>Body</p>"}
FEED = """<rss xmlns:content="http://purl.org/rss/1.0/modules/content/"><channel>
<item><title>Old</title><link>https://x/old/</link><pubDate>Mon, 07 Sep 2026 23:04:18 +0000</pubDate>
<description>o</description><content:encoded><![CDATA[<p>o</p>]]></content:encoded></item>
<item><title>New</title><link>https://x/new/</link><pubDate>Fri, 30 Oct 2026 15:56:14 +0000</pubDate>
<description>n</description><content:encoded><![CDATA[<p>n</p>]]></content:encoded></item>
</channel></rss>"""


class Decide(unittest.TestCase):
    def test_send_only_when_requested(self):
        self.assertEqual(m.decide(FRESH, NOW, [], True), "send")
        self.assertEqual(m.decide(FRESH, NOW, [], False), "draft")

    def test_old_essay_never_goes_out(self):
        old = {**FRESH, "published": NOW - timedelta(hours=25)}
        self.assertEqual(m.decide(old, NOW, [], True), "skip-old")

    def test_duplicates_skip_in_every_live_status(self):
        for s in ("sent", "scheduled", "draft", "about_to_send", "managed_by_rss"):
            self.assertEqual(m.decide(FRESH, NOW, [s], True), "skip-duplicate")

    def test_deleted_email_does_not_block(self):
        self.assertEqual(m.decide(FRESH, NOW, ["deleted"], True), "send")


class Feed(unittest.TestCase):
    def test_newest_first_with_full_content(self):
        items = m.parse_feed(FEED)
        self.assertEqual(items[0]["title"], "New")
        self.assertEqual(items[0]["content"], "<p>n</p>")


class Build(unittest.TestCase):
    def test_email_shape(self):
        e = m.build_email(FRESH, "draft")
        self.assertEqual((e["subject"], e["status"], e["canonical_url"]), ("T", "draft", "https://x/y/"))
        self.assertIn("<em>A &amp; B</em>", e["body"])
        self.assertTrue(e["body"].index("Body") < e["body"].index("Read it on the site"))


if __name__ == "__main__":
    unittest.main()
