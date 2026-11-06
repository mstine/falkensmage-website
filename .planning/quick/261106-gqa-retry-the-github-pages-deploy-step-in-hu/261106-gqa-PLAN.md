---
phase: quick-261106-gqa
plan: 01
type: execute
wave: 1
depends_on: []
files_modified:
  - .github/workflows/hugo.yml
autonomous: true
requirements:
  - GQA-RETRY
  - GQA-COMMIT

estimate:
  tokens: 25000
  raw_tokens: 25000
  tasks: 2
  confidence: low

must_haves:
  truths:
    - "A failed deploy try is retried after waits of 2, 5, 10, 15 and 20 minutes, six tries in all, about 52 minutes of waiting"
    - "A successful try skips every later wait, every later try and the final failure step, and the deploy job ends green"
    - "The deploy job fails only when the sixth try failed, so email, webmentions and mentions-probe run after any successful try and are skipped when all six failed"
    - "The github-pages environment URL comes from whichever try produced page_url"
    - "hugo.yml parses as YAML and all five Python suites under tests/ pass"
    - "Exactly one ci: commit holds the hugo.yml change, and nothing else is in it"
  artifacts:
    - path: ".github/workflows/hugo.yml"
      provides: "deploy job with six continue-on-error deploy-pages tries, five waits, and a final step that fails only when try6 failed"
      contains: "id: try6"
  key_links:
    - from: ".github/workflows/hugo.yml deploy steps try2..try6 and each wait step"
      to: "the previous try's step outcome"
      via: "step-level if: steps.try<N-1>.outcome == 'failure' (outcome, not conclusion, because continue-on-error turns a failed conclusion into success)"
      pattern: "steps\\.try[1-5]\\.outcome == 'failure'"
    - from: ".github/workflows/hugo.yml jobs email, webmentions, mentions-probe"
      to: "the deploy job"
      via: "needs: deploy (mentions-probe: needs: [build, deploy])"
      pattern: "needs: deploy"
---

<objective>
Review the retry change already written in the working tree of `.github/workflows/hugo.yml`, fix only real defects, and commit it as one `ci:` commit. Nothing is re-implemented.

Purpose: on 2026-11-06 Pages refused the deploy that notes.yml dispatched to add a note's u-syndication links for about 45 minutes ("Deployment request failed ... due to in progress deployment. Please cancel <sha> first"), although the previous deploy had gone green and the Pages cancel API said that deployment was finished. Nothing retried and a human had to start a deploy. The diff makes the deploy job try up to six times over about 52 minutes and fail only when every try failed.

Output: one `ci:` commit on main containing only `.github/workflows/hugo.yml`, plus the review verdicts recorded in the SUMMARY.

Shape note: this plan does not lead with a tracer task. A tracer proves a new path through the layers, and here the implementation already exists and the scope is the live diff (per the planning constraints). The two tasks are review, then commit.
</objective>

<execution_context>
@~/.claude/gsd-core/workflows/execute-plan.md
@~/.claude/gsd-core/templates/summary.md
</execution_context>

<context>
@.planning/STATE.md
@CLAUDE.md
@.github/workflows/hugo.yml
@.github/workflows/notes.yml

Scope authority: the live output of `git diff .github/workflows/hugo.yml`. At planning time the diff (a) adds a comment block above `deploy:` explaining the incident, (b) replaces the single deploy step with steps `try1` to `try6`, each `uses: actions/deploy-pages@v5` with `continue-on-error: true`, with a sleep step before each of try2..try6 (120, 300, 600, 900, 1200 seconds), (c) adds a final step "Fail if every try failed", (d) changes `environment.url` to an `||` chain over the six tries' `page_url`, and (e) adds `timeout-minutes: 70` to the deploy job.

