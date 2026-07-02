---
status: testing
phase: 06-offer-pages
source: [06-VERIFICATION.md]
started: 2026-07-02
updated: 2026-07-02
---

## Current Test

number: 1
name: 375px visual overflow check on the four new /work/ pages
expected: |
  No horizontal scroll on /work/, /work/the-query/, /work/the-cast/, /work/the-daemon/
  at a 375px viewport; the section-void/section-depth alternation and Triad Rule read as
  intentional visual rhythm, not accidental clipping or color clash.
awaiting: user response

## Tests

### 1. 375px visual overflow check on the four new /work/ pages
expected: Open /work/, /work/the-query/, /work/the-cast/, /work/the-daemon/ via `hugo server --buildDrafts` in a browser at a 375px viewport (DevTools device toolbar). No horizontal scroll on any page; the Triad Rule / section-void/section-depth alternation reads as coherent visual rhythm. (Zero new CSS was introduced — confirmed by an empty `git diff` against main.css — so overflow is unlikely, but the specific new pages with longer pitch paragraphs and price lines have never been rendered and eyeballed at 375px.)
result: [pending]

### 2. Voice/comprehension spot-check for a first-time visitor
expected: Read the four /work/ pages (and the repointed homepage CTA) end-to-end as a stranger arriving from social media would. A first-time visitor understands what each offer is, what it costs, and what clicking the CTA does — especially that The Daemon's CTA books a $150 clarity consult (credited), NOT a $4,500 purchase — within seconds. Voice lands as intended (matches the homepage register).
result: [pending]

## Summary

total: 2
passed: 0
issues: 0
pending: 2
skipped: 0
blocked: 0

## Gaps
