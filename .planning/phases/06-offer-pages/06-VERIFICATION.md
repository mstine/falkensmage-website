---
phase: 06-offer-pages
verified: 2026-07-02T00:00:00Z
status: human_needed
score: 11/11 must-haves verified
behavior_unverified: 0
overrides_applied: 0
human_verification:
  - test: "Open /work/, /work/the-query/, /work/the-cast/, /work/the-daemon/ in a real browser (or hugo server --buildDrafts + DevTools) at a 375px viewport and confirm no horizontal overflow and that the Triad Rule / section-void/section-depth alternation reads visually coherent on each page."
    expected: "No horizontal scroll at 375px; sections read as intentional visual rhythm, not accidental clipping or color clash."
    why_human: "This mirrors the project's own pre-existing manual-only gate (Phase 1 THEME-05: 'no horizontal scroll at 375px' — explicitly documented as un-automatable, requires browser DevTools). Phase 6 adds four new pages built on the same CSS with zero new selectors, but the manual gate has never been exercised against these specific new pages/content lengths (long pitch paragraphs, price lines) — grep/build checks cannot see rendered visual overflow or spacing."
  - test: "Read the four offer/hub pages (and the repointed homepage CTA) end-to-end as a stranger arriving from social media would, and confirm the voice lands as intended and the pricing/CTA mechanics (especially The Daemon's consult-gate) are immediately legible without a second read."
    expected: "A first-time visitor understands what each offer is, what it costs, and what clicking the CTA does (esp. that The Daemon's CTA books a $150 consult, not a $4,500 purchase) within seconds."
    why_human: "Voice/tone quality and message clarity for a real human reader are inherently subjective judgments that automated grep/structure checks cannot make — the phase's own core value ('a stranger... instantly understands... in under ten seconds') is a UX/comprehension claim, not a structural one."
---

# Phase 6: Offer Pages Verification Report

**Phase Goal:** Turn falkensmage.com into a linkable commerce surface — a `/work/` hub plus The Query / The Cast / The Daemon offer pages with Cal.com link-out CTAs; homepage secondary CTA repointed to `/work/`. Composes ONLY from the existing `arcaeon` design system; holds v1.0 perf/a11y budgets.

