#!/usr/bin/env python3
"""send-fa-email.py — turn the newest Feral Architecture essay into a Buttondown email.

Runs after deploy, so the email can never point at a page that isn't live. It sends
only when the release asked it to (SEND_EMAIL=true, from workflow_dispatch); every
other trigger leaves a draft, so a nightly rebuild can't mail outside the chosen hour.

When a send is requested and the essay already has a draft (made by an earlier push,
nightly or note-driven run), that one draft is promoted to about_to_send via PATCH
instead of being skipped as a duplicate, so any edits made to it in Buttondown are
mailed as left. A requested send that cannot happen exits 1 (red job): essay older
than 24h, or an email beyond draft that is not on its way out (paused, errored,
managed_by_rss, ...). An email that already went out, or is going out, is success and
sends nothing. Non-send triggers never PATCH and never fail on a skip.

Env: BUTTONDOWN_API_KEY, SEND_EMAIL ("true" to send), DRY_RUN ("1" to skip all writes).
Exit 1 if the essay page never comes up, Buttondown refuses the email, or a requested
send cannot happen.
"""
import email.utils
import html
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

FEED = "https://falkensmage.com/fa/index.xml"
API = "https://api.buttondown.com/v1"
MAX_AGE = timedelta(hours=24)
CONTENT = "{http://purl.org/rss/1.0/modules/content/}encoded"
UA = {"User-Agent": "falkensmage-site-deploy"}
# Statuses meaning the email has gone out or is committed to go out on its own.
DELIVERED = frozenset({"sent", "about_to_send", "in_flight", "scheduled",
                       "throttled", "resending", "partially_sent"})


def parse_feed(xml_text):
    """Essays in the feed, newest first."""
    items = []
    for it in ET.fromstring(xml_text).iter("item"):
        items.append({
            "title": (it.findtext("title") or "").strip(),
            "url": (it.findtext("link") or "").strip(),
            "subtitle": (it.findtext("description") or "").strip(),
            "content": it.findtext(CONTENT) or "",
            "published": email.utils.parsedate_to_datetime(it.findtext("pubDate")),
        })
    return sorted(items, key=lambda i: i["published"], reverse=True)


def decide(item, now, existing_statuses, send_requested):
    """One of 'skip-old', 'skip-duplicate', 'send', 'promote', 'draft'."""
    if now - item["published"] > MAX_AGE:
        return "skip-old"
    live = [s for s in existing_statuses if s != "deleted"]
    if not live:
        return "send" if send_requested else "draft"
    if send_requested and all(s == "draft" for s in live):
        return "promote"
    return "skip-duplicate"


def pick_draft(existing):
    """Id of exactly one draft (lowest id by string sort, so reruns agree), else None."""
    ids = sorted(str(eid) for eid, status in existing if status == "draft")
    return ids[0] if ids else None


def send_blocked(action, send_requested, statuses):
    """Failure message when a requested send cannot happen, else None."""
    if not send_requested:
        return None
    if action == "skip-old":
        return f"send requested but the essay is older than {MAX_AGE} (24h window); nothing sent"
    if action == "skip-duplicate":
        live = [s for s in statuses if s != "deleted"]
        if any(s in DELIVERED for s in live):
            return None
        return f"send requested but existing email status {sorted(live)} cannot be sent; nothing sent"
    return None


def build_email(item, status):
    body = ""
    if item["subtitle"]:
        body += f"<p><em>{html.escape(item['subtitle'], quote=False)}</em></p>\n"
    body += item["content"] + f'\n<p><a href="{item["url"]}">Read it on the site</a></p>\n'
    return {"subject": item["title"], "body": body, "canonical_url": item["url"], "status": status}


def api(path, key, payload=None, method=None):
    req = urllib.request.Request(f"{API}{path}", headers={
        **UA, "Authorization": f"Token {key}", "Content-Type": "application/json",
    }, data=json.dumps(payload).encode() if payload is not None else None, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def statuses_for_subject(subject, key):
    """(id, status) pairs for emails whose subject is exactly `subject`."""
    q = urllib.parse.urlencode({"subject": subject, "page_size": 100, "excluded_fields": "body"})
    return [(e.get("id"), e.get("status")) for e in api(f"/emails?{q}", key).get("results", [])
            if e.get("subject") == subject]


def page_is_up(url, tries=10, wait=15):
    for n in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=20) as r:
                if r.status == 200:
                    return True
        except urllib.error.URLError as e:
            print(f"send-fa-email: {url} not up yet ({e})")
        if n < tries - 1:
            time.sleep(wait)
    return False


def act(item, key, send, dry, now):
    existing = statuses_for_subject(item["title"], key)
    statuses = [status for _, status in existing]
    action = decide(item, now, statuses, send)
    print(f"send-fa-email: {action}: {item['title']}{' (dry run)' if dry else ''}")
    problem = send_blocked(action, send, statuses)
    if problem:
        sys.exit("send-fa-email: " + problem)
    if action.startswith("skip") or dry:
        return
    if not page_is_up(item["url"]):
        sys.exit(f"send-fa-email: {item['url']} never returned 200; no email created")
    if action == "promote":
        eid = pick_draft(existing)
        if eid is None:
            sys.exit("send-fa-email: promote chosen but no draft id found; nothing sent")
        # Status only: edits made to the draft in Buttondown are mailed as left.
        made = api(f"/emails/{urllib.parse.quote(eid, safe='')}", key,
                   {"status": "about_to_send"}, method="PATCH")
        print(f"send-fa-email: promoted {eid} status {made.get('status')}")
        return
    status = "about_to_send" if action == "send" else "draft"
    made = api("/emails", key, build_email(item, status))
    print(f"send-fa-email: created {made.get('id')} status {made.get('status')}")


def main():
    key = os.environ.get("BUTTONDOWN_API_KEY", "")
    send = os.environ.get("SEND_EMAIL", "") == "true"
    dry = os.environ.get("DRY_RUN", "") == "1"
    if not key:
        sys.exit("send-fa-email: BUTTONDOWN_API_KEY is not set")

    with urllib.request.urlopen(urllib.request.Request(FEED, headers=UA), timeout=30) as r:
        items = parse_feed(r.read().decode("utf-8"))
    if not items:
        sys.exit("send-fa-email: feed has no items")
    act(items[0], key, send, dry, datetime.now(timezone.utc))


if __name__ == "__main__":
    main()
