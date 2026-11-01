#!/usr/bin/env python3
"""Tests for scripts/notes-backstop.sh and scripts/install-notes-backstop.sh.

    python3 -I -S -B tests/test-notes-backstop.py

macOS only, and deliberately not in CI: the backstop is a LaunchAgent on this Mac, uses BSD
`date -j`/`date -r`, and has no reason to exist on an Ubuntu runner. Run it here after
touching either script.

Every case runs the real script against a stand-in `gh` (NOTES_BACKSTOP_GH) that prints a
canned last-run time and records each call, with "now" pinned (NOTES_BACKSTOP_NOW), so no
case touches GitHub. The point of the backstop is to act when GitHub has gone quiet and to
stay out of the way when it hasn't, so both directions are asserted, along with the
sentinel's write-on-failure / clear-on-success contract.
"""
import os
import plistlib
import stat
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "notes-backstop.sh"
INSTALLER = ROOT / "scripts" / "install-notes-backstop.sh"

NOW = int(datetime(2026, 11, 1, 18, 30, tzinfo=timezone.utc).timestamp())

FAKE_GH = """#!/bin/bash
echo "$*" >> "$FAKE_GH_CALLS"
case "$1 $2" in
  "run list")     printf '%s\\n' "$FAKE_GH_LAST"; exit "${FAKE_GH_LIST_RC:-0}" ;;
  "workflow run") echo "dispatched"; exit "${FAKE_GH_RUN_RC:-0}" ;;
esac
exit 99
"""


def iso(minutes_before_now):
    return datetime.fromtimestamp(NOW - minutes_before_now * 60, timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


class Backstop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.gh = d / "gh"
        self.gh.write_text(FAKE_GH)
        self.gh.chmod(self.gh.stat().st_mode | stat.S_IEXEC)
        self.calls = d / "calls.log"
        self.calls.touch()
        self.sentinel = d / "logs" / "backstop.SENTINEL.md"

    def tearDown(self):
        self.tmp.cleanup()

    def run_script(self, last, list_rc=0, run_rc=0, gh=None):
        env = {
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",  # launchd's PATH
            "HOME": self.tmp.name,
            "NOTES_BACKSTOP_GH": str(gh or self.gh),
            "NOTES_BACKSTOP_NOW": str(NOW),
            "NOTES_BACKSTOP_SENTINEL": str(self.sentinel),
            "FAKE_GH_CALLS": str(self.calls),
            "FAKE_GH_LAST": last,
            "FAKE_GH_LIST_RC": str(list_rc),
            "FAKE_GH_RUN_RC": str(run_rc),
        }
        return subprocess.run(["/bin/bash", str(SCRIPT)], env=env, capture_output=True, text=True)

    def dispatched(self):
        return any(line.startswith("workflow run notes.yml") for line in self.calls.read_text().splitlines())

    def test_recent_run_does_nothing(self):
        r = self.run_script(iso(6))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.dispatched())
        self.assertIn("nothing to do", r.stdout)

    def test_gap_at_threshold_dispatches(self):
        r = self.run_script(iso(20))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.dispatched())

    def test_just_under_threshold_does_not(self):
        r = self.run_script(iso(19))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.dispatched())

    def test_the_2026_11_01_gap_dispatches_against_main(self):
        # 16:54Z last run, checked at 18:30Z: the shape of the day this was built for.
        r = self.run_script("2026-11-01T16:54:53Z")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("workflow run notes.yml --repo mstine/falkensmage-website --ref main",
                      self.calls.read_text())
        self.assertIn("DISPATCHED: last run 95m ago", r.stdout)

    def test_no_runs_ever_dispatches(self):
        r = self.run_script("")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(self.dispatched())

    def test_list_failure_writes_sentinel_and_does_not_dispatch(self):
        r = self.run_script(iso(60), list_rc=4)
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(self.dispatched())
        self.assertIn("gh run list exited 4", self.sentinel.read_text())

    def test_dispatch_failure_writes_sentinel(self):
        r = self.run_script(iso(60), run_rc=1)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("gh workflow run exited 1", self.sentinel.read_text())

    def test_unparseable_time_fails_loudly(self):
        r = self.run_script("yesterday-ish")
        self.assertNotEqual(r.returncode, 0)
        self.assertFalse(self.dispatched())
        self.assertIn("could not parse", self.sentinel.read_text())

    def test_clean_run_clears_sentinel(self):
        self.run_script(iso(60), list_rc=4)
        self.assertTrue(self.sentinel.exists())
        r = self.run_script(iso(3))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertFalse(self.sentinel.exists())


class Installer(unittest.TestCase):
    def test_generated_plist(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "agent.plist"
            r = subprocess.run(["/bin/bash", str(INSTALLER), "--output", str(out)],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0, r.stderr)
            p = plistlib.loads(out.read_bytes())
        self.assertEqual(p["Label"], "net.ritualsync.falkensmage-notes-backstop")
        self.assertEqual(p["ProgramArguments"], ["/bin/bash", str(SCRIPT)])
        self.assertEqual(p["StartInterval"], 900)
        self.assertTrue(p["RunAtLoad"])
        self.assertEqual(p["EnvironmentVariables"]["PATH"], "/usr/bin:/bin:/usr/sbin:/sbin")


if __name__ == "__main__":
    unittest.main()
