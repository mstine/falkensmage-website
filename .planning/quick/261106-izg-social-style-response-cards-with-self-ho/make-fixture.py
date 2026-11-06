#!/usr/bin/env python3
"""Review-gate fixture for quick task 261106-izg: seeds data/webmentions.json and two cached
avatars so the Lovers note's Responses section can be built and screenshotted offline.

    python3 -I .planning/quick/261106-izg-social-style-response-cards-with-self-ho/make-fixture.py

Run from the repo root. Writes data/webmentions.json and static/webmention-avatars/ (both
gitignored). Delete both afterwards. Stdlib only; nothing is fetched.
"""
import binascii
import datetime
import importlib.util
import struct
import zlib
from pathlib import Path

ROOT = Path.cwd()
spec = importlib.util.spec_from_file_location("pull_webmentions", ROOT / "scripts" / "pull-webmentions.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def png(rgb, size=96):
    def chunk(tag, body):
        return (struct.pack(">I", len(body)) + tag + body
                + struct.pack(">I", binascii.crc32(tag + body) & 0xFFFFFFFF))
    row = b"\x00" + bytes(rgb) * size
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * size)) + chunk(b"IEND", b""))


ROWAN = "https://avatars.webmention.io/fixture/rowan.png"
SOL = "https://avatars.webmention.io/fixture/sol.png"
m.AVATAR_DIR.mkdir(parents=True, exist_ok=True)
(m.AVATAR_DIR / (m.avatar_name(ROWAN) + ".png")).write_bytes(png((0xFF, 0xB3, 0x47)))   # fusion gold
(m.AVATAR_DIR / (m.avatar_name(SOL) + ".png")).write_bytes(png((0x5B, 0xE7, 0xFF)))     # ion glow
m.fetch_avatar = lambda url: None   # only the seeded cache resolves

TARGET = "https://falkensmage.com/notes/the-lovers-isn-t-a-romance/"


def kid(wm_id, prop, source, url, name, author_url, photo=None, text=None, published=None):
    author = {"type": "card", "name": name, "url": author_url}
    if photo:
        author["photo"] = photo
    c = {"type": "entry", "wm-id": wm_id, "wm-property": prop, "wm-target": TARGET,
         "wm-source": source, "wm-private": False, "url": url, "author": author}
    if text:
        c["content"] = {"text": text}
    if published:
        c["published"] = published
    return c


MAST = "@falkensmage@mastodon.social/117570501730802441"
children = [
    kid(1, "in-reply-to", f"https://brid.gy/comment/mastodon/{MAST}/1",
        "https://rowanvale.example/.ghost/activitypub/note/fixture", "Rowan Vale",
        "https://rowanvale.example/", ROWAN,
        "Fixture reply: the Lovers as a choice rather than a romance, and a longer line to check wrapping.",
        "2026-11-05T12:00:00+00:00"),
    kid(2, "in-reply-to", "https://brid.gy/comment/bluesky/falkensmage.com/fixture/2",
        "https://bsky.app/profile/wren.example/post/3fixture", "Wren",
        "https://bsky.app/profile/wren.example", None,
        "Fixture reply with no photo, so the initial shows.", "2026-11-05T15:30:00+00:00"),
    kid(3, "like-of", f"https://brid.gy/like/mastodon/{MAST}/11", f"https://mastodon.social/@falkensmage/117570501730802441#favorited-by-11",
        "Rowan Vale", "https://rowanvale.example/", ROWAN),
    kid(4, "like-of", f"https://brid.gy/like/mastodon/{MAST}/12", f"https://mastodon.social/@falkensmage/117570501730802441#favorited-by-12",
        "Ivy Marsh", "https://ivymarsh.example/"),
    kid(5, "repost-of", f"https://brid.gy/repost/mastodon/{MAST}/13", f"https://mastodon.social/@falkensmage/117570501730802441#reblogged-by-13",
        "Sol Ortega", "https://solortega.example/", SOL),
]
pages, counts, blocked, avatar_counts = m.assemble(children, m.load_blocklist(m.BLOCKLIST), m.AVATAR_DIR)
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
pages = m.write_data(m.DATA, pages, now)
m.prune_avatars(m.AVATAR_DIR, pages)
print("fixture written:", avatar_counts)