Grounded facts the review relies on (checked while planning):
- actions/deploy-pages v5 inputs: `timeout` defaults to 600000 ms (10 minutes) per try; its only output is `page_url`.
- `tests/test-notes.py` class `WorkflowConfig` already parses hugo.yml: it pins the job list `build, deploy, email, webmentions, mentions-probe`, the `pages` concurrency group, the send_email default, and that no hugo.yml job holds `contents: write`. It passes with the diff applied.
- All five suites passed with the diff applied at planning time (about 70 seconds in total; test-notes.py is about 55 seconds of it).
- At git HEAD, hugo.yml contains no `try1`, so the structural check in Task 1 fails on HEAD and passes only with the diff.
- The old step id appears outside hugo.yml only in historical planning docs under `.planning/phases/04-production-deploy/`. Leave those alone.
</context>

<tasks>

<task type="auto">
  <name>Task 1: Review the retry diff against its contract and run every gate</name>
  <files>.github/workflows/hugo.yml</files>
  <read_first>
    - .github/workflows/hugo.yml (the whole file: the deploy job plus the email, webmentions and mentions-probe jobs below it)
    - output of git diff .github/workflows/hugo.yml
  </read_first>
  <action>
Read the live diff and confirm each item below. Every verdict here was reasoned out during planning. Your job is to confirm that the file matches it, not to argue it again. Record one line per item in the SUMMARY: the verdict, plus the arithmetic for item 3.

1. Step-level if and outcome (GQA-RETRY): each of try2..try6, and the wait step right before it, carries `if: steps.try<N-1>.outcome == 'failure'`, and every try carries `continue-on-error: true`. Outcome is the right property. With continue-on-error, a failed step's conclusion becomes success while its outcome stays failure. The implicit `success() &&` prefix on a step-level if stays true, because a continue-on-error failure leaves the job status successful. Correct as written.

2. Environment URL: `jobs.<id>.environment.url` accepts the steps context. In GitHub expressions, `||` returns the first non-empty operand, and a failed or skipped try contributes an empty page_url. deploy-pages can set page_url before a later failure within the same try, which is harmless because every try's page_url is the same site URL. Correct as written.

3. timeout-minutes 70: the waits total 3120 seconds (52 minutes). In the observed failure, Pages refuses the request in seconds, so try6 starts at about 53 minutes with about 17 minutes left. That is more than deploy-pages' 10-minute per-try default. If instead tries hang until their own 10-minute timeouts, the worst case is 52 + 60 = 112 minutes, so the 70-minute cap can end the job before try6 runs. The run still ends non-green and the downstream jobs are skipped, the same as when all six tries fail. Verdict: keep 70. It is not a defect. Do not reword the diff's comment over this. Put the hang-path arithmetic in the SUMMARY.

4. A success short-circuits: when try N succeeds, try N+1 is skipped (outcome skipped). Every later wait, every later try and the final step test for 'failure' only, so all of them skip. Correct as written.

5. Final failure step: "Fail if every try failed" has `if: steps.try6.outcome == 'failure'`, has no continue-on-error, and exits 1. try6 runs only when try5 failed, which runs only when try4 failed, and so on back to try1. So this step fires only when all six failed. Correct as written.

6. Downstream needs (GQA-RETRY): deploy keeps `needs: build`, email and webmentions keep `needs: deploy`, and mentions-probe keeps `needs: [build, deploy]`. A failed try under continue-on-error leaves the deploy job successful, so a late success still lets the downstream jobs run. Correct as written.

7. No stale reference: hugo.yml no longer refers to the old step id `deployment` in any expression.

8. Residual risk, not a defect: the workflow-level concurrency group `pages` holds at most one pending run. While a retry window is open, a second queued run cancels the earlier pending one. Content is unaffected, because the newer run builds the newer main. But a pending dispatch with `send_email: true` could be replaced by a push or a notes.yml dispatch that only leaves a draft. This existed before; the diff widens the window from about a minute to up to about an hour. Write it in the SUMMARY under a heading Matt will see. Do not change concurrency, because that is outside this diff's scope.

