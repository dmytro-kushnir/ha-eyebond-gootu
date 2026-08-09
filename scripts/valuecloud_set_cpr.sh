#!/bin/sh
# Background launchers — HA shell_command hard-limits at 60s.
set -eu
MODE="${1:-}"
if [ -z "$MODE" ]; then
  echo "usage: $0 \"<mode>\"" >&2
  exit 2
fi
mkdir -p /config/shell
# Avoid nohup.out on SD; discard launcher stdout.
nohup python3 /config/shell/valuecloud_set_cpr.py --mode "$MODE" \
  >/dev/null 2>>/config/shell/valuecloud_cpr.log &
exit 0