**Verified:** 2026-07-02
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | `/work/` hub renders and links to all three offer pages (OFFER-01) | ✓ VERIFIED | `public/work/index.html` built and contains `href=/work/the-query/`, `href=/work/the-cast/`, `href=/work/the-daemon/` in a `social-grid`/`social-card` layout ranging `.Pages.ByWeight`; `tests/validate-phase-06.sh` OFFER-01 section: 4/4 pass |
| 2 | The Query renders $250 / 90-min archetypal tarot pitch with "Book & Pay" CTA (OFFER-02) | ✓ VERIFIED | `public/work/the-query/index.html` contains `<p>$250 / 90 minutes</p>` and `<a href=https://cal.com/PLACEHOLDER/the-query class="glow-radiant-core cta-button" target=_blank rel="noopener noreferrer">Book & Pay</a>`; validator OFFER-02: 3/3 pass |
| 3 | The Cast renders $325 / 90-min archetypal astrology pitch with "Book & Pay" CTA (OFFER-03) | ✓ VERIFIED | `public/work/the-cast/index.html` contains `<p>$325 / 90 minutes</p>` and identical CTA pattern resolving to `https://cal.com/PLACEHOLDER/the-cast`; validator OFFER-03: 3/3 pass |
| 4 | The Daemon renders $4,500 / 6-month coaching, consult-gated "Book a Clarity Consult ($150, credited)" CTA — NOT a direct buy (OFFER-04) | ✓ VERIFIED | `public/work/the-daemon/index.html` contains `<p>$4,500</p>` (no duration suffix — `duration` field correctly omitted from front matter) and CTA text exactly `Book a Clarity Consult ($150, credited)`; body prose makes the $150-credited gate explicit ("that $150 is credited straight into the $4,500... If it's not, you've spent $150 finding that out instead of $4,500"); validator's concrete negative check confirms CTA text is NOT `$4,500`/`Buy Now`/`Book & Pay` |
| 5 | Cal.com URLs are single-source config; no hardcoded booking URL anywhere in templates/content (OFFER-05) | ✓ VERIFIED | `hugo.toml` has `[params.booking]` with exactly `the-query`/`the-cast`/`the-daemon` keys; both `work/single.html` and `work/list.html` dereference `index site.Params.booking .Params.booking_key` (grep confirms zero `cal\.com` literals in templates or `content/work/*.md`); built CTA hrefs on all three offer pages match the `hugo.toml` values exactly (`the-query`→`.../the-query`, `the-cast`→`.../the-cast`, `the-daemon`→`.../the-daemon-consult`) |
| 6 | Homepage secondary CTA points to `/work/` (NAV-01) | ✓ VERIFIED | `content/_index.md` `cta_secondary: "Want to work together? <a href=\"/work/\">See how we can work together</a>"`; built `public/index.html` contains `<a href=/work/>See how we can work together</a>`; old `mailto:falkensmage@falkenslabyrinth.com` absent from built homepage; `safeHTML` front-matter mechanism (identity-cta.html) unchanged, no `target="_blank"` (correct internal-nav convention) |
| 7 | Composition is pure arcaeon reuse — no new CSS system/`<style>` blocks/new design language (OFFERQ-01) | ✓ VERIFIED | `git diff` across all Phase 6 commits vs. `themes/arcaeon/assets/css/main.css` is empty (zero lines changed — confirmed by direct diff, not just claim); both `work/single.html` and `work/list.html` contain zero `<style` blocks; only pre-existing classes used (`section`, `section-void`, `section-depth`, `section-content`, `display-text`, `glow-radiant-core`, `glow-interactive`, `social-grid`/`social-card`, `sigil-arc`, `sigil-boundary-tr`, `currently-label`) |
| 8 | Budgets held: CTAs link OUT only (no embedded widget/script), zero external deps/CDN/JS, viewport meta present, self-hosted fonts; `hugo --minify` builds clean (OFFERQ-02) | ✓ VERIFIED | Rendered `public/work/*` pages contain exactly one `<script>` tag each — the pre-existing Plausible analytics tag (unchanged from v1.0), zero booking-provider scripts/widgets/embeds; every `target=_blank` CTA carries `rel="noopener noreferrer"`; all four `/work/` pages carry `<meta name=viewport content="width=device-width,initial-scale=1">`; fonts are the same pre-existing self-hosted `.woff2` preloads; `rm -rf public/ resources/_gen/ && hugo --minify --quiet` exits 0 with no errors |
| 9 | Language hygiene: no "tarot reader" / "chaos magician" anywhere in `content/work/` (project-memory rule) | ✓ VERIFIED | `grep -rniE "tarot reader\|chaos magician" content/ themes/arcaeon/layouts/work/` returns zero matches repo-wide; practitioner framing used is "archetypal tarotist" (the-query) and "chaos witch and astrologer" (the-cast/the-daemon) |
| 10 | `tests/validate-phase-06.sh` exists, is executable, exits 0 with 32 checks passed | ✓ VERIFIED | Ran directly: `bash tests/validate-phase-06.sh` → "Results: 32 passed, 0 failed", "ALL CHECKS PASSED", exit code 0. Script is a genuine regression gate — checks are real assertions against built HTML/config, not hardcoded passes (spot-verified several checks by hand against `public/`, matched independently) |
| 11 | No regression to prior phases; pre-existing `validate-phase-02.sh` failures correctly out of scope | ✓ VERIFIED | `tests/validate-phase-01.sh`: 46/46 automated pass + 1 pre-existing manual-only item, exit 0. `tests/validate-phase-03.sh`: 39/39 pass, exit 0. `tests/validate-phase-02.sh`: 16/16 pass except SOCIAL-04 and CTA-01 — both confirmed via `git log -p` to predate Phase 6 (SOCIAL-04's `mytarotpulse.com` vs `my.tarotpulse.com` mismatch and CTA-01's removed "Coaching" text both trace to commit `aea350b`, April 2026, well before Phase 6's July commits); documented in `deferred-items.md` exactly as claimed |

**Score:** 11/11 truths verified (0 present-but-behavior-unverified)

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `hugo.toml` | `[params.booking]` table, 3 placeholder keys | ✓ VERIFIED | Confirmed present, values are `https://cal.com/PLACEHOLDER/*` placeholders per OFFER-F1 (explicitly deferred, documented) |
| `themes/arcaeon/layouts/work/single.html` | Offer-page template, config-driven CTA | ✓ VERIFIED | Exists, 3-section composition, `glow-radiant-core` CTA, dereferences `index site.Params.booking .Params.booking_key`, zero `<style>` |
| `themes/arcaeon/layouts/work/list.html` | Hub template, cards ranging offer pages | ✓ VERIFIED | Exists, ranges `.Pages.ByWeight`, links via `.RelPermalink`, zero `<style>` |
| `content/work/_index.md` | Hub front-door content | ✓ VERIFIED | Exists, short 2-sentence framing, no card markup (template-generated), no CTA link (correct — cards are the nav) |
| `content/work/the-query.md` | Tarot offer content | ✓ VERIFIED | Exists, canonical front matter exact match ($250, 90 minutes, Book & Pay, the-query, weight 10) |
| `content/work/the-cast.md` | Astrology offer content | ✓ VERIFIED | Exists, canonical front matter exact match ($325, 90 minutes, Book & Pay, the-cast, weight 20) |
| `content/work/the-daemon.md` | Coaching offer content | ✓ VERIFIED | Exists, canonical front matter exact match ($4,500, duration omitted, consult-gated CTA text, the-daemon, weight 30) |
| `content/_index.md` (`cta_secondary`) | Repointed to `/work/` | ✓ VERIFIED | Changed exactly one field value; mechanism (safeHTML raw-`<a>` string) preserved |
| `tests/validate-phase-06.sh` | 32-check regression gate | ✓ VERIFIED | Exists, executable, exits 0, 32/32 pass |

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `content/work/the-query.md` `booking_key: the-query` | `hugo.toml [params.booking]."the-query"` | `work/single.html` `index site.Params.booking .Params.booking_key` | ✓ WIRED | Built HTML CTA href = `https://cal.com/PLACEHOLDER/the-query`, exact match to config value |
| `content/work/the-cast.md` `booking_key: the-cast` | `hugo.toml [params.booking]."the-cast"` | same mechanism | ✓ WIRED | Built HTML CTA href = `https://cal.com/PLACEHOLDER/the-cast`, exact match |
| `content/work/the-daemon.md` `booking_key: the-daemon` | `hugo.toml [params.booking]."the-daemon"` | same mechanism | ✓ WIRED | Built HTML CTA href = `https://cal.com/PLACEHOLDER/the-daemon-consult`, exact match |
| `content/work/_index.md` (hub) | each offer page | `work/list.html` `range .Pages.ByWeight` + `.RelPermalink` | ✓ WIRED | Built hub HTML contains internal links to all 3 offer paths, ordered by weight (Query→Cast→Daemon) |
| `content/_index.md` `cta_secondary` | `/work/` hub | `identity-cta.html` rendering `cta_secondary \| safeHTML` | ✓ WIRED | Built homepage HTML contains `<a href=/work/>See how we can work together</a>`; old mailto absent |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|---------------------|--------|
| `work/single.html` CTA href | `index site.Params.booking .Params.booking_key` | `hugo.toml [params.booking]` | Yes — real (placeholder-but-configured) URLs, not empty/static stub | ✓ FLOWING |
| `work/list.html` offer cards | `.Pages.ByWeight` | Hugo content collection (`content/work/*.md`) | Yes — 3 real pages rendered with real front-matter values (price/summary/offer_name) | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Clean build succeeds | `rm -rf public/ resources/_gen/ && hugo --minify --quiet` | exit 0, no warnings/errors | ✓ PASS |
| All 4 `/work/` pages render with correct data | direct `grep` against built `public/work/*/index.html` | prices/CTAs/hrefs all match canonical table exactly | ✓ PASS |
| Zero booking script/widget in built output | `grep -rn "<script" public/work/` | only Plausible analytics tag (pre-existing, unchanged) | ✓ PASS |
| No new CSS introduced | `git diff` vs. `themes/arcaeon/assets/css/main.css` across all Phase 6 commits | zero lines changed | ✓ PASS |
| Language hygiene repo-wide | `grep -rniE "tarot reader|chaos magician" content/ themes/arcaeon/layouts/work/` | zero matches | ✓ PASS |

### Probe Execution

| Probe | Command | Result | Status |
|-------|---------|--------|--------|
| `tests/validate-phase-06.sh` | `bash tests/validate-phase-06.sh` | 32 passed, 0 failed, exit 0 | ✓ PASS |
| `tests/validate-phase-01.sh` (regression) | `bash tests/validate-phase-01.sh` | 46 passed, 0 failed, 1 manual-only, exit 0 | ✓ PASS |
| `tests/validate-phase-02.sh` (regression) | `bash tests/validate-phase-02.sh` | 16 passed, 2 failed (SOCIAL-04, CTA-01), exit 1 | ⚠️ PRE-EXISTING FAILURE — confirmed via `git log -p` to predate Phase 6 (traces to commit `aea350b`, April 2026); not attributable to this phase; correctly logged in `deferred-items.md` |
| `tests/validate-phase-03.sh` (regression) | `bash tests/validate-phase-03.sh` | 39 passed, 0 failed, exit 0 | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|--------------|--------|----------|
| OFFER-01 | 06-01, 06-02 | `/work/` hub renders and links to all three offers | ✓ SATISFIED | Truth #1 |
| OFFER-02 | 06-02 | The Query — $250/90-min tarot, "Book & Pay" CTA | ✓ SATISFIED | Truth #2 |
| OFFER-03 | 06-02 | The Cast — $325/90-min astrology, "Book & Pay" CTA | ✓ SATISFIED | Truth #3 |
| OFFER-04 | 06-02 | The Daemon — $4,500 consult-gated coaching CTA | ✓ SATISFIED | Truth #4 |
| OFFER-05 | 06-01 | Single-source Cal.com config, no hardcoded URLs | ✓ SATISFIED | Truth #5 |
| NAV-01 | 06-03 | Homepage secondary CTA → `/work/` | ✓ SATISFIED | Truth #6 |
| OFFERQ-01 | 06-01, 06-03 | Pure arcaeon design-system reuse | ✓ SATISFIED | Truth #7 |
| OFFERQ-02 | 06-01, 06-03 | Budgets held (link-out, zero deps, mobile-first, WCAG AA) | ✓ SATISFIED | Truth #8 |

No orphaned requirements — all 8 v1.1 requirement IDs are declared in plan frontmatter and mapped to satisfied truths; REQUIREMENTS.md traceability table shows 8/8 mapped, 0 unmapped, matching this verification's findings.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `hugo.toml` | 17-19 | `PLACEHOLDER` in Cal.com URL values | ℹ️ Info | Not a debt marker — explicitly documented, intentional design decision (OFFER-05/OFFER-F1: placeholders swapped in one location once Cal.com is stood up). Referenced formal follow-up work exists (OFFER-F1 in ROADMAP/REQUIREMENTS.md). Not a gap. |

No TBD/FIXME/XXX/TODO/HACK markers, no empty implementations, no hardcoded-empty-data stubs, and no console.log-only implementations found in any Phase 6 file (`hugo.toml`, both `work/` templates, all 4 content files, `tests/validate-phase-06.sh`, `content/_index.md`).

### Human Verification Required

1. **375px visual overflow check on the four new `/work/` pages**
   **Test:** Open `/work/`, `/work/the-query/`, `/work/the-cast/`, `/work/the-daemon/` via `hugo server --buildDrafts` in a browser at a 375px viewport (DevTools device toolbar).
   **Expected:** No horizontal scroll on any page; the Triad Rule / section-void/section-depth alternation reads as coherent visual rhythm.
   **Why human:** Mirrors the project's own pre-existing manual-only gate (Phase 1's THEME-05), which is explicitly documented as un-automatable. Zero new CSS was introduced (confirmed by diff), which makes overflow unlikely, but the specific new pages/longer pitch paragraphs have never actually been rendered and eyeballed at 375px.

2. **Voice/comprehension spot-check for a first-time visitor**
   **Test:** Read all four pages (plus the repointed homepage CTA) as a stranger arriving from social media would.
   **Expected:** The offer, price, and CTA mechanics are immediately clear — especially that The Daemon's CTA books a $150 consult (credited), not a direct $4,500 purchase.
   **Why human:** Voice quality and message clarity for a human reader are subjective judgments outside grep/structural verification; this is also literally the project's stated Core Value ("a stranger... instantly understands... in under ten seconds").

### Gaps Summary

No gaps found. All 8 requirement IDs (OFFER-01 through OFFER-05, NAV-01, OFFERQ-01, OFFERQ-02) are verified against the actual built codebase — not just SUMMARY.md claims. Every artifact was independently re-verified by reading source files directly, running a fresh clean `hugo --minify` build, grepping the actual rendered HTML output, and diffing git history for the two pre-existing `validate-phase-02.sh` failures to confirm they predate this phase. The only open items are two human-judgment spot-checks (visual overflow at 375px, and voice/comprehension quality) that no automated check in this codebase's own conventions claims to cover — routing this to `human_needed` rather than `passed`, per the verification decision tree.

---

*Verified: 2026-07-02*
*Verifier: Claude (gsd-verifier)*
