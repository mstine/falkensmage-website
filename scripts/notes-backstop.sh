#!/usr/bin/env bash
# notes-backstop.sh — restart the Notes syndication schedule when GitHub drops it.
#
# WHY THIS EXISTS: .github/workflows/notes.yml runs on cron every 15 minutes, and GitHub
# treats scheduled runs as best effort. On 2026-11-01 it fired every 15 minutes until
# 03:18Z, then twice in sixteen hours, and the Rewired bonus Note scheduled for 12:30 CST
# went out at 12:51 only because someone noticed and dispatched it by hand. Nothing
# reported the gap: a skipped cron run leaves no trace at all.
#
# WHAT IT DOES: asks GitHub when notes.yml last started (any trigger, any outcome). If that
# was more than NOTES_BACKSTOP_MAX_GAP_MIN minutes ago (default 20: the cron slots are 15
# apart, plus GitHub's usual few minutes of lag), it dispatches the workflow. It never
# decides whether a note is due. The workflow already does that, makes no network call
# when nothing is, and posts each note at most once per platform (see the header of
# scripts/syndicate-notes.py), so an extra run is always safe. This only puts the 15-minute
# rhythm back; when GitHub's schedule is healthy it does nothing.
#
# FAILURE: any failure (gh missing, auth gone, API down) writes NOTES_BACKSTOP_SENTINEL and
# exits non-zero; the next clean run removes it. Same convention as the Rewired jobs'
# ~/Library/Logs/*.SENTINEL.md files.
#
# Runs from a LaunchAgent (scripts/install-notes-backstop.sh) under launchd's bare PATH, so
# gh is located explicitly. It runs only while this Mac is awake.
#
# Overrides (tests/test-notes-backstop.py uses all of them):
#   NOTES_BACKSTOP_GH            gh binary (default: /opt/homebrew/bin/gh, /usr/local/bin/gh, gh)
#   NOTES_BACKSTOP_REPO          default mstine/falkensmage-website
#   NOTES_BACKSTOP_MAX_GAP_MIN   default 20
#   NOTES_BACKSTOP_NOW           epoch seconds standing in for "now"
#   NOTES_BACKSTOP_SENTINEL      default ~/Library/Logs/falkensmage-notes-backstop.SENTINEL.md

set -uo pipefail

REPO="${NOTES_BACKSTOP_REPO:-mstine/falkensmage-website}"
MAX_GAP_MIN="${NOTES_BACKSTOP_MAX_GAP_MIN:-20}"
NOW="${NOTES_BACKSTOP_NOW:-$(date -u +%s)}"
SENTINEL="${NOTES_BACKSTOP_SENTINEL:-$HOME/Library/Logs/falkensmage-notes-backstop.SENTINEL.md}"
WORKFLOW="notes.yml"

stamp() { date -u -r "$NOW" +%Y-%m-%dT%H:%M:%SZ; }

fail() {
  mkdir -p "$(dirname "$SENTINEL")"
  {
    echo "# falkensmage Notes backstop FAILED — $(stamp)"
    echo
    echo "$1"
    echo
    echo "While this stands, scheduled Notes depend on GitHub's cron alone. A later clean run removes this file."
  } > "$SENTINEL"
  echo "$(stamp) FAIL: $1" >&2
  exit 1
}

GH=""
for cand in ${NOTES_BACKSTOP_GH:-} /opt/homebrew/bin/gh /usr/local/bin/gh gh; do
  if command -v "$cand" >/dev/null 2>&1; then GH="$(command -v "$cand")"; break; fi
done
[ -n "$GH" ] || fail "no gh found (tried: ${NOTES_BACKSTOP_GH:-} /opt/homebrew/bin/gh /usr/local/bin/gh gh) — set NOTES_BACKSTOP_GH"

# `&& … || …`, not a bare assignment: a failing $(…) must reach fail(), not vanish.
last="$("$GH" run list --repo "$REPO" --workflow "$WORKFLOW" --limit 1 \
  --json createdAt --jq '.[0].createdAt // ""' 2>&1)" && rc=0 || rc=$?
[ "$rc" -eq 0 ] || fail "gh run list exited $rc: $last"

if [ -z "$last" ]; then
  gap_min="none"
else
  last_epoch="$(date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$last" +%s 2>/dev/null)" \
    || fail "could not parse the last run time: '$last'"
  gap_min=$(( (NOW - last_epoch) / 60 ))
fi

if [ "$gap_min" != "none" ] && [ "$gap_min" -lt "$MAX_GAP_MIN" ]; then
  rm -f "$SENTINEL"
  echo "$(stamp) ok: last run ${gap_min}m ago (${last}), nothing to do"
  exit 0
fi

out="$("$GH" workflow run "$WORKFLOW" --repo "$REPO" --ref main 2>&1)" && rc=0 || rc=$?
[ "$rc" -eq 0 ] || fail "gh workflow run exited $rc after a ${gap_min}m gap: $out"

rm -f "$SENTINEL"
echo "$(stamp) DISPATCHED: last run ${gap_min}m ago (${last:-never}) — GitHub's schedule had gone quiet"