What counts as a real defect: YAML that does not parse; an if that can never fire or fires on the wrong condition; a try without continue-on-error; a final step that can fire after a successful try or fails to fire after six failures; a downstream job that loses its dependency on deploy; any check in verify failing. For a real defect, make the smallest edit to `.github/workflows/hugo.yml` that fixes it and rerun the whole verify. These are NOT defects: comment wording, step names, wait durations, the 70-minute cap (see item 3), and the first try's step being named without "(try 1)". Do not add tests, scripts or files. Do not touch notes.yml.
  </action>
  <verify>
    <automated>python3 -I -c 'import yaml; t=open(".github/workflows/hugo.yml").read(); w=yaml.safe_load(t); j=w["jobs"]; d=j["deploy"]; s=d["steps"]; f="steps.try%d.outcome == \x27failure\x27"; tries=[x for x in s if x.get("uses")=="actions/deploy-pages@v5"]; waits=[x for x in s if str(x.get("run","")).startswith("sleep ")]; sl=[int(x["run"].split()[1]) for x in waits]; kind=[x.get("id") or ("wait" if x in waits else "final") for x in s]; assert kind==["try1","wait","try2","wait","try3","wait","try4","wait","try5","wait","try6","final"], kind; assert all(x.get("continue-on-error") is True for x in tries); assert "if" not in tries[0]; assert [x["if"] for x in tries[1:]]==[f%i for i in range(1,6)]; assert [x["if"] for x in waits]==[f%i for i in range(1,6)]; assert sl==[120,300,600,900,1200], sl; fin=s[-1]; assert fin["if"]==f%6 and "exit 1" in fin["run"] and "continue-on-error" not in fin; assert d["needs"]=="build" and d["timeout-minutes"]*60>=sum(sl)+600; assert d["environment"]["url"].strip("${} ")==" || ".join("steps.try%d.outputs.page_url"%i for i in range(1,7)); assert j["email"]["needs"]=="deploy" and j["webmentions"]["needs"]=="deploy" and j["mentions-probe"]["needs"]==["build","deploy"]; assert "steps.deployment" not in t; print("deploy retry chain OK")' && for t in tests/test-*.py; do python3 -I -S -B "$t" || exit 1; done</automated>
  </verify>
  <done>The structural check prints "deploy retry chain OK". It covers: YAML parses; step order try1, wait, try2 ... try6, final; all six tries continue-on-error; the if chain on outcome; sleeps 120/300/600/900/1200; final step gated on try6 and exiting 1; timeout at least the waits plus one full deploy-pages window; the URL chain over all six tries; downstream needs intact; no old step id. Each of the five suites (test-notes-backstop, test-notes, test-pull-webmentions, test-send-fa-email, test-send-webmentions) reports OK. Note: the suites run in a loop because python3 runs only one script per call, so a glob passed to a single python3 hands the rest to unittest as bogus test names. The eight verdicts are noted for the SUMMARY. Any defect fixed is named with its one-line cause.</done>
</task>

<task type="auto">
  <name>Task 2: Commit the reviewed change as one ci: commit</name>
  <files>.github/workflows/hugo.yml</files>
  <read_first>
    - output of git status --porcelain (confirm what else is dirty, so none of it is swept in)
  </read_first>
  <action>
Stage exactly one path with `git add .github/workflows/hugo.yml` (GQA-COMMIT). Never use `git add .`, `git add -A` or `git commit -a`. The new `.planning/quick/261106-gqa-*` files belong to the orchestrator's docs commit, not this one. Commit on the current branch (main; branching_strategy is none). Do not pass --no-verify. Use one -m per paragraph so the message is:

Subject: `ci: retry the Pages deploy up to six times over about 52 minutes`

Body paragraph 1: On 2026-11-06 Pages refused the deploy that notes.yml dispatched to add a note's syndication links, for about 45 minutes ("due to in progress deployment. Please cancel <sha> first"), while the cancel API reported that deployment finished. Nothing retried, and a human started the deploy later.

