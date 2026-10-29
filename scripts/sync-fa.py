#!/usr/bin/env python3
"""sync-fa.py — one-way sync of published Feral Architecture essays into content/fa/.

Psyche drafts (~/.psyche/drafts) are the single source of truth. This script never
writes back to them; it regenerates content/fa/<slug>/ page bundles from scratch on
every run, so an edit made here instead of in the draft is overwritten, loudly, next
run (design principle 10: maintenance never returns to the failing substrate).

A draft is published when its frontmatter has `published_at` and a `published_url`
ending in /p/<slug> or /fa/<slug>, and its status is not withdrawn or superseded.

Usage: python3 scripts/sync-fa.py [--drafts DIR] [--covers DIR]
Exit 1 if any published essay fails to produce a bundle.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "fa"
SOURCE_DIRS = ["feral-architecture", "hermetic", "hermetic/foundations", "hermetic/deeper-cuts"]
SERIES = {
    "hermetic/foundations": "The Construct · Foundations",
    "hermetic/deeper-cuts": "The Construct · Deeper Cuts",
}
FM_RE = re.compile(r"\A---\n(.*?)\n---\n", re.S)
SLUG_RE = re.compile(r"/(?:p|fa)/([a-z0-9-]+)")
# Old site paths inside essay bodies: feralarchitecture.com/p/<slug> → /fa/<slug>/
XLINK_RE = re.compile(r"https?://(?:www\.)?feralarchitecture(?:\.substack)?\.com/p/([a-z0-9-]+)[^\s)\"']*")
# Other old-site paths: the ones with a home here map over; Substack-only ones
# (Chat, subscribe, …) have nothing to point at, so the link becomes plain text.
SITE_PATHS = {"": "/fa/", "about": "/fa/about/", "archive": "/fa/archive/"}
SITELINK_RE = re.compile(r"\[([^\]]+)\]\(https?://(?:www\.)?feralarchitecture(?:\.substack)?\.com/?([a-z-]*)[^)\s]*\)")
PASTE_MARK = "PASTE EVERYTHING BELOW THIS LINE"
# Substack-era paste instruction: "[insert cover: foundation-1-the-morrigan-and-grep]"
# names an essay by its draft filename (minus the date). Becomes that essay's
# cover, linked to the essay.
INSERT_COVER_RE = re.compile(r"\[insert cover:\s*([a-z0-9-]+)\s*\]", re.I)
IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)\)")
MAX_EDGE = 1600


try:
    import yaml
except ImportError:  # the line-based reader below copes with simple frontmatter
    yaml = None

_parsed = {}


def field(fm, key):
    if yaml is not None:
        if fm not in _parsed:
            try:
                _parsed[fm] = yaml.safe_load(fm) or {}
            except yaml.YAMLError:
                _parsed[fm] = None
        data = _parsed[fm]
        if isinstance(data, dict):
            v = data.get(key)
            if v is None:
                return ""
            if hasattr(v, "isoformat"):
                return v.isoformat()
            return " ".join(str(v).split()) if isinstance(v, str) else str(v)
    return _field_lines(fm, key)


def _field_lines(fm, key):
    m = re.search(rf"^{key}:\s*(.*)$", fm, re.M)
    if not m:
        return ""
    v = m.group(1).strip()
    if v in (">-", "|", ">", "|-"):  # folded scalar: join the indented lines below it
        rest = fm[m.end():].split("\n")[1:]
        lines = []
        for line in rest:
            if line.startswith("  "):
                lines.append(line.strip())
            else:
                break
        v = " ".join(lines)
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
        v = v[1:-1].replace("''", "'") if v[0] == "'" else json.loads(v)
    return v


def tokens(s):
    return set(re.findall(r"[a-z0-9]+", s.lower())) - {"the", "a", "of", "and", "is", "it", "cover", "final"}


def first_image(d):
    if not d.is_dir():
        return None
    imgs = sorted(p for p in d.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp"))
    covers = [p for p in imgs if "cover" in p.name.lower()]
    return (covers or imgs or [None])[0]


def resolve_cover(draft, fm, covers):
    rel = field(fm, "cover_image")
    if rel and (draft.parent / rel).is_file():
        return draft.parent / rel
    src = field(fm, "cover_source")
    if src:
        src = re.sub(r"\s+\(.*$", "", src)
        p = Path(os.path.expanduser(src.replace("/Documents/Business-Brand/", "/mnemosyne/business-brand/")))
        if p.is_file():
            return p
    if not covers.is_dir():
        return None
    stem = draft.stem
    # The Construct: construct-foundation-1-*, construct-deeper-cut-2-*
    m = re.match(r"\d{4}-\d{2}-\d{2}-((?:foundation|deeper-cut)-\d+)", stem)
    if m:
        for d in sorted(covers.glob(f"construct-{m.group(1)}-*")):
            img = first_image(d / "final") or first_image(d)
            if img:
                return img
    # Everything else: same date prefix, best word overlap with the draft name
    date = stem[:10]
    want = tokens(stem[11:])
    best, score = None, 0
    for d in covers.glob(f"{date}-*"):
        s = len(want & tokens(d.name[11:]))
        if s > score:
            best, score = d, s
    if best:
        return first_image(best / "final") or first_image(best)
    return None


def resolve_inline(draft, ref, covers):
    p = (draft.parent / ref).resolve()
    if p.is_file():
        return p
    # assets/<dir>/<file> → covers/<dir>/{final,images,.}/<file>
    parts = Path(ref).parts
    if "assets" in parts and len(parts) >= parts.index("assets") + 3:
        i = parts.index("assets")
        d, name = parts[i + 1], parts[-1]
        for sub in ("final", "images", "."):
            c = covers / d / sub / name
            if c.is_file():
                return c
    return None


def put_image(src, dest):
    """Copy src to dest as a JPEG no larger than MAX_EDGE on its long side."""
    r = subprocess.run(
        ["sips", "-s", "format", "jpeg", "-s", "formatOptions", "82", "-Z", str(MAX_EDGE), str(src), "--out", str(dest)],
        capture_output=True, text=True,
    )
    if r.returncode != 0 or not dest.is_file():
        raise RuntimeError(f"sips failed on {src}: {r.stderr.strip()}")


def clean_body(body, title, subtitle):
    lines = body.lstrip("\n").split("\n")
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    while lines and not lines[0].strip():
        lines = lines[1:]
    # The italic dek line (bare, or labeled "**Subtitle:**") duplicates `subtitle`;
    # the template renders that. A divider right under it is draft scaffolding too.
    if lines and re.fullmatch(r"(?:\*\*Subtitle:\*\*\s*)?\*[^*].*\*", lines[0].strip()):
        lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
        if lines and re.fullmatch(r"---[ \t]*", lines[0]):
            lines = lines[1:]
        while lines and not lines[0].strip():
            lines = lines[1:]
    body = "\n".join(lines).strip() + "\n"
    # Back-to-back dividers (a removed Substack widget leaves one on each side) → one.
    return re.sub(r"(?m)^---[ \t]*\n(?:[ \t]*\n)*---[ \t]*$", "---", body)


def rewrite_links(body, known, withdrawn, where, problems):
    def essay(mm):
        slug = mm.group(1)
        if slug in withdrawn:
            return "/fa/"
        if slug not in known:
            problems.append(f"{where}: link to unknown slug /p/{slug} (left pointing at /fa/{slug}/)")
        return f"/fa/{slug}/"

    def site(mm):
        text, path = mm.group(1), mm.group(2)
        if path in SITE_PATHS:
            return f"[{text}]({SITE_PATHS[path]})"
        problems.append(f"{where}: unlinked Substack-only link [{text}](/{path})")
        return text

    # A link to a withdrawn piece keeps its words and loses the link.
    body = re.sub(r"\[([^\]]+)\]\(" + XLINK_RE.pattern + r"\)",
                  lambda mm: mm.group(1) if mm.group(2) in withdrawn else mm.group(0), body)
    body = XLINK_RE.sub(essay, body)
    return SITELINK_RE.sub(site, body)


def page_body(text):
    """Body of a page draft: drop frontmatter, any Substack paste marker, HTML comments."""
    m = FM_RE.match(text)
    body = text[m.end():] if m else text
    if PASTE_MARK in body:
        body = body.split(PASTE_MARK, 1)[1].split("\n", 1)[1]
    return re.sub(r"<!--.*?-->", "", body, flags=re.S)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--drafts", default=os.path.expanduser("~/.psyche/drafts"))
    ap.add_argument("--covers", default=os.path.expanduser("~/mnemosyne/business-brand/Feral-Architecture/covers"))
    args = ap.parse_args()
    drafts, covers = Path(args.drafts), Path(args.covers)

    legacy = set(json.loads((ROOT / "data" / "fa-legacy.json").read_text())["essays"])
    essays, withdrawn, problems, skipped = [], set(), [], []
    for sub in SOURCE_DIRS:
        for p in sorted((drafts / sub).glob("*.md")):
            text = p.read_text(encoding="utf-8")
            m = FM_RE.match(text)
            if not m:
                continue
            fm = m.group(1)
            url = field(fm, "published_url")
            sm = SLUG_RE.search(url or "")
            status = field(fm, "status")
            if sm and status.startswith("withdrawn"):
                withdrawn.add(sm.group(1))
                continue
            if not (sm and field(fm, "published_at")) or status.startswith("superseded"):
                continue
            # Old essays must be on the legacy list (stops retired pitch emails that once
            # carried a Substack URL); new essays publish straight to falkensmage.com.
            if "falkensmage.com/fa/" not in url and sm.group(1) not in legacy:
                skipped.append(f"{sub}/{p.name}")
                continue
            essays.append((p, sub, fm, text[m.end():], sm.group(1)))

    pages = json.loads((ROOT / "data" / "fa-pages.json").read_text())["pages"]
    slugs = [e[4] for e in essays]
    known = set(slugs) | {pg["slug"] for pg in pages}
    dupes = {s for s in slugs if slugs.count(s) > 1}
    if dupes:
        sys.exit(f"sync-fa: duplicate slugs across drafts: {sorted(dupes)}")

    # Regenerate from scratch: every bundle under content/fa/ is owned by this script.
    if OUT.exists():
        for child in OUT.iterdir():
            if child.is_dir():
                shutil.rmtree(child)
    OUT.mkdir(parents=True, exist_ok=True)

    no_cover = []
    by_stem = {}  # draft stem minus date → (slug, title, cover path)
    for p, sub, fm, body, slug in essays:
        title = field(fm, "title")
        subtitle = field(fm, "subtitle")
        if not subtitle:
            dek = re.search(r"^\*([^*].*)\*\s*$", body, re.M)
            subtitle = dek.group(1) if dek else ""
        bundle = OUT / slug
        bundle.mkdir()

        body = clean_body(body, title, subtitle)
        body = rewrite_links(body, known, withdrawn, slug, problems)

        def inline(mm):
            alt, ref = mm.group(1), mm.group(2)
            if ref.startswith(("http://", "https://")):
                return mm.group(0)
            src = resolve_inline(p, ref, covers)
            if not src:
                problems.append(f"{slug}: dropped unresolvable inline image {ref}")
                return ""
            name = re.sub(r"[^a-z0-9.-]+", "-", Path(ref).stem.lower()) + ".jpg"
            put_image(src, bundle / name)
            return f"![{alt}]({name})"

        # A cover image opening the body duplicates the cover the template renders.
        lead = IMG_RE.match(body)
        if lead and "cover" in Path(lead.group(2)).stem.lower():
            body = body[lead.end():].lstrip("\n")
        body = IMG_RE.sub(inline, body)

        cover = resolve_cover(p, fm, covers)
        by_stem[re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)] = (slug, title, cover)
        if cover:
            put_image(cover, bundle / "cover.jpg")
        else:
            no_cover.append(slug)

        front = {
            "title": title,
            "subtitle": subtitle,
            "date": field(fm, "published_at"),
            "slug": slug,
            "legacy_url": f"https://feralarchitecture.com/p/{slug}",
            "source": f"{sub}/{p.name}",
        }
        if sub in SERIES:
            front["series"] = SERIES[sub]
        if cover:
            front["cover"] = "cover.jpg"
        head = "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items())
        (bundle / "index.md").write_text(f"---\n{head}\n---\n\n{body}", encoding="utf-8")

    for weight, pg in enumerate(pages, start=1):
        src = drafts / pg["source"]
        body = page_body(src.read_text(encoding="utf-8"))
        h1 = re.search(r"^# (.+)$", body, re.M)
        title = h1.group(1).strip() if h1 else pg["slug"].replace("-", " ").title()
        dek = re.search(r"^\*([^*].*)\*\s*$", body, re.M)
        body = rewrite_links(clean_body(body, title, ""), known, withdrawn, pg["slug"], problems)
        bundle = OUT / pg["slug"]
        bundle.mkdir()

        def insert_cover(mm, where=pg["slug"], bundle=bundle):
            name = mm.group(1).lower()
            hit = by_stem.get(name)
            if not hit or not hit[2]:
                problems.append(f"{where}: dropped unresolvable placeholder {mm.group(0)}")
                return ""
            eslug, etitle, ecover = hit
            put_image(ecover, bundle / f"cover-{name}.jpg")
            return f"[![{etitle}](cover-{name}.jpg)](/fa/{eslug}/)"

        body = INSERT_COVER_RE.sub(insert_cover, body)
        if pg.get("grid"):
            # Grid cards read cover-first: "**I · Title**\n*[![…](cover)](link)*" → cover line, then title.
            body = re.sub(r"^(\*\*[^\n]+\*\*)\n(\*\[!\[[^\n]+\)\*)$", r"\2\n\1", body, flags=re.M)
        front = {"title": title, "subtitle": dek.group(1) if dek else "", "slug": pg["slug"],
                 "fa_page": True, "weight": weight, "source": pg["source"]}
        if pg.get("grid"):
            front["grid"] = True
        if pg["slug"] != "about" and pg.get("legacy", True):
            front["legacy_url"] = f"https://feralarchitecture.com/p/{pg['slug']}"
        head = "\n".join(f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items())
        (bundle / "index.md").write_text(f"---\n{head}\n---\n\n{body}", encoding="utf-8")

    archive = OUT / "archive"
    archive.mkdir()
    (archive / "index.md").write_text(
        '---\ntitle: "Archive"\nslug: "archive"\nlayout: "archive"\nfa_page: true\n---\n', encoding="utf-8")

    print(f"sync-fa: {len(pages)} pages + archive → content/fa/")
    print(f"sync-fa: {len(essays)} essays → content/fa/ ({len(essays) - len(no_cover)} with covers)")
    for s in skipped:
        print(f"sync-fa: skipped (not a legacy essay): {s}")
    if withdrawn:
        print(f"sync-fa: withdrawn, excluded: {', '.join(sorted(withdrawn))}")
    for s in no_cover:
        print(f"sync-fa: WARN no cover resolved for {s}")
    for line in problems:
        print(f"sync-fa: WARN {line}")


if __name__ == "__main__":
    main()
