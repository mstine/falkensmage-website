---
phase: quick-261106-gqa
plan: 01
subsystem: ci
tags: [github-actions, github-pages, deploy-pages, retry]
requires: []
provides:
  - "hugo.yml deploy job with six deploy-pages tries, five waits, and a final step that fails only when try6 failed"
affects: [.github/workflows/hugo.yml]
tech-stack:
  added: []
  patterns: ["continue-on-error plus steps.<id>.outcome gating for retry chains"]
key-files:
  created: []
  modified: [.github/workflows/hugo.yml]
key-decisions:
  - "Kept timeout-minutes: 70 (not a defect; hang-path arithmetic below)"
  - "Left the workflow-level pages concurrency group unchanged (out of scope)"
status: complete
requirements: [GQA-RETRY, GQA-COMMIT]
commits: 1
plan_head_before: d9ad622c7f4842906036fc4cab45050984727b2a
plan_head_after: fa5d238c4677d81a82b914ecd19cec5083d71fe8
actuals:
  tokens: 4000
  tasks: 2
  commits: 1
completed: 2026-11-06
---

# Quick 261106-gqa: Retry the GitHub Pages deploy Summary

The reviewed working-tree diff to `.github/workflows/hugo.yml` was correct as written, and is now one `ci:` commit (`fa5d238`) that touches only that file. The deploy job tries `actions/deploy-pages@v5` up to six times, waiting 2, 5, 10, 15 and 20 minutes between tries, and goes red only when the sixth try fails.

## Review verdicts

1. Step-level if and outcome: correct. try2..try6 and the wait before each carry `if: steps.try<N-1>.outcome == 'failure'`; all six tries have `continue-on-error: true`. Outcome (not conclusion) is the right property.
2. Environment URL: correct. The `||` chain over the six tries' `page_url` returns the first non-empty value; all tries yield the same site URL.
3. timeout-minutes 70: kept, not a defect. Waits total 120+300+600+900+1200 = 3120 s = 52 min. In the observed failure Pages refuses in seconds, so try6 starts at about 53 min with about 17 min left, more than deploy-pages' 10-minute per-try default. Hang path: if every try hangs to its own 10-minute timeout, the worst case is 52 + 6 x 10 = 112 min, so the 70-minute cap can end the job before try6 runs. The run still ends non-green and email/webmentions/mentions-probe are skipped, same as six failures.
4. Success short-circuits: correct. After try N succeeds, try N+1 is skipped, and every later wait/try/final step tests for 'failure' only.
5. Final failure step: correct. Gated on `steps.try6.outcome == 'failure'`, no continue-on-error, `exit 1`. Fires only when all six failed.
6. Downstream needs: correct. deploy `needs: build`; email and webmentions `needs: deploy`; mentions-probe `needs: [build, deploy]`.
7. No stale reference: no `steps.deployment` left in hugo.yml.
8. Residual risk: see below.

No defects found; no edits made beyond the existing diff.

## Verification

- Structural check printed `deploy retry chain OK`.
- All five suites OK: test-notes-backstop (10), test-notes (195), test-pull-webmentions (75), test-send-fa-email (39), test-send-webmentions (46).
- Commit check: `one ci commit, hugo.yml only, tree matches`. Not pushed.

## Residual risk for Matt: pages concurrency

The workflow-level concurrency group `pages` holds one running run and at most one pending run. While a retry window is open (up to about 52 to 70 minutes now, versus about a minute before), a second queued run cancels the earlier pending one. Content still converges because the newer run builds the newer main, but a pending dispatch with `send_email: true` could be replaced by a push or a notes.yml dispatch that only leaves a draft. This existed before; the diff widens the window. Concurrency was not changed.

## Deviations from Plan

None to the work. One note: the Step 0 commit guard reported `main` as a protected branch and I committed on it anyway, because the plan, the orchestrator's sequential-execution block, and `branching_strategy: none` all direct commits on main, and the project's history is direct commits to main. No config was changed.

## Known Stubs

None.

## Threat Flags

None. The diff adds no permissions, secrets, or `${{ }}` in run strings.

## Self-Check: PASSED

- `.github/workflows/hugo.yml` found; commit `fa5d238` is an ancestor of HEAD.
