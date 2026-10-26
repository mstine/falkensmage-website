#!/usr/bin/env python3
"""check-cutover.py — prove every old feralarchitecture.com URL lands somewhere real.

Run after the Cloudflare redirect rules go live:

    python3 scripts/check-cutover.py

Or before cutover, to prove every redirect *target* exists on a local or deployed build:

    python3 scripts/check-cutover.py --targets-only --site http://127.0.0.1:1313

Reads data/fa-legacy.json (the Substack export's slug list), so it checks exactly what
the gate built against. For each old URL it expects: first hop a 301 (permanent, so
search engines and Buttondown move with it), and a final 200 at the expected new page.
Exit 1 on any miss.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OLD = "https://feralarchitecture.com"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def hop(url):
    """One request, no redirect following. Returns (status, location)."""
    opener = urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, method="GET", headers={"User-Agent": "fa-cutover-check"})
    try:
        r = opener.open(req, timeout=20)
        return r.status, None
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get("Location")
    except urllib.error.URLError as e:
        return None, str(e.reason)


def follow(url, limit=5):
    """Follow redirects by hand. Returns (first_status, final_status, final_url, hops)."""
    first, hops = None, 0
    while True:
        status, loc = hop(url)
        if first is None:
            first = status
        if status in (301, 302, 307, 308) and loc and hops < limit:
            url = urllib.parse.urljoin(url, loc)
            hops += 1
            continue
        return first, status, url, hops


def expectations(site):
    legacy = json.loads((ROOT / "data" / "fa-legacy.json").read_text())
    for slug in legacy["essays"] + legacy["pages"]:
        yield f"{OLD}/p/{slug}", f"{site}/fa/{slug}/"
    for slug in legacy["withdrawn"]:
        yield f"{OLD}/p/{slug}", f"{site}/fa/"
    yield f"{OLD}/about", f"{site}/fa/about/"
    yield f"{OLD}/feed", f"{site}/fa/index.xml"
    yield f"{OLD}/", f"{site}/fa/"
    yield f"{OLD}/archive", f"{site}/fa/"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site", default="https://falkensmage.com")
    ap.add_argument("--targets-only", action="store_true",
                    help="skip the old URLs; just confirm every redirect target returns 200")
    args = ap.parse_args()

    misses, total = [], 0
    for old, want in expectations(args.site.rstrip("/")):
        total += 1
        if args.targets_only:
            first, final, url, _ = follow(want)
            ok = final == 200
            detail = f"{want} → {final}"
        else:
            first, final, url, hops = follow(old)
            ok = first == 301 and final == 200 and url.rstrip("/") == want.rstrip("/")
            detail = f"{old} → first {first}, final {final} at {url} ({hops} hops); want {want}"
        if not ok:
            misses.append(detail)
        time.sleep(0.15)

    mode = "targets" if args.targets_only else "redirects"
    print(f"check-cutover ({mode}): {total - len(misses)}/{total} OK")
    for m in misses:
        print(f"  MISS {m}")
    sys.exit(1 if misses else 0)


if __name__ == "__main__":
    main()
