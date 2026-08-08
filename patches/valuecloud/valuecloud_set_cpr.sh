#!/bin/sh
# Launch ValueCloud CPR write in background (HA shell_command limit is 60s).
set -eu
MODE="${1:-}"
if [ -z "$MODE" ]; then
  echo "usage: $0 \"<mode>\"" >&2
  exit 2
fi
LOG="/config/shell/valuecloud_cpr.log"
mkdir -p /config/shell
# Soft-rotate oversized log before append.
if [ -f "$LOG" ]; then
  size=$(wc -c <"$LOG" 2>/dev/null || echo 0)
  if [ "$size" -gt 100000 ]; then
    tail -c 50000 "$LOG" >"$LOG.tmp" && mv "$LOG.tmp" "$LOG"
  fi
fi
{
  echo "---- $(date -Iseconds) mode=$MODE ----"
  python3 /config/shell/valuecloud_set_cpr.py --mode "$MODE"
} >>"$LOG" 2>&1 &
exit 0
