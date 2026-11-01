#!/usr/bin/env bash
# Generate and install the Notes backstop LaunchAgent (scripts/notes-backstop.sh).
#
# Same shape as rewired-site's scripts/install-launchagent.sh: this script IS the source of
# truth. It generates the plist from a heredoc, deriving the repo path from its own
# location, then (re)loads the agent. No plist is committed, so there is no second copy to
# drift from this one.
#
# Every 900 seconds (StartInterval). launchd skips intervals while the Mac sleeps and runs
# once on wake, which is what a backstop wants: the first run after waking catches up.
#
# Usage:
#   scripts/install-notes-backstop.sh              # generate + (re)load the real agent
#   scripts/install-notes-backstop.sh --output P   # generate only, to path P (no load)
#   scripts/install-notes-backstop.sh --no-load    # generate the real plist, skip launchctl
#
# Safe to re-run any time.

set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="net.ritualsync.falkensmage-notes-backstop"
LOG="$HOME/Library/Logs/falkensmage-notes-backstop.launchd.log"

PLIST="$HOME/Library/LaunchAgents/${LABEL}.plist"
LOAD=1

while [ $# -gt 0 ]; do
  case "$1" in
    --output)
      [ $# -ge 2 ] || { echo "--output requires a path argument" >&2; exit 1; }
      PLIST="$2"
      LOAD=0
      shift 2
      ;;
    --no-load)
      LOAD=0
      shift
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 1
      ;;
  esac
done

mkdir -p "$(dirname "$PLIST")"

cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${REPO}/scripts/notes-backstop.sh</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/usr/bin:/bin:/usr/sbin:/sbin</string>
  </dict>
  <key>StartInterval</key>
  <integer>900</integer>
  <key>RunAtLoad</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${LOG}</string>
  <key>StandardErrorPath</key>
  <string>${LOG}</string>
</dict>
</plist>
EOF

if command -v plutil >/dev/null 2>&1; then
  plutil -lint "$PLIST"
fi

if [ "$LOAD" -eq 1 ]; then
  mkdir -p "$(dirname "$LOG")"
  # Idempotent: unload first (no-op if it wasn't loaded) so a second run
  # doesn't fail on "already loaded".
  launchctl unload "$PLIST" 2>/dev/null || true
  launchctl load "$PLIST"
  echo "Installed and loaded: $PLIST"
else
  echo "Generated: $PLIST"
fi