Body paragraph 2: The deploy job now tries actions/deploy-pages up to six times, waiting 2, 5, 10, 15 and 20 minutes between tries, and fails only when the sixth try fails. A successful try skips every later wait and try. email, webmentions and mentions-probe still need deploy.

Trailer paragraph: `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`

If Task 1 fixed a defect, add one sentence to body paragraph 2 naming the fix. Do not push. Pushing is outside this plan. A push to main will run the new deploy job, which will be its first live exercise.
  </action>
  <verify>
    <automated>files="$(git show --format= --name-only HEAD)" && test "$files" = ".github/workflows/hugo.yml" && subj="$(git log -1 --format=%s)" && case "$subj" in "ci: retry the Pages deploy"*) ;; *) false ;; esac && body="$(git log -1 --format=%B)" && case "$body" in *"Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"*) ;; *) false ;; esac && git diff --quiet HEAD -- .github/workflows/hugo.yml && echo "one ci commit, hugo.yml only, tree matches"</automated>
  </verify>
  <done>HEAD is a single commit whose subject starts "ci: retry the Pages deploy" and which changes only .github/workflows/hugo.yml. The working-tree hugo.yml equals the committed one, and the commit carries the Co-Authored-By trailer. Nothing was pushed, and no other dirty or untracked file entered the commit.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| deploy job to the Pages API | deploy-pages trades the job's OIDC token (workflow-level `id-token: write`, `pages: write`) for a Pages deployment, up to six times per run |
| `pages` concurrency group | One running and at most one pending run; the retry window holds the group for up to about 70 minutes |

## STRIDE Threat Register

| Threat ID | Category | Component | Severity | Disposition | Mitigation Plan |
|-----------|----------|-----------|----------|-------------|-----------------|
| T-gqa-01 | Repudiation | continue-on-error on every try | high | mitigate | The final step is gated on `steps.try6.outcome == 'failure'` and exits 1, so six failures cannot end green. The Task 1 structural check pins the gate, the missing continue-on-error, and the exit 1 |
| T-gqa-02 | Elevation of Privilege | deploy job permissions | medium | mitigate | The diff adds no permissions, secrets or `${{ }}` in run strings. test-notes.py's test_the_other_workflows_deploy_permissions_do_not_change stays green in Task 1 |
| T-gqa-03 | Denial of Service | `pages` concurrency during the retry window | medium | accept | A second queued run replaces the earlier pending one. Content still converges to the newest main, but a pending `send_email: true` dispatch can be lost to a draft. This existed before and the window is wider now. Recorded in the SUMMARY for Matt (Task 1 item 8); changing concurrency is outside this diff |
| T-gqa-04 | Denial of Service | job timeout vs hung tries | low | accept | If tries hang until deploy-pages' 10-minute timeout, the 70-minute cap can end the job before try6. The run still ends non-green and the downstream jobs are skipped. Arithmetic recorded in the SUMMARY (Task 1 item 3) |
| T-gqa-SC | Tampering | npm/pip/cargo installs | high | accept | No package installs in this plan |
</threat_model>

<verification>
- The Task 1 structural check prints "deploy retry chain OK" (it fails at git HEAD, which has no try1).
- `for t in tests/test-*.py; do python3 -I -S -B "$t" || exit 1; done` exits 0 with five OK suites.
- The Task 2 check prints "one ci commit, hugo.yml only, tree matches".
- The SUMMARY records eight review verdicts, the timeout arithmetic, and the concurrency residual risk.
</verification>

<success_criteria>
The retry diff is confirmed correct item by item, or fixed where a real defect was found. hugo.yml parses, every Python suite is green, and the change sits on main as exactly one `ci:` commit touching only `.github/workflows/hugo.yml`. Matt can read the hang-path timeout note and the concurrency residual risk in the SUMMARY without opening the workflow.
</success_criteria>

<output>
Create `.planning/quick/261106-gqa-retry-the-github-pages-deploy-step-in-hu/261106-gqa-SUMMARY.md` when done
</output>
