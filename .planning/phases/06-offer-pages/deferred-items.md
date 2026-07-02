# Deferred Items — Phase 06 (offer-pages)

Logged during 06-03 execution. These are pre-existing failures unrelated to
this plan's changes (content/_index.md `cta_secondary` repoint, tests/validate-phase-06.sh).
Per the executor's scope-boundary rule, out-of-scope pre-existing failures are
logged here, not fixed.

## validate-phase-02.sh pre-existing failures (confirmed present at HEAD~1, before 06-03)

1. **SOCIAL-04** — expects platform domain string `my.tarotpulse.com` (with a dot
   after "my") in built HTML. Actual TarotPulse URL in `content/_index.md`
   `social_links` is `https://mytarotpulse.com` (no dot). This mismatch predates
   Phase 6 — confirmed via `git show HEAD~1:content/_index.md`, the URL was
   already `mytarotpulse.com` before this plan's commit. The phase-2 validator's
   platform-domain list was never updated when the TarotPulse URL was set/changed
   in an earlier phase.

2. **CTA-01** — expects literal text `Coaching` present in built HTML (from an
   original "Coaching. Speaking. Collaboration." CTA copy). The homepage
   `identity_blocks` copy was rewritten in a later phase (commit `aea350b fix(02):
   desktop hero aspect ratio + real copy in Matt's voice`) to the current
   "archetypal tarotist, astrologer, and chaos witch" voice — the word "Coaching"
   no longer appears anywhere on the page. Confirmed present at HEAD~1 (before
   06-03) via `git show HEAD~1:content/_index.md` — not introduced by this plan.

Neither failure is caused by, or in scope of, plan 06-03 (which only touches
`content/_index.md`'s `cta_secondary` line and adds `tests/validate-phase-06.sh`).
Recommend a future phase (or a dedicated tech-debt plan) reconcile
`tests/validate-phase-02.sh`'s stale assertions against the current homepage copy.
